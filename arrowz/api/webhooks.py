# -*- coding: utf-8 -*-
# Copyright (c) 2024, Arrowz and contributors
# For license information, please see license.txt

"""
Webhook API Endpoints for Omni-Channel Platform

This module handles incoming webhooks from:
- WhatsApp Cloud API
- WhatsApp On-Premise API
- Telegram Bot API
- OpenMeetings callbacks

Strategy: "Ack-and-Queue" - Return 200 immediately, process in background
"""

import frappe
import json
import hmac
import hashlib
from frappe import _


# =============================================================================
# WhatsApp Cloud API Webhooks
# =============================================================================

@frappe.whitelist(allow_guest=True)
def whatsapp_cloud_webhook():
    """
    WhatsApp Cloud API Webhook Handler
    
    Handles:
    - Webhook verification (GET request)
    - Message notifications (POST request)
    - Status updates
    - Template callbacks
    """
    if frappe.request.method == "GET":
        return _verify_whatsapp_webhook()
    elif frappe.request.method == "POST":
        return _process_whatsapp_webhook()
    else:
        frappe.throw(_("Method not allowed"), frappe.MethodNotAllowedError)


def _verify_whatsapp_webhook():
    """Verify WhatsApp webhook subscription"""
    mode = frappe.request.args.get("hub.mode")
    token = frappe.request.args.get("hub.verify_token")
    challenge = frappe.request.args.get("hub.challenge")
    
    # Get the expected verify token from settings
    settings = frappe.get_cached_doc("AZ Omni Provider", {"provider_type": "WhatsApp Cloud"})
    expected_token = settings.get_password("verify_token") if settings else None
    
    if mode == "subscribe" and token == expected_token:
        frappe.response["http_status_code"] = 200
        frappe.response["message"] = challenge
        return challenge
    else:
        frappe.throw(_("Verification failed"), frappe.AuthenticationError)


def _process_whatsapp_webhook():
    """Process incoming WhatsApp messages"""
    # Immediately acknowledge receipt
    frappe.response["http_status_code"] = 200
    
    try:
        payload = json.loads(frappe.request.data)
        
        # Verify webhook signature if configured
        signature = frappe.request.headers.get("X-Hub-Signature-256")
        if signature:
            _verify_whatsapp_signature(frappe.request.data, signature)
        
        # Queue for background processing
        frappe.enqueue(
            "arrowz.integrations.whatsapp.process_webhook",
            queue="default",
            timeout=300,
            payload=payload
        )
        
        return {"status": "queued"}
        
    except Exception as e:
        frappe.log_error(
            title="WhatsApp Webhook Error",
            message=f"Error: {str(e)}\nPayload: {frappe.request.data}"
        )
        # Still return 200 to prevent retry storms
        return {"status": "error", "message": str(e)}


def _verify_whatsapp_signature(payload, signature):
    """Verify the webhook signature from Meta"""
    settings = frappe.get_cached_doc("AZ Omni Provider", {"provider_type": "WhatsApp Cloud"})
    app_secret = settings.get_password("app_secret") if settings else None
    
    if not app_secret:
        return  # Skip verification if no secret configured
    
    expected_signature = "sha256=" + hmac.new(
        app_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        frappe.throw(_("Invalid signature"), frappe.AuthenticationError)


# =============================================================================
# WhatsApp On-Premise Webhooks
# =============================================================================

@frappe.whitelist(allow_guest=True)
def whatsapp_onprem_webhook():
    """
    WhatsApp On-Premise API Webhook Handler
    
    Handles incoming messages from on-premise WhatsApp Business API
    """
    if frappe.request.method != "POST":
        frappe.throw(_("Method not allowed"), frappe.MethodNotAllowedError)
    
    # Immediately acknowledge
    frappe.response["http_status_code"] = 200
    
    try:
        payload = json.loads(frappe.request.data)
        
        # Verify authentication token
        auth_token = frappe.request.headers.get("Authorization", "").replace("Bearer ", "")
        _verify_onprem_token(auth_token)
        
        # Queue for processing
        frappe.enqueue(
            "arrowz.integrations.whatsapp.process_onprem_webhook",
            queue="default",
            timeout=300,
            payload=payload
        )
        
        return {"status": "queued"}
        
    except Exception as e:
        frappe.log_error(
            title="WhatsApp On-Prem Webhook Error",
            message=f"Error: {str(e)}\nPayload: {frappe.request.data}"
        )
        return {"status": "error", "message": str(e)}


def _verify_onprem_token(token):
    """Verify on-premise authentication token"""
    settings = frappe.get_cached_doc("AZ Omni Provider", {"provider_type": "WhatsApp On-Premise"})
    expected_token = settings.get_password("webhook_token") if settings else None
    
    if expected_token and not hmac.compare_digest(token, expected_token):
        frappe.throw(_("Invalid token"), frappe.AuthenticationError)


# =============================================================================
# Telegram Bot Webhooks
# =============================================================================

@frappe.whitelist(allow_guest=True)
def telegram_webhook():
    """
    Telegram Bot API Webhook Handler
    
    Handles:
    - Message updates
    - Callback queries
    - Inline queries
    - Chat member updates
    """
    if frappe.request.method != "POST":
        frappe.throw(_("Method not allowed"), frappe.MethodNotAllowedError)
    
    # Immediately acknowledge
    frappe.response["http_status_code"] = 200
    
    try:
        payload = json.loads(frappe.request.data)
        
        # Verify secret token if configured
        secret_token = frappe.request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret_token:
            _verify_telegram_secret(secret_token)
        
        # Queue for processing
        frappe.enqueue(
            "arrowz.integrations.telegram.process_webhook",
            queue="default",
            timeout=300,
            payload=payload
        )
        
        return {"status": "queued"}
        
    except Exception as e:
        frappe.log_error(
            title="Telegram Webhook Error",
            message=f"Error: {str(e)}\nPayload: {frappe.request.data}"
        )
        return {"status": "error", "message": str(e)}


def _verify_telegram_secret(token):
    """Verify Telegram secret token"""
    settings = frappe.get_cached_doc("AZ Omni Provider", {"provider_type": "Telegram"})
    expected_token = settings.get_password("webhook_secret") if settings else None
    
    if expected_token and not hmac.compare_digest(token, expected_token):
        frappe.throw(_("Invalid secret token"), frappe.AuthenticationError)


@frappe.whitelist(allow_guest=True)
def telegram_webhook_by_bot(bot_id):
    """
    Bot-specific webhook endpoint
    
    Allows multiple Telegram bots with different webhooks
    URL: /api/method/arrowz.api.webhooks.telegram_webhook_by_bot?bot_id=xxx
    """
    if frappe.request.method != "POST":
        frappe.throw(_("Method not allowed"), frappe.MethodNotAllowedError)
    
    frappe.response["http_status_code"] = 200
    
    try:
        payload = json.loads(frappe.request.data)
        payload["_bot_id"] = bot_id
        
        frappe.enqueue(
            "arrowz.integrations.telegram.process_webhook",
            queue="default",
            timeout=300,
            payload=payload
        )
        
        return {"status": "queued"}
        
    except Exception as e:
        frappe.log_error(
            title=f"Telegram Bot {bot_id} Webhook Error",
            message=f"Error: {str(e)}\nPayload: {frappe.request.data}"
        )
        return {"status": "error", "message": str(e)}


# =============================================================================
# OpenMeetings Callbacks
# =============================================================================

@frappe.whitelist(allow_guest=True)
def openmeetings_callback():
    """
    OpenMeetings Callback Handler
    
    Handles:
    - Room events (user joined, left)
    - Recording status updates
    - Meeting ended notifications
    """
    if frappe.request.method != "POST":
        frappe.throw(_("Method not allowed"), frappe.MethodNotAllowedError)
    
    frappe.response["http_status_code"] = 200
    
    try:
        payload = json.loads(frappe.request.data)
        
        # Verify callback signature
        signature = frappe.request.headers.get("X-OM-Signature")
        if signature:
            _verify_openmeetings_signature(frappe.request.data, signature)
        
        event_type = payload.get("type")
        
        if event_type == "user_joined":
            _handle_user_joined(payload)
        elif event_type == "user_left":
            _handle_user_left(payload)
        elif event_type == "recording_ready":
            _handle_recording_ready(payload)
        elif event_type == "room_closed":
            _handle_room_closed(payload)
        else:
            frappe.log_error(
                title="Unknown OpenMeetings Event",
                message=f"Type: {event_type}\nPayload: {json.dumps(payload)}"
            )
        
        return {"status": "processed"}
        
    except Exception as e:
        frappe.log_error(
            title="OpenMeetings Callback Error",
            message=f"Error: {str(e)}\nPayload: {frappe.request.data}"
        )
        return {"status": "error", "message": str(e)}


def _verify_openmeetings_signature(payload, signature):
    """Verify OpenMeetings callback signature"""
    settings = frappe.get_cached_doc("AZ Omni Provider", {"provider_type": "OpenMeetings"})
    secret = settings.get_password("callback_secret") if settings else None
    
    if not secret:
        return
    
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        frappe.throw(_("Invalid signature"), frappe.AuthenticationError)


def _handle_user_joined(payload):
    """Handle user joined event"""
    room_id = payload.get("room_id")
    user_id = payload.get("user_id")
    user_name = payload.get("user_name")
    
    # Find the meeting room
    room = frappe.get_all(
        "AZ Meeting Room",
        filters={"external_room_id": room_id},
        limit=1
    )
    
    if room:
        doc = frappe.get_doc("AZ Meeting Room", room[0].name)
        
        # Update participant attended status
        for p in doc.participants:
            if p.email == payload.get("email"):
                p.attended = 1
                break
        
        doc.save(ignore_permissions=True)
        
        # Broadcast to connected clients
        frappe.publish_realtime(
            "meeting_user_joined",
            {
                "room": doc.name,
                "user": user_name,
                "user_id": user_id
            },
            doctype="AZ Meeting Room",
            docname=doc.name
        )


def _handle_user_left(payload):
    """Handle user left event"""
    room_id = payload.get("room_id")
    user_name = payload.get("user_name")
    
    room = frappe.get_all(
        "AZ Meeting Room",
        filters={"external_room_id": room_id},
        limit=1
    )
    
    if room:
        frappe.publish_realtime(
            "meeting_user_left",
            {
                "room": room[0].name,
                "user": user_name
            },
            doctype="AZ Meeting Room",
            docname=room[0].name
        )


def _handle_recording_ready(payload):
    """Handle recording ready event"""
    room_id = payload.get("room_id")
    recording_id = payload.get("recording_id")
    recording_url = payload.get("recording_url")
    duration = payload.get("duration")
    file_size = payload.get("file_size")
    
    room = frappe.get_all(
        "AZ Meeting Room",
        filters={"external_room_id": room_id},
        limit=1
    )
    
    if room:
        doc = frappe.get_doc("AZ Meeting Room", room[0].name)
        doc.append("recordings", {
            "recording_name": f"Recording {len(doc.recordings) + 1}",
            "external_id": recording_id,
            "recording_url": recording_url,
            "duration": duration,
            "file_size": file_size,
            "recorded_on": frappe.utils.now_datetime()
        })
        doc.save(ignore_permissions=True)
        
        # Notify room owner
        frappe.publish_realtime(
            "recording_ready",
            {
                "room": doc.name,
                "recording_id": recording_id,
                "url": recording_url
            },
            user=doc.owner
        )


def _handle_room_closed(payload):
    """Handle room closed event"""
    room_id = payload.get("room_id")
    
    room = frappe.get_all(
        "AZ Meeting Room",
        filters={"external_room_id": room_id},
        limit=1
    )
    
    if room:
        doc = frappe.get_doc("AZ Meeting Room", room[0].name)
        doc.status = "Ended"
        doc.actual_end_time = frappe.utils.now_datetime()
        doc.save(ignore_permissions=True)
        
        frappe.publish_realtime(
            "meeting_ended",
            {"room": doc.name},
            doctype="AZ Meeting Room",
            docname=doc.name
        )


# =============================================================================
# Webhook Management Endpoints
# =============================================================================

@frappe.whitelist()
def setup_webhooks():
    """
    Setup all webhook URLs for enabled providers
    
    Returns the webhook URLs to be configured in each provider's dashboard
    """
    frappe.only_for(["System Manager", "Omni Channel Manager"])
    
    site_url = frappe.utils.get_url()
    
    webhooks = {
        "whatsapp_cloud": {
            "url": f"{site_url}/api/method/arrowz.api.webhooks.whatsapp_cloud_webhook",
            "description": "Configure this URL in Meta Developer Console > WhatsApp > Configuration > Webhook"
        },
        "whatsapp_onprem": {
            "url": f"{site_url}/api/method/arrowz.api.webhooks.whatsapp_onprem_webhook",
            "description": "Configure this URL in your WhatsApp Business API container"
        },
        "telegram": {
            "url": f"{site_url}/api/method/arrowz.api.webhooks.telegram_webhook",
            "description": "Use this URL with Telegram Bot API setWebhook method"
        },
        "openmeetings": {
            "url": f"{site_url}/api/method/arrowz.api.webhooks.openmeetings_callback",
            "description": "Configure this URL in OpenMeetings Admin > Configuration > Callback URL"
        }
    }
    
    return webhooks


@frappe.whitelist()
def register_telegram_webhook(bot_token, bot_id=None):
    """
    Register webhook URL with Telegram Bot API
    
    Args:
        bot_token: Telegram bot token
        bot_id: Optional bot identifier for multi-bot setup
    """
    import requests
    
    site_url = frappe.utils.get_url()
    
    if bot_id:
        webhook_url = f"{site_url}/api/method/arrowz.api.webhooks.telegram_webhook_by_bot?bot_id={bot_id}"
    else:
        webhook_url = f"{site_url}/api/method/arrowz.api.webhooks.telegram_webhook"
    
    # Get secret token from provider settings
    settings = frappe.get_cached_doc("AZ Omni Provider", {"provider_type": "Telegram"})
    secret_token = settings.get_password("webhook_secret") if settings else None
    
    params = {
        "url": webhook_url,
        "allowed_updates": json.dumps(["message", "callback_query", "inline_query", "chat_member"])
    }
    
    if secret_token:
        params["secret_token"] = secret_token
    
    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/setWebhook",
        data=params
    )
    
    result = response.json()
    
    if result.get("ok"):
        return {
            "status": "success",
            "message": "Webhook registered successfully",
            "webhook_url": webhook_url
        }
    else:
        frappe.throw(f"Failed to register webhook: {result.get('description')}")


@frappe.whitelist()
def get_webhook_status():
    """
    Get the status of all configured webhooks
    """
    frappe.only_for(["System Manager", "Omni Channel Manager"])
    
    status = {}
    
    # Check WhatsApp Cloud
    try:
        provider = frappe.get_all(
            "AZ Omni Provider",
            filters={"provider_type": "WhatsApp Cloud", "enabled": 1},
            limit=1
        )
        status["whatsapp_cloud"] = {
            "configured": bool(provider),
            "enabled": bool(provider)
        }
    except Exception as e:
        status["whatsapp_cloud"] = {"error": str(e)}
    
    # Check Telegram
    try:
        provider = frappe.get_all(
            "AZ Omni Provider",
            filters={"provider_type": "Telegram", "enabled": 1},
            limit=1
        )
        status["telegram"] = {
            "configured": bool(provider),
            "enabled": bool(provider)
        }
    except Exception as e:
        status["telegram"] = {"error": str(e)}
    
    # Check OpenMeetings
    try:
        provider = frappe.get_all(
            "AZ Omni Provider",
            filters={"provider_type": "OpenMeetings", "enabled": 1},
            limit=1
        )
        status["openmeetings"] = {
            "configured": bool(provider),
            "enabled": bool(provider)
        }
    except Exception as e:
        status["openmeetings"] = {"error": str(e)}
    
    return status
