"""
Arrowz Engine - VPN Manager

Manages WireGuard VPN tunnel configuration, peer management,
and status monitoring.
"""

import logging
from typing import Any, Dict, List, Optional

from arrowz_engine.models import VPNConfig
from arrowz_engine.utils.shell import run_command

logger = logging.getLogger("arrowz_engine.managers.vpn")

WIREGUARD_CONF_DIR = "/etc/wireguard"


class VPNManager:
    """
    Manages WireGuard VPN configuration.

    Generates WireGuard interface configuration files and manages
    the tunnel lifecycle via wg-quick.
    """

    def __init__(self):
        self._current_config: Optional[VPNConfig] = None

    def apply_config(self, config: VPNConfig) -> Dict[str, Any]:
        """
        Generate WireGuard configuration and bring up the tunnel.

        Steps:
        1. Generate wg config file (/etc/wireguard/<iface>.conf)
        2. Bring down existing tunnel (if running)
        3. Bring up tunnel with new config
        4. Verify tunnel is active

        Args:
            config: VPNConfig payload from Frappe.

        Returns:
            Dict with apply results.
        """
        self._current_config = config
        results = {}

        if not config.enabled:
            # TODO: Bring down the tunnel if running
            # run_command(f"wg-quick down {config.interface}")
            results["status"] = "disabled"
            logger.info("VPN disabled for interface %s.", config.interface)
            return results

        # TODO: Step 1 - Generate WireGuard config
        conf_content = self._generate_wg_conf(config)
        conf_path = f"{WIREGUARD_CONF_DIR}/{config.interface}.conf"
        results["config_path"] = conf_path
        results["config_lines"] = conf_content.count("\n") + 1

        # TODO: Step 2 - Write config file
        # with open(conf_path, "w", mode=0o600) as f:
        #     f.write(conf_content)

        # TODO: Step 3 - Restart tunnel
        # run_command(f"wg-quick down {config.interface} 2>/dev/null")
        # stdout, stderr, rc = run_command(f"wg-quick up {config.interface}")
        # results["up_rc"] = rc
        results["restarted"] = False  # stub

        # TODO: Step 4 - Verify
        # stdout, _, rc = run_command(f"wg show {config.interface}")
        # results["active"] = rc == 0
        results["active"] = False  # stub
        results["peers_count"] = len(config.peers)

        logger.info("VPN configuration applied (stub) for %s.", config.interface)
        return results

    def _generate_wg_conf(self, config: VPNConfig) -> str:
        """
        Generate WireGuard configuration file content.

        Args:
            config: VPNConfig to translate.

        Returns:
            WireGuard .conf file content as string.
        """
        lines = [
            "# Arrowz Engine - Auto-generated WireGuard configuration",
            "# DO NOT EDIT MANUALLY - managed by Arrowz Engine",
            "",
            "[Interface]",
        ]

        if config.private_key:
            lines.append(f"PrivateKey = {config.private_key}")
        if config.address:
            lines.append(f"Address = {config.address}")
        lines.append(f"ListenPort = {config.listen_port}")
        if config.dns:
            lines.append(f"DNS = {', '.join(config.dns)}")

        for peer in config.peers:
            lines.append("")
            lines.append("[Peer]")
            if peer.comment:
                lines.append(f"# {peer.comment}")
            lines.append(f"PublicKey = {peer.public_key}")
            if peer.preshared_key:
                lines.append(f"PresharedKey = {peer.preshared_key}")
            lines.append(f"AllowedIPs = {', '.join(peer.allowed_ips)}")
            if peer.endpoint:
                lines.append(f"Endpoint = {peer.endpoint}")
            lines.append(f"PersistentKeepalive = {peer.persistent_keepalive}")

        lines.append("")
        return "\n".join(lines)

    def get_peers(self) -> List[Dict[str, Any]]:
        """
        Get WireGuard peer information via `wg show`.

        Parses the output of `wg show <interface>` to extract
        peer details including last handshake, transfer stats,
        and endpoint information.

        Returns:
            List of dicts with peer details.
        """
        peers = []
        interface = "wg0"
        if self._current_config:
            interface = self._current_config.interface

        try:
            stdout, stderr, rc = run_command(f"wg show {interface}", timeout=10)
            if rc != 0:
                logger.warning("wg show %s failed (rc=%d): %s", interface, rc, stderr)
                return peers

            # TODO: Parse wg show output
            # Format:
            # interface: wg0
            #   public key: <key>
            #   private key: (hidden)
            #   listening port: 51820
            #
            # peer: <public_key>
            #   endpoint: 1.2.3.4:51820
            #   allowed ips: 10.0.0.0/24
            #   latest handshake: 1 minute, 30 seconds ago
            #   transfer: 1.23 MiB received, 4.56 MiB sent
            current_peer: Optional[Dict[str, Any]] = None

            for line in stdout.splitlines():
                line = line.strip()
                if line.startswith("peer:"):
                    if current_peer:
                        peers.append(current_peer)
                    current_peer = {"public_key": line.split(":", 1)[1].strip()}
                elif current_peer:
                    if line.startswith("endpoint:"):
                        current_peer["endpoint"] = line.split(":", 1)[1].strip()
                    elif line.startswith("allowed ips:"):
                        current_peer["allowed_ips"] = line.split(":", 1)[1].strip()
                    elif line.startswith("latest handshake:"):
                        current_peer["latest_handshake"] = line.split(":", 1)[1].strip()
                    elif line.startswith("transfer:"):
                        current_peer["transfer"] = line.split(":", 1)[1].strip()

            if current_peer:
                peers.append(current_peer)

        except Exception as exc:
            logger.error("Failed to get WireGuard peers: %s", exc)

        return peers
