# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
Network Events - Doc event handlers for network management doctypes.

These functions are triggered by doc_events in hooks.py when network-related
DocTypes are saved, updated, or deleted. They compile and push configuration
changes to the appropriate Arrowz Box Engine.
"""

import frappe
from frappe import _


def on_config_change(doc, method):
	"""Push network config when WAN/LAN/Route/DNS changes.

	Handles: WAN Connection, LAN Network, Static Route, DNS Entry
	"""
	box_name = doc.get("arrowz_box")
	if not box_name:
		return

	_enqueue_config_push(box_name, "network")


def on_firewall_change(doc, method):
	"""Push firewall config when rules change.

	Handles: Firewall Rule, NAT Rule, Port Forward
	"""
	box_name = doc.get("arrowz_box")
	if not box_name:
		return

	_enqueue_config_push(box_name, "firewall")


def on_client_change(doc, method):
	"""Push client config when client settings change.

	Handles: Network Client, MAC Blacklist, IP Reservation
	"""
	box_name = doc.get("arrowz_box")
	if not box_name:
		return

	_enqueue_config_push(box_name, "clients")


def on_bandwidth_change(doc, method):
	"""Push bandwidth config when assignments change.

	Handles: Bandwidth Assignment
	"""
	box_name = doc.get("arrowz_box")
	if not box_name:
		return

	_enqueue_config_push(box_name, "bandwidth")


def on_wifi_change(doc, method):
	"""Push WiFi config when network settings change.

	Handles: WiFi Network
	"""
	box_name = doc.get("arrowz_box")
	if not box_name:
		return

	_enqueue_config_push(box_name, "wifi")


def on_vpn_change(doc, method):
	"""Push VPN config when peers or tunnels change.

	Handles: VPN Peer, Site to Site Tunnel
	"""
	# VPN Peer links via vpn_server, not directly to box
	box_name = doc.get("arrowz_box")
	if not box_name and doc.get("vpn_server"):
		box_name = frappe.db.get_value("VPN Server", doc.vpn_server, "arrowz_box")

	if not box_name:
		return

	_enqueue_config_push(box_name, "vpn")


def on_vpn_server_change(doc, method):
	"""Push VPN config when server settings change.

	Handles: VPN Server
	"""
	box_name = doc.get("arrowz_box")
	if not box_name:
		return

	_enqueue_config_push(box_name, "vpn")


def on_vpn_policy_change(doc, method):
	"""Push VPN config when access policies change.

	When a policy changes, we need to re-push VPN config for the
	linked server's box so peers are re-evaluated.

	Handles: VPN Access Policy
	"""
	vpn_server = doc.get("vpn_server")
	if not vpn_server:
		return

	box_name = frappe.db.get_value("VPN Server", vpn_server, "arrowz_box")
	if not box_name:
		return

	_enqueue_config_push(box_name, "vpn")


def _enqueue_config_push(box_name: str, config_type: str):
	"""Enqueue a config push as a background job to avoid blocking saves.

	Uses a short queue with deduplication key to avoid flooding.

	Args:
		box_name: Arrowz Box name
		config_type: Config section to push (network/firewall/clients/bandwidth/wifi/vpn/dns)
	"""
	# Check if box exists and is not in maintenance
	status = frappe.db.get_value("Arrowz Box", box_name, "status")
	if status == "Maintenance":
		return

	frappe.enqueue(
		"arrowz.events.network._push_config",
		queue="short",
		box_name=box_name,
		config_type=config_type,
		deduplicate=True,
		job_id=f"config_push_{box_name}_{config_type}",
	)


def _push_config(box_name: str, config_type: str):
	"""Actually push config to the box (runs in background).

	Args:
		box_name: Arrowz Box name
		config_type: Config section type
	"""
	try:
		from arrowz.arrowz_api.utils.box_connector import BoxConnector
		from arrowz.arrowz_api.utils.config_compiler import ConfigCompiler

		compiler = ConfigCompiler(box_name)
		connector = BoxConnector(box_name=box_name)

		compile_methods = {
			"network": (compiler.compile_network, connector.push_network_config),
			"firewall": (compiler.compile_firewall, connector.push_firewall_config),
			"clients": (compiler.compile_clients, connector.push_client_config),
			"bandwidth": (compiler.compile_bandwidth, connector.push_bandwidth_config),
			"wifi": (compiler.compile_wifi, connector.push_wifi_config),
			"vpn": (compiler.compile_vpn, connector.push_vpn_config),
			"dns": (compiler.compile_dns, connector.push_dns_config),
		}

		if config_type not in compile_methods:
			frappe.log_error(f"Unknown config type: {config_type}", "Config Push Error")
			return

		compile_fn, push_fn = compile_methods[config_type]
		config = compile_fn()
		result = push_fn(config)

		# Log success
		frappe.get_doc({
			"doctype": "Arrowz Box Health Log",
			"arrowz_box": box_name,
			"log_type": "Config Push",
			"status": "Online",
			"message": f"Pushed {config_type} config successfully",
			"details": frappe.as_json(result),
		}).insert(ignore_permissions=True)

	except Exception as e:
		frappe.log_error(
			f"Config push failed for {box_name} ({config_type}): {e}",
			"Config Push Error",
		)
		# Log failure
		try:
			frappe.get_doc({
				"doctype": "Arrowz Box Health Log",
				"arrowz_box": box_name,
				"log_type": "Config Error",
				"status": "Error",
				"severity": "Error",
				"message": f"Failed to push {config_type} config: {str(e)}",
			}).insert(ignore_permissions=True)
		except Exception:
			pass
