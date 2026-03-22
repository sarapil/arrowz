# Dinstar UC2000-VE GSM Gateway — API & Integration Guide

> **Arrowz** integration for Dinstar UC2000-VE-8G GSM VoIP Gateway.  
> Full Python client, Frappe REST API, live dashboard page, and topology graph node.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Network Topology](#network-topology)
3. [Device Web Interface Catalog](#device-web-interface-catalog)
4. [Python Client (`DinstarClient`)](#python-client-dinstarclient)
5. [Frappe REST API Endpoints](#frappe-rest-api-endpoints)
6. [Dashboard Page](#dashboard-page)
7. [Topology Integration](#topology-integration)
8. [Data Models & Enums](#data-models--enums)
9. [Configuration](#configuration)
10. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────┐
│         Frappe Web UI               │
│  ┌─────────────┐  ┌──────────────┐  │
│  │  Dashboard   │  │  Topology    │  │
│  │  Page (JS)   │  │  Graph (JS)  │  │
│  └──────┬───────┘  └──────┬───────┘  │
│         │                  │          │
│  ┌──────▼──────────────────▼───────┐  │
│  │     Frappe API Layer            │  │
│  │   arrowz/api/dinstar.py         │  │
│  │   @frappe.whitelist() endpoints │  │
│  └──────────────┬──────────────────┘  │
│                 │                     │
│  ┌──────────────▼──────────────────┐  │
│  │     DinstarClient               │  │
│  │   arrowz/integrations/dinstar/  │  │
│  │   • client.py   (HTTP session)  │  │
│  │   • parser.py   (HTML→Dict)    │  │
│  │   • constants.py (URLs, enums)  │  │
│  └──────────────┬──────────────────┘  │
└─────────────────┼─────────────────────┘
                  │ HTTPS (10.10.1.2)
                  │ OpenVPN TLS tunnel
┌─────────────────▼─────────────────────┐
│  Dinstar UC2000-VE-8G                 │
│  • 8× GSM ports (SIM slots)          │
│  • Embedded web UI (MatrixSSL/4.3.0)  │
│  • goform-based POST API              │
│  • SIP registration → FreePBX         │
└───────────────────────────────────────┘
```

### Connection Path

| Hop | From | To | Protocol | Port |
|-----|------|-----|----------|------|
| 1 | Frappe (Docker) | VPS | Docker bridge | — |
| 2 | VPS (10.10.1.1) | Dinstar (10.10.1.2) | OpenVPN TLS | UDP 51821 (tun1) |
| 3 | Client → Dinstar | Web UI | HTTPS | 443 |
| 4 | Dinstar ports | FreePBX | PJSIP/UDP | 51600 |

---

## Network Topology

```
FreePBX (Asterisk 21)
  │ SIP/UDP :51600
  │
  ├── gsm-port1  (SipAcc: gsm-port1, Psw: Gsm1@Arwz2026)
  ├── gsm-port2  (SipAcc: gsm-port2, Psw: Gsm2@Arwz2026)
  ├── gsm-port3  (SipAcc: gsm-port3, Psw: Gsm3@Arwz2026)
  ├── gsm-port4  (SipAcc: gsm-port4, Psw: Gsm4@Arwz2026)
  ├── gsm-port5  (SipAcc: gsm-port5, Psw: Gsm5@Arwz2026)
  ├── gsm-port6  (SipAcc: gsm-port6, Psw: Gsm6@Arwz2026)
  ├── gsm-port7  (SipAcc: gsm-port7, Psw: Gsm7@Arwz2026)  ← Port with SIM (Etisalat Egypt)
  └── gsm-port8  (SipAcc: gsm-port8, Psw: Gsm8@Arwz2026)

Dialplan:
  • from-gsm-inbound     → Routes GSM incoming calls to extensions
  • gsm-outbound         → Round-robin across 8 ports with jitter buffer
  • from-internal-custom  → Handles _0X., _+0X., _+20X., _+X. patterns
```

---

## Device Web Interface Catalog

The Dinstar UC2000-VE web UI is a goform-based embedded interface using:
- **Pages**: `.htm` files with inline JavaScript data
- **Forms**: POST to `/goform/*` endpoints
- **AJAX**: GET to `/goform/*` for live data
- **Session**: Cookie-based `JSESSIONID`, login via `/goform/IADIdentityAuth`

### Page Categories (80+ pages)

| Category | Pages | Description |
|----------|-------|-------------|
| **System** | `enSysInfo`, `enSummary`, `enLocalNetwork`, `enManageCfg`, `enPassword`, `enRestart`, `enFirmwareUpload`, `enDataRestore`, `enDefaultSet`, `enSysLog`, `enFileLog`, `enProvision` | System info, network config, management |
| **SIP/VoIP** | `enSIPCfg`, `enPortList`, `enPortInfo`, `enServiceCfg`, `enMediaParamCfg`, `enDigitMap`, `enCallConference`, `enCallForwardTimeCfg` | SIP registration, codec, DTMF, call features |
| **Statistics** | `enCallStat`, `enCurrentCallStat`, `enCallCDR`, `enRTPStat`, `enProtocolStat`, `enEccStat` | Call stats, CDR, RTP quality, error codes |
| **GSM/Mobile** | `enGsmOperate`, `enGSMEvent`, `enWIAPortStatNew`, `enWIABasicCfg`, `enWIASimCfg`, `enWIACarrierCfg`, `enWIACarrierRule`, `enIMEITerm` | Module control, SIM config, carrier rules |
| **SMS** | `enSMSCfg`, `enSMSOverview`, `enWIASendMsg`, `enSmsRecvNew`, `enSmsSendRecord`, `enSMSRouting`, `enSMSBalance` | SMS send/receive/routing/balance |
| **Routing** | `enPortGroup`, `enIpGroup`, `enIpCfg` | Port grouping, IP routing |
| **Heartbeat** | `enHBBasicCfg`, `enHBSim`, `enHBBalance`, `enHBPhoneNumber`, `enScheduleTaskCfg` | SIM heartbeat, balance check |
| **Network** | `enVPNCfg`, `enVLANCfg`, `enFirewallACCRule`, `enPingTest`, `enTracertTest`, `enNetworkCaptureNew` | VPN, VLAN, firewall, diagnostics |

### GoForm Endpoints (45+ endpoints)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/goform/IADIdentityAuth` | POST | Login authentication |
| `/goform/SipCfg` | POST | Update SIP proxy config |
| `/goform/PortCfg` | POST | Update per-port SIP accounts |
| `/goform/EiaMediaParamCfg` | POST | Update codecs/DTMF/tones |
| `/goform/LocalNetwork` | POST | Update WAN/LAN settings |
| `/goform/ManageCfg` | POST | Update NTP/web ports/SSH |
| `/goform/WIAMsgSend` | POST | Send SMS message |
| `/goform/WIASMSRouteCfg` | POST | Set SMS routing rules |
| `/goform/WIAGSMRule` | POST | Set GSM operate rules |
| `/goform/ModuleGotoResetNew` | POST | Reset GSM module |
| `/goform/ModuleGotoBlockNew` | POST | Block/unblock module |
| `/goform/CallGotoBlockNew` | POST | Block/unblock calls |
| `/goform/Restart` | POST | Reboot device |
| `/goform/EiaSummaryQuery` | GET | Live summary AJAX data |
| `/goform/WebGetOvpnInfo` | GET | OpenVPN status |

See `arrowz/integrations/dinstar/constants.py` for the complete catalog.

---

## Python Client (`DinstarClient`)

**Location**: `arrowz/integrations/dinstar/client.py`

### Quick Start

```python
from arrowz.integrations.dinstar import DinstarClient

# Connect
client = DinstarClient(
    host="10.10.1.2",
    username="admin",
    password="admin",
    protocol="https",
    verify_ssl=False,
    timeout=15,
)
client.login()

# Read status
info = client.get_system_info()
ports = client.get_port_status()
stats = client.get_call_stats()

# Full dashboard data (all at once)
full = client.get_full_status()
print(f"Health: {full['device_health']['status']} ({full['device_health']['score']}/100)")

# Send SMS
client.send_sms(port=7, number="01234567890", message="Hello from Arrowz!")

# Control modules
client.reset_module(port=0)
client.block_module(port=3)
client.unblock_module(port=3)

# Update config
client.set_media_config(CoderPT0="8", DTMFMethod="0")  # PCMA + RFC2833
```

### Session Management

The client uses cookie-based sessions with automatic re-login:

- Login POST → `/goform/IADIdentityAuth` with `username` + `password`
- Session cookie: `JSESSIONID`
- Auto re-login every **5 minutes** (configurable via `_session_lifetime`)
- All methods call `_ensure_auth()` before making requests

### API Method Reference

#### System

| Method | Returns | Description |
|--------|---------|-------------|
| `get_system_info()` | `Dict` | Model, uptime, WAN mode, NTP time, VPN status |
| `get_summary()` | `Dict` | Live summary via AJAX polling |
| `test_connection()` | `Dict` | Connectivity test with latency measurement |
| `restart_device()` | `str` | ⚠️ Reboot device (drops all calls!) |

#### Ports & GSM

| Method | Returns | Description |
|--------|---------|-------------|
| `get_port_status()` | `List[Dict]` | Per-port GSM status (SIM, power, signal, band) |
| `get_port_info()` | `List[Dict]` | Port type and SIP account mapping |
| `reset_module(port)` | `str` | Reset GSM module on port |
| `block_module(port)` | `str` | Block GSM module |
| `unblock_module(port)` | `str` | Unblock GSM module |
| `block_call(port)` | `str` | Block calls on port |
| `unblock_call(port)` | `str` | Unblock calls on port |

#### Call Statistics

| Method | Returns | Description |
|--------|---------|-------------|
| `get_call_stats()` | `Dict` | Per-port call stats with totals and ASR |
| `get_ecc_stats()` | `List[Dict]` | Error cause code breakdown per port |
| `get_current_calls()` | `List` | Currently active calls |
| `get_cdr_records(port, start, end)` | `List` | Call Detail Records |

#### SMS

| Method | Returns | Description |
|--------|---------|-------------|
| `send_sms(port, number, message)` | `str` | Send single SMS |
| `send_sms_batch(port, numbers, msg)` | `str` | Send to multiple numbers |
| `stop_sms_send()` | `str` | Cancel ongoing SMS send |
| `get_received_sms(port, filter)` | `List` | Received SMS messages |
| `get_sms_overview()` | `List` | Per-port SMS counters |
| `get_sms_routing()` | `List[Dict]` | SMS routing rules |
| `set_sms_routing(rules)` | `str` | Update SMS routing rules |

#### Configuration

| Method | Returns | Description |
|--------|---------|-------------|
| `get_sip_config()` | `Dict` | Full SIP configuration |
| `set_sip_config(**kwargs)` | `str` | Update SIP settings |
| `get_port_config()` | `Dict` | Per-port SIP account config |
| `set_port_config(port, **kwargs)` | `str` | Update single port SIP |
| `get_media_config()` | `Dict` | Codecs, DTMF, tones |
| `set_media_config(**kwargs)` | `str` | Update media settings |
| `get_network_config()` | `Dict` | WAN/LAN configuration |
| `get_management_config()` | `Dict` | NTP, ports, SSH/telnet |
| `get_service_config()` | `Dict` | Dial settings, hook flash |
| `set_service_config(**kwargs)` | `str` | Update service settings |
| `get_wia_basic_config()` | `Dict` | GSM advanced config |
| `set_wia_basic_config(**kwargs)` | `str` | Update GSM advanced |
| `get_vpn_config()` | `Dict` | OpenVPN status and config |

#### GSM Operations

| Method | Returns | Description |
|--------|---------|-------------|
| `get_gsm_operate_rules()` | `List[Dict]` | Prefix match/add/delete rules |
| `set_gsm_operate_rules(rules)` | `str` | Update GSM operate rules |
| `get_gsm_events(port)` | `List` | GSM events (registration, signal) |

#### Dashboard

| Method | Returns | Description |
|--------|---------|-------------|
| `get_full_status()` | `Dict` | Everything above in one call |
| `_calculate_health(status)` | `Dict` | Health score (0-100) with 5 checks |

### Health Score Calculation

The health system runs **5 checks** with a maximum score of **100**:

| Check | Points | Pass Condition |
|-------|--------|----------------|
| System Reachable | 25 | Device responds to requests |
| Stable Uptime | 15 | Uptime > 5 minutes |
| SIM Cards Present | 20 | At least 1 SIM detected |
| Powered Modules | 20 | At least 1 module powered on |
| ASR Quality | 20 | ASR ≥ 50% (or no calls yet) |

**Status thresholds**: Score ≥ 80 → `healthy` | ≥ 50 → `degraded` | < 50 → `critical`

### Exception Hierarchy

```python
DinstarError                  # Base exception
├── DinstarAuthError          # Login failed (wrong credentials)
└── DinstarConnectionError    # Network unreachable / timeout
```

---

## Frappe REST API Endpoints

**Location**: `arrowz/api/dinstar.py`

All endpoints require authentication and **System Manager** or **Network Manager** role.

### Read Endpoints

```
GET /api/method/arrowz.api.dinstar.get_status
GET /api/method/arrowz.api.dinstar.get_port_status
GET /api/method/arrowz.api.dinstar.get_call_stats
GET /api/method/arrowz.api.dinstar.get_ecc_stats
GET /api/method/arrowz.api.dinstar.get_sip_config
GET /api/method/arrowz.api.dinstar.get_media_config
GET /api/method/arrowz.api.dinstar.get_network_config
GET /api/method/arrowz.api.dinstar.get_sms_overview
GET /api/method/arrowz.api.dinstar.get_gsm_status
GET /api/method/arrowz.api.dinstar.get_vpn_status
GET /api/method/arrowz.api.dinstar.test_connection
```

### Write Endpoints

```
POST /api/method/arrowz.api.dinstar.send_sms
  Body: { port: 7, number: "01234567890", message: "Hello" }

POST /api/method/arrowz.api.dinstar.control_module
  Body: { port: 0, action: "reset"|"block"|"unblock"|"block_call"|"unblock_call" }

POST /api/method/arrowz.api.dinstar.update_sip_config
  Body: { SipPxyIP: "10.10.1.1", SipPxyPort: "51600" }

POST /api/method/arrowz.api.dinstar.update_media_config
  Body: { CoderPT0: "8", DTMFMethod: "0" }
```

### Topology Endpoint

```
GET /api/method/arrowz.api.dinstar.get_topology_node
  Returns: { node: {...}, child_nodes: [...], edges: [...] }
```

### Example: cURL

```bash
# Get full status
curl -s -H "Authorization: token api_key:api_secret" \
  "http://dev.localhost:8000/api/method/arrowz.api.dinstar.get_status" | jq .

# Send SMS
curl -X POST -H "Authorization: token api_key:api_secret" \
  -H "Content-Type: application/json" \
  -d '{"port": 7, "number": "01234567890", "message": "Test"}' \
  "http://dev.localhost:8000/api/method/arrowz.api.dinstar.send_sms"

# Test connection
curl -s -H "Authorization: token api_key:api_secret" \
  "http://dev.localhost:8000/api/method/arrowz.api.dinstar.test_connection" | jq .
```

### Example: JavaScript (Frappe Client)

```javascript
// Full status
const status = await frappe.xcall("arrowz.api.dinstar.get_status");
console.log("Health:", status.device_health.status, status.device_health.score);

// Send SMS
await frappe.xcall("arrowz.api.dinstar.send_sms", {
    port: 7,
    number: "01234567890",
    message: "Hello from Frappe!"
});

// Control module
await frappe.xcall("arrowz.api.dinstar.control_module", {
    port: 0,
    action: "reset"
});
```

### Client Factory (`_get_client`)

The API layer creates `DinstarClient` instances with configuration lookup:

1. **AZ Server Config** doctype (if it has `dinstar_host` / `dinstar_ip` fields)
2. **site_config.json** keys: `dinstar_host`, `dinstar_username`, `dinstar_password`, `dinstar_protocol`
3. **Fallback**: `10.10.1.2` / `admin` / `admin` / `https`

To configure via site_config:
```json
{
  "dinstar_host": "10.10.1.2",
  "dinstar_username": "admin",
  "dinstar_password": "admin",
  "dinstar_protocol": "https"
}
```

---

## Dashboard Page

**URL**: `/app/dinstar-dashboard`  
**Location**: `arrowz/arrowz/page/dinstar_dashboard/`  
**Roles**: System Manager, Network Manager

### Features

| Section | Description |
|---------|-------------|
| **Health Banner** | Animated SVG score ring (0-100), 5 health checks, system meta (uptime, WAN, NTP, ports) |
| **Port Grid** | 8 GSM module cards showing power state, SIM status, SIP account, band type, reset/block controls |
| **Call Statistics** | Per-port table: Total, Answered, Failed, Busy, No Answer, Rejected, Duration, ASR% |
| **ECC Statistics** | Error cause code breakdown: No Carrier, No Dialtone, Congestion, Unallocated, etc. |
| **SIP Config** | Server IP, port, transport, register interval, session timers |
| **Media Config** | Codec (PCMA/PCMU/G729), DTMF method, call progress tone, SRTP mode, RTP port |
| **Network Config** | WAN mode (DHCP/Static/PPPoE), IP, gateway, LAN settings, NTP, web ports |
| **SMS Panel** | Send form (port, number, message) + routing rules table (32 rules) |
| **GSM Rules** | Operate rules display (prefix match, delete, add per port) |

### Auto-Refresh

The dashboard auto-refreshes every **30 seconds** (configurable). Toolbar buttons:

- 🔄 **Refresh** — Manual immediate refresh
- 🔌 **Test Connection** — Connectivity test with latency
- ⏱ **Auto Refresh** (toggle on/off)

### File Structure

```
arrowz/arrowz/page/dinstar_dashboard/
├── __init__.py                     # Empty init
├── dinstar_dashboard.json          # Frappe Page DocType definition
├── dinstar_dashboard.py            # Empty server-side (all via API)
├── dinstar_dashboard.js            # ~540 lines — DinstarDashboard class
└── dinstar_dashboard.html          # Template with all sections

arrowz/public/css/
└── dinstar_dashboard.css           # ~300 lines — styling with responsive breakpoints
```

### Port Card States

| State | Visual | Meaning |
|-------|--------|---------|
| `port-active` | Green left border, bright bg | SIM present + Module powered on |
| `port-nosim` | Amber left border | Module on but no SIM card |
| `port-off` | Gray left border, dim | Module powered off, no SIM |
| `port-off-sim` | Red left border | Has SIM but module off |

---

## Topology Integration

The Dinstar gateway integrates into the Arrowz Topology page (`/app/arrowz-topology`) as a group of nodes.

### Node Types

| Type | Icon | Color | Description |
|------|------|-------|-------------|
| `az-dinstar-gw` | 📱 | Rose (#f43f5e) | Gateway device node |
| `az-dinstar-port` | 📶 | Pink (#ec4899) | Individual GSM port |
| `az-group-gsm` | 📱 | Rose | Group container for all GSM nodes |

### Graph Structure

```
[Server Config] ──(GSM, animated)──▶ [Dinstar UC2000-VE (8P)]
                                         │
                                         ├── [Port 0 (gsm-port1)]
                                         ├── [Port 1 (gsm-port2)]
                                         ├── ...
                                         └── [Port 7 (gsm-port8)]
```

### Data Flow

1. Topology page's `fetchData()` makes a parallel request to `arrowz.api.dinstar.get_topology_node`
2. Returns gateway node + 8 child port nodes + edges
3. `transformData()` renders them in the "📱 GSM Gateway" group
4. Port nodes show SIP account, SIM presence, and power status
5. Edge from server-config to gateway is animated with "GSM" label

### Topology Data Format

```json
{
  "node": {
    "id": "dinstar-gw",
    "label": "Dinstar UC2000-VE (8P)",
    "type": "az-dinstar-gw",
    "data": {
      "total_ports": 8,
      "uptime": "0d 5h 32m",
      "vpn_enabled": true,
      "sim_count": 1,
      "powered_count": 0
    }
  },
  "child_nodes": [
    {
      "id": "dinstar-port-0",
      "label": "Port 0 (gsm-port1)",
      "type": "az-dinstar-port",
      "data": {
        "port_index": 0,
        "sip_account": "gsm-port1",
        "status": "powered_off",
        "is_powered": false,
        "has_sim": false
      }
    }
  ],
  "edges": [
    { "source": "dinstar-gw", "target": "dinstar-port-0", "type": "az-manages" }
  ]
}
```

---

## Data Models & Enums

### Port Status (WIAPortStatNew)

```json
{
  "port_index": 7,
  "port_name": "Port 7",
  "gsm_port_name": "gsm-port8",
  "Clir": "0",
  "TxGain": "3",
  "RxGain": "7",
  "BandType": "512",
  "band_type_label": "Default (Auto)",
  "NetWorkMode": "0",
  "network_mode_label": "Auto",
  "SMSC": "+20112008000",
  "Modulepower": "ON",
  "has_sim": true,
  "is_powered": true
}
```

### Call Statistics

```json
{
  "ports": [
    {
      "port": 0,
      "total_calls": 15,
      "answered": 12,
      "failed": 1,
      "busy": 0,
      "no_answer": 2,
      "rejected": 0,
      "duration_seconds": 1842,
      "asr_percent": 80.0
    }
  ],
  "totals": {
    "port": "TOTAL",
    "total_calls": 15,
    "answered": 12,
    "asr_percent": 80.0,
    "duration_seconds": 1842
  }
}
```

### Health Score

```json
{
  "score": 80,
  "max_score": 100,
  "status": "healthy",
  "checks": [
    { "name": "System Reachable", "status": "pass", "points": 25 },
    { "name": "Stable Uptime", "status": "pass", "points": 15 },
    { "name": "SIM Cards (1/8)", "status": "pass", "points": 20 },
    { "name": "Powered Modules (0/8)", "status": "warn", "points": 0 },
    { "name": "ASR (no calls yet)", "status": "pass", "points": 20 }
  ]
}
```

### Enum Maps

#### Codec Map

| Code | Name | Label | Bandwidth |
|------|------|-------|-----------|
| 0 | PCMU | G.711 µ-law | 64 kbps |
| 8 | PCMA | G.711 A-law | 64 kbps |
| 4 | G723 | G.723.1 | 6.3 kbps |
| 18 | G729 | G.729A | 8 kbps |
| 2 | G726 | G.726-32 | 32 kbps |
| 3 | GSM | GSM FR | 13 kbps |
| 98 | iLBC | iLBC | 15 kbps |

#### DTMF Method Map

| Code | Method |
|------|--------|
| 0 | RFC2833 |
| 1 | SIP INFO |
| 2 | Inband |
| 3 | RFC2833 + SIP INFO |

#### Call Progress Tone Map

| Code | Country |
|------|---------|
| 0 | China |
| 1 | USA |
| 2 | UK |
| 8 | India |
| 12 | Turkey ← currently configured |
| 15 | Custom |

#### Port Status Map

| Status | Label | Color | Icon |
|--------|-------|-------|------|
| Idle | Idle | Green | ✅ |
| Talking | In Call | Amber | 📞 |
| Ringing | Ringing | Blue | 🔔 |
| Blocked | Blocked | Red | 🚫 |
| NoSIM | No SIM | Gray | ⚠️ |
| PowerOff | Power Off | Dark | ⬛ |

#### Signal Strength (dBm)

| Range | Bars | Label |
|-------|------|-------|
| -70 to 0 | 5 | Excellent |
| -85 to -70 | 4 | Good |
| -100 to -85 | 3 | Fair |
| -110 to -100 | 2 | Poor |
| -120 to -110 | 1 | Very Poor |
| < -120 | 0 | No Signal |

---

## Configuration

### site_config.json

Add to `sites/dev.localhost/site_config.json`:

```json
{
  "dinstar_host": "10.10.1.2",
  "dinstar_username": "admin",
  "dinstar_password": "admin",
  "dinstar_protocol": "https"
}
```

### Current Device State (as of build)

| Setting | Value |
|---------|-------|
| Device IP | 10.10.1.2 (OpenVPN tun1) |
| Web Auth | admin / admin |
| Total Ports | 8 |
| SIM Present | Port 7 only (Etisalat Egypt, SMSC: +20112008000) |
| Module Power | All OFF |
| WAN Mode | DHCP (192.168.11.1) |
| VPN | OpenVPN enabled |
| NTP | 0.pool.ntp.org |
| Web Ports | HTTP 80, HTTPS 443 |
| Telnet | Port 23, enabled |
| SSH | Disabled |
| SIP Transport | UDP |
| SIP Proxy | 10.10.1.1:51600 |
| Codec | PCMA (G.711 A-law) |
| DTMF | RFC2833 (Payload 101) |
| Call Tone | Turkey (#12) |
| WAN MTU | 1400 |

---

## Troubleshooting

### Connection Issues

```bash
# Test VPN connectivity
ssh -p 1352 root@157.173.125.136 "ping -c 3 10.10.1.2"

# Test HTTPS access
ssh -p 1352 root@157.173.125.136 "curl -sk https://10.10.1.2/enSysInfo.htm | head -20"

# From Frappe console
bench --site dev.localhost console
>>> from arrowz.integrations.dinstar import DinstarClient
>>> c = DinstarClient("10.10.1.2")
>>> c.test_connection()
```

### Parser Issues

If the device firmware changes its HTML format:

1. Fetch the raw page: `client._get_page("system_info")`
2. Check the JavaScript data pattern (JSON var, MM_callJS, document.write)
3. Update the corresponding parser method in `parser.py`
4. Patterns to look for:
   - `var text = '{...}';` → `parse_json_var()`
   - `onLoad="MM_callJS(...)"` → `parse_onload_args()`
   - `document.write("<tr>...")` → `parse_table_rows()`
   - `<input name="..." value="...">` → `parse_form_fields()`

### Dashboard Not Loading

```bash
# Rebuild assets
bench build --app arrowz

# Clear cache
bench --site dev.localhost clear-cache

# Check the page exists
bench --site dev.localhost console
>>> frappe.get_doc("Page", "dinstar-dashboard")
```

### API Errors

All API errors are logged to Frappe's error log:
- Check: **Setup > Error Log** in the Frappe UI
- Or: `bench --site dev.localhost console` → `frappe.get_all("Error Log", filters={"method": ["like", "%dinstar%"]})`

---

## File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `arrowz/integrations/dinstar/__init__.py` | 51 | Package init, exports |
| `arrowz/integrations/dinstar/constants.py` | 316 | 80+ page URLs, 45+ goforms, enum maps |
| `arrowz/integrations/dinstar/parser.py` | 452 | HTML/JS parser (15+ methods) |
| `arrowz/integrations/dinstar/client.py` | 970 | HTTP client (50+ methods) |
| `arrowz/api/dinstar.py` | 443 | Frappe API (14 endpoints) |
| `arrowz/arrowz/page/dinstar_dashboard/dinstar_dashboard.js` | 544 | Dashboard UI class |
| `arrowz/arrowz/page/dinstar_dashboard/dinstar_dashboard.html` | — | Dashboard template |
| `arrowz/arrowz/page/dinstar_dashboard/dinstar_dashboard.json` | — | Page DocType config |
| `arrowz/public/css/dinstar_dashboard.css` | ~300 | Dashboard styles |
| `arrowz/arrowz/page/arrowz_topology/arrowz_topology.js` | — | Modified for Dinstar nodes |
| **Total** | **~3100** | — |

---

*Built for Arrowz v16.0.0 — MIT License — 2026*
