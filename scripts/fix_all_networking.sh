#!/bin/bash
# =============================================================
# Arrowz: Fix ALL Nginx proxy issues
# 1. /ws          → Asterisk HTTP (127.0.0.1:8088)
# 2. /socket.io   → Frappe socketio (127.0.0.1:9001)
# 3. /             → Frappe web     (127.0.0.1:8001)
#
# Run on VPS host: bash fix_all_networking.sh
# =============================================================
set -euo pipefail

echo "=============================================="
echo "  Arrowz Complete Networking Fix"
echo "=============================================="

# ─── Find Nginx config ───
NGINX_CONF=""
for path in \
    "/etc/nginx/sites-available/dev.tavira-group.com.conf" \
    "/etc/nginx/sites-available/dev.tavira-group.com" \
    "/etc/nginx/conf.d/dev.tavira-group.com.conf"; do
    if [ -f "$path" ]; then
        NGINX_CONF="$path"
        break
    fi
done

if [ -z "$NGINX_CONF" ]; then
    NGINX_CONF=$(grep -rl "dev.tavira-group.com" /etc/nginx/ 2>/dev/null | head -1 || echo "")
fi

if [ -z "$NGINX_CONF" ]; then
    echo "❌ Cannot find Nginx config for dev.tavira-group.com"
    exit 1
fi

echo "[INFO] Nginx config: $NGINX_CONF"
BACKUP="${NGINX_CONF}.bak.$(date +%s)"
cp "$NGINX_CONF" "$BACKUP"
echo "[INFO] Backup: $BACKUP"

# ═══════════════════════════════════════════════
# STEP 1: Detect PBX container and verify port
# ═══════════════════════════════════════════════
echo ""
echo "━━━ STEP 1: PBX Container ━━━"

PBX_CONTAINER=$(docker ps --format "{{.Names}}" | grep -iE "pbx|freepbx|asterisk" | head -1 || echo "")
ASTERISK_HOST="127.0.0.1"
ASTERISK_PORT="8088"
ASTERISK_SCHEME="http"

if [ -n "$PBX_CONTAINER" ]; then
    echo "  Container: $PBX_CONTAINER"

    # Check port 8088 mapping
    P8088=$(docker port "$PBX_CONTAINER" 8088 2>/dev/null | head -1 || echo "")
    P8089=$(docker port "$PBX_CONTAINER" 8089 2>/dev/null | head -1 || echo "")
    echo "  Port 8088: ${P8088:-NOT MAPPED}"
    echo "  Port 8089: ${P8089:-NOT MAPPED}"

    # Test plain HTTP first (preferred)
    if [ -n "$P8088" ]; then
        HP=$(echo "$P8088" | grep -oP '\d+$')
        if curl -sf --max-time 3 "http://127.0.0.1:${HP}/httpstatus" >/dev/null 2>&1; then
            ASTERISK_PORT="$HP"
            ASTERISK_SCHEME="http"
            echo "  ✅ Asterisk reachable: http://127.0.0.1:${HP}"
        fi
    fi

    # Fallback to TLS
    if [ "$ASTERISK_SCHEME" = "http" ] && ! curl -sf --max-time 3 "http://127.0.0.1:${ASTERISK_PORT}/httpstatus" >/dev/null 2>&1; then
        if [ -n "$P8089" ]; then
            HP=$(echo "$P8089" | grep -oP '\d+$')
            if curl -sfk --max-time 3 "https://127.0.0.1:${HP}/httpstatus" >/dev/null 2>&1; then
                ASTERISK_PORT="$HP"
                ASTERISK_SCHEME="https"
                echo "  ✅ Asterisk reachable: https://127.0.0.1:${HP} (TLS)"
            fi
        fi
    fi
else
    echo "  ⚠️  No PBX container found, using defaults"
fi

ASTERISK_UPSTREAM="${ASTERISK_SCHEME}://${ASTERISK_HOST}:${ASTERISK_PORT}/ws"
echo "  🎯 Asterisk upstream: $ASTERISK_UPSTREAM"

# ═══════════════════════════════════════════════
# STEP 2: Detect Frappe container ports
# ═══════════════════════════════════════════════
echo ""
echo "━━━ STEP 2: Frappe Container ━━━"

FRAPPE_CONTAINER=$(docker ps --format "{{.Names}}" | grep -iE "frappe|development" | grep -v redis | head -1 || echo "")
FRAPPE_WEB_PORT="8001"
FRAPPE_SOCKETIO_PORT="9001"

if [ -n "$FRAPPE_CONTAINER" ]; then
    echo "  Container: $FRAPPE_CONTAINER"

    # Detect web port (8000 or 8001)
    for try_port in 8001 8000; do
        PM=$(docker port "$FRAPPE_CONTAINER" "$try_port" 2>/dev/null | head -1 || echo "")
        if [ -n "$PM" ]; then
            FRAPPE_WEB_PORT=$(echo "$PM" | grep -oP '\d+$')
            echo "  Web port: container $try_port → host $FRAPPE_WEB_PORT"
            break
        fi
    done

    # Detect socketio port (9001 or 9000)
    for try_port in 9001 9000; do
        PM=$(docker port "$FRAPPE_CONTAINER" "$try_port" 2>/dev/null | head -1 || echo "")
        if [ -n "$PM" ]; then
            FRAPPE_SOCKETIO_PORT=$(echo "$PM" | grep -oP '\d+$')
            echo "  Socketio port: container $try_port → host $FRAPPE_SOCKETIO_PORT"
            break
        fi
    done

    echo "  All port mappings:"
    docker port "$FRAPPE_CONTAINER" 2>/dev/null | sed 's/^/    /'
else
    echo "  ⚠️  No Frappe container found, using defaults (8001/9001)"
fi

echo "  🎯 Frappe web: 127.0.0.1:$FRAPPE_WEB_PORT"
echo "  🎯 Frappe socketio: 127.0.0.1:$FRAPPE_SOCKETIO_PORT"

# ═══════════════════════════════════════════════
# STEP 3: Generate correct Nginx config
# ═══════════════════════════════════════════════
echo ""
echo "━━━ STEP 3: Generating Nginx Config ━━━"

# Build SSL directives for Asterisk if needed
PROXY_SSL=""
if [ "$ASTERISK_SCHEME" = "https" ]; then
    PROXY_SSL="
        proxy_ssl_verify off;
        proxy_ssl_server_name off;"
fi

# Use Python to precisely edit the config
python3 - "$NGINX_CONF" "$ASTERISK_UPSTREAM" "$FRAPPE_WEB_PORT" "$FRAPPE_SOCKETIO_PORT" "$ASTERISK_SCHEME" << 'PYEOF'
import re, sys

nginx_conf = sys.argv[1]
asterisk_upstream = sys.argv[2]
frappe_web_port = sys.argv[3]
frappe_sio_port = sys.argv[4]
asterisk_scheme = sys.argv[5]

with open(nginx_conf, "r") as f:
    content = f.read()

original = content
changes = []

# ═══ Build location /ws block ═══
ssl_directives = ""
if asterisk_scheme == "https":
    ssl_directives = """
        proxy_ssl_verify off;
        proxy_ssl_server_name off;"""

ws_block = f"""location /ws {{
        proxy_pass {asterisk_upstream};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;{ssl_directives}

        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_buffering off;
        proxy_cache off;
    }}"""

# Replace or insert /ws block
ws_pattern = r'location\s+/ws\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}'
if re.search(ws_pattern, content):
    content = re.sub(ws_pattern, ws_block, content, count=1)
    changes.append("Replaced location /ws")
elif "location / {" in content:
    content = content.replace("location / {", ws_block + "\n\n    location / {", 1)
    changes.append("Inserted location /ws")

# ═══ Fix /socket.io block ═══
# Find the socket.io location block specifically and fix its proxy_pass
sio_block_pattern = r'(location\s+/socket\.io\s*\{[^}]*?proxy_pass\s+http://127\.0\.0\.1:)\d+([^}]*\})'
sio_match = re.search(sio_block_pattern, content, re.DOTALL)
if sio_match:
    old_full = sio_match.group(0)
    old_port = re.search(r'proxy_pass\s+http://127\.0\.0\.1:(\d+)', old_full).group(1)
    if old_port != frappe_sio_port:
        new_block = re.sub(
            r'(proxy_pass\s+http://127\.0\.0\.1:)\d+',
            rf'\g<1>{frappe_sio_port}',
            old_full
        )
        content = content.replace(old_full, new_block)
        changes.append(f"Fixed /socket.io port: {old_port} → {frappe_sio_port}")
    else:
        changes.append(f"/socket.io port already correct: {frappe_sio_port}")
else:
    changes.append("No /socket.io block found (may need manual check)")

# ═══ Fix main location / block ═══
# Find the MAIN location / block (not /ws, not /socket.io) and fix its proxy_pass
# This is trickier — we need to find "location / {" specifically
lines = content.split('\n')
in_main_location = False
brace_depth = 0
main_loc_start = -1

for i, line in enumerate(lines):
    stripped = line.strip()
    # Match "location / {" but not "location /ws" or "location /socket.io"
    if re.match(r'location\s+/\s*\{', stripped) and '/ws' not in stripped and '/socket' not in stripped:
        in_main_location = True
        main_loc_start = i
        brace_depth = 1
        continue
    if in_main_location:
        brace_depth += stripped.count('{') - stripped.count('}')
        # Fix proxy_pass in main location block
        pp_match = re.match(r'(\s*proxy_pass\s+http://127\.0\.0\.1:)(\d+)(.*)', line)
        if pp_match and pp_match.group(2) != frappe_web_port:
            old_port = pp_match.group(2)
            lines[i] = f"{pp_match.group(1)}{frappe_web_port}{pp_match.group(3)}"
            changes.append(f"Fixed location / port: {old_port} → {frappe_web_port}")
        if brace_depth <= 0:
            in_main_location = False

content = '\n'.join(lines)

# ═══ Ensure map block exists ═══
if 'map $http_upgrade $connection_upgrade' not in content:
    map_block = """map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

"""
    # Insert before first 'server {' block
    content = re.sub(r'(server\s*\{)', map_block + r'\1', content, count=1)
    changes.append("Added map $http_upgrade block")

if content != original:
    with open(nginx_conf, "w") as f:
        f.write(content)

for c in changes:
    print(f"  ✅ {c}")

if content == original:
    print("  ℹ️  No changes needed")
PYEOF

# ═══════════════════════════════════════════════
# STEP 4: Test and Reload
# ═══════════════════════════════════════════════
echo ""
echo "━━━ STEP 4: Test & Reload ━━━"

if nginx -t 2>&1; then
    systemctl reload nginx
    echo "  ✅ Nginx reloaded"
else
    echo "  ❌ Config test FAILED — restoring backup"
    cp "$BACKUP" "$NGINX_CONF"
    nginx -t && systemctl reload nginx
    echo "  ↩️  Restored from backup"
    exit 1
fi

# ═══════════════════════════════════════════════
# STEP 5: Verification
# ═══════════════════════════════════════════════
echo ""
echo "━━━ VERIFICATION ━━━"
sleep 1

# Test /ws (Asterisk WebSocket)
echo -n "  /ws (Asterisk):    "
WS_CODE=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 5 \
    -H "Upgrade: websocket" \
    -H "Connection: Upgrade" \
    -H "Sec-WebSocket-Key: dGVzdA==" \
    -H "Sec-WebSocket-Version: 13" \
    "https://dev.tavira-group.com/ws" 2>/dev/null || echo "000")
case "$WS_CODE" in
    101) echo "✅ 101 Switching Protocols — PERFECT" ;;
    200) echo "✅ 200 — Asterisk reachable" ;;
    400) echo "✅ 400 — Asterisk rejects curl, browser will work" ;;
    426) echo "✅ 426 — Upgrade Required, normal for curl test" ;;
    502) echo "❌ 502 — Upstream unreachable. Check: curl http://127.0.0.1:${ASTERISK_PORT}/httpstatus" ;;
    000) echo "❌ Connection failed" ;;
    *)   echo "⚠️  HTTP $WS_CODE" ;;
esac

# Test /socket.io (Frappe)
echo -n "  /socket.io:        "
SIO_CODE=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 5 \
    "https://dev.tavira-group.com/socket.io/?EIO=4&transport=polling" 2>/dev/null || echo "000")
case "$SIO_CODE" in
    200) echo "✅ 200 — Socket.io working" ;;
    400) echo "⚠️  400 — Running but needs valid session" ;;
    502) echo "❌ 502 — Socketio unreachable on port $FRAPPE_SOCKETIO_PORT" ;;
    000) echo "❌ Connection failed" ;;
    *)   echo "⚠️  HTTP $SIO_CODE" ;;
esac

# Test / (Frappe web)
echo -n "  / (Frappe web):    "
WEB_CODE=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 5 \
    "https://dev.tavira-group.com/" 2>/dev/null || echo "000")
case "$WEB_CODE" in
    200) echo "✅ 200 — Frappe web working" ;;
    301|302) echo "✅ ${WEB_CODE} redirect — working" ;;
    502) echo "❌ 502 — Frappe web unreachable on port $FRAPPE_WEB_PORT" ;;
    000) echo "❌ Connection failed" ;;
    *)   echo "⚠️  HTTP $WEB_CODE" ;;
esac

# Show final port summary
echo ""
echo "━━━ FINAL CONFIG ━━━"
echo ""
grep -E "proxy_pass|location" "$NGINX_CONF" | grep -v "^\s*#" | head -20 | sed 's/^/  /'

echo ""
echo "=============================================="
echo "  Summary"
echo "=============================================="
echo "  /ws         → ${ASTERISK_SCHEME}://127.0.0.1:${ASTERISK_PORT}/ws  (Asterisk WebRTC)"
echo "  /socket.io  → http://127.0.0.1:${FRAPPE_SOCKETIO_PORT}  (Frappe realtime)"
echo "  /           → http://127.0.0.1:${FRAPPE_WEB_PORT}  (Frappe web)"
echo "  Config: $NGINX_CONF"
echo "  Backup: $BACKUP"
echo ""
echo "  Next: Hard-refresh browser (Ctrl+Shift+R)"
echo "=============================================="
