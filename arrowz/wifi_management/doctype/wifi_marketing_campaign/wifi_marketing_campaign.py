# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WiFiMarketingCampaign(Document):
	def validate(self):
		self.validate_dates()

	def validate_dates(self):
		"""Validate that end date is after start date."""
		if self.start_date and self.end_date:
			if self.end_date < self.start_date:
				frappe.throw(frappe._("End Date must be after Start Date"))
