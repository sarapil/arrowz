# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


class WiFiUserAccount(Document):
	def validate(self):
		self.validate_email()
		self.validate_mac_addresses()
		self.validate_max_devices()

	def validate_email(self):
		"""Validate email format if provided."""
		if self.email:
			email_pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
			if not email_pattern.match(self.email):
				frappe.throw(frappe._("Invalid email format"))

	def validate_mac_addresses(self):
		"""Validate MAC address format for each entry."""
		if self.mac_addresses:
			mac_pattern = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
			for line in self.mac_addresses.strip().split("\n"):
				mac = line.strip()
				if mac and not mac_pattern.match(mac):
					frappe.throw(
						frappe._("Invalid MAC address format: {0}. Expected: XX:XX:XX:XX:XX:XX").format(mac)
					)

	def validate_max_devices(self):
		"""Ensure max devices is a positive number."""
		if self.max_devices is not None and self.max_devices < 0:
			frappe.throw(frappe._("Max Devices must be 0 or a positive number"))
