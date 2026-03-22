#!/usr/bin/env bash
# ============================================================================
# Arrowz - Asterisk Error Auto-Fix Script
# ============================================================================
# Version: 2.0.0  |  Date: 2026-02-23
#
# Designed to run INSIDE the FreePBX container.
# Fixes all critical Asterisk configuration errors found in log analysis.
#
# Deployment:
#   The script is auto-deployed to /etc/asterisk/.arrowz/ inside FreePBX
#   via the shared volume mount.
#
# Usage (inside FreePBX container):
#   bash /etc/asterisk/.arrowz/fix_asterisk_errors.sh [OPTIONS]
#
# Options:
#   --dry-run         Show what would change without applying
#   --fix-all         Fix all issues (default)
#   --fix <target>    Fix specific: ssl|pjsip|opus|transport|ami|security
#   --reload          Reload Asterisk after fixes
#   --verify          Run verification only (no fixes)
#   --diagnose        Full diagnostic report without fixing
#   -h, --help        Show usage
#
# Examples:
#   bash fix_asterisk_errors.sh --dry-run          # Preview all fixes
#   bash fix_asterisk_errors.sh --fix-all --reload # Fix everything + reload
#   bash fix_asterisk_errors.sh --fix ssl --reload  # Fix SSL only + reload
#   bash fix_asterisk_errors.sh --verify           # Just check current state
#   bash fix_asterisk_errors.sh --diagnose         # Full health report
# ============================================================================

set -euo pipefail

# ─── Colors ───────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ─── Detect Environment ──────────────────────────────────────────
detect_environment() {
    if [[ -f "/etc/freepbx.conf" ]] || [[ -f "/var/www/html/admin/bootstrap.php" ]]; then
        # Inside FreePBX container
        AST_BASE="/etc/asterisk"
        AST_KEYS="/etc/asterisk/keys"
        LOG_BASE="/var/log/asterisk"
        ENVIRONMENT="freepbx"
        CAN_RELOAD=true
        CAN_CLI=true
        SUDO=""
    elif [[ -d "/mnt/pbx/etc/asterisk" ]]; then
        # Dev container with PBX volume mount
        AST_BASE="/mnt/pbx/etc/asterisk"
        AST_KEYS="/mnt/pbx/etc/asterisk/keys"
        LOG_BASE="/mnt/pbx/logs/asterisk"
        ENVIRONMENT="dev-container"
        CAN_RELOAD=false
        CAN_CLI=false
        SUDO="sudo"
    else
        echo -e "${RED}✗ لا يمكن العثور على ملفات Asterisk${NC}"
        echo -e "${RED}  يجب تشغيل هذا السكريبت من داخل حاوية FreePBX${NC}"
        echo -e "${RED}  أو من dev container مع /mnt/pbx مُثبّت${NC}"
        exit 1
    fi

    # Check if running as root (needed inside FreePBX)
    if [[ "$ENVIRONMENT" == "freepbx" ]] && [[ "$(id -u)" -ne 0 ]]; then
        echo -e "${YELLOW}⚠ يُفضّل التشغيل كـ root داخل حاوية FreePBX${NC}"
        SUDO="sudo"
    fi
}

# ─── Parse Arguments ─────────────────────────────────────────────
DRY_RUN=false
FIX_TARGET="all"
DO_RELOAD=false
VERIFY_ONLY=false
DIAGNOSE_ONLY=false

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)    DRY_RUN=true; shift ;;
            --fix-all)    FIX_TARGET="all"; shift ;;
            --fix)        FIX_TARGET="$2"; shift 2 ;;
            --reload)     DO_RELOAD=true; shift ;;
            --verify)     VERIFY_ONLY=true; shift ;;
            --diagnose)   DIAGNOSE_ONLY=true; shift ;;
            -h|--help)    show_usage; exit 0 ;;
            *)            echo -e "${RED}خيار غير معروف: $1${NC}"; show_usage; exit 1 ;;
        esac
    done
}

show_usage() {
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║         Arrowz - Asterisk Error Auto-Fix Script             ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  الاستخدام:                                                  ║
║    bash fix_asterisk_errors.sh [OPTIONS]                     ║
║                                                              ║
║  الخيارات:                                                   ║
║    --dry-run         معاينة بدون تطبيق                       ║
║    --fix-all         إصلاح الكل (افتراضي)                    ║
║    --fix <target>    إصلاح محدد:                             ║
║                      ssl|pjsip|opus|transport|ami|security   ║
║    --reload          إعادة تحميل Asterisk بعد الإصلاح        ║
║    --verify          فحص فقط بدون إصلاح                      ║
║    --diagnose        تقرير تشخيصي كامل                       ║
║    -h, --help        عرض المساعدة                            ║
║                                                              ║
║  أمثلة:                                                      ║
║    bash fix_asterisk_errors.sh --dry-run                     ║
║    bash fix_asterisk_errors.sh --fix-all --reload            ║
║    bash fix_asterisk_errors.sh --fix ssl --reload            ║
║    bash fix_asterisk_errors.sh --diagnose                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
}

# ─── Helpers ──────────────────────────────────────────────────────
BACKUP_DIR=""
FIXES_APPLIED=0
FIXES_SKIPPED=0
ERRORS_FOUND=0

backup_file() {
    local file="$1"
    if [[ -f "$file" ]]; then
        if [[ -z "$BACKUP_DIR" ]]; then
            BACKUP_DIR="${AST_BASE}/.arrowz/backups/$(date +%Y%m%d_%H%M%S)"
        fi
        $SUDO mkdir -p "$BACKUP_DIR"
        $SUDO cp "$file" "$BACKUP_DIR/$(basename "$file")"
        echo -e "  ${DIM}↳ نسخة احتياطية: $(basename "$file")${NC}"
    fi
}

# Run Asterisk CLI command (only works inside FreePBX container)
ast_cmd() {
    local cmd="$1"
    if [[ "$CAN_CLI" == true ]]; then
        $SUDO asterisk -rx "$cmd" 2>/dev/null
    else
        echo -e "  ${DIM}[لا يمكن التنفيذ من خارج الحاوية] $cmd${NC}"
    fi
}

print_header() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║       ${BOLD}Arrowz - أداة إصلاح أخطاء Asterisk التلقائية${NC}${CYAN}        ║${NC}"
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC}  البيئة:     ${YELLOW}${ENVIRONMENT}${NC}"
    echo -e "${CYAN}║${NC}  المسار:     ${YELLOW}${AST_BASE}${NC}"
    echo -e "${CYAN}║${NC}  معاينة:     ${YELLOW}${DRY_RUN}${NC}"
    echo -e "${CYAN}║${NC}  الهدف:      ${YELLOW}${FIX_TARGET}${NC}"
    echo -e "${CYAN}║${NC}  إعادة تحميل: ${YELLOW}${DO_RELOAD}${NC}"

    # Show Asterisk version if available
    if [[ "$CAN_CLI" == true ]]; then
        local version
        version=$($SUDO asterisk -rx "core show version" 2>/dev/null | head -1 || echo "غير متوفر")
        echo -e "${CYAN}║${NC}  الإصدار:    ${YELLOW}${version}${NC}"
    fi

    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ============================================================================
# DIAGNOSTIC MODE
# ============================================================================
run_diagnose() {
    echo -e "${BOLD}${MAGENTA}━━━━━━━━━━━━━━━━━━ تقرير تشخيصي شامل ━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # 1. Asterisk Status
    echo -e "${BOLD}📡 حالة Asterisk:${NC}"
    if [[ "$CAN_CLI" == true ]]; then
        local uptime
        uptime=$(ast_cmd "core show uptime" 2>/dev/null || echo "غير متصل")
        echo -e "  $uptime"

        local channels
        channels=$(ast_cmd "core show channels count" 2>/dev/null | tail -2 || echo "0")
        echo -e "  $channels"
    else
        echo -e "  ${DIM}(لا يمكن الفحص من خارج الحاوية)${NC}"
    fi
    echo ""

    # 2. Transports
    echo -e "${BOLD}🔌 Transports:${NC}"
    if [[ "$CAN_CLI" == true ]]; then
        ast_cmd "pjsip show transports" 2>/dev/null | head -20 || echo "  فشل القراءة"
    else
        echo -e "  Config:"
        $SUDO grep -E '^\[|^type=|^protocol=|^bind=' "$AST_BASE/pjsip.transports.conf" 2>/dev/null | head -15
        echo ""
        echo -e "  Custom:"
        $SUDO grep -E '^\[|^type=|^protocol=|^bind=|^cert' "$AST_BASE/pjsip.transports_custom.conf" 2>/dev/null | head -10
    fi
    echo ""

    # 3. Endpoints
    echo -e "${BOLD}📞 Endpoints:${NC}"
    if [[ "$CAN_CLI" == true ]]; then
        ast_cmd "pjsip show endpoints" 2>/dev/null | head -30 || echo "  فشل القراءة"
    else
        echo -e "  Custom endpoints:"
        $SUDO grep '^\[' "$AST_BASE/pjsip.endpoint_custom.conf" 2>/dev/null
    fi
    echo ""

    # 4. Certificates
    echo -e "${BOLD}🔐 الشهادات:${NC}"
    $SUDO ls -lh "$AST_KEYS"/*.pem "$AST_KEYS"/*.crt "$AST_KEYS"/*.key 2>/dev/null | \
        awk '{print "  " $5 "\t" $9}' || echo "  لا توجد شهادات"
    echo ""

    # 5. Recent Errors (last 20)
    echo -e "${BOLD}🔴 آخر الأخطاء (بدون SSL scanners):${NC}"
    local log_file="$LOG_BASE/full"
    $SUDO grep -i "ERROR" "$log_file" 2>/dev/null | \
        grep -v "iostream.c\|SSL_shutdown\|ssl connection" | \
        tail -10 || echo "  لا توجد أخطاء حديثة"
    echo ""

    # 6. Security - Recent attacks
    echo -e "${BOLD}🛡️ هجمات أمنية (آخر 24 ساعة):${NC}"
    local yesterday
    yesterday=$(date -d "yesterday" +%Y%m%d 2>/dev/null || date +%Y%m%d)
    local attack_log="$LOG_BASE/full-${yesterday}"
    if $SUDO test -f "$attack_log" 2>/dev/null; then
        local brute_count
        brute_count=$($SUDO grep -c "Failed to authenticate\|No matching endpoint" "$attack_log" 2>/dev/null || echo "0")
        local ssl_count
        ssl_count=$($SUDO grep -c "ssl connection\|SSL_shutdown" "$attack_log" 2>/dev/null || echo "0")
        local ip_count
        ip_count=$($SUDO grep -i "failed for" "$attack_log" 2>/dev/null | \
            grep -oP "'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" | sort -u | wc -l || echo "0")

        echo -e "  محاولات Brute-force: ${RED}${brute_count}${NC}"
        echo -e "  محاولات SSL scan:    ${YELLOW}${ssl_count}${NC}"
        echo -e "  عناوين IP مهاجمة:    ${RED}${ip_count}${NC}"

        if [[ "$ip_count" -gt 0 ]]; then
            echo -e "  ${DIM}أكثر الـ IPs نشاطاً:${NC}"
            $SUDO grep -i "failed for" "$attack_log" 2>/dev/null | \
                grep -oP "'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" | \
                sort | uniq -c | sort -rn | head -5 | \
                awk '{print "    " $2 " (" $1 " محاولة)"}' || true
        fi
    else
        echo -e "  ${DIM}لا يوجد لوج الأمس${NC}"
    fi
    echo ""

    # 7. AMI Status
    echo -e "${BOLD}📋 AMI (Asterisk Manager):${NC}"
    if [[ "$CAN_CLI" == true ]]; then
        ast_cmd "manager show connected" 2>/dev/null | head -10 || echo "  فشل القراءة"
    else
        echo -e "  AMI Config:"
        $SUDO grep -E "^enabled|^port|^bindaddr" "$AST_BASE/manager.conf" 2>/dev/null | head -5
    fi
    echo ""

    # 8. Module Status
    echo -e "${BOLD}📦 Modules المعطلة:${NC}"
    if [[ "$CAN_CLI" == true ]]; then
        local failed_modules
        failed_modules=$(ast_cmd "module show" 2>/dev/null | grep -i "not running\|failed" | head -10 || true)
        if [[ -n "$failed_modules" ]]; then
            echo "$failed_modules"
        else
            echo -e "  ${GREEN}✓ جميع الـ modules تعمل${NC}"
        fi
    else
        $SUDO grep "ERROR.*loader.c" "$LOG_BASE/full" 2>/dev/null | tail -5 || echo "  لا توجد أخطاء"
    fi
    echo ""

    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# ============================================================================
# VERIFY MODE
# ============================================================================
run_verify() {
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━ فحص الإعدادات ━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    local all_ok=true

    # 1. SSL
    echo -e "${BOLD}1. شهادات SSL:${NC}"
    local cert_ok=true
    for f in fullchain.pem privkey.pem; do
        if $SUDO test -f "$AST_KEYS/$f" 2>/dev/null; then
            local size
            size=$($SUDO stat -c%s "$AST_KEYS/$f" 2>/dev/null || echo "0")
            if [[ "$size" -gt 100 ]]; then
                echo -e "  ${GREEN}✓${NC} $f (${size} bytes)"
            else
                echo -e "  ${RED}✗${NC} $f (ملف فارغ!)"
                cert_ok=false
            fi
        else
            echo -e "  ${RED}✗${NC} $f مفقود"
            cert_ok=false
        fi
    done
    [[ "$cert_ok" == false ]] && all_ok=false

    # 2. PJSIP Duplicates
    echo ""
    echo -e "${BOLD}2. كائنات PJSIP المكررة:${NC}"
    local sections
    sections=$($SUDO grep -c '^\[' "$AST_BASE/pjsip.endpoint_custom.conf" 2>/dev/null || echo "0")
    local unique_sections
    unique_sections=$($SUDO grep '^\[' "$AST_BASE/pjsip.endpoint_custom.conf" 2>/dev/null | sort -u | wc -l || echo "0")

    if [[ "$sections" == "$unique_sections" ]]; then
        echo -e "  ${GREEN}✓${NC} لا توجد تكرارات ($sections sections)"
    else
        echo -e "  ${RED}✗${NC} يوجد تكرار: $sections إجمالي vs $unique_sections فريد"
        all_ok=false
    fi

    # Check AOR has no endpoint options
    local bad_aor
    bad_aor=$($SUDO cat "$AST_BASE/pjsip.endpoint_custom.conf" 2>/dev/null | \
        sed -n '/\-aor\]/,/^$/p' | \
        grep -c 'dtls_auto_generate_cert\|media_encryption\|ice_support' || echo "0")
    bad_aor=$(echo "$bad_aor" | tr -d '[:space:]')
    if [[ "$bad_aor" -gt 0 ]]; then
        echo -e "  ${RED}✗${NC} AOR يحتوي على خيارات endpoint ($bad_aor خيارات خاطئة)"
        all_ok=false
    else
        echo -e "  ${GREEN}✓${NC} AOR نظيف"
    fi

    # 3. Transport Port
    echo ""
    echo -e "${BOLD}3. Transport external_signaling_port:${NC}"
    local port_val
    port_val=$($SUDO grep "external_signaling_port=" "$AST_BASE/pjsip.transports.conf" 2>/dev/null | head -1 | cut -d= -f2)
    if [[ -z "$port_val" ]]; then
        echo -e "  ${GREEN}✓${NC} لا يوجد external_signaling_port (OK)"
    elif [[ "$port_val" =~ ^[0-9]+$ ]]; then
        echo -e "  ${GREEN}✓${NC} external_signaling_port=$port_val"
    else
        echo -e "  ${RED}✗${NC} external_signaling_port=$port_val (يجب أن يكون رقم!)"
        all_ok=false
    fi

    # 4. Opus Codec
    echo ""
    echo -e "${BOLD}4. Opus Codec:${NC}"
    local opus_bw
    opus_bw=$($SUDO grep "^max_bandwidth=" "$AST_BASE/codecs.conf" 2>/dev/null | head -1 | cut -d= -f2)
    if [[ "$opus_bw" == "full" ]]; then
        echo -e "  ${GREEN}✓${NC} max_bandwidth=$opus_bw"
    elif [[ "$opus_bw" == "fullband" ]]; then
        echo -e "  ${RED}✗${NC} max_bandwidth=fullband (يجب أن يكون 'full')"
        all_ok=false
    else
        echo -e "  ${YELLOW}⚠${NC} max_bandwidth=$opus_bw"
    fi

    # 5. Custom Transport Certs
    echo ""
    echo -e "${BOLD}5. مسارات الشهادات (transports_custom):${NC}"
    local custom_cert
    custom_cert=$($SUDO grep "cert_file=" "$AST_BASE/pjsip.transports_custom.conf" 2>/dev/null | head -1 | cut -d= -f2)
    local custom_key
    custom_key=$($SUDO grep "priv_key_file=" "$AST_BASE/pjsip.transports_custom.conf" 2>/dev/null | head -1 | cut -d= -f2)

    # In dev-container, config paths reference /etc/asterisk/keys/
    # but actual files are at /mnt/pbx/etc/asterisk/keys/
    local resolved_cert="$custom_cert"
    local resolved_key="$custom_key"
    if [[ "$ENVIRONMENT" == "dev-container" ]]; then
        resolved_cert=$(echo "$custom_cert" | sed 's|^/etc/asterisk|/mnt/pbx/etc/asterisk|')
        resolved_key=$(echo "$custom_key" | sed 's|^/etc/asterisk|/mnt/pbx/etc/asterisk|')
    fi

    if [[ -n "$custom_cert" ]]; then
        if $SUDO test -f "$resolved_cert" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} cert_file=$custom_cert"
        else
            echo -e "  ${RED}✗${NC} cert_file=$custom_cert (الملف مفقود!)"
            all_ok=false
        fi
    fi
    if [[ -n "$custom_key" ]]; then
        if $SUDO test -f "$resolved_key" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} priv_key_file=$custom_key"
        else
            echo -e "  ${RED}✗${NC} priv_key_file=$custom_key (الملف مفقود!)"
            all_ok=false
        fi
    fi

    # 6. Asterisk Live Check
    if [[ "$CAN_CLI" == true ]]; then
        echo ""
        echo -e "${BOLD}6. فحص Asterisk مباشر:${NC}"

        # Transports loaded?
        local transports
        transports=$(ast_cmd "pjsip show transports" 2>/dev/null | grep -c "Transport:" || echo "0")
        echo -e "  Transports محمّلة: ${transports}"

        # Endpoints loaded?
        local endpoints
        endpoints=$(ast_cmd "pjsip show endpoints" 2>/dev/null | grep -c "Endpoint:" || echo "0")
        echo -e "  Endpoints محمّلة: ${endpoints}"

        # Check specific endpoint 1001
        local ep_1001
        ep_1001=$(ast_cmd "pjsip show endpoint 1001" 2>/dev/null | head -3 || echo "")
        if [[ -n "$ep_1001" ]] && ! echo "$ep_1001" | grep -qi "unable\|not found"; then
            echo -e "  ${GREEN}✓${NC} Extension 1001 محمّل"
        else
            echo -e "  ${RED}✗${NC} Extension 1001 غير محمّل"
            all_ok=false
        fi
    fi

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    if [[ "$all_ok" == true ]]; then
        echo -e "${GREEN}${BOLD}✓ جميع الفحوصات ناجحة!${NC}"
    else
        echo -e "${RED}${BOLD}✗ بعض الفحوصات فشلت — شغّل السكريبت بدون --verify للإصلاح${NC}"
    fi
    echo ""
}

# ============================================================================
# FIX 1: SSL Certificate Paths
# ============================================================================
fix_ssl() {
    echo -e "${YELLOW}━━━ إصلاح 1: مسارات شهادات SSL ━━━${NC}"

    local cert_file="${AST_KEYS}/fullchain.pem"
    local key_file="${AST_KEYS}/privkey.pem"
    local real_cert="${AST_KEYS}/tavirapbx-fullchain.crt"
    local real_key="${AST_KEYS}/tavirapbx.key"

    # Check source certs exist
    if ! $SUDO test -f "$real_cert" 2>/dev/null; then
        echo -e "  ${RED}✗ الشهادة المصدر غير موجودة: $real_cert${NC}"
        ((ERRORS_FOUND++))
        return
    fi
    if ! $SUDO test -f "$real_key" 2>/dev/null; then
        echo -e "  ${RED}✗ المفتاح المصدر غير موجود: $real_key${NC}"
        ((ERRORS_FOUND++))
        return
    fi

    echo -e "  ${GREEN}✓${NC} الشهادة المصدر: $(basename "$real_cert")"
    echo -e "  ${GREEN}✓${NC} المفتاح المصدر: $(basename "$real_key")"

    # Check if already fixed
    if $SUDO test -f "$cert_file" 2>/dev/null && $SUDO test -f "$key_file" 2>/dev/null; then
        local cert_size real_cert_size
        cert_size=$($SUDO stat -c%s "$cert_file" 2>/dev/null || echo "0")
        real_cert_size=$($SUDO stat -c%s "$real_cert" 2>/dev/null || echo "0")
        if [[ "$cert_size" == "$real_cert_size" ]] && [[ "$cert_size" -gt 100 ]]; then
            echo -e "  ${GREEN}✓${NC} الشهادات مُثبّتة بالفعل"
            ((FIXES_SKIPPED++))
            echo ""
            return
        fi
    fi

    if [[ "$DRY_RUN" == true ]]; then
        echo -e "  ${BLUE}[معاينة] سيتم نسخ: fullchain.pem ← tavirapbx-fullchain.crt${NC}"
        echo -e "  ${BLUE}[معاينة] سيتم نسخ: privkey.pem ← tavirapbx.key${NC}"
    else
        backup_file "$cert_file" 2>/dev/null || true
        backup_file "$key_file" 2>/dev/null || true
        $SUDO cp "$real_cert" "$cert_file"
        $SUDO cp "$real_key" "$key_file"
        $SUDO chmod 640 "$cert_file" "$key_file"
        # Set ownership to asterisk user if it exists
        if id asterisk &>/dev/null; then
            $SUDO chown asterisk:asterisk "$cert_file" "$key_file"
        fi
        echo -e "  ${GREEN}✓ تم إنشاء fullchain.pem${NC}"
        echo -e "  ${GREEN}✓ تم إنشاء privkey.pem${NC}"
        ((FIXES_APPLIED++))
    fi
    echo ""
}

# ============================================================================
# FIX 2: PJSIP Endpoint Custom Config
# ============================================================================
fix_pjsip() {
    echo -e "${YELLOW}━━━ إصلاح 2: إعدادات PJSIP Endpoints ━━━${NC}"

    local conf_file="${AST_BASE}/pjsip.endpoint_custom.conf"

    if ! $SUDO test -f "$conf_file" 2>/dev/null; then
        echo -e "  ${RED}✗ الملف غير موجود: $conf_file${NC}"
        ((ERRORS_FOUND++))
        return
    fi

    # Count issues
    local total_sections unique_sections
    total_sections=$($SUDO grep -c '^\[' "$conf_file" 2>/dev/null || echo "0")
    unique_sections=$($SUDO grep '^\[' "$conf_file" 2>/dev/null | sort -u | wc -l || echo "0")
    local bad_aor
    bad_aor=$($SUDO grep -A20 '\-aor\]' "$conf_file" 2>/dev/null | \
        grep -c 'dtls_auto_generate_cert\|media_encryption\|ice_support' || echo "0")

    echo -e "  Sections:        $total_sections (فريدة: $unique_sections)"
    echo -e "  خيارات AOR خاطئة: $bad_aor"

    if [[ "$total_sections" == "$unique_sections" ]] && [[ "$bad_aor" -eq 0 ]]; then
        echo -e "  ${GREEN}✓${NC} الإعدادات نظيفة"
        ((FIXES_SKIPPED++))
        echo ""
        return
    fi

    if [[ "$DRY_RUN" == true ]]; then
        echo -e "  ${BLUE}[معاينة] سيتم إعادة كتابة pjsip.endpoint_custom.conf${NC}"
    else
        backup_file "$conf_file"

        $SUDO tee "$conf_file" > /dev/null << 'PJSIP_EOF'
; ============================================================================
; Arrowz Labs - PJSIP Custom Endpoints Configuration
; Fixed by Arrowz Asterisk Doctor
; ============================================================================

; --- WebRTC Global Template ---
[arkan-webrtc](!)
type=endpoint
transport=transport-wss
context=from-internal
disallow=all
allow=opus
allow=g722
allow=ulaw
allow=alaw
webrtc=yes
dtls_auto_generate_cert=yes
media_encryption=dtls
media_encryption_optimistic=no
dtls_setup=actpass
ice_support=yes
use_avpf=yes
bundle=yes
max_audio_streams=1
max_video_streams=1
rtp_symmetric=yes
force_rport=yes
rewrite_contact=yes
direct_media=no
media_use_received_transport=yes
trust_id_inbound=yes
trust_id_outbound=yes
send_pai=yes
send_rpid=yes
rtcp_mux=yes

; --- Extension 1001 (WebRTC) ---
[1001](arkan-webrtc)
aors=1001
auth=1001-auth
callerid="John Doe" <1001>

[1001-auth]
type=auth
auth_type=userpass
username=1001
password=YourSecurePassword123!

[1001-aor]
type=aor
max_contacts=1
remove_existing=yes
qualify_frequency=60

; --- Existing Extensions WebRTC Overrides ---
[2210](+)
webrtc=yes

[2211](+)
webrtc=yes

[2290](+)
webrtc=yes
PJSIP_EOF

        echo -e "  ${GREEN}✓ تم إعادة كتابة الملف (نظيف، بدون تكرار)${NC}"
        ((FIXES_APPLIED++))
    fi
    echo ""
}

# ============================================================================
# FIX 3: Opus Codec
# ============================================================================
fix_opus() {
    echo -e "${YELLOW}━━━ إصلاح 3: Opus Codec max_bandwidth ━━━${NC}"

    local conf_file="${AST_BASE}/codecs.conf"

    if ! $SUDO test -f "$conf_file" 2>/dev/null; then
        echo -e "  ${RED}✗ الملف غير موجود: $conf_file${NC}"
        ((ERRORS_FOUND++))
        return
    fi

    local current_val
    current_val=$($SUDO grep "^max_bandwidth=" "$conf_file" 2>/dev/null | head -1 || echo "")
    echo -e "  الحالي: ${current_val:-لا يوجد}"

    if [[ "$current_val" == "max_bandwidth=fullband" ]]; then
        if [[ "$DRY_RUN" == true ]]; then
            echo -e "  ${BLUE}[معاينة] سيتم تغيير: fullband → full${NC}"
        else
            backup_file "$conf_file"
            $SUDO sed -i 's/^max_bandwidth=fullband/max_bandwidth=full/' "$conf_file"
            echo -e "  ${GREEN}✓ تم تغيير max_bandwidth إلى full${NC}"
            ((FIXES_APPLIED++))
        fi
    elif [[ "$current_val" == "max_bandwidth=full" ]]; then
        echo -e "  ${GREEN}✓${NC} القيمة صحيحة بالفعل"
        ((FIXES_SKIPPED++))
    else
        echo -e "  ${YELLOW}⚠ قيمة غير متوقعة: $current_val${NC}"
    fi
    echo ""
}

# ============================================================================
# FIX 4: Transport external_signaling_port + cert paths
# ============================================================================
fix_transport() {
    echo -e "${YELLOW}━━━ إصلاح 4: Transport Configuration ━━━${NC}"

    local conf_file="${AST_BASE}/pjsip.transports.conf"

    if ! $SUDO test -f "$conf_file" 2>/dev/null; then
        echo -e "  ${RED}✗ الملف غير موجود: $conf_file${NC}"
        ((ERRORS_FOUND++))
        return
    fi

    # --- Fix external_signaling_port ---
    local bad_port
    bad_port=$($SUDO grep "external_signaling_port=pbx" "$conf_file" 2>/dev/null | head -1 || echo "")

    if [[ -n "$bad_port" ]]; then
        echo -e "  ${RED}✗${NC} external_signaling_port خاطئ (يحتوي domain بدل port)"

        local bind_port
        bind_port=$($SUDO grep "^bind=0.0.0.0:" "$conf_file" 2>/dev/null | head -1 | sed 's/.*://')
        local fix_port="${bind_port:-51600}"

        if [[ "$DRY_RUN" == true ]]; then
            echo -e "  ${BLUE}[معاينة] سيتم تغيير external_signaling_port إلى ${fix_port}${NC}"
        else
            backup_file "$conf_file"
            $SUDO sed -i "s/external_signaling_port=pbx\.tavira-group\.com/external_signaling_port=${fix_port}/" "$conf_file"
            echo -e "  ${GREEN}✓ تم تغيير external_signaling_port إلى ${fix_port}${NC}"
            echo -e "  ${YELLOW}⚠ تنبيه: FreePBX قد يُعيد الكتابة عند fwconsole reload${NC}"
            echo -e "  ${YELLOW}  → أصلحه نهائياً من: Admin → Asterisk SIP Settings${NC}"
            ((FIXES_APPLIED++))
        fi
    else
        echo -e "  ${GREEN}✓${NC} external_signaling_port صحيح"
        ((FIXES_SKIPPED++))
    fi

    # --- Fix custom transport cert paths ---
    local custom_conf="${AST_BASE}/pjsip.transports_custom.conf"
    if $SUDO test -f "$custom_conf" 2>/dev/null; then
        local needs_cert_fix=false
        if $SUDO grep -q "cert_file=/etc/asterisk/keys/fullchain.pem" "$custom_conf" 2>/dev/null; then
            needs_cert_fix=true
        fi

        if [[ "$needs_cert_fix" == true ]]; then
            if [[ "$DRY_RUN" == true ]]; then
                echo -e "  ${BLUE}[معاينة] سيتم تحديث مسارات الشهادات في transports_custom${NC}"
            else
                backup_file "$custom_conf"
                $SUDO sed -i 's|cert_file=/etc/asterisk/keys/fullchain.pem|cert_file=/etc/asterisk/keys/tavirapbx-fullchain.crt|' "$custom_conf"
                $SUDO sed -i 's|priv_key_file=/etc/asterisk/keys/privkey.pem|priv_key_file=/etc/asterisk/keys/tavirapbx.key|' "$custom_conf"
                echo -e "  ${GREEN}✓ تم تحديث مسارات الشهادات${NC}"
                ((FIXES_APPLIED++))
            fi
        else
            echo -e "  ${GREEN}✓${NC} مسارات الشهادات صحيحة"
        fi
    fi
    echo ""
}

# ============================================================================
# FIX 5: AMI Connectivity Check & Fix
# ============================================================================
fix_ami() {
    echo -e "${YELLOW}━━━ إصلاح 5: AMI (Asterisk Manager) ━━━${NC}"

    if [[ "$CAN_CLI" != true ]]; then
        echo -e "  ${DIM}(يتطلب التشغيل من داخل حاوية FreePBX)${NC}"
        echo ""
        return
    fi

    # Check if AMI is responding
    local ami_check
    ami_check=$(ast_cmd "manager show connected" 2>/dev/null || echo "FAILED")

    if echo "$ami_check" | grep -qi "failed\|error"; then
        echo -e "  ${RED}✗${NC} AMI لا يستجيب"
        ((ERRORS_FOUND++))

        # Try to reload AMI
        if [[ "$DRY_RUN" == true ]]; then
            echo -e "  ${BLUE}[معاينة] سيتم إعادة تحميل AMI${NC}"
        else
            ast_cmd "manager reload" 2>/dev/null || true
            sleep 1
            ami_check=$(ast_cmd "manager show connected" 2>/dev/null || echo "FAILED")
            if echo "$ami_check" | grep -qi "failed"; then
                echo -e "  ${RED}✗ AMI لا يزال لا يعمل بعد إعادة التحميل${NC}"
            else
                echo -e "  ${GREEN}✓ تم إصلاح AMI بعد إعادة التحميل${NC}"
                ((FIXES_APPLIED++))
            fi
        fi
    else
        local connected
        connected=$(echo "$ami_check" | grep -c "connected" || echo "0")
        echo -e "  ${GREEN}✓${NC} AMI يعمل ($connected اتصال)"
        ((FIXES_SKIPPED++))
    fi

    # Show AMI config
    local ami_enabled
    ami_enabled=$($SUDO grep "^enabled" "$AST_BASE/manager.conf" 2>/dev/null | head -1)
    echo -e "  Config: $ami_enabled"

    local ami_port
    ami_port=$($SUDO grep "^port" "$AST_BASE/manager.conf" 2>/dev/null | head -1)
    echo -e "  $ami_port"
    echo ""
}

# ============================================================================
# FIX 6: Security - Block top attackers
# ============================================================================
fix_security() {
    echo -e "${YELLOW}━━━ إصلاح 6: حظر عناوين IP المهاجمة ━━━${NC}"

    local yesterday
    yesterday=$(date -d "yesterday" +%Y%m%d 2>/dev/null || date +%Y%m%d)
    local log_file="$LOG_BASE/full-${yesterday}"

    if ! $SUDO test -f "$log_file" 2>/dev/null; then
        log_file="$LOG_BASE/full"
    fi

    # Get top attacker IPs (more than 50 attempts)
    local top_ips
    top_ips=$($SUDO grep -i "failed for\|No matching endpoint" "$log_file" 2>/dev/null | \
        grep -oP "'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+" | \
        sed "s/'//" | sort | uniq -c | sort -rn | \
        awk '$1 > 50 {print $2}' || true)

    if [[ -z "$top_ips" ]]; then
        echo -e "  ${GREEN}✓${NC} لا توجد عناوين IP تتجاوز 50 محاولة"
        ((FIXES_SKIPPED++))
        echo ""
        return
    fi

    local ip_count
    ip_count=$(echo "$top_ips" | wc -l)
    echo -e "  عناوين IP مع أكثر من 50 محاولة: ${RED}${ip_count}${NC}"

    # Check if iptables is available
    if command -v iptables &>/dev/null; then
        while IFS= read -r ip; do
            [[ -z "$ip" ]] && continue

            # Check if already blocked
            if $SUDO iptables -C INPUT -s "$ip" -j DROP 2>/dev/null; then
                echo -e "  ${GREEN}✓${NC} $ip محظور بالفعل"
                continue
            fi

            if [[ "$DRY_RUN" == true ]]; then
                echo -e "  ${BLUE}[معاينة] سيتم حظر: $ip${NC}"
            else
                $SUDO iptables -I INPUT -s "$ip" -j DROP 2>/dev/null && \
                    echo -e "  ${GREEN}✓ تم حظر: $ip${NC}" || \
                    echo -e "  ${RED}✗ فشل حظر: $ip${NC}"
                ((FIXES_APPLIED++))
            fi
        done <<< "$top_ips"
    else
        echo -e "  ${YELLOW}⚠ iptables غير متوفر${NC}"
        echo -e "  ${YELLOW}  عناوين IP الموصى بحظرها:${NC}"
        echo "$top_ips" | while read -r ip; do
            echo -e "    ${RED}$ip${NC}"
        done
    fi
    echo ""
}

# ============================================================================
# RELOAD Asterisk
# ============================================================================
reload_asterisk() {
    echo -e "${YELLOW}━━━ إعادة تحميل Asterisk ━━━${NC}"

    if [[ "$CAN_CLI" != true ]]; then
        echo -e "  ${YELLOW}⚠ لا يمكن إعادة التحميل من خارج الحاوية${NC}"
        echo -e "  ${YELLOW}  شغّل الأمر التالي داخل حاوية FreePBX:${NC}"
        echo -e "  ${CYAN}  asterisk -rx 'core reload'${NC}"
        echo -e "  ${CYAN}  # أو: fwconsole reload${NC}"
        echo ""
        return
    fi

    if [[ "$DRY_RUN" == true ]]; then
        echo -e "  ${BLUE}[معاينة] سيتم تنفيذ: asterisk -rx 'core reload'${NC}"
        echo ""
        return
    fi

    echo -e "  جارٍ إعادة تحميل PJSIP..."
    ast_cmd "module reload res_pjsip.so" || true
    sleep 1

    echo -e "  جارٍ إعادة تحميل Core..."
    ast_cmd "core reload" || true
    sleep 2

    # Verify after reload
    echo ""
    echo -e "  ${BOLD}التحقق بعد التحميل:${NC}"

    local transports
    transports=$(ast_cmd "pjsip show transports" 2>/dev/null || echo "")
    local transport_count
    transport_count=$(echo "$transports" | grep -c "Transport:" || echo "0")
    echo -e "  Transports: ${transport_count}"

    local endpoints
    endpoints=$(ast_cmd "pjsip show endpoints" 2>/dev/null || echo "")
    local endpoint_count
    endpoint_count=$(echo "$endpoints" | grep -c "Endpoint:" || echo "0")
    echo -e "  Endpoints: ${endpoint_count}"

    # Check for new errors
    local new_version
    new_version=$(ast_cmd "core show version" 2>/dev/null | head -1 || echo "فشل")
    echo -e "  الإصدار: ${new_version}"

    if [[ "$transport_count" -gt 0 ]] && [[ "$endpoint_count" -gt 0 ]]; then
        echo -e "  ${GREEN}✓ إعادة التحميل ناجحة!${NC}"
    else
        echo -e "  ${RED}✗ قد تكون هناك مشاكل — تحقق من اللوجات${NC}"
    fi
    echo ""
}

# ============================================================================
# PRINT SUMMARY
# ============================================================================
print_summary() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                        ${BOLD}الملخص${NC}${CYAN}                               ║${NC}"
    echo -e "${CYAN}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${CYAN}║${NC}  ${GREEN}تم إصلاحه:     ${FIXES_APPLIED}${NC}"
    echo -e "${CYAN}║${NC}  ${YELLOW}صحيح بالفعل:   ${FIXES_SKIPPED}${NC}"
    echo -e "${CYAN}║${NC}  ${RED}أخطاء:         ${ERRORS_FOUND}${NC}"

    if [[ -n "$BACKUP_DIR" ]]; then
        echo -e "${CYAN}║${NC}  ${BLUE}النسخ الاحتياطية: ${BACKUP_DIR}${NC}"
    fi

    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [[ "$DRY_RUN" == true ]]; then
        echo -e "${YELLOW}${BOLD}هذه معاينة فقط — لم يتم تطبيق أي تغييرات.${NC}"
        echo -e "${YELLOW}شغّل بدون --dry-run لتطبيق الإصلاحات.${NC}"
        echo ""
    fi
}

# ============================================================================
# MAIN
# ============================================================================
main() {
    detect_environment
    parse_args "$@"
    print_header

    # Special modes
    if [[ "$DIAGNOSE_ONLY" == true ]]; then
        run_diagnose
        exit 0
    fi

    if [[ "$VERIFY_ONLY" == true ]]; then
        run_verify
        exit 0
    fi

    # Run fixes
    echo -e "${CYAN}${BOLD}جارٍ تطبيق الإصلاحات...${NC}"
    echo ""

    case "$FIX_TARGET" in
        all)
            fix_ssl
            fix_pjsip
            fix_opus
            fix_transport
            fix_ami
            fix_security
            ;;
        ssl)       fix_ssl ;;
        pjsip)     fix_pjsip ;;
        opus)      fix_opus ;;
        transport) fix_transport ;;
        ami)       fix_ami ;;
        security)  fix_security ;;
        *)
            echo -e "${RED}هدف غير معروف: $FIX_TARGET${NC}"
            echo -e "الأهداف المتاحة: ssl, pjsip, opus, transport, ami, security"
            exit 1 ;;
    esac

    print_summary

    # Reload if requested
    if [[ "$DO_RELOAD" == true ]] && [[ "$FIXES_APPLIED" -gt 0 ]]; then
        reload_asterisk
    elif [[ "$DO_RELOAD" == true ]] && [[ "$FIXES_APPLIED" -eq 0 ]]; then
        echo -e "${YELLOW}لم يتم تطبيق إصلاحات — لا حاجة لإعادة التحميل${NC}"
        echo ""
    elif [[ "$FIXES_APPLIED" -gt 0 ]] && [[ "$DRY_RUN" == false ]]; then
        echo -e "${YELLOW}${BOLD}لتطبيق التغييرات، أعد تحميل Asterisk:${NC}"
        if [[ "$CAN_CLI" == true ]]; then
            echo -e "  ${CYAN}asterisk -rx 'core reload'${NC}"
            echo -e "  أو أضف ${CYAN}--reload${NC} للسكريبت"
        else
            echo -e "  داخل حاوية FreePBX:"
            echo -e "  ${CYAN}asterisk -rx 'core reload'${NC}"
            echo -e "  ${CYAN}fwconsole reload${NC}"
        fi
        echo ""
    fi
}

main "$@"
