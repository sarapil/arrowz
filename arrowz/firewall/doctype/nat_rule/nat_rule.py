# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


class NATRule(Document):
	def validate(self):
		self.validate_nat_type_fields()
		self.validate_addresses()
		self.validate_ports()

	def validate_nat_type_fields(self):
		"""Ensure required fields based on NAT type."""
		if self.nat_type == "SNAT" and not self.translated_address:
			frappe.throw(frappe._("Translated Address is required for SNAT rules."))
		if self.nat_type == "DNAT" and not self.translated_address:
			frappe.throw(frappe._("Translated Address is required for DNAT rules."))

	def validate_addresses(self):
		"""Validate IP address fields."""
		ip_pattern = re.compile(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(\/\d{1,2})?$")
		for field in ("source_address", "destination_address", "translated_address"):
			value = self.get(field)
			if value and not ip_pattern.match(value):
				frappe.throw(
					frappe._("{0} must be a valid IP address or CIDR notation.").format(
						self.meta.get_label(field)
					)
				)

	def validate_ports(self):
		"""Validate port fields."""
		for field in ("source_port", "destination_port", "translated_port"):
			value = self.get(field)
			if value:
				self._validate_port(value, self.meta.get_label(field))

	def _validate_port(self, value, label):
		port_pattern = re.compile(r"^(\d{1,5})([-:]\d{1,5})?$")
		if not port_pattern.match(value):
			frappe.throw(
				frappe._("{0} must be a valid port number or range (e.g. 80 or 80-443).").format(label)
			)
		for part in re.split(r"[-:]", value):
			part = part.strip()
			if part and (int(part) < 1 or int(part) > 65535):
				frappe.throw(frappe._("Port numbers in {0} must be between 1 and 65535.").format(label))

	def on_update(self):
		self.push_nat_config()

	def push_nat_config(self):
		"""Push NAT rule configuration to the Arrowz Box."""
		frappe.publish_realtime(
			"nat_rule_update",
			{
				"rule": self.name,
				"arrowz_box": self.arrowz_box,
				"nat_type": self.nat_type,
				"enabled": self.enabled,
				"priority": self.priority,
			},
			doctype=self.doctype,
			docname=self.name,
		)
		frappe.msgprint(
			frappe._("NAT rule configuration pushed ({0}).").format(self.nat_type),
			alert=True,
		)
