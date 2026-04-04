// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Arrowz Network Topology — Comprehensive Visual Graph
 * ======================================================
 * Full interactive topology using frappe_visual (Cytoscape.js engine).
 * Shows ALL Arrowz modules as sub-networks with:
 *   • Rich HTML node labels with icons, badges, action buttons
 *   • Context menus with permission-aware CRUD
 *   • Expandable/collapsible sub-network groups
 *   • Side panel for node details
 *   • Workspace quick-links
 *   • Multiple layout algorithms
 *   • Search, filter, export
 */

frappe.pages["arrowz-topology"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Network Topology"),
		single_column: true,
	});

	// Load topology CSS
	const cssLink = document.createElement("link");
	cssLink.rel = "stylesheet";
	cssLink.href = "/assets/arrowz/css/arrowz_topology.css";
	document.head.appendChild(cssLink);

	page.main.html(frappe.render_template("arrowz_topology"));
	new ArrowzTopology(page);
};

/* ═══════════════════════════════════════════════════════════════════
   ARROWZ TOPOLOGY — Main Class
   ═══════════════════════════════════════════════════════════════════ */

class ArrowzTopology {
	constructor(page) {
		this.page = page;
		this.engine = null;
		this.cy = null;
		this.data = null;
		this.permissions = { can_write: false };
		this.activeLayout = "fcose";
		this.activeFilter = "all";
		this.sidePanel = null;
		this.init();
	}

	async init() {
		this.showLoader(true);
		try {
			await this.loadEngine();
			await this.fetchData();
			this.buildGraph();
			this.setupHtmlLabels();
			this.setupContextMenu();
			this.setupSidePanel();
			this.setupToolbar();
			this.setupSearch();
			this.setupFilters();
			this.setupWorkspaceLinks();
			this.updateStatusBar();
			this.setupKeyboard();
			// Fit after layout settles
			setTimeout(() => {
				if (this.engine) this.engine.fit(50);
			}, 1200);
		} catch (err) {
			console.error("[Arrowz Topology] Init error:", err);
			frappe.msgprint({
				title: __("Topology Error"),
				message: err.message || __("Failed to load topology"),
				indicator: "red",
			});
		} finally {
			this.showLoader(false);
		}
	}

	/* ─── Engine Loading ─────────────────────────────────────── */
	async loadEngine() {
		if (!frappe.visual || !frappe.visual.engine) {
			throw new Error(__("frappe_visual is not installed"));
		}
		const GraphEngine = await frappe.visual.engine();
		if (!GraphEngine) {
			throw new Error(__("Failed to load visual engine"));
		}
		this.GraphEngine = GraphEngine;
		this.ColorSystem = frappe.visual.ColorSystem;
		this.FloatingWindow = frappe.visual.FloatingWindow;
		this.registerNodeTypes();
	}

	/* ─── Custom Node Type Registration ──────────────────────── */
	registerNodeTypes() {
		const CS = this.ColorSystem;

		// Infrastructure
		CS.registerNodeType("az-server", {
			palette: "indigo", icon: "🏢", shape: "roundrectangle", width: 180, height: 60,
		});
		CS.registerNodeType("az-box", {
			palette: "teal", icon: "📡", shape: "roundrectangle", width: 160, height: 55,
		});
		CS.registerNodeType("az-interface", {
			palette: "cyan", icon: "🔌", shape: "ellipse", width: 50, height: 50,
		});
		CS.registerNodeType("az-wan", {
			palette: "orange", icon: "🌐", shape: "roundrectangle", width: 150, height: 50,
		});
		CS.registerNodeType("az-lan", {
			palette: "emerald", icon: "🏠", shape: "roundrectangle", width: 150, height: 50,
		});

		// VPN
		CS.registerNodeType("az-vpn-server", {
			palette: "indigo", icon: "🔒", shape: "roundrectangle", width: 160, height: 55,
		});
		CS.registerNodeType("az-vpn-peer", {
			palette: "violet", icon: "🔑", shape: "roundrectangle", width: 140, height: 48,
		});
		CS.registerNodeType("az-tunnel", {
			palette: "purple", icon: "🔗", shape: "roundrectangle", width: 160, height: 50,
		});

		// VoIP
		CS.registerNodeType("az-extension", {
			palette: "amber", icon: "📞", shape: "roundrectangle", width: 140, height: 48,
		});
		CS.registerNodeType("az-trunk", {
			palette: "orange", icon: "📡", shape: "roundrectangle", width: 150, height: 50,
		});
		CS.registerNodeType("az-inbound", {
			palette: "green", icon: "📥", shape: "roundrectangle", width: 140, height: 45,
		});
		CS.registerNodeType("az-outbound", {
			palette: "blue", icon: "📤", shape: "roundrectangle", width: 140, height: 45,
		});

		// Omni / Meetings
		CS.registerNodeType("az-omni", {
			palette: "green", icon: "💬", shape: "roundrectangle", width: 150, height: 50,
		});
		CS.registerNodeType("az-meeting", {
			palette: "violet", icon: "🎥", shape: "roundrectangle", width: 150, height: 50,
		});

		// WiFi
		CS.registerNodeType("az-wifi", {
			palette: "blue", icon: "📶", shape: "roundrectangle", width: 140, height: 48,
		});
		CS.registerNodeType("az-wifi-ap", {
			palette: "cyan", icon: "📡", shape: "roundrectangle", width: 140, height: 48,
		});

		// Firewall
		CS.registerNodeType("az-firewall", {
			palette: "red", icon: "🛡️", shape: "roundrectangle", width: 140, height: 48,
		});

		// Clients
		CS.registerNodeType("az-client", {
			palette: "pink", icon: "💻", shape: "roundrectangle", width: 130, height: 45,
		});

		// Dinstar GSM Gateway
		CS.registerNodeType("az-dinstar-gw", {
			palette: "rose", icon: "📱", shape: "roundrectangle", width: 280, height: 155,
		});
		CS.registerNodeType("az-dinstar-port", {
			palette: "pink", icon: "📶", shape: "roundrectangle", width: 170, height: 70,
		});

		// Monitoring
		CS.registerNodeType("az-alert", {
			palette: "red", icon: "🚨", shape: "roundrectangle", width: 140, height: 45,
		});
		CS.registerNodeType("az-health", {
			palette: "emerald", icon: "❤️", shape: "roundrectangle", width: 140, height: 45,
		});

		// Workspace link
		CS.registerNodeType("az-link", {
			palette: "slate", icon: "🔗", shape: "roundrectangle", width: 130, height: 42,
		});

		// Groups (compound parents)
		CS.registerNodeType("az-group-infra", {
			palette: "teal", icon: "🏗️", shape: "roundrectangle", width: 200, height: 80,
		});
		CS.registerNodeType("az-group-voip", {
			palette: "amber", icon: "☎️", shape: "roundrectangle", width: 200, height: 80,
		});
		CS.registerNodeType("az-group-vpn", {
			palette: "indigo", icon: "🔒", shape: "roundrectangle", width: 200, height: 80,
		});
		CS.registerNodeType("az-group-wifi", {
			palette: "blue", icon: "📶", shape: "roundrectangle", width: 200, height: 80,
		});
		CS.registerNodeType("az-group-firewall", {
			palette: "red", icon: "🛡️", shape: "roundrectangle", width: 200, height: 80,
		});
		CS.registerNodeType("az-group-comms", {
			palette: "green", icon: "💬", shape: "roundrectangle", width: 200, height: 80,
		});
		CS.registerNodeType("az-group-monitor", {
			palette: "rose", icon: "📊", shape: "roundrectangle", width: 200, height: 80,
		});
		CS.registerNodeType("az-group-clients", {
			palette: "pink", icon: "👥", shape: "roundrectangle", width: 200, height: 80,
		});
		CS.registerNodeType("az-group-gsm", {
			palette: "rose", icon: "📱", shape: "roundrectangle", width: 200, height: 80,
		});

		// Edge types
		CS.registerEdgeType("az-manages", { color: "#14b8a6", width: 2 });
		CS.registerEdgeType("az-connects", { color: "#6366f1", width: 2 });
		CS.registerEdgeType("az-tunnel", { color: "#8b5cf6", width: 3 });
		CS.registerEdgeType("az-route", { color: "#f59e0b", width: 1.5 });
		CS.registerEdgeType("az-serves", { color: "#3b82f6", width: 1.5 });
		CS.registerEdgeType("az-monitors", { color: "#ef4444", width: 1.5 });
		CS.registerEdgeType("az-calls", { color: "#f97316", width: 2 });
	}

	/* ─── Data Fetching ──────────────────────────────────────── */
	async fetchData() {
		try {
			const dinstarPromise = Promise.race([
				frappe.xcall("arrowz.api.dinstar.get_topology_node").catch(() => null),
				new Promise(resolve => setTimeout(() => resolve(null), 8000)),
			]);
			const [r, dinstarData] = await Promise.all([
				frappe.xcall("arrowz.api.topology.get_topology_data"),
				dinstarPromise,
			]);
			this.data = r;
			this.data.dinstar = dinstarData;
			this.permissions = r.permissions || { can_write: false };
		} catch (err) {
			console.warn("[Arrowz Topology] API error, using empty data:", err);
			this.data = this.getEmptyData();
		}
	}

	getEmptyData() {
		return {
			server_config: {},
			boxes: [], interfaces: [], wan_connections: [], lan_networks: [],
			vpn_servers: [], vpn_peers: [], site_to_site_tunnels: [],
			extensions: [], trunks: [], inbound_routes: [], outbound_routes: [],
			omni_providers: [], meeting_rooms: [],
			wifi_networks: [], wifi_aps: [],
			firewall_zones: [],
			network_clients: [],
			active_alerts: [], wan_health: [],
			workspace_links: [],
			dinstar: null,
			permissions: { can_write: false },
			summary: {},
		};
	}

	/* ─── Graph Building ─────────────────────────────────────── */
	buildGraph() {
		const { nodes, edges } = this.transformData();

		const container = document.getElementById("topology-graph-container");
		if (!container) throw new Error("Graph container not found");

		// Explicit sizing
		container.style.height = "calc(100vh - 160px)";
		container.style.minHeight = "500px";

		this.engine = new this.GraphEngine({
			container: container,
			nodes: nodes,
			edges: edges,
			layout: "fcose",
			layoutOptions: {
				quality: "proof",
				nodeSeparation: 150,
				idealEdgeLength: 180,
				nodeRepulsion: 12000,
				edgeElasticity: 0.3,
				gravity: 0.15,
				gravityRange: 5,
				nestingFactor: 0.08,
			},
			minimap: true,
			contextMenu: false, // We build our own
			expandCollapse: true,
			animate: true,
			antLines: true,
			pulseNodes: true,
			onNodeClick: (data, evt) => this.onNodeClick(data, evt),
			onNodeDblClick: (data, evt) => this.onNodeDblClick(data),
		});

		this.cy = this.engine.cy;
	}

	/* ─── Data → Graph Elements ──────────────────────────────── */
	transformData() {
		const d = this.data;
		const nodes = [];
		const edges = [];
		let edgeId = 0;
		const eid = () => `e-${++edgeId}`;

		// ───── Group (Compound) Nodes ─────
		const groups = {
			"grp-infra": { label: __("🏗️ Infrastructure"), type: "az-group-infra", category: "infrastructure" },
			"grp-voip": { label: __("☎️ VoIP & PBX"), type: "az-group-voip", category: "voip" },
			"grp-vpn": { label: __("🔒 VPN"), type: "az-group-vpn", category: "vpn" },
			"grp-wifi": { label: __("📶 WiFi & Hotspot"), type: "az-group-wifi", category: "wifi" },
			"grp-firewall": { label: __("🛡️ Firewall"), type: "az-group-firewall", category: "firewall" },
			"grp-comms": { label: __("💬 Communications"), type: "az-group-comms", category: "comms" },
			"grp-monitor": { label: __("📊 Monitoring"), type: "az-group-monitor", category: "monitoring" },
			"grp-clients": { label: __("👥 Clients"), type: "az-group-clients", category: "clients" },
			"grp-gsm": { label: __("📱 GSM Gateway"), type: "az-group-gsm", category: "gsm" },
		};

		// Only add groups that have children
		const groupChildren = {
			"grp-infra": 0, "grp-voip": 0, "grp-vpn": 0, "grp-wifi": 0,
			"grp-firewall": 0, "grp-comms": 0, "grp-monitor": 0, "grp-clients": 0,
			"grp-gsm": 0,
		};

		// Helper to add nodes to a group
		const addNode = (id, label, type, parent, doctype, docname, status, meta = {}) => {
			if (parent && groupChildren[parent] !== undefined) groupChildren[parent]++;
			const nodeData = { id, label, type, parent, doctype, docname, status, meta };
			nodes.push(nodeData);
			return nodeData;
		};

		// ───── Server Config (center node) ─────
		if (d.server_config && d.server_config.name) {
			const sc = d.server_config;
			addNode("server-config", sc.server_name || sc.display_name || "Arrowz Server", "az-server",
				null, "AZ Server Config", sc.name,
				sc.is_active ? "active" : "disabled",
				{ host: sc.host, port: sc.port, protocol: sc.protocol, type: sc.server_type, status: sc.connection_status });
		}

		// ───── Boxes → Infrastructure ─────
		(d.boxes || []).forEach((b) => {
			const statusMap = { Active: "active", Online: "active", Offline: "error", Disabled: "disabled" };
			addNode(`box-${b.name}`, b.box_name || b.name, "az-box", "grp-infra",
				"Arrowz Box", b.name,
				statusMap[b.status] || "warning",
				{ ip: b.box_ip, type: b.device_type, port: b.api_port, location: b.location, engine: b.engine_status });
		});

		// ───── Interfaces → Infrastructure ─────
		(d.interfaces || []).forEach((iface) => {
			addNode(`iface-${iface.name}`, iface.interface_name || iface.name,
				"az-interface", "grp-infra", "Network Interface", iface.name,
				iface.status === "Active" ? "active" : "warning",
				{ ip: iface.ip_address, mac: iface.mac_address, speed: iface.speed, role: iface.role, type: iface.interface_type });
			// Edge: box → interface
			if (iface.arrowz_box && nodes.find((n) => n.id === `box-${iface.arrowz_box}`)) {
				edges.push({ id: eid(), source: `box-${iface.arrowz_box}`, target: `iface-${iface.name}`,
					type: "az-manages", label: "", animated: false });
			}
		});

		// ───── WAN Connections → Infrastructure ─────
		(d.wan_connections || []).forEach((w) => {
			addNode(`wan-${w.name}`, w.wan_name || w.name, "az-wan", "grp-infra",
				"WAN Connection", w.name,
				w.status === "Active" ? "active" : "warning",
				{ ip: w.ip_address, gw: w.gateway, type: w.connection_type, uptime: w.uptime_percentage, current_ip: w.current_ip });
			if (w.arrowz_box) {
				edges.push({ id: eid(), source: `box-${w.arrowz_box}`, target: `wan-${w.name}`,
					type: "az-connects", animated: false });
			}
		});

		// ───── LAN Networks → Infrastructure ─────
		(d.lan_networks || []).forEach((l) => {
			addNode(`lan-${l.name}`, l.network_name || l.name, "az-lan", "grp-infra",
				"LAN Network", l.name,
				l.enabled ? "active" : "disabled",
				{ ip: l.ip_address, subnet: l.subnet_mask, vlan: l.vlan_id, dhcp: l.enable_dhcp, zone: l.firewall_zone });
			if (l.arrowz_box) {
				edges.push({ id: eid(), source: `box-${l.arrowz_box}`, target: `lan-${l.name}`,
					type: "az-connects", animated: false });
			}
		});

		// ───── VPN Servers → VPN ─────
		(d.vpn_servers || []).forEach((v) => {
			addNode(`vpn-srv-${v.name}`, v.server_name || v.name, "az-vpn-server", "grp-vpn",
				"VPN Server", v.name,
				(v.status === "Active" || v.status === "Running" || v.enabled) ? "active" : "disabled",
				{ address: v.server_address, endpoint: v.endpoint, port: v.listen_port,
					peers: v.connected_peers, type: v.vpn_type, box: v.arrowz_box });
			// Edge: box → vpn server (primary link)
			if (v.arrowz_box) {
				const boxId = `box-${v.arrowz_box}`;
				if (nodes.find((n) => n.id === boxId)) {
					edges.push({ id: eid(), source: boxId, target: `vpn-srv-${v.name}`,
						type: "az-tunnel", animated: true });
				}
			}
			// Edge: server-config → vpn server (fallback if no box)
			if (!v.arrowz_box && d.server_config && d.server_config.name) {
				edges.push({ id: eid(), source: "server-config", target: `vpn-srv-${v.name}`,
					type: "az-tunnel", animated: true });
			}
		});

		// ───── VPN Peers → VPN ─────
		(d.vpn_peers || []).forEach((p) => {
			addNode(`vpn-peer-${p.name}`, p.peer_name || p.name,
				"az-vpn-peer", "grp-vpn",
				"VPN Peer", p.name,
				p.status === "Active" || p.status === "Connected" ? "active" : "disabled",
				{ ips: p.allowed_ips, endpoint: p.endpoint, customer: p.customer, bytes_in: p.bytes_received, bytes_out: p.bytes_sent });
			// Edge: vpn server → peer
			if (p.vpn_server) {
				const srvId = `vpn-srv-${p.vpn_server}`;
				if (nodes.find((n) => n.id === srvId)) {
					edges.push({ id: eid(), source: srvId, target: `vpn-peer-${p.name}`,
						type: "az-tunnel", animated: true, label: "" });
				}
			}
		});

		// ───── Site-to-Site Tunnels → VPN ─────
		(d.site_to_site_tunnels || []).forEach((t) => {
			addNode(`s2s-${t.name}`, t.tunnel_name || t.name,
				"az-tunnel", "grp-vpn",
				"Site to Site Tunnel", t.name,
				t.status === "Active" || t.status === "Connected" ? "active" : (t.enabled ? "warning" : "disabled"),
				{ remote: t.remote_endpoint, local_subnet: t.local_subnet, remote_subnet: t.remote_subnet,
					type: t.vpn_type, port: t.listen_port, bytes_in: t.bytes_in, bytes_out: t.bytes_out });
			// Edge: box → tunnel
			if (t.arrowz_box) {
				const boxId = `box-${t.arrowz_box}`;
				if (nodes.find((n) => n.id === boxId)) {
					edges.push({ id: eid(), source: boxId, target: `s2s-${t.name}`,
						type: "az-tunnel", animated: true });
				}
			}
		});

		// ───── Extensions → VoIP ─────
		(d.extensions || []).forEach((ext) => {
			addNode(`ext-${ext.name}`, `${ext.extension || ""} ${ext.display_name || ext.name}`.trim(),
				"az-extension", "grp-voip",
				"AZ Extension", ext.name,
				ext.is_active ? "active" : "disabled",
				{ number: ext.extension, user: ext.user, type: ext.extension_type, server: ext.server, sync: ext.sync_status });
			if (d.server_config && d.server_config.name) {
				edges.push({ id: eid(), source: "server-config", target: `ext-${ext.name}`,
					type: "az-calls", animated: false });
			}
		});

		// ───── Trunks → VoIP ─────
		(d.trunks || []).forEach((t) => {
			addNode(`trunk-${t.name}`, t.trunk_name || t.name, "az-trunk", "grp-voip",
				"AZ Trunk", t.name,
				t.status === "Active" || t.status === "Registered" ? "active" : "warning",
				{ host: t.host, port: t.port, type: t.trunk_type, provider: t.provider, channels: t.max_channels });
			if (d.server_config && d.server_config.name) {
				edges.push({ id: eid(), source: "server-config", target: `trunk-${t.name}`,
					type: "az-calls", animated: false });
			}
		});

		// ───── Inbound Routes → VoIP ─────
		(d.inbound_routes || []).forEach((r) => {
			addNode(`inbound-${r.name}`, r.route_name || r.did_pattern || r.name, "az-inbound", "grp-voip",
				"AZ Inbound Route", r.name,
				r.is_enabled ? "active" : "disabled",
				{ did: r.did_pattern, dest_type: r.destination_type, dest: r.destination, trunk: r.trunk });
		});

		// ───── Outbound Routes → VoIP ─────
		(d.outbound_routes || []).forEach((r) => {
			addNode(`outbound-${r.name}`, r.route_name || r.name, "az-outbound", "grp-voip",
				"AZ Outbound Route", r.name,
				r.is_enabled ? "active" : "disabled",
				{ trunk: r.primary_trunk, pattern: r.dial_pattern, priority: r.priority });
			if (r.primary_trunk) {
				const trunkId = `trunk-${r.primary_trunk}`;
				if (nodes.find((n) => n.id === trunkId)) {
					edges.push({ id: eid(), source: `outbound-${r.name}`, target: trunkId,
						type: "az-route", animated: false });
				}
			}
		});

		// ───── Omni Providers → Communications ─────
		(d.omni_providers || []).forEach((op) => {
			const typeMap = { WhatsApp: "whatsapp", Telegram: "telegram" };
			addNode(`omni-${op.name}`, op.provider_name || op.name,
				typeMap[op.provider_type] || "az-omni", "grp-comms",
				"AZ Omni Provider", op.name,
				op.is_enabled ? "active" : "disabled",
				{ type: op.provider_type, url: op.base_url });
		});

		// ───── Meeting Rooms → Communications ─────
		(d.meeting_rooms || []).forEach((m) => {
			addNode(`meeting-${m.name}`, m.room_name || m.name, "az-meeting", "grp-comms",
				"AZ Meeting Room", m.name,
				m.status === "Active" ? "active" : "disabled",
				{ type: m.room_type, max: m.max_participants, permanent: m.is_permanent, organizer: m.organizer });
		});

		// ───── WiFi Networks → WiFi ─────
		(d.wifi_networks || []).forEach((w) => {
			addNode(`wifi-${w.name}`, w.ssid || w.name, "az-wifi", "grp-wifi",
				"WiFi Network", w.name,
				w.enabled ? "active" : "disabled",
				{ ssid: w.ssid, band: w.band, channel: w.channel, encryption: w.encryption, max_clients: w.max_clients });
			if (w.arrowz_box) {
				edges.push({ id: eid(), source: `box-${w.arrowz_box}`, target: `wifi-${w.name}`,
					type: "az-serves", animated: false });
			}
		});

		// ───── WiFi APs → WiFi ─────
		(d.wifi_aps || []).forEach((ap) => {
			addNode(`wifiap-${ap.name}`, ap.ap_name || ap.name, "az-wifi-ap", "grp-wifi",
				"WiFi Access Point", ap.name,
				ap.status === "Active" || ap.status === "Online" ? "active" : "warning",
				{ mac: ap.mac_address, model: ap.model, clients: ap.connected_clients, location: ap.location, uptime: ap.uptime });
			if (ap.arrowz_box) {
				edges.push({ id: eid(), source: `box-${ap.arrowz_box}`, target: `wifiap-${ap.name}`,
					type: "az-manages", animated: false });
			}
		});

		// ───── Firewall Zones → Firewall ─────
		(d.firewall_zones || []).forEach((fz) => {
			addNode(`fw-${fz.name}`, fz.zone_name || fz.name, "az-firewall", "grp-firewall",
				"Firewall Zone", fz.name, "active",
				{ policy: fz.default_policy, masquerade: fz.enable_masquerade, interfaces: fz.interfaces, color: fz.color });
			if (fz.arrowz_box) {
				edges.push({ id: eid(), source: `box-${fz.arrowz_box}`, target: `fw-${fz.name}`,
					type: "az-manages", animated: false });
			}
		});

		// ───── Network Clients → Clients ─────
		(d.network_clients || []).forEach((c) => {
			addNode(`client-${c.name}`, c.hostname || c.name, "az-client", "grp-clients",
				"Network Client", c.name,
				c.status === "Active" || c.status === "Online" ? "active" : "disabled",
				{ ip: c.ip_address, mac: c.mac_address, group: c.client_group, conn: c.connection_type });
		});

		// ───── Alerts → Monitoring ─────
		(d.active_alerts || []).forEach((a) => {
			const sevMap = { Critical: "error", Warning: "warning", Info: "active" };
			addNode(`alert-${a.name}`, `${a.alert_type || ""}: ${(a.message || "").substring(0, 40)}`,
				"az-alert", "grp-monitor",
				"Network Alert", a.name,
				sevMap[a.severity] || "warning",
				{ severity: a.severity, box: a.arrowz_box });
			if (a.arrowz_box) {
				edges.push({ id: eid(), source: `box-${a.arrowz_box}`, target: `alert-${a.name}`,
					type: "az-monitors", animated: false });
			}
		});

		// ───── WAN Health → Monitoring ─────
		(d.wan_health || []).forEach((h) => {
			addNode(`health-${h.name}`, `Health: ${h.wan_connection || h.name}`, "az-health", "grp-monitor",
				"WAN Health Check", h.name,
				h.status === "Healthy" || h.status === "OK" ? "active" : "warning",
				{ latency: h.latency_ms, loss: h.packet_loss_percent, jitter: h.jitter_ms, ip: h.public_ip });
		});

		// ───── Dinstar GSM Gateway → GSM ─────
		{
			const din = d.dinstar || {};
			const gw = din.node || {};
			const gwData = gw.data || {};
			const isOffline = !din.node || gwData.status === "offline" || gwData.error;
			const gwId = gw.id || "dinstar-gw";
			const gwLabel = isOffline
				? "Dinstar UC2000-VE (VPN ⛔)"
				: (gw.label || "Dinstar UC2000-VE (8P)");

			// Port nodes — use real data or fallback placeholders
			const childNodes = (din.child_nodes && din.child_nodes.length > 0)
				? din.child_nodes
				: Array.from({length: 8}, (_, i) => ({
					id: `dinstar-port-${i}`,
					label: `Port ${i} (gsm-port${i+1})`,
					type: "az-dinstar-port",
					data: { port_index: i, sip_account: `gsm-port${i+1}`,
						status: "unknown", is_powered: false, has_sim: false }
				}));

			// Build port grid summary for gateway card
			const portGrid = childNodes.map(p => {
				const pd = p.data || {};
				return { sim: pd.has_sim, power: pd.is_powered, sip: pd.sip_account };
			});

			const gwNode = addNode(gwId, gwLabel, "az-dinstar-gw", "grp-gsm",
				null, null,
				isOffline ? "error" : "active",
				{ ports: gwData.total_ports || 8, uptime: gwData.uptime || (isOffline ? "VPN disconnected" : ""),
				  vpn: gwData.vpn_enabled, sim_count: gwData.sim_count,
				  powered: gwData.powered_count, wan: gwData.wan_mode,
				  status_text: isOffline ? "VPN disconnected — device unreachable" : "Online" });
			// Attach port grid data for the HTML label renderer
			if (gwNode) gwNode._portGrid = portGrid;

			childNodes.forEach((port) => {
				const pd = port.data || {};
				const portStatus = isOffline ? "disabled"
					: pd.is_powered && pd.has_sim ? "active"
					: pd.is_powered && !pd.has_sim ? "warning"
					: !pd.is_powered && pd.has_sim ? "warning"
					: "disabled";
				addNode(port.id, port.label, "az-dinstar-port", "grp-gsm",
					null, null, portStatus,
					{ sip: pd.sip_account, sim: pd.has_sim, power: pd.is_powered,
					  smsc: pd.smsc, band: pd.band_type, mode: pd.network_mode });
				edges.push({ id: eid(), source: gwId, target: port.id,
					type: "az-manages", animated: false });
			});

			// Edge: server-config → dinstar gateway
			if (d.server_config && d.server_config.name) {
				edges.push({ id: eid(), source: "server-config", target: gwId,
					type: "az-calls", animated: !isOffline, label: "GSM",
					...(isOffline ? {style: {opacity: 0.4}} : {}) });
			}
		}

		// ───── Add group nodes that have children ─────
		Object.entries(groups).forEach(([gid, cfg]) => {
			if (groupChildren[gid] > 0) {
				nodes.unshift({
					id: gid, label: cfg.label, type: cfg.type,
					meta: { category: cfg.category, childCount: groupChildren[gid] },
					childCount: groupChildren[gid],
					summary: { [__("Items")]: groupChildren[gid] },
				});
			}
		});

		// ───── Server → Group connections ─────
		if (d.server_config && d.server_config.name) {
			Object.keys(groups).forEach((gid) => {
				if (groupChildren[gid] > 0) {
					edges.push({ id: eid(), source: "server-config", target: gid,
						type: "default", animated: false });
				}
			});
		}

		return { nodes, edges };
	}

	/* ─── HTML Labels (Rich Node Rendering) ──────────────────── */
	setupHtmlLabels() {
		if (!this.cy || !this.cy.nodeHtmlLabel) return;

		const statusDot = (st) => {
			const colors = { active: "#10b981", warning: "#f59e0b", error: "#ef4444", disabled: "#94a3b8" };
			return `<span class="az-status-dot" style="background:${colors[st] || "#94a3b8"}"></span>`;
		};

		const typeIcons = {
			"az-server": "🏢", "az-box": "📡", "az-interface": "🔌", "az-wan": "🌐", "az-lan": "🏠",
			"az-vpn-server": "🔒", "az-vpn-peer": "🔑", "az-tunnel": "🔗",
			"az-extension": "📞", "az-trunk": "📡", "az-inbound": "📥", "az-outbound": "📤",
			"az-omni": "💬", "whatsapp": "💬", "telegram": "✈️", "az-meeting": "🎥",
			"az-wifi": "📶", "az-wifi-ap": "📡", "az-firewall": "🛡️",
			"az-client": "💻", "az-alert": "🚨", "az-health": "❤️", "az-link": "🔗",
			"az-dinstar-gw": "📱", "az-dinstar-port": "📶",
		};

		// ─── Dinstar Gateway: rich card with port grid ───
		const renderGatewayCard = (data) => {
			const m = data.meta || {};
			const st = data.status || "";
			const isOffline = st === "error";
			const simCount = m.sim_count ?? "?";
			const poweredCount = m.powered ?? "?";
			const totalPorts = m.ports || 8;
			const uptimeText = m.uptime || "—";

			// Build mini port grid from child nodes data stored on gateway
			const portData = data._portGrid || [];
			let portGrid = "";
			for (let i = 0; i < totalPorts; i++) {
				const p = portData[i] || {};
				const hasSim = p.sim;
				const isPowered = p.power;
				let cls = "dg-port-off";
				let simIcon = "<span class='dg-nosim'>✕</span>";
				if (isOffline) {
					cls = "dg-port-unknown";
					simIcon = "<span class='dg-unknown'>?</span>";
				} else if (isPowered && hasSim) {
					cls = "dg-port-active";
					simIcon = "<span class='dg-sim'>●</span>";
				} else if (isPowered && !hasSim) {
					cls = "dg-port-nosim";
					simIcon = "<span class='dg-nosim'>✕</span>";
				} else if (!isPowered && hasSim) {
					cls = "dg-port-simoff";
					simIcon = "<span class='dg-simoff'>◐</span>";
				}
				portGrid += `<div class="dg-port ${cls}" title="Port ${i}: ${isPowered ? 'ON' : 'OFF'} | SIM: ${hasSim ? 'Yes' : 'No'}">
					<span class="dg-port-num">${i}</span>${simIcon}
				</div>`;
			}

			return `
				<div class="az-node-card az-type-az-dinstar-gw az-st-${st} dg-gw-card" data-id="${data.id}">
					<div class="az-node-header">
						<span class="az-node-icon">📱</span>
						<span class="az-node-title">${this.truncate(data.label, 30)}</span>
						${statusDot(st)}
					</div>
					<div class="dg-gw-stats">
						<span class="dg-stat" title="SIM Cards">💳 ${simCount}/${totalPorts}</span>
						<span class="dg-stat" title="Powered">⚡ ${poweredCount}/${totalPorts}</span>
						<span class="dg-stat" title="Uptime">⏱ ${this.truncate(uptimeText, 12)}</span>
					</div>
					<div class="dg-port-grid">${portGrid}</div>
				</div>`;
		};

		// ─── Dinstar Port: detailed card ───
		const renderPortCard = (data) => {
			const m = data.meta || {};
			const st = data.status || "";
			const hasSim = m.sim;
			const isPowered = m.power;
			const sipAcc = m.sip || "";

			const powerIcon = isPowered
				? "<span class='dp-on' title='Module ON'>⚡</span>"
				: "<span class='dp-off' title='Module OFF'>⭘</span>";
			const simIcon = hasSim
				? "<span class='dp-sim-yes' title='SIM Present'>💳</span>"
				: "<span class='dp-sim-no' title='No SIM'>∅</span>";
			const smscLine = m.smsc ? `<span class="dp-smsc" title="SMSC">${m.smsc}</span>` : "";

			return `
				<div class="az-node-card az-type-az-dinstar-port az-st-${st} dp-card" data-id="${data.id}">
					<div class="dp-header">
						<span class="dp-port-label">${this.truncate(data.label, 22)}</span>
						${statusDot(st)}
					</div>
					<div class="dp-indicators">
						${powerIcon}${simIcon}
						<span class="dp-sip" title="SIP Account">${sipAcc}</span>
					</div>
					${smscLine}
				</div>`;
		};

		// Labels for leaf nodes (non-parent)
		this.cy.nodeHtmlLabel([
			{
				query: "node[type = 'az-dinstar-gw']",
				halign: "center",
				valign: "center",
				cssClass: "az-html-label",
				tpl: (data) => renderGatewayCard(data),
			},
			{
				query: "node[type = 'az-dinstar-port']",
				halign: "center",
				valign: "center",
				cssClass: "az-html-label",
				tpl: (data) => renderPortCard(data),
			},
			{
				query: "node:childless[type != 'az-dinstar-gw'][type != 'az-dinstar-port']",
				halign: "center",
				valign: "center",
				cssClass: "az-html-label",
				tpl: (data) => {
					const icon = typeIcons[data.type] || "●";
					const st = data.status || "";
					const metaLine = this.getMetaLine(data);
					return `
						<div class="az-node-card az-type-${data.type} az-st-${st}" data-id="${data.id}">
							<div class="az-node-header">
								<span class="az-node-icon">${icon}</span>
								<span class="az-node-title">${this.truncate(data.label, 28)}</span>
								${statusDot(st)}
							</div>
							${metaLine ? `<div class="az-node-meta">${metaLine}</div>` : ""}
						</div>`;
				},
			},
			{
				query: "node:parent",
				halign: "center",
				valign: "top",
				cssClass: "az-html-group-label",
				tpl: (data) => {
					return `
						<div class="az-group-header az-type-${data.type}">
							<span class="az-group-title">${data.label}</span>
							${data.childCount ? `<span class="az-group-badge">${data.childCount}</span>` : ""}
						</div>`;
				},
			},
		]);
	}

	getMetaLine(data) {
		const m = data.meta || {};
		if (m.ip) return m.ip;
		if (m.host) return `${m.host}${m.port ? ':' + m.port : ''}`;
		if (m.number) return `#${m.number}`;
		if (m.address) return m.address;
		if (m.subnet) return m.subnet;
		if (m.ssid) return m.ssid;
		if (m.ips) return m.ips;
		if (m.url) return m.url;
		if (m.endpoint) return m.endpoint;
		if (m.did) return m.did;
		if (m.severity) return m.severity;
		if (m.latency) return `${m.latency}ms`;
		if (m.provider) return m.provider;
		if (m.user) return m.user;
		return "";
	}

	truncate(str, len) {
		if (!str) return "";
		return str.length > len ? str.substring(0, len) + "…" : str;
	}

	/* ─── Custom Context Menu ────────────────────────────────── */
	setupContextMenu() {
		if (!this.cy) return;
		const self = this;

		this.cy.cxtmenu({
			selector: "node:childless",
			commands: [
				{
					content: '<span class="az-ctx-icon">👁️</span> ' + __("Details"),
					select: (ele) => self.showSidePanelFor(ele.data()),
				},
				{
					content: '<span class="az-ctx-icon">📂</span> ' + __("Open Form"),
					select: (ele) => {
						const d = ele.data();
						if (d.doctype && d.docname) frappe.set_route("Form", d.doctype, d.docname);
					},
				},
				{
					content: '<span class="az-ctx-icon">📋</span> ' + __("Open List"),
					select: (ele) => {
						const d = ele.data();
						if (d.doctype) frappe.set_route("List", d.doctype);
					},
				},
				{
					content: '<span class="az-ctx-icon">✏️</span> ' + __("Quick Edit"),
					select: (ele) => {
						const d = ele.data();
						if (d.doctype && d.docname && self.permissions.can_write) {
							frappe.set_route("Form", d.doctype, d.docname);
						} else if (!self.permissions.can_write) {
							frappe.show_alert({ message: __("No write permission"), indicator: "orange" });
						}
					},
				},
				{
					content: '<span class="az-ctx-icon">🔍</span> ' + __("Focus"),
					select: (ele) => self.engine._focusNode(ele),
				},
				{
					content: '<span class="az-ctx-icon">🪟</span> ' + __("Window"),
					select: (ele) => self.openDetailWindow(ele),
				},
			],
			fillColor: "rgba(15, 23, 42, 0.94)",
			activeFillColor: "rgba(99, 102, 241, 0.9)",
			activePadding: 10,
			indicatorSize: 16,
			separatorWidth: 3,
			spotlightPadding: 8,
			adaptativeNodeSpotlightRadius: true,
			minSpotlightRadius: 20,
			maxSpotlightRadius: 45,
			zIndex: 9999,
		});

		// Group context menu
		this.cy.cxtmenu({
			selector: "node:parent",
			commands: [
				{
					content: '<span class="az-ctx-icon">📋</span> ' + __("Open List"),
					select: (ele) => {
						const d = ele.data();
						const routeMap = {
							"az-group-infra": "Arrowz Box",
							"az-group-voip": "AZ Extension",
							"az-group-vpn": "VPN Server",
							"az-group-wifi": "WiFi Network",
							"az-group-firewall": "Firewall Zone",
							"az-group-comms": "AZ Omni Provider",
							"az-group-monitor": "Network Alert",
							"az-group-clients": "Network Client",
						};
						const dt = routeMap[d.type];
						if (dt) frappe.set_route("List", dt);
					},
				},
				{
					content: '<span class="az-ctx-icon">🔍</span> ' + __("Focus Group"),
					select: (ele) => self.engine._focusNode(ele),
				},
			],
			fillColor: "rgba(15, 23, 42, 0.92)",
			activeFillColor: "rgba(99, 102, 241, 0.9)",
			activePadding: 8,
			indicatorSize: 14,
			zIndex: 9999,
		});
	}

	/* ─── Node Click → Side Panel ────────────────────────────── */
	onNodeClick(data, evt) {
		// Don't show panel for group nodes
		if (data.parent === undefined && data.childCount) return;
		this.showSidePanelFor(data);
	}

	onNodeDblClick(data) {
		if (data.doctype && data.docname) {
			frappe.set_route("Form", data.doctype, data.docname);
		} else if (data.doctype) {
			frappe.set_route("List", data.doctype);
		}
	}

	/* ─── Side Panel ─────────────────────────────────────────── */
	setupSidePanel() {
		this.sidePanel = document.getElementById("topology-side-panel");
		const closeBtn = document.getElementById("side-panel-close");
		if (closeBtn) {
			closeBtn.addEventListener("click", () => this.closeSidePanel());
		}
	}

	showSidePanelFor(data) {
		if (!this.sidePanel) return;
		const body = document.getElementById("side-panel-body");
		if (!body) return;

		const m = data.meta || {};
		const statusColors = { active: "#10b981", warning: "#f59e0b", error: "#ef4444", disabled: "#94a3b8" };
		const statusColor = statusColors[data.status] || "#94a3b8";
		const statusLabel = data.status ? data.status.charAt(0).toUpperCase() + data.status.slice(1) : "—";

		let metaRows = "";
		Object.entries(m).forEach(([k, v]) => {
			if (v !== null && v !== undefined && v !== "") {
				metaRows += `<div class="az-sp-row"><span class="az-sp-key">${this.humanize(k)}</span><span class="az-sp-val">${v}</span></div>`;
			}
		});

		// Connections
		const node = this.cy?.getElementById(data.id);
		let connHtml = "";
		if (node && node.length) {
			const neighbors = node.neighborhood("node");
			if (neighbors.length > 0) {
				connHtml = `<div class="az-sp-section">
					<h4>${__("Connections")} (${neighbors.length})</h4>
					${neighbors.map((n) => `<div class="az-sp-conn" data-node-id="${n.id()}">${n.data("label") || n.id()}</div>`).join("")}
				</div>`;
			}
		}

		body.innerHTML = `
			<div class="az-sp-header" style="border-color: ${statusColor}">
				<h3>${data.label || data.id}</h3>
				<div class="az-sp-status" style="color: ${statusColor}">● ${statusLabel}</div>
			</div>
			${data.doctype ? `<div class="az-sp-doctype">${data.doctype}</div>` : ""}
			<div class="az-sp-section">
				<h4>${__("Properties")}</h4>
				${metaRows || `<div class="az-sp-empty">${__("No additional properties")}</div>`}
			</div>
			${connHtml}
			<div class="az-sp-actions">
				${data.doctype && data.docname ? `<button class="btn btn-xs btn-primary az-sp-btn" onclick="frappe.set_route('Form','${data.doctype}','${data.docname}')">${__("Open Form")}</button>` : ""}
				${data.doctype ? `<button class="btn btn-xs btn-default az-sp-btn" onclick="frappe.set_route('List','${data.doctype}')">${__("Open List")}</button>` : ""}
				${data.doctype && data.docname && this.permissions.can_write ? `<button class="btn btn-xs btn-warning az-sp-btn" onclick="frappe.set_route('Form','${data.doctype}','${data.docname}')">${__("Edit")}</button>` : ""}
			</div>
		`;

		// Connection click → focus node
		body.querySelectorAll(".az-sp-conn").forEach((el) => {
			el.addEventListener("click", () => {
				const nid = el.dataset.nodeId;
				const n = this.cy.getElementById(nid);
				if (n.length) {
					this.engine._focusNode(n);
					this.showSidePanelFor(n.data());
				}
			});
		});

		this.sidePanel.classList.add("open");
	}

	closeSidePanel() {
		if (this.sidePanel) this.sidePanel.classList.remove("open");
	}

	humanize(str) {
		return str.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
	}

	/* ─── Floating Detail Window ─────────────────────────────── */
	openDetailWindow(ele) {
		const data = ele.data();
		const m = data.meta || {};
		let content = '<div class="az-win-content">';
		content += `<div class="az-win-status az-st-${data.status || ""}">● ${data.status || "—"}</div>`;
		Object.entries(m).forEach(([k, v]) => {
			if (v !== null && v !== undefined && v !== "") {
				content += `<div class="az-win-row"><span>${this.humanize(k)}</span><span>${v}</span></div>`;
			}
		});
		if (data.doctype) {
			content += `<div class="az-win-actions">`;
			content += `<button class="btn btn-xs btn-primary" onclick="frappe.set_route('Form','${data.doctype}','${data.docname || ""}')">${__("Open")}</button>`;
			content += `</div>`;
		}
		content += "</div>";

		if (this.FloatingWindow) {
			new this.FloatingWindow({
				title: data.label || data.id,
				color: data.borderColor,
				content: content,
				icon: data.icon,
				width: 350,
				height: 250,
			});
		}
	}

	/* ─── Toolbar ────────────────────────────────────────────── */
	setupToolbar() {
		// Layout buttons
		document.querySelectorAll("[data-layout]").forEach((btn) => {
			btn.addEventListener("click", () => {
				document.querySelectorAll("[data-layout]").forEach((b) => b.classList.remove("active"));
				btn.classList.add("active");
				const layout = btn.dataset.layout;
				this.activeLayout = layout;
				if (this.engine) this.engine.runLayout(layout);
			});
		});

		// Zoom controls
		document.getElementById("btn-zoom-in")?.addEventListener("click", () => this.engine?.zoomIn());
		document.getElementById("btn-zoom-out")?.addEventListener("click", () => this.engine?.zoomOut());
		document.getElementById("btn-fit")?.addEventListener("click", () => this.engine?.fit(50));

		// Export
		document.getElementById("btn-export-png")?.addEventListener("click", () => {
			if (!this.engine) return;
			const a = document.createElement("a");
			a.href = this.engine.toPNG();
			a.download = "arrowz-topology.png";
			a.click();
		});

		// Close all windows
		document.getElementById("btn-close-windows")?.addEventListener("click", () => {
			if (this.FloatingWindow) this.FloatingWindow.closeAll();
			this.closeSidePanel();
		});

		// Fullscreen
		document.getElementById("btn-fullscreen")?.addEventListener("click", () => {
			const container = document.querySelector(".az-topology-wrapper");
			if (!container) return;
			if (document.fullscreenElement) {
				document.exitFullscreen();
			} else {
				container.requestFullscreen();
			}
		});

		// Side panel toggle
		document.getElementById("btn-toggle-panel")?.addEventListener("click", () => {
			if (this.sidePanel?.classList.contains("open")) {
				this.closeSidePanel();
			}
		});

		// Refresh
		document.getElementById("btn-refresh")?.addEventListener("click", () => {
			this.refresh();
		});

		// Quick-add
		document.getElementById("btn-quick-add")?.addEventListener("click", (e) => {
			this.showQuickAddMenu(e.target);
		});
	}

	/* ─── Quick Add Menu ─────────────────────────────────────── */
	showQuickAddMenu(target) {
		if (!this.permissions.can_write) {
			frappe.show_alert({ message: __("No write permission"), indicator: "orange" });
			return;
		}
		const items = [
			{ label: __("New Extension"), doctype: "AZ Extension" },
			{ label: __("New Trunk"), doctype: "AZ Trunk" },
			{ label: __("New VPN Server"), doctype: "VPN Server" },
			{ label: __("New VPN Peer"), doctype: "VPN Peer" },
			{ label: __("New S2S Tunnel"), doctype: "Site to Site Tunnel" },
			{ label: __("New Box"), doctype: "Arrowz Box" },
			{ label: __("New WiFi Network"), doctype: "WiFi Network" },
			{ label: __("New Firewall Zone"), doctype: "Firewall Zone" },
			{ label: __("New Omni Provider"), doctype: "AZ Omni Provider" },
			{ label: __("New Meeting Room"), doctype: "AZ Meeting Room" },
		];

		// Remove any existing popup
		document.querySelector(".az-quick-add-popup")?.remove();

		const menu = items.map((item) =>
			`<div class="az-qa-item" data-dt="${item.doctype}">${item.label}</div>`
		).join("");

		const popup = document.createElement("div");
		popup.className = "az-quick-add-popup";
		popup.innerHTML = menu;
		popup.style.position = "absolute";
		const rect = target.getBoundingClientRect();
		popup.style.top = (rect.bottom + 4) + "px";
		popup.style.left = rect.left + "px";

		popup.querySelectorAll(".az-qa-item").forEach((el) => {
			el.addEventListener("click", () => {
				frappe.new_doc(el.dataset.dt);
				popup.remove();
			});
		});

		document.body.appendChild(popup);
		setTimeout(() => {
			const handler = (e) => {
				if (!popup.contains(e.target)) {
					popup.remove();
					document.removeEventListener("click", handler);
				}
			};
			document.addEventListener("click", handler);
		}, 100);
	}

	/* ─── Search ─────────────────────────────────────────────── */
	setupSearch() {
		const input = document.getElementById("topology-search");
		const clear = document.getElementById("search-clear");
		if (!input) return;

		let debounce;
		input.addEventListener("input", () => {
			clearTimeout(debounce);
			if (clear) clear.style.display = input.value ? "block" : "none";
			debounce = setTimeout(() => {
				if (this.engine) this.engine.search(input.value);
			}, 250);
		});

		if (clear) {
			clear.addEventListener("click", () => {
				input.value = "";
				clear.style.display = "none";
				if (this.engine) this.engine.clearFilter();
			});
		}
	}

	/* ─── Filters ────────────────────────────────────────────── */
	setupFilters() {
		document.querySelectorAll("[data-filter]").forEach((btn) => {
			btn.addEventListener("click", () => {
				document.querySelectorAll("[data-filter]").forEach((b) => b.classList.remove("active"));
				btn.classList.add("active");
				this.activeFilter = btn.dataset.filter;
				this.applyFilter(this.activeFilter);
			});
		});
	}

	applyFilter(filter) {
		if (!this.cy) return;
		this.cy.elements().removeClass("fv-dimmed");

		if (filter === "all") return;

		const groupMap = {
			infrastructure: "grp-infra",
			voip: "grp-voip",
			vpn: "grp-vpn",
			wifi: "grp-wifi",
			firewall: "grp-firewall",
			comms: "grp-comms",
			monitoring: "grp-monitor",
			clients: "grp-clients",
		};

		const groupId = groupMap[filter];
		if (!groupId) return;

		const groupNode = this.cy.getElementById(groupId);
		if (!groupNode.length) return;

		// Show group + children + server, dim everything else
		const keep = groupNode.union(groupNode.descendants()).union(this.cy.getElementById("server-config"));
		const keepEdges = keep.connectedEdges();
		this.cy.elements().not(keep.union(keepEdges)).addClass("fv-dimmed");

		this.cy.animate({
			fit: { eles: keep, padding: 60 },
			duration: 600,
		});
	}

	/* ─── Workspace Quick Links ──────────────────────────────── */
	setupWorkspaceLinks() {
		const container = document.getElementById("topology-quick-links");
		if (!container) return;

		const links = this.data?.workspace_links || [];
		if (links.length === 0) return;

		const iconMap = {
			headset: "📱", monitor: "🖥️", "bar-chart": "📊", phone: "📞",
			"message-square": "💬", activity: "📈", "credit-card": "💳",
			wifi: "📶", settings: "⚙️", sliders: "🔧",
		};

		container.innerHTML = links.map((lnk) =>
			`<a href="${lnk.route}" class="az-qlink az-qlink-${lnk.category || "default"}">
				<span class="az-qlink-icon">${iconMap[lnk.icon] || "🔗"}</span>
				<span class="az-qlink-label">${lnk.label}</span>
			</a>`
		).join("");
	}

	/* ─── Status Bar ─────────────────────────────────────────── */
	updateStatusBar() {
		const stats = this.data?.summary || {};
		const bar = document.getElementById("topology-status-bar");
		if (!bar) return;

		const items = [
			{ label: __("Boxes"), val: stats.boxes || 0, icon: "📡" },
			{ label: __("Extensions"), val: stats.extensions || 0, icon: "📞" },
			{ label: __("VPN Peers"), val: stats.vpn_peers || 0, icon: "🔑" },
			{ label: __("Tunnels"), val: stats.tunnels || 0, icon: "🔗" },
			{ label: __("WiFi"), val: stats.wifi_networks || 0, icon: "📶" },
			{ label: __("Clients"), val: stats.clients || 0, icon: "💻" },
			{ label: __("Alerts"), val: stats.alerts || 0, icon: "🚨" },
			{ label: __("Calls Today"), val: stats.call_logs_today || 0, icon: "📞" },
		];

		bar.innerHTML = items.map((s) =>
			`<div class="az-stat"><span class="az-stat-icon">${s.icon}</span><span class="az-stat-val">${s.val}</span><span class="az-stat-label">${s.label}</span></div>`
		).join("");
	}

	/* ─── Keyboard Shortcuts ─────────────────────────────────── */
	setupKeyboard() {
		document.addEventListener("keydown", (e) => {
			// Escape closes panel
			if (e.key === "Escape") {
				this.closeSidePanel();
				if (this.engine) this.engine.clearFilter();
			}
			// Ctrl+F focuses search
			if (e.ctrlKey && e.key === "f") {
				e.preventDefault();
				document.getElementById("topology-search")?.focus();
			}
		});
	}

	/* ─── Refresh ────────────────────────────────────────────── */
	async refresh() {
		this.showLoader(true);
		try {
			// Destroy old engine
			if (this.engine) {
				this.engine.destroy();
				this.engine = null;
				this.cy = null;
			}
			await this.fetchData();
			this.buildGraph();
			this.setupHtmlLabels();
			this.setupContextMenu();
			this.updateStatusBar();
			setTimeout(() => this.engine?.fit(50), 1200);
		} catch (err) {
			console.error("[Arrowz Topology] Refresh error:", err);
		} finally {
			this.showLoader(false);
		}
	}

	/* ─── Loader ─────────────────────────────────────────────── */
	showLoader(show) {
		const loader = document.getElementById("topology-loader");
		if (loader) loader.style.display = show ? "flex" : "none";
	}
}
