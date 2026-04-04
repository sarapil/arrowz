# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Client Provisioning API - Endpoints for network client operations.

Used by the UI and automation to manage client state
(block, unblock, disconnect, assign plans).
"""

import frappe
from frappe import _


@frappe.whitelist(methods=["POST"])
def block_client(mac_address: str, box_name: str = None, reason: str = ""):
	"""Block a network client by MAC address.

	Args:
		mac_address: Client MAC address
		box_name: Arrowz Box name (auto-detect from client if not provided)
		reason: Reason for blocking
	"""
	frappe.only_for(["AZ User", "AZ Manager", "System Manager"])


	mac = mac_address.upper().replace("-", ":")

	if not box_name and frappe.db.exists("Network Client", mac):
		box_name = frappe.db.get_value("Network Client", mac, "arrowz_box")

	if not box_name:
		frappe.throw(_("Cannot determine box for client {0}").format(mac))

	# Update client record
	if frappe.db.exists("Network Client", mac):
		frappe.db.set_value("Network Client", mac, {
			"is_blocked": 1,
			"status": "Blocked",
		})

	# Add to blacklist
	if not frappe.db.exists("MAC Blacklist", {"mac_address": mac, "arrowz_box": box_name}):
		frappe.get_doc({
			"doctype": "MAC Blacklist",
			"mac_address": mac,
			"arrowz_box": box_name,
			"reason": reason,
		}).insert(ignore_permissions=True)

	# Push to engine
	from arrowz.arrowz_api.utils.box_connector import BoxConnector

	connector = BoxConnector(box_name=box_name)
	result = connector.block_client(mac)

	frappe.db.commit()
	return {"status": "success", "message": _("Client blocked"), "engine_result": result}


@frappe.whitelist(methods=["POST"])
def unblock_client(mac_address: str, box_name: str = None):
	"""Unblock a network client by MAC address.

	Args:
		mac_address: Client MAC address
		box_name: Arrowz Box name
	"""
	frappe.only_for(["AZ User", "AZ Manager", "System Manager"])


	mac = mac_address.upper().replace("-", ":")

	if not box_name and frappe.db.exists("Network Client", mac):
		box_name = frappe.db.get_value("Network Client", mac, "arrowz_box")

	if not box_name:
		frappe.throw(_("Cannot determine box for client {0}").format(mac))

	# Update client record
	if frappe.db.exists("Network Client", mac):
		frappe.db.set_value("Network Client", mac, {
			"is_blocked": 0,
			"status": "Offline",
		})

	# Remove from blacklist
	from frappe.query_builder import DocType

	MBL = DocType("MAC Blacklist")
	frappe.qb.from_(MBL).delete().where(
		(MBL.mac_address == mac) & (MBL.arrowz_box == box_name)
	).run()

	# Push to engine
	from arrowz.arrowz_api.utils.box_connector import BoxConnector

	connector = BoxConnector(box_name=box_name)
	result = connector.unblock_client(mac)

	frappe.db.commit()
	return {"status": "success", "message": _("Client unblocked"), "engine_result": result}


@frappe.whitelist(methods=["POST"])
def disconnect_client(mac_address: str, box_name: str = None):
	"""Force disconnect a network client.

	Args:
		mac_address: Client MAC address
		box_name: Arrowz Box name
	"""
	frappe.only_for(["AZ User", "AZ Manager", "System Manager"])


	mac = mac_address.upper().replace("-", ":")

	if not box_name and frappe.db.exists("Network Client", mac):
		box_name = frappe.db.get_value("Network Client", mac, "arrowz_box")

	if not box_name:
		frappe.throw(_("Cannot determine box for client {0}").format(mac))

	from arrowz.arrowz_api.utils.box_connector import BoxConnector

	connector = BoxConnector(box_name=box_name)
	result = connector.disconnect_client(mac)

	# Update status
	if frappe.db.exists("Network Client", mac):
		frappe.db.set_value("Network Client", mac, "status", "Offline")

	frappe.db.commit()
	return {"status": "success", "message": _("Client disconnected"), "engine_result": result}


@frappe.whitelist(methods=["POST"])
def assign_bandwidth_plan(mac_address: str, plan_name: str, box_name: str = None):
	"""Assign a bandwidth plan to a client.

	Args:
		mac_address: Client MAC address
		plan_name: Bandwidth Plan name
		box_name: Arrowz Box name
	"""
	frappe.only_for(["AZ Manager", "System Manager"])


	mac = mac_address.upper().replace("-", ":")

	if not box_name and frappe.db.exists("Network Client", mac):
		box_name = frappe.db.get_value("Network Client", mac, "arrowz_box")

	if not box_name:
		frappe.throw(_("Cannot determine box for client {0}").format(mac))

	# Update client's bandwidth plan
	if frappe.db.exists("Network Client", mac):
		frappe.db.set_value("Network Client", mac, "bandwidth_plan", plan_name)

	# Create or update bandwidth assignment
	from frappe.query_builder import DocType

	BA = DocType("Bandwidth Assignment")
	existing = (
		frappe.qb.from_(BA)
		.select(BA.name)
		.where(BA.network_client == mac)
		.where(BA.arrowz_box == box_name)
		.where(BA.enabled == 1)
		.run(as_dict=True)
	)

	if existing:
		frappe.db.set_value("Bandwidth Assignment", existing[0].name, "bandwidth_plan", plan_name)
	else:
		frappe.get_doc({
			"doctype": "Bandwidth Assignment",
			"arrowz_box": box_name,
			"target_type": "Client",
			"network_client": mac,
			"bandwidth_plan": plan_name,
			"enabled": 1,
		}).insert(ignore_permissions=True)

	frappe.db.commit()
	return {"status": "success", "message": _("Bandwidth plan assigned")}


@frappe.whitelist()
def get_client_details(mac_address: str):
	"""Get detailed information about a network client.

	Args:
		mac_address: Client MAC address

	Returns:
		Client details with sessions, usage, and assignments
	"""
	frappe.only_for(["AZ User", "AZ Manager", "System Manager"])


	mac = mac_address.upper().replace("-", ":")

	if not frappe.db.exists("Network Client", mac):
		frappe.throw(_("Client not found: {0}").format(mac))

	client = frappe.get_doc("Network Client", mac)

	# Get recent sessions
	from frappe.query_builder import DocType

	CS = DocType("Client Session")
	sessions = (
		frappe.qb.from_(CS)
		.select(CS.star)
		.where(CS.network_client == mac)
		.orderby(CS.creation, order=frappe.qb.desc)
		.limit(10)
		.run(as_dict=True)
	)

	# Get bandwidth assignment
	BA = DocType("Bandwidth Assignment")
	assignments = (
		frappe.qb.from_(BA)
		.select(BA.star)
		.where(BA.network_client == mac)
		.where(BA.enabled == 1)
		.run(as_dict=True)
	)

	return {
		"client": client.as_dict(),
		"sessions": sessions,
		"bandwidth_assignments": assignments,
	}
