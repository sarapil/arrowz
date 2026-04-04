# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz Agent API
Handles agent-specific operations like status management and extension info.
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_my_extension():
    """
    Get the current user's extension configuration.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    
    extension = frappe.db.get_value(
        "AZ Extension",
        {"user": user, "is_active": 1},
        ["name", "extension", "display_name", "server", "enable_video", "enable_recording"],
        as_dict=True
    )
    
    if extension:
        # Get server info
        server = frappe.db.get_value(
            "AZ Server Config",
            extension.server,
            ["server_name", "server_address"],
            as_dict=True
        )
        extension.server_name = server.server_name if server else None
    
    return extension


@frappe.whitelist()
def update_status(status):
    """
    Update agent status.
    
    Args:
        status: available, busy, away, dnd, offline
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    user = frappe.session.user
    valid_statuses = ["available", "busy", "away", "dnd", "offline"]
    
    if status not in valid_statuses:
        frappe.throw(_("Invalid status: {0}").format(status))
    
    # Store status (could use Redis for real-time)
    frappe.cache().set_value(f"agent_status_{user}", status, expires_in_sec=3600)
    
    # Emit real-time event
    frappe.publish_realtime(
        "agent_status_changed",
        {
            "user": user,
            "status": status
        }
    )
    
    return {"status": status}


@frappe.whitelist()
def get_status():
    """
    Get current agent status.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    status = frappe.cache().get_value(f"agent_status_{user}") or "available"
    return {"status": status}


@frappe.whitelist()
def get_my_stats(date=None):
    """
    Get statistics for the current user.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    from frappe.utils import today
    
    user = frappe.session.user
    if not date:
        date = today()
    
    extension = frappe.db.get_value(
        "AZ Extension",
        {"user": user, "is_active": 1},
        "extension"
    )
    
    if not extension:
        return {}
    
    # Get call statistics
    from arrowz.arrowz.doctype.az_call_log.az_call_log import get_call_statistics
    stats = get_call_statistics(date_from=date, date_to=date, extension=extension)
    
    return stats


@frappe.whitelist()
def get_recent_contacts(limit=10):
    """
    Get recently called contacts for quick dial.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    
    extension = frappe.db.get_value(
        "AZ Extension",
        {"user": user, "is_active": 1},
        "extension"
    )
    
    if not extension:
        return []
    
    # Get unique recent contacts
    contacts = frappe.db.sql("""
        SELECT 
            CASE 
                WHEN direction = 'Inbound' THEN caller_id
                ELSE callee_id
            END as phone,
            MAX(contact_name) as name,
            MAX(party_type) as party_type,
            MAX(party) as party,
            COUNT(*) as call_count,
            MAX(start_time) as last_call
        FROM `tabAZ Call Log`
        WHERE extension = %s
        GROUP BY phone
        ORDER BY last_call DESC
        LIMIT %s
    """, (extension, limit), as_dict=True)
    
    return contacts


@frappe.whitelist()
def get_agent_info():
    """
    Get agent information for the dashboard.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    
    extension = frappe.db.get_value(
        "AZ Extension",
        {"user": user, "is_active": 1},
        ["name", "extension", "display_name", "status"],
        as_dict=True
    )
    
    status = frappe.cache().get_value(f"agent_status_{user}") or "available"
    
    return {
        "extension": extension.extension if extension else None,
        "display_name": extension.display_name if extension else None,
        "status": status
    }


@frappe.whitelist()
def get_agent_stats():
    """
    Get agent statistics for today.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    from frappe.utils import today, getdate
    
    user = frappe.session.user
    
    extension = frappe.db.get_value(
        "AZ Extension",
        {"user": user, "is_active": 1},
        "extension"
    )
    
    if not extension:
        return {"total_calls": 0, "avg_duration": 0, "inbound": 0, "outbound": 0}
    
    # Get today's stats
    stats = frappe.db.sql("""
        SELECT 
            COUNT(*) as total_calls,
            AVG(duration) as avg_duration,
            SUM(CASE WHEN direction = 'Inbound' THEN 1 ELSE 0 END) as inbound,
            SUM(CASE WHEN direction = 'Outbound' THEN 1 ELSE 0 END) as outbound
        FROM `tabAZ Call Log`
        WHERE extension = %s
        AND DATE(start_time) = %s
    """, (extension, today()), as_dict=True)
    
    if stats:
        return {
            "total_calls": stats[0].total_calls or 0,
            "avg_duration": stats[0].avg_duration or 0,
            "inbound": stats[0].inbound or 0,
            "outbound": stats[0].outbound or 0
        }
    
    return {"total_calls": 0, "avg_duration": 0, "inbound": 0, "outbound": 0}


@frappe.whitelist()
def get_recent_calls(limit=20):
    """
    Get recent calls for the current user.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    
    extension = frappe.db.get_value(
        "AZ Extension",
        {"user": user, "is_active": 1},
        "extension"
    )
    
    if not extension:
        return []
    
    calls = frappe.db.sql("""
        SELECT 
            name,
            direction,
            caller_id,
            callee_id,
            contact_name,
            duration,
            start_time,
            status
        FROM `tabAZ Call Log`
        WHERE extension = %s
        ORDER BY start_time DESC
        LIMIT %s
    """, (extension, int(limit)), as_dict=True)
    
    return calls


@frappe.whitelist()
def set_status(status):
    """
    Set agent status (alias for update_status).
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    return update_status(status)


@frappe.whitelist()
def set_agent_status(status):
    """
    Set agent status (alias for update_status).
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    return update_status(status)


@frappe.whitelist()
def get_agent_dashboard_data():
    """
    Get comprehensive agent dashboard data.
    Returns stats, recent calls, and active call info for the current user.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    from frappe.utils import today, get_datetime
    
    user = frappe.session.user
    user_fullname = frappe.db.get_value("User", user, "full_name") or user
    
    # Get user's extension
    extension = frappe.db.get_value(
        "AZ Extension",
        {"user": user, "is_active": 1},
        ["name", "extension", "display_name"],
        as_dict=True
    )
    
    ext = extension.extension if extension else None
    
    # Get today's stats
    calls_today = 0
    missed_calls = 0
    avg_duration = 0
    total_duration = 0
    
    if ext:
        stats = frappe.db.sql("""
            SELECT 
                COUNT(*) as total_calls,
                AVG(CASE WHEN duration > 0 THEN duration END) as avg_duration,
                SUM(CASE WHEN status = 'Missed' THEN 1 ELSE 0 END) as missed,
                SUM(duration) as total_duration
            FROM `tabAZ Call Log`
            WHERE extension = %s
            AND DATE(start_time) = %s
        """, (ext, today()), as_dict=True)
        
        if stats and stats[0]:
            calls_today = stats[0].total_calls or 0
            missed_calls = stats[0].missed or 0
            avg_duration = stats[0].avg_duration or 0
            total_duration = stats[0].total_duration or 0
    
    # Get queue count (waiting calls)
    queue_count = frappe.db.count("AZ Call Log", {
        "status": ["in", ["Ringing", "Queued"]],
        "start_time": [">=", today()]
    })
    
    # Get recent calls
    recent_calls = []
    if ext:
        recent_calls = frappe.db.sql("""
            SELECT 
                name,
                direction,
                CASE WHEN direction = 'Inbound' THEN caller_id ELSE callee_id END as phone,
                contact_name,
                duration,
                start_time,
                status
            FROM `tabAZ Call Log`
            WHERE extension = %s
            ORDER BY start_time DESC
            LIMIT 10
        """, (ext,), as_dict=True)
    
    # Check for active call
    active_call = None
    if ext:
        active = frappe.db.get_value(
            "AZ Call Log",
            {
                "extension": ext,
                "status": ["in", ["In Progress", "Ringing", "On Hold"]]
            },
            ["name", "direction", "caller_id", "callee_id", "contact_name", "duration", "status", "start_time"],
            as_dict=True
        )
        if active:
            # Calculate live duration
            if active.start_time:
                elapsed = (get_datetime() - get_datetime(active.start_time)).total_seconds()
                active["duration"] = int(elapsed)
            active["phone"] = active.caller_id if active.direction == "Inbound" else active.callee_id
            active_call = active
    
    # Get agent status
    status = frappe.cache().get_value(f"agent_status_{user}") or "available"
    
    return {
        "agent_name": user_fullname,
        "extension": ext,
        "status": status,
        "calls_handled": calls_today,
        "avg_duration": avg_duration,
        "missed_calls": missed_calls,
        "queue_count": queue_count,
        "avg_rating": None,  # Placeholder for rating system
        "recent_calls": recent_calls,
        "active_call": active_call
    }
