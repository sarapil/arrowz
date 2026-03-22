# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AlertRule(Document):
	def validate(self):
		if self.condition_value is None:
			frappe.throw("Condition Value is required.")

		if self.notification_channels in ("Email", "Both") and not self.email_recipients:
			frappe.throw("Email Recipients are required when notification channel includes Email.")

		if self.notification_channels in ("Webhook", "Both") and not self.webhook_url:
			frappe.throw("Webhook URL is required when notification channel includes Webhook.")

		if self.cooldown_minutes and self.cooldown_minutes < 0:
			frappe.throw("Cooldown minutes cannot be negative.")
