#!/bin/bash
# =============================================================================
# Emergency Fix: pjsip.endpoint_custom.conf
# =============================================================================
# The file pjsip.endpoint_custom.conf is #included at LINE 11 of
# pjsip.endpoint.conf — BEFORE [2210] is defined at line 54.
# Having [2210](+) in the _custom file causes:
#   "Category addition requested, but category '2210' does not exist"
#
# The CORRECT overrides are already in pjsip.endpoint_custom_post.conf
# which is loaded AFTER all endpoints are defined.
#
# FIX: Clear the _custom.conf file (keep only comments).
# =============================================================================

set -euo pipefail

# Auto-detect FreePBX container
PBX=""
for name in "initpbx-freepbx-1" "initpbx_freepbx_1" "freepbx"; do
    if docker ps --format '{{.Names}}' | grep -q "^${name}$"; then
        PBX="$name"; break
    fi
done
[ -z "$PBX" ] && PBX=$(docker ps --format '{{.Names}}\t{{.Image}}' | grep -i 'freepbx\|sangoma' | head -1 | awk '{print $1}')
[ -z "$PBX" ] && { echo "ERROR: FreePBX container not found!"; exit 1; }
echo "Found: $PBX"

echo ""
echo "=== BEFORE (broken) ==="
docker exec "$PBX" cat /etc/asterisk/pjsip.endpoint_custom.conf
echo ""

# Write clean file — no endpoint overrides (those go in _custom_post.conf)
FIXED="; Arrowz - PJSIP Custom Endpoints (PRE-load)
; Fixed: $(date '+%Y-%m-%d %H:%M')
;
; WARNING: This file is included BEFORE endpoints are defined.
; Do NOT use [name](+) here — it will fail!
; All endpoint overrides go in pjsip.endpoint_custom_post.conf instead."

echo "$FIXED" | docker exec -i "$PBX" tee /etc/asterisk/pjsip.endpoint_custom.conf > /dev/null

echo "=== AFTER (fixed) ==="
docker exec "$PBX" cat /etc/asterisk/pjsip.endpoint_custom.conf
echo ""

echo "=== Reloading PJSIP... ==="
docker exec "$PBX" asterisk -rx "module reload res_pjsip.so" 2>/dev/null
sleep 3

echo ""
echo "=== Checking for errors... ==="
docker exec "$PBX" asterisk -rx "core show warnings" 2>/dev/null | tail -5

echo ""
echo "=== Verify 2210 endpoint loaded ==="
docker exec "$PBX" asterisk -rx "pjsip show endpoint 2210" 2>/dev/null | head -15

echo ""
echo "=== Current contacts ==="
docker exec "$PBX" asterisk -rx "pjsip show contacts" 2>/dev/null

echo ""
echo "✅ Fix applied! Now restart Zoiper on your phone to re-register."
