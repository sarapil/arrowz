#!/bin/bash
###############################################################################
# Fix .ovpn for NetworkManager — Run on VPS HOST
# ================================================
# Converts existing .ovpn file to NetworkManager-compatible format.
#
# Usage:
#   bash fix_ovpn_for_nm.sh                         → fix admin
#   bash fix_ovpn_for_nm.sh /path/to/file.ovpn      → fix specific file
###############################################################################

set -euo pipefail

CONTAINER="initpbx-freepbx-1"
PEER_NAME="${1:-admin}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Fix .ovpn for NetworkManager                    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# If argument is a file path, use it directly
if [[ -f "$PEER_NAME" ]]; then
    SRC_FILE="$PEER_NAME"
    PEER_NAME=$(basename "$SRC_FILE" .ovpn)
else
    # Try to find in known locations
    SRC_FILE=""
    for loc in \
        "/opt/proj/initpbx/vpn-clients/${PEER_NAME}.ovpn" \
        "/tmp/${PEER_NAME}.ovpn" \
        "${HOME}/${PEER_NAME}.ovpn"; do
        if [[ -f "$loc" ]]; then
            SRC_FILE="$loc"
            break
        fi
    done

    # Try to get from container
    if [[ -z "$SRC_FILE" ]]; then
        echo -e "${YELLOW}  Getting .ovpn from container...${NC}"
        docker cp "${CONTAINER}:/etc/openvpn/peers/${PEER_NAME}/${PEER_NAME}.ovpn" "/tmp/${PEER_NAME}.ovpn" 2>/dev/null
        SRC_FILE="/tmp/${PEER_NAME}.ovpn"
    fi
fi

if [[ ! -f "$SRC_FILE" ]]; then
    echo -e "${RED}  Cannot find .ovpn for '${PEER_NAME}'${NC}"
    exit 1
fi

echo "  Source: $SRC_FILE"
echo ""

# ── Extract key parts from original ──
REMOTE=$(grep "^remote " "$SRC_FILE" | head -1)
PROTO=$(grep "^proto " "$SRC_FILE" | head -1)
CIPHER=$(grep "^cipher " "$SRC_FILE" | head -1 || echo "cipher AES-256-CBC")
AUTH=$(grep "^auth " "$SRC_FILE" | head -1 || echo "auth SHA256")

# Extract the <secret> block
SECRET_BLOCK=$(sed -n '/<secret>/,/<\/secret>/p' "$SRC_FILE")

if [[ -z "$REMOTE" ]]; then
    echo -e "${RED}  No 'remote' directive found in file!${NC}"
    exit 1
fi

if [[ -z "$SECRET_BLOCK" ]]; then
    echo -e "${RED}  No <secret> block found in file!${NC}"
    exit 1
fi

# ── Create NM-compatible file ──
NM_FILE="$(dirname "$SRC_FILE")/${PEER_NAME}-nm.ovpn"

# Extract remote IP and port
REMOTE_HOST=$(echo "$REMOTE" | awk '{print $2}')
REMOTE_PORT=$(echo "$REMOTE" | awk '{print $3}')
PROTO_VAL=$(echo "$PROTO" | awk '{print $2}')

# Extract ifconfig line
IFCONFIG=$(grep "^ifconfig " "$SRC_FILE" | head -1)

cat > "$NM_FILE" << NMEOF
# OpenVPN Static Key — ${PEER_NAME} (NetworkManager compatible)
# Import: nmcli connection import type openvpn file ${PEER_NAME}-nm.ovpn

${PROTO}
${REMOTE}
dev tun
resolv-retry infinite
nobind

${IFCONFIG}
allow-deprecated-insecure-static-crypto

persist-tun
persist-key

ping 10
ping-restart 60

data-ciphers AES-256-GCM:AES-256-CBC
${CIPHER}
${AUTH}

verb 3

${SECRET_BLOCK}
NMEOF

echo -e "${GREEN}[✓] Created: ${NM_FILE}${NC}"
echo ""

# ── Also create a separate key file (some NM versions need this) ──
KEY_FILE="$(dirname "$SRC_FILE")/${PEER_NAME}-static.key"
sed -n '/<secret>/,/<\/secret>/{ /<secret>/d; /<\/secret>/d; p; }' "$SRC_FILE" > "$KEY_FILE"

# And a version that references the key file
NM_FILE2="$(dirname "$SRC_FILE")/${PEER_NAME}-nm2.ovpn"
cat > "$NM_FILE2" << NM2EOF
# OpenVPN Static Key — ${PEER_NAME} (NM + external key file)
# Import: nmcli connection import type openvpn file ${PEER_NAME}-nm2.ovpn
# Note: ${PEER_NAME}-static.key must be in same directory

${PROTO}
${REMOTE}
dev tun
resolv-retry infinite
nobind

${IFCONFIG}
allow-deprecated-insecure-static-crypto

persist-tun
persist-key

ping 10
ping-restart 60

secret ${PEER_NAME}-static.key

data-ciphers AES-256-GCM:AES-256-CBC
${CIPHER}
${AUTH}

verb 3
NM2EOF

echo -e "${GREEN}[✓] Created: ${NM_FILE2}  (references external key file)${NC}"
echo -e "${GREEN}[✓] Created: ${KEY_FILE}${NC}"
echo ""

# ── Show the NM file ──
echo -e "${CYAN}── ${PEER_NAME}-nm.ovpn (inline key) ──${NC}"
echo ""
cat "$NM_FILE"
echo ""

# ── Import instructions ──
echo -e "${YELLOW}── Import Methods ──${NC}"
echo ""
echo "  Method 1 — CLI:"
echo "    nmcli connection import type openvpn file ${NM_FILE}"
echo "    nmcli connection up ${PEER_NAME}-nm"
echo ""
echo "  Method 2 — GUI (GNOME):"
echo "    Settings → Network → VPN → + → Import from file"
echo "    Select: ${NM_FILE}"
echo ""
echo "  Method 3 — GUI (KDE):"
echo "    System Settings → Connections → + → Import VPN"
echo "    Select: ${NM_FILE}"
echo ""
echo "  Method 4 — If inline key fails, use external key version:"
echo "    Copy BOTH files to same folder:"
echo "      ${NM_FILE2}"
echo "      ${KEY_FILE}"
echo "    Then import ${NM_FILE2}"
echo ""
echo "  Method 5 — Manual with NM (if import still fails):"
echo "    nmcli connection add type vpn vpn-type openvpn \\"
echo "      con-name '${PEER_NAME}-vpn' \\"
echo "      vpn.data 'remote=$(echo "$REMOTE" | awk '{print $2}'), \\"
echo "               port=$(echo "$REMOTE" | awk '{print $3}'), \\"
echo "               connection-type=static-key, \\"
echo "               static-key=${KEY_FILE}, \\"
echo "               cipher=AES-256-CBC, \\"
echo "               auth=SHA256'"
echo ""
echo "  Method 6 — Bypass NM entirely (direct CLI):"
echo "    sudo openvpn --config ${SRC_FILE}"
echo ""
