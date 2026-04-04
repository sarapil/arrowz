# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Hotspot API - Endpoints for WiFi Hotspot and Captive Portal operations.

Handles voucher validation, user authentication, session management,
and marketing campaign tracking for captive portals.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date


@frappe.whitelist(methods=["POST"], allow_guest=True)
def validate_voucher(voucher_code: str, mac_address: str):
	"""Validate a WiFi voucher and start a session.

	Called by the captive portal when a user enters a voucher code.

	Args:
		voucher_code: The voucher code entered by user
		mac_address: Client MAC address from captive portal
	"""
	if not frappe.db.exists("WiFi Voucher", voucher_code):
		return {"status": "error", "message": _("Invalid voucher code")}

	voucher = frappe.get_doc("WiFi Voucher", voucher_code)

	if voucher.status != "Available":
		return {"status": "error", "message": _("Voucher is {0}").format(voucher.status)}

	# Activate voucher
	voucher.status = "Active"
	voucher.activated_on = now_datetime()
	voucher.expires_on = add_to_date(now_datetime(), hours=voucher.validity_hours)
	voucher.used_by_mac = mac_address.upper()
	voucher.save(ignore_permissions=True)

	# Create session
	session = frappe.get_doc({
		"doctype": "WiFi User Session",
		"wifi_voucher": voucher_code,
		"mac_address": mac_address.upper(),
		"start_time": now_datetime(),
		"status": "Active",
	})
	session.insert(ignore_permissions=True)

	frappe.db.commit()

	# Authorize on engine
	_authorize_on_engine(mac_address, voucher)

	return {
		"status": "success",
		"message": _("Voucher activated"),
		"session_id": session.name,
		"expires_on": str(voucher.expires_on),
		"bandwidth_plan": voucher.bandwidth_plan,
	}


@frappe.whitelist(methods=["POST"], allow_guest=True)
def authenticate_user(username: str, password: str, mac_address: str):
	"""Authenticate a WiFi user account.

	Called by the captive portal for username/password authentication.

	Args:
		username: WiFi user account username
		password: User password
		mac_address: Client MAC address
	"""
	if not frappe.db.exists("WiFi User Account", username):
		return {"status": "error", "message": _("Invalid credentials")}

	user_account = frappe.get_doc("WiFi User Account", username)

	if user_account.status != "Active":
		return {"status": "error", "message": _("Account is {0}").format(user_account.status)}

	# Check password
	stored_password = user_account.get_password("password")
	if stored_password != password:
		return {"status": "error", "message": _("Invalid credentials")}

	# Check max devices
	if user_account.max_devices:
		from frappe.query_builder import DocType

		WUS = DocType("WiFi User Session")
		active_sessions = (
			frappe.qb.from_(WUS)
			.select(WUS.name)
			.where(WUS.wifi_user_account == username)
			.where(WUS.status == "Active")
			.run()
		)
		if len(active_sessions) >= user_account.max_devices:
			return {"status": "error", "message": _("Maximum devices exceeded")}

	# Check validity dates
	now = now_datetime()
	if user_account.valid_from and now < user_account.valid_from:
		return {"status": "error", "message": _("Account not yet active")}
	if user_account.valid_until and now > user_account.valid_until:
		user_account.status = "Expired"
		user_account.save(ignore_permissions=True)
		return {"status": "error", "message": _("Account has expired")}

	# Create session
	session = frappe.get_doc({
		"doctype": "WiFi User Session",
		"wifi_user_account": username,
		"mac_address": mac_address.upper(),
		"start_time": now,
		"status": "Active",
	})
	session.insert(ignore_permissions=True)

	# Update account stats
	user_account.last_login = now
	user_account.total_sessions = (user_account.total_sessions or 0) + 1
	user_account.save(ignore_permissions=True)

	frappe.db.commit()

	return {
		"status": "success",
		"message": _("Authentication successful"),
		"session_id": session.name,
		"bandwidth_plan": user_account.bandwidth_plan,
	}


@frappe.whitelist(methods=["POST"], allow_guest=True)
def end_session(session_id: str):
	"""End a WiFi hotspot session.

	Args:
		session_id: WiFi User Session name
	"""
	if not frappe.db.exists("WiFi User Session", session_id):
		return {"status": "error", "message": _("Session not found")}

	session = frappe.get_doc("WiFi User Session", session_id)
	session.end_time = now_datetime()
	session.status = "Ended"
	session.disconnect_reason = "Normal"
	session.save(ignore_permissions=True)

	# Deauthorize on engine
	if session.arrowz_box and session.mac_address:
		try:
			from arrowz.arrowz_api.utils.box_connector import BoxConnector

			connector = BoxConnector(box_name=session.arrowz_box)
			connector.deauthorize_hotspot_client(session.mac_address)
		except Exception:
			frappe.log_error("Failed to deauthorize client on engine", "Hotspot API Error")

	frappe.db.commit()
	return {"status": "success", "message": _("Session ended")}


@frappe.whitelist(methods=["POST"], allow_guest=True)
def track_campaign_event(campaign_name: str, event_type: str = "impression"):
	"""Track a marketing campaign event.

	Args:
		campaign_name: WiFi Marketing Campaign name
		event_type: Event type (impression or click)
	"""
	if not frappe.db.exists("WiFi Marketing Campaign", campaign_name):
		return {"status": "error"}

	if event_type == "impression":
		frappe.db.set_value(
			"WiFi Marketing Campaign",
			campaign_name,
			"impression_count",
			frappe.db.get_value("WiFi Marketing Campaign", campaign_name, "impression_count") + 1,
			update_modified=False,
		)
	elif event_type == "click":
		frappe.db.set_value(
			"WiFi Marketing Campaign",
			campaign_name,
			"click_count",
			frappe.db.get_value("WiFi Marketing Campaign", campaign_name, "click_count") + 1,
			update_modified=False,
		)

	frappe.db.commit()
	return {"status": "success"}


def _authorize_on_engine(mac_address: str, voucher):
	"""Authorize client on the Engine after successful auth.

	Args:
		mac_address: Client MAC
		voucher: WiFi Voucher document
	"""
	try:
		# Find the box from the hotspot profile or use default
		settings = frappe.get_cached_doc("Arrowz Network Settings")
		box_name = settings.default_box

		if box_name:
			from arrowz.arrowz_api.utils.box_connector import BoxConnector

			connector = BoxConnector(box_name=box_name)
			connector.authorize_hotspot_client(mac_address, {
				"voucher_code": voucher.name,
				"bandwidth_plan": voucher.bandwidth_plan,
				"validity_hours": voucher.validity_hours,
				"expires_on": str(voucher.expires_on),
			})
	except Exception:
		frappe.log_error("Failed to authorize client on engine", "Hotspot API Error")
