#!/bin/bash
# =============================================================================
# Arrowz Infrastructure Master Setup
# =============================================================================
#
# One script to rule them all. Orchestrates the complete Arrowz service
# infrastructure: shared Docker network, FreePBX fixes, OpenMeetings.
#
# Run on VPS HOST as root/sudo.
#
# Usage:
#   chmod +x arrowz_infra_setup.sh
#   sudo ./arrowz_infra_setup.sh [command]
#
# Commands:
#   setup       Full setup (network + connect + fix PJSIP)
#   network     Create shared network only
#   connect     Connect existing containers to shared network
#   fix-pjsip   Fix PJSIP local_net only
#   om-up       Start OpenMeetings stack
#   om-down     Stop OpenMeetings stack
#   status      Show current network topology
#   help        Show this help
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---- Configuration ----
NETWORK_NAME="arrowz_shared_net"
NETWORK_SUBNET="172.30.0.0/16"

# Container name patterns (auto-detected below)
# Override with env vars if needed:
#   FRAPPE_CONTAINER=my-frappe FREEPBX_CONTAINER=my-pbx ./arrowz_infra_setup.sh setup
FRAPPE_CONTAINER="${FRAPPE_CONTAINER:-}"
FREEPBX_CONTAINER="${FREEPBX_CONTAINER:-}"

# Paths (adjust to your VPS layout)
FREEPBX_COMPOSE_DIR="/opt/proj/initpbx"
OM_COMPOSE_DIR="${SCRIPT_DIR}/openmeetings"

# ---- Docker Compose command detection ----
if docker compose version &>/dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &>/dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"  # fallback, will error if missing
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC}    $*"; }
log_ok()      { echo -e "${GREEN}[OK]${NC}      $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $*"; }
log_err()     { echo -e "${RED}[ERROR]${NC}   $*"; }
log_section() { echo -e "\n${CYAN}${BOLD}━━━ $* ━━━${NC}\n"; }

# ---- Auto-detect container names ----
auto_detect_containers() {
    if [ -z "$FRAPPE_CONTAINER" ]; then
        # Try common names: frappe-dev, devcontainer-frappe-1, *frappe*
        for pattern in "frappe-dev" "devcontainer-frappe-1" "development-devcontainer-frappe-1" "development_devcontainer-frappe-1" "development_devcontainer_frappe_1"; do
            if docker ps --format '{{.Names}}' | grep -q "^${pattern}$"; then
                FRAPPE_CONTAINER="$pattern"
                break
            fi
        done
        # Fallback: search by image
        if [ -z "$FRAPPE_CONTAINER" ]; then
            FRAPPE_CONTAINER=$(docker ps --format '{{.Names}}\t{{.Image}}' | grep -i 'frappe/bench\|frappe_docker' | head -1 | awk '{print $1}')
        fi
        # Last resort: search by volume mount
        if [ -z "$FRAPPE_CONTAINER" ]; then
            FRAPPE_CONTAINER=$(docker ps -q | xargs -r docker inspect --format '{{.Name}} {{range .Mounts}}{{.Destination}} {{end}}' 2>/dev/null | grep '/workspace/development' | head -1 | awk '{print $1}' | sed 's|^/||')
        fi
    fi
    
    if [ -z "$FREEPBX_CONTAINER" ]; then
        for pattern in "initpbx-freepbx-1" "initpbx_freepbx_1" "freepbx" "asterisk"; do
            if docker ps --format '{{.Names}}' | grep -q "^${pattern}$"; then
                FREEPBX_CONTAINER="$pattern"
                break
            fi
        done
        # Fallback: search by image
        if [ -z "$FREEPBX_CONTAINER" ]; then
            FREEPBX_CONTAINER=$(docker ps --format '{{.Names}}\t{{.Image}}' | grep -i 'freepbx\|sangoma\|tiredofit/freepbx' | head -1 | awk '{print $1}')
        fi
    fi
    
    [ -n "$FRAPPE_CONTAINER" ] && log_ok "Detected Frappe container: $FRAPPE_CONTAINER" || log_warn "Frappe container not found"
    [ -n "$FREEPBX_CONTAINER" ] && log_ok "Detected FreePBX container: $FREEPBX_CONTAINER" || log_warn "FreePBX container not found"
}

# ---- Functions ----

create_network() {
    log_section "Creating Shared Network"
    
    if docker network inspect "$NETWORK_NAME" &>/dev/null; then
        local subnet=$(docker network inspect "$NETWORK_NAME" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
        log_warn "Network '$NETWORK_NAME' already exists (subnet: $subnet)"
    else
        docker network create \
            --driver bridge \
            --subnet "$NETWORK_SUBNET" \
            --opt com.docker.network.bridge.name=br-arrowz \
            "$NETWORK_NAME"
        log_ok "Created network: $NETWORK_NAME ($NETWORK_SUBNET)"
    fi
}

connect_container() {
    local container="$1"
    local aliases="${2:-}"
    
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        log_warn "Container '$container' not running — skip"
        return 1
    fi
    
    if docker network inspect "$NETWORK_NAME" --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null | grep -q "$container"; then
        local ip=$(docker inspect "$container" --format "{{with index .NetworkSettings.Networks \"$NETWORK_NAME\"}}{{.IPAddress}}{{end}}")
        log_warn "'$container' already on $NETWORK_NAME (IP: $ip)"
        return 0
    fi
    
    local alias_args=""
    if [ -n "$aliases" ]; then
        for alias in $aliases; do
            alias_args+=" --alias $alias"
        done
    fi
    
    docker network connect $alias_args "$NETWORK_NAME" "$container"
    local ip=$(docker inspect "$container" --format "{{with index .NetworkSettings.Networks \"$NETWORK_NAME\"}}{{.IPAddress}}{{end}}")
    log_ok "Connected '$container' → $NETWORK_NAME (IP: $ip, aliases: ${aliases:-none})"
}

connect_all() {
    log_section "Connecting Containers"
    connect_container "$FRAPPE_CONTAINER" "frappe frappe-dev"
    connect_container "$FREEPBX_CONTAINER" "freepbx pbx asterisk"
}

fix_pjsip() {
    log_section "Fixing PJSIP local_net"
    
    if ! docker ps --format '{{.Names}}' | grep -q "^${FREEPBX_CONTAINER}$"; then
        log_err "FreePBX container not running!"
        return 1
    fi
    
    # Write custom transport config
    local custom_config="; Arrowz Custom PJSIP Transport Config
; Auto-generated by arrowz_infra_setup.sh — $(date)
; local_net=172.16.0.0/12 covers ALL Docker bridge subnets

[transport-wss]
type=transport
protocol=wss
bind=0.0.0.0:8089
cert_file=/etc/asterisk/keys/tavirapbx-fullchain.crt
priv_key_file=/etc/asterisk/keys/tavirapbx.key
method=tlsv1_2
external_media_address=pbx.tavira-group.com
external_signaling_address=pbx.tavira-group.com
local_net=172.16.0.0/12
local_net=10.0.0.0/8
local_net=192.168.0.0/16
local_net=157.173.125.136/32"
    
    echo "$custom_config" | docker exec -i "$FREEPBX_CONTAINER" tee /etc/asterisk/pjsip.transports_custom.conf > /dev/null
    log_ok "Wrote pjsip.transports_custom.conf"
    
    # Try updating via fwconsole
    docker exec "$FREEPBX_CONTAINER" fwconsole setting LOCALNETS '172.16.0.0/12,10.0.0.0/8,192.168.0.0/16,157.173.125.136/32' 2>/dev/null && \
        log_ok "Updated FreePBX LOCALNETS setting" || \
        log_warn "fwconsole LOCALNETS failed — update via GUI"
    
    # Reload
    docker exec "$FREEPBX_CONTAINER" asterisk -rx "module reload res_pjsip.so" 2>/dev/null
    log_ok "Reloaded PJSIP module"
    
    sleep 2
    log_info "Active transports:"
    docker exec "$FREEPBX_CONTAINER" asterisk -rx "pjsip show transports" 2>/dev/null | head -15
}

om_up() {
    log_section "Starting OpenMeetings"
    
    if [ ! -f "$OM_COMPOSE_DIR/docker-compose.yml" ]; then
        log_err "OpenMeetings compose not found at $OM_COMPOSE_DIR/docker-compose.yml"
        log_info "Copy docker/openmeetings/docker-compose.yml to $OM_COMPOSE_DIR first"
        return 1
    fi
    
    # Ensure network exists
    create_network
    
    cd "$OM_COMPOSE_DIR"
    $DOCKER_COMPOSE up -d
    
    log_ok "OpenMeetings starting..."
    log_info "Wait ~60s for initial setup, then access:"
    log_info "  https://dev.tavira-group.com/openmeetings"
}

om_down() {
    log_section "Stopping OpenMeetings"
    
    if [ ! -f "$OM_COMPOSE_DIR/docker-compose.yml" ]; then
        log_warn "OpenMeetings compose not found"
        return 1
    fi
    
    cd "$OM_COMPOSE_DIR"
    $DOCKER_COMPOSE down
    log_ok "OpenMeetings stopped"
}

show_status() {
    log_section "Network Topology: $NETWORK_NAME"
    
    if ! docker network inspect "$NETWORK_NAME" &>/dev/null; then
        log_warn "Network '$NETWORK_NAME' does not exist yet"
        log_info "Run: $0 setup"
        return 0
    fi
    
    local subnet=$(docker network inspect "$NETWORK_NAME" --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
    echo -e "  Network: ${BOLD}$NETWORK_NAME${NC}"
    echo -e "  Subnet:  ${BOLD}$subnet${NC}"
    echo -e "  Driver:  bridge"
    echo ""
    
    printf "  ${BOLD}%-30s %-20s %s${NC}\n" "CONTAINER" "IP" "ALIASES"
    printf "  %-30s %-20s %s\n" "─────────────────────────────" "───────────────────" "───────────────"
    
    docker network inspect "$NETWORK_NAME" --format '{{range $id, $container := .Containers}}{{printf "  %-30s %-20s" $container.Name $container.IPv4Address}}{{range $container.Aliases}}{{printf "%s " .}}{{end}}{{println}}{{end}}' 2>/dev/null
    
    echo ""
    
    # Quick connectivity check
    log_info "Connectivity matrix:"
    local containers=($(docker network inspect "$NETWORK_NAME" --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null))
    
    for src in "${containers[@]}"; do
        for dst in "${containers[@]}"; do
            if [ "$src" != "$dst" ]; then
                local dst_ip=$(docker inspect "$dst" --format "{{with index .NetworkSettings.Networks \"$NETWORK_NAME\"}}{{.IPAddress}}{{end}}" 2>/dev/null)
                if docker exec "$src" ping -c1 -W1 "$dst_ip" &>/dev/null; then
                    echo -e "  ${GREEN}✅${NC} $src → $dst ($dst_ip)"
                else
                    echo -e "  ${RED}❌${NC} $src → $dst ($dst_ip)"
                fi
            fi
        done
    done
    
    echo ""
    
    # Show all container networks for context
    log_info "All Arrowz-related containers and their networks:"
    for container in "$FRAPPE_CONTAINER" "$FREEPBX_CONTAINER" "arrowz-openmeetings"; do
        if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
            local networks=$(docker inspect "$container" --format '{{range $name, $net := .NetworkSettings.Networks}}{{printf "  %s (%s)\n" $name $net.IPAddress}}{{end}}' 2>/dev/null)
            echo -e "  ${BOLD}$container:${NC}"
            echo "$networks"
        fi
    done
}

show_help() {
    echo ""
    echo "Arrowz Infrastructure Setup"
    echo "==========================="
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup       Full setup: create network + connect containers + fix PJSIP"
    echo "  network     Create the shared Docker network only"
    echo "  connect     Connect existing containers to shared network"
    echo "  fix-pjsip   Fix FreePBX PJSIP local_net configuration"
    echo "  om-up       Start OpenMeetings stack"
    echo "  om-down     Stop OpenMeetings stack"
    echo "  status      Show current network topology and connectivity"
    echo "  help        Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 setup              # First-time full setup"
    echo "  $0 status             # Check what's connected"
    echo "  $0 connect            # Reconnect after container restart"
    echo "  $0 om-up              # Launch OpenMeetings"
    echo ""
    echo "Adding a new container to the shared network:"
    echo "  docker network connect --alias myservice $NETWORK_NAME <container>"
    echo ""
}

# ---- Main ----

COMMAND="${1:-help}"

# Auto-detect containers for commands that need them
case "$COMMAND" in
    setup|connect|fix-pjsip|status)
        auto_detect_containers
        ;;
esac

case "$COMMAND" in
    setup)
        create_network
        connect_all
        fix_pjsip
        show_status
        echo ""
        log_ok "Full setup complete! 🎉"
        echo ""
        ;;
    network)
        create_network
        ;;
    connect)
        connect_all
        ;;
    fix-pjsip)
        fix_pjsip
        ;;
    om-up)
        om_up
        ;;
    om-down)
        om_down
        ;;
    status)
        show_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_err "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
