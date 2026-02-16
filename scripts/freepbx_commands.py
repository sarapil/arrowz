#!/usr/bin/env python3
"""
FreePBX Command Generator
=========================
يولد أوامر التشخيص التي يمكن تشغيلها مباشرة على خادم FreePBX.
هذا مفيد عندما لا يتوفر وصول SSH مباشر.

Usage:
    python3 freepbx_commands.py diagnose
    python3 freepbx_commands.py port 51600
    python3 freepbx_commands.py logs
    python3 freepbx_commands.py extension 2211
"""

import sys


def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def diagnose_full():
    """Generate full diagnostic commands."""
    print_header("🔍 أوامر التشخيص الكاملة لـ FreePBX")
    print("""
انسخ والصق هذه الأوامر على خادم FreePBX واحدة تلو الأخرى:

# 1. فحص إصدار Asterisk
asterisk -rx "core show version"

# 2. فحص منافذ SIP المستمعة
asterisk -rx "pjsip show transports"

# 3. فحص إذا كان المنفذ 51600 يستمع
ss -tuln | grep -E ':(51600|5060|8089)'
# أو
netstat -tuln | grep -E ':(51600|5060|8089)'

# 4. فحص كل المنافذ المستمعة لـ Asterisk
ss -tulnp | grep asterisk

# 5. فحص تكوين PJSIP transports
cat /etc/asterisk/pjsip.transports.conf
cat /etc/asterisk/pjsip.transports_custom.conf 2>/dev/null || echo "No custom config"

# 6. فحص القنوات النشطة
asterisk -rx "core show channels"

# 7. فحص نقاط نهاية PJSIP
asterisk -rx "pjsip show endpoints"

# 8. فحص جهات الاتصال المسجلة
asterisk -rx "pjsip show contacts"

# 9. فحص إعدادات RTP
asterisk -rx "rtp show settings"

# 10. فحص سجل الأخطاء الأخير
tail -100 /var/log/asterisk/full | grep -i "error\\|warning\\|fail"

# 11. فحص إعداد WebRTC
asterisk -rx "pjsip show endpoint 2211"
""")


def diagnose_port(port):
    """Generate port-specific diagnostic commands."""
    print_header(f"🔌 فحص المنفذ {port}")
    print(f"""
# فحص إذا كان المنفذ {port} يستمع
ss -tuln | grep :{port}
netstat -tuln | grep :{port}

# فحص أي عملية تستخدم هذا المنفذ
lsof -i :{port}
fuser {port}/tcp 2>/dev/null && echo "Port in use" || echo "Port free"
fuser {port}/udp 2>/dev/null && echo "Port in use (UDP)" || echo "Port free (UDP)"

# فحص transports المكونة
asterisk -rx "pjsip show transports"

# فحص تكوين transport للمنفذ {port}
grep -r "{port}" /etc/asterisk/pjsip*.conf

# فحص سجلات Asterisk لأخطاء الربط
grep -i "bind\\|{port}\\|transport" /var/log/asterisk/full | tail -50

# فحص firewall
iptables -L -n | grep {port} || echo "No iptables rule for {port}"
firewall-cmd --list-ports 2>/dev/null | grep {port} || echo "No firewalld rule (or not using firewalld)"
""")


def diagnose_extension(ext):
    """Generate extension-specific diagnostic commands."""
    print_header(f"📞 فحص الامتداد {ext}")
    print(f"""
# فحص نقطة النهاية
asterisk -rx "pjsip show endpoint {ext}"

# فحص AOR (Address of Record)
asterisk -rx "pjsip show aor {ext}"

# فحص Auth
asterisk -rx "pjsip show auth {ext}"

# فحص حالة التسجيل
asterisk -rx "pjsip show contacts" | grep {ext}

# فحص إعدادات WebRTC للامتداد
grep -A 20 "\\[{ext}\\]" /etc/asterisk/pjsip.endpoint.conf

# فحص إعدادات AOR
grep -A 10 "\\[{ext}\\]" /etc/asterisk/pjsip.aor.conf

# البحث عن أي تكوين للامتداد
grep -r "{ext}" /etc/asterisk/pjsip*.conf | head -50
""")


def diagnose_logs():
    """Generate log viewing commands."""
    print_header("📋 أوامر عرض السجلات")
    print("""
# عرض آخر 100 سطر من السجل الكامل
tail -100 /var/log/asterisk/full

# متابعة السجل في الوقت الفعلي
tail -f /var/log/asterisk/full

# فلترة السجل لـ PJSIP فقط
tail -100 /var/log/asterisk/full | grep -i pjsip

# فلترة السجل لأخطاء فقط
tail -200 /var/log/asterisk/full | grep -i "error\\|fail\\|warning"

# فلترة السجل لـ WebRTC/ICE
tail -200 /var/log/asterisk/full | grep -i "ice\\|webrtc\\|dtls\\|srtp"

# فلترة لمكالمات معينة
tail -500 /var/log/asterisk/full | grep -i "invite\\|cancel\\|bye"

# عرض سجل الأمان
tail -50 /var/log/asterisk/security_log

# عرض سجل قناة محددة
tail -200 /var/log/asterisk/full | grep -i "PJSIP/2211"
""")


def diagnose_webrtc():
    """Generate WebRTC-specific diagnostic commands."""
    print_header("🌐 فحص تكوين WebRTC")
    print("""
# فحص تكوين http.conf للـ WebSocket
cat /etc/asterisk/http.conf

# فحص المنفذ 8089 (WebSocket)
ss -tuln | grep 8089

# فحص شهادات TLS
ls -la /etc/asterisk/keys/

# فحص إعدادات ICE/STUN/TURN
grep -i "ice\\|stun\\|turn\\|external\\|local_net" /etc/asterisk/rtp.conf

# فحص إعدادات RTP الكاملة
cat /etc/asterisk/rtp.conf

# فحص أن res_http_websocket محمل
asterisk -rx "module show like websocket"

# فحص res_pjsip_transport_websocket
asterisk -rx "module show like pjsip"

# اختبار STUN server
asterisk -rx "stun show status" 2>/dev/null || echo "STUN status command may not exist"

# فحص NAT settings
grep -i "nat\\|external\\|local" /etc/asterisk/pjsip.conf /etc/asterisk/pjsip*.conf 2>/dev/null | head -20
""")


def diagnose_rtp():
    """Generate RTP-specific diagnostic commands."""
    print_header("🎵 فحص إعدادات RTP")
    print("""
# فحص إعدادات RTP
asterisk -rx "rtp show settings"

# فحص تكوين rtp.conf
cat /etc/asterisk/rtp.conf

# فحص نطاق المنافذ المستخدمة
grep -i "rtpstart\\|rtpend\\|port" /etc/asterisk/rtp.conf

# فحص المنافذ RTP المستمعة حالياً
ss -uln | grep -E ':1[0-9]{4}' | head -20

# فحص إعدادات ICE
grep -i ice /etc/asterisk/rtp.conf

# فحص STUN server
grep -i stun /etc/asterisk/rtp.conf /etc/asterisk/pjsip*.conf 2>/dev/null
""")


def diagnose_database():
    """Generate database query commands."""
    print_header("🗄️ استعلامات قاعدة البيانات")
    print("""
# فحص قاعدة بيانات Asterisk
asterisk -rx "database show"

# فحص تخزين PJSIP
asterisk -rx "database show PJSIP"

# فحص البريد الصوتي
asterisk -rx "database show voicemail"

# استعلام قاعدة بيانات FreePBX MySQL
mysql -u root asterisk -e "SELECT * FROM kvstore WHERE module='pjsip';" 2>/dev/null || echo "Need MySQL password"

# عرض إعدادات SIP
mysql -u root asterisk -e "SELECT keyword,data FROM sip WHERE id='2211' LIMIT 50;" 2>/dev/null

# عرض كل الامتدادات
mysql -u root asterisk -e "SELECT extension,name FROM users ORDER BY extension;" 2>/dev/null
""")


def diagnose_sip_trace():
    """Generate SIP trace commands."""
    print_header("🔬 تتبع SIP")
    print("""
# تشغيل تتبع SIP (مفيد لتشخيص المكالمات)
asterisk -rx "pjsip set logger on"

# تتبع أكثر تفصيلاً
asterisk -rx "pjsip set logger verbose on"

# إيقاف التتبع
asterisk -rx "pjsip set logger off"

# مشاهدة السجل أثناء التتبع
tail -f /var/log/asterisk/full | grep -i "pjsip\\|sip\\|invite\\|register"

# تتبع باستخدام sngrep (إذا مثبت)
sngrep

# تتبع باستخدام tcpdump
tcpdump -i any -s 0 -w /tmp/sip_trace.pcap port 51600 or port 5060 or port 8089

# تشغيل debug level
asterisk -rx "core set debug 5"

# إيقاف debug
asterisk -rx "core set debug 0"
""")


def diagnose_calls():
    """Generate call debugging commands."""
    print_header("📱 تشخيص المكالمات")
    print("""
# عرض القنوات النشطة
asterisk -rx "core show channels"

# عرض القنوات بتفصيل
asterisk -rx "core show channels verbose"

# عرض مكالمات PJSIP
asterisk -rx "pjsip show channels"

# متابعة القنوات الجديدة
asterisk -rx "core set verbose 5"

# فحص CDR
asterisk -rx "cdr show status"

# فحص المكالمات المعلقة
asterisk -rx "core show calls"

# فحص Bridges
asterisk -rx "bridge show all"

# قطع مكالمة معينة (استبدل CHANNEL_NAME)
# asterisk -rx "channel request hangup PJSIP/2211-00000001"
""")


def diagnose_reload():
    """Generate reload commands."""
    print_header("🔄 أوامر إعادة التحميل")
    print("""
# إعادة تحميل PJSIP
asterisk -rx "pjsip reload"
# أو
asterisk -rx "module reload res_pjsip.so"

# إعادة تحميل HTTP (للـ WebSocket)
asterisk -rx "module reload res_http_websocket.so"

# إعادة تحميل RTP
asterisk -rx "module reload"

# إعادة تحميل الكل
asterisk -rx "core reload"

# إعادة قراءة التكوين
asterisk -rx "config reload"

# ⚠️ إعادة تشغيل Asterisk (استخدم بحذر)
# fwconsole restart

# إعادة تحميل FreePBX
fwconsole reload
""")


def main():
    if len(sys.argv) < 2:
        print("""
FreePBX Command Generator
=========================
يولد أوامر التشخيص التي يمكن تشغيلها على خادم FreePBX.

الاستخدام:
    python3 freepbx_commands.py <command> [args]

الأوامر المتاحة:
    diagnose          - أوامر التشخيص الكاملة
    port <number>     - فحص منفذ محدد
    extension <ext>   - فحص امتداد محدد
    logs              - أوامر عرض السجلات
    webrtc            - فحص تكوين WebRTC
    rtp               - فحص إعدادات RTP
    database          - استعلامات قاعدة البيانات
    sip-trace         - تتبع SIP
    calls             - تشخيص المكالمات
    reload            - أوامر إعادة التحميل
    all               - كل الأوامر معاً

أمثلة:
    python3 freepbx_commands.py port 51600
    python3 freepbx_commands.py extension 2211
    python3 freepbx_commands.py diagnose
""")
        return

    command = sys.argv[1].lower()

    if command == "diagnose":
        diagnose_full()
    elif command == "port":
        port = sys.argv[2] if len(sys.argv) > 2 else "51600"
        diagnose_port(port)
    elif command == "extension":
        ext = sys.argv[2] if len(sys.argv) > 2 else "2211"
        diagnose_extension(ext)
    elif command == "logs":
        diagnose_logs()
    elif command == "webrtc":
        diagnose_webrtc()
    elif command == "rtp":
        diagnose_rtp()
    elif command == "database":
        diagnose_database()
    elif command == "sip-trace":
        diagnose_sip_trace()
    elif command == "calls":
        diagnose_calls()
    elif command == "reload":
        diagnose_reload()
    elif command == "all":
        diagnose_full()
        diagnose_logs()
        diagnose_webrtc()
        diagnose_rtp()
        diagnose_sip_trace()
        diagnose_calls()
        diagnose_database()
        diagnose_reload()
    else:
        print(f"❌ أمر غير معروف: {command}")
        print("استخدم 'python3 freepbx_commands.py' لعرض المساعدة")


if __name__ == "__main__":
    main()
