# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class AZSMSMessage(Document):
    """
    AZ SMS Message DocType
    Records all SMS messages sent and received.
    """
    
    def before_save(self):
        """Calculate character and segment counts, resolve CRM contact."""
        self.calculate_message_stats()
        if not self.contact_name:
            self.resolve_crm_contact()
    
    def calculate_message_stats(self):
        """Calculate character count and segment count."""
        if self.message_content:
            self.character_count = len(self.message_content)
            
            # SMS segment calculation (160 chars for GSM, 70 for Unicode)
            if self.is_unicode():
                chars_per_segment = 70 if self.character_count <= 70 else 67
            else:
                chars_per_segment = 160 if self.character_count <= 160 else 153
            
            self.segment_count = max(1, -(-self.character_count // chars_per_segment))  # Ceiling division
    
    def is_unicode(self):
        """Check if message contains Unicode characters."""
        if not self.message_content:
            return False
        
        gsm_chars = set('@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ !"#¤%&\'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà')
        extended_gsm = set('^{}\\[~]|€')
        
        for char in self.message_content:
            if char not in gsm_chars and char not in extended_gsm:
                return True
        return False
    
    def resolve_crm_contact(self):
        """Resolve phone number to CRM contact."""
        if not self.phone_number:
            return
        
        # Clean phone number
        import re
        phone_clean = re.sub(r'[^\d]', '', self.phone_number)[-10:]
        
        # Search in configured DocTypes
        search_doctypes = ["Lead", "Customer", "Contact"]
        
        for doctype in search_doctypes:
            try:
                results = frappe.db.sql("""
                    SELECT name, 
                           COALESCE(lead_name, customer_name, first_name, name) as display_name
                    FROM `tab{doctype}`
                    WHERE REPLACE(REPLACE(REPLACE(COALESCE(mobile_no, phone, ''), '-', ''), ' ', ''), '+', '') LIKE %s
                    LIMIT 1
                """.format(doctype=doctype), (f"%{phone_clean}",), as_dict=True)
                
                if results:
                    self.party_type = doctype
                    self.party = results[0].name
                    self.contact_name = results[0].display_name
                    break
            except Exception:
                continue
    
    def send(self):
        """Send this SMS message."""
        from arrowz.arrowz.doctype.az_sms_provider.az_sms_provider import get_default_provider
        
        if self.direction != "Outbound":
            frappe.throw("Can only send outbound messages")
        
        provider = None
        if self.provider:
            provider = frappe.get_doc("AZ SMS Provider", self.provider)
        else:
            provider = get_default_provider()
        
        if not provider:
            frappe.throw("No SMS provider configured")
        
        self.provider = provider.name
        self.status = "Pending"
        self.sent_time = now_datetime()
        
        result = provider.send_sms(
            self.phone_number,
            self.message_content,
            self.media_url if self.has_media else None
        )
        
        if result.get("success"):
            self.status = "Sent"
            self.provider_message_id = result.get("message_sid") or result.get("message_id")
            self.delivery_status = "sent"
        else:
            self.status = "Failed"
            self.error_message = result.get("error")
            self.delivery_status = "failed"
        
        self.save(ignore_permissions=True)
        
        return result
    
    def update_delivery_status(self, status, error_code=None, error_message=None):
        """Update delivery status from webhook."""
        self.delivery_status = status
        
        if status == "delivered":
            self.status = "Delivered"
            self.delivered_time = now_datetime()
        elif status in ["failed", "undelivered"]:
            self.status = "Failed"
            self.error_code = error_code
            self.error_message = error_message
        
        self.save(ignore_permissions=True)
        
        # Emit real-time event
        frappe.publish_realtime(
            "sms_status_update",
            {
                "message": self.name,
                "status": self.status,
                "delivery_status": self.delivery_status
            }
        )


@frappe.whitelist()
def send_sms(to_number, message, provider=None, party_type=None, party=None, related_call=None):
    """Send an SMS message."""
    frappe.only_for(["AZ Manager", "System Manager"])

    doc = frappe.get_doc({
        "doctype": "AZ SMS Message",
        "direction": "Outbound",
        "phone_number": to_number,
        "message_content": message,
        "provider": provider,
        "party_type": party_type,
        "party": party,
        "related_call": related_call
    })
    doc.insert(ignore_permissions=True)
    
    return doc.send()


@frappe.whitelist()
def get_sms_history(phone_number=None, party_type=None, party=None, limit=20):
    """Get SMS history for a phone number or party."""
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    filters = {}
    
    if phone_number:
        filters["phone_number"] = ["like", f"%{phone_number[-10:]}"]
    
    if party_type and party:
        filters["party_type"] = party_type
        filters["party"] = party
    
    messages = frappe.get_all(
        "AZ SMS Message",
        filters=filters,
        fields=[
            "name", "direction", "status", "phone_number",
            "message_content", "sent_time", "contact_name",
            "delivery_status"
        ],
        order_by="sent_time desc",
        limit=limit
    )
    
    return messages
