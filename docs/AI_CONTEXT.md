# Arrowz - AI Context Document

> **Purpose:** Provide complete context for AI models to understand the Arrowz application without reading all source code.  
> **Last Updated:** February 17, 2026  
> **Version:** 1.0.0

---

## 📌 Quick Reference

```
App Name:        Arrowz
Type:            Frappe Framework Application
Purpose:         Enterprise VoIP & Unified Communications
License:         MIT
Python:          3.11+
Framework:       Frappe (ERPNext compatible)
Frontend:        Vanilla JS + JsSIP (WebRTC)
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRAPPE FRAMEWORK                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Arrowz    │  │   ERPNext   │  │   Other Frappe Apps     │  │
│  │   (VoIP)    │  │   (CRM)     │  │   (HRMS, LMS, etc.)     │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                      │                │
│         └────────────────┼──────────────────────┘                │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    MariaDB Database                          ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Redis Cache/Queue                         ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL INTEGRATIONS                         │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│  FreePBX/    │ OpenMeetings │  WhatsApp    │    Telegram        │
│  Asterisk    │   Server     │  Cloud API   │    Bot API         │
└──────────────┴──────────────┴──────────────┴────────────────────┘
```

---

## 📁 Directory Structure

```
arrowz/
├── arrowz/                          # Main Python module
│   ├── arrowz/                      # App module (same name convention)
│   │   ├── doctype/                 # 17 DocTypes
│   │   │   ├── az_call_log/         # Call detail records
│   │   │   ├── az_extension/        # User extensions
│   │   │   ├── az_server_config/    # PBX server config
│   │   │   ├── az_conversation_session/  # Chat sessions
│   │   │   ├── az_meeting_room/     # Video rooms
│   │   │   └── ...
│   │   ├── page/                    # Desk pages
│   │   │   ├── arrowz_dashboard/
│   │   │   ├── arrowz_wallboard/
│   │   │   └── ...
│   │   └── workspace/               # Workspace definition
│   ├── api/                         # API modules
│   │   ├── webrtc.py               # Softphone APIs
│   │   ├── sms.py                  # SMS APIs
│   │   ├── analytics.py            # Analytics APIs
│   │   ├── agent.py                # Agent status APIs
│   │   └── wallboard.py            # Wallboard APIs
│   ├── integrations/                # External integrations
│   │   ├── freepbx/
│   │   ├── openmeetings/
│   │   ├── whatsapp/
│   │   └── telegram/
│   ├── public/                      # Frontend assets
│   │   ├── js/
│   │   │   ├── arrowz.js           # Core namespace
│   │   │   ├── softphone_v2.js     # WebRTC softphone (2365 lines)
│   │   │   ├── phone_actions.js    # Click-to-call
│   │   │   ├── screen_pop.js       # Incoming call popup
│   │   │   └── omni_panel.js       # Communication panel
│   │   └── css/
│   │       ├── arrowz.css
│   │       └── softphone.css
│   ├── hooks.py                     # App configuration
│   ├── freepbx_token.py            # OAuth2 token manager
│   ├── pbx_monitor.py              # SSH-based PBX monitor
│   └── tasks.py                    # Background tasks
├── docs/                            # Documentation
│   ├── FEATURES_EN.md              # Features (English)
│   ├── FEATURES_AR.md              # Features (Arabic)
│   ├── ROADMAP.md                  # Roadmap & proposals
│   └── API_REFERENCE.md            # API documentation
└── scripts/                         # Utility scripts
```

---

## 🗃️ DocType Summary

### Configuration DocTypes
| DocType | Table | Purpose |
|---------|-------|---------|
| `Arrowz Settings` | `tabArrowz Settings` | Global settings (Single) |
| `AZ Server Config` | `tabAZ Server Config` | PBX/Meeting servers |
| `AZ Extension` | `tabAZ Extension` | User SIP extensions |

### Call Management DocTypes
| DocType | Table | Purpose |
|---------|-------|---------|
| `AZ Call Log` | `tabAZ Call Log` | Call detail records |
| `AZ Call Transfer Log` | `tabAZ Call Transfer Log` | Transfer history |

### Routing DocTypes
| DocType | Table | Purpose |
|---------|-------|---------|
| `AZ Trunk` | `tabAZ Trunk` | SIP trunks |
| `AZ Inbound Route` | `tabAZ Inbound Route` | Inbound routing |
| `AZ Outbound Route` | `tabAZ Outbound Route` | Outbound routing |

### Omni-Channel DocTypes
| DocType | Table | Purpose |
|---------|-------|---------|
| `AZ Omni Provider` | `tabAZ Omni Provider` | Channel providers |
| `AZ Omni Channel` | `tabAZ Omni Channel` | Channel instances |
| `AZ Conversation Session` | `tabAZ Conversation Session` | Chat threads |
| `AZ Conversation Message` | `tabAZ Conversation Message` | Messages (child) |

### SMS DocTypes
| DocType | Table | Purpose |
|---------|-------|---------|
| `AZ SMS Provider` | `tabAZ SMS Provider` | SMS gateways |
| `AZ SMS Message` | `tabAZ SMS Message` | SMS records |

### Meeting DocTypes
| DocType | Table | Purpose |
|---------|-------|---------|
| `AZ Meeting Room` | `tabAZ Meeting Room` | Video rooms |
| `AZ Meeting Participant` | `tabAZ Meeting Participant` | Participants (child) |
| `AZ Meeting Recording` | `tabAZ Meeting Recording` | Recordings (child) |

---

## 🔌 API Patterns

### Authentication
All APIs use Frappe's session authentication. Guest endpoints use `@frappe.whitelist(allow_guest=True)`.

### Common Response Format
```python
{
    "success": True/False,
    "message": "Description",
    "data": {...}  # or []
}
```

### Key API Modules

#### `api.webrtc` - Softphone APIs
```python
get_sip_credentials()     # Get SIP config for JsSIP
make_call(extension, number)
end_call(call_id)
hold_call(call_id)
transfer_call(call_id, target, type)
send_dtmf(call_id, digit)
```

#### `api.sms` - SMS APIs
```python
send_sms(to, message, provider=None)
get_sms_history(phone=None, party_type=None, party=None)
```

#### `api.analytics` - Analytics APIs
```python
get_dashboard_data(date_range)
get_call_trend(days=7)
get_agent_metrics(agent=None)
get_hourly_distribution()
```

---

## 🔄 Background Tasks

### Scheduler Events (hooks.py)
```python
scheduler_events = {
    "cron": {
        "*/5 * * * *": ["arrowz.tasks.check_agent_presence"],
        "*/10 * * * *": ["arrowz.tasks.cleanup_stuck_calls"],
        "*/15 * * * *": ["arrowz.tasks.check_session_windows"],
    },
    "hourly": [
        "arrowz.tasks.sync_extension_status",
        "arrowz.tasks.sync_meeting_rooms",
    ],
    "daily": [
        "arrowz.tasks.cleanup_old_presence",
        "arrowz.tasks.send_daily_report",
        "arrowz.tasks.archive_old_sessions",
        "arrowz.tasks.cleanup_temp_rooms",
    ],
    "weekly": [
        "arrowz.tasks.generate_weekly_analytics",
        "arrowz.tasks.generate_omni_report",
    ]
}
```

---

## 📡 Real-Time Events

### Socket.IO Events
```javascript
// Call events
frappe.realtime.on("arrowz_incoming_call", callback)
frappe.realtime.on("arrowz_call_started", callback)
frappe.realtime.on("arrowz_call_ended", callback)

// Message events
frappe.realtime.on("new_message", callback)
frappe.realtime.on("message_status", callback)

// Presence events
frappe.realtime.on("arrowz_presence_update", callback)
```

### Publishing Events (Python)
```python
frappe.publish_realtime(
    "arrowz_incoming_call",
    {"caller": "1001", "callee": "1002"},
    user=frappe.session.user
)
```

---

## 🔗 External Integrations

### FreePBX Integration
- **GraphQL API**: Extension CRUD, user management
- **AMI**: Real-time call events
- **SSH**: Direct configuration, log access
- **OAuth2**: Token management with auto-refresh

### OpenMeetings Integration
- **REST API**: Room management, recordings
- **Secure Hash**: User authentication

### WhatsApp Cloud API
- **Webhook**: Message receive, status updates
- **REST API**: Send messages, templates

### Telegram Bot API
- **Webhook**: Message receive
- **REST API**: Send messages, media

---

## 🛠️ Key Configuration

### Server Config Fields (`AZ Server Config`)
```
server_name          # Unique identifier
server_type          # freepbx, asterisk, openmeetings
host                 # Server hostname
port                 # Server port
websocket_url        # WSS URL for WebRTC
sip_domain           # SIP domain
graphql_url          # GraphQL endpoint
graphql_client_id    # OAuth2 client ID
graphql_client_secret # OAuth2 secret (encrypted)
ssh_host             # SSH hostname
ssh_username         # SSH user
ssh_password         # SSH password (encrypted)
```

### Extension Fields (`AZ Extension`)
```
extension            # Extension number (e.g., 1001)
user                 # Linked Frappe User
display_name         # Caller ID name
sip_password         # SIP password (encrypted)
extension_type       # SIP, WebRTC, Both
server               # Link to AZ Server Config
sync_status          # Synced, Not Synced, Failed
```

---

## 🧪 Testing Approach

### Unit Tests
- DocType validation
- API function tests
- Integration mocks

### Integration Tests
- FreePBX sync
- WebSocket events
- Webhook handling

### E2E Tests
- Softphone registration
- Call flow
- Message sending

---

## 📊 Database Queries

### Common Queries
```python
# Get active extensions for user
extensions = frappe.get_all("AZ Extension",
    filters={"user": frappe.session.user, "is_active": 1},
    fields=["extension", "server", "display_name"]
)

# Get today's calls
calls = frappe.get_all("AZ Call Log",
    filters={"call_date": today()},
    fields=["*"]
)

# Get conversation sessions
sessions = frappe.get_all("AZ Conversation Session",
    filters={"status": "Active"},
    fields=["name", "channel", "contact_phone"]
)
```

---

## 🔐 Security Model

### Roles
- **Arrowz User**: Basic calling, messaging
- **Arrowz Agent**: Queue management, reports
- **Arrowz Manager**: All features, configuration
- **System Manager**: Full access

### Permissions
- DocType level: Read, Write, Create, Delete
- Field level: Password fields encrypted
- API level: Role checks in whitelisted methods

---

## 🚀 Deployment

### Development
```bash
bench start  # Port 8001 (configured)
```

### Production
- Gunicorn workers: 17 (configured)
- Socket.IO: Port 9001
- Redis: Cache + Queue
- Supervisor/Systemd managed

---

## 📝 Coding Conventions

### Python
- PEP 8 style
- Type hints encouraged
- Docstrings for public methods

### JavaScript
- `arrowz.*` namespace for all code
- ES6+ syntax
- JSDoc comments

### File Naming
- Snake_case for Python files
- Kebab-case for JS/CSS files
- DocTypes use Title Case with AZ prefix

---

## 🔍 Troubleshooting Quick Reference

| Issue | Cause | Solution |
|-------|-------|----------|
| WebRTC 30s delay | ICE negotiation | Use TURN server |
| 401 GraphQL | Invalid token | Check credentials, use SSH fallback |
| 502 Bad Gateway | Bench not running | `bench start` |
| No incoming calls | Extension not registered | Check WebSocket URL |

---

*This document provides complete context for AI models to understand and work with the Arrowz application.*
