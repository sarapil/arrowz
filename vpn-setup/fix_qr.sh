#!/bin/bash
###############################################################################
# Fix WireGuard QR Code — Run on VPS HOST
# =========================================
# Reads admin config from FreePBX container, strips Unicode comments,
# ensures clean config, regenerates QR code.
#
# Usage:  bash fix_qr.sh [peer_name]
#         bash fix_qr.sh          → defaults to "admin"
#         bash fix_qr.sh ahmed
###############################################################################

set -euo pipefail

CONTAINER="initpbx-freepbx-1"
PEER="${1:-admin}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Fix WireGuard QR — Peer: ${PEER}${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ── Step 1: Read the original config ──
echo -e "${YELLOW}[1] Reading config from container...${NC}"
ORIGINAL=$(docker exec "$CONTAINER" cat "/etc/wireguard/peers/${PEER}/${PEER}.conf" 2>&1)

if [[ $? -ne 0 ]] || [[ -z "$ORIGINAL" ]]; then
    echo -e "${RED}✗ Could not read config for peer '${PEER}'${NC}"
    echo "  Available peers:"
    docker exec "$CONTAINER" ls /etc/wireguard/peers/ 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✓ Original config:${NC}"
echo "─────────────────────────────────"
echo "$ORIGINAL"
echo "─────────────────────────────────"
echo ""

# ── Step 2: Create clean config (strip comments, trim whitespace, fix line endings) ──
echo -e "${YELLOW}[2] Creating clean config...${NC}"
CLEAN=$(echo "$ORIGINAL" | grep -v '^#' | grep -v '^$' | sed 's/\r$//' | sed 's/[[:space:]]*$//')

# Ensure sections have blank line between them
CLEAN=$(echo "$CLEAN" | sed 's/^\[Peer\]/\n[Peer]/')

echo -e "${GREEN}✓ Clean config:${NC}"
echo "─────────────────────────────────"
echo "$CLEAN"
echo "─────────────────────────────────"
echo ""

# ── Step 3: Validate endpoint ──
ENDPOINT=$(echo "$CLEAN" | grep -i "^Endpoint" | head -1 | sed 's/Endpoint[[:space:]]*=[[:space:]]*//')
if [[ -z "$ENDPOINT" ]]; then
    echo -e "${RED}✗ No Endpoint found in config!${NC}"
    exit 1
fi

# Validate format: host:port
if [[ ! "$ENDPOINT" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$ ]] && \
   [[ ! "$ENDPOINT" =~ ^[a-zA-Z0-9._-]+:[0-9]+$ ]]; then
    echo -e "${RED}✗ Invalid endpoint format: '${ENDPOINT}'${NC}"
    echo "  Expected: IP:PORT or HOSTNAME:PORT"
    exit 1
fi
echo -e "${GREEN}✓ Endpoint valid: ${ENDPOINT}${NC}"
echo ""

# ── Step 4: Write clean config to temp file ──
TMPFILE="/tmp/wg_${PEER}_clean.conf"
echo "$CLEAN" > "$TMPFILE"

# ── Step 5: Generate QR code ──
echo -e "${YELLOW}[3] Generating QR code...${NC}"
echo ""

# Try on host first
if command -v qrencode &>/dev/null; then
    echo -e "${GREEN}📱 Scan this QR code with WireGuard app:${NC}"
    echo ""
    qrencode -t ansiutf8 < "$TMPFILE"
    echo ""
    # Also save PNG
    qrencode -t png -o "/tmp/wg_${PEER}_qr.png" < "$TMPFILE"
    echo -e "${GREEN}✓ PNG saved: /tmp/wg_${PEER}_qr.png${NC}"
else
    # Fall back to container's qrencode
    echo -e "${YELLOW}  qrencode not on host, using container...${NC}"
    docker cp "$TMPFILE" "${CONTAINER}:/tmp/wg_clean.conf"
    docker exec "$CONTAINER" qrencode -t ansiutf8 < "$TMPFILE"
    echo ""
fi

# ── Step 6: Also save clean config inside container ──
echo ""
echo -e "${YELLOW}[4] Saving clean config to container...${NC}"
docker cp "$TMPFILE" "${CONTAINER}:/etc/wireguard/peers/${PEER}/${PEER}_clean.conf"
echo -e "${GREEN}✓ Saved: /etc/wireguard/peers/${PEER}/${PEER}_clean.conf${NC}"

# ── Step 7: Regenerate QR inside container ──
docker exec "$CONTAINER" bash -c "qrencode -t png -o '/etc/wireguard/peers/${PEER}/${PEER}_clean_qr.png' < '/etc/wireguard/peers/${PEER}/${PEER}_clean.conf'" 2>/dev/null || true

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Done!                                           ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}║  Option 1: Scan the QR above                    ║${NC}"
echo -e "${CYAN}║  Option 2: Manually import the config:           ║${NC}"
echo -e "${CYAN}║    ${TMPFILE}  ║${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}║  Option 3: Copy text config to phone:            ║${NC}"
echo -e "${CYAN}║    Open WireGuard app → + → Create from scratch  ║${NC}"
echo -e "${CYAN}║    or import from file/text                      ║${NC}"
echo -e "${CYAN}║                                                  ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# Show config one more time for easy copy-paste
echo -e "${GREEN}📋 Config for manual entry:${NC}"
echo ""
echo "$CLEAN"
echo ""
