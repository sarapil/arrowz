# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# License: MIT

"""
Telegram Integration Driver

Integrates with Telegram Bot API for:
- Sending and receiving messages
- Media handling (up to 2GB files)
- Inline keyboards and interactive buttons
- Bot commands
- Webhook management

Also integrates with frappe_telegram app if installed.
"""

import frappe
from frappe import _
from typing import Dict, List, Optional, Any
import json

from arrowz.integrations.base import BaseDriver


class TelegramDriver(BaseDriver):
    """
    Telegram Bot API Driver
    
    Uses Telegram's Bot API for messaging.
    """
    
    def __init__(self, provider):
        super().__init__(provider)
        self.bot_token = None
    
    def _configure_auth(self):
        """Configure bot token for API calls"""
        if self.channel:
            self.bot_token = self.channel.get_password("access_token")
            self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection by getting bot info"""
        try:
            result = self._make_request("GET", "getMe")
            
            if result.get("ok"):
                bot_info = result.get("result", {})
                return {
                    "status": "success",
                    "message": f"Connected to @{bot_info.get('username')}",
                    "details": bot_info
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("description", "Unknown error")
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def send_text_message(self, recipient: str, message: str,
                         parse_mode: str = "HTML",
                         reply_markup: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Send a text message via Telegram
        
        Args:
            recipient: Chat ID
            message: Message text
            parse_mode: 'HTML' or 'Markdown'
            reply_markup: Inline keyboard or reply keyboard
        """
        data = {
            "chat_id": recipient,
            "text": message,
            "parse_mode": parse_mode
        }
        
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        result = self._make_request("POST", "sendMessage", data=data)
        
        if result.get("ok"):
            msg_result = result.get("result", {})
            message_id = str(msg_result.get("message_id"))
            
            self.log_message("outbound", recipient, message, message_id)
            
            return {
                "message_id": message_id,
                "status": "sent",
                "details": msg_result
            }
        else:
            frappe.throw(_("Failed to send message: {0}").format(result.get("description")))
    
    def send_media_message(self, recipient: str, media_url: str, 
                          media_type: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a media message via Telegram
        
        Args:
            recipient: Chat ID
            media_url: URL or file_id of the media
            media_type: 'photo', 'video', 'audio', 'document', 'voice', 'animation'
            caption: Optional caption
        """
        method_map = {
            "image": "sendPhoto",
            "photo": "sendPhoto",
            "video": "sendVideo",
            "audio": "sendAudio",
            "document": "sendDocument",
            "voice": "sendVoice",
            "animation": "sendAnimation"
        }
        
        method = method_map.get(media_type, "sendDocument")
        
        param_map = {
            "sendPhoto": "photo",
            "sendVideo": "video",
            "sendAudio": "audio",
            "sendDocument": "document",
            "sendVoice": "voice",
            "sendAnimation": "animation"
        }
        
        param = param_map.get(method, "document")
        
        data = {
            "chat_id": recipient,
            param: media_url
        }
        
        if caption:
            data["caption"] = caption
            data["parse_mode"] = "HTML"
        
        result = self._make_request("POST", method, data=data)
        
        if result.get("ok"):
            msg_result = result.get("result", {})
            message_id = str(msg_result.get("message_id"))
            
            self.log_message("outbound", recipient, caption or f"[{media_type}]", message_id)
            
            return {
                "message_id": message_id,
                "status": "sent",
                "details": msg_result
            }
        else:
            frappe.throw(_("Failed to send media: {0}").format(result.get("description")))
    
    def send_inline_keyboard(self, recipient: str, message: str,
                            buttons: List[List[Dict]]) -> Dict[str, Any]:
        """
        Send a message with inline keyboard buttons
        
        Args:
            recipient: Chat ID
            message: Message text
            buttons: 2D array of button objects, e.g.:
                [[{"text": "Yes", "callback_data": "yes"}],
                 [{"text": "No", "callback_data": "no"}]]
        """
        reply_markup = {
            "inline_keyboard": buttons
        }
        
        return self.send_text_message(recipient, message, reply_markup=reply_markup)
    
    def send_contact_card(self, recipient: str, phone_number: str,
                         first_name: str, last_name: str = "") -> Dict[str, Any]:
        """Send a contact card"""
        data = {
            "chat_id": recipient,
            "phone_number": phone_number,
            "first_name": first_name,
            "last_name": last_name
        }
        
        result = self._make_request("POST", "sendContact", data=data)
        
        if result.get("ok"):
            return {
                "message_id": str(result.get("result", {}).get("message_id")),
                "status": "sent"
            }
        else:
            frappe.throw(_("Failed to send contact: {0}").format(result.get("description")))
    
    def send_location(self, recipient: str, latitude: float, 
                     longitude: float) -> Dict[str, Any]:
        """Send a location"""
        data = {
            "chat_id": recipient,
            "latitude": latitude,
            "longitude": longitude
        }
        
        result = self._make_request("POST", "sendLocation", data=data)
        
        if result.get("ok"):
            return {
                "message_id": str(result.get("result", {}).get("message_id")),
                "status": "sent"
            }
        else:
            frappe.throw(_("Failed to send location: {0}").format(result.get("description")))
    
    def answer_callback_query(self, callback_query_id: str, 
                             text: Optional[str] = None,
                             show_alert: bool = False) -> Dict[str, Any]:
        """Answer an inline keyboard button click"""
        data = {
            "callback_query_id": callback_query_id,
            "show_alert": show_alert
        }
        
        if text:
            data["text"] = text
        
        result = self._make_request("POST", "answerCallbackQuery", data=data)
        
        return {"status": "success" if result.get("ok") else "error"}
    
    def edit_message_text(self, chat_id: str, message_id: str,
                         new_text: str, reply_markup: Optional[Dict] = None) -> Dict[str, Any]:
        """Edit an existing message"""
        data = {
            "chat_id": chat_id,
            "message_id": int(message_id),
            "text": new_text,
            "parse_mode": "HTML"
        }
        
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        result = self._make_request("POST", "editMessageText", data=data)
        
        return {"status": "success" if result.get("ok") else "error"}
    
    def delete_message(self, chat_id: str, message_id: str) -> Dict[str, Any]:
        """Delete a message"""
        data = {
            "chat_id": chat_id,
            "message_id": int(message_id)
        }
        
        result = self._make_request("POST", "deleteMessage", data=data)
        
        return {"status": "success" if result.get("ok") else "error"}
    
    def get_file(self, file_id: str) -> Dict[str, Any]:
        """Get file info for downloading"""
        data = {"file_id": file_id}
        
        result = self._make_request("POST", "getFile", data=data)
        
        if result.get("ok"):
            file_info = result.get("result", {})
            file_path = file_info.get("file_path")
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            
            return {
                "file_id": file_id,
                "file_path": file_path,
                "file_size": file_info.get("file_size"),
                "download_url": download_url
            }
        else:
            frappe.throw(_("Failed to get file: {0}").format(result.get("description")))
    
    def set_webhook(self, url: str, secret_token: Optional[str] = None) -> Dict[str, Any]:
        """Set webhook URL for receiving updates"""
        data = {
            "url": url,
            "allowed_updates": ["message", "callback_query", "inline_query"]
        }
        
        if secret_token:
            data["secret_token"] = secret_token
        
        result = self._make_request("POST", "setWebhook", data=data)
        
        return {
            "status": "success" if result.get("ok") else "error",
            "message": result.get("description")
        }
    
    def delete_webhook(self) -> Dict[str, Any]:
        """Delete the webhook"""
        result = self._make_request("POST", "deleteWebhook")
        
        return {
            "status": "success" if result.get("ok") else "error"
        }
    
    def get_webhook_info(self) -> Dict[str, Any]:
        """Get current webhook info"""
        result = self._make_request("GET", "getWebhookInfo")
        
        if result.get("ok"):
            return result.get("result", {})
        else:
            return {"error": result.get("description")}


# Webhook Processing Functions

def process_telegram_webhook(payload: Dict, channel: str) -> Dict:
    """
    Process incoming webhook from Telegram
    
    Args:
        payload: Update object from Telegram
        channel: Channel name
        
    Returns:
        Processing result
    """
    # Queue for background processing
    frappe.enqueue(
        "arrowz.integrations.telegram.process_telegram_update",
        payload=payload,
        channel=channel,
        queue="short"
    )
    
    return {"status": "queued"}


def process_telegram_update(payload: Dict, channel: str):
    """
    Background job to process Telegram update
    
    Handles:
    - Messages (text, media, etc.)
    - Callback queries (button clicks)
    - Inline queries
    """
    from arrowz.arrowz.doctype.az_conversation_session.az_conversation_session import get_or_create_session
    
    try:
        # Handle regular messages
        if "message" in payload:
            process_telegram_message(payload["message"], channel)
        
        # Handle edited messages
        elif "edited_message" in payload:
            process_telegram_message(payload["edited_message"], channel, is_edit=True)
        
        # Handle callback queries (button clicks)
        elif "callback_query" in payload:
            process_callback_query(payload["callback_query"], channel)
        
        # Handle channel posts
        elif "channel_post" in payload:
            process_telegram_message(payload["channel_post"], channel, is_channel=True)
    
    except Exception as e:
        frappe.log_error(
            f"Failed to process Telegram update: {str(e)}\nPayload: {json.dumps(payload)}",
            "Telegram Webhook Processing Error"
        )


def process_telegram_message(message: Dict, channel: str, 
                            is_edit: bool = False, is_channel: bool = False):
    """Process a Telegram message"""
    from arrowz.arrowz.doctype.az_conversation_session.az_conversation_session import get_or_create_session
    
    chat = message.get("chat", {})
    chat_id = str(chat.get("id"))
    message_id = str(message.get("message_id"))
    
    # Get sender info
    sender = message.get("from", {})
    sender_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip()
    sender_username = sender.get("username", "")
    
    # Extract message content
    content = ""
    message_type = "text"
    media_url = None
    
    if "text" in message:
        content = message.get("text", "")
    elif "photo" in message:
        message_type = "image"
        photos = message.get("photo", [])
        if photos:
            media_url = photos[-1].get("file_id")  # Get highest resolution
        content = message.get("caption", "[Photo]")
    elif "video" in message:
        message_type = "video"
        media_url = message.get("video", {}).get("file_id")
        content = message.get("caption", "[Video]")
    elif "audio" in message:
        message_type = "audio"
        media_url = message.get("audio", {}).get("file_id")
        content = message.get("caption", "[Audio]")
    elif "document" in message:
        message_type = "document"
        media_url = message.get("document", {}).get("file_id")
        content = message.get("caption", f"[Document: {message.get('document', {}).get('file_name', 'file')}]")
    elif "voice" in message:
        message_type = "audio"
        media_url = message.get("voice", {}).get("file_id")
        content = "[Voice Message]"
    elif "sticker" in message:
        message_type = "sticker"
        media_url = message.get("sticker", {}).get("file_id")
        content = f"[Sticker: {message.get('sticker', {}).get('emoji', '')}]"
    elif "location" in message:
        message_type = "location"
        loc = message.get("location", {})
        content = f"📍 Location: {loc.get('latitude')}, {loc.get('longitude')}"
    elif "contact" in message:
        message_type = "contact"
        contact = message.get("contact", {})
        content = f"📇 Contact: {contact.get('first_name', '')} {contact.get('phone_number', '')}"
    
    # Handle bot commands
    if content.startswith("/"):
        handle_bot_command(content, chat_id, sender, channel)
        return
    
    # Get or create session
    session = get_or_create_session(
        channel=channel,
        participant_id=chat_id,
        participant_name=sender_name or sender_username,
        participant_phone=None  # Telegram doesn't share phone by default
    )
    
    # Add message to session
    session.add_message({
        "message_id": message_id,
        "direction": "inbound",
        "message_type": message_type,
        "content": content,
        "media_url": media_url,
        "timestamp": message.get("date"),
        "sender": sender_name or sender_username
    })
    
    # Broadcast real-time notification
    frappe.publish_realtime(
        "arrowz_new_message",
        {
            "channel": channel,
            "session": session.name,
            "sender": sender_name or sender_username,
            "content": content[:100],
            "message_type": message_type,
            "platform": "Telegram"
        }
    )


def process_callback_query(callback_query: Dict, channel: str):
    """Process a callback query (inline button click)"""
    query_id = callback_query.get("id")
    data = callback_query.get("data", "")
    message = callback_query.get("message", {})
    chat_id = str(message.get("chat", {}).get("id"))
    
    # Get channel driver to respond
    channel_doc = frappe.get_doc("AZ Omni Channel", channel)
    driver = channel_doc.get_driver()
    
    # Acknowledge the callback
    driver.answer_callback_query(query_id, text="Processing...")
    
    # Handle the callback data
    # Format expected: action:param1:param2
    parts = data.split(":")
    action = parts[0] if parts else ""
    
    if action == "confirm":
        driver.send_text_message(chat_id, "✅ Confirmed!")
    elif action == "cancel":
        driver.send_text_message(chat_id, "❌ Cancelled")
    elif action == "meeting":
        # Create instant meeting
        from arrowz.arrowz.doctype.az_meeting_room.az_meeting_room import create_instant_meeting
        meeting = create_instant_meeting(
            room_name=f"Telegram Meeting - {frappe.utils.now()}",
            link_doctype="AZ Conversation Session",
            link_name=parts[1] if len(parts) > 1 else None
        )
        driver.send_text_message(
            chat_id,
            f"🎥 Meeting created!\n\nJoin here: {meeting.get('participant_url')}"
        )
    else:
        # Custom callback handling
        frappe.publish_realtime(
            "arrowz_telegram_callback",
            {
                "channel": channel,
                "chat_id": chat_id,
                "action": action,
                "data": parts[1:] if len(parts) > 1 else []
            }
        )


def handle_bot_command(command: str, chat_id: str, sender: Dict, channel: str):
    """Handle Telegram bot commands"""
    channel_doc = frappe.get_doc("AZ Omni Channel", channel)
    driver = channel_doc.get_driver()
    
    cmd = command.split()[0].lower()
    args = command.split()[1:] if len(command.split()) > 1 else []
    
    if cmd == "/start":
        welcome_msg = f"""
👋 Welcome to Arrowz Communication Hub!

You can use this bot to:
• Send messages to our team
• Schedule video meetings
• Get support

Type /help for available commands.
        """
        driver.send_text_message(chat_id, welcome_msg)
    
    elif cmd == "/help":
        help_msg = """
📖 Available Commands:

/start - Start the bot
/help - Show this help message
/meeting - Request a video meeting
/status - Check your request status
/contact - Get contact information
        """
        driver.send_text_message(chat_id, help_msg)
    
    elif cmd == "/meeting":
        # Send meeting request options
        buttons = [
            [{"text": "📅 Schedule Meeting", "callback_data": "meeting:schedule"}],
            [{"text": "🚀 Instant Meeting", "callback_data": "meeting:instant"}]
        ]
        driver.send_inline_keyboard(
            chat_id,
            "How would you like to meet?",
            buttons
        )
    
    elif cmd == "/status":
        # Check for open sessions
        from arrowz.arrowz.doctype.az_conversation_session.az_conversation_session import get_sessions_for_user
        # This would need to match by Telegram chat_id
        driver.send_text_message(chat_id, "📊 Checking your status...")
    
    elif cmd == "/contact":
        # Get company contact info from settings
        driver.send_text_message(
            chat_id,
            "📞 Contact us:\n\nPhone: +1234567890\nEmail: support@company.com"
        )
    
    else:
        driver.send_text_message(
            chat_id,
            "❓ Unknown command. Type /help for available commands."
        )


# Integration with frappe_telegram app

def sync_with_frappe_telegram():
    """
    Sync channels with frappe_telegram app if installed
    
    This allows using existing Telegram bots configured in frappe_telegram
    """
    if not frappe.db.exists("DocType", "Telegram Bot"):
        return []
    
    bots = frappe.get_all(
        "Telegram Bot",
        filters={"enabled": 1},
        fields=["name", "bot_name", "bot_token"]
    )
    
    synced = []
    for bot in bots:
        # Check if channel exists
        existing = frappe.db.exists(
            "AZ Omni Channel",
            {"account_id": bot.name}
        )
        
        if not existing:
            # Get or create Telegram provider
            provider = frappe.db.get_value(
                "AZ Omni Provider",
                {"provider_type": "Telegram Bot"},
                "name"
            )
            
            if not provider:
                provider_doc = frappe.get_doc({
                    "doctype": "AZ Omni Provider",
                    "provider_name": "Telegram",
                    "provider_type": "Telegram Bot",
                    "is_enabled": 1,
                    "driver_class": "arrowz.integrations.telegram.TelegramDriver"
                })
                provider_doc.insert(ignore_permissions=True)
                provider = provider_doc.name
            
            # Create channel
            channel = frappe.get_doc({
                "doctype": "AZ Omni Channel",
                "channel_name": bot.bot_name,
                "provider": provider,
                "account_id": bot.name,
                "access_token": bot.bot_token,
                "is_active": 1
            })
            channel.insert(ignore_permissions=True)
            synced.append(channel.name)
    
    return synced
