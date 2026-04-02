#!/bin/bash
###############################################################################
# Remote deployment script — runs ON the VPS host
# Copies tarball into FreePBX container and starts OpenVPN TLS
###############################################################################
set -e

CONTAINER="initpbx-freepbx-1"
REMOTE_DIR="/etc/openvpn/dinstar-tls"

echo "[2a] Stopping existing dinstar VPN if running..."
docker exec "$CONTAINER" bash -c "pkill -f 'dinstar-tls' 2>/dev/null || true"
sleep 1

echo "[2b] Cleaning old config..."
docker exec "$CONTAINER" bash -c "rm -rf ${REMOTE_DIR}"

echo "[2c] Creating directory..."
docker exec "$CONTAINER" mkdir -p ${REMOTE_DIR}/pki

echo "[2d] Copying tarball into container..."
docker cp /tmp/dinstar-vpn-deploy.tar.gz ${CONTAINER}:/tmp/dinstar-vpn-deploy.tar.gz

echo "[2e] Extracting..."
docker exec "$CONTAINER" bash -c "
    cd ${REMOTE_DIR}
    tar xzf /tmp/dinstar-vpn-deploy.tar.gz
    chmod 600 pki/*.key
    rm -f /tmp/dinstar-vpn-deploy.tar.gz
    echo 'Files:'
    ls -la ${REMOTE_DIR}/pki/
"

echo "[2f] Starting OpenVPN TLS server..."
docker exec "$CONTAINER" bash -c "
    sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1
    openvpn --config ${REMOTE_DIR}/server.conf --daemon openvpn-dinstar-tls
    sleep 3
"

echo "[2g] Verifying..."
echo "  Process:"
docker exec "$CONTAINER" ps aux | grep "[o]penvpn.*dinstar-tls" || echo "    ❌ NOT RUNNING"
echo "  Port 51821:"
docker exec "$CONTAINER" ss -ulnp | grep "51821" || echo "    ❌ NOT listening"
echo "  tun1:"
docker exec "$CONTAINER" ip addr show tun1 2>/dev/null | grep inet || echo "    ⚠  tun1 not up yet (waiting for client)"
echo "  Log:"
docker exec "$CONTAINER" tail -5 /var/log/openvpn-dinstar-tls.log 2>/dev/null || echo "    No log"

echo "[2h] Adding auto-start to rc.local..."
docker exec "$CONTAINER" bash -c "
    if [[ ! -f /etc/rc.local ]]; then
        echo '#!/bin/bash' > /etc/rc.local
        echo 'exit 0' >> /etc/rc.local
        chmod +x /etc/rc.local
    fi
    if ! grep -q 'dinstar-tls' /etc/rc.local 2>/dev/null; then
        sed -i '/^exit 0/i openvpn --config ${REMOTE_DIR}/server.conf --daemon openvpn-dinstar-tls' /etc/rc.local
        echo '  ✓ Added to rc.local'
    else
        echo '  ✓ Already in rc.local'
    fi
"

echo "[2i] Saving .ovpn to VPS..."
mkdir -p /opt/proj/initpbx/vpn-clients
docker exec "$CONTAINER" cat ${REMOTE_DIR}/dinstar-tls.ovpn > /opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn
echo "  ✓ /opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn"

echo "[2j] Opening port 51821/udp..."
if command -v ufw &>/dev/null; then
    ufw allow 51821/udp comment "Dinstar VPN TLS" 2>/dev/null || true
    echo "  ✓ ufw"
else
    iptables -C INPUT -p udp --dport 51821 -j ACCEPT 2>/dev/null || {
        iptables -A INPUT -p udp --dport 51821 -j ACCEPT 2>/dev/null || true
    }
    echo "  ✓ iptables"
fi

echo ""
echo "✅ Dinstar OpenVPN TLS Server Deployed!"
echo "   VPN: 10.10.1.1 ↔ 10.10.1.2 on port 51821/udp (tun1)"
echo "   Client .ovpn: /opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn"
