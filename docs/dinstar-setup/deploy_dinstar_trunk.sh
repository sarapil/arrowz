#!/bin/bash
###############################################################################
# Deploy Dinstar PJSIP Trunk to FreePBX Container
# ================================================
# Run this FROM the Frappe container. SSHs to VPS host → docker exec.
#
# Usage:
#   bash deploy_dinstar_trunk.sh
###############################################################################

set -euo pipefail

VPS_HOST="157.173.125.136"
VPS_PORT="1352"
VPS_USER="root"
CONTAINER="initpbx-freepbx-1"

DINSTAR_USER="dinstar"
DINSTAR_PASS='D1nstar#VPN2026!'
DINSTAR_VPN_IP="10.10.1.2"
FREEPBX_VPN_IP="10.10.1.1"
SIP_PORT="51600"
CONTEXT="from-dinstar"
DEFAULT_EXT="1155"

SSH_CMD="ssh -o StrictHostKeyChecking=no -p ${VPS_PORT} ${VPS_USER}@${VPS_HOST}"

echo "═══════════════════════════════════════════════════════"
echo "  Deploying Dinstar PJSIP Trunk (Direct VPN)"
echo "═══════════════════════════════════════════════════════"
echo ""

${SSH_CMD} << 'REMOTE_SCRIPT'
set -e
CONTAINER="initpbx-freepbx-1"

echo "[1] Adding VPN to transport local_net..."
docker exec "$CONTAINER" bash -c '
CUSTOM_POST="/etc/asterisk/pjsip.transports_custom_post.conf"
if grep -q "10.10.1.0" "$CUSTOM_POST" 2>/dev/null; then
    echo "  ✓ Already configured"
else
    cat >> "$CUSTOM_POST" << TEOF

; Dinstar VPN — Transport Override
[0.0.0.0-udp](+)
local_net=10.10.1.0/24
local_net=10.10.0.0/24

TEOF
    echo "  ✓ Added VPN subnets"
fi
'

echo ""
echo "[2] Creating PJSIP auth..."
docker exec "$CONTAINER" bash -c '
AUTH_FILE="/etc/asterisk/pjsip.auth_custom_post.conf"
if grep -q "dinstar-auth" "$AUTH_FILE" 2>/dev/null; then
    echo "  ✓ Already exists"
else
    cat >> "$AUTH_FILE" << AEOF

[dinstar-auth]
type=auth
auth_type=userpass
username=dinstar
password=D1nstar#VPN2026!

AEOF
    echo "  ✓ Auth created"
fi
'

echo ""
echo "[3] Creating PJSIP AOR..."
docker exec "$CONTAINER" bash -c '
AOR_FILE="/etc/asterisk/pjsip.aor_custom_post.conf"
if grep -q "\[dinstar\]" "$AOR_FILE" 2>/dev/null; then
    echo "  ✓ Already exists"
else
    cat >> "$AOR_FILE" << OEOF

[dinstar]
type=aor
max_contacts=8
qualify_frequency=30
default_expiration=120
minimum_expiration=60

OEOF
    echo "  ✓ AOR created"
fi
'

echo ""
echo "[4] Creating PJSIP endpoint..."
docker exec "$CONTAINER" bash -c '
EP_FILE="/etc/asterisk/pjsip.endpoint_custom_post.conf"
if grep -q "\[dinstar\]" "$EP_FILE" 2>/dev/null; then
    echo "  ✓ Already exists"
else
    cat >> "$EP_FILE" << EEOF

; Dinstar UC2000-VE-8G GSM Gateway — Direct VPN
[dinstar]
type=endpoint
context=from-dinstar
disallow=all
allow=alaw
allow=ulaw
allow=gsm
auth=dinstar-auth
aors=dinstar
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
rtp_keepalive=15
rtp_timeout=60
rtp_timeout_hold=300
callerid=GSM Gateway <dinstar>
media_address=10.10.1.1

EEOF
    echo "  ✓ Endpoint created"
fi
'

echo ""
echo "[5] Creating PJSIP identify..."
docker exec "$CONTAINER" bash -c '
ID_FILE="/etc/asterisk/pjsip.identify_custom_post.conf"
if grep -q "dinstar-identify" "$ID_FILE" 2>/dev/null; then
    echo "  ✓ Already exists"
else
    cat >> "$ID_FILE" << IEOF

[dinstar-identify]
type=identify
endpoint=dinstar
match=10.10.1.2/32

IEOF
    echo "  ✓ Identify created (match 10.10.1.2)"
fi
'

echo ""
echo "[6] Creating inbound dialplan [from-dinstar]..."
docker exec "$CONTAINER" bash -c '
EXT_FILE="/etc/asterisk/extensions_custom.conf"
if grep -q "\[from-dinstar\]" "$EXT_FILE" 2>/dev/null; then
    echo "  ✓ Already exists"
else
    cat >> "$EXT_FILE" << DEOF

; Dinstar UC2000-VE-8G — Inbound GSM Calls
[from-dinstar]
exten => _X.,1,NoOp(=== INBOUND GSM via Dinstar ===)
 same => n,NoOp(From: ${CALLERID(num)} To: ${EXTEN})
 same => n,Set(CALLERID(name)=GSM-${CALLERID(num)})
 same => n,Set(DEST=${EXTEN})
 same => n,GotoIf($[${DIALPLAN_EXISTS(from-internal,${DEST},1)}]?internal)
 same => n,Goto(from-internal,1155,1)
 same => n(internal),Goto(from-internal,${DEST},1)

exten => i,1,NoOp(Invalid destination from Dinstar: ${EXTEN})
 same => n,Goto(from-internal,1155,1)

DEOF
    echo "  ✓ Context created"
fi
'

echo ""
echo "[7] Reloading Asterisk..."
docker exec "$CONTAINER" bash -c '
  asterisk -rx "module reload res_pjsip.so" 2>/dev/null
  sleep 1
  asterisk -rx "module reload res_pjsip_transport_management.so" 2>/dev/null
  sleep 1
  asterisk -rx "dialplan reload" 2>/dev/null
  echo "  ✓ Reloaded"
'

echo ""
echo "[8] Verifying..."
echo "  Endpoint:"
docker exec "$CONTAINER" asterisk -rx "pjsip show endpoint dinstar" 2>/dev/null | head -5 || echo "    ⚠  Not loaded"
echo ""
echo "  Auth:"
docker exec "$CONTAINER" asterisk -rx "pjsip show auth dinstar-auth" 2>/dev/null | head -3 || echo "    ⚠  Not loaded"
echo ""
echo "  Dialplan:"
docker exec "$CONTAINER" asterisk -rx "dialplan show from-dinstar" 2>/dev/null | head -5 || echo "    ⚠  Not loaded"

echo ""
echo "  ✅ PJSIP Trunk Deployed!"
echo "  Dinstar SIP: 10.10.1.1:51600  user: dinstar"
REMOTE_SCRIPT

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  ✅ Trunk Configuration Complete"
echo ""
echo "  Configure Dinstar SIP:"
echo "    Server: ${FREEPBX_VPN_IP}  Port: ${SIP_PORT}"
echo "    Username: ${DINSTAR_USER}  Password: ${DINSTAR_PASS}"
echo "═══════════════════════════════════════════════════════"
