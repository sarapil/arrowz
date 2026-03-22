# Copyright (c) 2026, Arrowz Team
# License: MIT

"""
Dinstar UC2000-VE GSM Gateway Integration

Comprehensive Python client for managing Dinstar VoIP GSM Gateways
via their embedded web interface (goform-based API).

Features:
- Full authentication with session management
- System info, port status, GSM module control
- SIP/Media/Network configuration
- Call statistics, CDR records, live calls
- SMS send/receive/routing
- GSM events, signal monitoring
- Port groups, IP groups, digit maps
- VPN configuration
- Firmware & management settings

Usage:
    from arrowz.integrations.dinstar import DinstarClient

    client = DinstarClient(host="10.10.1.2", username="admin", password="admin")
    client.login()
    info = client.get_system_info()
    ports = client.get_port_status()
"""

from arrowz.integrations.dinstar.client import DinstarClient
from arrowz.integrations.dinstar.constants import (
    DINSTAR_PAGES,
    DINSTAR_GOFORMS,
    PORT_STATUS_MAP,
    BAND_TYPE_MAP,
    NETWORK_MODE_MAP,
    CODEC_MAP,
    DTMF_METHOD_MAP,
)

__all__ = [
    "DinstarClient",
    "DINSTAR_PAGES",
    "DINSTAR_GOFORMS",
    "PORT_STATUS_MAP",
    "BAND_TYPE_MAP",
    "NETWORK_MODE_MAP",
    "CODEC_MAP",
    "DTMF_METHOD_MAP",
]
