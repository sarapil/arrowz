# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see LICENSE

"""
CAPS Gate — Standardized capability check entry point.

Usage::

    from arrowz.caps.gate import check_user_capability
    check_user_capability("AZ_manage_projects", throw=True)
"""

import frappe


def check_user_capability(capability_name: str, throw: bool = True) -> bool:
    """Check if current user has the named capability."""
    try:
        from caps.services.capability_service import check_capability
        return check_capability(capability_name, frappe.session.user, throw=throw)
    except ImportError:
        # CAPS app not installed — allow all
        return True
