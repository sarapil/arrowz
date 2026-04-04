# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$")


class NetworkClient(Document):
	def validate(self):
		self.validate_mac_address()
		self.normalize_mac_address()

	def validate_mac_address(self):
		if not self.mac_address:
			frappe.throw(frappe._("MAC Address is required"))
		if not MAC_REGEX.match(self.mac_address):
			frappe.throw(
				frappe._("Invalid MAC Address format: {0}. Expected format: AA:BB:CC:DD:EE:FF").format(
					self.mac_address
				)
			)

	def normalize_mac_address(self):
		"""Auto-format MAC address to uppercase colon-separated format."""
		raw = self.mac_address.replace("-", ":").upper()
		self.mac_address = raw

	@frappe.whitelist(methods=["POST"])
	def block_client(self):
		"""Block this client from the network."""
		frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

		self.is_blocked = 1
		self.status = "Blocked"
		self.save()
		frappe.logger().info(f"Client {self.mac_address} blocked")

	@frappe.whitelist(methods=["POST"])
	def unblock_client(self):
		"""Unblock this client."""
		frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

		self.is_blocked = 0
		self.status = "Offline"
		self.save()
		frappe.logger().info(f"Client {self.mac_address} unblocked")

	@frappe.whitelist(methods=["POST"])
	def disconnect_client(self):
		"""Disconnect this client from the network."""
		frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

		self.status = "Offline"
		self.save()
		frappe.logger().info(f"Client {self.mac_address} disconnected")
