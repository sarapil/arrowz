# Arrowz API Reference

## Overview

This document provides a comprehensive API reference for the Arrowz Omni-Channel Platform.

---

## REST API Endpoints

### Communications API

Base path: `/api/method/arrowz.api.communications`

---

### `get_communication_history`

Get unified communication history for a document.

**Method:** POST  
**Authentication:** Required

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| doctype | string | Yes | Reference DocType (e.g., "Lead", "Customer") |
| docname | string | Yes | Reference document name |
| channels | array | No | List of channels to filter |
| limit | integer | No | Number of records (default: 50) |
| offset | integer | No | Pagination offset |

**Response:**

```json
{
    "communications": [
        {
            "type": "conversation",
            "channel": "WhatsApp",
            "session_id": "AZ-CONV-00001",
            "contact_name": "John Doe",
            "contact_number": "+1234567890",
            "last_activity": "2024-01-15 10:30:00",
            "status": "Active",
            "unread_count": 3,
            "messages": [...]
        }
    ],
    "total": 25,
    "stats": {
        "total_communications": 100,
        "total_unread": 5,
        "channels": {
            "whatsapp": {"sessions": 10, "unread": 3},
            "telegram": {"sessions": 5, "unread": 2}
        }
    },
    "has_more": true
}
```

---

### `get_communication_stats`

Get communication statistics for a document.

**Method:** POST  
**Authentication:** Required

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| doctype | string | Yes | Reference DocType |
| docname | string | Yes | Reference document name |

**Response:**

```json
{
    "total_communications": 100,
    "total_unread": 5,
    "channels": {
        "whatsapp": {"sessions": 10, "unread": 3},
        "telegram": {"sessions": 5, "unread": 2},
        "email": {"count": 50, "unread": 0},
        "phone": {"count": 30, "missed": 5},
        "video": {"count": 5, "upcoming": 1}
    }
}
```

---

### `send_message`

Send a message through any channel.

**Method:** POST  
**Authentication:** Required

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| channel | string | Yes | "WhatsApp", "Telegram", "Email" |
| recipient | string | Yes | Phone number, chat_id, or email |
| message | string | Yes | Message content |
| message_type | string | No | "text", "image", "document", "template" |
| media_url | string | No | URL for media messages |
| reference_doctype | string | No | Link to document type |
| reference_name | string | No | Link to document name |
| template_name | string | No | Template name for template messages |
| template_params | object | No | Template parameters |

**Response:**

```json
{
    "success": true,
    "message_id": "wamid.xxx"
}
```

---

### `get_conversation_messages`

Get messages for a conversation session.

**Method:** POST  
**Authentication:** Required

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | AZ Conversation Session name |
| limit | integer | No | Number of messages (default: 50) |
| before_timestamp | datetime | No | For pagination |

**Response:**

```json
{
    "session": {
        "name": "AZ-CONV-00001",
        "channel_type": "WhatsApp",
        "contact_name": "John Doe",
        "status": "Active"
    },
    "messages": [
        {
            "message_id": "wamid.xxx",
            "direction": "Incoming",
            "message_type": "Text",
            "content": "Hello!",
            "timestamp": "2024-01-15 10:30:00",
            "status": "Delivered"
        }
    ],
    "has_more": false
}
```

---

### `mark_messages_read`

Mark all messages in a session as read.

**Method:** POST  
**Authentication:** Required

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | AZ Conversation Session name |

---

### `assign_conversation`

Assign a conversation to a user.

**Method:** POST  
**Authentication:** Required

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | AZ Conversation Session name |
| user | string | Yes | User ID to assign |

---

### `close_conversation`

Close a conversation session.

**Method:** POST  
**Authentication:** Required

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| session_id | string | Yes | AZ Conversation Session name |
| reason | string | No | Closure reason |

---

### `get_active_conversations`

Get active conversations.

**Method:** POST  
**Authentication:** Required

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user | string | No | Filter by assigned user |
| channel_type | string | No | Filter by channel |
| limit | integer | No | Number of conversations |

---

### `get_quick_replies`

Get quick reply templates for a channel.

**Method:** POST  
**Authentication:** Required

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| channel_type | string | Yes | "WhatsApp" or "Telegram" |

**Response:**

```json
[
    {"label": "👋 Greeting", "message": "Hello! How can I help you today?"},
    {"label": "🙏 Thank you", "message": "Thank you for contacting us!"}
]
```

---

### `schedule_meeting`

Schedule a video meeting.

**Method:** POST  
**Authentication:** Required

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| reference_doctype | string | Yes | Link document type |
| reference_name | string | Yes | Link document name |
| participants | array | Yes | List of participants |
| room_name | string | Yes | Meeting room name |
| scheduled_start | datetime | Yes | Start time |
| scheduled_end | datetime | No | End time |
| room_type | string | No | "Permanent" or "Temporary" |
| allow_recording | boolean | No | Enable recording |

**Participant Object:**

```json
{
    "name": "John Doe",
    "email": "john@example.com",
    "is_moderator": 1
}
```

---

### `start_whatsapp_conversation`

Quick action to start a WhatsApp conversation.

**Method:** POST  
**Authentication:** Required

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| phone_number | string | Yes | Contact phone number |
| reference_doctype | string | No | Link document type |
| reference_name | string | No | Link document name |
| template_name | string | No | Template for expired window |

---

## Webhook Endpoints

Base path: `/api/method/arrowz.api.webhooks`

### WhatsApp Cloud Webhook

**URL:** `/api/method/arrowz.api.webhooks.whatsapp_cloud_webhook`

**GET** - Webhook verification  
**POST** - Message notifications

**Headers:**
- `X-Hub-Signature-256`: HMAC signature for verification

---

### WhatsApp On-Premise Webhook

**URL:** `/api/method/arrowz.api.webhooks.whatsapp_onprem_webhook`

**POST** - Message notifications

**Headers:**
- `Authorization`: Bearer token

---

### Telegram Webhook

**URL:** `/api/method/arrowz.api.webhooks.telegram_webhook`

**POST** - Bot updates

**Headers:**
- `X-Telegram-Bot-Api-Secret-Token`: Optional secret

---

### Telegram Bot-Specific Webhook

**URL:** `/api/method/arrowz.api.webhooks.telegram_webhook_by_bot?bot_id={bot_id}`

For multi-bot setups.

---

### OpenMeetings Callback

**URL:** `/api/method/arrowz.api.webhooks.openmeetings_callback`

**POST** - Room events

**Payload Events:**
- `user_joined`
- `user_left`
- `recording_ready`
- `room_closed`

---

## Webhook Management

### `setup_webhooks`

Get webhook URLs for all providers.

**Method:** POST  
**Authentication:** Required (System Manager)

**Response:**

```json
{
    "whatsapp_cloud": {
        "url": "https://site.com/api/method/arrowz.api.webhooks.whatsapp_cloud_webhook",
        "description": "Configure in Meta Developer Console"
    },
    "telegram": {
        "url": "https://site.com/api/method/arrowz.api.webhooks.telegram_webhook",
        "description": "Use with Telegram setWebhook"
    }
}
```

---

### `register_telegram_webhook`

Register webhook with Telegram.

**Method:** POST  
**Authentication:** Required

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| bot_token | string | Yes | Telegram bot token |
| bot_id | string | No | Bot identifier for multi-bot |

---

### `get_webhook_status`

Check webhook configuration status.

**Method:** POST  
**Authentication:** Required (System Manager)

---

## Notifications API

Base path: `/api/method/arrowz.notifications`

### `get_notification_summary`

Get notification summary for current user.

**Method:** POST  
**Authentication:** Required

**Response:**

```json
{
    "counts": {
        "total": 10,
        "whatsapp": 5,
        "telegram": 3,
        "email": 2,
        "calls_missed": 0,
        "meetings_upcoming": 1
    },
    "recent_conversations": [...],
    "upcoming_meetings": [...]
}
```

---

## Real-time Events

Subscribe to events using `frappe.realtime.on()`:

### Message Events

```javascript
frappe.realtime.on("new_message", function(data) {
    console.log("New message:", data);
    // data: {session_id, channel, message, contact_name, preview}
});

frappe.realtime.on("message_status", function(data) {
    console.log("Status update:", data);
    // data: {session_id, message_id, status}
});
```

### Conversation Events

```javascript
frappe.realtime.on("conversation_update", function(data) {
    // data: {session_id, status, channel}
});

frappe.realtime.on("conversation_assigned", function(data) {
    // data: {session_id, channel, contact, assigned_by}
});

frappe.realtime.on("window_expired", function(data) {
    // data: {session_id, contact}
});
```

### Meeting Events

```javascript
frappe.realtime.on("meeting_started", function(data) {
    // data: {room, room_name, host_url}
});

frappe.realtime.on("meeting_ended", function(data) {
    // data: {room, room_name}
});

frappe.realtime.on("meeting_user_joined", function(data) {
    // data: {room, user, user_id}
});

frappe.realtime.on("recording_ready", function(data) {
    // data: {room, recording_id, url}
});
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 429 | Rate Limited - Too many requests |
| 500 | Server Error - Check Error Log |

---

## Rate Limits

Rate limits are configured per provider in AZ Omni Provider:

- `rate_limit_per_second`: Requests per second
- `rate_limit_per_day`: Requests per day

WhatsApp Cloud API has additional limits enforced by Meta:
- 80 messages/second for Business API
- Template message limits vary by tier
