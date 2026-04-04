# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe


def get_context(context):
    """
    PBX Monitor Dashboard Page
    Shows real-time PBX status and diagnostics.
    """
    context.no_cache = 1
    
    # Check if user has permission
    if not frappe.has_permission("AZ Server Config", "read"):
        frappe.throw("You don't have permission to access this page", frappe.PermissionError)
    
    # Get server configurations
    servers = frappe.get_all(
        "AZ Server Config",
        filters={"is_active": 1, "ssh_enabled": 1},
        fields=["name", "server_name", "server_type", "ssh_host", "host"]
    )
    
    context.servers = servers
    context.default_server = servers[0].name if servers else None
    context.title = "PBX Monitor"
