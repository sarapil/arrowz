# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WiFiHotspotProfile(Document):
	def validate(self):
		self.validate_auth_methods()
		self.validate_timeouts()

	def validate_auth_methods(self):
		"""Ensure at least one authentication method is configured."""
		if not self.auth_methods or len(self.auth_methods) == 0:
			frappe.throw(frappe._("At least one authentication method is required"))

		enabled_methods = [m for m in self.auth_methods if m.enabled]
		if not enabled_methods:
			frappe.throw(frappe._("At least one authentication method must be enabled"))

	def validate_timeouts(self):
		"""Validate timeout values are positive."""
		if self.session_timeout and self.session_timeout < 0:
			frappe.throw(frappe._("Session Timeout must be a positive number"))
		if self.idle_timeout and self.idle_timeout < 0:
			frappe.throw(frappe._("Idle Timeout must be a positive number"))
