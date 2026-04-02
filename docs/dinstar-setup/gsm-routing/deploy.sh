#!/bin/bash
# ==============================================================
# Dinstar UC2000-VE-8G — GSM Routing Deploy Script
# Runs from Frappe dev container, deploys to FreePBX
# ==============================================================

set -e

VPS_HOST="157.173.125.136"
VPS_PORT="1352"
CONTAINER="initpbx-freepbx-1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/tmp/known_hosts"

echo "=== Deploying GSM Routing to FreePBX ==="
echo ""

# Step 1: Upload deploy script
echo "[1/3] Uploading remote deploy script..."
scp $SSH_OPTS -P $VPS_PORT \
    "$SCRIPT_DIR/remote_deploy.sh" \
    root@$VPS_HOST:/tmp/remote_gsm_deploy.sh

# Step 2: Copy into container
echo "[2/3] Copying into container..."
ssh $SSH_OPTS -p $VPS_PORT root@$VPS_HOST \
    "docker cp /tmp/remote_gsm_deploy.sh $CONTAINER:/root/remote_gsm_deploy.sh && \
     docker exec $CONTAINER chmod +x /root/remote_gsm_deploy.sh"

# Step 3: Execute inside container
echo "[3/3] Executing inside container..."
ssh $SSH_OPTS -p $VPS_PORT root@$VPS_HOST \
    "docker exec $CONTAINER bash /root/remote_gsm_deploy.sh"

echo ""
echo "=== Deployment Complete ==="
