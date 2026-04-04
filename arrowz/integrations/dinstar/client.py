# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# License: MIT

"""
Dinstar UC2000-VE GSM Gateway — HTTP Client

Full-featured client for the Dinstar embedded web interface.
Handles authentication, session management, page fetching,
data parsing, and configuration updates via goform POST.

Architecture:
    The Dinstar web UI uses a cookie-based session (JSESSIONID).
    Pages are .htm files with embedded JavaScript that contain
    data as inline JSON, document.write() table rows, or
    MM_callJS() onLoad function arguments.
    Configuration changes POST to /goform/* endpoints.

Thread Safety:
    Each DinstarClient instance maintains its own requests.Session.
    For Frappe background jobs, create a new instance per job.

Usage:
    client = DinstarClient("10.10.1.2", "admin", "admin")
    client.login()
    
    # Read status
    info = client.get_system_info()
    ports = client.get_port_status()
    stats = client.get_call_stats()
    
    # Send SMS
    client.send_sms(port=7, number="01234567890", message="Hello")
    
    # Update config
    client.set_media_config(codec="PCMA", dtmf="RFC2833")
"""

import requests
from requests.exceptions import RequestException, Timeout
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode
import time
import json

from arrowz.integrations.dinstar.parser import DinstarParser
from arrowz.integrations.dinstar.constants import (
    DINSTAR_PAGES,
    DINSTAR_GOFORMS,
    PORT_STATUS_MAP,
    BAND_TYPE_MAP,
    NETWORK_MODE_MAP,
    CODEC_MAP,
    DTMF_METHOD_MAP,
    CALL_PROGRESS_TONE_MAP,
    SIP_TRANSPORT_MAP,
    SRTP_MODE_MAP,
    CALL_STAT_COLUMNS,
    ECC_STAT_COLUMNS,
)


class DinstarError(Exception):
    """Base exception for Dinstar client errors."""
    pass


class DinstarAuthError(DinstarError):
    """Authentication failed."""
    pass


class DinstarConnectionError(DinstarError):
    """Network connection error."""
    pass


class DinstarClient:
    """
    HTTP client for Dinstar UC2000-VE GSM Gateway web interface.
    
    Provides high-level methods for all device operations organized
    into categories:
    
    - System: info, uptime, restart, firmware
    - Ports: status, config, SIP accounts
    - Calls: stats, CDR, live calls
    - SMS: send, receive, routing, overview
    - GSM: signal, module control, events
    - Config: SIP, media, network, management
    - Groups: port groups, IP groups, digit maps
    - VPN: OpenVPN status and config
    
    Attributes:
        host: Device IP address
        username: Web admin username
        password: Web admin password
        protocol: http or https (default: https)
        verify_ssl: Whether to verify SSL certificates (default: False)
        timeout: Request timeout in seconds (default: 15)
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        protocol: str = "https",
        verify_ssl: bool = False,
        timeout: int = 15,
        port: Optional[int] = None,
    ):
        self.host = host
        self.username = username
        self.password = password
        self.protocol = protocol
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.port = port
        self.base_url = f"{protocol}://{host}"
        if port:
            self.base_url = f"{protocol}://{host}:{port}"

        self.session = requests.Session()
        self.session.verify = verify_ssl
        self._authenticated = False
        self._last_login = 0
        self._session_lifetime = 300  # Re-login every 5 minutes
        self.parser = DinstarParser()

    # ═══════════════════════════════════════════════════════════════
    # Authentication
    # ═══════════════════════════════════════════════════════════════

    def login(self) -> bool:
        """
        Authenticate with the Dinstar web interface.
        
        Returns:
            True if login succeeded
            
        Raises:
            DinstarAuthError: If authentication fails
            DinstarConnectionError: If device is unreachable
        """
        url = f"{self.base_url}{DINSTAR_GOFORMS['login']}"
        data = {
            "username": self.username,
            "password": self.password,
        }

        try:
            response = self.session.post(
                url,
                data=urlencode(data),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.timeout,
                allow_redirects=False,
            )

            # Dinstar returns 302 redirect on success, sets JSESSIONID cookie
            if response.status_code in (200, 302):
                if "JSESSIONID" in self.session.cookies.get_dict():
                    self._authenticated = True
                    self._last_login = time.time()
                    return True
                # Some firmware versions redirect without explicit cookie check
                self._authenticated = True
                self._last_login = time.time()
                return True

            raise DinstarAuthError(
                f"Login failed with status {response.status_code}"
            )

        except Timeout:
            raise DinstarConnectionError(
                f"Connection timeout to {self.host}"
            )
        except RequestException as e:
            raise DinstarConnectionError(
                f"Connection error to {self.host}: {str(e)}"
            )

    def _ensure_auth(self):
        """Ensure we have a valid session, re-login if expired."""
        if not self._authenticated or (
            time.time() - self._last_login > self._session_lifetime
        ):
            self.login()

    # ═══════════════════════════════════════════════════════════════
    # Low-level HTTP
    # ═══════════════════════════════════════════════════════════════

    def _get_page(self, page_key: str) -> str:
        """
        Fetch an HTML page from the device.
        
        Args:
            page_key: Key from DINSTAR_PAGES dict
            
        Returns:
            Raw HTML content
        """
        self._ensure_auth()
        path = DINSTAR_PAGES.get(page_key)
        if not path:
            raise DinstarError(f"Unknown page key: {page_key}")

        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except RequestException as e:
            raise DinstarConnectionError(f"Failed to fetch {page_key}: {e}")

    def _post_goform(
        self,
        goform_key: str,
        data: Dict[str, Any],
        extra_path: str = "",
    ) -> str:
        """
        POST to a goform endpoint.
        
        Args:
            goform_key: Key from DINSTAR_GOFORMS dict
            data: Form data to POST
            extra_path: Optional suffix to append to URL
            
        Returns:
            Response text
        """
        self._ensure_auth()
        path = DINSTAR_GOFORMS.get(goform_key)
        if not path:
            raise DinstarError(f"Unknown goform key: {goform_key}")

        url = f"{self.base_url}{path}{extra_path}"
        try:
            response = self.session.post(
                url,
                data=urlencode(data),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.timeout,
            )
            return response.text
        except RequestException as e:
            raise DinstarConnectionError(f"Failed to POST {goform_key}: {e}")

    def _get_goform(self, goform_key: str, params: Optional[Dict] = None) -> str:
        """GET request to a goform endpoint (for AJAX queries)."""
        self._ensure_auth()
        path = DINSTAR_GOFORMS.get(goform_key)
        if not path:
            raise DinstarError(f"Unknown goform key: {goform_key}")

        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(
                url, params=params, timeout=self.timeout
            )
            return response.text
        except RequestException as e:
            raise DinstarConnectionError(f"Failed to GET {goform_key}: {e}")

    # ═══════════════════════════════════════════════════════════════
    # SYSTEM INFORMATION
    # ═══════════════════════════════════════════════════════════════

    def get_system_info(self) -> Dict[str, Any]:
        """
        Get system information: model, uptime, WAN mode, NTP time, VPN status.
        
        Returns:
            {
                "TotalPort": "8",
                "WanMode": "DHCP",
                "VPNEnable": "checked",
                "NtpTime": "2026/03/02 21:53:00",
                "uptime_seconds": 2071,
                "uptime_formatted": "0d 0h 34m",
                ...
            }
        """
        html = self._get_page("system_info")
        info = self.parser.parse_system_info(html)
        info["_source"] = "enSysInfo.htm"
        return info

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary/dashboard overview via AJAX polling.
        
        The summary page uses AJAX to fetch live data. We try the
        goform endpoint directly.
        """
        try:
            text = self._get_goform("summary_query")
            if text and text.strip().startswith("{"):
                return json.loads(text)
        except Exception:
            pass

        # Fallback: parse the summary page
        html = self._get_page("summary")
        return self.parser.parse_onload_args(html)

    # ═══════════════════════════════════════════════════════════════
    # PORT STATUS & GSM MODULE
    # ═══════════════════════════════════════════════════════════════

    def get_port_status(self) -> List[Dict[str, Any]]:
        """
        Get per-port GSM module status.
        
        Returns list of port dicts:
            [{
                "port_index": 0,
                "port_name": "Port 0",
                "gsm_port_name": "gsm-port1",
                "Clir": "0",
                "TxGain": "3",
                "RxGain": "7",
                "Apn": "",
                "BandType": "512",
                "strBandType": "Default(Auto)",
                "NetWorkMode": "0",
                "SMSC": "+20112008000",
                "ModuReset": "Reset",
                "SetModule": "Block/Unblock",
                "SetCall": "Block/Unblock",
                "SetSMS": "Block/Unblock",
                "Modulepower": "ON/OFF",
                "Modulepowername": "ModulePowerOn/ModulePowerOff",
            }, ...]
        """
        html = self._get_page("wia_port_stat")
        ports = self.parser.parse_port_status(html)
        # Enrich with human-readable values
        for port in ports:
            bt = port.get("BandType", "")
            port["band_type_label"] = BAND_TYPE_MAP.get(str(bt), f"Unknown ({bt})")
            nm = port.get("NetWorkMode", "")
            port["network_mode_label"] = NETWORK_MODE_MAP.get(str(nm), f"Unknown ({nm})")
            port["SMSC"] = port.get("szSMSC", "")  # normalize key name
            port["has_sim"] = port["SMSC"] != ""
            port["is_powered"] = port.get("Modulepower", "") == "ON"
        return ports

    def get_port_info(self) -> List[Dict[str, str]]:
        """
        Get port type and SIP account mapping.
        
        Returns:
            [{"port": 0, "type": "GSM", "active": "Yes", "sip_account": "gsm-port1"}, ...]
        """
        html = self._get_page("port_info")
        return self.parser.parse_port_info(html)

    def reset_module(self, port: int) -> str:
        """Reset a GSM module on specified port."""
        return self._post_goform("module_reset_new", {"port": str(port)})

    def block_module(self, port: int) -> str:
        """Block a GSM module on specified port."""
        return self._post_goform("module_block_new", {"port": str(port), "action": "B"})

    def unblock_module(self, port: int) -> str:
        """Unblock a GSM module on specified port."""
        return self._post_goform("module_block_new", {"port": str(port), "action": "U"})

    def block_call(self, port: int) -> str:
        """Block calls on a specified port."""
        return self._post_goform("call_block_new", {"port": str(port), "action": "B"})

    def unblock_call(self, port: int) -> str:
        """Unblock calls on a specified port."""
        return self._post_goform("call_block_new", {"port": str(port), "action": "U"})

    def power_on_module(self, port: int) -> str:
        """Power ON a GSM module on specified port."""
        return self._post_goform("module_power_on", {"PortNo": str(port)})

    def power_off_module(self, port: int) -> str:
        """Power OFF a GSM module on specified port."""
        return self._post_goform("module_power_off", {"PortNo": str(port)})

    # ═══════════════════════════════════════════════════════════════
    # CALL STATISTICS & CDR
    # ═══════════════════════════════════════════════════════════════

    def get_call_stats(self) -> List[Dict[str, Any]]:
        """
        Get per-port call statistics.
        
        Returns list of per-port stats:
            [{"port": 0, "total_calls": 0, "answered": 0, ...}, ...]
        """
        html = self._get_page("call_stat")
        stats = self.parser.parse_call_stats(html)
        # Calculate totals
        totals = {
            "port": "TOTAL",
            "total_calls": sum(s.get("total_calls", 0) for s in stats),
            "answered": sum(s.get("answered", 0) for s in stats),
            "failed": sum(s.get("failed", 0) for s in stats),
            "busy": sum(s.get("busy", 0) for s in stats),
            "no_answer": sum(s.get("no_answer", 0) for s in stats),
            "rejected": sum(s.get("rejected", 0) for s in stats),
            "duration_seconds": sum(s.get("duration_seconds", 0) for s in stats),
        }
        total_calls = totals["total_calls"]
        totals["asr_percent"] = (
            round(totals["answered"] / total_calls * 100, 1)
            if total_calls > 0
            else 0
        )
        return {"ports": stats, "totals": totals}

    def get_ecc_stats(self) -> List[Dict[str, Any]]:
        """
        Get per-port ECC (Error Cause Code) statistics.
        Shows detailed breakdown of call failure reasons.
        """
        html = self._get_page("ecc_stat")
        return self.parser.parse_ecc_stats(html)

    def get_current_calls(self) -> List[Dict[str, Any]]:
        """Get currently active calls."""
        html = self._get_page("current_call_stat")
        return self.parser.parse_table_rows(html)

    def get_cdr_records(
        self,
        port: int = 255,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get Call Detail Records.
        
        Args:
            port: Port number (255 = all ports)
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
        """
        html = self._get_page("call_cdr")
        rows = self.parser.parse_table_rows(html)
        return rows

    # ═══════════════════════════════════════════════════════════════
    # SMS
    # ═══════════════════════════════════════════════════════════════

    def send_sms(
        self,
        port: int,
        number: str,
        message: str,
        encoding: str = "ASCII",
    ) -> str:
        """
        Send an SMS message.
        
        Args:
            port: GSM port to send from (0-7)
            number: Destination phone number
            message: Message text
            encoding: "ASCII" or "UCS2" (for Unicode)
            
        Returns:
            Response text from device
        """
        data = {
            "SendMode": "0",  # 0 = single, 1 = batch
            "Addressee": number,
            "MsgInfo": message,
            "Encoding": encoding,
            f"Index{port}": "on",
        }
        return self._post_goform("sms_send", data)

    def send_sms_batch(
        self,
        port: int,
        numbers: List[str],
        message: str,
        encoding: str = "ASCII",
    ) -> str:
        """
        Send SMS to multiple numbers.
        
        Args:
            port: GSM port to send from
            numbers: List of phone numbers
            message: Message text
            encoding: Character encoding
        """
        data = {
            "SendMode": "1",
            "Addressee": "\n".join(numbers),
            "MsgInfo": message,
            "Encoding": encoding,
            f"Index{port}": "on",
        }
        return self._post_goform("sms_send", data)

    def stop_sms_send(self) -> str:
        """Stop an ongoing SMS send operation."""
        return self._post_goform("sms_send_stop", {})

    def get_received_sms(
        self,
        port: int = 255,
        number_filter: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Get received SMS messages.
        
        Args:
            port: Port filter (255 = all)
            number_filter: Phone number filter
        """
        html = self._get_page("sms_recv")
        return self.parser.parse_table_rows(html)

    def get_sms_overview(self) -> List[Dict[str, Any]]:
        """
        Get SMS overview: per-port send/receive counts, limits.
        """
        html = self._get_page("sms_overview")
        return self.parser.parse_table_rows(html)

    def get_sms_routing(self) -> List[Dict[str, Any]]:
        """Get SMS routing rules."""
        html = self._get_page("sms_routing")
        return self.parser.parse_sms_routing(html)

    def set_sms_routing(self, rules: List[Dict]) -> str:
        """
        Update SMS routing rules.
        
        Args:
            rules: List of rule dicts with keys:
                enable, dest_num, src_mode, dest_value,
                prefix_to_add, digit_delete
        """
        data = {}
        for i, rule in enumerate(rules):
            data[f"enable{i}"] = rule.get("enable", "0")
            data[f"dest_num{i}"] = rule.get("dest_num", "")
            data[f"src_mode{i}"] = rule.get("src_mode", "0")
            data[f"dest_value{i}"] = rule.get("dest_value", "255")
            data[f"prefix_to_add{i}"] = rule.get("prefix_to_add", "")
            data[f"digit_delete{i}"] = rule.get("digit_delete", "")
        return self._post_goform("sms_routing", data)

    # ═══════════════════════════════════════════════════════════════
    # SIP CONFIGURATION
    # ═══════════════════════════════════════════════════════════════

    def get_sip_config(self) -> Dict[str, Any]:
        """Get full SIP configuration."""
        html = self._get_page("sip_cfg")
        return self.parser.parse_sip_config(html)

    def set_sip_config(self, **kwargs) -> str:
        """
        Update SIP configuration.
        
        Kwargs can include any SipCfg form field:
            SipPxyIP, SipPxyPort, SIPTransWay, SipRegIV,
            SipAllowSameUser, GSM_SIP_Binding, etc.
        """
        # Get current values first
        current = self.get_sip_config()
        data = current.get("raw", {})
        data.update(kwargs)
        return self._post_goform("sip_cfg", data)

    def get_port_config(self) -> Dict[str, Any]:
        """
        Get per-port SIP account configuration.
        
        Returns form fields for all ports:
            SipLocalPort[i], SipAcc[i], AuthenticateID[i],
            SipAccPsw[i], Register[i], TxGain[i], RxGain[i], etc.
        """
        html = self._get_page("port_list")
        return self.parser.parse_form_fields(html)

    def set_port_config(self, port: int, **kwargs) -> str:
        """
        Update a single port's SIP account settings.
        
        Args:
            port: Port index (0-7)
            **kwargs: Field values like SipAcc, SipAccPsw, TxGain, etc.
        """
        # Get all current config
        current = self.get_port_config()
        # Update specific port fields
        for key, value in kwargs.items():
            current[f"{key}{port}"] = value
        return self._post_goform("port_cfg", current)

    # ═══════════════════════════════════════════════════════════════
    # MEDIA CONFIGURATION
    # ═══════════════════════════════════════════════════════════════

    def get_media_config(self) -> Dict[str, Any]:
        """Get media/codec configuration."""
        html = self._get_page("media_param_cfg")
        config = self.parser.parse_media_config(html)
        # Add human-readable labels
        dtmf = config.get("dtmf_method", "")
        config["dtmf_method_label"] = DTMF_METHOD_MAP.get(str(dtmf), dtmf)
        tone = config.get("call_progress_tone", "")
        config["tone_label"] = CALL_PROGRESS_TONE_MAP.get(str(tone), tone)
        codec = config.get("codec_1_pt", "")
        config["codec_label"] = CODEC_MAP.get(str(codec), {}).get("label", codec)
        return config

    def set_media_config(self, **kwargs) -> str:
        """
        Update media configuration.
        
        Kwargs can include any MediaParamCfg form field:
            CoderName0, CoderPT0, DTMFMethod, CallProgressTone,
            SilenceSuppression, RtpPort, etc.
        """
        html = self._get_page("media_param_cfg")
        data = self.parser.parse_form_fields(html)
        data.update(kwargs)
        return self._post_goform("media_param_cfg", data)

    # ═══════════════════════════════════════════════════════════════
    # NETWORK CONFIGURATION
    # ═══════════════════════════════════════════════════════════════

    def get_network_config(self) -> Dict[str, Any]:
        """Get network (WAN/LAN) configuration."""
        html = self._get_page("local_network")
        return self.parser.parse_network_config(html)

    def get_management_config(self) -> Dict[str, Any]:
        """Get management settings (NTP, web ports, telnet, SSH)."""
        html = self._get_page("manage_cfg")
        return self.parser.parse_manage_config(html)

    # ═══════════════════════════════════════════════════════════════
    # GSM OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    def get_gsm_operate_rules(self) -> List[Dict[str, Any]]:
        """Get GSM routing/operate rules (prefix match/add/delete per port)."""
        html = self._get_page("gsm_operate")
        return self.parser.parse_gsm_operate(html)

    def set_gsm_operate_rules(self, rules: List[Dict]) -> str:
        """
        Update GSM operation rules.
        
        Args:
            rules: List of dicts with: enable, PreMatch, PreDelete, PreAdd, port
        """
        data = {}
        for i, rule in enumerate(rules):
            data[f"enable{i}"] = rule.get("enable", "0")
            data[f"PreMatch{i}"] = rule.get("PreMatch", "")
            data[f"PreDelete{i}"] = rule.get("PreDelete", "0")
            data[f"PreAdd{i}"] = rule.get("PreAdd", "")
            data[f"port{i}"] = rule.get("port", "255")
        return self._post_goform("gsm_rule", data)

    def get_gsm_events(self, port: int = 255) -> List[Dict[str, Any]]:
        """
        Get GSM events (registration, signal changes, errors).
        
        Args:
            port: Port filter (255 = all)
        """
        html = self._get_page("gsm_event")
        return self.parser.parse_table_rows(html)

    # ═══════════════════════════════════════════════════════════════
    # SERVICE CONFIGURATION
    # ═══════════════════════════════════════════════════════════════

    def get_service_config(self) -> Dict[str, Any]:
        """Get service configuration (dial settings, hook flash, redirect)."""
        html = self._get_page("service_cfg")
        return self.parser.parse_form_fields(html)

    def set_service_config(self, **kwargs) -> str:
        """Update service configuration."""
        current = self.get_service_config()
        current.update(kwargs)
        return self._post_goform("service_cfg", current)

    # ═══════════════════════════════════════════════════════════════
    # WIA BASIC CONFIGURATION (GSM advanced)
    # ═══════════════════════════════════════════════════════════════

    def get_wia_basic_config(self) -> Dict[str, Any]:
        """
        Get WIA (Wireless Intelligent Access) basic configuration.
        Includes: SIM mode, work mode, remote call settings,
        SMS reports, callback, event reporting URL.
        """
        html = self._get_page("wia_basic_cfg")
        return self.parser.parse_form_fields(html)

    def set_wia_basic_config(self, **kwargs) -> str:
        """Update WIA basic configuration."""
        current = self.get_wia_basic_config()
        current.update(kwargs)
        return self._post_goform("wia_basic_cfg", current)

    # ═══════════════════════════════════════════════════════════════
    # VPN CONFIGURATION
    # ═══════════════════════════════════════════════════════════════

    def get_vpn_config(self) -> Dict[str, Any]:
        """Get VPN (OpenVPN) configuration and status."""
        html = self._get_page("vpn_cfg")
        fields = self.parser.parse_form_fields(html)
        # Also try to get OpenVPN info via AJAX
        try:
            ovpn_info = self._get_goform("vpn_info")
            if ovpn_info.strip().startswith("{"):
                fields["openvpn_status"] = json.loads(ovpn_info)
        except Exception:
            pass
        return fields

    # ═══════════════════════════════════════════════════════════════
    # RTP & PROTOCOL STATISTICS
    # ═══════════════════════════════════════════════════════════════

    def get_rtp_stats(self) -> List[Dict[str, Any]]:
        """Get RTP stream statistics."""
        html = self._get_page("rtp_stat")
        return self.parser.parse_table_rows(html)

    def get_protocol_stats(self) -> List[Dict[str, Any]]:
        """Get SIP protocol statistics."""
        html = self._get_page("protocol_stat")
        return self.parser.parse_table_rows(html)

    # ═══════════════════════════════════════════════════════════════
    # COMPREHENSIVE STATUS (Dashboard Data)
    # ═══════════════════════════════════════════════════════════════

    def get_full_status(self) -> Dict[str, Any]:
        """
        Comprehensive device status for dashboard display.
        
        Fetches system info, port status, call stats, and GSM events
        in a single call. Designed for the live dashboard.
        
        Returns:
            {
                "system": {...},
                "ports": [...],
                "port_info": [...],
                "call_stats": {...},
                "ecc_stats": [...],
                "sip_config": {...},
                "media_config": {...},
                "network_config": {...},
                "management_config": {...},
                "gsm_rules": [...],
                "sms_routing": [...],
                "device_health": {...},
            }
        """
        result = {}

        # System info
        try:
            result["system"] = self.get_system_info()
        except Exception as e:
            result["system"] = {"error": str(e)}

        # Port status
        try:
            result["ports"] = self.get_port_status()
        except Exception as e:
            result["ports"] = []

        # Port info
        try:
            result["port_info"] = self.get_port_info()
        except Exception as e:
            result["port_info"] = []

        # Call stats
        try:
            result["call_stats"] = self.get_call_stats()
        except Exception as e:
            result["call_stats"] = {"ports": [], "totals": {}}

        # ECC stats
        try:
            result["ecc_stats"] = self.get_ecc_stats()
        except Exception as e:
            result["ecc_stats"] = []

        # Configs
        try:
            result["sip_config"] = self.get_sip_config()
        except Exception as e:
            result["sip_config"] = {"error": str(e)}

        try:
            result["media_config"] = self.get_media_config()
        except Exception as e:
            result["media_config"] = {"error": str(e)}

        try:
            result["network_config"] = self.get_network_config()
        except Exception as e:
            result["network_config"] = {"error": str(e)}

        try:
            result["management_config"] = self.get_management_config()
        except Exception as e:
            result["management_config"] = {"error": str(e)}

        # GSM rules
        try:
            result["gsm_rules"] = self.get_gsm_operate_rules()
        except Exception as e:
            result["gsm_rules"] = []

        # SMS routing
        try:
            result["sms_routing"] = self.get_sms_routing()
        except Exception as e:
            result["sms_routing"] = []

        # Calculate health score
        result["device_health"] = self._calculate_health(result)

        return result

    def _calculate_health(self, status: Dict) -> Dict[str, Any]:
        """
        Calculate overall device health from status data.
        
        Health checks:
        - System reachable (uptime > 0)
        - Ports with SIM cards powered on
        - Call success rate (ASR)
        - SIP registration status
        """
        health = {
            "score": 0,
            "max_score": 100,
            "status": "unknown",
            "checks": [],
        }

        score = 0

        # Check 1: System reachable (25 points)
        sys_info = status.get("system", {})
        if sys_info and "error" not in sys_info:
            score += 25
            health["checks"].append({"name": "System Reachable", "status": "pass", "points": 25})
        else:
            health["checks"].append({"name": "System Reachable", "status": "fail", "points": 0})

        # Check 2: Uptime > 5 minutes (15 points)
        uptime = sys_info.get("uptime_seconds", 0)
        if uptime > 300:
            score += 15
            health["checks"].append({"name": "Stable Uptime", "status": "pass", "points": 15})
        else:
            health["checks"].append({"name": "Stable Uptime", "status": "warn", "points": 0})

        # Check 3: At least one SIM card present (20 points)
        ports = status.get("ports", [])
        sim_count = sum(1 for p in ports if p.get("has_sim"))
        if sim_count > 0:
            score += 20
            health["checks"].append({
                "name": f"SIM Cards ({sim_count}/8)",
                "status": "pass", "points": 20,
            })
        else:
            health["checks"].append({"name": "SIM Cards (0/8)", "status": "fail", "points": 0})

        # Check 4: Powered on modules (20 points)
        powered = sum(1 for p in ports if p.get("is_powered"))
        if powered > 0:
            score += 20
            health["checks"].append({
                "name": f"Powered Modules ({powered}/8)",
                "status": "pass", "points": 20,
            })
        else:
            health["checks"].append({"name": "Powered Modules (0/8)", "status": "warn", "points": 0})

        # Check 5: ASR > 50% if calls exist (20 points)
        totals = status.get("call_stats", {}).get("totals", {})
        total_calls = totals.get("total_calls", 0)
        asr = totals.get("asr_percent", 0)
        if total_calls == 0:
            score += 20  # No calls = no problem
            health["checks"].append({"name": "ASR (no calls yet)", "status": "pass", "points": 20})
        elif asr >= 50:
            score += 20
            health["checks"].append({
                "name": f"ASR ({asr}%)",
                "status": "pass", "points": 20,
            })
        elif asr >= 25:
            score += 10
            health["checks"].append({
                "name": f"ASR ({asr}%)",
                "status": "warn", "points": 10,
            })
        else:
            health["checks"].append({
                "name": f"ASR ({asr}%)",
                "status": "fail", "points": 0,
            })

        health["score"] = score
        if score >= 80:
            health["status"] = "healthy"
        elif score >= 50:
            health["status"] = "degraded"
        else:
            health["status"] = "critical"

        return health

    # ═══════════════════════════════════════════════════════════════
    # DEVICE CONTROL
    # ═══════════════════════════════════════════════════════════════

    def restart_device(self) -> str:
        """Restart the Dinstar device. ⚠️ This will drop all active calls!"""
        return self._post_goform("restart", {"restart": "1"})

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connectivity to the device.
        
        Returns:
            {"status": "ok"/"error", "message": "...", "latency_ms": N}
        """
        start = time.time()
        try:
            self.login()
            info = self.get_system_info()
            latency = round((time.time() - start) * 1000)
            return {
                "status": "ok",
                "message": f"Connected ({info.get('TotalPort', '?')} ports, "
                           f"uptime: {info.get('uptime_formatted', 'unknown')})",
                "latency_ms": latency,
                "system_info": info,
            }
        except DinstarAuthError as e:
            return {"status": "auth_error", "message": str(e), "latency_ms": -1}
        except DinstarConnectionError as e:
            return {"status": "connection_error", "message": str(e), "latency_ms": -1}
        except Exception as e:
            return {"status": "error", "message": str(e), "latency_ms": -1}

    def __repr__(self):
        return f"DinstarClient({self.host}, authenticated={self._authenticated})"
