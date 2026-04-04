# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FirewallRuleSet(Document):
	def validate(self):
		self.validate_rule_set_name()
		self.validate_priority()

	def validate_rule_set_name(self):
		if self.rule_set_name and not self.rule_set_name.replace("_", "").replace("-", "").replace(" ", "").isalnum():
			frappe.throw(
				frappe._("Rule Set Name must contain only alphanumeric characters, hyphens, underscores, or spaces.")
			)

	def validate_priority(self):
		if self.priority is not None and self.priority < 0:
			frappe.throw(frappe._("Priority must be a non-negative integer."))
