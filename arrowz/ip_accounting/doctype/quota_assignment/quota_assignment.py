# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, add_days, get_first_day, get_last_day, getdate


class QuotaAssignment(Document):
	def validate(self):
		self.validate_target()
		self.calculate_next_reset()

	def validate_target(self):
		"""Ensure correct target field is set based on target_type."""
		if self.target_type == "Client":
			if not self.network_client:
				frappe.throw(_("Network Client is required when Target Type is Client"))
			self.client_group = None
		elif self.target_type == "Group":
			if not self.client_group:
				frappe.throw(_("Client Group is required when Target Type is Group"))
			self.network_client = None

	def calculate_next_reset(self):
		"""Calculate next_reset datetime based on quota_type."""
		if not self.usage_quota:
			return

		quota = frappe.get_cached_doc("Usage Quota", self.usage_quota)
		now = now_datetime()

		if quota.quota_type == "Daily":
			next_day = add_days(getdate(now), 1)
			self.next_reset = frappe.utils.get_datetime(f"{next_day} 00:00:00")
		elif quota.quota_type == "Weekly":
			days_until_monday = (7 - now.weekday()) % 7 or 7
			next_monday = add_days(getdate(now), days_until_monday)
			self.next_reset = frappe.utils.get_datetime(f"{next_monday} 00:00:00")
		elif quota.quota_type == "Monthly":
			last_day = get_last_day(now)
			next_month_first = add_days(last_day, 1)
			self.next_reset = frappe.utils.get_datetime(f"{next_month_first} 00:00:00")

	@frappe.whitelist(methods=["POST"])
	def reset_usage(self):
		"""Reset current usage counters."""
		frappe.only_for(["System Manager"])

		self.current_download_mb = 0
		self.current_upload_mb = 0
		self.current_total_mb = 0
		self.last_reset = now_datetime()
		self.status = "Active"
		self.calculate_next_reset()
		self.save()

	@frappe.whitelist(methods=["POST"])
	def recalculate_status(self):
		"""Recalculate assignment status based on current usage vs quota limits."""
		frappe.only_for(["AZ Manager", "System Manager"])

		if not self.usage_quota:
			return

		quota = frappe.get_cached_doc("Usage Quota", self.usage_quota)
		exceeded = False
		warning = False
		notify_pct = quota.notify_at_percentage or 80

		for limit_field, current_field in [
			("download_limit_mb", "current_download_mb"),
			("upload_limit_mb", "current_upload_mb"),
			("total_limit_mb", "current_total_mb"),
		]:
			limit_val = quota.get(limit_field) or 0
			current_val = self.get(current_field) or 0

			if limit_val > 0:
				usage_pct = (current_val / limit_val) * 100
				if usage_pct >= 100:
					exceeded = True
				elif usage_pct >= notify_pct:
					warning = True

		if exceeded:
			self.status = "Exceeded"
		elif warning:
			self.status = "Warning"
		else:
			self.status = "Active"

		self.save()
