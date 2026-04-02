#!/bin/bash
# ==============================================================
# Dinstar UC2000-VE-8G — GSM Routing Remote Deploy Script
# Runs INSIDE FreePBX container
# ==============================================================
# Creates:
#   - 8 PJSIP endpoints (gsm-port1 through gsm-port8)
#   - Inbound routing: each port → extension 7001-7008
#   - Outbound routing: round-robin across all available ports
# ==============================================================

set -e

A="/etc/asterisk"
NUM_PORTS=8
BASE_EXT=7000  # Port N → Extension 7000+N (7001-7008)

echo "╔══════════════════════════════════════════════╗"
echo "║  Dinstar GSM Gateway — 8-Port PJSIP Setup   ║"
echo "╚══════════════════════════════════════════════╝"

# ==============================================================
# STEP 1: Backup
# ==============================================================
echo ""
echo "=== [1/5] Backing up configs ==="
BK="/root/gsm-backup-$(date +%Y%m%d%H%M%S)"
mkdir -p "$BK"
for f in pjsip.endpoint_custom_post.conf pjsip.auth_custom_post.conf \
         pjsip.aor_custom_post.conf pjsip.identify_custom_post.conf \
         extensions_custom.conf pjsip.transports_custom_post.conf; do
    cp "$A/$f" "$BK/$f" 2>/dev/null || true
done
echo "  Backed up to $BK"

# ==============================================================
# STEP 2: Remove old dinstar entries (keep non-dinstar entries)
# ==============================================================
echo ""
echo "=== [2/5] Removing old dinstar entries ==="

# Remove [dinstar*] sections from PJSIP files (keep everything else like [2210])
for f in pjsip.endpoint_custom_post.conf pjsip.auth_custom_post.conf \
         pjsip.aor_custom_post.conf pjsip.identify_custom_post.conf; do
    awk '
        /^\[dinstar/ { skip=1; next }
        /^\[gsm-port/ { skip=1; next }
        /^\[/ { skip=0 }
        /^; =+ *$/ && skip { next }
        /^; Dinstar/ && skip { next }
        !skip { print }
    ' "$A/$f" > "$A/$f.tmp" && mv "$A/$f.tmp" "$A/$f"
done

# Remove old dialplan (from-dinstar context and any gsm contexts)
awk '
    /^\[from-dinstar\]/ { skip=1; next }
    /^\[from-gsm-inbound\]/ { skip=1; next }
    /^\[gsm-outbound\]/ { skip=1; next }
    /^; === ARROWZ GSM/ { skip=1; next }
    /^\[/ { skip=0 }
    /^; =+ *$/ && skip { next }
    /^; Dinstar/ && skip { next }
    !skip { print }
' "$A/extensions_custom.conf" > "$A/extensions_custom.conf.tmp"
mv "$A/extensions_custom.conf.tmp" "$A/extensions_custom.conf"

# Also remove any gsm-outbound line from from-internal-custom
sed -i '/gsm-outbound/d' "$A/extensions_custom.conf"

echo "  Old entries removed"

# ==============================================================
# STEP 3: Write PJSIP Configs
# ==============================================================
echo ""
echo "=== [3/5] Writing PJSIP configs for 8 GSM ports ==="

# --- ENDPOINTS ---
cat >> "$A/pjsip.endpoint_custom_post.conf" << 'MARKER'

; ===========================================================================
; Dinstar UC2000-VE-8G — 8 GSM Port Endpoints
; Each port registers independently for per-port routing
; Inbound: port N → extension 700N
; Outbound: round-robin across all registered ports
; ===========================================================================
MARKER

for i in $(seq 1 $NUM_PORTS); do
    EXT=$((BASE_EXT + i))
    cat >> "$A/pjsip.endpoint_custom_post.conf" << EOF
[gsm-port${i}]
type=endpoint
context=from-gsm-inbound
disallow=all
allow=alaw
allow=ulaw
allow=gsm
auth=gsm-port${i}-auth
aors=gsm-port${i}
direct_media=no
force_rport=yes
rewrite_contact=yes
rtp_symmetric=yes
ice_support=no
media_encryption=no
identify_by=username,auth_username
trust_id_inbound=yes
send_rpid=yes
dtmf_mode=rfc4733
rtp_keepalive=15
rtp_timeout=60
callerid=GSM-${i} <${EXT}>
media_address=10.10.1.1

EOF
done
echo "  $NUM_PORTS endpoints written"

# --- AUTHS ---
# Passwords: Gsm{N}@Arwz2026
cat >> "$A/pjsip.auth_custom_post.conf" << 'MARKER'

; ===========================================================================
; Dinstar UC2000-VE-8G — GSM Port Authentication
; ===========================================================================
MARKER

for i in $(seq 1 $NUM_PORTS); do
    cat >> "$A/pjsip.auth_custom_post.conf" << EOF
[gsm-port${i}-auth]
type=auth
auth_type=userpass
username=gsm-port${i}
password=Gsm${i}@Arwz2026

EOF
done
echo "  $NUM_PORTS auth entries written"

# --- AORS ---
cat >> "$A/pjsip.aor_custom_post.conf" << 'MARKER'

; ===========================================================================
; Dinstar UC2000-VE-8G — GSM Port AORs (Address of Record)
; ===========================================================================
MARKER

for i in $(seq 1 $NUM_PORTS); do
    cat >> "$A/pjsip.aor_custom_post.conf" << EOF
[gsm-port${i}]
type=aor
max_contacts=1
qualify_frequency=30
default_expiration=120
minimum_expiration=60
remove_existing=yes

EOF
done
echo "  $NUM_PORTS AOR entries written"

# ==============================================================
# STEP 4: Write Dialplan
# ==============================================================
echo ""
echo "=== [4/5] Writing dialplan ==="

cat >> "$A/extensions_custom.conf" << 'DIALPLAN'

; ===========================================================================
; Dinstar UC2000-VE-8G — GSM Gateway Routing
; ===========================================================================
;
; INBOUND:  GSM port N → Extension 700N (each SIM has its own extension)
; OUTBOUND: Any extension → Round-robin across all available GSM ports
;
; Port-Extension Mapping:
;   Port 1 (gsm-port1) → Extension 7001
;   Port 2 (gsm-port2) → Extension 7002
;   Port 3 (gsm-port3) → Extension 7003
;   Port 4 (gsm-port4) → Extension 7004
;   Port 5 (gsm-port5) → Extension 7005
;   Port 6 (gsm-port6) → Extension 7006
;   Port 7 (gsm-port7) → Extension 7007
;   Port 8 (gsm-port8) → Extension 7008
; ===========================================================================

; -------------------------------------------------------------------
; INBOUND: Incoming GSM calls → route to owner's extension
; -------------------------------------------------------------------
[from-gsm-inbound]
; Calls with a dialed number (DID)
exten => _X.,1,NoOp(=== GSM INBOUND: ${EXTEN} via ${CHANNEL(endpoint)} ===)
 same => n,Set(PORT=${CHANNEL(endpoint):8})
 same => n,Set(GSM_EXT=$[7000 + ${PORT}])
 same => n,NoOp(Port ${PORT} → Extension ${GSM_EXT})
 same => n,Set(CALLERID(name)=GSM-${PORT}:${CALLERID(num)})
 same => n,Set(__FROM_GSM_PORT=${PORT})
 same => n,Dial(PJSIP/${GSM_EXT},30,tT)
 same => n,GotoIf($["${DIALSTATUS}"="BUSY"]?busy:unavail)
 same => n(busy),VoiceMail(${GSM_EXT},b)
 same => n,Hangup()
 same => n(unavail),VoiceMail(${GSM_EXT},u)
 same => n,Hangup()

; Calls without DID (empty extension)
exten => s,1,NoOp(=== GSM INBOUND (no DID) via ${CHANNEL(endpoint)} ===)
 same => n,Set(PORT=${CHANNEL(endpoint):8})
 same => n,Set(GSM_EXT=$[7000 + ${PORT}])
 same => n,Set(CALLERID(name)=GSM-${PORT}:${CALLERID(num)})
 same => n,Dial(PJSIP/${GSM_EXT},30,tT)
 same => n,VoiceMail(${GSM_EXT},u)
 same => n,Hangup()

; -------------------------------------------------------------------
; OUTBOUND: Round-robin GSM port selection
; Distributes outgoing calls fairly across all registered ports
; If a port is busy/unavailable, tries the next one (up to all 8)
; -------------------------------------------------------------------
[gsm-outbound]
exten => _X.,1,NoOp(=== GSM OUTBOUND: ${EXTEN} from ${CALLERID(num)} ===)
 same => n,Set(RR=${DB(gsm/rr)})
 same => n,Set(RR=${IF($["${RR}"=""]?1:${RR})})
 same => n,Set(DB(gsm/rr)=$[$[${RR}] % 8 + 1])
 same => n,Set(PORT=${RR})
 same => n,Set(TRIED=0)
 same => n(try),NoOp(--- Trying gsm-port${PORT} [attempt $[${TRIED}+1]/8] ---)
 same => n,Dial(PJSIP/${EXTEN}@gsm-port${PORT},60,T)
 same => n,NoOp(Result: ${DIALSTATUS})
 same => n,GotoIf($["${DIALSTATUS}"="CHANUNAVAIL"]?next)
 same => n,GotoIf($["${DIALSTATUS}"="CONGESTION"]?next)
 same => n,GotoIf($["${DIALSTATUS}"="BUSY"]?next)
 same => n,Hangup()
 same => n(next),Set(PORT=$[$[${PORT}] % 8 + 1])
 same => n,Set(TRIED=$[${TRIED} + 1])
 same => n,GotoIf($[${TRIED} < 8]?try)
 same => n,Playback(all-circuits-busy-now)
 same => n,Hangup()

; -------------------------------------------------------------------
; OUTBOUND ROUTE: External numbers → GSM gateway
; Patterns: Egyptian mobile (01X), landline (0X), international (00X)
; -------------------------------------------------------------------
[from-internal-custom]
; Route external calls (starting with 0) through GSM gateway
exten => _0X.,1,Goto(gsm-outbound,${EXTEN},1)

DIALPLAN

echo "  Dialplan written (inbound + outbound + route)"

# ==============================================================
# STEP 5: Reload Asterisk
# ==============================================================
echo ""
echo "=== [5/5] Reloading Asterisk ==="

# Use fwconsole if available, fallback to asterisk CLI
if command -v fwconsole &>/dev/null; then
    fwconsole r 2>/dev/null || true
    sleep 2
fi
asterisk -rx "core reload" 2>/dev/null || true
sleep 3

echo ""
echo "=== Verification ==="
echo ""
echo "--- PJSIP Endpoints ---"
asterisk -rx "pjsip show endpoints" 2>/dev/null | grep -E "Endpoint:|gsm-port" | head -20
echo ""
echo "--- Dialplan: from-gsm-inbound ---"
asterisk -rx "dialplan show from-gsm-inbound" 2>/dev/null | head -5
echo ""
echo "--- Dialplan: gsm-outbound ---"
asterisk -rx "dialplan show gsm-outbound" 2>/dev/null | head -5
echo ""

echo "╔══════════════════════════════════════════════╗"
echo "║              DEPLOYMENT COMPLETE             ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  8 GSM Port Endpoints: gsm-port1..8         ║"
echo "║  Extensions: 7001-7008                       ║"
echo "║  Outbound: Round-robin via gsm-outbound      ║"
echo "║  SIP Port: 51600 (VPN: 10.10.1.1)           ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  Port Credentials:                           ║"
for i in $(seq 1 $NUM_PORTS); do
    printf "║  Port %d: gsm-port%-2d / Gsm%d@Arwz2026       ║\n" $i $i $i
done
echo "╚══════════════════════════════════════════════╝"
