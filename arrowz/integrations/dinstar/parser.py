# Copyright (c) 2026, Arrowz Team
# License: MIT

"""
Dinstar HTML/JS Parser — Extracts structured data from Dinstar web pages.

The Dinstar web UI renders data via embedded JavaScript in HTML pages using
patterns like:
  - document.write("<tr>...</tr>")  → table rows with stats
  - var text = '{JSON}';            → inline JSON objects  
  - MM_callJS(arg1, arg2, ...)      → onLoad function args
  - <input name="..." value="...">  → form field values

This module provides parsers for each pattern.
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from html.parser import HTMLParser


class DinstarParser:
    """Parses Dinstar web page HTML to extract structured data."""

    # ─── JSON in var text = '...'; ──────────────────────────────

    @staticmethod
    def parse_json_var(html: str, var_name: str = "text") -> Optional[Dict]:
        """
        Extract JSON from: var <var_name> = '{...}';
        
        Args:
            html: Raw HTML page content
            var_name: JavaScript variable name (default: "text")
            
        Returns:
            Parsed JSON dict or None
        """
        pattern = rf"var\s+{var_name}\s*=\s*'(\{{.*?\}})'\s*;"
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None

    # ─── MM_callJS onLoad args ──────────────────────────────────

    @staticmethod
    def parse_onload_args(html: str) -> Dict[str, str]:
        """
        Extract arguments from <body onLoad="MM_callJS(...)">
        
        Returns dict with positional arg names based on the function definition.
        """
        # Get function definition parameter names
        func_match = re.search(
            r'function\s+MM_callJS\s*\(([^)]*)\)', html
        )
        param_names = []
        if func_match:
            param_names = [p.strip() for p in func_match.group(1).split(",") if p.strip()]

        # Get call arguments from onLoad
        call_match = re.search(
            r'onLoad\s*=\s*"MM_callJS\(([^"]*)\)"', html
        )
        if not call_match:
            return {}

        raw_args = call_match.group(1)
        # Parse arguments (may be quoted strings or numbers)
        args = []
        for arg in re.findall(r"'([^']*)'|(\d+)", raw_args):
            args.append(arg[0] if arg[0] else arg[1])

        result = {}
        for i, val in enumerate(args):
            key = param_names[i] if i < len(param_names) else f"arg{i}"
            result[key] = val

        return result

    # ─── document.write table rows ──────────────────────────────

    @staticmethod
    def parse_table_rows(html: str) -> List[List[str]]:
        """
        Extract table data from document.write("<tr>...</tr>") patterns.
        
        Returns list of rows, each row is list of cell values.
        """
        rows = []
        # Find all document.write containing <tr>
        doc_write_match = re.search(
            r'document\.write\s*\(\s*"((?:<tr[^"]*)+)"\s*\)', html, re.DOTALL
        )
        if not doc_write_match:
            return rows

        content = doc_write_match.group(1)
        # Split into rows
        tr_parts = re.split(r'<tr[^>]*>', content)
        for tr in tr_parts:
            if not tr.strip():
                continue
            cells = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.DOTALL)
            if cells:
                # Clean HTML from cell values
                clean_cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                rows.append(clean_cells)

        return rows

    # ─── Form field values ──────────────────────────────────────

    @staticmethod
    def parse_form_fields(html: str) -> Dict[str, str]:
        """
        Extract name/value pairs from <input> and <select> tags.
        """
        fields = {}
        # Input fields with value
        for match in re.finditer(
            r'<input[^>]*name\s*=\s*"([^"]*)"[^>]*value\s*=\s*"([^"]*)"',
            html
        ):
            fields[match.group(1)] = match.group(2)

        # Also check value before name
        for match in re.finditer(
            r'<input[^>]*value\s*=\s*"([^"]*)"[^>]*name\s*=\s*"([^"]*)"',
            html
        ):
            if match.group(2) not in fields:
                fields[match.group(2)] = match.group(1)

        # Textareas
        for match in re.finditer(
            r'<textarea[^>]*name\s*=\s*"([^"]*)"[^>]*>(.*?)</textarea>',
            html, re.DOTALL
        ):
            fields[match.group(1)] = match.group(2).strip()

        # Radio buttons (only checked ones)
        for match in re.finditer(
            r'<input[^>]*name\s*=\s*"([^"]*)"[^>]*value\s*=\s*"([^"]*)"[^>]*checked',
            html
        ):
            fields[match.group(1)] = match.group(2)

        # Checkbox (checked = on)
        for match in re.finditer(
            r'<input[^>]*name\s*=\s*"([^"]*)"[^>]*type\s*=\s*"checkbox"[^>]*checked',
            html
        ):
            fields[match.group(1)] = "on"

        return fields

    # ─── Select options ─────────────────────────────────────────

    @staticmethod
    def parse_select_options(html: str, select_name: str) -> List[Dict[str, str]]:
        """Extract options from a <select> element."""
        options = []
        # Find the select element
        select_match = re.search(
            rf'<select[^>]*name\s*=\s*"{select_name}"[^>]*>(.*?)</select>',
            html, re.DOTALL
        )
        if select_match:
            for opt in re.finditer(
                r'<option[^>]*value\s*=\s*"([^"]*)"[^>]*>(.*?)</option>',
                select_match.group(1)
            ):
                selected = 'selected' in opt.group(0)
                options.append({
                    "value": opt.group(1),
                    "label": re.sub(r'<[^>]+>', '', opt.group(2)).strip(),
                    "selected": selected,
                })

        return options

    # ─── System Info Parser ─────────────────────────────────────

    @staticmethod
    def parse_system_info(html: str) -> Dict[str, Any]:
        """
        Parse enSysInfo.htm → system info.
        
        Extracts from MM_callJS(TotalPort, IsSupportComplexCfg, WanMode,
            RouteModeFlag, VoiceVlanValid, ManageVlanValid, VPNEnable, NtpTime)
        Also extracts uptime from: var temp = 'seconds'; var d = Math.floor(h/24);
        """
        info = DinstarParser.parse_onload_args(html)

        # Uptime in seconds
        uptime_match = re.search(r"var\s+temp\s*=\s*'(\d+)'", html)
        if uptime_match:
            uptime_sec = int(uptime_match.group(1))
            days = uptime_sec // 86400
            hours = (uptime_sec % 86400) // 3600
            minutes = (uptime_sec % 3600) // 60
            info["uptime_seconds"] = uptime_sec
            info["uptime_formatted"] = f"{days}d {hours}h {minutes}m"

        return info

    # ─── Port Status Parser ─────────────────────────────────────

    @staticmethod
    def parse_port_status(html: str) -> List[Dict[str, Any]]:
        """
        Parse enWIAPortStatNew.htm → per-port GSM module status.
        
        Returns list of port dicts with: Clir, TxGain, RxGain, Apn,
        BandType, strBandType, NetWorkMode, SMSC, ModuReset, SetModule,
        SetCall, SetSMS, Modulepower, Modulepowername
        """
        data = DinstarParser.parse_json_var(html, "text")
        if data and "GSMStateNew" in data:
            ports = data["GSMStateNew"]
            for i, port in enumerate(ports):
                port["port_index"] = i
                port["port_name"] = f"Port {i}"
                port["gsm_port_name"] = f"gsm-port{i + 1}"
            return ports
        return []

    # ─── Call Statistics Parser ──────────────────────────────────

    @staticmethod
    def parse_call_stats(html: str) -> List[Dict[str, Any]]:
        """
        Parse enCallStat.htm → per-port call statistics.
        
        Returns list of dicts with: port, total, answered, failed, busy,
        no_answer, rejected, duration, asr
        """
        rows = DinstarParser.parse_table_rows(html)
        stats = []
        for row in rows:
            if len(row) >= 9:
                try:
                    stat = {
                        "port": int(row[0]),
                        "total_calls": int(row[1]),
                        "answered": int(row[2]),
                        "failed": int(row[3]),
                        "busy": int(row[4]),
                        "no_answer": int(row[5]),
                        "rejected": int(row[6]),
                        "duration_seconds": int(row[7]),
                        "asr_percent": float(row[8]) if row[8] else 0,
                    }
                    stats.append(stat)
                except (ValueError, IndexError):
                    pass
        return stats

    # ─── ECC Statistics Parser ───────────────────────────────────

    @staticmethod
    def parse_ecc_stats(html: str) -> List[Dict[str, Any]]:
        """
        Parse enEccStat.htm → per-port ECC (error cause code) statistics.
        """
        rows = DinstarParser.parse_table_rows(html)
        stats = []
        for row in rows:
            if len(row) >= 13:
                try:
                    stat = {
                        "port": int(row[0]),
                        "total_calls": int(row[1]),
                        "duration": row[2],  # "H:M" format
                        "answered": int(row[3]),
                        "busy": int(row[4]),
                        "no_answer": int(row[5]),
                        "no_carrier": int(row[6]),
                        "no_dialtone": int(row[7]),
                        "congestion": int(row[8]),
                        "unallocated_number": int(row[9]),
                        "normal_clearing": int(row[10]),
                        "call_rejected": int(row[11]),
                        "other": int(row[12]),
                    }
                    stats.append(stat)
                except (ValueError, IndexError):
                    pass
        return stats

    # ─── Port Info Parser ────────────────────────────────────────

    @staticmethod
    def parse_port_info(html: str) -> List[Dict[str, str]]:
        """
        Parse enPortInfo.htm → port type and SIP account info.
        
        Returns list: [{port, type, active, sip_account}, ...]
        """
        rows = DinstarParser.parse_table_rows(html)
        ports = []
        for row in rows:
            if len(row) >= 4:
                ports.append({
                    "port": int(row[0]) if row[0].isdigit() else row[0],
                    "type": row[1],
                    "active": row[2],
                    "sip_account": row[3],
                })
        return ports

    # ─── GSM Operate Rules Parser ────────────────────────────────

    @staticmethod
    def parse_gsm_operate(html: str) -> List[Dict[str, Any]]:
        """
        Parse enGsmOperate.htm → GSM routing rules (prefix match/add/delete).
        """
        data = DinstarParser.parse_json_var(html, "text")
        if data and "GsmList" in data:
            rules = data["GsmList"]
            for i, rule in enumerate(rules):
                rule["rule_index"] = i
            return rules
        return []

    # ─── SMS Routing Parser ──────────────────────────────────────

    @staticmethod
    def parse_sms_routing(html: str) -> List[Dict[str, Any]]:
        """
        Parse enSMSRouting.htm → SMS routing rules.
        """
        data = DinstarParser.parse_json_var(html, "text")
        if data and "SMSRouteList" in data:
            routes = data["SMSRouteList"]
            for i, route in enumerate(routes):
                route["rule_index"] = i
            return routes
        return []

    # ─── SIP Config Parser ──────────────────────────────────────

    @staticmethod
    def parse_sip_config(html: str) -> Dict[str, Any]:
        """
        Parse enSIPCfg.htm → full SIP configuration.
        Returns all form fields as a flat dict.
        """
        fields = DinstarParser.parse_form_fields(html)
        # Categorize
        return {
            "sip_proxy": {
                "ip": fields.get("SipPxyIP", ""),
                "port": fields.get("SipPxyPort", ""),
                "transport": fields.get("SIPTransWay", ""),
                "register_interval": fields.get("SipRegIV", ""),
            },
            "timers": {
                "T1": fields.get("SipT1", ""),
                "T2": fields.get("SipT2", ""),
                "T4": fields.get("SipT4", ""),
                "TMax": fields.get("SipInvTmr", ""),
            },
            "session": {
                "timer_enable": fields.get("SessionTimerEn", ""),
                "session_expires": fields.get("SessionTimerExpire", ""),
                "min_se": fields.get("SessionTimerMinSE", ""),
            },
            "features": {
                "gsm_sip_binding": fields.get("GSM_SIP_Binding", ""),
                "allow_same_user": fields.get("SipAllowSameUser", ""),
                "imei_enable": fields.get("IMEI_En", ""),
                "imsi_enable": fields.get("IMSI_En", ""),
                "encryption": fields.get("Encryption", ""),
            },
            "raw": fields,
        }

    # ─── Media Config Parser ────────────────────────────────────

    @staticmethod
    def parse_media_config(html: str) -> Dict[str, Any]:
        """Parse enMediaParamCfg.htm → media/codec configuration."""
        fields = DinstarParser.parse_form_fields(html)
        return {
            "rtp_port": fields.get("RtpPort", ""),
            "silence_suppression": fields.get("SilenceSuppression", ""),
            "busytone_detect": fields.get("BusytoneDetect", ""),
            "udp_checksum": fields.get("UdpChecksumDetect", ""),
            "srtp_mode": fields.get("SRTPMode", ""),
            "call_progress_tone": fields.get("CallProgressTone", ""),
            "dtmf_method": fields.get("DTMFMethod", ""),
            "dtmf_payload": fields.get("Payload2833", ""),
            "dtmf_volume": fields.get("DTMFVolume", ""),
            "dtmf_send_interval": fields.get("DTMFSendInterval", ""),
            "codec_1": fields.get("CoderName0", ""),
            "codec_1_pt": fields.get("CoderPT0", ""),
            "codec_1_ptime": fields.get("CoderPktTime0", ""),
            "ivr_duration": fields.get("IVRDuration", ""),
            "play_hint_to_port": fields.get("PlayHintToOPort", ""),
            "tone_ringback": fields.get("ToneRingBack", ""),
            "tone_busy": fields.get("ToneBusy", ""),
            "tone_dial": fields.get("ToneDial", ""),
            "raw": fields,
        }

    # ─── Network Config Parser ───────────────────────────────────

    @staticmethod
    def parse_network_config(html: str) -> Dict[str, Any]:
        """Parse enLocalNetwork.htm → network configuration."""
        fields = DinstarParser.parse_form_fields(html)
        return {
            "wan_mode": fields.get("WanGetIPMode", ""),
            "dhcp_ip": fields.get("TmpDhcpIP", ""),
            "dhcp_mask": fields.get("TmpDhcpMask", ""),
            "static_ip": fields.get("WanIP", ""),
            "static_mask": fields.get("WanMask", ""),
            "gateway": fields.get("GateWay", ""),
            "pppoe_user": fields.get("PPPoEAcc", ""),
            "wan_mtu": fields.get("WANMTU", ""),
            "lan_eth_mode": fields.get("LanEthMode", ""),
            "lan_ip": fields.get("LanIP", ""),
            "raw": fields,
        }

    # ─── Management Config Parser ────────────────────────────────

    @staticmethod
    def parse_manage_config(html: str) -> Dict[str, Any]:
        """Parse enManageCfg.htm → management settings."""
        fields = DinstarParser.parse_form_fields(html)
        return {
            "ntp_enabled": fields.get("NTPEnable", ""),
            "ntp_primary": fields.get("PrimNTPServAddr", ""),
            "ntp_secondary": fields.get("SecondNTPServAddr", ""),
            "web_port": fields.get("WebPort", ""),
            "web_port_ssl": fields.get("WebPortSSL", ""),
            "http_redirect": fields.get("HTTPState", ""),
            "telnet_port": fields.get("TelnetPort", ""),
            "telnet_enabled": fields.get("TelnetEnable", ""),
            "ssh_enabled": fields.get("SSHEnable", ""),
            "raw": fields,
        }
