#!/bin/bash
###############################################################################
# Enable Full Tunnel — Run on VPS HOST
# ======================================
# Changes WireGuard from split-tunnel to full-tunnel:
#   - Adds NAT/Masquerade on server (so VPN clients use VPS IP for internet)
#   - Updates admin client config: AllowedIPs = 0.0.0.0/0
#   - Regenerates QR code
#
# Usage:  bash 3_enable_full_tunnel.sh
###############################################################################

set -euo pipefail

CONTAINER="initpbx-freepbx-1"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Enable Full Tunnel — All traffic via VPS IP     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Step 1: Add NAT/Masquerade to server wg0.conf
###############################################################################
echo -e "${YELLOW}[1/4] Adding NAT masquerade to server config...${NC}"

docker exec "$CONTAINER" bash -c '
WG_CONF="/etc/wireguard/wg0.conf"
MAIN_IFACE=$(ip route | grep default | awk "{print \$5}" | head -1)

# Check if masquerade already exists
if grep -q "MASQUERADE" "$WG_CONF" 2>/dev/null; then
    echo "  NAT masquerade already in config — skipping"
    exit 0
fi

# Add masquerade rules after existing PostUp lines
# We need to add BEFORE PostDown lines
sed -i "/^PostUp = iptables -A FORWARD -o wg0/a PostUp = iptables -t nat -A POSTROUTING -s 10.10.0.0/24 -o ${MAIN_IFACE} -j MASQUERADE" "$WG_CONF"
sed -i "/^PostDown = iptables -D FORWARD -o wg0/a PostDown = iptables -t nat -D POSTROUTING -s 10.10.0.0/24 -o ${MAIN_IFACE} -j MASQUERADE" "$WG_CONF"

echo "  Added NAT masquerade via ${MAIN_IFACE}"
'

echo -e "${GREEN}[✓] Server NAT configured${NC}"

###############################################################################
# Step 2: Apply masquerade NOW (without restart)
###############################################################################
echo -e "${YELLOW}[2/4] Applying NAT rules to running interface...${NC}"

docker exec "$CONTAINER" bash -c '
MAIN_IFACE=$(ip route | grep default | awk "{print \$5}" | head -1)

# Check if already applied
if iptables -t nat -C POSTROUTING -s 10.10.0.0/24 -o ${MAIN_IFACE} -j MASQUERADE 2>/dev/null; then
    echo "  NAT rule already active"
else
    iptables -t nat -A POSTROUTING -s 10.10.0.0/24 -o ${MAIN_IFACE} -j MASQUERADE
    echo "  NAT rule applied on ${MAIN_IFACE}"
fi

# Ensure IP forwarding is on
sysctl -w net.ipv4.ip_forward=1 > /dev/null
echo "  IP forwarding: enabled"
'

echo -e "${GREEN}[✓] NAT active${NC}"

###############################################################################
# Step 3: Update ALL client configs — AllowedIPs = 0.0.0.0/0
###############################################################################
echo -e "${YELLOW}[3/4] Updating client configs to full tunnel...${NC}"

docker exec "$CONTAINER" bash -c '
PEERS_DIR="/etc/wireguard/peers"

for peer_dir in "${PEERS_DIR}"/*/; do
    [ -d "$peer_dir" ] || continue
    peer_name=$(basename "$peer_dir")
    [[ "$peer_name" == *".removed"* ]] && continue

    conf="${peer_dir}/${peer_name}.conf"
    [ -f "$conf" ] || continue

    # Check current AllowedIPs
    current=$(grep "^AllowedIPs" "$conf" | head -1)

    if echo "$current" | grep -q "0.0.0.0/0"; then
        echo "  ${peer_name}: already full tunnel"
        continue
    fi

    # Replace AllowedIPs line
    sed -i "s|^AllowedIPs = .*|AllowedIPs = 0.0.0.0/0, ::/0|" "$conf"
    echo "  ${peer_name}: updated to full tunnel (0.0.0.0/0)"
done
'

echo -e "${GREEN}[✓] Client configs updated${NC}"

###############################################################################
# Step 4: Regenerate QR codes
###############################################################################
echo -e "${YELLOW}[4/4] Regenerating QR codes...${NC}"

docker exec "$CONTAINER" bash -c '
PEERS_DIR="/etc/wireguard/peers"

for peer_dir in "${PEERS_DIR}"/*/; do
    [ -d "$peer_dir" ] || continue
    peer_name=$(basename "$peer_dir")
    [[ "$peer_name" == *".removed"* ]] && continue

    conf="${peer_dir}/${peer_name}.conf"
    [ -f "$conf" ] || continue

    # Generate clean config (no comments, no empty lines)
    clean=$(grep -v "^#" "$conf" | grep -v "^$" | sed "s/\r$//" | sed "s/[[:space:]]*$//")
    echo "$clean" > "${peer_dir}/${peer_name}_clean.conf"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Peer: ${peer_name}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "$clean"
    echo ""

    if command -v qrencode &>/dev/null; then
        echo "  QR Code:"
        qrencode -t ansiutf8 <<< "$clean"
        qrencode -t png -o "${peer_dir}/${peer_name}_qr.png" <<< "$clean" 2>/dev/null || true
    fi
done
'

echo ""
echo -e "${GREEN}[✓] QR codes regenerated${NC}"

###############################################################################
# Verify
###############################################################################
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Full Tunnel Enabled!                            ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}║  What changed:                                   ║${NC}"
echo -e "${CYAN}║  1. Server: Added NAT masquerade                 ║${NC}"
echo -e "${CYAN}║  2. Clients: AllowedIPs = 0.0.0.0/0             ║${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}║  Now all VPN client traffic routes through       ║${NC}"
echo -e "${CYAN}║  the VPS IP: 157.173.125.136                     ║${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}║  On phone: Delete old tunnel, scan new QR        ║${NC}"
echo -e "${CYAN}║  Test: Visit whatismyip.com — should show VPS IP ║${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# Show current NAT rules
echo -e "${YELLOW}Current NAT rules:${NC}"
docker exec "$CONTAINER" iptables -t nat -L POSTROUTING -n -v 2>/dev/null | head -5
echo ""

# Show server status
echo -e "${YELLOW}WireGuard status:${NC}"
docker exec "$CONTAINER" wg show wg0 2>/dev/null | head -15
