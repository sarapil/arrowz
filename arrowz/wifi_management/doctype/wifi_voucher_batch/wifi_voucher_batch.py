# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import secrets
import string

import frappe
from frappe.model.document import Document


class WiFiVoucherBatch(Document):
	def validate(self):
		self.validate_voucher_count()
		self.validate_code_length()
		if not self.created_by:
			self.created_by = frappe.session.user

	def validate_voucher_count(self):
		"""Ensure voucher count is greater than 0."""
		if not self.voucher_count or self.voucher_count <= 0:
			frappe.throw(frappe._("Voucher Count must be greater than 0"))

	def validate_code_length(self):
		"""Ensure code length is reasonable."""
		if self.code_length and (self.code_length < 4 or self.code_length > 20):
			frappe.throw(frappe._("Code Length must be between 4 and 20"))

	@frappe.whitelist(methods=["POST"])
	def generate_vouchers(self):
		"""Generate voucher codes for this batch."""
		if self.status != "Draft":
			frappe.throw(frappe._("Vouchers can only be generated for Draft batches"))

		prefix = self.prefix or ""
		code_length = self.code_length or 8
		charset = string.ascii_uppercase + string.digits

		generated = 0
		for _ in range(self.voucher_count):
			code = prefix + "".join(secrets.choice(charset) for _ in range(code_length))

			voucher = frappe.get_doc({
				"doctype": "WiFi Voucher",
				"voucher_code": code,
				"batch": self.name,
				"status": "Available",
				"bandwidth_plan": self.bandwidth_plan,
				"usage_quota": self.usage_quota,
				"validity_hours": self.validity_hours,
			})
			voucher.insert(ignore_permissions=True)
			generated += 1

		self.status = "Generated"
		self.save(ignore_permissions=True)

		frappe.msgprint(frappe._("{0} vouchers generated successfully").format(generated))
		return {"generated": generated}
