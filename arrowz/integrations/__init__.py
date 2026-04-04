# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# License: MIT

"""
Arrowz Integrations Package

This package contains connectors for external communication platforms:
- WhatsApp (Cloud API & On-Premise)
- Telegram
- OpenMeetings (Video Conferencing)
- Other messaging platforms

Each connector follows the Driver Pattern for consistent API.
"""

from arrowz.integrations.base import BaseDriver
from arrowz.integrations.whatsapp import WhatsAppCloudDriver
from arrowz.integrations.telegram import TelegramDriver
from arrowz.integrations.openmeetings import OpenMeetingsConnector

__all__ = [
    "BaseDriver",
    "WhatsAppCloudDriver",
    "TelegramDriver",
    "OpenMeetingsConnector"
]
