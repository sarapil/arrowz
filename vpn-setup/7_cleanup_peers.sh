#!/bin/bash
###############################################################################
# Cleanup old OpenVPN peers — Run on VPS HOST
# Removes admin and sarapil configs, keys, and logs
###############################################################################

set -euo pipefail

CONTAINER="initpbx-freepbx-1"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${YELLOW}Cleaning up old OpenVPN peers: admin, sarapil${NC}"
echo ""

# Kill all OpenVPN first
echo "  Stopping all OpenVPN..."
docker exec "$CONTAINER" pkill -f openvpn 2>/dev/null || true
sleep 1

# Remove peer directories and configs
for PEER in admin sarapil; do
    echo ""
    echo -e "${YELLOW}── Removing: ${PEER} ──${NC}"

    # Server config
    docker exec "$CONTAINER" rm -f "/etc/openvpn/server-${PEER}.conf" && \
        echo "  Deleted: server-${PEER}.conf" || true

    # Peer directory (keys, .ovpn, static.key)
    docker exec "$CONTAINER" rm -rf "/etc/openvpn/peers/${PEER}" && \
        echo "  Deleted: peers/${PEER}/" || true

    # Logs
    docker exec "$CONTAINER" rm -f "/var/log/openvpn-${PEER}.log" \
                                    "/var/log/openvpn-${PEER}-status.log" && \
        echo "  Deleted: logs" || true

    # Systemd service
    docker exec "$CONTAINER" bash -c "
        systemctl disable openvpn-${PEER} 2>/dev/null || true
        rm -f /etc/systemd/system/openvpn-${PEER}.service
    " 2>/dev/null && echo "  Deleted: systemd service" || true

    # PID file
    docker exec "$CONTAINER" rm -f "/var/run/openvpn-${PEER}.pid" 2>/dev/null || true

    # Host-side client files
    rm -f "/opt/proj/initpbx/vpn-clients/${PEER}.ovpn" \
          "/opt/proj/initpbx/vpn-clients/${PEER}-nm.ovpn" \
          "/opt/proj/initpbx/vpn-clients/${PEER}-nm2.ovpn" \
          "/opt/proj/initpbx/vpn-clients/${PEER}-static.key" 2>/dev/null && \
        echo "  Deleted: host client files" || true

    echo -e "${GREEN}  [✓] ${PEER} removed${NC}"
done

# Show what's left
echo ""
echo -e "${YELLOW}── Remaining ──${NC}"
echo "  Server configs:"
docker exec "$CONTAINER" ls -la /etc/openvpn/server-*.conf 2>/dev/null || echo "    (none)"
echo "  Peer directories:"
docker exec "$CONTAINER" ls -la /etc/openvpn/peers/ 2>/dev/null || echo "    (none)"
echo "  Client files on host:"
ls -la /opt/proj/initpbx/vpn-clients/ 2>/dev/null || echo "    (none)"
echo ""

echo -e "${GREEN}Done! Only 'arkan' remains.${NC}"
echo ""
echo "To restart arkan's OpenVPN:"
echo "  docker exec -d $CONTAINER openvpn --config /etc/openvpn/server-arkan.conf"
echo ""
