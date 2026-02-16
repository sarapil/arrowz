#!/usr/bin/env python3
"""
FreePBX Debugger Tool
=====================
A comprehensive debugging tool for FreePBX 17 integration with Arrowz.

Features:
- SSH connection to FreePBX server
- Read Asterisk logs in real-time
- Query Asterisk database (astdb)
- Execute Asterisk CLI commands
- Check SIP/PJSIP registrations and settings
- Monitor RTP ports and WebSocket connections

Usage:
    python3 freepbx_debugger.py --host pbx.tavira-group.com --user root
    
Commands:
    logs          - Tail Asterisk logs
    pjsip-status  - Show PJSIP endpoint status
    channels      - Show active channels
    rtp-check     - Check RTP settings
    db-query      - Query Asterisk database
    webrtc-check  - Check WebRTC settings
    sip-trace     - Enable SIP tracing
"""

import argparse
import subprocess
import sys
import os
from datetime import datetime

# Configuration
DEFAULT_HOST = "pbx.tavira-group.com"
DEFAULT_USER = "root"
DEFAULT_SSH_KEY = None  # Will use default SSH key if None

class FreePBXDebugger:
    def __init__(self, host, user, ssh_key=None, port=22):
        self.host = host
        self.user = user
        self.ssh_key = ssh_key
        self.port = port
        
    def _ssh_cmd(self, command, timeout=30):
        """Execute SSH command and return output."""
        ssh_args = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10"]
        
        if self.ssh_key:
            ssh_args.extend(["-i", self.ssh_key])
        
        ssh_args.extend(["-p", str(self.port), f"{self.user}@{self.host}", command])
        
        try:
            result = subprocess.run(
                ssh_args,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", -1
        except Exception as e:
            return "", str(e), -1
    
    def _asterisk_cmd(self, command):
        """Execute Asterisk CLI command."""
        return self._ssh_cmd(f'asterisk -rx "{command}"')
    
    def test_connection(self):
        """Test SSH connection to FreePBX."""
        print(f"🔌 Testing connection to {self.host}...")
        stdout, stderr, code = self._ssh_cmd("echo 'Connected!' && hostname")
        
        if code == 0:
            print(f"✅ Connected to: {stdout.strip()}")
            return True
        else:
            print(f"❌ Connection failed: {stderr}")
            return False
    
    def get_asterisk_version(self):
        """Get Asterisk version."""
        stdout, _, code = self._asterisk_cmd("core show version")
        if code == 0:
            return stdout.strip()
        return "Unknown"
    
    def tail_logs(self, lines=50, follow=False, filter_text=None):
        """Tail Asterisk full log."""
        log_file = "/var/log/asterisk/full"
        
        cmd = f"tail -n {lines}"
        if follow:
            cmd += " -f"
        cmd += f" {log_file}"
        
        if filter_text:
            cmd += f" | grep -i '{filter_text}'"
        
        print(f"📋 Tailing {log_file} (last {lines} lines)...")
        print("-" * 80)
        
        if follow:
            # For follow mode, use Popen for real-time output
            ssh_args = ["ssh", "-o", "StrictHostKeyChecking=no"]
            if self.ssh_key:
                ssh_args.extend(["-i", self.ssh_key])
            ssh_args.extend([f"{self.user}@{self.host}", cmd])
            
            try:
                process = subprocess.Popen(ssh_args, stdout=subprocess.PIPE, text=True)
                for line in process.stdout:
                    print(line, end='')
            except KeyboardInterrupt:
                print("\n\n⏹️ Stopped tailing logs.")
        else:
            stdout, stderr, code = self._ssh_cmd(cmd, timeout=60)
            if code == 0:
                print(stdout)
            else:
                print(f"❌ Error: {stderr}")
    
    def pjsip_show_endpoints(self, extension=None):
        """Show PJSIP endpoints status."""
        print("📞 PJSIP Endpoints Status:")
        print("-" * 80)
        
        if extension:
            stdout, _, _ = self._asterisk_cmd(f"pjsip show endpoint {extension}")
        else:
            stdout, _, _ = self._asterisk_cmd("pjsip show endpoints")
        
        print(stdout)
    
    def pjsip_show_registrations(self):
        """Show PJSIP registrations."""
        print("📝 PJSIP Registrations:")
        print("-" * 80)
        stdout, _, _ = self._asterisk_cmd("pjsip show registrations")
        print(stdout)
    
    def pjsip_show_contacts(self):
        """Show PJSIP contacts (registered devices)."""
        print("📱 PJSIP Contacts:")
        print("-" * 80)
        stdout, _, _ = self._asterisk_cmd("pjsip show contacts")
        print(stdout)
    
    def show_channels(self):
        """Show active channels."""
        print("📡 Active Channels:")
        print("-" * 80)
        stdout, _, _ = self._asterisk_cmd("core show channels verbose")
        print(stdout)
    
    def show_transports(self):
        """Show PJSIP transports."""
        print("🚀 PJSIP Transports:")
        print("-" * 80)
        stdout, _, _ = self._asterisk_cmd("pjsip show transports")
        print(stdout)
    
    def check_rtp_settings(self):
        """Check RTP settings."""
        print("🎵 RTP Settings:")
        print("-" * 80)
        
        # Check rtp.conf
        stdout, _, _ = self._ssh_cmd("cat /etc/asterisk/rtp.conf 2>/dev/null | grep -v '^;' | grep -v '^$'")
        print("=== rtp.conf ===")
        print(stdout)
        
        # Check current RTP debug
        stdout, _, _ = self._asterisk_cmd("rtp show settings")
        print("\n=== RTP Show Settings ===")
        print(stdout)
    
    def check_pjsip_transport_config(self):
        """Check PJSIP transport configuration."""
        print("🔧 PJSIP Transport Configuration:")
        print("-" * 80)
        
        # Get pjsip transport config
        stdout, _, _ = self._ssh_cmd("grep -A 20 'type=transport' /etc/asterisk/pjsip*.conf 2>/dev/null | head -100")
        print(stdout)
    
    def check_webrtc_extension(self, extension):
        """Check WebRTC settings for specific extension."""
        print(f"🌐 WebRTC Settings for Extension {extension}:")
        print("-" * 80)
        
        stdout, _, _ = self._asterisk_cmd(f"pjsip show endpoint {extension}")
        print(stdout)
        
        # Check aor
        print(f"\n=== AOR for {extension} ===")
        stdout, _, _ = self._asterisk_cmd(f"pjsip show aor {extension}")
        print(stdout)
        
        # Check auth
        print(f"\n=== Auth for {extension} ===")
        stdout, _, _ = self._asterisk_cmd(f"pjsip show auth {extension}")
        print(stdout)
    
    def sip_trace_start(self):
        """Start SIP tracing."""
        print("🔍 Starting SIP trace...")
        stdout, _, _ = self._asterisk_cmd("pjsip set logger on")
        print(stdout)
        print("✅ SIP tracing enabled. Check logs with: python3 freepbx_debugger.py logs --follow")
    
    def sip_trace_stop(self):
        """Stop SIP tracing."""
        print("⏹️ Stopping SIP trace...")
        stdout, _, _ = self._asterisk_cmd("pjsip set logger off")
        print(stdout)
    
    def check_port(self, port):
        """Check if a specific port is listening."""
        print(f"🔌 Checking port {port}...")
        stdout, stderr, code = self._ssh_cmd(f"ss -tlnp | grep :{port}")
        
        if stdout.strip():
            print(f"✅ Port {port} is listening:")
            print(stdout)
        else:
            print(f"❌ Port {port} is NOT listening")
            # Check if asterisk owns any relevant ports
            stdout2, _, _ = self._ssh_cmd("ss -tlnp | grep asterisk")
            if stdout2:
                print("\nAsterisk is listening on:")
                print(stdout2)
    
    def query_database(self, family=None, key=None):
        """Query Asterisk database (astdb)."""
        print("🗄️ Asterisk Database Query:")
        print("-" * 80)
        
        if family and key:
            cmd = f"database show {family}/{key}"
        elif family:
            cmd = f"database show {family}"
        else:
            # Show all families
            stdout, _, _ = self._asterisk_cmd("database show")
            print(stdout[:5000] if len(stdout) > 5000 else stdout)  # Limit output
            return
        
        stdout, _, _ = self._asterisk_cmd(cmd)
        print(stdout)
    
    def check_freepbx_settings(self):
        """Check FreePBX GUI settings via database."""
        print("⚙️ FreePBX Settings:")
        print("-" * 80)
        
        # Check SIP settings from FreePBX
        stdout, _, _ = self._ssh_cmd(
            "mysql -N -e \"SELECT keyword, data FROM asterisk.sipsettings WHERE keyword LIKE '%rtp%' OR keyword LIKE '%nat%' OR keyword LIKE '%ice%' ORDER BY keyword;\" 2>/dev/null"
        )
        if stdout.strip():
            print("=== SIP Settings (Database) ===")
            print(stdout)
        
        # Check PJSIP settings
        stdout, _, _ = self._ssh_cmd(
            "mysql -N -e \"SELECT keyword, data FROM asterisk.pjsipsettings ORDER BY keyword;\" 2>/dev/null | head -50"
        )
        if stdout.strip():
            print("\n=== PJSIP Settings (Database) ===")
            print(stdout)
    
    def restart_asterisk(self):
        """Restart Asterisk gracefully."""
        print("🔄 Restarting Asterisk...")
        stdout, stderr, code = self._asterisk_cmd("core restart gracefully")
        if code == 0:
            print("✅ Asterisk restart initiated")
        else:
            print(f"❌ Error: {stderr}")
    
    def reload_pjsip(self):
        """Reload PJSIP module."""
        print("🔄 Reloading PJSIP...")
        stdout, _, _ = self._asterisk_cmd("pjsip reload")
        print(stdout)
    
    def full_diagnostics(self, extension=None):
        """Run full diagnostics."""
        print("=" * 80)
        print("🏥 FULL FREEPBX DIAGNOSTICS")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Asterisk version
        print("1️⃣ Asterisk Version:")
        print(self.get_asterisk_version())
        print()
        
        # Transports
        print("2️⃣ PJSIP Transports:")
        self.show_transports()
        print()
        
        # Ports
        print("3️⃣ Listening Ports:")
        for port in [51600, 5060, 5061, 8089, 10500, 10700]:
            self.check_port(port)
        print()
        
        # WebRTC extension
        if extension:
            print(f"4️⃣ WebRTC Extension {extension} Details:")
            self.check_webrtc_extension(extension)
        
        # Active channels
        print("5️⃣ Active Channels:")
        self.show_channels()
        print()
        
        # RTP Settings
        print("6️⃣ RTP Settings:")
        self.check_rtp_settings()
        print()
        
        print("=" * 80)
        print("✅ Diagnostics complete!")


def main():
    parser = argparse.ArgumentParser(
        description="FreePBX Debugger Tool for Arrowz",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 freepbx_debugger.py test                    # Test connection
  python3 freepbx_debugger.py logs -n 100             # Show last 100 log lines
  python3 freepbx_debugger.py logs --follow           # Follow logs in real-time
  python3 freepbx_debugger.py logs --filter PJSIP     # Filter logs
  python3 freepbx_debugger.py pjsip-status            # Show PJSIP status
  python3 freepbx_debugger.py pjsip-status 2211       # Show extension 2211 details
  python3 freepbx_debugger.py channels                # Show active channels
  python3 freepbx_debugger.py port 51600              # Check if port 51600 is listening
  python3 freepbx_debugger.py webrtc 2211             # Check WebRTC config for 2211
  python3 freepbx_debugger.py sip-trace start         # Start SIP tracing
  python3 freepbx_debugger.py diagnose 2211           # Full diagnostics
        """
    )
    
    parser.add_argument("--host", default=DEFAULT_HOST, help="FreePBX hostname")
    parser.add_argument("--user", default=DEFAULT_USER, help="SSH username")
    parser.add_argument("--key", default=DEFAULT_SSH_KEY, help="SSH private key path")
    parser.add_argument("--port", type=int, default=22, help="SSH port")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Test connection
    subparsers.add_parser("test", help="Test SSH connection")
    
    # Logs
    logs_parser = subparsers.add_parser("logs", help="View Asterisk logs")
    logs_parser.add_argument("-n", "--lines", type=int, default=50, help="Number of lines")
    logs_parser.add_argument("-f", "--follow", action="store_true", help="Follow logs")
    logs_parser.add_argument("--filter", help="Filter logs by text")
    
    # PJSIP status
    pjsip_parser = subparsers.add_parser("pjsip-status", help="Show PJSIP status")
    pjsip_parser.add_argument("extension", nargs="?", help="Specific extension")
    
    # Channels
    subparsers.add_parser("channels", help="Show active channels")
    
    # Transports
    subparsers.add_parser("transports", help="Show PJSIP transports")
    
    # Registrations
    subparsers.add_parser("registrations", help="Show PJSIP registrations")
    
    # Contacts
    subparsers.add_parser("contacts", help="Show PJSIP contacts")
    
    # RTP
    subparsers.add_parser("rtp", help="Check RTP settings")
    
    # Port check
    port_parser = subparsers.add_parser("port", help="Check if port is listening")
    port_parser.add_argument("port_number", type=int, help="Port number to check")
    
    # WebRTC check
    webrtc_parser = subparsers.add_parser("webrtc", help="Check WebRTC settings for extension")
    webrtc_parser.add_argument("extension", help="Extension number")
    
    # SIP trace
    trace_parser = subparsers.add_parser("sip-trace", help="SIP tracing")
    trace_parser.add_argument("action", choices=["start", "stop"], help="Start or stop tracing")
    
    # Database query
    db_parser = subparsers.add_parser("db", help="Query Asterisk database")
    db_parser.add_argument("--family", help="Database family")
    db_parser.add_argument("--key", help="Database key")
    
    # FreePBX settings
    subparsers.add_parser("settings", help="Show FreePBX database settings")
    
    # Reload
    subparsers.add_parser("reload-pjsip", help="Reload PJSIP module")
    
    # Full diagnostics
    diag_parser = subparsers.add_parser("diagnose", help="Run full diagnostics")
    diag_parser.add_argument("extension", nargs="?", help="Extension to check")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    debugger = FreePBXDebugger(args.host, args.user, args.key, args.port)
    
    # Test connection first for most commands
    if args.command != "test" and not debugger.test_connection():
        print("\n❌ Cannot connect to FreePBX. Please check credentials and network.")
        return
    
    # Execute command
    if args.command == "test":
        debugger.test_connection()
        print(f"\nAsterisk: {debugger.get_asterisk_version()}")
        
    elif args.command == "logs":
        debugger.tail_logs(args.lines, args.follow, args.filter)
        
    elif args.command == "pjsip-status":
        debugger.pjsip_show_endpoints(args.extension)
        
    elif args.command == "channels":
        debugger.show_channels()
        
    elif args.command == "transports":
        debugger.show_transports()
        
    elif args.command == "registrations":
        debugger.pjsip_show_registrations()
        
    elif args.command == "contacts":
        debugger.pjsip_show_contacts()
        
    elif args.command == "rtp":
        debugger.check_rtp_settings()
        
    elif args.command == "port":
        debugger.check_port(args.port_number)
        
    elif args.command == "webrtc":
        debugger.check_webrtc_extension(args.extension)
        
    elif args.command == "sip-trace":
        if args.action == "start":
            debugger.sip_trace_start()
        else:
            debugger.sip_trace_stop()
            
    elif args.command == "db":
        debugger.query_database(args.family, args.key)
        
    elif args.command == "settings":
        debugger.check_freepbx_settings()
        
    elif args.command == "reload-pjsip":
        debugger.reload_pjsip()
        
    elif args.command == "diagnose":
        debugger.full_diagnostics(args.extension)


if __name__ == "__main__":
    main()
