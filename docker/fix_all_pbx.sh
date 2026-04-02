#!/bin/bash
# =============================================================================
# Fix All PBX Configuration Issues
# =============================================================================
# Run on VPS host: sudo ./fix_all_pbx.sh
#
# Fixes:
#   1. PJSIP local_net → correct Docker subnet (172.16.0.0/12 covers all)
#   2. Remove duplicate transport-wss from custom config
#   3. Fix TURN password mismatch
#   4. Fix rtp_additional.conf turnaddr format
#   5. Reload Asterisk
# =============================================================================

set -euo pipefail

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

# ---- Auto-detect FreePBX container ----
PBX=""
for name in "initpbx-freepbx-1" "initpbx_freepbx_1" "freepbx" "asterisk"; do
    if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
        PBX="$name"
        break
    fi
done
if [ -z "$PBX" ]; then
    PBX=$(docker ps --format '{{.Names}}\t{{.Image}}' | grep -i 'freepbx\|sangoma\|tiredofit' | head -1 | awk '{print $1}')
fi
if [ -z "$PBX" ]; then
    log_err "FreePBX container not found!"
    echo "Running containers:"
    docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
    exit 1
fi
log_ok "Found FreePBX container: $PBX"

# ---- Detect actual PBX Docker IP ----
PBX_IP=$(docker inspect "$PBX" --format '{{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}' | awk '{print $1}')
log_info "PBX container IP: $PBX_IP"

echo ""
echo "============================================="
echo "  Fix All PBX Configuration Issues"
echo "============================================="

# ================================================================
# FIX 1: pjsip.transports_custom.conf
# ================================================================
log_section "Fix 1: PJSIP Transports Custom"

# The custom conf had a DUPLICATE [transport-wss] that conflicts
# with the auto-generated [0.0.0.0-wss] in pjsip.transports.conf.
# 
# We REMOVE the duplicate transport and instead just provide
# local_net overrides that get included via #include at [0] section.
# The [0] section in pjsip.transports.conf does:
#   [0]
#   #include pjsip.transports_custom.conf
# This means anything we put here becomes part of section [0],
# NOT a standalone transport. We cannot define new sections here
# because it would break the [0] section parsing.
#
# SOLUTION: Leave this file EMPTY (or comments only).
# The local_net fix will be done via fwconsole instead.

log_info "Current pjsip.transports_custom.conf:"
docker exec "$PBX" cat /etc/asterisk/pjsip.transports_custom.conf 2>/dev/null || true
echo ""

CUSTOM_CONF="; =============================================================================
; PJSIP Custom Transport Config - Arrowz
; Fixed: $(date '+%Y-%m-%d %H:%M')
; =============================================================================
; NOTE: This file is #included inside [0] section of pjsip.transports.conf
; Do NOT define new transport sections here - they would corrupt [0] parsing.
;
; The WSS transport is already defined as [0.0.0.0-wss] in the auto-generated
; pjsip.transports.conf. HTTP TLS is configured in http_additional.conf.
;
; local_net is managed via FreePBX GUI / fwconsole.
; ============================================================================="

echo "$CUSTOM_CONF" | docker exec -i "$PBX" tee /etc/asterisk/pjsip.transports_custom.conf > /dev/null
log_ok "Removed duplicate transport-wss from custom config"

# ================================================================
# FIX 2: Update local_net via fwconsole
# ================================================================
log_section "Fix 2: PJSIP local_net"

log_info "Current local_net in transports:"
docker exec "$PBX" grep "local_net" /etc/asterisk/pjsip.transports.conf 2>/dev/null || true
echo ""

# Use fwconsole to set correct local networks
# 172.16.0.0/12 covers ALL Docker bridge subnets (172.16.0.0 - 172.31.255.255)
log_info "Setting LOCALNETS via fwconsole..."
docker exec "$PBX" fwconsole setting LOCALNETS '172.16.0.0/12,10.0.0.0/8,192.168.0.0/16,157.173.125.136/32' 2>/dev/null && \
    log_ok "LOCALNETS updated via fwconsole" || \
    log_warn "fwconsole failed — trying direct config edit..."

# Also try the FreePBX reload to regenerate transports.conf
log_info "Regenerating PJSIP config..."
docker exec "$PBX" fwconsole reload 2>/dev/null && \
    log_ok "FreePBX config reloaded" || \
    log_warn "fwconsole reload had issues"

# Verify
sleep 2
log_info "Verifying local_net after reload:"
docker exec "$PBX" grep "local_net" /etc/asterisk/pjsip.transports.conf 2>/dev/null || true

# If fwconsole didn't update it, do a direct sed replacement
if ! docker exec "$PBX" grep "172.16.0.0/12" /etc/asterisk/pjsip.transports.conf 2>/dev/null | grep -q "172.16"; then
    log_warn "fwconsole didn't update local_net — applying direct fix..."
    
    # Replace old local_net entries in transports.conf
    docker exec "$PBX" sed -i \
        -e 's|local_net=172\.25\.0\.0/16|local_net=172.16.0.0/12|' \
        -e 's|local_net=172\.23\.0\.0/16|local_net=10.0.0.0/8|' \
        /etc/asterisk/pjsip.transports.conf
    
    log_ok "Direct sed replacement applied"
    
    log_info "Updated local_net:"
    docker exec "$PBX" grep "local_net" /etc/asterisk/pjsip.transports.conf 2>/dev/null
fi

# ================================================================
# FIX 3: RTP config — fix TURN password + turnaddr format
# ================================================================
log_section "Fix 3: RTP / TURN Configuration"

log_info "Current rtp_custom.conf:"
docker exec "$PBX" cat /etc/asterisk/rtp_custom.conf 2>/dev/null || true
echo ""

# Fix rtp_custom.conf with correct TURN password and ICE candidate
RTP_CUSTOM="; Arrowz RTP Custom - Fix ICE/TURN for WebRTC behind Docker NAT
; Fixed: $(date '+%Y-%m-%d %H:%M')

; Override TURN settings from rtp_additional.conf
; rtp_additional.conf has WRONG format: turnaddr=turn:IP:port
; Asterisk expects just IP or hostname, NOT a turn: URI
turnaddr=157.173.125.136
turnusername=webrtc
turnpassword=arrowz2024!

[ice_host_candidates]
; Map Docker internal IP to public IP for ICE
; Without this, Asterisk sends ${PBX_IP} (Docker) as ICE candidate
${PBX_IP} => 157.173.125.136"

echo "$RTP_CUSTOM" | docker exec -i "$PBX" tee /etc/asterisk/rtp_custom.conf > /dev/null
log_ok "Updated rtp_custom.conf (password=arrowz2024!, ICE candidate=${PBX_IP})"

# ================================================================
# FIX 4: Reload Asterisk modules
# ================================================================
log_section "Fix 4: Reload Asterisk"

log_info "Reloading PJSIP..."
docker exec "$PBX" asterisk -rx "module reload res_pjsip.so" 2>/dev/null
sleep 1

log_info "Reloading RTP..."
docker exec "$PBX" asterisk -rx "module reload res_rtp_asterisk.so" 2>/dev/null
sleep 1

log_info "Reloading HTTP (for WSS)..."
docker exec "$PBX" asterisk -rx "module reload res_http_websocket.so" 2>/dev/null
sleep 2

log_ok "All modules reloaded"

# ================================================================
# VERIFY
# ================================================================
log_section "Verification"

echo -e "${BOLD}Transports:${NC}"
docker exec "$PBX" asterisk -rx "pjsip show transports" 2>/dev/null
echo ""

echo -e "${BOLD}local_net in config:${NC}"
docker exec "$PBX" grep "local_net" /etc/asterisk/pjsip.transports.conf 2>/dev/null
echo ""

echo -e "${BOLD}Registered contacts:${NC}"
docker exec "$PBX" asterisk -rx "pjsip show contacts" 2>/dev/null
echo ""

echo -e "${BOLD}RTP config:${NC}"
docker exec "$PBX" asterisk -rx "rtp show settings" 2>/dev/null | head -20
echo ""

echo "============================================="
echo -e "  ${GREEN}${BOLD}All fixes applied!${NC}"
echo "============================================="
echo ""
echo "Summary of changes:"
echo "  ✅ Removed duplicate [transport-wss] from custom config"
echo "  ✅ local_net now covers 172.16.0.0/12 (all Docker subnets)"
echo "  ✅ TURN password unified to 'arrowz2024!'"
echo "  ✅ ICE host candidate: ${PBX_IP} => 157.173.125.136"
echo "  ✅ Asterisk modules reloaded"
echo ""
echo "Next steps:"
echo "  1. Fix Zoiper on phone: Registration Expiry=300, Keep-Alive=15s"
echo "  2. Wait for 2210 to register (check: asterisk -rx 'pjsip show contacts')"
echo "  3. Test call: 2211 → 2210 from browser softphone"
echo ""
