// Copyright (c) 2026, Arrowz and contributors
// For license information, please see license.txt

frappe.ui.form.on("VPN Peer", {
	refresh(frm) {
		// Status indicator
		const status = frm.doc.status || "Disconnected";
		const color = status === "Connected" ? "green" : "grey";
		frm.dashboard.set_headline(
			`<span class="indicator-pill ${color}">${__(status)}</span>`
		);

		// Traffic stats
		if (frm.doc.bytes_received || frm.doc.bytes_sent) {
			const rx = frappe.utils.file_size(frm.doc.bytes_received || 0);
			const tx = frappe.utils.file_size(frm.doc.bytes_sent || 0);
			frm.dashboard.add_indicator(__("↓ {0} / ↑ {1}", [rx, tx]), "blue");
		}

		if (frm.doc.last_handshake) {
			frm.dashboard.add_indicator(
				__("Last handshake: {0}", [frappe.datetime.prettyDate(frm.doc.last_handshake)]),
				"grey"
			);
		}

		if (!frm.is_new()) {
			// Generate Client Config button
			frm.add_custom_button(__("Client Config"), () => {
				frm.call("generate_client_config").then((r) => {
					if (r.message) {
						const d = new frappe.ui.Dialog({
							title: __("WireGuard Client Configuration"),
							size: "large",
							fields: [
								{
									fieldtype: "HTML",
									fieldname: "config_html",
								},
							],
						});
						d.fields_dict.config_html.$wrapper.html(`
							<pre class="vpn-config-block" style="
								background: var(--bg-dark-gray, #1e1e1e);
								color: var(--text-light, #d4d4d4);
								padding: 16px;
								border-radius: 8px;
								font-size: 13px;
								line-height: 1.6;
								overflow-x: auto;
								white-space: pre-wrap;
							">${frappe.utils.escape_html(r.message)}</pre>
							<div style="margin-top:12px">
								<button class="btn btn-sm btn-primary-dark copy-config-btn">
									${__("Copy to Clipboard")}
								</button>
							</div>
						`);
						d.fields_dict.config_html.$wrapper.find(".copy-config-btn").on("click", function () {
							frappe.utils.copy_to_clipboard(r.message);
							frappe.show_alert({ message: __("Copied!"), indicator: "green" });
						});
						d.show();
					}
				});
			}, __("Actions"));

			// QR Code button
			frm.add_custom_button(__("QR Code"), () => {
				frm.call("generate_qr_code").then((r) => {
					if (r.message) {
						const data = r.message;
						const d = new frappe.ui.Dialog({
							title: __("WireGuard QR Code"),
							fields: [
								{
									fieldtype: "HTML",
									fieldname: "qr_html",
								},
							],
						});
						d.fields_dict.qr_html.$wrapper.html(`
							<div style="text-align:center; padding:20px">
								<p style="margin-bottom:16px; color:var(--text-muted)">
									${__("Scan with WireGuard mobile app")}
								</p>
								<img src="data:image/png;base64,${data.qr_base64}"
									style="max-width:300px; border-radius:12px; box-shadow:0 4px 16px rgba(0,0,0,0.12)"
									alt="WireGuard QR Code" />
								<div style="margin-top:16px">
									<a class="btn btn-sm btn-default download-qr-btn"
										href="data:image/png;base64,${data.qr_base64}"
										download="${data.filename}">
										${__("Download PNG")}
									</a>
								</div>
							</div>
						`);
						d.show();
					}
				});
			}, __("Actions"));

			// Revoke button
			if (frm.doc.enabled) {
				frm.add_custom_button(__("Revoke Access"), () => {
					frappe.confirm(
						__("This will disconnect and disable this peer. Continue?"),
						() => {
							frm.call("revoke_peer").then(() => frm.reload_doc());
						}
					);
				}, __("Actions"));
			}

			// View Server shortcut
			if (frm.doc.vpn_server) {
				frm.add_custom_button(__("View Server"), () => {
					frappe.set_route("Form", "VPN Server", frm.doc.vpn_server);
				}, __("View"));
			}
		}
	},

	vpn_server(frm) {
		// Auto-fill DNS from server
		if (frm.doc.vpn_server && !frm.doc.dns) {
			frappe.db.get_value("VPN Server", frm.doc.vpn_server, "dns_servers").then((r) => {
				if (r.message && r.message.dns_servers) {
					frm.set_value("dns", r.message.dns_servers);
				}
			});
		}
	},
});
