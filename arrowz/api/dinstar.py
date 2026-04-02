# Copyright (c) 2026, Arrowz Team
# License: MIT

"""
Dinstar API — Frappe Whitelisted Endpoints

Provides REST API endpoints for the Dinstar GSM Gateway dashboard.
All endpoints require authentication and "System Manager" or "Network Manager" role.

Endpoints:
    GET  /api/method/arrowz.api.dinstar.get_status           → Full device status
    GET  /api/method/arrowz.api.dinstar.get_port_status       → Per-port GSM status
    GET  /api/method/arrowz.api.dinstar.get_call_stats        → Call statistics
    GET  /api/method/arrowz.api.dinstar.get_sip_config        → SIP configuration
    GET  /api/method/arrowz.api.dinstar.get_media_config      → Media/codec config
    GET  /api/method/arrowz.api.dinstar.get_network_config    → Network settings
    GET  /api/method/arrowz.api.dinstar.get_sms_overview      → SMS overview
    POST /api/method/arrowz.api.dinstar.send_sms              → Send SMS
    POST /api/method/arrowz.api.dinstar.control_module        → Reset/Block GSM module
    POST /api/method/arrowz.api.dinstar.update_sip_config     → Update SIP settings
    POST /api/method/arrowz.api.dinstar.update_media_config   → Update media settings
    GET  /api/method/arrowz.api.dinstar.test_connection       → Test device connectivity
    GET  /api/method/arrowz.api.dinstar.get_topology_node     → Topology graph data
"""

import frappe
from frappe import _
from typing import Dict, Any, Optional
import json


def _get_client():
    """
    Create a DinstarClient from AZ Server Config or site_config.
    
    Connectivity path:
        Frappe container (172.22.0.3) → FreePBX container (172.22.0.2:10443)
        → socat proxy → OpenVPN tun1 → Dinstar (10.10.1.2:443)
    
    Looks for Dinstar connection settings in this order:
    1. AZ Server Config doctype (if exists) with dinstar_* fields
    2. site_config.json dinstar_* keys
    3. Fallback: FreePBX proxy at 172.22.0.2:10443
    """
    from arrowz.integrations.dinstar.client import DinstarClient

    # Try AZ Server Config first
    host = None
    username = "admin"
    password = "admin"
    protocol = "https"

    try:
        if frappe.db.exists("DocType", "AZ Server Config"):
            configs = frappe.get_all(
                "AZ Server Config",
                filters={"is_active": 1},
                fields=["name"],
                limit=1,
            )
            if configs:
                doc = frappe.get_doc("AZ Server Config", configs[0].name)
                host = getattr(doc, "dinstar_host", None) or getattr(doc, "dinstar_ip", None)
                username = getattr(doc, "dinstar_username", None) or "admin"
                # Only attempt get_password if the field actually exists on the doctype
                if doc.meta.has_field("dinstar_password"):
                    try:
                        password = doc.get_password("dinstar_password") or "admin"
                    except Exception:
                        pass
    except Exception:
        pass

    # Fallback to site_config
    if not host:
        host = frappe.conf.get("dinstar_host", "172.22.0.2")
        username = frappe.conf.get("dinstar_username", "admin")
        password = frappe.conf.get("dinstar_password", "admin")
        protocol = frappe.conf.get("dinstar_protocol", "https")

    # Default port: 10443 = socat proxy in FreePBX container
    # (FreePBX:10443 → Dinstar:443 via OpenVPN tun1)
    port = frappe.conf.get("dinstar_port", 10443)
    if isinstance(port, str):
        port = int(port)

    client = DinstarClient(
        host=host,
        username=username,
        password=password,
        protocol=protocol,
        verify_ssl=False,
        timeout=15,
        port=port,
    )
    return client


def _check_permission():
    """Check user has admin/network manager role."""


# ═══════════════════════════════════════════════════════════════════
# READ ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_status():
    """
    Get comprehensive Dinstar device status for dashboard.
    Returns system info, port status, call stats, configs, and health score.
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    _check_permission()
    try:
        client = _get_client()
        return client.get_full_status()
    except Exception as e:
        frappe.log_error(f"Dinstar status error: {str(e)}", "Dinstar API Error")
        return {"error": str(e), "device_health": {"status": "unreachable", "score": 0}}


@frappe.whitelist()
def get_port_status():
    """Get per-port GSM module status with SIM, power, signal info."""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        return {
            "ports": client.get_port_status(),
            "port_info": client.get_port_info(),
        }
    except Exception as e:
        frappe.log_error(f"Dinstar port status error: {str(e)}", "Dinstar API Error")
        return {"error": str(e), "ports": [], "port_info": []}


@frappe.whitelist()
def get_call_stats():
    """Get per-port call statistics with totals."""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        return client.get_call_stats()
    except Exception as e:
        frappe.log_error(f"Dinstar call stats error: {str(e)}", "Dinstar API Error")
        return {"error": str(e), "ports": [], "totals": {}}


@frappe.whitelist()
def get_ecc_stats():
    """Get per-port error cause code statistics."""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        return client.get_ecc_stats()
    except Exception as e:
        return {"error": str(e)}


@frappe.whitelist()
def get_sip_config():
    """Get SIP proxy, timers, and feature configuration."""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        return client.get_sip_config()
    except Exception as e:
        return {"error": str(e)}


@frappe.whitelist()
def get_media_config():
    """Get media/codec configuration."""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        return client.get_media_config()
    except Exception as e:
        return {"error": str(e)}


@frappe.whitelist()
def get_network_config():
    """Get WAN/LAN network configuration."""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        return {
            "network": client.get_network_config(),
            "management": client.get_management_config(),
        }
    except Exception as e:
        return {"error": str(e)}


@frappe.whitelist()
def get_sms_overview():
    """Get SMS overview: per-port counts, routing rules."""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        return {
            "overview": client.get_sms_overview(),
            "routing": client.get_sms_routing(),
        }
    except Exception as e:
        return {"error": str(e)}


@frappe.whitelist()
def get_gsm_status():
    """Get GSM-specific data: operate rules, events."""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        return {
            "rules": client.get_gsm_operate_rules(),
            "events": client.get_gsm_events(),
        }
    except Exception as e:
        return {"error": str(e)}


@frappe.whitelist()
def get_vpn_status():
    """Get VPN configuration and connection status."""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        return client.get_vpn_config()
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════
# WRITE / CONTROL ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def send_sms(port, number, message, encoding="ASCII"):
    """
    Send SMS from a specific GSM port.
    
    Args:
        port: GSM port index (0-7)
        number: Destination phone number
        message: SMS text
        encoding: ASCII or UCS2
    """
    frappe.only_for(["System Manager"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        result = client.send_sms(int(port), number, message, encoding)
        frappe.logger().info(f"Dinstar SMS sent: port={port}, to={number}")
        return {"status": "sent", "response": result}
    except Exception as e:
        frappe.log_error(f"Dinstar SMS error: {str(e)}", "Dinstar SMS Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def control_module(port, action):
    """
    Control a GSM module: reset, block, or unblock.
    
    Args:
        port: GSM port index (0-7)
        action: "reset", "block", "unblock", "block_call", "unblock_call", "power_on", "power_off"
    """
    frappe.only_for(["System Manager"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        port = int(port)

        actions = {
            "reset": client.reset_module,
            "block": client.block_module,
            "unblock": client.unblock_module,
            "block_call": client.block_call,
            "unblock_call": client.unblock_call,
            "power_on": client.power_on_module,
            "power_off": client.power_off_module,
        }

        if action not in actions:
            return {"status": "error", "message": f"Unknown action: {action}"}

        result = actions[action](port)
        frappe.logger().info(f"Dinstar module control: port={port}, action={action}")
        return {"status": "ok", "action": action, "port": port, "response": result}

    except Exception as e:
        frappe.log_error(f"Dinstar control error: {str(e)}", "Dinstar Control Error")
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def update_sip_config(**kwargs):
    """Update SIP configuration. Pass field names and values as kwargs."""
    frappe.only_for(["System Manager"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        # Filter out frappe internals
        clean = {k: v for k, v in kwargs.items() if not k.startswith("_") and k != "cmd"}
        result = client.set_sip_config(**clean)
        return {"status": "ok", "response": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def update_media_config(**kwargs):
    """Update media/codec configuration."""
    frappe.only_for(["System Manager"])
    _check_permission()
    try:
        client = _get_client()
        client.login()
        clean = {k: v for k, v in kwargs.items() if not k.startswith("_") and k != "cmd"}
        result = client.set_media_config(**clean)
        return {"status": "ok", "response": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@frappe.whitelist()
def test_connection():
    """Test connectivity to the Dinstar device."""
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    _check_permission()
    try:
        client = _get_client()
        return client.test_connection()
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════════════════════════════════
# TOPOLOGY INTEGRATION
# ═══════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_topology_node():
    """
    Get Dinstar device data formatted for the topology graph.
    
    Returns a node dict compatible with arrowz_topology:
    {
        "node": { id, label, type, data },
        "child_nodes": [ port nodes ],
        "edges": [ connections ],
    }
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    _check_permission()
    try:
        client = _get_client()
        # Use shorter timeout for topology — avoids blocking page load
        client.timeout = 6
        client.login()

        sys_info = client.get_system_info()
        ports = client.get_port_status()
        port_info = client.get_port_info()

        # Main gateway node
        total_ports = sys_info.get("TotalPort", "8")
        uptime = sys_info.get("uptime_formatted", "unknown")
        vpn = sys_info.get("VPNEnable", "")
        sim_count = sum(1 for p in ports if p.get("has_sim"))
        powered = sum(1 for p in ports if p.get("is_powered"))

        gateway_node = {
            "id": "dinstar-gw",
            "label": f"Dinstar UC2000-VE ({total_ports}P)",
            "type": "az-dinstar-gw",
            "data": {
                "total_ports": int(total_ports),
                "uptime": uptime,
                "vpn_enabled": vpn == "checked",
                "wan_mode": sys_info.get("WanMode", ""),
                "sim_count": sim_count,
                "powered_count": powered,
                "ntp_time": sys_info.get("NtpTime", ""),
            },
        }

        # Port nodes
        child_nodes = []
        edges = []
        for i, port in enumerate(ports):
            pi = port_info[i] if i < len(port_info) else {}
            sip_acc = pi.get("sip_account", f"gsm-port{i+1}")
            is_powered = port.get("is_powered", False)
            has_sim = port.get("has_sim", False)

            status = "powered_off"
            if is_powered and has_sim:
                status = "active"
            elif is_powered and not has_sim:
                status = "no_sim"
            elif not is_powered and has_sim:
                status = "powered_off_sim"

            node = {
                "id": f"dinstar-port-{i}",
                "label": f"Port {i} ({sip_acc})",
                "type": "az-dinstar-port",
                "data": {
                    "port_index": i,
                    "sip_account": sip_acc,
                    "status": status,
                    "is_powered": is_powered,
                    "has_sim": has_sim,
                    "smsc": port.get("SMSC", "") or port.get("szSMSC", ""),
                    "band_type": port.get("band_type_label", ""),
                    "network_mode": port.get("network_mode_label", ""),
                    "tx_gain": port.get("TxGain", ""),
                    "rx_gain": port.get("RxGain", ""),
                    "module_power": port.get("Modulepower", ""),
                },
            }
            child_nodes.append(node)
            edges.append({
                "source": "dinstar-gw",
                "target": f"dinstar-port-{i}",
                "type": "az-manages",
            })

        return {
            "node": gateway_node,
            "child_nodes": child_nodes,
            "edges": edges,
        }

    except Exception as e:
        frappe.log_error(f"Dinstar topology error: {str(e)}", "Dinstar Topology Error")
        return {
            "node": {
                "id": "dinstar-gw",
                "label": "Dinstar (Offline)",
                "type": "az-dinstar-gw",
                "data": {"status": "offline", "error": str(e)},
            },
            "child_nodes": [],
            "edges": [],
        }
