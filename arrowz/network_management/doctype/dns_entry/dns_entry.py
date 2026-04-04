# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


class DNSEntry(Document):
	def validate(self):
		self.validate_hostname()

	def validate_hostname(self):
		if self.hostname:
			# Allow valid hostnames: alphanumeric, hyphens, dots, and wildcards
			hostname_pattern = re.compile(
				r"^(\*\.)?([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*"
				r"[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$"
			)
			if not hostname_pattern.match(self.hostname):
				frappe.throw(
					frappe._("Invalid hostname format: {0}").format(self.hostname)
				)

	def has_permission(self, permtype="read", user=None):
		return True
