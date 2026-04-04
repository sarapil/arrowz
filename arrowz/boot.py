# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# License: MIT

"""
Arrowz Boot Session

Values to inject into frappe.boot for client-side access.
"""

import frappe


def boot_session(bootinfo):
    """Add Arrowz configuration to boot session"""
    
    if frappe.session.user == "Guest":
        return
    
    bootinfo.arrowz = get_arrowz_boot_info()


def get_arrowz_boot_info():
    """Get Arrowz configuration for current user"""
    info = {
        "enabled": False,
        "has_extension": False,
        "extension": None,
        "features": {}
    }
    
    try:
        # Get settings
        settings = frappe.get_single("Arrowz Settings")
        
        info["features"] = {
            "screen_pop": settings.get("enable_screen_pop", False),
            "recording": settings.get("enable_call_recording", False),
            "sms": settings.get("enable_sms", False),
            "ai": settings.get("enable_ai_features", False)
        }
        
        # Check if user has extension
        extension = frappe.db.get_value(
            "AZ Extension",
            {"user": frappe.session.user, "is_active": 1},
            ["name", "extension", "sip_username"],
            as_dict=True
        )
        
        if extension:
            info["enabled"] = True
            info["has_extension"] = True
            info["extension"] = extension.extension
            info["sip_username"] = extension.sip_username
        
        # Check user roles
        user_roles = frappe.get_roles(frappe.session.user)
        info["is_agent"] = "Call Center Agent" in user_roles
        info["is_manager"] = "Call Center Manager" in user_roles or "System Manager" in user_roles
        
    except Exception as e:
        frappe.log_error(f"Error loading Arrowz boot info: {str(e)}")
    
    return info
