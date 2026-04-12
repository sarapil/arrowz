# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz Call Log API
API methods for call log management and retrieval
"""

import frappe
from frappe import _
from frappe.utils import nowdate, add_days, getdate


@frappe.whitelist()
def get_call_history(extension=None, call_type=None, date_range="today", limit=50):
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])
def get_call_history(extension=None, call_type=None, date_range="today", limit=50):
    """
    Get call history with filters
    
    Args:
        extension: Filter by extension number
        call_type: Filter by call type (inbound, outbound, missed)
        date_range: Date range filter (today, week, month, all)
        limit: Maximum number of records to return
    
    Returns:
        List of call log records
    """
    frappe.has_permission("AZ Call Log", "read", throw=True)
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    filters = {}
    
    # Extension filter
    if extension:
        filters["extension"] = extension
    else:
        # Get user's extensions if no specific extension selected
        user_extensions = get_user_extensions()
        if user_extensions:
            filters["extension"] = ["in", [e.get("extension") for e in user_extensions]]
    
    # Call type filter
    if call_type:
        if call_type == "missed":
            filters["status"] = "missed"
        else:
            filters["direction"] = call_type
    
    # Date range filter - use start_time field
    today = nowdate()
    if date_range == "today":
        filters["start_time"] = [">=", today]
    elif date_range == "week":
        filters["start_time"] = [">=", add_days(today, -7)]
    elif date_range == "month":
        filters["start_time"] = [">=", add_days(today, -30)]
    # 'all' doesn't add date filter
    
    try:
        calls = frappe.get_all(
            "AZ Call Log",
            filters=filters,
            fields=[
                "name", "caller_id", "callee_id", "extension",
                "direction", "status", "duration", "start_time",
                "contact_name", "recording_url", "recording_path"
            ],
            order_by="start_time desc",
            limit=int(limit)
        )
        
        # Process calls to add phone_number for display
        for call in calls:
            # Determine the phone number based on direction
            if call.get("direction") == "inbound":
                call["phone_number"] = call.get("caller_id") or ""
            else:
                call["phone_number"] = call.get("callee_id") or ""
            
            # Add call_datetime for backward compatibility
            call["call_datetime"] = call.get("start_time")
        
        return calls
        
    except Exception as e:
        frappe.log_error(f"Error getting call history: {str(e)}", "Call Log API")
        return []


def get_user_extensions():
    """Get extensions assigned to current user"""
    user = frappe.session.user
    
    if not user or user == "Guest":
        return []
    
    try:
        extensions = frappe.get_all(
            "AZ Extension",
            filters={"user": user, "is_active": 1},
            fields=["name", "extension", "display_name"]
        )
        return extensions
    except Exception:
        return []


@frappe.whitelist()
def get_call_statistics(extension=None, date_range="today"):
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])
def get_call_statistics(extension=None, date_range="today"):
    """
    Get call statistics for dashboard
    
    Args:
        extension: Filter by extension
        date_range: Date range (today, week, month)
    
    Returns:
        Statistics dictionary
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    filters = {}
    
    if extension:
        filters["extension"] = extension
    else:
        user_extensions = get_user_extensions()
        if user_extensions:
            filters["extension"] = ["in", [e.get("extension") for e in user_extensions]]
    
    # Date filter - use start_time field
    today = nowdate()
    if date_range == "today":
        filters["start_time"] = [">=", today]
    elif date_range == "week":
        filters["start_time"] = [">=", add_days(today, -7)]
    elif date_range == "month":
        filters["start_time"] = [">=", add_days(today, -30)]
    
    try:
        # Total calls
        total_calls = frappe.db.count("AZ Call Log", filters)
        
        # Inbound calls
        inbound_filters = dict(filters)
        inbound_filters["direction"] = "inbound"
        inbound_calls = frappe.db.count("AZ Call Log", inbound_filters)
        
        # Outbound calls
        outbound_filters = dict(filters)
        outbound_filters["direction"] = "outbound"
        outbound_calls = frappe.db.count("AZ Call Log", outbound_filters)
        
        # Missed calls
        missed_filters = dict(filters)
        missed_filters["status"] = "missed"
        missed_calls = frappe.db.count("AZ Call Log", missed_filters)
        
        # Total duration
        duration_result = frappe.db.sql("""
            SELECT SUM(duration) as total_duration
            FROM `tabAZ Call Log`
            WHERE extension IN (
                SELECT extension FROM `tabAZ Extension` WHERE user = %s AND is_active = 1
            )
            AND DATE(start_time) >= %s
        """, (frappe.session.user, add_days(today, -30) if date_range == "month" else today), as_dict=True)
        
        total_duration = duration_result[0].get("total_duration") or 0 if duration_result else 0
        
        return {
            "total_calls": total_calls,
            "inbound_calls": inbound_calls,
            "outbound_calls": outbound_calls,
            "missed_calls": missed_calls,
            "total_duration": total_duration,
            "total_duration_formatted": format_duration(total_duration)
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting call statistics: {str(e)}", "Call Log API")
        return {
            "total_calls": 0,
            "inbound_calls": 0,
            "outbound_calls": 0,
            "missed_calls": 0,
            "total_duration": 0,
            "total_duration_formatted": "0:00"
        }


def format_duration(seconds):
    """Format seconds to human readable duration"""
    if not seconds:
        return "0:00"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{str(minutes).zfill(2)}:{str(secs).zfill(2)}"
    return f"{minutes}:{str(secs).zfill(2)}"


@frappe.whitelist()
def get_recent_calls(limit=10):
    """Get recent calls for quick access"""
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user_extensions = get_user_extensions()
    
    if not user_extensions:
        return []
    
    extensions = [e.get("extension") for e in user_extensions]
    
    try:
        calls = frappe.get_all(
            "AZ Call Log",
            filters={
                "extension": ["in", extensions]
            },
            fields=[
                "name", "caller_id", "callee_id", "extension",
                "direction", "status", "duration", "start_time",
                "contact_name"
            ],
            order_by="start_time desc",
            limit=int(limit)
        )
        
        # Process calls for display
        for call in calls:
            if call.get("direction") == "inbound":
                call["phone_number"] = call.get("caller_id") or ""
            else:
                call["phone_number"] = call.get("callee_id") or ""
            call["call_datetime"] = call.get("start_time")
        
        return calls
        
    except Exception as e:
        frappe.log_error(f"Error getting recent calls: {str(e)}", "Call Log API")
        return []
