# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FirewallZone(Document):
	def validate(self):
		self.validate_zone_name()
		self.validate_interfaces()

	def validate_zone_name(self):
		if self.zone_name and not self.zone_name.replace("_", "").replace("-", "").isalnum():
			frappe.throw(
				frappe._("Zone Name must contain only alphanumeric characters, hyphens, or underscores.")
			)

	def validate_interfaces(self):
		if self.interfaces:
			ifaces = [i.strip() for i in self.interfaces.split(",") if i.strip()]
			self.interfaces = ", ".join(ifaces)

	def on_update(self):
		self.push_zone_config()

	def push_zone_config(self):
		"""Push zone configuration to the Arrowz Box."""
		frappe.publish_realtime(
			"firewall_zone_update",
			{
				"zone_name": self.zone_name,
				"arrowz_box": self.arrowz_box,
				"default_policy": self.default_policy,
				"enable_masquerade": self.enable_masquerade,
				"enable_logging": self.enable_logging,
				"interfaces": self.interfaces,
			},
			doctype=self.doctype,
			docname=self.name,
		)
		frappe.msgprint(
			frappe._("Zone configuration pushed for {0}").format(self.zone_name),
			alert=True,
		)
