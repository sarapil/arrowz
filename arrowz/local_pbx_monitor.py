# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
Local PBX Monitor
=================
Monitors FreePBX directly from mounted volumes (no SSH required).
Reads logs, configs, and databases from /mnt/pbx/

Volume Mappings Expected:
- /mnt/pbx/logs/asterisk   -> Asterisk logs
- /mnt/pbx/logs/apache2    -> Apache logs  
- /mnt/pbx/etc/asterisk    -> Asterisk config files
- /mnt/pbx/db              -> Database backups
- /mnt/pbx/recordings      -> Call recordings
- /mnt/pbx/voicemail       -> Voicemail files
- /mnt/pbx/astdb.sqlite3   -> Asterisk internal DB
- /mnt/pbx/keys            -> TLS/DTLS keys
"""

import frappe
import os
import re
import sqlite3
import glob
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


# Base mount path
PBX_MOUNT = "/mnt/pbx"


class LocalPBXMonitor:
    """
    Local PBX Monitor - reads directly from mounted FreePBX volumes.
    No SSH required - much faster and more reliable.
    """
    
    def __init__(self):
        self.mount_path = PBX_MOUNT
        self.logs_path = os.path.join(self.mount_path, "logs")
        self.etc_path = os.path.join(self.mount_path, "etc/asterisk")
        self.db_path = os.path.join(self.mount_path, "db")
        self.recordings_path = os.path.join(self.mount_path, "recordings")
        self.voicemail_path = os.path.join(self.mount_path, "voicemail")
        self.astdb_path = os.path.join(self.mount_path, "astdb.sqlite3")
    
    def check_mounts(self) -> Dict[str, bool]:
        """Check which PBX volumes are mounted."""
        mounts = {
            "logs": os.path.exists(os.path.join(self.logs_path, "asterisk")),
            "config": os.path.exists(self.etc_path),
            "database": os.path.exists(self.db_path),
            "recordings": os.path.exists(self.recordings_path),
            "voicemail": os.path.exists(self.voicemail_path),
            "astdb": os.path.exists(self.astdb_path)
        }
        return mounts
    
    def is_available(self) -> bool:
        """Check if PBX mounts are available."""
        mounts = self.check_mounts()
        return any(mounts.values())
    
    # ===== LOG READING =====
    
    def read_log(self, log_file: str, lines: int = 100, 
                 filter_pattern: Optional[str] = None) -> str:
        """Read log file from mounted volume."""
        log_path = os.path.join(self.logs_path, "asterisk", log_file)
        
        if not os.path.exists(log_path):
            return f"Log file not found: {log_path}"
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                
            # Get last N lines
            result_lines = all_lines[-lines:]
            
            # Apply filter if provided
            if filter_pattern:
                pattern = re.compile(filter_pattern, re.IGNORECASE)
                result_lines = [l for l in result_lines if pattern.search(l)]
            
            return ''.join(result_lines)
        except Exception as e:
            return f"Error reading log: {str(e)}"
    
    def get_full_log(self, lines: int = 100) -> str:
        """Get main Asterisk full log."""
        return self.read_log("full", lines)
    
    def get_error_log(self, lines: int = 100) -> str:
        """Get error log entries."""
        return self.read_log("full", lines * 2, r"error|warning|fail|critical")
    
    def get_sip_log(self, lines: int = 100) -> str:
        """Get SIP-related log entries."""
        return self.read_log("full", lines * 3, r"pjsip|sip|invite|register|ack|bye|cancel")
    
    def get_webrtc_log(self, lines: int = 100) -> str:
        """Get WebRTC/ICE-related log entries."""
        return self.read_log("full", lines * 3, r"ice|dtls|srtp|webrtc|stun|turn|rtp")
    
    def get_call_log(self, lines: int = 100) -> str:
        """Get call-related log entries."""
        return self.read_log("full", lines * 3, r"dial|answer|hangup|bridge|channel")
    
    def search_logs(self, pattern: str, lines: int = 200) -> str:
        """Search logs for a specific pattern."""
        return self.read_log("full", lines, pattern)
    
    # ===== CONFIG READING =====
    
    def read_config(self, config_file: str) -> str:
        """Read Asterisk config file."""
        config_path = os.path.join(self.etc_path, config_file)
        
        if not os.path.exists(config_path):
            return f"Config file not found: {config_path}"
        
        try:
            with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"Error reading config: {str(e)}"
    
    def get_pjsip_config(self) -> Dict[str, str]:
        """Get all PJSIP configuration files."""
        configs = {}
        pjsip_files = [
            "pjsip.conf",
            "pjsip.endpoint.conf", 
            "pjsip.endpoint_custom.conf",
            "pjsip.transports.conf",
            "pjsip.transports_custom.conf",
            "pjsip.aor.conf",
            "pjsip.auth.conf",
            "pjsip.registration.conf"
        ]
        
        for filename in pjsip_files:
            content = self.read_config(filename)
            if not content.startswith("Config file not found"):
                configs[filename] = content
        
        return configs
    
    def get_extension_config(self, extension: str) -> Dict[str, Any]:
        """Get configuration for a specific extension."""
        result = {
            "extension": extension,
            "endpoint": None,
            "aor": None,
            "auth": None,
            "issues": []
        }
        
        # Read endpoint config
        endpoint_content = self.read_config("pjsip.endpoint.conf")
        if f"[{extension}]" in endpoint_content:
            # Extract extension section
            lines = endpoint_content.split('\n')
            in_section = False
            section_lines = []
            for line in lines:
                if line.strip() == f"[{extension}]":
                    in_section = True
                    section_lines.append(line)
                elif in_section:
                    if line.startswith('[') and not line.startswith(f'[{extension}'):
                        break
                    section_lines.append(line)
            result["endpoint"] = '\n'.join(section_lines)
            
            # Check WebRTC settings
            section_text = result["endpoint"].lower()
            if "webrtc=yes" not in section_text:
                result["issues"].append("Missing webrtc=yes")
            if "ice_support=yes" not in section_text:
                result["issues"].append("Missing ice_support=yes")
            if "media_encryption=dtls" not in section_text:
                result["issues"].append("Missing media_encryption=dtls")
            if "direct_media=no" not in section_text:
                result["issues"].append("direct_media should be 'no' for WebRTC")
        else:
            result["issues"].append(f"Extension {extension} not found in pjsip.endpoint.conf")
        
        # Check custom config
        custom_content = self.read_config("pjsip.endpoint_custom.conf")
        if f"[{extension}]" in custom_content:
            result["custom_config"] = True
        
        return result
    
    def get_rtp_config(self) -> str:
        """Get RTP configuration."""
        return self.read_config("rtp.conf")
    
    def get_http_config(self) -> str:
        """Get HTTP/WebSocket configuration."""
        return self.read_config("http.conf")
    
    # ===== ASTERISK DATABASE =====
    
    def query_astdb(self, family: Optional[str] = None, key: Optional[str] = None) -> List[Dict]:
        """Query Asterisk internal database (SQLite)."""
        if not os.path.exists(self.astdb_path):
            return [{"error": "astdb.sqlite3 not mounted"}]
        
        try:
            conn = sqlite3.connect(f"file:{self.astdb_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            
            if family and key:
                cursor.execute("SELECT * FROM astdb WHERE key LIKE ?", 
                             (f"/{family}/{key}%",))
            elif family:
                cursor.execute("SELECT * FROM astdb WHERE key LIKE ?", 
                             (f"/{family}/%",))
            else:
                cursor.execute("SELECT * FROM astdb LIMIT 100")
            
            rows = cursor.fetchall()
            conn.close()
            
            return [{"key": row[0], "value": row[1]} for row in rows]
        except Exception as e:
            return [{"error": str(e)}]
    
    # ===== RECORDINGS =====
    
    def list_recordings(self, date: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """List call recordings."""
        if not os.path.exists(self.recordings_path):
            return [{"error": "Recordings not mounted"}]
        
        recordings = []
        pattern = os.path.join(self.recordings_path, "**", "*.wav")
        
        for filepath in glob.glob(pattern, recursive=True)[:limit]:
            stat = os.stat(filepath)
            recordings.append({
                "filename": os.path.basename(filepath),
                "path": filepath,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return sorted(recordings, key=lambda x: x["modified"], reverse=True)
    
    # ===== DIAGNOSTICS =====
    
    def diagnose_webrtc(self, extension: Optional[str] = None) -> Dict[str, Any]:
        """Run WebRTC diagnostics."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "mounts": self.check_mounts(),
            "issues": [],
            "recommendations": []
        }
        
        if not self.is_available():
            result["error"] = "PBX volumes not mounted"
            return result
        
        # Check HTTP config for WebSocket
        http_config = self.get_http_config()
        if "enabled=yes" not in http_config.lower():
            result["issues"].append("HTTP server not enabled")
            result["recommendations"].append("Enable HTTP server in http.conf")
        if "bindport=8089" not in http_config:
            result["issues"].append("WebSocket port 8089 not configured")
        
        # Check RTP config
        rtp_config = self.get_rtp_config()
        if "stunaddr" not in rtp_config.lower():
            result["issues"].append("No STUN server configured")
            result["recommendations"].append("Add stunaddr=stun.l.google.com:19302 to rtp.conf")
        if "icesupport" not in rtp_config.lower():
            result["issues"].append("ICE support not configured in rtp.conf")
        
        # Check transports
        transport_config = self.read_config("pjsip.transports.conf")
        if "protocol=wss" not in transport_config.lower():
            result["issues"].append("No WSS transport configured")
            result["recommendations"].append("Configure WSS transport for WebRTC")
        
        # Check specific extension if provided
        if extension:
            ext_config = self.get_extension_config(extension)
            result["extension_config"] = ext_config
            result["issues"].extend(ext_config.get("issues", []))
        
        # Check recent error logs
        error_log = self.get_error_log(50)
        if "ice" in error_log.lower() and "fail" in error_log.lower():
            result["issues"].append("ICE failures detected in logs")
        if "dtls" in error_log.lower() and ("fail" in error_log.lower() or "error" in error_log.lower()):
            result["issues"].append("DTLS errors detected in logs")
        
        result["recent_errors"] = error_log
        
        return result
    
    def get_call_quality_metrics(self, lines: int = 500) -> Dict[str, Any]:
        """Analyze call quality from logs."""
        log_content = self.get_full_log(lines)
        
        metrics = {
            "total_calls": 0,
            "failed_calls": 0,
            "ice_failures": 0,
            "dtls_errors": 0,
            "registration_failures": 0,
            "recent_issues": []
        }
        
        # Count patterns
        metrics["total_calls"] = len(re.findall(r"INVITE sip:", log_content, re.IGNORECASE))
        metrics["failed_calls"] = len(re.findall(r"SIP/2.0 (4\d\d|5\d\d|6\d\d)", log_content))
        metrics["ice_failures"] = len(re.findall(r"ICE.*fail", log_content, re.IGNORECASE))
        metrics["dtls_errors"] = len(re.findall(r"DTLS.*error", log_content, re.IGNORECASE))
        metrics["registration_failures"] = len(re.findall(r"401 Unauthorized", log_content))
        
        # Extract recent issues
        for line in log_content.split('\n'):
            if any(word in line.lower() for word in ['error', 'fail', 'warning']):
                if len(metrics["recent_issues"]) < 10:
                    metrics["recent_issues"].append(line.strip()[:200])
        
        return metrics


# ===== Frappe API Endpoints =====

@frappe.whitelist()
def check_pbx_mounts() -> Dict:
    """Check PBX volume mounts."""
    monitor = LocalPBXMonitor()
    return {
        "available": monitor.is_available(),
        "mounts": monitor.check_mounts()
    }


@frappe.whitelist()
def get_pbx_logs(log_type: str = "full", lines: int = 100, 
                 filter_text: Optional[str] = None) -> Dict:
    """Get PBX logs."""
    monitor = LocalPBXMonitor()
    
    if not monitor.is_available():
        return {"error": "PBX volumes not mounted"}
    
    if log_type == "errors":
        logs = monitor.get_error_log(lines)
    elif log_type == "sip":
        logs = monitor.get_sip_log(lines)
    elif log_type == "webrtc":
        logs = monitor.get_webrtc_log(lines)
    elif log_type == "calls":
        logs = monitor.get_call_log(lines)
    elif log_type == "search" and filter_text:
        logs = monitor.search_logs(filter_text, lines)
    else:
        logs = monitor.get_full_log(lines)
    
    return {"logs": logs, "type": log_type}


@frappe.whitelist()
def get_extension_config(extension: str) -> Dict:
    """Get extension configuration."""
    monitor = LocalPBXMonitor()
    
    if not monitor.is_available():
        return {"error": "PBX volumes not mounted"}
    
    return monitor.get_extension_config(extension)


@frappe.whitelist()
def diagnose_webrtc(extension: Optional[str] = None) -> Dict:
    """Run WebRTC diagnostics."""
    monitor = LocalPBXMonitor()
    return monitor.diagnose_webrtc(extension)


@frappe.whitelist()
def get_pjsip_configs() -> Dict:
    """Get all PJSIP configuration files."""
    monitor = LocalPBXMonitor()
    
    if not monitor.is_available():
        return {"error": "PBX volumes not mounted"}
    
    return monitor.get_pjsip_config()


@frappe.whitelist()
def get_call_quality() -> Dict:
    """Get call quality metrics."""
    monitor = LocalPBXMonitor()
    
    if not monitor.is_available():
        return {"error": "PBX volumes not mounted"}
    
    return monitor.get_call_quality_metrics()


@frappe.whitelist()
def list_recordings(limit: int = 20) -> Dict:
    """List call recordings."""
    monitor = LocalPBXMonitor()
    
    if not monitor.is_available():
        return {"error": "PBX volumes not mounted"}
    
    return {"recordings": monitor.list_recordings(limit=limit)}


@frappe.whitelist()
def query_astdb(family: Optional[str] = None, key: Optional[str] = None) -> Dict:
    """Query Asterisk database."""
    monitor = LocalPBXMonitor()
    
    if not monitor.is_available():
        return {"error": "PBX volumes not mounted"}
    
    return {"results": monitor.query_astdb(family, key)}
