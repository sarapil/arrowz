# -*- coding: utf-8 -*-

# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Communications API for Omni-Channel Platform

This module provides REST API endpoints for:
- Fetching communication history for any DocType
- Sending messages across channels
- Managing conversations
- Real-time status updates
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, add_days
import json


# =============================================================================
# Communication History APIs
# =============================================================================

@frappe.whitelist()
def get_communication_history(doctype, docname, channels=None, limit=50, offset=0):
    """
    Get unified communication history for a document
    
    Args:
        doctype: Reference DocType (e.g., "Lead", "Customer")
        docname: Reference document name
        channels: Optional list of channels to filter (e.g., ["WhatsApp", "Telegram", "Email"])
        limit: Number of records per page
        offset: Pagination offset
    
    Returns:
        Dict with communications list and metadata
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    if isinstance(channels, str):
        channels = json.loads(channels) if channels else None
    
    # Build communications list from multiple sources
    communications = []
    
    # Check if Conversation Session table exists
    if frappe.db.table_exists("tabAZ Conversation Session"):
        # 1. Get Conversation Sessions (WhatsApp, Telegram)
        session_filters = {
            "link_doctype": doctype,
            "link_name": docname
        }
        
        if channels:
            session_filters["channel"] = ["in", channels]
        
        try:
            sessions = frappe.get_all(
                "AZ Conversation Session",
                filters=session_filters,
                fields=["name", "channel", "participant_name", "participant_phone", 
                        "last_activity", "status", "unread_count"],
                order_by="last_activity desc",
                limit=limit,
                start=offset
            )
            
            for session in sessions:
                # Get channel details
                channel_info = {}
                if session.channel:
                    try:
                        ch = frappe.get_cached_doc("AZ Omni Channel", session.channel)
                        channel_info = {"channel_type": ch.channel_type, "channel_name": ch.name}
                    except:
                        pass
                
                communications.append({
                    "type": "conversation",
                    "channel": channel_info.get("channel_type", "Unknown"),
                    "session_id": session.name,
                    "contact_name": session.participant_name,
                    "contact_number": session.participant_phone,
                    "last_activity": session.last_activity,
                    "status": session.status,
                    "unread_count": session.unread_count,
                    "messages": []  # Load on demand
                })
        except Exception:
            pass  # Table doesn't exist yet
    
    # 2. Get Email Communications
    if not channels or "Email" in channels:
        emails = frappe.get_all(
            "Communication",
            filters={
                "reference_doctype": doctype,
                "reference_name": docname,
                "communication_type": "Communication",
                "communication_medium": "Email"
            },
            fields=["name", "subject", "sender", "recipients", "sent_or_received",
                    "creation", "seen", "content"],
            order_by="creation desc",
            limit=limit,
            start=offset
        )
        
        for email in emails:
            communications.append({
                "type": "email",
                "channel": "Email",
                "id": email.name,
                "subject": email.subject,
                "from": email.sender,
                "to": email.recipients,
                "direction": "outgoing" if email.sent_or_received == "Sent" else "incoming",
                "last_activity": email.creation,
                "seen": email.seen,
                "preview": email.content[:200] if email.content else ""
            })
    
    # 3. Get Phone Calls (from AZ Call Log)
    if not channels or "Phone" in channels:
        try:
            calls = frappe.get_all(
                "AZ Call Log",
                filters={
                    "linked_doctype": doctype,
                    "linked_document": docname
                },
                fields=["name", "caller_id", "callee_id", "direction", "duration",
                        "status", "start_time", "recording_url"],
                order_by="start_time desc",
                limit=limit,
                start=offset
            )
            
            for call in calls:
                communications.append({
                    "type": "call",
                    "channel": "Phone",
                    "id": call.name,
                    "caller": call.caller_id,
                    "receiver": call.callee_id,
                    "call_type": call.direction,
                    "duration": call.duration,
                    "status": call.status,
                    "last_activity": call.start_time,
                    "recording_url": call.recording_url
                })
        except Exception:
            pass  # Table doesn't exist
    
    # 4. Get Meeting Rooms
    if not channels or "Video" in channels:
        try:
            meetings = frappe.get_all(
                "AZ Meeting Room",
                filters={
                    "link_doctype": doctype,
                    "link_name": docname
                },
                fields=["name", "room_name", "status", "room_type", "scheduled_start",
                        "scheduled_end", "allow_recording"],
                order_by="scheduled_start desc",
                limit=limit,
                start=offset
            )
            
            for meeting in meetings:
                # Get participant count
                try:
                    participant_count = frappe.db.count(
                        "AZ Meeting Participant",
                        filters={"parent": meeting.name}
                    )
                except:
                    participant_count = 0
                
                communications.append({
                    "type": "meeting",
                    "channel": "Video",
                    "id": meeting.name,
                    "room_name": meeting.room_name,
                    "status": meeting.status,
                    "room_type": meeting.room_type,
                    "scheduled_start": meeting.scheduled_start,
                    "scheduled_end": meeting.scheduled_end,
                    "participants": participant_count,
                    "last_activity": meeting.scheduled_start
                })
        except Exception:
            pass  # Table doesn't exist
    
    # Sort all communications by activity time
    communications.sort(key=lambda x: get_datetime(x.get("last_activity") or "1970-01-01"), reverse=True)
    
    # Get aggregated stats
    stats = get_communication_stats(doctype, docname)
    
    return {
        "communications": communications[:limit],
        "total": len(communications),
        "stats": stats,
        "has_more": len(communications) > limit
    }


@frappe.whitelist()
def get_communication_stats(doctype, docname):
    """
    Get communication statistics for a document
    
    Returns counts and summaries for each channel
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    stats = {
        "total_communications": 0,
        "total_unread": 0,
        "channels": {}
    }
    
    # Check if conversation table exists
    if frappe.db.table_exists("tabAZ Conversation Session"):
        try:
            # Get sessions for this document
            sessions = frappe.get_all(
                "AZ Conversation Session",
                filters={
                    "link_doctype": doctype,
                    "link_name": docname
                },
                fields=["name", "channel", "unread_count"]
            )
            
            whatsapp_count = 0
            whatsapp_unread = 0
            telegram_count = 0
            telegram_unread = 0
            
            for session in sessions:
                # Get channel type from channel link
                if session.channel:
                    try:
                        ch = frappe.get_cached_doc("AZ Omni Channel", session.channel)
                        if ch.channel_type == "WhatsApp":
                            whatsapp_count += 1
                            whatsapp_unread += session.unread_count or 0
                        elif ch.channel_type == "Telegram":
                            telegram_count += 1
                            telegram_unread += session.unread_count or 0
                    except:
                        pass
            
            if whatsapp_count:
                stats["channels"]["whatsapp"] = {
                    "sessions": whatsapp_count,
                    "unread": whatsapp_unread
                }
                stats["total_unread"] += whatsapp_unread
            
            if telegram_count:
                stats["channels"]["telegram"] = {
                    "sessions": telegram_count,
                    "unread": telegram_unread
                }
                stats["total_unread"] += telegram_unread
        except Exception:
            pass
    
    # Email stats
    try:
        email_count = frappe.db.count(
            "Communication",
            filters={
                "reference_doctype": doctype,
                "reference_name": docname,
                "communication_medium": "Email"
            }
        )
        
        unread_emails = frappe.db.count(
            "Communication",
            filters={
                "reference_doctype": doctype,
                "reference_name": docname,
                "communication_medium": "Email",
                "seen": 0
            }
        )
        
        stats["channels"]["email"] = {
            "count": email_count,
            "unread": unread_emails
        }
        stats["total_unread"] += unread_emails
    except Exception:
        pass
    
    # Call stats from AZ Call Log
    try:
        call_count = frappe.db.count(
            "AZ Call Log",
            filters={
                "linked_doctype": doctype,
                "linked_document": docname
            }
        )
        
        missed_calls = frappe.db.count(
            "AZ Call Log",
            filters={
                "linked_doctype": doctype,
                "linked_document": docname,
                "status": "Missed"
            }
        )
        
        stats["channels"]["phone"] = {
            "count": call_count,
            "missed": missed_calls
        }
    except Exception:
        pass
    
    # Meeting stats
    try:
        meeting_count = frappe.db.count(
            "AZ Meeting Room",
            filters={
                "link_doctype": doctype,
                "link_name": docname
            }
        )
        
        upcoming_meetings = frappe.db.count(
            "AZ Meeting Room",
            filters={
                "link_doctype": doctype,
                "link_name": docname,
                "status": "Scheduled",
                "scheduled_start": [">=", now_datetime()]
            }
        )
        
        stats["channels"]["video"] = {
            "count": meeting_count,
            "upcoming": upcoming_meetings
        }
    except Exception:
        pass
    
    # Calculate total
    stats["total_communications"] = sum([
        stats["channels"].get("whatsapp", {}).get("sessions", 0),
        stats["channels"].get("telegram", {}).get("sessions", 0),
        stats["channels"].get("email", {}).get("count", 0),
        stats["channels"].get("phone", {}).get("count", 0),
        stats["channels"].get("video", {}).get("count", 0)
    ])
    
    return stats


# =============================================================================
# Send Message APIs
# =============================================================================

@frappe.whitelist()
def send_message(channel, recipient, message, message_type="text", 
                 media_url=None, reference_doctype=None, reference_name=None,
                 template_name=None, template_params=None):
    """
    Send a message through any channel
    
    Args:
        channel: "WhatsApp", "Telegram", "SMS", "Email"
        recipient: Phone number, chat_id, or email
        message: Message content
        message_type: "text", "image", "document", "template"
        media_url: URL for media messages
        reference_doctype: Optional link to document
        reference_name: Optional document name
        template_name: For template messages
        template_params: Template parameters as JSON
    
    Returns:
        Message status and ID
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    if isinstance(template_params, str):
        template_params = json.loads(template_params) if template_params else None
    
    if channel == "WhatsApp":
        return _send_whatsapp_message(
            recipient, message, message_type, media_url,
            reference_doctype, reference_name, template_name, template_params
        )
    elif channel == "Telegram":
        return _send_telegram_message(
            recipient, message, message_type, media_url,
            reference_doctype, reference_name
        )
    elif channel == "Email":
        return _send_email_message(
            recipient, message, reference_doctype, reference_name
        )
    else:
        frappe.throw(f"Unsupported channel: {channel}")


def _send_whatsapp_message(recipient, message, message_type, media_url,
                           ref_doctype, ref_name, template_name, template_params):
    """Send WhatsApp message"""
    from arrowz.integrations.whatsapp import WhatsAppCloudDriver
    
    # Get active WhatsApp channel
    channel = frappe.get_all(
        "AZ Omni Channel",
        filters={
            "channel_type": "WhatsApp",
            "enabled": 1,
            "is_default": 1
        },
        fields=["name", "provider"],
        limit=1
    )
    
    if not channel:
        frappe.throw(_("No active WhatsApp channel configured"))
    
    channel = frappe.get_doc("AZ Omni Channel", channel[0].name)
    provider = frappe.get_doc("AZ Omni Provider", channel.provider)
    
    # Initialize driver
    driver = WhatsAppCloudDriver(
        access_token=provider.get_password("api_key"),
        phone_number_id=channel.get_password("channel_id")
    )
    
    # Send message
    if message_type == "template":
        result = driver.send_template(
            recipient=recipient,
            template_name=template_name,
            template_params=template_params
        )
    elif message_type == "text":
        result = driver.send_text(recipient, message)
    elif message_type in ["image", "document", "video", "audio"]:
        result = driver.send_media(recipient, media_url, message_type, message)
    else:
        frappe.throw(f"Unsupported message type: {message_type}")
    
    # Log the message
    if result.get("success"):
        _log_outgoing_message(
            channel_type="WhatsApp",
            channel_name=channel.name,
            recipient=recipient,
            message=message,
            message_type=message_type,
            message_id=result.get("message_id"),
            ref_doctype=ref_doctype,
            ref_name=ref_name
        )
    
    return result


def _send_telegram_message(recipient, message, message_type, media_url,
                           ref_doctype, ref_name):
    """Send Telegram message"""
    from arrowz.integrations.telegram import TelegramDriver
    
    # Get active Telegram channel
    channel = frappe.get_all(
        "AZ Omni Channel",
        filters={
            "channel_type": "Telegram",
            "enabled": 1,
            "is_default": 1
        },
        fields=["name", "provider"],
        limit=1
    )
    
    if not channel:
        frappe.throw(_("No active Telegram channel configured"))
    
    channel = frappe.get_doc("AZ Omni Channel", channel[0].name)
    provider = frappe.get_doc("AZ Omni Provider", channel.provider)
    
    # Initialize driver
    driver = TelegramDriver(
        bot_token=provider.get_password("api_key")
    )
    
    # Send message
    if message_type == "text":
        result = driver.send_text(recipient, message)
    elif message_type in ["image", "document", "video", "audio"]:
        result = driver.send_media(recipient, media_url, message_type, message)
    else:
        frappe.throw(f"Unsupported message type: {message_type}")
    
    # Log the message
    if result.get("success"):
        _log_outgoing_message(
            channel_type="Telegram",
            channel_name=channel.name,
            recipient=recipient,
            message=message,
            message_type=message_type,
            message_id=result.get("message_id"),
            ref_doctype=ref_doctype,
            ref_name=ref_name
        )
    
    return result


def _send_email_message(recipient, message, ref_doctype, ref_name):
    """Send email message"""
    frappe.sendmail(
        recipients=[recipient],
        message=message,
        reference_doctype=ref_doctype,
        reference_name=ref_name
    )
    
    return {"success": True}


def _log_outgoing_message(channel_type, channel_name, recipient, message,
                          message_type, message_id, ref_doctype, ref_name):
    """Log outgoing message to conversation session"""
    # Find or create session
    session = frappe.get_all(
        "AZ Conversation Session",
        filters={
            "channel_type": channel_type,
            "contact_number": recipient,
            "status": ["in", ["Active", "Pending"]]
        },
        fields=["name"],
        limit=1
    )
    
    if session:
        session_doc = frappe.get_doc("AZ Conversation Session", session[0].name)
    else:
        # Create new session
        session_doc = frappe.get_doc({
            "doctype": "AZ Conversation Session",
            "channel_type": channel_type,
            "channel": channel_name,
            "contact_number": recipient,
            "status": "Active",
            "reference_doctype": ref_doctype,
            "reference_name": ref_name
        })
        session_doc.insert(ignore_permissions=True)
    
    # Add message to session
    session_doc.append("messages", {
        "message_id": message_id,
        "direction": "Outgoing",
        "message_type": message_type.capitalize(),
        "content": message,
        "timestamp": now_datetime(),
        "status": "Sent"
    })
    
    session_doc.last_message_at = now_datetime()
    session_doc.save(ignore_permissions=True)


# =============================================================================
# Conversation Management APIs
# =============================================================================

@frappe.whitelist()
def get_conversation_messages(session_id, limit=50, before_timestamp=None):
    """
    Get messages for a conversation session
    
    Args:
        session_id: AZ Conversation Session name
        limit: Number of messages
        before_timestamp: For pagination, get messages before this time
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    session = frappe.get_doc("AZ Conversation Session", session_id)
    
    filters = {"parent": session_id}
    if before_timestamp:
        filters["timestamp"] = ["<", before_timestamp]
    
    messages = frappe.get_all(
        "AZ Conversation Message",
        filters=filters,
        fields=["name", "message_id", "direction", "message_type", "content",
                "media_url", "timestamp", "status", "error_message"],
        order_by="timestamp desc",
        limit=limit
    )
    
    return {
        "session": {
            "name": session.name,
            "channel_type": session.channel_type,
            "contact_name": session.contact_name,
            "contact_number": session.contact_number,
            "status": session.status,
            "assigned_to": session.assigned_to
        },
        "messages": list(reversed(messages)),  # Oldest first
        "has_more": len(messages) == limit
    }


@frappe.whitelist()
def mark_messages_read(session_id):
    """Mark all messages in a session as read"""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    session = frappe.get_doc("AZ Conversation Session", session_id)
    session.unread_count = 0
    session.save(ignore_permissions=True)
    
    return {"success": True}


@frappe.whitelist()
def assign_conversation(session_id, user):
    """Assign a conversation to a user"""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    session = frappe.get_doc("AZ Conversation Session", session_id)
    session.assigned_to = user
    session.save(ignore_permissions=True)
    
    # Notify the assigned user
    frappe.publish_realtime(
        "conversation_assigned",
        {
            "session": session_id,
            "assigned_by": frappe.session.user,
            "channel": session.channel_type,
            "contact": session.contact_name or session.contact_number
        },
        user=user
    )
    
    return {"success": True}


@frappe.whitelist()
def close_conversation(session_id, reason=None):
    """Close a conversation session"""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    session = frappe.get_doc("AZ Conversation Session", session_id)
    session.status = "Closed"
    session.closed_by = frappe.session.user
    session.closed_at = now_datetime()
    if reason:
        session.add_comment("Comment", reason)
    session.save(ignore_permissions=True)
    
    return {"success": True}


@frappe.whitelist()
def get_active_conversations(user=None, channel_type=None, limit=50):
    """
    Get active conversations for the current user or all
    
    Args:
        user: Filter by assigned user
        channel_type: Filter by channel
        limit: Number of conversations
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    # Check if table exists
    if not frappe.db.table_exists("tabAZ Conversation Session"):
        return []
    
    filters = {"status": ["in", ["Active", "Pending"]]}
    
    if user:
        filters["assigned_to"] = user
    
    if channel_type:
        filters["channel"] = channel_type
    
    try:
        sessions = frappe.get_all(
            "AZ Conversation Session",
            filters=filters,
            fields=["name", "channel", "participant_name", "participant_phone",
                    "last_activity", "status", "unread_count", "assigned_to",
                    "link_doctype", "link_name", "last_message_preview"],
            order_by="last_activity desc",
            limit=limit
        )
        
        return sessions
        
    except Exception:
        return []


# =============================================================================
# Quick Actions APIs
# =============================================================================

@frappe.whitelist()
def get_quick_replies(channel_type):
    """Get quick reply templates for a channel"""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    # This could be extended to support custom quick replies per user/team
    default_replies = {
        "WhatsApp": [
            {"label": "👋 Greeting", "message": "Hello! How can I help you today?"},
            {"label": "🙏 Thank you", "message": "Thank you for contacting us!"},
            {"label": "⏳ Please wait", "message": "Please hold on, I'll get back to you shortly."},
            {"label": "📞 Call request", "message": "Would you like us to call you?"},
            {"label": "📧 Email request", "message": "Could you please share your email address?"}
        ],
        "Telegram": [
            {"label": "👋 Greeting", "message": "Hello! How can I assist you?"},
            {"label": "🙏 Thank you", "message": "Thank you for reaching out!"},
            {"label": "⏳ Please wait", "message": "I'll check and get back to you."},
            {"label": "📞 Call request", "message": "Shall we schedule a call?"},
            {"label": "🔗 Website", "message": "Visit our website for more info."}
        ]
    }
    
    return default_replies.get(channel_type, [])


@frappe.whitelist()
def schedule_meeting(reference_doctype, reference_name, participants, 
                     room_name, scheduled_start, scheduled_end=None,
                     room_type="Temporary", allow_recording=False):
    """
    Quick action to schedule a meeting from any DocType
    
    Args:
        reference_doctype: Link document type
        reference_name: Link document name
        participants: List of participant dicts [{email, name, is_moderator}]
        room_name: Meeting room name
        scheduled_start: Meeting start datetime
        scheduled_end: Optional end datetime
        room_type: "Permanent" or "Temporary"
        allow_recording: Whether recording is allowed
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    if isinstance(participants, str):
        participants = json.loads(participants)
    
    room = frappe.get_doc({
        "doctype": "AZ Meeting Room",
        "room_name": room_name,
        "room_type": room_type,
        "status": "Scheduled",
        "scheduled_start": scheduled_start,
        "scheduled_end": scheduled_end,
        "allow_recording": allow_recording,
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "participants": [
            {
                "participant_type": p.get("type", "Contact"),
                "participant_name": p.get("name"),
                "email": p.get("email"),
                "is_moderator": p.get("is_moderator", 0)
            }
            for p in participants
        ]
    })
    
    room.insert()
    
    return {
        "success": True,
        "room_id": room.name,
        "join_url": room.host_url
    }


@frappe.whitelist()
def start_whatsapp_conversation(phone_number, reference_doctype=None, 
                                 reference_name=None, template_name=None):
    """
    Quick action to start a WhatsApp conversation
    
    If the 24h window is closed, a template message must be used
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    # Check for existing active session
    existing = frappe.get_all(
        "AZ Conversation Session",
        filters={
            "channel_type": "WhatsApp",
            "contact_number": phone_number,
            "status": "Active",
            "window_expires_at": [">=", now_datetime()]
        },
        limit=1
    )
    
    if existing:
        return {
            "success": True,
            "session_id": existing[0].name,
            "window_open": True
        }
    
    # Window is closed, template required
    if not template_name:
        return {
            "success": False,
            "window_open": False,
            "message": "24h window expired. Please select a template to initiate conversation."
        }
    
    # Send template and create session
    result = send_message(
        channel="WhatsApp",
        recipient=phone_number,
        message="",
        message_type="template",
        template_name=template_name,
        reference_doctype=reference_doctype,
        reference_name=reference_name
    )
    
    if result.get("success"):
        # Get the created session
        session = frappe.get_all(
            "AZ Conversation Session",
            filters={
                "channel_type": "WhatsApp",
                "contact_number": phone_number
            },
            order_by="creation desc",
            limit=1
        )
        
        return {
            "success": True,
            "session_id": session[0].name if session else None,
            "window_open": True
        }
    
    return result


# =============================================================================
# Dashboard Statistics API
# =============================================================================

@frappe.whitelist()
def get_communications_stats():
    """
    Get communications statistics for the dashboard.
    Returns call counts, SMS counts, and recording counts for today.
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    from frappe.utils import today
    
    user = frappe.session.user
    date_filter = today()
    
    # Get user's extension
    extension = frappe.db.get_value(
        "AZ Extension",
        {"user": user, "is_active": 1},
        "extension"
    )
    
    # Total calls today
    total_calls = frappe.db.count(
        "AZ Call Log",
        filters={
            "creation": [">=", date_filter]
        }
    ) if frappe.db.table_exists("tabAZ Call Log") else 0
    
    # Missed calls today
    missed_calls = frappe.db.count(
        "AZ Call Log",
        filters={
            "creation": [">=", date_filter],
            "status": "Missed"
        }
    ) if frappe.db.table_exists("tabAZ Call Log") else 0
    
    # Total SMS today
    total_sms = frappe.db.count(
        "AZ SMS Message",
        filters={
            "creation": [">=", date_filter]
        }
    ) if frappe.db.table_exists("tabAZ SMS Message") else 0
    
    # Total recordings
    total_recordings = frappe.db.count(
        "AZ Call Log",
        filters={
            "recording_url": ["is", "set"]
        }
    ) if frappe.db.table_exists("tabAZ Call Log") else 0
    
    return {
        "total_calls": total_calls,
        "missed_calls": missed_calls,
        "total_sms": total_sms,
        "total_recordings": total_recordings
    }
