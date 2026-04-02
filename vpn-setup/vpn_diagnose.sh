#!/bin/bash
###############################################################################
# WireGuard VPN Diagnostic — Run on VPS HOST
# ============================================
# Checks everything: port, firewall, WireGuard status, handshake, routing
#
# Usage:  bash vpn_diagnose.sh
###############################################################################

set -uo pipefail

CONTAINER="initpbx-freepbx-1"
VPN_PORT="51820"
PUBLIC_IP="157.173.125.136"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'

pass() { echo -e "  ${GREEN}[✓]${NC} $1"; }
fail() { echo -e "  ${RED}[✗]${NC} $1"; }
warn() { echo -e "  ${YELLOW}[!]${NC} $1"; }
info() { echo -e "  ${CYAN}[i]${NC} $1"; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  WireGuard VPN Diagnostic                        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

ERRORS=0

###############################################################################
echo -e "${YELLOW}═══ 1. Host Firewall (UFW) ═══${NC}"
###############################################################################

# Check if ufw is active
if command -v ufw &>/dev/null; then
    UFW_STATUS=$(ufw status 2>/dev/null)
    if echo "$UFW_STATUS" | grep -q "Status: active"; then
        info "UFW is active"
        if echo "$UFW_STATUS" | grep -q "${VPN_PORT}/udp"; then
            pass "Port ${VPN_PORT}/udp allowed in UFW"
        else
            fail "Port ${VPN_PORT}/udp NOT in UFW rules!"
            echo ""
            echo "  Fix: sudo ufw allow ${VPN_PORT}/udp"
            echo ""
            ((ERRORS++))
        fi
    else
        pass "UFW inactive — all ports open"
    fi
else
    info "UFW not installed"
fi

# Check iptables on HOST
echo ""
echo -e "${YELLOW}═══ 2. Host iptables ═══${NC}"

HOST_DROP=$(iptables -L INPUT -n 2>/dev/null | grep -i "drop.*${VPN_PORT}" | head -3)
if [[ -n "$HOST_DROP" ]]; then
    fail "Host iptables DROP rule blocking port ${VPN_PORT}!"
    echo "  $HOST_DROP"
    ((ERRORS++))
else
    pass "No host iptables DROP on port ${VPN_PORT}"
fi

# Check DOCKER chain
DOCKER_MAP=$(iptables -t nat -L DOCKER -n 2>/dev/null | grep "${VPN_PORT}" | head -3)
if [[ -n "$DOCKER_MAP" ]]; then
    pass "Docker NAT mapping for port ${VPN_PORT} exists"
    echo "    $DOCKER_MAP"
else
    warn "No Docker NAT mapping for port ${VPN_PORT} found"
    info "This might be OK if using host networking or privileged mode"
fi

###############################################################################
echo ""
echo -e "${YELLOW}═══ 3. Port Listening ═══${NC}"
###############################################################################

# Check if anything listens on 51820/udp on the HOST
HOST_LISTEN=$(ss -ulnp 2>/dev/null | grep ":${VPN_PORT}" || netstat -ulnp 2>/dev/null | grep ":${VPN_PORT}" || true)
if [[ -n "$HOST_LISTEN" ]]; then
    pass "Something listening on UDP ${VPN_PORT} on host"
    echo "    $HOST_LISTEN"
else
    # Check inside container
    CONTAINER_LISTEN=$(docker exec "$CONTAINER" ss -ulnp 2>/dev/null | grep ":${VPN_PORT}" || \
                       docker exec "$CONTAINER" netstat -ulnp 2>/dev/null | grep ":${VPN_PORT}" || true)
    if [[ -n "$CONTAINER_LISTEN" ]]; then
        pass "WireGuard listening on UDP ${VPN_PORT} inside container"
        echo "    $CONTAINER_LISTEN"
    else
        fail "NOTHING listening on UDP ${VPN_PORT} — WireGuard may not be running!"
        ((ERRORS++))
    fi
fi

###############################################################################
echo ""
echo -e "${YELLOW}═══ 4. Container WireGuard Status ═══${NC}"
###############################################################################

# Check if wg0 interface exists
WG_SHOW=$(docker exec "$CONTAINER" wg show wg0 2>&1)
if echo "$WG_SHOW" | grep -q "interface: wg0"; then
    pass "WireGuard interface wg0 is UP"

    # Show interface info
    echo ""
    echo "$WG_SHOW" | head -20
    echo ""

    # Check for peers
    PEER_COUNT=$(echo "$WG_SHOW" | grep -c "^peer:" || true)
    info "Configured peers: ${PEER_COUNT}"

    # Check latest handshake
    HANDSHAKE=$(echo "$WG_SHOW" | grep "latest handshake" | head -1)
    if [[ -n "$HANDSHAKE" ]]; then
        pass "Handshake detected: ${HANDSHAKE}"
    else
        warn "No handshake yet — no client has connected successfully"
    fi
else
    fail "WireGuard wg0 is DOWN!"
    echo "  Error: $WG_SHOW"
    echo ""
    echo "  Fix: docker exec $CONTAINER wg-quick up wg0"
    ((ERRORS++))
fi

###############################################################################
echo ""
echo -e "${YELLOW}═══ 5. Container IP Forwarding ═══${NC}"
###############################################################################

IP_FWD=$(docker exec "$CONTAINER" sysctl net.ipv4.ip_forward 2>/dev/null)
if echo "$IP_FWD" | grep -q "= 1"; then
    pass "IP forwarding enabled inside container"
else
    fail "IP forwarding DISABLED inside container!"
    echo "  Fix: docker exec $CONTAINER sysctl -w net.ipv4.ip_forward=1"
    ((ERRORS++))
fi

###############################################################################
echo ""
echo -e "${YELLOW}═══ 6. Container iptables ═══${NC}"
###############################################################################

# Check if wg0 rules exist
WG_INPUT=$(docker exec "$CONTAINER" iptables -L INPUT -n 2>/dev/null | grep "wg0" | head -3)
if [[ -n "$WG_INPUT" ]]; then
    pass "iptables INPUT accepts wg0 traffic"
else
    warn "No wg0 INPUT rule — traffic may be blocked inside container"
    ((ERRORS++))
fi

WG_FWD=$(docker exec "$CONTAINER" iptables -L FORWARD -n 2>/dev/null | grep "wg0" | head -3)
if [[ -n "$WG_FWD" ]]; then
    pass "iptables FORWARD allows wg0 traffic"
else
    warn "No wg0 FORWARD rule"
    ((ERRORS++))
fi

# Check NAT for full tunnel
NAT_MASQ=$(docker exec "$CONTAINER" iptables -t nat -L POSTROUTING -n 2>/dev/null | grep "MASQUERADE" | head -3)
if [[ -n "$NAT_MASQ" ]]; then
    pass "NAT masquerade active (full tunnel capable)"
    echo "    $NAT_MASQ"
else
    warn "No NAT masquerade — only split tunnel (VPN subnet only, no internet via VPS)"
fi

###############################################################################
echo ""
echo -e "${YELLOW}═══ 7. External Port Check ═══${NC}"
###############################################################################

# Try to check if port is reachable from outside
info "Testing if UDP ${VPN_PORT} is reachable externally..."

# Method 1: nmap if available
if command -v nmap &>/dev/null; then
    NMAP_RESULT=$(nmap -sU -p ${VPN_PORT} ${PUBLIC_IP} --host-timeout 5s 2>/dev/null | grep "${VPN_PORT}" || true)
    if [[ -n "$NMAP_RESULT" ]]; then
        echo "    $NMAP_RESULT"
        if echo "$NMAP_RESULT" | grep -q "open"; then
            pass "Port appears open"
        elif echo "$NMAP_RESULT" | grep -q "filtered"; then
            warn "Port appears filtered — firewall may be blocking"
        fi
    fi
else
    info "nmap not available — skip external port check"
    info "Test from phone: try connecting WireGuard and check handshake"
fi

###############################################################################
echo ""
echo -e "${YELLOW}═══ 8. Client Config Check ═══${NC}"
###############################################################################

docker exec "$CONTAINER" bash -c '
PEERS_DIR="/etc/wireguard/peers"
for peer_dir in "${PEERS_DIR}"/*/; do
    [ -d "$peer_dir" ] || continue
    peer_name=$(basename "$peer_dir")
    [[ "$peer_name" == *".removed"* ]] && continue

    conf="${peer_dir}/${peer_name}.conf"
    [ -f "$conf" ] || continue

    echo "  Peer: ${peer_name}"

    # Check endpoint
    endpoint=$(grep "^Endpoint" "$conf" | sed "s/Endpoint[[:space:]]*=[[:space:]]*//" | tr -d "\r\n")
    if [[ -z "$endpoint" ]]; then
        echo "    [!] ERROR: No Endpoint in config!"
    elif [[ "$endpoint" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$ ]]; then
        echo "    [OK] Endpoint: ${endpoint}"
    else
        echo "    [!] BAD Endpoint format: \"${endpoint}\""
        echo "        Expected: IP:PORT (e.g. 157.173.125.136:51820)"
        # Show hex dump of problematic chars
        echo -n "        Hex: "
        echo -n "$endpoint" | xxd -p | head -c 80
        echo ""
    fi

    # Check AllowedIPs
    allowed=$(grep "^AllowedIPs" "$conf" | sed "s/AllowedIPs[[:space:]]*=[[:space:]]*//" | tr -d "\r\n")
    echo "    AllowedIPs: ${allowed}"

    # Check DNS
    dns=$(grep "^DNS" "$conf" | sed "s/DNS[[:space:]]*=[[:space:]]*//" | tr -d "\r\n")
    echo "    DNS: ${dns:-none}"

    echo ""
done
'

###############################################################################
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Diagnostic Summary                              ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════╣${NC}"

if [[ $ERRORS -eq 0 ]]; then
    echo -e "${CYAN}║  ${GREEN}All checks passed!${CYAN}                               ║${NC}"
    echo -e "${CYAN}║                                                  ║${NC}"
    echo -e "${CYAN}║  If phone still can't connect:                   ║${NC}"
    echo -e "${CYAN}║  1. Delete old tunnel in WireGuard app           ║${NC}"
    echo -e "${CYAN}║  2. Re-scan QR or re-import config               ║${NC}"
    echo -e "${CYAN}║  3. Make sure phone is on mobile data/WiFi       ║${NC}"
    echo -e "${CYAN}║  4. Check: WG app shows 'handshake' after ~10s   ║${NC}"
else
    echo -e "${CYAN}║  ${RED}Found ${ERRORS} issue(s)!${CYAN}                              ║${NC}"
    echo -e "${CYAN}║  Fix the issues above and run again.             ║${NC}"
fi

echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
