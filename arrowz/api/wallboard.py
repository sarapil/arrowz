# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz Wallboard API
Provides real-time data for the manager wallboard.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, today, time_diff_in_seconds


@frappe.whitelist()
def get_active_calls():
    """
    Get all currently active calls across all extensions.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    calls = frappe.get_all(
        "AZ Call Log",
        filters={
            "status": ["in", ["Ringing", "In Progress", "On Hold"]]
        },
        fields=[
            "name", "call_id", "direction", "status",
            "caller_id", "callee_id", "contact_name",
            "extension", "start_time", "answer_time"
        ],
        order_by="start_time desc"
    )
    
    # Calculate durations
    now = now_datetime()
    
    for call in calls:
        start = call.answer_time or call.start_time
        if start:
            call.duration = int(time_diff_in_seconds(now, start))
        else:
            call.duration = 0
    
    return calls


@frappe.whitelist()
def get_agent_status():
    """
    Get status of all configured agents/extensions.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    extensions = frappe.get_all(
        "AZ Extension",
        filters={"is_active": 1},
        fields=["name", "extension", "display_name", "user"]
    )
    
    agents = []
    for ext in extensions:
        # Get user info
        user_info = {}
        if ext.user:
            user_info = frappe.db.get_value(
                "User", ext.user,
                ["full_name", "user_image"],
                as_dict=True
            ) or {}
        
        # Get today's call count
        calls_today = frappe.db.count(
            "AZ Call Log",
            filters={
                "extension": ext.extension,
                "start_time": [">=", today()]
            }
        )
        
        # Check for active calls
        active_call = frappe.db.exists(
            "AZ Call Log",
            {
                "extension": ext.extension,
                "status": ["in", ["In Progress", "On Hold"]]
            }
        )
        
        # Determine status
        if active_call:
            status = "on_call"
        else:
            # Could integrate with presence system
            status = "available"
        
        agents.append({
            "name": ext.user or ext.name,
            "extension": ext.extension,
            "full_name": ext.display_name or user_info.get("full_name", ext.extension),
            "status": status,
            "calls_today": calls_today,
            "user_image": user_info.get("user_image")
        })
    
    return agents


@frappe.whitelist()
def get_hourly_stats(date=None):
    """
    Get hourly call statistics for a given date.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not date:
        date = today()
    
    # Query hourly data
    hourly_data = frappe.db.sql("""
        SELECT 
            HOUR(start_time) as hour,
            direction,
            COUNT(*) as count
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) = %s
        GROUP BY HOUR(start_time), direction
        ORDER BY hour
    """, (date,), as_dict=True)
    
    # Initialize result
    hours = [f"{str(h).zfill(2)}:00" for h in range(24)]
    inbound = [0] * 24
    outbound = [0] * 24
    
    for row in hourly_data:
        hour = row.hour
        if row.direction == "Inbound":
            inbound[hour] = row.count
        elif row.direction == "Outbound":
            outbound[hour] = row.count
    
    return {
        "hours": hours,
        "inbound": inbound,
        "outbound": outbound
    }


@frappe.whitelist()
def get_queue_status():
    """
    Get call queue status (if queues are configured).
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    # Placeholder for queue integration
    return {
        "waiting": 0,
        "longest_wait": 0,
        "avg_wait": 0,
        "available_agents": 0
    }


@frappe.whitelist()
def get_sla_metrics(date=None):
    """
    Get SLA metrics for the specified date.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not date:
        date = today()
    
    # Total inbound calls
    total = frappe.db.count(
        "AZ Call Log",
        filters={
            "direction": "Inbound",
            "start_time": [">=", date]
        }
    )
    
    # Answered within threshold (e.g., 20 seconds)
    sla_threshold = 20  # seconds
    
    answered_in_sla = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabAZ Call Log`
        WHERE direction = 'Inbound'
        AND DATE(start_time) = %s
        AND disposition = 'ANSWERED'
        AND TIMESTAMPDIFF(SECOND, start_time, answer_time) <= %s
    """, (date, sla_threshold))[0][0] or 0
    
    sla_rate = (answered_in_sla / total * 100) if total > 0 else 0
    
    return {
        "total_calls": total,
        "answered_in_sla": answered_in_sla,
        "sla_rate": round(sla_rate, 1),
        "threshold_seconds": sla_threshold
    }


@frappe.whitelist()
def get_wallboard_data():
    """
    Get all wallboard data in a single API call.
    Returns comprehensive dashboard data for managers.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    date = today()
    
    # Get today's statistics
    stats = get_today_stats()
    
    # Get active calls
    active_calls = get_active_calls()
    
    # Get agent status
    agents = get_agent_status()
    
    # Get hourly stats
    hourly = get_hourly_stats(date)
    
    # Get SLA metrics
    sla = get_sla_metrics(date)
    
    # Get queue status
    queue = get_queue_status()
    
    return {
        "success": True,
        "stats": stats,
        "active_calls": active_calls,
        "agents": agents,
        "hourly": hourly,
        "sla": sla,
        "queue": queue,
        "timestamp": str(now_datetime())
    }


@frappe.whitelist()
def get_today_stats():
    """
    Get today's call statistics summary.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    date = today()
    
    # Total calls
    total = frappe.db.count(
        "AZ Call Log",
        filters={"start_time": [">=", date]}
    )
    
    # Inbound calls
    inbound = frappe.db.count(
        "AZ Call Log",
        filters={
            "direction": "Inbound",
            "start_time": [">=", date]
        }
    )
    
    # Outbound calls
    outbound = frappe.db.count(
        "AZ Call Log",
        filters={
            "direction": "Outbound",
            "start_time": [">=", date]
        }
    )
    
    # Answered calls
    answered = frappe.db.count(
        "AZ Call Log",
        filters={
            "disposition": "ANSWERED",
            "start_time": [">=", date]
        }
    )
    
    # Missed calls
    missed = frappe.db.count(
        "AZ Call Log",
        filters={
            "disposition": ["in", ["NO ANSWER", "BUSY", "FAILED"]],
            "start_time": [">=", date]
        }
    )
    
    # Average duration
    avg_duration = frappe.db.sql("""
        SELECT AVG(duration) as avg_dur
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) = %s
        AND disposition = 'ANSWERED'
    """, (date,))[0][0] or 0
    
    # Active calls count
    active_count = len(get_active_calls())
    
    return {
        "total": total,
        "inbound": inbound,
        "outbound": outbound,
        "answered": answered,
        "missed": missed,
        "answer_rate": round((answered / total * 100) if total > 0 else 0, 1),
        "avg_duration": int(avg_duration),
        "active_calls": active_count
    }
