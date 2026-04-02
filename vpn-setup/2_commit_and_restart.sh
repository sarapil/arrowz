#!/bin/bash
###############################################################################
# Commit FreePBX Container → New Image + Restart with Volumes
# ============================================================
#
# RUNS ON: VPS HOST (not inside container!)
#
# HOW TO USE:
#   1. First run script #1 inside the container
#   2. Then run this script on the HOST:
#      bash 2_commit_and_restart.sh
#
# WHAT IT DOES:
#   1. Stops the running container
#   2. docker commit → new image (arkan/freepbx-vpn:latest)
#   3. Creates persistent volume directories on host
#   4. Generates updated docker-compose.override.yml
#   5. Restarts with proper volumes + capabilities
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
# Auto-detect container name & compose project
CONTAINER_NAME="${FREEPBX_CONTAINER:-initpbx-freepbx-1}"
NEW_IMAGE="arkan/freepbx-vpn:latest"
COMPOSE_DIR="${COMPOSE_DIR:-/opt/proj/initpbx}"   # Where docker-compose.yml lives
DATA_ROOT="${DATA_ROOT:-/opt/data/freepbx}"        # Persistent storage root

# VPN port
VPN_PORT="51820"

###############################################################################
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  📦 Commit & Restart FreePBX with VPN Support              ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  Container:  ${CONTAINER_NAME}                        ║${NC}"
echo -e "${CYAN}║  New Image:  ${NEW_IMAGE}                     ║${NC}"
echo -e "${CYAN}║  Data Root:  ${DATA_ROOT}                     ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# Pre-flight checks
###############################################################################
info "Checking container status..."

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    # Check if it exists but stopped
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        warn "Container exists but is stopped"
    else
        err "Container '${CONTAINER_NAME}' not found!"
        echo ""
        echo "Available containers:"
        docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}'
        echo ""
        echo "Set FREEPBX_CONTAINER=<name> if using a different container name"
        exit 1
    fi
fi

# Get current image info
CURRENT_IMAGE=$(docker inspect --format '{{.Config.Image}}' "${CONTAINER_NAME}" 2>/dev/null || echo "unknown")
info "Current image: ${CURRENT_IMAGE}"

###############################################################################
# Step 1: Copy persistent data BEFORE stopping
###############################################################################
info "Step 1: Creating persistent data directories..."

mkdir -p "${DATA_ROOT}"/{wireguard,asterisk-config,asterisk-spool,asterisk-log,asterisk-lib,mysql,tftpboot}

# Copy current data from container to host (first time only)
copy_if_empty() {
    local host_dir="$1"
    local container_path="$2"
    local desc="$3"
    
    if [[ -z "$(ls -A "${host_dir}" 2>/dev/null)" ]]; then
        info "  Copying ${desc} from container → ${host_dir}"
        docker cp "${CONTAINER_NAME}:${container_path}/." "${host_dir}/" 2>/dev/null || warn "  Could not copy ${container_path}"
    else
        warn "  ${host_dir} already has data — skipping copy (${desc})"
    fi
}

copy_if_empty "${DATA_ROOT}/wireguard"      "/etc/wireguard"       "WireGuard config"
copy_if_empty "${DATA_ROOT}/asterisk-config" "/etc/asterisk"        "Asterisk config"
copy_if_empty "${DATA_ROOT}/asterisk-spool"  "/var/spool/asterisk"  "Asterisk spool"
copy_if_empty "${DATA_ROOT}/asterisk-log"    "/var/log/asterisk"    "Asterisk logs"
copy_if_empty "${DATA_ROOT}/asterisk-lib"    "/var/lib/asterisk"    "Asterisk data"
copy_if_empty "${DATA_ROOT}/tftpboot"        "/tftpboot"            "TFTP boot"

# MySQL — only if DB is inside this container
if docker exec "${CONTAINER_NAME}" test -d /var/lib/mysql 2>/dev/null; then
    copy_if_empty "${DATA_ROOT}/mysql" "/var/lib/mysql" "MariaDB data"
fi

log "Persistent directories ready at ${DATA_ROOT}/"

###############################################################################
# Step 2: Commit container as new image
###############################################################################
info "Step 2: Committing container to new image..."

# Commit with metadata
docker commit \
    --change 'LABEL maintainer="arkan-labs"' \
    --change 'LABEL description="FreePBX 17 + WireGuard VPN"' \
    --change "LABEL build-date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "${CONTAINER_NAME}" "${NEW_IMAGE}"

# Verify
NEW_IMAGE_ID=$(docker images --format '{{.ID}}' "${NEW_IMAGE}")
NEW_IMAGE_SIZE=$(docker images --format '{{.Size}}' "${NEW_IMAGE}")
log "Image committed: ${NEW_IMAGE} (${NEW_IMAGE_ID}, ${NEW_IMAGE_SIZE})"

###############################################################################
# Step 3: Generate docker-compose.override.yml
###############################################################################
info "Step 3: Generating docker-compose override..."

OVERRIDE_FILE="${COMPOSE_DIR}/docker-compose.override.yml"

# Backup existing override if any
if [[ -f "${OVERRIDE_FILE}" ]]; then
    cp "${OVERRIDE_FILE}" "${OVERRIDE_FILE}.bak.$(date +%Y%m%d_%H%M%S)"
    warn "Backed up existing override file"
fi

cat > "${OVERRIDE_FILE}" << YAMLEOF
# ============================================================================
# Docker Compose Override — FreePBX + WireGuard VPN
# Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')
#
# This file overrides the base docker-compose.yml to:
#   1. Use the committed image with WireGuard installed
#   2. Mount persistent volumes
#   3. Add capabilities for VPN (NET_ADMIN, SYS_MODULE)
#   4. Expose WireGuard port (51820/UDP)
# ============================================================================

services:
  freepbx:
    image: ${NEW_IMAGE}

    # ── Capabilities for WireGuard ──
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    sysctls:
      - net.ipv4.ip_forward=1
      - net.ipv4.conf.all.src_valid_mark=1

    # ── WireGuard port ──
    ports:
      - "${VPN_PORT}:${VPN_PORT}/udp"

    # ── Persistent Volumes ──
    volumes:
      # WireGuard config, keys, peers
      - ${DATA_ROOT}/wireguard:/etc/wireguard

      # Asterisk / FreePBX
      - ${DATA_ROOT}/asterisk-config:/etc/asterisk
      - ${DATA_ROOT}/asterisk-spool:/var/spool/asterisk
      - ${DATA_ROOT}/asterisk-log:/var/log/asterisk
      - ${DATA_ROOT}/asterisk-lib:/var/lib/asterisk

      # Phone provisioning
      - ${DATA_ROOT}/tftpboot:/tftpboot

    # ── Healthcheck ──
    healthcheck:
      test: ["CMD", "asterisk", "-rx", "core show uptime"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
YAMLEOF

# Add MySQL volume only if DB is local
if docker exec "${CONTAINER_NAME}" test -d /var/lib/mysql 2>/dev/null; then
    cat >> "${OVERRIDE_FILE}" << DBEOF

      # MariaDB data (local DB)
      - ${DATA_ROOT}/mysql:/var/lib/mysql
DBEOF
fi

log "Override file: ${OVERRIDE_FILE}"

###############################################################################
# Step 4: Show what will change
###############################################################################
echo ""
info "Override file contents:"
echo "───────────────────────────────────────────"
cat "${OVERRIDE_FILE}"
echo "───────────────────────────────────────────"
echo ""

###############################################################################
# Step 5: Confirm & Restart
###############################################################################
echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  ⚠️  Ready to restart FreePBX with VPN support              ║${NC}"
echo -e "${YELLOW}║                                                            ║${NC}"
echo -e "${YELLOW}║  This will:                                                ║${NC}"
echo -e "${YELLOW}║    1. Stop the current container                           ║${NC}"
echo -e "${YELLOW}║    2. Remove it                                            ║${NC}"
echo -e "${YELLOW}║    3. Start a new one from the committed image             ║${NC}"
echo -e "${YELLOW}║    4. With persistent volumes + VPN capabilities           ║${NC}"
echo -e "${YELLOW}║                                                            ║${NC}"
echo -e "${YELLOW}║  All data has been copied to: ${DATA_ROOT}/  ║${NC}"
echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

read -p "Proceed with restart? [y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    warn "Aborted. You can restart manually:"
    echo "  cd ${COMPOSE_DIR}"
    echo "  docker compose down"
    echo "  docker compose up -d"
    exit 0
fi

###############################################################################
# Step 6: Restart
###############################################################################
info "Step 6: Restarting FreePBX..."

cd "${COMPOSE_DIR}"

# Stop
docker compose down
log "Container stopped"

# Start with override
docker compose up -d
log "Container started with new image + volumes"

# Wait for it to come up
info "Waiting for FreePBX to start..."
sleep 10

# Check status
echo ""
docker compose ps
echo ""

# Check WireGuard
info "Checking WireGuard inside new container..."
sleep 5

NEWCONTAINER=$(docker compose ps --format '{{.Name}}' | head -1)
if docker exec "${NEWCONTAINER}" wg show wg0 2>/dev/null; then
    log "WireGuard is running inside the container!"
else
    warn "WireGuard not running yet. Starting it..."
    docker exec "${NEWCONTAINER}" wg-quick up wg0 2>&1 || true
    sleep 2
    docker exec "${NEWCONTAINER}" wg show wg0 2>/dev/null && log "WireGuard started!" || warn "WireGuard may need manual start"
fi

###############################################################################
# Final Summary
###############################################################################
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  ✅ FreePBX + VPN — Restart Complete                        ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  Image:   ${NEW_IMAGE}                             ║${NC}"
echo -e "${CYAN}║  Data:    ${DATA_ROOT}/                            ║${NC}"
echo -e "${CYAN}║  VPN:     0.0.0.0:${VPN_PORT}/UDP → wg0                        ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  Persistent Volumes:                                       ║${NC}"
echo -e "${CYAN}║    ${DATA_ROOT}/wireguard      → /etc/wireguard   ║${NC}"
echo -e "${CYAN}║    ${DATA_ROOT}/asterisk-config → /etc/asterisk   ║${NC}"
echo -e "${CYAN}║    ${DATA_ROOT}/asterisk-spool  → /var/spool/ast  ║${NC}"
echo -e "${CYAN}║    ${DATA_ROOT}/asterisk-log    → /var/log/ast    ║${NC}"
echo -e "${CYAN}║    ${DATA_ROOT}/asterisk-lib    → /var/lib/ast    ║${NC}"
echo -e "${CYAN}║    ${DATA_ROOT}/tftpboot        → /tftpboot       ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║  Management (inside container):                            ║${NC}"
echo -e "${CYAN}║    docker exec -it <name> /etc/wireguard/add_peer.sh       ║${NC}"
echo -e "${CYAN}║    docker exec -it <name> /etc/wireguard/list_peers.sh     ║${NC}"
echo -e "${CYAN}║    docker exec -it <name> wg show                          ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
log "Done! 🎉"
