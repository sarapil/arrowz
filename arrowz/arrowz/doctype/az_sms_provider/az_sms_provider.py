# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, get_datetime
import requests
import json


class AZSMSProvider(Document):
    """
    AZ SMS Provider DocType
    Manages SMS provider configurations with provider-agnostic architecture.
    """
    
    def before_save(self):
        """Generate webhook URL and validate configuration."""
        self.generate_webhook_url()
        self.reset_daily_usage_if_needed()
    
    def validate(self):
        """Ensure only one default provider."""
        if self.is_default:
            frappe.db.sql("""
                UPDATE `tabAZ SMS Provider`
                SET is_default = 0
                WHERE name != %s
            """, (self.name,))
    
    def generate_webhook_url(self):
        """Generate the webhook URL for this provider."""
        site_url = frappe.utils.get_url()
        self.webhook_url = f"{site_url}/api/method/arrowz.api.sms.webhook/{self.name}"
    
    def reset_daily_usage_if_needed(self):
        """Reset daily usage counter if it's a new day."""
        if self.last_usage_reset != today():
            self.current_daily_usage = 0
            self.last_usage_reset = today()
    
    def can_send(self):
        """Check if provider can send (rate limits, daily limits)."""
        self.reset_daily_usage_if_needed()
        
        if self.daily_limit > 0 and self.current_daily_usage >= self.daily_limit:
            return False, "Daily limit reached"
        
        return True, None
    
    def increment_usage(self):
        """Increment usage counter after successful send."""
        frappe.db.set_value(
            "AZ SMS Provider", self.name,
            "current_daily_usage", self.current_daily_usage + 1
        )
    
    @frappe.whitelist()
    def test_connection(self):
        """Test the provider connection."""
        frappe.only_for(["System Manager"])

        try:
            if self.provider_type == "Twilio":
                return self._test_twilio()
            elif self.provider_type == "Vonage":
                return self._test_vonage()
            elif self.provider_type == "MessageBird":
                return self._test_messagebird()
            else:
                return self._test_generic()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _test_twilio(self):
        """Test Twilio connection."""
        from requests.auth import HTTPBasicAuth
        
        response = requests.get(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}.json",
            auth=HTTPBasicAuth(self.account_sid, self.get_password("auth_token"))
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "account_status": data.get("status"),
                "friendly_name": data.get("friendly_name")
            }
        return {"success": False, "error": f"HTTP {response.status_code}"}
    
    def _test_vonage(self):
        """Test Vonage connection."""
        response = requests.get(
            "https://rest.nexmo.com/account/get-balance",
            params={
                "api_key": self.get_password("api_key"),
                "api_secret": self.get_password("api_secret")
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "balance": data.get("value"),
                "auto_reload": data.get("autoReload")
            }
        return {"success": False, "error": f"HTTP {response.status_code}"}
    
    def _test_messagebird(self):
        """Test MessageBird connection."""
        response = requests.get(
            "https://rest.messagebird.com/balance",
            headers={"Authorization": f"AccessKey {self.get_password('api_key')}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "balance": data.get("amount"),
                "type": data.get("type")
            }
        return {"success": False, "error": f"HTTP {response.status_code}"}
    
    def _test_generic(self):
        """Generic connection test."""
        if not self.api_base_url:
            return {"success": False, "error": "API Base URL required for custom provider"}
        
        try:
            response = requests.get(self.api_base_url, timeout=10)
            return {"success": response.status_code < 500, "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_sms(self, to_number, message, media_url=None):
        """Send SMS using this provider."""
        can_send, reason = self.can_send()
        if not can_send:
            return {"success": False, "error": reason}
        
        try:
            if self.provider_type == "Twilio":
                result = self._send_twilio(to_number, message, media_url)
            elif self.provider_type == "Vonage":
                result = self._send_vonage(to_number, message)
            elif self.provider_type == "MessageBird":
                result = self._send_messagebird(to_number, message)
            else:
                result = self._send_generic(to_number, message)
            
            if result.get("success"):
                self.increment_usage()
            
            return result
        except Exception as e:
            frappe.log_error(str(e), "SMS Send Error")
            return {"success": False, "error": str(e)}
    
    def _send_twilio(self, to_number, message, media_url=None):
        """Send via Twilio."""
        from requests.auth import HTTPBasicAuth
        
        payload = {
            "From": self.sender_id,
            "To": to_number,
            "Body": message
        }
        
        if media_url:
            payload["MediaUrl"] = media_url
        
        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json",
            data=payload,
            auth=HTTPBasicAuth(self.account_sid, self.get_password("auth_token"))
        )
        
        if response.status_code == 201:
            data = response.json()
            return {"success": True, "message_sid": data.get("sid")}
        return {"success": False, "error": response.text}
    
    def _send_vonage(self, to_number, message):
        """Send via Vonage."""
        response = requests.post(
            "https://rest.nexmo.com/sms/json",
            json={
                "api_key": self.get_password("api_key"),
                "api_secret": self.get_password("api_secret"),
                "from": self.sender_id,
                "to": to_number,
                "text": message
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            messages = data.get("messages", [])
            if messages and messages[0].get("status") == "0":
                return {"success": True, "message_id": messages[0].get("message-id")}
            return {"success": False, "error": messages[0].get("error-text") if messages else "Unknown error"}
        return {"success": False, "error": response.text}
    
    def _send_messagebird(self, to_number, message):
        """Send via MessageBird."""
        response = requests.post(
            "https://rest.messagebird.com/messages",
            json={
                "originator": self.sender_id,
                "recipients": [to_number],
                "body": message
            },
            headers={"Authorization": f"AccessKey {self.get_password('api_key')}"}
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            return {"success": True, "message_id": data.get("id")}
        return {"success": False, "error": response.text}
    
    def _send_generic(self, to_number, message):
        """Send via generic/custom API."""
        if not self.api_base_url:
            return {"success": False, "error": "API Base URL required"}
        
        # Generic POST with standard fields
        response = requests.post(
            self.api_base_url,
            json={
                "to": to_number,
                "from": self.sender_id,
                "message": message
            },
            headers={
                "Authorization": f"Bearer {self.get_password('api_key')}",
                "Content-Type": "application/json"
            }
        )
        
        return {
            "success": response.status_code in [200, 201, 202],
            "status_code": response.status_code,
            "response": response.text[:500]
        }


def get_default_provider():
    """Get the default active SMS provider."""
    provider = frappe.db.get_value(
        "AZ SMS Provider",
        {"is_active": 1, "is_default": 1},
        "name"
    )
    
    if not provider:
        # Fallback to any active provider
        provider = frappe.db.get_value(
            "AZ SMS Provider",
            {"is_active": 1},
            "name"
        )
    
    if provider:
        return frappe.get_doc("AZ SMS Provider", provider)
    
    return None
