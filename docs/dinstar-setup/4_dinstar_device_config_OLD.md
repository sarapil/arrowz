# Dinstar UC2000-VE-8G — Device Configuration Guide

## Architecture (8-Port Individual Registration via VPN)

```
  Egypt Office                             VPS (157.173.125.136)
┌─────────────────────┐                 ┌──────────────────────────────────┐
│                     │                 │  FreePBX Container               │
│  ┌────────────────┐ │                 │                                  │
│  │ Dinstar        │ │   OpenVPN TLS   │  ┌────────────────────┐          │
│  │ UC2000-VE-8G   │═╪═══(UDP 51821)══╪══│ OpenVPN TLS Server │          │
│  │                │ │   tls-auth      │  │ tun1: 10.10.1.1    │          │
│  │ tun: 10.10.1.2 │ │                 │  └─────────┬──────────┘          │
│  │                │ │                 │            │                      │
│  │ Port 1: gsm-port1 ─────────────────▶ Asterisk PJSIP (51600/udp)    │
│  │ Port 2: gsm-port2 ─────────────────▶   8 endpoints: gsm-port1..8   │
│  │ Port 3: gsm-port3 ─────────────────▶   8 extensions: 7001-7008     │
│  │ Port 4: gsm-port4 ─────────────────▶                                │
│  │ Port 5: gsm-port5 ─────────────────▶ Inbound:  port N → ext 700N   │
│  │ Port 6: gsm-port6 ─────────────────▶ Outbound: round-robin all     │
│  │ Port 7: gsm-port7 ─────────────────▶                                │
│  │ Port 8: gsm-port8 ─────────────────▶                                │
│  │                │ │                 │                                  │
│  │ 8× SIM Cards  │ │                 │  ┌────────────────────┐          │
│  └────────────────┘ │                 │  │ Extensions:        │          │
│                     │                 │  │ 2210, 2211, etc.   │          │
│  ┌────────────────┐ │   OpenVPN S.Key │  │ 7001-7008 (GSM)    │          │
│  │ ARKAN PHONE    │═╪═══(UDP 51820)══╪══│ tun0: 10.10.0.1    │          │
│  │ tun: 10.10.0.2 │ │                 │  └────────────────────┘          │
│  └────────────────┘ │                 └──────────────────────────────────┘
└─────────────────────┘
```

**Architecture**: Each of the 8 GSM ports registers independently as a separate SIP
endpoint. This allows per-port routing for incoming calls and round-robin distribution
for outgoing calls.

## Port-Extension Mapping

| GSM Port | SIP Username | Password | Extension | Purpose |
|----------|-------------|----------|-----------|---------|
| Port 1 | `gsm-port1` | `Gsm1@Arwz2026` | 7001 | SIM 1 owner |
| Port 2 | `gsm-port2` | `Gsm2@Arwz2026` | 7002 | SIM 2 owner |
| Port 3 | `gsm-port3` | `Gsm3@Arwz2026` | 7003 | SIM 3 owner |
| Port 4 | `gsm-port4` | `Gsm4@Arwz2026` | 7004 | SIM 4 owner |
| Port 5 | `gsm-port5` | `Gsm5@Arwz2026` | 7005 | SIM 5 owner |
| Port 6 | `gsm-port6` | `Gsm6@Arwz2026` | 7006 | SIM 6 owner |
| Port 7 | `gsm-port7` | `Gsm7@Arwz2026` | 7007 | SIM 7 owner |
| Port 8 | `gsm-port8` | `Gsm8@Arwz2026` | 7008 | SIM 8 owner |

**SIP Server**: `10.10.1.1` (VPN IP)  
**SIP Port**: `51600` (UDP)

## Step 1: Access Dinstar Web Interface

1. Connect to the Dinstar via Ethernet
2. Default IP: `192.168.1.1` (check your manual)
3. Default login: `admin` / `admin` (CHANGE THIS!)
4. Browser: `http://192.168.1.1`

## Step 2: Network Settings

Navigate to: **System Configuration → Network → LAN Setting**

| Setting | Value | Notes |
|---------|-------|-------|
| IP Address | `192.168.x.50` | Static IP on your LAN |
| Subnet Mask | `255.255.255.0` | Match your LAN |
| Default Gateway | `192.168.x.1` | Your router |
| DNS Server | `8.8.8.8` | Or your local DNS |

> ⚠️ **Important**: Use a STATIC IP. DHCP may change the IP and break the VPN.

## Step 3: Configure OpenVPN on Dinstar

Navigate to: **System Configuration → Network → VPN** (or **System → OpenVPN**)

### Option A: Upload .ovpn file (Recommended)
1. Download `dinstar-tls.ovpn` from the VPS:
   ```bash
   scp -P 1352 root@157.173.125.136:/opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn .
   ```
2. Upload the file to the Dinstar web UI under VPN/OpenVPN settings
3. Enable VPN

### Option B: Manual Configuration (if the UI requires separate fields)

| Setting | Value |
|---------|-------|
| **Enable VPN** | ✅ Enabled |
| **VPN Type** | OpenVPN |
| **Server Address** | `157.173.125.136` |
| **Server Port** | `51821` |
| **Protocol** | `UDP` |
| **Device** | `TUN` |
| **Cipher** | `AES-256-CBC` |
| **Auth/HMAC** | `SHA1` ⚠️ NOT SHA256! |
| **TLS Auth** | Enabled, Direction = `1` (client) |

**Certificate Fields** (copy from `dinstar-tls.ovpn`):
- **CA Certificate**: Content between `<ca>` and `</ca>` tags
- **Client Certificate**: Content between `<cert>` and `</cert>` tags
- **Client Key**: Content between `<key>` and `</key>` tags
- **TLS Auth Key**: Content between `<tls-auth>` and `</tls-auth>` tags

> ⚠️ **IMPORTANT**: Auth MUST be SHA1, not SHA256. Dinstar has OpenVPN 2.3.6 which
> requires SHA1 for compatibility with our server (which uses `compat-mode 2.3.0`).

### After Enabling VPN:
- Wait 10-30 seconds for connection
- Check **System Status → VPN Status** — should show "Connected"
- The Dinstar gets IP: `10.10.1.2` (from pool `10.10.1.0/24`)
- It can now reach FreePBX at: `10.10.1.1`

### Verify VPN (from VPS):
```bash
# Check if Dinstar is connected
docker exec initpbx-freepbx-1 tail -10 /var/log/openvpn-dinstar-tls.log

# Ping Dinstar through VPN
docker exec initpbx-freepbx-1 ping -c 3 10.10.1.2
```

## Step 4: SIP Configuration — 8 Individual Port Accounts

### Method A: SIP Account Mode (Recommended for UC2000-VE)

Navigate to: **System Configuration → SIP → SIP Account** (or **Trunk → SIP Trunk**)

The Dinstar UC2000-VE-8G supports assigning individual SIP accounts per port.
Create **8 SIP accounts**, one for each GSM port:

#### Global SIP Settings

| Setting | Value | Notes |
|---------|-------|-------|
| **SIP Server** | `10.10.1.1` | FreePBX VPN IP |
| **SIP Port** | `51600` | FreePBX PJSIP UDP port |
| **Transport** | `UDP` | |
| **NAT Traversal** | `Disable` | ★ Direct VPN, no NAT |
| **DTMF Mode** | `RFC2833` | |
| **Register Expiry** | `120` seconds | |
| **Heartbeat/OPTIONS** | `30` seconds | Keep-alive |

#### Per-Port SIP Account Configuration

**Port 1:**

| Setting | Value |
|---------|-------|
| SIP Account | `gsm-port1` |
| Password | `Gsm1@Arwz2026` |
| SIP Server | `10.10.1.1` |
| SIP Port | `51600` |
| Register | ✅ Yes |
| Assigned Port | Port 1 |

**Port 2:**

| Setting | Value |
|---------|-------|
| SIP Account | `gsm-port2` |
| Password | `Gsm2@Arwz2026` |
| SIP Server | `10.10.1.1` |
| SIP Port | `51600` |
| Register | ✅ Yes |
| Assigned Port | Port 2 |

**Port 3:**

| Setting | Value |
|---------|-------|
| SIP Account | `gsm-port3` |
| Password | `Gsm3@Arwz2026` |
| SIP Server | `10.10.1.1` |
| SIP Port | `51600` |
| Register | ✅ Yes |
| Assigned Port | Port 3 |

**Port 4:**

| Setting | Value |
|---------|-------|
| SIP Account | `gsm-port4` |
| Password | `Gsm4@Arwz2026` |
| SIP Server | `10.10.1.1` |
| SIP Port | `51600` |
| Register | ✅ Yes |
| Assigned Port | Port 4 |

**Port 5:**

| Setting | Value |
|---------|-------|
| SIP Account | `gsm-port5` |
| Password | `Gsm5@Arwz2026` |
| SIP Server | `10.10.1.1` |
| SIP Port | `51600` |
| Register | ✅ Yes |
| Assigned Port | Port 5 |

**Port 6:**

| Setting | Value |
|---------|-------|
| SIP Account | `gsm-port6` |
| Password | `Gsm6@Arwz2026` |
| SIP Server | `10.10.1.1` |
| SIP Port | `51600` |
| Register | ✅ Yes |
| Assigned Port | Port 6 |

**Port 7:**

| Setting | Value |
|---------|-------|
| SIP Account | `gsm-port7` |
| Password | `Gsm7@Arwz2026` |
| SIP Server | `10.10.1.1` |
| SIP Port | `51600` |
| Register | ✅ Yes |
| Assigned Port | Port 7 |

**Port 8:**

| Setting | Value |
|---------|-------|
| SIP Account | `gsm-port8` |
| Password | `Gsm8@Arwz2026` |
| SIP Server | `10.10.1.1` |
| SIP Port | `51600` |
| Register | ✅ Yes |
| Assigned Port | Port 8 |

### Method B: Multiple SIP Trunks (Alternative)

If your Dinstar firmware uses "SIP Trunk" instead of "SIP Account" per port:

1. Create **8 separate SIP trunks** (Trunk 1 through Trunk 8)
2. Each trunk has the same SIP Server but different credentials
3. Assign each trunk to one physical port

| Trunk | Username | Password | Assigned Port |
|-------|----------|----------|---------------|
| Trunk 1 | `gsm-port1` | `Gsm1@Arwz2026` | Port 1 |
| Trunk 2 | `gsm-port2` | `Gsm2@Arwz2026` | Port 2 |
| Trunk 3 | `gsm-port3` | `Gsm3@Arwz2026` | Port 3 |
| Trunk 4 | `gsm-port4` | `Gsm4@Arwz2026` | Port 4 |
| Trunk 5 | `gsm-port5` | `Gsm5@Arwz2026` | Port 5 |
| Trunk 6 | `gsm-port6` | `Gsm6@Arwz2026` | Port 6 |
| Trunk 7 | `gsm-port7` | `Gsm7@Arwz2026` | Port 7 |
| Trunk 8 | `gsm-port8` | `Gsm8@Arwz2026` | Port 8 |

All trunks use: Server `10.10.1.1`, Port `51600`, UDP, Register = Yes

## Step 5: Codec Configuration

Navigate to: **System Configuration → SIP → Codec**

### Priority Order:

| Priority | Codec | Notes |
|----------|-------|-------|
| 1 | **G.711A (alaw)** | ★ Best — PCM, no transcoding |
| 2 | **G.711U (ulaw)** | Backup PCM codec |
| 3 | **GSM** | Fallback (lower quality) |

> 💡 **Why alaw first?** The Dinstar converts GSM → PCM internally. Using alaw/ulaw
> means Asterisk doesn't need to transcode — best audio quality, lowest CPU.

## Step 6: Port Configuration (SIM Cards)

Navigate to: **Port Configuration → GSM/CDMA**

For each of the 8 ports:

| Setting | Value | Notes |
|---------|-------|-------|
| **Enable** | ✅ | Enable ports with SIM cards |
| **SIM Status** | Should show "Ready" | If not, check SIM insertion |
| **SIP Account** | `gsm-portN` | Match to the SIP account for this port |
| **CallerID** | SIM's phone number | e.g., `01001234567` |

### SIM Card Setup

1. Insert SIM cards into the slots (push until click)
2. Wait ~30 seconds for GSM registration
3. Check **System Status** → each port should show:
   - SIM: ✅ Ready
   - GSM: ✅ Registered
   - Signal: ≥ -85 dBm (good)

## Step 7: Routing Rules

### 7a. Inbound Routes (GSM → FreePBX)

Navigate to: **Routing Configuration → Tel→IP Route**

Each port sends calls to FreePBX using its own SIP account. The Asterisk
dialplan (`from-gsm-inbound`) automatically routes based on endpoint name:

- Calls from `gsm-port1` → Extension 7001
- Calls from `gsm-port2` → Extension 7002
- ... and so on

**For each port (1-8):**

| Setting | Value | Notes |
|---------|-------|-------|
| **Enable** | ✅ | |
| **Route Name** | `GSM-Port-N-In` | Replace N with port number |
| **Source Port** | `Port N` | The specific GSM port |
| **Destination** | SIP Account `gsm-portN` | Same port's SIP account |
| **Caller ID Mode** | `Transparent` | Pass GSM caller ID through |
| **Called Number** | Leave empty or `s` | FreePBX handles routing |

> 💡 **Key**: Each port MUST send calls using its OWN SIP account (`gsm-portN`).
> This is how Asterisk identifies which port the call came in on, and routes to
> the correct extension.

### 7b. Outbound Routes (FreePBX → GSM)

Navigate to: **Routing Configuration → IP→Tel Route**

Outbound routing is handled primarily by Asterisk's round-robin dialplan.
When Asterisk dials `PJSIP/NUMBER@gsm-port3`, the call arrives at the
Dinstar as an INVITE to the `gsm-port3` SIP account. The Dinstar must route
this to physical **Port 3**.

| Setting | Value | Notes |
|---------|-------|-------|
| **Route Name** | `PBX-to-Port-N` | One rule per port |
| **Source** | SIP Account `gsm-portN` | Calls to this SIP account |
| **Destination Port** | `Port N` | Route to the physical port |
| **Strip Digits** | `0` | Don't strip any digits |

> 💡 **How round-robin works**: Asterisk picks a port (e.g., gsm-port5) and sends
> the call. The Dinstar receives it on the gsm-port5 account and routes to physical
> Port 5. If Port 5 is busy, Asterisk tries gsm-port6, etc.

## Step 8: Verify Registration

### On the Dinstar:
Navigate to: **System Status → SIP Status**
- Each port should show: ✅ **Registered**
- If "Trying" or "Failed":
  1. Check VPN is connected (Step 3)
  2. Verify SIP server = `10.10.1.1` port `51600`
  3. Check username/password matches exactly

### On Asterisk CLI:
```bash
# Check all registered contacts
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show contacts"
# Should show 8 contacts:
#   gsm-port1/sip:gsm-port1@10.10.1.2:XXXX
#   gsm-port2/sip:gsm-port2@10.10.1.2:XXXX
#   ... (one per port)

# Check specific endpoint
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show endpoint gsm-port1"

# Check all GSM endpoints at once
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show endpoints" | grep gsm

# Check AOR registration status
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show aors" | grep gsm
```

## Step 9: Test Calls

### Test Inbound (GSM → Extension):
1. Call the SIM number in **Port 1** from a mobile phone
2. Should ring extension **7001**
3. Answer on ARKAN PHONE or IP phone
4. Repeat for each port → verify correct extension rings

### Test Outbound (Extension → GSM):
1. From any extension (e.g., 2210), dial `01XXXXXXXXX` (mobile number starting with 0)
2. Call routes through `gsm-outbound` round-robin
3. Check which port was used in Asterisk logs
4. Make several calls — verify they distribute across different ports

### Test Round-Robin Distribution:
```bash
# Check the current round-robin counter
docker exec initpbx-freepbx-1 asterisk -rx "database show gsm"
# Should show: /gsm/rr : N (where N is 1-8, the next port to use)
```

## Step 10: Advanced Settings

### DTMF Settings

| Setting | Value | Notes |
|---------|-------|-------|
| **DTMF Mode** | `RFC2833` | Matches Asterisk `rfc4733` |
| **DTMF Payload** | `101` | Standard |

### Session Settings

| Setting | Value | Notes |
|---------|-------|-------|
| **NAT Traversal** | `Disable` | ★ Direct VPN, no NAT |
| **PRACK** | `Disable` | |
| **Session Timer** | `Disable` | FreePBX handles this |

## Troubleshooting

| Issue | Check |
|-------|-------|
| VPN not connecting | Dinstar logs, firewall port 51821/UDP, auth=SHA1 |
| SIP registration failing | VPN status first, then SIP server/port/credentials |
| Only some ports register | Check per-port SIP account assignment |
| One-way audio | Disable NAT traversal on Dinstar, check `media_address` |
| No audio at all | Verify VPN connected, check RTP ports |
| Incoming goes to wrong ext | Check each port has correct SIP account mapping |
| Outbound not distributing | `database show gsm` on Asterisk CLI |
| Echo/quality issues | Check GSM signal strength (≥ -85 dBm) |
| Call drops after 30s | Check heartbeat/keepalive = 30s |
| "CHANUNAVAIL" on outbound | That port not registered, round-robin skips it |

## Quick Reference Card

```
╔══════════════════════════════════════════════════════╗
║           DINSTAR UC2000-VE-8G — QUICK REF          ║
╠══════════════════════════════════════════════════════╣
║  VPN Server:  157.173.125.136:51821/udp             ║
║  VPN Tunnel:  10.10.1.2 → 10.10.1.1                ║
║  Auth: SHA1 | Cipher: AES-256-CBC | TLS-Auth: dir 1 ║
╠══════════════════════════════════════════════════════╣
║  SIP Server:  10.10.1.1:51600 (UDP, via VPN)        ║
║  NAT:         DISABLED (direct VPN tunnel)           ║
║  Codecs:      alaw > ulaw > gsm                     ║
║  DTMF:        RFC2833                                ║
╠══════════════════════════════════════════════════════╣
║  Port 1: gsm-port1 / Gsm1@Arwz2026 → Ext 7001     ║
║  Port 2: gsm-port2 / Gsm2@Arwz2026 → Ext 7002     ║
║  Port 3: gsm-port3 / Gsm3@Arwz2026 → Ext 7003     ║
║  Port 4: gsm-port4 / Gsm4@Arwz2026 → Ext 7004     ║
║  Port 5: gsm-port5 / Gsm5@Arwz2026 → Ext 7005     ║
║  Port 6: gsm-port6 / Gsm6@Arwz2026 → Ext 7006     ║
║  Port 7: gsm-port7 / Gsm7@Arwz2026 → Ext 7007     ║
║  Port 8: gsm-port8 / Gsm8@Arwz2026 → Ext 7008     ║
╠══════════════════════════════════════════════════════╣
║  Outbound: Any ext dials 0XX.. → round-robin ports   ║
║  Inbound:  GSM call on port N → rings ext 700N      ║
╚══════════════════════════════════════════════════════╝
```
