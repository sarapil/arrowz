# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
ConfigCompiler - Compiles Frappe DocType data into configuration
dictionaries that the Arrowz Engine understands.

Each compile method reads relevant doctypes for a specific box
and produces a structured config dict ready to push via BoxConnector.
"""

import frappe
from frappe.query_builder import DocType


class ConfigCompiler:
	"""Compiles configuration from Frappe doctypes for an Arrowz Box."""

	def __init__(self, box_name: str):
		"""Initialize compiler for a specific Arrowz Box.

		Args:
			box_name: Name of the Arrowz Box document
		"""
		self.box_name = box_name
		self.box = frappe.get_doc("Arrowz Box", box_name)

	def compile_full(self) -> dict:
		"""Compile complete configuration for the box.

		Returns:
			Complete config dict with all sections
		"""
		return {
			"box": self.box_name,
			"version": self.box.engine_version or "1.0",
			"network": self.compile_network(),
			"firewall": self.compile_firewall(),
			"clients": self.compile_clients(),
			"bandwidth": self.compile_bandwidth(),
			"wifi": self.compile_wifi(),
			"vpn": self.compile_vpn(),
			"dns": self.compile_dns(),
		}

	def compile_network(self) -> dict:
		"""Compile network configuration (WAN, LAN, interfaces, routes).

		Returns:
			Network config dict
		"""
		NI = DocType("Network Interface")
		interfaces = (
			frappe.qb.from_(NI)
			.select(NI.star)
			.where(NI.arrowz_box == self.box_name)
			.run(as_dict=True)
		)

		WAN = DocType("WAN Connection")
		wan_connections = (
			frappe.qb.from_(WAN)
			.select(WAN.star)
			.where(WAN.arrowz_box == self.box_name)
			.where(WAN.enabled == 1)
			.orderby(WAN.priority)
			.run(as_dict=True)
		)

		LAN = DocType("LAN Network")
		lan_networks = (
			frappe.qb.from_(LAN)
			.select(LAN.star)
			.where(LAN.arrowz_box == self.box_name)
			.where(LAN.enabled == 1)
			.run(as_dict=True)
		)

		SR = DocType("Static Route")
		static_routes = (
			frappe.qb.from_(SR)
			.select(SR.star)
			.where(SR.arrowz_box == self.box_name)
			.where(SR.enabled == 1)
			.orderby(SR.metric)
			.run(as_dict=True)
		)

		LB = DocType("Load Balancer Profile")
		load_balancer = (
			frappe.qb.from_(LB)
			.select(LB.star)
			.where(LB.arrowz_box == self.box_name)
			.where(LB.enabled == 1)
			.run(as_dict=True)
		)

		return {
			"interfaces": [_serialize(i) for i in interfaces],
			"wan_connections": [_serialize(w) for w in wan_connections],
			"lan_networks": [_serialize_lan(ln) for ln in lan_networks],
			"static_routes": [_serialize(r) for r in static_routes],
			"load_balancer_profiles": [_serialize(lb) for lb in load_balancer],
		}

	def compile_firewall(self) -> dict:
		"""Compile firewall configuration (zones, rules, NAT, port forwards).

		Returns:
			Firewall config dict for nftables
		"""
		FZ = DocType("Firewall Zone")
		zones = (
			frappe.qb.from_(FZ)
			.select(FZ.star)
			.where(FZ.arrowz_box == self.box_name)
			.run(as_dict=True)
		)

		FRS = DocType("Firewall Rule Set")
		rule_sets = (
			frappe.qb.from_(FRS)
			.select(FRS.star)
			.where(FRS.arrowz_box == self.box_name)
			.where(FRS.enabled == 1)
			.orderby(FRS.priority)
			.run(as_dict=True)
		)

		FR = DocType("Firewall Rule")
		rules = (
			frappe.qb.from_(FR)
			.select(FR.star)
			.where(FR.arrowz_box == self.box_name)
			.where(FR.enabled == 1)
			.orderby(FR.rule_number)
			.run(as_dict=True)
		)

		NR = DocType("NAT Rule")
		nat_rules = (
			frappe.qb.from_(NR)
			.select(NR.star)
			.where(NR.arrowz_box == self.box_name)
			.where(NR.enabled == 1)
			.orderby(NR.priority)
			.run(as_dict=True)
		)

		PF = DocType("Port Forward")
		port_forwards = (
			frappe.qb.from_(PF)
			.select(PF.star)
			.where(PF.arrowz_box == self.box_name)
			.where(PF.enabled == 1)
			.run(as_dict=True)
		)

		return {
			"zones": [_serialize(z) for z in zones],
			"rule_sets": [_serialize(rs) for rs in rule_sets],
			"rules": [_serialize(r) for r in rules],
			"nat_rules": [_serialize(nr) for nr in nat_rules],
			"port_forwards": [_serialize(pf) for pf in port_forwards],
		}

	def compile_clients(self) -> dict:
		"""Compile client management configuration.

		Returns:
			Client config dict (reservations, blocks, groups)
		"""
		IR = DocType("IP Reservation")
		reservations = (
			frappe.qb.from_(IR)
			.select(IR.star)
			.where(IR.arrowz_box == self.box_name)
			.where(IR.enabled == 1)
			.run(as_dict=True)
		)

		MB = DocType("MAC Blacklist")
		blacklist = (
			frappe.qb.from_(MB)
			.select(MB.mac_address)
			.where(MB.arrowz_box == self.box_name)
			.where(MB.enabled == 1)
			.run(as_dict=True)
		)

		MW = DocType("MAC Whitelist")
		whitelist = (
			frappe.qb.from_(MW)
			.select(MW.mac_address)
			.where(MW.arrowz_box == self.box_name)
			.where(MW.enabled == 1)
			.run(as_dict=True)
		)

		NC = DocType("Network Client")
		blocked_clients = (
			frappe.qb.from_(NC)
			.select(NC.mac_address)
			.where(NC.arrowz_box == self.box_name)
			.where(NC.is_blocked == 1)
			.run(as_dict=True)
		)

		return {
			"ip_reservations": [_serialize(r) for r in reservations],
			"mac_blacklist": [entry.mac_address for entry in blacklist],
			"mac_whitelist": [entry.mac_address for entry in whitelist],
			"blocked_clients": [entry.mac_address for entry in blocked_clients],
		}

	def compile_bandwidth(self) -> dict:
		"""Compile bandwidth/QoS configuration.

		Returns:
			Bandwidth config dict for tc (traffic control)
		"""
		BA = DocType("Bandwidth Assignment")
		assignments = (
			frappe.qb.from_(BA)
			.select(BA.star)
			.where(BA.arrowz_box == self.box_name)
			.where(BA.enabled == 1)
			.orderby(BA.priority)
			.run(as_dict=True)
		)

		# Enrich with plan details
		enriched = []
		for a in assignments:
			entry = _serialize(a)
			if a.bandwidth_plan:
				plan = frappe.get_cached_doc("Bandwidth Plan", a.bandwidth_plan)
				entry["plan"] = {
					"download_kbps": a.get("override_download_kbps") or plan.download_kbps,
					"upload_kbps": a.get("override_upload_kbps") or plan.upload_kbps,
					"burst_download_kbps": plan.burst_download_kbps,
					"burst_upload_kbps": plan.burst_upload_kbps,
					"burst_duration_seconds": plan.burst_duration_seconds,
				}
				if plan.qos_policy:
					qos = frappe.get_cached_doc("QoS Policy", plan.qos_policy)
					entry["qos_classes"] = [
						{
							"class_name": c.class_name,
							"priority": c.priority,
							"rate_kbps": c.rate_kbps,
							"ceil_kbps": c.ceil_kbps,
							"match_protocol": c.match_protocol,
							"match_dscp": c.match_dscp,
							"match_ports": c.match_ports,
							"quantum": c.quantum,
						}
						for c in qos.classes
					]
			enriched.append(entry)

		# Traffic rules
		TR = DocType("Traffic Rule")
		traffic_rules = (
			frappe.qb.from_(TR)
			.select(TR.star)
			.where(TR.arrowz_box == self.box_name)
			.where(TR.enabled == 1)
			.orderby(TR.priority)
			.run(as_dict=True)
		)

		return {
			"assignments": enriched,
			"traffic_rules": [_serialize(r) for r in traffic_rules],
		}

	def compile_wifi(self) -> dict:
		"""Compile WiFi configuration.

		Returns:
			WiFi config dict for hostapd
		"""
		WN = DocType("WiFi Network")
		networks = (
			frappe.qb.from_(WN)
			.select(WN.star)
			.where(WN.arrowz_box == self.box_name)
			.where(WN.enabled == 1)
			.run(as_dict=True)
		)

		enriched = []
		for net in networks:
			entry = _serialize(net)
			# Get password as cleartext for hostapd config
			if net.get("password"):
				try:
					doc = frappe.get_doc("WiFi Network", net.name)
					entry["password"] = doc.get_password("password")
				except Exception:
					pass

			# Hotspot profile details
			if net.get("hotspot_profile"):
				profile = frappe.get_cached_doc("WiFi Hotspot Profile", net.hotspot_profile)
				entry["hotspot"] = {
					"session_timeout": profile.session_timeout,
					"idle_timeout": profile.idle_timeout,
					"bandwidth_plan": profile.bandwidth_plan,
					"auth_methods": [
						{"method": m.method, "priority": m.priority}
						for m in profile.auth_methods
						if m.enabled
					],
					"walled_garden": [
						{"type": w.entry_type, "value": w.value}
						for w in profile.walled_garden
					],
				}
				if profile.splash_page:
					splash = frappe.get_cached_doc("WiFi Splash Page", profile.splash_page)
					entry["hotspot"]["splash"] = {
						"template": splash.template,
						"title": splash.title,
						"welcome_message": splash.welcome_message,
						"primary_color": splash.primary_color,
						"logo_url": splash.logo_url,
					}
			enriched.append(entry)

		# Captive portals
		CP = DocType("Captive Portal")
		portals = (
			frappe.qb.from_(CP)
			.select(CP.star)
			.where(CP.arrowz_box == self.box_name)
			.where(CP.enabled == 1)
			.run(as_dict=True)
		)

		return {
			"networks": enriched,
			"captive_portals": [_serialize(p) for p in portals],
		}

	def compile_vpn(self) -> dict:
		"""Compile VPN configuration.

		Returns:
			VPN config dict for WireGuard/OpenVPN
		"""
		VS = DocType("VPN Server")
		servers = (
			frappe.qb.from_(VS)
			.select(VS.star)
			.where(VS.arrowz_box == self.box_name)
			.where(VS.enabled == 1)
			.run(as_dict=True)
		)

		enriched = []
		for server in servers:
			entry = _serialize(server)
			# Get peers
			VP = DocType("VPN Peer")
			peers = (
				frappe.qb.from_(VP)
				.select(VP.star)
				.where(VP.vpn_server == server.name)
				.where(VP.enabled == 1)
				.run(as_dict=True)
			)
			entry["peers"] = [_serialize(p) for p in peers]
			enriched.append(entry)

		# Site-to-site tunnels
		ST = DocType("Site to Site Tunnel")
		tunnels = (
			frappe.qb.from_(ST)
			.select(ST.star)
			.where(ST.arrowz_box == self.box_name)
			.where(ST.enabled == 1)
			.run(as_dict=True)
		)

		return {
			"servers": enriched,
			"tunnels": [_serialize(t) for t in tunnels],
		}

	def compile_dns(self) -> dict:
		"""Compile DNS configuration.

		Returns:
			DNS config dict for dnsmasq
		"""
		DE = DocType("DNS Entry")
		entries = (
			frappe.qb.from_(DE)
			.select(DE.star)
			.where(DE.arrowz_box == self.box_name)
			.where(DE.enabled == 1)
			.run(as_dict=True)
		)

		return {
			"entries": [_serialize(e) for e in entries],
		}


def _serialize(doc: dict) -> dict:
	"""Serialize a document dict, removing internal Frappe fields.

	Args:
		doc: Document dict from query

	Returns:
		Cleaned dict suitable for Engine API
	"""
	exclude_fields = {
		"owner", "creation", "modified", "modified_by",
		"docstatus", "idx", "doctype", "_user_tags",
		"_comments", "_assign", "_liked_by",
	}
	return {
		k: v for k, v in doc.items()
		if k not in exclude_fields and not k.startswith("_")
	}


def _serialize_lan(doc: dict) -> dict:
	"""Serialize LAN network with DHCP details."""
	result = _serialize(doc)
	if doc.get("enable_dhcp"):
		result["dhcp"] = {
			"enabled": True,
			"start": doc.get("dhcp_start"),
			"end": doc.get("dhcp_end"),
			"lease_time": doc.get("dhcp_lease_time"),
			"domain": doc.get("domain_name"),
			"dns_primary": doc.get("dns_primary"),
			"dns_secondary": doc.get("dns_secondary"),
		}
	return result
