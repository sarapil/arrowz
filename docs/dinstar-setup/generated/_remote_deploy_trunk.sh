#!/bin/bash
###############################################################################
# Remote PJSIP trunk script — runs ON the VPS host
###############################################################################
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
    echo "  ✓ Created"
fi
'

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
    echo "  ✓ Created"
fi
'

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
    echo "  ✓ Created"
fi
'

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
    echo "  ✓ Created (match 10.10.1.2)"
fi
'

echo "[6] Creating dialplan [from-dinstar]..."
docker exec "$CONTAINER" bash -c '
EXT_FILE="/etc/asterisk/extensions_custom.conf"
if grep -q "\[from-dinstar\]" "$EXT_FILE" 2>/dev/null; then
    echo "  ✓ Already exists"
else
    cat >> "$EXT_FILE" << DEOF

; Dinstar UC2000-VE-8G — Inbound GSM Calls
[from-dinstar]
exten => _X.,1,NoOp(=== INBOUND GSM via Dinstar ===)
 same => n,NoOp(From: \${CALLERID(num)} To: \${EXTEN})
 same => n,Set(CALLERID(name)=GSM-\${CALLERID(num)})
 same => n,Set(DEST=\${EXTEN})
 same => n,GotoIf(\$[\${DIALPLAN_EXISTS(from-internal,\${DEST},1)}]?internal)
 same => n,Goto(from-internal,1155,1)
 same => n(internal),Goto(from-internal,\${DEST},1)

exten => i,1,NoOp(Invalid destination from Dinstar: \${EXTEN})
 same => n,Goto(from-internal,1155,1)

DEOF
    echo "  ✓ Created"
fi
'

echo "[7] Reloading Asterisk..."
docker exec "$CONTAINER" bash -c '
  asterisk -rx "module reload res_pjsip.so" 2>/dev/null
  sleep 1
  asterisk -rx "module reload res_pjsip_transport_management.so" 2>/dev/null
  sleep 1
  asterisk -rx "dialplan reload" 2>/dev/null
  echo "  ✓ Reloaded"
'

echo "[8] Verifying..."
echo "  Endpoint:"
docker exec "$CONTAINER" asterisk -rx "pjsip show endpoint dinstar" 2>/dev/null | head -5 || echo "    ⚠  Not loaded"
echo "  Contacts:"
docker exec "$CONTAINER" asterisk -rx "pjsip show contacts" 2>/dev/null | grep -i dinstar || echo "    ⚠  Not registered yet (waiting for Dinstar)"
echo "  Dialplan:"
docker exec "$CONTAINER" asterisk -rx "dialplan show from-dinstar" 2>/dev/null | head -5 || echo "    ⚠  Not loaded"

echo ""
echo "✅ PJSIP Trunk Deployed!"
echo "   Dinstar SIP: 10.10.1.1:51600  user: dinstar / D1nstar#VPN2026!"
