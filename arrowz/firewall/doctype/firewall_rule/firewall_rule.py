# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


class FirewallRule(Document):
	def validate(self):
		self.validate_ports()
		self.validate_addresses()

	def validate_ports(self):
		"""Validate port fields contain valid port numbers or ranges."""
		for field in ("source_port", "destination_port"):
			value = self.get(field)
			if value:
				self._validate_port_value(value, self.meta.get_label(field))

	def _validate_port_value(self, value, label):
		"""Check that a port value is a valid number, range, or comma-separated list."""
		port_pattern = re.compile(r"^(\d{1,5})([-:]\d{1,5})?(,\s*\d{1,5}([-:]\d{1,5})?)*$")
		if not port_pattern.match(value):
			frappe.throw(
				frappe._("{0} must be a valid port number, range (e.g. 80-443), or comma-separated list.").format(label)
			)
		# Validate individual port numbers are in range 1-65535
		for part in re.split(r"[,\-:]", value):
			part = part.strip()
			if part and (int(part) < 1 or int(part) > 65535):
				frappe.throw(frappe._("Port numbers in {0} must be between 1 and 65535.").format(label))

	def validate_addresses(self):
		"""Validate IP/CIDR address fields."""
		for field in ("source_address", "destination_address"):
			value = self.get(field)
			if value:
				self._validate_address(value, self.meta.get_label(field))

	def _validate_address(self, value, label):
		"""Check that an address is a valid IP, CIDR, or address group reference."""
		# Allow simple IP, CIDR notation, or named address groups
		ip_cidr_pattern = re.compile(
			r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(\/\d{1,2})?$"
		)
		if not ip_cidr_pattern.match(value) and not value.replace("_", "").replace("-", "").isalnum():
			frappe.throw(
				frappe._("{0} must be a valid IP address, CIDR notation, or address group name.").format(label)
			)

	def on_update(self):
		self.push_rule_config()

	def push_rule_config(self):
		"""Push firewall rule configuration to the Arrowz Box."""
		frappe.publish_realtime(
			"firewall_rule_update",
			{
				"rule": self.name,
				"arrowz_box": self.arrowz_box,
				"rule_set": self.rule_set,
				"rule_number": self.rule_number,
				"action": self.action,
				"protocol": self.protocol,
				"enabled": self.enabled,
			},
			doctype=self.doctype,
			docname=self.name,
		)
		frappe.msgprint(
			frappe._("Firewall rule #{0} configuration pushed.").format(self.rule_number),
			alert=True,
		)
