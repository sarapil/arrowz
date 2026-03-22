# Arrowz Softphone — Full Prompt Context

> **Purpose**: This file contains ALL information any AI prompt needs to work on the Arrowz softphone.
> Copy this entire file as context when starting a new chat session.
> **Last Updated**: 2026-02-25

---

## 1. Environment & Infrastructure

### Docker Topology

```
┌──────────────────────────────────────────────────────────────────┐
│  VPS: 157.173.125.136  (Hetzner, Debian)                        │
│                                                                  │
│  ┌─────────────────────┐  ┌──────────────────────┐              │
│  │  frappe-bench        │  │  FreePBX (Asterisk)  │              │
│  │  container           │  │  container           │              │
│  │  IP: 172.21.0.3      │  │  IP: 172.23.0.2      │              │
│  │  Host: 00ec6dfb0050  │  │  Asterisk 22.7.0     │              │
│  │                      │  │  FreePBX 17.0.19.32  │              │
│  │  Ports:              │  │                      │              │
│  │   8000 (web)         │  │  Ports:              │              │
│  │   9000 (socketio)    │  │   8089 (WSS)         │              │
│  │   6787 (file watch)  │  │   5060 (SIP UDP/TCP) │              │
│  │                      │  │   5038 (AMI)         │              │
│  │  PBX mount:          │  │   3478 (TURN/STUN)   │              │
│  │   /mnt/pbx/ (ro)     │  │   10000-20000 (RTP)  │              │
│  └──────────┬───────────┘  └──────────┬───────────┘              │
│             │  Docker network          │                         │
│             └──────────────────────────┘                         │
│                                                                  │
│  ┌─────────────────────┐  ┌──────────────────────┐              │
│  │  MariaDB             │  │  Redis               │              │
│  │  host: mariadb       │  │  cache: redis-cache  │              │
│  │                      │  │  queue: redis-queue   │              │
│  └──────────────────────┘  └──────────────────────┘              │
│                                                                  │
│  ┌─────────────────────┐                                        │
│  │  coturn (TURN/STUN) │                                        │
│  │  Port 3478 UDP/TCP  │                                        │
│  │  Credentials:       │                                        │
│  │   user: webrtc      │                                        │
│  │   pass: Arrowz2024! │                                        │
│  └─────────────────────┘                                        │
└──────────────────────────────────────────────────────────────────┘
```

### Key IPs & Domains

| Entity | Value |
|--------|-------|
| **VPS Public IP** | `157.173.125.136` |
| **SIP Domain** | `pbx.tavira-group.com` → resolves to `157.173.125.136` |
| **Frappe URL** | `https://dev.tavira-group.com` / `http://dev.localhost:8000` |
| **Frappe container IP** | `172.21.0.3` |
| **PBX container IP** | `172.23.0.2` |
| **Client public IP** | `41.40.114.156` (Egypt, may change) |
| **WebSocket URL** | `wss://pbx.tavira-group.com:8089/ws` |
| **TURN server** | `turn:157.173.125.136:3478` (coturn, UDP+TCP) |
| **STUN server** | `stun:stun.l.google.com:19302` |

### PBX Volume Mount

The PBX filesystem is mounted read-only at `/mnt/pbx/`:
```
/mnt/pbx/
├── etc/asterisk/          # All Asterisk config files
│   ├── pjsip.endpoint.conf        # FreePBX auto-generated (DO NOT EDIT)
│   ├── pjsip.endpoint_custom.conf # Our overrides
│   ├── rtp_custom.conf            # ICE/TURN config
│   ├── manager_custom.conf        # AMI user
│   └── http_custom.conf           # (empty)
├── logs/asterisk/
│   └── full                       # Main Asterisk log
├── db/                            # SQL dumps
├── recordings/                    # Call recordings (.wav)
└── voicemail/                     # Voicemail files
```

### Asterisk Custom Config (Current)

**rtp_custom.conf**:
```ini
turnaddr=157.173.125.136
turnusername=webrtc
turnpassword=Arrowz2024!

[ice_host_candidates]
172.23.0.2 => 157.173.125.136
```

**pjsip.endpoint_custom.conf**:
```ini
[2210](+)
media_encryption=no
ice_support=no
use_avpf=no
rtcp_mux=no
bundle=no
```

**manager_custom.conf**:
```ini
[arrowz_admin]
secret=ArrowzAMI2024!
deny=0.0.0.0/0.0.0.0
permit=0.0.0.0/0.0.0.0
read=system,call,log,verbose,command,agent,user,config,dtmf,reporting,cdr,dialplan
write=system,call,log,verbose,command,agent,user,config,dtmf,reporting,cdr,dialplan,originate
```

---

## 2. Frappe / Bench Setup

### Site Config

```json
{
  "db_name": "_7ad329d6da0dcdc2",
  "db_password": "123",
  "db_type": "mariadb",
  "developer_mode": 1,
  "host_name": "http://dev.localhost:8000",
  "socketio_host": "http://dev.localhost:9000",
  "theme": "tavira_theme"
}
```

### Common Site Config (highlights)

```json
{
  "db_host": "mariadb",
  "default_site": "dev.localhost",
  "redis_cache": "redis://redis-cache:6379",
  "redis_queue": "redis://redis-queue:6379",
  "host_name": "https://dev.tavira-group.com"
}
```

### Arrowz App Location

```
/workspace/development/frappe-bench/apps/arrowz/
├── arrowz/
│   ├── hooks.py           # App hooks
│   ├── api/
│   │   └── webrtc.py      # WebRTC API endpoints (688 lines)
│   ├── arrowz/
│   │   └── doctype/
│   │       └── az_server_config/   # Server configuration DocType
│   │       └── az_extension/       # SIP extension DocType
│   │       └── az_call_log/        # Call log DocType
│   └── public/
│       ├── js/
│       │   ├── lib/
│       │   │   └── jssip.min.js       # JsSIP 3.x library
│       │   ├── softphone.js           # v1 (legacy, 73K)
│       │   ├── softphone_v2.js        # v2 (current backup, 154K, 3571 lines)
│       │   ├── softphone_v3.js        # v3 (ACTIVE in hooks.py, 86K, 1985 lines)
│       │   ├── arrowz.js              # Core app JS
│       │   ├── arrowz_theme.js        # Theme engine
│       │   ├── phone_actions.js       # Click-to-call on DocTypes
│       │   ├── screen_pop.js          # Incoming call screen pop
│       │   ├── omni_panel.js          # WhatsApp/Telegram panel
│       │   └── omni_doctype_extension.js  # Navbar notifications
│       └── css/
│           ├── softphone_v2.css       # Softphone styles (ACTIVE)
│           ├── arrowz.css             # Core styles
│           ├── arrowz_theme.css       # Theme styles
│           ├── phone_actions.css
│           ├── screen_pop.css
│           └── omni_panel.css
├── CONTEXT.md              # Full app technical context
├── INTEGRATIONS.md         # External system integrations
└── PROMPT_CONTEXT.md       # THIS FILE
```

### hooks.py — JS/CSS Loading

```python
app_include_js = [
    "/assets/arrowz/js/lib/jssip.min.js",
    "/assets/arrowz/js/arrowz.js",
    "/assets/arrowz/js/arrowz_theme.js",
    "/assets/arrowz/js/phone_actions.js",
    "/assets/arrowz/js/softphone_v3.js",       # ← ACTIVE version
    "/assets/arrowz/js/screen_pop.js",
    "/assets/arrowz/js/omni_panel.js",
    "/assets/arrowz/js/omni_doctype_extension.js",
]

app_include_css = [
    "/assets/arrowz/css/arrowz_theme.css",
    "/assets/arrowz/css/arrowz.css",
    "/assets/arrowz/css/phone_actions.css",
    "/assets/arrowz/css/softphone_v2.css",     # ← CSS still v2 name
    "/assets/arrowz/css/screen_pop.css",
    "/assets/arrowz/css/omni_panel.css"
]
```

---

## 3. Database Records (Current State)

### AZ Server Config: `FP17_arkpbx`

| Field | Value |
|-------|-------|
| `server_type` | FreePBX |
| `host` | `pbx.tavira-group.com` |
| `port` | 8089 |
| `protocol` | WSS |
| `websocket_url` | `wss://pbx.tavira-group.com:8089/ws` |
| `sip_domain` | `pbx.tavira-group.com` |
| `webrtc_enabled` | 1 |
| `stun_server` | `stun:stun.l.google.com:19302` |
| `turn_server` | `turn:157.173.125.136:3478` |
| `turn_username` | `webrtc` |
| `turn_password` | `Arrowz2024!` |
| `ami_enabled` | 1 |
| `ami_host` | `172.23.0.2` |
| `ami_port` | 5038 |
| `ami_username` | `arrowz` |
| `ami_password` | (set) |
| `connection_status` | Connected |
| `is_active` | 1 |
| `is_default` | 1 |

### AZ Extensions

| Name | Extension | SIP User | User | Active |
|------|-----------|----------|------|--------|
| EXT-2290 | 2290 | 2290 | Administrator | ✅ |
| EXT-2211 | 2211 | 2211 | Administrator | ✅ |
| EXT-2210 | 2210 | 2210 | moatazarkan6@gmail.com | ✅ |

### Extension Types

| Extension | Type | Transport | Network |
|-----------|------|-----------|---------|
| 2210 | Physical SIP phone | UDP | LAN 192.168.10.4, public 41.40.114.156 |
| 2211 | WebRTC softphone | WSS | Browser, public 41.40.114.156 |
| 2290 | WebRTC softphone | WSS | Browser |

---

## 4. WebRTC API — `arrowz/api/webrtc.py`

### Endpoint: `get_webrtc_config(extension_name=None)`

Returns to frontend:
```json
{
  "extension": "2211",
  "extension_name": "EXT-2211",
  "sip_uri": "sip:2211@pbx.tavira-group.com",
  "sip_password": "<from DB>",
  "sip_domain": "pbx.tavira-group.com",
  "websocket_servers": ["wss://pbx.tavira-group.com:8089/ws"],
  "ice_servers": [
    {"urls": "stun:stun.l.google.com:19302"},
    {"urls": "stun:stun.l.google.com:19302"},
    {"urls": "turn:157.173.125.136:3478", "username": "webrtc", "credential": "Arrowz2024!"}
  ],
  "registrar_server": "sip:pbx.tavira-group.com",
  "transport": "wss",
  "all_extensions": [...],
  "has_multiple_extensions": true,
  "pbx_public_ip": "157.173.125.136"
}
```

### All API Endpoints

| Method | Function | Purpose |
|--------|----------|---------|
| `get_webrtc_config` | Config + credentials for JsSIP init | Returns ice_servers, sip_uri, ws_servers |
| `get_user_extensions` | List active extensions for user | Multi-extension dropdown |
| `initiate_call` | Create outbound AZ Call Log | Returns call_log name |
| `answer_call` | Mark call log → In Progress | Status update |
| `end_call` | Mark call log → Completed | Duration calc |
| `reject_call` | Mark call log → Missed | Rejection reason |
| `hold_call` | Toggle hold + realtime event | Hold/unhold |
| `send_dtmf` | Log DTMF (client-side JsSIP handles actual DTMF) | Audit trail |
| `transfer_call` | Blind/attended transfer | Via AMI or refer |
| `get_active_calls` | Active calls for user | Dashboard widget |
| `create_call_url` | Deep link helper | Quick dial URLs |
| `log_incoming_call` | Create inbound AZ Call Log | With deadlock retry |
| `update_incoming_call_answered` | Mark inbound → In Progress | Answer tracking |
| `update_call_completed` | Finalize call with duration | Cleanup |
| `update_call_failed` | Mark Failed/Missed | Error reason parsing |
| `reload_asterisk_config` | AMI: reload pjsip+rtp+core | System Manager only |

---

## 5. Current Softphone Architecture (v3)

### File: `softphone_v3.js` (1985 lines)

**Structure:**
```
Lines 1-13      : Header, BUILD marker
Lines 14-128    : IIFE + Cross-Tab Leader Election
Lines 129-169   : Detect installed apps (WhatsApp, Telegram)
Lines 170-230   : SVG Icons definitions
Lines 231-330   : arrowz.softphone = { state, init(), loadExtensions() }
Lines 331-460   : setupJsSIP(), UA event handlers
Lines 461-550   : Incoming call handler (newRTCSession)
Lines 551-930   : UI rendering (renderNavbarWidget, renderDropdown, renderActiveCallUI, ...)
Lines 931-1100  : Dialpad, call timer, status updates
Lines 1100-1265 : Extension switcher, dialpad input handler, quickCall
Lines 1265-1400 : makeCall() — getUserMedia + ICE + ua.call()
Lines 1400-1610 : Session event handlers (peerconnection, confirmed, ended, failed)
Lines 1610-1680 : answerCall() — answer incoming
Lines 1680-1770 : hangup(), endCall()
Lines 1770-1840 : hangupLine(), hangupAll(), multi-line management
Lines 1840-1950 : sendDTMF(), transfer(), audio, notifications
Lines 1950-1985 : Navigation helpers, jQuery init
```

**Key JsSIP Coupling Points** (methods that directly call JsSIP API):
```javascript
// In setupJsSIP():
new JsSIP.WebSocketInterface(wsUrl)        // WebSocket transport
new JsSIP.UA(configuration)                // User Agent creation
this.ua.start()                            // Connect & register
this.ua.stop()                             // Disconnect
this.ua.unregister()                       // SIP UNREGISTER
this.ua.on('connected', ...)               // Events
this.ua.on('disconnected', ...)
this.ua.on('registered', ...)
this.ua.on('unregistered', ...)
this.ua.on('registrationFailed', ...)
this.ua.on('newRTCSession', ...)           // Incoming/outgoing session

// In makeCall():
this.ua.call(targetUri, options)           // Initiate outbound call
// options.pcConfig.iceServers = [...]      // ICE configuration

// In answerCall():
this.session.answer(options)               // Answer incoming call

// In hangup():
this.session.terminate()                   // End call

// In sendDTMF():
this.session.sendDTMF(digit)               // In-band DTMF

// In transfer():
this.session.refer(target)                 // Blind transfer

// Session events (on newRTCSession):
session.on('peerconnection', ...)          // Access RTCPeerConnection
session.on('confirmed', ...)               // Call connected
session.on('ended', ...)                   // Call ended
session.on('failed', ...)                  // Call failed
session.on('hold', ...)                    // On hold
session.on('unhold', ...)                  // Resume
session.on('sdp', ...)                     // SDP manipulation

// In peerconnection handler:
pc.ontrack = (event) => { ... }            // Remote media
pc.oniceconnectionstatechange              // ICE state monitoring
pc.onicegatheringstatechange               // ICE gathering
pc.onicecandidate                          // ICE candidate logging
```

**ICE Server Config Pattern** (appears in both makeCall & answerCall):
```javascript
let iceServers = [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    { urls: 'turn:openrelay.metered.ca:80',
      username: 'openrelayproject', credential: 'openrelayproject' },
    { urls: 'turn:openrelay.metered.ca:443',
      username: 'openrelayproject', credential: 'openrelayproject' },
    { urls: 'turn:openrelay.metered.ca:443?transport=tcp',
      username: 'openrelayproject', credential: 'openrelayproject' }
];
// Then merge with backend ice_servers (from get_webrtc_config)
if (this.config.ice_servers && this.config.ice_servers.length > 0) {
    iceServers = [...this.config.ice_servers, ...iceServers];
}
```

**Multi-Line Support:**
- `maxLines: 4` — up to 4 concurrent calls
- `sessions[]` — array of active JsSIP sessions
- `activeLineIndex` — currently focused line
- `holdAllExcept(idx)` / `switchToLine(idx)` — line switching
- `hangupLine(idx)` / `hangupAll()` — per-line control

**Cross-Tab Leader Election:**
- Uses `BroadcastChannel('arrowz_softphone')` + `localStorage`
- Only leader tab registers SIP UA with Asterisk
- Heartbeat every 2s, timeout 6s
- On leader close → another tab claims leadership
- Non-leader tabs show "Standby", receive call notifications via BroadcastChannel

**SDP Rewriting (Docker NAT workaround):**
- `pbx_public_ip` from backend → rewrite SDP `c=` line and `a=candidate` lines
- Replaces Docker internal IP (`172.23.0.2`) with public IP in remote SDP

---

## 6. AZ Server Config DocType

### JSON Schema Fields (key WebRTC ones)

```json
{
  "fields": [
    {"fieldname": "webrtc_enabled", "fieldtype": "Check", "default": "1"},
    {"fieldname": "stun_server", "fieldtype": "Data", "default": "stun:stun.l.google.com:19302"},
    {"fieldname": "turn_server", "fieldtype": "Data"},
    {"fieldname": "turn_username", "fieldtype": "Data", "depends_on": "turn_server"},
    {"fieldname": "turn_password", "fieldtype": "Password", "depends_on": "turn_server"}
  ]
}
```

**Note**: There is currently NO `ua_provider` / `webrtc_library` field.
This needs to be added to support the adapter pattern.

### Python Controller Key Methods

```python
class AZServerConfig(Document):
    def before_save(self):
        # Auto-build websocket_url, auto-set AMI/SSH host from main host

    def validate(self):
        # Ensure single default server

    def test_connection(self):
        # TCP socket test to host:port

    def test_ami(self):
        # TCP to AMI, read Asterisk banner

    def get_webrtc_config(self):
        # Return WebSocket/STUN/TURN dict

def get_default_server():
    # Get first active default server
```

---

## 7. Known Issues & Recent Fixes

### Issue 1: ICE Failure — No Relay Candidates
- **Symptom**: Browser logs show only `host` and `srflx` candidates, no `relay`
- **Root Cause**: coturn was installed but ports not exposed in docker-compose
- **Fix**: User opened ports 3478 (UDP+TCP) in docker-compose + firewall
- **Status**: ✅ coturn now running (confirmed via STUN test — 56-byte response)
- **Remaining**: Softphone code has OpenRelay TURN hardcoded alongside backend config

### Issue 2: Outgoing 503 Service Unavailable (2211 → 2210)
- **Symptom**: `503 Service Unavailable` immediately on outgoing call
- **Root Cause**: Extension 2210 (plain SIP phone) had WebRTC settings (dtls/ice/avpf) in `pjsip.endpoint.conf`
- **Fix**: Added `[2210](+)` override in `pjsip.endpoint_custom.conf` to disable WebRTC
- **Status**: ✅ File written; ⚠️ PJSIP reload attempted (success reported) but endpoint still showed old values in last check

### Issue 3: Docker NAT SDP
- **Symptom**: Asterisk sends `172.23.0.2` (Docker IP) in SDP to browser
- **Fix**: `ice_host_candidates` in rtp_custom.conf + SDP rewriting in softphone JS
- **Status**: ✅ Working

---

## 8. Build & Development Commands

```bash
# Build arrowz assets only
bench build --app arrowz

# Clear cache after changes
bench --site dev.localhost clear-cache

# Full rebuild
bench build --app arrowz && bench --site dev.localhost clear-cache

# Start dev server (all processes)
bench start

# Database migration (after DocType changes)
bench --site dev.localhost migrate

# Execute Python one-liners
bench --site dev.localhost execute "<python_expression>"

# AMI reload (from within frappe-bench container)
python3 -c "
import socket, time
s = socket.socket(); s.connect(('172.23.0.2', 5038)); s.settimeout(8)
time.sleep(0.2); s.recv(256)
s.send(b'Action: Login\r\nUsername: arrowz_admin\r\nSecret: ArrowzAMI2024!\r\n\r\n')
time.sleep(0.3); s.recv(512)
s.send(b'Action: Command\r\nCommand: module reload res_pjsip.so\r\n\r\n')
time.sleep(3); print(s.recv(4096).decode()[:200])
s.send(b'Action: Logoff\r\n\r\n'); s.close()
"

# Check Asterisk logs
tail -100 /mnt/pbx/logs/asterisk/full
grep -i "webrtc\|ice\|dtls\|2211\|2210" /mnt/pbx/logs/asterisk/full | tail -30
```

---

## 9. Adapter Pattern — Design Plan

### Goal
Replace direct JsSIP coupling in `softphone_v3.js` with a pluggable adapter layer.
Allow switching between SIP/WebRTC libraries via `AZ Server Config`.

### Proposed Adapters

| Adapter | Library | Use Case | SIP Support | Signaling |
|---------|---------|----------|-------------|-----------|
| `jssip` | JsSIP 3.x | Default, current | Full SIP UA | SIP over WSS |
| `sipjs` | SIP.js 0.21+ | Alternative SIP UA | Full SIP UA | SIP over WSS |
| `peerjs` | PeerJS | P2P calls (no PBX) | None | PeerJS cloud/custom |
| `simplewebrtc` | SimpleWebRTC | Group calls | None | Custom signaling |
| `webrtc-native` | webrtc-adapter + raw API | Manual SDP | Manual | Custom |

### Adapter Interface

```javascript
class BaseAdapter {
    constructor(config) {}

    // Lifecycle
    async init()              // Load library, create transport
    async connect()           // Connect WebSocket
    async disconnect()        // Disconnect
    async register()          // SIP REGISTER (if applicable)
    async unregister()        // SIP UNREGISTER
    destroy()                 // Full cleanup

    // Calls
    async makeCall(target, options)    // Returns session handle
    async answerCall(session, options) // Answer incoming
    async hangup(session)              // End call
    async hold(session)                // Hold
    async unhold(session)              // Unhold
    async sendDTMF(session, digit)     // DTMF
    async transfer(session, target)    // Blind transfer
    async attendedTransfer(session, target) // Attended

    // Media
    async getUserMedia(constraints)
    setIceServers(servers)
    getLocalStream()
    getRemoteStream(session)

    // State
    isRegistered()
    isConnected()
    getActiveSessions()

    // Events (EventEmitter pattern)
    on(event, handler)     // Subscribe
    off(event, handler)    // Unsubscribe
    emit(event, data)      // Internal

    // Standard Events:
    // 'connected', 'disconnected', 'registered', 'unregistered',
    // 'registrationFailed', 'incomingCall', 'callConfirmed',
    // 'callEnded', 'callFailed', 'hold', 'unhold',
    // 'iceStateChange', 'remoteStream'
}
```

### New AZ Server Config Field (to add)

```json
{
  "fieldname": "ua_provider",
  "fieldtype": "Select",
  "label": "WebRTC Library",
  "options": "JsSIP\nSIP.js\nPeerJS\nSimpleWebRTC\nWebRTC Native",
  "default": "JsSIP",
  "depends_on": "webrtc_enabled"
}
```

### File Structure (planned)

```
arrowz/public/js/
├── lib/
│   ├── jssip.min.js         # Existing
│   └── sip-0.21.2.min.js    # To add (SIP.js)
├── webrtc_adapters/
│   ├── base_adapter.js      # Abstract base class
│   ├── adapter_loader.js    # Factory: config → adapter instance
│   ├── jssip_adapter.js     # JsSIP implementation
│   ├── sipjs_adapter.js     # SIP.js implementation
│   ├── peerjs_adapter.js    # PeerJS implementation (stub)
│   └── native_adapter.js    # Raw WebRTC + webrtc-adapter (stub)
├── softphone_v3.js          # UI — calls adapter, NOT JsSIP directly
└── ...
```

---

## 10. Frontend JavaScript Namespace

```javascript
window.arrowz = {
    softphone: {
        // State
        initialized, registered, ua, sessions[], session,
        activeLineIndex, maxLines, config, allExtensions, activeExtension,
        audioPlayer, localStream, remoteStream,
        callTimer, callStartTime, callStartTimes,

        // Core methods
        init(), setupJsSIP(), loadExtensions(),
        makeCall(number), answerCall(), hangup(),
        sendDTMF(digit), transfer(),
        hold(), unhold(), switchToLine(idx),
        hangupLine(idx), hangupAll(),

        // UI methods
        renderNavbarWidget(), renderDropdown(),
        openDropdown(), closeDropdown(), toggleDropdown(),
        renderActiveCallUI(), renderIncomingCallUI(),
        showActiveCallUI(), hideCallUI(),
        updateNavbarStatus(status, text),
        updateCallTimer(),

        // Utility
        playRingtone(), stopRingtone(),
        showNotification(), formatPhoneNumber(),
        lookupContact(number), showHistory(), showSettings()
    },
    omni: { ... },        // Omni-channel
    omni_panel: { ... },  // Chat panel
    theme: { ... }        // Theme engine
};
```

---

## 11. Realtime Events (Socket.IO)

### Server → Client
```python
frappe.publish_realtime("softphone_call_event", data, user=user)
frappe.publish_realtime("softphone_status", data, user=user)
frappe.publish_realtime("incoming_call", data, user=user)
frappe.publish_realtime("call_answered", data, user=user)
frappe.publish_realtime("call_ended", data, user=user)
```

### Client Subscriptions
```javascript
frappe.realtime.on("softphone_call_event", handler)
frappe.realtime.on("incoming_call", handler)
```

---

## 12. CSS Theme Compatibility

The softphone UI uses these CSS class prefixes:
- `.sp-*` — Softphone-specific classes
- `.arrowz-*` — App-wide classes
- Theme variables defined in `arrowz_theme.css` and `arrowz_theme.js`

The UI layer in `softphone_v3.js` is self-contained:
- Renders via `innerHTML` (no framework dependency)
- All HTML generated in JS methods
- CSS file: `softphone_v2.css` (loaded in hooks.py, works for v3 too)
- Theme-agnostic: adapter swap does NOT affect UI — only the SIP/media layer changes

---

## 13. Testing Checklist

After any softphone change, verify:

- [ ] Registration: Status shows "Registered" / green dot
- [ ] Outgoing call: Dial 2210 from 2211 → phone rings
- [ ] Incoming call: Call 2211 from 2210 → softphone rings
- [ ] Answer: Click answer → ringing stops, audio flows both ways
- [ ] Hangup: Click hangup → call ends cleanly
- [ ] DTMF: Send digits during call → heard on other end
- [ ] Transfer: Transfer to another extension
- [ ] Multi-line: Make 2nd call while 1st on hold
- [ ] Cross-tab: Open 2 tabs → only 1 registers (leader)
- [ ] Reconnect: Refresh page → re-registers automatically
- [ ] ICE: Console shows `relay` candidates (TURN working)
- [ ] SDP: No Docker IPs (172.x) in SDP sent to browser

### Quick Console Checks
```javascript
// Check registration
arrowz.softphone.registered  // should be true

// Check UA
arrowz.softphone.ua          // JsSIP.UA instance

// Check config
arrowz.softphone.config.ice_servers  // should include TURN

// Check adapter (after adapter pattern)
arrowz.softphone.adapter.constructor.name  // "JsSIPAdapter" etc
```

---

## 14. Appendix: Key File Paths (Absolute)

```
# Softphone JS
/workspace/development/frappe-bench/apps/arrowz/arrowz/public/js/softphone_v3.js
/workspace/development/frappe-bench/apps/arrowz/arrowz/public/js/softphone_v2.js

# WebRTC API
/workspace/development/frappe-bench/apps/arrowz/arrowz/api/webrtc.py

# Hooks
/workspace/development/frappe-bench/apps/arrowz/arrowz/hooks.py

# DocType: AZ Server Config
/workspace/development/frappe-bench/apps/arrowz/arrowz/arrowz/doctype/az_server_config/az_server_config.json
/workspace/development/frappe-bench/apps/arrowz/arrowz/arrowz/doctype/az_server_config/az_server_config.py
/workspace/development/frappe-bench/apps/arrowz/arrowz/arrowz/doctype/az_server_config/az_server_config.js

# CSS
/workspace/development/frappe-bench/apps/arrowz/arrowz/public/css/softphone_v2.css

# JsSIP Library
/workspace/development/frappe-bench/apps/arrowz/arrowz/public/js/lib/jssip.min.js

# PBX Configs (read-only mount)
/mnt/pbx/etc/asterisk/pjsip.endpoint_custom.conf
/mnt/pbx/etc/asterisk/rtp_custom.conf
/mnt/pbx/etc/asterisk/manager_custom.conf

# Asterisk Logs
/mnt/pbx/logs/asterisk/full
```
