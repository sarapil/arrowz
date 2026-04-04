// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Dinstar Dashboard — Live GSM Gateway Monitoring & Control
 * ==========================================================
 * Interactive dashboard for the Dinstar UC2000-VE GSM Gateway.
 * Features:
 *   • Health score ring with animated checks
 *   • Per-port GSM module cards with power/SIM/signal status
 *   • Call statistics table with ASR calculation
 *   • ECC (Error Cause Code) breakdown
 *   • SIP, Media, Network configuration panels
 *   • SMS send form & routing rules
 *   • GSM operate rules display
 *   • Auto-refresh with configurable interval
 */

frappe.pages["dinstar-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Dinstar GSM Gateway"),
		single_column: true,
	});

	// Add CSS
	const css = document.createElement("link");
	css.rel = "stylesheet";
	css.href = "/assets/arrowz/css/dinstar_dashboard.css";
	document.head.appendChild(css);

	page.main.html(frappe.render_template("dinstar_dashboard"));

	window.dinstarDashboard = new DinstarDashboard(page);
};

class DinstarDashboard {
	constructor(page) {
		this.page = page;
		this.data = null;
		this.refreshTimer = null;
		this.refreshInterval = 30000; // 30 seconds
		this.init();
	}

	async init() {
		this.setupToolbar();
		this.showLoader(true);
		try {
			await this.fetchData();
			this.render();
		} catch (err) {
			console.error("[Dinstar] Init error:", err);
			frappe.msgprint({
				title: __("Dinstar Connection Error"),
				message: err.message || __("Failed to connect to Dinstar gateway"),
				indicator: "red",
			});
		} finally {
			this.showLoader(false);
		}
		this.startAutoRefresh();
	}

	setupToolbar() {
		// Refresh button
		this.page.add_button(__("Refresh"), () => this.refresh(), {
			icon: "refresh",
		});

		// Test Connection
		this.page.add_button(__("Test Connection"), () => this.testConnection(), {
			icon: "check",
		});

		// Auto-refresh toggle
		this.page.add_field({
			fieldname: "auto_refresh",
			label: __("Auto Refresh"),
			fieldtype: "Check",
			default: 1,
			change: () => {
				const val = this.page.fields_dict.auto_refresh.get_value();
				if (val) {
					this.startAutoRefresh();
				} else {
					this.stopAutoRefresh();
				}
			},
		});
	}

	startAutoRefresh() {
		this.stopAutoRefresh();
		this.refreshTimer = setInterval(() => this.refresh(), this.refreshInterval);
	}

	stopAutoRefresh() {
		if (this.refreshTimer) {
			clearInterval(this.refreshTimer);
			this.refreshTimer = null;
		}
	}

	async refresh() {
		try {
			await this.fetchData();
			this.render();
		} catch (err) {
			console.error("[Dinstar] Refresh error:", err);
		}
	}

	async fetchData() {
		const r = await frappe.xcall("arrowz.api.dinstar.get_status");
		this.data = r;
		return r;
	}

	render() {
		if (!this.data) return;
		this.renderHealth();
		this.renderPorts();
		this.renderCallStats();
		this.renderEccStats();
		this.renderSipConfig();
		this.renderMediaConfig();
		this.renderNetworkConfig();
		this.renderSmsRouting();
		this.renderGsmRules();
	}

	// ─── Health Banner ─────────────────────────────────────────

	renderHealth() {
		const health = this.data.device_health || {};
		const sys = this.data.system || {};
		const score = health.score || 0;
		const status = health.status || "unknown";

		// Score ring animation
		const ring = document.getElementById("healthRingFg");
		if (ring) ring.setAttribute("stroke-dasharray", `${score}, 100`);

		const scoreText = document.getElementById("healthScoreText");
		if (scoreText) scoreText.textContent = score;

		// Status text and color
		const statusText = document.getElementById("healthStatusText");
		const banner = document.getElementById("healthBanner");
		const statusColors = {
			healthy: { text: "Healthy", cls: "health-healthy" },
			degraded: { text: "Degraded", cls: "health-degraded" },
			critical: { text: "Critical", cls: "health-critical" },
			unreachable: { text: "Unreachable", cls: "health-critical" },
			unknown: { text: "Unknown", cls: "health-unknown" },
		};
		const sc = statusColors[status] || statusColors.unknown;
		if (statusText) statusText.textContent = `Dinstar Gateway — ${sc.text}`;
		if (banner) {
			banner.className = `dinstar-health-banner ${sc.cls}`;
		}

		// Ring color
		const ringColors = {
			healthy: "#10b981",
			degraded: "#f59e0b",
			critical: "#ef4444",
			unreachable: "#6b7280",
			unknown: "#6b7280",
		};
		if (ring) ring.style.stroke = ringColors[status] || "#6b7280";

		// Health checks
		const checksEl = document.getElementById("healthChecks");
		if (checksEl && health.checks) {
			checksEl.innerHTML = health.checks
				.map((c) => {
					const icons = { pass: "✅", warn: "⚠️", fail: "❌" };
					return `<span class="health-check-item">${icons[c.status] || "❓"} ${c.name}</span>`;
				})
				.join("");
		}

		// Meta info
		this.setEl("metaUptime", sys.uptime_formatted || "--");
		this.setEl("metaNtpTime", sys.NtpTime || "--");
		this.setEl("metaWanMode", sys.WanMode || "--");
		this.setEl("metaVpn", sys.VPNEnable === "checked" ? "✅ Enabled" : "❌ Disabled");
	}

	// ─── Port Grid ─────────────────────────────────────────────

	renderPorts() {
		const grid = document.getElementById("portGrid");
		if (!grid) return;

		const ports = this.data.ports || [];
		const portInfo = this.data.port_info || [];

		if (!ports.length) {
			grid.innerHTML = '<div class="text-muted text-center p-4">No port data available</div>';
			return;
		}

		grid.innerHTML = ports
			.map((port, i) => {
				const pi = portInfo[i] || {};
				const isPowered = port.is_powered;
				const hasSim = port.has_sim;
				const sipAcc = pi.sip_account || port.gsm_port_name || `gsm-port${i + 1}`;

				// Status determination
				let statusCls = "port-off";
				let statusIcon = "⬛";
				let statusLabel = "Power Off";
				if (isPowered && hasSim) {
					statusCls = "port-active";
					statusIcon = "✅";
					statusLabel = "Active";
				} else if (isPowered && !hasSim) {
					statusCls = "port-nosim";
					statusIcon = "⚠️";
					statusLabel = "No SIM";
				} else if (!isPowered && hasSim) {
					statusCls = "port-off-sim";
					statusIcon = "🔌";
					statusLabel = "Off (SIM)";
				}

				const smsc = port.SMSC || "";
				const smscShort = smsc ? smsc.replace("+", "") : "—";

				return `
				<div class="port-card ${statusCls}" data-port="${i}">
					<div class="port-card-header">
						<span class="port-number">Port ${i}</span>
						<span class="port-status-icon">${statusIcon}</span>
					</div>
					<div class="port-card-body">
						<div class="port-sip">${this.esc(sipAcc)}</div>
						<div class="port-detail"><span>Power:</span> <strong>${port.Modulepower || "?"}</strong></div>
						<div class="port-detail"><span>Band:</span> ${port.band_type_label || "?"}</div>
						<div class="port-detail"><span>Mode:</span> ${port.network_mode_label || "?"}</div>
						<div class="port-detail"><span>SMSC:</span> ${smscShort}</div>
						<div class="port-detail"><span>Gain:</span> TX:${port.TxGain || "?"} RX:${port.RxGain || "?"}</div>
					</div>
					<div class="port-card-actions">
						<button class="btn btn-xs btn-default" onclick="dinstarDashboard.controlModule(${i}, 'reset')" title="Reset Module">
							🔄
						</button>
						<button class="btn btn-xs btn-default" onclick="dinstarDashboard.controlModule(${i}, 'unblock')" title="Unblock">
							🟢
						</button>
						<button class="btn btn-xs btn-danger" onclick="dinstarDashboard.controlModule(${i}, 'block')" title="Block">
							🔴
						</button>
					</div>
				</div>`;
			})
			.join("");
	}

	// ─── Call Statistics ────────────────────────────────────────

	renderCallStats() {
		const stats = this.data.call_stats || {};
		const ports = stats.ports || [];
		const totals = stats.totals || {};

		// Totals summary
		const totalsEl = document.getElementById("callTotals");
		if (totalsEl) {
			totalsEl.innerHTML = `
				<div class="stat-pill"><span class="stat-label">Total Calls</span><span class="stat-value">${totals.total_calls || 0}</span></div>
				<div class="stat-pill stat-success"><span class="stat-label">Answered</span><span class="stat-value">${totals.answered || 0}</span></div>
				<div class="stat-pill stat-danger"><span class="stat-label">Failed</span><span class="stat-value">${totals.failed || 0}</span></div>
				<div class="stat-pill stat-warning"><span class="stat-label">Busy</span><span class="stat-value">${totals.busy || 0}</span></div>
				<div class="stat-pill stat-info"><span class="stat-label">ASR</span><span class="stat-value">${totals.asr_percent || 0}%</span></div>
			`;
		}

		// Per-port table
		const tbody = document.getElementById("callStatsTableBody");
		if (tbody) {
			tbody.innerHTML = ports
				.map((s) => {
					const asrCls = s.asr_percent >= 60 ? "text-success" : s.asr_percent >= 30 ? "text-warning" : "text-danger";
					return `<tr>
						<td><strong>Port ${s.port}</strong></td>
						<td>${s.total_calls}</td><td>${s.answered}</td><td>${s.failed}</td>
						<td>${s.busy}</td><td>${s.no_answer}</td>
						<td class="${asrCls}"><strong>${s.asr_percent}%</strong></td>
					</tr>`;
				})
				.join("");
		}
	}

	// ─── ECC Statistics ─────────────────────────────────────────

	renderEccStats() {
		const stats = this.data.ecc_stats || [];
		const tbody = document.getElementById("eccStatsTableBody");
		if (tbody) {
			tbody.innerHTML = stats
				.map((s) => `<tr>
					<td><strong>Port ${s.port}</strong></td>
					<td>${s.total_calls}</td><td>${s.duration}</td><td>${s.answered}</td>
					<td>${s.busy}</td><td>${s.no_answer}</td>
					<td>${s.congestion}</td><td>${s.call_rejected}</td>
				</tr>`)
				.join("");
		}
	}

	// ─── SIP Config ─────────────────────────────────────────────

	renderSipConfig() {
		const cfg = this.data.sip_config || {};
		const el = document.getElementById("sipConfigBody");
		if (!el || cfg.error) {
			if (el) el.innerHTML = `<div class="text-danger">${cfg.error || "N/A"}</div>`;
			return;
		}
		const proxy = cfg.sip_proxy || {};
		const timers = cfg.timers || {};
		const features = cfg.features || {};
		el.innerHTML = `
			<div class="config-grid">
				<div class="config-item"><span>Proxy IP</span><strong>${this.esc(proxy.ip)}</strong></div>
				<div class="config-item"><span>Proxy Port</span><strong>${this.esc(proxy.port)}</strong></div>
				<div class="config-item"><span>Transport</span><strong>${this.esc(proxy.transport)}</strong></div>
				<div class="config-item"><span>Register Interval</span><strong>${this.esc(proxy.register_interval)}s</strong></div>
				<div class="config-item"><span>T1 Timer</span><strong>${this.esc(timers.T1)}ms</strong></div>
				<div class="config-item"><span>T2 Timer</span><strong>${this.esc(timers.T2)}ms</strong></div>
				<div class="config-item"><span>SIP-GSM Binding</span><strong>${features.gsm_sip_binding === "1" ? "✅" : "❌"}</strong></div>
				<div class="config-item"><span>IMEI Header</span><strong>${features.imei_enable === "1" ? "✅" : "❌"}</strong></div>
			</div>
		`;
	}

	// ─── Media Config ───────────────────────────────────────────

	renderMediaConfig() {
		const cfg = this.data.media_config || {};
		const el = document.getElementById("mediaConfigBody");
		if (!el || cfg.error) {
			if (el) el.innerHTML = `<div class="text-danger">${cfg.error || "N/A"}</div>`;
			return;
		}
		el.innerHTML = `
			<div class="config-grid">
				<div class="config-item"><span>Codec</span><strong>${this.esc(cfg.codec_label || cfg.codec_1)}</strong></div>
				<div class="config-item"><span>RTP Port</span><strong>${this.esc(cfg.rtp_port)}</strong></div>
				<div class="config-item"><span>DTMF</span><strong>${this.esc(cfg.dtmf_method_label)}</strong></div>
				<div class="config-item"><span>DTMF Payload</span><strong>${this.esc(cfg.dtmf_payload)}</strong></div>
				<div class="config-item"><span>Country Tone</span><strong>${this.esc(cfg.tone_label)}</strong></div>
				<div class="config-item"><span>Silence Supp.</span><strong>${cfg.silence_suppression === "1" ? "✅" : "❌"}</strong></div>
				<div class="config-item"><span>SRTP</span><strong>${this.esc(cfg.srtp_mode)}</strong></div>
				<div class="config-item"><span>IVR Duration</span><strong>${this.esc(cfg.ivr_duration)}s</strong></div>
			</div>
		`;
	}

	// ─── Network Config ─────────────────────────────────────────

	renderNetworkConfig() {
		const cfg = this.data.network_config || {};
		const mgmt = this.data.management_config || {};
		const el = document.getElementById("networkConfigBody");
		if (!el) return;
		el.innerHTML = `
			<div class="config-grid">
				<div class="config-item"><span>WAN Mode</span><strong>${this.esc(cfg.wan_mode)}</strong></div>
				<div class="config-item"><span>DHCP IP</span><strong>${this.esc(cfg.dhcp_ip)}</strong></div>
				<div class="config-item"><span>Gateway</span><strong>${this.esc(cfg.gateway)}</strong></div>
				<div class="config-item"><span>MTU</span><strong>${this.esc(cfg.wan_mtu)}</strong></div>
				<div class="config-item"><span>NTP</span><strong>${mgmt.ntp_enabled === "1" ? "✅" : "❌"}</strong></div>
				<div class="config-item"><span>NTP Server</span><strong>${this.esc(mgmt.ntp_primary)}</strong></div>
				<div class="config-item"><span>Web Port</span><strong>${this.esc(mgmt.web_port)}</strong></div>
				<div class="config-item"><span>SSH</span><strong>${mgmt.ssh_enabled === "1" ? "✅" : "❌"}</strong></div>
			</div>
		`;
	}

	// ─── SMS Routing ────────────────────────────────────────────

	renderSmsRouting() {
		const routes = this.data.sms_routing || [];
		const el = document.getElementById("smsRoutingBody");
		if (!el) return;

		const active = routes.filter((r) => r.enable === 1 || r.enable === "1");
		if (!active.length) {
			el.innerHTML = '<div class="text-muted">No active SMS routing rules</div>';
			return;
		}

		el.innerHTML = `
			<table class="table table-sm">
				<thead><tr><th>#</th><th>Dest Num</th><th>Source</th><th>Dest Port</th><th>Prefix Add</th></tr></thead>
				<tbody>${active
					.map(
						(r, i) =>
							`<tr><td>${i + 1}</td><td>${this.esc(r.dest_num)}</td><td>${r.src_mode}</td>
							<td>${r.dest_value === 255 || r.dest_value === "255" ? "All" : `Port ${r.dest_value}`}</td>
							<td>${this.esc(r.prefix_to_add)}</td></tr>`
					)
					.join("")}</tbody>
			</table>`;
	}

	// ─── GSM Rules ──────────────────────────────────────────────

	renderGsmRules() {
		const rules = this.data.gsm_rules || [];
		const el = document.getElementById("gsmRulesBody");
		if (!el) return;

		const active = rules.filter((r) => r.enable === "1" || r.enable === 1);
		if (!active.length) {
			el.innerHTML = '<div class="text-muted">No active GSM operate rules</div>';
			return;
		}

		el.innerHTML = `
			<table class="table table-sm">
				<thead><tr><th>#</th><th>Prefix Match</th><th>Delete Digits</th><th>Prefix Add</th><th>Port</th></tr></thead>
				<tbody>${active
					.map(
						(r, i) =>
							`<tr><td>${i + 1}</td><td>${this.esc(r.PreMatch)}</td><td>${r.PreDelete}</td>
							<td>${this.esc(r.PreAdd)}</td>
							<td>${r.port === 255 || r.port === "255" ? "All" : `Port ${r.port}`}</td></tr>`
					)
					.join("")}</tbody>
			</table>`;
	}

	// ─── Actions ────────────────────────────────────────────────

	async sendSMS() {
		const port = document.getElementById("smsPort").value;
		const number = document.getElementById("smsNumber").value;
		const message = document.getElementById("smsMessage").value;

		if (!number || !message) {
			frappe.msgprint(__("Please enter number and message"));
			return;
		}

		try {
			const r = await frappe.xcall("arrowz.api.dinstar.send_sms", {
				port,
				number,
				message,
			});
			if (r.status === "sent") {
				frappe.show_alert({ message: __("SMS sent successfully"), indicator: "green" });
				document.getElementById("smsMessage").value = "";
			} else {
				frappe.msgprint({ title: __("SMS Error"), message: r.message, indicator: "red" });
			}
		} catch (err) {
			frappe.msgprint({ title: __("Error"), message: err.message, indicator: "red" });
		}
	}

	async controlModule(port, action) {
		const confirmed = await new Promise((resolve) => {
			frappe.confirm(
				__(`Are you sure you want to ${action} Port ${port}?`),
				() => resolve(true),
				() => resolve(false)
			);
		});

		if (!confirmed) return;

		try {
			const r = await frappe.xcall("arrowz.api.dinstar.control_module", { port, action });
			if (r.status === "ok") {
				frappe.show_alert({
					message: __(`Port ${port}: ${action} successful`),
					indicator: "green",
				});
				setTimeout(() => this.refresh(), 2000);
			} else {
				frappe.msgprint({ title: __("Error"), message: r.message, indicator: "red" });
			}
		} catch (err) {
			frappe.msgprint({ title: __("Error"), message: err.message, indicator: "red" });
		}
	}

	async testConnection() {
		frappe.show_alert(__("Testing connection..."));
		try {
			const r = await frappe.xcall("arrowz.api.dinstar.test_connection");
			const indicator = r.status === "ok" ? "green" : "red";
			frappe.msgprint({
				title: __("Connection Test"),
				message: `${r.message}${r.latency_ms > 0 ? ` (${r.latency_ms}ms)` : ""}`,
				indicator,
			});
		} catch (err) {
			frappe.msgprint({ title: __("Error"), message: err.message, indicator: "red" });
		}
	}

	async refreshPorts() {
		try {
			const r = await frappe.xcall("arrowz.api.dinstar.get_port_status");
			this.data.ports = r.ports || [];
			this.data.port_info = r.port_info || [];
			this.renderPorts();
			frappe.show_alert({ message: __("Ports refreshed"), indicator: "green" });
		} catch (err) {
			frappe.msgprint({ title: __("Error"), message: err.message, indicator: "red" });
		}
	}

	// ─── Helpers ────────────────────────────────────────────────

	showLoader(show) {
		const el = document.getElementById("dinstarLoader");
		if (el) el.style.display = show ? "flex" : "none";
	}

	setEl(id, text) {
		const el = document.getElementById(id);
		if (el) el.textContent = text;
	}

	esc(str) {
		if (str === undefined || str === null) return "";
		const div = document.createElement("div");
		div.textContent = String(str);
		return div.innerHTML;
	}

	destroy() {
		this.stopAutoRefresh();
	}
}
