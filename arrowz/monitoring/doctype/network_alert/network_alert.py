# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class NetworkAlert(Document):
	@frappe.whitelist(methods=["POST"])
	def acknowledge(self):
		"""Acknowledge this alert."""
		if self.status != "Active":
			frappe.throw("Only active alerts can be acknowledged.")
		self.status = "Acknowledged"
		self.acknowledged_by = frappe.session.user
		self.acknowledged_on = now_datetime()
		self.save()
		frappe.msgprint("Alert acknowledged.", indicator="blue", alert=True)

	@frappe.whitelist(methods=["POST"])
	def resolve(self):
		"""Resolve this alert."""
		if self.status == "Resolved":
			frappe.throw("This alert is already resolved.")
		self.status = "Resolved"
		self.resolved_on = now_datetime()
		if not self.acknowledged_by:
			self.acknowledged_by = frappe.session.user
			self.acknowledged_on = now_datetime()
		self.save()
		frappe.msgprint("Alert resolved.", indicator="green", alert=True)
