# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class WiFiVoucher(Document):
	def validate(self):
		self.validate_voucher_code()

	def validate_voucher_code(self):
		"""Ensure voucher code is not empty."""
		if not self.voucher_code or not self.voucher_code.strip():
			frappe.throw(frappe._("Voucher Code cannot be empty"))

	@frappe.whitelist(methods=["POST"])
	def activate(self, mac_address=None):
		"""Activate the voucher for a given MAC address."""
		if self.status != "Available":
			frappe.throw(frappe._("Only Available vouchers can be activated"))

		now = now_datetime()
		self.status = "Active"
		self.activated_on = now
		self.used_by_mac = mac_address

		if self.validity_hours:
			self.expires_on = now + timedelta(hours=self.validity_hours)

		self.save(ignore_permissions=True)

		frappe.msgprint(frappe._("Voucher {0} activated").format(self.voucher_code))
		return {"status": self.status, "expires_on": str(self.expires_on)}

	@frappe.whitelist(methods=["POST"])
	def deactivate(self):
		"""Deactivate / disable the voucher."""
		if self.status not in ("Available", "Active"):
			frappe.throw(frappe._("Only Available or Active vouchers can be deactivated"))

		self.status = "Disabled"
		self.save(ignore_permissions=True)

		frappe.msgprint(frappe._("Voucher {0} deactivated").format(self.voucher_code))
		return {"status": self.status}
