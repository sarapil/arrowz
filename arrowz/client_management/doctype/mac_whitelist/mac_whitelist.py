# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


MAC_REGEX = re.compile(r"^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$")


class MACWhitelist(Document):
	def validate(self):
		self.validate_mac_address()
		self.normalize_mac_address()

	def before_insert(self):
		self.added_by = frappe.session.user

	def validate_mac_address(self):
		if not self.mac_address or not MAC_REGEX.match(self.mac_address):
			frappe.throw(
				frappe._("Invalid MAC Address format: {0}. Expected format: AA:BB:CC:DD:EE:FF").format(
					self.mac_address
				)
			)

	def normalize_mac_address(self):
		"""Auto-format MAC address to uppercase colon-separated format."""
		self.mac_address = self.mac_address.replace("-", ":").upper()
