#!/bin/bash
# =============================================================================
# fix_pbx_rtp.sh — Fix Asterisk/Docker RTP & NAT for WebRTC + SIP calls
# =============================================================================
# RUN ON THE VPS HOST (not inside Docker)
# Path: /opt/proj/frappe_dev/development/frappe-bench/apps/arrowz/scripts/fix_pbx_rtp.sh
#
# ROOT CAUSE: Asterisk sends Docker IP (172.23.0.2) in SDP to SIP phones.
#   The SIP phone can't reach 172.23.0.2, so no RTP flows → call disconnects
#   after 30 seconds with "lack of audio RTP activity".
#
# This script fixes:
#   1. Docker: Expose RTP port range (10500-10700/UDP) from PBX container
#   2. Asterisk transport: Fix local_net so external_media_address is applied
#   3. Asterisk transport: Remove duplicate WSS transport
#   4. Asterisk: Reload config
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[FIX]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*"; }
info() { echo -e "${CYAN}[INFO]${NC} $*"; }

# =============================================================================
# Step 0: Detect PBX container
# =============================================================================
log "Looking for FreePBX/Asterisk Docker container..."

PBX_CONTAINER=""
for name in initpbx-freepbx-1 freepbx freepbx-app asterisk initpbx_freepbx_1; do
    if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
        PBX_CONTAINER="$name"
        break
    fi
done

if [ -z "$PBX_CONTAINER" ]; then
    # Try partial match
    PBX_CONTAINER=$(docker ps --format '{{.Names}}' | grep -i "freepbx\|asterisk\|pbx" | head -1)
fi

if [ -z "$PBX_CONTAINER" ]; then
    err "Cannot find PBX container. Is it running?"
    exit 1
fi
log "Found PBX container: $PBX_CONTAINER"

# Get container ID for inspect
PBX_ID=$(docker inspect --format '{{.Id}}' "$PBX_CONTAINER")
PBX_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$PBX_CONTAINER" 2>/dev/null || echo "172.23.0.2")
log "PBX container IP: $PBX_IP"

# Detect VPS public IP
VPS_IP=$(curl -s4 ifconfig.me 2>/dev/null || curl -s4 icanhazip.com 2>/dev/null || echo "157.173.125.136")
log "VPS public IP: $VPS_IP"

# =============================================================================
# Step 1: Check current Docker port mappings
# =============================================================================
log "Checking current Docker port mappings..."
echo ""
docker port "$PBX_CONTAINER" 2>/dev/null || true
echo ""

# Check if RTP ports are mapped
RTP_MAPPED=false
if docker port "$PBX_CONTAINER" 2>/dev/null | grep -q "105[0-9][0-9]/udp"; then
    RTP_MAPPED=true
    log "RTP ports appear to be mapped already."
else
    warn "RTP ports (10500-10700/UDP) are NOT mapped!"
    warn "This is the PRIMARY reason for no audio in calls."
fi

# =============================================================================
# Step 2: Fix Asterisk configs INSIDE the container
# =============================================================================
log "Fixing Asterisk configuration inside container..."

# --- 2a: Fix pjsip.transports_custom.conf (remove duplicate WSS transport) ---
info "Removing duplicate WSS transport from pjsip.transports_custom.conf..."
docker exec "$PBX_CONTAINER" bash -c "
    CONF='/etc/asterisk/pjsip.transports_custom.conf'
    if [ -f \"\$CONF\" ]; then
        cp \"\$CONF\" \"\${CONF}.bak.\$(date +%s)\"
        # Clear the file - the auto-generated 0.0.0.0-wss transport handles WSS
        echo '; pjsip.transports_custom.conf - Cleaned by fix_pbx_rtp.sh' > \"\$CONF\"
        echo '; Duplicate WSS transport removed - using FreePBX auto-generated transport' >> \"\$CONF\"
        echo '[FIX] Cleaned pjsip.transports_custom.conf'
    fi
"

# --- 2b: Fix transport local_net ---
# The auto-generated pjsip.transports.conf has local_net=172.23.0.0/16 which
# makes Docker-NATted SIP phones appear 'local', preventing external_media_address.
# We fix this directly in the auto-generated file (it won't regenerate until FreePBX apply).
info "Fixing transport local_net in pjsip.transports.conf..."
docker exec "$PBX_CONTAINER" bash -c "
    CONF='/etc/asterisk/pjsip.transports.conf'
    if [ -f \"\$CONF\" ]; then
        cp \"\$CONF\" \"\${CONF}.bak.\$(date +%s)\"

        # Replace broad Docker subnet with just the container's own IP
        # This ensures remote SIP phones (through Docker NAT) get external_media_address
        sed -i 's|local_net=172.23.0.0/16|local_net=${PBX_IP}/32|g' \"\$CONF\"
        sed -i 's|local_net=172.25.0.0/16|local_net=${PBX_IP}/32|g' \"\$CONF\"

        # Remove VPS public IP from local_net (it's NOT local!)
        sed -i '/local_net=${VPS_IP}\/32/d' \"\$CONF\"

        echo '[FIX] Fixed local_net in pjsip.transports.conf'
        echo '--- Updated transport config: ---'
        grep -A15 '\\[0.0.0.0-udp\\]' \"\$CONF\" | head -20
        echo '---'
        grep -A15 '\\[0.0.0.0-wss\\]' \"\$CONF\" | head -20
    fi
"

# --- 2c: Fix rtp_custom.conf (ensure correct ice_host_candidates) ---
info "Verifying rtp_custom.conf ice_host_candidates mapping..."
docker exec "$PBX_CONTAINER" bash -c "
    CONF='/etc/asterisk/rtp_custom.conf'
    if [ -f \"\$CONF\" ]; then
        # Check if ice_host_candidates has the right mapping
        if grep -q '${PBX_IP} => ${VPS_IP}' \"\$CONF\"; then
            echo '[OK] ice_host_candidates mapping is correct: ${PBX_IP} => ${VPS_IP}'
        else
            cp \"\$CONF\" \"\${CONF}.bak.\$(date +%s)\"
            cat > \"\$CONF\" << 'RTPEOF'
; Arrowz RTP Custom - ICE/TURN for WebRTC behind Docker NAT
; Fixed by fix_pbx_rtp.sh

turnaddr=${VPS_IP}
turnusername=webrtc
turnpassword=Arrowz2024!

[ice_host_candidates]
; Map Docker internal IP to public IP for ICE
${PBX_IP} => ${VPS_IP}
RTPEOF
            echo '[FIX] Updated rtp_custom.conf with correct ice_host_candidates'
        fi
    fi
"

# --- 2d: Verify endpoint 2210 has WebRTC disabled ---
info "Checking endpoint 2210 (SIP phone - should NOT have WebRTC)..."
docker exec "$PBX_CONTAINER" bash -c "
    CONF='/etc/asterisk/pjsip.endpoint_custom_post.conf'
    if grep -q '\\[2210\\]' \"\$CONF\" 2>/dev/null; then
        echo '[OK] 2210 override exists in endpoint_custom_post.conf'
        grep -A6 '\\[2210\\]' \"\$CONF\"
    else
        echo '[WARN] 2210 override not found — adding it'
        cp \"\$CONF\" \"\${CONF}.bak.\$(date +%s)\" 2>/dev/null || true
        cat >> \"\$CONF\" << 'EOF'

; 2210 - Regular SIP Phone (NOT WebRTC)
[2210](+)
media_encryption=no
ice_support=no
use_avpf=no
rtcp_mux=no
bundle=no
EOF
        echo '[FIX] Added 2210 WebRTC override'
    fi
"

# =============================================================================
# Step 3: Reload Asterisk (apply config changes without restart)
# =============================================================================
log "Reloading Asterisk configuration..."
docker exec "$PBX_CONTAINER" asterisk -rx "module reload res_pjsip.so" 2>/dev/null || true
docker exec "$PBX_CONTAINER" asterisk -rx "pjsip reload" 2>/dev/null || true
sleep 2

# Verify
info "Verifying transport config..."
docker exec "$PBX_CONTAINER" asterisk -rx "pjsip show transports" 2>/dev/null || true
echo ""
info "Verifying endpoint 2210..."
docker exec "$PBX_CONTAINER" asterisk -rx "pjsip show endpoint 2210" 2>/dev/null | grep -E "media_encryption|ice_support|use_avpf|transport" | head -10 || true
echo ""
info "Verifying endpoint 2211..."
docker exec "$PBX_CONTAINER" asterisk -rx "pjsip show endpoint 2211" 2>/dev/null | grep -E "media_encryption|ice_support|use_avpf|transport" | head -10 || true

# =============================================================================
# Step 4: Docker RTP port fix
# =============================================================================
if [ "$RTP_MAPPED" = false ]; then
    echo ""
    echo "============================================================================="
    warn "CRITICAL: RTP ports are NOT mapped in Docker!"
    echo "============================================================================="
    echo ""
    echo "Without RTP port mapping, audio CANNOT flow even with correct SDP."
    echo ""
    echo "You have two options:"
    echo ""
    echo -e "${CYAN}Option A (RECOMMENDED - easiest):${NC} Use Docker host networking"
    echo "  Edit your docker-compose.yml for the PBX container and add:"
    echo "    network_mode: host"
    echo "  Then restart: docker compose up -d"
    echo "  This eliminates ALL Docker NAT issues."
    echo ""
    echo -e "${CYAN}Option B:${NC} Add RTP port range to docker-compose.yml"
    echo "  Under the PBX service's 'ports:' section, add:"
    echo "    - \"10500-10700:10500-10700/udp\""
    echo "  Then restart: docker compose up -d"
    echo ""

    # Try to find docker-compose file
    COMPOSE_FILE=""
    for path in \
        /opt/proj/initpbx/docker-compose.yml \
        /opt/proj/initpbx/docker-compose.yaml \
        /opt/initpbx/docker-compose.yml \
        /root/initpbx/docker-compose.yml \
        /home/*/initpbx/docker-compose.yml; do
        if [ -f "$path" ] 2>/dev/null; then
            COMPOSE_FILE="$path"
            break
        fi
    done

    if [ -n "$COMPOSE_FILE" ]; then
        log "Found Docker Compose file: $COMPOSE_FILE"
        echo ""
        echo "Current ports section:"
        grep -A20 "ports:" "$COMPOSE_FILE" | head -20
        echo ""

        read -p "Add RTP ports (10500-10700/UDP) to $COMPOSE_FILE? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp "$COMPOSE_FILE" "${COMPOSE_FILE}.bak.$(date +%s)"

            # Add RTP port mapping after the last port line
            if grep -q "10500-10700" "$COMPOSE_FILE"; then
                log "RTP ports already in compose file."
            else
                # Find the ports section and add RTP ports
                sed -i '/^\s*-\s*"[0-9]*:[0-9]*/a\      - "10500-10700:10500-10700/udp"' "$COMPOSE_FILE"
                log "Added RTP port mapping to $COMPOSE_FILE"
                echo ""
                warn "You must restart the PBX container for this to take effect:"
                echo "  cd $(dirname $COMPOSE_FILE)"
                echo "  docker compose down && docker compose up -d"
            fi
        fi
    else
        warn "Could not find docker-compose.yml automatically."
        echo "Please find it manually and add the RTP port mapping."
    fi
fi

# =============================================================================
# Step 5: Check TURN server
# =============================================================================
echo ""
log "Checking if TURN server is running on port 3478..."
if ss -ulnp | grep -q ":3478 " 2>/dev/null || netstat -ulnp 2>/dev/null | grep -q ":3478 "; then
    log "TURN server is listening on port 3478"
else
    warn "No TURN server detected on port 3478!"
    echo "  Without TURN, WebRTC calls may fail on restrictive networks."
    echo "  Install coturn: apt install coturn"
    echo "  Or the calls may work with just STUN if the network allows direct UDP."
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "============================================================================="
log "PBX Configuration Fix Summary"
echo "============================================================================="
echo ""
echo "✅ Removed duplicate WSS transport (pjsip.transports_custom.conf)"
echo "✅ Fixed local_net: Docker subnet → container IP only (${PBX_IP}/32)"
echo "✅ Removed VPS public IP from local_net"
echo "✅ Verified ice_host_candidates mapping (${PBX_IP} → ${VPS_IP})"
echo "✅ Verified endpoint 2210 has WebRTC disabled"
echo "✅ Reloaded Asterisk PJSIP module"
echo ""
if [ "$RTP_MAPPED" = false ]; then
    echo -e "${RED}⚠️  RTP PORTS STILL NOT MAPPED — Docker restart needed!${NC}"
    echo "   Without RTP port mapping (10500-10700/UDP), there will be NO AUDIO."
    echo "   See Option A or B above to fix."
else
    echo "✅ RTP ports are mapped"
fi
echo ""
echo "After fixing RTP ports, test with:"
echo "  1. Reload browser (Ctrl+Shift+R)"
echo "  2. Check console: 'Arrowz: SIP registered'"
echo "  3. Call 2210 from WebRTC softphone"
echo "  4. Should see 'ICE connection state: connected' in browser console"
echo "============================================================================="
