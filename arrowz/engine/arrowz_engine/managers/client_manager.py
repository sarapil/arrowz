# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz Engine - Client Manager

Manages connected network clients: DHCP reservations, MAC-based
access control (block/unblock), and client disconnection.
"""

import logging
from typing import Any, Dict, List, Optional

from arrowz_engine.models import ClientConfig
from arrowz_engine.utils.shell import run_command

logger = logging.getLogger("arrowz_engine.managers.client")

DNSMASQ_RESERVATIONS_FILE = "/etc/dnsmasq.d/arrowz-reservations.conf"
DNSMASQ_LEASE_FILE = "/var/lib/misc/dnsmasq.leases"
PROC_ARP = "/proc/net/arp"


class ClientManager:
    """
    Manages network client operations.

    Handles DHCP static reservations, MAC-based blocking via nftables,
    and client disconnection via ARP and hostapd commands.
    """

    def __init__(self):
        self._current_config: Optional[ClientConfig] = None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def apply_config(self, config: ClientConfig) -> Dict[str, Any]:
        """
        Apply client management configuration.

        Steps:
        1. Write DHCP static reservations to dnsmasq config
        2. Update MAC block list in nftables
        3. Restart dnsmasq to pick up reservation changes

        Args:
            config: ClientConfig payload from Frappe.

        Returns:
            Dict with apply results.
        """
        self._current_config = config
        results = {}

        # TODO: Step 1 - Generate DHCP reservations
        reservation_lines = []
        for res in config.reservations:
            # dnsmasq format: dhcp-host=<mac>,<ip>,<hostname>
            parts = [res.mac_address, res.ip_address]
            if res.hostname:
                parts.append(res.hostname)
            reservation_lines.append(f"dhcp-host={','.join(parts)}")

        results["reservations"] = len(reservation_lines)

        # TODO: Write reservations file
        # with open(DNSMASQ_RESERVATIONS_FILE, "w") as f:
        #     f.write("# Arrowz Engine - Auto-generated DHCP reservations\n")
        #     f.write("\n".join(reservation_lines))
        #     f.write("\n")

        # TODO: Step 2 - Update MAC blocks in firewall
        # This should coordinate with FirewallManager
        results["blocked_macs"] = len(config.blocked_macs)

        # TODO: Step 3 - Restart dnsmasq
        # run_command("systemctl restart dnsmasq")
        results["dnsmasq_restarted"] = False  # stub

        logger.info("Client configuration applied (stub).")
        return results

    # ------------------------------------------------------------------
    # Query Methods
    # ------------------------------------------------------------------

    def get_connected(self) -> List[Dict[str, Any]]:
        """
        Get a list of currently connected clients.

        Merges data from:
        - /proc/net/arp (ARP table → MAC + IP)
        - dnsmasq leases (hostname + lease expiry)
        - hostapd station list (WiFi signal, connected time)

        Returns:
            List of dicts with client details.
        """
        clients_by_mac: Dict[str, Dict[str, Any]] = {}

        # --- ARP table ---
        try:
            with open(PROC_ARP, "r") as f:
                lines = f.readlines()
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 6 and parts[2] != "0x0":  # Skip incomplete entries
                    mac = parts[3].lower()
                    clients_by_mac[mac] = {
                        "mac_address": mac,
                        "ip_address": parts[0],
                        "interface": parts[5],
                        "source": "arp",
                    }
        except FileNotFoundError:
            logger.warning("ARP file not found: %s", PROC_ARP)
        except Exception as exc:
            logger.error("Failed to read ARP table: %s", exc)

        # --- DHCP leases ---
        try:
            with open(DNSMASQ_LEASE_FILE, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        mac = parts[1].lower()
                        if mac in clients_by_mac:
                            clients_by_mac[mac]["hostname"] = (
                                parts[3] if parts[3] != "*" else None
                            )
                            clients_by_mac[mac]["lease_expires"] = parts[0]
                        else:
                            clients_by_mac[mac] = {
                                "mac_address": mac,
                                "ip_address": parts[2],
                                "hostname": parts[3] if parts[3] != "*" else None,
                                "lease_expires": parts[0],
                                "source": "dhcp",
                            }
        except FileNotFoundError:
            logger.debug("DHCP lease file not found: %s", DNSMASQ_LEASE_FILE)
        except Exception as exc:
            logger.error("Failed to read DHCP leases: %s", exc)

        # --- WiFi stations (optional enrichment) ---
        try:
            stdout, _, rc = run_command("hostapd_cli all_sta", timeout=5)
            if rc == 0:
                # TODO: Parse and merge WiFi station data
                pass
        except Exception:
            pass  # hostapd may not be running

        return list(clients_by_mac.values())

    # ------------------------------------------------------------------
    # Client Actions
    # ------------------------------------------------------------------

    def block(self, mac_address: str) -> Dict[str, Any]:
        """
        Block a client by MAC address.

        Adds an nftables rule to drop all traffic from the MAC and
        optionally disconnects the client.

        Args:
            mac_address: Client MAC address to block.

        Returns:
            Dict with action results.
        """
        mac = mac_address.lower()
        result: Dict[str, Any] = {"mac_address": mac}

        # TODO: Add nftables rule to block MAC
        # run_command(
        #     f"nft add rule inet filter forward ether saddr {mac} drop "
        #     f"comment \"arrowz-block-{mac}\""
        # )
        result["firewall_rule_added"] = False  # stub

        # TODO: Disconnect the client
        # self.disconnect(mac)
        result["disconnected"] = False  # stub

        logger.info("Client %s blocked (stub).", mac)
        return result

    def unblock(self, mac_address: str) -> Dict[str, Any]:
        """
        Unblock a previously blocked client by MAC address.

        Removes the nftables drop rule for the MAC.

        Args:
            mac_address: Client MAC address to unblock.

        Returns:
            Dict with action results.
        """
        mac = mac_address.lower()
        result: Dict[str, Any] = {"mac_address": mac}

        # TODO: Remove nftables block rule for this MAC
        # Need to find the rule handle first:
        # run_command("nft -a list chain inet filter forward")
        # Then delete by handle:
        # run_command(f"nft delete rule inet filter forward handle {handle}")
        result["firewall_rule_removed"] = False  # stub

        logger.info("Client %s unblocked (stub).", mac)
        return result

    def disconnect(self, mac_address: str) -> Dict[str, Any]:
        """
        Forcefully disconnect a client by MAC address.

        Sends a deauthentication frame via hostapd (for WiFi clients)
        and deletes the ARP entry to force re-association.

        Args:
            mac_address: Client MAC address to disconnect.

        Returns:
            Dict with action results.
        """
        mac = mac_address.lower()
        result: Dict[str, Any] = {"mac_address": mac}

        # TODO: Deauth via hostapd (WiFi clients)
        # run_command(f"hostapd_cli deauthenticate {mac}")
        result["deauth_sent"] = False  # stub

        # TODO: Delete ARP entry
        # run_command(f"ip neigh del {ip} dev {iface}")  # need IP lookup first
        result["arp_cleared"] = False  # stub

        logger.info("Client %s disconnected (stub).", mac)
        return result
