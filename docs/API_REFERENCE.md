# Arrowz API Reference

> **Last Updated:** February 17, 2026  
> **Version:** 1.0.0  
> **Base URL:** `/api/method/`

---

## Authentication

All API endpoints require Frappe session authentication unless marked as `[Guest]`.

```bash
# Cookie-based authentication
curl -X POST "https://your-site.com/api/method/frappe.auth.get_logged_user" \
  -H "Cookie: sid=your-session-id"

# Token-based authentication
curl -X POST "https://your-site.com/api/method/endpoint" \
  -H "Authorization: token api_key:api_secret"
```

---

## WebRTC / Softphone APIs

### Get SIP Credentials
```
POST /api/method/arrowz.api.webrtc.get_sip_credentials
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| extension | string | No | Specific extension (defaults to user's primary) |

**Response:**
```json
{
  "success": true,
  "data": {
    "extension": "1001",
    "username": "1001",
    "password": "secure_password",
    "domain": "pbx.example.com",
    "websocket_url": "wss://pbx.example.com:8089/ws",
    "stun_server": "stun:stun.l.google.com:19302",
    "turn_server": "turn:turn.example.com:3478",
    "turn_username": "user",
    "turn_password": "pass"
  }
}
```

---

### Make Call
```
POST /api/method/arrowz.api.webrtc.make_call
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| extension | string | Yes | Caller extension |
| phone_number | string | Yes | Number to call |
| party_type | string | No | Lead, Contact, Customer, etc. |
| party | string | No | Document name for linking |

**Response:**
```json
{
  "success": true,
  "call_id": "CALL-2026-00001",
  "message": "Call initiated"
}
```

---

### End Call
```
POST /api/method/arrowz.api.webrtc.end_call
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| call_id | string | Yes | Call log name |

---

### Hold Call
```
POST /api/method/arrowz.api.webrtc.hold_call
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| call_id | string | Yes | Call log name |
| hold | boolean | Yes | true=hold, false=resume |

---

### Transfer Call
```
POST /api/method/arrowz.api.webrtc.transfer_call
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| call_id | string | Yes | Call log name |
| target | string | Yes | Target extension or number |
| transfer_type | string | No | "blind" or "attended" (default: blind) |

---

### Send DTMF
```
POST /api/method/arrowz.api.webrtc.send_dtmf
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| call_id | string | Yes | Call log name |
| digit | string | Yes | DTMF digit (0-9, *, #) |

---

## SMS APIs

### Send SMS
```
POST /api/method/arrowz.api.sms.send_sms
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| to | string | Yes | Recipient phone number |
| message | string | Yes | Message content |
| provider | string | No | Provider name (uses default) |
| party_type | string | No | Link to DocType |
| party | string | No | Link to document |

**Response:**
```json
{
  "success": true,
  "message_id": "SMS-2026-00001",
  "status": "sent"
}
```

---

### Get SMS History
```
POST /api/method/arrowz.api.sms.get_sms_history
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| phone | string | No | Phone number filter |
| party_type | string | No | DocType filter |
| party | string | No | Document filter |
| limit | int | No | Max results (default: 20) |

---

## Analytics APIs

### Get Dashboard Data
```
POST /api/method/arrowz.api.analytics.get_dashboard_data
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| date_from | string | No | Start date (YYYY-MM-DD) |
| date_to | string | No | End date (YYYY-MM-DD) |

**Response:**
```json
{
  "total_calls": 150,
  "answered_calls": 120,
  "missed_calls": 25,
  "abandoned_calls": 5,
  "avg_duration": 180,
  "avg_wait_time": 15,
  "sla_percentage": 85.5
}
```

---

### Get Call Trend
```
POST /api/method/arrowz.api.analytics.get_call_trend
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| days | int | No | Number of days (default: 7) |

**Response:**
```json
{
  "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
  "datasets": [
    {"label": "Inbound", "data": [45, 52, 48, 55, 42]},
    {"label": "Outbound", "data": [30, 28, 35, 32, 29]}
  ]
}
```

---

### Get Agent Metrics
```
POST /api/method/arrowz.api.analytics.get_agent_metrics
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| agent | string | No | Specific agent (default: all) |
| date_from | string | No | Start date |
| date_to | string | No | End date |

---

### Get Hourly Distribution
```
POST /api/method/arrowz.api.analytics.get_hourly_distribution
```

**Response:**
```json
{
  "hours": [0, 1, 2, ..., 23],
  "calls": [2, 1, 0, 0, 0, 5, 15, 45, 60, 55, ...]
}
```

---

## Agent APIs

### Get Agent Status
```
POST /api/method/arrowz.api.agent.get_status
```

**Response:**
```json
{
  "user": "john@example.com",
  "extension": "1001",
  "status": "available",
  "on_call": false,
  "queue_count": 3
}
```

---

### Set Agent Status
```
POST /api/method/arrowz.api.agent.set_status
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| status | string | Yes | available, busy, away, dnd |

---

### Agent Heartbeat
```
POST /api/method/arrowz.api.agent.heartbeat
```

Keep-alive for agent presence tracking. Should be called every 60 seconds.

---

## Wallboard APIs

### Get Live Calls
```
POST /api/method/arrowz.api.wallboard.get_live_calls
```

**Response:**
```json
{
  "calls": [
    {
      "call_id": "CALL-2026-00001",
      "extension": "1001",
      "phone_number": "+1234567890",
      "direction": "inbound",
      "status": "in_progress",
      "duration": 125,
      "agent": "John Doe"
    }
  ]
}
```

---

### Get All Agent Status
```
POST /api/method/arrowz.api.wallboard.get_agent_status
```

---

### Get Queue Metrics
```
POST /api/method/arrowz.api.wallboard.get_queue_metrics
```

---

## Omni-Channel APIs

### Send Message
```
POST /api/method/arrowz.api.omni.send_message
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session | string | Yes | Session name |
| message | string | Yes | Message content |
| message_type | string | No | text, image, document |
| media_url | string | No | URL for media messages |

---

### Get Session Messages
```
POST /api/method/arrowz.api.omni.get_messages
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session | string | Yes | Session name |
| limit | int | No | Max messages (default: 50) |
| offset | int | No | Pagination offset |

---

## Meeting APIs

### Create Meeting
```
POST /api/method/arrowz.api.meeting.create_room
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| name | string | Yes | Room name |
| room_type | string | No | conference, webinar, interview |
| scheduled_start | datetime | No | Schedule time |
| max_participants | int | No | Max users |

**Response:**
```json
{
  "success": true,
  "room": "ROOM-2026-00001",
  "join_url": "https://meetings.example.com/join/abc123"
}
```

---

### Get Join URL
```
POST /api/method/arrowz.api.meeting.get_join_url
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| room | string | Yes | Room name |

---

## Webhook Endpoints

### WhatsApp Webhook [Guest]
```
POST /api/method/arrowz.integrations.whatsapp.webhook
GET  /api/method/arrowz.integrations.whatsapp.webhook  # Verification
```

---

### Telegram Webhook [Guest]
```
POST /api/method/arrowz.integrations.telegram.webhook
```

---

### SMS Delivery Report [Guest]
```
POST /api/method/arrowz.api.sms.delivery_webhook
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 401 | Unauthorized - Invalid session |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 400 | Bad Request - Invalid parameters |
| 500 | Server Error - Internal error |

---

## Rate Limits

| Endpoint Type | Limit |
|---------------|-------|
| Standard API | 100/minute |
| Webhooks | 1000/minute |
| Analytics | 10/minute |

---

*For detailed examples, see the integration guides.*
