# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class BillingCycle(Document):
	def validate(self):
		if self.end_date and self.start_date and getdate(self.end_date) < getdate(self.start_date):
			frappe.throw("End Date cannot be before Start Date.")

		if self.next_invoice_date and getdate(self.next_invoice_date) < getdate(self.start_date):
			frappe.throw("Next Invoice Date cannot be before Start Date.")

	@frappe.whitelist(methods=["POST"])
	def generate_invoice(self):
		"""Generate an ERPNext Sales Invoice for this billing cycle."""
		frappe.only_for(["AZ Manager", "System Manager"])

		if self.status != "Active":
			frappe.throw("Invoices can only be generated for active billing cycles.")

		plan = frappe.get_doc("Billing Plan", self.billing_plan)

		if not plan.item:
			frappe.throw(
				f"Billing Plan '{plan.plan_name}' does not have an ERPNext Item configured."
			)

		amount = self._calculate_amount(plan)

		invoice = frappe.new_doc("Sales Invoice")
		invoice.customer = self.customer
		invoice.posting_date = nowdate()
		invoice.currency = plan.currency or "JOD"

		if plan.tax_template:
			invoice.taxes_and_charges = plan.tax_template

		invoice.append("items", {
			"item_code": plan.item,
			"qty": 1,
			"rate": amount,
			"description": f"Billing for {plan.plan_name} - Cycle {self.name}",
		})

		if plan.tax_template:
			invoice.set_taxes()

		invoice.insert()

		# Create usage invoice log
		log = frappe.new_doc("Usage Invoice Log")
		log.billing_cycle = self.name
		log.customer = self.customer
		log.sales_invoice = invoice.name
		log.invoice_date = nowdate()
		log.period_start = self.last_invoice_date or self.start_date
		log.period_end = nowdate()
		log.total_amount = amount
		log.status = "Invoiced"
		log.insert()

		# Update billing cycle
		self.last_invoice_date = nowdate()
		self.total_billed = (self.total_billed or 0) + amount
		self.save()

		frappe.msgprint(
			f"Sales Invoice {invoice.name} created successfully.",
			indicator="green",
			alert=True,
		)
		return invoice.name

	def _calculate_amount(self, plan):
		"""Calculate the invoice amount based on the billing plan type."""
		if plan.billing_type == "Flat":
			return plan.flat_rate or 0

		if plan.billing_type == "Hybrid":
			return plan.flat_rate or 0

		# For Tiered and Usage Based, return 0 as placeholder
		# Actual usage-based calculation requires usage data integration
		return 0
