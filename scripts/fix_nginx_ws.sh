#!/bin/bash
# =============================================================================
# Arrowz — Fix Nginx WebSocket Proxy for dev.tavira-group.com
# =============================================================================
# Run this script ON THE VPS HOST (157.173.125.136) via SSH
#
# Usage:
#   ssh root@157.173.125.136 'bash -s' < fix_nginx_ws.sh
#   — OR —
#   scp fix_nginx_ws.sh root@157.173.125.136:/tmp/ && ssh root@157.173.125.136 bash /tmp/fix_nginx_ws.sh
# =============================================================================

set -euo pipefail

echo "=== Arrowz Nginx WebSocket Proxy Fix ==="
echo ""

# 1. Find the PBX container's current IP
echo "--- Step 1: Finding PBX container IP ---"
PBX_CONTAINER=$(docker ps --filter "name=freepbx\|initpbx\|pbx" --format "{{.Names}}" | head -1)

if [ -z "$PBX_CONTAINER" ]; then
    echo "❌ No PBX container found. Looking for containers with port 8088..."
    PBX_CONTAINER=$(docker ps --format "{{.Names}}\t{{.Ports}}" | grep 8088 | awk '{print $1}' | head -1)
fi

if [ -z "$PBX_CONTAINER" ]; then
    echo "❌ Could not find PBX container. Listing all containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "Set PBX_CONTAINER manually and re-run, or provide IP below:"
    read -p "Enter PBX container name or IP: " PBX_INPUT
    if [[ "$PBX_INPUT" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        PBX_IP="$PBX_INPUT"
    else
        PBX_CONTAINER="$PBX_INPUT"
    fi
fi

if [ -z "${PBX_IP:-}" ]; then
    PBX_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$PBX_CONTAINER" 2>/dev/null)
fi

echo "✅ PBX Container: ${PBX_CONTAINER:-direct-ip}"
echo "✅ PBX IP: $PBX_IP"

# 2. Verify Asterisk HTTP is reachable
echo ""
echo "--- Step 2: Testing Asterisk HTTP (port 8088) ---"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "http://${PBX_IP}:8088/httpstatus" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Asterisk HTTP reachable at http://${PBX_IP}:8088"
elif [ "$HTTP_CODE" = "000" ]; then
    echo "❌ Cannot reach http://${PBX_IP}:8088 — Asterisk HTTP not running or IP wrong"
    echo "   Check: docker exec $PBX_CONTAINER asterisk -rx 'http show status'"
    exit 1
else
    echo "⚠️  Asterisk HTTP returned $HTTP_CODE at http://${PBX_IP}:8088"
fi

# 3. Find the Nginx config file
echo ""
echo "--- Step 3: Updating Nginx config ---"
NGINX_CONF=""
for f in /etc/nginx/sites-enabled/dev.tavira-group.com \
         /etc/nginx/sites-available/dev.tavira-group.com \
         /etc/nginx/conf.d/dev.tavira-group.com.conf \
         /etc/nginx/sites-enabled/dev-tavira \
         /etc/nginx/conf.d/dev-tavira.conf; do
    if [ -f "$f" ]; then
        NGINX_CONF="$f"
        break
    fi
done

if [ -z "$NGINX_CONF" ]; then
    echo "Looking for Nginx config by content..."
    NGINX_CONF=$(grep -rl "dev.tavira-group.com" /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null | head -1)
fi

if [ -z "$NGINX_CONF" ]; then
    echo "❌ Cannot find Nginx config for dev.tavira-group.com"
    echo "   Checking all Nginx configs..."
    grep -rl "server_name" /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null | while read f; do
        echo "  $f: $(grep server_name "$f" | head -1)"
    done
    exit 1
fi

echo "✅ Found config: $NGINX_CONF"

# 4. Check if /ws location already exists
if grep -q "location /ws" "$NGINX_CONF"; then
    echo "ℹ️  location /ws already exists in config. Updating proxy_pass target..."
    # Update the proxy_pass line in the /ws location block
    sed -i "/location \/ws/,/}/ s|proxy_pass http://[^;]*;|proxy_pass http://${PBX_IP}:8088;|" "$NGINX_CONF"
else
    echo "ℹ️  Adding location /ws block..."
    # Insert before the last closing brace of the HTTPS server block
    # Find the line with the last `}` in the file (closing the server block)
    cat >> /tmp/nginx_ws_block.conf <<WSEOF

    # ==================================================================
    # Asterisk WebSocket Proxy (Arrowz WebRTC Softphone)
    # ------------------------------------------------------------------
    # Proxies WSS (port 443) → Asterisk plain HTTP (port 8088)
    # Nginx terminates SSL. Asterisk gets plain WebSocket.
    # This makes VoIP traffic indistinguishable from HTTPS (DPI-evasion)
    # ==================================================================
    location /ws {
        proxy_pass http://${PBX_IP}:8088/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_connect_timeout 5s;
    }
WSEOF

    # Insert the block before the last } in the HTTPS server block
    # This is a simplistic approach - manual verification recommended
    LAST_BRACE=$(grep -n "^}" "$NGINX_CONF" | tail -1 | cut -d: -f1)
    if [ -n "$LAST_BRACE" ]; then
        sed -i "${LAST_BRACE}r /tmp/nginx_ws_block.conf" "$NGINX_CONF"
        echo "✅ Inserted /ws location block at line $LAST_BRACE"
    else
        echo "❌ Could not find insertion point. Add manually:"
        cat /tmp/nginx_ws_block.conf
    fi
    rm -f /tmp/nginx_ws_block.conf
fi

# 5. Test Nginx config
echo ""
echo "--- Step 4: Testing Nginx config ---"
nginx -t 2>&1

# 6. Reload Nginx
echo ""
echo "--- Step 5: Reloading Nginx ---"
systemctl reload nginx
echo "✅ Nginx reloaded"

# 7. Test the /ws endpoint
echo ""
echo "--- Step 6: Testing wss://dev.tavira-group.com/ws ---"
sleep 1
WS_CODE=$(curl -sSk -o /dev/null -w "%{http_code}" -H "Upgrade: websocket" -H "Connection: Upgrade" "https://dev.tavira-group.com/ws" 2>/dev/null)
echo "Response code: $WS_CODE"

if [ "$WS_CODE" = "101" ] || [ "$WS_CODE" = "426" ]; then
    echo "✅ WebSocket proxy working! (101=upgrade success, 426=upgrade required but reachable)"
elif [ "$WS_CODE" = "400" ]; then
    echo "✅ WebSocket proxy working! Asterisk returned 400 (expected for non-WS curl request)"
elif [ "$WS_CODE" = "502" ]; then
    echo "❌ Still 502 — Nginx cannot reach Asterisk at http://${PBX_IP}:8088"
    echo "   Check: docker exec $PBX_CONTAINER asterisk -rx 'http show status'"
    echo "   Check: curl -v http://${PBX_IP}:8088/httpstatus"
else
    echo "⚠️  Got HTTP $WS_CODE — may need further investigation"
fi

echo ""
echo "=== Done ==="
echo "PBX IP: $PBX_IP"
echo "Nginx conf: $NGINX_CONF"
echo ""
echo "If the PBX container restarts and gets a new IP, re-run this script."
echo "For a permanent fix, use Docker network alias or container hostname."
