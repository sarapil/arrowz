# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


class StaticRoute(Document):
	def validate(self):
		self.validate_cidr()

	def validate_cidr(self):
		if self.destination:
			cidr_pattern = re.compile(
				r"^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)"
				r"/(3[0-2]|[12]?\d)$"
			)
			if not cidr_pattern.match(self.destination):
				frappe.throw(
					frappe._("Invalid CIDR format for Destination. Expected format: x.x.x.x/y")
				)

	def on_update(self):
		self.push_config()

	def push_config(self):
		"""Push static route configuration to the Arrowz Box."""
		# Placeholder for actual config push logic
		frappe.logger().info(f"Static route config push requested for {self.name}")

	def has_permission(self, permtype="read", user=None):
		return True
