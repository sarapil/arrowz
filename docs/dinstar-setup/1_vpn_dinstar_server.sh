#!/bin/bash
###############################################################################
# Dinstar GSM Gateway — OpenVPN TLS Server Setup (Run on VPS HOST)
# ==================================================================
# Creates an OpenVPN TLS server on the FreePBX container so the
# Dinstar UC2000-VE-8G can connect DIRECTLY via VPN.
#
# The Dinstar supports OpenVPN TLS natively (proven with existing config).
# No gateway machine needed — direct tunnel!
#
# Architecture (SIMPLIFIED):
#   [Dinstar UC2000-VE-8G] ═══OpenVPN TLS═══ [FreePBX/Asterisk]
#       10.10.1.2                              10.10.1.1
#       SIP → 10.10.1.1:51600                 PJSIP endpoint
#       RTP direct over tunnel                 No NAT needed
#
# This creates:
#   - Easy-RSA CA + server cert + client cert
#   - tls-auth HMAC key
#   - OpenVPN TLS server config (port 51821/UDP, tun1)
#   - Client .ovpn file with all certs inline (Dinstar-compatible)
###############################################################################

set -euo pipefail

CONTAINER="initpbx-freepbx-1"
PORT="51821"
PUBLIC_IP="157.173.125.136"
SRV_IP="10.10.1.1"       # FreePBX VPN IP
CLI_IP="10.10.1.2"       # Dinstar VPN IP
VPN_NET="10.10.1.0"
VPN_MASK="255.255.255.0"
TUN_DEV="tun1"           # tun0 = arkan static VPN
CLIENT_NAME="dinstar"
OVPN_DIR="/etc/openvpn/dinstar-tls"

echo "═══════════════════════════════════════════════════════════"
echo "  Dinstar OpenVPN TLS Server Setup"
echo "  Port: ${PORT}/UDP  Subnet: ${SRV_IP} ↔ ${CLI_IP}"
echo "  Interface: ${TUN_DEV}  (separate from arkan on tun0)"
echo "═══════════════════════════════════════════════════════════"

# ── 1. Check existing arkan VPN is still running ──
echo ""
echo "[1] Checking existing arkan VPN (tun0)..."
docker exec "$CONTAINER" ip addr show tun0 2>/dev/null | grep inet || {
    echo "  ⚠  tun0 (arkan VPN) not running — that's OK, this is independent"
}

# ── 2. Clean previous dinstar-tls config ──
echo ""
echo "[2] Cleaning previous dinstar-tls config..."
docker exec "$CONTAINER" bash -c "
    pkill -f 'openvpn.*dinstar-tls' 2>/dev/null || true
    sleep 1
    rm -rf ${OVPN_DIR}
    echo '  ✓ Clean'
"

# ── 3. Install easy-rsa if not present ──
echo ""
echo "[3] Ensuring easy-rsa is available..."
docker exec "$CONTAINER" bash -c "
    if ! command -v easyrsa &>/dev/null && [[ ! -d /usr/share/easy-rsa ]]; then
        echo '  Installing easy-rsa...'
        apt-get update -qq && apt-get install -y -qq easy-rsa 2>/dev/null
    fi
    # Find easy-rsa location
    if command -v easyrsa &>/dev/null; then
        echo \"  ✓ easy-rsa found: \$(which easyrsa)\"
    elif [[ -f /usr/share/easy-rsa/easyrsa ]]; then
        echo '  ✓ easy-rsa found: /usr/share/easy-rsa/easyrsa'
    else
        echo '  ℹ  easy-rsa binary not found, will use openssl directly'
    fi
"

# ── 4. Create PKI (CA + Server + Client certs) ──
echo ""
echo "[4] Creating PKI infrastructure..."

docker exec "$CONTAINER" bash -c "
    set -e
    mkdir -p ${OVPN_DIR}/pki

    cd ${OVPN_DIR}/pki

    # ── 4a. Generate CA ──
    echo '  [4a] Generating CA...'
    openssl req -x509 -newkey rsa:2048 -keyout ca.key -out ca.crt \
        -days 3650 -nodes -subj '/CN=Arrowz-Dinstar-CA' 2>/dev/null
    echo '       ✓ CA created (valid 10 years)'

    # ── 4b. Generate Server cert ──
    echo '  [4b] Generating server certificate...'
    openssl req -newkey rsa:2048 -keyout server.key -out server.csr \
        -nodes -subj '/CN=dinstar-vpn-server' 2>/dev/null

    # Create extensions file for server
    cat > server_ext.cnf << 'EXTEOF'
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
EXTEOF

    openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
        -CAcreateserial -out server.crt -days 3650 \
        -extfile server_ext.cnf 2>/dev/null
    echo '       ✓ Server cert created'

    # ── 4c. Generate Client cert (Dinstar) ──
    echo '  [4c] Generating client certificate (${CLIENT_NAME})...'
    openssl req -newkey rsa:2048 -keyout ${CLIENT_NAME}.key -out ${CLIENT_NAME}.csr \
        -nodes -subj '/CN=${CLIENT_NAME}' 2>/dev/null

    # Create extensions file for client
    cat > client_ext.cnf << 'EXTEOF'
basicConstraints=CA:FALSE
keyUsage=digitalSignature
extendedKeyUsage=clientAuth
EXTEOF

    openssl x509 -req -in ${CLIENT_NAME}.csr -CA ca.crt -CAkey ca.key \
        -CAcreateserial -out ${CLIENT_NAME}.crt -days 3650 \
        -extfile client_ext.cnf 2>/dev/null
    echo '       ✓ Client cert created'

    # ── 4d. Generate Diffie-Hellman parameters ──
    echo '  [4d] Generating DH parameters (this may take a moment)...'
    openssl dhparam -out dh2048.pem 2048 2>/dev/null
    echo '       ✓ DH params created'

    # ── 4e. Generate tls-auth key ──
    echo '  [4e] Generating tls-auth HMAC key...'
    openvpn --genkey secret ta.key 2>/dev/null || openvpn --genkey --secret ta.key 2>/dev/null
    echo '       ✓ tls-auth key created'

    # Summary
    echo ''
    echo '  PKI Files:'
    ls -la ${OVPN_DIR}/pki/ | grep -v '^\.\|csr\|cnf\|srl'
"

# ── 5. Create Server Config ──
echo ""
echo "[5] Creating OpenVPN TLS server config..."

docker exec "$CONTAINER" bash -c "cat > ${OVPN_DIR}/server.conf << 'SRVEOF'
# ═══════════════════════════════════════════════════
# Dinstar GSM Gateway — OpenVPN TLS Server
# ═══════════════════════════════════════════════════
# Point-to-point TLS mode for Dinstar UC2000-VE-8G
# Server: ${SRV_IP}, Client: ${CLI_IP}

port ${PORT}
proto udp
dev ${TUN_DEV}
dev-type tun

# Topology: point-to-point (1 client only)
topology p2p
ifconfig ${SRV_IP} ${CLI_IP}

# PKI
ca   ${OVPN_DIR}/pki/ca.crt
cert ${OVPN_DIR}/pki/server.crt
key  ${OVPN_DIR}/pki/server.key
dh   ${OVPN_DIR}/pki/dh2048.pem

# HMAC authentication (tls-auth)
tls-auth ${OVPN_DIR}/pki/ta.key 0
# key-direction 0 = server side

# Encryption (match Dinstar's proven config)
cipher AES-256-CBC
data-ciphers AES-256-GCM:AES-256-CBC
auth SHA256
tls-version-min 1.0

# Keepalive
ping 10
ping-restart 60

# Persist
persist-key
persist-tun

# MTU (match Dinstar's working config)
tun-mtu 1400
mssfix 1360

# Logging
verb 3
log /var/log/openvpn-dinstar-tls.log
status /var/log/openvpn-dinstar-tls-status.log 30

# Push routes so Dinstar can reach Asterisk
# (not needed for p2p, but explicit is good)
push "route ${SRV_IP} 255.255.255.255"
SRVEOF
"
echo "  ✓ Server config created at ${OVPN_DIR}/server.conf"

# ── 6. Start OpenVPN Server ──
echo ""
echo "[6] Starting OpenVPN TLS server..."

docker exec "$CONTAINER" bash -c "
    sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1
    openvpn --config ${OVPN_DIR}/server.conf --daemon openvpn-dinstar-tls
    sleep 3
"

# ── 7. Verify Server ──
echo ""
echo "[7] Verifying server..."

echo "  Process:"
docker exec "$CONTAINER" ps aux | grep "[o]penvpn.*dinstar-tls" || echo "    ❌ NOT RUNNING!"

echo "  Interface (${TUN_DEV}):"
docker exec "$CONTAINER" ip addr show ${TUN_DEV} 2>/dev/null | grep inet || echo "    ⚠  ${TUN_DEV} not up yet (waiting for client)"

echo "  Listening (port ${PORT}):"
docker exec "$CONTAINER" ss -ulnp | grep "${PORT}" || echo "    ❌ NOT listening!"

echo "  Log (last 5 lines):"
docker exec "$CONTAINER" tail -5 /var/log/openvpn-dinstar-tls.log 2>/dev/null || echo "    No log yet"

# ── 8. Open port on VPS host firewall ──
echo ""
echo "[8] Opening port ${PORT}/udp on host firewall..."
if command -v ufw &>/dev/null; then
    ufw allow ${PORT}/udp comment "Dinstar VPN TLS" 2>/dev/null || true
    echo "  ✓ ufw rule added"
else
    iptables -C INPUT -p udp --dport ${PORT} -j ACCEPT 2>/dev/null || {
        iptables -A INPUT -p udp --dport ${PORT} -j ACCEPT 2>/dev/null || true
    }
    echo "  ✓ iptables rule added"
fi

# ── 9. Generate Client .ovpn (Dinstar-compatible format) ──
echo ""
echo "[9] Generating Dinstar client .ovpn..."

CA_CRT=$(docker exec "$CONTAINER" cat ${OVPN_DIR}/pki/ca.crt)
CLI_CRT=$(docker exec "$CONTAINER" cat ${OVPN_DIR}/pki/${CLIENT_NAME}.crt)
CLI_KEY=$(docker exec "$CONTAINER" cat ${OVPN_DIR}/pki/${CLIENT_NAME}.key)
TA_KEY=$(docker exec "$CONTAINER" cat ${OVPN_DIR}/pki/ta.key)

mkdir -p /opt/proj/initpbx/vpn-clients

cat > /opt/proj/initpbx/vpn-clients/${CLIENT_NAME}-tls.ovpn << EOF
# ═══════════════════════════════════════════════════
# Dinstar UC2000-VE-8G → FreePBX OpenVPN TLS Client
# ═══════════════════════════════════════════════════
# Upload this to Dinstar web UI: System → OpenVPN
#
# After connecting:
#   SIP Server IP:   ${SRV_IP}
#   SIP Server Port: ${FREEPBX_SIP_PORT:-51600}
#   Username:        dinstar
#   Password:        D1nstar#VPN2026!

client
dev tun
proto udp
remote ${PUBLIC_IP} ${PORT}
resolv-retry infinite
nobind
persist-key
persist-tun
verb 4
reneg-sec 0

# Encryption (proven working on Dinstar)
cipher AES-256-CBC
data-ciphers AES-256-GCM:AES-256-CBC
auth SHA256

# Server certificate verification
remote-cert-tls server
tls-version-min 1.0

# MTU settings (proven working on Dinstar)
tun-mtu 1400
mssfix 1360

# tls-auth: key-direction 1 = client side
key-direction 1

<ca>
${CA_CRT}
</ca>
<cert>
${CLI_CRT}
</cert>
<key>
${CLI_KEY}
</key>
<tls-auth>
${TA_KEY}
</tls-auth>
EOF

echo "  ✓ File: /opt/proj/initpbx/vpn-clients/${CLIENT_NAME}-tls.ovpn"

# ── 10. Verify certs match ──
echo ""
echo "[10] Certificate verification:"
SRV_CA_HASH=$(docker exec "$CONTAINER" openssl x509 -in ${OVPN_DIR}/pki/ca.crt -noout -fingerprint 2>/dev/null | cut -d= -f2)
CLI_CA_HASH=$(echo "$CA_CRT" | openssl x509 -noout -fingerprint 2>/dev/null | cut -d= -f2)
echo "  Server CA fingerprint: ${SRV_CA_HASH}"
echo "  Client CA fingerprint: ${CLI_CA_HASH}"
if [[ "$SRV_CA_HASH" == "$CLI_CA_HASH" ]]; then
    echo "  ✅ CA certs MATCH"
else
    echo "  ❌ CA mismatch!"
    exit 1
fi

# ── 11. Auto-start ──
echo ""
echo "[11] Adding auto-start to rc.local..."
docker exec "$CONTAINER" bash -c "
    if ! grep -q 'dinstar-tls' /etc/rc.local 2>/dev/null; then
        if [[ ! -f /etc/rc.local ]]; then
            echo '#!/bin/bash' > /etc/rc.local
            echo 'exit 0' >> /etc/rc.local
            chmod +x /etc/rc.local
        fi
        sed -i '/^exit 0/i openvpn --config ${OVPN_DIR}/server.conf --daemon openvpn-dinstar-tls' /etc/rc.local
        echo '  ✓ Added to rc.local'
    else
        echo '  ✓ Already in rc.local'
    fi
"

# ── 12. Setup NAT/routing ──
echo ""
echo "[12] Setting up NAT for Dinstar subnet..."
docker exec "$CONTAINER" bash -c "
    IFACE=\$(ip route | grep default | awk '{print \$5}' | head -1)
    iptables -t nat -C POSTROUTING -s ${CLI_IP}/32 -o \${IFACE} -j MASQUERADE 2>/dev/null || \
        iptables -t nat -A POSTROUTING -s ${CLI_IP}/32 -o \${IFACE} -j MASQUERADE
    echo \"  ✓ NAT via \${IFACE}\"
"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ OpenVPN TLS Server READY"
echo ""
echo "  VPN Tunnel:  ${SRV_IP} ↔ ${CLI_IP} on port ${PORT}/udp"
echo "  Interface:   ${TUN_DEV}"
echo "  Auth:        TLS (certificates + tls-auth HMAC)"
echo ""
echo "  Client file: /opt/proj/initpbx/vpn-clients/${CLIENT_NAME}-tls.ovpn"
echo ""
echo "  Next Steps:"
echo "  1. Copy the .ovpn content to Dinstar:"
echo "     cat /opt/proj/initpbx/vpn-clients/${CLIENT_NAME}-tls.ovpn"
echo ""
echo "  2. Upload to Dinstar web UI → System → OpenVPN"
echo "     Or paste the sections (CA, Cert, Key, TLS-Auth) separately"
echo ""
echo "  3. Run the Asterisk trunk script:"
echo "     bash 3_asterisk_dinstar_trunk.sh"
echo ""
echo "  4. Configure Dinstar SIP:"
echo "     SIP Server: ${SRV_IP}  Port: 51600"
echo "     Username: dinstar  Password: D1nstar#VPN2026!"
echo "═══════════════════════════════════════════════════════════"
