#!/bin/bash
###############################################################################
# Quick Host Firewall — Allow WireGuard UDP through VPS firewall
# ================================================================
#
# RUNS ON: VPS HOST (before or after container restart)
#
# This ensures port 51820/UDP reaches the container.
# Also loads the WireGuard kernel module on the host.
###############################################################################

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

VPN_PORT="51820"

echo ""
info "Setting up host firewall + kernel module for WireGuard..."
echo ""

###############################################################################
# 1. Load WireGuard kernel module on HOST
###############################################################################
info "Loading WireGuard kernel module..."

if lsmod | grep -q wireguard; then
    log "WireGuard module already loaded"
else
    modprobe wireguard 2>/dev/null && log "WireGuard module loaded" || {
        warn "Could not load wireguard module. Installing..."
        apt-get update -qq
        apt-get install -y -qq wireguard-dkms wireguard-tools 2>/dev/null || \
        apt-get install -y -qq linux-headers-$(uname -r) wireguard 2>/dev/null || \
        warn "WireGuard might already be built into kernel 6.8+"
    }
    modprobe wireguard 2>/dev/null || warn "Module may be built-in (kernel 6.8+)"
fi

# Make persistent
if ! grep -q "wireguard" /etc/modules-load.d/wireguard.conf 2>/dev/null; then
    echo "wireguard" > /etc/modules-load.d/wireguard.conf
    log "WireGuard module set to load on boot"
fi



###############################################################################
# 3. IP Forwarding (host level)
###############################################################################
info "Enabling IP forwarding on host..."

sysctl -w net.ipv4.ip_forward=1 >/dev/null
if ! grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
fi
log "IP forwarding enabled"

###############################################################################
# Verify
###############################################################################
echo ""
info "Verification:"
echo "  Kernel module: $(lsmod | grep wireguard | awk '{print "loaded ("$3" users)"}' || echo 'built-in or not loaded')"
echo "  Port ${VPN_PORT}/UDP: $(ss -ulnp | grep ${VPN_PORT} | head -1 || echo 'not yet listening (starts with container)')"
echo "  IP forwarding: $(sysctl net.ipv4.ip_forward | awk '{print $3}')"
echo ""
log "Host ready for WireGuard container! 🎉"
