# Arrowz - Integration Map

ge

## System Integration Overview

```
                              ┌─────────────────────────────────────────┐
                              │              ARROWZ                     │
                              │         (Frappe App)                    │
                              └────────────────┬────────────────────────┘
                                               │
              ┌────────────────────────────────┼────────────────────────────────┐
              │                                │                                │
              ▼                                ▼                                ▼
┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────────┐
│    TELEPHONY LAYER      │   │   MESSAGING LAYER       │   │    VIDEO LAYER          │
├─────────────────────────┤   ├─────────────────────────┤   ├─────────────────────────┤
│                         │   │                         │   │                         │
│   ┌─────────────────┐   │   │   ┌─────────────────┐   │   │   ┌─────────────────┐   │
│   │   FreePBX       │   │   │   │   WhatsApp      │   │   │   │  OpenMeetings   │   │
│   │   (Asterisk)    │   │   │   │   Cloud API     │   │   │   │    Server       │   │
│   └────────┬────────┘   │   │   └────────┬────────┘   │   │   └────────┬────────┘   │
│            │            │   │            │            │   │            │            │
│   Protocols:            │   │   Protocols:            │   │   Protocols:            │
│   • WebSocket (WSS)     │   │   • REST (HTTPS)        │   │   • REST (HTTPS)        │
│   • AMI (TCP)           │   │   • Webhooks            │   │                         │
│   • SIP/RTP             │   │                         │   │                         │
│                         │   │   ┌─────────────────┐   │   │                         │
│                         │   │   │   Telegram      │   │   │                         │
│                         │   │   │   Bot API       │   │   │                         │
│                         │   │   └────────┬────────┘   │   │                         │
│                         │   │            │            │   │                         │
│                         │   │   Protocols:            │   │                         │
│                         │   │   • REST (HTTPS)        │   │                         │
│                         │   │   • Webhooks            │   │                         │
└─────────────────────────┘   └─────────────────────────┘   └─────────────────────────┘
```

## 1. FreePBX / Asterisk Integration

### Connection Types

#### A. WebSocket (WebRTC Signaling)
- **URL Format**: `wss://pbx.example.com:8089/ws`
- **Purpose**: SIP signaling for browser-based calls
- **Library**: JsSIP (JavaScript)
- **Configuration**: `AZ Server Config.websocket_url`

```javascript
// Example JsSIP connection
const socket = new JsSIP.WebSocketInterface('wss://pbx.example.com:8089/ws');
const ua = new JsSIP.UA({
    sockets: [socket],
    uri: 'sip:1001@pbx.example.com',
    password: 'sippassword'
});
```

#### B. AMI (Asterisk Manager Interface)
- **Port**: 5038 (default)
- **Purpose**: Event monitoring, call origination
- **Protocol**: TCP text-based
- **Configuration**: `AZ Server Config.ami_port`

```python
# Example AMI events we process
# - Newchannel: Call started
# - Hangup: Call ended
# - Bridge: Call connected
# - Hold: Call on hold
```

#### C. Local PBX Mount (`/mnt/pbx`)
- **Purpose**: Direct config/log reading without SSH
- **Type**: Docker volume mount (read-only)
- **Module**: `arrowz.local_pbx_monitor`

```python
from arrowz.local_pbx_monitor import LocalPBXMonitor

monitor = LocalPBXMonitor()
monitor.diagnose_webrtc("1001")    # Full WebRTC check
monitor.get_pjsip_config()        # Read all PJSIP files
monitor.get_extension_config("1001")  # Check extension
monitor.search_logs("ICE")        # Search logs
```

Available paths (see `arrowz.dev_constants`):
| Path | Content |
|------|---------|
| `/mnt/pbx/etc/asterisk/` | All Asterisk config files |
| `/mnt/pbx/logs/asterisk/` | Logs (full, queue, security) |
| `/mnt/pbx/db/` | Database SQL dumps |
| `/mnt/pbx/recordings/` | Call recordings |
| `/mnt/pbx/voicemail/` | Voicemail storage |

### Data Flow
```
Browser ──JsSIP──> WebSocket ──> Asterisk
                                    │
                                    ├── SIP Registration
                                    ├── INVITE (make call)
                                    ├── BYE (end call)
                                    └── RTP (audio/video)
```

### Required FreePBX Modules
- WebRTC (Asterisk WebSocket)
- PJSIP (SIP transport)
- Core PBX
- Manager (AMI)

---

## 2. WhatsApp Integration

### Meta Cloud API
- **API Version**: v17.0+
- **Base URL**: `https://graph.facebook.com`
- **Authentication**: Bearer token (access_token)

### Configuration Required
| Setting | Source | Location in Arrowz |
|---------|--------|-------------------|
| Phone Number ID | Meta Business | `AZ Omni Provider.phone_number_id` |
| Access Token | Meta Business | `AZ Omni Provider.access_token` |
| Business Account ID | Meta Business | `AZ Omni Provider.business_account_id` |
| Webhook Verify Token | Your choice | `AZ Omni Provider.webhook_secret` |

### Webhook Setup
```
Webhook URL: https://yoursite.com/api/method/arrowz.api.webhooks.whatsapp_cloud_webhook
Events to Subscribe:
- messages
- message_delivery
- message_read
```

### API Endpoints Used
```python
# Send text message
POST /v17.0/{phone_number_id}/messages
{
    "messaging_product": "whatsapp",
    "to": "1234567890",
    "type": "text",
    "text": {"body": "Hello"}
}

# Send template message
POST /v17.0/{phone_number_id}/messages
{
    "messaging_product": "whatsapp",
    "to": "1234567890",
    "type": "template",
    "template": {
        "name": "hello_world",
        "language": {"code": "en_US"}
    }
}

# Download media
GET /v17.0/{media_id}
```

### 24-Hour Window Rules
- Initiated by customer message
- Free-form messaging allowed within 24h
- After 24h, only templates allowed
- Tracked in `AZ Conversation Session.window_expires`

---

## 3. Telegram Integration

### Bot API
- **Base URL**: `https://api.telegram.org/bot{token}`
- **Authentication**: Bot token in URL

### Configuration Required
| Setting | Source | Location in Arrowz |
|---------|--------|-------------------|
| Bot Token | BotFather | `AZ Omni Provider.bot_token` |
| Webhook Secret | Your choice | `AZ Omni Provider.webhook_secret` |

### Webhook Setup
```python
# Set webhook
POST /bot{token}/setWebhook
{
    "url": "https://yoursite.com/api/method/arrowz.api.webhooks.telegram_webhook",
    "secret_token": "your_secret"
}
```

### API Endpoints Used
```python
# Send message
POST /bot{token}/sendMessage
{
    "chat_id": 123456789,
    "text": "Hello",
    "parse_mode": "HTML"
}

# Send photo
POST /bot{token}/sendPhoto
{
    "chat_id": 123456789,
    "photo": "https://example.com/image.jpg",
    "caption": "Image caption"
}

# Get file
GET /bot{token}/getFile?file_id={file_id}
GET https://api.telegram.org/file/bot{token}/{file_path}
```

---

## 4. OpenMeetings Integration

### REST API
- **Base URL**: `https://meetings.example.com/openmeetings/services`
- **Authentication**: Session-based (login first)

### Configuration Required
| Setting | Source | Location in Arrowz |
|---------|--------|-------------------|
| Server URL | OpenMeetings | `AZ Server Config.host` |
| Admin Username | OpenMeetings | `AZ Server Config.username` |
| Admin Password | OpenMeetings | `AZ Server Config.password` |

### API Endpoints Used
```python
# Login (get SID)
GET /user/login?user={user}&pass={pass}

# Create room
POST /room/
{
    "name": "Meeting Room",
    "type": 1,  # 1=Conference, 2=Webinar
    "capacity": 50
}

# Get room hash (for guest access)
POST /user/hash
{
    "roomId": 123,
    "firstname": "John",
    "lastname": "Doe",
    "email": "john@example.com"
}

# Get recordings
GET /record/room/{roomId}
```

### Room Types
| Type ID | Name | Purpose |
|---------|------|---------|
| 1 | Conference | Standard meeting |
| 2 | Webinar | Presenter + viewers |
| 3 | Interview | 1-on-1 meeting |

---

## 5. ERPNext CRM Integration

### DocTypes Linked
```
Arrowz                          ERPNext/Frappe
──────────────────────────────────────────────
AZ Call Log.contact      ───>   Contact
AZ Call Log.lead         ───>   Lead
AZ Call Log.customer     ───>   Customer
AZ Conversation Session  ───>   Contact/Lead
Screen Pop               ───>   Contact/Lead/Customer/Supplier
```

### Contact Search Logic
```python
# Priority order for phone lookup:
1. Contact (phone, mobile_no)
2. Lead (phone, mobile_no)
3. Customer (mobile_no - custom field)
4. Supplier (mobile_no - custom field)
5. Employee (cell_number)
```

### Click-to-Call DocTypes
Enhanced with phone action buttons:
- Contact
- Lead
- Customer
- Supplier
- Employee
- Sales Order
- Purchase Order
- Quotation
- Opportunity
- Issue
- Project
- Task
- Address
- Sales Partner

---

## 6. OpenAI Integration (AI Features)

### API
- **Base URL**: `https://api.openai.com/v1`
- **Model**: GPT-4 / GPT-4-turbo
- **Authentication**: Bearer token

### Features Using OpenAI
1. **Sentiment Analysis**: Analyze call/message sentiment
2. **Transcription**: Convert speech to text (Whisper)
3. **Coaching**: Real-time agent suggestions
4. **Summaries**: Post-call summaries

### Configuration
```python
# In Arrowz Settings
openai_api_key = "sk-..."
enable_sentiment = True
enable_coaching = True
sentiment_model = "gpt-4-turbo-preview"
```

---

## 7. Frappe Framework Integration

### Hooks Used

#### Document Events
```python
doc_events = {
    "Contact": {"after_insert": "arrowz.events.contact.after_insert"},
    "Lead": {"after_insert": "arrowz.events.lead.after_insert"},
    "AZ Conversation Session": {"on_update": "arrowz.events.conversation.on_session_update"},
    "AZ Meeting Room": {"after_insert": "arrowz.events.meeting.after_room_create"}
}
```

#### Scheduled Tasks
```python
scheduler_events = {
    "cron": {"*/5 * * * *": ["arrowz.tasks.cleanup_stale_presence"]},
    "hourly": ["arrowz.tasks.sync_pbx_status"],
    "daily": ["arrowz.tasks.cleanup_old_presence_logs"]
}
```

#### Boot Session
```python
boot_session = "arrowz.boot.boot_session"
# Injects: arrowz_settings, user_extensions, has_pbx_access
```

#### Notification Config
```python
notification_config = "arrowz.notifications.get_notification_config"
```

### Real-time (Socket.IO)
```python
# Publishing events
frappe.publish_realtime("arrowz_call_started", message, user=user)

# JavaScript subscription
frappe.realtime.on("arrowz_call_started", handler);
```

---

## 8. Related Frappe Apps

### Optional Dependencies
| App | Purpose | Integration Point |
|-----|---------|------------------|
| `erpnext` | CRM, Customer, Supplier | Contact lookup, call logging |
| `frappe_whatsapp` | Alternative WhatsApp | Can coexist (different channels) |
| `telephony` | Frappe telephony core | Not required (Arrowz is standalone) |

### Compatibility Notes
- Arrowz works standalone with just `frappe`
- ERPNext enhances contact lookup and CRM features
- Does not conflict with `frappe_whatsapp` (different API approach)

---

## 6. MikroTik RouterOS Integration

### Connection Type
- **Protocol**: RouterOS API (binary, TCP)
- **Ports**: 8728 (plaintext), 8729 (SSL)
- **Library**: `librouteros` 4.0.0 (Python)
- **Configuration**: `Arrowz Box` DocType (device_type=MikroTik)

### Architecture

```
                  ┌─────────────────────────────────────────┐
                  │            Arrowz Box DocType            │
                  │  device_type = "MikroTik"                │
                  │  mikrotik_api_port = 8728               │
                  │  mikrotik_username / mikrotik_password   │
                  └──────────────┬──────────────────────────┘
                                 │
                  ┌──────────────▼──────────────────────────┐
                  │         ProviderFactory                  │
                  │  get_provider(box_doc) → MikroTikProvider│
                  └──────────────┬──────────────────────────┘
                                 │
                  ┌──────────────▼──────────────────────────┐
                  │       MikroTikProvider                   │
                  │  (BaseProvider implementation)           │
                  │  • System info/reboot                    │
                  │  • Interfaces (ethernet/VLAN/bridge)     │
                  │  • IP addresses / DHCP / DNS             │
                  │  • Routing (static/connected)            │
                  │  • Firewall (filter + NAT)               │
                  │  • Queues / bandwidth                    │
                  │  • WiFi (v6 wireless + v7 wave2)         │
                  │  • VPN (WireGuard)                       │
                  │  • ARP table                             │
                  │  • Full config pull/push                 │
                  └──────────────┬──────────────────────────┘
                                 │
                  ┌──────────────▼──────────────────────────┐
                  │        RouterOSClient                    │
                  │  (librouteros wrapper)                   │
                  │  connect/disconnect, retry, SSL          │
                  │  print_resource / add / set / remove     │
                  └──────────────┬──────────────────────────┘
                                 │
                  ┌──────────────▼──────────────────────────┐
                  │     MikroTik Router (RouterOS)           │
                  │  API port 8728/8729                      │
                  └─────────────────────────────────────────┘
```

### Sync Engine

```python
from arrowz.device_providers.sync_engine import SyncEngine

# Pull config from device → Frappe DocTypes
engine = SyncEngine(box_doc)
result = engine.pull()

# Push Frappe DocType config → device
result = engine.push()

# Compare configs
diff = engine.diff()
```

### Supported Features
| Category | RouterOS Commands Used |
|----------|-----------------------|
| System | `/system/resource`, `/system/identity`, `/system/reboot` |
| Interfaces | `/interface/print`, `/interface/ethernet`, `/interface/vlan` |
| IP | `/ip/address`, `/ip/dhcp-server`, `/ip/dhcp-client` |
| DNS | `/ip/dns`, `/ip/dns/static` |
| Routing | `/ip/route` |
| Firewall | `/ip/firewall/filter`, `/ip/firewall/nat` |
| Queues | `/queue/simple` |
| WiFi v6 | `/interface/wireless` |
| WiFi v7 | `/interface/wifi`, `/interface/wifiwave2` |
| VPN | `/interface/wireguard`, `/interface/wireguard/peers` |
| ARP | `/ip/arp` |

---

## 7. Linux Box Integration

### Connection Type
- **Protocol**: HTTPS REST API + HMAC-SHA256 authentication
- **Library**: `BoxConnector` (custom, `arrowz.box_connector`)
- **Configuration**: `Arrowz Box` DocType (device_type=Linux Box)

### Data Flow
```
Arrowz Box → ProviderFactory → LinuxProvider → BoxConnector → HTTPS → Box Agent
                                                    │
                                                    └── Bearer token + HMAC
```

### Endpoints (via BoxConnector)
| Endpoint | Purpose |
|----------|---------|
| `/api/health` | Health check |
| `/api/config` | Push full configuration |
| `/api/clients` | Connected clients |
| `/api/wifi` | WiFi settings |
| `/api/vpn` | VPN configuration |
| `/api/accounting` | IP accounting data |
| `/api/logs` | System logs |

---

## 8. Device Provider Abstraction Layer

All device integrations are unified through the provider pattern:

```python
from arrowz.device_providers import ProviderFactory

# Auto-detect provider from DocType
box = frappe.get_doc("Arrowz Box", "my-device")
with ProviderFactory.connect(box) as provider:
    info = provider.get_system_info()
    interfaces = provider.get_interfaces()
    config = provider.get_full_config()
```

### ErrorTracker
Multi-layer execution tracing across: provider → transport → command → mapper → sync

```python
from arrowz.device_providers.error_tracker import ErrorTracker

tracker = ErrorTracker()
with tracker.trace("sync_pull", box_name="my-device"):
    with tracker.span("transport"):
        # API calls traced with timing
        pass
```

Results logged to `MikroTik Sync Log` DocType for audit trail.

---

## 9. Security Considerations

### Authentication Flow
```
Browser → Frappe Session → Arrowz API → External Service
                │                            │
                └── Session Cookie           └── Service Token
```

### Credential Storage
| Credential | Storage | Encryption |
|------------|---------|------------|
| SIP Password | `AZ Extension.sip_password` | Frappe Password field |
| WhatsApp Token | `AZ Omni Provider.access_token` | Frappe Password field |
| OpenAI Key | `Arrowz Settings` | Frappe Password field |
| AMI Password | `AZ Server Config.password` | Frappe Password field |
| MikroTik Password | `Arrowz Box.mikrotik_password` | Frappe Password field |
| Box API Token | `Arrowz Box.api_token` | Frappe Password field |

### Webhook Security
```python
# Signature validation
def validate_whatsapp_signature(request):
    signature = request.headers.get('X-Hub-Signature-256')
    expected = hmac.new(secret, request.data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## 10. Network Requirements

### Outbound Connections
| Service | Protocol | Port | Purpose |
|---------|----------|------|---------|
| FreePBX | WSS | 8089 | WebRTC |
| FreePBX | TCP | 5038 | AMI |
| WhatsApp | HTTPS | 443 | API calls |
| Telegram | HTTPS | 443 | API calls |
| OpenMeetings | HTTPS | 443 | API calls |
| OpenAI | HTTPS | 443 | AI features |
| MikroTik | TCP | 8728 | RouterOS API |
| MikroTik | TCP/SSL | 8729 | RouterOS API (SSL) |
| Linux Box | HTTPS | 443 | Box Agent REST API |

### Inbound Webhooks
| Service | Path | Purpose |
|---------|------|---------|
| WhatsApp | `/api/method/arrowz.api.webhooks.whatsapp_cloud_webhook` | Messages |
| Telegram | `/api/method/arrowz.api.webhooks.telegram_webhook` | Updates |
| OpenMeetings | `/api/method/arrowz.api.webhooks.openmeetings_callback` | Events |

### WebRTC Media
- STUN/TURN servers for NAT traversal
- RTP/SRTP for audio (UDP, various ports)
- ICE candidates exchange via WebSocket

### Local Mounts (Dev Environment Only)
| Mount | Path | Purpose |
|-------|------|---------|
| FreePBX Config | `/mnt/pbx/etc/asterisk/` | Asterisk config files |
| FreePBX Logs | `/mnt/pbx/logs/asterisk/` | Asterisk logs |
| FreePBX DB | `/mnt/pbx/db/` | SQL database dumps |
| Recordings | `/mnt/pbx/recordings/` | Call recordings |
| Voicemail | `/mnt/pbx/voicemail/` | Voicemail files |

---

*This document should be updated when adding new integrations.*
*Last Updated: February 2026*
