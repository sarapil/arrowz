#!/bin/bash
###############################################################################
# OpenVPN Static Key Setup — Run on VPS HOST
# ============================================
# Sets up OpenVPN in STATIC KEY mode inside FreePBX container.
#
# Why static key?
#   - NO TLS handshake → DPI (Egypt, China, etc.) cannot fingerprint it
#   - Looks like random UDP traffic
#   - Works through restrictive firewalls
#   - Simple setup, single .ovpn file for client
#
# Limitation: Point-to-point (1 client per port).
#   For multiple clients: run script again with different port/name.
#
# Usage:
#   bash 4_setup_openvpn_static.sh                    → admin on UDP 51820
#   bash 4_setup_openvpn_static.sh ahmed 51821         → ahmed on UDP 51821
#   bash 4_setup_openvpn_static.sh omar 51822 tcp      → omar on TCP 51822
#
###############################################################################

set -euo pipefail

# ─── Arguments ───
PEER_NAME="${1:-admin}"
VPN_PORT="${2:-51820}"
VPN_PROTO="${3:-udp}"

# ─── Config ───
CONTAINER="initpbx-freepbx-1"
PUBLIC_IP="157.173.125.136"
# Point-to-point IPs (server ↔ client)
# Each peer gets a unique /30 subnet based on port offset
PORT_OFFSET=$(( VPN_PORT - 51820 ))
SERVER_TUN_IP="10.10.${PORT_OFFSET}.1"
CLIENT_TUN_IP="10.10.${PORT_OFFSET}.2"
DNS_SERVERS="1.1.1.1"

# ─── Colors ───
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; }
info() { echo -e "${CYAN}[i]${NC} $1"; }

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  OpenVPN Static Key Setup (No Handshake / Anti-DPI)  ║${NC}"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Peer:     ${PEER_NAME}                              ${NC}"
echo -e "${CYAN}║  Port:     ${VPN_PORT}/${VPN_PROTO}                  ${NC}"
echo -e "${CYAN}║  Tunnel:   ${SERVER_TUN_IP} ↔ ${CLIENT_TUN_IP}      ${NC}"
echo -e "${CYAN}║  Endpoint: ${PUBLIC_IP}:${VPN_PORT}                  ${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Step 1: Stop WireGuard on same port (if running)
###############################################################################
info "Step 1: Checking for conflicting services on port ${VPN_PORT}..."

docker exec "$CONTAINER" bash -c "
    # Stop WireGuard if it's on the same port
    if ip link show wg0 &>/dev/null; then
        WG_PORT=\$(wg show wg0 listen-port 2>/dev/null || echo '')
        if [[ \"\$WG_PORT\" == \"${VPN_PORT}\" ]]; then
            echo '  Stopping WireGuard (same port)...'
            wg-quick down wg0 2>/dev/null || true
            systemctl disable wg-quick@wg0 2>/dev/null || true
            echo '  WireGuard stopped'
        fi
    fi
" 2>/dev/null || true

log "Port ${VPN_PORT} cleared"

###############################################################################
# Step 2: Install OpenVPN inside container
###############################################################################
info "Step 2: Installing OpenVPN..."

docker exec "$CONTAINER" bash -c '
    if command -v openvpn &>/dev/null; then
        echo "  OpenVPN already installed: $(openvpn --version | head -1)"
    else
        apt-get update -qq
        apt-get install -y -qq openvpn
        apt-get clean
        rm -rf /var/lib/apt/lists/*
        echo "  OpenVPN installed: $(openvpn --version | head -1)"
    fi
'

log "OpenVPN ready"

###############################################################################
# Step 3: Generate static key
###############################################################################
info "Step 3: Generating static key for '${PEER_NAME}'..."

OVPN_DIR="/etc/openvpn"
PEER_DIR="${OVPN_DIR}/peers/${PEER_NAME}"

docker exec "$CONTAINER" bash -c "
    mkdir -p '${PEER_DIR}'
    chmod 700 '${OVPN_DIR}/peers' '${PEER_DIR}'

    if [[ -f '${PEER_DIR}/static.key' ]]; then
        echo '  Static key already exists — keeping it'
    else
        openvpn --genkey secret '${PEER_DIR}/static.key'
        chmod 600 '${PEER_DIR}/static.key'
        echo '  New static key generated'
    fi
"

log "Static key ready"

###############################################################################
# Step 4: Create server config
###############################################################################
info "Step 4: Creating server config..."

SERVER_CONF="${OVPN_DIR}/server-${PEER_NAME}.conf"

docker exec "$CONTAINER" bash -c "cat > '${SERVER_CONF}' << 'SRVEOF'
# OpenVPN Static Key Server — ${PEER_NAME}
# Port: ${VPN_PORT}/${VPN_PROTO}
# NO handshake, NO TLS — invisible to DPI

proto ${VPN_PROTO}
port ${VPN_PORT}
dev tun-${PEER_NAME}
dev-type tun

ifconfig ${SERVER_TUN_IP} ${CLIENT_TUN_IP}
secret ${PEER_DIR}/static.key
allow-deprecated-insecure-static-crypto

ping 10
ping-restart 60

persist-tun
persist-key

verb 3
log-append /var/log/openvpn-${PEER_NAME}.log
status /var/log/openvpn-${PEER_NAME}-status.log 30

data-ciphers AES-256-GCM:AES-256-CBC
cipher AES-256-CBC
auth SHA256
SRVEOF
"

# Fix: the heredoc doesn't expand vars inside 'SRVEOF', so we need to do replacements
docker exec "$CONTAINER" bash -c "
    sed -i 's|\${PEER_NAME}|${PEER_NAME}|g' '${SERVER_CONF}'
    sed -i 's|\${VPN_PORT}|${VPN_PORT}|g' '${SERVER_CONF}'
    sed -i 's|\${VPN_PROTO}|${VPN_PROTO}|g' '${SERVER_CONF}'
    sed -i 's|\${SERVER_TUN_IP}|${SERVER_TUN_IP}|g' '${SERVER_CONF}'
    sed -i 's|\${CLIENT_TUN_IP}|${CLIENT_TUN_IP}|g' '${SERVER_CONF}'
    sed -i 's|\${PEER_DIR}|${PEER_DIR}|g' '${SERVER_CONF}'
"

log "Server config: ${SERVER_CONF}"

###############################################################################
# Step 5: Create client .ovpn file (self-contained)
###############################################################################
info "Step 5: Creating client .ovpn file..."

# Read the static key from container
STATIC_KEY=$(docker exec "$CONTAINER" cat "${PEER_DIR}/static.key")

CLIENT_OVPN="${PEER_DIR}/${PEER_NAME}.ovpn"

# ── File 1: Standard .ovpn (OpenVPN CLI / Android / iOS) ──
docker exec "$CONTAINER" bash -c "cat > '${CLIENT_OVPN}' << CLIENTEOF
# OpenVPN Static Key — ${PEER_NAME}
# Server: ${PUBLIC_IP}:${VPN_PORT}/${VPN_PROTO}

proto ${VPN_PROTO}
remote ${PUBLIC_IP} ${VPN_PORT}
dev tun
resolv-retry infinite
nobind

ifconfig ${CLIENT_TUN_IP} ${SERVER_TUN_IP}
allow-deprecated-insecure-static-crypto

redirect-gateway def1
dhcp-option DNS ${DNS_SERVERS}

persist-tun
persist-key

ping 10
ping-restart 60

data-ciphers AES-256-GCM:AES-256-CBC
cipher AES-256-CBC
auth SHA256

verb 3

<secret>
${STATIC_KEY}
</secret>
CLIENTEOF
"
log "Client file (standard): ${CLIENT_OVPN}"

# ── File 2: NetworkManager-compatible .ovpn ──
NM_OVPN="${PEER_DIR}/${PEER_NAME}-nm.ovpn"

docker exec "$CONTAINER" bash -c "cat > '${NM_OVPN}' << CLIENTEOF
# OpenVPN Static Key — ${PEER_NAME} (NetworkManager compatible)
# Import: nmcli connection import type openvpn file ${PEER_NAME}-nm.ovpn

proto ${VPN_PROTO}
remote ${PUBLIC_IP} ${VPN_PORT}
dev tun
resolv-retry infinite
nobind

ifconfig ${CLIENT_TUN_IP} ${SERVER_TUN_IP}
allow-deprecated-insecure-static-crypto

persist-tun
persist-key

ping 10
ping-restart 60

data-ciphers AES-256-GCM:AES-256-CBC
cipher AES-256-CBC
auth SHA256

verb 3

<secret>
${STATIC_KEY}
</secret>
CLIENTEOF
"
log "Client file (NetworkManager): ${NM_OVPN}"

###############################################################################
# Step 6: Setup NAT/masquerade for full tunnel
###############################################################################
info "Step 6: Setting up NAT for full tunnel..."

docker exec "$CONTAINER" bash -c '
    MAIN_IFACE=$(ip route | grep default | awk "{print \$5}" | head -1)

    # Enable IP forwarding
    sysctl -w net.ipv4.ip_forward=1 > /dev/null

    # Add masquerade if not exists
    if ! iptables -t nat -C POSTROUTING -s '"${CLIENT_TUN_IP}"'/32 -o ${MAIN_IFACE} -j MASQUERADE 2>/dev/null; then
        iptables -t nat -A POSTROUTING -s '"${CLIENT_TUN_IP}"'/32 -o ${MAIN_IFACE} -j MASQUERADE
        echo "  NAT masquerade added for '"${CLIENT_TUN_IP}"' via ${MAIN_IFACE}"
    else
        echo "  NAT masquerade already exists"
    fi

    # Allow forwarding
    iptables -C FORWARD -i tun-'"${PEER_NAME}"' -j ACCEPT 2>/dev/null || \
        iptables -A FORWARD -i tun-'"${PEER_NAME}"' -j ACCEPT
    iptables -C FORWARD -o tun-'"${PEER_NAME}"' -j ACCEPT 2>/dev/null || \
        iptables -A FORWARD -o tun-'"${PEER_NAME}"' -j ACCEPT
'

log "NAT configured"

###############################################################################
# Step 7: Start OpenVPN server
###############################################################################
info "Step 7: Starting OpenVPN server..."

# Stop if already running for this peer
docker exec "$CONTAINER" bash -c "
    # Kill existing instance for this peer
    if [[ -f /var/run/openvpn-${PEER_NAME}.pid ]]; then
        kill \$(cat /var/run/openvpn-${PEER_NAME}.pid) 2>/dev/null || true
        rm -f /var/run/openvpn-${PEER_NAME}.pid
        sleep 1
    fi

    # Also kill by config name
    pkill -f 'openvpn.*server-${PEER_NAME}' 2>/dev/null || true
    sleep 1

    # Start OpenVPN
    openvpn --config '${SERVER_CONF}' \
            --daemon openvpn-${PEER_NAME} \
            --writepid /var/run/openvpn-${PEER_NAME}.pid

    sleep 2

    # Verify
    if ip link show tun-${PEER_NAME} &>/dev/null; then
        echo '  OpenVPN is UP!'
        ip addr show tun-${PEER_NAME} | grep inet
    else
        echo '  WARNING: tun interface not found yet, checking process...'
        ps aux | grep 'openvpn.*${PEER_NAME}' | grep -v grep || echo '  Process not running!'
        cat /var/log/openvpn-${PEER_NAME}.log 2>/dev/null | tail -10
    fi
"

log "OpenVPN server started"

###############################################################################
# Step 8: Create systemd service for auto-start
###############################################################################
info "Step 8: Creating auto-start service..."

docker exec "$CONTAINER" bash -c "cat > /etc/systemd/system/openvpn-${PEER_NAME}.service << SVCEOF
[Unit]
Description=OpenVPN Static Key - ${PEER_NAME}
After=network.target

[Service]
Type=simple
ExecStartPre=/sbin/sysctl -w net.ipv4.ip_forward=1
ExecStart=/usr/sbin/openvpn --config ${SERVER_CONF}
ExecStartPost=/bin/bash -c 'IFACE=\$(ip route | grep default | awk \"{print \\\\\$5}\" | head -1); iptables -t nat -A POSTROUTING -s ${CLIENT_TUN_IP}/32 -o \${IFACE} -j MASQUERADE 2>/dev/null || true'
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload 2>/dev/null || true
systemctl enable openvpn-${PEER_NAME} 2>/dev/null || true
" 2>/dev/null || warn "systemd setup skipped (will use manual start)"

log "Auto-start configured"

###############################################################################
# Step 9: Copy .ovpn to host for easy transfer
###############################################################################
info "Step 9: Copying client file to host..."

HOST_DIR="/opt/proj/initpbx/vpn-clients"
mkdir -p "$HOST_DIR"
docker cp "${CONTAINER}:${CLIENT_OVPN}" "${HOST_DIR}/${PEER_NAME}.ovpn"
docker cp "${CONTAINER}:${NM_OVPN}" "${HOST_DIR}/${PEER_NAME}-nm.ovpn" 2>/dev/null || true

log "Client files: ${HOST_DIR}/${PEER_NAME}.ovpn  &  ${PEER_NAME}-nm.ovpn"

###############################################################################
# Step 10: Display client config and QR info
###############################################################################
echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  OpenVPN Static Key — Setup Complete!                 ║${NC}"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                       ║${NC}"
echo -e "${CYAN}║  Peer:     ${PEER_NAME}                              ${NC}"
echo -e "${CYAN}║  Server:   ${PUBLIC_IP}:${VPN_PORT}/${VPN_PROTO}     ${NC}"
echo -e "${CYAN}║  Tunnel:   ${SERVER_TUN_IP} ↔ ${CLIENT_TUN_IP}      ${NC}"
echo -e "${CYAN}║  Mode:     Static Key (NO handshake)                  ║${NC}"
echo -e "${CYAN}║  Cipher:   AES-256-CBC + SHA256                       ║${NC}"
echo -e "${CYAN}║  Routing:  Full tunnel (all traffic via VPS)          ║${NC}"
echo -e "${CYAN}║                                                       ║${NC}"
echo -e "${CYAN}║  Client:   ${HOST_DIR}/${PEER_NAME}.ovpn             ${NC}"
echo -e "${CYAN}║                                                       ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${GREEN}── Client .ovpn content ──${NC}"
echo ""
docker exec "$CONTAINER" cat "${CLIENT_OVPN}"
echo ""

echo -e "${YELLOW}── How to install on phone ──${NC}"
echo ""
echo "  1. Install 'OpenVPN Connect' app (iOS/Android)"
echo ""
echo "  2. Transfer .ovpn file to phone:"
echo "     Option A: SCP from your laptop:"
echo "       scp -P 1352 root@${PUBLIC_IP}:${HOST_DIR}/${PEER_NAME}.ovpn ."
echo ""
echo "     Option B: Quick HTTP server (run on VPS, download on phone):"
echo "       cd ${HOST_DIR} && python3 -m http.server 8888 --bind 0.0.0.0"
echo "       → Open: http://${PUBLIC_IP}:8888/${PEER_NAME}.ovpn"
echo "       → CTRL+C to stop the server after download!"
echo ""
echo "     Option C: Base64 (copy-paste into phone file):"
echo "       base64 ${HOST_DIR}/${PEER_NAME}.ovpn"
echo ""
echo "  3. Import .ovpn in OpenVPN Connect app"
echo "  4. Connect → Done!"
echo ""
echo "  Test: Visit whatismyip.com → Should show ${PUBLIC_IP}"
echo ""

###############################################################################
# Verify server status
###############################################################################
echo -e "${YELLOW}── Server Status ──${NC}"
docker exec "$CONTAINER" bash -c "
    echo 'Process:'
    ps aux | grep 'openvpn.*${PEER_NAME}' | grep -v grep || echo '  NOT RUNNING!'
    echo ''
    echo 'Interface:'
    ip addr show tun-${PEER_NAME} 2>/dev/null || echo '  tun not found yet'
    echo ''
    echo 'Log (last 5 lines):'
    tail -5 /var/log/openvpn-${PEER_NAME}.log 2>/dev/null || echo '  No log yet'
"
