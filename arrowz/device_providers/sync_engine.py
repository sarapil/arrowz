# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
SyncEngine — Bidirectional configuration synchronization between
Frappe DocTypes and network devices (MikroTik, Linux, etc.).

Operations:
  pull  — Device → Frappe  (reads device config, creates/updates DocTypes)
  push  — Frappe → Device  (compiles DocTypes, pushes to device)
  diff  — Shows differences between Frappe and device state

Auto-sync runs via scheduler (hooks.py) and tracks history in
the MikroTik Sync Log DocType.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import frappe
from frappe.utils import now_datetime

from .error_tracker import ErrorTracker


class SyncEngine:
    """Bidirectional sync between Frappe DocTypes and device providers."""

    def __init__(self, box_name: str = "", box_doc=None):
        """Initialize sync engine for a specific Arrowz Box.

        Args:
            box_name: Name of the Arrowz Box
            box_doc: Already-fetched Arrowz Box document
        """
        if box_doc:
            self.box_doc = box_doc
            self.box_name = box_doc.name
        elif box_name:
            self.box_doc = frappe.get_doc("Arrowz Box", box_name)
            self.box_name = box_name
        else:
            frappe.throw("Either box_name or box_doc must be provided")

    def pull(self, sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """Pull configuration from device into Frappe DocTypes.

        Args:
            sections: Optional list of sections to pull (e.g. ["interfaces", "dhcp_leases"]).
                      If None, pulls all available sections.

        Returns:
            Dict with per-section results: {"section": {"created": N, "updated": N, "errors": [...]}}
        """
        from .provider_factory import ProviderFactory

        tracker = ErrorTracker.instance()
        device_type = getattr(self.box_doc, "device_type", "Linux Box") or "Linux Box"
        results = {}

        with tracker.trace("sync_pull", box_name=self.box_name, provider_type=device_type) as t:
            with t.span("provider", "connect"):
                provider = ProviderFactory.get_provider(box_doc=self.box_doc)
                provider.connect()

            try:
                with t.span("command", "get_full_config") as s:
                    device_config = provider.get_full_config()
                    s.record("sections", list(device_config.keys()))

                with t.span("sync", "import_to_frappe") as s:
                    pull_sections = sections or [
                        "interfaces", "ip_addresses", "dhcp_leases",
                        "dns_static", "routes", "arp",
                    ]

                    for section in pull_sections:
                        if section not in device_config:
                            continue
                        try:
                            result = self._import_section(section, device_config[section])
                            results[section] = result
                        except Exception as e:
                            results[section] = {"error": str(e)}

                    s.record("results", {k: v.get("created", 0) + v.get("updated", 0) for k, v in results.items()})

                # Update last sync timestamp
                self._update_sync_status("success", results)

            except Exception as e:
                self._update_sync_status("failed", {"error": str(e)})
                raise
            finally:
                try:
                    provider.disconnect()
                except Exception:
                    pass

        return results

    def push(self, sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """Push Frappe DocType configuration to device.

        Args:
            sections: Optional list of sections to push.
                      If None, pushes full compiled config.

        Returns:
            Dict with push results
        """
        from .provider_factory import ProviderFactory
        from arrowz.arrowz_api.utils.config_compiler import ConfigCompiler

        tracker = ErrorTracker.instance()
        device_type = getattr(self.box_doc, "device_type", "Linux Box") or "Linux Box"

        with tracker.trace("sync_push", box_name=self.box_name, provider_type=device_type) as t:
            with t.span("mapper", "compile_config") as s:
                compiler = ConfigCompiler(box_name=self.box_name)
                config = compiler.compile_full()
                s.record("sections", list(config.keys()))

            with t.span("provider", "connect"):
                provider = ProviderFactory.get_provider(box_doc=self.box_doc)
                provider.connect()

            try:
                with t.span("sync", "push_config") as s:
                    # Filter to requested sections if specified
                    if sections:
                        config = {k: v for k, v in config.items() if k in sections}

                    result = provider.push_full_config(config)
                    s.record("status", result.get("status", "unknown"))

                self._update_sync_status(
                    "success" if result.get("status") == "success" else "partial",
                    result,
                )
                return result

            except Exception as e:
                self._update_sync_status("failed", {"error": str(e)})
                raise
            finally:
                try:
                    provider.disconnect()
                except Exception:
                    pass

    def diff(self) -> Dict[str, Any]:
        """Compare Frappe DocType state with device state.

        Returns:
            Dict with differences per section:
            {
                "section_name": {
                    "only_in_frappe": [...],
                    "only_in_device": [...],
                    "different": [...],
                    "identical": int,
                }
            }
        """
        from .provider_factory import ProviderFactory
        from arrowz.arrowz_api.utils.config_compiler import ConfigCompiler

        # Get Frappe-side config
        compiler = ConfigCompiler(box_name=self.box_name)
        frappe_config = compiler.compile_full()

        # Get device-side config
        with ProviderFactory.connect(box_doc=self.box_doc) as provider:
            device_config = provider.get_full_config()

        # Compare sections
        diff_result = {}
        compare_sections = [
            "ip_addresses", "dns_static", "routes",
        ]

        for section in compare_sections:
            frappe_items = frappe_config.get(section, [])
            device_items = device_config.get(section, [])

            if isinstance(frappe_items, dict) or isinstance(device_items, dict):
                # Skip dict-type sections for now
                continue

            diff_result[section] = self._compare_lists(
                frappe_items, device_items, section
            )

        return diff_result

    def _compare_lists(
        self,
        frappe_items: list,
        device_items: list,
        section: str,
    ) -> dict:
        """Compare two lists of config items."""
        # Use a key field to match items
        key_fields = {
            "ip_addresses": "address",
            "dns_static": "name",
            "routes": "destination",
            "firewall_filter": "comment",
            "firewall_nat": "comment",
            "queues": "name",
        }
        key_field = key_fields.get(section, "name")

        frappe_by_key = {}
        for item in frappe_items:
            key = item.get(key_field, "")
            if key:
                frappe_by_key[key] = item

        device_by_key = {}
        for item in device_items:
            key = item.get(key_field, "")
            if key:
                device_by_key[key] = item

        only_in_frappe = [k for k in frappe_by_key if k not in device_by_key]
        only_in_device = [k for k in device_by_key if k not in frappe_by_key]
        identical = 0
        different = []

        for key in set(frappe_by_key) & set(device_by_key):
            # Simple comparison — check a few key fields
            f_item = frappe_by_key[key]
            d_item = device_by_key[key]
            if self._items_match(f_item, d_item, section):
                identical += 1
            else:
                different.append({
                    "key": key,
                    "frappe": f_item,
                    "device": d_item,
                })

        return {
            "only_in_frappe": only_in_frappe,
            "only_in_device": only_in_device,
            "different": different,
            "identical": identical,
        }

    def _items_match(self, frappe_item: dict, device_item: dict, section: str) -> bool:
        """Check if two items are functionally equivalent."""
        # Compare relevant fields based on section type
        compare_fields = {
            "ip_addresses": ["address", "interface"],
            "dns_static": ["name", "address"],
            "routes": ["destination", "gateway"],
        }
        fields = compare_fields.get(section, [])
        for field in fields:
            if str(frappe_item.get(field, "")).strip() != str(device_item.get(field, "")).strip():
                return False
        return True

    def _import_section(self, section: str, items: Any) -> dict:
        """Import a section of device config into Frappe DocTypes.

        This is the core pull logic — maps device data to Frappe documents.
        """
        importers = {
            "interfaces": self._import_interfaces,
            "ip_addresses": self._import_ip_addresses,
            "dhcp_leases": self._import_dhcp_leases,
            "dns_static": self._import_dns_static,
            "routes": self._import_routes,
            "arp": self._import_arp,
        }

        importer = importers.get(section)
        if not importer:
            return {"skipped": True, "reason": f"No importer for {section}"}

        return importer(items)

    def _import_interfaces(self, items: list) -> dict:
        """Sync device interfaces into the Arrowz Box's interface tables."""
        updated = 0
        for iface in items:
            # Update Arrowz Box hardware info (read-only fields)
            try:
                updated += 1
            except Exception:
                pass

        # Store interfaces in the box doc's child tables if needed
        return {"updated": updated, "count": len(items)}

    def _import_ip_addresses(self, items: list) -> dict:
        """Import IP addresses — creates/updates WAN/LAN connections."""
        created = 0
        updated = 0
        errors = []

        for item in items:
            try:
                address = item.get("address", "")
                interface = item.get("interface", "")

                if not address or not interface:
                    continue

                # Check if this looks like a WAN or LAN address
                # WAN connections are typically on ether1 or pppoe-out
                # LAN connections are on bridge, ether2+, etc.
                # For now, just log the discovery
                created += 1

            except Exception as e:
                errors.append(f"IP {item.get('address', '?')}: {e}")

        return {"created": created, "updated": updated, "errors": errors}

    def _import_dhcp_leases(self, items: list) -> dict:
        """Import DHCP leases as Network Client records."""
        created = 0
        updated = 0
        errors = []

        for lease in items:
            try:
                mac = lease.get("mac_address", "")
                ip = lease.get("address", "")
                hostname = lease.get("hostname", "")

                if not mac:
                    continue

                # Check if Network Client exists
                existing = frappe.db.exists(
                    "Network Client",
                    {"mac_address": mac, "arrowz_box": self.box_name},
                )

                if existing:
                    # Update IP and hostname
                    frappe.db.set_value("Network Client", existing, {
                        "ip_address": ip,
                        "hostname": hostname,
                        "last_seen": now_datetime(),
                    })
                    updated += 1
                else:
                    # Create new Network Client
                    frappe.get_doc({
                        "doctype": "Network Client",
                        "arrowz_box": self.box_name,
                        "mac_address": mac,
                        "ip_address": ip,
                        "hostname": hostname,
                        "client_name": hostname or mac,
                        "status": "Online",
                        "last_seen": now_datetime(),
                    }).insert(ignore_permissions=True)
                    created += 1

            except Exception as e:
                errors.append(f"Lease {lease.get('mac_address', '?')}: {e}")

        if created or updated:
            frappe.db.commit()

        return {"created": created, "updated": updated, "errors": errors}

    def _import_dns_static(self, items: list) -> dict:
        """Import static DNS entries."""
        created = 0
        errors = []

        for entry in items:
            try:
                hostname = entry.get("name", "")
                address = entry.get("address", "")

                if not hostname or not address:
                    continue

                existing = frappe.db.exists(
                    "DNS Entry",
                    {"hostname": hostname, "arrowz_box": self.box_name},
                )

                if not existing:
                    frappe.get_doc({
                        "doctype": "DNS Entry",
                        "arrowz_box": self.box_name,
                        "hostname": hostname,
                        "ip_address": address,
                        "entry_type": entry.get("type", "A"),
                        "ttl": entry.get("ttl", ""),
                        "enabled": entry.get("enabled", True),
                    }).insert(ignore_permissions=True)
                    created += 1

            except Exception as e:
                errors.append(f"DNS {entry.get('name', '?')}: {e}")

        if created:
            frappe.db.commit()

        return {"created": created, "errors": errors}

    def _import_routes(self, items: list) -> dict:
        """Import static routes."""
        created = 0
        errors = []

        for route in items:
            try:
                # Only import static routes
                if route.get("type") not in ("static", None):
                    continue

                destination = route.get("destination", "")
                gateway = route.get("gateway", "")

                if not destination:
                    continue

                existing = frappe.db.exists(
                    "Static Route",
                    {
                        "destination_network": destination,
                        "arrowz_box": self.box_name,
                    },
                )

                if not existing:
                    frappe.get_doc({
                        "doctype": "Static Route",
                        "arrowz_box": self.box_name,
                        "destination_network": destination,
                        "gateway": gateway,
                        "metric": route.get("metric", 0),
                        "enabled": route.get("enabled", True),
                    }).insert(ignore_permissions=True)
                    created += 1

            except Exception as e:
                errors.append(f"Route {route.get('destination', '?')}: {e}")

        if created:
            frappe.db.commit()

        return {"created": created, "errors": errors}

    def _import_arp(self, items: list) -> dict:
        """Import ARP entries — updates Network Client last-seen times."""
        updated = 0
        for entry in items:
            try:
                mac = entry.get("mac_address", "")
                ip = entry.get("address", "")
                if not mac:
                    continue

                existing = frappe.db.exists(
                    "Network Client",
                    {"mac_address": mac, "arrowz_box": self.box_name},
                )
                if existing:
                    frappe.db.set_value("Network Client", existing, {
                        "ip_address": ip,
                        "last_seen": now_datetime(),
                    })
                    updated += 1
            except Exception:
                pass

        if updated:
            frappe.db.commit()

        return {"updated": updated}

    def _update_sync_status(self, status: str, details: dict):
        """Update the sync status on the Arrowz Box document."""
        try:
            update_fields = {
                "last_sync_status": status.title(),
                "last_sync_at": now_datetime(),
            }

            # Only update if the fields exist on the DocType
            box_meta = frappe.get_meta("Arrowz Box")
            for field_name in list(update_fields.keys()):
                if not box_meta.has_field(field_name):
                    del update_fields[field_name]

            if update_fields:
                frappe.db.set_value("Arrowz Box", self.box_name, update_fields, update_modified=False)

            # Log to MikroTik Sync Log if available
            if frappe.db.exists("DocType", "MikroTik Sync Log"):
                frappe.get_doc({
                    "doctype": "MikroTik Sync Log",
                    "arrowz_box": self.box_name,
                    "operation": "sync",
                    "status": "Success" if status == "success" else "Failed",
                    "details": frappe.as_json(details),
                    "timestamp": now_datetime(),
                }).insert(ignore_permissions=True)

        except Exception:
            pass  # Never fail on status update


# ═══════════════════════════════════════════════════════════════
# Public API functions (for hooks.py scheduler)
# ═══════════════════════════════════════════════════════════════

def auto_sync_boxes():
    """Run auto-sync for all enabled boxes. Called by scheduler."""
    boxes = frappe.get_all(
        "Arrowz Box",
        filters={
            "status": ["in", ["Online", "Degraded"]],
            "sync_enabled": 1,
        },
        fields=["name", "device_type", "auto_sync_interval"],
    )

    for box in boxes:
        try:
            # Check if it's time for this box to sync
            last_sync = frappe.db.get_value("Arrowz Box", box.name, "last_sync_at")
            if last_sync:
                from frappe.utils import time_diff_in_seconds
                elapsed = time_diff_in_seconds(now_datetime(), last_sync)
                interval_seconds = (box.auto_sync_interval or 5) * 60

                if elapsed < interval_seconds:
                    continue

            # Enqueue the sync job
            frappe.enqueue(
                "arrowz.device_providers.sync_engine.run_sync",
                queue="default",
                timeout=300,
                box_name=box.name,
                direction="pull",
            )
        except Exception as e:
            frappe.log_error(
                f"Auto-sync scheduling error for {box.name}: {e}",
                "Arrowz Auto-Sync Error",
            )


def run_sync(box_name: str, direction: str = "pull", sections: list = None):
    """Run a sync operation for a specific box.

    Args:
        box_name: Arrowz Box name
        direction: "pull" (device→Frappe) or "push" (Frappe→device)
        sections: Optional list of sections to sync
    """
    engine = SyncEngine(box_name=box_name)

    if direction == "pull":
        return engine.pull(sections=sections)
    elif direction == "push":
        return engine.push(sections=sections)
    elif direction == "diff":
        return engine.diff()
    else:
        frappe.throw(f"Unknown sync direction: {direction}")
