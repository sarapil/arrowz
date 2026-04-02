#!/bin/bash
###############################################################################
# OpenVPN Clean Setup — Run on VPS HOST
# ======================================
# Cleans all old configs, creates ONE working tunnel.
# Generates fresh matching client file.
#
# Usage:  bash 6_openvpn_clean.sh [name] [port]
#         bash 6_openvpn_clean.sh sarapil 51820
###############################################################################

set -euo pipefail

PEER_NAME="${1:-sarapil}"
VPN_PORT="${2:-51820}"
CONTAINER="initpbx-freepbx-1"
PUBLIC_IP="157.173.125.136"
SERVER_TUN_IP="10.10.0.1"
CLIENT_TUN_IP="10.10.0.2"
DNS="1.1.1.1"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Clean OpenVPN Static Key Setup                  ║${NC}"
echo -e "${CYAN}║  Peer: ${PEER_NAME}  Port: ${VPN_PORT}/udp       ${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
echo -e "${YELLOW}[1/7] Killing ALL old OpenVPN processes...${NC}"
###############################################################################
docker exec "$CONTAINER" bash -c '
    pkill -f openvpn 2>/dev/null || true
    sleep 1
    pkill -9 -f openvpn 2>/dev/null || true
    rm -f /var/run/openvpn-*.pid
    echo "  All OpenVPN processes killed"
'

###############################################################################
echo -e "${YELLOW}[2/7] Cleaning old configs...${NC}"
###############################################################################
docker exec "$CONTAINER" bash -c '
    rm -f /etc/openvpn/server-*.conf
    echo "  Old server configs removed"
'

###############################################################################
echo -e "${YELLOW}[3/7] Stopping WireGuard if running...${NC}"
###############################################################################
docker exec "$CONTAINER" bash -c '
    if ip link show wg0 &>/dev/null; then
        wg-quick down wg0 2>/dev/null || true
        echo "  WireGuard stopped"
    else
        echo "  No WireGuard (OK)"
    fi
'

###############################################################################
echo -e "${YELLOW}[4/7] Generating fresh static key...${NC}"
###############################################################################
docker exec "$CONTAINER" bash -c "
    mkdir -p /etc/openvpn/peers/${PEER_NAME}
    chmod 700 /etc/openvpn/peers/${PEER_NAME}

    # Generate NEW key (overwrite old to ensure match)
    openvpn --genkey secret /etc/openvpn/peers/${PEER_NAME}/static.key
    chmod 600 /etc/openvpn/peers/${PEER_NAME}/static.key
    echo '  Fresh static key generated'
"

###############################################################################
echo -e "${YELLOW}[5/7] Creating server config...${NC}"
###############################################################################
docker exec "$CONTAINER" bash -c "cat > /etc/openvpn/server-${PEER_NAME}.conf << 'EOF'
proto udp
port ${VPN_PORT}
dev tun
ifconfig ${SERVER_TUN_IP} ${CLIENT_TUN_IP}
secret /etc/openvpn/peers/${PEER_NAME}/static.key
allow-deprecated-insecure-static-crypto
ping 10
ping-restart 60
persist-tun
persist-key
data-ciphers AES-256-GCM:AES-256-CBC
cipher AES-256-CBC
auth SHA256
verb 3
log-append /var/log/openvpn-${PEER_NAME}.log
status /var/log/openvpn-${PEER_NAME}-status.log 30
EOF
echo '  Server config created'
"

###############################################################################
echo -e "${YELLOW}[6/7] Starting OpenVPN server...${NC}"
###############################################################################
docker exec "$CONTAINER" bash -c "
    # Clear old log
    > /var/log/openvpn-${PEER_NAME}.log 2>/dev/null || true

    # Start
    openvpn --config /etc/openvpn/server-${PEER_NAME}.conf --daemon openvpn-${PEER_NAME}
    sleep 2

    # Verify
    if ip link show tun0 &>/dev/null; then
        echo '  [OK] tun0 is UP'
        ip addr show tun0 | grep inet | head -1
    else
        echo '  [FAIL] tun0 not found'
        cat /var/log/openvpn-${PEER_NAME}.log | tail -5
        exit 1
    fi

    # Setup NAT for full tunnel
    MAIN_IFACE=\$(ip route | grep default | awk '{print \$5}' | head -1)
    sysctl -w net.ipv4.ip_forward=1 > /dev/null

    iptables -t nat -C POSTROUTING -s ${CLIENT_TUN_IP}/32 -o \${MAIN_IFACE} -j MASQUERADE 2>/dev/null || \
        iptables -t nat -A POSTROUTING -s ${CLIENT_TUN_IP}/32 -o \${MAIN_IFACE} -j MASQUERADE

    echo \"  NAT via \${MAIN_IFACE}\"
"
echo -e "${GREEN}  Server running on ${VPN_PORT}/udp${NC}"

###############################################################################
echo -e "${YELLOW}[7/7] Generating client .ovpn...${NC}"
###############################################################################

# Read the SAME key that server uses
STATIC_KEY=$(docker exec "$CONTAINER" cat "/etc/openvpn/peers/${PEER_NAME}/static.key")

# Create client file on host
HOST_DIR="/opt/proj/initpbx/vpn-clients"
mkdir -p "$HOST_DIR"

cat > "${HOST_DIR}/${PEER_NAME}.ovpn" << EOF
proto udp
remote ${PUBLIC_IP} ${VPN_PORT}
dev tun
ifconfig ${CLIENT_TUN_IP} ${SERVER_TUN_IP}
secret [inline]
allow-deprecated-insecure-static-crypto
redirect-gateway def1
dhcp-option DNS ${DNS}
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
EOF

echo -e "${GREEN}  Client file: ${HOST_DIR}/${PEER_NAME}.ovpn${NC}"

###############################################################################
# Verify
###############################################################################
echo ""
echo -e "${CYAN}═══ Verification ═══${NC}"

echo ""
echo "Server process:"
docker exec "$CONTAINER" ps aux | grep "[o]penvpn" || echo "  NOT RUNNING!"

echo ""
echo "Server tun:"
docker exec "$CONTAINER" ip addr show tun0 2>/dev/null | grep inet || echo "  No tun0"

echo ""
echo "Listening:"
docker exec "$CONTAINER" ss -ulnp | grep "${VPN_PORT}" || echo "  Nothing on ${VPN_PORT}"

echo ""
echo "Log:"
docker exec "$CONTAINER" tail -5 "/var/log/openvpn-${PEER_NAME}.log" 2>/dev/null

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Done! Now on your machine:                      ║${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}║  1. Copy the .ovpn file:                         ║${NC}"
echo -e "${CYAN}║     scp -P 1352 root@${PUBLIC_IP}:${HOST_DIR}/${PEER_NAME}.ovpn .  ${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}║  2. Connect:                                     ║${NC}"
echo -e "${CYAN}║     sudo openvpn --config ${PEER_NAME}.ovpn      ║${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}║  3. Test:                                        ║${NC}"
echo -e "${CYAN}║     ping 10.10.0.1                               ║${NC}"
echo -e "${CYAN}║     curl ifconfig.me  (should show ${PUBLIC_IP}) ║${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# Quick HTTP server to download .ovpn
echo -e "${YELLOW}Quick download option (run then download from phone/PC):${NC}"
echo "  cd ${HOST_DIR} && python3 -m http.server 8888"
echo "  → http://${PUBLIC_IP}:8888/${PEER_NAME}.ovpn"
echo "  → CTRL+C after download"
echo ""
