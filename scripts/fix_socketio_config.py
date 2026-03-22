#!/usr/bin/env python3
"""
Fix Frappe Socket.io client connection for production behind Nginx.

The browser tries to connect to dev.tavira-group.com:9001 directly,
but port 9001 is only accessible inside Docker — it should go through
Nginx on port 443 which proxies /socket.io to the container.

Usage (inside Frappe container):
  cd /home/frappe/frappe-bench
  python apps/arrowz/scripts/fix_socketio_config.py
"""
import json
import os
import sys
import glob
import shutil

BENCH_PATH = os.environ.get("BENCH_PATH", "/home/frappe/frappe-bench")

# Also check workspace paths
SEARCH_DIRS = [
    os.path.join(BENCH_PATH, "sites"),
    "/workspace/development/frappe-bench/sites",
]

site_configs = []
for sdir in SEARCH_DIRS:
    if os.path.isdir(sdir):
        found = glob.glob(os.path.join(sdir, "*/site_config.json"))
        site_configs.extend([
            p for p in found
            if "assets" not in p and "common" not in p
        ])
        if site_configs:
            break

if not site_configs:
    print("❌ No site_config.json found!")
    print(f"   Searched: {SEARCH_DIRS}")
    sys.exit(1)

for site_config_path in site_configs:
    site_name = os.path.basename(os.path.dirname(site_config_path))
    print(f"\n━━━ Site: {site_name} ━━━")
    print(f"  Config: {site_config_path}")

    with open(site_config_path, "r") as f:
        config = json.load(f)

    changes = {}

    # ─── Fix socketio_port ───
    # When behind Nginx (production), the browser should connect to
    # the SAME port as the page (443 for HTTPS). Nginx then proxies
    # /socket.io internally to the Frappe socketio process.
    #
    # For local development (bench start), socketio_port=9001 is correct.
    # But when accessed via dev.tavira-group.com (Nginx), it must be 443.
    #
    # Solution: Set socketio_port=443. This makes the browser connect to
    # wss://dev.tavira-group.com:443/socket.io which hits Nginx.
    current_port = config.get("socketio_port")
    if current_port and str(current_port) == "443":
        print(f"  ✅ socketio_port already correct: 443")
    elif current_port:
        changes["socketio_port_old"] = current_port
        config["socketio_port"] = 443
        print(f"  ✅ socketio_port: {current_port} → 443")
    else:
        config["socketio_port"] = 443
        changes["socketio_port_old"] = "NOT SET"
        print(f"  ✅ socketio_port: not set → 443")

    # ─── DO NOT change host_name ───
    # host_name = "http://dev.localhost:8000" is the INTERNAL address
    # used by bench/gunicorn. Changing it breaks bench operations.
    # The Nginx proxy handles the external domain mapping.
    host_name = config.get("host_name", "")
    print(f"  ℹ️  host_name kept as-is: {host_name} (internal bench address)")

    # ─── Show warning about developer_mode ───
    if config.get("developer_mode"):
        print(f"  ℹ️  developer_mode=1 — socketio_port=443 overrides direct port")
        print(f"      Local 'bench start' still works (socketio binds to 9001 inside container)")
        print(f"      External access via Nginx uses port 443 → /socket.io → 127.0.0.1:9001")

    if changes:
        # Backup (only first time)
        backup_path = site_config_path + ".bak.socketio"
        if not os.path.exists(backup_path):
            shutil.copy2(site_config_path, backup_path)
            print(f"  📋 Backup: {backup_path}")

        with open(site_config_path, "w") as f:
            json.dump(config, f, indent=1, sort_keys=True)

        print(f"  ✅ Config updated")
        print(f"  ⚠️  Run: bench --site {site_name} clear-cache")
    else:
        print(f"  ℹ️  No changes needed")

    # Show current relevant settings
    print(f"\n  Current config:")
    for key in ("socketio_port", "host_name", "developer_mode",
                "webserver_port", "db_name"):
        if key in config:
            val = config[key]
            if key == "db_name":
                val = val[:4] + "..." # Truncate sensitive info
            print(f"    {key}: {val}")

print("\n✅ Done")
print("\nPort Architecture:")
print("  Browser → wss://dev.tavira-group.com:443/socket.io")
print("       → Nginx proxy_pass → http://127.0.0.1:9001")
print("       → Frappe socketio (inside Docker container)")
