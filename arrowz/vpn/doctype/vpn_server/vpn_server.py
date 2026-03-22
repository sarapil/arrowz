# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import subprocess

import frappe
from frappe.model.document import Document


class VPNServer(Document):
	def validate(self):
		if self.vpn_type == "WireGuard" and not self.listen_port:
			self.listen_port = 51820
		if self.server_address and "/" not in self.server_address:
			frappe.throw("Server Address must include CIDR notation (e.g. 10.10.0.1/24)")

	@frappe.whitelist(methods=["POST"])
	def generate_keys(self):
		"""Generate WireGuard key pair for this server."""
		if self.vpn_type != "WireGuard":
			frappe.throw("Key generation is only supported for WireGuard servers.")
		try:
			private_key = subprocess.check_output(["wg", "genkey"], text=True).strip()
			public_key = subprocess.check_output(
				["wg", "pubkey"], input=private_key, text=True
			).strip()
			self.private_key = private_key
			self.public_key = public_key
			self.save()
			frappe.msgprint("WireGuard keys generated successfully.", indicator="green", alert=True)
		except FileNotFoundError:
			frappe.throw("WireGuard tools (wg) not found on this system.")
		except subprocess.CalledProcessError as e:
			frappe.throw(f"Failed to generate keys: {e}")

	@frappe.whitelist(methods=["POST"])
	def restart_server(self):
		"""Restart the VPN server process."""
		frappe.publish_realtime(
			"vpn_server_restart",
			{"server": self.name, "vpn_type": self.vpn_type},
			user=frappe.session.user,
		)
		self.status = "Running"
		self.save()
		frappe.msgprint("VPN Server restart initiated.", indicator="blue", alert=True)
