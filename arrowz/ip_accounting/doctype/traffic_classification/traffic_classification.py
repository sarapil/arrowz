# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document


class TrafficClassification(Document):
	def validate(self):
		self.validate_match_value()

	def validate_match_value(self):
		"""Validate match_value format based on match_type."""
		if not self.match_value:
			return

		if self.match_type == "Port":
			# Port must be a number between 1 and 65535, or a range like 8000-8080
			port_pattern = re.compile(r"^\d+(-\d+)?$")
			if not port_pattern.match(self.match_value):
				frappe.throw(_("Port match value must be a number or range (e.g., 80 or 8000-8080)"))

			parts = self.match_value.split("-")
			for part in parts:
				port = int(part)
				if port < 1 or port > 65535:
					frappe.throw(_("Port number must be between 1 and 65535"))

			if len(parts) == 2 and int(parts[0]) >= int(parts[1]):
				frappe.throw(_("Port range start must be less than end"))

		elif self.match_type == "Domain":
			# Domain pattern: allow wildcards like *.example.com
			domain_pattern = re.compile(r"^[\w\-*]+\.[\w\-.*]+$")
			if not domain_pattern.match(self.match_value):
				frappe.throw(_("Invalid domain pattern. Use formats like example.com or *.example.com"))

		elif self.match_type == "IP Range":
			# IP range: CIDR notation like 192.168.1.0/24 or range like 192.168.1.1-192.168.1.254
			cidr_pattern = re.compile(
				r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$"
			)
			range_pattern = re.compile(
				r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}-\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
			)
			if not (cidr_pattern.match(self.match_value) or range_pattern.match(self.match_value)):
				frappe.throw(
					_("IP Range must be in CIDR notation (e.g., 192.168.1.0/24) or range format (e.g., 192.168.1.1-192.168.1.254)")
				)
