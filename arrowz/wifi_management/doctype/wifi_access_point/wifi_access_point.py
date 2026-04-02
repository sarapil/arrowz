# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


class WiFiAccessPoint(Document):
	def validate(self):
		self.validate_mac_address()
		self.validate_interface_name()

	def validate_mac_address(self):
		"""Validate MAC address format if provided."""
		if self.mac_address:
			mac_pattern = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
			if not mac_pattern.match(self.mac_address):
				frappe.throw(
					frappe._("Invalid MAC address format. Expected format: XX:XX:XX:XX:XX:XX")
				)

	def validate_interface_name(self):
		"""Validate interface name is not empty."""
		if self.interface_name and not self.interface_name.strip():
			frappe.throw(frappe._("Interface Name cannot be empty"))

	@frappe.whitelist(methods=["POST"])
	def refresh_status(self):
		"""Refresh the access point status from the Arrowz Box."""
		frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

		frappe.msgprint(frappe._("Status refresh requested for {0}").format(self.ap_name))
		return {"status": self.status, "connected_clients": self.connected_clients}
