#!/bin/bash
###############################################################################
# Dinstar GSM Gateway — Asterisk PJSIP Trunk Configuration (Run on VPS HOST)
# ===========================================================================
# Configures FreePBX/Asterisk to accept SIP from the Dinstar UC2000-VE-8G
# connecting DIRECTLY via OpenVPN TLS tunnel.
#
# Dinstar at 10.10.1.2 → VPN → FreePBX at 10.10.1.1:51600
# NO gateway machine — NO NAT — direct VPN tunnel!
#
# Creates:
#   - PJSIP Endpoint (dinstar) with auth, AOR
#   - Transport local_net (VPN subnet)
#   - IP-based identify (match 10.10.1.2)
#   - Inbound dialplan context (from-dinstar)
###############################################################################

set -euo pipefail

CONTAINER="initpbx-freepbx-1"
DINSTAR_USER="dinstar"
DINSTAR_PASS="D1nstar#VPN2026!"
DINSTAR_VPN_IP="10.10.1.2"       # Dinstar's VPN IP (direct)
FREEPBX_VPN_IP="10.10.1.1"       # FreePBX VPN IP
SIP_PORT="51600"                  # FreePBX PJSIP UDP port
CONTEXT="from-dinstar"            # Inbound context for GSM calls
DEFAULT_EXT="1155"                # Default extension for unrouted inbound calls

echo "═══════════════════════════════════════════════════════"
echo "  Dinstar PJSIP Trunk Configuration (Direct VPN)"
echo "  Dinstar: ${DINSTAR_VPN_IP} → FreePBX: ${FREEPBX_VPN_IP}:${SIP_PORT}"
echo "═══════════════════════════════════════════════════════"

# ── 1. Add VPN subnet to transport local_net ──
echo ""
echo "[1] Fixing PJSIP transport — adding VPN to local_net..."

docker exec "$CONTAINER" bash -c "
CUSTOM_POST='/etc/asterisk/pjsip.transports_custom_post.conf'

if grep -q '10.10.1.0' \"\$CUSTOM_POST\" 2>/dev/null; then
    echo '  ✓ VPN local_net already configured'
else
    cat >> \"\$CUSTOM_POST\" << 'TEOF'

; =============================================================================
; Dinstar VPN — Transport Override
; Add VPN subnets to local_net so Asterisk uses VPN IP in SDP
; (prevents Asterisk from using external_media_address for RTP)
; =============================================================================
[0.0.0.0-udp](+)
local_net=10.10.1.0/24
local_net=10.10.0.0/24

TEOF
    echo '  ✓ Added VPN subnets to UDP transport local_net'
fi
"

# ── 2. Create PJSIP Auth ──
echo ""
echo "[2] Creating PJSIP auth for Dinstar..."

docker exec "$CONTAINER" bash -c "
AUTH_FILE='/etc/asterisk/pjsip.auth_custom_post.conf'

if grep -q '${DINSTAR_USER}-auth' \"\$AUTH_FILE\" 2>/dev/null; then
    echo '  ✓ Auth already exists'
else
    cat >> \"\$AUTH_FILE\" << 'AEOF'

; =============================================================================
; Dinstar UC2000-VE-8G GSM Gateway — Authentication
; =============================================================================
[${DINSTAR_USER}-auth]
type=auth
auth_type=userpass
username=${DINSTAR_USER}
password=${DINSTAR_PASS}

AEOF
    echo '  ✓ Auth created: ${DINSTAR_USER}-auth'
fi
"

# ── 3. Create PJSIP AOR (Address of Record) ──
echo ""
echo "[3] Creating PJSIP AOR for Dinstar..."

docker exec "$CONTAINER" bash -c "
AOR_FILE='/etc/asterisk/pjsip.aor_custom_post.conf'

if grep -q '${DINSTAR_USER}' \"\$AOR_FILE\" 2>/dev/null; then
    echo '  ✓ AOR already exists'
else
    cat >> \"\$AOR_FILE\" << 'OEOF'

; =============================================================================
; Dinstar UC2000-VE-8G GSM Gateway — AOR
; max_contacts=8 because the Dinstar has 8 GSM ports
; =============================================================================
[${DINSTAR_USER}]
type=aor
max_contacts=8
qualify_frequency=30
default_expiration=120
minimum_expiration=60

OEOF
    echo '  ✓ AOR created: ${DINSTAR_USER}'
fi
"

# ── 4. Create PJSIP Endpoint ──
echo ""
echo "[4] Creating PJSIP endpoint for Dinstar..."

docker exec "$CONTAINER" bash -c "
EP_FILE='/etc/asterisk/pjsip.endpoint_custom_post.conf'

if grep -q '\\[${DINSTAR_USER}\\]' \"\$EP_FILE\" 2>/dev/null; then
    echo '  ✓ Endpoint already exists'
else
    cat >> \"\$EP_FILE\" << 'EEOF'

; =============================================================================
; Dinstar UC2000-VE-8G GSM Gateway — Endpoint (Direct VPN)
; =============================================================================
; Dinstar connects DIRECTLY via OpenVPN TLS tunnel (no gateway/NAT).
; Traffic: Dinstar (10.10.1.2) → VPN tunnel → Asterisk (10.10.1.1:51600)
;
; Key settings:
;   - direct_media=no: Force RTP through Asterisk (consistent routing)
;   - rtp_symmetric=yes: RTP comes back on same VPN path
;   - force_rport=yes: Handle any port remapping
;   - alaw,ulaw: Best codecs for GSM→PCM (no transcoding loss)
;   - media_address: Use VPN IP for RTP
; =============================================================================
[${DINSTAR_USER}]
type=endpoint
context=${CONTEXT}
disallow=all
allow=alaw
allow=ulaw
allow=gsm
auth=${DINSTAR_USER}-auth
aors=${DINSTAR_USER}
direct_media=no
force_rport=yes
rewrite_contact=yes
rtp_symmetric=yes
ice_support=no
media_encryption=no
trust_id_inbound=yes
send_rpid=yes
send_pai=yes
dtmf_mode=rfc4733
t38_udptl=yes
t38_udptl_ec=redundancy
language=en
; Keepalive
rtp_keepalive=15
rtp_timeout=60
rtp_timeout_hold=300
; Caller ID
callerid=GSM Gateway <${DINSTAR_USER}>
; Media address — use VPN IP for RTP in SDP
media_address=${FREEPBX_VPN_IP}

EEOF
    echo '  ✓ Endpoint created: ${DINSTAR_USER}'
fi
"

# ── 5. Create Identify (IP-based matching) ──
echo ""
echo "[5] Creating PJSIP identify for Dinstar VPN IP..."

docker exec "$CONTAINER" bash -c "
ID_FILE='/etc/asterisk/pjsip.identify_custom_post.conf'

if grep -q '${DINSTAR_USER}-identify' \"\$ID_FILE\" 2>/dev/null; then
    echo '  ✓ Identify already exists'
else
    cat >> \"\$ID_FILE\" << 'IEOF'

; =============================================================================
; Dinstar — IP-based identification
; Matches SIP from Dinstar's VPN IP directly (no gateway NAT)
; =============================================================================
[${DINSTAR_USER}-identify]
type=identify
endpoint=${DINSTAR_USER}
match=${DINSTAR_VPN_IP}/32

IEOF
    echo '  ✓ Identify created: match ${DINSTAR_VPN_IP}'
fi
"

# ── 6. Create Inbound Dialplan Context ──
echo ""
echo "[6] Creating inbound dialplan context [${CONTEXT}]..."

docker exec "$CONTAINER" bash -c "
EXT_FILE='/etc/asterisk/extensions_custom.conf'

if grep -q '\\[${CONTEXT}\\]' \"\$EXT_FILE\" 2>/dev/null; then
    echo '  ✓ Context already exists'
else
    cat >> \"\$EXT_FILE\" << 'DEOF'

; =============================================================================
; Dinstar UC2000-VE-8G — Inbound GSM Calls (Direct VPN)
; =============================================================================
; Calls coming IN from GSM network through the Dinstar gateway.
;
; Routing logic:
;   1. Match internal extension → ring it directly
;   2. Otherwise → ring default extension (1155)
; =============================================================================

[${CONTEXT}]
; --- Log all incoming GSM calls ---
exten => _X.,1,NoOp(=== INBOUND GSM via Dinstar ===)
 same => n,NoOp(From: \${CALLERID(num)} To: \${EXTEN})
 same => n,Set(CALLERID(name)=GSM-\${CALLERID(num)})

; --- Try to match internal extension first ---
 same => n,Set(DEST=\${EXTEN})
 same => n,GotoIf(\$[\${DIALPLAN_EXISTS(from-internal,\${DEST},1)}]?internal)

; Otherwise, route to default extension
 same => n,Goto(from-internal,${DEFAULT_EXT},1)

; Internal extension match
 same => n(internal),Goto(from-internal,\${DEST},1)

; Fallback / invalid
exten => i,1,NoOp(Invalid destination from Dinstar: \${EXTEN})
 same => n,Goto(from-internal,${DEFAULT_EXT},1)

DEOF
    echo '  ✓ Context created: ${CONTEXT}'
fi
"

# ── 7. Reload Asterisk ──
echo ""
echo "[7] Reloading Asterisk configuration..."

docker exec "$CONTAINER" bash -c "
  asterisk -rx 'module reload res_pjsip.so' 2>/dev/null
  sleep 1
  asterisk -rx 'module reload res_pjsip_transport_management.so' 2>/dev/null
  sleep 1
  asterisk -rx 'dialplan reload' 2>/dev/null
  sleep 1
  echo '  ✓ PJSIP + Dialplan reloaded'
"

# ── 8. Verify ──
echo ""
echo "[8] Verifying PJSIP configuration..."

echo "  Endpoint:"
docker exec "$CONTAINER" asterisk -rx "pjsip show endpoint ${DINSTAR_USER}" 2>/dev/null | head -10 || echo "    ⚠  Not loaded yet"

echo ""
echo "  Auth:"
docker exec "$CONTAINER" asterisk -rx "pjsip show auth ${DINSTAR_USER}-auth" 2>/dev/null | head -5 || echo "    ⚠  Not loaded yet"

echo ""
echo "  Transport local_net:"
docker exec "$CONTAINER" asterisk -rx "pjsip show transport 0.0.0.0-udp" 2>/dev/null | grep -i local_net || echo "    Check manually"

echo ""
echo "  Dialplan [${CONTEXT}]:"
docker exec "$CONTAINER" asterisk -rx "dialplan show ${CONTEXT}" 2>/dev/null | head -10 || echo "    ⚠  Not loaded"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ Asterisk Trunk Configuration Complete"
echo ""
echo "  Trunk:    ${DINSTAR_USER}"
echo "  Context:  ${CONTEXT}"
echo "  Auth:     ${DINSTAR_USER} / ${DINSTAR_PASS}"
echo "  Codecs:   alaw, ulaw, gsm"
echo ""
echo "  Configure Dinstar SIP with:"
echo "    SIP Server:   ${FREEPBX_VPN_IP} (VPN direct)"
echo "    SIP Port:     ${SIP_PORT}"
echo "    Username:     ${DINSTAR_USER}"
echo "    Password:     ${DINSTAR_PASS}"
echo ""
echo "  Outbound Route (add in FreePBX GUI):"
echo "    Trunk: PJSIP/${DINSTAR_USER}"
echo "    Pattern: 0X. (local calls starting with 0)"
echo "    Pattern: +20X. (Egypt country code)"
echo ""
echo "  Test from Asterisk CLI:"
echo "    asterisk -rx 'pjsip show contacts'"
echo "    asterisk -rx 'pjsip show endpoint ${DINSTAR_USER}'"
echo "═══════════════════════════════════════════════════════"
