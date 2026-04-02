#!/bin/bash
###############################################################################
# WireGuard VPN Server Setup for Arrowz PBX
# VPS: 157.173.125.136 (Ubuntu 24.04)
# Purpose: VPN-only access to FreePBX/Asterisk
#
# Architecture:
#   VPN Server: 10.10.0.1/24 on wg0 (port 51820/UDP)
#   PBX Container: 172.21.0.2 (Docker network initpbx_default)
#   Frappe Container: 172.26.0.3 (Docker network frappe_dev_shared)
#
# Usage: ssh -p 1352 root@157.173.125.136 'bash -s' < setup_wireguard.sh
#   OR:  scp this to VPS and run: bash setup_wireguard.sh
###############################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

###############################################################################
# Configuration
###############################################################################
VPN_SUBNET="10.10.0.0/24"
VPN_SERVER_IP="10.10.0.1"
VPN_PORT="51820"
VPN_INTERFACE="wg0"
PUBLIC_IP="157.173.125.136"

# Docker networks to route to
PBX_NETWORK="172.21.0.0/16"     # initpbx_default
FRAPPE_NETWORK="172.26.0.0/16"  # frappe_dev_shared

# PBX Container IP
PBX_IP="172.21.0.2"

# Main network interface (auto-detect)
MAIN_IFACE=$(ip route | grep default | awk '{print $5}' | head -1)

# Keys directory
WG_DIR="/etc/wireguard"
KEYS_DIR="${WG_DIR}/keys"
PEERS_DIR="${WG_DIR}/peers"

###############################################################################
# Step 0: Add SSH key for dev container (if not already there)
###############################################################################
step_ssh_key() {
    info "Step 0: Checking SSH authorized keys..."
    
    DEV_KEY="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCwqvp75j+qht4P8UP2ZcaZ4wxjpQRynM8I9N0o0/uNtX4asxhAHBM4dIYcRtTAzZoyqepv1QSSVusZNTzJRde5Q3WKqSJzgJv6zaJQ230ABVRv3SIvhPQ6bAKnyn3l6q1XrzjjrM7gppBBHBtKGjMnqKGFk45YoutCdOev4JdViAoWjsNfnw3eoctvS81SWQwgiddPHTkutIbLcttzQ/LMth/cc+jTWRyVuYMbNzNYl2cOUw5CJEIfh+3I6/f6e8oXoLkzCeTubRPK2pEu/WgW0FNBzqxJq/RxanxmCCAIkaTXCfkNTpsnxpEgbHPBWUSQrFAnwRBUnzvpFoyMhHZSNc/DjCGK1lE/w9wHOWt5DYAzBKCJYEh5yzoPOOfISH040J0kj2wRR8BYciN60x7Q5AhVW7E+AfEwxVZhI8oi8gR9BC28NWGBYW13w7TfB+3MEeAFwhh876SfPH+VJcP102eSIz3CGLu+776TqCVlACfa0kCLjsgP6d1wm/lMIGREFbNkq9eYLQHO+tAHGwQepLGKLYrCD5HNuBVZWRfAuCnGiZHi27lEsZxL2gHLghdy6BTP+ThXpnzHLd/gvNwHZNEY6+tSSw1ESId0B3vGQFI4FBGHscDs1OKUujoRct1dK3yn6f9bbHo7FjVKTcz26dj01ag3OACMKhb4eFpHkw== arrowz@frappe"
    
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    
    if grep -q "arrowz@frappe" ~/.ssh/authorized_keys 2>/dev/null; then
        log "SSH key already authorized"
    else
        echo "$DEV_KEY" >> ~/.ssh/authorized_keys
        chmod 600 ~/.ssh/authorized_keys
        log "SSH key added to authorized_keys"
    fi
}

###############################################################################
# Step 1: Install WireGuard
###############################################################################
step_install() {
    info "Step 1: Installing WireGuard..."
    
    if command -v wg &>/dev/null; then
        log "WireGuard already installed: $(wg --version 2>&1 || echo 'unknown version')"
        return 0
    fi
    
    apt-get update -qq
    apt-get install -y -qq wireguard wireguard-tools qrencode
    
    # Load kernel module
    modprobe wireguard 2>/dev/null || true
    
    # Verify
    if command -v wg &>/dev/null; then
        log "WireGuard installed successfully"
    else
        error "WireGuard installation failed!"
        exit 1
    fi
}

###############################################################################
# Step 2: Generate Server Keys
###############################################################################
step_keys() {
    info "Step 2: Generating server keys..."
    
    mkdir -p "$KEYS_DIR" "$PEERS_DIR"
    chmod 700 "$WG_DIR" "$KEYS_DIR" "$PEERS_DIR"
    
    if [[ -f "${KEYS_DIR}/server_private.key" ]]; then
        warn "Server keys already exist, skipping generation"
        log "Server Public Key: $(cat ${KEYS_DIR}/server_public.key)"
        return 0
    fi
    
    # Generate server keypair
    wg genkey | tee "${KEYS_DIR}/server_private.key" | wg pubkey > "${KEYS_DIR}/server_public.key"
    chmod 600 "${KEYS_DIR}/server_private.key"
    
    log "Server keys generated"
    log "Server Public Key: $(cat ${KEYS_DIR}/server_public.key)"
}

###############################################################################
# Step 3: Configure WireGuard Server
###############################################################################
step_configure() {
    info "Step 3: Configuring WireGuard server..."
    
    local SERVER_PRIVATE_KEY
    SERVER_PRIVATE_KEY=$(cat "${KEYS_DIR}/server_private.key")
    
    info "Detected main interface: ${MAIN_IFACE}"
    
    cat > "${WG_DIR}/${VPN_INTERFACE}.conf" << WGEOF
# ============================================================================
# WireGuard VPN Server - Arrowz PBX Access
# Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
# ============================================================================

[Interface]
Address = ${VPN_SERVER_IP}/24
ListenPort = ${VPN_PORT}
PrivateKey = ${SERVER_PRIVATE_KEY}

# --- NAT & Forwarding Rules ---
# Enable IP forwarding + masquerade for VPN clients accessing Docker networks
PostUp = sysctl -w net.ipv4.ip_forward=1
PostUp = iptables -t nat -A POSTROUTING -s ${VPN_SUBNET} -o ${MAIN_IFACE} -j MASQUERADE
PostUp = iptables -A FORWARD -i ${VPN_INTERFACE} -j ACCEPT
PostUp = iptables -A FORWARD -o ${VPN_INTERFACE} -j ACCEPT

# Route to Docker PBX network
PostUp = iptables -t nat -A POSTROUTING -s ${VPN_SUBNET} -d ${PBX_NETWORK} -j MASQUERADE
PostUp = iptables -t nat -A POSTROUTING -s ${VPN_SUBNET} -d ${FRAPPE_NETWORK} -j MASQUERADE

PostDown = iptables -t nat -D POSTROUTING -s ${VPN_SUBNET} -o ${MAIN_IFACE} -j MASQUERADE
PostDown = iptables -D FORWARD -i ${VPN_INTERFACE} -j ACCEPT
PostDown = iptables -D FORWARD -o ${VPN_INTERFACE} -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -s ${VPN_SUBNET} -d ${PBX_NETWORK} -j MASQUERADE
PostDown = iptables -t nat -D POSTROUTING -s ${VPN_SUBNET} -d ${FRAPPE_NETWORK} -j MASQUERADE

# === Peers will be added below by add_peer.sh ===

WGEOF

    chmod 600 "${WG_DIR}/${VPN_INTERFACE}.conf"
    log "WireGuard config created at ${WG_DIR}/${VPN_INTERFACE}.conf"
}

###############################################################################
# Step 4: Enable IP Forwarding (persistent)
###############################################################################
step_forwarding() {
    info "Step 4: Enabling IP forwarding..."
    
    # Make persistent
    if grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf; then
        log "IP forwarding already enabled in sysctl.conf"
    else
        echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
        log "Added ip_forward to sysctl.conf"
    fi
    
    sysctl -w net.ipv4.ip_forward=1 >/dev/null
    log "IP forwarding enabled"
}

###############################################################################
# Step 5: Configure Firewall
###############################################################################
step_firewall() {
    info "Step 5: Configuring firewall..."
    
    # Check if ufw is active
    if command -v ufw &>/dev/null && ufw status | grep -q "active"; then
        info "UFW is active, adding rules..."
        
        # Allow WireGuard port
        ufw allow ${VPN_PORT}/udp comment "WireGuard VPN"
        
        # Allow forwarding in UFW
        if ! grep -q "DEFAULT_FORWARD_POLICY=\"ACCEPT\"" /etc/default/ufw; then
            sed -i 's/DEFAULT_FORWARD_POLICY="DROP"/DEFAULT_FORWARD_POLICY="ACCEPT"/' /etc/default/ufw
            warn "Changed UFW forward policy to ACCEPT - will take effect on ufw reload"
        fi
        
        # Add NAT rules to UFW before.rules if not already there
        if ! grep -q "POSTROUTING.*${VPN_SUBNET}" /etc/ufw/before.rules; then
            # Insert NAT rules before the *filter section
            sed -i "1i\\
# NAT for WireGuard VPN\\
*nat\\
:POSTROUTING ACCEPT [0:0]\\
-A POSTROUTING -s ${VPN_SUBNET} -o ${MAIN_IFACE} -j MASQUERADE\\
COMMIT\\
" /etc/ufw/before.rules
            warn "Added NAT rules to /etc/ufw/before.rules"
        fi
        
        ufw reload
        log "UFW configured"
    else
        info "UFW not active, using iptables directly..."
        
        # Allow WireGuard port via iptables
        iptables -C INPUT -p udp --dport ${VPN_PORT} -j ACCEPT 2>/dev/null || \
            iptables -A INPUT -p udp --dport ${VPN_PORT} -j ACCEPT
        
        log "iptables rule added for port ${VPN_PORT}/UDP"
        
        # Save iptables rules (if iptables-persistent installed)
        if command -v netfilter-persistent &>/dev/null; then
            netfilter-persistent save
            log "iptables rules saved"
        else
            warn "Consider installing iptables-persistent: apt install iptables-persistent"
        fi
    fi
}

###############################################################################
# Step 6: Start WireGuard
###############################################################################
step_start() {
    info "Step 6: Starting WireGuard..."
    
    # Stop if already running
    wg-quick down ${VPN_INTERFACE} 2>/dev/null || true
    
    # Start
    wg-quick up ${VPN_INTERFACE}
    
    # Enable on boot
    systemctl enable wg-quick@${VPN_INTERFACE}
    
    # Verify
    echo ""
    info "WireGuard Status:"
    wg show ${VPN_INTERFACE}
    echo ""
    
    ip addr show ${VPN_INTERFACE}
    
    log "WireGuard is running!"
}

###############################################################################
# Step 7: Create Peer Management Script
###############################################################################
step_create_peer_script() {
    info "Step 7: Creating peer management tools..."
    
    # === ADD PEER SCRIPT ===
    cat > "${WG_DIR}/add_peer.sh" << 'ADDEOF'
#!/bin/bash
###############################################################################
# Add a new WireGuard VPN Peer
# Usage: /etc/wireguard/add_peer.sh <peer_name> [ip_suffix]
# Example: /etc/wireguard/add_peer.sh ahmed 10  -> 10.10.0.10
###############################################################################
set -euo pipefail

WG_DIR="/etc/wireguard"
KEYS_DIR="${WG_DIR}/keys"
PEERS_DIR="${WG_DIR}/peers"
VPN_INTERFACE="wg0"
VPN_SERVER_IP="10.10.0.1"
VPN_PORT="51820"
PUBLIC_IP="157.173.125.136"
DNS_SERVERS="1.1.1.1, 8.8.8.8"

# Docker networks the peer can access
ALLOWED_IPS_SERVER_SIDE=""  # Will be set to peer IP

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <peer_name> [ip_suffix]"
    echo "Example: $0 ahmed 10   -> assigns 10.10.0.10"
    echo ""
    echo "Existing peers:"
    ls -1 "${PEERS_DIR}/" 2>/dev/null | sed 's/.conf$//' || echo "  (none)"
    exit 1
fi

PEER_NAME="$1"

# Auto-assign IP or use provided suffix
if [[ $# -ge 2 ]]; then
    IP_SUFFIX="$2"
else
    # Find next available IP (start from .2)
    USED_IPS=$(grep -r "AllowedIPs" "${WG_DIR}/${VPN_INTERFACE}.conf" 2>/dev/null | grep -oP '10\.10\.0\.\K[0-9]+' | sort -n)
    IP_SUFFIX=2
    while echo "$USED_IPS" | grep -q "^${IP_SUFFIX}$"; do
        ((IP_SUFFIX++))
    done
fi

PEER_IP="10.10.0.${IP_SUFFIX}"
PEER_DIR="${PEERS_DIR}/${PEER_NAME}"

if [[ -d "$PEER_DIR" ]]; then
    echo "Error: Peer '${PEER_NAME}' already exists at ${PEER_DIR}"
    exit 1
fi

echo "Creating peer: ${PEER_NAME} (${PEER_IP})"

# Create peer directory
mkdir -p "$PEER_DIR"

# Generate peer keys
wg genkey | tee "${PEER_DIR}/private.key" | wg pubkey > "${PEER_DIR}/public.key"
wg genpsk > "${PEER_DIR}/preshared.key"
chmod 600 "${PEER_DIR}/private.key" "${PEER_DIR}/preshared.key"

PEER_PRIVATE=$(cat "${PEER_DIR}/private.key")
PEER_PUBLIC=$(cat "${PEER_DIR}/public.key")
PEER_PSK=$(cat "${PEER_DIR}/preshared.key")
SERVER_PUBLIC=$(cat "${KEYS_DIR}/server_public.key")

# Create client config
cat > "${PEER_DIR}/${PEER_NAME}.conf" << CONFEOF
# ============================================
# WireGuard Client Config - ${PEER_NAME}
# IP: ${PEER_IP}
# Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
# ============================================

[Interface]
PrivateKey = ${PEER_PRIVATE}
Address = ${PEER_IP}/32
DNS = ${DNS_SERVERS}

[Peer]
PublicKey = ${SERVER_PUBLIC}
PresharedKey = ${PEER_PSK}
Endpoint = ${PUBLIC_IP}:${VPN_PORT}
# Route VPN subnet + Docker PBX + Frappe networks through VPN
AllowedIPs = 10.10.0.0/24, 172.21.0.0/16, 172.26.0.0/16
PersistentKeepalive = 25
CONFEOF

# Add peer to server config
cat >> "${WG_DIR}/${VPN_INTERFACE}.conf" << SRVEOF

# --- Peer: ${PEER_NAME} (${PEER_IP}) ---
[Peer]
PublicKey = ${PEER_PUBLIC}
PresharedKey = ${PEER_PSK}
AllowedIPs = ${PEER_IP}/32
SRVEOF

# Add peer to running interface (hot-add, no restart needed)
wg set ${VPN_INTERFACE} peer "${PEER_PUBLIC}" \
    preshared-key "${PEER_DIR}/preshared.key" \
    allowed-ips "${PEER_IP}/32"

# Save peer info
echo "${PEER_IP}" > "${PEER_DIR}/ip.txt"
echo "${PEER_NAME}" > "${PEER_DIR}/name.txt"
date -u '+%Y-%m-%d %H:%M:%S UTC' > "${PEER_DIR}/created.txt"

echo ""
echo "✅ Peer '${PEER_NAME}' created successfully!"
echo "   IP Address:  ${PEER_IP}"
echo "   Config file: ${PEER_DIR}/${PEER_NAME}.conf"
echo ""
echo "📋 Client config:"
echo "─────────────────────────────────────────"
cat "${PEER_DIR}/${PEER_NAME}.conf"
echo "─────────────────────────────────────────"

# Generate QR code if qrencode is available
if command -v qrencode &>/dev/null; then
    echo ""
    echo "📱 QR Code (scan with WireGuard mobile app):"
    qrencode -t ansiutf8 < "${PEER_DIR}/${PEER_NAME}.conf"
    
    # Also save QR as PNG
    qrencode -t png -o "${PEER_DIR}/${PEER_NAME}_qr.png" < "${PEER_DIR}/${PEER_NAME}.conf"
    echo ""
    echo "QR PNG saved: ${PEER_DIR}/${PEER_NAME}_qr.png"
fi

echo ""
echo "🔗 Connection test (after client connects):"
echo "   ping ${PEER_IP}"
echo ""
echo "📡 PBX access via VPN:"
echo "   SIP:  ${PEER_IP} -> 172.21.0.2:5060"
echo "   WSS:  ${PEER_IP} -> 172.21.0.2:8089"
ADDEOF

    chmod +x "${WG_DIR}/add_peer.sh"
    log "add_peer.sh created"

    # === REMOVE PEER SCRIPT ===
    cat > "${WG_DIR}/remove_peer.sh" << 'RMEOF'
#!/bin/bash
###############################################################################
# Remove a WireGuard VPN Peer
# Usage: /etc/wireguard/remove_peer.sh <peer_name>
###############################################################################
set -euo pipefail

WG_DIR="/etc/wireguard"
PEERS_DIR="${WG_DIR}/peers"
VPN_INTERFACE="wg0"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <peer_name>"
    echo ""
    echo "Existing peers:"
    ls -1 "${PEERS_DIR}/" 2>/dev/null || echo "  (none)"
    exit 1
fi

PEER_NAME="$1"
PEER_DIR="${PEERS_DIR}/${PEER_NAME}"

if [[ ! -d "$PEER_DIR" ]]; then
    echo "Error: Peer '${PEER_NAME}' not found"
    exit 1
fi

PEER_PUBLIC=$(cat "${PEER_DIR}/public.key")

# Remove from running interface
wg set ${VPN_INTERFACE} peer "${PEER_PUBLIC}" remove

# Remove from config file (remove the peer block)
# This removes from "# --- Peer: name" to the next "# --- Peer:" or end
python3 -c "
import re
with open('${WG_DIR}/${VPN_INTERFACE}.conf', 'r') as f:
    content = f.read()
# Remove the peer block for this specific peer
pattern = r'\n# --- Peer: ${PEER_NAME} \(.*?\) ---\n\[Peer\]\n.*?(?=\n# --- Peer:|\n*$)'
content = re.sub(pattern, '', content, flags=re.DOTALL)
with open('${WG_DIR}/${VPN_INTERFACE}.conf', 'w') as f:
    f.write(content)
"

# Archive peer directory
mv "$PEER_DIR" "${PEER_DIR}.removed.$(date +%Y%m%d)"

echo "✅ Peer '${PEER_NAME}' removed"
echo "   Archived to: ${PEER_DIR}.removed.$(date +%Y%m%d)"
RMEOF

    chmod +x "${WG_DIR}/remove_peer.sh"
    log "remove_peer.sh created"

    # === LIST PEERS SCRIPT ===
    cat > "${WG_DIR}/list_peers.sh" << 'LSEOF'
#!/bin/bash
###############################################################################
# List all WireGuard VPN Peers
###############################################################################
WG_DIR="/etc/wireguard"
PEERS_DIR="${WG_DIR}/peers"
VPN_INTERFACE="wg0"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              WireGuard VPN Peers - Arrowz PBX               ║"
echo "╠══════════════════════════════════════════════════════════════╣"

if [[ ! -d "$PEERS_DIR" ]] || [[ -z "$(ls -A $PEERS_DIR 2>/dev/null)" ]]; then
    echo "║  No peers configured                                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    exit 0
fi

printf "║ %-15s %-15s %-12s %-15s ║\n" "Name" "IP" "Status" "Last Handshake"
echo "╠══════════════════════════════════════════════════════════════╣"

for peer_dir in "${PEERS_DIR}"/*/; do
    [[ -d "$peer_dir" ]] || continue
    name=$(basename "$peer_dir")
    [[ "$name" == *".removed"* ]] && continue
    
    ip=$(cat "${peer_dir}/ip.txt" 2>/dev/null || echo "unknown")
    pubkey=$(cat "${peer_dir}/public.key" 2>/dev/null || echo "")
    
    # Get status from wg show
    if [[ -n "$pubkey" ]]; then
        handshake=$(wg show ${VPN_INTERFACE} latest-handshakes 2>/dev/null | grep "$pubkey" | awk '{print $2}')
        if [[ -n "$handshake" && "$handshake" != "0" ]]; then
            status="🟢 Online"
            hs_time=$(date -d @"$handshake" '+%H:%M:%S' 2>/dev/null || echo "$handshake")
        else
            status="🔴 Offline"
            hs_time="never"
        fi
    else
        status="⚪ Unknown"
        hs_time="n/a"
    fi
    
    printf "║ %-15s %-15s %-12s %-15s ║\n" "$name" "$ip" "$status" "$hs_time"
done

echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Server Status:"
wg show ${VPN_INTERFACE} 2>/dev/null | head -5
LSEOF

    chmod +x "${WG_DIR}/list_peers.sh"
    log "list_peers.sh created"
}

###############################################################################
# Step 8: Create First Test Peer (admin)
###############################################################################
step_first_peer() {
    info "Step 8: Creating first peer (admin)..."
    
    if [[ -d "${PEERS_DIR}/admin" ]]; then
        warn "Admin peer already exists"
        return 0
    fi
    
    "${WG_DIR}/add_peer.sh" admin 2
}

###############################################################################
# Step 9: Docker Network Verification & Route Setup
###############################################################################
step_docker_routes() {
    info "Step 9: Verifying Docker network routing..."
    
    # Check Docker networks
    echo ""
    info "Docker networks:"
    docker network ls --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}" 2>/dev/null || warn "Cannot list Docker networks"
    
    echo ""
    
    # Get PBX network info
    PBX_NET_INFO=$(docker network inspect initpbx_default 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data:
    net = data[0]
    subnet = net.get('IPAM', {}).get('Config', [{}])[0].get('Subnet', 'unknown')
    gw = net.get('IPAM', {}).get('Config', [{}])[0].get('Gateway', 'unknown')
    print(f'Subnet: {subnet}, Gateway: {gw}')
" 2>/dev/null || echo "Could not inspect PBX network")
    
    info "PBX Network: $PBX_NET_INFO"
    
    # Get Frappe network info
    FRAPPE_NET_INFO=$(docker network inspect frappe_dev_shared 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data:
    net = data[0]
    subnet = net.get('IPAM', {}).get('Config', [{}])[0].get('Subnet', 'unknown')
    gw = net.get('IPAM', {}).get('Config', [{}])[0].get('Gateway', 'unknown')
    print(f'Subnet: {subnet}, Gateway: {gw}')
" 2>/dev/null || echo "Could not inspect Frappe network")
    
    info "Frappe Network: $FRAPPE_NET_INFO"
    
    # Verify PBX container is reachable
    echo ""
    if ping -c 1 -W 2 172.21.0.2 &>/dev/null; then
        log "PBX container (172.21.0.2) is reachable from host"
    else
        warn "PBX container (172.21.0.2) not directly reachable - checking Docker bridge..."
        # The host should be able to reach Docker containers via their bridge IP
        docker exec initpbx-freepbx-1 echo "PBX container alive" 2>/dev/null && log "PBX container is running" || warn "PBX container may not be running"
    fi
    
    # IP routes check
    echo ""
    info "Current routes involving Docker networks:"
    ip route | grep -E "172\.(21|26)" || warn "No Docker network routes found (normal if using Docker default bridge)"
    
    log "Docker routing verified"
}

###############################################################################
# Step 10: Final Summary
###############################################################################
step_summary() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║          🔒 WireGuard VPN Server - Setup Complete          ║"
    echo "╠══════════════════════════════════════════════════════════════╣"
    echo "║                                                            ║"
    printf "║  Server IP:    %-43s ║\n" "${PUBLIC_IP}:${VPN_PORT}/UDP"
    printf "║  VPN IP:       %-43s ║\n" "${VPN_SERVER_IP}/24"
    printf "║  Interface:    %-43s ║\n" "${VPN_INTERFACE}"
    echo "║                                                            ║"
    echo "║  PBX via VPN:                                              ║"
    printf "║    SIP:        %-43s ║\n" "172.21.0.2:5060 (UDP)"
    printf "║    SIP-TLS:    %-43s ║\n" "172.21.0.2:5061 (TCP)"
    printf "║    WSS:        %-43s ║\n" "172.21.0.2:8089 (TCP)"
    printf "║    RTP:        %-43s ║\n" "172.21.0.2:10000-20000 (UDP)"
    printf "║    AMI:        %-43s ║\n" "172.21.0.2:5038 (TCP)"
    echo "║                                                            ║"
    echo "║  Management:                                               ║"
    echo "║    Add peer:    /etc/wireguard/add_peer.sh <name> [ip]     ║"
    echo "║    Remove peer: /etc/wireguard/remove_peer.sh <name>       ║"
    echo "║    List peers:  /etc/wireguard/list_peers.sh               ║"
    echo "║    Show status: wg show                                    ║"
    echo "║                                                            ║"
    echo "║  Config files:                                             ║"
    echo "║    Server:  /etc/wireguard/wg0.conf                        ║"
    echo "║    Peers:   /etc/wireguard/peers/<name>/<name>.conf        ║"
    echo "║    Keys:    /etc/wireguard/keys/                           ║"
    echo "║                                                            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Show the admin peer config for immediate testing
    if [[ -f "${PEERS_DIR}/admin/admin.conf" ]]; then
        echo "═══════════════════════════════════════════════════════════════"
        echo "  📋 Admin Client Config (copy to WireGuard client):"
        echo "═══════════════════════════════════════════════════════════════"
        cat "${PEERS_DIR}/admin/admin.conf"
        echo "═══════════════════════════════════════════════════════════════"
    fi
}

###############################################################################
# Main
###############################################################################
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║     🔒 WireGuard VPN Setup for Arrowz PBX                  ║"
    echo "║     VPS: ${PUBLIC_IP}                              ║"
    echo "║     VPN: ${VPN_SERVER_IP}/24 on port ${VPN_PORT}/UDP                  ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    step_ssh_key
    step_install
    step_keys
    step_configure
    step_forwarding
    step_firewall
    step_start
    step_create_peer_script
    step_first_peer
    step_docker_routes
    step_summary
    
    echo ""
    log "Setup complete! 🎉"
    echo ""
}

main "$@"
