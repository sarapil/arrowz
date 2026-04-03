# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

"""
Arrowz SMS API
Handles SMS sending, receiving, and webhook processing.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def send_sms(to_number, message, provider=None, party_type=None, party=None, related_call=None):
    """
    Send an SMS message.
    
    Args:
        to_number: The recipient phone number
        message: The message content
        provider: Optional specific provider to use
        party_type: Optional CRM party type (Lead, Customer, etc.)
        party: Optional CRM party name
        related_call: Optional related call log
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    from arrowz.arrowz.doctype.az_sms_message.az_sms_message import send_sms as _send_sms
    return _send_sms(to_number, message, provider, party_type, party, related_call)


@frappe.whitelist()
def get_sms_history(phone_number=None, party_type=None, party=None, limit=20):
    """
    Get SMS history for a phone number or party.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    from arrowz.arrowz.doctype.az_sms_message.az_sms_message import get_sms_history as _get_history
    return _get_history(phone_number, party_type, party, limit)


@frappe.whitelist(allow_guest=True)
def webhook(provider):
    """
    Webhook endpoint for SMS delivery reports and incoming messages.
    
    Args:
        provider: The provider name (from URL path)
    """
    # Verify provider exists
    if not frappe.db.exists("AZ SMS Provider", provider):
        frappe.throw(_("Unknown provider"), frappe.AuthenticationError)
    
    provider_doc = frappe.get_doc("AZ SMS Provider", provider)
    
    # Get webhook data
    data = frappe.request.get_json() or frappe.request.form.to_dict()
    
    if not data:
        return {"status": "no_data"}
    
    # Process based on provider type
    if provider_doc.provider_type == "Twilio":
        return _process_twilio_webhook(data)
    elif provider_doc.provider_type == "Vonage":
        return _process_vonage_webhook(data)
    elif provider_doc.provider_type == "MessageBird":
        return _process_messagebird_webhook(data)
    else:
        return _process_generic_webhook(data, provider)


def _process_twilio_webhook(data):
    """Process Twilio webhook data."""
    message_sid = data.get("MessageSid")
    status = data.get("MessageStatus") or data.get("SmsStatus")
    
    if message_sid:
        # Find message by provider ID
        message = frappe.db.get_value(
            "AZ SMS Message",
            {"provider_message_id": message_sid},
            "name"
        )
        
        if message:
            doc = frappe.get_doc("AZ SMS Message", message)
            
            if status:
                doc.update_delivery_status(
                    status,
                    data.get("ErrorCode"),
                    data.get("ErrorMessage")
                )
            
            return {"status": "processed"}
    
    # Check for incoming message
    from_number = data.get("From")
    body = data.get("Body")
    
    if from_number and body:
        # Create inbound message
        doc = frappe.get_doc({
            "doctype": "AZ SMS Message",
            "direction": "Inbound",
            "phone_number": from_number,
            "message_content": body,
            "status": "Received",
            "sent_time": now_datetime(),
            "provider_message_id": message_sid
        })
        doc.insert(ignore_permissions=True)
        
        # Emit real-time event
        frappe.publish_realtime(
            "sms_received",
            {
                "message": doc.name,
                "from": from_number,
                "content": body[:100]
            }
        )
        
        return {"status": "received"}
    
    return {"status": "ignored"}


def _process_vonage_webhook(data):
    """Process Vonage webhook data."""
    message_id = data.get("messageId") or data.get("message-id")
    status = data.get("status")
    
    if message_id and status:
        message = frappe.db.get_value(
            "AZ SMS Message",
            {"provider_message_id": message_id},
            "name"
        )
        
        if message:
            doc = frappe.get_doc("AZ SMS Message", message)
            doc.update_delivery_status(
                status,
                data.get("err-code"),
                data.get("error-text")
            )
            return {"status": "processed"}
    
    # Incoming message
    from_number = data.get("msisdn")
    body = data.get("text")
    
    if from_number and body:
        doc = frappe.get_doc({
            "doctype": "AZ SMS Message",
            "direction": "Inbound",
            "phone_number": from_number,
            "message_content": body,
            "status": "Received",
            "sent_time": now_datetime(),
            "provider_message_id": message_id
        })
        doc.insert(ignore_permissions=True)
        
        frappe.publish_realtime(
            "sms_received",
            {"message": doc.name, "from": from_number}
        )
        
        return {"status": "received"}
    
    return {"status": "ignored"}


def _process_messagebird_webhook(data):
    """Process MessageBird webhook data."""
    message_id = data.get("id")
    status = data.get("status")
    
    if message_id and status:
        message = frappe.db.get_value(
            "AZ SMS Message",
            {"provider_message_id": message_id},
            "name"
        )
        
        if message:
            doc = frappe.get_doc("AZ SMS Message", message)
            doc.update_delivery_status(status)
            return {"status": "processed"}
    
    return {"status": "ignored"}


def _process_generic_webhook(data, provider):
    """Process generic webhook data."""
    # Log for debugging
    frappe.log_error(
        f"SMS Webhook from {provider}: {data}",
        "SMS Webhook"
    )
    
    return {"status": "logged"}


@frappe.whitelist()
def get_sms_statistics(from_date=None, to_date=None):
    """
    Get SMS statistics for a date range.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    from frappe.utils import today
    
    if not from_date:
        from_date = today()
    if not to_date:
        to_date = today()
    
    # Total messages
    total = frappe.db.count(
        "AZ SMS Message",
        filters={"sent_time": ["between", [from_date, to_date]]}
    )
    
    # By direction
    outbound = frappe.db.count(
        "AZ SMS Message",
        filters={
            "sent_time": ["between", [from_date, to_date]],
            "direction": "Outbound"
        }
    )
    
    inbound = frappe.db.count(
        "AZ SMS Message",
        filters={
            "sent_time": ["between", [from_date, to_date]],
            "direction": "Inbound"
        }
    )
    
    # Delivery stats
    delivered = frappe.db.count(
        "AZ SMS Message",
        filters={
            "sent_time": ["between", [from_date, to_date]],
            "status": "Delivered"
        }
    )
    
    failed = frappe.db.count(
        "AZ SMS Message",
        filters={
            "sent_time": ["between", [from_date, to_date]],
            "status": "Failed"
        }
    )
    
    return {
        "total": total,
        "outbound": outbound,
        "inbound": inbound,
        "delivered": delivered,
        "failed": failed,
        "delivery_rate": round((delivered / outbound * 100) if outbound > 0 else 0, 1)
    }
