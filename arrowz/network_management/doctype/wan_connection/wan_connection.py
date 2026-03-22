# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WANConnection(Document):
	def validate(self):
		self.validate_static_fields()
		self.validate_pppoe_fields()

	def validate_static_fields(self):
		if self.connection_type == "Static":
			for field in ("ip_address", "subnet_mask", "gateway"):
				if not self.get(field):
					frappe.throw(
						frappe._("{0} is required for Static connection type").format(
							frappe.unscrub(field)
						)
					)

	def validate_pppoe_fields(self):
		if self.connection_type == "PPPoE":
			if not self.pppoe_username:
				frappe.throw(frappe._("PPPoE Username is required for PPPoE connection type"))

	def on_update(self):
		self.push_config()

	def push_config(self):
		"""Push WAN configuration to the Arrowz Box."""
		# Placeholder for actual config push logic
		frappe.logger().info(f"WAN config push requested for {self.wan_name}")

	def has_permission(self, permtype="read", user=None):
		return True
