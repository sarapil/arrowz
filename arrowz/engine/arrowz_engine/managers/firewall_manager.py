"""
Arrowz Engine - Firewall Manager

Manages nftables rulesets for packet filtering, NAT, and MAC-based
access control.
"""

import logging
import textwrap
from typing import Any, Dict, List, Optional

from arrowz_engine.models import FirewallConfig
from arrowz_engine.utils.shell import run_command

logger = logging.getLogger("arrowz_engine.managers.firewall")

# Path where the generated nftables ruleset is written before atomic load
NFTABLES_CONF_PATH = "/etc/nftables.d/arrowz.conf"
NFTABLES_MAIN_CONF = "/etc/nftables.conf"


class FirewallManager:
    """
    Manages nftables firewall rules.

    Generates a complete nftables ruleset from the FirewallConfig
    and atomically loads it via `nft -f`.
    """

    def __init__(self):
        self._current_config: Optional[FirewallConfig] = None

    def apply_config(self, config: FirewallConfig) -> Dict[str, Any]:
        """
        Generate and apply an nftables ruleset from the provided config.

        Steps:
        1. Generate the nftables ruleset string
        2. Write to NFTABLES_CONF_PATH
        3. Validate with `nft -c -f`
        4. Apply atomically with `nft -f`

        Args:
            config: FirewallConfig payload from Frappe.

        Returns:
            Dict with apply results.
        """
        self._current_config = config
        results = {}

        # TODO: Step 1 - Generate nftables ruleset
        ruleset = self._generate_ruleset(config)
        results["ruleset_lines"] = ruleset.count("\n") + 1

        # TODO: Step 2 - Write ruleset to file
        # with open(NFTABLES_CONF_PATH, "w") as f:
        #     f.write(ruleset)
        results["config_path"] = NFTABLES_CONF_PATH

        # TODO: Step 3 - Validate ruleset
        # stdout, stderr, rc = run_command(f"nft -c -f {NFTABLES_CONF_PATH}")
        # if rc != 0:
        #     raise RuntimeError(f"nftables validation failed: {stderr}")
        results["validated"] = False  # stub

        # TODO: Step 4 - Apply ruleset atomically
        # stdout, stderr, rc = run_command(f"nft -f {NFTABLES_CONF_PATH}")
        # if rc != 0:
        #     raise RuntimeError(f"nftables apply failed: {stderr}")
        results["applied"] = False  # stub

        logger.info("Firewall configuration applied (stub).")
        return results

    def _generate_ruleset(self, config: FirewallConfig) -> str:
        """
        Generate a complete nftables ruleset from config.

        Produces a ruleset with:
        - inet filter table (input, forward, output chains)
        - ip nat table (postrouting for masquerade)
        - Custom rules from config
        - Port forwarding (DNAT) rules
        - MAC-based blocking

        Args:
            config: FirewallConfig to translate.

        Returns:
            Complete nftables ruleset as a string.
        """
        # TODO: Build full nftables ruleset
        ruleset = textwrap.dedent(f"""\
            #!/usr/sbin/nft -f
            # Arrowz Engine - Auto-generated nftables ruleset
            # DO NOT EDIT MANUALLY - managed by Arrowz Engine

            flush ruleset

            table inet filter {{
                chain input {{
                    type filter hook input priority 0; policy {config.default_input_policy};

                    # Accept established/related connections
                    ct state established,related accept

                    # Accept loopback
                    iif lo accept

                    # Accept ICMP
                    ip protocol icmp accept
                    ip6 nexthdr icmpv6 accept

                    # TODO: Add custom input rules from config.rules
                }}

                chain forward {{
                    type filter hook forward priority 0; policy {config.default_forward_policy};

                    # Accept established/related connections
                    ct state established,related accept

                    # TODO: Add MAC blocks from config.blocked_macs
                    # TODO: Add custom forward rules from config.rules
                }}

                chain output {{
                    type filter hook output priority 0; policy {config.default_output_policy};
                }}
            }}
        """)

        # Add NAT table if enabled
        if config.nat_enabled:
            wan_iface = config.wan_interface or "eth0"
            ruleset += textwrap.dedent(f"""
            table ip nat {{
                chain postrouting {{
                    type nat hook postrouting priority 100;
                    oifname "{wan_iface}" masquerade
                }}

                chain prerouting {{
                    type nat hook prerouting priority -100;
                    # TODO: Add port forwards from config.port_forwards
                }}
            }}
            """)

        return ruleset

    def get_logs(self, limit: int = 100) -> List[Dict[str, str]]:
        """
        Parse recent firewall log entries.

        Reads from kernel log (dmesg) or journald for nftables log
        prefix entries.

        Args:
            limit: Maximum number of log entries to return.

        Returns:
            List of dicts with parsed log entries.
        """
        logs = []

        try:
            # TODO: Parse firewall logs from journald or dmesg
            stdout, stderr, rc = run_command(
                f"journalctl -k --no-pager -n {limit} --grep='nft\\|ARROWZ'",
                timeout=10,
            )
            if rc == 0:
                for line in stdout.strip().splitlines():
                    logs.append({"raw": line.strip()})
        except Exception as exc:
            logger.error("Failed to get firewall logs: %s", exc)

        return logs
