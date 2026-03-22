"""
Arrowz Engine - Network Manager

Manages network interface configuration, DHCP, ARP, and routing.
Interacts with the Linux networking stack via ip, ifconfig, and
dnsmasq configuration files.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from arrowz_engine.models import NetworkConfig
from arrowz_engine.utils.shell import run_command

logger = logging.getLogger("arrowz_engine.managers.network")

# Default paths
DNSMASQ_LEASE_FILE = "/var/lib/misc/dnsmasq.leases"
DNSMASQ_CONF_DIR = "/etc/dnsmasq.d"
PROC_ARP = "/proc/net/arp"


class NetworkManager:
    """
    Manages network interfaces, DHCP server, and routing.

    Applies configuration received from the Frappe Interface Layer
    and provides read-only accessors for current network state.
    """

    def __init__(self):
        self._current_config: Optional[NetworkConfig] = None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def apply_config(self, config: NetworkConfig) -> Dict[str, Any]:
        """
        Apply network configuration.

        Steps:
        1. Configure WAN interface (DHCP / static / PPPoE)
        2. Configure LAN interface with static IP
        3. Generate dnsmasq DHCP configuration
        4. Apply static routes
        5. Restart affected services

        Args:
            config: NetworkConfig payload from Frappe.

        Returns:
            Dict with apply results per step.
        """
        results = {}
        self._current_config = config

        # TODO: Step 1 - Configure WAN interface
        # if config.wan_type == "static":
        #     run_command(f"ip addr flush dev {config.wan_interface}")
        #     run_command(f"ip addr add {config.wan_ip}/{config.wan_netmask} dev {config.wan_interface}")
        #     run_command(f"ip route add default via {config.wan_gateway}")
        results["wan"] = {"status": "stub", "interface": config.wan_interface}

        # TODO: Step 2 - Configure LAN interface
        # run_command(f"ip addr flush dev {config.lan_interface}")
        # run_command(f"ip addr add {config.lan_ip}/{config.lan_netmask} dev {config.lan_interface}")
        results["lan"] = {"status": "stub", "interface": config.lan_interface}

        # TODO: Step 3 - Generate dnsmasq DHCP config
        # Write dhcp-range, dns-server lines to DNSMASQ_CONF_DIR/arrowz.conf
        results["dhcp"] = {"status": "stub", "enabled": config.dhcp_enabled}

        # TODO: Step 4 - Apply static routes
        # for route in config.static_routes:
        #     run_command(f"ip route add {route['destination']} via {route['gateway']}")
        results["routes"] = {"status": "stub", "count": len(config.static_routes)}

        # TODO: Step 5 - Restart services
        # run_command("systemctl restart dnsmasq")

        logger.info("Network configuration applied (stub).")
        return results

    # ------------------------------------------------------------------
    # Read-Only Accessors
    # ------------------------------------------------------------------

    def get_interfaces(self) -> List[Dict[str, Any]]:
        """
        List all network interfaces with their current status.

        Parses output of `ip -j addr show` for JSON-formatted data,
        falling back to plain-text parsing if JSON is unavailable.

        Returns:
            List of dicts with interface details.
        """
        interfaces = []

        try:
            stdout, stderr, rc = run_command("ip -j addr show", timeout=10)
            if rc == 0 and stdout.strip():
                import json
                interfaces = json.loads(stdout)
                # TODO: Transform to consistent format
                return interfaces
        except Exception:
            pass

        # Fallback: parse plain-text output
        try:
            stdout, stderr, rc = run_command("ip addr show", timeout=10)
            if rc == 0:
                # TODO: Parse plain-text ip addr output
                logger.debug("Parsing plain-text ip addr output (stub).")
        except Exception as exc:
            logger.error("Failed to get interfaces: %s", exc)

        return interfaces

    def get_dhcp_leases(self) -> List[Dict[str, str]]:
        """
        Parse DHCP leases from the dnsmasq lease file.

        Lease file format (one per line):
        <timestamp> <mac> <ip> <hostname> <client-id>

        Returns:
            List of dicts with lease details.
        """
        leases = []

        try:
            with open(DNSMASQ_LEASE_FILE, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        leases.append({
                            "expires": parts[0],
                            "mac_address": parts[1],
                            "ip_address": parts[2],
                            "hostname": parts[3] if parts[3] != "*" else None,
                            "client_id": parts[4] if len(parts) > 4 else None,
                        })
        except FileNotFoundError:
            logger.warning("DHCP lease file not found: %s", DNSMASQ_LEASE_FILE)
        except Exception as exc:
            logger.error("Failed to parse DHCP leases: %s", exc)

        return leases

    def get_arp_table(self) -> List[Dict[str, str]]:
        """
        Parse the ARP table from /proc/net/arp.

        Format:
        IP address       HW type     Flags       HW address            Mask     Device
        192.168.1.1      0x1         0x2         aa:bb:cc:dd:ee:ff     *        eth0

        Returns:
            List of dicts with ARP entry details.
        """
        entries = []

        try:
            with open(PROC_ARP, "r") as f:
                lines = f.readlines()

            # Skip header line
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 6:
                    entries.append({
                        "ip_address": parts[0],
                        "hw_type": parts[1],
                        "flags": parts[2],
                        "mac_address": parts[3],
                        "mask": parts[4],
                        "device": parts[5],
                    })
        except FileNotFoundError:
            logger.warning("ARP file not found: %s", PROC_ARP)
        except Exception as exc:
            logger.error("Failed to parse ARP table: %s", exc)

        return entries

    def get_routing_table(self) -> List[Dict[str, str]]:
        """
        Parse the routing table from `ip route show`.

        Returns:
            List of dicts with route details.
        """
        routes = []

        try:
            stdout, stderr, rc = run_command("ip route show", timeout=10)
            if rc == 0:
                for line in stdout.strip().splitlines():
                    route = {"raw": line.strip()}

                    # Parse common fields
                    parts = line.strip().split()
                    if parts:
                        route["destination"] = parts[0]

                    if "via" in parts:
                        idx = parts.index("via")
                        if idx + 1 < len(parts):
                            route["gateway"] = parts[idx + 1]

                    if "dev" in parts:
                        idx = parts.index("dev")
                        if idx + 1 < len(parts):
                            route["device"] = parts[idx + 1]

                    if "src" in parts:
                        idx = parts.index("src")
                        if idx + 1 < len(parts):
                            route["source"] = parts[idx + 1]

                    routes.append(route)
        except Exception as exc:
            logger.error("Failed to get routing table: %s", exc)

        return routes
