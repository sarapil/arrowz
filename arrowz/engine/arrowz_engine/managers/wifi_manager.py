"""
Arrowz Engine - WiFi Manager

Manages hostapd configuration for access point functionality,
including hotspot / captive portal support.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from arrowz_engine.models import WiFiConfig
from arrowz_engine.utils.shell import run_command

logger = logging.getLogger("arrowz_engine.managers.wifi")

HOSTAPD_CONF_PATH = "/etc/hostapd/hostapd.conf"
HOSTAPD_CLI = "hostapd_cli"


class WiFiManager:
    """
    Manages WiFi access point via hostapd.

    Generates hostapd.conf from WiFiConfig, restarts the service,
    and provides query methods for station information.
    """

    def __init__(self):
        self._current_config: Optional[WiFiConfig] = None

    def apply_config(self, config: WiFiConfig) -> Dict[str, Any]:
        """
        Generate hostapd.conf and restart the service.

        Steps:
        1. Generate hostapd.conf content from config
        2. Write to HOSTAPD_CONF_PATH
        3. Restart hostapd service
        4. Verify hostapd is running

        Args:
            config: WiFiConfig payload from Frappe.

        Returns:
            Dict with apply results.
        """
        self._current_config = config
        results = {}

        # TODO: Step 1 - Generate hostapd.conf
        conf_content = self._generate_hostapd_conf(config)
        results["config_lines"] = conf_content.count("\n") + 1

        # TODO: Step 2 - Write config file
        # with open(HOSTAPD_CONF_PATH, "w") as f:
        #     f.write(conf_content)
        results["config_path"] = HOSTAPD_CONF_PATH

        # TODO: Step 3 - Restart hostapd
        # stdout, stderr, rc = run_command("systemctl restart hostapd")
        # results["restart_rc"] = rc
        results["restarted"] = False  # stub

        # TODO: Step 4 - Verify running
        # stdout, _, rc = run_command("systemctl is-active hostapd")
        # results["active"] = stdout.strip() == "active"
        results["active"] = False  # stub

        logger.info("WiFi configuration applied (stub).")
        return results

    def _generate_hostapd_conf(self, config: WiFiConfig) -> str:
        """
        Generate hostapd.conf content from WiFiConfig.

        Args:
            config: WiFiConfig to translate.

        Returns:
            hostapd.conf file content as string.
        """
        lines = [
            "# Arrowz Engine - Auto-generated hostapd configuration",
            "# DO NOT EDIT MANUALLY - managed by Arrowz Engine",
            "",
            f"interface={config.interface or 'wlan0'}",
            f"ssid={config.ssid}",
            f"channel={config.channel}",
            f"hw_mode={config.hw_mode}",
            f"country_code={config.country_code}",
            f"max_num_sta={config.max_clients}",
            "",
            "# Authentication",
            "auth_algs=1",
            "wpa=2",
            "wpa_key_mgmt=WPA-PSK",
            "rsn_pairwise=CCMP",
        ]

        if config.passphrase:
            lines.append(f"wpa_passphrase={config.passphrase}")

        if config.hidden:
            lines.append("ignore_broadcast_ssid=1")

        # 802.11n
        if config.ieee80211n:
            lines.append("ieee80211n=1")
            lines.append("wmm_enabled=1")

        # 802.11ac
        if config.ieee80211ac:
            lines.append("ieee80211ac=1")

        # 802.11ax
        if config.ieee80211ax:
            lines.append("ieee80211ax=1")

        lines.append("")
        return "\n".join(lines)

    def get_clients(self) -> List[Dict[str, Any]]:
        """
        Get list of connected WiFi stations via hostapd_cli.

        Parses the output of `hostapd_cli all_sta` which returns
        per-station blocks with MAC, signal, rates, etc.

        Returns:
            List of dicts with station details.
        """
        clients = []

        try:
            stdout, stderr, rc = run_command(f"{HOSTAPD_CLI} all_sta", timeout=10)
            if rc != 0:
                logger.warning("hostapd_cli all_sta failed (rc=%d): %s", rc, stderr)
                return clients

            # TODO: Parse hostapd_cli all_sta output
            # Format:
            # <mac_address>
            # flags=[AUTH][ASSOC][AUTHORIZED]
            # rx_packets=12345
            # tx_packets=6789
            # signal=-45
            # connected_time=3600
            # ...
            # (blank line between stations)
            current_station: Optional[Dict[str, Any]] = None

            for line in stdout.splitlines():
                line = line.strip()
                if not line:
                    if current_station:
                        clients.append(current_station)
                        current_station = None
                    continue

                # MAC address line (starts a new station block)
                if re.match(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$", line):
                    if current_station:
                        clients.append(current_station)
                    current_station = {"mac_address": line}
                elif current_station and "=" in line:
                    key, _, value = line.partition("=")
                    current_station[key] = value

            # Don't forget the last station
            if current_station:
                clients.append(current_station)

        except Exception as exc:
            logger.error("Failed to get WiFi clients: %s", exc)

        return clients

    def get_status(self) -> Dict[str, Any]:
        """
        Get WiFi radio and SSID status.

        Returns:
            Dict with radio status, SSID info, and client count.
        """
        status: Dict[str, Any] = {
            "enabled": False,
            "ssid": None,
            "channel": None,
            "band": None,
            "clients_connected": 0,
            "hostapd_running": False,
        }

        try:
            # Check if hostapd is running
            stdout, _, rc = run_command("systemctl is-active hostapd", timeout=5)
            status["hostapd_running"] = stdout.strip() == "active"

            if status["hostapd_running"]:
                status["enabled"] = True

                # Get status from hostapd_cli
                stdout, _, rc = run_command(f"{HOSTAPD_CLI} status", timeout=5)
                if rc == 0:
                    for line in stdout.splitlines():
                        if "=" in line:
                            key, _, value = line.partition("=")
                            key = key.strip()
                            value = value.strip()
                            if key == "ssid[0]":
                                status["ssid"] = value
                            elif key == "channel":
                                status["channel"] = int(value) if value.isdigit() else value
                            elif key == "num_sta[0]":
                                status["clients_connected"] = (
                                    int(value) if value.isdigit() else 0
                                )

                # Infer band from config
                if self._current_config:
                    status["band"] = self._current_config.band

        except Exception as exc:
            logger.error("Failed to get WiFi status: %s", exc)

        return status
