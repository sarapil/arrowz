# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
Webhook Handlers - Endpoints for receiving webhooks from Engine boxes.

These endpoints handle incoming notifications and events from
the Engine layer, including alerts, WAN failover events, and
client state changes.
"""

import frappe
from frappe import _


@frappe.whitelist(methods=["POST"], allow_guest=True)
def engine_webhook(**kwargs):
	"""General webhook endpoint for Engine notifications.

	The Engine sends webhooks for:
	- WAN failover events
	- Service failures
	- Threshold alerts (CPU, RAM, disk)
	- Client events (mass disconnect, etc.)
	"""
	box_name = _authenticate_request()
	if not box_name:
		frappe.throw(_("Unauthorized"), frappe.AuthenticationError)

	data = frappe.parse_json(frappe.request.data) if frappe.request.data else {}
	event_type = data.get("event_type", "")

	handlers = {
		"wan_failover": _handle_wan_failover,
		"service_failure": _handle_service_failure,
		"threshold_alert": _handle_threshold_alert,
		"client_event": _handle_client_event,
		"config_applied": _handle_config_applied,
		"firewall_event": _handle_firewall_event,
	}

	handler = handlers.get(event_type, _handle_generic_event)
	result = handler(box_name, data)

	frappe.db.commit()
	return result


def _handle_wan_failover(box_name: str, data: dict) -> dict:
	"""Handle WAN failover event from Engine."""
	# Log the event
	frappe.get_doc({
		"doctype": "Network Event",
		"arrowz_box": box_name,
		"event_type": "WAN Failover",
		"source": data.get("wan_name"),
		"details": data.get("details", "WAN failover triggered"),
		"severity": "Warning",
		"raw_data": frappe.as_json(data),
	}).insert(ignore_permissions=True)

	# Create alert
	frappe.get_doc({
		"doctype": "Network Alert",
		"arrowz_box": box_name,
		"alert_type": "WAN Failover",
		"severity": "Warning",
		"message": _("WAN failover on {0}: {1} → {2}").format(
			box_name,
			data.get("from_wan", "unknown"),
			data.get("to_wan", "unknown"),
		),
		"details": frappe.as_json(data),
	}).insert(ignore_permissions=True)

	# Update WAN connection statuses
	if data.get("from_wan"):
		wan_name = data["from_wan"]
		if frappe.db.exists("WAN Connection", wan_name):
			frappe.db.set_value("WAN Connection", wan_name, "status", "Disconnected")

	if data.get("to_wan"):
		wan_name = data["to_wan"]
		if frappe.db.exists("WAN Connection", wan_name):
			frappe.db.set_value("WAN Connection", wan_name, "status", "Connected")

	# Realtime notification
	frappe.publish_realtime(
		"arrowz_wan_failover",
		{"box": box_name, "data": data},
		after_commit=True,
	)

	return {"status": "success", "message": "WAN failover processed"}


def _handle_service_failure(box_name: str, data: dict) -> dict:
	"""Handle service failure event from Engine."""
	service = data.get("service_name", "unknown")

	frappe.get_doc({
		"doctype": "Network Alert",
		"arrowz_box": box_name,
		"alert_type": "Service Down",
		"severity": "Critical",
		"message": _("Service {0} failed on {1}").format(service, box_name),
		"details": frappe.as_json(data),
	}).insert(ignore_permissions=True)

	frappe.get_doc({
		"doctype": "Network Event",
		"arrowz_box": box_name,
		"event_type": "Service Restart",
		"source": service,
		"details": data.get("details", f"Service {service} failed"),
		"severity": "Error",
		"raw_data": frappe.as_json(data),
	}).insert(ignore_permissions=True)

	frappe.publish_realtime(
		"arrowz_service_failure",
		{"box": box_name, "service": service},
		after_commit=True,
	)

	return {"status": "success", "message": "Service failure logged"}


def _handle_threshold_alert(box_name: str, data: dict) -> dict:
	"""Handle threshold alert from Engine (CPU, RAM, disk)."""
	alert_type = data.get("metric", "Custom")
	value = data.get("value", 0)

	# Map metric to alert type
	type_map = {
		"cpu": "High CPU",
		"ram": "High RAM",
		"disk": "High Disk",
	}

	frappe.get_doc({
		"doctype": "Network Alert",
		"arrowz_box": box_name,
		"alert_type": type_map.get(alert_type, alert_type),
		"severity": data.get("severity", "Warning"),
		"message": _("{0} alert on {1}: {2}%").format(alert_type.upper(), box_name, value),
		"details": frappe.as_json(data),
	}).insert(ignore_permissions=True)

	return {"status": "success", "message": "Threshold alert logged"}


def _handle_client_event(box_name: str, data: dict) -> dict:
	"""Handle client connection/disconnection event."""
	mac = data.get("mac_address", "").upper()
	action = data.get("action", "")

	event_type = "Client Connected" if action == "connect" else "Client Disconnected"

	frappe.get_doc({
		"doctype": "Network Event",
		"arrowz_box": box_name,
		"event_type": event_type,
		"source": mac,
		"details": data.get("details", ""),
		"severity": "Info",
		"raw_data": frappe.as_json(data),
	}).insert(ignore_permissions=True)

	# Update client status
	if mac and frappe.db.exists("Network Client", mac):
		status = "Online" if action == "connect" else "Offline"
		updates = {"status": status, "last_seen": frappe.utils.now_datetime()}
		if action == "connect":
			updates["ip_address"] = data.get("ip_address")
			updates["connection_type"] = data.get("connection_type")
		frappe.db.set_value("Network Client", mac, updates, update_modified=False)

	return {"status": "success"}


def _handle_config_applied(box_name: str, data: dict) -> dict:
	"""Handle config applied confirmation from Engine."""
	frappe.get_doc({
		"doctype": "Arrowz Box Health Log",
		"arrowz_box": box_name,
		"log_type": "Config Push",
		"status": "Online",
		"message": _("Configuration applied successfully"),
		"details": frappe.as_json(data),
	}).insert(ignore_permissions=True)

	if data.get("config_hash"):
		frappe.db.set_value("Arrowz Box", box_name, "engine_config_hash", data["config_hash"])

	return {"status": "success"}


def _handle_firewall_event(box_name: str, data: dict) -> dict:
	"""Handle firewall log entries from Engine."""
	entries = data.get("entries", [])

	for entry in entries[:100]:  # Limit batch size
		frappe.get_doc({
			"doctype": "Firewall Log",
			"arrowz_box": box_name,
			"action": entry.get("action"),
			"protocol": entry.get("protocol"),
			"source_ip": entry.get("source_ip"),
			"destination_ip": entry.get("destination_ip"),
			"source_port": entry.get("source_port"),
			"destination_port": entry.get("destination_port"),
			"interface_in": entry.get("interface_in"),
			"interface_out": entry.get("interface_out"),
			"packet_length": entry.get("packet_length"),
			"raw_log": entry.get("raw_log"),
		}).insert(ignore_permissions=True)

	return {"status": "success", "logged": len(entries)}


def _handle_generic_event(box_name: str, data: dict) -> dict:
	"""Handle any unrecognized event type."""
	frappe.get_doc({
		"doctype": "Network Event",
		"arrowz_box": box_name,
		"event_type": "Config Changed",
		"source": data.get("source", "Engine"),
		"details": data.get("details", frappe.as_json(data)),
		"severity": data.get("severity", "Info"),
		"raw_data": frappe.as_json(data),
	}).insert(ignore_permissions=True)

	return {"status": "success"}


def _authenticate_request() -> str | None:
	"""Authenticate incoming webhook request.

	Returns:
		Box name if authenticated, None otherwise
	"""
	auth_header = frappe.request.headers.get("Authorization", "")
	if not auth_header.startswith("Bearer "):
		return None

	token = auth_header[7:]
	box_name = frappe.request.headers.get("X-Arrowz-Box", "")

	if not box_name:
		return None

	try:
		box = frappe.get_doc("Arrowz Box", box_name)
		stored_token = box.get_password("api_token")
		if stored_token and stored_token == token:
			return box_name
	except Exception:
		pass

	return None
