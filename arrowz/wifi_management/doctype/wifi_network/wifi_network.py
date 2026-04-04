# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WiFiNetwork(Document):
	def validate(self):
		self.validate_password()
		self.validate_vlan()
		self.validate_tx_power()

	def validate_password(self):
		"""Ensure password is set when encryption is not Open."""
		if self.encryption and self.encryption != "Open" and not self.password:
			frappe.throw(frappe._("Password is required when encryption is not Open"))

	def validate_vlan(self):
		"""Validate VLAN ID range."""
		if self.vlan_id and (self.vlan_id < 1 or self.vlan_id > 4094):
			frappe.throw(frappe._("VLAN ID must be between 1 and 4094"))

	def validate_tx_power(self):
		"""Validate TX power range."""
		if self.tx_power and self.tx_power < 0:
			frappe.throw(frappe._("TX Power must be 0 (auto) or a positive value"))

	def on_update(self):
		"""Push hostapd configuration to the Arrowz Box."""
		self.push_hostapd_config()

	def push_hostapd_config(self):
		"""Generate and push hostapd configuration to the Arrowz Box."""
		if not self.arrowz_box:
			return

		config = {
			"ssid": self.ssid,
			"band": self.band,
			"channel": self.channel or "auto",
			"channel_width": self.channel_width,
			"encryption": self.encryption,
			"hidden_ssid": self.hidden_ssid,
			"max_clients": self.max_clients,
			"vlan_id": self.vlan_id,
			"tx_power": self.tx_power,
			"country_code": self.country_code,
		}

		frappe.publish_realtime(
			"wifi_config_update",
			{"arrowz_box": self.arrowz_box, "config": config},
			doctype="Arrowz Box",
			docname=self.arrowz_box,
		)
