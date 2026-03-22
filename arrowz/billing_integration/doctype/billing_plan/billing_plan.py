# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BillingPlan(Document):
	def validate(self):
		self._validate_pricing_method()

	def _validate_pricing_method(self):
		"""Ensure at least one pricing method is configured."""
		if self.billing_type == "Flat" and not self.flat_rate:
			frappe.throw("Flat Rate is required for Flat billing type.")

		if self.billing_type == "Tiered" and not self.tiers:
			frappe.throw("At least one tier is required for Tiered billing type.")

		if self.billing_type == "Usage Based" and not self.usage_quota:
			frappe.throw("Usage Quota is required for Usage Based billing type.")

		if self.billing_type == "Hybrid":
			if not self.flat_rate:
				frappe.throw("Flat Rate is required for Hybrid billing type.")
			if not self.usage_quota and not self.tiers:
				frappe.throw(
					"Either Usage Quota or Tiers must be set for Hybrid billing type."
				)
