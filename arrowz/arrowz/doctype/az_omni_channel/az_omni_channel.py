# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# License: MIT

"""
AZ Omni Channel - Communication Channel Configuration

Each channel represents a specific communication endpoint:
- A WhatsApp Business number
- A Telegram bot
- An SMS sender ID
- etc.

Channels handle:
- Credential storage (encrypted)
- Message routing rules
- Working hours configuration
- Automation settings
- Statistics tracking
"""

import frappe
from frappe.model.document import Document
from frappe import _
import hashlib
import hmac


class AZOmniChannel(Document):
    """Omni-Channel Communication Channel"""
    
    def validate(self):
        """Validate channel configuration"""
        self.validate_credentials()
        self.generate_verify_token()
    
    def validate_credentials(self):
        """Validate required credentials based on provider type"""
        if not self.provider:
            return
        
        provider = frappe.get_doc("AZ Omni Provider", self.provider)
        
        # WhatsApp requires specific credentials
        if provider.provider_type in ["WhatsApp Cloud API", "WhatsApp On-Premise"]:
            if not self.phone_number_id:
                frappe.throw(_("Phone Number ID is required for WhatsApp"))
            if not self.access_token:
                frappe.throw(_("Access Token is required for WhatsApp"))
        
        # Telegram requires bot token
        elif provider.provider_type == "Telegram Bot":
            if not self.access_token:
                frappe.throw(_("Bot Token is required for Telegram"))
    
    def generate_verify_token(self):
        """Generate a unique verify token for webhook verification"""
        if not self.verify_token:
            import secrets
            self.verify_token = secrets.token_urlsafe(32)
    
    def get_provider(self):
        """Get the parent provider document"""
        return frappe.get_doc("AZ Omni Provider", self.provider)
    
    def get_driver(self):
        """Get the driver instance with channel credentials"""
        provider = self.get_provider()
        driver = provider.get_driver()
        driver.set_channel(self)
        return driver
    
    def verify_webhook_signature(self, payload, signature):
        """Verify webhook signature from provider"""
        provider = self.get_provider()
        
        if not provider.verify_signature:
            return True
        
        secret = self.get_password("app_secret")
        if not secret:
            frappe.log_error("No app secret configured for webhook verification", "Webhook Error")
            return False
        
        if provider.provider_type in ["WhatsApp Cloud API", "Facebook Messenger", "Instagram Direct"]:
            # Meta uses HMAC-SHA256
            expected_signature = "sha256=" + hmac.new(
                secret.encode(),
                payload.encode() if isinstance(payload, str) else payload,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected_signature)
        
        elif provider.provider_type == "Telegram Bot":
            # Telegram uses secret_token header
            return hmac.compare_digest(signature, secret)
        
        return True
    
    def increment_conversation_count(self):
        """Increment total conversation count"""
        frappe.db.set_value(
            self.doctype, self.name,
            "total_conversations",
            self.total_conversations + 1,
            update_modified=False
        )
    
    def update_active_conversations(self, count):
        """Update active conversation count"""
        frappe.db.set_value(
            self.doctype, self.name,
            "active_conversations",
            count,
            update_modified=False
        )
    
    @frappe.whitelist()
    def sync_templates(self):
        """Sync message templates from provider"""
        frappe.only_for(["AZ Manager", "System Manager"])

        try:
            driver = self.get_driver()
            templates = driver.fetch_templates()
            return {
                "status": "success",
                "templates_synced": len(templates),
                "templates": templates
            }
        except Exception as e:
            frappe.log_error(f"Template sync failed: {str(e)}", "Template Sync Error")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @frappe.whitelist()
    def test_send_message(self, recipient, message):
        """Send a test message"""
        frappe.only_for(["AZ Manager", "System Manager"])

        try:
            driver = self.get_driver()
            result = driver.send_text_message(recipient, message)
            return {
                "status": "success",
                "message_id": result.get("message_id"),
                "details": result
            }
        except Exception as e:
            frappe.log_error(f"Test message failed: {str(e)}", "Test Message Error")
            return {
                "status": "error",
                "message": str(e)
            }


@frappe.whitelist()
def get_channels_by_provider(provider_type):
    """Get all active channels for a provider type"""
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    channels = frappe.db.sql("""
        SELECT c.name, c.channel_name, c.phone_number_id, c.channel_type, p.icon, p.color
        FROM `tabAZ Omni Channel` c
        JOIN `tabAZ Omni Provider` p ON c.provider = p.name
        WHERE p.provider_type = %s AND c.is_active = 1
        ORDER BY c.channel_name
    """, provider_type, as_dict=True)
    
    return channels


@frappe.whitelist()
def get_channel_statistics(channel_name):
    """Get detailed statistics for a channel"""
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    channel = frappe.get_doc("AZ Omni Channel", channel_name)
    
    # Get conversation statistics
    today = frappe.utils.today()
    
    stats = {
        "total_conversations": channel.total_conversations,
        "active_conversations": channel.active_conversations,
        "avg_response_time": channel.avg_response_time,
        "satisfaction_score": channel.satisfaction_score,
        "today_conversations": frappe.db.count(
            "AZ Conversation Session",
            filters={
                "channel": channel_name,
                "creation": [">=", today]
            }
        )
    }
    
    return stats
