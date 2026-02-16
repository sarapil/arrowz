# Arrowz API Reference
## Complete Backend API Specifications

---

## 📡 API Overview

All APIs are whitelisted Frappe methods accessible via:
```
POST /api/method/arrowz.api.{module}.{function}
```

---

## 1️⃣ WebRTC API (`arrowz.api.webrtc`)

### `get_webrtc_config`
Get WebRTC/SIP configuration for current user

```python
@frappe.whitelist()
def get_webrtc_config(user=None):
    """
    Get WebRTC configuration for softphone initialization.
    
    Args:
        user (str, optional): User email. Defaults to current user.
    
    Returns:
        dict: {
            "extension": "1001",
            "sip_uri": "sip:1001@pbx.example.com",
            "sip_password": "secret",
            "sip_domain": "pbx.example.com",
            "display_name": "John Doe",
            "websocket_servers": ["wss://pbx.example.com:8089/ws"],
            "stun_server": "stun:stun.l.google.com:19302",
            "turn_server": null,
            "ice_servers": [...],
            "extension_type": "WebRTC",
            "encryption": "DTLS-SRTP",
            "transport": "WSS",
            "ai_enabled": true,
            "recording_enabled": false,
            "webrtc_enabled": true
        }
        
    Errors:
        - "No extension found for user"
        - "Extension is not active"
        - "No PBX server configured"
    
    Implementation Notes:
        1. First check if user has extension assigned
        2. Get server config (from extension or default)
        3. Build WebSocket URL if not explicitly set
        4. Include ICE servers for NAT traversal
        5. Return configuration object for JsSIP
    """
```

### `register_extension`
Log SIP extension registration event

```python
@frappe.whitelist()
def register_extension(extension, user_agent=None):
    """
    Log successful SIP registration.
    
    Args:
        extension (str): Extension number
        user_agent (str, optional): Client user agent string
    
    Returns:
        dict: {"success": True, "message": "..."}
    """
```

### `log_webrtc_event`
Log WebRTC events for debugging/monitoring

```python
@frappe.whitelist()
def log_webrtc_event(event_type, extension=None, details=None, error_message=None):
    """
    Log WebRTC events.
    
    Args:
        event_type (str): Type of event (connection, registration, call, error)
        extension (str, optional): Extension number
        details (str, optional): Event details
        error_message (str, optional): Error message if applicable
    
    Returns:
        dict: {"success": True}
        
    Event Types:
        - sip_connecting
        - sip_connected
        - sip_disconnected
        - sip_registration
        - sip_registration_failed
        - call_started
        - call_ended
        - call_failed
        - media_error
    """
```

### `test_connectivity`
Test WebRTC/PBX connectivity

```python
@frappe.whitelist()
def test_connectivity():
    """
    Test WebRTC configuration and connectivity.
    
    Returns:
        dict: {
            "success": True/False,
            "tests": {
                "extension_configured": True,
                "sip_credentials": True,
                "websocket_url": True,
                "stun_server": True,
                "pbx_reachable": True
            },
            "message": "All tests passed"
        }
    """
```

---

## 2️⃣ AI API (`arrowz.api.ai`)

### `get_caller_history`
Get caller interaction history for AI context

```python
@frappe.whitelist()
def get_caller_history(contact=None, phone_number=None):
    """
    Get caller's historical data for AI analysis.
    
    Args:
        contact (str, optional): Contact document name
        phone_number (str, optional): Phone number to lookup
    
    Returns:
        dict: {
            "call_history": [
                {
                    "direction": "Inbound",
                    "start_time": "2024-01-15 10:30:00",
                    "duration": 180,
                    "status": "Completed",
                    "ai_sentiment": "positive",
                    "ai_summary": "..."
                }
            ],
            "crm_history": {
                "opportunities": [...],
                "quotations": [...]
            },
            "total_calls": 5,
            "last_call": {...}
        }
    """
```

### `generate_call_insights`
Generate AI-powered pre-call insights

```python
@frappe.whitelist()
def generate_call_insights(caller_info, history):
    """
    Generate AI insights before/during call.
    
    Args:
        caller_info (dict): Caller information
        history (dict): Caller history from get_caller_history
    
    Returns:
        dict: {
            "insights": "Customer has shown interest in...",
            "talking_points": [
                "Mention the pending quotation",
                "Ask about project timeline"
            ],
            "sentiment": "positive",
            "risk_level": "low",
            "recommended_actions": [...]
        }
    
    Implementation Notes:
        1. Check if OpenAI is configured
        2. Build context from history
        3. Call OpenAI API with structured prompt
        4. Parse and return insights
    """
```

### `analyze_sentiment`
Analyze text sentiment in real-time

```python
@frappe.whitelist()
def analyze_sentiment(text, context=None):
    """
    Analyze sentiment of text (transcript segment).
    
    Args:
        text (str): Text to analyze
        context (str, optional): Previous conversation context
    
    Returns:
        dict: {
            "sentiment": "positive",  # positive/neutral/negative
            "score": 0.85,  # 0-1 confidence
            "emotions": ["happy", "satisfied"],
            "key_phrases": ["great service", "thank you"]
        }
    """
```

### `generate_call_summary`
Generate post-call summary

```python
@frappe.whitelist()
def generate_call_summary(call_data, transcript=None):
    """
    Generate AI summary after call ends.
    
    Args:
        call_data (dict): Call metadata
        transcript (str, optional): Full call transcript
    
    Returns:
        dict: {
            "summary": "Customer called about...",
            "key_topics": ["pricing", "delivery"],
            "action_items": [
                "Send revised quotation",
                "Schedule follow-up call"
            ],
            "sentiment_summary": "Customer was initially frustrated but...",
            "next_steps": "Follow up within 2 days"
        }
    """
```

### `get_coaching_suggestions`
Get real-time coaching suggestions

```python
@frappe.whitelist()
def get_coaching_suggestions(transcript, sentiment, context=None):
    """
    Get AI coaching tips during call.
    
    Args:
        transcript (str): Current transcript
        sentiment (str): Current sentiment
        context (dict, optional): Call context
    
    Returns:
        dict: {
            "suggestions": [
                {
                    "type": "warning",
                    "message": "Customer seems frustrated, consider empathizing"
                },
                {
                    "type": "tip",
                    "message": "This is a good time to mention the discount"
                }
            ],
            "sentiment_trend": "declining",
            "recommended_response": "I understand your concern..."
        }
    """
```

---

## 3️⃣ CRM API (`arrowz.api.crm`)

### `get_contact_by_phone`
Find contact by phone number with fuzzy matching

```python
@frappe.whitelist()
def get_contact_by_phone(phone_number):
    """
    Find contact by phone number.
    
    Args:
        phone_number (str): Phone number to search
    
    Returns:
        dict: {
            "name": "CONT-00001",
            "first_name": "John",
            "last_name": "Doe",
            "email_id": "john@example.com",
            "phone": "+1234567890",
            "mobile_no": "+0987654321",
            "company_name": "Acme Corp",
            "customer": "CUST-00001",
            "recent_calls": [...],
            "opportunities": [...],
            "outstanding_amount": 5000
        }
        
    Implementation Notes:
        1. Clean/normalize phone number
        2. Try exact match on phone, mobile_no
        3. Try with country code variations
        4. Try fuzzy match (last 7-10 digits)
        5. Enhance with CRM data
    """
```

### `get_contact_call_summary`
Get comprehensive call summary for contact

```python
@frappe.whitelist()
def get_contact_call_summary(contact):
    """
    Get call statistics for a contact.
    
    Args:
        contact (str): Contact document name
    
    Returns:
        dict: {
            "total_calls": 25,
            "inbound": 15,
            "outbound": 10,
            "total_duration": 7200,  # seconds
            "avg_duration": 288,
            "last_call": "2024-01-15",
            "sentiment_breakdown": {
                "positive": 60,
                "neutral": 30,
                "negative": 10
            },
            "recent_calls": [...],
            "top_topics": ["pricing", "support", "delivery"]
        }
    """
```

### `create_lead_from_call`
Create lead from unknown caller

```python
@frappe.whitelist()
def create_lead_from_call(phone_number, call_log=None, additional_info=None):
    """
    Create a Lead from unknown caller.
    
    Args:
        phone_number (str): Caller's phone number
        call_log (str, optional): Call log reference
        additional_info (dict, optional): Extra info collected
    
    Returns:
        dict: {
            "success": True,
            "lead": "LEAD-00001",
            "message": "Lead created successfully"
        }
    """
```

### `link_call_to_opportunity`
Link call to opportunity

```python
@frappe.whitelist()
def link_call_to_opportunity(call_log, opportunity):
    """
    Link a call log to an opportunity.
    
    Args:
        call_log (str): Call log name
        opportunity (str): Opportunity name
    
    Returns:
        dict: {"success": True}
    """
```

### `schedule_follow_up`
Schedule follow-up call/event

```python
@frappe.whitelist()
def schedule_follow_up(contact, datetime, notes=None, reminder=True):
    """
    Schedule a follow-up call.
    
    Args:
        contact (str): Contact to call
        datetime (str): When to follow up
        notes (str, optional): Follow-up notes
        reminder (bool): Create reminder event
    
    Returns:
        dict: {
            "success": True,
            "event": "EVT-00001"
        }
    """
```

---

## 4️⃣ Call Log API (`arrowz.api.call_log`)

### `save_call_log`
Save comprehensive call log

```python
@frappe.whitelist()
def save_call_log(call_data):
    """
    Save or update call log with all data.
    
    Args:
        call_data (dict): {
            "session_id": "unique-session-id",
            "direction": "Inbound",
            "local_party": "1001",
            "remote_party": "+1234567890",
            "start_time": "2024-01-15 10:30:00",
            "end_time": "2024-01-15 10:35:00",
            "duration": 300,
            "status": "Completed",
            "ai_data": {
                "sentiment_changes": [...],
                "transcripts": [...],
                "key_topics": [...]
            },
            "metrics": {
                "audio_quality": [...],
                "packet_loss": [...],
                "jitter": [...]
            }
        }
    
    Returns:
        dict: {
            "success": True,
            "call_log": "CALL-2024-00001",
            "message": "Call log saved"
        }
        
    Implementation Notes:
        1. Check for existing log by session_id
        2. Map data to DocType fields
        3. Calculate quality scores
        4. Link to CRM entities
        5. Process AI data (sentiment logs)
    """
```

### `get_call_analytics_dashboard`
Get dashboard analytics data

```python
@frappe.whitelist()
def get_call_analytics_dashboard(period="today", user=None):
    """
    Get call analytics for dashboard.
    
    Args:
        period (str): today/week/month/year
        user (str, optional): Filter by user
    
    Returns:
        dict: {
            "summary": {
                "total_calls": 150,
                "inbound": 80,
                "outbound": 70,
                "missed": 10,
                "avg_duration": 180,
                "total_duration": 27000
            },
            "by_hour": [...],
            "by_day": [...],
            "by_user": [...],
            "sentiment_breakdown": {...},
            "top_contacts": [...],
            "quality_metrics": {...}
        }
    """
```

### `get_call_quality_report`
Get call quality metrics

```python
@frappe.whitelist()
def get_call_quality_report(period="week", threshold=None):
    """
    Get call quality report.
    
    Returns:
        dict: {
            "avg_quality_score": 85.5,
            "calls_below_threshold": 12,
            "packet_loss_avg": 1.2,
            "jitter_avg": 15.3,
            "issues": [
                {"type": "packet_loss", "count": 5, "severity": "high"},
                {"type": "jitter", "count": 3, "severity": "medium"}
            ]
        }
    """
```

---

## 5️⃣ Presence API (`arrowz.api.presence`)

### `update_user_status`
Update user presence status

```python
@frappe.whitelist()
def update_user_status(status, timestamp=None):
    """
    Update user's presence status.
    
    Args:
        status (str): online/busy/away/dnd/offline
        timestamp (str, optional): When status changed
    
    Returns:
        dict: {"success": True, "status": "online"}
        
    Side Effects:
        - Updates User document
        - Logs to CC Presence Log
        - Broadcasts via Socket.IO
    """
```

### `get_team_presence`
Get team members' presence

```python
@frappe.whitelist()
def get_team_presence(include_self=False):
    """
    Get presence of team members.
    
    Returns:
        list: [
            {
                "user": "user@example.com",
                "full_name": "John Doe",
                "status": "online",
                "last_active": "2024-01-15 10:30:00",
                "avatar": "/files/john.jpg",
                "is_online": True,
                "current_call": null
            }
        ]
    """
```

### `send_presence_heartbeat`
Send heartbeat to maintain online status

```python
@frappe.whitelist()
def send_presence_heartbeat(last_activity=None):
    """
    Send heartbeat to maintain presence.
    
    Should be called every 1-2 minutes from frontend.
    """
```

---

## 🔐 Permission Notes

### Role-Based Access
| API | Required Role |
|-----|---------------|
| get_webrtc_config | System User |
| AI APIs | Arrowz User |
| CRM APIs | Sales User or Arrowz User |
| Call Log APIs | Arrowz User |
| Presence APIs | System User |

### Permission Implementation
```python
# Example permission check
@frappe.whitelist()
def sensitive_function():
    if not frappe.has_permission("AZ Call Log", "read"):
        frappe.throw(_("Insufficient permissions"))
```

---

## 📊 Error Handling

### Standard Error Response
```python
{
    "error": "Error type or code",
    "message": "Human readable message",
    "details": {...}  # Optional
}
```

### Common Errors
| Error | HTTP Code | Meaning |
|-------|-----------|---------|
| Configuration error | 500 | Missing settings |
| Extension not found | 404 | User has no extension |
| Server not configured | 500 | No PBX server |
| API key missing | 500 | OpenAI not configured |

---

## 7️⃣ Call Transfer API (`arrowz.api.transfer`)

### `attended_transfer`
Initiate attended (warm) call transfer

```python
@frappe.whitelist()
def attended_transfer(call_id, target_extension):
    """
    Initiate attended transfer (consult first, then transfer).
    
    Args:
        call_id (str): Current call session ID
        target_extension (str): Extension to transfer to
    
    Returns:
        dict: {
            "success": True,
            "consult_channel": "SIP/1002-xxx",
            "message": "Consultation call initiated"
        }
    
    Process:
        1. Put original caller on hold
        2. Dial target extension
        3. Agent can speak with target
        4. Call complete_attended_transfer() or cancel_transfer()
    
    Implementation:
        Uses JsSIP's session.refer() with replaces header
    """
```

### `complete_attended_transfer`
Complete attended transfer after consultation

```python
@frappe.whitelist()
def complete_attended_transfer(call_id, consult_channel):
    """
    Complete attended transfer after consultation.
    
    Args:
        call_id (str): Original call session ID
        consult_channel (str): Consultation channel from attended_transfer
    
    Returns:
        dict: {
            "success": True,
            "message": "Transfer completed"
        }
    
    Side Effects:
        - Creates AZ Call Transfer Log entry
        - Updates original AZ Call Log
    """
```

### `blind_transfer`
Initiate blind (cold) transfer - Supervisors only

```python
@frappe.whitelist()
def blind_transfer(call_id, target_extension):
    """
    Initiate blind transfer (immediate, no consultation).
    
    Args:
        call_id (str): Current call session ID
        target_extension (str): Extension to transfer to
    
    Returns:
        dict: {
            "success": True,
            "message": "Transfer initiated"
        }
    
    Permissions:
        Requires 'Arrowz Supervisor' role
    
    Implementation:
        Uses JsSIP session.refer() directly
    """
```

### `get_available_transfer_targets`
Get list of extensions available for transfer

```python
@frappe.whitelist()
def get_available_transfer_targets():
    """
    Get available extensions for transfer.
    
    Returns:
        list: [
            {
                "extension": "1002",
                "display_name": "John Doe",
                "status": "available",  # available, busy, offline
                "user": "john@example.com"
            }
        ]
    
    Implementation Notes:
        - Excludes current user's extension
        - Shows real-time presence status
        - Sorted by availability then name
    """
```

---

## 8️⃣ Recording API (`arrowz.api.recordings`)

### `stream`
Stream recording file to browser

```python
@frappe.whitelist()
def stream(call_id):
    """
    Stream recording file for playback.
    
    Args:
        call_id (str): AZ Call Log document name
    
    Returns:
        Binary audio file (audio/wav or audio/mp3)
    
    Implementation:
        1. Verify permission on AZ Call Log
        2. Get file path from Docker volume
        3. Stream with proper Content-Type header
    """
```

### `get_recording_url`
Get secure time-limited URL for recording

```python
@frappe.whitelist()
def get_recording_url(call_id):
    """
    Get secure URL for recording playback.
    
    Args:
        call_id (str): AZ Call Log document name
    
    Returns:
        dict: {
            "url": "/api/method/arrowz.api.recordings.stream_secure?token=xxx",
            "expires_in": 3600
        }
    
    Security:
        - Token stored in Redis cache
        - Expires after 1 hour
        - One-time use optional
    """
```

### `stream_secure`
Stream recording with token-based authentication

```python
@frappe.whitelist(allow_guest=True)
def stream_secure(token):
    """
    Stream recording using secure token.
    
    Args:
        token (str): Time-limited token from get_recording_url
    
    Returns:
        Binary audio file
    
    Errors:
        - "Invalid or expired token"
    """
```

---

## 9️⃣ SMS API (`arrowz.api.sms`)

### `send_sms`
Send SMS message

```python
@frappe.whitelist()
def send_sms(to_number, message, linked_doctype=None, linked_docname=None, provider=None):
    """
    Send SMS message via configured provider.
    
    Args:
        to_number (str): Recipient phone number (E.164 format)
        message (str): Message body (max 160 for single SMS)
        linked_doctype (str, optional): Link to CRM record type
        linked_docname (str, optional): Link to CRM record name
        provider (str, optional): Specific provider to use
    
    Returns:
        dict: {
            "success": True,
            "message_id": "SMS-0001",
            "provider_message_id": "SM1234567890",
            "status": "Sent"
        }
    
    Provider Selection:
        1. Use specified provider if given
        2. Use default provider from AZ SMS Provider
        3. Fail if no provider configured
    
    Implementation Notes:
        - Auto-formats phone numbers to E.164
        - Creates AZ SMS Message record
        - Triggers webhook for delivery receipts
    """
```

### `get_sms_history`
Get SMS history for contact/lead

```python
@frappe.whitelist()
def get_sms_history(linked_doctype=None, linked_docname=None, phone_number=None, limit=50):
    """
    Get SMS message history.
    
    Args:
        linked_doctype (str, optional): Filter by linked record type
        linked_docname (str, optional): Filter by linked record
        phone_number (str, optional): Filter by phone number
        limit (int): Max messages to return
    
    Returns:
        list: [
            {
                "name": "SMS-0001",
                "direction": "Outbound",
                "from_number": "+1234567890",
                "to_number": "+0987654321",
                "message_body": "Hello...",
                "timestamp": "2024-01-15 10:30:00",
                "status": "Delivered"
            }
        ]
    """
```

### `handle_webhook`
Process delivery receipt webhooks from providers

```python
@frappe.whitelist(allow_guest=True)
def handle_webhook(provider):
    """
    Handle SMS provider webhooks.
    
    Args:
        provider (str): Provider name (from URL)
    
    Request Body:
        Provider-specific format
    
    Returns:
        dict: {"success": True}
    
    Implementation:
        1. Parse provider-specific format
        2. Find AZ SMS Message by provider_message_id
        3. Update status (Delivered, Failed)
        4. Log any errors
    """
```

---

## 🔟 FreePBX API (`arrowz.api.freepbx`)

### `list_extensions`
List all extensions from FreePBX via GraphQL

```python
@frappe.whitelist()
def list_extensions(server=None):
    """
    Get all extensions from FreePBX.
    
    Args:
        server (str, optional): Server config name
    
    Returns:
        list: [
            {
                "extension_id": "1001",
                "display_name": "John Doe",
                "tech": "pjsip",
                "transport": "wss"
            }
        ]
    
    Implementation:
        Uses FreePBX GraphQL API
    """
```

### `sync_extension`
Sync extension from FreePBX to local

```python
@frappe.whitelist()
def sync_extension(extension_id, server=None):
    """
    Sync single extension from FreePBX.
    
    Creates or updates AZ Extension record.
    
    Returns:
        dict: {
            "success": True,
            "action": "created" | "updated",
            "extension": "1001"
        }
    """
```

### `create_extension`
Create extension in FreePBX

```python
@frappe.whitelist()
def create_extension(extension_id, display_name, password, server=None, webrtc=True):
    """
    Create new extension in FreePBX via GraphQL.
    
    Args:
        extension_id (str): Extension number
        display_name (str): User display name
        password (str): SIP password
        server (str, optional): Server config name
        webrtc (bool): Enable WebRTC settings
    
    Returns:
        dict: {
            "success": True,
            "extension_id": "1001"
        }
    
    Implementation:
        Uses GraphQL addExtension mutation
    """
```

### `list_inbound_routes`
List inbound routes from FreePBX

```python
@frappe.whitelist()
def list_inbound_routes(server=None):
    """
    Get all inbound routes from FreePBX.
    
    Returns:
        list: [
            {
                "id": 1,
                "description": "Main Line",
                "did": "1234567890",
                "destination": "from-internal,1001,1"
            }
        ]
    """
```

### `create_trunk_ssh`
Create trunk via fwconsole SSH (fallback)

```python
@frappe.whitelist()
def create_trunk_ssh(trunk_data, server=None):
    """
    Create PJSIP trunk via fwconsole SSH.
    
    Used because Trunks not available in GraphQL API.
    
    Args:
        trunk_data (dict): {
            "name": "trunk-01",
            "host": "sip.provider.com",
            "username": "account",
            "secret": "password"
        }
        server (str, optional): Server config name
    
    Returns:
        dict: {
            "success": True,
            "output": "Trunk created..."
        }
    
    Requirements:
        - SSH enabled on server config
        - SSH key or password configured
    """
```

### `reload_config`
Reload FreePBX configuration

```python
@frappe.whitelist()
def reload_config(server=None):
    """
    Apply pending FreePBX changes.
    
    Equivalent to 'fwconsole reload'.
    
    Returns:
        dict: {
            "success": True,
            "message": "Configuration reloaded"
        }
    """
```

---

## 1️⃣1️⃣ Click-to-Dial API (`arrowz.api.click_to_dial`)

### `initiate_call`
Initiate outbound call via AMI

```python
@frappe.whitelist()
def initiate_call(phone_number, extension=None, linked_doctype=None, linked_docname=None):
    """
    Initiate outbound call (Click-to-Dial).
    
    Args:
        phone_number (str): Number to dial
        extension (str, optional): Agent's extension (default: current user)
        linked_doctype (str, optional): Link to CRM record
        linked_docname (str, optional): CRM record name
    
    Returns:
        dict: {
            "success": True,
            "action_id": "arrowz-12345",
            "message": "Call initiated"
        }
    
    Process:
        1. Send AMI Originate command
        2. First leg: Ring agent's extension
        3. When answered: Dial customer number
        4. Bridge both channels
    
    Implementation:
        Uses Asterisk AMI Originate action
    """
```

### `get_call_status`
Get status of initiated call

```python
@frappe.whitelist()
def get_call_status(action_id):
    """
    Get status of Click-to-Dial call.
    
    Args:
        action_id (str): From initiate_call response
    
    Returns:
        dict: {
            "status": "ringing" | "answered" | "busy" | "failed",
            "channel": "PJSIP/1001-xxx",
            "duration": 0
        }
    """
```

---

## 🔐 Updated Permission Notes

### Role-Based Access
| API Module | Required Role |
|------------|---------------|
| WebRTC | System User |
| AI | Arrowz User |
| CRM | Sales User or Arrowz User |
| Call Log | Arrowz User |
| Presence | System User |
| Transfer | Arrowz User (Blind: Arrowz Supervisor) |
| Recordings | Arrowz User + Call Log Read |
| SMS | Arrowz User |
| FreePBX | Arrowz Admin |
| Click-to-Dial | Arrowz User |

---

*Next: See `04-FRONTEND-GUIDE.md` for JavaScript specifications*

