# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import ipaddress

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class VPNPeer(Document):
	def validate(self):
		# Public key required for WireGuard, optional for OpenVPN static key
		if not self.public_key:
			vpn_type = ""
			if self.vpn_server:
				vpn_type = frappe.db.get_value("VPN Server", self.vpn_server, "vpn_type") or ""
			if vpn_type != "OpenVPN":
				frappe.throw(_("Public Key is required for a VPN peer."))
		if not self.allowed_ips:
			frappe.throw(_("Allowed IPs must be specified."))
		if self.access_policy:
			self._enforce_access_policy()

	def _enforce_access_policy(self):
		"""Validate peer against linked VPN Access Policy rules."""
		policy = frappe.get_doc("VPN Access Policy", self.access_policy)

		if not policy.enabled:
			return

		# 1. Validity date check
		today = getdate(nowdate())
		if policy.valid_from and getdate(policy.valid_from) > today:
			frappe.throw(
				_("Access Policy '{0}' is not yet valid (starts {1}).").format(
					policy.policy_name, policy.valid_from
				)
			)
		if policy.valid_until and getdate(policy.valid_until) < today:
			frappe.throw(
				_("Access Policy '{0}' has expired (ended {1}).").format(
					policy.policy_name, policy.valid_until
				)
			)

		# 2. Max connections check
		if policy.max_connections and policy.max_connections > 0:
			current_peers = frappe.db.count("VPN Peer", filters={
				"access_policy": self.access_policy,
				"enabled": 1,
				"name": ["!=", self.name],
			})
			if current_peers >= policy.max_connections:
				frappe.throw(
					_("Access Policy '{0}' has reached its max connections limit ({1}).").format(
						policy.policy_name, policy.max_connections
					)
				)

		# 3. Allowed networks check — peer's allowed_ips must fall within allowed ranges
		if policy.allowed_networks:
			allowed_nets = self._parse_cidrs(policy.allowed_networks)
			if allowed_nets:
				peer_nets = self._parse_cidrs(self.allowed_ips)
				for pnet in peer_nets:
					if not any(pnet.subnet_of(anet) for anet in allowed_nets):
						frappe.throw(
							_("Peer network {0} is not within the policy's allowed networks.").format(str(pnet))
						)

		# 4. Blocked networks check
		if policy.blocked_networks:
			blocked_nets = self._parse_cidrs(policy.blocked_networks)
			peer_nets = self._parse_cidrs(self.allowed_ips)
			for pnet in peer_nets:
				for bnet in blocked_nets:
					if pnet.overlaps(bnet):
						frappe.throw(
							_("Peer network {0} overlaps with blocked network {1}.").format(
								str(pnet), str(bnet)
							)
						)

		# 5. 2FA flag — just set a warning, actual 2FA is enforced at connection time
		if policy.require_2fa:
			frappe.msgprint(
				_("Note: This peer's policy requires 2FA authentication at connection time."),
				indicator="blue", alert=True,
			)

	@staticmethod
	def _parse_cidrs(cidr_text):
		"""Parse comma or newline separated CIDR list into network objects."""
		networks = []
		if not cidr_text:
			return networks
		for part in cidr_text.replace(",", "\n").strip().splitlines():
			part = part.strip()
			if not part:
				continue
			try:
				networks.append(ipaddress.ip_network(part, strict=False))
			except ValueError:
				pass
		return networks

	def on_update(self):
		"""Push WireGuard configuration when peer is updated."""
		if self.vpn_server:
			frappe.publish_realtime(
				"vpn_peer_config_update",
				{"peer": self.name, "server": self.vpn_server},
				user=frappe.session.user,
			)

	@frappe.whitelist()
	def generate_client_config(self):
		"""Generate WireGuard client configuration text."""
		server = frappe.get_doc("VPN Server", self.vpn_server)
		config_lines = [
			"[Interface]",
			"PrivateKey = <CLIENT_PRIVATE_KEY>",
			f"Address = {self.allowed_ips}",
			f"DNS = {self.dns or server.dns_servers or '8.8.8.8'}",
			f"MTU = {server.mtu or 1420}",
			"",
			"[Peer]",
			f"PublicKey = {server.public_key or '<SERVER_PUBLIC_KEY>'}",
			f"Endpoint = {server.endpoint or '<SERVER_ENDPOINT>'}:{server.listen_port or 51820}",
			"AllowedIPs = 0.0.0.0/0",
			f"PersistentKeepalive = {self.keepalive or 25}",
		]
		if self.preshared_key:
			config_lines.insert(-1, f"PresharedKey = {self.get_password('preshared_key')}")
		return "\n".join(config_lines)

	@frappe.whitelist(methods=["POST"])
	def revoke_peer(self):
		"""Revoke this peer's access."""
		self.enabled = 0
		self.status = "Disconnected"
		self.save()
		frappe.publish_realtime(
			"vpn_peer_revoked",
			{"peer": self.name, "server": self.vpn_server},
			user=frappe.session.user,
		)
		frappe.msgprint(_("Peer access revoked."), indicator="orange", alert=True)

	@frappe.whitelist()
	def generate_qr_code(self):
		"""Generate QR code PNG (base64) for WireGuard mobile import.

		Returns:
			dict: {config: str, qr_base64: str, filename: str}
		"""
		config_text = self.generate_client_config()

		import base64
		import io

		import qrcode
		from qrcode.image.pil import PilImage

		qr = qrcode.QRCode(
			version=None,
			error_correction=qrcode.constants.ERROR_CORRECT_M,
			box_size=8,
			border=2,
		)
		qr.add_data(config_text)
		qr.make(fit=True)
		img = qr.make_image(image_factory=PilImage, fill_color="black", back_color="white")

		buffer = io.BytesIO()
		img.save(buffer, format="PNG")
		b64 = base64.b64encode(buffer.getvalue()).decode("ascii")

		safe_name = (self.peer_name or self.name).replace(" ", "_").replace("/", "-")
		return {
			"config": config_text,
			"qr_base64": b64,
			"filename": f"wg_{safe_name}.png",
		}
