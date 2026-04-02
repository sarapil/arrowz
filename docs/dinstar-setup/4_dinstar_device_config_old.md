# Dinstar UC2000-VE-8G — Device Configuration Guide

## Architecture (Direct VPN — No Gateway!)

```
  Egypt Office                             VPS (157.173.125.136)
┌─────────────────────┐                 ┌──────────────────────────┐
│                     │                 │  FreePBX Container       │
│  ┌────────────────┐ │                 │                          │
│  │ Dinstar        │ │   OpenVPN TLS   │  ┌────────────────────┐  │
│  │ UC2000-VE-8G   │═╪═══(UDP 51821)══╪══│ OpenVPN TLS Server │  │
│  │                │ │   tls-auth      │  │ tun1: 10.10.1.1    │  │
│  │ tun: 10.10.1.2 │ │                 │  └─────────┬──────────┘  │
│  │                │ │                 │            │              │
│  │ SIP ──────────────────────────────────▶ Asterisk PJSIP      │
│  │ 10.10.1.1:51600│ │                 │    endpoint: dinstar   │
│  │                │ │                 │    10.10.1.1:51600     │
│  │ 8× SIM Cards  │ │                 │                          │
│  └────────────────┘ │                 │  ┌────────────────────┐  │
│                     │                 │  │ Extensions:        │  │
│  ┌────────────────┐ │   OpenVPN S.Key │  │ 1155, 2210, 2211   │  │
│  │ ARKAN PHONE    │═╪═══(UDP 51820)══╪══│ 2290, 9999, etc.   │  │
│  │ tun: 10.10.0.2 │ │                 │  │ tun0: 10.10.0.1    │  │
│  └────────────────┘ │                 │  └────────────────────┘  │
└─────────────────────┘                 └──────────────────────────┘
```

**Key difference from old plan**: The Dinstar supports OpenVPN natively — no gateway
machine needed! The Dinstar connects directly to FreePBX over a VPN tunnel.

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

### Option A: Upload .ovpn file
1. Download `dinstar-tls.ovpn` from the VPS:
   ```bash
   scp -P 1352 root@157.173.125.136:/opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn .
   ```
2. Upload the file to the Dinstar web UI

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
| **Auth** | `SHA256` |
| **TLS Auth** | Enabled, Direction = `1` (client) |

**Certificate Fields** (copy from `dinstar-tls.ovpn`):
- **CA Certificate**: Content between `<ca>` and `</ca>` tags
- **Client Certificate**: Content between `<cert>` and `</cert>` tags
- **Client Key**: Content between `<key>` and `</key>` tags
- **TLS Auth Key**: Content between `<tls-auth>` and `</tls-auth>` tags

### After Enabling VPN:
- Wait 10-30 seconds for connection
- Check **System Status → VPN Status** — should show "Connected"
- The Dinstar gets IP: `10.10.1.2`
- It can now reach FreePBX at: `10.10.1.1`

### Verify VPN (from VPS):
```bash
# Check if Dinstar is connected (run on VPS host)
docker exec initpbx-freepbx-1 tail -10 /var/log/openvpn-dinstar-tls.log

# Ping Dinstar through VPN
docker exec initpbx-freepbx-1 ping -c 3 10.10.1.2
```

## Step 4: SIP Trunk Configuration

Navigate to: **Trunk Configuration → SIP Trunk**

### Trunk 1 Settings (to FreePBX via VPN — DIRECT)

| Setting | Value | Notes |
|---------|-------|-------|
| **Enable** | ✅ Checked | |
| **Trunk Name** | `FreePBX-VPN` | Descriptive name |
| **Trunk Type** | `Registration` | Dinstar registers to FreePBX |
| **SIP Server Address** | `10.10.1.1` | ★ FreePBX VPN IP (direct!) |
| **SIP Server Port** | `51600` | ★ FreePBX PJSIP port (non-standard) |
| **Register Username** | `dinstar` | Must match Asterisk auth |
| **Register Password** | `D1nstar#VPN2026!` | Must match Asterisk auth |
| **Domain** | `10.10.1.1` | Same as SIP Server |
| **Transport** | `UDP` | |
| **Register Expiry** | `120` | Seconds |
| **Heartbeat Mode** | `OPTIONS` | SIP keepalive |
| **Heartbeat Interval** | `30` | Seconds |

> ℹ️ **Note**: The SIP server is the VPN IP `10.10.1.1`, NOT the public IP.
> The SIP port is `51600`, NOT the standard `5060`. This is FreePBX's non-standard port.

### Advanced Trunk Settings

| Setting | Value | Notes |
|---------|-------|-------|
| **DTMF Mode** | `RFC2833` | Matches Asterisk rfc4733 |
| **DTMF Payload** | `101` | Standard |
| **NAT Traversal** | `Disable` | ★ NOT needed — direct VPN! |
| **PRACK** | `Disable` | Not needed |
| **Session Timer** | `Disable` | FreePBX handles this |

> ⚠️ **NAT Traversal = Disable** — The Dinstar talks to FreePBX directly over VPN.
> There's no NAT between them. Enabling NAT might cause audio issues.

## Step 5: Codec Configuration

Navigate to: **System Configuration → SIP → Codec**

### Priority Order:

| Priority | Codec | Notes |
|----------|-------|-------|
| 1 | **G.711A (alaw)** | ★ Best — PCM, no transcoding |
| 2 | **G.711U (ulaw)** | Backup PCM codec |
| 3 | G.729 | Low bandwidth (needs license) |

> 💡 **Why alaw first?** The Dinstar converts GSM → PCM internally. Using alaw/ulaw
> means Asterisk doesn't need to transcode — best audio quality, lowest CPU.

## Step 6: Port Configuration (GSM Channels)

Navigate to: **Port Configuration → GSM/CDMA**

For each of the 8 ports:

| Setting | Value | Notes |
|---------|-------|-------|
| **Enable** | ✅ | Enable ports with SIM cards |
| **SIM Status** | Should show "Ready" | If not, check SIM insertion |
| **Trunk** | `FreePBX-VPN` | Link to the trunk from Step 4 |
| **CallerID** | SIM's phone number | e.g., `+201001234567` |

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

| Setting | Value | Notes |
|---------|-------|-------|
| **Enable** | ✅ | |
| **Route Name** | `GSM-to-PBX` | |
| **Source Port** | `All Ports` | Or specific ports |
| **Destination Trunk** | `FreePBX-VPN` | |
| **Hotline** | `1155` | Default extension |
| **Caller ID Mode** | `Transparent` | Pass GSM caller ID |

**Routing Options:**
- **Hotline mode** (simplest): All calls go to extension `1155`
- **DID mode**: Caller dials extension number after connecting
- **IVR mode**: Route to IVR, caller chooses extension

### 7b. Outbound Routes (FreePBX → GSM)

Navigate to: **Routing Configuration → IP→Tel Route**

| Setting | Value | Notes |
|---------|-------|-------|
| **Enable** | ✅ | |
| **Route Name** | `PBX-to-GSM` | |
| **Source Trunk** | `FreePBX-VPN` | |
| **Destination Port** | `Any Available` | Auto-selects free GSM port |
| **Port Selection** | `Round Robin` | Distribute calls evenly |
| **Strip Digits** | `0` | Or strip prefix if needed |

### 7c. FreePBX Outbound Route (do in FreePBX GUI)

In FreePBX web interface → **Connectivity → Outbound Routes**:

1. Create new route: "GSM Outbound"
2. **Trunk Sequence**: PJSIP/dinstar
3. **Dial Patterns**:

| Prefix | Match Pattern | Notes |
|--------|---------------|-------|
| | `0XXXXXXXXXX` | Egyptian local (11 digits) |
| | `01XXXXXXXXX` | Egyptian mobile |
| | `02XXXXXXXX` | Cairo landline |
| | `+20XXXXXXXXX` | International format |

## Step 8: Verify Registration

### On the Dinstar:
Navigate to: **System Status → SIP Trunk Status**
- Status should show: ✅ **Registered**
- If "Trying" or "Failed":
  1. Check VPN is connected (Step 3)
  2. Verify SIP server = `10.10.1.1` port `51600`
  3. Check username/password

### On Asterisk CLI:
```bash
# Check if Dinstar is registered
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show contacts"
# Should show: dinstar/sip:dinstar@10.10.1.2:5060

# Check endpoint details
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show endpoint dinstar"

# Check AOR
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show aor dinstar"
```

## Step 9: Test Calls

### Test Inbound (GSM → Extension):
1. Call the Dinstar's SIM number from a mobile phone
2. Should ring extension 1155 (or configured extension)
3. Answer on ARKAN PHONE or IP phone

### Test Outbound (Extension → GSM):
1. From extension 1155 or 2210, dial a mobile number
2. Call routes through Dinstar to GSM
3. Mobile phone should ring

## Troubleshooting

| Issue | Check |
|-------|-------|
| VPN not connecting | Dinstar logs, firewall port 51821/UDP |
| SIP registration failing | VPN status first, then SIP server/port/credentials |
| One-way audio | Disable NAT traversal on Dinstar, check media_address |
| No audio at all | Verify VPN is connected, check RTP ports |
| Echo/quality issues | Check GSM signal strength (≥ -85 dBm) |
| Call drops after 30s | Check heartbeat/keepalive settings |
