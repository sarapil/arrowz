# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
FreePBX Monitor Service
=======================
Monitors FreePBX/Asterisk in real-time via SSH.
Provides live log streaming, call monitoring, and diagnostics.
"""

import frappe
import subprocess
import threading
import time
import re
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable


class PBXMonitor:
    """
    FreePBX Monitor - connects via SSH to monitor PBX in real-time.
    """
    
    def __init__(self, server_name: str):
        """
        Initialize PBX Monitor.
        
        Args:
            server_name: Name of AZ Server Config document
        """
        self.server_name = server_name
        self.server = None
        self.ssh_host = None
        self.ssh_user = None
        self.ssh_port = 22
        self.ssh_key = None
        self._load_server_config()
        
        self._monitoring = False
        self._monitor_thread = None
        self._callbacks: List[Callable] = []
    
    def _load_server_config(self):
        """Load server configuration from database."""
        self.server = frappe.get_doc("AZ Server Config", self.server_name)
        
        # SSH settings from server config
        self.ssh_host = self.server.ssh_host or self.server.host or self.server.sip_domain
        self.ssh_user = self.server.ssh_username or 'root'
        self.ssh_port = self.server.ssh_port or 22
        
        # Handle SSH authentication
        self.ssh_auth_type = getattr(self.server, 'ssh_auth_type', 'password')
        
        if self.ssh_auth_type == 'key':
            self.ssh_key = self.server.ssh_private_key
        else:
            self.ssh_key = None
            # Note: Password auth via subprocess is tricky, recommend key-based auth
    
    def _ssh_cmd(self, command: str, timeout: int = 30) -> tuple:
        """
        Execute SSH command and return output.
        
        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        ssh_args = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=10",
            "-o", "BatchMode=yes"  # Don't ask for password
        ]
        
        if self.ssh_key:
            ssh_args.extend(["-i", self.ssh_key])
        
        ssh_args.extend([
            "-p", str(self.ssh_port),
            f"{self.ssh_user}@{self.ssh_host}",
            command
        ])
        
        try:
            result = subprocess.run(
                ssh_args,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", -1
        except Exception as e:
            return "", str(e), -1
    
    def _asterisk_cmd(self, command: str) -> tuple:
        """Execute Asterisk CLI command."""
        return self._ssh_cmd(f'asterisk -rx "{command}"')
    
    def test_connection(self) -> Dict[str, Any]:
        """Test SSH connection to FreePBX."""
        stdout, stderr, code = self._ssh_cmd("echo 'Connected!' && hostname")
        
        if code == 0:
            hostname = stdout.strip().split('\n')[-1]
            version_out, _, _ = self._asterisk_cmd("core show version")
            
            return {
                "success": True,
                "hostname": hostname,
                "asterisk_version": version_out.strip() if version_out else "Unknown"
            }
        else:
            return {
                "success": False,
                "error": stderr
            }
    
    # ===== PJSIP Status =====
    
    def get_endpoints(self) -> List[Dict]:
        """Get all PJSIP endpoints with their status."""
        stdout, _, code = self._asterisk_cmd("pjsip show endpoints")
        
        if code != 0:
            return []
        
        endpoints = []
        # Parse endpoint output
        for line in stdout.split('\n'):
            if line.strip() and 'Endpoint:' in line and '/' in line:
                parts = line.split()
                if len(parts) >= 2:
                    endpoint_info = parts[1].split('/')
                    ext = endpoint_info[0]
                    status = 'Unknown'
                    
                    # Find status
                    for i, p in enumerate(parts):
                        if p in ['Available', 'Unavailable', 'Busy', 'Ringing', 'InUse']:
                            status = p
                            break
                    
                    endpoints.append({
                        "extension": ext,
                        "status": status
                    })
        
        return endpoints
    
    def get_endpoint_detail(self, extension: str) -> Dict:
        """Get detailed info for a specific endpoint."""
        stdout, _, code = self._asterisk_cmd(f"pjsip show endpoint {extension}")
        
        if code != 0:
            return {"error": "Failed to get endpoint"}
        
        details = {
            "extension": extension,
            "raw_output": stdout,
            "settings": {}
        }
        
        # Parse key settings
        setting_patterns = {
            "dtls_auto_generate_cert": r"dtls_auto_generate_cert\s*:\s*(\w+)",
            "media_encryption": r"media_encryption\s*:\s*(\w+)",
            "ice_support": r"ice_support\s*:\s*(\w+)",
            "webrtc": r"webrtc\s*:\s*(\w+)",
            "direct_media": r"direct_media\s*:\s*(\w+)",
            "force_rport": r"force_rport\s*:\s*(\w+)",
            "rewrite_contact": r"rewrite_contact\s*:\s*(\w+)"
        }
        
        for key, pattern in setting_patterns.items():
            match = re.search(pattern, stdout, re.IGNORECASE)
            if match:
                details["settings"][key] = match.group(1)
        
        return details
    
    def get_contacts(self) -> List[Dict]:
        """Get all registered contacts."""
        stdout, _, code = self._asterisk_cmd("pjsip show contacts")
        
        if code != 0:
            return []
        
        contacts = []
        for line in stdout.split('\n'):
            if 'Contact:' in line and '@' in line:
                parts = line.split()
                if len(parts) >= 2:
                    contact_uri = parts[1] if len(parts) > 1 else ""
                    status = "Unknown"
                    rtt = "N/A"
                    
                    for p in parts:
                        if p in ['Avail', 'NonQual', 'Unavail', 'Unknown']:
                            status = p
                        if 'ms' in p.lower():
                            rtt = p
                    
                    contacts.append({
                        "contact": contact_uri,
                        "status": status,
                        "rtt": rtt
                    })
        
        return contacts
    
    # ===== Call Monitoring =====
    
    def get_active_channels(self) -> List[Dict]:
        """Get all active channels."""
        stdout, _, code = self._asterisk_cmd("core show channels verbose")
        
        if code != 0:
            return []
        
        channels = []
        for line in stdout.split('\n'):
            if 'PJSIP/' in line:
                parts = line.split()
                if parts:
                    channels.append({
                        "channel": parts[0],
                        "raw": line.strip()
                    })
        
        return channels
    
    def get_active_calls_count(self) -> int:
        """Get count of active calls."""
        stdout, _, _ = self._asterisk_cmd("core show calls")
        
        # Parse "X active calls" or "X calls processed"
        match = re.search(r'(\d+)\s+active\s+call', stdout, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0
    
    # ===== Log Monitoring =====
    
    def get_recent_logs(self, lines: int = 50, filter_text: str = None) -> str:
        """Get recent log lines."""
        cmd = f"tail -n {lines} /var/log/asterisk/full"
        if filter_text:
            cmd += f" | grep -i '{filter_text}'"
        
        stdout, _, code = self._ssh_cmd(cmd, timeout=60)
        return stdout if code == 0 else ""
    
    def get_error_logs(self, lines: int = 50) -> str:
        """Get recent error logs."""
        return self.get_recent_logs(lines * 2, "error\\|fail\\|warning")
    
    def get_sip_logs(self, lines: int = 100) -> str:
        """Get recent SIP-related logs."""
        return self.get_recent_logs(lines * 2, "invite\\|register\\|cancel\\|bye\\|ack")
    
    def get_ice_logs(self, lines: int = 100) -> str:
        """Get ICE/WebRTC related logs."""
        return self.get_recent_logs(lines * 2, "ice\\|dtls\\|srtp\\|webrtc")
    
    # ===== WebRTC Configuration =====
    
    def configure_webrtc_extension(self, extension: str) -> Dict:
        """
        Configure extension for WebRTC using direct file editing.
        This sets the required PJSIP settings for WebRTC.
        """
        # WebRTC required settings
        webrtc_settings = {
            "dtls_auto_generate_cert": "yes",
            "webrtc": "yes",
            "media_encryption": "dtls",
            "ice_support": "yes",
            "rtp_symmetric": "yes",
            "force_rport": "yes",
            "rewrite_contact": "yes",
            "direct_media": "no",
            "use_avpf": "yes",
            "media_use_received_transport": "yes"
        }
        
        # Create custom config content
        config_lines = [f"\n; WebRTC settings for extension {extension} - Added by Arrowz"]
        for key, value in webrtc_settings.items():
            config_lines.append(f"{key}={value}")
        
        config_content = '\n'.join(config_lines)
        
        # Add to pjsip.endpoint_custom.conf
        cmd = f'''cat >> /etc/asterisk/pjsip.endpoint_custom.conf << 'EOF'

[{extension}](+)
{chr(10).join([f'{k}={v}' for k, v in webrtc_settings.items()])}
EOF'''
        
        stdout, stderr, code = self._ssh_cmd(cmd)
        
        if code == 0:
            # Reload PJSIP
            self._asterisk_cmd("pjsip reload")
            return {"success": True, "message": f"WebRTC configured for {extension}"}
        else:
            return {"success": False, "error": stderr}
    
    def check_webrtc_settings(self, extension: str) -> Dict:
        """Check if extension has proper WebRTC settings."""
        details = self.get_endpoint_detail(extension)
        
        required_settings = {
            "webrtc": "yes",
            "ice_support": "yes",
            "media_encryption": "dtls",
            "direct_media": "no"
        }
        
        issues = []
        for key, expected in required_settings.items():
            actual = details.get("settings", {}).get(key, "unknown")
            if actual.lower() != expected.lower():
                issues.append(f"{key}: expected '{expected}', got '{actual}'")
        
        return {
            "extension": extension,
            "webrtc_ready": len(issues) == 0,
            "issues": issues,
            "settings": details.get("settings", {})
        }
    
    # ===== RTP & Transport =====
    
    def get_transports(self) -> List[Dict]:
        """Get PJSIP transports."""
        stdout, _, code = self._asterisk_cmd("pjsip show transports")
        
        if code != 0:
            return []
        
        transports = []
        for line in stdout.split('\n'):
            if 'Transport:' in line and '-' in line:
                parts = line.split()
                if len(parts) >= 4:
                    transports.append({
                        "name": parts[1] if len(parts) > 1 else "",
                        "type": parts[2] if len(parts) > 2 else "",
                        "bind": parts[-1] if parts else ""
                    })
        
        return transports
    
    def get_rtp_settings(self) -> str:
        """Get RTP settings."""
        stdout, _, _ = self._asterisk_cmd("rtp show settings")
        return stdout
    
    def check_port(self, port: int) -> Dict:
        """Check if a port is listening."""
        stdout, _, code = self._ssh_cmd(f"ss -tuln | grep :{port}")
        
        return {
            "port": port,
            "listening": code == 0 and stdout.strip() != "",
            "details": stdout.strip()
        }
    
    # ===== SIP Tracing =====
    
    def enable_sip_trace(self, verbose: bool = False) -> Dict:
        """Enable SIP logging."""
        if verbose:
            self._asterisk_cmd("pjsip set logger verbose on")
        else:
            self._asterisk_cmd("pjsip set logger on")
        
        return {"success": True, "message": "SIP tracing enabled"}
    
    def disable_sip_trace(self) -> Dict:
        """Disable SIP logging."""
        self._asterisk_cmd("pjsip set logger off")
        return {"success": True, "message": "SIP tracing disabled"}
    
    # ===== Diagnostics =====
    
    def full_diagnostics(self, extension: str = None) -> Dict:
        """Run full diagnostics."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "connection": self.test_connection(),
            "transports": self.get_transports(),
            "endpoints_count": len(self.get_endpoints()),
            "contacts": self.get_contacts(),
            "active_channels": self.get_active_channels(),
            "active_calls": self.get_active_calls_count(),
            "ports": {
                "51600": self.check_port(51600),
                "8089": self.check_port(8089)
            }
        }
        
        if extension:
            results["extension_details"] = self.get_endpoint_detail(extension)
            results["webrtc_check"] = self.check_webrtc_settings(extension)
        
        results["recent_errors"] = self.get_error_logs(20)
        
        return results


# ===== Frappe API Endpoints =====

@frappe.whitelist()
def test_pbx_connection(server_name: str) -> Dict:
    """Test connection to PBX server."""
    frappe.only_for(["System Manager"])

    monitor = PBXMonitor(server_name)
    return monitor.test_connection()


@frappe.whitelist()
def get_pbx_status(server_name: str) -> Dict:
    """Get quick PBX status."""
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    monitor = PBXMonitor(server_name)
    
    return {
        "endpoints": monitor.get_endpoints(),
        "contacts": monitor.get_contacts(),
        "active_calls": monitor.get_active_calls_count(),
        "transports": monitor.get_transports()
    }


@frappe.whitelist()
def get_extension_webrtc_status(server_name: str, extension: str) -> Dict:
    """Check WebRTC configuration for an extension."""
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    monitor = PBXMonitor(server_name)
    return monitor.check_webrtc_settings(extension)


@frappe.whitelist()
def configure_extension_webrtc(server_name: str, extension: str) -> Dict:
    """Configure extension for WebRTC."""
    frappe.only_for(["System Manager"])

    monitor = PBXMonitor(server_name)
    return monitor.configure_webrtc_extension(extension)


@frappe.whitelist()
def get_pbx_logs(server_name: str, log_type: str = "recent", lines: int = 50) -> Dict:
    """Get PBX logs."""
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    monitor = PBXMonitor(server_name)
    
    if log_type == "errors":
        logs = monitor.get_error_logs(lines)
    elif log_type == "sip":
        logs = monitor.get_sip_logs(lines)
    elif log_type == "ice":
        logs = monitor.get_ice_logs(lines)
    else:
        logs = monitor.get_recent_logs(lines)
    
    return {"logs": logs}


@frappe.whitelist()
def run_pbx_diagnostics(server_name: str, extension: str = None) -> Dict:
    """Run full PBX diagnostics."""
    frappe.only_for(["System Manager"])

    monitor = PBXMonitor(server_name)
    return monitor.full_diagnostics(extension)


@frappe.whitelist()
def enable_sip_trace(server_name: str, verbose: bool = False) -> Dict:
    """Enable SIP tracing on PBX."""
    frappe.only_for(["AZ Manager", "System Manager"])

    monitor = PBXMonitor(server_name)
    return monitor.enable_sip_trace(verbose)


@frappe.whitelist()
def disable_sip_trace(server_name: str) -> Dict:
    """Disable SIP tracing on PBX."""
    frappe.only_for(["AZ Manager", "System Manager"])

    monitor = PBXMonitor(server_name)
    return monitor.disable_sip_trace()


@frappe.whitelist()
def diagnose_ringing_issue(server_name: str, extension: str = None) -> Dict:
    """
    Diagnose the 'ringing continues after answer' issue.
    This typically happens when:
    1. 200 OK is not received by the caller
    2. Media path is broken (ICE/NAT issue)
    3. Missing WebRTC settings
    """
    frappe.only_for(["System Manager"])

    monitor = PBXMonitor(server_name)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "issue": "Ringing continues after answer",
        "possible_causes": [],
        "recommendations": []
    }
    
    # Check connection first
    conn = monitor.test_connection()
    if not conn.get("success"):
        results["error"] = "Cannot connect to PBX via SSH"
        return results
    
    # Check transports
    transports = monitor.get_transports()
    results["transports"] = transports
    
    # Check if UDP transport exists
    has_udp = any('udp' in t.get('type', '').lower() for t in transports)
    has_wss = any('wss' in t.get('type', '').lower() for t in transports)
    
    if not has_wss:
        results["possible_causes"].append("No WSS transport for WebRTC")
        results["recommendations"].append("Enable WebSocket Secure (WSS) transport in FreePBX")
    
    # Check WebRTC settings for extension
    if extension:
        webrtc_check = monitor.check_webrtc_settings(extension)
        results["webrtc_check"] = webrtc_check
        
        if not webrtc_check.get("webrtc_ready"):
            results["possible_causes"].append(f"Extension {extension} not configured for WebRTC")
            results["recommendations"].append(f"Configure WebRTC settings for extension {extension}")
            results["recommendations"].append("Required: webrtc=yes, ice_support=yes, media_encryption=dtls, direct_media=no")
    
    # Get recent SIP logs
    sip_logs = monitor.get_sip_logs(50)
    results["recent_sip_logs"] = sip_logs
    
    # Look for specific patterns in logs
    if "200 OK" in sip_logs and "ACK" not in sip_logs:
        results["possible_causes"].append("200 OK sent but ACK not received")
        results["recommendations"].append("Check NAT settings - ACK may not be reaching PBX")
    
    if "ICE" in sip_logs.upper() and "failed" in sip_logs.lower():
        results["possible_causes"].append("ICE negotiation failed")
        results["recommendations"].append("Configure STUN/TURN servers for NAT traversal")
    
    # Get ICE related logs
    ice_logs = monitor.get_ice_logs(30)
    results["recent_ice_logs"] = ice_logs
    
    # Check RTP settings
    rtp_settings = monitor.get_rtp_settings()
    results["rtp_settings"] = rtp_settings
    
    if "stunaddr" not in rtp_settings.lower():
        results["possible_causes"].append("No STUN server configured")
        results["recommendations"].append("Configure STUN server in RTP settings")
    
    # Final recommendations
    if not results["possible_causes"]:
        results["possible_causes"].append("Configuration appears correct - issue may be network/NAT related")
    
    results["recommendations"].append("Enable SIP trace and make a test call for detailed analysis")
    
    return results


@frappe.whitelist()
def live_call_trace(server_name: str, duration: int = 30) -> Dict:
    """
    Start a live trace of SIP messages for the specified duration.
    Returns the captured SIP messages.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    monitor = PBXMonitor(server_name)
    
    # Enable SIP trace
    monitor.enable_sip_trace(verbose=True)
    
    # Wait for messages
    import time
    time.sleep(min(duration, 30))  # Max 30 seconds
    
    # Get the logs
    logs = monitor.get_sip_logs(200)
    
    # Disable trace
    monitor.disable_sip_trace()
    
    return {
        "trace_duration": duration,
        "sip_messages": logs
    }
