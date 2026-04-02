#!/bin/bash
###############################################################################
# Deploy Dinstar OpenVPN TLS Server to FreePBX Container
# ======================================================
# Run this FROM the Frappe container. It will SSH to the VPS host
# and use docker exec to install everything in the FreePBX container.
#
# Usage:
#   bash deploy_dinstar_vpn.sh
#   (you will be prompted for VPS root password)
###############################################################################

set -euo pipefail

VPS_HOST="157.173.125.136"
VPS_PORT="1352"
VPS_USER="root"
CONTAINER="initpbx-freepbx-1"
GEN_DIR="/workspace/development/dinstar-setup/generated"
REMOTE_DIR="/etc/openvpn/dinstar-tls"

SSH_CMD="ssh -o StrictHostKeyChecking=no -p ${VPS_PORT} ${VPS_USER}@${VPS_HOST}"
SCP_CMD="scp -o StrictHostKeyChecking=no -P ${VPS_PORT}"

echo "═══════════════════════════════════════════════════════════"
echo "  Deploying Dinstar OpenVPN TLS to FreePBX Container"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  This will SSH to ${VPS_HOST}:${VPS_PORT}"
echo "  You will be prompted for the root password."
echo ""

# ── Verify local files ──
echo "[0] Verifying local files..."
for f in pki/ca.crt pki/ca.key pki/server.crt pki/server.key pki/dinstar.crt pki/dinstar.key pki/dh2048.pem pki/ta.key server.conf dinstar-tls.ovpn; do
    if [[ ! -s "${GEN_DIR}/${f}" ]]; then
        echo "  ❌ Missing: ${GEN_DIR}/${f}"
        exit 1
    fi
done
echo "  ✓ All files present"

# ── Step 1: Copy files to VPS host /tmp ──
echo ""
echo "[1] Copying files to VPS host..."

# Create a tarball of everything
TARBALL="/tmp/dinstar-vpn-deploy.tar.gz"
cd "${GEN_DIR}"
tar czf "${TARBALL}" pki/ server.conf dinstar-tls.ovpn
echo "  Tarball: $(wc -c < ${TARBALL}) bytes"

${SCP_CMD} "${TARBALL}" ${VPS_USER}@${VPS_HOST}:/tmp/dinstar-vpn-deploy.tar.gz
echo "  ✓ Files copied to VPS"

# ── Step 2: Deploy into FreePBX container ──
echo ""
echo "[2] Deploying into FreePBX container..."

${SSH_CMD} << 'REMOTE_SCRIPT'
set -e
CONTAINER="initpbx-freepbx-1"
REMOTE_DIR="/etc/openvpn/dinstar-tls"

echo "  [2a] Stopping existing dinstar VPN if running..."
docker exec "$CONTAINER" bash -c "pkill -f 'dinstar-tls' 2>/dev/null || true"
sleep 1

echo "  [2b] Cleaning old config..."
docker exec "$CONTAINER" bash -c "rm -rf ${REMOTE_DIR}"

echo "  [2c] Creating directory structure..."
docker exec "$CONTAINER" mkdir -p ${REMOTE_DIR}/pki

echo "  [2d] Copying tarball into container..."
docker cp /tmp/dinstar-vpn-deploy.tar.gz ${CONTAINER}:/tmp/dinstar-vpn-deploy.tar.gz

echo "  [2e] Extracting inside container..."
docker exec "$CONTAINER" bash -c "
    cd ${REMOTE_DIR}
    tar xzf /tmp/dinstar-vpn-deploy.tar.gz
    chmod 600 pki/*.key
    rm -f /tmp/dinstar-vpn-deploy.tar.gz
    echo '    Files deployed:'
    ls -la ${REMOTE_DIR}/
    ls -la ${REMOTE_DIR}/pki/
"

echo "  [2f] Starting OpenVPN TLS server..."
docker exec "$CONTAINER" bash -c "
    sysctl -w net.ipv4.ip_forward=1 >/dev/null 2>&1
    openvpn --config ${REMOTE_DIR}/server.conf --daemon openvpn-dinstar-tls
    sleep 3
"

echo "  [2g] Verifying..."
echo "    Process:"
docker exec "$CONTAINER" ps aux | grep "[o]penvpn.*dinstar-tls" || echo "      ❌ NOT RUNNING"

echo "    Port 51821:"
docker exec "$CONTAINER" ss -ulnp | grep "51821" || echo "      ❌ NOT listening"

echo "    tun1:"
docker exec "$CONTAINER" ip addr show tun1 2>/dev/null | grep inet || echo "      ⚠  tun1 not up yet (waiting for client)"

echo "    Log:"
docker exec "$CONTAINER" tail -5 /var/log/openvpn-dinstar-tls.log 2>/dev/null || echo "      No log"

echo "  [2h] Adding auto-start to rc.local..."
docker exec "$CONTAINER" bash -c "
    if [[ ! -f /etc/rc.local ]]; then
        echo '#!/bin/bash' > /etc/rc.local
        echo 'exit 0' >> /etc/rc.local
        chmod +x /etc/rc.local
    fi
    if ! grep -q 'dinstar-tls' /etc/rc.local 2>/dev/null; then
        sed -i '/^exit 0/i openvpn --config ${REMOTE_DIR}/server.conf --daemon openvpn-dinstar-tls' /etc/rc.local
        echo '    ✓ Added to rc.local'
    else
        echo '    ✓ Already in rc.local'
    fi
"

echo "  [2i] Saving .ovpn client file to VPS..."
docker exec "$CONTAINER" cat ${REMOTE_DIR}/dinstar-tls.ovpn > /opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn 2>/dev/null || {
    mkdir -p /opt/proj/initpbx/vpn-clients
    docker exec "$CONTAINER" cat ${REMOTE_DIR}/dinstar-tls.ovpn > /opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn
}
echo "    ✓ Saved to /opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn"

echo "  [2j] Opening port 51821/udp on host firewall..."
if command -v ufw &>/dev/null; then
    ufw allow 51821/udp comment "Dinstar VPN TLS" 2>/dev/null || true
    echo "    ✓ ufw rule added"
else
    iptables -C INPUT -p udp --dport 51821 -j ACCEPT 2>/dev/null || {
        iptables -A INPUT -p udp --dport 51821 -j ACCEPT 2>/dev/null || true
    }
    echo "    ✓ iptables rule added"
fi

echo ""
echo "  ✅ Deployment complete!"
REMOTE_SCRIPT

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✅ Dinstar OpenVPN TLS Server Deployed!"
echo ""
echo "  VPN:  10.10.1.1 ↔ 10.10.1.2  port 51821/udp  tun1"
echo "  Auth: TLS (certificates + tls-auth HMAC)"
echo ""
echo "  Client .ovpn file (for Dinstar):"
echo "    Local:  ${GEN_DIR}/dinstar-tls.ovpn"
echo "    VPS:    /opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn"
echo ""
echo "  Next steps:"
echo "    1. Upload dinstar-tls.ovpn to Dinstar web UI"
echo "    2. Run: bash /workspace/development/dinstar-setup/deploy_dinstar_trunk.sh"
echo "    3. Configure Dinstar SIP → 10.10.1.1:51600"
echo "═══════════════════════════════════════════════════════════"
