#!/bin/bash
# =====================================================
# Rebuild Development Container with PBX Volumes
# =====================================================
#
# This script rebuilds the development container with
# FreePBX volume mounts for local log/config access.
#
# Usage:
#   ./rebuild-with-pbx.sh
#
# Requirements:
#   - FreePBX data at /opt/proj/initpbx/fpbx_data/
#   - Docker and docker-compose installed
#
# =====================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔄 Rebuilding development container with PBX volumes..."

# Check if PBX data directory exists
if [ ! -d "/opt/proj/initpbx/fpbx_data" ]; then
    echo "⚠️  Warning: FreePBX data directory not found at /opt/proj/initpbx/fpbx_data"
    echo "   PBX volumes will not be mounted. Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Create mount point directories if they don't exist
echo "📁 Creating mount point directories..."
sudo mkdir -p /mnt/pbx/{logs/asterisk,logs/apache2,logs/pbx,etc/asterisk,db,mysql,recordings,voicemail,callaccounting,keys,ssl}

# Stop existing container
echo "⏹️  Stopping existing containers..."
docker-compose -f docker-compose.yml -f docker-compose.pbx.yml down 2>/dev/null || true

# Rebuild and start
echo "🚀 Starting containers with PBX volumes..."
docker-compose -f docker-compose.yml -f docker-compose.pbx.yml up -d --build

echo ""
echo "✅ Development container rebuilt with PBX volumes!"
echo ""
echo "📂 PBX Volumes mounted at /mnt/pbx/:"
echo "   - logs/asterisk  → Asterisk logs"
echo "   - logs/apache2   → Apache logs"
echo "   - etc/asterisk   → PJSIP configs"
echo "   - astdb.sqlite3  → Asterisk DB"
echo "   - recordings     → Call recordings"
echo "   - voicemail      → Voicemail files"
echo ""
echo "🔧 To verify, run inside the container:"
echo "   bench --site dev.localhost execute arrowz.local_pbx_monitor.check_pbx_mounts"
echo ""
