# Copyright (c) 2026, Arrowz and contributors
# License: MIT

"""
Arrowz Notifications API
Provides notification management for softphone
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, get_datetime


@frappe.whitelist()
def get_pending_notifications():
    """
    Get pending notifications for the current user.
    
    Returns:
        dict with pending_sms and missed_calls counts
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    
    # Get user's extensions
    extensions = frappe.get_all(
        "AZ Extension",
        filters={"user": user, "is_active": 1},
        pluck="extension"
    )
    
    if not extensions:
        return {
            "pending_sms": [],
            "missed_calls": 0
        }
    
    # Count unread SMS
    pending_sms = []
    try:
        if frappe.db.table_exists("AZ SMS Message"):
            sms_messages = frappe.get_all(
                "AZ SMS Message",
                filters={
                    "direction": "Inbound",
                    "read_status": 0,
                    "recipient": ["in", extensions]
                },
                fields=["name", "sender", "message", "received_time"],
                order_by="received_time desc",
                limit=10
            )
            pending_sms = sms_messages
    except Exception:
        pass
    
    # Count missed calls today
    missed_calls = 0
    try:
        if frappe.db.table_exists("AZ Call Log"):
            today = now_datetime().date()
            missed_calls = frappe.db.count(
                "AZ Call Log",
                filters={
                    "status": "Missed",
                    "direction": "Inbound",
                    "callee_id": ["in", extensions],
                    "start_time": [">=", today]
                }
            )
    except Exception:
        pass
    
    return {
        "pending_sms": pending_sms,
        "missed_calls": missed_calls
    }


@frappe.whitelist()
def mark_sms_read(name):
    """
    Mark an SMS as read.
    
    Args:
        name: SMS Message name
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    try:
        frappe.db.set_value("AZ SMS Message", name, "read_status", 1)
        frappe.db.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def get_unread_count():
    """
    Get count of unread notifications.
    
    Returns:
        dict with counts
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    
    extensions = frappe.get_all(
        "AZ Extension",
        filters={"user": user, "is_active": 1},
        pluck="extension"
    )
    
    if not extensions:
        return {"sms": 0, "missed": 0, "total": 0}
    
    sms_count = 0
    missed_count = 0
    
    try:
        if frappe.db.table_exists("AZ SMS Message"):
            sms_count = frappe.db.count(
                "AZ SMS Message",
                filters={
                    "direction": "Inbound",
                    "read_status": 0,
                    "recipient": ["in", extensions]
                }
            )
    except Exception:
        pass
    
    try:
        if frappe.db.table_exists("AZ Call Log"):
            today = now_datetime().date()
            missed_count = frappe.db.count(
                "AZ Call Log",
                filters={
                    "status": "Missed",
                    "direction": "Inbound",
                    "callee_id": ["in", extensions],
                    "start_time": [">=", today],
                    "acknowledged": 0
                }
            )
    except Exception:
        pass
    
    return {
        "sms": sms_count,
        "missed": missed_count,
        "total": sms_count + missed_count
    }


@frappe.whitelist()
def acknowledge_missed_call(name):
    """
    Acknowledge a missed call.
    
    Args:
        name: Call Log name
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    try:
        frappe.db.set_value("AZ Call Log", name, "acknowledged", 1)
        frappe.db.commit()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
