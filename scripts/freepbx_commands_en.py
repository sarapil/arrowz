#!/usr/bin/env python3
"""
FreePBX Command Generator
=========================
Generates diagnostic commands to run directly on FreePBX server.
Useful when direct SSH access is not available.
"""

import sys


def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def diagnose_full():
    """Generate full diagnostic commands."""
    print_header("FULL DIAGNOSTICS - FreePBX")
    print("""
Copy and paste these commands on FreePBX server one by one:

# 1. Check Asterisk version
asterisk -rx "core show version"

# 2. Check listening SIP ports
asterisk -rx "pjsip show transports"

# 3. Check if port 51600 is listening
ss -tuln | grep -E ':(51600|5060|8089)'
# or
netstat -tuln | grep -E ':(51600|5060|8089)'

# 4. Check all Asterisk listening ports
ss -tulnp | grep asterisk

# 5. Check PJSIP transports configuration
cat /etc/asterisk/pjsip.transports.conf
cat /etc/asterisk/pjsip.transports_custom.conf 2>/dev/null || echo "No custom config"

# 6. Check active channels
asterisk -rx "core show channels"

# 7. Check PJSIP endpoints
asterisk -rx "pjsip show endpoints"

# 8. Check registered contacts
asterisk -rx "pjsip show contacts"

# 9. Check RTP settings
asterisk -rx "rtp show settings"

# 10. Check recent error logs
tail -100 /var/log/asterisk/full | grep -i "error\|warning\|fail"

# 11. Check WebRTC settings
asterisk -rx "pjsip show endpoint 2211"
""")


def diagnose_port(port):
    """Generate port-specific diagnostic commands."""
    print_header(f"PORT {port} DIAGNOSTICS")
    print(f"""
# Check if port {port} is listening
ss -tuln | grep :{port}
netstat -tuln | grep :{port}

# Check which process uses this port
lsof -i :{port}
fuser {port}/tcp 2>/dev/null && echo "Port in use" || echo "Port free"
fuser {port}/udp 2>/dev/null && echo "Port in use (UDP)" || echo "Port free (UDP)"

# Check configured transports
asterisk -rx "pjsip show transports"

# Check transport config for port {port}
grep -r "{port}" /etc/asterisk/pjsip*.conf

# Check Asterisk logs for binding errors
grep -i "bind\|{port}\|transport" /var/log/asterisk/full | tail -50

# Check firewall
iptables -L -n | grep {port} || echo "No iptables rule for {port}"
firewall-cmd --list-ports 2>/dev/null | grep {port} || echo "No firewalld rule"
""")


def diagnose_extension(ext):
    """Generate extension-specific diagnostic commands."""
    print_header(f"EXTENSION {ext} DIAGNOSTICS")
    print(f"""
# Check endpoint
asterisk -rx "pjsip show endpoint {ext}"

# Check AOR (Address of Record)
asterisk -rx "pjsip show aor {ext}"

# Check Auth
asterisk -rx "pjsip show auth {ext}"

# Check registration status
asterisk -rx "pjsip show contacts" | grep {ext}

# Check WebRTC settings for extension
grep -A 20 "\[{ext}\]" /etc/asterisk/pjsip.endpoint.conf

# Check AOR settings
grep -A 10 "\[{ext}\]" /etc/asterisk/pjsip.aor.conf

# Search for any extension config
grep -r "{ext}" /etc/asterisk/pjsip*.conf | head -50
""")


def diagnose_logs():
    """Generate log viewing commands."""
    print_header("LOG VIEWING COMMANDS")
    print("""
# View last 100 lines of full log
tail -100 /var/log/asterisk/full

# Follow log in real-time
tail -f /var/log/asterisk/full

# Filter log for PJSIP only
tail -100 /var/log/asterisk/full | grep -i pjsip

# Filter log for errors only
tail -200 /var/log/asterisk/full | grep -i "error\|fail\|warning"

# Filter log for WebRTC/ICE
tail -200 /var/log/asterisk/full | grep -i "ice\|webrtc\|dtls\|srtp"

# Filter for specific calls
tail -500 /var/log/asterisk/full | grep -i "invite\|cancel\|bye"

# View security log
tail -50 /var/log/asterisk/security_log

# View specific channel log
tail -200 /var/log/asterisk/full | grep -i "PJSIP/2211"
""")


def diagnose_webrtc():
    """Generate WebRTC-specific diagnostic commands."""
    print_header("WebRTC CONFIGURATION CHECK")
    print("""
# Check http.conf for WebSocket
cat /etc/asterisk/http.conf

# Check port 8089 (WebSocket)
ss -tuln | grep 8089

# Check TLS certificates
ls -la /etc/asterisk/keys/

# Check ICE/STUN/TURN settings
grep -i "ice\|stun\|turn\|external\|local_net" /etc/asterisk/rtp.conf

# Check full RTP settings
cat /etc/asterisk/rtp.conf

# Check res_http_websocket is loaded
asterisk -rx "module show like websocket"

# Check res_pjsip_transport_websocket
asterisk -rx "module show like pjsip"

# Check NAT settings
grep -i "nat\|external\|local" /etc/asterisk/pjsip.conf /etc/asterisk/pjsip*.conf 2>/dev/null | head -20
""")


def diagnose_rtp():
    """Generate RTP-specific diagnostic commands."""
    print_header("RTP SETTINGS CHECK")
    print("""
# Check RTP settings
asterisk -rx "rtp show settings"

# Check rtp.conf
cat /etc/asterisk/rtp.conf

# Check port range used
grep -i "rtpstart\|rtpend\|port" /etc/asterisk/rtp.conf

# Check currently listening RTP ports
ss -uln | grep -E ':1[0-9]{4}' | head -20

# Check ICE settings
grep -i ice /etc/asterisk/rtp.conf

# Check STUN server
grep -i stun /etc/asterisk/rtp.conf /etc/asterisk/pjsip*.conf 2>/dev/null
""")


def diagnose_database():
    """Generate database query commands."""
    print_header("DATABASE QUERIES")
    print("""
# Check Asterisk database
asterisk -rx "database show"

# Check PJSIP storage
asterisk -rx "database show PJSIP"

# Check voicemail
asterisk -rx "database show voicemail"

# Query FreePBX MySQL database
mysql -u root asterisk -e "SELECT * FROM kvstore WHERE module='pjsip';" 2>/dev/null || echo "Need MySQL password"

# Show SIP settings
mysql -u root asterisk -e "SELECT keyword,data FROM sip WHERE id='2211' LIMIT 50;" 2>/dev/null

# Show all extensions
mysql -u root asterisk -e "SELECT extension,name FROM users ORDER BY extension;" 2>/dev/null
""")


def diagnose_sip_trace():
    """Generate SIP trace commands."""
    print_header("SIP TRACING")
    print("""
# Enable SIP trace (useful for call debugging)
asterisk -rx "pjsip set logger on"

# More verbose tracing
asterisk -rx "pjsip set logger verbose on"

# Disable tracing
asterisk -rx "pjsip set logger off"

# Watch log while tracing
tail -f /var/log/asterisk/full | grep -i "pjsip\|sip\|invite\|register"

# Trace using sngrep (if installed)
sngrep

# Trace using tcpdump
tcpdump -i any -s 0 -w /tmp/sip_trace.pcap port 51600 or port 5060 or port 8089

# Enable debug level
asterisk -rx "core set debug 5"

# Disable debug
asterisk -rx "core set debug 0"
""")


def diagnose_calls():
    """Generate call debugging commands."""
    print_header("CALL DEBUGGING")
    print("""
# Show active channels
asterisk -rx "core show channels"

# Show channels verbose
asterisk -rx "core show channels verbose"

# Show PJSIP calls
asterisk -rx "pjsip show channels"

# Follow new channels
asterisk -rx "core set verbose 5"

# Check CDR
asterisk -rx "cdr show status"

# Check pending calls
asterisk -rx "core show calls"

# Check Bridges
asterisk -rx "bridge show all"

# Hangup specific call (replace CHANNEL_NAME)
# asterisk -rx "channel request hangup PJSIP/2211-00000001"
""")


def diagnose_reload():
    """Generate reload commands."""
    print_header("RELOAD COMMANDS")
    print("""
# Reload PJSIP
asterisk -rx "pjsip reload"
# or
asterisk -rx "module reload res_pjsip.so"

# Reload HTTP (for WebSocket)
asterisk -rx "module reload res_http_websocket.so"

# Reload RTP
asterisk -rx "module reload"

# Reload all
asterisk -rx "core reload"

# Re-read configuration
asterisk -rx "config reload"

# WARNING: Restart Asterisk (use with caution)
# fwconsole restart

# Reload FreePBX
fwconsole reload
""")


def print_quick_check():
    """Print quick check commands for immediate diagnosis."""
    print_header("QUICK CHECK - Run these first!")
    print("""
# Quick status check - copy all at once:
echo "=== Asterisk Version ===" && asterisk -rx "core show version"
echo "=== Listening Ports ===" && ss -tuln | grep -E ':(51600|5060|8089|5061)'
echo "=== PJSIP Transports ===" && asterisk -rx "pjsip show transports"
echo "=== Active Channels ===" && asterisk -rx "core show channels"
echo "=== PJSIP Contacts ===" && asterisk -rx "pjsip show contacts"
echo "=== Recent Errors ===" && tail -20 /var/log/asterisk/full | grep -i error
""")


def main():
    if len(sys.argv) < 2:
        print("""
FreePBX Command Generator
=========================
Generates diagnostic commands to run on FreePBX server.

Usage:
    python3 freepbx_commands.py <command> [args]

Available Commands:
    quick             - Quick status check commands
    diagnose          - Full diagnostic commands
    port <number>     - Check specific port (default: 51600)
    extension <ext>   - Check specific extension (default: 2211)
    logs              - Log viewing commands
    webrtc            - WebRTC configuration check
    rtp               - RTP settings check
    database          - Database query commands
    sip-trace         - SIP tracing commands
    calls             - Call debugging commands
    reload            - Reload commands
    all               - All commands together

Examples:
    python3 freepbx_commands.py quick
    python3 freepbx_commands.py port 51600
    python3 freepbx_commands.py extension 2211
    python3 freepbx_commands.py diagnose
""")
        return

    command = sys.argv[1].lower()

    if command == "quick":
        print_quick_check()
    elif command == "diagnose":
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
    elif command in ["sip-trace", "trace"]:
        diagnose_sip_trace()
    elif command == "calls":
        diagnose_calls()
    elif command == "reload":
        diagnose_reload()
    elif command == "all":
        print_quick_check()
        diagnose_full()
        diagnose_logs()
        diagnose_webrtc()
        diagnose_rtp()
        diagnose_sip_trace()
        diagnose_calls()
        diagnose_database()
        diagnose_reload()
    else:
        print(f"Unknown command: {command}")
        print("Use 'python3 freepbx_commands.py' to see help")


if __name__ == "__main__":
    main()
