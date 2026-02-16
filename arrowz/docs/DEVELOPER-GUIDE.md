# Arrowz Developer Guide
## Technical Documentation for Developers

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Getting Started](#getting-started)
3. [API Reference](#api-reference)
4. [DocType Reference](#doctype-reference)
5. [Frontend Development](#frontend-development)
6. [Real-time Events](#real-time-events)
7. [Testing](#testing)
8. [Deployment](#deployment)

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Softphone│  │ Wallboard│  │ Analytics│  │ Screen Pop │  │
│  │  (JsSIP) │  │ (Charts) │  │ (ECharts)│  │   (AJAX)   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘  │
│       │             │             │              │          │
├───────┴─────────────┴─────────────┴──────────────┴──────────┤
│                     Frappe Framework                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    Arrowz API                         │   │
│  │  /api/method/arrowz.api.{module}.{function}          │   │
│  └────────────────────────┬─────────────────────────────┘   │
│                           │                                  │
│  ┌────────────────────────┴─────────────────────────────┐   │
│  │                    DocTypes                           │   │
│  │  AZ Call Log │ AZ Extension │ AZ Server Config │ ... │   │
│  └──────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────┤
│                    External Services                         │
│  ┌──────────────┐  ┌────────────┐  ┌──────────────────┐    │
│  │   FreePBX    │  │   OpenAI   │  │   SMS Provider   │    │
│  │ (AMI/GraphQL)│  │   (GPT-4)  │  │ (Twilio/Custom)  │    │
│  └──────────────┘  └────────────┘  └──────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
arrowz/
├── arrowz/
│   ├── __init__.py
│   ├── hooks.py                    # App configuration
│   ├── modules.txt                 # Module definition
│   │
│   ├── arrowz/                     # Main module
│   │   ├── doctype/                # All DocTypes
│   │   │   ├── arrowz_settings/
│   │   │   ├── az_server_config/
│   │   │   ├── az_extension/
│   │   │   ├── az_call_log/
│   │   │   ├── az_call_transfer_log/
│   │   │   ├── az_sms_provider/
│   │   │   └── az_sms_message/
│   │   │
│   │   ├── page/                   # Custom pages
│   │   │   ├── arrowz_agent_dashboard/
│   │   │   ├── arrowz_wallboard/
│   │   │   └── arrowz_analytics/
│   │   │
│   │   └── workspace/              # Workspace definitions
│   │       └── arrowz_workspace.json
│   │
│   ├── api/                        # Backend API
│   │   ├── __init__.py
│   │   ├── webrtc.py
│   │   ├── wallboard.py
│   │   ├── agent.py
│   │   ├── analytics.py
│   │   ├── recording.py
│   │   ├── sms.py
│   │   └── screenpop.py
│   │
│   ├── public/                     # Frontend assets
│   │   ├── js/
│   │   │   ├── arrowz.js
│   │   │   ├── softphone.js
│   │   │   └── screen_pop.js
│   │   └── css/
│   │       ├── arrowz.css
│   │       ├── softphone.css
│   │       └── screen_pop.css
│   │
│   └── docs/                       # Documentation
│       ├── USER-GUIDE-AGENT.md
│       ├── USER-GUIDE-MANAGER.md
│       ├── USER-GUIDE-ADMIN.md
│       └── DEVELOPER-GUIDE.md
│
├── pyproject.toml                  # Python dependencies
└── package.json                    # JS dependencies (if any)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Frappe Framework v15+
- MariaDB 10.6+
- Redis 7+

### Installation

```bash
# Clone into apps directory
cd frappe-bench/apps
git clone https://github.com/arrowz/arrowz.git

# Install app
bench --site your-site install-app arrowz

# Run migrations
bench --site your-site migrate

# Build assets
bench build --app arrowz
```

### Development Setup

```bash
# Start bench with hot reload
bench start

# Watch for frontend changes
bench watch

# Run in developer mode
bench set-config -g developer_mode 1
```

---

## 🔌 API Reference

### WebRTC API (`arrowz.api.webrtc`)

#### Get WebRTC Configuration
```python
@frappe.whitelist()
def get_webrtc_config() -> dict
```

**Response:**
```json
{
  "sip_uri": "sip:101@pbx.example.com",
  "sip_password": "****",
  "websocket_url": "wss://pbx.example.com:8089/ws",
  "stun_servers": ["stun:stun.l.google.com:19302"],
  "turn_servers": [],
  "display_name": "John Doe"
}
```

#### Start Call
```python
@frappe.whitelist()
def start_call(
    destination: str,
    call_type: str = "voice"
) -> dict
```

#### End Call
```python
@frappe.whitelist()
def end_call(call_id: str) -> dict
```

#### Transfer Call
```python
@frappe.whitelist()
def transfer_call(
    call_id: str,
    target: str,
    transfer_type: str = "blind"  # blind | attended
) -> dict
```

---

### Wallboard API (`arrowz.api.wallboard`)

#### Get Live Data
```python
@frappe.whitelist()
def get_wallboard_data() -> dict
```

**Response:**
```json
{
  "active_calls": 12,
  "calls_in_queue": 3,
  "avg_wait_time": 45,
  "service_level": 87,
  "agents": [
    {
      "name": "Ahmed",
      "extension": "101",
      "status": "on_call",
      "call_duration": 154
    }
  ],
  "calls": [
    {
      "id": "call-123",
      "caller_id": "0501234567",
      "agent": "Ahmed",
      "direction": "inbound",
      "duration": 154
    }
  ]
}
```

---

### Analytics API (`arrowz.api.analytics`)

#### Get Call Volume
```python
@frappe.whitelist()
def get_call_volume(
    from_date: str,
    to_date: str,
    group_by: str = "day"  # day | week | month
) -> dict
```

#### Get Agent Performance
```python
@frappe.whitelist()
def get_agent_performance(
    from_date: str,
    to_date: str,
    agent: str = None
) -> list
```

---

### SMS API (`arrowz.api.sms`)

#### Send SMS
```python
@frappe.whitelist()
def send_sms(
    to_number: str,
    message: str,
    party_type: str = None,
    party: str = None
) -> dict
```

#### Get Conversation
```python
@frappe.whitelist()
def get_sms_conversation(
    phone_number: str,
    limit: int = 50
) -> list
```

---

## 🔐 FreePBX OAuth Integration

Arrowz uses OAuth2 Client Credentials flow for secure communication with FreePBX GraphQL API.

### Token Management

The `freepbx_token.py` module handles automatic token management:

```python
from arrowz.freepbx_token import execute_graphql, get_access_token

# Get current access token (auto-refreshes if needed)
token = get_access_token("My Server Config")

# Execute GraphQL query with automatic authentication
response = execute_graphql(
    server_name="My Server Config",
    query="""
        query listExtensions {
            listExtensions {
                status
                extension { id name }
            }
        }
    """,
    variables={}
)
```

### Key Features

- **Automatic Token Refresh**: Tokens are refreshed 5 minutes before expiry
- **Redis Caching**: Tokens are cached in Redis for performance
- **SSL Flexibility**: `verify_ssl` field allows self-signed certificates

### OAuth Flow

1. User configures **Client ID** and **Client Secret** in AZ Server Config
2. System automatically fetches access token from FreePBX
3. Token is cached in Redis with TTL matching token expiry
4. On API call, system checks if token is valid or needs refresh
5. All GraphQL calls use the cached token automatically

### Configuration Fields (AZ Server Config)

| Field | Purpose |
|-------|---------|
| `graphql_client_id` | OAuth2 Client ID |
| `graphql_client_secret` | OAuth2 Client Secret (Password field) |
| `verify_ssl` | Whether to verify SSL certificates (default: No) |
| `token_status` | Read-only: Current token status |
| `token_expires_at` | Read-only: Token expiry timestamp |

### Creating OAuth App in FreePBX

1. Go to **Admin → API → Applications**
2. Create new application with type **Machine-to-Machine**
3. Grant required scopes (gql for GraphQL access)
4. Copy Client ID and Client Secret to AZ Server Config

---

## 📄 DocType Reference

### AZ Call Log

**Key Fields:**
| Field | Type | Description |
|-------|------|-------------|
| call_id | Data | Unique call identifier |
| caller_id | Data | Caller phone number |
| callee_id | Data | Destination number |
| direction | Select | inbound/outbound |
| status | Select | completed/missed/voicemail |
| call_datetime | Datetime | Start time |
| duration_seconds | Int | Duration in seconds |
| agent | Link (User) | Assigned agent |
| recording_url | Data | Path to recording |
| party_type | Link (DocType) | Linked party type |
| party | Dynamic Link | Linked party |

**Controller Methods:**
```python
class AZCallLog(Document):
    def validate(self):
        self.calculate_duration()
    
    def after_insert(self):
        self.link_crm_record()
    
    def calculate_duration(self):
        # Auto-calculate if end_time set
        pass
    
    def link_crm_record(self):
        # Search and link CRM party
        pass
```

### AZ Extension

**Key Fields:**
| Field | Type | Description |
|-------|------|-------------|
| user | Link (User) | Associated user |
| extension | Data | Extension number |
| sip_username | Data | SIP username |
| sip_password | Password | SIP password |
| server_config | Link | PBX server |
| websocket_url | Data | WebSocket URL |

**Controller Methods:**
```python
class AZExtension(Document):
    def get_webrtc_config(self) -> dict:
        """Return WebRTC configuration"""
        pass
```

---

## 🎨 Frontend Development

### Softphone Component

```javascript
// Initialize softphone
arrowz.softphone = new ArrowzSoftphone();

// Event listeners
arrowz.softphone.on('registered', () => {
    console.log('SIP Registered');
});

arrowz.softphone.on('incoming', (call) => {
    // Handle incoming call
});

arrowz.softphone.on('connected', (call) => {
    // Call connected
});

// Make a call
arrowz.softphone.makeCall('0501234567');

// End current call
arrowz.softphone.hangup();
```

### Screen Pop Integration

```javascript
// Trigger screen pop manually
arrowz.screenpop.trigger('0501234567');

// Listen for screen pop events
frappe.realtime.on('arrowz_incoming_call', (data) => {
    arrowz.screenpop.show(data.caller_id, data.call_id, 'incoming');
});
```

### Adding Custom Actions to Forms

```javascript
// In doctype JS file
frappe.ui.form.on('Customer', {
    refresh(frm) {
        if (frm.doc.mobile_no) {
            // Add call button
            frm.add_custom_button(__('Call'), () => {
                arrowz.call.dial(frm.doc.mobile_no);
            }, __('Actions'));
            
            // Add SMS button
            frm.add_custom_button(__('SMS'), () => {
                arrowz.sms.showSendDialog(
                    frm.doc.mobile_no,
                    'Customer',
                    frm.doc.name
                );
            }, __('Actions'));
        }
    }
});
```

---

## ⚡ Real-time Events

### Server to Client Events

```python
# Publish event from server
frappe.publish_realtime(
    event='arrowz_incoming_call',
    message={
        'caller_id': '0501234567',
        'call_id': 'call-123',
        'extension': '101'
    },
    user=target_user
)
```

### Available Events

| Event | Description | Payload |
|-------|-------------|---------|
| `arrowz_incoming_call` | New incoming call | caller_id, call_id |
| `arrowz_call_ended` | Call ended | call_id, duration |
| `arrowz_call_connected` | Call connected | call_id, remote_number |
| `arrowz_agent_status_changed` | Agent status change | user, status |
| `arrowz_queue_update` | Queue stats update | queue_data |
| `arrowz_sms_received` | New SMS received | from, content |

### Client-side Handling

```javascript
// Subscribe to events
frappe.realtime.on('arrowz_incoming_call', (data) => {
    console.log('Incoming call from:', data.caller_id);
    
    // Show notification
    arrowz.utils.showNotification('Incoming Call', {
        body: data.caller_id
    });
    
    // Play ringtone
    arrowz.utils.playSound('ring');
});
```

---

## 🧪 Testing

### Running Tests

```bash
# All tests
bench --site test_site run-tests --app arrowz

# Specific module
bench --site test_site run-tests --module arrowz.arrowz.doctype.az_call_log

# With coverage
bench --site test_site run-tests --app arrowz --coverage
```

### Writing Tests

```python
# arrowz/arrowz/doctype/az_call_log/test_az_call_log.py

import frappe
from frappe.tests import IntegrationTestCase

class TestAZCallLog(IntegrationTestCase):
    def setUp(self):
        self.call_log = frappe.get_doc({
            "doctype": "AZ Call Log",
            "call_id": "test-123",
            "caller_id": "0501234567",
            "direction": "inbound",
            "status": "completed"
        }).insert()
    
    def test_duration_calculation(self):
        self.call_log.call_datetime = "2024-01-01 10:00:00"
        self.call_log.end_datetime = "2024-01-01 10:05:30"
        self.call_log.calculate_duration()
        
        self.assertEqual(self.call_log.duration_seconds, 330)
    
    def tearDown(self):
        frappe.delete_doc("AZ Call Log", self.call_log.name)
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Disable developer mode
- [ ] Set up SSL certificates
- [ ] Configure Redis for production
- [ ] Set up backup schedule
- [ ] Configure STUN/TURN servers
- [ ] Set up monitoring

### Environment Variables

```bash
# .env or site_config.json
OPENAI_API_KEY=sk-xxxxx
SMS_PROVIDER_API_KEY=xxxxx
RECORDING_STORAGE_PATH=/var/recordings
```

### Nginx Configuration for WebSocket

```nginx
location /socket.io {
    proxy_pass http://127.0.0.1:9000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}

location /ws {
    proxy_pass http://pbx-server:8089;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

## 📚 Additional Resources

- [Frappe Framework Documentation](https://frappeframework.com/docs)
- [JsSIP Documentation](https://jssip.net/documentation)
- [FreePBX GraphQL API](https://wiki.freepbx.org/display/FPG/GraphQL+API)
- [WebRTC Guide](https://webrtc.org/getting-started/overview)

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Create Pull Request

---

**Happy Coding! 💻**
