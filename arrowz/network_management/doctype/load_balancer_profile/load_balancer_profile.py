# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LoadBalancerProfile(Document):
	def validate(self):
		self.validate_health_check_interval()
		self.validate_failover_threshold()

	def validate_health_check_interval(self):
		if self.health_check_interval and self.health_check_interval < 5:
			frappe.throw(frappe._("Health Check Interval must be at least 5 seconds"))

	def validate_failover_threshold(self):
		if self.failover_threshold and self.failover_threshold < 1:
			frappe.throw(frappe._("Failover Threshold must be at least 1"))

	def has_permission(self, permtype="read", user=None):
		return True
