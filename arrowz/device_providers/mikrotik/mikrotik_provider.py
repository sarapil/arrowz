# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
MikroTikProvider — BaseProvider implementation for MikroTik RouterOS devices.

Maps every BaseProvider abstract method to RouterOS API calls via RouterOSClient.
Data is translated between Arrowz canonical format and RouterOS format inline.

Supported features:
  - System info & resources
  - Interfaces (ethernet, bridge, vlan, bonding)
  - IP addresses
  - DHCP servers, leases, static leases, pools
  - DNS resolver + static entries
  - Routing
  - Firewall filter + NAT
  - Simple queues (bandwidth)
  - Wireless (WiFi)
  - VPN (WireGuard)
  - ARP table
  - Full config pull/push for sync
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ..base_provider import (
    BaseProvider,
    CommandError,
    ConnectionError,
    ProviderError,
    SyncError,
)
from .routeros_client import RouterOSClient


def _ros_bool(value: str) -> bool:
    """Convert RouterOS boolean string to Python bool."""
    return str(value).lower() in ("true", "yes")


def _ros_int(value: str, default: int = 0) -> int:
    """Convert RouterOS string to int, handling empty/missing values."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _parse_uptime(uptime_str: str) -> int:
    """Parse RouterOS uptime string to seconds.

    Examples: "3d5h2m10s", "5h30m", "45s", "1w2d3h4m5s"
    """
    if not uptime_str:
        return 0

    total = 0
    pattern = re.compile(r"(\d+)([wdhms])")
    multipliers = {"w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}

    for match in pattern.finditer(uptime_str):
        value, unit = match.groups()
        total += int(value) * multipliers.get(unit, 0)

    return total


def _parse_rate(rate_str: str) -> int:
    """Parse RouterOS rate string to bits per second.

    Examples: "10M", "100k", "1G", "512000"
    """
    if not rate_str:
        return 0

    rate_str = str(rate_str).strip()

    multipliers = {"k": 1_000, "M": 1_000_000, "G": 1_000_000_000}
    for suffix, mult in multipliers.items():
        if rate_str.endswith(suffix):
            try:
                return int(float(rate_str[:-1]) * mult)
            except ValueError:
                return 0

    try:
        return int(rate_str)
    except ValueError:
        return 0


class MikroTikProvider(BaseProvider):
    """MikroTik RouterOS device provider.

    Communicates with MikroTik routers via the RouterOS API
    (librouteros). Supports all standard Arrowz network operations.
    """

    PROVIDER_TYPE = "mikrotik"
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
        "reboot",
    )

    def __init__(self, box_doc, settings=None):
        super().__init__(box_doc, settings)
        self._client: Optional[RouterOSClient] = None

    @property
    def client(self) -> RouterOSClient:
        if self._client is None:
            self._client = RouterOSClient.from_box_doc(self.box_doc)
        return self._client

    # ═══════════════════════════════════════════════════════════════
    # CONNECTION LIFECYCLE
    # ═══════════════════════════════════════════════════════════════

    def connect(self) -> None:
        self.client.connect()
        self._connected = True

    def disconnect(self) -> None:
        if self._client:
            self._client.disconnect()
        self._connected = False

    def test_connection(self) -> Dict[str, Any]:
        import time
        start = time.time()
        try:
            if not self._connected:
                self.connect()

            identity = self.client.get_identity()
            elapsed = (time.time() - start) * 1000

            return {
                "status": "online",
                "message": f"Connected to {identity}",
                "response_time_ms": round(elapsed, 2),
                "device_info": {
                    "identity": identity,
                    "provider": self.PROVIDER_TYPE,
                },
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
        resource = self.client.get_resource()
        identity = self.client.get_identity()
        routerboard = self.client.get_routerboard()

        return {
            "hostname": identity,
            "model": routerboard.get("model", resource.get("board-name", "")),
            "serial_number": routerboard.get("serial-number", ""),
            "os_version": resource.get("version", ""),
            "firmware_version": routerboard.get("current-firmware", ""),
            "architecture": resource.get("architecture-name", ""),
            "uptime_seconds": _parse_uptime(resource.get("uptime", "")),
            "board_name": resource.get("board-name", ""),
            "platform": resource.get("platform", ""),
            "routeros_version": resource.get("version", ""),
        }

    def get_system_resources(self) -> Dict[str, Any]:
        r = self.client.get_resource()

        total_ram = _ros_int(r.get("total-memory", "0"))
        free_ram = _ros_int(r.get("free-memory", "0"))
        used_ram = total_ram - free_ram
        total_disk = _ros_int(r.get("total-hdd-space", "0"))
        free_disk = _ros_int(r.get("free-hdd-space", "0"))
        used_disk = total_disk - free_disk

        return {
            "cpu_usage_percent": _ros_int(r.get("cpu-load", "0")),
            "cpu_cores": _ros_int(r.get("cpu-count", "1")),
            "cpu_model": r.get("cpu", ""),
            "ram_total_mb": total_ram // (1024 * 1024) if total_ram else 0,
            "ram_used_mb": used_ram // (1024 * 1024) if used_ram else 0,
            "ram_usage_percent": round(used_ram / total_ram * 100, 1) if total_ram else 0,
            "disk_total_mb": total_disk // (1024 * 1024) if total_disk else 0,
            "disk_used_mb": used_disk // (1024 * 1024) if used_disk else 0,
            "disk_usage_percent": round(used_disk / total_disk * 100, 1) if total_disk else 0,
            "uptime_seconds": _parse_uptime(r.get("uptime", "")),
        }

    def reboot(self) -> Dict[str, Any]:
        try:
            self.client.command("system", "reboot")
            return {"status": "success", "message": "Reboot initiated"}
        except Exception as e:
            # RouterOS may close connection immediately on reboot
            if "connection closed" in str(e).lower():
                return {"status": "success", "message": "Reboot initiated (connection closed)"}
            return {"status": "error", "message": str(e)}

    # ═══════════════════════════════════════════════════════════════
    # INTERFACES
    # ═══════════════════════════════════════════════════════════════

    def get_interfaces(self) -> List[Dict[str, Any]]:
        raw = self.client.print("interface")
        result = []
        for iface in raw:
            result.append({
                "id": iface.get(".id", ""),
                "name": iface.get("name", ""),
                "type": iface.get("type", ""),
                "mac_address": iface.get("mac-address", ""),
                "status": "up" if _ros_bool(iface.get("running", "false")) else "down",
                "disabled": _ros_bool(iface.get("disabled", "false")),
                "speed": iface.get("speed", ""),
                "mtu": _ros_int(iface.get("mtu", "1500")),
                "actual_mtu": _ros_int(iface.get("actual-mtu", "0")),
                "rx_bytes": _ros_int(iface.get("rx-byte", "0")),
                "tx_bytes": _ros_int(iface.get("tx-byte", "0")),
                "comment": iface.get("comment", ""),
                "default_name": iface.get("default-name", ""),
            })
        return result

    def set_interface(self, interface_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        self.client.set("interface", id=interface_id, **config)
        # Fetch updated state
        all_ifaces = self.get_interfaces()
        return next((i for i in all_ifaces if i["id"] == interface_id), {})

    # ═══════════════════════════════════════════════════════════════
    # IP ADDRESSES
    # ═══════════════════════════════════════════════════════════════

    def get_ip_addresses(self) -> List[Dict[str, Any]]:
        raw = self.client.print("ip", "address")
        result = []
        for addr in raw:
            result.append({
                "id": addr.get(".id", ""),
                "address": addr.get("address", ""),
                "interface": addr.get("interface", ""),
                "network": addr.get("network", ""),
                "enabled": not _ros_bool(addr.get("disabled", "false")),
                "actual_interface": addr.get("actual-interface", ""),
                "comment": addr.get("comment", ""),
            })
        return result

    def add_ip_address(self, config: Dict[str, Any]) -> Dict[str, Any]:
        new_id = self.client.add(
            "ip", "address",
            address=config["address"],
            interface=config["interface"],
            comment=config.get("comment", ""),
            disabled=config.get("disabled", False),
        )
        return {"id": new_id, **config}

    def remove_ip_address(self, address_id: str) -> bool:
        self.client.remove("ip", "address", id=address_id)
        return True

    # ═══════════════════════════════════════════════════════════════
    # DHCP
    # ═══════════════════════════════════════════════════════════════

    def get_dhcp_servers(self) -> List[Dict[str, Any]]:
        servers = self.client.print("ip", "dhcp-server")
        networks = self.client.print("ip", "dhcp-server", "network")
        pools = self.client.print("ip", "pool")

        # Build lookup maps
        pool_map = {p.get("name", ""): p for p in pools}
        net_map = {}
        for n in networks:
            # Networks don't have a direct 1:1 key to servers,
            # but we match by gateway/address overlap
            net_map[n.get(".id", "")] = n

        result = []
        for srv in servers:
            pool_name = srv.get("address-pool", "")
            pool_info = pool_map.get(pool_name, {})
            # Find matching network entry
            srv_network = {}
            for n in networks:
                # Match by checking if the network's gateway interface matches
                srv_network = n  # simplified — first match
                break

            result.append({
                "id": srv.get(".id", ""),
                "name": srv.get("name", ""),
                "interface": srv.get("interface", ""),
                "pool_name": pool_name,
                "pool_ranges": pool_info.get("ranges", ""),
                "network": srv_network.get("address", ""),
                "gateway": srv_network.get("gateway", ""),
                "dns_servers": srv_network.get("dns-server", "").split(",") if srv_network.get("dns-server") else [],
                "lease_time": srv.get("lease-time", ""),
                "enabled": not _ros_bool(srv.get("disabled", "false")),
                "authoritative": srv.get("authoritative", ""),
            })
        return result

    def add_dhcp_server(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Step 1: Create IP pool
        pool_name = config.get("pool_name", f"pool-{config['interface']}")
        pool_ranges = config.get("pool_ranges", "")
        if pool_ranges:
            self.client.add("ip", "pool", name=pool_name, ranges=pool_ranges)

        # Step 2: Create DHCP network
        if config.get("network"):
            net_kwargs = {
                "address": config["network"],
                "gateway": config.get("gateway", ""),
            }
            if config.get("dns_servers"):
                net_kwargs["dns_server"] = ",".join(config["dns_servers"])
            if config.get("domain"):
                net_kwargs["domain"] = config["domain"]
            self.client.add("ip", "dhcp-server", "network", **net_kwargs)

        # Step 3: Create DHCP server
        srv_id = self.client.add(
            "ip", "dhcp-server",
            name=config.get("name", f"dhcp-{config['interface']}"),
            interface=config["interface"],
            address_pool=pool_name,
            lease_time=config.get("lease_time", "10m"),
            disabled=config.get("disabled", False),
        )

        return {"id": srv_id, **config}

    def update_dhcp_server(self, server_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        update = {}
        if "lease_time" in config:
            update["lease_time"] = config["lease_time"]
        if "disabled" in config:
            update["disabled"] = config["disabled"]
        if "address_pool" in config:
            update["address_pool"] = config["address_pool"]

        if update:
            self.client.set("ip", "dhcp-server", id=server_id, **update)

        return {"id": server_id, **config}

    def remove_dhcp_server(self, server_id: str) -> bool:
        self.client.remove("ip", "dhcp-server", id=server_id)
        return True

    def get_dhcp_leases(self) -> List[Dict[str, Any]]:
        raw = self.client.print("ip", "dhcp-server", "lease")
        result = []
        for lease in raw:
            result.append({
                "id": lease.get(".id", ""),
                "address": lease.get("address", ""),
                "mac_address": lease.get("mac-address", ""),
                "hostname": lease.get("host-name", ""),
                "server": lease.get("server", ""),
                "status": lease.get("status", ""),
                "expires_at": lease.get("expires-after", ""),
                "is_static": not _ros_bool(lease.get("dynamic", "false")),
                "active_address": lease.get("active-address", ""),
                "active_mac": lease.get("active-mac-address", ""),
                "comment": lease.get("comment", ""),
                "disabled": _ros_bool(lease.get("disabled", "false")),
            })
        return result

    def add_dhcp_static_lease(self, config: Dict[str, Any]) -> Dict[str, Any]:
        new_id = self.client.add(
            "ip", "dhcp-server", "lease",
            mac_address=config["mac_address"],
            address=config.get("address", ""),
            server=config.get("server", "all"),
            comment=config.get("comment", ""),
        )
        return {"id": new_id, **config}

    def remove_dhcp_static_lease(self, lease_id: str) -> bool:
        self.client.remove("ip", "dhcp-server", "lease", id=lease_id)
        return True

    # ═══════════════════════════════════════════════════════════════
    # DNS
    # ═══════════════════════════════════════════════════════════════

    def get_dns_config(self) -> Dict[str, Any]:
        raw = self.client.print("ip", "dns")
        if not raw:
            return {}

        dns = raw[0]
        return {
            "servers": dns.get("servers", "").split(",") if dns.get("servers") else [],
            "allow_remote_requests": _ros_bool(dns.get("allow-remote-requests", "false")),
            "cache_size_kb": _ros_int(dns.get("cache-size", "2048")) // 1024,
            "cache_used_kb": _ros_int(dns.get("cache-used", "0")) // 1024,
            "max_udp_packet_size": _ros_int(dns.get("max-udp-packet-size", "4096")),
        }

    def set_dns_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        update = {}
        if "servers" in config:
            update["servers"] = ",".join(config["servers"]) if isinstance(config["servers"], list) else config["servers"]
        if "allow_remote_requests" in config:
            update["allow_remote_requests"] = config["allow_remote_requests"]
        if "cache_size_kb" in config:
            update["cache_size"] = config["cache_size_kb"] * 1024

        # DNS config is a singleton — use set without id
        if update:
            raw = self.client.print("ip", "dns")
            if raw:
                self.client.set("ip", "dns", id=raw[0].get(".id", ""), **update)

        return self.get_dns_config()

    def get_dns_static_entries(self) -> List[Dict[str, Any]]:
        raw = self.client.print("ip", "dns", "static")
        result = []
        for entry in raw:
            result.append({
                "id": entry.get(".id", ""),
                "name": entry.get("name", ""),
                "address": entry.get("address", ""),
                "type": entry.get("type", "A"),
                "ttl": entry.get("ttl", ""),
                "enabled": not _ros_bool(entry.get("disabled", "false")),
                "comment": entry.get("comment", ""),
            })
        return result

    def add_dns_static_entry(self, config: Dict[str, Any]) -> Dict[str, Any]:
        new_id = self.client.add(
            "ip", "dns", "static",
            name=config["name"],
            address=config.get("address", ""),
            type=config.get("type", "A"),
            ttl=config.get("ttl", "1d"),
            comment=config.get("comment", ""),
            disabled=config.get("disabled", False),
        )
        return {"id": new_id, **config}

    def remove_dns_static_entry(self, entry_id: str) -> bool:
        self.client.remove("ip", "dns", "static", id=entry_id)
        return True

    # ═══════════════════════════════════════════════════════════════
    # ROUTING
    # ═══════════════════════════════════════════════════════════════

    def get_routes(self) -> List[Dict[str, Any]]:
        raw = self.client.print("ip", "route")
        result = []
        for route in raw:
            route_type = "static"
            if _ros_bool(route.get("dynamic", "false")):
                route_type = "dynamic"
            elif _ros_bool(route.get("connect", "false")):
                route_type = "connected"

            result.append({
                "id": route.get(".id", ""),
                "destination": route.get("dst-address", ""),
                "gateway": route.get("gateway", ""),
                "interface": route.get("gateway", ""),  # gateway can be interface name
                "metric": _ros_int(route.get("distance", "0")),
                "type": route_type,
                "enabled": not _ros_bool(route.get("disabled", "false")),
                "active": _ros_bool(route.get("active", "false")),
                "routing_table": route.get("routing-table", "main"),
                "comment": route.get("comment", ""),
            })
        return result

    def add_route(self, config: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = {
            "dst_address": config["destination"],
            "gateway": config.get("gateway", ""),
            "distance": config.get("metric", 1),
            "comment": config.get("comment", ""),
            "disabled": config.get("disabled", False),
        }
        if config.get("routing_table"):
            kwargs["routing_table"] = config["routing_table"]

        new_id = self.client.add("ip", "route", **kwargs)
        return {"id": new_id, **config}

    def remove_route(self, route_id: str) -> bool:
        self.client.remove("ip", "route", id=route_id)
        return True

    # ═══════════════════════════════════════════════════════════════
    # FIREWALL
    # ═══════════════════════════════════════════════════════════════

    def get_firewall_filter_rules(self) -> List[Dict[str, Any]]:
        raw = self.client.print("ip", "firewall", "filter")
        result = []
        for idx, rule in enumerate(raw):
            result.append({
                "id": rule.get(".id", ""),
                "chain": rule.get("chain", ""),
                "action": rule.get("action", ""),
                "protocol": rule.get("protocol", ""),
                "src_address": rule.get("src-address", ""),
                "dst_address": rule.get("dst-address", ""),
                "src_port": rule.get("src-port", ""),
                "dst_port": rule.get("dst-port", ""),
                "in_interface": rule.get("in-interface", ""),
                "out_interface": rule.get("out-interface", ""),
                "in_interface_list": rule.get("in-interface-list", ""),
                "out_interface_list": rule.get("out-interface-list", ""),
                "connection_state": rule.get("connection-state", ""),
                "comment": rule.get("comment", ""),
                "enabled": not _ros_bool(rule.get("disabled", "false")),
                "position": idx,
                "bytes": _ros_int(rule.get("bytes", "0")),
                "packets": _ros_int(rule.get("packets", "0")),
                "log": _ros_bool(rule.get("log", "false")),
                "log_prefix": rule.get("log-prefix", ""),
            })
        return result

    def add_firewall_filter_rule(self, config: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = {}
        field_map = {
            "chain": "chain",
            "action": "action",
            "protocol": "protocol",
            "src_address": "src_address",
            "dst_address": "dst_address",
            "src_port": "src_port",
            "dst_port": "dst_port",
            "in_interface": "in_interface",
            "out_interface": "out_interface",
            "in_interface_list": "in_interface_list",
            "out_interface_list": "out_interface_list",
            "connection_state": "connection_state",
            "comment": "comment",
            "disabled": "disabled",
            "log": "log",
            "log_prefix": "log_prefix",
        }
        for arrowz_key, ros_key in field_map.items():
            if arrowz_key in config and config[arrowz_key]:
                kwargs[ros_key] = config[arrowz_key]

        # Place-before for ordering
        if "place_before" in config:
            kwargs["place_before"] = config["place_before"]

        new_id = self.client.add("ip", "firewall", "filter", **kwargs)
        return {"id": new_id, **config}

    def update_firewall_filter_rule(self, rule_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        self.client.set("ip", "firewall", "filter", id=rule_id, **config)
        return {"id": rule_id, **config}

    def remove_firewall_filter_rule(self, rule_id: str) -> bool:
        self.client.remove("ip", "firewall", "filter", id=rule_id)
        return True

    def get_firewall_nat_rules(self) -> List[Dict[str, Any]]:
        raw = self.client.print("ip", "firewall", "nat")
        result = []
        for idx, rule in enumerate(raw):
            result.append({
                "id": rule.get(".id", ""),
                "chain": rule.get("chain", ""),
                "action": rule.get("action", ""),
                "protocol": rule.get("protocol", ""),
                "src_address": rule.get("src-address", ""),
                "dst_address": rule.get("dst-address", ""),
                "src_port": rule.get("src-port", ""),
                "dst_port": rule.get("dst-port", ""),
                "to_addresses": rule.get("to-addresses", ""),
                "to_ports": rule.get("to-ports", ""),
                "in_interface": rule.get("in-interface", ""),
                "out_interface": rule.get("out-interface", ""),
                "in_interface_list": rule.get("in-interface-list", ""),
                "out_interface_list": rule.get("out-interface-list", ""),
                "comment": rule.get("comment", ""),
                "enabled": not _ros_bool(rule.get("disabled", "false")),
                "position": idx,
                "bytes": _ros_int(rule.get("bytes", "0")),
                "packets": _ros_int(rule.get("packets", "0")),
                "log": _ros_bool(rule.get("log", "false")),
            })
        return result

    def add_firewall_nat_rule(self, config: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = {}
        for key in ("chain", "action", "protocol", "src_address", "dst_address",
                     "src_port", "dst_port", "to_addresses", "to_ports",
                     "in_interface", "out_interface", "in_interface_list",
                     "out_interface_list", "comment", "disabled", "log"):
            if key in config and config[key]:
                kwargs[key] = config[key]

        new_id = self.client.add("ip", "firewall", "nat", **kwargs)
        return {"id": new_id, **config}

    def remove_firewall_nat_rule(self, rule_id: str) -> bool:
        self.client.remove("ip", "firewall", "nat", id=rule_id)
        return True

    # ═══════════════════════════════════════════════════════════════
    # QUEUES / BANDWIDTH
    # ═══════════════════════════════════════════════════════════════

    def get_queues(self) -> List[Dict[str, Any]]:
        raw = self.client.print("queue", "simple")
        result = []
        for q in raw:
            # max-limit format: "upload/download" e.g. "5M/10M"
            max_limit = q.get("max-limit", "0/0")
            burst_limit = q.get("burst-limit", "0/0")
            burst_threshold = q.get("burst-threshold", "0/0")
            burst_time = q.get("burst-time", "0s/0s")

            ul_max, dl_max = self._parse_rate_pair(max_limit)
            ul_burst, dl_burst = self._parse_rate_pair(burst_limit)
            ul_burst_th, dl_burst_th = self._parse_rate_pair(burst_threshold)
            ul_burst_t, dl_burst_t = self._parse_time_pair(burst_time)

            result.append({
                "id": q.get(".id", ""),
                "name": q.get("name", ""),
                "target": q.get("target", ""),
                "max_download": dl_max,
                "max_upload": ul_max,
                "burst_download": dl_burst,
                "burst_upload": ul_burst,
                "burst_threshold_dl": dl_burst_th,
                "burst_threshold_ul": ul_burst_th,
                "burst_time_dl": dl_burst_t,
                "burst_time_ul": ul_burst_t,
                "priority": _ros_int(q.get("priority", "8")),
                "enabled": not _ros_bool(q.get("disabled", "false")),
                "comment": q.get("comment", ""),
                "bytes_in": _ros_int(q.get("bytes", "0").split("/")[1] if "/" in q.get("bytes", "") else q.get("bytes", "0")),
                "bytes_out": _ros_int(q.get("bytes", "0").split("/")[0] if "/" in q.get("bytes", "") else "0"),
                "parent": q.get("parent", ""),
            })
        return result

    def add_queue(self, config: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = {
            "name": config.get("name", ""),
            "target": config.get("target", ""),
            "comment": config.get("comment", ""),
            "disabled": config.get("disabled", False),
        }

        # Build max-limit as "upload/download"
        ul = config.get("max_upload", "0")
        dl = config.get("max_download", "0")
        kwargs["max_limit"] = f"{ul}/{dl}"

        if config.get("burst_upload") or config.get("burst_download"):
            bul = config.get("burst_upload", "0")
            bdl = config.get("burst_download", "0")
            kwargs["burst_limit"] = f"{bul}/{bdl}"

        if config.get("burst_threshold_ul") or config.get("burst_threshold_dl"):
            btul = config.get("burst_threshold_ul", "0")
            btdl = config.get("burst_threshold_dl", "0")
            kwargs["burst_threshold"] = f"{btul}/{btdl}"

        if config.get("priority"):
            kwargs["priority"] = config["priority"]

        if config.get("parent"):
            kwargs["parent"] = config["parent"]

        new_id = self.client.add("queue", "simple", **kwargs)
        return {"id": new_id, **config}

    def update_queue(self, queue_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = {}
        if "name" in config:
            kwargs["name"] = config["name"]
        if "target" in config:
            kwargs["target"] = config["target"]
        if "max_upload" in config or "max_download" in config:
            ul = config.get("max_upload", "0")
            dl = config.get("max_download", "0")
            kwargs["max_limit"] = f"{ul}/{dl}"
        if "comment" in config:
            kwargs["comment"] = config["comment"]
        if "disabled" in config:
            kwargs["disabled"] = config["disabled"]

        if kwargs:
            self.client.set("queue", "simple", id=queue_id, **kwargs)

        return {"id": queue_id, **config}

    def remove_queue(self, queue_id: str) -> bool:
        self.client.remove("queue", "simple", id=queue_id)
        return True

    # ═══════════════════════════════════════════════════════════════
    # WIRELESS / WIFI
    # ═══════════════════════════════════════════════════════════════

    def get_wireless_interfaces(self) -> List[Dict[str, Any]]:
        # Try WiFi Wave2 first (RouterOS 7+), fall back to legacy wireless
        try:
            return self._get_wifi_v7()
        except (CommandError, ProviderError):
            pass

        try:
            return self._get_wifi_v6()
        except (CommandError, ProviderError):
            pass

        return []

    def _get_wifi_v7(self) -> List[Dict[str, Any]]:
        """Get WiFi interfaces using RouterOS 7 WiFi Wave2 API."""
        raw = self.client.print("interface", "wifi")
        result = []
        for w in raw:
            result.append({
                "id": w.get(".id", ""),
                "name": w.get("name", ""),
                "ssid": w.get("configuration.ssid", w.get("ssid", "")),
                "band": w.get("configuration.band", ""),
                "channel": w.get("configuration.channel", ""),
                "frequency": _ros_int(w.get("configuration.frequency", "0")),
                "security_profile": w.get("security", ""),
                "mode": w.get("configuration.mode", "ap"),
                "enabled": not _ros_bool(w.get("disabled", "false")),
                "running": _ros_bool(w.get("running", "false")),
                "mac_address": w.get("mac-address", ""),
                "connected_clients": _ros_int(w.get("registered-peers", "0")),
            })
        return result

    def _get_wifi_v6(self) -> List[Dict[str, Any]]:
        """Get wireless interfaces using legacy wireless API (RouterOS 6)."""
        raw = self.client.print("interface", "wireless")
        result = []
        for w in raw:
            result.append({
                "id": w.get(".id", ""),
                "name": w.get("name", ""),
                "ssid": w.get("ssid", ""),
                "band": w.get("band", ""),
                "channel": w.get("channel-width", ""),
                "frequency": _ros_int(w.get("frequency", "0")),
                "security_profile": w.get("security-profile", ""),
                "mode": w.get("mode", "ap-bridge"),
                "enabled": not _ros_bool(w.get("disabled", "false")),
                "running": _ros_bool(w.get("running", "false")),
                "mac_address": w.get("mac-address", ""),
                "connected_clients": 0,  # Need registration-table for this
            })
        return result

    def set_wireless_interface(self, iface_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        # Try v7 first, then v6
        try:
            self.client.set("interface", "wifi", id=iface_id, **config)
        except CommandError:
            self.client.set("interface", "wireless", id=iface_id, **config)

        return {"id": iface_id, **config}

    def get_wireless_clients(self) -> List[Dict[str, Any]]:
        """Get connected wireless clients from registration table."""
        result = []

        # Try v7
        try:
            raw = self.client.print("interface", "wifi", "registration-table")
            for c in raw:
                result.append({
                    "mac_address": c.get("mac-address", ""),
                    "interface": c.get("interface", ""),
                    "signal_strength": _ros_int(c.get("signal", "0")),
                    "tx_rate": c.get("tx-rate", ""),
                    "rx_rate": c.get("rx-rate", ""),
                    "uptime": c.get("uptime", ""),
                    "bytes_in": _ros_int(c.get("bytes", "0").split(",")[0] if "," in c.get("bytes", "") else "0"),
                    "bytes_out": _ros_int(c.get("bytes", "0").split(",")[1] if "," in c.get("bytes", "") else "0"),
                })
            return result
        except CommandError:
            pass

        # Try v6
        try:
            raw = self.client.print("interface", "wireless", "registration-table")
            for c in raw:
                result.append({
                    "mac_address": c.get("mac-address", ""),
                    "interface": c.get("interface", ""),
                    "signal_strength": _ros_int(c.get("signal-strength", "0")),
                    "tx_rate": c.get("tx-rate", ""),
                    "rx_rate": c.get("rx-rate", ""),
                    "uptime": c.get("uptime", ""),
                    "bytes_in": _ros_int(c.get("bytes", "0")),
                    "bytes_out": 0,
                })
        except CommandError:
            pass

        return result

    # ═══════════════════════════════════════════════════════════════
    # VPN (WireGuard)
    # ═══════════════════════════════════════════════════════════════

    def get_vpn_interfaces(self) -> List[Dict[str, Any]]:
        try:
            raw = self.client.print("interface", "wireguard")
        except CommandError:
            return []

        result = []
        for wg in raw:
            result.append({
                "id": wg.get(".id", ""),
                "name": wg.get("name", ""),
                "type": "wireguard",
                "listen_port": _ros_int(wg.get("listen-port", "0")),
                "public_key": wg.get("public-key", ""),
                "private_key": "***",  # redacted
                "mtu": _ros_int(wg.get("mtu", "1420")),
                "enabled": not _ros_bool(wg.get("disabled", "false")),
                "running": _ros_bool(wg.get("running", "false")),
            })
        return result

    def get_vpn_peers(self) -> List[Dict[str, Any]]:
        try:
            raw = self.client.print("interface", "wireguard", "peers")
        except CommandError:
            return []

        result = []
        for peer in raw:
            result.append({
                "id": peer.get(".id", ""),
                "interface": peer.get("interface", ""),
                "public_key": peer.get("public-key", ""),
                "endpoint": f"{peer.get('endpoint-address', '')}:{peer.get('endpoint-port', '')}",
                "allowed_address": peer.get("allowed-address", ""),
                "preshared_key": "***" if peer.get("preshared-key") else "",
                "persistent_keepalive": peer.get("persistent-keepalive", ""),
                "last_handshake": peer.get("last-handshake", ""),
                "rx_bytes": _ros_int(peer.get("rx", "0")),
                "tx_bytes": _ros_int(peer.get("tx", "0")),
                "enabled": not _ros_bool(peer.get("disabled", "false")),
                "comment": peer.get("comment", ""),
            })
        return result

    def add_vpn_peer(self, config: Dict[str, Any]) -> Dict[str, Any]:
        kwargs = {
            "interface": config["interface"],
            "public_key": config["public_key"],
            "allowed_address": config.get("allowed_address", "0.0.0.0/0"),
            "comment": config.get("comment", ""),
            "disabled": config.get("disabled", False),
        }
        if config.get("endpoint"):
            parts = config["endpoint"].rsplit(":", 1)
            kwargs["endpoint_address"] = parts[0]
            if len(parts) > 1:
                kwargs["endpoint_port"] = parts[1]

        if config.get("preshared_key"):
            kwargs["preshared_key"] = config["preshared_key"]
        if config.get("persistent_keepalive"):
            kwargs["persistent_keepalive"] = config["persistent_keepalive"]

        new_id = self.client.add("interface", "wireguard", "peers", **kwargs)
        return {"id": new_id, **config}

    def remove_vpn_peer(self, peer_id: str) -> bool:
        self.client.remove("interface", "wireguard", "peers", id=peer_id)
        return True

    # ═══════════════════════════════════════════════════════════════
    # ARP TABLE
    # ═══════════════════════════════════════════════════════════════

    def get_arp_table(self) -> List[Dict[str, Any]]:
        raw = self.client.print("ip", "arp")
        result = []
        for entry in raw:
            status = "reachable"
            if _ros_bool(entry.get("dynamic", "false")):
                status = "dynamic"
            if _ros_bool(entry.get("complete", "false")):
                status = "reachable"
            if entry.get("mac-address", "") == "":
                status = "incomplete"

            result.append({
                "id": entry.get(".id", ""),
                "address": entry.get("address", ""),
                "mac_address": entry.get("mac-address", ""),
                "interface": entry.get("interface", ""),
                "status": status,
                "comment": entry.get("comment", ""),
            })
        return result

    # ═══════════════════════════════════════════════════════════════
    # FULL CONFIG (for sync)
    # ═══════════════════════════════════════════════════════════════

    def get_full_config(self) -> Dict[str, Any]:
        """Pull complete MikroTik configuration."""
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

        sections = {
            "system": self.get_system_info,
            "interfaces": self.get_interfaces,
            "ip_addresses": self.get_ip_addresses,
            "dhcp_servers": self.get_dhcp_servers,
            "dhcp_leases": self.get_dhcp_leases,
            "dns": self.get_dns_config,
            "dns_static": self.get_dns_static_entries,
            "routes": self.get_routes,
            "firewall_filter": self.get_firewall_filter_rules,
            "firewall_nat": self.get_firewall_nat_rules,
            "queues": self.get_queues,
            "wireless": self.get_wireless_interfaces,
            "vpn_interfaces": self.get_vpn_interfaces,
            "vpn_peers": self.get_vpn_peers,
            "arp": self.get_arp_table,
        }

        errors = []
        for section, getter in sections.items():
            try:
                config[section] = getter()
            except Exception as e:
                errors.append(f"{section}: {e}")

        if errors:
            config["_sync_errors"] = errors

        return config

    # ═══════════════════════════════════════════════════════════════
    # PUSH OVERRIDES (for sync engine)
    # ═══════════════════════════════════════════════════════════════

    def _push_ip_addresses(self, items: list) -> dict:
        created, updated, errors = 0, 0, []
        existing = {a["address"]: a for a in self.get_ip_addresses()}

        for item in items:
            try:
                addr = item.get("address", "")
                if addr in existing:
                    # Already exists — skip or update
                    updated += 1
                else:
                    self.add_ip_address(item)
                    created += 1
            except Exception as e:
                errors.append(str(e))

        return {"created": created, "updated": updated, "errors": errors}

    def _push_dns_static(self, items: list) -> dict:
        created, errors = 0, []
        existing = {e["name"]: e for e in self.get_dns_static_entries()}

        for item in items:
            try:
                name = item.get("name", "")
                if name in existing:
                    # Remove old, add new
                    self.remove_dns_static_entry(existing[name]["id"])
                self.add_dns_static_entry(item)
                created += 1
            except Exception as e:
                errors.append(str(e))

        return {"created": created, "errors": errors}

    def _push_routes(self, items: list) -> dict:
        created, errors = 0, []
        existing = {r["destination"]: r for r in self.get_routes() if r["type"] == "static"}

        for item in items:
            try:
                dest = item.get("destination", "")
                if dest not in existing:
                    self.add_route(item)
                    created += 1
            except Exception as e:
                errors.append(str(e))

        return {"created": created, "errors": errors}

    def _push_firewall_filter(self, items: list) -> dict:
        created, errors = 0, []
        for item in items:
            try:
                self.add_firewall_filter_rule(item)
                created += 1
            except Exception as e:
                errors.append(str(e))
        return {"created": created, "errors": errors}

    def _push_firewall_nat(self, items: list) -> dict:
        created, errors = 0, []
        for item in items:
            try:
                self.add_firewall_nat_rule(item)
                created += 1
            except Exception as e:
                errors.append(str(e))
        return {"created": created, "errors": errors}

    def _push_queues(self, items: list) -> dict:
        created, updated, errors = 0, 0, []
        existing = {q["name"]: q for q in self.get_queues()}

        for item in items:
            try:
                name = item.get("name", "")
                if name in existing:
                    self.update_queue(existing[name]["id"], item)
                    updated += 1
                else:
                    self.add_queue(item)
                    created += 1
            except Exception as e:
                errors.append(str(e))

        return {"created": created, "updated": updated, "errors": errors}

    # ═══════════════════════════════════════════════════════════════
    # INTERNAL HELPERS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _parse_rate_pair(rate_str: str) -> tuple:
        """Parse RouterOS rate pair "upload/download" → (upload, download)."""
        parts = str(rate_str).split("/", 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        return parts[0].strip(), "0"

    @staticmethod
    def _parse_time_pair(time_str: str) -> tuple:
        """Parse RouterOS time pair "upload/download" → (upload, download)."""
        parts = str(time_str).split("/", 1)
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        return parts[0].strip(), "0s"
