# Copyright (c) 2026, Arrowz Team
# License: MIT

"""
AZ Conversation Session - Chat Session Management

Unlike email threads, instant messaging uses "sessions" as the core concept.
This is especially important for platforms like WhatsApp that enforce
a 24-hour customer service window.

Key Features:
- Session lifecycle management (active, pending, resolved, expired)
- 24-hour window tracking for WhatsApp
- Assignment and routing
- Metrics tracking (response time, resolution time)
- Document linking (Lead, Customer, Contact, etc.)
"""

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime, add_to_date, time_diff_in_seconds


class AZConversationSession(Document):
    """Conversation Session Management"""
    
    def validate(self):
        """Validate session"""
        self.set_window_expiry()
        self.auto_link_contact()
        self.update_last_activity()
    
    def before_insert(self):
        """Before inserting new session"""
        self.session_start = now_datetime()
        self.last_activity = now_datetime()
        
        # Increment channel conversation count
        if self.channel:
            channel = frappe.get_doc("AZ Omni Channel", self.channel)
            channel.increment_conversation_count()
    
    def set_window_expiry(self):
        """Set 24-hour window expiry for WhatsApp"""
        if self.channel:
            channel = frappe.get_cached_doc("AZ Omni Channel", self.channel)
            provider = frappe.get_cached_doc("AZ Omni Provider", channel.provider)
            
            if provider.provider_type in ["WhatsApp Cloud API", "WhatsApp On-Premise"]:
                if not self.window_expires and self.last_activity:
                    self.window_expires = add_to_date(self.last_activity, hours=24)
                
                # Check if window is still active
                if self.window_expires:
                    self.is_window_active = now_datetime() < self.window_expires
    
    def auto_link_contact(self):
        """Automatically link to Contact/Lead based on phone number"""
        if self.participant_phone and not self.contact:
            # Try to find Contact
            contact = frappe.db.get_value(
                "Contact Phone",
                {"phone": self.participant_phone},
                "parent"
            )
            if contact:
                self.contact = contact
                
                # Get linked Customer/Lead from Contact
                links = frappe.get_all(
                    "Dynamic Link",
                    filters={"parent": contact, "parenttype": "Contact"},
                    fields=["link_doctype", "link_name"]
                )
                for link in links:
                    if link.link_doctype == "Customer":
                        self.customer = link.link_name
                    elif link.link_doctype == "Lead":
                        self.lead = link.link_name
        
        # If no contact found, try to find Lead
        if self.participant_phone and not self.lead and not self.contact:
            lead = frappe.db.get_value(
                "Lead",
                {"mobile_no": self.participant_phone},
                "name"
            )
            if lead:
                self.lead = lead
    
    def update_last_activity(self):
        """Update last activity timestamp"""
        self.last_activity = now_datetime()
        
        # Reset window expiry for WhatsApp on new message
        if self.channel:
            channel = frappe.get_cached_doc("AZ Omni Channel", self.channel)
            provider = frappe.get_cached_doc("AZ Omni Provider", channel.provider)
            
            if provider.provider_type in ["WhatsApp Cloud API", "WhatsApp On-Premise"]:
                self.window_expires = add_to_date(now_datetime(), hours=24)
                self.is_window_active = 1
    
    def add_message(self, message_data):
        """Add a message to the session"""
        message = self.append("messages", {
            "message_id": message_data.get("message_id"),
            "direction": message_data.get("direction", "inbound"),
            "message_type": message_data.get("message_type", "text"),
            "content": message_data.get("content"),
            "media_url": message_data.get("media_url"),
            "timestamp": message_data.get("timestamp") or now_datetime(),
            "status": message_data.get("status", "delivered"),
            "sender": message_data.get("sender")
        })
        
        # Update session metrics
        self.message_count = len(self.messages)
        self.last_message_preview = (message_data.get("content") or "")[:200]
        self.update_last_activity()
        
        # Update unread count for inbound messages
        if message_data.get("direction") == "inbound":
            self.unread_count = (self.unread_count or 0) + 1
        
        # Calculate first response time if this is first outbound message
        if message_data.get("direction") == "outbound" and not self.first_response_time:
            self.first_response_time = time_diff_in_seconds(
                now_datetime(), self.session_start
            ) / 60  # Convert to minutes
        
        self.save(ignore_permissions=True)
        
        # Broadcast real-time update
        self.broadcast_update(message_data)
        
        return message
    
    def broadcast_update(self, message_data=None):
        """Broadcast real-time update to connected clients"""
        event_data = {
            "session": self.name,
            "channel": self.channel,
            "participant_name": self.participant_name,
            "participant_phone": self.participant_phone,
            "status": self.status,
            "unread_count": self.unread_count,
            "last_message": self.last_message_preview,
            "message": message_data
        }
        
        # Broadcast to assigned user
        if self.assigned_to:
            frappe.publish_realtime(
                "arrowz_conversation_update",
                event_data,
                user=self.assigned_to
            )
        
        # Broadcast to channel listeners
        frappe.publish_realtime(
            f"arrowz_channel_{self.channel}",
            event_data
        )
    
    @frappe.whitelist()
    def mark_as_read(self):
        """Mark all messages as read"""
        self.unread_count = 0
        self.save(ignore_permissions=True)
        return {"status": "success"}
    
    @frappe.whitelist()
    def assign_to_user(self, user):
        """Assign session to a user"""
        self.assigned_to = user
        self.save(ignore_permissions=True)
        
        # Notify the assigned user
        frappe.publish_realtime(
            "arrowz_session_assigned",
            {
                "session": self.name,
                "participant_name": self.participant_name,
                "channel": self.channel
            },
            user=user
        )
        
        return {"status": "success", "assigned_to": user}
    
    @frappe.whitelist()
    def resolve(self):
        """Mark session as resolved"""
        self.status = "Resolved"
        self.session_end = now_datetime()
        
        if self.session_start:
            self.resolution_time = time_diff_in_seconds(
                now_datetime(), self.session_start
            ) / 60  # Convert to minutes
        
        self.save(ignore_permissions=True)
        
        return {"status": "success"}
    
    @frappe.whitelist()
    def escalate(self, level=None, reason=None):
        """Escalate the session"""
        self.status = "Escalated"
        self.escalation_level = (level or self.escalation_level + 1)
        self.priority = "Urgent"
        
        if reason:
            self.notes = f"{self.notes or ''}\n\nEscalated: {reason}"
        
        self.save(ignore_permissions=True)
        
        return {"status": "success", "escalation_level": self.escalation_level}
    
    @frappe.whitelist()
    def send_message(self, content, message_type="text", media_url=None):
        """Send a message through this session"""
        channel = frappe.get_doc("AZ Omni Channel", self.channel)
        driver = channel.get_driver()
        
        # Check if window is active for WhatsApp
        if not self.is_window_active:
            frappe.throw(_("24-hour window has expired. Please use a template message."))
        
        # Send via driver
        result = driver.send_message(
            recipient=self.participant_id,
            content=content,
            message_type=message_type,
            media_url=media_url
        )
        
        # Add message to session
        self.add_message({
            "message_id": result.get("message_id"),
            "direction": "outbound",
            "message_type": message_type,
            "content": content,
            "media_url": media_url,
            "sender": frappe.session.user,
            "status": "sent"
        })
        
        return result


@frappe.whitelist()
def get_or_create_session(channel, participant_id, participant_name=None, participant_phone=None):
    """Get existing active session or create new one"""
    # Check for existing active session
    existing = frappe.db.get_value(
        "AZ Conversation Session",
        {
            "channel": channel,
            "participant_id": participant_id,
            "status": ["in", ["Active", "Pending"]]
        },
        "name"
    )
    
    if existing:
        return frappe.get_doc("AZ Conversation Session", existing)
    
    # Create new session
    session = frappe.get_doc({
        "doctype": "AZ Conversation Session",
        "channel": channel,
        "participant_id": participant_id,
        "participant_name": participant_name,
        "participant_phone": participant_phone
    })
    session.insert(ignore_permissions=True)
    
    return session


@frappe.whitelist()
def get_sessions_for_user(user=None, status=None, channel=None, limit=50):
    """Get conversation sessions for a user"""
    filters = {}
    
    if user:
        filters["assigned_to"] = user
    
    if status:
        filters["status"] = status
    else:
        filters["status"] = ["in", ["Active", "Pending", "Escalated"]]
    
    if channel:
        filters["channel"] = channel
    
    sessions = frappe.get_all(
        "AZ Conversation Session",
        filters=filters,
        fields=[
            "name", "channel", "participant_name", "participant_phone",
            "status", "priority", "unread_count", "last_message_preview",
            "last_activity", "is_window_active", "contact", "customer", "lead"
        ],
        order_by="last_activity desc",
        limit=limit
    )
    
    # Add channel info
    for session in sessions:
        channel_info = frappe.db.get_value(
            "AZ Omni Channel",
            session.channel,
            ["channel_name", "provider"],
            as_dict=True
        )
        if channel_info:
            session["channel_name"] = channel_info.channel_name
            
            provider_info = frappe.db.get_value(
                "AZ Omni Provider",
                channel_info.provider,
                ["icon", "color", "provider_type"],
                as_dict=True
            )
            if provider_info:
                session["provider_icon"] = provider_info.icon
                session["provider_color"] = provider_info.color
                session["provider_type"] = provider_info.provider_type
    
    return sessions


@frappe.whitelist()
def check_expired_sessions():
    """Check and expire sessions with expired windows (scheduled task)"""
    expired_sessions = frappe.get_all(
        "AZ Conversation Session",
        filters={
            "status": ["in", ["Active", "Pending"]],
            "window_expires": ["<", now_datetime()],
            "is_window_active": 1
        }
    )
    
    for session in expired_sessions:
        frappe.db.set_value(
            "AZ Conversation Session",
            session.name,
            "is_window_active",
            0,
            update_modified=False
        )
    
    return len(expired_sessions)
