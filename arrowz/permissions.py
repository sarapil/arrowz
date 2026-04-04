# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Permissions module for Arrowz Communications app.
"""

import frappe


def has_app_permission() -> bool:
    """
    Check if the current user has permission to access the Arrowz app.
    
    Returns:
        bool: True if user has permission, False otherwise.
    """
    if frappe.session.user == "Administrator":
        return True
    
    # Check if user has any relevant role
    user_roles = frappe.get_roles(frappe.session.user)
    allowed_roles = [
        "System Manager",
        "VoIP Manager",
        "VoIP User",
        "Support Team",
        "Sales User",
        "Sales Manager"
    ]
    
    return bool(set(user_roles) & set(allowed_roles))
