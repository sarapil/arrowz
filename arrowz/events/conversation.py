# -*- coding: utf-8 -*-
# Copyright (c) 2024, Arrowz and contributors
# For license information, please see license.txt

"""
Conversation Event Handlers

Handles events for AZ Conversation Session DocType:
- Session creation
- Session updates
- Message notifications
- Auto-linking to contacts
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date


def on_session_create(doc, method):
    """
    Handle new conversation session creation
    
    - Auto-link to existing Contact/Lead/Customer
    - Notify assigned user if any
    - Broadcast real-time event
    """
    # Try to auto-link to existing contact
    if not doc.reference_doctype and doc.contact_number:
        link_to_contact(doc)
    
    # Notify team about new conversation
    if doc.channel_type in ["WhatsApp", "Telegram"]:
        frappe.publish_realtime(
            "new_conversation",
            {
                "session_id": doc.name,
                "channel": doc.channel_type,
                "contact_name": doc.contact_name,
                "contact_number": doc.contact_number,
                "timestamp": str(now_datetime())
            },
            after_commit=True
        )


def on_session_update(doc, method):
    """
    Handle conversation session updates
    
    - Track window expiry for WhatsApp
    - Notify on status changes
    - Broadcast updates to connected clients
    """
    # Check if there are new messages
    if doc.has_value_changed("last_message_at"):
        handle_new_message(doc)
    
    # Check if assignment changed
    if doc.has_value_changed("assigned_to"):
        notify_assignment(doc)
    
    # Check if status changed
    if doc.has_value_changed("status"):
        handle_status_change(doc)


def link_to_contact(doc):
    """
    Try to find and link existing Contact/Lead/Customer by phone number
    """
    phone = doc.contact_number
    if not phone:
        return
    
    # Normalize phone number (remove spaces, dashes, etc.)
    normalized = normalize_phone(phone)
    
    # Try to find Contact first
    contact = frappe.get_all(
        "Contact",
        filters=[
            ["Contact Phone", "phone", "like", f"%{normalized[-10:]}%"]
        ],
        fields=["name", "first_name", "last_name"],
        limit=1
    )
    
    if contact:
        doc.reference_doctype = "Contact"
        doc.reference_name = contact[0].name
        doc.contact_name = f"{contact[0].first_name or ''} {contact[0].last_name or ''}".strip()
        return
    
    # Try to find Lead
    lead = frappe.get_all(
        "Lead",
        filters=[
            ["mobile_no", "like", f"%{normalized[-10:]}%"]
        ],
        fields=["name", "lead_name"],
        limit=1
    )
    
    if lead:
        doc.reference_doctype = "Lead"
        doc.reference_name = lead[0].name
        doc.contact_name = lead[0].lead_name
        return
    
    # Try to find Customer
    customer = frappe.get_all(
        "Customer",
        filters=[
            ["mobile_no", "like", f"%{normalized[-10:]}%"]
        ],
        fields=["name", "customer_name"],
        limit=1
    )
    
    if customer:
        doc.reference_doctype = "Customer"
        doc.reference_name = customer[0].name
        doc.contact_name = customer[0].customer_name


def normalize_phone(phone):
    """Remove non-numeric characters from phone number"""
    import re
    return re.sub(r'[^\d]', '', phone)


def handle_new_message(doc):
    """
    Handle new message in session
    
    - Update unread count
    - Send notification
    - Broadcast to clients
    """
    # Get the latest message
    if doc.messages:
        latest = doc.messages[-1]
        
        # If incoming message, increment unread
        if latest.direction == "Incoming":
            # Notify assigned user or all team members
            notify_new_message(doc, latest)
        
        # Broadcast to connected clients viewing this document
        frappe.publish_realtime(
            "new_message",
            {
                "session_id": doc.name,
                "channel": doc.channel_type,
                "message": {
                    "id": latest.message_id,
                    "direction": latest.direction,
                    "type": latest.message_type,
                    "content": latest.content,
                    "timestamp": str(latest.timestamp),
                    "status": latest.status
                },
                "contact_name": doc.contact_name,
                "contact_number": doc.contact_number,
                "reference_doctype": doc.reference_doctype,
                "reference_name": doc.reference_name,
                "preview": (latest.content or "")[:100] if latest.message_type == "Text" else f"[{latest.message_type}]"
            },
            doctype="AZ Conversation Session",
            docname=doc.name,
            after_commit=True
        )
        
        # Also broadcast to the reference document if linked
        if doc.reference_doctype and doc.reference_name:
            frappe.publish_realtime(
                "new_message",
                {
                    "session_id": doc.name,
                    "channel": doc.channel_type,
                    "contact_name": doc.contact_name,
                    "preview": (latest.content or "")[:100] if latest.message_type == "Text" else f"[{latest.message_type}]"
                },
                doctype=doc.reference_doctype,
                docname=doc.reference_name,
                after_commit=True
            )


def notify_new_message(doc, message):
    """
    Send notification for new incoming message
    """
    recipients = []
    
    # Notify assigned user
    if doc.assigned_to:
        recipients.append(doc.assigned_to)
    else:
        # Notify all users with Omni Channel Manager or Agent role
        recipients = frappe.get_all(
            "Has Role",
            filters={"role": ["in", ["Omni Channel Manager", "Omni Channel Agent"]]},
            fields=["parent"],
            distinct=True
        )
        recipients = [r.parent for r in recipients]
    
    # Create notification
    for user in recipients:
        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": f"New {doc.channel_type} message from {doc.contact_name or doc.contact_number}",
            "document_type": "AZ Conversation Session",
            "document_name": doc.name,
            "for_user": user,
            "type": "Alert",
            "email_content": message.content[:500] if message.content else f"[{message.message_type}]"
        }).insert(ignore_permissions=True)


def notify_assignment(doc):
    """
    Notify user when conversation is assigned to them
    """
    if doc.assigned_to:
        frappe.publish_realtime(
            "conversation_assigned",
            {
                "session_id": doc.name,
                "channel": doc.channel_type,
                "contact": doc.contact_name or doc.contact_number,
                "assigned_by": frappe.session.user
            },
            user=doc.assigned_to,
            after_commit=True
        )
        
        # Create notification
        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": f"Conversation assigned: {doc.contact_name or doc.contact_number}",
            "document_type": "AZ Conversation Session",
            "document_name": doc.name,
            "for_user": doc.assigned_to,
            "type": "Assignment"
        }).insert(ignore_permissions=True)


def handle_status_change(doc):
    """
    Handle conversation status changes
    """
    # Broadcast status change
    frappe.publish_realtime(
        "conversation_update",
        {
            "session_id": doc.name,
            "status": doc.status,
            "channel": doc.channel_type
        },
        doctype="AZ Conversation Session",
        docname=doc.name,
        after_commit=True
    )
    
    # If closed, log the closure
    if doc.status == "Closed":
        doc.add_comment(
            "Info",
            f"Conversation closed by {frappe.session.user}"
        )


def update_message_status(session_id, message_id, status, timestamp=None):
    """
    Update the status of a sent message
    
    Called when we receive status updates from WhatsApp/Telegram
    """
    session = frappe.get_doc("AZ Conversation Session", session_id)
    
    for msg in session.messages:
        if msg.message_id == message_id:
            msg.status = status
            if status == "Read" and timestamp:
                msg.read_at = timestamp
            break
    
    session.save(ignore_permissions=True)
    
    # Broadcast status update
    frappe.publish_realtime(
        "message_status",
        {
            "session_id": session_id,
            "message_id": message_id,
            "status": status
        },
        doctype="AZ Conversation Session",
        docname=session_id,
        after_commit=True
    )


def check_window_expiry():
    """
    Scheduled task to check for expired WhatsApp 24h windows
    
    Updates session status when window expires
    """
    expired_sessions = frappe.get_all(
        "AZ Conversation Session",
        filters={
            "channel_type": "WhatsApp",
            "status": "Active",
            "window_expires_at": ["<", now_datetime()]
        },
        fields=["name"]
    )
    
    for session in expired_sessions:
        doc = frappe.get_doc("AZ Conversation Session", session.name)
        doc.status = "Window Expired"
        doc.save(ignore_permissions=True)
        
        frappe.publish_realtime(
            "window_expired",
            {
                "session_id": doc.name,
                "contact": doc.contact_name or doc.contact_number
            },
            user=doc.assigned_to or doc.owner,
            after_commit=True
        )


def reopen_window(session_id, new_expiry):
    """
    Reopen a WhatsApp conversation window
    
    Called when customer sends a new message
    """
    session = frappe.get_doc("AZ Conversation Session", session_id)
    session.status = "Active"
    session.window_expires_at = new_expiry
    session.save(ignore_permissions=True)
    
    frappe.publish_realtime(
        "window_reopened",
        {
            "session_id": session_id,
            "expires_at": str(new_expiry)
        },
        doctype="AZ Conversation Session",
        docname=session_id,
        after_commit=True
    )
