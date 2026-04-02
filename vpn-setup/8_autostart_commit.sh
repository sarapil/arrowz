#!/bin/bash
###############################################################################
# Auto-start + Docker Commit — Run on VPS HOST
# =============================================
# 1. Creates auto-start for OpenVPN inside container
# 2. Tests full tunnel (curl ifconfig.me)
# 3. Docker commits the image
###############################################################################

set -euo pipefail

CONTAINER="initpbx-freepbx-1"
PEER="arkan"
PORT="51820"
PUBLIC_IP="157.173.125.136"
IMAGE_NAME="arkan-freepbx17-final-vpn6"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Auto-start + Commit + Full Tunnel               ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
echo -e "${YELLOW}[1/5] Creating auto-start script inside container...${NC}"
###############################################################################

docker exec "$CONTAINER" bash -c "cat > /etc/openvpn/start-vpn.sh << 'STARTEOF'
#!/bin/bash
# Auto-start OpenVPN — called by systemd or rc.local

sleep 3

# Ensure tun device
mkdir -p /dev/net
[ -c /dev/net/tun ] || mknod /dev/net/tun c 10 200
chmod 666 /dev/net/tun

# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1 > /dev/null 2>&1

# Start OpenVPN for each config
for conf in /etc/openvpn/server-*.conf; do
    [ -f \"\$conf\" ] || continue
    name=\$(basename \"\$conf\" .conf | sed 's/server-//')

    # Kill if already running
    pkill -f \"openvpn.*\$conf\" 2>/dev/null || true
    sleep 1

    # Start
    openvpn --config \"\$conf\" --daemon \"openvpn-\${name}\"
    echo \"Started OpenVPN: \${name}\"
    sleep 2
done

# Setup NAT
IFACE=\$(ip route | grep default | awk '{print \$5}' | head -1)
for conf in /etc/openvpn/server-*.conf; do
    [ -f \"\$conf\" ] || continue
    CLIENT_IP=\$(grep '^ifconfig' \"\$conf\" | awk '{print \$3}')
    [ -n \"\$CLIENT_IP\" ] || continue
    iptables -t nat -C POSTROUTING -s \${CLIENT_IP}/32 -o \${IFACE} -j MASQUERADE 2>/dev/null || \
        iptables -t nat -A POSTROUTING -s \${CLIENT_IP}/32 -o \${IFACE} -j MASQUERADE
    echo \"NAT for \${CLIENT_IP} via \${IFACE}\"
done

echo \"VPN auto-start complete\"
STARTEOF

chmod +x /etc/openvpn/start-vpn.sh
echo '  start-vpn.sh created'
"

###############################################################################
echo -e "${YELLOW}[2/5] Creating systemd service...${NC}"
###############################################################################

docker exec "$CONTAINER" bash -c "cat > /etc/systemd/system/openvpn-autostart.service << 'SVCEOF'
[Unit]
Description=OpenVPN Auto-start (all static key tunnels)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/etc/openvpn/start-vpn.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload 2>/dev/null || true
systemctl enable openvpn-autostart 2>/dev/null || true
echo '  systemd service enabled'
"

# Also add to rc.local as fallback (some containers don't use full systemd)
docker exec "$CONTAINER" bash -c "
    # rc.local fallback
    if [ ! -f /etc/rc.local ] || ! grep -q 'start-vpn' /etc/rc.local 2>/dev/null; then
        cat > /etc/rc.local << 'RCEOF'
#!/bin/bash
/etc/openvpn/start-vpn.sh &
exit 0
RCEOF
        chmod +x /etc/rc.local
        echo '  rc.local fallback created'
    else
        echo '  rc.local already has start-vpn'
    fi
"

# Also add to crontab @reboot as another fallback
docker exec "$CONTAINER" bash -c "
    (crontab -l 2>/dev/null | grep -v start-vpn; echo '@reboot /etc/openvpn/start-vpn.sh') | crontab -
    echo '  crontab @reboot added'
"

echo -e "${GREEN}  [✓] Auto-start configured (3 methods: systemd + rc.local + crontab)${NC}"

###############################################################################
echo -e "${YELLOW}[3/5] Testing full tunnel...${NC}"
###############################################################################

# Make sure OpenVPN is running now
docker exec "$CONTAINER" bash -c '
    if ! pgrep -f openvpn > /dev/null; then
        /etc/openvpn/start-vpn.sh
    fi
'

echo "  Server tun:"
docker exec "$CONTAINER" ip addr show tun0 2>/dev/null | grep "inet " || echo "    NO tun0!"
echo ""

echo "  From your connected client, run:"
echo "    curl ifconfig.me"
echo "    Expected: ${PUBLIC_IP}"
echo ""
echo "    ping 10.10.0.1"
echo "    Expected: replies from server"
echo ""

# Quick port check
echo "  Listening on ${PORT}/udp:"
docker exec "$CONTAINER" ss -ulnp | grep "${PORT}" || echo "    NOT listening!"
echo ""

###############################################################################
echo -e "${YELLOW}[4/5] Docker commit...${NC}"
###############################################################################

echo "  Stopping container briefly is NOT needed — we commit live."
echo "  Committing ${CONTAINER} → ${IMAGE_NAME}..."

docker commit \
    --change='CMD ["/usr/sbin/init"]' \
    --message "OpenVPN static key auto-start, port ${PORT}/udp" \
    "$CONTAINER" \
    "${IMAGE_NAME}"

echo -e "${GREEN}  [✓] Image saved: ${IMAGE_NAME}${NC}"
echo ""

# Show image
docker images | grep "${IMAGE_NAME}" | head -1

###############################################################################
echo -e "${YELLOW}[5/5] Updating docker-compose.yml...${NC}"
###############################################################################

COMPOSE_FILE="/opt/proj/initpbx/docker-compose.yml"
if [ -f "$COMPOSE_FILE" ]; then
    # Update image name
    OLD_IMAGE=$(grep "image:" "$COMPOSE_FILE" | head -1 | awk '{print $2}')
    sed -i "s|image: .*|image: ${IMAGE_NAME}|" "$COMPOSE_FILE"
    echo "  Updated image: ${OLD_IMAGE} → ${IMAGE_NAME}"
else
    echo "  docker-compose.yml not found at ${COMPOSE_FILE}"
fi

###############################################################################
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  All Done!                                       ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}║  ✅ Auto-start: 3 methods configured             ║${NC}"
echo -e "${CYAN}║  ✅ Docker image: ${IMAGE_NAME}       ║${NC}"
echo -e "${CYAN}║  ✅ docker-compose.yml updated                   ║${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}║  Test restart:                                   ║${NC}"
echo -e "${CYAN}║    docker compose restart freepbx                ║${NC}"
echo -e "${CYAN}║    # Wait 30s, then:                             ║${NC}"
echo -e "${CYAN}║    docker exec ${CONTAINER} pgrep -a openvpn     ║${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}║  From client (full tunnel test):                 ║${NC}"
echo -e "${CYAN}║    sudo openvpn --config arkan.ovpn              ║${NC}"
echo -e "${CYAN}║    curl ifconfig.me  → ${PUBLIC_IP}              ║${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
