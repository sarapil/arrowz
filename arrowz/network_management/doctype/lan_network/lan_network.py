# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


class LANNetwork(Document):
	def validate(self):
		self.validate_ip_address()
		self.validate_subnet_mask()
		self.validate_dhcp_range()

	def validate_ip_address(self):
		if self.ip_address:
			ip_pattern = re.compile(
				r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$"
			)
			if not ip_pattern.match(self.ip_address):
				frappe.throw(frappe._("Invalid IP Address format for Gateway IP"))

	def validate_subnet_mask(self):
		if self.subnet_mask:
			ip_pattern = re.compile(
				r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$"
			)
			if not ip_pattern.match(self.subnet_mask):
				frappe.throw(frappe._("Invalid Subnet Mask format"))

	def validate_dhcp_range(self):
		if self.enable_dhcp:
			if not self.dhcp_start or not self.dhcp_end:
				frappe.throw(
					frappe._("DHCP Start and End addresses are required when DHCP is enabled")
				)

	def on_update(self):
		self.push_config()

	def push_config(self):
		"""Push LAN configuration to the Arrowz Box."""
		# Placeholder for actual config push logic
		frappe.logger().info(f"LAN config push requested for {self.network_name}")

	def has_permission(self, permtype="read", user=None):
		return True
