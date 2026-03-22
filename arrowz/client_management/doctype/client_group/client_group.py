# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ClientGroup(Document):
	def validate(self):
		self.validate_no_circular_parent()

	def validate_no_circular_parent(self):
		"""Ensure parent_group does not create a circular reference."""
		if not self.parent_group:
			return

		visited = set()
		current = self.parent_group

		while current:
			if current == self.name:
				frappe.throw(
					frappe._("Circular reference detected: {0} cannot be a parent of itself").format(
						self.name
					)
				)
			if current in visited:
				frappe.throw(
					frappe._("Circular reference detected in parent group hierarchy")
				)
			visited.add(current)
			current = frappe.db.get_value("Client Group", current, "parent_group")
