# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
BaseProvider — Abstract Base Class for all device providers.

Every router/device backend MUST implement this interface. The methods
map directly to the Frappe DocType operations that the Arrowz platform
needs to perform: CRUD on network resources (interfaces, IPs, routes,
firewall rules, queues, WiFi, VPN, DNS, clients).

Design Principles:
  1. All methods return plain dicts/lists — no device-specific objects.
  2. Errors raise ProviderError (or subclass) with execution-layer context.
  3. Connection lifecycle is explicit: connect() / disconnect() / context manager.
  4. Every method receives/returns data in Arrowz's canonical format;
     data translation happens inside each provider (via Mappers).
"""

from __future__ import annotations

import contextlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ProviderError(Exception):
    """Base exception for all provider-layer errors."""

    def __init__(self, message: str, layer: str = "provider", details: dict | None = None):
        self.layer = layer
        self.details = details or {}
        super().__init__(f"[{layer}] {message}")


class ConnectionError(ProviderError):
    """Raised when connection to the device fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, layer="connection", **kwargs)


class AuthenticationError(ProviderError):
    """Raised when authentication credentials are rejected."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, layer="authentication", **kwargs)


class CommandError(ProviderError):
    """Raised when a command/API call to the device fails."""

    def __init__(self, message: str, command: str = "", **kwargs):
        self.command = command
        details = kwargs.pop("details", {})
        details["command"] = command
        super().__init__(message, layer="command", details=details, **kwargs)


class SyncError(ProviderError):
    """Raised when a sync operation fails."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, layer="sync", **kwargs)


class BaseProvider(ABC):
    """Abstract base class for network device providers.

    Subclasses implement device-specific API calls while conforming
    to a unified interface that the Arrowz platform consumes.

    Usage as context manager:
        with ProviderFactory.get(box_name="my-router") as provider:
            info = provider.get_system_info()
    """

    # Provider metadata — subclasses MUST set these
    PROVIDER_TYPE: str = "unknown"       # e.g. "linux", "mikrotik"
    PROVIDER_VERSION: str = "1.0.0"
    SUPPORTED_FEATURES: tuple = ()       # e.g. ("interfaces", "firewall", "dhcp", ...)

    def __init__(self, box_doc, settings=None):
        """Initialize provider with an Arrowz Box document.

        Args:
            box_doc: frappe Document for 'Arrowz Box'
            settings: Optional ArrowzNetworkSettings doc (auto-loaded if None)
        """
        self.box_doc = box_doc
        self.box_name = box_doc.name
        self._settings = settings
        self._connected = False

    @property
    def settings(self):
        """Lazy-load Arrowz Network Settings."""
        if self._settings is None:
            import frappe
            self._settings = frappe.get_cached_doc("Arrowz Network Settings")
        return self._settings

    @property
    def is_connected(self) -> bool:
        return self._connected

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with contextlib.suppress(Exception):
            self.disconnect()
        return False

    # ═══════════════════════════════════════════════════════════════
    # CONNECTION LIFECYCLE
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the device. Raises ConnectionError on failure."""
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to the device gracefully."""
        ...

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test connectivity and return device status.

        Returns:
            {
                "status": "online" | "offline" | "error",
                "message": str,
                "response_time_ms": float,
                "device_info": {...}   # basic identity info
            }
        """
        ...

    # ═══════════════════════════════════════════════════════════════
    # SYSTEM INFORMATION
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    def get_system_info(self) -> Dict[str, Any]:
        """Get device identity and software version.

        Returns:
            {
                "hostname": str,
                "model": str,
                "serial_number": str,
                "os_version": str,
                "firmware_version": str,
                "architecture": str,
                "uptime_seconds": int,
            }
        """
        ...

    @abstractmethod
    def get_system_resources(self) -> Dict[str, Any]:
        """Get real-time CPU, RAM, disk usage.

        Returns:
            {
                "cpu_usage_percent": float,
                "cpu_cores": int,
                "cpu_model": str,
                "ram_total_mb": int,
                "ram_used_mb": int,
                "ram_usage_percent": float,
                "disk_total_mb": int,
                "disk_used_mb": int,
                "disk_usage_percent": float,
                "uptime_seconds": int,
            }
        """
        ...

    @abstractmethod
    def reboot(self) -> Dict[str, Any]:
        """Reboot the device.

        Returns:
            {"status": "success" | "error", "message": str}
        """
        ...

    # ═══════════════════════════════════════════════════════════════
    # INTERFACES
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    def get_interfaces(self) -> List[Dict[str, Any]]:
        """Get all network interfaces.

        Returns list of:
            {
                "id": str,           # device-internal ID
                "name": str,         # interface name (e.g. "ether1")
                "type": str,         # "ethernet" | "bridge" | "vlan" | "bonding" | "wireless" | "wireguard" | "pppoe"
                "mac_address": str,
                "status": str,       # "up" | "down" | "disabled"
                "speed": str,        # e.g. "1Gbps"
                "mtu": int,
                "rx_bytes": int,
                "tx_bytes": int,
                "comment": str,
            }
        """
        ...

    @abstractmethod
    def set_interface(self, interface_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update interface configuration.

        Args:
            interface_id: Device-internal interface ID
            config: Fields to update (name, mtu, disabled, comment, etc.)

        Returns:
            Updated interface dict
        """
        ...

    # ═══════════════════════════════════════════════════════════════
    # IP ADDRESSES
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    def get_ip_addresses(self) -> List[Dict[str, Any]]:
        """Get all IP addresses assigned to interfaces.

        Returns list of:
            {
                "id": str,
                "address": str,       # CIDR notation e.g. "192.168.1.1/24"
                "interface": str,     # interface name
                "network": str,       # network address
                "enabled": bool,
                "comment": str,
            }
        """
        ...

    @abstractmethod
    def add_ip_address(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add an IP address to an interface.

        Args:
            config: {"address": "192.168.1.1/24", "interface": "ether2", "comment": "..."}

        Returns:
            Created IP address dict with "id"
        """
        ...

    @abstractmethod
    def remove_ip_address(self, address_id: str) -> bool:
        """Remove an IP address by its device-internal ID."""
        ...

    # ═══════════════════════════════════════════════════════════════
    # DHCP
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    def get_dhcp_servers(self) -> List[Dict[str, Any]]:
        """Get DHCP server configurations.

        Returns list of:
            {
                "id": str,
                "name": str,
                "interface": str,
                "pool_name": str,
                "network": str,
                "gateway": str,
                "dns_servers": list[str],
                "lease_time": str,
                "enabled": bool,
            }
        """
        ...

    @abstractmethod
    def add_dhcp_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a DHCP server with pool and network."""
        ...

    @abstractmethod
    def update_dhcp_server(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update DHCP server configuration."""
        ...

    @abstractmethod
    def remove_dhcp_server(self, server_id: str) -> bool:
        """Remove a DHCP server and associated pool/network."""
        ...

    @abstractmethod
    def get_dhcp_leases(self) -> List[Dict[str, Any]]:
        """Get current DHCP leases.

        Returns list of:
            {
                "id": str,
                "address": str,
                "mac_address": str,
                "hostname": str,
                "server": str,
                "status": str,        # "bound" | "waiting" | "offered"
                "expires_at": str,
                "is_static": bool,
            }
        """
        ...

    @abstractmethod
    def add_dhcp_static_lease(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a static DHCP lease (IP reservation).

        Args:
            config: {"mac_address": "AA:BB:CC:DD:EE:FF", "address": "192.168.1.100", "comment": "..."}
        """
        ...

    @abstractmethod
    def remove_dhcp_static_lease(self, lease_id: str) -> bool:
        """Remove a static DHCP lease."""
        ...

    # ═══════════════════════════════════════════════════════════════
    # DNS
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    def get_dns_config(self) -> Dict[str, Any]:
        """Get DNS resolver configuration.

        Returns:
            {
                "servers": list[str],
                "allow_remote_requests": bool,
                "cache_size_kb": int,
                "cache_used_kb": int,
            }
        """
        ...

    @abstractmethod
    def set_dns_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Set DNS resolver configuration."""
        ...

    @abstractmethod
    def get_dns_static_entries(self) -> List[Dict[str, Any]]:
        """Get static DNS entries.

        Returns list of:
            {
                "id": str,
                "name": str,        # hostname
                "address": str,     # IP address
                "type": str,        # "A" | "CNAME" | etc.
                "ttl": str,
                "enabled": bool,
                "comment": str,
            }
        """
        ...

    @abstractmethod
    def add_dns_static_entry(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a static DNS entry."""
        ...

    @abstractmethod
    def remove_dns_static_entry(self, entry_id: str) -> bool:
        """Remove a static DNS entry."""
        ...

    # ═══════════════════════════════════════════════════════════════
    # ROUTING
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    def get_routes(self) -> List[Dict[str, Any]]:
        """Get routing table.

        Returns list of:
            {
                "id": str,
                "destination": str,    # CIDR e.g. "0.0.0.0/0"
                "gateway": str,
                "interface": str,
                "metric": int,
                "type": str,           # "static" | "connected" | "dynamic"
                "enabled": bool,
                "comment": str,
            }
        """
        ...

    @abstractmethod
    def add_route(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a static route."""
        ...

    @abstractmethod
    def remove_route(self, route_id: str) -> bool:
        """Remove a static route."""
        ...

    # ═══════════════════════════════════════════════════════════════
    # FIREWALL
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    def get_firewall_filter_rules(self) -> List[Dict[str, Any]]:
        """Get firewall filter rules.

        Returns list of:
            {
                "id": str,
                "chain": str,        # "input" | "forward" | "output"
                "action": str,       # "accept" | "drop" | "reject" | "log"
                "protocol": str,
                "src_address": str,
                "dst_address": str,
                "src_port": str,
                "dst_port": str,
                "in_interface": str,
                "out_interface": str,
                "comment": str,
                "enabled": bool,
                "position": int,
                "bytes": int,
                "packets": int,
            }
        """
        ...

    @abstractmethod
    def add_firewall_filter_rule(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a firewall filter rule."""
        ...

    @abstractmethod
    def update_firewall_filter_rule(self, rule_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing firewall filter rule."""
        ...

    @abstractmethod
    def remove_firewall_filter_rule(self, rule_id: str) -> bool:
        """Remove a firewall filter rule."""
        ...

    @abstractmethod
    def get_firewall_nat_rules(self) -> List[Dict[str, Any]]:
        """Get NAT rules (srcnat + dstnat)."""
        ...

    @abstractmethod
    def add_firewall_nat_rule(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a NAT rule."""
        ...

    @abstractmethod
    def remove_firewall_nat_rule(self, rule_id: str) -> bool:
        """Remove a NAT rule."""
        ...

    # ═══════════════════════════════════════════════════════════════
    # QUEUES / BANDWIDTH
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    def get_queues(self) -> List[Dict[str, Any]]:
        """Get bandwidth queues (simple queues).

        Returns list of:
            {
                "id": str,
                "name": str,
                "target": str,         # IP or subnet
                "max_download": str,    # e.g. "10M"
                "max_upload": str,
                "burst_download": str,
                "burst_upload": str,
                "burst_threshold_dl": str,
                "burst_threshold_ul": str,
                "burst_time_dl": str,
                "burst_time_ul": str,
                "priority": int,
                "enabled": bool,
                "comment": str,
                "bytes_in": int,
                "bytes_out": int,
            }
        """
        ...

    @abstractmethod
    def add_queue(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a bandwidth queue."""
        ...

    @abstractmethod
    def update_queue(self, queue_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update a bandwidth queue."""
        ...

    @abstractmethod
    def remove_queue(self, queue_id: str) -> bool:
        """Remove a bandwidth queue."""
        ...

    # ═══════════════════════════════════════════════════════════════
    # WIRELESS / WIFI
    # ═══════════════════════════════════════════════════════════════

    def get_wireless_interfaces(self) -> List[Dict[str, Any]]:
        """Get wireless interfaces and SSIDs.

        Default: return empty (device may not support WiFi).
        Override in providers for WiFi-capable devices.

        Returns list of:
            {
                "id": str,
                "name": str,
                "ssid": str,
                "band": str,           # "2ghz" | "5ghz"
                "channel": int,
                "frequency": int,
                "security_profile": str,
                "mode": str,           # "ap" | "station"
                "enabled": bool,
                "connected_clients": int,
            }
        """
        return []

    def set_wireless_interface(self, iface_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update wireless interface configuration."""
        raise ProviderError(f"WiFi not supported by {self.PROVIDER_TYPE}", layer="feature")

    def get_wireless_clients(self) -> List[Dict[str, Any]]:
        """Get connected wireless clients."""
        return []

    # ═══════════════════════════════════════════════════════════════
    # VPN
    # ═══════════════════════════════════════════════════════════════

    def get_vpn_interfaces(self) -> List[Dict[str, Any]]:
        """Get VPN tunnel interfaces (WireGuard, IPsec, etc.).

        Returns list of:
            {
                "id": str,
                "name": str,
                "type": str,          # "wireguard" | "ipsec" | "l2tp" | "pptp"
                "listen_port": int,
                "public_key": str,
                "private_key": str,   # redacted
                "enabled": bool,
                "running": bool,
            }
        """
        return []

    def get_vpn_peers(self) -> List[Dict[str, Any]]:
        """Get VPN peers.

        Returns list of:
            {
                "id": str,
                "interface": str,
                "public_key": str,
                "endpoint": str,
                "allowed_address": str,
                "last_handshake": str,
                "rx_bytes": int,
                "tx_bytes": int,
                "enabled": bool,
                "comment": str,
            }
        """
        return []

    def add_vpn_peer(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a VPN peer."""
        raise ProviderError(f"VPN not supported by {self.PROVIDER_TYPE}", layer="feature")

    def remove_vpn_peer(self, peer_id: str) -> bool:
        """Remove a VPN peer."""
        raise ProviderError(f"VPN not supported by {self.PROVIDER_TYPE}", layer="feature")

    # ═══════════════════════════════════════════════════════════════
    # ARP / CLIENT DISCOVERY
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    def get_arp_table(self) -> List[Dict[str, Any]]:
        """Get ARP table entries.

        Returns list of:
            {
                "id": str,
                "address": str,       # IP
                "mac_address": str,
                "interface": str,
                "status": str,        # "reachable" | "stale" | "permanent"
            }
        """
        ...

    # ═══════════════════════════════════════════════════════════════
    # FULL CONFIG OPERATIONS (for sync)
    # ═══════════════════════════════════════════════════════════════

    @abstractmethod
    def get_full_config(self) -> Dict[str, Any]:
        """Pull complete device configuration as a structured dict.

        Used by the SyncEngine for pull operations (device → Frappe).

        Returns:
            {
                "system": {...},
                "interfaces": [...],
                "ip_addresses": [...],
                "dhcp_servers": [...],
                "dhcp_leases": [...],
                "dns": {...},
                "dns_static": [...],
                "routes": [...],
                "firewall_filter": [...],
                "firewall_nat": [...],
                "queues": [...],
                "wireless": [...],
                "vpn_interfaces": [...],
                "vpn_peers": [...],
                "arp": [...],
            }
        """
        ...

    def push_full_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Push complete configuration to device.

        Used by the SyncEngine for push operations (Frappe → device).
        Default implementation calls individual push methods.

        Args:
            config: Full config dict from ConfigCompiler

        Returns:
            {"status": "success" | "partial" | "error", "results": {...}, "errors": [...]}
        """
        results = {}
        errors = []

        push_methods = {
            "ip_addresses": self._push_ip_addresses,
            "dhcp_servers": self._push_dhcp_servers,
            "dns_static": self._push_dns_static,
            "routes": self._push_routes,
            "firewall_filter": self._push_firewall_filter,
            "firewall_nat": self._push_firewall_nat,
            "queues": self._push_queues,
        }

        for section, push_fn in push_methods.items():
            if section in config:
                try:
                    results[section] = push_fn(config[section])
                except Exception as e:
                    errors.append({"section": section, "error": str(e)})

        status = "success" if not errors else ("partial" if results else "error")
        return {"status": status, "results": results, "errors": errors}

    # Override these in subclasses for bulk push
    def _push_ip_addresses(self, items: list) -> dict:
        return {"skipped": True}

    def _push_dhcp_servers(self, items: list) -> dict:
        return {"skipped": True}

    def _push_dns_static(self, items: list) -> dict:
        return {"skipped": True}

    def _push_routes(self, items: list) -> dict:
        return {"skipped": True}

    def _push_firewall_filter(self, items: list) -> dict:
        return {"skipped": True}

    def _push_firewall_nat(self, items: list) -> dict:
        return {"skipped": True}

    def _push_queues(self, items: list) -> dict:
        return {"skipped": True}

    # ═══════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════

    def supports(self, feature: str) -> bool:
        """Check if this provider supports a given feature.

        Args:
            feature: Feature name e.g. "wifi", "vpn", "queues"
        """
        return feature in self.SUPPORTED_FEATURES

    def get_provider_info(self) -> Dict[str, Any]:
        """Return metadata about this provider."""
        return {
            "type": self.PROVIDER_TYPE,
            "version": self.PROVIDER_VERSION,
            "supported_features": list(self.SUPPORTED_FEATURES),
            "connected": self._connected,
            "box_name": self.box_name,
        }
