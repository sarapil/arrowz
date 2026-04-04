# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Device Providers — Abstract Router Integration Layer

This package provides a pluggable abstraction layer for communicating with
different network device types (Linux boxes, MikroTik routers, etc.).

Architecture:
    BaseProvider (ABC)
        ├── LinuxProvider     — wraps BoxConnector for Linux-based Arrowz Engines
        └── MikroTikProvider  — direct RouterOS API via librouteros

    ProviderFactory.get(box_doc) → BaseProvider subclass

    ErrorTracker  — traces errors through execution layers
    SyncEngine    — bidirectional config sync with conflict resolution

Usage:
    from arrowz.device_providers import ProviderFactory

    provider = ProviderFactory.get(box_name="my-router")
    info = provider.get_system_info()
    interfaces = provider.get_interfaces()
"""

from arrowz.device_providers.provider_factory import ProviderFactory
from arrowz.device_providers.error_tracker import ErrorTracker

__all__ = ["ProviderFactory", "ErrorTracker"]
