# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
LinuxProvider — BaseProvider implementation wrapping the existing BoxConnector.

This provider bridges the abstract BaseProvider interface to the existing
REST API-based BoxConnector that communicates with the Arrowz Engine
(FastAPI agent running on Linux boxes).

The Arrowz Engine manages: ip, nftables, dnsmasq, hostapd, tc, wg
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..base_provider import (
    BaseProvider,
    CommandError,
    ConnectionError,
    ProviderError,
)


class LinuxProvider(BaseProvider):
    """Linux box provider using the existing BoxConnector REST API.

    Wraps the BoxConnector methods to conform to the BaseProvider interface.
    The actual network management is performed by the Arrowz Engine agent
    running on the Linux box.
    """

    PROVIDER_TYPE = "linux"
    PROVIDER_VERSION = "1.0.0"
    SUPPORTED_FEATURES = (
        "interfaces",
        "ip_addresses",
        "dhcp",
        "dns",
        "routing",
        "firewall",
        "nat",
        "queues",
        "wifi",
        "vpn",
        "arp",
        "system",
        "clients",
        "hotspot",
    )

    def __init__(self, box_doc, settings=None):
        super().__init__(box_doc, settings)
        self._connector = None

    @property
    def connector(self):
        """Lazy-load BoxConnector."""
        if self._connector is None:
            from arrowz.arrowz_api.utils.box_connector import BoxConnector
            self._connector = BoxConnector(box_doc=self.box_doc)
        return self._connector

    # ═══════════════════════════════════════════════════════════════
    # CONNECTION LIFECYCLE
    # ═══════════════════════════════════════════════════════════════

    def connect(self) -> None:
        """Linux provider uses stateless REST — connection is implicit."""
        try:
            self.connector.health_check()
            self._connected = True
        except Exception as e:
            raise ConnectionError(f"Cannot reach Arrowz Engine on {self.box_doc.box_ip}: {e}") from e

    def disconnect(self) -> None:
        """REST is stateless — nothing to disconnect."""
        self._connected = False

    def test_connection(self) -> Dict[str, Any]:
        import time
        start = time.time()
        try:
            health = self.connector.health_check()
            elapsed = (time.time() - start) * 1000
            return {
                "status": "online",
                "message": "Engine is healthy",
                "response_time_ms": round(elapsed, 2),
                "device_info": health,
            }
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return {
                "status": "error",
                "message": str(e),
                "response_time_ms": round(elapsed, 2),
                "device_info": {},
            }

    # ═══════════════════════════════════════════════════════════════
    # SYSTEM INFORMATION
    # ═══════════════════════════════════════════════════════════════

    def get_system_info(self) -> Dict[str, Any]:
        try:
            telemetry = self.connector.get_telemetry()
            health = self.connector.health_check()
            return {
                "hostname": telemetry.get("hostname", ""),
                "model": telemetry.get("hardware", {}).get("model", "Linux Box"),
                "serial_number": telemetry.get("hardware", {}).get("serial", ""),
                "os_version": telemetry.get("os_version", ""),
                "firmware_version": health.get("version", ""),
                "architecture": telemetry.get("hardware", {}).get("architecture", ""),
                "uptime_seconds": telemetry.get("uptime_seconds", 0),
            }
        except Exception as e:
            raise CommandError(f"Failed to get system info: {e}", command="get_telemetry")

    def get_system_resources(self) -> Dict[str, Any]:
        try:
            telemetry = self.connector.get_telemetry()
            hw = telemetry.get("hardware", {})
            return {
                "cpu_usage_percent": hw.get("cpu_usage", 0),
                "cpu_cores": hw.get("cpu_cores", 1),
                "cpu_model": hw.get("cpu_model", ""),
                "ram_total_mb": hw.get("ram_total_mb", 0),
                "ram_used_mb": hw.get("ram_used_mb", 0),
                "ram_usage_percent": hw.get("ram_usage_percent", 0),
                "disk_total_mb": hw.get("disk_total_mb", 0),
                "disk_used_mb": hw.get("disk_used_mb", 0),
                "disk_usage_percent": hw.get("disk_usage_percent", 0),
                "uptime_seconds": telemetry.get("uptime_seconds", 0),
            }
        except Exception as e:
            raise CommandError(f"Failed to get resources: {e}", command="get_telemetry")

    def reboot(self) -> Dict[str, Any]:
        try:
            self.connector.restart_service("system")
            return {"status": "success", "message": "Reboot initiated"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ═══════════════════════════════════════════════════════════════
    # INTERFACES
    # ═══════════════════════════════════════════════════════════════

    def get_interfaces(self) -> List[Dict[str, Any]]:
        try:
            raw = self.connector.get_interfaces()
            # Normalize to canonical format
            result = []
            for iface in raw:
                result.append({
                    "id": iface.get("name", ""),
                    "name": iface.get("name", ""),
                    "type": iface.get("type", "ethernet"),
                    "mac_address": iface.get("mac_address", iface.get("mac", "")),
                    "status": iface.get("state", iface.get("status", "unknown")),
                    "speed": iface.get("speed", ""),
                    "mtu": iface.get("mtu", 1500),
                    "rx_bytes": iface.get("rx_bytes", 0),
                    "tx_bytes": iface.get("tx_bytes", 0),
                    "comment": "",
                })
            return result
        except Exception as e:
            raise CommandError(f"Failed to get interfaces: {e}", command="get_interfaces")

    def set_interface(self, interface_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Linux interface changes go through config push, not direct API."""
        raise ProviderError(
            "Direct interface modification not supported. Use config push instead.",
            layer="feature",
        )

    # ═══════════════════════════════════════════════════════════════
    # IP ADDRESSES
    # ═══════════════════════════════════════════════════════════════

    def get_ip_addresses(self) -> List[Dict[str, Any]]:
        interfaces = self.get_interfaces()
        # Extract IPs from interface data (Engine reports IPs per interface)
        result = []
        for iface in interfaces:
            for addr in iface.get("addresses", []):
                result.append({
                    "id": f"{iface['name']}-{addr}",
                    "address": addr,
                    "interface": iface["name"],
                    "network": "",
                    "enabled": iface["status"] == "up",
                    "comment": "",
                })
        return result

    def add_ip_address(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """IP changes go through config push."""
        raise ProviderError(
            "Direct IP address modification not supported. Use config push.",
            layer="feature",
        )

    def remove_ip_address(self, address_id: str) -> bool:
        raise ProviderError(
            "Direct IP address modification not supported. Use config push.",
            layer="feature",
        )

    # ═══════════════════════════════════════════════════════════════
    # DHCP
    # ═══════════════════════════════════════════════════════════════

    def get_dhcp_servers(self) -> List[Dict[str, Any]]:
        # Linux uses dnsmasq — config is compiled from DocTypes
        # Not directly queryable as separate servers
        return []

    def add_dhcp_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        raise ProviderError("DHCP is managed via config push (dnsmasq)", layer="feature")

    def update_dhcp_server(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        raise ProviderError("DHCP is managed via config push (dnsmasq)", layer="feature")

    def remove_dhcp_server(self, server_id: str) -> bool:
        raise ProviderError("DHCP is managed via config push (dnsmasq)", layer="feature")

    def get_dhcp_leases(self) -> List[Dict[str, Any]]:
        try:
            raw = self.connector.get_dhcp_leases()
            result = []
            for lease in raw:
                result.append({
                    "id": lease.get("mac_address", ""),
                    "address": lease.get("ip_address", lease.get("address", "")),
                    "mac_address": lease.get("mac_address", ""),
                    "hostname": lease.get("hostname", ""),
                    "server": "dnsmasq",
                    "status": "bound",
                    "expires_at": lease.get("expires", ""),
                    "is_static": lease.get("is_static", False),
                })
            return result
        except Exception as e:
            raise CommandError(f"Failed to get DHCP leases: {e}", command="get_dhcp_leases")

    def add_dhcp_static_lease(self, config: Dict[str, Any]) -> Dict[str, Any]:
        raise ProviderError("Static leases managed via config push", layer="feature")

    def remove_dhcp_static_lease(self, lease_id: str) -> bool:
        raise ProviderError("Static leases managed via config push", layer="feature")

    # ═══════════════════════════════════════════════════════════════
    # DNS
    # ═══════════════════════════════════════════════════════════════

    def get_dns_config(self) -> Dict[str, Any]:
        return {
            "servers": [],
            "allow_remote_requests": True,
            "cache_size_kb": 0,
            "cache_used_kb": 0,
        }

    def set_dns_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        raise ProviderError("DNS is managed via config push (dnsmasq)", layer="feature")

    def get_dns_static_entries(self) -> List[Dict[str, Any]]:
        return []

    def add_dns_static_entry(self, config: Dict[str, Any]) -> Dict[str, Any]:
        raise ProviderError("DNS entries managed via config push", layer="feature")

    def remove_dns_static_entry(self, entry_id: str) -> bool:
        raise ProviderError("DNS entries managed via config push", layer="feature")

    # ═══════════════════════════════════════════════════════════════
    # ROUTING
    # ═══════════════════════════════════════════════════════════════

    def get_routes(self) -> List[Dict[str, Any]]:
        try:
            raw = self.connector.get_routing_table()
            result = []
            for route in raw:
                result.append({
                    "id": f"{route.get('destination', '')}-{route.get('gateway', '')}",
                    "destination": route.get("destination", ""),
                    "gateway": route.get("gateway", route.get("via", "")),
                    "interface": route.get("interface", route.get("dev", "")),
                    "metric": route.get("metric", 0),
                    "type": route.get("type", "static"),
                    "enabled": True,
                    "comment": "",
                })
            return result
        except Exception as e:
            raise CommandError(f"Failed to get routes: {e}", command="get_routing_table")

    def add_route(self, config: Dict[str, Any]) -> Dict[str, Any]:
        raise ProviderError("Routes managed via config push", layer="feature")

    def remove_route(self, route_id: str) -> bool:
        raise ProviderError("Routes managed via config push", layer="feature")

    # ═══════════════════════════════════════════════════════════════
    # FIREWALL
    # ═══════════════════════════════════════════════════════════════

    def get_firewall_filter_rules(self) -> List[Dict[str, Any]]:
        # nftables rules are compiled from DocTypes and pushed
        return []

    def add_firewall_filter_rule(self, config: Dict[str, Any]) -> Dict[str, Any]:
        raise ProviderError("Firewall managed via config push (nftables)", layer="feature")

    def update_firewall_filter_rule(self, rule_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        raise ProviderError("Firewall managed via config push (nftables)", layer="feature")

    def remove_firewall_filter_rule(self, rule_id: str) -> bool:
        raise ProviderError("Firewall managed via config push (nftables)", layer="feature")

    def get_firewall_nat_rules(self) -> List[Dict[str, Any]]:
        return []

    def add_firewall_nat_rule(self, config: Dict[str, Any]) -> Dict[str, Any]:
        raise ProviderError("NAT managed via config push (nftables)", layer="feature")

    def remove_firewall_nat_rule(self, rule_id: str) -> bool:
        raise ProviderError("NAT managed via config push (nftables)", layer="feature")

    # ═══════════════════════════════════════════════════════════════
    # QUEUES / BANDWIDTH
    # ═══════════════════════════════════════════════════════════════

    def get_queues(self) -> List[Dict[str, Any]]:
        return []

    def add_queue(self, config: Dict[str, Any]) -> Dict[str, Any]:
        raise ProviderError("Queues managed via config push (tc)", layer="feature")

    def update_queue(self, queue_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        raise ProviderError("Queues managed via config push (tc)", layer="feature")

    def remove_queue(self, queue_id: str) -> bool:
        raise ProviderError("Queues managed via config push (tc)", layer="feature")

    # ═══════════════════════════════════════════════════════════════
    # WIRELESS / WIFI
    # ═══════════════════════════════════════════════════════════════

    def get_wireless_interfaces(self) -> List[Dict[str, Any]]:
        try:
            status = self.connector.get_wifi_status()
            return status.get("interfaces", [])
        except Exception:
            return []

    def get_wireless_clients(self) -> List[Dict[str, Any]]:
        try:
            return self.connector.get_wifi_clients()
        except Exception:
            return []

    # ═══════════════════════════════════════════════════════════════
    # VPN (WireGuard)
    # ═══════════════════════════════════════════════════════════════

    def get_vpn_interfaces(self) -> List[Dict[str, Any]]:
        """Get WireGuard interfaces from the Linux box via Engine API."""
        try:
            result = self.connector._request("GET", "/api/v1/vpn/interfaces")
            raw = result.get("interfaces", [])
        except Exception:
            return []

        interfaces = []
        for wg in raw:
            interfaces.append({
                "id": wg.get("name", wg.get("interface", "")),
                "name": wg.get("name", wg.get("interface", "")),
                "type": "wireguard",
                "listen_port": int(wg.get("listen_port", wg.get("listening_port", 0))),
                "public_key": wg.get("public_key", ""),
                "private_key": "***",
                "enabled": wg.get("enabled", True),
                "running": wg.get("running", wg.get("up", False)),
            })
        return interfaces

    def get_vpn_peers(self) -> List[Dict[str, Any]]:
        """Get WireGuard peers with handshake and transfer stats."""
        try:
            raw = self.connector.get_vpn_peers()
        except Exception:
            return []

        peers = []
        for peer in raw:
            peers.append({
                "id": peer.get("public_key", peer.get("id", "")),
                "interface": peer.get("interface", ""),
                "public_key": peer.get("public_key", ""),
                "endpoint": peer.get("endpoint", ""),
                "allowed_address": peer.get("allowed_ips", peer.get("allowed_address", "")),
                "last_handshake": peer.get("last_handshake", peer.get("latest_handshake", "")),
                "rx_bytes": int(peer.get("rx_bytes", peer.get("transfer_rx", 0))),
                "tx_bytes": int(peer.get("tx_bytes", peer.get("transfer_tx", 0))),
                "enabled": peer.get("enabled", True),
                "comment": peer.get("comment", peer.get("name", "")),
            })
        return peers

    def add_vpn_peer(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Add a WireGuard peer via the Engine API."""
        payload = {
            "interface": config.get("interface", "wg0"),
            "public_key": config["public_key"],
            "allowed_ips": config.get("allowed_address", config.get("allowed_ips", "0.0.0.0/0")),
        }
        if config.get("endpoint"):
            payload["endpoint"] = config["endpoint"]
        if config.get("preshared_key"):
            payload["preshared_key"] = config["preshared_key"]
        if config.get("persistent_keepalive"):
            payload["persistent_keepalive"] = config["persistent_keepalive"]
        if config.get("comment"):
            payload["comment"] = config["comment"]

        try:
            result = self.connector._request("POST", "/api/v1/vpn/peers", payload)
            return {"id": result.get("id", config["public_key"]), **config}
        except Exception as e:
            raise CommandError(f"Failed to add VPN peer: {e}", command="add_vpn_peer")

    def remove_vpn_peer(self, peer_id: str) -> bool:
        """Remove a WireGuard peer via the Engine API."""
        try:
            self.connector._request("DELETE", f"/api/v1/vpn/peers/{peer_id}")
            return True
        except Exception as e:
            raise CommandError(f"Failed to remove VPN peer: {e}", command="remove_vpn_peer")

    # ═══════════════════════════════════════════════════════════════
    # ARP TABLE
    # ═══════════════════════════════════════════════════════════════

    def get_arp_table(self) -> List[Dict[str, Any]]:
        try:
            raw = self.connector.get_arp_table()
            result = []
            for entry in raw:
                result.append({
                    "id": f"{entry.get('ip_address', '')}-{entry.get('mac_address', '')}",
                    "address": entry.get("ip_address", entry.get("address", "")),
                    "mac_address": entry.get("mac_address", ""),
                    "interface": entry.get("interface", entry.get("device", "")),
                    "status": entry.get("state", "reachable"),
                })
            return result
        except Exception as e:
            raise CommandError(f"Failed to get ARP table: {e}", command="get_arp_table")

    # ═══════════════════════════════════════════════════════════════
    # FULL CONFIG (for sync)
    # ═══════════════════════════════════════════════════════════════

    def get_full_config(self) -> Dict[str, Any]:
        """Pull available config from the Linux box."""
        config = {
            "system": {},
            "interfaces": [],
            "ip_addresses": [],
            "dhcp_servers": [],
            "dhcp_leases": [],
            "dns": {},
            "dns_static": [],
            "routes": [],
            "firewall_filter": [],
            "firewall_nat": [],
            "queues": [],
            "wireless": [],
            "vpn_interfaces": [],
            "vpn_peers": [],
            "arp": [],
        }

        getters = {
            "system": self.get_system_info,
            "interfaces": self.get_interfaces,
            "dhcp_leases": self.get_dhcp_leases,
            "routes": self.get_routes,
            "wireless": self.get_wireless_interfaces,
            "vpn_interfaces": self.get_vpn_interfaces,
            "vpn_peers": self.get_vpn_peers,
            "arp": self.get_arp_table,
        }

        errors = []
        for section, getter in getters.items():
            try:
                config[section] = getter()
            except Exception as e:
                errors.append(f"{section}: {e}")

        if errors:
            config["_sync_errors"] = errors

        return config

    def push_full_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Push config through BoxConnector's REST API.

        The Linux provider routes full pushes through the existing
        BoxConnector push_config() method which calls the Engine.
        """
        try:
            result = self.connector.push_config(config)
            return {"status": "success", "results": result, "errors": []}
        except Exception as e:
            return {"status": "error", "results": {}, "errors": [str(e)]}
