# -*- coding: utf-8 -*-
# Copyright (c) 2024, Arrowz and contributors
# For license information, please see license.txt

"""
Dashboard API for Arrowz

This module provides REST API endpoints for dashboard statistics and data.
"""

import frappe
from frappe import _
from frappe.utils import today, now_datetime, add_days


@frappe.whitelist()
def get_communications_stats():
    """
    Get communications statistics for the dashboard.
    Returns call counts, SMS counts, and recording counts for today.
    """
    date_filter = today()
    
    # Total calls today
    total_calls = 0
    missed_calls = 0
    total_recordings = 0
    
    if frappe.db.table_exists("tabAZ Call Log"):
        total_calls = frappe.db.count(
            "AZ Call Log",
            filters={
                "creation": [">=", date_filter]
            }
        ) or 0
        
        missed_calls = frappe.db.count(
            "AZ Call Log",
            filters={
                "creation": [">=", date_filter],
                "status": "Missed"
            }
        ) or 0
        
        total_recordings = frappe.db.count(
            "AZ Call Log",
            filters={
                "recording_url": ["is", "set"]
            }
        ) or 0
    
    # Total SMS today
    total_sms = 0
    if frappe.db.table_exists("tabAZ SMS Message"):
        total_sms = frappe.db.count(
            "AZ SMS Message",
            filters={
                "creation": [">=", date_filter]
            }
        ) or 0
    
    return {
        "total_calls": total_calls,
        "missed_calls": missed_calls,
        "total_sms": total_sms,
        "total_recordings": total_recordings
    }


@frappe.whitelist()
def get_overview_stats():
    """
    Get overview statistics for the main dashboard.
    """
    from frappe.utils import get_datetime, add_days
    
    today_date = today()
    week_ago = add_days(today_date, -7)
    
    stats = {
        "today": {},
        "week": {},
        "trends": {}
    }
    
    if frappe.db.table_exists("tabAZ Call Log"):
        # Today's stats
        stats["today"]["calls"] = frappe.db.count("AZ Call Log", {"creation": [">=", today_date]}) or 0
        stats["today"]["inbound"] = frappe.db.count("AZ Call Log", {"creation": [">=", today_date], "direction": "Inbound"}) or 0
        stats["today"]["outbound"] = frappe.db.count("AZ Call Log", {"creation": [">=", today_date], "direction": "Outbound"}) or 0
        stats["today"]["missed"] = frappe.db.count("AZ Call Log", {"creation": [">=", today_date], "status": "Missed"}) or 0
        
        # Week stats
        stats["week"]["calls"] = frappe.db.count("AZ Call Log", {"creation": [">=", week_ago]}) or 0
        
        # Calculate average call duration
        avg_duration = frappe.db.sql("""
            SELECT AVG(duration) as avg_duration 
            FROM `tabAZ Call Log` 
            WHERE DATE(creation) = %s AND duration > 0
        """, (today_date,), as_dict=True)
        stats["today"]["avg_duration"] = round(avg_duration[0].avg_duration or 0, 1)
    
    if frappe.db.table_exists("tabAZ SMS Message"):
        stats["today"]["sms"] = frappe.db.count("AZ SMS Message", {"creation": [">=", today_date]}) or 0
        stats["week"]["sms"] = frappe.db.count("AZ SMS Message", {"creation": [">=", week_ago]}) or 0
    
    return stats


@frappe.whitelist()
def get_agent_status_summary():
    """
    Get summary of all agent statuses for wallboard.
    """
    agents = frappe.get_all(
        "AZ Extension",
        filters={"is_active": 1},
        fields=["name", "extension", "display_name", "user"]
    )
    
    summary = {
        "available": 0,
        "busy": 0,
        "away": 0,
        "dnd": 0,
        "offline": 0,
        "agents": []
    }
    
    for agent in agents:
        status = frappe.cache().get_value(f"agent_status_{agent.user}") or "offline"
        summary[status] = summary.get(status, 0) + 1
        summary["agents"].append({
            "name": agent.name,
            "extension": agent.extension,
            "display_name": agent.display_name or agent.extension,
            "user": agent.user,
            "status": status
        })
    
    return summary


@frappe.whitelist()
def get_active_calls():
    """
    Get list of currently active calls.
    """
    # In a real implementation, this would query the PBX for active channels
    # For now, return calls that started recently and have no end_time
    
    if not frappe.db.table_exists("tabAZ Call Log"):
        return []
    
    active_calls = frappe.get_all(
        "AZ Call Log",
        filters={
            "status": "Active"
        },
        fields=[
            "name", "caller_id", "callee_id", "direction", 
            "start_time", "extension", "contact_name"
        ],
        order_by="start_time desc",
        limit=20
    )
    
    return active_calls


@frappe.whitelist()
def get_queue_status():
    """
    Get call queue status for wallboard.
    """
    # This would integrate with FreePBX/Asterisk queue status
    # For now, return sample data structure
    
    queues = []
    
    if frappe.db.table_exists("tabAZ Queue"):
        queue_list = frappe.get_all(
            "AZ Queue",
            filters={"is_active": 1},
            fields=["name", "queue_number", "queue_name"]
        )
        
        for q in queue_list:
            queues.append({
                "name": q.name,
                "queue_number": q.queue_number,
                "queue_name": q.queue_name,
                "waiting": 0,  # Would come from AMI
                "agents": 0,   # Would come from AMI
                "available_agents": 0
            })
    
    return queues
