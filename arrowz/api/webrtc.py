# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz WebRTC API
Handles all WebRTC-related operations including call initiation, management, and JsSIP integration.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def get_webrtc_config(extension_name=None):
    """
    Get WebRTC configuration for the current user.
    Returns SIP credentials and server configuration for JsSIP.
    
    Args:
        extension_name: Optional specific extension to use (for users with multiple extensions)
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    
    # Find user's extensions
    if extension_name:
        # Use specific extension if provided
        extension = frappe.db.get_value(
            "AZ Extension",
            {"name": extension_name, "user": user, "is_active": 1},
            ["name", "extension", "sip_username", "sip_password", "server", "display_name"],
            as_dict=True
        )
    else:
        # Get default (first active) extension
        extension = frappe.db.get_value(
            "AZ Extension",
            {"user": user, "is_active": 1},
            ["name", "extension", "sip_username", "sip_password", "server", "display_name"],
            as_dict=True
        )
    
    if not extension:
        return None  # Return None instead of throwing error
    
    # Get server config
    server = frappe.get_doc("AZ Server Config", extension.server)
    
    # Get SIP domain from server config
    # Priority: sip_domain > domain from websocket_url > host
    sip_domain = server.sip_domain
    if not sip_domain and server.websocket_url:
        # Extract domain from websocket URL (e.g., wss://pbx.example.com:8089/ws -> pbx.example.com)
        import re
        match = re.search(r'wss?://([^:/]+)', server.websocket_url)
        if match:
            sip_domain = match.group(1)
    if not sip_domain:
        sip_domain = server.host
    
    # Build WebSocket servers list (direct connection to Asterisk)
    ws_servers = []
    if server.websocket_url:
        ws_servers.append(server.websocket_url)
    else:
        protocol = "wss" if getattr(server, 'use_ssl', False) else "ws"
        ws_servers.append(f"{protocol}://{server.host}:{server.port or 8089}/ws")
    
    # -----------------------------------------------------------------
    # Nginx Reverse-Proxy WSS URL (DPI Evasion)
    # -----------------------------------------------------------------
    # When configured, the softphone connects via Nginx on port 443
    # (path: /ws) instead of directly to Asterisk on port 8089.
    # This makes WebRTC traffic indistinguishable from normal HTTPS
    # to Deep Packet Inspection (DPI) systems.
    #
    # Priority for WebSocket URL resolution (frontend):
    #   1. websocket_proxy_url  → Nginx on 443 (DPI-evasion mode)
    #   2. websocket_servers[0] → Direct WSS to Asterisk on 8089
    # -----------------------------------------------------------------
    websocket_proxy_url = None
    site_config = frappe.get_site_config()
    
    # Check for proxy URL in site_config, server config, or derive from site URL
    ws_proxy = getattr(server, 'websocket_proxy_url', None) or \
               site_config.get('arrowz_websocket_proxy_url')
    
    if ws_proxy:
        websocket_proxy_url = ws_proxy
    else:
        # Auto-derive proxy URL from the actual request or site config.
        # frappe.utils.get_url() often returns http://dev.localhost:8000 from
        # site_config even when the user accesses via https://domain.com through
        # Nginx.  So we check the *request* headers first.
        try:
            derived_host = None
            is_https = False

            # 1. Check actual request headers (most reliable)
            if hasattr(frappe, 'request') and frappe.request:
                req = frappe.request
                # X-Forwarded-Proto set by Nginx / reverse proxy
                proto = (
                    req.headers.get('X-Forwarded-Proto', '')
                    or req.headers.get('X-Forwarded-Ssl', '')
                    or req.environ.get('wsgi.url_scheme', '')
                )
                if proto.lower() in ('https', 'on'):
                    is_https = True
                    # Prefer X-Forwarded-Host, then Host header
                    host = (
                        req.headers.get('X-Forwarded-Host', '')
                        or req.headers.get('Host', '')
                    ).split(':')[0]  # strip port
                    if host and host != 'localhost' \
                       and not host.startswith('127.') \
                       and not host.endswith('.localhost'):
                        derived_host = host

            # 2. Fallback: check frappe.utils.get_url()
            if not derived_host:
                from urllib.parse import urlparse
                site_url = frappe.utils.get_url()
                if site_url and 'https://' in site_url:
                    parsed = urlparse(site_url)
                    if parsed.hostname and parsed.hostname != 'localhost' \
                       and not parsed.hostname.startswith('127.') \
                       and not parsed.hostname.endswith('.localhost'):
                        derived_host = parsed.hostname
                        is_https = True

            if derived_host and is_https:
                websocket_proxy_url = f"wss://{derived_host}/ws"
        except Exception:
            pass
    
    # Build ICE servers
    ice_servers = [{"urls": "stun:stun.l.google.com:19302"}]
    
    # Get additional STUN/TURN from server config
    if server.stun_server:
        ice_servers.append({"urls": server.stun_server})
    
    if server.turn_server:
        turn_config = {"urls": server.turn_server}
        if server.turn_username:
            turn_config["username"] = server.turn_username
        if server.turn_password:
            turn_config["credential"] = server.get_password("turn_password")
        ice_servers.append(turn_config)
    
    # Get all user's extensions for dropdown
    all_extensions = frappe.get_all(
        "AZ Extension",
        filters={"user": user, "is_active": 1},
        fields=["name", "extension", "display_name", "server"],
        order_by="extension asc"
    )
    
    # Resolve PBX public IP for SDP rewriting (Docker NAT workaround)
    pbx_public_ip = None
    try:
        # Try external_ip field first (explicit override)
        pbx_public_ip = getattr(server, 'external_ip', None)
    except Exception:
        pass
    
    if not pbx_public_ip:
        try:
            import socket
            pbx_public_ip = socket.gethostbyname(sip_domain)
        except Exception:
            pbx_public_ip = server.host
    
    # Resolve adapter library name (defaults to jssip)
    webrtc_library = getattr(server, 'webrtc_library', None) or 'jssip'
    
    # -----------------------------------------------------------------
    # VPN Direct Mode Detection
    # -----------------------------------------------------------------
    # When the server has VPN mode enabled AND the client is connecting
    # from the VPN subnet, we return simplified config:
    #   - ws:// instead of wss:// (no SSL needed over VPN tunnel)
    #   - Empty ICE servers (no TURN/STUN — direct L3 reachability)
    #   - No SDP rewrite (VPN IPs are directly routable)
    #   - No Nginx proxy (direct to Asterisk HTTP on port 8088)
    # -----------------------------------------------------------------
    vpn_mode = False
    vpn_enabled = getattr(server, 'vpn_enabled', False)
    
    if vpn_enabled:
        vpn_ws_host = getattr(server, 'vpn_ws_host', None) or '10.10.0.1'
        vpn_ws_port = getattr(server, 'vpn_ws_port', None) or 8088
        vpn_sip_domain_val = getattr(server, 'vpn_sip_domain', None) or vpn_ws_host
        
        # Auto-detect: check if the client IP is on the VPN subnet
        client_ip = _get_client_ip()
        if client_ip and _is_vpn_client(client_ip):
            vpn_mode = True
        
        # Also allow explicit override via query parameter
        if frappe.form_dict.get('vpn') == '1':
            vpn_mode = True
    
    if vpn_mode:
        # Override connection settings for VPN direct mode
        sip_domain = vpn_sip_domain_val
        ws_servers = [f"ws://{vpn_ws_host}:{vpn_ws_port}/ws"]
        websocket_proxy_url = None  # bypass Nginx
        ice_servers = []             # no TURN/STUN needed
        pbx_public_ip = None         # no SDP rewrite
    
    return {
        "extension": extension.extension,
        "extension_name": extension.name,
        "extension_display_name": extension.display_name or extension.extension,
        "display_name": frappe.db.get_value("User", user, "full_name") or user,
        "sip_uri": f"sip:{extension.sip_username or extension.extension}@{sip_domain}",
        "sip_password": frappe.get_doc("AZ Extension", extension.name).get_password("sip_password"),
        "sip_domain": sip_domain,
        "websocket_servers": ws_servers,
        "websocket_proxy_url": websocket_proxy_url,
        "ice_servers": ice_servers,
        "registrar_server": f"sip:{sip_domain}",
        "transport": "ws" if vpn_mode else (server.protocol or "wss"),
        "session_timers": True,
        "session_timers_refresh_method": "invite",
        "all_extensions": all_extensions,
        "has_multiple_extensions": len(all_extensions) > 1,
        "pbx_public_ip": pbx_public_ip,
        "webrtc_library": webrtc_library,
        # VPN mode flag for frontend
        "vpn_mode": vpn_mode,
        # Connection mode indicator for frontend diagnostics
        "connection_mode": "vpn" if vpn_mode else ("nginx_proxy" if websocket_proxy_url else "direct"),
    }


@frappe.whitelist()
def get_user_extensions():
    """
    Get all active extensions for the current user.
    Used for extension selector dropdown.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    
    extensions = frappe.get_all(
        "AZ Extension",
        filters={"user": user, "is_active": 1},
        fields=["name", "extension", "display_name", "server", "status"],
        order_by="extension asc"
    )
    
    # Get server names for display
    for ext in extensions:
        ext["server_name"] = frappe.db.get_value("AZ Server Config", ext.server, "display_name") or ext.server
    
    return extensions


@frappe.whitelist()
def initiate_call(number, video=False, extension_name=None):
    """
    Initiate an outbound call.
    
    Args:
        number: The phone number or extension to call
        video: Whether to enable video
        extension_name: Optional specific extension to use
        
    Returns:
        Call log details and session info
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    
    # Get user's extension
    if extension_name:
        extension = frappe.db.get_value(
            "AZ Extension",
            {"name": extension_name, "user": user, "is_active": 1},
            ["name", "extension", "server", "enable_video"],
            as_dict=True
        )
    else:
        extension = frappe.db.get_value(
            "AZ Extension",
            {"user": user, "is_active": 1},
            ["name", "extension", "server", "enable_video"],
            as_dict=True
        )
    
    if not extension:
        frappe.throw(_("No active extension configured"))
    
    # Check video capability
    if video and not extension.enable_video:
        video = False
    
    # Create call log
    from arrowz.arrowz.doctype.az_call_log.az_call_log import create_call_log
    
    call_log = create_call_log(
        direction="Outbound",
        caller_id=extension.extension,
        callee_id=number,
        extension=extension.extension,
        server=extension.server
    )
    
    # Emit real-time event
    frappe.publish_realtime(
        "call_initiated",
        {
            "call_log": call_log.name,
            "number": number,
            "video": video
        },
        user=user
    )
    
    return {
        "call_log": call_log.name,
        "call_id": call_log.call_id,
        "target": number,
        "video": video,
        "status": "initiating"
    }


@frappe.whitelist()
def answer_call(call_id, video=False):
    """
    Answer an incoming call.
    
    Args:
        call_id: The call log ID or AMI call ID
        video: Whether to answer with video
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    
    # Update call log
    call_log = frappe.db.get_value(
        "AZ Call Log",
        {"call_id": call_id},
        "name"
    ) or call_id
    
    frappe.db.set_value("AZ Call Log", call_log, {
        "status": "In Progress",
        "answer_time": now_datetime()
    })
    
    frappe.publish_realtime(
        "call_answered",
        {"call_log": call_log},
        user=user
    )
    
    return {"status": "answered", "call_log": call_log}


@frappe.whitelist()
def hangup_call(call_id):
    """
    Hang up an active call.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    
    call_log = frappe.db.get_value(
        "AZ Call Log",
        {"call_id": call_id},
        "name"
    ) or call_id
    
    if call_log:
        doc = frappe.get_doc("AZ Call Log", call_log)
        doc.end_call("ANSWERED")
    
    return {"status": "ended", "call_log": call_log}


@frappe.whitelist()
def reject_call(call_id):
    """
    Reject an incoming call.
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    call_log = frappe.db.get_value(
        "AZ Call Log",
        {"call_id": call_id},
        "name"
    ) or call_id
    
    if call_log:
        frappe.db.set_value("AZ Call Log", call_log, {
            "status": "Missed",
            "disposition": "CANCELLED",
            "end_time": now_datetime()
        })
    
    return {"status": "rejected"}


@frappe.whitelist()
def toggle_hold(call_id, hold=True):
    """
    Put call on hold or resume.
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    call_log = frappe.db.get_value(
        "AZ Call Log",
        {"call_id": call_id},
        "name"
    ) or call_id
    
    if call_log:
        frappe.db.set_value("AZ Call Log", call_log, {
            "status": "On Hold" if hold else "In Progress"
        })
        
        frappe.publish_realtime(
            "call_hold_changed",
            {"call_log": call_log, "on_hold": hold},
            user=frappe.session.user
        )
    
    return {"status": "on_hold" if hold else "active"}


@frappe.whitelist()
def send_dtmf(call_id, digits):
    """
    Send DTMF tones during a call.
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    # DTMF is handled client-side by JsSIP
    # This logs the event server-side
    frappe.publish_realtime(
        "dtmf_sent",
        {"call_id": call_id, "digits": digits},
        user=frappe.session.user
    )
    
    return {"status": "sent", "digits": digits}


@frappe.whitelist()
def transfer_call(call_id, target, transfer_type="blind"):
    """
    Transfer an active call.
    
    Args:
        call_id: The call to transfer
        target: The target extension or number
        transfer_type: "blind" or "attended"
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    from arrowz.arrowz.doctype.az_call_transfer_log.az_call_transfer_log import initiate_transfer
    
    call_log = frappe.db.get_value(
        "AZ Call Log",
        {"call_id": call_id},
        "name"
    ) or call_id
    
    transfer_log = initiate_transfer(
        call_log=call_log,
        transfer_type=transfer_type.capitalize(),
        to_extension=target
    )
    
    frappe.publish_realtime(
        "transfer_initiated",
        {
            "call_log": call_log,
            "transfer_log": transfer_log.name,
            "target": target,
            "type": transfer_type
        },
        user=frappe.session.user
    )
    
    return {
        "status": "transferring",
        "transfer_log": transfer_log.name,
        "target": target
    }


@frappe.whitelist()
def get_active_calls():
    """
    Get all active calls for the current user.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    user = frappe.session.user
    
    extension = frappe.db.get_value(
        "AZ Extension",
        {"user": user, "is_active": 1},
        "extension"
    )
    
    if not extension:
        return []
    
    calls = frappe.get_all(
        "AZ Call Log",
        filters={
            "extension": extension,
            "status": ["in", ["Ringing", "In Progress", "On Hold"]]
        },
        fields=[
            "name", "call_id", "direction", "status",
            "caller_id", "callee_id", "contact_name",
            "start_time", "answer_time"
        ],
        order_by="start_time desc"
    )
    
    # Calculate durations
    from frappe.utils import time_diff_in_seconds
    now = now_datetime()
    
    for call in calls:
        if call.answer_time:
            call.duration = int(time_diff_in_seconds(now, call.answer_time))
        else:
            call.duration = 0
    
    return calls


@frappe.whitelist()
def show_dialer():
    """
    Show the dialer UI (for URL shortcuts).
    Returns JavaScript to execute.
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    return "frappe.require('/assets/arrowz/js/softphone.js', () => arrowz.softphone.show());"


@frappe.whitelist()
def on_incoming_call(caller_id, call_id=None):
    """
    Handle incoming call notification from WebRTC client.
    Creates a call log and publishes realtime event to other tabs/devices.
    
    Args:
        caller_id: The caller's phone number or extension
        call_id: Optional JsSIP call ID for tracking
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    import time
    
    user = frappe.session.user
    
    # Get user's extension
    extension = frappe.db.get_value(
        "AZ Extension",
        {"user": user, "is_active": 1},
        "extension"
    )
    
    # Create call log for incoming call with retry logic for deadlock
    max_retries = 3
    call_log = None
    
    for attempt in range(max_retries):
        try:
            call_log = frappe.get_doc({
                "doctype": "AZ Call Log",
                "direction": "Inbound",
                "caller_id": caller_id,
                "callee_id": extension or user,
                "status": "Ringing",
                "call_id": call_id,
                "start_time": now_datetime(),
                "extension": extension
            })
            call_log.insert(ignore_permissions=True)
            frappe.db.commit()
            break
        except frappe.QueryDeadlockError:
            frappe.db.rollback()
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff
            else:
                # On final attempt, just publish the event without creating log
                frappe.publish_realtime(
                    "incoming_call",
                    {
                        "caller_id": caller_id,
                        "call_id": call_id,
                        "call_log": None
                    },
                    user=user
                )
                return {"status": "ok", "call_log": None, "warning": "Could not create call log due to concurrent request"}
        except Exception as e:
            frappe.log_error(f"Error creating call log: {str(e)}", "Incoming Call Error")
            break
    
    # Publish realtime event to all user's sessions
    frappe.publish_realtime(
        "incoming_call",
        {
            "caller_id": caller_id,
            "call_id": call_id,
            "call_log": call_log.name if call_log else None
        },
        user=user
    )
    
    return {"status": "ok", "call_log": call_log.name if call_log else None}


@frappe.whitelist()
def update_call_answered(call_log=None, call_id=None):
    """
    Update call log when call is answered (confirmed).
    Called from WebRTC client when call connects.
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    try:
        doc = None
        if call_log:
            doc = frappe.get_doc("AZ Call Log", call_log)
        elif call_id:
            name = frappe.db.get_value("AZ Call Log", {"call_id": call_id}, "name")
            if name:
                doc = frappe.get_doc("AZ Call Log", name)
        
        if not doc:
            return {"success": False, "error": "Call log not found"}
        
        doc.status = "In Progress"
        doc.answer_time = now_datetime()
        doc.save(ignore_permissions=True)
        
        frappe.publish_realtime(
            "call_answered",
            {"call_log": doc.name, "status": "In Progress"},
            user=frappe.session.user
        )
        
        return {"success": True, "call_log": doc.name}
        
    except Exception as e:
        frappe.log_error(f"Error updating call answered: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_call_ended(call_log=None, call_id=None, duration=0, disposition="ANSWERED"):
    """
    Update call log when call ends normally.
    Called from WebRTC client when call terminates.
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    try:
        doc = None
        if call_log:
            doc = frappe.get_doc("AZ Call Log", call_log)
        elif call_id:
            name = frappe.db.get_value("AZ Call Log", {"call_id": call_id}, "name")
            if name:
                doc = frappe.get_doc("AZ Call Log", name)
        
        if not doc:
            return {"success": False, "error": "Call log not found"}
        
        doc.status = "Completed"
        doc.end_time = now_datetime()
        doc.disposition = disposition
        
        # Use provided duration or calculate from answer_time
        if duration:
            doc.duration = int(duration)
        elif doc.answer_time:
            from frappe.utils import time_diff_in_seconds
            doc.duration = int(time_diff_in_seconds(now_datetime(), doc.answer_time))
        
        doc.save(ignore_permissions=True)
        
        frappe.publish_realtime(
            "call_ended",
            {"call_log": doc.name, "duration": doc.duration, "disposition": disposition},
            user=frappe.session.user
        )
        
        return {"success": True, "call_log": doc.name, "duration": doc.duration}
        
    except Exception as e:
        frappe.log_error(f"Error updating call ended: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def update_call_failed(call_log=None, call_id=None, reason="Failed"):
    """
    Update call log when call fails.
    Called from WebRTC client when call fails or is rejected.
    """
    frappe.only_for(["AZ Manager", "System Manager"])

    try:
        doc = None
        if call_log:
            doc = frappe.get_doc("AZ Call Log", call_log)
        elif call_id:
            name = frappe.db.get_value("AZ Call Log", {"call_id": call_id}, "name")
            if name:
                doc = frappe.get_doc("AZ Call Log", name)
        
        if not doc:
            return {"success": False, "error": "Call log not found"}
        
        # Determine status based on reason
        if "Missed" in reason or "Cancelled" in reason:
            doc.status = "Missed"
            doc.disposition = "NO ANSWER"
        elif "Busy" in reason:
            doc.status = "Failed"
            doc.disposition = "BUSY"
        elif "Rejected" in reason or "Declined" in reason:
            doc.status = "Failed"
            doc.disposition = "CANCELLED"
        else:
            doc.status = "Failed"
            doc.disposition = "FAILED"
        
        doc.end_time = now_datetime()
        doc.notes = f"WebRTC: {reason}" if not doc.notes else f"{doc.notes}\nWebRTC: {reason}"
        
        doc.save(ignore_permissions=True)
        
        frappe.publish_realtime(
            "call_failed",
            {"call_log": doc.name, "reason": reason},
            user=frappe.session.user
        )
        
        return {"success": True, "call_log": doc.name}
        
    except Exception as e:
        frappe.log_error(f"Error updating call failed: {str(e)}")
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def reload_asterisk():
    """Reload Asterisk config via AMI socket connection."""
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    
    import socket as sock
    
    server = frappe.get_single("AZ Server Config")
    if not server:
        return {"success": False, "error": "AZ Server Config not found"}
    
    ami_host = server.host or "157.173.125.136"
    ami_port = int(getattr(server, 'ami_port', 5038) or 5038)
    ami_user = getattr(server, 'ami_user', '') or ''
    ami_secret = getattr(server, 'ami_secret', '') or ''
    
    if not ami_user or not ami_secret:
        return {"success": False, "error": "AMI credentials not configured in AZ Server Config"}
    
    results = []
    
    try:
        s = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        s.settimeout(10)
        s.connect((ami_host, ami_port))
        
        # Read banner
        banner = s.recv(1024).decode('utf-8', errors='replace')
        results.append(f"Banner: {banner.strip()}")
        
        # Login
        login_cmd = f"Action: Login\r\nUsername: {ami_user}\r\nSecret: {ami_secret}\r\n\r\n"
        s.sendall(login_cmd.encode())
        login_resp = s.recv(4096).decode('utf-8', errors='replace')
        results.append(f"Login: {login_resp.strip()}")
        
        if "Success" not in login_resp:
            s.close()
            return {"success": False, "error": f"AMI login failed: {login_resp.strip()}", "results": results}
        
        # Reload PJSIP
        reload_cmds = [
            ("Reload PJSIP", "Action: Command\r\nCommand: module reload res_pjsip.so\r\n\r\n"),
            ("Reload RTP", "Action: Command\r\nCommand: module reload res_rtp_asterisk.so\r\n\r\n"),
            ("Core Reload", "Action: Command\r\nCommand: core reload\r\n\r\n"),
        ]
        
        import time
        for label, cmd in reload_cmds:
            s.sendall(cmd.encode())
            time.sleep(1)
            resp = s.recv(4096).decode('utf-8', errors='replace')
            results.append(f"{label}: {resp.strip()}")
        
        # Logoff
        s.sendall(b"Action: Logoff\r\n\r\n")
        s.close()
        
        return {"success": True, "message": "Asterisk reload commands sent", "results": results}
        
    except sock.timeout:
        return {"success": False, "error": f"Connection to {ami_host}:{ami_port} timed out", "results": results}
    except ConnectionRefusedError:
        return {"success": False, "error": f"Connection refused to {ami_host}:{ami_port}", "results": results}
    except Exception as e:
        return {"success": False, "error": str(e), "results": results}


# -----------------------------------------------------------------
# VPN Detection Helpers
# -----------------------------------------------------------------

def _get_client_ip():
    """
    Extract the real client IP from the request, respecting proxy headers.
    Returns None if no request context (e.g. background job).
    """
    try:
        if not hasattr(frappe, 'request') or not frappe.request:
            return None
        
        req = frappe.request
        # X-Forwarded-For can be comma-separated: client, proxy1, proxy2
        xff = req.headers.get('X-Forwarded-For', '')
        if xff:
            return xff.split(',')[0].strip()
        
        # X-Real-IP (set by Nginx)
        xri = req.headers.get('X-Real-IP', '')
        if xri:
            return xri.strip()
        
        # Direct connection
        return req.remote_addr
    except Exception:
        return None


def _is_vpn_client(ip_str):
    """
    Check if the client IP belongs to the VPN subnet (10.10.0.0/24).
    This matches OpenVPN static-key clients on the 10.10.0.x range.
    """
    try:
        import ipaddress
        ip = ipaddress.ip_address(ip_str)
        vpn_network = ipaddress.ip_network('10.10.0.0/24')
        return ip in vpn_network
    except (ValueError, TypeError):
        return False
