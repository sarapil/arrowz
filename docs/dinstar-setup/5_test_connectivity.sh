#!/bin/bash
###############################################################################
# Dinstar Integration — Connectivity Test Script (Direct VPN Architecture)
# Run on VPS HOST to verify the entire chain works
###############################################################################

set -euo pipefail

CONTAINER="initpbx-freepbx-1"
ARKAN_VPN_IP="10.10.0.1"     # Existing VPN (arkan/softphone)
DINSTAR_SRV_IP="10.10.1.1"   # Dinstar VPN server side
DINSTAR_CLI_IP="10.10.1.2"   # Dinstar VPN client side
SIP_PORT="51600"

echo "═══════════════════════════════════════════════════════"
echo "  Dinstar Integration — Connectivity Tests (Direct VPN)"
echo "═══════════════════════════════════════════════════════"

PASS=0
FAIL=0

pass() { PASS=$((PASS+1)); echo "  ✅ $1"; }
fail() { FAIL=$((FAIL+1)); echo "  ❌ $1"; }
warn() { echo "  ⚠️  $1"; }

# ── Test 1: Existing VPN (arkan) ──
echo ""
echo "── Test 1: Existing VPN (arkan on tun0) ──"
if docker exec "$CONTAINER" ip addr show tun0 2>/dev/null | grep -q "$ARKAN_VPN_IP"; then
    pass "tun0 UP with $ARKAN_VPN_IP"
else
    warn "tun0 not up (arkan VPN — independent of Dinstar)"
fi

# ── Test 2: Dinstar VPN (tun1) ──
echo ""
echo "── Test 2: Dinstar VPN (TLS server on tun1) ──"
if docker exec "$CONTAINER" ip addr show tun1 2>/dev/null | grep -q "$DINSTAR_SRV_IP"; then
    pass "tun1 UP with $DINSTAR_SRV_IP"
else
    fail "tun1 not up — run 1_vpn_dinstar_server.sh first"
fi

# ── Test 3: OpenVPN processes ──
echo ""
echo "── Test 3: OpenVPN processes ──"
ARKAN_PROC=$(docker exec "$CONTAINER" pgrep -af "server-arkan\|openvpn-arkan" 2>/dev/null | wc -l)
DINSTAR_PROC=$(docker exec "$CONTAINER" pgrep -af "dinstar-tls" 2>/dev/null | wc -l)

[[ "$ARKAN_PROC" -ge 1 ]] && pass "arkan OpenVPN running" || warn "arkan OpenVPN not running (independent)"
[[ "$DINSTAR_PROC" -ge 1 ]] && pass "dinstar-tls OpenVPN running" || fail "dinstar-tls OpenVPN not running"

# ── Test 4: Port listening ──
echo ""
echo "── Test 4: Ports ──"
docker exec "$CONTAINER" ss -ulnp | grep -q "51820" && pass "Port 51820/udp (arkan VPN)" || warn "Port 51820 not listening (arkan)"
docker exec "$CONTAINER" ss -ulnp | grep -q "51821" && pass "Port 51821/udp (dinstar VPN)" || fail "Port 51821 not listening"
docker exec "$CONTAINER" ss -ulnp | grep -q "$SIP_PORT" && pass "Port $SIP_PORT/udp (PJSIP)" || fail "Port $SIP_PORT not listening"

# ── Test 5: Dinstar VPN connectivity ──
echo ""
echo "── Test 5: Dinstar VPN Client Connectivity ──"
if docker exec "$CONTAINER" ping -c 2 -W 3 "$DINSTAR_CLI_IP" &>/dev/null; then
    pass "Dinstar reachable at $DINSTAR_CLI_IP (VPN connected!)"
else
    warn "Dinstar not reachable at $DINSTAR_CLI_IP (may not be connected yet)"
fi

# ── Test 6: PJSIP configuration ──
echo ""
echo "── Test 6: PJSIP Configuration ──"

# Check endpoint exists
if docker exec "$CONTAINER" asterisk -rx "pjsip show endpoint dinstar" 2>/dev/null | grep -q "type.*endpoint"; then
    pass "PJSIP endpoint 'dinstar' exists"
else
    fail "PJSIP endpoint 'dinstar' not found — run 3_asterisk_dinstar_trunk.sh"
fi

# Check auth exists
if docker exec "$CONTAINER" asterisk -rx "pjsip show auth dinstar-auth" 2>/dev/null | grep -q "type.*auth"; then
    pass "PJSIP auth 'dinstar-auth' exists"
else
    fail "PJSIP auth 'dinstar-auth' not found"
fi

# Check transport local_net
if docker exec "$CONTAINER" asterisk -rx "pjsip show transport 0.0.0.0-udp" 2>/dev/null | grep -q "10.10.1"; then
    pass "Transport has VPN local_net (10.10.1.x)"
else
    warn "Transport may not have VPN local_net — check pjsip.transports_custom_post.conf"
fi

# ── Test 7: Dinstar registration ──
echo ""
echo "── Test 7: Dinstar SIP Registration ──"
CONTACTS=$(docker exec "$CONTAINER" asterisk -rx "pjsip show contacts" 2>/dev/null)
if echo "$CONTACTS" | grep -qi "dinstar"; then
    pass "Dinstar is REGISTERED"
    echo "$CONTACTS" | grep -i "dinstar" | sed 's/^/    /'
else
    warn "Dinstar not registered yet (configure device → Steps 3 & 4 in device guide)"
fi

# ── Test 8: Dialplan context ──
echo ""
echo "── Test 8: Dialplan ──"
if docker exec "$CONTAINER" asterisk -rx "dialplan show from-dinstar" 2>/dev/null | grep -q "INBOUND GSM"; then
    pass "Dialplan context [from-dinstar] loaded"
else
    fail "Dialplan context [from-dinstar] not found"
fi

# ── Test 9: OpenVPN logs ──
echo ""
echo "── Test 9: VPN Logs (last 5 lines) ──"
echo "  arkan:"
docker exec "$CONTAINER" tail -3 /var/log/openvpn-arkan.log 2>/dev/null | sed 's/^/    /' || echo "    No log"
echo ""
echo "  dinstar-tls:"
docker exec "$CONTAINER" tail -5 /var/log/openvpn-dinstar-tls.log 2>/dev/null | sed 's/^/    /' || echo "    No log yet"

# ── Test 10: Certificate validity ──
echo ""
echo "── Test 10: TLS Certificates ──"
CERT_DIR="/etc/openvpn/dinstar-tls/pki"
SRV_EXPIRY=$(docker exec "$CONTAINER" openssl x509 -in ${CERT_DIR}/server.crt -noout -enddate 2>/dev/null | cut -d= -f2)
CLI_EXPIRY=$(docker exec "$CONTAINER" openssl x509 -in ${CERT_DIR}/dinstar.crt -noout -enddate 2>/dev/null | cut -d= -f2)
if [[ -n "$SRV_EXPIRY" ]]; then
    pass "Server cert expires: $SRV_EXPIRY"
else
    fail "Server cert not found"
fi
if [[ -n "$CLI_EXPIRY" ]]; then
    pass "Client cert expires: $CLI_EXPIRY"
else
    fail "Client cert not found"
fi

# ── Summary ──
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════════════════"

if [[ $FAIL -eq 0 ]]; then
    echo "  🎉 All tests passed! System is ready."
    echo ""
    echo "  Quick commands:"
    echo "    docker exec $CONTAINER asterisk -rx 'pjsip show contacts'"
    echo "    docker exec $CONTAINER asterisk -rx 'pjsip show endpoint dinstar'"
    echo "    docker exec $CONTAINER tail -f /var/log/openvpn-dinstar-tls.log"
else
    echo "  Fix the failed tests above, then run this script again."
fi
echo ""
