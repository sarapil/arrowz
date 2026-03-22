// Copyright (c) 2026, Arrowz and contributors
// For license information, please see license.txt

frappe.ui.form.on("VPN Access Policy", {
	refresh(frm) {
		// Status indicator
		if (frm.doc.enabled) {
			frm.dashboard.set_headline(
				`<span class="indicator-pill green">${__("Active")}</span>`
			);
		} else {
			frm.dashboard.set_headline(
				`<span class="indicator-pill grey">${__("Disabled")}</span>`
			);
		}

		// Validity info
		if (frm.doc.valid_from || frm.doc.valid_until) {
			let validity_text = "";
			if (frm.doc.valid_from && frm.doc.valid_until) {
				validity_text = __("Valid: {0} → {1}", [frm.doc.valid_from, frm.doc.valid_until]);
			} else if (frm.doc.valid_from) {
				validity_text = __("Valid from: {0}", [frm.doc.valid_from]);
			} else {
				validity_text = __("Valid until: {0}", [frm.doc.valid_until]);
			}

			const today = frappe.datetime.get_today();
			let expired = false;
			if (frm.doc.valid_until && frm.doc.valid_until < today) {
				expired = true;
			}
			frm.dashboard.add_indicator(validity_text, expired ? "red" : "blue");
		}

		if (!frm.is_new()) {
			// Show linked peers count
			frappe.db.count("VPN Peer", {
				access_policy: frm.doc.name,
				enabled: 1,
			}).then((count) => {
				if (count > 0) {
					frm.dashboard.add_indicator(
						__("{0} active peers using this policy", [count]),
						count >= (frm.doc.max_connections || 999) ? "orange" : "green"
					);
				}
			});

			// View linked peers
			frm.add_custom_button(__("View Peers"), () => {
				frappe.set_route("List", "VPN Peer", {
					access_policy: frm.doc.name,
				});
			});

			// View Server
			if (frm.doc.vpn_server) {
				frm.add_custom_button(__("View Server"), () => {
					frappe.set_route("Form", "VPN Server", frm.doc.vpn_server);
				});
			}
		}
	},

	valid_from(frm) {
		_validate_dates(frm);
	},

	valid_until(frm) {
		_validate_dates(frm);
	},
});

function _validate_dates(frm) {
	if (frm.doc.valid_from && frm.doc.valid_until) {
		if (frm.doc.valid_from > frm.doc.valid_until) {
			frappe.show_alert({
				message: __("Valid From must be before Valid Until"),
				indicator: "orange",
			});
		}
	}
}
