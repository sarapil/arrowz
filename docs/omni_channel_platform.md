# Arrowz Omni-Channel Platform Documentation

## Overview

The Arrowz Omni-Channel Platform provides a unified communication interface for your Frappe/ERPNext system. It integrates multiple communication channels including:

- **WhatsApp** (via Meta Cloud API or On-Premise)
- **Telegram** (via Bot API)
- **Email** (native Frappe)
- **Phone/PBX** (via Arrowz VoIP)
- **Video Meetings** (via OpenMeetings)

All communications are accessible from a unified panel embedded in 15+ DocTypes, providing complete visibility into customer interactions.

---

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Features](#features)
4. [User Guide](#user-guide)
5. [Admin Guide](#admin-guide)
6. [Developer Guide](#developer-guide)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- Frappe Framework v15+
- ERPNext (recommended for full functionality)
- frappe_whatsapp app (for WhatsApp integration)
- frappe_telegram app (for Telegram integration)

### Install Steps

```bash
# Install Arrowz app
bench get-app --branch main arrowz

# Install on your site
bench --site your-site.localhost install-app arrowz

# Run migrations
bench --site your-site.localhost migrate

# Build assets
bench build --app arrowz
```

---

## Configuration

### 1. WhatsApp Setup

#### Meta Cloud API (Recommended)

1. Go to **AZ Omni Provider** list
2. Create new provider:
   - **Provider Type**: WhatsApp Cloud
   - **Provider Name**: Meta Cloud WhatsApp
   - **Endpoint URL**: `https://graph.facebook.com/v18.0`
   - **API Key**: Your Meta Access Token
   - **App Secret**: Your Meta App Secret
   - **Verify Token**: Custom token for webhook verification

3. Create **AZ Omni Channel**:
   - **Channel Type**: WhatsApp
   - **Provider**: Select the provider created above
   - **Channel ID**: Your Phone Number ID from Meta
   - **Channel Name**: Business WhatsApp

4. Configure Webhook in Meta Developer Console:
   ```
   URL: https://your-site.com/api/method/arrowz.api.webhooks.whatsapp_cloud_webhook
   Verify Token: (same as configured in provider)
   ```

#### On-Premise API

For self-hosted WhatsApp Business API:

1. Create provider with **Provider Type**: WhatsApp On-Premise
2. Set **Endpoint URL** to your container's API URL
3. Configure authentication credentials

### 2. Telegram Setup

1. Create a Telegram Bot via @BotFather
2. Create **AZ Omni Provider**:
   - **Provider Type**: Telegram
   - **API Key**: Your Bot Token
   - **Webhook Secret**: Optional secret for verification

3. Create **AZ Omni Channel** for the bot

4. Register webhook:
   ```python
   frappe.call({
       method: "arrowz.api.webhooks.register_telegram_webhook",
       args: {
           bot_token: "YOUR_BOT_TOKEN"
       }
   })
   ```

### 3. OpenMeetings Setup

1. Install and configure OpenMeetings server
2. Create **AZ Omni Provider**:
   - **Provider Type**: OpenMeetings
   - **Endpoint URL**: `https://your-om-server.com/openmeetings`
   - **Username**: Admin username
   - **API Key**: Admin password or API key

3. Test connection:
   ```python
   from arrowz.integrations.openmeetings import OpenMeetingsConnector
   connector = OpenMeetingsConnector(...)
   print(connector.get_room_list())
   ```

---

## Features

### Unified Communication Panel

The communication panel appears on all supported DocTypes:

- Lead
- Customer
- Contact
- Opportunity
- Prospect
- Supplier
- Sales Order
- Purchase Order
- Quotation
- Employee
- Address
- Sales Partner
- Issue
- Project
- Task

**Features:**
- View all communications in one place
- Filter by channel (WhatsApp, Telegram, Email, Phone, Video)
- Unread message badges
- Quick reply to messages
- Send new messages
- Schedule video meetings
- View call history
- Real-time updates

### WhatsApp Integration

- **24-Hour Window Tracking**: Automatically tracks the 24-hour conversation window
- **Template Messages**: Send approved templates when window expires
- **Media Support**: Images, documents, videos, audio
- **Status Tracking**: Sent, Delivered, Read status for messages
- **Auto-Linking**: Automatically links conversations to Contacts/Leads/Customers

### Telegram Integration

- **Bot Commands**: Built-in commands (/start, /help, /meeting)
- **Inline Keyboards**: Interactive message buttons
- **Callback Queries**: Handle button clicks
- **Rich Media**: Send documents, images, locations

### Video Meetings (OpenMeetings)

- **Permanent Rooms**: Persistent meeting rooms for recurring meetings
- **Temporary Rooms**: Auto-cleanup after meeting ends
- **Hash-Based Access**: Secure links without requiring login
- **Recording**: Optional recording with download links
- **Calendar Integration**: iCal invitations for participants
- **Participant Management**: Track attendance

---

## User Guide

### Viewing Communication History

1. Open any supported document (Lead, Customer, etc.)
2. The Communication Panel appears below the form fields
3. Click on channel tabs to filter by channel
4. Click on a conversation to view details

### Sending WhatsApp Message

1. Click the WhatsApp button in quick actions
2. Enter phone number (auto-filled if available)
3. If 24h window expired, select a template
4. Type your message
5. Click Send

### Starting a Telegram Conversation

1. The contact must first message your bot
2. Once they do, the conversation appears in the panel
3. Click to open and reply

### Scheduling a Video Meeting

1. Click the Video button in quick actions
2. Enter meeting name and time
3. Add participants with email addresses
4. Click Schedule
5. Invitations are sent automatically

### Managing Conversations

- **Assign**: Assign conversations to team members
- **Close**: Close resolved conversations
- **Quick Replies**: Use pre-defined quick reply templates

---

## Admin Guide

### Managing Providers

Providers are the connection configurations for each communication service.

**AZ Omni Provider Fields:**
- Provider Type (WhatsApp Cloud, WhatsApp On-Premise, Telegram, OpenMeetings, SMS)
- Provider Name
- Endpoint URL
- Authentication credentials
- Rate limits
- Capabilities

### Managing Channels

Channels are individual communication endpoints (phone numbers, bots).

**AZ Omni Channel Fields:**
- Channel Type
- Provider (link)
- Channel ID (phone number ID, bot ID)
- Routing rules
- Working hours
- Auto-reply messages
- Default status

### Monitoring

1. **Webhook Status**: Check `/api/method/arrowz.api.webhooks.get_webhook_status`
2. **Active Conversations**: View AZ Conversation Session list
3. **Meeting Rooms**: View AZ Meeting Room list
4. **Error Logs**: Check Error Log for integration issues

### Scheduled Tasks

The following tasks run automatically:

| Task | Schedule | Description |
|------|----------|-------------|
| check_window_expiry | Every 15 min | Check WhatsApp 24h window expiry |
| sync_openmeetings_status | Hourly | Sync meeting status |
| cleanup_ended_conversations | Daily | Archive old conversations |
| cleanup_temporary_rooms | Daily | Delete old temporary rooms |
| generate_omni_channel_report | Weekly | Email analytics report |

---

## Developer Guide

### Architecture

```
arrowz/
├── arrowz/
│   ├── api/
│   │   ├── webhooks.py      # Webhook endpoints
│   │   └── communications.py # Communication API
│   ├── doctype/
│   │   ├── az_omni_provider/
│   │   ├── az_omni_channel/
│   │   ├── az_conversation_session/
│   │   ├── az_meeting_room/
│   │   └── ... child tables
│   ├── events/
│   │   ├── conversation.py  # Session event handlers
│   │   └── meeting.py       # Meeting event handlers
│   ├── integrations/
│   │   ├── base.py          # BaseDriver abstract class
│   │   ├── whatsapp.py      # WhatsApp drivers
│   │   ├── telegram.py      # Telegram driver
│   │   └── openmeetings.py  # OpenMeetings connector
│   ├── public/
│   │   ├── js/
│   │   │   ├── omni_panel.js           # Communication panel
│   │   │   └── omni_doctype_extension.js
│   │   └── css/
│   │       └── omni_panel.css
│   ├── notifications.py     # Notification config
│   └── tasks.py             # Scheduled tasks
```

### Driver Pattern

All communication integrations follow the Driver Pattern:

```python
from arrowz.integrations.base import BaseDriver

class MyCustomDriver(BaseDriver):
    def __init__(self, api_key, **kwargs):
        super().__init__(provider_type="MyProvider")
        self.api_key = api_key
    
    def send_text(self, recipient, message, **kwargs):
        # Implementation
        return {"success": True, "message_id": "xxx"}
    
    def send_media(self, recipient, media_url, media_type, caption=None, **kwargs):
        # Implementation
        pass
    
    def get_message_status(self, message_id):
        # Implementation
        pass
```

### Adding New DocTypes

To add the communication panel to a new DocType:

1. Add to `arrowz.omni.supported_doctypes` in `omni_doctype_extension.js`
2. Add doctype_js entry in `hooks.py`:
   ```python
   doctype_js = {
       "Your DocType": "public/js/your_doctype.js",
   }
   ```
3. Create the extension file:
   ```javascript
   frappe.ui.form.on('Your DocType', {
       refresh: function(frm) {
           if (!frm.is_new() && typeof arrowz.omni !== 'undefined') {
               arrowz.omni.init(frm);
           }
       }
   });
   ```

### Webhook Processing

Webhooks follow the "Ack-and-Queue" strategy:

1. Immediately return HTTP 200
2. Validate signature/token
3. Queue payload for background processing
4. Process in worker with `frappe.enqueue()`

```python
@frappe.whitelist(allow_guest=True)
def my_webhook():
    frappe.response["http_status_code"] = 200
    
    payload = json.loads(frappe.request.data)
    
    frappe.enqueue(
        "arrowz.integrations.my_driver.process_webhook",
        queue="default",
        payload=payload
    )
    
    return {"status": "queued"}
```

### Real-time Events

Events published via `frappe.publish_realtime()`:

| Event | Description |
|-------|-------------|
| new_message | New incoming/outgoing message |
| message_status | Message status update |
| conversation_update | Session status change |
| conversation_assigned | Conversation assigned |
| window_expired | WhatsApp window expired |
| meeting_started | Meeting started |
| meeting_ended | Meeting ended |
| meeting_user_joined | User joined meeting |
| meeting_user_left | User left meeting |
| recording_ready | Recording available |

---

## API Reference

### Communications API

#### Get Communication History

```python
frappe.call({
    method: "arrowz.api.communications.get_communication_history",
    args: {
        doctype: "Lead",
        docname: "LEAD-00001",
        channels: ["WhatsApp", "Telegram"],  // Optional filter
        limit: 50,
        offset: 0
    }
})
```

#### Send Message

```python
frappe.call({
    method: "arrowz.api.communications.send_message",
    args: {
        channel: "WhatsApp",
        recipient: "+1234567890",
        message: "Hello!",
        message_type: "text",  // text, image, document, template
        reference_doctype: "Lead",
        reference_name: "LEAD-00001"
    }
})
```

#### Schedule Meeting

```python
frappe.call({
    method: "arrowz.api.communications.schedule_meeting",
    args: {
        reference_doctype: "Project",
        reference_name: "PROJ-00001",
        room_name: "Weekly Standup",
        scheduled_start: "2024-01-15 10:00:00",
        scheduled_end: "2024-01-15 11:00:00",
        participants: [
            {name: "John Doe", email: "john@example.com", is_moderator: 1}
        ]
    }
})
```

### Webhook URLs

| Provider | URL |
|----------|-----|
| WhatsApp Cloud | `/api/method/arrowz.api.webhooks.whatsapp_cloud_webhook` |
| WhatsApp On-Prem | `/api/method/arrowz.api.webhooks.whatsapp_onprem_webhook` |
| Telegram | `/api/method/arrowz.api.webhooks.telegram_webhook` |
| OpenMeetings | `/api/method/arrowz.api.webhooks.openmeetings_callback` |

---

## Troubleshooting

### WhatsApp Messages Not Received

1. Check webhook configuration in Meta Developer Console
2. Verify webhook URL is accessible (HTTPS required)
3. Check Error Log for webhook errors
4. Verify Verify Token matches

### Telegram Bot Not Responding

1. Ensure bot token is correct
2. Check if webhook is registered: `getWebhookInfo` API
3. Verify webhook URL is HTTPS with valid certificate
4. Check Error Log for processing errors

### OpenMeetings Connection Failed

1. Verify server URL and credentials
2. Check if OpenMeetings server is running
3. Ensure REST API is enabled in OpenMeetings
4. Test with curl: `curl -X POST https://server/openmeetings/services/user/login`

### Communication Panel Not Showing

1. Clear browser cache
2. Run `bench build --app arrowz`
3. Check browser console for JavaScript errors
4. Verify DocType is in supported list

### Missing Messages

1. Check if session exists in AZ Conversation Session
2. Verify webhook is processing correctly
3. Check worker queue status: `bench doctor`
4. Review Error Log for processing failures

---

## Support

For support and feature requests, please contact the Arrowz team or create an issue in the GitHub repository.
