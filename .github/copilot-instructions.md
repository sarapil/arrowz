# Arrowz Project - AI Developer Guidelines

You are an expert Senior Developer specializing in Frappe Framework (v16) and the specific architecture of the **Arrowz** application.

---

## 🛑 PART 1: CODING STANDARDS & BEST PRACTICES
*Strictly follow these rules for all code generation.*

### 1. General Philosophy
- **No Core Touches:** NEVER suggest modifying files inside `apps/frappe` or `apps/erpnext`.
- **App-First:** All code belongs to the `arrowz` app.
- **Version 16 Syntax:** Use Python 3.10+ and modern JS (ES6+). Frappe v16 patterns.

### 2. Python (Server-Side)
- **ORM Over SQL:** Use `frappe.db.get_value` instead of `frappe.get_doc` for reading single fields (Performance).
- **Query Builder:** Use `frappe.qb` instead of raw SQL.
- **Namespacing:** When calling internal APIs, always use the `arrowz.api` namespace defined in the project structure.
- **Device Providers:** Use `ProviderFactory.get_provider(box_doc)` — never instantiate providers directly.
- **Constants:** Import from `arrowz.dev_constants` — never hardcode paths like `/mnt/pbx`.

### 3. JavaScript (Client-Side)
- **API Calls:** Always use `frappe.call`. Never use raw `fetch` or `$.ajax`.
- **Arrowz Namespace:** Use `arrowz.softphone`, `arrowz.omni`, etc., for client interactions as defined in `public/js/arrowz.js`.
- **Events:** Use `frappe.ui.form.on` for form events.

---

## 🗺️ PART 2: ARROWZ PROJECT CONTEXT
*Use this context to understand the app structure, DocTypes, and available APIs.*

### 📋 App Overview
- **App Name**: Arrowz (Unified Network & WiFi Management Platform with VoIP)
- **Core Function**: Enterprise VoIP, WebRTC Softphone, WhatsApp/Telegram, Network/WiFi Management, MikroTik integration.
- **Frappe Version**: v16+
- **Python**: 3.10+ (virtualenv at `frappe-bench/env/`)
- **Dev Site**: `dev.localhost`

### 🏗️ Architecture
The app is divided into these layers:
1. **Frontend**: Softphone (WebRTC/JsSIP), Omni Panel (Chat), Screen Pop.
2. **API Layer**: `arrowz/api/` (Endpoints for WebRTC, SMS, Analytics, etc.).
3. **Integration**: Connectors for FreePBX, WhatsApp Cloud, Telegram, OpenMeetings.
4. **Device Providers**: `arrowz/device_providers/` — Abstract provider layer for network devices.
5. **Network Modules**: 11 modules covering interfaces, WiFi, firewall, VPN, bandwidth, billing, monitoring.

### 📁 Key Files & Modules

```
arrowz/
├── api/                    # REST API endpoints (frappe.call targets)
│   ├── webrtc.py           # arrowz.api.webrtc.get_webrtc_config
│   ├── sms.py              # SMS handling
│   ├── communications.py   # Omni-channel messaging
│   └── ...
├── device_providers/       # ★ Device abstraction layer
│   ├── base_provider.py    # ABC with 50+ abstract methods
│   ├── provider_factory.py # Factory: device_type → provider
│   ├── error_tracker.py    # Multi-layer execution tracing
│   ├── sync_engine.py      # Pull/push/diff sync engine
│   ├── linux/              # Linux Box via BoxConnector
│   └── mikrotik/           # MikroTik via librouteros
├── integrations/           # External API wrappers
│   ├── whatsapp.py
│   └── openmeetings.py
├── public/js/
│   ├── softphone_v2.js     # Global: arrowz.softphone
│   └── omni_panel.js       # Chat UI
├── local_pbx_monitor.py    # ★ /mnt/pbx reader (no SSH needed)
├── dev_constants.py        # ★ All environment constants
├── box_connector.py        # HTTPS REST client for Linux boxes
├── config_compiler.py      # DocType → config dict compiler
├── tasks.py                # VoIP scheduled tasks
├── tasks_network.py        # Network scheduled tasks
└── hooks.py                # Frappe hooks (v16)
```

### 🔧 Key DocTypes

**VoIP/Communications:**
- `AZ Call Log` — Call records (call_id, caller, recording_url)
- `AZ Extension` — SIP credentials, WebRTC config
- `AZ Server Config` — PBX settings (WebSocket, AMI, GraphQL, SSH, OpenMeetings)
- `AZ Conversation Session` / `AZ Conversation Message` — Omni-channel
- `AZ Omni Provider` — WhatsApp/Telegram config

**Network Management:**
- `Arrowz Box` — Network device (Linux/MikroTik) with device_type, sync fields
- `Arrowz Network Settings` — Global network configuration
- `MikroTik Sync Log` — Sync operation audit trail

**Plus 70+ DocTypes across:** Network, WiFi, Client, Bandwidth, Firewall, VPN, Billing, Monitoring, IP Accounting modules.

### 🔌 Available API Endpoints
- **WebRTC Config**: `arrowz.api.webrtc.get_webrtc_config`
- **Search Contacts**: `arrowz.api.contacts.search_contacts`
- **Send Message**: `arrowz.api.communications.send_message`
- **Dashboard Stats**: `arrowz.api.wallboard.get_realtime_stats`
- **PBX Diagnostics**: `arrowz.local_pbx_monitor.diagnose_webrtc`
- **PBX Logs**: `arrowz.local_pbx_monitor.get_pbx_logs`

### 🌐 Frontend Global Objects
- `arrowz.softphone.dial(number)`
- `arrowz.softphone.answer()`
- `arrowz.softphone.transfer(target)`

### 🔄 Real-time Events
- `arrowz_call_started`, `call_received`, `call_ended`
- `new_message`, `new_omni_message`
- `arrowz_presence_update`, `extension_status`
- `wallboard_update`

### 🧪 Integration Notes
- **FreePBX**: WebSocket (wss://), AMI, and local mount at `/mnt/pbx/`
- **WhatsApp**: Meta Cloud API v17+ (Graph API)
- **MikroTik**: RouterOS API via librouteros 4.0.0 (port 8728/8729)
- **OpenMeetings**: REST API
- **Linux Box**: HTTPS REST + HMAC-SHA256 via BoxConnector

### 📂 FreePBX Mount (`/mnt/pbx`)
In dev environment, FreePBX volumes are mounted read-only:
- `/mnt/pbx/etc/asterisk/` — Config files (pjsip, extensions, manager, http, rtp)
- `/mnt/pbx/logs/asterisk/` — Logs (full, queue_log, freepbx.log, security)
- `/mnt/pbx/db/` — SQL database dumps
- `/mnt/pbx/recordings/` — Call recordings
- `/mnt/pbx/voicemail/` — Voicemail files

Use `from arrowz.dev_constants import PBX_MOUNT, PBX_CONFIG_FILES, PBX_LOG_FILES`