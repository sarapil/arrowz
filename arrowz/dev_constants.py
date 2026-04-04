# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Development Environment Constants
===================================

Central reference for all environment-specific paths, ports, and configuration
constants used across the Arrowz platform — both development and production.

Import and use these constants instead of hardcoding paths:

    from arrowz.dev_constants import PBX_MOUNT, BENCH_PATH, LOG_PATHS

This module is the **single source of truth** for:
- FreePBX mount paths and file locations
- Bench directory structure
- Service ports and connection defaults
- Environment detection (dev vs production)
"""

import os
from pathlib import Path


# =============================================================================
# ENVIRONMENT DETECTION
# =============================================================================

#: True if running in developer_mode (bench start), False in production
IS_DEV = bool(os.environ.get("DEV_SERVER") or os.path.exists("/workspace/development"))

#: Container OS: Debian GNU/Linux 12 (bookworm) in dev container
CONTAINER_OS = "Debian GNU/Linux 12 (bookworm)"


# =============================================================================
# BENCH PATHS
# =============================================================================

#: Root bench directory
BENCH_PATH = "/workspace/development/frappe-bench"

#: Apps directory containing all Frappe apps
APPS_PATH = os.path.join(BENCH_PATH, "apps")

#: Arrowz app root
ARROWZ_APP_PATH = os.path.join(APPS_PATH, "arrowz")

#: Arrowz Python package root
ARROWZ_PACKAGE_PATH = os.path.join(ARROWZ_APP_PATH, "arrowz")

#: Sites directory
SITES_PATH = os.path.join(BENCH_PATH, "sites")

#: Development site
DEV_SITE = "dev.localhost"

#: Python virtual environment
VENV_PATH = os.path.join(BENCH_PATH, "env")

#: Bench logs directory
BENCH_LOGS_PATH = os.path.join(BENCH_PATH, "logs")


# =============================================================================
# FREEPBX / PBX MOUNT — CRITICAL FOR VOIP DEBUGGING
# =============================================================================
#
# The /mnt/pbx directory is a Docker volume mount from the FreePBX container.
# It provides read-only access to FreePBX/Asterisk configuration, logs, and
# data WITHOUT needing SSH access to the PBX server.
#
# This is the PRIMARY debugging resource when troubleshooting:
# - Softphone registration failures
# - WebRTC/ICE/DTLS connection issues
# - SIP call setup problems
# - Audio quality issues (codec, RTP)
# - Extension misconfiguration
# - Call routing / dialplan issues
# - Call recording access
# - Voicemail file access
#
# Docker volume mapping (in docker-compose.yml):
#   volumes:
#     - freepbx_etc:/mnt/pbx/etc:ro
#     - freepbx_logs:/mnt/pbx/logs:ro
#     - freepbx_recordings:/mnt/pbx/recordings:ro
#     - freepbx_voicemail:/mnt/pbx/voicemail:ro
#     - freepbx_db:/mnt/pbx/db:ro
#

#: Base mount path for FreePBX volumes
PBX_MOUNT = "/mnt/pbx"


# -- PBX Subdirectories --

#: Asterisk configuration files (pjsip.conf, extensions.conf, etc.)
PBX_ETC_PATH = os.path.join(PBX_MOUNT, "etc", "asterisk")

#: Asterisk log files (full, queue_log, freepbx.log, etc.)
PBX_LOGS_PATH = os.path.join(PBX_MOUNT, "logs", "asterisk")

#: Apache/HTTP server logs (FreePBX web UI)
PBX_APACHE_LOGS = os.path.join(PBX_MOUNT, "logs", "apache2")

#: FreePBX database backup SQL dumps
PBX_DB_PATH = os.path.join(PBX_MOUNT, "db")

#: Call recordings directory
PBX_RECORDINGS_PATH = os.path.join(PBX_MOUNT, "recordings")

#: Voicemail storage
PBX_VOICEMAIL_PATH = os.path.join(PBX_MOUNT, "voicemail")

#: TLS/DTLS certificates and keys
PBX_KEYS_PATH = os.path.join(PBX_ETC_PATH, "keys")


# -- Key FreePBX Config Files (for debugging) --

PBX_CONFIG_FILES = {
    # SIP/PJSIP Configuration (most important for VoIP debugging)
    "pjsip_main":          os.path.join(PBX_ETC_PATH, "pjsip.conf"),
    "pjsip_endpoints":     os.path.join(PBX_ETC_PATH, "pjsip.endpoint.conf"),
    "pjsip_transports":    os.path.join(PBX_ETC_PATH, "pjsip.transports.conf"),
    "pjsip_auth":          os.path.join(PBX_ETC_PATH, "pjsip.auth.conf"),
    "pjsip_aor":           os.path.join(PBX_ETC_PATH, "pjsip.aor.conf"),
    "pjsip_registration":  os.path.join(PBX_ETC_PATH, "pjsip.registration.conf"),
    "pjsip_identify":      os.path.join(PBX_ETC_PATH, "pjsip.identify.conf"),
    "pjsip_custom":        os.path.join(PBX_ETC_PATH, "pjsip_custom.conf"),
    "pjsip_endpoint_custom": os.path.join(PBX_ETC_PATH, "pjsip.endpoint_custom.conf"),

    # Legacy SIP (if still in use)
    "sip_additional":      os.path.join(PBX_ETC_PATH, "sip_additional.conf"),
    "sip_custom":          os.path.join(PBX_ETC_PATH, "sip_custom.conf"),

    # Extensions / Dialplan
    "extensions_main":     os.path.join(PBX_ETC_PATH, "extensions.conf"),
    "extensions_additional": os.path.join(PBX_ETC_PATH, "extensions_additional.conf"),
    "extensions_custom":   os.path.join(PBX_ETC_PATH, "extensions_custom.conf"),

    # AMI (Asterisk Manager Interface)
    "manager_main":        os.path.join(PBX_ETC_PATH, "manager.conf"),
    "manager_additional":  os.path.join(PBX_ETC_PATH, "manager_additional.conf"),
    "manager_custom":      os.path.join(PBX_ETC_PATH, "manager_custom.conf"),

    # HTTP / WebSocket
    "http_main":           os.path.join(PBX_ETC_PATH, "http.conf"),
    "http_additional":     os.path.join(PBX_ETC_PATH, "http_additional.conf"),

    # RTP / Media
    "rtp_main":            os.path.join(PBX_ETC_PATH, "rtp.conf"),
    "rtp_additional":      os.path.join(PBX_ETC_PATH, "rtp_additional.conf"),

    # Queues
    "queues_main":         os.path.join(PBX_ETC_PATH, "queues.conf"),
    "queues_additional":   os.path.join(PBX_ETC_PATH, "queues_additional.conf"),

    # Voicemail
    "voicemail_main":      os.path.join(PBX_ETC_PATH, "voicemail.conf"),

    # CDR (Call Detail Records)
    "cdr_adaptive_odbc":   os.path.join(PBX_ETC_PATH, "cdr_adaptive_odbc.conf"),

    # Main Asterisk config
    "asterisk_main":       os.path.join(PBX_ETC_PATH, "asterisk.conf"),

    # Codecs
    "codecs":              os.path.join(PBX_ETC_PATH, "codecs.conf"),

    # Logger
    "logger":              os.path.join(PBX_ETC_PATH, "logger.conf"),
}


# -- Key FreePBX Log Files (for debugging) --

PBX_LOG_FILES = {
    # Main Asterisk full log (ALL events — primary debugging resource)
    "full":             os.path.join(PBX_LOGS_PATH, "full"),

    # FreePBX application log (module errors, GUI operations)
    "freepbx":          os.path.join(PBX_LOGS_PATH, "freepbx.log"),

    # Security events (failed auth, blocked IPs)
    "security":         os.path.join(PBX_LOGS_PATH, "freepbx_security.log"),

    # Call queue operations
    "queue":            os.path.join(PBX_LOGS_PATH, "queue_log"),

    # fail2ban events
    "fail2ban":         os.path.join(PBX_LOGS_PATH, "fail2ban"),

    # Firewall events
    "firewall":         os.path.join(PBX_LOGS_PATH, "firewall.log"),

    # UCP (User Control Panel)
    "ucp_out":          os.path.join(PBX_LOGS_PATH, "ucp_out.log"),
    "ucp_err":          os.path.join(PBX_LOGS_PATH, "ucp_err.log"),

    # Chat log
    "chat":             os.path.join(PBX_LOGS_PATH, "chat.log"),

    # CDR custom and CSV directories
    "cdr_custom_dir":   os.path.join(PBX_LOGS_PATH, "cdr-custom"),
    "cdr_csv_dir":      os.path.join(PBX_LOGS_PATH, "cdr-csv"),
}


# -- PBX Database Dumps --

PBX_DB_FILES = {
    # Full Asterisk database dump (extensions, users, settings)
    "asterisk_db":      os.path.join(PBX_DB_PATH, "asterisk_20260205_165024.sql"),

    # CDR database dump (call records)
    "cdr_db":           os.path.join(PBX_DB_PATH, "asteriskcdrdb_20260205_165024.sql"),

    # Complete combined dump
    "complete_db":      os.path.join(PBX_DB_PATH, "asterisk_complete_20260205_165024.sql"),
}


# =============================================================================
# SERVICE PORTS
# =============================================================================

PORTS = {
    # Frappe / Bench Services
    "frappe_web":       8000,    # Gunicorn web server
    "socketio":         9000,    # Socket.IO real-time server
    "file_watcher":     6787,    # bench watch file watcher

    # FreePBX / Asterisk
    "pbx_webrtc_wss":   8089,    # WebSocket Secure (WebRTC signaling)
    "pbx_ami":          5038,    # Asterisk Manager Interface
    "pbx_sip_udp":      5060,    # SIP UDP (chan_sip / PJSIP)
    "pbx_sip_tls":      5061,    # SIP TLS
    "pbx_rtp_start":    10000,   # RTP media port range start
    "pbx_rtp_end":      20000,   # RTP media port range end
    "pbx_http":         80,      # FreePBX Web UI HTTP
    "pbx_https":        443,     # FreePBX Web UI HTTPS

    # Database & Cache
    "mariadb":          3306,    # MariaDB database
    "redis_cache":      13000,   # Redis cache
    "redis_queue":      11000,   # Redis queue (RQ)
    "redis_realtime":   13000,   # Redis pub/sub for Socket.IO

    # MikroTik RouterOS (when integrated)
    "mikrotik_api":     8728,    # RouterOS API (plaintext)
    "mikrotik_api_ssl": 8729,    # RouterOS API (SSL)
    "mikrotik_winbox":  8291,    # WinBox management
    "mikrotik_web":     80,      # RouterOS WebFig
    "mikrotik_ssh":     22,      # RouterOS SSH
}


# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================

#: Map of environment variables used by Arrowz
ENV_VARS = {
    # Arrowz-specific
    "ARROWZ_DEBUG":              "Enable debug mode for Arrowz (1/0)",
    "ARROWZ_DISABLE_WEBHOOKS":   "Disable webhook processing (1/0)",
    "ARROWZ_OPENAI_TIMEOUT":     "OpenAI API timeout in seconds (default: 30)",

    # FreePBX connection (used in AZ Server Config)
    "PBX_HOST":                  "FreePBX server hostname/IP",
    "PBX_SSH_USER":              "SSH username for PBX server",
    "PBX_SSH_KEY":               "Path to SSH private key for PBX",
    "PBX_AMI_USER":              "AMI username",
    "PBX_AMI_SECRET":            "AMI password",

    # OpenMeetings
    "OM_HOST":                   "OpenMeetings server URL",
    "OM_ADMIN_USER":             "OpenMeetings admin username",
    "OM_ADMIN_PASS":             "OpenMeetings admin password",

    # Frappe / Bench (set in common_site_config.json)
    "REDIS_CACHE":               "Redis cache URL",
    "REDIS_QUEUE":               "Redis queue URL",
    "DB_HOST":                   "MariaDB host",
    "DB_PORT":                   "MariaDB port",
}


# =============================================================================
# ARROWZ MODULE INVENTORY
# =============================================================================

#: Complete list of Arrowz modules and their purpose
MODULES = {
    "arrowz":              "Core VoIP & Communications (DocTypes: AZ Call Log, AZ Extension, etc.)",
    "arrowz_api":          "REST API endpoints (webrtc, contacts, sms, analytics, wallboard)",
    "arrowz_setup":        "Setup & Config (Arrowz Box, Network Settings, MikroTik Sync Log)",
    "network_management":  "Network Management (Interfaces, IP Addresses, DHCP, DNS, Routing)",
    "wifi_management":     "WiFi Management (SSID Profiles, Access Points, Hotspot)",
    "client_management":   "Client Management (Connected devices, sessions, MAC filtering)",
    "bandwidth_control":   "Bandwidth Control (QoS, Speed Limits, Traffic Shaping)",
    "firewall":            "Firewall (Rules, NAT, Port Forwarding, Layer7 Protocols)",
    "vpn":                 "VPN Management (WireGuard, L2TP, PPPoE, SSTP tunnels)",
    "billing_integration": "Billing Integration (Vouchers, Quotas, Usage tracking)",
    "monitoring":          "Monitoring & Alerts (Health checks, Alert rules, Dashboards)",
    "ip_accounting":       "IP Accounting (Traffic analysis, Per-IP bandwidth tracking)",
}


# =============================================================================
# DEVICE PROVIDER CONSTANTS
# =============================================================================

#: Supported device types for Arrowz Box
DEVICE_TYPES = ["Linux Box", "MikroTik"]

#: Provider module paths
PROVIDER_PATHS = {
    "Linux Box": "arrowz.device_providers.linux.LinuxProvider",
    "MikroTik":  "arrowz.device_providers.mikrotik.MikroTikProvider",
}

#: MikroTik default API ports
MIKROTIK_DEFAULT_API_PORT = 8728
MIKROTIK_DEFAULT_API_SSL_PORT = 8729


# =============================================================================
# DEBUGGING QUICK REFERENCE
# =============================================================================
#
# --- FreePBX/VoIP Debugging via /mnt/pbx ---
#
# 1. Check PBX mounts are available:
#    >>> from arrowz.dev_constants import PBX_MOUNT
#    >>> import os; os.path.exists(PBX_MOUNT)
#
# 2. Read Asterisk full log (last 100 lines):
#    $ tail -100 /mnt/pbx/logs/asterisk/full
#
# 3. Filter SIP/registration issues:
#    $ grep -i "register\|401\|403" /mnt/pbx/logs/asterisk/full | tail -50
#
# 4. Check WebRTC/ICE/DTLS errors:
#    $ grep -i "ice\|dtls\|srtp\|webrtc" /mnt/pbx/logs/asterisk/full | tail -50
#
# 5. Check extension PJSIP config:
#    $ grep -A 20 "\[1001\]" /mnt/pbx/etc/asterisk/pjsip.endpoint.conf
#
# 6. Check WebSocket transport:
#    $ cat /mnt/pbx/etc/asterisk/pjsip.transports.conf
#
# 7. Check AMI config:
#    $ cat /mnt/pbx/etc/asterisk/manager.conf
#
# 8. Check HTTP/WebSocket port:
#    $ cat /mnt/pbx/etc/asterisk/http.conf
#
# 9. Search any pattern:
#    $ grep -rn "pattern" /mnt/pbx/logs/asterisk/full
#
# 10. Use the built-in API:
#     >>> from arrowz.local_pbx_monitor import LocalPBXMonitor
#     >>> monitor = LocalPBXMonitor()
#     >>> monitor.diagnose_webrtc("1001")
#
# --- MikroTik Debugging ---
#
# 1. Test connection:
#    bench --site dev.localhost console
#    >>> box = frappe.get_doc("Arrowz Box", "my-mikrotik")
#    >>> box.test_connection()
#
# 2. View device config:
#    >>> box.get_device_config()
#
# 3. Run sync:
#    >>> box.sync_pull()
#    >>> box.sync_push()
#    >>> box.sync_diff()
#
# 4. Check sync logs:
#    >>> frappe.get_all("MikroTik Sync Log",
#    ...     filters={"arrowz_box": "my-mikrotik"},
#    ...     order_by="creation desc", limit=10)
#
