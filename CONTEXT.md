# Arrowz - Complete Technical Context

> This document provides comprehensive technical context for developers, AI assistants, and maintainers working with the Arrowz application.

## Table of Contents
1. [Application Identity](#application-identity)
2. [Technology Stack](#technology-stack)
3. [Core Concepts](#core-concepts)
4. [DocType Reference](#doctype-reference)
5. [API Reference](#api-reference)
6. [Frontend Components](#frontend-components)
7. [Integration Drivers](#integration-drivers)
8. [Real-time Events](#real-time-events)
9. [Scheduled Tasks](#scheduled-tasks)
10. [Configuration Options](#configuration-options)
11. [Security Model](#security-model)
12. [Error Handling](#error-handling)
13. [Performance Considerations](#performance-considerations)
14. [Troubleshooting Guide](#troubleshooting-guide)

---

## Application Identity

| Attribute | Value |
|-----------|-------|
| **Name** | Arrowz |
| **Type** | Frappe Framework Application |
| **Module** | Arrowz |
| **Version** | 1.0.0 |
| **License** | MIT |
| **Primary Purpose** | Enterprise VoIP Call Management & Omni-Channel Communications |

### Core Capabilities
1. **WebRTC Softphone** - Browser-based VoIP calling
2. **Omni-Channel Messaging** - WhatsApp, Telegram integration
3. **Video Conferencing** - OpenMeetings integration
4. **AI Analytics** - Sentiment analysis, coaching
5. **CRM Integration** - Contact identification, history

---

## Technology Stack

### Backend
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Frappe | v15+ |
| Language | Python | 3.10+ |
| Database | MariaDB | 10.6+ |
| Cache | Redis | 6+ |
| Queue | RQ (Redis Queue) | - |

### Frontend
| Component | Technology | Version |
|-----------|------------|---------|
| UI Framework | Frappe Desk | v15+ |
| JavaScript | ES6+ | - |
| CSS | Custom + Bootstrap | 4.x |
| WebRTC | JsSIP | 3.x |
| Real-time | Socket.IO | 4.x |

### External Integrations
| Service | Protocol | Purpose |
|---------|----------|---------|
| FreePBX/Asterisk | WebSocket (WSS) | SIP signaling for WebRTC |
| FreePBX/Asterisk | AMI (TCP) | Call events |
| WhatsApp | REST (Graph API) | Messaging |
| Telegram | REST (Bot API) | Messaging |
| OpenMeetings | REST API | Video conferencing |
| OpenAI | REST API | AI features |

---

## Core Concepts

### 1. Extensions
An **Extension** represents a SIP phone line mapped to a Frappe user.

```
User (Frappe) ─────> AZ Extension ─────> PBX (FreePBX)
                         │
                         ├── extension: "1001"
                         ├── sip_password: "secret"
                         ├── server: "AZ Server Config/main"
                         └── webrtc_enabled: 1
```

### 2. Call Flow
```
Incoming Call:
PBX ──WebSocket──> JsSIP ──> softphone_v2.js ──> UI Notification
                                    │
                                    └──> screen_pop.js ──> Contact Lookup

Outgoing Call:
User clicks "Call" ──> arrowz.softphone.dial() ──> JsSIP ──WebSocket──> PBX
```

### 3. Omni-Channel Flow
```
External Message (WhatsApp/Telegram):
Platform ──Webhook──> arrowz.api.webhooks ──> AZ Conversation Session
                                                    │
                                                    └──> Socket.IO ──> omni_panel.js

Agent Reply:
omni_panel.js ──> arrowz.api.communications ──> Integration Driver ──> Platform
```

### 4. Video Meeting Flow
```
Create Meeting:
User ──> AZ Meeting Room ──> openmeetings.py ──> OpenMeetings Server
                                                        │
                                                        └── External Room ID

Join Meeting:
User clicks "Join" ──> Open meeting URL in new tab
```

---

## DocType Reference

### Arrowz Settings (Single)
**Purpose**: Global application configuration

| Field | Type | Description |
|-------|------|-------------|
| `enable_ai` | Check | Enable AI features |
| `openai_api_key` | Password | OpenAI API key |
| `default_server` | Link | Default PBX server |
| `enable_sentiment` | Check | Real-time sentiment |
| `enable_coaching` | Check | AI coaching suggestions |
| `screen_pop_enabled` | Check | Show caller info popup |
| `auto_answer_delay` | Int | Seconds before auto-answer |

### AZ Server Config
**Purpose**: PBX and OpenMeetings server configuration

| Field | Type | Description |
|-------|------|-------------|
| `server_name` | Data | Friendly name |
| `server_type` | Select | FreePBX/Asterisk/OpenMeetings |
| `host` | Data | Server hostname/IP |
| `websocket_url` | Data | WebSocket URL for WebRTC |
| `ami_port` | Int | AMI port (5038) |
| `username` | Data | Admin username |
| `password` | Password | Admin password |
| `is_default` | Check | Default server |

### AZ Extension
**Purpose**: Map Frappe users to SIP extensions

| Field | Type | Description |
|-------|------|-------------|
| `extension` | Data | SIP extension number |
| `user` | Link (User) | Linked Frappe user |
| `display_name` | Data | Caller ID name |
| `server` | Link (AZ Server Config) | PBX server |
| `sip_password` | Password | SIP auth password |
| `webrtc_enabled` | Check | Enable WebRTC |
| `ring_timeout` | Int | Ring timeout seconds |
| `voicemail_enabled` | Check | Send to VM on timeout |

### AZ Call Log
**Purpose**: Call history records

| Field | Type | Description |
|-------|------|-------------|
| `call_id` | Data | Unique call identifier |
| `caller` | Data | Caller phone/extension |
| `receiver` | Data | Receiver phone/extension |
| `direction` | Select | Inbound/Outbound/Internal |
| `status` | Select | Ringing/In Progress/Completed/Missed/Failed |
| `start_time` | Datetime | Call start |
| `end_time` | Datetime | Call end |
| `duration` | Int | Duration in seconds |
| `recording_url` | Data | Recording file URL |
| `user` | Link (User) | Associated user |
| `contact` | Link (Contact) | Linked contact |
| `lead` | Link (Lead) | Linked lead |
| `acknowledged` | Check | Agent acknowledged missed call |
| `notes` | Text | Agent notes |
| `sentiment_score` | Float | AI sentiment (-1 to 1) |
| `transcription` | Long Text | Call transcription |

### AZ SMS Message
**Purpose**: SMS history

| Field | Type | Description |
|-------|------|-------------|
| `phone` | Data | Phone number |
| `message` | Text | Message content |
| `direction` | Select | Inbound/Outbound |
| `status` | Select | Sent/Delivered/Failed/Received |
| `provider` | Link (AZ SMS Provider) | SMS gateway |
| `sent_time` | Datetime | Timestamp |
| `external_id` | Data | Provider message ID |

### AZ SMS Provider
**Purpose**: SMS gateway configuration

| Field | Type | Description |
|-------|------|-------------|
| `provider_name` | Data | Friendly name |
| `provider_type` | Select | Twilio/Vonage/Plivo/Custom |
| `api_key` | Data | API key |
| `api_secret` | Password | API secret |
| `from_number` | Data | Sender number |
| `webhook_url` | Data | Webhook for delivery status |
| `is_default` | Check | Default provider |

### AZ Omni Provider
**Purpose**: WhatsApp/Telegram configuration

| Field | Type | Description |
|-------|------|-------------|
| `provider_name` | Data | Friendly name |
| `channel_type` | Select | WhatsApp/Telegram/Video Conference |
| `phone_number_id` | Data | WhatsApp Phone Number ID |
| `access_token` | Password | API access token |
| `webhook_secret` | Password | Webhook verification |
| `business_account_id` | Data | WhatsApp Business ID |
| `bot_token` | Password | Telegram bot token |
| `is_active` | Check | Provider active |

### AZ Omni Channel
**Purpose**: Channel routing and assignment

| Field | Type | Description |
|-------|------|-------------|
| `channel_name` | Data | Channel name |
| `provider` | Link (AZ Omni Provider) | Provider |
| `channel_id` | Data | Platform channel ID |
| `assigned_users` | Table MultiSelect | Assigned agents |
| `auto_assign` | Check | Round-robin assignment |
| `working_hours` | Table | Operating hours |

### AZ Conversation Session
**Purpose**: Chat session tracking

| Field | Type | Description |
|-------|------|-------------|
| `contact_number` | Data | Customer phone/ID |
| `contact_name` | Data | Customer name |
| `channel_type` | Select | WhatsApp/Telegram |
| `channel` | Link (AZ Omni Channel) | Channel |
| `status` | Select | Active/Waiting/Resolved/Expired |
| `assigned_agent` | Link (User) | Assigned agent |
| `first_message_time` | Datetime | Session start |
| `last_message_time` | Datetime | Last activity |
| `unread_count` | Int | Unread messages |
| `window_expires` | Datetime | 24h window expiry |
| `linked_contact` | Link (Contact) | CRM contact |
| `linked_lead` | Link (Lead) | CRM lead |

### AZ Conversation Message
**Purpose**: Individual chat messages

| Field | Type | Description |
|-------|------|-------------|
| `session` | Link (AZ Conversation Session) | Parent session |
| `message` | Long Text | Message content |
| `direction` | Select | Inbound/Outbound |
| `message_type` | Select | Text/Image/Document/Audio/Video |
| `timestamp` | Datetime | Message time |
| `media_url` | Data | Attachment URL |
| `media_mime_type` | Data | MIME type |
| `external_id` | Data | Platform message ID |
| `status` | Select | Sent/Delivered/Read/Failed |
| `sender_agent` | Link (User) | Sending agent |

### AZ Meeting Room
**Purpose**: Video conference rooms

| Field | Type | Description |
|-------|------|-------------|
| `room_name` | Data | Room title |
| `room_type` | Select | Conference/Webinar/Interview |
| `external_room_id` | Data | OpenMeetings room ID |
| `moderator` | Link (User) | Room owner |
| `is_locked` | Check | Require password |
| `password` | Password | Room password |
| `max_participants` | Int | Participant limit |
| `recording_enabled` | Check | Auto-record |
| `scheduled_time` | Datetime | Meeting time |
| `meeting_url` | Data | Join URL |

### AZ Meeting Participant
**Purpose**: Meeting attendance

| Field | Type | Description |
|-------|------|-------------|
| `meeting_room` | Link (AZ Meeting Room) | Room |
| `user` | Link (User) | Frappe user |
| `external_user_id` | Data | OpenMeetings user ID |
| `is_moderator` | Check | Moderator role |
| `join_time` | Datetime | Joined at |
| `leave_time` | Datetime | Left at |
| `is_present` | Check | Currently in room |

### AZ Meeting Recording
**Purpose**: Meeting recordings

| Field | Type | Description |
|-------|------|-------------|
| `meeting_room` | Link (AZ Meeting Room) | Room |
| `file_url` | Data | Recording URL |
| `file_name` | Data | File name |
| `duration` | Int | Duration seconds |
| `size` | Int | File size bytes |
| `recording_date` | Datetime | Recording time |

---

## API Reference

### arrowz.api.webrtc

```python
@frappe.whitelist()
def get_webrtc_config():
    """
    Get JsSIP configuration for current user.
    
    Returns:
        dict: {
            extension: str,
            extension_name: str,
            sip_uri: str,
            sip_password: str,
            websocket_servers: list[str],
            display_name: str,
            all_extensions: list[dict],  # If user has multiple
            outbound_proxy: str | None
        }
    """

@frappe.whitelist()
def switch_extension(extension_name: str):
    """Switch active extension for current user."""

@frappe.whitelist()
def register_webrtc_session(extension: str, user_agent: str):
    """Register WebRTC session for presence tracking."""
```

### arrowz.api.contacts

```python
@frappe.whitelist()
def search_contacts(query: str, limit: int = 10):
    """
    Search contacts across all linked DocTypes.
    
    Searches: Lead, Customer, Contact, Supplier, Employee
    
    Returns:
        list[dict]: [{
            doctype: str,
            name: str,
            full_name: str,
            phone: str,
            email: str
        }]
    """

@frappe.whitelist()
def get_contact_by_phone(phone: str):
    """Get contact details by phone number."""
```

### arrowz.api.notifications

```python
@frappe.whitelist()
def get_pending_notifications():
    """
    Get pending SMS and missed calls for current user.
    
    Returns:
        dict: {
            pending_sms: list[dict],
            missed_calls: int
        }
    """

@frappe.whitelist()
def get_unread_count():
    """Get total unread notification count."""

@frappe.whitelist()
def acknowledge_missed_call(call_log: str):
    """Mark missed call as acknowledged."""
```

### arrowz.api.call_log

```python
@frappe.whitelist()
def create_call_log(data: dict):
    """Create new call log entry."""

@frappe.whitelist()
def update_call_status(call_id: str, status: str, duration: int = None):
    """Update call status."""

@frappe.whitelist()
def get_recent_calls(limit: int = 20, direction: str = None):
    """Get recent calls for current user."""

@frappe.whitelist()
def get_call_stats(start_date: str, end_date: str):
    """Get call statistics for date range."""
```

### arrowz.api.sms

```python
@frappe.whitelist()
def send_sms(phone: str, message: str, provider: str = None):
    """Send SMS message."""

@frappe.whitelist()
def get_sms_history(phone: str = None, limit: int = 20):
    """Get SMS history."""
```

### arrowz.api.communications

```python
@frappe.whitelist()
def send_message(session: str, message: str, message_type: str = "Text"):
    """Send message to conversation session."""

@frappe.whitelist()
def get_active_conversations(user: str = None, limit: int = 20):
    """Get active conversations for user."""

@frappe.whitelist()
def get_conversation_messages(session: str, limit: int = 50):
    """Get messages for conversation session."""

@frappe.whitelist()
def assign_conversation(session: str, agent: str):
    """Assign conversation to agent."""

@frappe.whitelist()
def resolve_conversation(session: str):
    """Mark conversation as resolved."""
```

### arrowz.api.wallboard

```python
@frappe.whitelist()
def get_realtime_stats():
    """
    Get real-time dashboard statistics.
    
    Returns:
        dict: {
            active_calls: int,
            waiting_queue: int,
            agents_online: int,
            agents_busy: int,
            agents_away: int,
            avg_wait_time: float,
            calls_today: int,
            missed_today: int,
            sms_today: int,
            conversations_active: int
        }
    """

@frappe.whitelist()
def get_agent_status():
    """Get all agent statuses."""

@frappe.whitelist()
def set_agent_status(status: str):
    """Set current agent status."""
```

### arrowz.api.analytics

```python
@frappe.whitelist()
def get_call_volume_report(start_date: str, end_date: str, group_by: str = "day"):
    """Get call volume analytics."""

@frappe.whitelist()
def get_agent_performance(start_date: str, end_date: str, agent: str = None):
    """Get agent performance metrics."""

@frappe.whitelist()
def get_sentiment_trends(start_date: str, end_date: str):
    """Get sentiment analysis trends."""
```

### arrowz.api.webhooks

```python
@frappe.whitelist(allow_guest=True)
def whatsapp_cloud_webhook():
    """Handle WhatsApp Cloud API webhooks."""

@frappe.whitelist(allow_guest=True)
def telegram_webhook():
    """Handle Telegram Bot API webhooks."""

@frappe.whitelist(allow_guest=True)
def openmeetings_callback():
    """Handle OpenMeetings callbacks."""
```

---

## Frontend Components

### arrowz.js (Core Namespace)
```javascript
window.arrowz = {
    settings: {},      // App settings from boot
    softphone: {},     // Softphone component
    omni: {},          // Omni-channel components
    call: {},          // Call utilities
    
    init() { },        // Initialize app
    formatPhone(phone) { },  // Format phone number
    playSound(sound) { }     // Play notification sound
};
```

### softphone_v2.js (WebRTC Softphone)
```javascript
arrowz.softphone = {
    // State
    initialized: false,
    registered: false,
    ua: null,              // JsSIP User Agent
    session: null,         // Active call session
    config: null,          // WebRTC config
    allExtensions: [],     // User's extensions
    activeExtension: null,
    
    // Methods
    async init() { },          // Initialize softphone
    renderNavbarWidget() { },  // Render navbar UI
    setupJsSIP() { },          // Configure JsSIP
    
    // Call Operations
    dial(number) { },          // Make call
    answer() { },              // Answer incoming
    hangup() { },              // End call
    toggleMute() { },          // Mute/unmute
    toggleHold() { },          // Hold/unhold
    transfer(target) { },      // Transfer call
    sendDTMF(digit) { },       // Send DTMF
    
    // UI Operations
    toggleDropdown() { },
    showDialerUI() { },
    showActiveCallUI() { },
    showIncomingUI(caller) { },
    
    // Extension Management
    switchExtension(ext) { },
    
    // Status Updates
    updateNavbarStatus(status, text) { },
    updateNavbarBadge() { }
};
```

### omni_panel.js (Chat Panel)
```javascript
arrowz.omni.panel = {
    visible: false,
    currentSession: null,
    conversations: [],
    
    show() { },
    hide() { },
    toggle() { },
    
    loadConversations() { },
    selectConversation(session) { },
    sendMessage(text) { },
    attachFile(file) { },
    
    renderConversationList() { },
    renderChatArea() { },
    scrollToBottom() { }
};
```

### omni_doctype_extension.js (DocType Enhancements)
```javascript
arrowz.omni.NotificationBadge = class {
    constructor() { },
    render() { },
    fetch_count() { },
    update_badge(count) { },
    update_list(conversations) { },
    setup_realtime() { },
    show_notification(data) { }
};
```

### phone_actions.js (Click-to-Call)
```javascript
arrowz.phone_actions = {
    init() { },
    addPhoneButtons(frm) { },
    
    call(number) { },
    sendSMS(number) { },
    sendWhatsApp(number) { },
    showCallHistory(number) { }
};
```

### screen_pop.js (Caller ID Popup)
```javascript
arrowz.screenpop = {
    show(caller, callId) { },
    hide() { },
    
    lookupContact(phone) { },
    openRecord(doctype, name) { },
    createLead(phone) { }
};
```

---

## Integration Drivers

### arrowz/integrations/base.py
```python
class BaseConnector:
    """Base class for all integration connectors."""
    
    def __init__(self, config: dict): ...
    def send_message(self, to: str, message: str, **kwargs) -> dict: ...
    def get_media(self, media_id: str) -> bytes: ...
    def validate_webhook(self, request) -> bool: ...
```

### arrowz/integrations/whatsapp.py
```python
class WhatsAppCloudConnector(BaseConnector):
    """WhatsApp Cloud API connector."""
    
    API_VERSION = "v17.0"
    BASE_URL = "https://graph.facebook.com"
    
    def send_text(self, to: str, message: str) -> dict: ...
    def send_template(self, to: str, template: str, params: list) -> dict: ...
    def send_media(self, to: str, media_type: str, media_url: str) -> dict: ...
    def mark_read(self, message_id: str) -> dict: ...
    def download_media(self, media_id: str) -> bytes: ...
    
    def parse_webhook(self, payload: dict) -> dict: ...
    def verify_webhook(self, mode: str, token: str, challenge: str) -> str: ...
```

### arrowz/integrations/telegram.py
```python
class TelegramConnector(BaseConnector):
    """Telegram Bot API connector."""
    
    BASE_URL = "https://api.telegram.org/bot"
    
    def send_message(self, chat_id: str, text: str, **kwargs) -> dict: ...
    def send_photo(self, chat_id: str, photo_url: str, caption: str) -> dict: ...
    def send_document(self, chat_id: str, doc_url: str) -> dict: ...
    def get_file(self, file_id: str) -> bytes: ...
    
    def set_webhook(self, url: str, secret: str) -> bool: ...
    def parse_update(self, update: dict) -> dict: ...
```

### arrowz/integrations/openmeetings.py
```python
class OpenMeetingsConnector:
    """OpenMeetings REST API connector."""
    
    def __init__(self, server_config): ...
    def authenticate(self) -> str: ...
    
    def create_room(self, name: str, room_type: int, **kwargs) -> dict: ...
    def delete_room(self, room_id: int) -> bool: ...
    def get_room_hash(self, room_id: int, user: str) -> str: ...
    
    def invite_user(self, room_id: int, user_email: str) -> dict: ...
    def get_recordings(self, room_id: int) -> list: ...
    def download_recording(self, recording_id: int) -> bytes: ...
```

---

## Real-time Events

### Published Events (Python → JavaScript)

| Event | Payload | Trigger |
|-------|---------|---------|
| `arrowz_call_started` | `{call_id, caller, receiver, direction}` | New call initiated |
| `arrowz_call_ended` | `{call_id, duration, status}` | Call terminated |
| `arrowz_call_updated` | `{call_id, status}` | Call status change |
| `arrowz_new_sms` | `{phone, message, direction}` | SMS received |
| `arrowz_missed_call` | `{call_id, caller}` | Missed call |
| `arrowz_presence_update` | `{user, status}` | Agent status change |
| `new_message` | `{session, message, channel}` | Omni-channel message |
| `message_status` | `{message_id, status}` | Message delivery status |
| `conversation_update` | `{session, status, assigned}` | Conversation changed |
| `meeting_user_joined` | `{room, user}` | User joined meeting |
| `meeting_user_left` | `{room, user}` | User left meeting |
| `meeting_ended` | `{room}` | Meeting ended |

### Publishing Example (Python)
```python
frappe.publish_realtime(
    event="arrowz_call_started",
    message={
        "call_id": call_doc.name,
        "caller": call_doc.caller,
        "receiver": call_doc.receiver,
        "direction": call_doc.direction
    },
    user=target_user  # or room=, doctype=
)
```

### Subscribing Example (JavaScript)
```javascript
frappe.realtime.on("arrowz_call_started", (data) => {
    arrowz.screenpop.show(data.caller, data.call_id);
});
```

---

## Scheduled Tasks

### Defined in arrowz/tasks.py

| Task | Schedule | Purpose |
|------|----------|---------|
| `cleanup_stale_presence` | */5 * * * * | Remove stale presence records |
| `check_window_expiry` | */15 * * * * | Expire 24h WhatsApp windows |
| `sync_pbx_status` | Hourly | Sync with PBX |
| `sync_openmeetings_status` | Hourly | Sync meeting status |
| `cleanup_old_presence_logs` | Daily | Remove old presence logs |
| `generate_daily_report` | Daily | Create daily summary |
| `cleanup_ended_conversations` | Daily | Archive old conversations |
| `cleanup_temporary_rooms` | Daily | Delete temp meeting rooms |
| `cleanup_stale_calls` | Called manually | Clean stuck calls |
| `generate_weekly_analytics` | Weekly | Weekly analytics report |
| `generate_omni_channel_report` | Weekly | Omni-channel metrics |

---

## Configuration Options

### Site Config (site_config.json)
```json
{
  "arrowz_settings": {
    "enable_ai": true,
    "openai_api_key": "sk-xxx",
    "default_pbx": "AZ Server Config/main-pbx",
    "enable_debug_logging": false
  }
}
```

### Environment Variables
```bash
ARROWZ_DEBUG=1                    # Enable debug logging
ARROWZ_DISABLE_WEBHOOKS=0         # Disable webhook processing
ARROWZ_OPENAI_TIMEOUT=30          # OpenAI request timeout
```

---

## Security Model

### Permission Roles
| Role | Permissions |
|------|-------------|
| System Manager | Full access |
| Call Center Manager | View all, manage agents |
| Call Center Agent | Own calls, assigned conversations |

### API Security
- All whitelisted methods require login (default)
- Webhook endpoints use `allow_guest=True` with signature validation
- SIP passwords encrypted in database
- API keys stored as Password field type

### Data Protection
- Call recordings require explicit permission
- Recording URLs include time-limited tokens
- GDPR compliance hooks available

---

## Error Handling

### Python Patterns
```python
# User-facing error
frappe.throw(_("Extension not configured"), exc=frappe.ValidationError)

# Background error logging
try:
    result = external_api_call()
except Exception as e:
    frappe.log_error(
        message=frappe.get_traceback(),
        title="External API Error"
    )
    # Optionally re-raise or return graceful fallback
```

### JavaScript Patterns
```javascript
try {
    const { message } = await frappe.call({
        method: 'arrowz.api.webrtc.get_webrtc_config'
    });
} catch (error) {
    console.error('Arrowz: API error:', error);
    frappe.show_alert({
        message: __('Failed to load configuration'),
        indicator: 'red'
    });
}
```

---

## Performance Considerations

### Database
- Index on `AZ Call Log.start_time` for reporting
- Index on `AZ Conversation Session.status` for active queries
- Limit result sets in list queries

### Caching
- WebRTC config cached per session
- Contact search results cached briefly
- Wallboard stats with short TTL

### Real-time
- Use room-based events when possible
- Debounce rapid status updates
- Batch notification counts

---

## Troubleshooting Guide

### Softphone Not Appearing
1. Check browser console for JavaScript errors
2. Verify `softphone_v2.js` is included in `app_include_js`
3. Check navbar selector matches Frappe version
4. Ensure user has extension assigned

### WebRTC Registration Failed
1. Verify PBX WebSocket URL (wss://, not ws://)
2. Check SIP credentials in AZ Extension
3. Confirm PBX WebSocket module enabled
4. Test WebSocket connectivity

### Omni-Channel Not Receiving Messages
1. Verify webhook URL is publicly accessible
2. Check webhook signature validation
3. Inspect Error Log for webhook errors
4. Confirm provider credentials

### Calls Not Logging
1. Check AMI connection to PBX
2. Verify event handlers in hooks.py
3. Inspect background job queue
4. Check Error Log for exceptions

---

## Quick Reference Commands

```bash
# Development
bench build --app arrowz          # Build assets
bench watch --app arrowz          # Watch mode
bench --site dev.localhost clear-cache

# Testing
bench --site dev.localhost console
>>> frappe.call('arrowz.api.webrtc.get_webrtc_config')

# Maintenance
bench --site dev.localhost migrate
bench restart

# Logs
tail -f logs/worker.error.log
tail -f logs/frappe.log
```

---

*Last Updated: January 2026*
