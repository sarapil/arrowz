#!/bin/bash
# =============================================================================
# Arrowz Shared Network Setup
# =============================================================================
#
# Creates a shared Docker bridge network (arrowz_shared_net) and connects
# all Arrowz services to it, enabling direct container-to-container
# communication without going through Docker host port mapping.
#
# Run this script on the VPS HOST (not inside a container).
#
# Usage:
#   chmod +x setup_shared_network.sh
#   sudo ./setup_shared_network.sh
#
# What it does:
#   1. Creates arrowz_shared_net (172.30.0.0/16)
#   2. Connects existing containers to the shared network
#   3. Shows the resulting network topology
#
# After running:
#   - Containers can reach each other by name and IP
#   - Each container keeps its original network too (dual-homed)
#   - No ports need to be published between containers on this network
# =============================================================================

set -euo pipefail

# ---- Configuration ----
NETWORK_NAME="arrowz_shared_net"
NETWORK_SUBNET="172.30.0.0/16"  # Dedicated subnet for shared services

# Container names — auto-detected if not set via env var
FRAPPE_CONTAINER="${FRAPPE_CONTAINER:-}"
FREEPBX_CONTAINER="${FREEPBX_CONTAINER:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_err()   { echo -e "${RED}[ERROR]${NC} $*"; }

# ---- Auto-detect container names ----
if [ -z "$FRAPPE_CONTAINER" ]; then
    for pattern in "frappe-dev" "devcontainer-frappe-1" "development-devcontainer-frappe-1" "development_devcontainer-frappe-1" "development_devcontainer_frappe_1"; do
        if docker ps --format '{{.Names}}' | grep -q "^${pattern}$"; then FRAPPE_CONTAINER="$pattern"; break; fi
    done
    [ -z "$FRAPPE_CONTAINER" ] && FRAPPE_CONTAINER=$(docker ps --format '{{.Names}}\t{{.Image}}' | grep -i 'frappe/bench' | head -1 | awk '{print $1}')
    [ -z "$FRAPPE_CONTAINER" ] && FRAPPE_CONTAINER=$(docker ps -q | xargs -r docker inspect --format '{{.Name}} {{range .Mounts}}{{.Destination}} {{end}}' 2>/dev/null | grep '/workspace/development' | head -1 | awk '{print $1}' | sed 's|^/||')
fi

if [ -z "$FREEPBX_CONTAINER" ]; then
    for pattern in "initpbx-freepbx-1" "initpbx_freepbx_1" "freepbx" "asterisk"; do
        if docker ps --format '{{.Names}}' | grep -q "^${pattern}$"; then FREEPBX_CONTAINER="$pattern"; break; fi
    done
    [ -z "$FREEPBX_CONTAINER" ] && FREEPBX_CONTAINER=$(docker ps --format '{{.Names}}\t{{.Image}}' | grep -i 'freepbx\|sangoma' | head -1 | awk '{print $1}')
fi

log_info "Frappe container: ${FRAPPE_CONTAINER:-NOT FOUND}"
log_info "FreePBX container: ${FREEPBX_CONTAINER:-NOT FOUND}"

# ---- Step 1: Create the shared network ----
echo ""
echo "============================================="
echo "  Arrowz Shared Network Setup"
echo "============================================="
echo ""

if docker network inspect "$NETWORK_NAME" &>/dev/null; then
    log_warn "Network '$NETWORK_NAME' already exists"
    EXISTING_SUBNET=$(docker network inspect "$NETWORK_NAME" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
    log_info "Existing subnet: $EXISTING_SUBNET"
else
    log_info "Creating network '$NETWORK_NAME' with subnet $NETWORK_SUBNET..."
    docker network create \
        --driver bridge \
        --subnet "$NETWORK_SUBNET" \
        --opt com.docker.network.bridge.name=br-arrowz \
        "$NETWORK_NAME"
    log_ok "Network created: $NETWORK_NAME ($NETWORK_SUBNET)"
fi

echo ""

# ---- Step 2: Connect containers ----
connect_container() {
    local container="$1"
    local alias="${2:-}"
    
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        log_warn "Container '$container' is not running — skipping"
        return 1
    fi
    
    # Check if already connected
    if docker network inspect "$NETWORK_NAME" --format '{{range .Containers}}{{.Name}} {{end}}' | grep -q "$container"; then
        local ip=$(docker inspect "$container" --format "{{with index .NetworkSettings.Networks \"$NETWORK_NAME\"}}{{.IPAddress}}{{end}}")
        log_warn "'$container' already connected to $NETWORK_NAME (IP: $ip)"
        return 0
    fi
    
    if [ -n "$alias" ]; then
        docker network connect --alias "$alias" "$NETWORK_NAME" "$container"
    else
        docker network connect "$NETWORK_NAME" "$container"
    fi
    
    local ip=$(docker inspect "$container" --format "{{with index .NetworkSettings.Networks \"$NETWORK_NAME\"}}{{.IPAddress}}{{end}}")
    log_ok "Connected '$container' → $NETWORK_NAME (IP: $ip)"
}

log_info "Connecting containers to shared network..."
echo ""

# Connect Frappe dev container (with alias for DNS)
connect_container "$FRAPPE_CONTAINER" "frappe"

# Connect FreePBX container (with alias for DNS)
connect_container "$FREEPBX_CONTAINER" "freepbx"

echo ""

# ---- Step 3: Show network topology ----
log_info "Network topology for '$NETWORK_NAME':"
echo ""
printf "  %-30s %-18s %s\n" "CONTAINER" "IP" "ALIASES"
printf "  %-30s %-18s %s\n" "─────────" "──" "───────"

docker network inspect "$NETWORK_NAME" --format '{{range $id, $container := .Containers}}{{printf "  %-30s %-18s" $container.Name $container.IPv4Address}}{{range $container.Aliases}}{{printf "%s " .}}{{end}}{{println}}{{end}}'

echo ""

# ---- Step 4: Verify connectivity ----
log_info "Verifying connectivity..."

# Test from frappe → freepbx
if docker ps --format '{{.Names}}' | grep -q "^${FRAPPE_CONTAINER}$"; then
    FREEPBX_IP=$(docker inspect "$FREEPBX_CONTAINER" --format "{{with index .NetworkSettings.Networks \"$NETWORK_NAME\"}}{{.IPAddress}}{{end}}" 2>/dev/null || echo "")
    if [ -n "$FREEPBX_IP" ]; then
        if docker exec "$FRAPPE_CONTAINER" ping -c1 -W2 "$FREEPBX_IP" &>/dev/null; then
            log_ok "frappe-dev → freepbx ($FREEPBX_IP): REACHABLE ✅"
        else
            log_err "frappe-dev → freepbx ($FREEPBX_IP): UNREACHABLE ❌"
        fi
        
        # Test DNS resolution
        if docker exec "$FRAPPE_CONTAINER" getent hosts freepbx &>/dev/null; then
            RESOLVED=$(docker exec "$FRAPPE_CONTAINER" getent hosts freepbx | awk '{print $1}')
            log_ok "DNS 'freepbx' resolves to: $RESOLVED ✅"
        else
            log_warn "DNS 'freepbx' not resolving — container may need restart"
        fi
    fi
fi

echo ""
echo "============================================="
echo "  Setup Complete!"
echo "============================================="
echo ""
echo "Containers on $NETWORK_NAME can now reach each other directly."
echo ""
echo "From frappe-dev, you can now use:"
echo "  - freepbx:8088    (Asterisk HTTP)"
echo "  - freepbx:8089    (Asterisk WSS)"
echo "  - freepbx:5060    (SIP UDP)"
echo "  - freepbx:51600   (SIP transport)"
echo ""
echo "To add more containers later:"
echo "  docker network connect $NETWORK_NAME <container_name>"
echo ""
echo "To add OpenMeetings:"
echo "  docker-compose -f docker-compose.openmeetings.yml up -d"
echo ""
