# Copyright (c) 2024, Arrowz Team
# License: MIT

"""
Arrowz Notification Configuration

Define notification rules for Arrowz events.
"""

import frappe
from frappe import _


def get_notification_config():
    """
    Return notification configuration for Arrowz.
    
    This defines what shows up in the notification dropdown.
    """
    return {
        "for_doctype": {
            "AZ Call Log": {
                "status": ["=", "missed"]
            },
            "AZ SMS Message": {
                "direction": ["=", "inbound"],
                "is_read": ["=", 0]
            },
            # Omni-Channel notifications
            "AZ Conversation Session": {
                "status": ["in", ["Active", "Pending"]],
                "unread_count": [">", 0]
            },
            "AZ Meeting Room": {
                "status": ["=", "Scheduled"]
            }
        },
        "for_module": {
            "Arrowz": ["AZ Conversation Session", "AZ Meeting Room", "AZ Omni Provider"]
        },
        "for_module_doctypes": {
            "Arrowz": [
                "AZ Omni Provider",
                "AZ Omni Channel", 
                "AZ Conversation Session",
                "AZ Meeting Room",
                "AZ Call Log",
                "AZ SMS Message"
            ]
        }
    }


def send_missed_call_notification(call_log):
    """Send notification for missed call"""
    if call_log.status != "missed":
        return
    
    # Get agent for the extension
    agent = frappe.db.get_value(
        "AZ Extension",
        {"extension": call_log.extension},
        "user"
    )
    
    if not agent:
        return
    
    # Create notification
    doc = frappe.get_doc({
        "doctype": "Notification Log",
        "for_user": agent,
        "type": "Alert",
        "document_type": "AZ Call Log",
        "document_name": call_log.name,
        "subject": f"Missed call from {call_log.caller_id}",
        "email_content": f"You missed a call from {call_log.caller_id} at {call_log.call_datetime}"
    })
    doc.insert(ignore_permissions=True)


def send_sms_notification(sms_message):
    """Send notification for incoming SMS"""
    if sms_message.direction != "inbound":
        return
    
    # Find user linked to this number
    # This would need to be customized based on your setup
    
    # Publish real-time event
    frappe.publish_realtime(
        event="arrowz_sms_received",
        message={
            "from": sms_message.phone_number,
            "content": sms_message.content[:100],
            "name": sms_message.name
        },
        after_commit=True
    )


# =============================================================================
# Omni-Channel Notification Helpers
# =============================================================================

def send_omni_notification(user, title, message, doctype=None, docname=None, 
                           notification_type="Alert"):
    """
    Send a notification to a user
    
    Args:
        user: User ID
        title: Notification title
        message: Notification message
        doctype: Optional linked DocType
        docname: Optional linked document name
        notification_type: Alert, Mention, Assignment, etc.
    """
    doc = frappe.get_doc({
        "doctype": "Notification Log",
        "subject": title,
        "email_content": message,
        "for_user": user,
        "type": notification_type,
        "document_type": doctype,
        "document_name": docname
    })
    doc.insert(ignore_permissions=True)
    
    # Also send real-time notification
    frappe.publish_realtime(
        "notification",
        {
            "title": title,
            "message": message,
            "type": notification_type,
            "doctype": doctype,
            "docname": docname
        },
        user=user,
        after_commit=True
    )


def get_unread_counts(user=None):
    """
    Get unread message counts across all channels for a user
    
    Args:
        user: Optional user ID. If not provided, uses current user.
    
    Returns:
        Dict with counts per channel
    """
    if not user:
        user = frappe.session.user
    
    counts = {
        "total": 0,
        "whatsapp": 0,
        "telegram": 0,
        "email": 0,
        "calls_missed": 0,
        "meetings_upcoming": 0
    }
    
    # WhatsApp unread
    whatsapp = frappe.db.sql("""
        SELECT COALESCE(SUM(unread_count), 0) as count
        FROM `tabAZ Conversation Session`
        WHERE channel_type = 'WhatsApp'
        AND status IN ('Active', 'Pending')
        AND (assigned_to = %s OR assigned_to IS NULL)
    """, user, as_dict=True)
    counts["whatsapp"] = int(whatsapp[0].count) if whatsapp else 0
    
    # Telegram unread
    telegram = frappe.db.sql("""
        SELECT COALESCE(SUM(unread_count), 0) as count
        FROM `tabAZ Conversation Session`
        WHERE channel_type = 'Telegram'
        AND status IN ('Active', 'Pending')
        AND (assigned_to = %s OR assigned_to IS NULL)
    """, user, as_dict=True)
    counts["telegram"] = int(telegram[0].count) if telegram else 0
    
    # Email unread
    email = frappe.db.count(
        "Communication",
        filters={
            "communication_type": "Communication",
            "communication_medium": "Email",
            "seen": 0,
            "recipients": ["like", f"%{user}%"]
        }
    )
    counts["email"] = email
    
    # Missed calls (today)
    from frappe.utils import today
    missed = frappe.db.count(
        "Call Log",
        filters={
            "status": "No Answer",
            "creation": [">=", today()],
            "receiver": user
        }
    )
    counts["calls_missed"] = missed
    
    # Upcoming meetings
    from frappe.utils import now_datetime, add_to_date
    end_of_day = add_to_date(now_datetime(), hours=24)
    meetings = frappe.db.count(
        "AZ Meeting Room",
        filters={
            "status": "Scheduled",
            "scheduled_start": ["between", [now_datetime(), end_of_day]],
            "owner": user
        }
    )
    counts["meetings_upcoming"] = meetings
    
    # Total
    counts["total"] = (
        counts["whatsapp"] + 
        counts["telegram"] + 
        counts["email"] + 
        counts["calls_missed"]
    )
    
    return counts


@frappe.whitelist()
def get_notification_summary():
    """
    API to get notification summary for current user
    """
    counts = get_unread_counts()
    
    # Get recent conversations
    recent = frappe.get_all(
        "AZ Conversation Session",
        filters={
            "status": ["in", ["Active", "Pending"]],
            "unread_count": [">", 0]
        },
        fields=["name", "channel_type", "contact_name", "contact_number", 
                "unread_count", "last_message_at"],
        order_by="last_message_at desc",
        limit=5
    )
    
    # Get upcoming meetings
    from frappe.utils import now_datetime
    meetings = frappe.get_all(
        "AZ Meeting Room",
        filters={
            "status": "Scheduled",
            "scheduled_start": [">=", now_datetime()]
        },
        fields=["name", "room_name", "scheduled_start", "host_url"],
        order_by="scheduled_start asc",
        limit=3
    )
    
    return {
        "counts": counts,
        "recent_conversations": recent,
        "upcoming_meetings": meetings
    }


def notify_window_expiring(session_id):
    """
    Notify when WhatsApp 24h window is about to expire
    """
    session = frappe.get_doc("AZ Conversation Session", session_id)
    
    user = session.assigned_to or session.owner
    
    send_omni_notification(
        user=user,
        title=_("WhatsApp Window Expiring"),
        message=_(
            "The 24-hour conversation window with {0} will expire soon. "
            "Send a template message to continue the conversation."
        ).format(session.contact_name or session.contact_number),
        doctype="AZ Conversation Session",
        docname=session_id,
        notification_type="Alert"
    )


def notify_meeting_reminder(room_id, minutes_before=15):
    """
    Send meeting reminder notifications
    """
    room = frappe.get_doc("AZ Meeting Room", room_id)
    
    # Notify all participants
    for p in room.participants:
        if p.email:
            # Find user by email
            user = frappe.db.get_value("User", {"email": p.email}, "name")
            if user:
                send_omni_notification(
                    user=user,
                    title=_("Meeting Starting Soon"),
                    message=_(
                        "The meeting '{0}' will start in {1} minutes. "
                        "<a href='{2}'>Join now</a>"
                    ).format(room.room_name, minutes_before, p.join_url),
                    doctype="AZ Meeting Room",
                    docname=room_id,
                    notification_type="Alert"
                )
    
    # Also notify the owner
    send_omni_notification(
        user=room.owner,
        title=_("Your Meeting Starting Soon"),
        message=_(
            "Your meeting '{0}' will start in {1} minutes. "
            "<a href='{2}'>Start meeting</a>"
        ).format(room.room_name, minutes_before, room.host_url),
        doctype="AZ Meeting Room",
        docname=room_id,
        notification_type="Alert"
    )


def check_meeting_reminders():
    """
    Scheduled task to check for upcoming meetings and send reminders
    """
    from frappe.utils import now_datetime, add_to_date
    
    # Find meetings starting in 15 minutes
    margin_start = add_to_date(now_datetime(), minutes=14)
    margin_end = add_to_date(now_datetime(), minutes=16)
    
    meetings = frappe.get_all(
        "AZ Meeting Room",
        filters={
            "status": "Scheduled",
            "scheduled_start": ["between", [margin_start, margin_end]],
            "reminder_sent": 0
        },
        fields=["name"]
    )
    
    for meeting in meetings:
        notify_meeting_reminder(meeting.name)
        frappe.db.set_value("AZ Meeting Room", meeting.name, "reminder_sent", 1)
