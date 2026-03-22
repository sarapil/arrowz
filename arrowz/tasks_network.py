# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
Network Management Scheduled Tasks

Background jobs for health checks, telemetry sync, analytics collection,
quota management, billing generation, and data cleanup.
"""

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import now_datetime, add_days, add_to_date, getdate


# ── Box Health ───────────────────────────────────────────────────────

def check_box_health():
	"""Check health of all active Arrowz Boxes.

	Runs every minute via scheduler.
	"""
	AB = DocType("Arrowz Box")
	boxes = (
		frappe.qb.from_(AB)
		.select(AB.name, AB.last_heartbeat, AB.status)
		.where(AB.status != "Maintenance")
		.run(as_dict=True)
	)

	settings = frappe.get_cached_doc("Arrowz Network Settings")
	timeout_seconds = (settings.health_check_interval or 60) * 3  # 3x interval = stale

	for box in boxes:
		if box.last_heartbeat:
			elapsed = (now_datetime() - box.last_heartbeat).total_seconds()
			if elapsed > timeout_seconds and box.status == "Online":
				frappe.db.set_value("Arrowz Box", box.name, "status", "Offline")
				# Create alert
				try:
					frappe.get_doc({
						"doctype": "Network Alert",
						"arrowz_box": box.name,
						"alert_type": "Service Down",
						"severity": "Critical",
						"message": _("Box {0} has not sent heartbeat for {1} seconds").format(
							box.name, int(elapsed)
						),
					}).insert(ignore_permissions=True)
				except Exception:
					pass

	frappe.db.commit()


def check_wan_health():
	"""Check WAN connection health for all active boxes.

	Runs every minute via scheduler. Retrieves WAN health data
	from each online box.
	"""
	AB = DocType("Arrowz Box")
	boxes = (
		frappe.qb.from_(AB)
		.select(AB.name)
		.where(AB.status == "Online")
		.run(as_dict=True)
	)

	for box in boxes:
		try:
			from arrowz.arrowz_api.utils.box_connector import BoxConnector

			connector = BoxConnector(box_name=box.name)
			wan_data = connector._request("GET", "/api/v1/network/wan/health")

			for wan in wan_data.get("connections", []):
				frappe.get_doc({
					"doctype": "WAN Health Check",
					"arrowz_box": box.name,
					"wan_connection": wan.get("name"),
					"status": wan.get("status", "Healthy"),
					"latency_ms": wan.get("latency_ms"),
					"packet_loss_percent": wan.get("packet_loss_percent"),
					"jitter_ms": wan.get("jitter_ms"),
					"target_host": wan.get("target_host"),
					"public_ip": wan.get("public_ip"),
				}).insert(ignore_permissions=True)

		except Exception:
			pass  # Box may be offline

	frappe.db.commit()


# ── Bandwidth & Accounting ───────────────────────────────────────────

def sync_bandwidth_stats():
	"""Sync bandwidth usage statistics from all online boxes.

	Runs every 5 minutes.
	"""
	AB = DocType("Arrowz Box")
	boxes = (
		frappe.qb.from_(AB)
		.select(AB.name)
		.where(AB.status == "Online")
		.run(as_dict=True)
	)

	for box in boxes:
		try:
			from arrowz.arrowz_api.utils.box_connector import BoxConnector

			connector = BoxConnector(box_name=box.name)
			stats = connector.get_traffic_stats("5min")

			for client_stat in stats.get("clients", []):
				frappe.get_doc({
					"doctype": "Bandwidth Usage",
					"arrowz_box": box.name,
					"network_client": client_stat.get("mac_address"),
					"period_type": "5min",
					"bytes_downloaded": client_stat.get("bytes_downloaded", 0),
					"bytes_uploaded": client_stat.get("bytes_uploaded", 0),
					"average_download_kbps": client_stat.get("avg_download_kbps"),
					"average_upload_kbps": client_stat.get("avg_upload_kbps"),
					"peak_download_kbps": client_stat.get("peak_download_kbps"),
					"peak_upload_kbps": client_stat.get("peak_upload_kbps"),
				}).insert(ignore_permissions=True)

		except Exception:
			frappe.log_error(
				f"Bandwidth sync failed for box {box.name}",
				"Bandwidth Sync Error",
			)

	frappe.db.commit()


def collect_ip_accounting():
	"""Collect IP accounting snapshots from all online boxes.

	Runs every 5 minutes.
	"""
	AB = DocType("Arrowz Box")
	boxes = (
		frappe.qb.from_(AB)
		.select(AB.name)
		.where(AB.status == "Online")
		.run(as_dict=True)
	)

	for box in boxes:
		try:
			from arrowz.arrowz_api.utils.box_connector import BoxConnector

			connector = BoxConnector(box_name=box.name)
			stats = connector.get_traffic_stats("5min")

			frappe.get_doc({
				"doctype": "IP Accounting Snapshot",
				"arrowz_box": box.name,
				"period": "5min",
				"total_bytes_in": stats.get("total_bytes_in", 0),
				"total_bytes_out": stats.get("total_bytes_out", 0),
				"total_packets_in": stats.get("total_packets_in", 0),
				"total_packets_out": stats.get("total_packets_out", 0),
				"active_connections": stats.get("active_connections", 0),
				"unique_clients": stats.get("unique_clients", 0),
				"top_talkers_json": frappe.as_json(stats.get("top_talkers", [])),
				"protocol_breakdown_json": frappe.as_json(stats.get("protocol_breakdown", {})),
			}).insert(ignore_permissions=True)

		except Exception:
			pass

	frappe.db.commit()


# ── WiFi ─────────────────────────────────────────────────────────────

def collect_wifi_analytics():
	"""Collect WiFi analytics from all online boxes.

	Runs every 5 minutes.
	"""
	AB = DocType("Arrowz Box")
	boxes = (
		frappe.qb.from_(AB)
		.select(AB.name)
		.where(AB.status == "Online")
		.run(as_dict=True)
	)

	for box in boxes:
		try:
			from arrowz.arrowz_api.utils.box_connector import BoxConnector

			connector = BoxConnector(box_name=box.name)
			wifi_data = connector.get_wifi_status()

			for network in wifi_data.get("networks", []):
				frappe.get_doc({
					"doctype": "WiFi Analytics",
					"arrowz_box": box.name,
					"wifi_network": network.get("ssid"),
					"period": "5min",
					"connected_clients": network.get("connected_clients", 0),
					"unique_clients": network.get("unique_clients", 0),
					"bytes_downloaded": network.get("bytes_downloaded", 0),
					"bytes_uploaded": network.get("bytes_uploaded", 0),
					"average_signal_strength": network.get("avg_signal"),
					"channel_utilization": network.get("channel_utilization"),
				}).insert(ignore_permissions=True)

		except Exception:
			pass

	frappe.db.commit()


def check_voucher_expiry():
	"""Check and expire WiFi vouchers that have passed their expiry time.

	Runs every minute.
	"""
	WV = DocType("WiFi Voucher")
	expired = (
		frappe.qb.from_(WV)
		.select(WV.name)
		.where(WV.status == "Active")
		.where(WV.expires_on <= now_datetime())
		.run(as_dict=True)
	)

	for voucher in expired:
		frappe.db.set_value("WiFi Voucher", voucher.name, "status", "Expired")

	# Also expire user sessions
	WUS = DocType("WiFi User Session")
	expired_sessions = (
		frappe.qb.from_(WUS)
		.select(WUS.name, WUS.wifi_voucher)
		.where(WUS.status == "Active")
		.where(WUS.wifi_voucher.isnotnull())
		.run(as_dict=True)
	)

	for session in expired_sessions:
		if session.wifi_voucher:
			voucher_status = frappe.db.get_value("WiFi Voucher", session.wifi_voucher, "status")
			if voucher_status == "Expired":
				frappe.db.set_value("WiFi User Session", session.name, {
					"status": "Expired",
					"end_time": now_datetime(),
					"disconnect_reason": "Quota",
				})

	frappe.db.commit()


# ── Quotas ───────────────────────────────────────────────────────────

def check_quota_usage():
	"""Check quota usage for all active assignments.

	Runs every 5 minutes.
	"""
	QA = DocType("Quota Assignment")
	assignments = (
		frappe.qb.from_(QA)
		.select(QA.star)
		.where(QA.enabled == 1)
		.run(as_dict=True)
	)

	for assignment in assignments:
		try:
			doc = frappe.get_doc("Quota Assignment", assignment.name)
			doc.recalculate_status()
		except Exception:
			pass

	frappe.db.commit()


def reset_daily_quotas():
	"""Reset daily quota counters. Runs daily."""
	_reset_quotas("Daily")


def reset_weekly_quotas():
	"""Reset weekly quota counters. Runs weekly."""
	_reset_quotas("Weekly")


def reset_monthly_quotas():
	"""Reset monthly quota counters. Runs monthly."""
	_reset_quotas("Monthly")


def _reset_quotas(quota_type: str):
	"""Reset quota assignments for the given period type."""
	QA = DocType("Quota Assignment")
	UQ = DocType("Usage Quota")

	assignments = (
		frappe.qb.from_(QA)
		.join(UQ).on(QA.usage_quota == UQ.name)
		.select(QA.name)
		.where(QA.enabled == 1)
		.where(UQ.quota_type == quota_type)
		.run(as_dict=True)
	)

	for assignment in assignments:
		try:
			doc = frappe.get_doc("Quota Assignment", assignment.name)
			doc.reset_usage()
		except Exception:
			pass

	frappe.db.commit()


# ── Alerts ───────────────────────────────────────────────────────────

def evaluate_alert_rules():
	"""Evaluate all enabled alert rules.

	Runs every 2 minutes.
	"""
	AR = DocType("Alert Rule")
	rules = (
		frappe.qb.from_(AR)
		.select(AR.star)
		.where(AR.enabled == 1)
		.run(as_dict=True)
	)

	for rule in rules:
		try:
			_evaluate_rule(rule)
		except Exception:
			pass

	frappe.db.commit()


def _evaluate_rule(rule: dict):
	"""Evaluate a single alert rule against current data."""
	# Check cooldown
	if rule.get("last_triggered"):
		cooldown = (rule.get("cooldown_minutes") or 15) * 60
		elapsed = (now_datetime() - rule["last_triggered"]).total_seconds()
		if elapsed < cooldown:
			return

	# Get current value based on alert type
	current_value = _get_metric_value(rule)
	if current_value is None:
		return

	# Evaluate condition
	op = rule.get("condition_operator", ">")
	threshold = rule.get("condition_value", 0)

	triggered = False
	if op == ">" and current_value > threshold:
		triggered = True
	elif op == "<" and current_value < threshold:
		triggered = True
	elif op == "=" and current_value == threshold:
		triggered = True
	elif op == ">=" and current_value >= threshold:
		triggered = True
	elif op == "<=" and current_value <= threshold:
		triggered = True

	if triggered:
		message = (rule.get("message_template") or
			_("{alert_type} alert: current value {value} {op} {threshold}")).format(
			alert_type=rule.get("alert_type"),
			value=current_value,
			op=op,
			threshold=threshold,
		)

		frappe.get_doc({
			"doctype": "Network Alert",
			"arrowz_box": rule.get("arrowz_box"),
			"alert_rule": rule.get("name"),
			"alert_type": rule.get("alert_type"),
			"severity": rule.get("severity", "Warning"),
			"message": message,
		}).insert(ignore_permissions=True)

		frappe.db.set_value("Alert Rule", rule["name"], {
			"last_triggered": now_datetime(),
			"trigger_count": (rule.get("trigger_count") or 0) + 1,
		})

		# Send notifications
		if rule.get("notification_channels") in ("Email", "Both") and rule.get("email_recipients"):
			_send_alert_email(rule, message)


def _get_metric_value(rule: dict):
	"""Get current metric value for an alert rule."""
	alert_type = rule.get("alert_type", "")
	box_name = rule.get("arrowz_box")

	if not box_name:
		return None

	# Get latest health log for the box
	ABHL = DocType("Arrowz Box Health Log")
	latest = (
		frappe.qb.from_(ABHL)
		.select(ABHL.cpu_usage, ABHL.ram_usage, ABHL.disk_usage, ABHL.active_clients)
		.where(ABHL.arrowz_box == box_name)
		.orderby(ABHL.creation, order=frappe.qb.desc)
		.limit(1)
		.run(as_dict=True)
	)

	if not latest:
		return None

	metric_map = {
		"High CPU": "cpu_usage",
		"High RAM": "ram_usage",
		"High Disk": "disk_usage",
		"Client Threshold": "active_clients",
	}

	field = metric_map.get(alert_type)
	if field:
		return latest[0].get(field)

	return None


def _send_alert_email(rule: dict, message: str):
	"""Send alert email notification."""
	recipients = [e.strip() for e in (rule.get("email_recipients") or "").split(",") if e.strip()]
	if not recipients:
		return

	try:
		frappe.sendmail(
			recipients=recipients,
			subject=_("Arrowz Alert: {0}").format(rule.get("alert_type")),
			message=message,
			now=True,
		)
	except Exception:
		frappe.log_error("Failed to send alert email", "Alert Email Error")


# ── Client Sync ──────────────────────────────────────────────────────

def sync_client_list():
	"""Sync connected client list from all online boxes.

	Runs hourly.
	"""
	AB = DocType("Arrowz Box")
	boxes = (
		frappe.qb.from_(AB)
		.select(AB.name)
		.where(AB.status == "Online")
		.run(as_dict=True)
	)

	for box in boxes:
		try:
			from arrowz.arrowz_api.utils.box_connector import BoxConnector

			connector = BoxConnector(box_name=box.name)
			clients = connector.get_connected_clients()

			# Mark all clients for this box as potentially offline
			NC = DocType("Network Client")
			frappe.qb.update(NC).set(NC.status, "Offline").where(
				(NC.arrowz_box == box.name) & (NC.status == "Online")
			).run()

			# Update connected clients
			for client in clients:
				mac = (client.get("mac_address") or "").upper()
				if not mac:
					continue

				if frappe.db.exists("Network Client", mac):
					frappe.db.set_value("Network Client", mac, {
						"status": "Online",
						"ip_address": client.get("ip_address"),
						"last_seen": now_datetime(),
						"connection_type": client.get("connection_type"),
					}, update_modified=False)

		except Exception:
			pass

	frappe.db.commit()


def cleanup_stale_sessions():
	"""End sessions that are stale (no activity for session timeout).

	Runs hourly.
	"""
	settings = frappe.get_cached_doc("Arrowz Network Settings")
	timeout_minutes = settings.session_timeout_minutes or 480

	cutoff = add_to_date(now_datetime(), minutes=-timeout_minutes)

	CS = DocType("Client Session")
	stale = (
		frappe.qb.from_(CS)
		.select(CS.name)
		.where(CS.status == "Active")
		.where(CS.start_time <= cutoff)
		.run(as_dict=True)
	)

	for session in stale:
		frappe.db.set_value("Client Session", session.name, {
			"status": "Ended",
			"end_time": now_datetime(),
			"disconnect_reason": "Timeout",
		})

	frappe.db.commit()


# ── Cleanup ──────────────────────────────────────────────────────────

def cleanup_old_logs():
	"""Delete old health logs, events, and firewall logs.

	Runs daily.
	"""
	settings = frappe.get_cached_doc("Arrowz Network Settings")
	retention_days = settings.retention_days_logs or 90
	cutoff = add_days(getdate(), -retention_days)

	for doctype in ("Arrowz Box Health Log", "Network Event", "Firewall Log"):
		DT = DocType(doctype)
		frappe.qb.from_(DT).delete().where(DT.creation < cutoff).run()

	frappe.db.commit()


def cleanup_old_sessions():
	"""Delete old client sessions and WiFi user sessions.

	Runs daily.
	"""
	settings = frappe.get_cached_doc("Arrowz Network Settings")
	retention_days = settings.retention_days_sessions or 180
	cutoff = add_days(getdate(), -retention_days)

	for doctype in ("Client Session", "WiFi User Session"):
		DT = DocType(doctype)
		frappe.qb.from_(DT).delete().where(DT.creation < cutoff).run()

	# Cleanup old bandwidth usage records
	accounting_retention = settings.retention_days_accounting or 365
	accounting_cutoff = add_days(getdate(), -accounting_retention)

	for doctype in ("Bandwidth Usage", "IP Accounting Snapshot", "WAN Health Check", "WiFi Analytics"):
		DT = DocType(doctype)
		frappe.qb.from_(DT).delete().where(DT.creation < accounting_cutoff).run()

	frappe.db.commit()


# ── Billing ──────────────────────────────────────────────────────────

def generate_daily_billing():
	"""Check for billing cycles that need invoices today.

	Runs daily.
	"""
	settings = frappe.get_cached_doc("Arrowz Network Settings")
	if not settings.enable_billing_integration or not settings.auto_generate_invoices:
		return

	today = getdate()

	BC = DocType("Billing Cycle")
	due_cycles = (
		frappe.qb.from_(BC)
		.select(BC.name)
		.where(BC.status == "Active")
		.where(BC.next_invoice_date <= today)
		.run(as_dict=True)
	)

	for cycle in due_cycles:
		try:
			doc = frappe.get_doc("Billing Cycle", cycle.name)
			doc.generate_invoice()
		except Exception as e:
			frappe.log_error(
				f"Invoice generation failed for cycle {cycle.name}: {e}",
				"Billing Error",
			)

	frappe.db.commit()


def generate_monthly_invoices():
	"""Generate monthly invoices for all active billing cycles.

	Runs monthly.
	"""
	generate_daily_billing()  # Same logic, just a monthly trigger


def generate_weekly_network_report():
	"""Generate weekly network usage summary report.

	Runs weekly.
	"""
	# Placeholder for weekly report generation
	pass
