# Arrowz Unique Advantages — مميزات Arrowz الفريدة
# ميزات لا يملكها Omada SDN ولا أى منافس تقليدى

> **تاريخ**: مارس 2026
> **الهدف**: توثيق كل ما يميز Arrowz عن Omada والمنافسين التقليديين

---

## الخلاصة التنفيذية

Arrowz ليس مجرد نظام إدارة شبكات — إنه **منصة اتصالات موحدة (Unified Communications Platform)** تجمع:
- 🌐 إدارة الشبكات (مثل Omada)
- 📞 اتصالات VoIP (مثل 3CX)
- 💬 قنوات تواصل (مثل Zendesk)
- 💰 فوترة ومحاسبة (مثل WHMCS)
- 📱 بوابات GSM (مثل Yeastar)

**لا يوجد منتج واحد فى السوق يجمع كل هذا.**

---

## 1. 📞 نظام VoIP متكامل (Arrowz Softphone)

### ما يملكه Arrowz:
| الميزة | التفاصيل | الحالة | Omada |
|--------|---------|--------|-------|
| **WebRTC Softphone** | هاتف مدمج فى المتصفح (JsSIP) — navbar dropdown + modal | ✅ مُنفَّذ | ❌ لا يوجد |
| **FreePBX/Asterisk AMI** | AMI integration (originate, redirect, status sync) | ✅ مُنفَّذ | ❌ |
| **SIP Extension Management** | ربط كل مستخدم بامتداد SIP + إعدادات شخصية (DocType: AZ Extension) | ✅ مُنفَّذ | ❌ |
| **Call Logging (CDR)** | تسجيل كل المكالمات + مدة + حالة (DocType: AZ Call Log) | ✅ مُنفَّذ | ❌ |
| **Click-to-Call** | اضغط على أى رقم فى النظام → اتصل مباشرة | ✅ مُنفَّذ | ❌ |
| **Call Transfer** | تحويل مكالمات (blind + attended) عبر API + DocType | ✅ مُنفَّذ | ❌ |
| **Call Park** | إيقاف مكالمة مؤقتاً (عبر FreePBX — لم يُنفَّذ فى Arrowz بعد) | 🔜 FreePBX فقط | ❌ |
| **Conference Bridge** | مؤتمرات صوتية (عبر FreePBX — لم يُنفَّذ فى Arrowz بعد) | 🔜 FreePBX فقط | ❌ |
| **BLF (Busy Lamp Field)** | حالة الامتدادات (sync_pbx_status يحدّث الحالة، لكن لا يوجد BLF panel) | 🔜 جزئى | ❌ |
| **Voicemail** | قراءة ملفات البريد الصوتى من PBX mount (للتشخيص فقط، لا إدارة) | 🔜 جزئى | ❌ |
| **Ring Groups** | مجموعات رنين (تُدار عبر FreePBX مباشرة — لم تُنفَّذ فى Arrowz) | 🔜 FreePBX فقط | ❌ |
| **IVR** | قوائم صوتية تفاعلية (تُدار عبر FreePBX مباشرة — لم تُنفَّذ فى Arrowz) | 🔜 FreePBX فقط | ❌ |

### القيمة المضافة:
> مدير الشبكة يستطيع الاتصال بالعملاء، تلقى المكالمات، وإدارة الشبكة — كله من واجهة واحدة.

---

## 2. 💬 قنوات تواصل متعددة (Omni-Channel)

### ما يملكه Arrowz:
| الميزة | التفاصيل | الحالة | Omada |
|--------|---------|--------|-------|
| **WhatsApp Cloud API** | إرسال واستقبال رسائل عبر WhatsApp Business (API + webhooks) | ✅ مُنفَّذ | ❌ |
| **Telegram Bot** | بوت تلقائى لاستقبال رسائل العملاء (polling + webhooks) | ✅ مُنفَّذ | ❌ |
| **SMS Integration** | إرسال رسائل SMS عبر بوابات GSM + DocType: AZ SMS Message | ✅ مُنفَّذ | ❌ |
| **Omni-Channel Panel** | لوحة موحدة لكل المحادثات (omni_panel.js) | ✅ مُنفَّذ | ❌ |
| **Conversation Sessions** | تتبع المحادثات (DocType: AZ Conversation Session) | ✅ مُنفَّذ | ❌ |
| **Auto-Reply Templates** | ردود تلقائية قابلة للتخصيص | 🔜 غير مُنفَّذ | ❌ |
| **Media Support** | إرسال واستقبال صور/مستندات/ملفات صوتية | ✅ مُنفَّذ | ❌ |
| **Notification Badge** | شارة إشعارات فى الـ navbar (omni_doctype_extension.js) | ✅ مُنفَّذ | ❌ |
| **Contact Linking** | ربط المحادثات بجهات الاتصال عبر API contacts | ✅ مُنفَّذ | ❌ |

### القيمة المضافة:
> العميل يرسل رسالة WhatsApp "الإنترنت بطيء" → الفنى يرى الرسالة + بيانات اتصال العميل + حالة الشبكة — كله فى مكان واحد.

---

## 3. 📱 بوابة GSM (Dinstar UC2000-VE-8G)

### ما يملكه Arrowz:
| الميزة | التفاصيل | Omada |
|--------|---------|-------|
| **8-Port GSM Management** | إدارة 8 منافذ GSM + حالة كل SIM | ❌ لا علاقة |
| **SIM Status Monitoring** | IMSI, IMEI, SMSC, signal strength لكل شريحة | ❌ |
| **Module Power Control** | تشغيل/إيقاف منافذ GSM عن بُعد | ❌ |
| **Outbound Call Routing** | توجيه المكالمات عبر GSM (توفير تكلفة) | ❌ |
| **SMS via GSM** | إرسال SMS عبر الشرائح المحلية (بدون تكلفة خارجية) | ❌ |
| **Round-Robin Routing** | توزيع المكالمات على المنافذ بالتساوى | ❌ |
| **Rich Topology View** | عرض Gateway + Ports مع حالة كل منفذ بصرياً | ❌ |
| **VPN Tunnel to Gateway** | OpenVPN TLS tunnel للاتصال الآمن | ❌ |

### القيمة المضافة:
> شركة تتصل بـ 100 عميل يومياً عبر الجوال ← بدلاً من استخدام هواتف جوالة، يتصلون من المتصفح عبر خطوط GSM → توفير كبير فى التكاليف.

---

## 4. 💰 نظام فوترة الشبكة (Network Billing)

### ما يملكه Arrowz:
| الميزة | التفاصيل | Omada |
|--------|---------|-------|
| الميزة | التفاصيل | الحالة | Omada |
|--------|---------|--------|-------|
| **WiFi Vouchers** | كوبونات إنترنت بمدة + سرعة + حجم (DocType: WiFi Voucher + Batch) | ✅ مُنفَّذ | ❌ |
| **Billing Plans** | خطط اشتراك (يومى/أسبوعى/شهرى) (DocType: Billing Plan + Tiers) | ✅ مُنفَّذ | ❌ |
| **Billing Cycles & Invoicing** | دورات فوترة + إنشاء فواتير تلقائى (generate_daily_billing) | ✅ مُنفَّذ | ❌ |
| **Bandwidth Management** | تخصيص سرعة لكل مستخدم/خطة (Bandwidth Assignment) | ✅ مُنفَّذ | ❌ |
| **Usage Quotas** | حدود استهلاك (GB) + تنبيه (DocType: Usage Quota + check_quota_usage) | ✅ مُنفَّذ | ❌ |
| **Captive Portal** | بوابة تسجيل دخول WiFi مخصصة | ✅ مُنفَّذ | ✅ (Omada أيضاً) |
| **Voucher Auto-Expiry** | انتهاء صلاحية الكوبونات تلقائياً (validity_hours → expires_on) | ✅ مُنفَّذ | ❌ |
| **Revenue Reports** | تقارير الإيرادات من الاشتراكات | 🔜 غير مُنفَّذ | ❌ |
| **Payment Gateway** | ربط مع بوابات الدفع (Frappe Payments app موجود لكن لا تكامل فى Arrowz) | 🔜 غير مُنفَّذ | ❌ |

### القيمة المضافة:
> فندق أو مقهى يبيع إنترنت WiFi بالساعة/اليوم — Arrowz يدير كل شيء من الإنشاء للفوترة للمراقبة.

---

## 5. 📊 IP Accounting & Traffic Analysis

### ما يملكه Arrowz:
| الميزة | التفاصيل | Omada |
|--------|---------|-------|
| الميزة | التفاصيل | الحالة | Omada |
|--------|---------|--------|-------|
| **IP Accounting** | تتبع استهلاك كل IP — upload + download (DocType: IP Accounting Snapshot) | ✅ مُنفَّذ | ❌ (DPI فقط) |
| **Traffic Classification** | تصنيف حركة البيانات (DocType: Traffic Classification + Top Application) | ✅ مُنفَّذ | ❌ |
| **Usage History** | سجل تاريخى للاستهلاك (snapshots مجدولة عبر collect_ip_accounting) | ✅ مُنفَّذ | ❌ |
| **Bandwidth Alerts** | تنبيه عند تجاوز حد معين (Usage Alert DocType) | ✅ مُنفَّذ | ⚠️ محدود |
| **Top Consumers** | قائمة أكثر المستهلكين (Top Application DocType) | ✅ مُنفَّذ | ⚠️ محدود |
| **Cost Allocation** | تقسيم التكلفة على الأقسام/العملاء | 🔜 غير مُنفَّذ | ❌ |

---

## 6. 🏢 تكامل ERP (Frappe/ERPNext)

### ما يملكه Arrowz:
| الميزة | التفاصيل | Omada |
|--------|---------|-------|
| **ERPNext Integration** | ربط مباشر مع نظام ERP كامل | ❌ مستقل تماماً |
| **Customer Management** | عملاء الشبكة = عملاء ERP (فواتير، مبيعات) | ❌ |
| **Employee Integration** | موظفى الشركة مع صلاحيات الشبكة | ❌ |
| **Asset Management** | أجهزة الشبكة = أصول فى ERP (اهلاك، صيانة) | ❌ |
| **HR Integration** | موظف جديد → حساب WiFi + امتداد SIP تلقائياً | ❌ |
| **Purchase Integration** | طلب شراء أجهزة شبكة من داخل النظام | ❌ |
| **Expense Tracking** | تتبع تكاليف الاتصالات + الإنترنت | ❌ |
| **User Permissions** | صلاحيات Frappe المتقدمة (Role-based + DocType-level) | ⚠️ محدود |

### القيمة المضافة:
> شركة تملك ERPNext ← تضيف Arrowz ← يصبح لديها نظام واحد لكل شيء: HR + محاسبة + مبيعات + شبكات + VoIP + تواصل.

---

## 7. 🎥 مؤتمرات الفيديو (OpenMeetings)

### ما يملكه Arrowz:
| الميزة | التفاصيل | Omada |
|--------|---------|-------|
| **Video Conferencing** | مؤتمرات فيديو عبر OpenMeetings | ❌ |
| **Room Management** | إنشاء وإدارة غرف الاجتماعات | ❌ |
| **Recording** | تسجيل الاجتماعات | ❌ |
| **Screen Sharing** | مشاركة الشاشة | ❌ |
| **Calendar Integration** | ربط مع تقويم Frappe | ❌ |
| **Invitation System** | دعوة المشاركين بالإيميل | ❌ |

---

## 8. 🔔 نظام تنبيهات متقدم (Network Alerts)

### ما يملكه Arrowz:
| الميزة | التفاصيل | الحالة | Omada |
|--------|---------|--------|-------|
| **Multi-Channel Alerts** | Email عبر evaluate_alert_rules + إرسال بيانات حية عبر Socket.IO | ✅ Email + Realtime | ✅ Email فقط |
| **Custom Alert Rules** | قواعد مخصصة (DocType: Alert Rule) + تقييم دورى | ✅ مُنفَّذ | ⚠️ محدود |
| **Alert History** | سجل كامل (DocType: Network Alert + Network Event) | ✅ مُنفَّذ | ✅ |
| **WAN Health Monitoring** | فحص دورى لحالة WAN (DocType: WAN Health Check) | ✅ مُنفَّذ | ⚠️ محدود |
| **Alert Escalation** | تصعيد التنبيه إذا لم يُعالج | 🔜 غير مُنفَّذ | ❌ |
| **Alert Correlation** | ربط التنبيهات المتعلقة | 🔜 غير مُنفَّذ | ❌ |

---

## 9. 🏗️ Device Provider Architecture

### ما يملكه Arrowz:
| الميزة | التفاصيل | Omada |
|--------|---------|-------|
| **Abstract Provider Layer** | ABC مع 50+ abstract methods | ❌ مغلق |
| **Factory Pattern** | إضافة أجهزة جديدة بسهولة | ❌ TP-Link فقط |
| **Multi-Vendor Support** | MikroTik + Linux Box + قابل للتوسيع | ❌ TP-Link فقط |
| **Bidirectional Sync** | مزامنة ثنائية بين الجهاز و Arrowz | ⚠️ (اتجاه واحد) |
| **Error Tracking** | تتبع الأخطاء متعدد الطبقات | ❌ |
| **Sync Engine** | محرك مزامنة مستقل | ❌ |
| **Provider Extensibility** | أى مطور يستطيع إضافة provider جديد | ❌ مغلق |

### القيمة المضافة:
> Omada يدعم **TP-Link فقط**. Arrowz يدعم **MikroTik** (الأكثر استخداماً عالمياً) + **Linux** + **أى جهاز آخر** عبر إضافة provider.

---

## 10. 🗺️ Topology التفاعلى

### ما يملكه Arrowz:
| الميزة | التفاصيل | Omada |
|--------|---------|-------|
| **Interactive Topology** | خريطة شبكة تفاعلية بالسحب والإفلات | ✅ (Omada أيضاً) |
| **Custom Node Types** | أنواع عقد مخصصة (Router, AP, Gateway, Dinstar...) | ⚠️ (محدود) |
| **Rich HTML Nodes** | عقد HTML غنية مع مؤشرات حالة | ❌ (أيقونات فقط) |
| **Port-Level Details** | تفاصيل كل منفذ فى العقدة مباشرة | ❌ |
| **Real-time Updates** | تحديث حى عبر Socket.IO | ⚠️ |
| **Integration with All Modules** | يعرض أجهزة من كل الوحدات | ⚠️ (شبكات فقط) |

---

## 11. 📋 Marketing Campaigns

### ما يملكه Arrowz:
| الميزة | التفاصيل | Omada |
|--------|---------|-------|
| الميزة | التفاصيل | الحالة | Omada |
|--------|---------|--------|-------|
| **Captive Portal Ads** | عرض إعلانات فى بوابة الدخول (redirect_url + ad_image + HTML) | ✅ مُنفَّذ | ❌ |
| **Campaign Targeting** | استهداف حسب Hotspot Profile | ✅ مُنفَّذ | ❌ |
| **Impression Tracking** | عدد مرات عرض الإعلان (impression_count) | ✅ مُنفَّذ | ❌ |
| **Click Tracking** | عدد النقرات على الإعلان (click_count) | ✅ مُنفَّذ | ❌ |
| **Campaign Scheduling** | تحديد تواريخ بداية ونهاية الحملة | ✅ مُنفَّذ | ❌ |
| **SMS Bulk Campaigns** | إرسال SMS جماعية عبر GSM | 🔜 غير مُنفَّذ | ❌ |
| **WhatsApp Campaigns** | رسائل WhatsApp جماعية | 🔜 غير مُنفَّذ | ❌ |

---

## 12. 🔓 Open Source + Self-Hosted

### ما يملكه Arrowz:
| الميزة | التفاصيل | Omada |
|--------|---------|-------|
| **Open Source** | كود مفتوح قابل للتعديل | ❌ مغلق |
| **Self-Hosted** | يعمل على سيرفرك (لا سحابة إجبارية) | ✅ (Hardware/Software) |
| **No License Fees** | بدون رسوم ترخيص | ⚠️ (Software مجانى، Hardware مدفوع) |
| **Custom Development** | أى مطور يستطيع التعديل والإضافة | ❌ |
| **Frappe Ecosystem** | آلاف التطبيقات الجاهزة فى بيئة Frappe | ❌ |
| **API-First** | كل شيء متاح عبر REST API | ⚠️ (محدود) |
| **Python/JS Stack** | تقنيات معروفة وسهلة التعلم | ❌ (C/embedded) |

---

## ملخص: الميزات الفريدة فى Arrowz

> **ملاحظة**: ✅ = مُنفَّذ فعلاً فى الكود | 🔜 = مخطط/جزئى

```
الفئة                          مُنفَّذ ✅    مخطط 🔜
──────────────────────────────────────────────────
📞 VoIP & Softphone              6          6 (FreePBX features)
💬 Omni-Channel                   8          1 (auto-reply)
📱 GSM Gateway                    8          0
💰 Network Billing                7          2 (revenue reports, payment)
📊 IP Accounting                  5          1 (cost allocation)
🏢 ERP Integration                8          0
🎥 Video Conferencing             6          0
🔔 Advanced Alerts                4          2 (escalation, correlation)
🏗️ Device Provider Architecture   7          0
📋 Marketing Campaigns            5          2 (SMS bulk, WhatsApp bulk)
🔓 Open Source                    7          0
──────────────────────────────────────────────────
الإجمالى                          71 ✅       14 🔜
الإجمالى                            ~85 ميزة (مع تفاصيل أدق)
```

---

## التموضع التنافسى (Competitive Positioning)

### Arrowz = Omada SDN + 3CX + Zendesk + WHMCS + GSM Gateway

```
┌─────────────────────────────────────────────┐
│              Arrowz Platform                 │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐      │
│  │ Network │ │  VoIP   │ │  Omni-   │      │
│  │ Mgmt    │ │ Phone   │ │  Channel │      │
│  │(≈Omada) │ │(≈3CX)  │ │(≈Zendesk)│      │
│  └─────────┘ └─────────┘ └──────────┘      │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐      │
│  │Billing  │ │  GSM    │ │  Video   │      │
│  │& Quotas │ │ Gateway │ │  Conf    │      │
│  │(≈WHMCS) │ │(≈Yeastar)│ │(≈Zoom)  │      │
│  └─────────┘ └─────────┘ └──────────┘      │
│  ┌───────────────────────────────────┐      │
│  │    ERPNext/Frappe Integration     │      │
│  │  (HR + Accounting + CRM + More)  │      │
│  └───────────────────────────────────┘      │
└─────────────────────────────────────────────┘
```

### الشعار المقترح:
> **Arrowz — One Platform. Every Connection.**
> إدارة الشبكة • الاتصالات • التواصل • الفوترة — كله فى مكان واحد.

---

## الشريحة المستهدفة

| الشريحة | لماذا Arrowz أفضل من Omada |
|---------|--------------------------|
| **الفنادق** | WiFi + VoIP + Billing + WhatsApp للضيوف — حل واحد |
| **مقاهى الإنترنت** | Vouchers + Billing + Bandwidth control |
| **ISPs الصغيرة** | Billing + IP Accounting + MikroTik support |
| **الشركات** | VoIP + Network + ERP integration |
| **مراكز الاتصال** | Softphone + GSM + Omni-channel + CDR |
| **MSPs** | Multi-tenant + Multi-vendor + Open API |
| **Co-working Spaces** | WiFi Billing + VoIP + Meeting Rooms |

---

## خلاصة

**Omada جيد فى**: إدارة شبكات WiFi البسيطة مع أجهزة TP-Link.

**Arrowz أفضل فى**: كل شيء آخر — خاصة عندما تحتاج:
1. 🌐 إدارة أجهزة من شركات مختلفة (ليس TP-Link فقط)
2. 📞 اتصالات VoIP مدمجة
3. 💬 تواصل مع العملاء (WhatsApp, Telegram)
4. 💰 فوترة ومحاسبة
5. 📱 بوابات GSM
6. 🏢 تكامل مع ERP
7. 🔓 حرية التعديل والتطوير (Open Source)

**النتيجة**: Arrowz ليس بديلاً لـ Omada — إنه **أكبر بكثير**. 🚀
