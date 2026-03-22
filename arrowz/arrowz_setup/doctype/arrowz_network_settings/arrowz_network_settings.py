# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ArrowzNetworkSettings(Document):
	"""Singleton settings for Arrowz Network Management Platform.

	Controls global defaults for network, WiFi, billing, monitoring,
	and security across all Arrowz Boxes.
	"""

	@staticmethod
	def get_settings() -> "ArrowzNetworkSettings":
		"""Get cached singleton instance."""
		return frappe.get_cached_doc("Arrowz Network Settings")

	def validate(self):
		self._validate_dns()
		self._validate_mtu()
		self._validate_retention()
		self._validate_security()

	def _validate_dns(self):
		"""Validate DNS server addresses."""
		import re
		ip_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
		for field in ("default_dns_primary", "default_dns_secondary"):
			val = self.get(field)
			if val and not ip_pattern.match(val):
				frappe.throw(
					frappe._("{0} is not a valid IP address").format(val),
					title=frappe._("Invalid DNS Server"),
				)

	def _validate_mtu(self):
		"""Validate MTU range."""
		if self.default_mtu and not (68 <= self.default_mtu <= 9000):
			frappe.throw(
				frappe._("MTU must be between 68 and 9000"),
				title=frappe._("Invalid MTU"),
			)

	def _validate_retention(self):
		"""Validate retention periods."""
		for field in ("retention_days_logs", "retention_days_accounting", "retention_days_sessions"):
			val = self.get(field)
			if val is not None and val < 1:
				frappe.throw(
					frappe._("Retention days must be at least 1"),
					title=frappe._("Invalid Retention Period"),
				)

	def _validate_security(self):
		"""Validate security settings."""
		if self.api_token_expiry_days and self.api_token_expiry_days < 1:
			frappe.throw(
				frappe._("API Token Expiry must be at least 1 day"),
				title=frappe._("Invalid Token Expiry"),
			)
		if self.invoice_day_of_month and not (1 <= self.invoice_day_of_month <= 28):
			frappe.throw(
				frappe._("Invoice day must be between 1 and 28"),
				title=frappe._("Invalid Invoice Day"),
			)

	@frappe.whitelist(methods=["POST"])
	def generate_hmac_secret(self):
		"""Generate a new HMAC secret key."""
		import secrets

		self.hmac_secret = secrets.token_hex(32)
		self.save()
		return {"status": "success", "message": frappe._("HMAC secret regenerated")}

	@frappe.whitelist(methods=["POST"])
	def test_default_box_connection(self):
		"""Test connectivity to the default Arrowz Box."""
		if not self.default_box:
			frappe.throw(frappe._("No default box configured"))

		box = frappe.get_doc("Arrowz Box", self.default_box)
		return box.test_connection()
