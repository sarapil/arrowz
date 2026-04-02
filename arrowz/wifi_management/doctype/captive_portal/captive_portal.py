# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CaptivePortal(Document):
	def validate(self):
		self.validate_port()
		self.validate_ssl()

	def validate_port(self):
		"""Validate listen port range."""
		if self.listen_port and (self.listen_port < 1 or self.listen_port > 65535):
			frappe.throw(frappe._("Listen Port must be between 1 and 65535"))

	def validate_ssl(self):
		"""Validate SSL cert and key paths are provided when SSL is enabled."""
		if self.ssl_enabled:
			if not self.ssl_cert_path:
				frappe.throw(frappe._("SSL Certificate Path is required when SSL is enabled"))
			if not self.ssl_key_path:
				frappe.throw(frappe._("SSL Key Path is required when SSL is enabled"))

	def on_update(self):
		"""Push captive portal configuration to the Arrowz Box."""
		self.push_portal_config()

	def push_portal_config(self):
		"""Generate and push captive portal configuration."""
		if not self.arrowz_box:
			return

		config = {
			"portal_name": self.portal_name,
			"enabled": self.enabled,
			"hotspot_profile": self.hotspot_profile,
			"listen_port": self.listen_port,
			"ssl_enabled": self.ssl_enabled,
			"ssl_cert_path": self.ssl_cert_path,
			"ssl_key_path": self.ssl_key_path,
			"redirect_url": self.redirect_url,
			"allowed_mac_bypass": self.allowed_mac_bypass,
		}

		frappe.publish_realtime(
			"captive_portal_config_update",
			{"arrowz_box": self.arrowz_box, "config": config},
			doctype="Arrowz Box",
			docname=self.arrowz_box,
		)

	@frappe.whitelist(methods=["POST"])
	def start_portal(self):
		"""Start the captive portal service."""
		frappe.only_for(["AZ Manager", "System Manager"])

		if self.status == "Running":
			frappe.throw(frappe._("Portal is already running"))

		self.status = "Running"
		self.save(ignore_permissions=True)

		frappe.msgprint(frappe._("Captive Portal {0} started").format(self.portal_name))
		return {"status": self.status}

	@frappe.whitelist(methods=["POST"])
	def stop_portal(self):
		"""Stop the captive portal service."""
		frappe.only_for(["AZ Manager", "System Manager"])

		if self.status == "Stopped":
			frappe.throw(frappe._("Portal is already stopped"))

		self.status = "Stopped"
		self.save(ignore_permissions=True)

		frappe.msgprint(frappe._("Captive Portal {0} stopped").format(self.portal_name))
		return {"status": self.status}
