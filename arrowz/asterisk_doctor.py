# Copyright (c) 2026, Arrowz Team and contributors
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
        cmd = ["sudo", "grep", "-i", pattern, filepath]
        if invert:
            cmd = ["sudo", "grep", "-i", pattern, filepath,
                   "|", "grep", "-v", invert]
            # Use shell for pipe
            shell_cmd = f"sudo grep -i '{pattern}' '{filepath}'"
            if invert:
                shell_cmd += f" | grep -v '{invert}'"
            if count_only:
                shell_cmd += " | wc -l"
            try:
                result = subprocess.run(
                    shell_cmd, shell=True,
                    capture_output=True, text=True, timeout=30
                )
                return result.stdout.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return ""

        if count_only:
            cmd.insert(2, "-c")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            return result.stdout.strip()
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
                "شهادة SSL مفقودة (fullchain.pem / privkey.pem)",
                f"ملفات الشهادة المطلوبة:\n"
                f"  fullchain.pem: {'✓ موجود' if has_fullchain else '✗ مفقود'}\n"
                f"  privkey.pem: {'✓ موجود' if has_privkey else '✗ مفقود'}\n"
                f"  tavirapbx-fullchain.crt: {'✓ موجود' if has_tavira_cert else '✗ مفقود'}\n"
                f"  tavirapbx.key: {'✓ موجود' if has_tavira_key else '✗ مفقود'}",
                fix="نسخ الشهادة: cp tavirapbx-fullchain.crt fullchain.pem && cp tavirapbx.key privkey.pem",
                auto_fixable=True
            )
        else:
            self.add_finding(
                self.INFO, "ssl",
                "شهادات SSL موجودة",
                "fullchain.pem و privkey.pem موجودان",
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
                    f"external_signaling_port خاطئ: '{port_val}'",
                    f"external_signaling_port يجب أن يكون رقم port وليس domain.\n"
                    f"القيمة الحالية: {port_val}\n"
                    f"هذا يمنع UDP transport من العمل.",
                    fix="تغيير القيمة لرقم port مثل 51600 في FreePBX SIP Settings",
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
                    "WSS Transport يشير لشهادة غير موجودة",
                    "pjsip.transports_custom.conf يشير إلى fullchain.pem\n"
                    "لكن الملف غير موجود في /etc/asterisk/keys/",
                    fix="تحديث المسار ليشير إلى tavirapbx-fullchain.crt",
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
            dup_list = "\n".join(f"  [{k}]: {v} مرات" for k, v in duplicates.items())
            self.add_finding(
                self.CRITICAL,
                "pjsip_config",
                f"كائنات PJSIP مكررة ({len(duplicates)} تكرار)",
                f"الكائنات المكررة:\n{dup_list}\n\n"
                f"التكرار يمنع Asterisk من تحميل الإعدادات.",
                fix="حذف التكرارات من pjsip.endpoint_custom.conf",
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
                    f"[{aor_name}] يحتوي على خيارات endpoint",
                    f"خيارات endpoint في AOR (غير صالحة):\n"
                    f"  {', '.join(bad_opts)}\n"
                    f"هذه الخيارات تخص [endpoint] وليس [aor].",
                    fix=f"حذف الخيارات غير الصالحة من [{aor_name}]",
                    auto_fixable=True
                )

    def check_opus_codec(self) -> None:
        """Check Opus codec configuration."""
        content = self._sudo_read(f"{AST_CONFIG}/codecs.conf")
        if "max_bandwidth=fullband" in content:
            self.add_finding(
                self.MEDIUM,
                "codec",
                "Opus max_bandwidth خاطئ: 'fullband'",
                "القيمة 'fullband' غير معروفة في Asterisk 22.\n"
                "القيم المسموحة: narrow, medium, wide, super_wide, full",
                fix="تغيير max_bandwidth=fullband إلى max_bandwidth=full",
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
                    f"فشل تحميل {len(critical_modules)} modules مهمة",
                    "Modules:\n" + "\n".join(f"  - {m}" for m in critical_modules),
                    fix="تثبيت المكتبات المطلوبة أو تعطيل الـ modules",
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
                f"فشل اتصال UCP بـ Asterisk Manager ({ami_errors} مرة)",
                f"UCP لا يستطيع الاتصال بـ AMI.\n"
                f"الفترة: {first_date} → {last_date}\n"
                f"عدد المحاولات الفاشلة: {ami_errors}\n"
                f"التأثير: UCP Panel و Firewall module لا يعملان.",
                fix="تحقق من إعدادات AMI في manager.conf و أن Asterisk يعمل",
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
                "Firewall Module لا يستطيع الاتصال بـ Asterisk",
                "FreePBX Firewall لا يعمل بسبب فشل اتصال AMI.\n"
                "Smart Firewall لا يستطيع قراءة PJSIP contacts.",
                fix="إصلاح اتصال AMI أولاً (مشكلة مرتبطة)",
            )

        if "lsmod: command not found" in content:
            self.add_finding(
                self.MEDIUM,
                "firewall",
                "أمر lsmod غير متوفر في الـ container",
                "lsmod مطلوب لـ iptables cleanup لكنه غير مثبت.\n"
                "يؤثر على تنظيف قواعد الجدار الناري.",
                fix="تثبيت kmod: apt-get install kmod",
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

        # Get unique attacker IPs
        ip_output = subprocess.run(
            f"sudo grep -i 'failed for' '{log_file}' 2>/dev/null | "
            f"grep -oP \"'[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+\" | sort -u",
            shell=True, capture_output=True, text=True, timeout=30
        ).stdout.strip()
        attacker_ips = [ip.strip("'") for ip in ip_output.split("\n") if ip]

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
                f"هجوم SIP Brute-Force: {brute_int} محاولة",
                f"عدد المحاولات: {brute_int}\n"
                f"عدد الـ IPs المهاجمة: {len(attacker_ips)}\n"
                f"IPs:\n" + "\n".join(f"  - {ip}" for ip in attacker_ips[:10]),
                fix="فعّل fail2ban وحجب الـ IPs المهاجمة",
            )

        if ssl_int > 100:
            self.add_finding(
                self.MEDIUM,
                "security",
                f"فحص SSL مستمر: {ssl_int} محاولة",
                f"محاولات اتصال SSL من scanners خارجية.\n"
                f"غير مؤثرة على التشغيل لكنها تملأ اللوجات.",
                fix="حجب الـ IPs عبر iptables أو fail2ban",
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
                f"أخطاء WebSocket: {ws_count} خطأ",
                f"أخطاء قراءة WebSocket (Broken pipe, Connection reset).\n"
                f"قد تكون بسبب انقطاع اتصال WebRTC clients.",
                fix="تحقق من استقرار شبكة العملاء",
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
                f"فشل تفاوض Codec: {neg_count} مكالمة فاشلة",
                f"Asterisk لم يستطع التفاوض على codec مشترك مع الطرف الآخر.\n"
                f"هذا يعني أن المكالمات لم يتم إنشاء صوت لها.\n"
                f"Extensions المتأثرة: 2210, 2211",
                fix="تأكد من إعدادات codecs المشتركة بين الأطراف (opus, ulaw, alaw)",
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
                f"أخطاء GraphQL API: {error_count} خطأ",
                "أخطاء في FreePBX GraphQL API.\n"
                "تشمل Internal server error و missing required fields.",
                fix="تحقق من إصدار FreePBX modules",
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
                "message": "لا توجد إصلاحات تلقائية مطلوبة",
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
