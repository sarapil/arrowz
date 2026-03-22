# Copyright (c) 2024, Arrowz Team
# License: MIT

"""
Arrowz Uninstallation Hooks

Cleanup functions when uninstalling the app.
"""

import frappe
from frappe import _


def before_uninstall(app_name=None):
    """Run before app uninstallation"""
    # Remove custom fields added by Arrowz
    remove_custom_fields()
    
    # Optionally remove roles (commented out to preserve user assignments)
    # remove_roles()
    
    frappe.msgprint(_("Arrowz cleanup completed. Custom fields have been removed."))


def remove_custom_fields():
    """Remove custom fields added by Arrowz"""
    # Get all custom fields with module = Arrowz
    custom_fields = frappe.get_all(
        "Custom Field",
        filters={"module": "Arrowz"},
        pluck="name"
    )
    
    for cf_name in custom_fields:
        try:
            frappe.delete_doc("Custom Field", cf_name, force=True)
        except Exception as e:
            frappe.log_error(f"Error removing custom field {cf_name}: {str(e)}")
    
    frappe.db.commit()


def remove_roles():
    """Remove Arrowz roles - use with caution"""
    roles = ["Call Center Agent", "Call Center Manager"]
    
    for role_name in roles:
        if frappe.db.exists("Role", role_name):
            # Check if role is in use
            has_permission = frappe.db.exists(
                "Has Role",
                {"role": role_name}
            )
            
            if not has_permission:
                try:
                    frappe.delete_doc("Role", role_name, force=True)
                except Exception as e:
                    frappe.log_error(f"Error removing role {role_name}: {str(e)}")
    
    frappe.db.commit()
