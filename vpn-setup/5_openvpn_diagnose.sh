#!/bin/bash
###############################################################################
# OpenVPN Server-Side Diagnostic — Run on VPS HOST
###############################################################################

CONTAINER="initpbx-freepbx-1"
PEER="admin"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}═══ OpenVPN Server Diagnostic ═══${NC}"
echo ""

echo -e "${YELLOW}[1] OpenVPN process:${NC}"
docker exec "$CONTAINER" ps aux | grep openvpn | grep -v grep
echo ""

echo -e "${YELLOW}[2] tun interfaces inside container:${NC}"
docker exec "$CONTAINER" ip addr show | grep -A3 "tun"
echo ""

echo -e "${YELLOW}[3] OpenVPN log (last 20 lines):${NC}"
docker exec "$CONTAINER" bash -c 'cat /var/log/openvpn-*.log 2>/dev/null | tail -20 || echo "No log found"'
echo ""

echo -e "${YELLOW}[4] Server config:${NC}"
docker exec "$CONTAINER" bash -c 'cat /etc/openvpn/server-*.conf 2>/dev/null || echo "No server config found"'
echo ""

echo -e "${YELLOW}[5] IP forwarding:${NC}"
docker exec "$CONTAINER" sysctl net.ipv4.ip_forward
echo ""

echo -e "${YELLOW}[6] iptables INPUT chain (tun):${NC}"
docker exec "$CONTAINER" iptables -L INPUT -n -v 2>/dev/null | grep -i "tun\|10.10" | head -5
echo ""

echo -e "${YELLOW}[7] iptables FORWARD chain (tun):${NC}"
docker exec "$CONTAINER" iptables -L FORWARD -n -v 2>/dev/null | grep -i "tun\|10.10" | head -5
echo ""

echo -e "${YELLOW}[8] Can container ping client through tunnel?${NC}"
docker exec "$CONTAINER" ping -c 2 -W 2 10.10.0.2 2>&1
echo ""

echo -e "${YELLOW}[9] Route table inside container:${NC}"
docker exec "$CONTAINER" ip route | grep -i "10.10"
echo ""

echo -e "${YELLOW}[10] Listening on UDP 51820:${NC}"
docker exec "$CONTAINER" ss -ulnp | grep 51820 || echo "  Nothing listening on 51820"
echo ""

echo -e "${YELLOW}[11] WireGuard still running? (conflict):${NC}"
docker exec "$CONTAINER" bash -c 'ip link show wg0 2>/dev/null && echo "WARNING: WireGuard wg0 still UP!" || echo "  No WireGuard (good)"'
echo ""

echo -e "${CYAN}═══ Quick Fix Attempts ═══${NC}"
echo ""

# If no tun interface, try to start openvpn
TUN_EXISTS=$(docker exec "$CONTAINER" ip link show tun-admin 2>/dev/null && echo "yes" || echo "no")
if [[ "$TUN_EXISTS" == "no" ]]; then
    echo -e "${YELLOW}  tun-admin not found. Attempting to start OpenVPN...${NC}"
    
    # Kill any existing
    docker exec "$CONTAINER" pkill -f "openvpn.*server-admin" 2>/dev/null || true
    sleep 1
    
    # Check if config exists
    CONF_EXISTS=$(docker exec "$CONTAINER" test -f /etc/openvpn/server-admin.conf && echo "yes" || echo "no")
    if [[ "$CONF_EXISTS" == "yes" ]]; then
        echo "  Starting: openvpn --config /etc/openvpn/server-admin.conf"
        docker exec -d "$CONTAINER" openvpn --config /etc/openvpn/server-admin.conf
        sleep 3
        
        # Check again
        docker exec "$CONTAINER" ip addr show tun-admin 2>/dev/null && echo -e "${GREEN}  [✓] tun-admin is UP now!${NC}" || echo -e "${RED}  [✗] Still no tun-admin${NC}"
        
        # Show log
        echo ""
        echo "  Log after start attempt:"
        docker exec "$CONTAINER" tail -10 /var/log/openvpn-admin.log 2>/dev/null
    else
        echo -e "${RED}  No server config found! Need to run 4_setup_openvpn_static.sh first${NC}"
    fi
else
    echo -e "${GREEN}  tun-admin exists — checking if ping works now...${NC}"
    
    # Make sure iptables allows it
    docker exec "$CONTAINER" iptables -C INPUT -i tun-admin -j ACCEPT 2>/dev/null || \
        docker exec "$CONTAINER" iptables -I INPUT 1 -i tun-admin -j ACCEPT
    docker exec "$CONTAINER" iptables -C FORWARD -i tun-admin -j ACCEPT 2>/dev/null || \
        docker exec "$CONTAINER" iptables -I FORWARD 1 -i tun-admin -j ACCEPT
    docker exec "$CONTAINER" iptables -C FORWARD -o tun-admin -j ACCEPT 2>/dev/null || \
        docker exec "$CONTAINER" iptables -I FORWARD 1 -o tun-admin -j ACCEPT
    
    echo "  iptables rules ensured for tun-admin"
    
    # Try ping
    docker exec "$CONTAINER" ping -c 2 -W 2 10.10.0.2 2>&1
fi
