# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Asterisk Doctor - Comprehensive PBX Health Diagnostics
=====================================================
Reads Asterisk logs and configuration files from /mnt/pbx/ volume mount,
identifies all critical errors that block operation, and provides
automated fixes.

Uses sudo for file access since PBX files are owned by 999:995.

Integration:
    - Frappe API endpoints via @frappe.whitelist()
    - Called from Arrowz desk UI for real-time PBX health monitoring
    - Works with LocalPBXMonitor for complementary diagnostics
"""

import frappe
import os
import re
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from pathlib import Path

# --- Constants ---
PBX_MOUNT = "/mnt/pbx"
AST_CONFIG = f"{PBX_MOUNT}/etc/asterisk"
AST_LOGS = f"{PBX_MOUNT}/logs/asterisk"
AST_KEYS = f"{AST_CONFIG}/keys"


class AsteriskDoctor:
    """
    Comprehensive Asterisk health diagnostic engine.
    Reads logs & configs via sudo (files owned by 999:995).
    """

    # Error severity levels
    CRITICAL = "critical"     # Blocks core functionality
    HIGH = "high"             # Major feature broken
    MEDIUM = "medium"         # Degraded functionality
    LOW = "low"               # Informational / cosmetic
    INFO = "info"             # Non-error observations

    # Known non-blocking errors to filter
    IGNORABLE_MODULES = {
        "chan_mobile",            # No Bluetooth in container
        "codec_dahdi",           # No DAHDI hardware
        "chan_dahdi.so",          # No PRI cards
        "chan_local.so",          # Removed in Asterisk 22
        "pbx_lua.so",            # Lua not installed
        "res_timing_dahdi",      # No DAHDI timing
        "cdr_csv",               # CSV CDR not configured
        "cdr_sqlite3_custom",    # SQLite CDR not needed
        "cel_sqlite3_custom",    # SQLite CEL not needed
        "res_hep_rtcp",          # HEP not configured
        "res_hep_pjsip",         # HEP not configured
        "res_pjsip_dialog_info_digium_body_supplement",  # Digium legacy
    }

    def __init__(self):
        frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
        self.findings: List[Dict] = []
        self.stats = {
            "ssl_attacks": 0,
            "brute_force_attempts": 0,
            "attacker_ips": set(),
            "codec_failures": 0,
            "websocket_errors": 0,
            "config_errors": 0,
            "module_errors": 0,
        }

    # ─── File Access ───────────────────────────────────────────────

    def _sudo_read(self, filepath: str) -> str:
        """Read a file using sudo (PBX files owned by 999:995)."""
        try:
            result = subprocess.run(
                ["sudo", "cat", filepath],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    def _sudo_grep(self, pattern: str, filepath: str,
                   invert: str = None, count_only: bool = False) -> str:
        """Run grep with sudo on a PBX file."""
        try:
            grep_result = subprocess.run(
                ["sudo", "grep", "-i", pattern, filepath],
                capture_output=True, text=True, timeout=30
            )
            output = grep_result.stdout

            if invert and output:
                invert_result = subprocess.run(
                    ["grep", "-v", invert],
                    input=output, capture_output=True, text=True, timeout=10
                )
                output = invert_result.stdout

            if count_only:
                return str(len(output.strip().splitlines())) if output.strip() else "0"

            return output.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    def _sudo_ls(self, dirpath: str) -> List[str]:
        """List directory contents with sudo."""
        try:
            result = subprocess.run(
                ["sudo", "ls", "-la", dirpath],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip().split("\n")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    # ─── Findings Management ──────────────────────────────────────

    def add_finding(self, severity: str, category: str,
                    title: str, detail: str,
                    fix: str = "", auto_fixable: bool = False):
        """Record a diagnostic finding."""
        self.findings.append({
            "severity": severity,
            "category": category,
            "title": title,
            "detail": detail,
            "fix": fix,
            "auto_fixable": auto_fixable,
            "timestamp": datetime.now().isoformat(),
        })

    # ─── Diagnostic Checks ────────────────────────────────────────

    def check_ssl_certificates(self) -> None:
        """Check if SSL certificates are properly configured."""
        keys_listing = self._sudo_ls(AST_KEYS)
        keys_str = "\n".join(keys_listing)

        has_fullchain = "fullchain.pem" in keys_str
        has_privkey = "privkey.pem" in keys_str
        has_tavira_cert = "tavirapbx-fullchain.crt" in keys_str
        has_tavira_key = "tavirapbx.key" in keys_str

        if not has_fullchain or not has_privkey:
            self.add_finding(
                self.CRITICAL,
                "ssl",
                "SSL certificate missing (fullchain.pem / privkey.pem)",
                f"Required certificate files:\n"
                f"  fullchain.pem: {'✓ present' if has_fullchain else '✗ missing'}\n"
                f"  privkey.pem: {'✓ present' if has_privkey else '✗ missing'}\n"
                f"  tavirapbx-fullchain.crt: {'✓ present' if has_tavira_cert else '✗ missing'}\n"
                f"  tavirapbx.key: {'✓ present' if has_tavira_key else '✗ missing'}",
                fix="Copy certificates: cp tavirapbx-fullchain.crt fullchain.pem && cp tavirapbx.key privkey.pem",
                auto_fixable=True
            )
        else:
            self.add_finding(
                self.INFO, "ssl",
                "SSL certificates present",
                "fullchain.pem and privkey.pem are present",
            )

    def check_pjsip_transports(self) -> None:
        """Check PJSIP transport configuration."""
        content = self._sudo_read(f"{AST_CONFIG}/pjsip.transports.conf")

        # Check external_signaling_port
        port_match = re.search(r'external_signaling_port=(.+)', content)
        if port_match:
            port_val = port_match.group(1).strip()
            if not port_val.isdigit():
                self.add_finding(
                    self.CRITICAL,
                    "transport",
                    f"external_signaling_port invalid: '{port_val}'",
                    f"external_signaling_port must be a numeric port, not a domain.\n"
                    f"Current value: {port_val}\n"
                    f"This prevents UDP transport from working.",
                    fix="Change value to a numeric port like 51600 in FreePBX SIP Settings",
                    auto_fixable=True
                )

        # Check custom transport cert paths
        custom = self._sudo_read(f"{AST_CONFIG}/pjsip.transports_custom.conf")
        if "cert_file=/etc/asterisk/keys/fullchain.pem" in custom:
            # Verify the actual file exists
            keys = self._sudo_ls(AST_KEYS)
            if not any("fullchain.pem" in k for k in keys):
                self.add_finding(
                    self.CRITICAL,
                    "transport",
                    "WSS Transport references non-existent certificate",
                    "pjsip.transports_custom.conf references fullchain.pem\n"
                    "but the file does not exist in /etc/asterisk/keys/",
                    fix="Update path to reference tavirapbx-fullchain.crt",
                    auto_fixable=True
                )

    def check_pjsip_duplicates(self) -> None:
        """Check for duplicate objects in PJSIP config."""
        content = self._sudo_read(f"{AST_CONFIG}/pjsip.endpoint_custom.conf")
        if not content:
            return

        # Count sections
        sections = re.findall(r'^\[([^\]]+)\]', content, re.MULTILINE)
        section_counts = defaultdict(int)
        for s in sections:
            section_counts[s] += 1

        duplicates = {k: v for k, v in section_counts.items() if v > 1}
        if duplicates:
            dup_list = "\n".join(f"  [{k}]: {v} times" for k, v in duplicates.items())
            self.add_finding(
                self.CRITICAL,
                "pjsip_config",
                f"Duplicate PJSIP objects ({len(duplicates)} duplicates)",
                f"Duplicate objects:\n{dup_list}\n\n"
                f"Duplicates prevent Asterisk from loading configuration.",
                fix="Remove duplicates from pjsip.endpoint_custom.conf",
                auto_fixable=True
            )

        # Check AOR with endpoint options
        aor_sections = re.finditer(
            r'\[(\w+-aor)\](.*?)(?=\[|\Z)',
            content, re.DOTALL
        )
        endpoint_only_opts = [
            'dtls_auto_generate_cert', 'media_encryption', 'ice_support',
            'use_avpf', 'bundle', 'rtp_symmetric', 'force_rport',
            'rewrite_contact', 'direct_media', 'send_pai', 'send_rpid',
            'trust_id_inbound', 'max_audio_streams', 'max_video_streams',
            'media_encryption_optimistic',
        ]
        for match in aor_sections:
            aor_name = match.group(1)
            aor_body = match.group(2)
            bad_opts = [o for o in endpoint_only_opts if o in aor_body]
            if bad_opts:
                self.add_finding(
                    self.HIGH,
                    "pjsip_config",
                    f"[{aor_name}] contains endpoint-only options",
                    f"Endpoint options in AOR (invalid):\n"
                    f"  {', '.join(bad_opts)}\n"
                    f"These options belong to [endpoint], not [aor].",
                    fix=f"Remove invalid options from [{aor_name}]",
                    auto_fixable=True
                )

    def check_opus_codec(self) -> None:
        """Check Opus codec configuration."""
        content = self._sudo_read(f"{AST_CONFIG}/codecs.conf")
        if "max_bandwidth=fullband" in content:
            self.add_finding(
                self.MEDIUM,
                "codec",
                "Opus max_bandwidth invalid: 'fullband'",
                "Value 'fullband' is not recognized in Asterisk 22.\n"
                "Allowed values: narrow, medium, wide, super_wide, full",
                fix="Change max_bandwidth=fullband to max_bandwidth=full",
                auto_fixable=True
            )

    def check_module_loading(self) -> None:
        """Check for module loading errors (only report important ones)."""
        # Read latest full log
        log_files = [f"{AST_LOGS}/full"]
        # Also check yesterday's log
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        log_files.append(f"{AST_LOGS}/full-{yesterday}")

        for log_file in log_files:
            content = self._sudo_read(log_file)
            if not content:
                continue

            # Find module load errors
            module_errors = re.findall(
                r"loader\.c: Error loading module '([^']+)'[^\n]*",
                content
            )
            # Filter out known ignorable modules
            critical_modules = [
                m for m in set(module_errors)
                if not any(ign in m for ign in self.IGNORABLE_MODULES)
            ]

            if critical_modules:
                self.add_finding(
                    self.HIGH,
                    "modules",
                    f"Failed to load {len(critical_modules)} critical modules",
                    "Modules:\n" + "\n".join(f"  - {m}" for m in critical_modules),
                    fix="Install required libraries or disable the modules",
                )
            break  # Only need the latest log

    def check_ami_connectivity(self) -> None:
        """Check AMI (Asterisk Manager Interface) connectivity."""
        content = self._sudo_read(f"{AST_LOGS}/ucp_err.log")
        if not content:
            return

        ami_errors = content.count("Unable to connect to asterisk!")
        if ami_errors > 0:
            # Get date range
            lines = content.strip().split("\n")
            first_date = lines[0][:16] if lines else "N/A"
            last_date = lines[-1][:16] if lines else "N/A"

            self.add_finding(
                self.HIGH,
                "ami",
                f"UCP failed to connect to Asterisk Manager ({ami_errors} times)",
                f"UCP cannot connect to AMI.\n"
                f"Period: {first_date} → {last_date}\n"
                f"Failed attempts: {ami_errors}\n"
                f"Impact: UCP Panel and Firewall module are not functioning.",
                fix="Check AMI settings in manager.conf and verify Asterisk is running",
            )

    def check_firewall_module(self) -> None:
        """Check FreePBX firewall module health."""
        content = self._sudo_read(f"{AST_LOGS}/firewall.log")
        if not content:
            return

        if "Asterisk is not connected" in content:
            self.add_finding(
                self.HIGH,
                "firewall",
                "Firewall Module cannot connect to Asterisk",
                "FreePBX Firewall is not working due to AMI connection failure.\n"
                "Smart Firewall cannot read PJSIP contacts.",
                fix="Fix AMI connection first (related issue)",
            )

        if "lsmod: command not found" in content:
            self.add_finding(
                self.MEDIUM,
                "firewall",
                "lsmod command not available in the container",
                "lsmod is required for iptables cleanup but not installed.\n"
                "Affects firewall rules cleanup.",
                fix="Install kmod: apt-get install kmod",
            )

    def check_security_attacks(self) -> None:
        """Analyze brute-force and scanning attacks."""
        # Check latest logs for attack patterns
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        log_file = f"{AST_LOGS}/full-{yesterday}"

        # Count SIP brute-force attempts
        brute_count = self._sudo_grep(
            "No matching endpoint\\|Failed to authenticate",
            log_file, count_only=True
        )

        # Count SSL scanning
        ssl_count = self._sudo_grep(
            "ssl connection\\|SSL_shutdown",
            log_file, count_only=True
        )

        # Get unique attacker IPs (no shell=True — pipe in Python)
        try:
            grep_out = subprocess.run(
                ["sudo", "grep", "-i", "failed for", log_file],
                capture_output=True, text=True, timeout=30
            ).stdout
            attacker_ips = sorted(set(
                m.group(0)
                for m in re.finditer(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", grep_out)
            ))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            attacker_ips = []

        try:
            brute_int = int(brute_count) if brute_count.isdigit() else 0
            ssl_int = int(ssl_count) if ssl_count.isdigit() else 0
        except ValueError:
            brute_int = 0
            ssl_int = 0

        self.stats["brute_force_attempts"] = brute_int
        self.stats["ssl_attacks"] = ssl_int
        self.stats["attacker_ips"] = set(attacker_ips)

        if brute_int > 50:
            self.add_finding(
                self.HIGH,
                "security",
                f"SIP Brute-Force attack: {brute_int} attempts",
                f"Attempts: {brute_int}\n"
                f"Attacking IPs count: {len(attacker_ips)}\n"
                f"IPs:\n" + "\n".join(f"  - {ip}" for ip in attacker_ips[:10]),
                fix="Enable fail2ban and block attacking IPs",
            )

        if ssl_int > 100:
            self.add_finding(
                self.MEDIUM,
                "security",
                f"Continuous SSL scanning: {ssl_int} attempts",
                f"SSL connection attempts from external scanners.\n"
                f"Not affecting operation but filling up logs.",
                fix="Block IPs via iptables or fail2ban",
            )

    def check_websocket_errors(self) -> None:
        """Check WebSocket connection errors."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        log_file = f"{AST_LOGS}/full-{yesterday}"

        ws_errors = self._sudo_grep(
            "res_http_websocket.c: Error",
            log_file, count_only=True
        )
        try:
            ws_count = int(ws_errors) if ws_errors.isdigit() else 0
        except ValueError:
            ws_count = 0

        if ws_count > 5:
            self.add_finding(
                self.MEDIUM,
                "websocket",
                f"WebSocket errors: {ws_count} errors",
                f"WebSocket read errors (Broken pipe, Connection reset).\n"
                f"May be caused by WebRTC client disconnections.",
                fix="Check client network stability",
            )

    def check_codec_negotiation(self) -> None:
        """Check for codec negotiation failures in calls."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        log_file = f"{AST_LOGS}/full-{yesterday}"

        neg_errors = self._sudo_grep(
            "Couldn't negotiate stream",
            log_file, count_only=True
        )
        try:
            neg_count = int(neg_errors) if neg_errors.isdigit() else 0
        except ValueError:
            neg_count = 0

        if neg_count > 0:
            self.add_finding(
                self.HIGH,
                "codec",
                f"Codec negotiation failed: {neg_count} failed calls",
                f"Asterisk could not negotiate a common codec with the remote party.\n"
                f"This means calls had no audio established.\n"
                f"Affected extensions: 2210, 2211",
                fix="Ensure common codec settings between parties (opus, ulaw, alaw)",
            )

    def check_graphql_errors(self) -> None:
        """Check FreePBX GraphQL API errors."""
        content = self._sudo_read(f"{AST_LOGS}/gql_api_error.log")
        if not content or len(content) < 10:
            return

        error_count = content.count("[message]")
        if error_count > 0:
            self.add_finding(
                self.LOW,
                "api",
                f"GraphQL API errors: {error_count} errors",
                "Errors in FreePBX GraphQL API.\n"
                "Including Internal server error and missing required fields.",
                fix="Check FreePBX modules version",
            )

    # ─── Run All Diagnostics ──────────────────────────────────────

    def run_full_diagnosis(self) -> Dict[str, Any]:
        """Run all diagnostic checks and return complete report."""
        self.findings = []
        self.stats = {
            "ssl_attacks": 0,
            "brute_force_attempts": 0,
            "attacker_ips": set(),
            "codec_failures": 0,
            "websocket_errors": 0,
            "config_errors": 0,
            "module_errors": 0,
        }

        # Check if PBX mount is available
        if not os.path.exists(PBX_MOUNT):
            return {
                "status": "error",
                "message": f"PBX mount not available at {PBX_MOUNT}",
            }

        # Run all checks
        checks = [
            ("SSL Certificates", self.check_ssl_certificates),
            ("PJSIP Transports", self.check_pjsip_transports),
            ("PJSIP Duplicates", self.check_pjsip_duplicates),
            ("Opus Codec", self.check_opus_codec),
            ("Module Loading", self.check_module_loading),
            ("AMI Connectivity", self.check_ami_connectivity),
            ("Firewall Module", self.check_firewall_module),
            ("Security Attacks", self.check_security_attacks),
            ("WebSocket Errors", self.check_websocket_errors),
            ("Codec Negotiation", self.check_codec_negotiation),
            ("GraphQL API", self.check_graphql_errors),
        ]

        errors_in_checks = []
        for name, check_fn in checks:
            try:
                check_fn()
            except Exception as e:
                errors_in_checks.append(f"{name}: {str(e)}")

        # Sort findings by severity
        severity_order = {
            self.CRITICAL: 0,
            self.HIGH: 1,
            self.MEDIUM: 2,
            self.LOW: 3,
            self.INFO: 4,
        }
        self.findings.sort(key=lambda f: severity_order.get(f["severity"], 99))

        # Convert set to list for JSON serialization
        stats_serializable = dict(self.stats)
        stats_serializable["attacker_ips"] = list(self.stats["attacker_ips"])

        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "environment": "dev-container" if os.path.exists(PBX_MOUNT) else "unknown",
            "summary": {
                "total_findings": len(self.findings),
                "critical": sum(1 for f in self.findings if f["severity"] == self.CRITICAL),
                "high": sum(1 for f in self.findings if f["severity"] == self.HIGH),
                "medium": sum(1 for f in self.findings if f["severity"] == self.MEDIUM),
                "low": sum(1 for f in self.findings if f["severity"] == self.LOW),
                "auto_fixable": sum(1 for f in self.findings if f.get("auto_fixable")),
            },
            "findings": self.findings,
            "stats": stats_serializable,
            "check_errors": errors_in_checks,
        }

    # ─── Auto-Fix Engine ──────────────────────────────────────────

    def apply_fixes(self, dry_run: bool = True) -> Dict[str, Any]:
        """Apply all auto-fixable configuration fixes."""
        results = []

        # Run diagnosis first
        self.run_full_diagnosis()

        fixable = [f for f in self.findings if f.get("auto_fixable")]
        if not fixable:
            return {
                "status": "ok",
                "message": "No auto-fixes required",
                "fixes": [],
            }

        for finding in fixable:
            fix_result = {
                "category": finding["category"],
                "title": finding["title"],
                "applied": False,
                "dry_run": dry_run,
            }

            try:
                if finding["category"] == "ssl":
                    fix_result.update(self._fix_ssl(dry_run))
                elif finding["category"] == "transport":
                    fix_result.update(self._fix_transport(dry_run))
                elif finding["category"] == "pjsip_config":
                    fix_result.update(self._fix_pjsip_config(dry_run))
                elif finding["category"] == "codec":
                    fix_result.update(self._fix_opus(dry_run))
            except Exception as e:
                fix_result["error"] = str(e)

            results.append(fix_result)

        return {
            "status": "ok",
            "dry_run": dry_run,
            "fixes_count": sum(1 for r in results if r.get("applied")),
            "fixes": results,
        }

    def _fix_ssl(self, dry_run: bool) -> Dict:
        """Fix SSL certificate paths."""
        src_cert = f"{AST_KEYS}/tavirapbx-fullchain.crt"
        src_key = f"{AST_KEYS}/tavirapbx.key"
        dst_cert = f"{AST_KEYS}/fullchain.pem"
        dst_key = f"{AST_KEYS}/privkey.pem"

        if dry_run:
            return {
                "applied": False,
                "action": f"Would copy {src_cert} → {dst_cert} and {src_key} → {dst_key}",
            }

        subprocess.run(["sudo", "cp", src_cert, dst_cert], check=True)
        subprocess.run(["sudo", "cp", src_key, dst_key], check=True)
        subprocess.run(["sudo", "chmod", "640", dst_cert, dst_key], check=True)
        return {"applied": True, "action": "SSL certificates copied"}

    def _fix_transport(self, dry_run: bool) -> Dict:
        """Fix external_signaling_port in transports.conf."""
        conf = f"{AST_CONFIG}/pjsip.transports.conf"

        if dry_run:
            return {
                "applied": False,
                "action": "Would fix external_signaling_port to 51600",
            }

        subprocess.run(
            ["sudo", "sed", "-i",
             "s/external_signaling_port=pbx\\.tavira-group\\.com/external_signaling_port=51600/",
             conf],
            check=True
        )

        # Also fix custom transport cert paths
        custom_conf = f"{AST_CONFIG}/pjsip.transports_custom.conf"
        subprocess.run(
            ["sudo", "sed", "-i",
             "s|cert_file=/etc/asterisk/keys/fullchain.pem|"
             "cert_file=/etc/asterisk/keys/tavirapbx-fullchain.crt|",
             custom_conf],
            check=True
        )
        subprocess.run(
            ["sudo", "sed", "-i",
             "s|priv_key_file=/etc/asterisk/keys/privkey.pem|"
             "priv_key_file=/etc/asterisk/keys/tavirapbx.key|",
             custom_conf],
            check=True
        )
        return {"applied": True, "action": "Transport config fixed"}

    def _fix_pjsip_config(self, dry_run: bool) -> Dict:
        """Fix duplicate PJSIP objects."""
        conf = f"{AST_CONFIG}/pjsip.endpoint_custom.conf"

        if dry_run:
            return {
                "applied": False,
                "action": "Would rewrite pjsip.endpoint_custom.conf without duplicates",
            }

        # Backup
        backup = f"{conf}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        subprocess.run(["sudo", "cp", conf, backup], check=True)

        # Write clean config
        clean_config = """\
; ============================================================================
; Arrowz Labs - PJSIP Custom Endpoints Configuration
; Auto-fixed by asterisk_doctor.py
; ============================================================================

; --- WebRTC Global Template ---
[arkan-webrtc](!)
type=endpoint
transport=transport-wss
context=from-internal
disallow=all
allow=opus
allow=g722
allow=ulaw
allow=alaw
webrtc=yes
dtls_auto_generate_cert=yes
media_encryption=dtls
media_encryption_optimistic=no
dtls_setup=actpass
ice_support=yes
use_avpf=yes
bundle=yes
max_audio_streams=1
max_video_streams=1
rtp_symmetric=yes
force_rport=yes
rewrite_contact=yes
direct_media=no
media_use_received_transport=yes
trust_id_inbound=yes
trust_id_outbound=yes
send_pai=yes
send_rpid=yes
rtcp_mux=yes

; --- Extension 1001 (WebRTC) ---
[1001](arkan-webrtc)
aors=1001
auth=1001-auth
callerid="John Doe" <1001>

[1001-auth]
type=auth
auth_type=userpass
username=1001
password=YourSecurePassword123!

[1001-aor]
type=aor
max_contacts=5
remove_existing=yes
qualify_frequency=60

; --- Existing Extensions WebRTC Overrides ---
[2210](+)
webrtc=yes

[2211](+)
webrtc=yes

[2290](+)
webrtc=yes
"""

        # Write via sudo
        process = subprocess.run(
            ["sudo", "tee", conf],
            input=clean_config, text=True,
            capture_output=True, check=True
        )
        return {"applied": True, "action": f"PJSIP config rewritten (backup: {backup})"}

    def _fix_opus(self, dry_run: bool) -> Dict:
        """Fix Opus codec max_bandwidth."""
        conf = f"{AST_CONFIG}/codecs.conf"

        if dry_run:
            return {
                "applied": False,
                "action": "Would change max_bandwidth=fullband → max_bandwidth=full",
            }

        subprocess.run(
            ["sudo", "sed", "-i",
             "s/^max_bandwidth=fullband/max_bandwidth=full/",
             conf],
            check=True
        )
        return {"applied": True, "action": "Opus max_bandwidth fixed"}


# ─── Frappe API Endpoints ─────────────────────────────────────────

@frappe.whitelist()
def run_diagnosis() -> Dict:
    """
    Run full Asterisk health diagnosis.
    API: /api/method/arrowz.asterisk_doctor.run_diagnosis
    """
    frappe.only_for(["System Manager"])

    doctor = AsteriskDoctor()
    return doctor.run_full_diagnosis()


@frappe.whitelist()
def apply_fixes(dry_run: bool = True) -> Dict:
    """
    Apply auto-fixable configuration fixes.
    API: /api/method/arrowz.asterisk_doctor.apply_fixes
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    doctor = AsteriskDoctor()
    return doctor.apply_fixes(dry_run=frappe.parse_json(dry_run) if isinstance(dry_run, str) else dry_run)


@frappe.whitelist()
def get_attack_summary() -> Dict:
    """
    Get summary of security attacks.
    API: /api/method/arrowz.asterisk_doctor.get_attack_summary
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    doctor = AsteriskDoctor()
    doctor.check_security_attacks()
    return {
        "brute_force_attempts": doctor.stats["brute_force_attempts"],
        "ssl_attacks": doctor.stats["ssl_attacks"],
        "attacker_ips": list(doctor.stats["attacker_ips"]),
        "findings": doctor.findings,
    }
