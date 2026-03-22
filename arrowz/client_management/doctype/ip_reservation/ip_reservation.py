# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import ipaddress
import re

import frappe
from frappe.model.document import Document


MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$")


class IPReservation(Document):
	def validate(self):
		self.validate_mac_format()
		self.normalize_mac_address()
		self.validate_ip_in_network()

	def validate_mac_format(self):
		if not self.mac_address or not MAC_REGEX.match(self.mac_address):
			frappe.throw(
				frappe._("Invalid MAC Address format: {0}. Expected format: AA:BB:CC:DD:EE:FF").format(
					self.mac_address
				)
			)

	def normalize_mac_address(self):
		"""Auto-format MAC address to uppercase colon-separated format."""
		self.mac_address = self.mac_address.replace("-", ":").upper()

	def validate_ip_in_network(self):
		"""Validate that the IP address falls within the LAN network range."""
		if not self.ip_address or not self.lan_network:
			return

		lan = frappe.get_doc("LAN Network", self.lan_network)
		subnet = getattr(lan, "subnet", None) or getattr(lan, "network_address", None)
		if not subnet:
			return

		try:
			network = ipaddress.ip_network(subnet, strict=False)
			ip = ipaddress.ip_address(self.ip_address)
			if ip not in network:
				frappe.throw(
					frappe._("IP Address {0} is not within the LAN network range {1}").format(
						self.ip_address, subnet
					)
				)
		except ValueError as e:
			frappe.throw(frappe._("Invalid IP or network address: {0}").format(str(e)))

	def on_update(self):
		self.push_dhcp_config()

	def push_dhcp_config(self):
		"""Push DHCP static reservation to the Arrowz Box."""
		frappe.logger().info(
			f"DHCP config push requested for reservation {self.mac_address} -> {self.ip_address}"
		)
