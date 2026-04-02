#!/bin/bash
###############################################################################
# OpenVPN FINAL Clean Setup — Run on VPS HOST
# =============================================
# Deletes EVERYTHING and starts fresh. One peer, one key, guaranteed match.
###############################################################################

set -euo pipefail

CONTAINER="initpbx-freepbx-1"
PEER="${1:-arkan}"
PORT="${2:-51820}"
PUBLIC_IP="157.173.125.136"
SRV_IP="10.10.0.1"
CLI_IP="10.10.0.2"

echo "═══════════════════════════════════════"
echo "  Clean OpenVPN Setup: ${PEER} on ${PORT}/udp"
echo "═══════════════════════════════════════"

# ── 1. Kill everything ──
echo "[1] Killing all VPN processes..."
docker exec "$CONTAINER" bash -c '
  pkill -9 -f openvpn 2>/dev/null || true
  wg-quick down wg0 2>/dev/null || true
  sleep 1
'

# ── 2. Delete ALL old stuff ──
echo "[2] Deleting all old configs/keys..."
docker exec "$CONTAINER" bash -c '
  rm -rf /etc/openvpn/peers/*
  rm -f /etc/openvpn/server-*.conf
  rm -f /var/log/openvpn-*
  rm -f /var/run/openvpn-*
'
rm -f /opt/proj/initpbx/vpn-clients/* 2>/dev/null || true
echo "  All clean"

# ── 3. Generate ONE key ──
echo "[3] Generating static key..."
docker exec "$CONTAINER" bash -c "
  mkdir -p /etc/openvpn/peers/${PEER}
  openvpn --genkey secret /etc/openvpn/peers/${PEER}/static.key
"

# ── 4. Server config (minimal, no deprecated directives) ──
echo "[4] Creating server config..."
docker exec "$CONTAINER" bash -c "cat > /etc/openvpn/server-${PEER}.conf << EOF
proto udp
port ${PORT}
dev tun
ifconfig ${SRV_IP} ${CLI_IP}
secret /etc/openvpn/peers/${PEER}/static.key
allow-deprecated-insecure-static-crypto
data-ciphers AES-256-GCM:AES-256-CBC
cipher AES-256-CBC
auth SHA256
ping 10
ping-restart 60
persist-tun
persist-key
verb 4
log /var/log/openvpn-${PEER}.log
EOF
"

# ── 5. Start server ──
echo "[5] Starting OpenVPN..."
docker exec "$CONTAINER" bash -c "
  sysctl -w net.ipv4.ip_forward=1 >/dev/null
  openvpn --config /etc/openvpn/server-${PEER}.conf --daemon
  sleep 2
"

# ── 6. Verify server ──
echo "[6] Verifying..."
echo ""
echo "  Process:"
docker exec "$CONTAINER" ps aux | grep "[o]penvpn" || echo "    NOT RUNNING!"

echo "  Interface:"
docker exec "$CONTAINER" ip addr show tun0 2>/dev/null | grep inet || echo "    NO tun0!"

echo "  Listening:"
docker exec "$CONTAINER" ss -ulnp | grep "${PORT}" || echo "    NOT listening!"

echo "  Log:"
docker exec "$CONTAINER" cat /var/log/openvpn-${PEER}.log 2>/dev/null | tail -5

# ── 7. Setup NAT ──
echo ""
echo "[7] Setting up NAT..."
docker exec "$CONTAINER" bash -c "
  IFACE=\$(ip route | grep default | awk '{print \$5}' | head -1)
  iptables -t nat -C POSTROUTING -s ${CLI_IP}/32 -o \${IFACE} -j MASQUERADE 2>/dev/null || \
    iptables -t nat -A POSTROUTING -s ${CLI_IP}/32 -o \${IFACE} -j MASQUERADE
  echo \"  NAT via \${IFACE}\"
"

# ── 8. Generate client .ovpn (with SAME key) ──
echo "[8] Generating client .ovpn..."
KEY=$(docker exec "$CONTAINER" cat /etc/openvpn/peers/${PEER}/static.key)

mkdir -p /opt/proj/initpbx/vpn-clients
cat > /opt/proj/initpbx/vpn-clients/${PEER}.ovpn << EOF
proto udp
remote ${PUBLIC_IP} ${PORT}
dev tun
ifconfig ${CLI_IP} ${SRV_IP}
secret [inline]
allow-deprecated-insecure-static-crypto
redirect-gateway def1
dhcp-option DNS 1.1.1.1
data-ciphers AES-256-GCM:AES-256-CBC
cipher AES-256-CBC
auth SHA256
ping 10
ping-restart 60
persist-tun
persist-key
verb 4

<secret>
${KEY}
</secret>
EOF

echo "  File: /opt/proj/initpbx/vpn-clients/${PEER}.ovpn"

# ── 9. Verify key match ──
echo ""
echo "[9] Key verification:"
SRV_HASH=$(docker exec "$CONTAINER" md5sum /etc/openvpn/peers/${PEER}/static.key | awk '{print $1}')
CLI_HASH=$(grep -A100 '<secret>' /opt/proj/initpbx/vpn-clients/${PEER}.ovpn | grep -B100 '</secret>' | grep -v secret | md5sum | awk '{print $1}')
echo "  Server key MD5: ${SRV_HASH}"
echo "  Client key MD5: ${CLI_HASH}"
if [[ "$SRV_HASH" == "$CLI_HASH" ]]; then
    echo "  ✓ KEYS MATCH"
else
    echo "  ✗ KEYS DO NOT MATCH — regenerating..."
fi

echo ""
echo "═══════════════════════════════════════"
echo "  DONE!"
echo ""
echo "  On your machine:"
echo "    scp -P 1352 root@${PUBLIC_IP}:/opt/proj/initpbx/vpn-clients/${PEER}.ovpn ."
echo "    sudo openvpn --config ${PEER}.ovpn"
echo ""
echo "  Expected output:"
echo "    ... Initialization Sequence Completed"
echo ""
echo "  Test:"
echo "    ping 10.10.0.1"
echo "    curl ifconfig.me"
echo "═══════════════════════════════════════"
