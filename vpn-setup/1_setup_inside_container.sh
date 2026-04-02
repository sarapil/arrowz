#!/bin/bash
###############################################################################
# WireGuard Setup - RUNS INSIDE FreePBX Container
# ================================================
#
# HOW TO USE:
#   1. From VPS host, copy this script into the container:
#      docker cp 1_setup_inside_container.sh initpbx-freepbx-1:/tmp/
#
#   2. Enter the container:
#      docker exec -it initpbx-freepbx-1 bash
#
#   3. Run:
#      bash /tmp/1_setup_inside_container.sh
#
#   4. Exit container, then run script #2 on the HOST to commit the image
#
# WHAT IT DOES:
#   - Installs wireguard-tools, qrencode, iptables-persistent
#   - Creates /etc/wireguard/ directory structure
#   - Generates server keypair
#   - Creates wg0.conf
#   - Creates peer management scripts (add/remove/list)
#   - Creates first admin peer
#   - Enables wg-quick@wg0 service (systemd)
#
# NOTE: On kernel 5.6+ WireGuard is built into the kernel — no module mount needed.
#       Container needs: --cap-add=NET_ADMIN
#                        --sysctl net.ipv4.ip_forward=1
###############################################################################

set -euo pipefail

# ─── Colors ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

# ─── Configuration ───────────────────────────────────────────────────
VPN_SUBNET="10.10.0.0/24"
VPN_SERVER_IP="10.10.0.1"
VPN_PORT="51820"
VPN_INTERFACE="wg0"
PUBLIC_IP="157.173.125.136"
DNS_SERVERS="1.1.1.1, 8.8.8.8"

WG_DIR="/etc/wireguard"
KEYS_DIR="${WG_DIR}/keys"
PEERS_DIR="${WG_DIR}/peers"

###############################################################################
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  🔒 WireGuard VPN Setup - Inside FreePBX Container         ║${NC}"
echo -e "${CYAN}║  Server: ${VPN_SERVER_IP}/24 on port ${VPN_PORT}/UDP                    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Step 1: Install packages
###############################################################################
info "Step 1: Installing WireGuard tools + utilities..."

apt-get update -qq

# wireguard-tools = wg, wg-quick (userspace only - kernel module on host)
# qrencode = QR codes for mobile clients
# iptables-persistent = save firewall rules across restarts
apt-get install -y -qq wireguard-tools qrencode iptables

if command -v wg &>/dev/null; then
    log "wireguard-tools installed"
else
    err "Failed to install wireguard-tools"
    exit 1
fi

if command -v qrencode &>/dev/null; then
    log "qrencode installed"
fi

# Clean apt cache to keep image small
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/apt-*

###############################################################################
# Step 2: Create directory structure
###############################################################################
info "Step 2: Creating directory structure..."

mkdir -p "${KEYS_DIR}" "${PEERS_DIR}"
chmod 700 "${WG_DIR}" "${KEYS_DIR}" "${PEERS_DIR}"

log "Directories created: ${WG_DIR}/{keys,peers}"

###############################################################################
# Step 3: Generate server keypair
###############################################################################
info "Step 3: Generating server keys..."

if [[ -f "${KEYS_DIR}/server_private.key" ]]; then
    warn "Server keys already exist — keeping existing keys"
else
    wg genkey | tee "${KEYS_DIR}/server_private.key" | wg pubkey > "${KEYS_DIR}/server_public.key"
    chmod 600 "${KEYS_DIR}/server_private.key"
    log "Server keypair generated"
fi

SERVER_PRIVATE_KEY=$(cat "${KEYS_DIR}/server_private.key")
SERVER_PUBLIC_KEY=$(cat "${KEYS_DIR}/server_public.key")
info "Server Public Key: ${SERVER_PUBLIC_KEY}"

###############################################################################
# Step 4: Create wg0.conf
###############################################################################
info "Step 4: Creating WireGuard config..."

# Detect container's main interface (eth0 usually in Docker)
MAIN_IFACE=$(ip route | grep default | awk '{print $5}' | head -1)
info "Detected interface: ${MAIN_IFACE}"

cat > "${WG_DIR}/${VPN_INTERFACE}.conf" << WGEOF
# ============================================================================
# WireGuard VPN Server — Arrowz PBX (inside FreePBX container)
# Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
# ============================================================================

[Interface]
Address = ${VPN_SERVER_IP}/24
ListenPort = ${VPN_PORT}
PrivateKey = ${SERVER_PRIVATE_KEY}

# IP forwarding (also set via Docker --sysctl)
PostUp = sysctl -w net.ipv4.ip_forward=1

# Allow VPN clients to reach the PBX services on this container
# (No NAT needed — PBX is on the same machine!)
PostUp = iptables -A INPUT -i ${VPN_INTERFACE} -j ACCEPT
PostUp = iptables -A FORWARD -i ${VPN_INTERFACE} -j ACCEPT
PostUp = iptables -A FORWARD -o ${VPN_INTERFACE} -j ACCEPT

PostDown = iptables -D INPUT -i ${VPN_INTERFACE} -j ACCEPT
PostDown = iptables -D FORWARD -i ${VPN_INTERFACE} -j ACCEPT
PostDown = iptables -D FORWARD -o ${VPN_INTERFACE} -j ACCEPT

# === Peers (managed by /etc/wireguard/add_peer.sh) ===

WGEOF

chmod 600 "${WG_DIR}/${VPN_INTERFACE}.conf"
log "Config created: ${WG_DIR}/${VPN_INTERFACE}.conf"

###############################################################################
# Step 5: Create peer management scripts
###############################################################################
info "Step 5: Creating peer management tools..."

# ╔════════════════════════════════════╗
# ║  add_peer.sh                       ║
# ╚════════════════════════════════════╝
cat > "${WG_DIR}/add_peer.sh" << 'ADDEOF'
#!/bin/bash
set -euo pipefail

WG_DIR="/etc/wireguard"
KEYS_DIR="${WG_DIR}/keys"
PEERS_DIR="${WG_DIR}/peers"
VPN_INTERFACE="wg0"
VPN_PORT="51820"
PUBLIC_IP="157.173.125.136"
DNS_SERVERS="1.1.1.1, 8.8.8.8"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <peer_name> [ip_suffix]"
    echo ""
    echo "  peer_name : A unique name (e.g. ahmed, phone_ahmed, laptop_omar)"
    echo "  ip_suffix : Last octet of 10.10.0.X (auto-assigned if omitted)"
    echo ""
    echo "Examples:"
    echo "  $0 ahmed          → auto-assign next IP"
    echo "  $0 ahmed_phone 10 → assign 10.10.0.10"
    echo ""
    echo "Existing peers:"
    for d in "${PEERS_DIR}"/*/; do
        [[ -d "$d" ]] || continue
        name=$(basename "$d")
        [[ "$name" == *".removed"* ]] && continue
        ip=$(cat "${d}/ip.txt" 2>/dev/null || echo "?")
        echo "  ${name}  →  ${ip}"
    done
    exit 1
fi

PEER_NAME="$1"

# ── Auto-assign or use provided IP suffix ──
if [[ $# -ge 2 ]]; then
    IP_SUFFIX="$2"
else
    USED=$(grep -oP '10\.10\.0\.\K[0-9]+' "${WG_DIR}/${VPN_INTERFACE}.conf" 2>/dev/null | sort -n -u)
    IP_SUFFIX=2
    while echo "$USED" | grep -qw "$IP_SUFFIX"; do ((IP_SUFFIX++)); done
fi

PEER_IP="10.10.0.${IP_SUFFIX}"
PEER_DIR="${PEERS_DIR}/${PEER_NAME}"

if [[ -d "$PEER_DIR" ]]; then
    echo "❌ Peer '${PEER_NAME}' already exists!"
    exit 1
fi

echo "🔧 Creating peer: ${PEER_NAME} (${PEER_IP})"
mkdir -p "$PEER_DIR"

# ── Generate keys ──
wg genkey | tee "${PEER_DIR}/private.key" | wg pubkey > "${PEER_DIR}/public.key"
wg genpsk > "${PEER_DIR}/preshared.key"
chmod 600 "${PEER_DIR}/private.key" "${PEER_DIR}/preshared.key"

PEER_PRIVATE=$(cat "${PEER_DIR}/private.key")
PEER_PUBLIC=$(cat "${PEER_DIR}/public.key")
PEER_PSK=$(cat "${PEER_DIR}/preshared.key")
SERVER_PUBLIC=$(cat "${KEYS_DIR}/server_public.key")

# ── Client config ──
cat > "${PEER_DIR}/${PEER_NAME}.conf" << CONFEOF
# ─────────────────────────────────────
# WireGuard Client — ${PEER_NAME}
# IP: ${PEER_IP}
# Created: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
# ─────────────────────────────────────

[Interface]
PrivateKey = ${PEER_PRIVATE}
Address = ${PEER_IP}/32
DNS = ${DNS_SERVERS}

[Peer]
PublicKey = ${SERVER_PUBLIC}
PresharedKey = ${PEER_PSK}
Endpoint = ${PUBLIC_IP}:${VPN_PORT}
AllowedIPs = 10.10.0.0/24
PersistentKeepalive = 25
CONFEOF

# ── Add peer to server config ──
cat >> "${WG_DIR}/${VPN_INTERFACE}.conf" << SRVEOF

# ─── Peer: ${PEER_NAME} (${PEER_IP}) ───
[Peer]
PublicKey = ${PEER_PUBLIC}
PresharedKey = ${PEER_PSK}
AllowedIPs = ${PEER_IP}/32
SRVEOF

# ── Hot-add to running interface ──
if ip link show ${VPN_INTERFACE} &>/dev/null; then
    wg set ${VPN_INTERFACE} peer "${PEER_PUBLIC}" \
        preshared-key "${PEER_DIR}/preshared.key" \
        allowed-ips "${PEER_IP}/32"
    echo "  ↳ Added to running interface (no restart needed)"
fi

# ── Save metadata ──
echo "${PEER_IP}" > "${PEER_DIR}/ip.txt"
echo "${PEER_NAME}" > "${PEER_DIR}/name.txt"
date -u '+%Y-%m-%d %H:%M:%S UTC' > "${PEER_DIR}/created.txt"

echo ""
echo "✅ Peer '${PEER_NAME}' created!"
echo ""
echo "📋 Client config (${PEER_DIR}/${PEER_NAME}.conf):"
echo "───────────────────────────────────────────"
cat "${PEER_DIR}/${PEER_NAME}.conf"
echo "───────────────────────────────────────────"

# ── QR Code ──
if command -v qrencode &>/dev/null; then
    echo ""
    echo "📱 QR Code:"
    qrencode -t ansiutf8 < "${PEER_DIR}/${PEER_NAME}.conf"
    qrencode -t png -o "${PEER_DIR}/${PEER_NAME}_qr.png" < "${PEER_DIR}/${PEER_NAME}.conf"
    echo "  PNG saved: ${PEER_DIR}/${PEER_NAME}_qr.png"
fi
ADDEOF
chmod +x "${WG_DIR}/add_peer.sh"

# ╔════════════════════════════════════╗
# ║  remove_peer.sh                    ║
# ╚════════════════════════════════════╝
cat > "${WG_DIR}/remove_peer.sh" << 'RMEOF'
#!/bin/bash
set -euo pipefail

WG_DIR="/etc/wireguard"
PEERS_DIR="${WG_DIR}/peers"
VPN_INTERFACE="wg0"

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <peer_name>"
    echo ""
    echo "Active peers:"
    for d in "${PEERS_DIR}"/*/; do
        [[ -d "$d" ]] || continue
        name=$(basename "$d")
        [[ "$name" == *".removed"* ]] && continue
        ip=$(cat "${d}/ip.txt" 2>/dev/null || echo "?")
        echo "  ${name}  →  ${ip}"
    done
    exit 1
fi

PEER_NAME="$1"
PEER_DIR="${PEERS_DIR}/${PEER_NAME}"

if [[ ! -d "$PEER_DIR" ]]; then
    echo "❌ Peer '${PEER_NAME}' not found"
    exit 1
fi

PEER_PUBLIC=$(cat "${PEER_DIR}/public.key")

# Remove from running interface
if ip link show ${VPN_INTERFACE} &>/dev/null; then
    wg set ${VPN_INTERFACE} peer "${PEER_PUBLIC}" remove
    echo "  ↳ Removed from running interface"
fi

# Remove from config file
python3 -c "
import re
with open('${WG_DIR}/${VPN_INTERFACE}.conf', 'r') as f:
    content = f.read()
pattern = r'\n# ─── Peer: ${PEER_NAME} \(.*?\) ───\n\[Peer\]\n.*?(?=\n# ─── Peer:|\Z)'
content = re.sub(pattern, '', content, flags=re.DOTALL)
with open('${WG_DIR}/${VPN_INTERFACE}.conf', 'w') as f:
    f.write(content.rstrip() + '\n')
"

# Archive
ARCHIVE="${PEER_DIR}.removed.$(date +%Y%m%d_%H%M%S)"
mv "$PEER_DIR" "$ARCHIVE"

echo "✅ Peer '${PEER_NAME}' removed"
echo "   Archived: ${ARCHIVE}"
RMEOF
chmod +x "${WG_DIR}/remove_peer.sh"

# ╔════════════════════════════════════╗
# ║  list_peers.sh                     ║
# ╚════════════════════════════════════╝
cat > "${WG_DIR}/list_peers.sh" << 'LSEOF'
#!/bin/bash
WG_DIR="/etc/wireguard"
PEERS_DIR="${WG_DIR}/peers"
VPN_INTERFACE="wg0"

echo ""
echo "┌──────────────────┬──────────────────┬──────────┬──────────────────┐"
printf "│ %-16s │ %-16s │ %-8s │ %-16s │\n" "Name" "IP" "Status" "Last Handshake"
echo "├──────────────────┼──────────────────┼──────────┼──────────────────┤"

count=0
for d in "${PEERS_DIR}"/*/; do
    [[ -d "$d" ]] || continue
    name=$(basename "$d")
    [[ "$name" == *".removed"* ]] && continue
    
    ip=$(cat "${d}/ip.txt" 2>/dev/null || echo "?")
    pubkey=$(cat "${d}/public.key" 2>/dev/null || echo "")
    
    status="🔴 Off"
    hs="never"
    if [[ -n "$pubkey" ]] && ip link show ${VPN_INTERFACE} &>/dev/null; then
        ts=$(wg show ${VPN_INTERFACE} latest-handshakes 2>/dev/null | grep "$pubkey" | awk '{print $2}')
        if [[ -n "$ts" && "$ts" != "0" ]]; then
            age=$(( $(date +%s) - ts ))
            if [[ $age -lt 180 ]]; then
                status="🟢 On "
            else
                status="🟡 Idle"
            fi
            hs=$(date -d @"$ts" '+%m-%d %H:%M' 2>/dev/null || echo "$ts")
        fi
    fi
    
    printf "│ %-16s │ %-16s │ %-8s │ %-16s │\n" "$name" "$ip" "$status" "$hs"
    ((count++))
done

echo "└──────────────────┴──────────────────┴──────────┴──────────────────┘"
echo "  Total peers: ${count}"
echo ""

if ip link show ${VPN_INTERFACE} &>/dev/null; then
    echo "Server status:"
    wg show ${VPN_INTERFACE} | head -6
fi
LSEOF
chmod +x "${WG_DIR}/list_peers.sh"

log "Peer scripts created: add_peer.sh, remove_peer.sh, list_peers.sh"

###############################################################################
# Step 6: Enable wg-quick@wg0 service
###############################################################################
info "Step 6: Enabling WireGuard systemd service..."

# Enable (will start on next boot / systemd reload)
systemctl enable wg-quick@${VPN_INTERFACE} 2>/dev/null || warn "Could not enable service (will try on start)"

log "wg-quick@${VPN_INTERFACE} enabled"

###############################################################################
# Step 7: Try to start WireGuard now (may fail if caps missing)
###############################################################################
info "Step 7: Attempting to start WireGuard..."

if wg-quick up ${VPN_INTERFACE} 2>&1; then
    log "WireGuard is UP!"
    echo ""
    wg show ${VPN_INTERFACE}
    echo ""
    ip addr show ${VPN_INTERFACE}
else
    warn "Could not start WireGuard now."
    warn "This is expected if the container lacks NET_ADMIN capability."
    warn "It will start after docker commit + restart with proper caps."
fi

###############################################################################
# Step 8: Create first admin peer
###############################################################################
info "Step 8: Creating admin peer..."

if [[ -d "${PEERS_DIR}/admin" ]]; then
    warn "Admin peer already exists"
else
    "${WG_DIR}/add_peer.sh" admin 2
fi

###############################################################################
# Summary
###############################################################################
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  ✅ WireGuard Setup Complete (Inside Container)             ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  Installed:                                                ║${NC}"
echo -e "${CYAN}║    • wireguard-tools (wg, wg-quick)                       ║${NC}"
echo -e "${CYAN}║    • qrencode (QR codes for mobile)                       ║${NC}"
echo -e "${CYAN}║    • iptables                                             ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  Created:                                                  ║${NC}"
echo -e "${CYAN}║    • /etc/wireguard/wg0.conf         (server config)      ║${NC}"
echo -e "${CYAN}║    • /etc/wireguard/keys/             (server keypair)     ║${NC}"
echo -e "${CYAN}║    • /etc/wireguard/peers/admin/      (first peer)        ║${NC}"
echo -e "${CYAN}║    • /etc/wireguard/add_peer.sh       (add new peer)      ║${NC}"
echo -e "${CYAN}║    • /etc/wireguard/remove_peer.sh    (remove peer)       ║${NC}"
echo -e "${CYAN}║    • /etc/wireguard/list_peers.sh     (list all peers)    ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  ⚡ NEXT STEP: Exit container, then run script #2         ║${NC}"
echo -e "${CYAN}║     on the HOST to commit the image.                       ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Show directories that should be volumes
echo -e "${YELLOW}📁 Directories to persist as Docker volumes:${NC}"
echo "  /etc/wireguard/       — VPN config, keys, peers"
echo "  /etc/asterisk/        — Asterisk/FreePBX config"
echo "  /var/spool/asterisk/  — Voicemail, recordings"
echo "  /var/log/asterisk/    — Asterisk logs"
echo "  /var/lib/asterisk/    — Asterisk data (sounds, moh, etc)"
echo "  /var/lib/mysql/       — MariaDB data (if DB is local)"
echo "  /tftpboot/            — Phone provisioning"
echo ""
