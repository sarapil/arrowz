"""
Seed VPN data into Frappe — matching the real OpenVPN Static Key setup on FreePBX container.

Usage:
    bench --site dev.localhost execute arrowz.scripts.seed_vpn_data.seed
"""
import frappe


def seed():
    """Create/update VPN Server + Peer records matching the live OpenVPN setup."""
    frappe.flags.ignore_permissions = True

    # ─── 1. Ensure an Arrowz Box exists for the PBX ───
    pbx_box_name = "PBX Server"
    if not frappe.db.exists("Arrowz Box", pbx_box_name):
        box = frappe.get_doc({
            "doctype": "Arrowz Box",
            "box_name": pbx_box_name,
            "device_type": "Linux Box",
            "box_ip": "157.173.125.136",
            "management_ip": "172.21.0.2",
            "enabled": 1,
        })
        box.insert(ignore_if_duplicate=True)
        print(f"✅ Created Arrowz Box: {pbx_box_name}")
    else:
        print(f"⏭️  Arrowz Box '{pbx_box_name}' already exists")

    # ─── 2. Remove old WireGuard VPN Server if exists ───
    old_wg = "PBX-WireGuard"
    if frappe.db.exists("VPN Server", old_wg):
        # Delete peers linked to old server first
        old_peers = frappe.get_all("VPN Peer", filters={"vpn_server": old_wg}, pluck="name")
        for p in old_peers:
            frappe.delete_doc("VPN Peer", p, force=True)
            print(f"🗑️  Deleted old VPN Peer: {p}")
        frappe.delete_doc("VPN Server", old_wg, force=True)
        print(f"🗑️  Deleted old VPN Server: {old_wg}")

    # ─── 3. Create OpenVPN Static Key Server ───
    vpn_server_name = "PBX-OpenVPN"
    if not frappe.db.exists("VPN Server", vpn_server_name):
        srv = frappe.get_doc({
            "doctype": "VPN Server",
            "server_name": vpn_server_name,
            "arrowz_box": pbx_box_name,
            "vpn_type": "OpenVPN",
            "enabled": 1,
            "status": "Running",
            "listen_port": 51820,
            "server_address": "10.10.0.1/24",
            "endpoint": "157.173.125.136:51820",
            "dns_servers": "1.1.1.1",
            "mtu": 1500,
            "keepalive": 10,
            "connected_peers": 1,
        })
        srv.insert(ignore_if_duplicate=True)
        print(f"✅ Created VPN Server: {vpn_server_name}")
    else:
        # Update existing
        srv = frappe.get_doc("VPN Server", vpn_server_name)
        srv.vpn_type = "OpenVPN"
        srv.status = "Running"
        srv.connected_peers = 1
        srv.save()
        print(f"✅ Updated VPN Server: {vpn_server_name}")

    # ─── 4. Create arkan VPN Peer ───
    arkan_peer_exists = frappe.db.exists("VPN Peer", {"peer_name": "arkan"})
    if not arkan_peer_exists:
        peer = frappe.get_doc({
            "doctype": "VPN Peer",
            "peer_name": "arkan",
            "vpn_server": vpn_server_name,
            "enabled": 1,
            "status": "Connected",
            "allowed_ips": "10.10.0.2/32",
            "public_key": "static-key-mode",
            "dns": "1.1.1.1",
            "keepalive": 10,
            "notes": "OpenVPN static key peer — anti-DPI, no handshake",
        })
        peer.insert(ignore_if_duplicate=True)
        print(f"✅ Created VPN Peer: arkan (10.10.0.2)")
    else:
        print(f"⏭️  VPN Peer 'arkan' already exists")

    # ─── 5. Clean up old admin peer ───
    admin_peer = frappe.db.exists("VPN Peer", {"peer_name": "admin"})
    if admin_peer:
        frappe.delete_doc("VPN Peer", admin_peer, force=True)
        print(f"🗑️  Deleted old VPN Peer: admin")

    frappe.db.commit()
    print("\n🎉 VPN seed data complete!")
    print(f"   VPN Servers: {frappe.db.count('VPN Server')}")
    print(f"   VPN Peers:   {frappe.db.count('VPN Peer')}")
