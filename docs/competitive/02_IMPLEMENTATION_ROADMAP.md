# Arrowz Implementation Roadmap — خارطة طريق التنفيذ
# سد الفجوات مع Omada SDN + تعزيز المميزات الفريدة

> **تاريخ**: مارس 2026
> **الهدف**: خطة تنفيذ مرحلية لجعل Arrowz منافساً كاملاً لـ Omada SDN

---

## المرحلة 1: فجوات حرجة (Critical Gaps) — الأسابيع 1-4

> **الهدف**: سد أهم الفجوات التى يلاحظها المستخدم فوراً

### 1.1 🔄 WAN Auto-Failover
**الأولوية**: 🔴 عالية | **الصعوبة**: منخفضة | **المدة**: 3 أيام

**الوصف**: عند انقطاع WAN الأساسى، يتم التبديل تلقائياً لـ WAN الاحتياطى

**التنفيذ الفنى**:
```python
# DocType: WAN Connection — إضافة حقول:
# - failover_priority (int)
# - health_check_enabled (bool)
# - health_check_target (IP/domain)
# - health_check_interval (seconds)
# - failover_threshold (consecutive failures)
# - is_backup (bool)

# Scheduled Task: كل 30 ثانية
def check_wan_failover():
    """
    1. Ping health_check_target لكل WAN
    2. إذا فشل أكثر من failover_threshold مرات متتالية
    3. تفعيل WAN الاحتياطى عبر Device Provider
    4. إرسال Network Alert + Email notification
    5. عند عودة WAN الأصلى → failback تلقائى (اختيارى)
    """
```

**الملفات**:
- `arrowz/arrowz/doctype/wan_connection/wan_connection.json` — حقول جديدة
- `arrowz/arrowz/tasks/wan_failover.py` — منطق الـ failover
- `arrowz/device_providers/base_provider.py` — `switch_default_route(wan_id)` method
- `hooks.py` — scheduled task كل 30 ثانية

---

### 1.2 📱 Progressive Web App (PWA) — بديل Mobile App
**الأولوية**: 🔴 عالية | **الصعوبة**: متوسطة | **المدة**: 5 أيام

**الوصف**: بدلاً من تطبيق native (تكلفة عالية)، نبنى PWA يعمل كتطبيق

**التنفيذ الفنى**:
```javascript
// 1. Service Worker لـ offline support
// 2. Web App Manifest للتثبيت على الشاشة الرئيسية
// 3. Push Notifications عبر FCM
// 4. واجهة مبسطة للجوال:
//    - Dashboard سريع (overview cards)
//    - Alert notifications
//    - Topology مبسط
//    - Quick actions (restart, block, etc.)
```

**الملفات**:
- `arrowz/public/manifest.json` — PWA manifest
- `arrowz/public/sw.js` — Service Worker
- `arrowz/arrowz/page/arrowz_mobile/` — صفحة مبسطة للجوال
- `arrowz/api/mobile.py` — API مبسط للجوال

---

### 1.3 📊 Automated Network Reports (PDF)
**الأولوية**: 🟡 متوسطة | **الصعوبة**: منخفضة | **المدة**: 3 أيام

**الوصف**: تقارير دورية PDF تُرسل بالإيميل (يومى/أسبوعى/شهرى)

**التنفيذ الفنى**:
```python
# DocType: Network Report Config
# - report_type: daily/weekly/monthly
# - recipients: Multi-select users/emails
# - sections: checkboxes (WAN health, WiFi stats, Client stats, etc.)
# - schedule: cron expression

# يستخدم Frappe's PDF generation (weasyprint/wkhtmltopdf)
# Template: Jinja2 HTML → PDF

@frappe.whitelist()
def generate_network_report(report_type="weekly"):
    """
    Sections:
    1. Executive Summary (uptime %, alerts count, top issues)
    2. WAN Health (latency, jitter, packet loss graphs)
    3. WiFi Performance (client count, throughput, channel utilization)
    4. Client Statistics (top clients, new/returning)
    5. Bandwidth Usage (top consumers, by time)
    6. Security Events (blocked attempts, firewall hits)
    7. VoIP Statistics (call volume, ASR, ACD) ← ميزة فريدة
    """
```

**الملفات**:
- `arrowz/arrowz/doctype/network_report_config/` — DocType جديد
- `arrowz/arrowz/report/network_summary/` — Frappe Report
- `arrowz/templates/network_report.html` — قالب PDF
- `arrowz/tasks/reports.py` — مهمة مجدولة

---

### 1.4 🔧 Firmware Management (مركزى)
**الأولوية**: 🟡 متوسطة | **الصعوبة**: متوسطة | **المدة**: 4 أيام

**الوصف**: تحديث firmware لكل الأجهزة من مكان واحد

**التنفيذ الفنى**:
```python
# DocType: Firmware Image
# - device_type: MikroTik / Linux Box
# - version: string
# - file: Attach (binary)
# - release_notes: Text
# - compatible_models: Table

# DocType: Firmware Update Job
# - target_devices: Link to Arrowz Box (multi)
# - firmware: Link to Firmware Image
# - schedule: datetime (or immediate)
# - status: Pending/In Progress/Completed/Failed
# - rollback_enabled: bool

# MikroTik: /system/package/update + /file/upload
# Linux Box: API endpoint for package update
```

**الملفات**:
- `arrowz/arrowz/doctype/firmware_image/` — DocType
- `arrowz/arrowz/doctype/firmware_update_job/` — DocType
- `arrowz/device_providers/base_provider.py` — `upgrade_firmware(file_path)` method
- `arrowz/device_providers/mikrotik/mikrotik_provider.py` — RouterOS upgrade
- `arrowz/tasks/firmware.py` — Background job

---

## المرحلة 2: تحسينات VoIP + WiFi — الأسابيع 5-10

### 2.0 ☎️ FreePBX Feature Management (إدارة ميزات VoIP من Arrowz)
**الأولوية**: 🟡 متوسطة | **الصعوبة**: متوسطة | **المدة**: 5 أيام

**الوصف**: هذه الميزات موجودة فعلاً فى FreePBX لكن تُدار من واجهة FreePBX مباشرة.
نريد إدارتها من داخل Arrowz (قراءة + تعديل عبر AMI/API).

**الميزات المطلوبة**:
```
الميزة              الحالة الحالية                    المطلوب
─────────────────────────────────────────────────────────────────
Call Park           FreePBX فقط                      DocType + AMI park/unpark
Conference Bridge   FreePBX فقط                      DocType + AMI confbridge
Ring Groups         FreePBX فقط                      DocType + AMI queue
IVR Management      FreePBX فقط                      DocType + AMI IVR read/write
Voicemail           قراءة من PBX mount (تشخيص فقط)   DocType + إدارة كاملة
BLF Panel           sync_pbx_status (حالة فقط)       لوحة BLF تفاعلية فى navbar
Auto-Reply          غير موجود                        DocType + قوالب ردود تلقائية
```

**التنفيذ الفنى**:
```python
# DocTypes جديدة:
# - AZ Ring Group: name, strategy (ringall/hunt/memoryhunt), members (Table), timeout
# - AZ IVR Menu: name, greeting_file, options (Table: digit → destination)
# - AZ Conference Room: name, pin, max_members, recording
# - AZ Voicemail Box: extension, greeting, email_notification, messages (child table)
# - AZ Auto Reply Template: name, channel (WhatsApp/Telegram/SMS), trigger, response

# AMI Commands:
# Park:       Action: Park, Channel: <channel>, Timeout: 120
# Conference: Action: ConfbridgeList/ConfbridgeKick/ConfbridgeMute
# Ring Group: Map to Asterisk Queue → Action: QueueAdd/QueueRemove
# IVR:        Read/Write via FreePBX REST API or dialplan manipulation

# BLF Panel: Real-time extension status grid in navbar
# Uses existing sync_pbx_status + frappe.publish_realtime
```

**الملفات**:
- `arrowz/arrowz/doctype/az_ring_group/` — DocType
- `arrowz/arrowz/doctype/az_ivr_menu/` — DocType
- `arrowz/arrowz/doctype/az_conference_room/` — DocType (صوتى، غير OpenMeetings)
- `arrowz/arrowz/doctype/az_voicemail_box/` — DocType
- `arrowz/arrowz/doctype/az_auto_reply_template/` — DocType
- `arrowz/public/js/blf_panel.js` — لوحة BLF تفاعلية
- `arrowz/api/pbx_features.py` — API endpoints للميزات الجديدة

---

### 2.1 📡 WiFi Auto Channel & Power Optimization
**الأولوية**: 🟡 متوسطة | **الصعوبة**: عالية | **المدة**: 7 أيام

**الوصف**: تحسين تلقائى لقنوات WiFi وقوة الإشارة لتقليل التداخل

**التنفيذ الفنى**:
```python
# MikroTik WiFi v7 يدعم:
# /interface/wifi scan → مسح الترددات المحيطة
# /interface/wifi/channel → تغيير القناة
# /interface/wifi set tx-power → تغيير القوة

# Algorithm:
# 1. كل ساعة: scan all APs → جمع بيانات التداخل
# 2. تحليل: channel utilization + interference + noise floor
# 3. حساب: أفضل channel assignment عبر graph coloring algorithm
# 4. تطبيق: push new channels فى ساعات الهدوء (مثلاً 3 AM)

# DocType: WiFi Optimization Profile
# - enabled: bool
# - scan_interval: hours
# - apply_time: time (e.g., 03:00)
# - min_channel_change_interval: hours
# - power_mode: auto/manual/fixed
# - max_tx_power: dBm
# - min_tx_power: dBm
```

**الملفات**:
- `arrowz/arrowz/doctype/wifi_optimization_profile/` — DocType
- `arrowz/wifi/channel_optimizer.py` — خوارزمية التحسين
- `arrowz/wifi/spectrum_analyzer.py` — تحليل الطيف
- `arrowz/device_providers/base_provider.py` — `scan_wifi_spectrum()`, `set_wifi_channel()`
- `arrowz/device_providers/mikrotik/mikrotik_provider.py` — تنفيذ MikroTik

---

### 2.2 🗺️ WiFi Heatmap (Floor Plan)
**الأولوية**: 🟡 متوسطة | **الصعوبة**: متوسطة | **المدة**: 5 أيام

**الوصف**: رسم خريطة حرارية للتغطية على مخطط الطابق

**التنفيذ الفنى**:
```javascript
// Page: arrowz_wifi_heatmap
// 1. Upload floor plan image (PNG/SVG)
// 2. Place AP icons on the map (drag & drop)
// 3. Set AP parameters (model, power, channel, height)
// 4. Calculate coverage using signal propagation model:
//    - Free Space Path Loss (FSPL)
//    - Wall attenuation factors (user configurable)
//    - Frequency-dependent (2.4GHz vs 5GHz vs 6GHz)
// 5. Render heatmap overlay (green→yellow→red)
// 6. Live mode: show actual RSSI from connected clients

// Libraries:
// - Canvas/SVG for rendering
// - heatmap.js for visualization
// - Signal propagation: FSPL + ITU-R P.1238 indoor model
```

**الملفات**:
- `arrowz/arrowz/page/arrowz_wifi_heatmap/` — صفحة جديدة
- `arrowz/arrowz/doctype/floor_plan/` — DocType (صورة + مقياس)
- `arrowz/arrowz/doctype/ap_placement/` — DocType (موقع AP على الخريطة)
- `arrowz/wifi/signal_model.py` — نموذج انتشار الإشارة
- `arrowz/public/js/heatmap_renderer.js` — عرض الخريطة الحرارية

---

### 2.3 🔀 Seamless Roaming Support
**الأولوية**: 🟡 متوسطة | **الصعوبة**: عالية (يعتمد على الأجهزة) | **المدة**: 3 أيام

**الوصف**: تمكين 802.11r/k/v على أجهزة MikroTik المدعومة

**التنفيذ الفنى**:
```python
# MikroTik WiFi v7 (CAPsMAN) يدعم:
# ft=yes (802.11r Fast Transition)
# rrm=yes (802.11k Radio Resource Management)

# DocType: WiFi Network — إضافة حقول:
# - fast_transition_enabled (bool) → 802.11r
# - rrm_enabled (bool) → 802.11k
# - roaming_aggressiveness: low/medium/high

# Push config via MikroTik provider:
# /interface/wifi/security set ft=yes ft-over-ds=yes
# /interface/wifi set rrm=yes
```

---

## المرحلة 3: إدارة متقدمة (Advanced Management) — الأسابيع 9-12

### 3.1 🔌 L2 Switch Management (MikroTik CRS)
**الأولوية**: 🟡 متوسطة | **الصعوبة**: متوسطة | **المدة**: 5 أيام

**الوصف**: إدارة منافذ المحولات + VLANs + STP + Port Mirroring

**التنفيذ الفنى**:
```python
# DocTypes الجديدة:
# - Switch Port: إعدادات كل منفذ (VLAN, PoE, speed, status)
# - VLAN Definition: VLAN ID + name + description + ports
# - Port Mirror: source port → destination port
# - STP Config: mode (RSTP/MSTP) + priority + cost

# MikroTik CRS switches عبر RouterOS API:
# /interface/bridge/port → إدارة منافذ الجسر
# /interface/bridge/vlan → VLAN filtering
# /interface/ethernet/switch → hardware offload
# /interface/bridge/port/set mirror=yes
# /interface/bridge/settings/set protocol-mode=rstp

# Device Provider extension:
class BaseProvider:
    def get_switch_ports(self) → List[Dict]
    def set_switch_port(self, port, config) → bool
    def get_vlans(self) → List[Dict]
    def set_vlan(self, vlan_id, ports, tagged, untagged) → bool
    def get_stp_status(self) → Dict
    def set_stp_config(self, mode, priority) → bool
    def set_port_mirror(self, source, destination) → bool
```

**الملفات**:
- `arrowz/arrowz/doctype/switch_port/` — DocType
- `arrowz/arrowz/doctype/vlan_definition/` — DocType
- `arrowz/arrowz/doctype/port_mirror/` — DocType
- `arrowz/device_providers/base_provider.py` — abstract methods
- `arrowz/device_providers/mikrotik/switch_manager.py` — MikroTik CRS

---

### 3.2 🕵️ Deep Packet Inspection (DPI)
**الأولوية**: 🟡 متوسطة | **الصعوبة**: عالية | **المدة**: 7 أيام

**الوصف**: تحديد التطبيقات والبروتوكولات فى الترافيك (YouTube, Facebook, etc.)

**التنفيذ الفنى**:
```python
# MikroTik يدعم L7 protocol detection:
# /ip/firewall/layer7-protocol
# + connection tracking markers

# nDPI / Suricata على Linux boxes

# DocType: Application Profile
# - name: "YouTube", "Facebook", "WhatsApp"
# - l7_regex: regex pattern
# - category: Social, Video, Gaming, Business
# - default_action: allow/block/throttle

# DocType: Application Usage
# - client: Link to Network Client
# - application: Link to Application Profile
# - bytes_up, bytes_down
# - timestamp

# Dashboard: Top Applications chart (pie + timeline)
```

---

### 3.3 📋 Zero-Touch Provisioning (ZTP)
**الأولوية**: 🔴 عالية | **الصعوبة**: متوسطة | **المدة**: 5 أيام

**الوصف**: جهاز جديد يتصل بالشبكة → يحصل على إعداداته تلقائياً

**التنفيذ الفنى**:
```python
# DocType: Device Template
# - device_type: MikroTik / Linux Box
# - model_pattern: regex (e.g., "RB4011*", "hAP ac*")
# - config_template: Jinja2 template
# - auto_adopt: bool
# - site: Link to Site/Location

# Flow:
# 1. جهاز جديد → DHCP يعطيه IP
# 2. Arrowz Scanner (scheduled task) يكتشف الجهاز عبر:
#    - mDNS/LLDP/SNMP discovery
#    - ARP table scanning
#    - MikroTik Neighbor Discovery (/ip/neighbor)
# 3. يطابق model مع Device Template
# 4. ينشئ Arrowz Box DocType تلقائياً
# 5. يطبق config_template عبر Device Provider
# 6. يرسل notification للمدير

# DocType: Device Discovery Log
# - mac, ip, model, hostname, discovered_at
# - status: new/adopted/ignored
# - adopted_box: Link to Arrowz Box
```

**الملفات**:
- `arrowz/arrowz/doctype/device_template/` — DocType
- `arrowz/arrowz/doctype/device_discovery_log/` — DocType
- `arrowz/network/device_scanner.py` — اكتشاف الأجهزة
- `arrowz/network/auto_provisioner.py` — تطبيق الإعدادات
- `hooks.py` — scheduled task كل 5 دقائق

---

### 3.4 🏢 MSP Mode (Multi-Tenant)
**الأولوية**: 🟡 متوسطة | **الصعوبة**: متوسطة | **المدة**: 5 أيام

**الوصف**: إدارة شبكات عملاء متعددين من واجهة واحدة

**التنفيذ الفنى**:
```python
# DocType: MSP Customer
# - customer_name
# - contact_person
# - sites: Table of Site entries
# - users: Table of User assignments
# - billing_plan: Link to Billing Plan

# DocType: Site
# - site_name, location, address
# - customer: Link to MSP Customer
# - boxes: Table of Arrowz Box links
# - server_config: Link to AZ Server Config

# Frappe User Permissions:
# - MSP Admin: sees all customers
# - Customer Admin: sees only their sites
# - Site Technician: sees only assigned sites

# Dashboard: MSP Overview
# - All customers with status
# - Per-customer: site count, device count, alerts
# - Quick drill-down to any customer's network
```

---

## المرحلة 4: تحسينات أمنية (Security Enhancements) — الأسابيع 13-16

### 4.1 🛡️ DoS Detection & Auto-Defense
**الأولوية**: 🟡 متوسطة | **الصعوبة**: متوسطة | **المدة**: 4 أيام

```python
# MikroTik:
# /ip/firewall/filter → connection-limit, src-address-list
# /ip/firewall/raw → prerouting chain for early drop

# DocType: DoS Protection Profile
# - TCP SYN Flood threshold
# - UDP Flood threshold
# - ICMP Flood threshold
# - Port Scan detection
# - Auto-block duration
# - Whitelist IPs

# Background job: analyse connection tracking stats
# Alert on anomaly → auto-add to address-list=dos-blocked
```

### 4.2 🔐 LDAP/Active Directory Integration
**الأولوية**: 🟢 منخفضة | **الصعوبة**: منخفضة | **المدة**: 2 أيام

```python
# Frappe يدعم LDAP أصلاً!
# نحتاج فقط:
# 1. ربط LDAP users بـ Network Client / WiFi User Account
# 2. Captive Portal auth عبر LDAP
# 3. VPN auth عبر LDAP

# DocType: LDAP Network Config (extends Frappe LDAP Settings)
# - map_groups_to_vlans: LDAP Group → VLAN
# - map_groups_to_bandwidth: LDAP Group → Bandwidth Plan
```

### 4.3 📱 PPSK (Private Pre-Shared Key)
**الأولوية**: 🟢 منخفضة | **الصعوبة**: متوسطة | **المدة**: 3 أيام

```python
# كل مستخدم له كلمة مرور WiFi فريدة
# MikroTik: /interface/wifi/access-list + private-passphrase

# DocType: WiFi Private Key
# - user: Link to WiFi User Account
# - ssid: Link to WiFi Network
# - passphrase: Password field
# - vlan_override: optional
# - bandwidth_override: optional
# - mac_address: optional (for extra security)
# - expires_on: date
```

---

## المرحلة 5: تجربة المستخدم (UX Enhancements) — الأسابيع 17-22

### 5.0 💰 Revenue Reports & Payment Integration
**الوصف**: تقارير إيرادات + ربط بوابات دفع (مذكورة فى الوثائق كميزة لكنها غير مُنفَّذة)

```python
# Revenue Reports:
# - Frappe Script Report: revenue by plan, by period, by customer
# - Dashboard charts: MRR, churn, ARPU
# - Export to PDF/Excel

# Payment Gateway (عبر Frappe Payments app):
# - Online voucher purchase
# - Subscription payment (credit card, mobile money)
# - Auto-activate plan on payment confirmation
# - Integration: Stripe / PayPal / local gateways
```

### 5.1 🔍 Network Search & Quick Actions
**الوصف**: بحث موحد عبر كل الأجهزة والعملاء والإعدادات

```javascript
// Ctrl+K / Cmd+K → command palette
// "find 192.168.1.50" → يبحث فى كل DocTypes
// "block MAC aa:bb:cc" → يضيف للقائمة السوداء
// "restart box-1" → يعيد تشغيل الجهاز
// "voucher 1h 10mbps" → ينشئ voucher
```

### 5.2 📊 Enhanced Topology — Live Data Overlay
**الوصف**: عرض بيانات حية على خريطة Topology

```javascript
// 1. Bandwidth per link (animated thickness)
// 2. Client count per AP (badge)
// 3. CPU/Memory per device (color gradient)
// 4. Alert indicators (pulsing red)
// 5. Traffic flow animation (directional particles)
```

### 5.3 📧 Notification Center
**الوصف**: مركز إشعارات موحد (alerts + calls + messages)

```javascript
// Unified notification panel:
// - Network alerts (WAN down, device offline)
// - VoIP events (missed calls, voicemail)
// - Omni-channel (new messages)
// - Security events (blocked attacks)
// - System events (firmware available, quota exceeded)
```

---

## ملخص الجدول الزمنى

```
الأسبوع    المهمة                          الأولوية
──────────────────────────────────────────────────
 1-2      WAN Auto-Failover               🔴
 2-3      PWA Mobile App                  🔴
 3-4      Automated Reports + Firmware    🟡
 5-6      FreePBX Feature Management      🟡
 6-8      WiFi Channel/Power Optimization 🟡
 8-10     WiFi Heatmap + Roaming          🟡
 10-12    L2 Switch Management            🟡
 12-13    DPI (Deep Packet Inspection)    🟡
 13-14    Zero-Touch Provisioning         🔴
 14-15    MSP Mode                        🟡
 15-16    DoS Defense                     🟡
 16-17    LDAP + PPSK                     🟢
 17-18    Network Search + Quick Actions  🟡
 19-20    Enhanced Topology               🟡
 20-22    Notification Center             🟡
```

---

## تقدير الجهد الإجمالى

| المرحلة | الأسابيع | الميزات | الـ DocTypes الجديدة |
|---------|---------|---------|---------------------|
| 1: فجوات حرجة | 4 | 4 | 3 |
| 2: VoIP + WiFi | 6 | 4 | 8 |
| 3: إدارة متقدمة | 4 | 4 | 7 |
| 4: أمان متقدم | 4 | 3 | 3 |
| 5: تجربة المستخدم | 4 | 3 | 0 |
| **الإجمالى** | **22 أسبوع** | **18 ميزة** | **21 DocType** |
