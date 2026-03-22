# Arrowz - Development Environment Context

## Quick Start for New Developers

This document provides essential context for developers joining the Arrowz project.
All environment constants are also available as importable Python values:

```python
from arrowz.dev_constants import PBX_MOUNT, BENCH_PATH, PORTS, ENV_VARS, MODULES
```

## Environment Details

| Attribute | Value |
|-----------|-------|
| **Container OS** | Debian GNU/Linux 12 (bookworm) |
| **Python** | 3.10+ (virtualenv at `frappe-bench/env/`) |
| **Node.js** | 18+ |
| **Frappe** | v16+ |
| **Database** | MariaDB 10.6+ |
| **Cache/Queue** | Redis (cache:13000, queue:11000) |
| **Dev Site** | `dev.localhost` |
| **Dev Mode** | `developer_mode: 1` in `site_config.json` |

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Frappe Web | 8000 | Gunicorn web server |
| Socket.IO | 9000 | Real-time events |
| File Watcher | 6787 | `bench watch` hot reload |
| MariaDB | 3306 | Database |
| Redis Cache | 13000 | Cache layer |
| Redis Queue | 11000 | Background job queue |
| PBX WebSocket | 8089 | WebRTC signaling (WSS) |
| PBX AMI | 5038 | Asterisk Manager Interface |
| MikroTik API | 8728 | RouterOS API |
| MikroTik API SSL | 8729 | RouterOS API (encrypted) |

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `ARROWZ_DEBUG` | Enable debug mode (1/0) |
| `ARROWZ_DISABLE_WEBHOOKS` | Disable webhook processing (1/0) |
| `ARROWZ_OPENAI_TIMEOUT` | OpenAI API timeout in seconds |
| `PBX_HOST` | FreePBX server hostname/IP |
| `PBX_SSH_USER` | SSH user for PBX server |
| `PBX_AMI_USER` | AMI username |
| `PBX_AMI_SECRET` | AMI password |
| `OM_HOST` | OpenMeetings server URL |

## Directory Layout

```
/workspace/development/
├── frappe-bench/                    # Main bench directory
│   ├── apps/                        # All installed apps
│   │   ├── frappe/                  # Core framework (v16)
│   │   ├── erpnext/                 # ERPNext ERP
│   │   ├── arrowz/                  # ★ THIS APPLICATION ★
│   │   ├── tavira_theme/            # Custom UI theme (LCD desktop, glassmorphism)
│   │   ├── hrms/                    # HR Management
│   │   └── ...                      # Other apps
│   │
│   ├── sites/
│   │   ├── dev.localhost/           # Development site
│   │   │   └── site_config.json     # Site configuration
│   │   └── common_site_config.json  # Shared config
│   │
│   ├── logs/                        # Application logs
│   ├── config/                      # Bench configuration
│   └── env/                         # Python virtual environment
│
├── .github/
│   └── copilot-instructions.md      # AI assistant context
│
└── /mnt/pbx/                        # ★ FreePBX mounted volumes (see below) ★
    ├── etc/asterisk/                # PBX configuration files
    ├── logs/asterisk/               # PBX logs (full, queue, security)
    ├── db/                          # Database SQL dumps
    ├── recordings/                  # Call recordings (.wav)
    └── voicemail/                   # Voicemail files
```

## Arrowz App Structure

```
/workspace/development/frappe-bench/apps/arrowz/
├── arrowz/                          # Main Python package
│   ├── api/                         # REST API endpoints
│   │   ├── webrtc.py               # JsSIP configuration
│   │   ├── contacts.py             # Contact search
│   │   ├── notifications.py        # Pending notifications
│   │   ├── communications.py       # Omni-channel messaging
│   │   ├── sms.py                  # SMS operations
│   │   ├── call_log.py             # Call history
│   │   ├── wallboard.py            # Dashboard stats
│   │   ├── analytics.py            # Reports
│   │   └── webhooks.py             # External webhooks
│   │
│   ├── arrowz/                      # Core VoIP module
│   │   └── doctype/                 # AZ Call Log, AZ Extension, etc.
│   │
│   ├── arrowz_setup/                # Setup & Configuration module
│   │   └── doctype/
│   │       ├── arrowz_box/          # Network device (Linux/MikroTik)
│   │       ├── arrowz_network_settings/
│   │       └── mikrotik_sync_log/   # Sync operation logging
│   │
│   ├── device_providers/            # ★ Device abstraction layer ★
│   │   ├── base_provider.py        # ABC with all abstract methods
│   │   ├── provider_factory.py     # Factory: device_type → provider
│   │   ├── error_tracker.py        # Multi-layer execution tracing
│   │   ├── sync_engine.py          # Bidirectional sync engine
│   │   ├── linux/                   # Linux Box provider (BoxConnector)
│   │   │   └── linux_provider.py
│   │   └── mikrotik/                # MikroTik RouterOS provider
│   │       ├── routeros_client.py  # Low-level API wrapper (librouteros)
│   │       └── mikrotik_provider.py # Full BaseProvider implementation
│   │
│   ├── network_management/          # Network interfaces, IP, DHCP, DNS
│   ├── wifi_management/             # WiFi SSIDs, APs, Hotspot
│   ├── client_management/           # Connected devices, sessions
│   ├── bandwidth_control/           # QoS, speed limits
│   ├── firewall/                    # Rules, NAT, port forwarding
│   ├── vpn/                         # WireGuard, L2TP, PPPoE, SSTP
│   ├── billing_integration/         # Vouchers, quotas, usage
│   ├── monitoring/                  # Alerts, health checks
│   ├── ip_accounting/               # Traffic analysis
│   │
│   ├── integrations/                # External connectors
│   │   ├── whatsapp.py             # WhatsApp Cloud API
│   │   ├── telegram.py             # Telegram Bot API
│   │   └── openmeetings.py         # Video conferencing
│   │
│   ├── events/                      # Document event handlers
│   │   └── network.py              # Network config push events
│   │
│   ├── public/                      # Static assets
│   │   ├── js/                      # JavaScript files
│   │   │   ├── softphone_v2.js     # WebRTC softphone
│   │   │   ├── omni_panel.js       # Chat panel
│   │   │   ├── phone_actions.js    # Click-to-call
│   │   │   └── screen_pop.js       # Caller ID popup
│   │   └── css/                     # Stylesheets
│   │
│   ├── hooks.py                     # Frappe hooks (v16)
│   ├── boot.py                      # Session boot data
│   ├── tasks.py                     # Scheduled jobs (VoIP)
│   ├── tasks_network.py             # Scheduled jobs (Network)
│   ├── local_pbx_monitor.py         # ★ /mnt/pbx reader (no SSH) ★
│   ├── dev_constants.py             # ★ Environment constants ★
│   ├── box_connector.py             # HTTPS REST client for Linux boxes
│   ├── config_compiler.py           # DocType → config dict compiler
│   └── ssh_manager.py               # SSH operations
│
├── docs/                            # Documentation
├── CONTEXT.md                       # Technical context
├── INTEGRATIONS.md                  # Integration map
├── ARCHITECTURE.md                  # Architecture diagrams
├── DEVELOPMENT.md                   # This file
├── TROUBLESHOOTING.md               # Problem/solution guide
├── README.md                        # Overview
└── pyproject.toml                   # Python package config
```

## FreePBX Mount — `/mnt/pbx` (VoIP Debugging)

The `/mnt/pbx` directory is a **Docker volume mount** from the FreePBX container.
It provides **read-only access** to all FreePBX/Asterisk files without SSH.

This is the **primary debugging resource** for VoIP/softphone issues.

### Directory Structure

```
/mnt/pbx/
├── etc/asterisk/                    # ★ Asterisk configuration
│   ├── pjsip.conf                  # Main PJSIP config (auto-generated)
│   ├── pjsip.endpoint.conf         # Extension endpoints (SIP accounts)
│   ├── pjsip.transports.conf       # WSS/UDP/TCP transports
│   ├── pjsip.auth.conf             # SIP authentication
│   ├── pjsip.aor.conf              # Address of Record
│   ├── pjsip.registration.conf     # SIP registrations
│   ├── extensions_additional.conf   # Dialplan (auto-generated)
│   ├── extensions_custom.conf       # Custom dialplan overrides
│   ├── manager.conf                 # AMI configuration
│   ├── http.conf                    # HTTP/WebSocket server
│   ├── rtp.conf                     # RTP media settings (STUN/ICE)
│   ├── voicemail.conf               # Voicemail settings
│   ├── queues.conf                  # Call queue configuration
│   ├── codecs.conf                  # Audio codec settings
│   └── keys/                        # TLS/DTLS certificates
│       ├── tavirapbx.pem           # PBX certificate
│       ├── ca.crt                   # CA certificate
│       └── integration/             # Integration certs
│
├── logs/asterisk/                   # ★ Asterisk logs
│   ├── full                         # Main log (ALL events) ← start here
│   ├── freepbx.log                  # FreePBX application log
│   ├── freepbx_security.log         # Security events
│   ├── queue_log                    # Queue operations
│   ├── fail2ban                     # Blocked IPs
│   ├── firewall.log                 # Firewall events
│   ├── full-YYYYMMDD              # Rotated daily logs
│   └── queue_log-YYYYMMDD         # Rotated queue logs
│
├── db/                              # ★ Database dumps
│   ├── asterisk_*.sql              # Full Asterisk DB
│   ├── asteriskcdrdb_*.sql         # CDR (Call Detail Records)
│   └── asterisk_complete_*.sql     # Complete dump
│
├── recordings/                      # ★ Call recordings (.wav)
└── voicemail/                       # ★ Voicemail files
    └── default/                     # Default context
        └── <extension>/             # Per-extension voicemail
            ├── INBOX/
            └── tmp/
```

### Quick Debugging Commands

```bash
# Check if PBX mounts are available
ls -la /mnt/pbx/

# Read main Asterisk log (last 100 lines)
tail -100 /mnt/pbx/logs/asterisk/full

# Filter SIP registration issues
grep -i "register\|401\|403\|unauthorized" /mnt/pbx/logs/asterisk/full | tail -50

# Filter WebRTC/ICE/DTLS errors
grep -i "ice\|dtls\|srtp\|webrtc\|stun\|turn" /mnt/pbx/logs/asterisk/full | tail -50

# Check specific extension config
grep -A 30 "\[1001\]" /mnt/pbx/etc/asterisk/pjsip.endpoint.conf

# Check WSS transport config
cat /mnt/pbx/etc/asterisk/pjsip.transports.conf

# Check AMI config
head -30 /mnt/pbx/etc/asterisk/manager.conf

# Search call errors
grep -i "error\|fail\|warning" /mnt/pbx/logs/asterisk/full | tail -50

# Check FreePBX version
grep "user_agent" /mnt/pbx/etc/asterisk/pjsip.conf
```

### Python API (LocalPBXMonitor)

```python
# In bench console: bench --site dev.localhost console
from arrowz.local_pbx_monitor import LocalPBXMonitor

monitor = LocalPBXMonitor()
monitor.check_mounts()           # Check what's available
monitor.get_full_log(100)        # Read last 100 lines
monitor.get_webrtc_log(50)       # Filter WebRTC/ICE entries
monitor.get_sip_log(50)          # Filter SIP entries
monitor.get_extension_config("1001")  # Check extension settings
monitor.diagnose_webrtc("1001")  # Full WebRTC diagnostics
monitor.get_call_quality_metrics()    # Call quality analysis
monitor.list_recordings()        # List call recordings
```

## Common Commands

### Development
```bash
# Start development server
cd /workspace/development/frappe-bench
bench start

# Build Arrowz assets
bench build --app arrowz

# Watch for changes (auto-rebuild)
bench watch --app arrowz

# Clear cache
bench --site dev.localhost clear-cache
```

### Database & Migrations
```bash
# Run migrations after DocType changes
bench --site dev.localhost migrate

# Access database console
bench --site dev.localhost mariadb

# Backup
bench --site dev.localhost backup
```

### Testing & Debugging
```bash
# Run tests
bench --site dev.localhost run-tests --app arrowz

# Python console
bench --site dev.localhost console

# Check errors
tail -f logs/frappe.log
tail -f logs/worker.error.log
```

### Server Management
```bash
# Restart all processes
bench restart

# List installed apps
bench --site dev.localhost list-apps
```

## Key DocTypes Reference

### Call Management
- `AZ Call Log` - Call records
- `AZ Extension` - SIP extensions
- `AZ Server Config` - PBX servers

### Messaging
- `AZ SMS Message` - SMS log
- `AZ SMS Provider` - SMS gateways
- `AZ Omni Provider` - WhatsApp/Telegram config
- `AZ Conversation Session` - Chat sessions
- `AZ Conversation Message` - Chat messages

### Video Meetings
- `AZ Meeting Room` - Conference rooms
- `AZ Meeting Participant` - Attendees
- `AZ Meeting Recording` - Recordings

### Configuration
- `Arrowz Settings` - Global settings

## API Patterns

### Creating an API Endpoint
```python
# arrowz/api/mymodule.py
import frappe

@frappe.whitelist()
def my_function(param1: str, param2: int = 10) -> dict:
    """
    API documentation.
    
    Args:
        param1: Description
        param2: Optional description
        
    Returns:
        dict: Result
    """
    # Permission check
    frappe.only_for(['System Manager', 'Call Center Agent'])
    
    # Implementation
    result = frappe.get_all("AZ Call Log", 
        filters={"caller": param1},
        limit=param2
    )
    
    return {"data": result}
```

### Calling from JavaScript
```javascript
const { message } = await frappe.call({
    method: 'arrowz.api.mymodule.my_function',
    args: { param1: 'value', param2: 20 }
});
console.log(message.data);
```

## Real-time Communication

### Publishing Events (Python)
```python
frappe.publish_realtime(
    event="arrowz_custom_event",
    message={"key": "value"},
    user=frappe.session.user
)
```

### Subscribing (JavaScript)
```javascript
frappe.realtime.on("arrowz_custom_event", (data) => {
    console.log(data.key);
});
```

## Integration Quick Reference

| Service | Type | Config DocType |
|---------|------|----------------|
| FreePBX | WebSocket + AMI | `AZ Server Config` |
| WhatsApp | REST + Webhooks | `AZ Omni Provider` |
| Telegram | REST + Webhooks | `AZ Omni Provider` |
| OpenMeetings | REST | `AZ Server Config` |
| OpenAI | REST | `Arrowz Settings` |
| Linux Box | HTTPS + HMAC | `Arrowz Box` (device_type=Linux Box) |
| MikroTik | RouterOS API | `Arrowz Box` (device_type=MikroTik) |
| /mnt/pbx | Local mount | No config — always available |

## Troubleshooting

### Softphone Not Showing
1. Check browser console for JS errors
2. Verify navbar selector in softphone_v2.js
3. Ensure user has AZ Extension assigned

### WebRTC Not Connecting
1. Check WebSocket URL (must be wss://)
2. Verify SIP credentials
3. Confirm PBX WebSocket enabled
4. **Use /mnt/pbx diagnostics:**
   ```bash
   grep -i "webrtc\|ice\|dtls" /mnt/pbx/logs/asterisk/full | tail -30
   ```

### Webhooks Not Working
1. Ensure URL is publicly accessible
2. Check webhook signature validation
3. Review Error Log in Frappe

### MikroTik Connection Failed
1. Verify API port (8728 or 8729 for SSL) is open
2. Check credentials in Arrowz Box DocType
3. Ensure API service is enabled on MikroTik:
   ```
   /ip/service/enable api
   ```

## Documentation Files

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Full technical context |
| `INTEGRATIONS.md` | Integration architecture |
| `ARCHITECTURE.md` | Architecture diagrams |
| `DEVELOPMENT.md` | This file — dev environment |
| `TROUBLESHOOTING.md` | Problem/solution guide |
| `CLAUDE.md` | Claude AI quick reference |
| `AI_GUIDELINES.md` | AI code generation rules |
| `.github/copilot-instructions.md` | GitHub Copilot context |
| `dev_constants.py` | All environment constants (Python) |
| `docs/INDEX.md` | Documentation hub |
| `docs/FREEPBX_SETUP.md` | FreePBX configuration guide |
| `docs/SERVER_ADMIN.md` | Production server admin |
| `docs/DEVELOPER_GUIDE.md` | Detailed developer guide |
| `docs/FEATURES_EN.md` | Complete feature reference |

## Production vs Development Differences

| Aspect | Development | Production |
|--------|------------|------------|
| **Server** | `bench start` (Werkzeug) | Gunicorn + Nginx + supervisor |
| **SSL** | Not required | Required (Let's Encrypt) |
| **Workers** | Single process | Multiple workers + queues |
| **Debug** | `developer_mode: 1` | `developer_mode: 0` |
| **Assets** | Live rebuild (`bench watch`) | Pre-built (`bench build`) |
| **DB** | Local MariaDB | MariaDB cluster (recommended) |
| **PBX Access** | `/mnt/pbx` mount | Network (SSH/AMI/WebSocket) |
| **MikroTik** | Direct API | Direct API |

---

*Last Updated: February 2026*
