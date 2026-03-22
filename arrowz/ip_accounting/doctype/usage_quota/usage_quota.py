# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UsageQuota(Document):
	def validate(self):
		self.validate_limits()

	def validate_limits(self):
		"""Validate that limits are greater than 0 when set."""
		for field in ("download_limit_mb", "upload_limit_mb", "total_limit_mb"):
			value = self.get(field)
			if value is not None and value != 0 and value < 0:
				frappe.throw(
					frappe._("{0} must be 0 (unlimited) or a positive number").format(
						self.meta.get_label(field)
					)
				)

		if self.action_on_exceed == "Throttle":
			if self.throttle_download_kbps and self.throttle_download_kbps <= 0:
				frappe.throw(frappe._("Throttle Download (kbps) must be greater than 0"))
			if self.throttle_upload_kbps and self.throttle_upload_kbps <= 0:
				frappe.throw(frappe._("Throttle Upload (kbps) must be greater than 0"))

		if self.notify_at_percentage and (
			self.notify_at_percentage < 0 or self.notify_at_percentage > 100
		):
			frappe.throw(frappe._("Notify at Percentage must be between 0 and 100"))
