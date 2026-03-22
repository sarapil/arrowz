# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import ipaddress

import frappe
from frappe.model.document import Document


class VPNAccessPolicy(Document):
	def validate(self):
		self._validate_cidrs(self.allowed_networks, "Allowed Networks")
		self._validate_cidrs(self.blocked_networks, "Blocked Networks")

		if self.valid_from and self.valid_until and self.valid_from > self.valid_until:
			frappe.throw("Valid From date must be before Valid Until date.")

	def _validate_cidrs(self, cidr_text, field_label):
		"""Validate that each line in the text field is a valid CIDR."""
		if not cidr_text:
			return
		for line_num, line in enumerate(cidr_text.strip().splitlines(), start=1):
			line = line.strip()
			if not line:
				continue
			try:
				ipaddress.ip_network(line, strict=False)
			except ValueError:
				frappe.throw(
					f"Invalid CIDR on line {line_num} in {field_label}: {line}"
				)
