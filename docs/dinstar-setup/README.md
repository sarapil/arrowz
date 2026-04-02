# Dinstar UC2000-VE-8G GSM Gateway — Setup Guide

## Overview

Connect a **Dinstar UC2000-VE-8G** (8-port GSM gateway) to **FreePBX/Asterisk** through an **encrypted OpenVPN TLS tunnel**, enabling:
- 📞 **Outbound**: Dial mobile/landline numbers from any Frappe/ARKAN PHONE extension
- 📲 **Inbound**: Receive GSM calls on your IP phone/softphone
- 🔒 **Encrypted**: All SIP/RTP traffic flows through OpenVPN TLS
- 🔗 **Direct**: No gateway machine needed — Dinstar has native OpenVPN support!

## Architecture

```
  Egypt Office                             VPS (157.173.125.136)
┌──────────────────────┐                 ┌──────────────────────────┐
│                      │                 │  FreePBX Container       │
│  ┌─────────────────┐ │                 │                          │
│  │ Dinstar         │ │   OpenVPN TLS   │  ┌────────────────────┐  │
│  │ UC2000-VE-8G    │═╪═══(UDP 51821)══╪══│ OpenVPN TLS Server │  │
│  │                 │ │   Certificates  │  │ tun1: 10.10.1.1    │  │
│  │ VPN: 10.10.1.2  │ │   + tls-auth   │  └─────────┬──────────┘  │
│  │ 8× SIM Cards   │ │                 │            │              │
│  │                 │──── SIP over VPN ────▶ Asterisk PJSIP      │
│  │                 │ │   10.10.1.1:    │    endpoint: dinstar   │
│  │                 │ │     51600       │    context: from-dinstar│
│  └─────────────────┘ │                 │                          │
│                      │                 │  ┌────────────────────┐  │
│  ┌─────────────────┐ │   OpenVPN S.Key │  │ Extensions:        │  │
│  │ ARKAN PHONE     │═╪═══(UDP 51820)══╪══│ 1155, 2210, 2211   │  │
│  │ VPN: 10.10.0.2  │ │                 │  │ 2290, 9999, etc.   │  │
│  └─────────────────┘ │                 │  └────────────────────┘  │
└──────────────────────┘                 └──────────────────────────┘
```

## Two VPN Instances (Independent)

| Property | ARKAN PHONE (arkan) | Dinstar GSM Gateway |
|----------|---------------------|---------------------|
| **Mode** | Static Key (no handshake, DPI-safe) | TLS (certificates + tls-auth) |
| **Port** | 51820/UDP | 51821/UDP |
| **Interface** | tun0 | tun1 |
| **Server IP** | 10.10.0.1 | 10.10.1.1 |
| **Client IP** | 10.10.0.2 | 10.10.1.2 |
| **Purpose** | WebRTC softphone | GSM trunk |

## Setup Steps

### Step 1: VPN TLS Server (Run on VPS)
```bash
ssh -p 1352 root@157.173.125.136
cd /path/to/dinstar-setup
bash 1_vpn_dinstar_server.sh
```
Creates:
- Easy-RSA CA + server cert + client cert
- tls-auth HMAC key
- OpenVPN TLS server on port 51821/tun1
- Client `.ovpn` file at `/opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn`

### Step 2: Asterisk Trunk (Run on VPS)
```bash
bash 3_asterisk_dinstar_trunk.sh
```
Creates PJSIP endpoint, auth, AOR, IP-identify, dialplan.

### Step 3: Configure Dinstar Device
Follow [4_dinstar_device_config.md](4_dinstar_device_config.md):
1. Upload the `.ovpn` to Dinstar's OpenVPN settings
2. Configure SIP trunk → `10.10.1.1:51600`
3. Configure routing rules

### Step 4: Verify
```bash
bash 5_test_connectivity.sh
```

## Quick Reference

| Component | Value | Notes |
|-----------|-------|-------|
| FreePBX VPN IP (dinstar) | `10.10.1.1` | OpenVPN TLS server |
| Dinstar VPN IP | `10.10.1.2` | OpenVPN TLS client |
| VPN Port (dinstar) | `51821/UDP` | TLS mode |
| PJSIP SIP port | `51600/UDP` | FreePBX non-standard |
| SIP credentials | `dinstar` / `D1nstar#VPN2026!` | Registration auth |
| Inbound context | `from-dinstar` | Routes GSM→extensions |
| Client .ovpn | `/opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn` | All certs inline |

## Files

| File | Run On | Purpose |
|------|--------|---------|
| `1_vpn_dinstar_server.sh` | VPS Host | OpenVPN TLS server + CA + certs + .ovpn |
| `3_asterisk_dinstar_trunk.sh` | VPS Host | PJSIP trunk + dialplan |
| `4_dinstar_device_config.md` | — | Dinstar web UI guide (VPN + SIP) |
| `5_test_connectivity.sh` | VPS Host | Verify everything works |

## Troubleshooting

```bash
# Check VPN server log
docker exec initpbx-freepbx-1 tail -20 /var/log/openvpn-dinstar-tls.log

# Check if Dinstar is connected
docker exec initpbx-freepbx-1 ping -c 3 10.10.1.2

# Check SIP registration
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show contacts"

# Check endpoint
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show endpoint dinstar"

# View all VPN interfaces
docker exec initpbx-freepbx-1 ip addr show | grep -A3 "tun[01]"

# Restart dinstar VPN
docker exec initpbx-freepbx-1 bash -c "pkill -f 'dinstar-tls'; sleep 2; openvpn --config /etc/openvpn/dinstar-tls/server.conf --daemon openvpn-dinstar-tls"
```
