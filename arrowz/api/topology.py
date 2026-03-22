"""
Topology API v2 — Comprehensive network topology data for visual graph.
Aggregates ALL modules: VPN, PBX, Network, WiFi, Firewall, Clients, Monitoring.
Returns a unified graph-ready structure with nodes, edges, groups, and metadata.
"""
import frappe
from frappe import _


@frappe.whitelist()
def get_topology_data():
    """
    Full topology: nodes grouped as sub-networks, edges for relationships,
    plus workspace_links for standalone actions and summary stats.
    """
    frappe.only_for(["System Manager", "Network Manager", "Network User"])

    user_roles = frappe.get_roles(frappe.session.user)
    can_write = "System Manager" in user_roles or "Network Manager" in user_roles

    data = {
        # Core infrastructure
        "server_config": get_server_config(),
        "boxes": get_boxes(),
        "interfaces": get_interfaces(),
        "wan_connections": get_wan_connections(),
        "lan_networks": get_lan_networks(),

        # VPN
        "vpn_servers": get_vpn_servers(),
        "vpn_peers": get_vpn_peers(),
        "site_to_site_tunnels": get_site_to_site_tunnels(),

        # PBX / VoIP
        "extensions": get_extensions(),
        "trunks": get_trunks(),
        "inbound_routes": get_inbound_routes(),
        "outbound_routes": get_outbound_routes(),

        # Omni & Meetings
        "omni_providers": get_omni_providers(),
        "meeting_rooms": get_meeting_rooms(),

        # WiFi
        "wifi_networks": get_wifi_networks(),
        "wifi_aps": get_wifi_aps(),

        # Firewall
        "firewall_zones": get_firewall_zones(),

        # Clients
        "network_clients": get_network_clients(),

        # Monitoring
        "active_alerts": get_active_alerts(),
        "wan_health": get_wan_health(),

        # Metadata
        "workspace_links": get_workspace_links(),
        "permissions": {
            "can_write": can_write,
            "user": frappe.session.user,
            "roles": user_roles,
        },
        "summary": get_summary_stats(),
    }

    return data


# ---------------------------------------------------------------------------
# Data fetchers — each returns [] on missing doctype / errors
# ---------------------------------------------------------------------------

def _safe_get_all(doctype, **kwargs):
    """Safely fetch records, returning [] if doctype missing or error."""
    try:
        if not frappe.db.exists("DocType", doctype):
            return []
        return frappe.get_all(doctype, **kwargs)
    except Exception:
        return []


def get_server_config():
    try:
        if frappe.db.exists("DocType", "AZ Server Config"):
            doc = frappe.get_all("AZ Server Config", fields=["name", "server_name",
                "server_type", "is_active", "is_default", "display_name",
                "host", "port", "protocol", "websocket_url", "sip_domain",
                "webrtc_enabled", "ami_enabled", "ami_host", "ami_port",
                "om_enabled", "om_url", "connection_status", "last_health_check"],
                limit=1)
            return doc[0] if doc else {}
    except Exception:
        pass
    return {}


def get_boxes():
    return _safe_get_all("Arrowz Box",
        fields=["name", "box_name", "device_type", "box_ip",
                 "status", "sync_enabled", "last_sync_at", "api_port",
                 "location", "customer", "hardware_profile",
                 "engine_status", "last_heartbeat"],
        order_by="creation desc")


def get_interfaces():
    return _safe_get_all("Network Interface",
        fields=["name", "interface_name", "arrowz_box", "interface_type",
                 "ip_address", "status", "speed", "mac_address",
                 "role", "mtu"],
        order_by="arrowz_box asc, interface_name asc")


def get_wan_connections():
    return _safe_get_all("WAN Connection",
        fields=["name", "wan_name", "arrowz_box", "interface",
                 "ip_address", "gateway", "status",
                 "connection_type", "enabled", "priority",
                 "uptime_percentage", "current_ip"],
        order_by="creation desc")


def get_lan_networks():
    return _safe_get_all("LAN Network",
        fields=["name", "network_name", "arrowz_box", "interface",
                 "ip_address", "subnet_mask", "vlan_id", "enable_dhcp",
                 "enabled", "firewall_zone"],
        order_by="creation desc")


def get_vpn_servers():
    return _safe_get_all("VPN Server",
        fields=["name", "server_name", "arrowz_box", "vpn_type",
                 "enabled", "status", "listen_port", "server_address",
                 "endpoint", "dns_servers", "connected_peers",
                 "mtu", "keepalive"],
        order_by="creation desc")


def get_vpn_peers():
    return _safe_get_all("VPN Peer",
        fields=["name", "peer_name", "vpn_server",
                 "enabled", "status", "allowed_ips",
                 "endpoint", "network_client", "customer",
                 "last_handshake", "bytes_received", "bytes_sent"],
        order_by="creation desc")


def get_site_to_site_tunnels():
    return _safe_get_all("Site to Site Tunnel",
        fields=["name", "tunnel_name", "arrowz_box",
                 "remote_endpoint", "remote_public_key",
                 "local_subnet", "remote_subnet",
                 "enabled", "status", "vpn_type",
                 "listen_port", "keepalive",
                 "last_handshake", "bytes_in", "bytes_out"],
        order_by="creation desc")


def get_extensions():
    return _safe_get_all("AZ Extension",
        fields=["name", "extension", "display_name", "user",
                 "status", "extension_type", "is_active", "server",
                 "sync_status", "last_registered", "registration_ip"],
        order_by="extension asc")


def get_trunks():
    return _safe_get_all("AZ Trunk",
        fields=["name", "trunk_name", "trunk_type", "provider",
                 "status", "server", "host", "port", "transport",
                 "max_channels", "current_channels", "priority"],
        order_by="creation desc")


def get_inbound_routes():
    return _safe_get_all("AZ Inbound Route",
        fields=["name", "route_name", "did_pattern", "destination_type",
                 "destination", "is_enabled", "server", "trunk",
                 "priority"],
        order_by="creation desc", limit=20)


def get_outbound_routes():
    return _safe_get_all("AZ Outbound Route",
        fields=["name", "route_name", "primary_trunk", "dial_pattern",
                 "is_enabled", "server", "prepend", "strip_digits",
                 "priority"],
        order_by="priority asc", limit=20)


def get_omni_providers():
    return _safe_get_all("AZ Omni Provider",
        fields=["name", "provider_name", "provider_type", "is_enabled",
                 "icon", "color", "base_url"],
        order_by="creation desc")


def get_meeting_rooms():
    return _safe_get_all("AZ Meeting Room",
        fields=["name", "room_name", "room_type", "status",
                 "max_participants", "is_permanent", "organizer",
                 "server_config"],
        order_by="creation desc")


def get_wifi_networks():
    return _safe_get_all("WiFi Network",
        fields=["name", "ssid", "arrowz_box",
                 "encryption", "enabled", "band", "channel",
                 "max_clients", "status", "hotspot_profile"],
        order_by="creation desc")


def get_wifi_aps():
    return _safe_get_all("WiFi Access Point",
        fields=["name", "ap_name", "arrowz_box", "mac_address",
                 "model", "location", "status", "connected_clients",
                 "last_seen", "uptime"],
        order_by="creation desc")


def get_firewall_zones():
    return _safe_get_all("Firewall Zone",
        fields=["name", "zone_name", "arrowz_box", "interfaces",
                 "default_policy", "enable_masquerade", "color",
                 "enable_logging"],
        order_by="creation desc")


def get_network_clients():
    return _safe_get_all("Network Client",
        fields=["name", "hostname", "arrowz_box", "ip_address",
                 "mac_address", "status", "client_group",
                 "connection_type", "is_blocked", "vendor",
                 "bandwidth_plan", "last_seen"],
        order_by="last_seen desc", limit=50)


def get_active_alerts():
    return _safe_get_all("Network Alert",
        fields=["name", "alert_type", "severity", "message",
                 "arrowz_box", "status", "timestamp", "creation",
                 "related_doctype", "related_name"],
        filters={"status": ["in", ["Open", "Active", "Critical"]]},
        order_by="creation desc", limit=20)


def get_wan_health():
    return _safe_get_all("WAN Health Check",
        fields=["name", "wan_connection", "arrowz_box", "status",
                 "latency_ms", "packet_loss_percent", "jitter_ms",
                 "timestamp", "public_ip"],
        order_by="timestamp desc", limit=10)


def get_workspace_links():
    """Return additional quick-links for standalone items in the topology."""
    return [
        {"label": _("Agent Dashboard"), "route": "/desk/arrowz-agent-dashboard",
         "icon": "headset", "category": "voip"},
        {"label": _("Wallboard"), "route": "/desk/arrowz-wallboard",
         "icon": "monitor", "category": "voip"},
        {"label": _("Analytics"), "route": "/desk/arrowz-analytics",
         "icon": "bar-chart", "category": "monitoring"},
        {"label": _("Call Log"), "route": "/desk/az-call-log",
         "icon": "phone", "category": "voip"},
        {"label": _("SMS Messages"), "route": "/desk/az-sms-message",
         "icon": "message-square", "category": "voip"},
        {"label": _("Bandwidth Plans"), "route": "/desk/bandwidth-plan",
         "icon": "activity", "category": "network"},
        {"label": _("Billing Plans"), "route": "/desk/billing-plan",
         "icon": "credit-card", "category": "billing"},
        {"label": _("WiFi Vouchers"), "route": "/desk/wifi-voucher",
         "icon": "wifi", "category": "wifi"},
        {"label": _("Arrowz Settings"), "route": "/desk/arrowz-settings",
         "icon": "settings", "category": "config"},
        {"label": _("Network Settings"), "route": "/desk/arrowz-network-settings",
         "icon": "sliders", "category": "config"},
    ]


def get_summary_stats():
    """Quick summary counts for the status bar."""
    stats = {}
    count_map = {
        "extensions": "AZ Extension",
        "trunks": "AZ Trunk",
        "boxes": "Arrowz Box",
        "vpn_servers": "VPN Server",
        "vpn_peers": "VPN Peer",
        "tunnels": "Site to Site Tunnel",
        "wifi_networks": "WiFi Network",
        "clients": "Network Client",
        "alerts": "Network Alert",
        "call_logs_today": None,
    }
    for key, dt in count_map.items():
        if dt is None:
            continue
        try:
            if frappe.db.exists("DocType", dt):
                stats[key] = frappe.db.count(dt)
            else:
                stats[key] = 0
        except Exception:
            stats[key] = 0

    # Today's calls
    try:
        if frappe.db.exists("DocType", "AZ Call Log"):
            stats["call_logs_today"] = frappe.db.count("AZ Call Log",
                filters={"start_time": [">=", frappe.utils.today()]})
        else:
            stats["call_logs_today"] = 0
    except Exception:
        stats["call_logs_today"] = 0

    return stats
