// Copyright (c) 2026, Arrowz and contributors
// For license information, please see license.txt

frappe.ui.form.on("VPN Server", {
	refresh(frm) {
		// Status indicator
		if (frm.doc.status === "Running") {
			frm.dashboard.set_headline(
				`<span class="indicator-pill green">${__("Running")}</span>`
			);
		} else if (frm.doc.status === "Error") {
			frm.dashboard.set_headline(
				`<span class="indicator-pill red">${__("Error")}</span>`
			);
		} else if (frm.doc.status === "Stopped") {
			frm.dashboard.set_headline(
				`<span class="indicator-pill grey">${__("Stopped")}</span>`
			);
		}

		// Show connected peers count
		if (frm.doc.connected_peers) {
			frm.dashboard.add_indicator(
				__("{0} connected peers", [frm.doc.connected_peers]),
				frm.doc.connected_peers > 0 ? "green" : "grey"
			);
		}

		if (!frm.is_new()) {
			// Generate Keys button (WireGuard only)
			if (frm.doc.vpn_type === "WireGuard") {
				frm.add_custom_button(__("Generate Keys"), () => {
					frappe.confirm(
						__("This will regenerate the server keys. All peers will need to update their config. Continue?"),
						() => {
							frm.call("generate_keys").then(() => frm.reload_doc());
						}
					);
				}, __("Actions"));
			}

			// Restart Server button
			frm.add_custom_button(__("Restart Server"), () => {
				frm.call("restart_server").then(() => frm.reload_doc());
			}, __("Actions"));

			// View Peers shortcut
			frm.add_custom_button(__("View Peers"), () => {
				frappe.set_route("List", "VPN Peer", {
					vpn_server: frm.doc.name,
				});
			}, __("View"));

			// View Access Policies shortcut
			frm.add_custom_button(__("Access Policies"), () => {
				frappe.set_route("List", "VPN Access Policy", {
					vpn_server: frm.doc.name,
				});
			}, __("View"));

			// View Tunnels shortcut
			frm.add_custom_button(__("Site-to-Site Tunnels"), () => {
				frappe.set_route("List", "Site to Site Tunnel", {
					arrowz_box: frm.doc.arrowz_box,
				});
			}, __("View"));
		}
	},

	vpn_type(frm) {
		// Set default port based on VPN type
		if (frm.doc.vpn_type === "WireGuard" && !frm.doc.listen_port) {
			frm.set_value("listen_port", 51820);
		} else if (frm.doc.vpn_type === "OpenVPN" && !frm.doc.listen_port) {
			frm.set_value("listen_port", 1194);
		}
	},

	server_address(frm) {
		// Validate CIDR notation
		if (frm.doc.server_address && !frm.doc.server_address.includes("/")) {
			frappe.show_alert({
				message: __("Server Address should include CIDR notation (e.g. 10.10.0.1/24)"),
				indicator: "orange",
			});
		}
	},
});
