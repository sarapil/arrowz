# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# License: MIT

"""
WhatsApp Integration Driver

Supports:
- WhatsApp Cloud API (Meta Business Platform)
- WhatsApp On-Premise API (deprecated)

Features:
- Text messages
- Media messages (images, videos, audio, documents)
- Template messages (for initiating conversations outside 24h window)
- Interactive messages (buttons, lists)
- Webhook verification and processing
"""

import frappe
from frappe import _
from typing import Dict, List, Optional, Any
import json
import hmac
import hashlib

from arrowz.integrations.base import BaseDriver


class WhatsAppCloudDriver(BaseDriver):
    """
    WhatsApp Cloud API Driver
    
    Uses Meta's Graph API for WhatsApp Business.
    """
    
    def _configure_auth(self):
        """Configure authentication headers for WhatsApp Cloud API"""
        if self.channel:
            access_token = self.channel.get_password("access_token")
            self.session.headers.update({
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            })
            self.phone_number_id = self.channel.phone_number_id
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection by fetching phone number info"""
        try:
            endpoint = f"{self.api_version}/{self.phone_number_id}"
            result = self._make_request("GET", endpoint)
            
            return {
                "status": "success",
                "message": f"Connected to {result.get('display_phone_number', 'Unknown')}",
                "details": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def send_text_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send a text message via WhatsApp"""
        recipient = self._normalize_phone_number(recipient)
        
        endpoint = f"{self.api_version}/{self.phone_number_id}/messages"
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": message
            }
        }
        
        result = self._make_request("POST", endpoint, data=data)
        
        message_id = result.get("messages", [{}])[0].get("id")
        
        # Log the message
        self.log_message("outbound", recipient, message, message_id)
        
        return {
            "message_id": message_id,
            "status": "sent",
            "details": result
        }
    
    def send_media_message(self, recipient: str, media_url: str, 
                          media_type: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """Send a media message via WhatsApp"""
        recipient = self._normalize_phone_number(recipient)
        
        endpoint = f"{self.api_version}/{self.phone_number_id}/messages"
        
        media_object = {"link": media_url}
        if caption:
            media_object["caption"] = caption
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": media_type,
            media_type: media_object
        }
        
        result = self._make_request("POST", endpoint, data=data)
        
        message_id = result.get("messages", [{}])[0].get("id")
        
        self.log_message("outbound", recipient, caption or f"[{media_type}]", message_id)
        
        return {
            "message_id": message_id,
            "status": "sent",
            "details": result
        }
    
    def send_template_message(self, recipient: str, template_name: str,
                             language_code: str = "en",
                             components: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Send a template message (for initiating conversations outside 24h window)
        
        Args:
            recipient: Phone number
            template_name: Name of the approved template
            language_code: Language code (e.g., 'en', 'ar')
            components: Template components (header, body, buttons with variables)
        """
        recipient = self._normalize_phone_number(recipient)
        
        endpoint = f"{self.api_version}/{self.phone_number_id}/messages"
        
        template_data = {
            "name": template_name,
            "language": {"code": language_code}
        }
        
        if components:
            template_data["components"] = components
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "template",
            "template": template_data
        }
        
        result = self._make_request("POST", endpoint, data=data)
        
        message_id = result.get("messages", [{}])[0].get("id")
        
        self.log_message("outbound", recipient, f"[Template: {template_name}]", message_id)
        
        return {
            "message_id": message_id,
            "status": "sent",
            "details": result
        }
    
    def send_interactive_message(self, recipient: str, interactive_type: str,
                                 body: str, buttons: Optional[List[Dict]] = None,
                                 sections: Optional[List[Dict]] = None,
                                 header: Optional[Dict] = None,
                                 footer: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an interactive message (buttons or list)
        
        Args:
            recipient: Phone number
            interactive_type: 'button' or 'list'
            body: Message body
            buttons: List of button objects (for button type)
            sections: List of section objects (for list type)
            header: Optional header object
            footer: Optional footer text
        """
        recipient = self._normalize_phone_number(recipient)
        
        endpoint = f"{self.api_version}/{self.phone_number_id}/messages"
        
        interactive = {
            "type": interactive_type,
            "body": {"text": body}
        }
        
        if header:
            interactive["header"] = header
        
        if footer:
            interactive["footer"] = {"text": footer}
        
        if interactive_type == "button" and buttons:
            interactive["action"] = {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": btn.get("id"),
                            "title": btn.get("title")
                        }
                    }
                    for btn in buttons[:3]  # Max 3 buttons
                ]
            }
        elif interactive_type == "list" and sections:
            interactive["action"] = {
                "button": "Select Option",
                "sections": sections
            }
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "interactive",
            "interactive": interactive
        }
        
        result = self._make_request("POST", endpoint, data=data)
        
        message_id = result.get("messages", [{}])[0].get("id")
        
        self.log_message("outbound", recipient, body, message_id)
        
        return {
            "message_id": message_id,
            "status": "sent",
            "details": result
        }
    
    def fetch_templates(self) -> List[Dict]:
        """Fetch approved message templates from WhatsApp Business"""
        if not self.channel or not self.channel.business_account_id:
            return []
        
        endpoint = f"{self.api_version}/{self.channel.business_account_id}/message_templates"
        
        result = self._make_request("GET", endpoint)
        
        templates = []
        for template in result.get("data", []):
            templates.append({
                "name": template.get("name"),
                "status": template.get("status"),
                "language": template.get("language"),
                "category": template.get("category"),
                "components": template.get("components", [])
            })
        
        return templates
    
    def get_media_url(self, media_id: str) -> str:
        """Get download URL for a media file"""
        endpoint = f"{self.api_version}/{media_id}"
        
        result = self._make_request("GET", endpoint)
        
        return result.get("url")
    
    def download_media(self, media_id: str) -> bytes:
        """Download media file from WhatsApp"""
        media_url = self.get_media_url(media_id)
        
        response = self.session.get(media_url, timeout=self.timeout)
        response.raise_for_status()
        
        return response.content
    
    def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a message as read"""
        endpoint = f"{self.api_version}/{self.phone_number_id}/messages"
        
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        result = self._make_request("POST", endpoint, data=data)
        
        return {"status": "success", "details": result}


class WhatsAppOnPremDriver(BaseDriver):
    """
    WhatsApp On-Premise API Driver (Deprecated)
    
    For legacy installations using the on-premise Docker-based API.
    """
    
    def _configure_auth(self):
        """Configure authentication for on-premise API"""
        if self.channel:
            api_key = self.channel.get_password("access_token")
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            })
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to on-premise API"""
        try:
            result = self._make_request("GET", "v1/health")
            
            return {
                "status": "success",
                "message": "Connected to on-premise API",
                "details": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def send_text_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Send text message via on-premise API"""
        recipient = self._normalize_phone_number(recipient)
        
        data = {
            "to": recipient,
            "type": "text",
            "text": {"body": message}
        }
        
        result = self._make_request("POST", "v1/messages", data=data)
        
        message_id = result.get("messages", [{}])[0].get("id")
        
        self.log_message("outbound", recipient, message, message_id)
        
        return {
            "message_id": message_id,
            "status": "sent",
            "details": result
        }
    
    def send_media_message(self, recipient: str, media_url: str, 
                          media_type: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """Send media message via on-premise API"""
        recipient = self._normalize_phone_number(recipient)
        
        media_object = {"link": media_url}
        if caption:
            media_object["caption"] = caption
        
        data = {
            "to": recipient,
            "type": media_type,
            media_type: media_object
        }
        
        result = self._make_request("POST", "v1/messages", data=data)
        
        message_id = result.get("messages", [{}])[0].get("id")
        
        self.log_message("outbound", recipient, caption or f"[{media_type}]", message_id)
        
        return {
            "message_id": message_id,
            "status": "sent",
            "details": result
        }


# Webhook Processing Functions

def verify_webhook(mode: str, token: str, challenge: str, channel: str) -> str:
    """
    Verify webhook subscription from Meta
    
    Args:
        mode: Should be 'subscribe'
        token: Verification token from Meta
        challenge: Challenge string to return
        channel: Channel name to verify against
        
    Returns:
        Challenge string if valid, raises error otherwise
    """
    channel_doc = frappe.get_doc("AZ Omni Channel", channel)
    
    if mode == "subscribe" and token == channel_doc.verify_token:
        return challenge
    
    frappe.throw(_("Webhook verification failed"))


def process_webhook(payload: Dict, channel: str) -> Dict:
    """
    Process incoming webhook from WhatsApp
    
    Args:
        payload: Webhook payload from Meta
        channel: Channel name
        
    Returns:
        Processing result
    """
    # Queue for background processing
    frappe.enqueue(
        "arrowz.integrations.whatsapp.process_whatsapp_message",
        payload=payload,
        channel=channel,
        queue="short"
    )
    
    return {"status": "queued"}


def process_whatsapp_message(payload: Dict, channel: str):
    """
    Background job to process WhatsApp webhook payload
    
    Handles:
    - Incoming messages
    - Message status updates
    - Errors
    """
    from arrowz.arrowz.doctype.az_conversation_session.az_conversation_session import get_or_create_session
    
    try:
        # Navigate to the actual message data
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        
        # Handle incoming messages
        messages = value.get("messages", [])
        for message in messages:
            process_incoming_message(message, value.get("contacts", []), channel)
        
        # Handle status updates
        statuses = value.get("statuses", [])
        for status in statuses:
            process_status_update(status)
        
        # Handle errors
        errors = value.get("errors", [])
        for error in errors:
            frappe.log_error(
                f"WhatsApp Error: {json.dumps(error)}",
                "WhatsApp Webhook Error"
            )
    
    except Exception as e:
        frappe.log_error(
            f"Failed to process WhatsApp webhook: {str(e)}\nPayload: {json.dumps(payload)}",
            "WhatsApp Webhook Processing Error"
        )


def process_incoming_message(message: Dict, contacts: List[Dict], channel: str):
    """Process a single incoming message"""
    from arrowz.arrowz.doctype.az_conversation_session.az_conversation_session import get_or_create_session
    
    sender = message.get("from")
    message_id = message.get("id")
    timestamp = message.get("timestamp")
    message_type = message.get("type")
    
    # Get sender name from contacts
    sender_name = "Unknown"
    for contact in contacts:
        if contact.get("wa_id") == sender:
            sender_name = contact.get("profile", {}).get("name", "Unknown")
            break
    
    # Extract message content
    content = ""
    media_url = None
    
    if message_type == "text":
        content = message.get("text", {}).get("body", "")
    elif message_type in ["image", "video", "audio", "document", "sticker"]:
        media_info = message.get(message_type, {})
        content = media_info.get("caption", f"[{message_type}]")
        media_url = media_info.get("id")  # Media ID, needs to be downloaded
    elif message_type == "location":
        loc = message.get("location", {})
        content = f"📍 Location: {loc.get('latitude')}, {loc.get('longitude')}"
    elif message_type == "contacts":
        content = f"📇 Contact shared"
    elif message_type == "interactive":
        interactive = message.get("interactive", {})
        if interactive.get("type") == "button_reply":
            content = interactive.get("button_reply", {}).get("title", "")
        elif interactive.get("type") == "list_reply":
            content = interactive.get("list_reply", {}).get("title", "")
    
    # Get or create session
    session = get_or_create_session(
        channel=channel,
        participant_id=sender,
        participant_name=sender_name,
        participant_phone=f"+{sender}"
    )
    
    # Add message to session
    session.add_message({
        "message_id": message_id,
        "direction": "inbound",
        "message_type": message_type,
        "content": content,
        "media_url": media_url,
        "timestamp": timestamp,
        "sender": sender_name
    })
    
    # Broadcast real-time notification
    frappe.publish_realtime(
        "arrowz_new_message",
        {
            "channel": channel,
            "session": session.name,
            "sender": sender_name,
            "content": content[:100],
            "message_type": message_type
        }
    )


def process_status_update(status: Dict):
    """Process message status update"""
    message_id = status.get("id")
    new_status = status.get("status")  # sent, delivered, read, failed
    recipient = status.get("recipient_id")
    timestamp = status.get("timestamp")
    
    # Update message status in database
    # This would update the AZ Conversation Message child table
    frappe.db.sql("""
        UPDATE `tabAZ Conversation Message`
        SET status = %s
        WHERE message_id = %s
    """, (new_status, message_id))
    
    frappe.db.commit()
