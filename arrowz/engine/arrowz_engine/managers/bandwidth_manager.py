# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz Engine - Bandwidth Manager

Manages traffic shaping using Linux tc (Traffic Control) with
HTB (Hierarchical Token Bucket) queuing discipline and SFQ
(Stochastic Fair Queuing) for leaf classes.
"""

import logging
from typing import Any, Dict, List, Optional

from arrowz_engine.models import BandwidthConfig
from arrowz_engine.utils.shell import run_command

logger = logging.getLogger("arrowz_engine.managers.bandwidth")


class BandwidthManager:
    """
    Manages bandwidth shaping via tc (traffic control).

    Uses HTB as the root queueing discipline with per-profile
    classes and SFQ as the leaf qdisc for fairness.
    """

    def __init__(self):
        self._current_config: Optional[BandwidthConfig] = None

    def apply_config(self, config: BandwidthConfig) -> Dict[str, Any]:
        """
        Generate and apply tc commands for bandwidth shaping.

        Steps:
        1. Clear existing tc rules on target interfaces
        2. Create root HTB qdisc
        3. Create root class with total bandwidth
        4. Create per-profile child classes
        5. Add SFQ leaf qdiscs
        6. Add filters for per-client rules

        Args:
            config: BandwidthConfig payload from Frappe.

        Returns:
            Dict with apply results.
        """
        self._current_config = config
        results = {}

        if not config.enabled:
            # TODO: Remove all tc rules
            results["status"] = "disabled"
            logger.info("Bandwidth shaping disabled.")
            return results

        wan_iface = config.wan_interface or "eth0"
        lan_iface = config.lan_interface or "br-lan"

        # TODO: Step 1 - Clear existing rules
        # run_command(f"tc qdisc del dev {wan_iface} root 2>/dev/null")
        # run_command(f"tc qdisc del dev {lan_iface} root 2>/dev/null")
        results["cleared"] = True  # stub

        # TODO: Step 2 - Create root HTB qdisc
        # run_command(f"tc qdisc add dev {lan_iface} root handle 1: htb default 99")
        results["root_qdisc"] = "stub"

        # TODO: Step 3 - Create root class
        # run_command(
        #     f"tc class add dev {lan_iface} parent 1: classid 1:1 "
        #     f"htb rate {config.total_download_kbps}kbit "
        #     f"ceil {config.total_download_kbps}kbit"
        # )
        results["root_class"] = {
            "download_kbps": config.total_download_kbps,
            "upload_kbps": config.total_upload_kbps,
        }

        # TODO: Step 4 - Create per-profile classes
        for i, profile in enumerate(config.profiles, start=10):
            # class_id = f"1:{i}"
            # run_command(
            #     f"tc class add dev {lan_iface} parent 1:1 classid {class_id} "
            #     f"htb rate {profile.download_kbps}kbit "
            #     f"ceil {profile.download_kbps}kbit "
            #     f"prio {profile.priority}"
            # )
            # Step 5 - Add SFQ leaf
            # run_command(f"tc qdisc add dev {lan_iface} parent {class_id} sfq perturb 10")
            pass
        results["profiles"] = len(config.profiles)

        # TODO: Step 6 - Add per-client filters
        # for rule in config.per_client_rules:
        #     # Match by IP or MAC and classify into appropriate class
        #     pass
        results["client_rules"] = len(config.per_client_rules)

        logger.info("Bandwidth configuration applied (stub).")
        return results

    def get_stats(self) -> Dict[str, Any]:
        """
        Parse tc statistics for all managed interfaces.

        Runs `tc -s qdisc show dev <iface>` and `tc -s class show dev <iface>`
        to collect current shaping statistics.

        Returns:
            Dict with per-interface tc statistics.
        """
        stats: Dict[str, Any] = {}

        interfaces = []
        if self._current_config:
            if self._current_config.wan_interface:
                interfaces.append(self._current_config.wan_interface)
            if self._current_config.lan_interface:
                interfaces.append(self._current_config.lan_interface)

        if not interfaces:
            interfaces = ["eth0", "br-lan"]  # Default guess

        for iface in interfaces:
            iface_stats: Dict[str, Any] = {}

            try:
                # Qdisc stats
                stdout, stderr, rc = run_command(
                    f"tc -s qdisc show dev {iface}", timeout=10
                )
                if rc == 0:
                    iface_stats["qdisc_raw"] = stdout.strip()

                # Class stats
                stdout, stderr, rc = run_command(
                    f"tc -s class show dev {iface}", timeout=10
                )
                if rc == 0:
                    iface_stats["class_raw"] = stdout.strip()

                # TODO: Parse raw output into structured data
                # (packets sent, bytes sent, drops, overlimits, etc.)

            except Exception as exc:
                logger.error("Failed to get tc stats for %s: %s", iface, exc)
                iface_stats["error"] = str(exc)

            stats[iface] = iface_stats

        return stats
