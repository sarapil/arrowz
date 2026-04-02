# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import ipaddress

import frappe
from frappe.model.document import Document


class SitetoSiteTunnel(Document):
	def validate(self):
		self._validate_subnet(self.local_subnet, "Local Subnet")
		self._validate_subnet(self.remote_subnet, "Remote Subnet")

	def on_update(self):
		"""Push tunnel configuration when updated."""
		frappe.publish_realtime(
			"site_to_site_tunnel_update",
			{"tunnel": self.name, "arrowz_box": self.arrowz_box},
			user=frappe.session.user,
		)

	def _validate_subnet(self, subnet, field_label):
		"""Validate that a subnet is a valid CIDR."""
		if not subnet:
			return
		try:
			ipaddress.ip_network(subnet, strict=False)
		except ValueError:
			frappe.throw(f"Invalid CIDR in {field_label}: {subnet}")

	@frappe.whitelist(methods=["POST"])
	def check_status(self):
		"""Check the current status of the tunnel."""
		frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

		frappe.publish_realtime(
			"site_to_site_tunnel_check",
			{"tunnel": self.name, "arrowz_box": self.arrowz_box},
			user=frappe.session.user,
		)
		frappe.msgprint("Tunnel status check initiated.", indicator="blue", alert=True)
