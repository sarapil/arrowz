# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
BoxConnector - Handles all communication between Frappe Interface Layer
and the Arrowz Engine (FastAPI agent) running on Linux Boxes.

Communication: HTTPS REST API with Bearer token + HMAC-SHA256 signing.
"""

import hashlib
import hmac
import json
import time

import frappe
import requests
from frappe import _


class BoxConnector:
	"""Manages API communication with an Arrowz Box Engine."""

	def __init__(self, box_doc=None, box_name: str = None):
		"""Initialize connector with an Arrowz Box document or name.

		Args:
			box_doc: Arrowz Box document instance
			box_name: Name of the Arrowz Box document
		"""
		if box_doc:
			self.box = box_doc
		elif box_name:
			self.box = frappe.get_doc("Arrowz Box", box_name)
		else:
			# Use default box from settings
			settings = frappe.get_cached_doc("Arrowz Network Settings")
			if not settings.default_box:
				frappe.throw(_("No Arrowz Box specified and no default box configured"))
			self.box = frappe.get_doc("Arrowz Box", settings.default_box)

		self.base_url = self._build_base_url()
		self.token = self.box.get_password("api_token") if self.box.api_token else None
		self.settings = frappe.get_cached_doc("Arrowz Network Settings")
		self.timeout = self.settings.api_timeout or 30
		self.retries = self.settings.retry_attempts or 3
		self.verify_ssl = bool(self.box.verify_ssl)

	def _build_base_url(self) -> str:
		"""Build base URL for the Engine API."""
		protocol = self.box.api_protocol or "https"
		return f"{protocol}://{self.box.box_ip}:{self.box.api_port}"

	def _get_headers(self, payload: str = "") -> dict:
		"""Build request headers with Bearer token and HMAC signature.

		Args:
			payload: JSON string of request body for HMAC signing
		"""
		headers = {
			"Content-Type": "application/json",
			"X-Arrowz-Box": self.box.name,
			"X-Arrowz-Timestamp": str(int(time.time())),
		}

		if self.token:
			headers["Authorization"] = f"Bearer {self.token}"

		# HMAC-SHA256 signing
		hmac_secret = self.settings.get_password("hmac_secret") if self.settings.hmac_secret else None
		if hmac_secret:
			message = f"{headers['X-Arrowz-Timestamp']}:{payload}"
			signature = hmac.new(
				hmac_secret.encode(),
				message.encode(),
				hashlib.sha256,
			).hexdigest()
			headers["X-Arrowz-Signature"] = signature

		return headers

	def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
		"""Make an authenticated request to the Engine API with retry logic.

		Args:
			method: HTTP method (GET, POST, PUT, DELETE)
			endpoint: API endpoint path (e.g., "/api/v1/health")
			data: Request body data

		Returns:
			Response JSON as dict
		"""
		url = f"{self.base_url}{endpoint}"
		payload = json.dumps(data, default=str) if data else ""
		headers = self._get_headers(payload)

		last_error = None
		for attempt in range(self.retries):
			try:
				response = requests.request(
					method=method,
					url=url,
					headers=headers,
					data=payload if data else None,
					timeout=self.timeout,
					verify=self.verify_ssl,
				)

				if response.status_code == 401:
					frappe.throw(
						_("Authentication failed for box {0}. Check API token.").format(self.box.name),
						title=_("Auth Error"),
					)

				if response.status_code == 403:
					frappe.throw(
						_("Access denied on box {0}. Check permissions.").format(self.box.name),
						title=_("Permission Error"),
					)

				response.raise_for_status()
				return response.json() if response.text else {}

			except requests.exceptions.ConnectionError as e:
				last_error = e
				if self.settings.debug_mode:
					frappe.log_error(
						f"Connection attempt {attempt + 1}/{self.retries} failed for {self.box.name}: {e}",
						"BoxConnector Connection Error",
					)
				if attempt < self.retries - 1:
					time.sleep(2 ** attempt)  # Exponential backoff

			except requests.exceptions.Timeout as e:
				last_error = e
				if attempt < self.retries - 1:
					time.sleep(1)

			except requests.exceptions.HTTPError as e:
				frappe.log_error(
					f"HTTP Error from {self.box.name}: {e.response.status_code} - {e.response.text}",
					"BoxConnector HTTP Error",
				)
				raise

		frappe.throw(
			_("Failed to connect to box {0} after {1} attempts: {2}").format(
				self.box.name, self.retries, str(last_error)
			),
			title=_("Connection Failed"),
		)

	# ── Health & Status ──────────────────────────────────────────────

	def health_check(self) -> dict:
		"""Check if the Engine is running and healthy.

		Returns:
			Dict with status, version, uptime info
		"""
		return self._request("GET", "/api/v1/health")

	def get_telemetry(self) -> dict:
		"""Get comprehensive telemetry data from the box.

		Returns:
			Dict with hardware metrics, client counts, interface stats
		"""
		return self._request("GET", "/api/v1/telemetry")

	def get_engine_status(self) -> dict:
		"""Get Engine service status and component health."""
		return self._request("GET", "/api/v1/status")

	# ── Configuration Push ───────────────────────────────────────────

	def push_config(self, config: dict) -> dict:
		"""Push full or partial configuration to the Engine.

		Args:
			config: Configuration dict (from ConfigCompiler)

		Returns:
			Dict with status and any errors
		"""
		return self._request("POST", "/api/v1/config/apply", config)

	def push_network_config(self, config: dict) -> dict:
		"""Push network-specific configuration (WAN, LAN, routes)."""
		return self._request("POST", "/api/v1/config/network", config)

	def push_firewall_config(self, config: dict) -> dict:
		"""Push firewall rules configuration (nftables)."""
		return self._request("POST", "/api/v1/config/firewall", config)

	def push_wifi_config(self, config: dict) -> dict:
		"""Push WiFi configuration (hostapd)."""
		return self._request("POST", "/api/v1/config/wifi", config)

	def push_bandwidth_config(self, config: dict) -> dict:
		"""Push bandwidth/QoS configuration (tc)."""
		return self._request("POST", "/api/v1/config/bandwidth", config)

	def push_client_config(self, config: dict) -> dict:
		"""Push client management config (DHCP reservations, blocks)."""
		return self._request("POST", "/api/v1/config/clients", config)

	def push_vpn_config(self, config: dict) -> dict:
		"""Push VPN configuration (WireGuard/OpenVPN)."""
		return self._request("POST", "/api/v1/config/vpn", config)

	def push_dns_config(self, config: dict) -> dict:
		"""Push DNS configuration."""
		return self._request("POST", "/api/v1/config/dns", config)

	# ── Client Operations ────────────────────────────────────────────

	def get_connected_clients(self) -> list:
		"""Get list of currently connected clients."""
		result = self._request("GET", "/api/v1/clients")
		return result.get("clients", [])

	def block_client(self, mac_address: str) -> dict:
		"""Block a client by MAC address."""
		return self._request("POST", "/api/v1/clients/block", {"mac_address": mac_address})

	def unblock_client(self, mac_address: str) -> dict:
		"""Unblock a client by MAC address."""
		return self._request("POST", "/api/v1/clients/unblock", {"mac_address": mac_address})

	def disconnect_client(self, mac_address: str) -> dict:
		"""Disconnect a client (force deauth)."""
		return self._request("POST", "/api/v1/clients/disconnect", {"mac_address": mac_address})

	# ── Service Control ──────────────────────────────────────────────

	def restart_service(self, service_name: str) -> dict:
		"""Restart a specific service on the box.

		Args:
			service_name: e.g., "hostapd", "dnsmasq", "nftables", "wireguard"
		"""
		return self._request("POST", f"/api/v1/services/{service_name}/restart")

	def get_service_status(self, service_name: str) -> dict:
		"""Get status of a specific service."""
		return self._request("GET", f"/api/v1/services/{service_name}/status")

	# ── Network Info ─────────────────────────────────────────────────

	def get_interfaces(self) -> list:
		"""Get all network interfaces and their status."""
		result = self._request("GET", "/api/v1/network/interfaces")
		return result.get("interfaces", [])

	def get_dhcp_leases(self) -> list:
		"""Get current DHCP leases."""
		result = self._request("GET", "/api/v1/network/dhcp/leases")
		return result.get("leases", [])

	def get_arp_table(self) -> list:
		"""Get ARP table entries."""
		result = self._request("GET", "/api/v1/network/arp")
		return result.get("entries", [])

	def get_routing_table(self) -> list:
		"""Get routing table."""
		result = self._request("GET", "/api/v1/network/routes")
		return result.get("routes", [])

	# ── WiFi/Hotspot ─────────────────────────────────────────────────

	def get_wifi_clients(self) -> list:
		"""Get connected WiFi clients with signal info."""
		result = self._request("GET", "/api/v1/wifi/clients")
		return result.get("clients", [])

	def get_wifi_status(self) -> dict:
		"""Get WiFi radio and SSID status."""
		return self._request("GET", "/api/v1/wifi/status")

	def authorize_hotspot_client(self, mac_address: str, session_data: dict) -> dict:
		"""Authorize a hotspot client after authentication."""
		payload = {"mac_address": mac_address, **session_data}
		return self._request("POST", "/api/v1/wifi/hotspot/authorize", payload)

	def deauthorize_hotspot_client(self, mac_address: str) -> dict:
		"""Deauthorize a hotspot client."""
		return self._request("POST", "/api/v1/wifi/hotspot/deauthorize", {"mac_address": mac_address})

	# ── VPN ──────────────────────────────────────────────────────────

	def get_vpn_peers(self) -> list:
		"""Get VPN peer status and handshake info."""
		result = self._request("GET", "/api/v1/vpn/peers")
		return result.get("peers", [])

	# ── IP Accounting ────────────────────────────────────────────────

	def get_traffic_stats(self, period: str = "5min") -> dict:
		"""Get traffic statistics for the given period."""
		return self._request("GET", f"/api/v1/accounting/stats?period={period}")

	def get_client_usage(self, mac_address: str) -> dict:
		"""Get usage data for a specific client."""
		return self._request("GET", f"/api/v1/accounting/client/{mac_address}")

	# ── Logs ─────────────────────────────────────────────────────────

	def get_firewall_logs(self, limit: int = 100) -> list:
		"""Get recent firewall log entries."""
		result = self._request("GET", f"/api/v1/logs/firewall?limit={limit}")
		return result.get("logs", [])

	def get_system_logs(self, limit: int = 100) -> list:
		"""Get recent system log entries."""
		result = self._request("GET", f"/api/v1/logs/system?limit={limit}")
		return result.get("logs", [])
