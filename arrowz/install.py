# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# License: MIT

"""
Arrowz Installation Hooks

Functions to run during app installation and migration.
"""

import frappe
from frappe import _


def before_install():
    """Run before app installation"""
    pass


def after_install():
    """Run after app installation"""
    # Create default roles
    create_default_roles()
    
    # Create default settings if not exists
    create_default_settings()
    
    # Add custom fields to existing doctypes
    add_custom_fields()

    # ── Desktop Icon injection (Frappe v16 /desk) ──
    from arrowz.desktop_utils import inject_app_desktop_icon
    inject_app_desktop_icon(
        app="arrowz",
        label="Arrowz",
        route="/desk/arrowz-topology",
        logo_url="/assets/arrowz/images/arrowz-logo-animated.svg",
        bg_color="#8B5CF6",
    )

    frappe.msgprint(_("Arrowz installed successfully! Configure your PBX settings to get started."))


def after_migrate():
    """Run after bench migrate"""
    # Ensure roles exist
    create_default_roles()
    
    # Update custom fields
    add_custom_fields()


def create_default_roles():
    """Create default Arrowz roles"""
    roles = [
        {
            "role_name": "Call Center Agent",
            "desk_access": 1,
            "description": "Can make/receive calls, view own call logs"
        },
        {
            "role_name": "Call Center Manager",
            "desk_access": 1,
            "description": "Can view all call logs, wallboard, analytics"
        }
    ]
    
    for role_data in roles:
        if not frappe.db.exists("Role", role_data["role_name"]):
            role = frappe.get_doc({
                "doctype": "Role",
                "role_name": role_data["role_name"],
                "desk_access": role_data["desk_access"],
                "description": role_data.get("description", "")
            })
            role.insert(ignore_permissions=True)
            frappe.db.commit()


def create_default_settings():
    """Create default Arrowz settings"""
    if not frappe.db.exists("Arrowz Settings", "Arrowz Settings"):
        settings = frappe.get_doc({
            "doctype": "Arrowz Settings",
            "enable_screen_pop": 1,
            "enable_call_recording": 1,
            "enable_sms": 0,
            "enable_ai_features": 0
        })
        settings.insert(ignore_permissions=True)
        frappe.db.commit()


def add_custom_fields():
    """Add custom fields to existing doctypes for call tracking"""
    custom_fields = {
        "Contact": [
            {
                "fieldname": "arrowz_last_call",
                "label": "Last Call",
                "fieldtype": "Datetime",
                "read_only": 1,
                "insert_after": "phone"
            },
            {
                "fieldname": "arrowz_total_calls",
                "label": "Total Calls",
                "fieldtype": "Int",
                "read_only": 1,
                "insert_after": "arrowz_last_call"
            }
        ],
        "Lead": [
            {
                "fieldname": "arrowz_last_call",
                "label": "Last Call",
                "fieldtype": "Datetime",
                "read_only": 1,
                "insert_after": "mobile_no"
            },
            {
                "fieldname": "arrowz_total_calls",
                "label": "Total Calls",
                "fieldtype": "Int",
                "read_only": 1,
                "insert_after": "arrowz_last_call"
            }
        ],
        "Customer": [
            {
                "fieldname": "arrowz_last_call",
                "label": "Last Call",
                "fieldtype": "Datetime",
                "read_only": 1,
                "insert_after": "mobile_no"
            },
            {
                "fieldname": "arrowz_total_calls",
                "label": "Total Calls",
                "fieldtype": "Int",
                "read_only": 1,
                "insert_after": "arrowz_last_call"
            }
        ]
    }
    
    for doctype, fields in custom_fields.items():
        # Check if doctype exists
        if not frappe.db.exists("DocType", doctype):
            continue
        
        for field_data in fields:
            fieldname = field_data["fieldname"]
            
            # Check if field already exists
            if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
                continue
            
            custom_field = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": doctype,
                "module": "Arrowz",
                **field_data
            })
            
            try:
                custom_field.insert(ignore_permissions=True)
            except Exception:
                pass
    
    frappe.db.commit()
