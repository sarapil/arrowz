# Omada SDN vs Arrowz — تحليل تنافسى شامل
# Competitive Feature-by-Feature Analysis

> **تاريخ التحليل**: مارس 2026
> **الهدف**: مقارنة كل ميزة بين Omada SDN و Arrowz لتحديد الفجوات والمميزات الفريدة

---

## الملخص التنفيذى

| المعيار | Omada SDN | Arrowz |
|---------|-----------|--------|
| **النوع** | منصة أجهزة + برامج مغلقة (TP-Link فقط) | منصة برمجية مفتوحة (متعددة الأجهزة) |
| **الأجهزة المدعومة** | TP-Link فقط (APs, Switches, Gateways) | MikroTik + Linux Boxes + أى جهاز قابل للتوسعة |
| **الإدارة** | Cloud / Hardware Controller / Software Controller | Frappe Web UI (self-hosted) |
| **التكلفة** | أجهزة TP-Link + اشتراك Cloud اختيارى | برنامج مفتوح المصدر + أى أجهزة |
| **VoIP** | ❌ لا يوجد | ✅ نظام كامل (WebRTC + PBX + GSM) |
| **Omni-Channel** | ❌ لا يوجد | ✅ WhatsApp + Telegram + SMS |
| **ERP Integration** | ❌ لا يوجد | ✅ تكامل كامل مع ERPNext |

---

## 1. 📡 إدارة الشبكة (Network Management)

### 1.1 إدارة الواجهات (Interface Management)

| الميزة | Omada | Arrowz | الحالة |
|--------|-------|--------|--------|
| عرض الواجهات (Interfaces List) | ✅ | ✅ | متساوى |
| إدارة WAN متعدد (Multi-WAN) | ✅ حتى 4 منافذ WAN | ✅ عدد غير محدود | ✅ Arrowz أفضل |
| WAN Load Balancing | ✅ | ✅ Load Balancer Profile | متساوى |
| WAN Failover | ✅ تلقائى | ⚠️ يحتاج تطوير | 🔴 فجوة |
| إعدادات LAN | ✅ | ✅ | متساوى |
| VLAN Support | ✅ متقدم (802.1Q) | ⚠️ أساسى عبر MikroTik | 🟡 فجوة جزئية |
| DHCP Server | ✅ Multi-Net DHCP | ✅ | متساوى |
| DHCP Reservation (IP Reservation) | ✅ | ✅ IP Reservation DocType | متساوى |
| DNS إدارة | ✅ أساسى | ✅ DNS Entry DocType | متساوى |
| Static Routes | ✅ | ✅ Static Route DocType | متساوى |
| LLDP / LLDP-MED | ✅ (اكتشاف IP Phones) | ❌ | 🔴 فجوة |
| PoE Management | ✅ (أجهزة TP-Link PoE) | ❌ | 🔴 فجوة (خاص بالأجهزة) |
| Link Aggregation (LAG) | ✅ | ❌ | 🔴 فجوة |

### 1.2 إدارة المحولات (Switch Management)

| الميزة | Omada | Arrowz | الحالة |
|--------|-------|--------|--------|
| L2/L3 Switch Management | ✅ كامل | ❌ لا يوجد | 🔴 فجوة كبيرة |
| Port Mirroring | ✅ | ❌ | 🔴 فجوة |
| STP/RSTP/MSTP | ✅ | ❌ | 🔴 فجوة |
| IGMP Snooping | ✅ | ❌ | 🔴 فجوة |
| 802.1X Port Auth | ✅ | ❌ | 🔴 فجوة |
| VRRP / ERPS | ✅ (L3 Switches) | ❌ | 🔴 فجوة |
| Stacking | ✅ (L3 Switches) | ❌ | 🔴 فجوة |

> **ملاحظة**: Omada يتفوق فى إدارة المحولات لأنه مصمم خصيصاً لأجهزة TP-Link.
> Arrowz يمكنه إضافة دعم MikroTik Switch عبر Device Provider الحالى.

---

## 2. 📶 إدارة WiFi (WiFi Management)

| الميزة | Omada | Arrowz | الحالة |
|--------|-------|--------|--------|
| إدارة نقاط الوصول (AP Management) | ✅ كامل | ✅ WiFi Access Point DocType | متساوى |
| SSID Management | ✅ متعدد | ✅ WiFi Network DocType | متساوى |
| WPA3 | ✅ | ⚠️ يعتمد على الجهاز | 🟡 |
| Band Steering | ✅ | ❌ | 🔴 فجوة |
| Auto Channel Selection | ✅ AI-driven | ❌ | 🔴 فجوة |
| Auto Power Adjustment | ✅ AI-driven | ❌ | 🔴 فجوة |
| Seamless Roaming (802.11r/k/v) | ✅ | ❌ | 🔴 فجوة |
| Mesh WiFi | ✅ | ❌ | 🔴 فجوة |
| WiFi Heatmap Simulator | ✅ | ❌ | 🔴 فجوة |
| WiFi Analytics | ✅ أساسى | ✅ WiFi Analytics DocType | متساوى |
| Rate Limiting per SSID | ✅ | ✅ عبر Bandwidth Plan | متساوى |
| MAC Filtering | ✅ | ✅ MAC Blacklist/Whitelist | متساوى |
| WiFi Scheduling | ✅ | ⚠️ عبر Bandwidth Schedule | 🟡 |
| Minimum RSSI (Weak Client Disconnect) | ✅ | ❌ | 🔴 فجوة |

---

## 3. 🔒 الأمان والجدار النارى (Security & Firewall)

| الميزة | Omada | Arrowz | الحالة |
|--------|-------|--------|--------|
| Firewall Rules | ✅ | ✅ Firewall Rule DocType | متساوى |
| Firewall Zones | ✅ ضمنى | ✅ Firewall Zone DocType | ✅ Arrowz أوضح |
| NAT Rules | ✅ | ✅ NAT Rule DocType | متساوى |
| Port Forwarding | ✅ | ✅ Port Forward DocType | متساوى |
| DoS Defense | ✅ تلقائى | ⚠️ عبر Firewall Rules يدوى | 🟡 فجوة جزئية |
| IP/MAC/URL Filtering | ✅ | ✅ عبر Firewall + MAC lists | متساوى |
| ACL (Access Control List) | ✅ متقدم | ✅ عبر Firewall Rules | متساوى |
| IP-MAC Binding | ✅ | ✅ IP Reservation | متساوى |
| Deep Packet Inspection (DPI) | ✅ Application identification | ❌ | 🔴 فجوة مهمة |
| Content Filtering | ✅ URL categories | ⚠️ URL filtering أساسى | 🟡 فجوة جزئية |
| Intrusion Detection (IDS/IPS) | ⚠️ محدود | ❌ | 🔴 فجوة |
| Firewall Logging | ✅ | ✅ Firewall Log DocType | متساوى |
| GeoIP Blocking | ❌ | ❌ | لا يوجد فى كلاهما |

---

## 4. 🔐 VPN

| الميزة | Omada | Arrowz | الحالة |
|--------|-------|--------|--------|
| IPSec VPN | ✅ حتى 100 tunnel | ⚠️ عبر MikroTik | 🟡 |
| OpenVPN | ✅ حتى 50 | ⚠️ عبر MikroTik/Linux | 🟡 |
| WireGuard | ✅ (أحدث firmware) | ✅ VPN Server DocType | متساوى |
| L2TP VPN | ✅ حتى 50 | ✅ | متساوى |
| PPTP VPN | ✅ حتى 50 | ✅ | متساوى |
| PPPoE Server | ❌ | ✅ | ✅ Arrowz أفضل |
| SSTP VPN | ❌ | ✅ | ✅ Arrowz أفضل |
| Site-to-Site VPN | ✅ One-click Auto IPSec | ✅ Site to Site Tunnel DocType | متساوى |
| VPN Access Policies | ⚠️ أساسى | ✅ VPN Access Policy DocType | ✅ Arrowz أفضل |
| VPN Client Management | ✅ | ✅ VPN Peer DocType | متساوى |
| SSL VPN | ✅ | ❌ | 🔴 فجوة |
| Remote Access (Client-to-Site) | ✅ | ✅ | متساوى |

---

## 5. 📊 التحكم فى النطاق الترددى (Bandwidth & QoS)

| الميزة | Omada | Arrowz | الحالة |
|--------|-------|--------|--------|
| QoS Policies | ✅ | ✅ QoS Policy + QoS Class | متساوى |
| Bandwidth Limiting (per client) | ✅ | ✅ Bandwidth Assignment | متساوى |
| Bandwidth Plans | ⚠️ أساسى (rate limit) | ✅ متقدم (Plans + Tiers) | ✅ Arrowz أفضل |
| Traffic Shaping | ✅ | ✅ Traffic Rule DocType | متساوى |
| Bandwidth Scheduling | ⚠️ محدود | ✅ Bandwidth Schedule + Slots | ✅ Arrowz أفضل |
| IP Accounting | ❌ | ✅ كامل (Snapshots + Classification) | ✅ Arrowz فريد |
| Usage Quotas | ❌ | ✅ Usage Quota + Assignment | ✅ Arrowz فريد |
| Application-based QoS | ✅ (DPI) | ❌ | 🔴 فجوة |
| Voice VLAN / QoS | ✅ تلقائى لـ IP Phones | ❌ | 🔴 فجوة |
| Usage Alerts | ❌ | ✅ Usage Alert DocType | ✅ Arrowz فريد |

---

## 6. 🌐 Captive Portal & Hotspot

| الميزة | Omada | Arrowz | الحالة |
|--------|-------|--------|--------|
| Captive Portal | ✅ | ✅ Captive Portal DocType | متساوى |
| Splash Page Designer | ✅ أساسى | ✅ WiFi Splash Page DocType | متساوى |
| Voucher System | ✅ | ✅ WiFi Voucher + Batch | متساوى |
| Hotspot Profiles | ✅ | ✅ WiFi Hotspot Profile | متساوى |
| Social Login (Facebook/Google) | ✅ | ✅ Social Login Provider | متساوى |
| RADIUS Authentication | ✅ | ⚠️ عبر MikroTik | 🟡 فجوة جزئية |
| LDAP Authentication | ✅ | ❌ | 🔴 فجوة |
| SMS Authentication | ✅ (Twilio) | ✅ عبر AZ SMS Provider | متساوى |
| Walled Garden | ✅ | ✅ Walled Garden Entry | متساوى |
| User Accounts | ✅ | ✅ WiFi User Account | متساوى |
| Session Management | ✅ | ✅ WiFi User Session | متساوى |
| Marketing Campaigns | ❌ | ✅ WiFi Marketing Campaign | ✅ Arrowz فريد |
| PPSK (Private Pre-Shared Key) | ✅ | ❌ | 🔴 فجوة |

---

## 7. 📈 المراقبة والتقارير (Monitoring & Reporting)

| الميزة | Omada | Arrowz | الحالة |
|--------|-------|--------|--------|
| Dashboard Overview | ✅ | ✅ متعدد (Topology + Dashboards) | ✅ Arrowz أفضل |
| Network Topology Map | ✅ أساسى | ✅ متقدم (Interactive Cytoscape.js) | ✅ Arrowz أفضل بكثير |
| Real-time Monitoring | ✅ | ✅ Socket.IO real-time | متساوى |
| Device Health Monitoring | ✅ | ✅ Arrowz Box Health Log | متساوى |
| WAN Health Checks | ✅ | ✅ WAN Health Check DocType | متساوى |
| Alert Rules | ✅ أساسى (notifications) | ✅ متقدم (Alert Rule + Network Alert) | ✅ Arrowz أفضل |
| Network Event Logging | ✅ | ✅ Network Event DocType | متساوى |
| Client Statistics | ✅ | ✅ Client Session | متساوى |
| Traffic Reports | ✅ | ✅ IP Accounting | متساوى |
| Network Report (PDF) | ✅ Automated periodic | ❌ | 🔴 فجوة |
| Email Notifications | ✅ | ✅ عبر Frappe Notifications | متساوى |
| AI-Driven Analysis | ✅ (قيد التطوير) | ✅ OpenAI (sentiment + coaching) | ✅ Arrowz أفضل |
| Syslog Integration | ✅ | ⚠️ محدود | 🟡 |

---

## 8. 🏗️ البنية التحتية والنشر (Infrastructure & Deployment)

| الميزة | Omada | Arrowz | الحالة |
|--------|-------|--------|--------|
| Cloud Management | ✅ 100% cloud | ⚠️ self-hosted (يمكن cloud) | 🟡 |
| Hardware Controller | ✅ OC200/OC300/OC400 | ❌ (web-based فقط) | خاص بـ Omada |
| Software Controller | ✅ (Linux/Docker) | ✅ (Frappe/Docker) | متساوى |
| Mobile App | ✅ iOS + Android | ❌ | 🔴 فجوة كبيرة |
| Zero-Touch Provisioning (ZTP) | ✅ | ❌ | 🔴 فجوة كبيرة |
| Multi-Site Management | ✅ | ✅ عبر Server Config | متساوى |
| MSP Mode | ✅ | ❌ | 🔴 فجوة |
| Multi-User Roles | ✅ | ✅ متقدم (10+ أدوار) | ✅ Arrowz أفضل |
| REST API | ⚠️ غير رسمى/محدود | ✅ 100+ endpoint موثق | ✅ Arrowz أفضل بكثير |
| Two-Factor Authentication | ✅ | ✅ عبر Frappe | متساوى |
| Firmware Update | ✅ مركزى | ❌ | 🔴 فجوة |
| Config Backup/Restore | ✅ | ✅ (get/push full config) | متساوى |
| Batch Device Management | ✅ | ⚠️ per-device | 🟡 |

---

## 9. ☎️ VoIP & اتصالات (Arrowz فقط — لا يوجد فى Omada)

> **ملاحظة**: بعض الميزات تُدار عبر FreePBX مباشرة وليس من داخل واجهة Arrowz (معلّمة بـ 🔜)

| الميزة | Omada | Arrowz | الحالة |
|--------|-------|--------|--------|
| WebRTC Softphone | ❌ | ✅ كامل (JsSIP + navbar) | ✅ مُنفَّذ |
| SIP Extensions | ❌ | ✅ AZ Extension DocType | ✅ مُنفَّذ |
| Call Logging (CDR) | ❌ | ✅ AZ Call Log + تحليلات | ✅ مُنفَّذ |
| Call Transfer | ❌ | ✅ (blind + attended) | ✅ مُنفَّذ |
| Call Recording | ❌ | ✅ | ✅ مُنفَّذ |
| Inbound/Outbound Routing | ❌ | ✅ DocTypes كاملة | ✅ مُنفَّذ |
| SIP Trunks | ❌ | ✅ AZ Trunk DocType | ✅ مُنفَّذ |
| Call Center Wallboard | ❌ | ✅ Real-time wallboard | ✅ مُنفَّذ |
| Agent Dashboard | ❌ | ✅ Personal agent view | ✅ مُنفَّذ |
| AI Sentiment Analysis | ❌ | ✅ OpenAI real-time | ✅ مُنفَّذ |
| AI Call Transcription | ❌ | ✅ Whisper API | ✅ مُنفَّذ |
| AI Agent Coaching | ❌ | ✅ Real-time suggestions | ✅ مُنفَّذ |
| Screen Pop (CRM) | ❌ | ✅ Multi-DocType lookup | ✅ مُنفَّذ |
| Click-to-Call | ❌ | ✅ 15 DocTypes | ✅ مُنفَّذ |
| GSM Gateway (Dinstar) | ❌ | ✅ 8-port management | ✅ مُنفَّذ |
| Audio Visualizer | ❌ | ✅ Real-time waveform | ✅ مُنفَّذ |
| IVR / Auto-Attendant | ❌ | ⚠️ عبر FreePBX فقط (لا إدارة من Arrowz) | 🔜 FreePBX |
| Ring Groups | ❌ | ⚠️ عبر FreePBX فقط | 🔜 FreePBX |
| Call Park | ❌ | ⚠️ عبر FreePBX فقط | 🔜 FreePBX |
| Conference Bridge | ❌ | ⚠️ عبر FreePBX فقط | 🔜 FreePBX |
| BLF Panel | ❌ | ⚠️ جزئى (sync_pbx_status فقط، لا لوحة BLF) | 🔜 جزئى |
| Voicemail Management | ❌ | ⚠️ قراءة فقط من PBX mount (تشخيص، لا إدارة) | 🔜 جزئى |

---

## 10. 💬 Omni-Channel (Arrowz فقط)

| الميزة | Omada | Arrowz |
|--------|-------|--------|
| WhatsApp Cloud API | ❌ | ✅ Send/Receive/Templates |
| WhatsApp On-Premise | ❌ | ✅ Self-hosted |
| Telegram Bot | ❌ | ✅ Full bot integration |
| SMS Gateway | ❌ | ✅ Multi-provider |
| Unified Chat Panel | ❌ | ✅ omni_panel.js |
| Conversation Sessions | ❌ | ✅ Threaded sessions |
| Agent Assignment | ❌ | ✅ Auto/manual |
| 24h Window Management | ❌ | ✅ Auto-expiry |

---

## 11. 🎥 Video Conferencing (Arrowz فقط)

| الميزة | Omada | Arrowz |
|--------|-------|--------|
| Meeting Rooms | ❌ | ✅ OpenMeetings |
| Recording | ❌ | ✅ |
| Participant Management | ❌ | ✅ |

---

## 12. 💰 الفوترة والمحاسبة (Billing — Arrowz فقط)

| الميزة | Omada | Arrowz |
|--------|-------|--------|
| Billing Plans | ❌ | ✅ Billing Plan DocType |
| Usage-based Billing | ❌ | ✅ Billing Cycle + Invoice |
| ERPNext Integration | ❌ | ✅ Full CRM/ERP |

---

## 13. 📊 ملخص الإحصائيات

### إجمالى المقارنة

| المقياس | العدد |
|---------|-------|
| إجمالى الميزات المقارنة | ~140 |
| Omada يتفوق | ~22 |
| Arrowz يتفوق | ~25 |
| متساوى | ~40 |
| Arrowz فريد ✅ (مُنفَّذ فعلاً) | ~38 |
| Arrowz فريد 🔜 (عبر FreePBX / مخطط) | ~14 |
| لا يوجد فى كلاهما | ~2 |

### فجوات حرجة فى Arrowz يجب معالجتها

| # | الفجوة | الأولوية | الصعوبة |
|---|--------|---------|---------|
| 1 | Mobile App (iOS/Android) | 🔴 عالية | عالية |
| 2 | Zero-Touch Provisioning (ZTP) | 🔴 عالية | متوسطة |
| 3 | WiFi Auto Channel / Power Adjustment | 🟡 متوسطة | عالية |
| 4 | Seamless Roaming (802.11r/k/v) | 🟡 متوسطة | عالية (يعتمد على الأجهزة) |
| 5 | Deep Packet Inspection (DPI) | 🟡 متوسطة | عالية |
| 6 | L2/L3 Switch Management | 🟡 متوسطة | متوسطة |
| 7 | WAN Failover (Auto) | 🟡 متوسطة | منخفضة |
| 8 | WiFi Heatmap | 🟡 متوسطة | متوسطة |
| 9 | Automated Network Reports (PDF) | 🟡 متوسطة | منخفضة |
| 10 | LDAP Authentication | 🟢 منخفضة | منخفضة |
| 11 | MSP Mode (Multi-tenant) | 🟡 متوسطة | متوسطة |
| 12 | Mesh WiFi | 🟡 متوسطة | عالية (يعتمد على الأجهزة) |
| 13 | Band Steering | 🟢 منخفضة | عالية (يعتمد على الأجهزة) |
| 14 | PPSK | 🟢 منخفضة | متوسطة |
| 15 | Firmware Management (centralized) | 🟡 متوسطة | متوسطة |

---

## الخلاصة

**Omada** هو حل **أجهزة + برامج مغلق** متفوق فى:
- إدارة أجهزة TP-Link (WiFi AP, Switches, Gateways) مع ZTP
- ميزات WiFi المتقدمة (roaming, band steering, heatmap)
- تطبيق جوال جاهز
- L2/L3 switch management

**Arrowz** هو حل **برمجى مفتوح** متفوق فى:
- **38 ميزة فريدة مُنفَّذة** + 14 مخططة لا توجد فى Omada (VoIP, Omni-Channel, AI, GSM, Billing, ERP)
- دعم أجهزة متعددة (MikroTik + Linux + قابل للتوسعة)
- API مفتوح ومتكامل (100+ endpoint)
- نظام أدوار وصلاحيات متقدم
- Topology تفاعلى متقدم
- تكامل ERP/CRM كامل
- لا يحتاج شراء أجهزة من مصنع واحد
