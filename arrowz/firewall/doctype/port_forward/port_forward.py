# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import re

import frappe
from frappe.model.document import Document


class PortForward(Document):
	def validate(self):
		self.validate_port_numbers()
		self.validate_internal_ip()

	def validate_port_numbers(self):
		"""Validate that port fields contain valid port numbers or ranges."""
		for field in ("external_port", "internal_port"):
			value = self.get(field)
			if value:
				self._validate_port(value, self.meta.get_label(field))

	def _validate_port(self, value, label):
		port_pattern = re.compile(r"^(\d{1,5})([-:]\d{1,5})?$")
		if not port_pattern.match(str(value)):
			frappe.throw(
				frappe._("{0} must be a valid port number or range (e.g. 80 or 80-443).").format(label)
			)
		for part in re.split(r"[-:]", str(value)):
			part = part.strip()
			if part and (int(part) < 1 or int(part) > 65535):
				frappe.throw(frappe._("Port numbers in {0} must be between 1 and 65535.").format(label))

	def validate_internal_ip(self):
		"""Validate the internal IP address."""
		if self.internal_ip:
			ip_pattern = re.compile(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$")
			if not ip_pattern.match(self.internal_ip):
				frappe.throw(frappe._("Internal IP must be a valid IPv4 address."))

	def on_update(self):
		self.push_port_forward_config()

	def push_port_forward_config(self):
		"""Push port forward configuration to the Arrowz Box."""
		frappe.publish_realtime(
			"port_forward_update",
			{
				"rule": self.name,
				"arrowz_box": self.arrowz_box,
				"protocol": self.protocol,
				"external_port": self.external_port,
				"internal_ip": self.internal_ip,
				"internal_port": self.internal_port,
				"enabled": self.enabled,
			},
			doctype=self.doctype,
			docname=self.name,
		)
		frappe.msgprint(
			frappe._("Port forward configuration pushed ({0} → {1}:{2}).").format(
				self.external_port, self.internal_ip, self.internal_port
			),
			alert=True,
		)
