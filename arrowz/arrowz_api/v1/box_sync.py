# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
Box Sync API - Endpoints for syncing Arrowz Box data.

Called by scheduled tasks or manually from the UI to sync
box telemetry, clients, and configuration state.
"""

import frappe
from frappe import _


@frappe.whitelist(methods=["POST"])
def sync_box(box_name: str):
	"""Sync telemetry and status from an Arrowz Box.

	Args:
		box_name: Name of the Arrowz Box document
	"""
	frappe.only_for(["AZ Manager", "System Manager"])


	box = frappe.get_doc("Arrowz Box", box_name)
	return box.sync_telemetry()


@frappe.whitelist(methods=["POST"])
def sync_all_boxes():
	"""Sync telemetry from all active Arrowz Boxes."""
	frappe.only_for(["AZ Manager", "System Manager"])


	from frappe.query_builder import DocType

	AB = DocType("Arrowz Box")
	boxes = (
		frappe.qb.from_(AB)
		.select(AB.name)
		.where(AB.status != "Maintenance")
		.run(as_dict=True)
	)

	results = []
	for box_row in boxes:
		try:
			box = frappe.get_doc("Arrowz Box", box_row.name)
			result = box.sync_telemetry()
			results.append({"box": box_row.name, **result})
		except Exception as e:
			results.append({"box": box_row.name, "status": "error", "message": str(e)})
			frappe.log_error(f"Sync failed for box {box_row.name}: {e}", "Box Sync Error")

	return {"status": "success", "results": results}


@frappe.whitelist(methods=["POST"])
def push_config(box_name: str, config_type: str = "full"):
	"""Push configuration to an Arrowz Box.

	Args:
		box_name: Name of the Arrowz Box
		config_type: Type of config to push (full/network/firewall/wifi/bandwidth/clients/vpn/dns)
	"""
	frappe.only_for(["AZ Manager", "System Manager"])


	box = frappe.get_doc("Arrowz Box", box_name)

	if config_type == "full":
		return box.push_full_config()

	from arrowz.arrowz_api.utils.box_connector import BoxConnector
	from arrowz.arrowz_api.utils.config_compiler import ConfigCompiler

	compiler = ConfigCompiler(box_name)
	connector = BoxConnector(box)

	compile_methods = {
		"network": (compiler.compile_network, connector.push_network_config),
		"firewall": (compiler.compile_firewall, connector.push_firewall_config),
		"wifi": (compiler.compile_wifi, connector.push_wifi_config),
		"bandwidth": (compiler.compile_bandwidth, connector.push_bandwidth_config),
		"clients": (compiler.compile_clients, connector.push_client_config),
		"vpn": (compiler.compile_vpn, connector.push_vpn_config),
		"dns": (compiler.compile_dns, connector.push_dns_config),
	}

	if config_type not in compile_methods:
		frappe.throw(_("Invalid config type: {0}").format(config_type))

	compile_fn, push_fn = compile_methods[config_type]
	config = compile_fn()
	return push_fn(config)
