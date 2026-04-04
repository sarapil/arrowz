// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

frappe.ui.form.on("Site to Site Tunnel", {
	refresh(frm) {
		// Status indicator
		const status = frm.doc.status || "Unknown";
		const colorMap = { Active: "green", Connected: "green", Disconnected: "grey", Error: "red" };
		const color = colorMap[status] || "grey";
		frm.dashboard.set_headline(
			`<span class="indicator-pill ${color}">${__(status)}</span>`
		);

		// Traffic stats
		if (frm.doc.bytes_in || frm.doc.bytes_out) {
			const rx = frappe.utils.file_size(frm.doc.bytes_in || 0);
			const tx = frappe.utils.file_size(frm.doc.bytes_out || 0);
			frm.dashboard.add_indicator(__("↓ {0} / ↑ {1}", [rx, tx]), "blue");
		}

		// Last handshake
		if (frm.doc.last_handshake) {
			frm.dashboard.add_indicator(
				__("Last handshake: {0}", [frappe.datetime.prettyDate(frm.doc.last_handshake)]),
				"grey"
			);
		}

		// Subnet info
		if (frm.doc.local_subnet && frm.doc.remote_subnet) {
			frm.dashboard.add_indicator(
				__("{0} ⇄ {1}", [frm.doc.local_subnet, frm.doc.remote_subnet]),
				"blue"
			);
		}

		if (!frm.is_new()) {
			// Check Status button
			frm.add_custom_button(__("Check Status"), () => {
				frm.call("check_status").then(() => {
					frappe.show_alert({ message: __("Status check initiated"), indicator: "blue" });
				});
			}, __("Actions"));

			// View Box
			if (frm.doc.arrowz_box) {
				frm.add_custom_button(__("View Box"), () => {
					frappe.set_route("Form", "Arrowz Box", frm.doc.arrowz_box);
				}, __("View"));
			}
		}
	},

	vpn_type(frm) {
		// Set default port based on VPN type
		if (frm.doc.vpn_type === "WireGuard" && !frm.doc.listen_port) {
			frm.set_value("listen_port", 51820);
		} else if (frm.doc.vpn_type === "IPSec" && !frm.doc.listen_port) {
			frm.set_value("listen_port", 500);
		}
	},

	local_subnet(frm) {
		_validate_subnet(frm, "local_subnet", "Local Subnet");
	},

	remote_subnet(frm) {
		_validate_subnet(frm, "remote_subnet", "Remote Subnet");
	},
});

function _validate_subnet(frm, field, label) {
	const val = frm.doc[field];
	if (val && !val.includes("/")) {
		frappe.show_alert({
			message: __("{0} should include CIDR notation (e.g. 192.168.1.0/24)", [label]),
			indicator: "orange",
		});
	}
}
