# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class ArrowzBox(Document):
	"""Represents a network device managed by Arrowz — either a Linux box
	running the Arrowz Engine or a MikroTik router with RouterOS API.

	Communication is handled through the device_providers abstraction:
	  - Linux Box  → BoxConnector REST API → FastAPI agent
	  - MikroTik   → RouterOS API via librouteros
	"""

	def validate(self):
		self._validate_ip()
		self._validate_port()
		self._validate_mikrotik()

	def _validate_ip(self):
		"""Validate IP address or hostname format."""
		import re

		ip_pattern = re.compile(
			r"^(?:(?:\d{1,3}\.){3}\d{1,3}|"
			r"[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z]{2,})+)$"
		)
		if self.box_ip and not ip_pattern.match(self.box_ip):
			frappe.throw(
				_("{0} is not a valid IP address or hostname").format(self.box_ip),
				title=_("Invalid Box IP"),
			)

	def _validate_port(self):
		"""Validate port range."""
		if self.api_port and not (1 <= self.api_port <= 65535):
			frappe.throw(
				_("API Port must be between 1 and 65535"),
				title=_("Invalid Port"),
			)

	def _validate_mikrotik(self):
		"""Validate MikroTik-specific fields when device_type is MikroTik."""
		if self.device_type == "MikroTik":
			port = self.mikrotik_api_port or 0
			if port and not (1 <= port <= 65535):
				frappe.throw(
					_("MikroTik API Port must be between 1 and 65535"),
					title=_("Invalid MikroTik Port"),
				)
			if not self.mikrotik_username:
				self.mikrotik_username = "admin"
			if not self.mikrotik_api_port:
				self.mikrotik_api_port = 8729 if self.mikrotik_use_ssl else 8728

	def _get_base_url(self) -> str:
		"""Build base URL for Engine API."""
		protocol = self.api_protocol or "https"
		return f"{protocol}://{self.box_ip}:{self.api_port}"

	def _get_connector(self):
		"""Get a BoxConnector instance for this box."""
		from arrowz.arrowz_api.utils.box_connector import BoxConnector

		return BoxConnector(self)

	@frappe.whitelist(methods=["POST"])
	def test_connection(self):
		"""Test connectivity using the appropriate device provider."""
		frappe.only_for(["System Manager"])

		try:
			from arrowz.device_providers.provider_factory import ProviderFactory

			result = ProviderFactory.test_connection(box_doc=self)

			if result.get("success"):
				self.status = "Online"
				self.last_heartbeat = now_datetime()

				sys_info = result.get("system_info", {})
				if sys_info:
					if self.device_type == "MikroTik":
						self.mikrotik_routeros_version = sys_info.get("os_version", "")
						self.mikrotik_model = sys_info.get("model", "")
						self.mikrotik_serial = sys_info.get("serial_number", "")
					else:
						if sys_info.get("firmware_version"):
							self.engine_version = sys_info["firmware_version"]
						if sys_info.get("os_version"):
							self.os_version = sys_info["os_version"]

				self.save(ignore_permissions=True)
				return {
					"status": "success",
					"message": _("Connection successful"),
					"data": result,
				}
			else:
				self.status = "Offline"
				self.save(ignore_permissions=True)
				return {
					"status": "error",
					"message": result.get("message", _("Connection failed")),
				}
		except Exception as e:
			self.status = "Offline"
			self.save(ignore_permissions=True)
			return {
				"status": "error",
				"message": _("Connection failed: {0}").format(str(e)),
			}

	@frappe.whitelist(methods=["POST"])
	def push_full_config(self):
		"""Compile and push complete configuration to this box."""
		frappe.only_for(["AZ Manager", "System Manager"])

		from arrowz.arrowz_api.utils.config_compiler import ConfigCompiler

		compiler = ConfigCompiler(self.name)
		config = compiler.compile_full()

		connector = self._get_connector()
		result = connector.push_config(config)

		if result.get("status") == "success":
			import hashlib
			import json

			config_json = json.dumps(config, sort_keys=True)
			self.engine_config_hash = hashlib.sha256(config_json.encode()).hexdigest()[:16]
			self.engine_last_config_push = now_datetime()
			self.save(ignore_permissions=True)

		return result

	@frappe.whitelist(methods=["POST"])
	def sync_telemetry(self):
		"""Pull latest telemetry data from the box."""
		frappe.only_for(["AZ Manager", "System Manager"])

		connector = self._get_connector()
		telemetry = connector.get_telemetry()

		if telemetry:
			# Update hardware info
			hw = telemetry.get("hardware", {})
			if hw:
				self.cpu_model = hw.get("cpu_model", self.cpu_model)
				self.cpu_cores = hw.get("cpu_cores", self.cpu_cores)
				self.total_ram_mb = hw.get("total_ram_mb", self.total_ram_mb)
				self.total_disk_mb = hw.get("total_disk_mb", self.total_disk_mb)
				self.os_version = hw.get("os_version", self.os_version)
				self.kernel_version = hw.get("kernel_version", self.kernel_version)

			# Update engine info
			engine = telemetry.get("engine", {})
			if engine:
				self.engine_version = engine.get("version", self.engine_version)
				self.engine_status = engine.get("status", self.engine_status)
				self.engine_uptime = engine.get("uptime", self.engine_uptime)

			self.last_heartbeat = now_datetime()
			self.status = "Online"
			self.save(ignore_permissions=True)

			# Log health
			_log_health(self.name, telemetry)

		return {"status": "success", "data": telemetry}

	@frappe.whitelist(methods=["POST"])
	def generate_api_token(self):
		"""Generate a new API Bearer token for this box."""
		frappe.only_for(["AZ Manager", "System Manager"])

		import secrets

		token = secrets.token_urlsafe(48)
		self.api_token = token
		self.save(ignore_permissions=True)

		return {
			"status": "success",
			"message": _("New API token generated. Save it securely."),
			"token": token,
		}

	@frappe.whitelist(methods=["POST"])
	def sync_pull(self):
		"""Pull device config into Frappe DocTypes.

		Reads all configuration from the device and creates/updates
		matching Frappe DocType records.
		"""
		frappe.only_for(["AZ Manager", "System Manager"])

		from arrowz.device_providers.sync_engine import SyncEngine

		engine = SyncEngine(box_doc=self)
		return engine.pull()

	@frappe.whitelist(methods=["POST"])
	def sync_push(self):
		"""Push Frappe config to device.

		Compiles all DocType data and pushes to the device via the
		appropriate provider (BoxConnector REST for Linux, RouterOS API for MikroTik).
		"""
		frappe.only_for(["AZ Manager", "System Manager"])

		from arrowz.device_providers.sync_engine import SyncEngine

		engine = SyncEngine(box_doc=self)
		return engine.push()

	@frappe.whitelist(methods=["POST"])
	def sync_diff(self):
		"""Compare Frappe state vs device state.

		Returns differences per section without making any changes.
		"""
		frappe.only_for(["AZ Manager", "System Manager"])

		from arrowz.device_providers.sync_engine import SyncEngine

		engine = SyncEngine(box_doc=self)
		return engine.diff()

	@frappe.whitelist(methods=["POST"])
	def get_device_config(self):
		"""Pull and return full device config without importing to DocTypes.

		Useful for debugging / preview of what the device currently has.
		"""
		frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

		from arrowz.device_providers.provider_factory import ProviderFactory

		with ProviderFactory.connect(box_doc=self) as provider:
			return provider.get_full_config()


def _log_health(box_name: str, telemetry: dict):
	"""Create a health log entry from telemetry data."""
	try:
		hw = telemetry.get("hardware", {})
		frappe.get_doc(
			{
				"doctype": "Arrowz Box Health Log",
				"arrowz_box": box_name,
				"log_type": "Heartbeat",
				"status": "Online",
				"cpu_usage": hw.get("cpu_usage"),
				"ram_usage": hw.get("ram_usage"),
				"disk_usage": hw.get("disk_usage"),
				"uptime_seconds": hw.get("uptime_seconds"),
				"active_clients": telemetry.get("clients", {}).get("active", 0),
				"details": frappe.as_json(telemetry),
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error("Arrowz Box Health Log Error")
