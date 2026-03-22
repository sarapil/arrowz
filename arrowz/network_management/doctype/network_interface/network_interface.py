# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


class NetworkInterface(Document):
	def validate(self):
		self.validate_mac_address()

	def validate_mac_address(self):
		if self.mac_address:
			mac_pattern = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
			if not mac_pattern.match(self.mac_address):
				frappe.throw(
					frappe._("Invalid MAC address format. Expected format: XX:XX:XX:XX:XX:XX")
				)

	def has_permission(self, permtype="read", user=None):
		return True

	@frappe.whitelist(methods=["POST"])
	def refresh_status(self):
		"""Refresh the interface status from the Arrowz Box."""
		# Placeholder for actual status refresh logic via API/SSH
		frappe.msgprint(frappe._("Status refresh requested for {0}").format(self.interface_name))
		return {"status": self.status}
