# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
Box Telemetry API - Endpoints for receiving telemetry data from boxes.

These endpoints are called by the Engine on each box to push
telemetry, health data, and event notifications to Frappe.
"""

import frappe
from frappe import _


@frappe.whitelist(methods=["POST"], allow_guest=True)
def heartbeat(**kwargs):
	"""Receive a heartbeat from an Arrowz Box Engine.

	This endpoint is called periodically by each box to report its status.
	Authentication is via Bearer token in the request headers.
	"""
	box_name = _authenticate_box()
	if not box_name:
		frappe.throw(_("Authentication failed"), frappe.AuthenticationError)

	data = frappe.parse_json(frappe.request.data) if frappe.request.data else {}

	try:
		box = frappe.get_doc("Arrowz Box", box_name)
		box.status = "Online"
		box.last_heartbeat = frappe.utils.now_datetime()

		# Update engine info if provided
		engine = data.get("engine", {})
		if engine:
			box.engine_version = engine.get("version", box.engine_version)
			box.engine_status = engine.get("status", box.engine_status)
			box.engine_uptime = engine.get("uptime", box.engine_uptime)

		box.save(ignore_permissions=True)
		frappe.db.commit()

		# Log health
		hw = data.get("hardware", {})
		if hw:
			frappe.get_doc({
				"doctype": "Arrowz Box Health Log",
				"arrowz_box": box_name,
				"log_type": "Heartbeat",
				"status": "Online",
				"cpu_usage": hw.get("cpu_usage"),
				"ram_usage": hw.get("ram_usage"),
				"disk_usage": hw.get("disk_usage"),
				"uptime_seconds": hw.get("uptime_seconds"),
				"active_clients": data.get("clients", {}).get("active", 0),
			}).insert(ignore_permissions=True)
			frappe.db.commit()

		return {"status": "success"}
	except Exception as e:
		frappe.log_error(f"Heartbeat error for {box_name}: {e}", "Box Telemetry Error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist(methods=["POST"], allow_guest=True)
def report_event(**kwargs):
	"""Receive a network event from an Arrowz Box Engine.

	Events include interface changes, client connections, service restarts, etc.
	"""
	box_name = _authenticate_box()
	if not box_name:
		frappe.throw(_("Authentication failed"), frappe.AuthenticationError)

	data = frappe.parse_json(frappe.request.data) if frappe.request.data else {}

	try:
		frappe.get_doc({
			"doctype": "Network Event",
			"arrowz_box": box_name,
			"event_type": data.get("event_type", "Config Changed"),
			"source": data.get("source"),
			"details": data.get("details"),
			"severity": data.get("severity", "Info"),
			"raw_data": frappe.as_json(data),
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		# Publish realtime event for UI
		frappe.publish_realtime(
			"arrowz_network_event",
			{"box": box_name, "event": data},
			after_commit=True,
		)

		return {"status": "success"}
	except Exception as e:
		frappe.log_error(f"Event report error for {box_name}: {e}", "Box Telemetry Error")
		return {"status": "error", "message": str(e)}


@frappe.whitelist(methods=["POST"], allow_guest=True)
def report_clients(**kwargs):
	"""Receive client status updates from an Arrowz Box Engine.

	Updates connected/disconnected client records.
	"""
	box_name = _authenticate_box()
	if not box_name:
		frappe.throw(_("Authentication failed"), frappe.AuthenticationError)

	data = frappe.parse_json(frappe.request.data) if frappe.request.data else {}
	clients = data.get("clients", [])

	updated = 0
	created = 0

	for client_data in clients:
		mac = client_data.get("mac_address", "").upper()
		if not mac:
			continue

		if frappe.db.exists("Network Client", mac):
			# Update existing client
			frappe.db.set_value("Network Client", mac, {
				"ip_address": client_data.get("ip_address"),
				"status": client_data.get("status", "Online"),
				"last_seen": frappe.utils.now_datetime(),
				"hostname": client_data.get("hostname") or frappe.db.get_value("Network Client", mac, "hostname"),
				"connection_type": client_data.get("connection_type"),
			}, update_modified=False)
			updated += 1
		else:
			# Auto-register if enabled
			settings = frappe.get_cached_doc("Arrowz Network Settings")
			if settings.auto_register_clients:
				try:
					frappe.get_doc({
						"doctype": "Network Client",
						"mac_address": mac,
						"hostname": client_data.get("hostname"),
						"ip_address": client_data.get("ip_address"),
						"arrowz_box": box_name,
						"client_group": settings.default_client_group,
						"status": "Online",
						"first_seen": frappe.utils.now_datetime(),
						"last_seen": frappe.utils.now_datetime(),
						"connection_type": client_data.get("connection_type"),
						"vendor": client_data.get("vendor"),
					}).insert(ignore_permissions=True)
					created += 1
				except Exception:
					pass  # Duplicate or validation error

	frappe.db.commit()
	return {"status": "success", "updated": updated, "created": created}


def _authenticate_box() -> str | None:
	"""Authenticate a box request using Bearer token.

	Returns:
		Box name if authenticated, None otherwise
	"""
	auth_header = frappe.request.headers.get("Authorization", "")
	if not auth_header.startswith("Bearer "):
		return None

	token = auth_header[7:]
	box_header = frappe.request.headers.get("X-Arrowz-Box", "")

	if not box_header:
		return None

	# Verify token matches box
	try:
		box = frappe.get_doc("Arrowz Box", box_header)
		stored_token = box.get_password("api_token")
		if stored_token and stored_token == token:
			return box_header
	except Exception:
		pass

	return None
