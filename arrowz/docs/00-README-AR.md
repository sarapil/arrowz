# ملخص مشروع Arrowz
## نظام إدارة المكالمات المؤسسي مع الذكاء الاصطناعي

---

## 📋 نظرة عامة

**Arrowz** هو تطبيق متكامل لإدارة المكالمات الهاتفية مبني على منصة Frappe Framework، 
مصمم للعمل مع ERPNext ويدعم تقنيات WebRTC للاتصال عبر المتصفح.

### الهدف الرئيسي
توفير حل call center متكامل يجمع بين:
- الاتصال الهاتفي عبر الويب (WebRTC)
- تكامل مع أنظمة PBX (FreePBX/Asterisk)
- ذكاء اصطناعي لتحليل المكالمات
- ربط تلقائي مع CRM

---

## 📁 هيكل الملفات

```
apps/arrowz/
├── pyproject.toml          # إعدادات المشروع
├── README.md               # وثائق المشروع
├── LICENSE                 # رخصة MIT
└── arrowz/
    ├── __init__.py         # تعريف الموديول
    ├── hooks.py            # إعدادات التطبيق
    ├── modules.txt         # قائمة الموديولات
    ├── api/                # واجهات برمجة التطبيقات
    ├── public/             # ملفات الواجهة
    │   ├── js/             # JavaScript
    │   └── css/            # Stylesheets
    └── docs/               # التوثيق الكامل
        ├── 00-README-AR.md       # هذا الملف
        ├── 01-OVERVIEW.md        # البنية العامة
        ├── 02-DATABASE-SCHEMA.md # مخطط قاعدة البيانات
        ├── 03-API-REFERENCE.md   # واجهات البرمجة
        ├── 04-FRONTEND-GUIDE.md  # دليل الواجهة
        ├── 05-INTEGRATION-GUIDE.md # دليل التكامل
        ├── 06-SUGGESTIONS.md     # المقترحات المستقبلية فقط
        └── 07-TECHNICAL-SPECS.md # المواصفات التنفيذية (جديد!)
```

---

## 📚 محتويات التوثيق

### 1. OVERVIEW (نظرة عامة)
- بنية النظام الكاملة
- المكونات الرئيسية
- تدفق العمليات
- فلسفة الهندسة المعمارية
- نقاط التكامل

### 2. DATABASE-SCHEMA (مخطط قاعدة البيانات)
جداول DocType:
| الجدول | الوظيفة |
|--------|---------|
| Arrowz Settings | إعدادات التطبيق العامة |
| AZ Server Config | إعدادات خوادم PBX + GraphQL + SSH |
| AZ Extension | ربط المستخدمين بالتحويلات |
| AZ Call Log | سجل المكالمات |
| AZ Sentiment Log | سجل تحليل المشاعر |
| AZ SMS Message | رسائل SMS (جديد!) |
| AZ SMS Provider | مزودي SMS (جديد!) |
| AZ Call Transfer Log | سجل التحويلات (جديد!) |

### 3. API-REFERENCE (واجهات البرمجة)
الوحدات:
- `webrtc.py` - إعدادات الاتصال
- `ai.py` - تكامل OpenAI
- `crm.py` - البحث في CRM
- `call_log.py` - تسجيل المكالمات
- `presence.py` - إدارة الحضور
- `transfer.py` - تحويل المكالمات (جديد!)
- `recordings.py` - تشغيل التسجيلات (جديد!)
- `sms.py` - رسائل SMS (جديد!)
- `freepbx.py` - GraphQL API (جديد!)
- `click_to_dial.py` - الاتصال بنقرة (جديد!)

### 4. FRONTEND-GUIDE (دليل الواجهة)
الفئات JavaScript:
- `ArrowzSoftphone` - واجهة الاتصال
- `ArrowzNavbarPhone` - زر Navbar (جديد!)
- `ArrowzSoftphonePopup` - نافذة متعددة التبويبات (جديد!)
- `ArrowzAI` - مساعد الذكاء الاصطناعي
- `ArrowzPresence` - إدارة الحضور
- `ArrowzLogger` - تسجيل الأحداث

### 5. INTEGRATION-GUIDE (دليل التكامل)
- إعداد FreePBX/Asterisk
- تكوين WebRTC
- FreePBX GraphQL API (جديد!)
- Docker Volume للتسجيلات (جديد!)
- AMI Events (جديد!)
- fwconsole SSH (جديد!)
- إعداد OpenAI
- تكامل CRM

### 6. SUGGESTIONS (المقترحات المستقبلية فقط)
⚠️ **تم نقل الميزات المقررة إلى 07-TECHNICAL-SPECS.md**

مقترحات للمستقبل:
- دعم Queue/ACD
- Enhanced AI Features
- Mobile PWA
- Dashboard & Analytics

### 7. TECHNICAL-SPECS (المواصفات التنفيذية) 🆕
**جميع القرارات المتخذة وخطة التنفيذ:**
- فلسفة الهندسة المعمارية
- Softphone UI (Navbar + Multi-tab)
- تحويل المكالمات (Attended/Blind)
- تشغيل التسجيلات (Docker Volume)
- FreePBX GraphQL Integration
- AMI Events Integration
- SMS Integration (Provider-agnostic)
- Video Calls (via PBX)
- Audio Controls & Noise Cancellation
- خريطة التنفيذ (Implementation Roadmap)

---

## 🚀 كيفية الاستخدام

### للذكاء الاصطناعي الذي سيكتب الكود:
1. ابدأ بقراءة `01-OVERVIEW.md` لفهم البنية العامة
2. **اقرأ `07-TECHNICAL-SPECS.md` للقرارات والمواصفات التنفيذية**
3. اقرأ `02-DATABASE-SCHEMA.md` لإنشاء DocTypes
4. استخدم `03-API-REFERENCE.md` لكتابة ملفات Python
5. استخدم `04-FRONTEND-GUIDE.md` لكتابة JavaScript
6. راجع `05-INTEGRATION-GUIDE.md` للتكاملات الخارجية
7. راجع `06-SUGGESTIONS.md` للمقترحات المستقبلية (غير مقررة بعد)

### للمطور البشري:
1. راجع `07-TECHNICAL-SPECS.md` للخطة التنفيذية الكاملة
2. راجع المقترحات المستقبلية في `06-SUGGESTIONS.md`
3. اتخذ قرارات حول المقترحات الجديدة
4. وجه الذكاء الاصطناعي للتنفيذ

---

## ⚙️ متطلبات النظام

| المتطلب | الإصدار |
|---------|---------|
| Frappe Framework | v15+ |
| Python | 3.10+ |
| Node.js | 18+ |
| MariaDB | 10.6+ |
| Redis | 6+ |

### تبعيات اختيارية:
- ERPNext v15+ (لميزات CRM)
- FreePBX 17+ (لتكامل PBX + GraphQL)
- OpenAI API Key (لميزات AI)
- Docker (للتسجيلات المشتركة)

---

## 🎯 القرارات المتخذة ✅

تم اتخاذ قرارات حول الميزات التالية - التفاصيل في `07-TECHNICAL-SPECS.md`:

| الميزة | القرار |
|--------|--------|
| Softphone UI | Navbar + Multi-tab popup |
| Call Transfer | Attended افتراضي، Blind للـ Supervisors |
| Recording Playback | Docker Shared Volume |
| SMS Integration | Provider-agnostic architecture |
| Video Calls | عبر PBX (PJSIP + WebRTC) |
| Audio Controls | Native browser + optional RNNoise |
| FreePBX Integration | GraphQL للـ Extensions، fwconsole للـ Trunks |
| Click-to-Dial | AMI Originate |
| Screen Pop | AMI Events + Socket.IO |

## ❓ قرارات مستقبلية

راجع `06-SUGGESTIONS.md`:
- دعم Queues
- Enhanced AI Features
- Mobile PWA
- Dashboard & Analytics

---

## 💡 فلسفة الهندسة المعمارية

```
┌─────────────────────────────────────────────────────────────┐
│                    Arrowz Architecture                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Asterisk = محرك الاتصال                                   │
│   • AMI للأحداث الفورية والتحكم                              │
│   • PJSIP للمرونة (SIP/WebRTC/Video)                       │
│                                                             │
│   ERPNext = العقل المدبر                                    │
│   • إدارة البيانات (Contacts, Leads, Customers)             │
│   • الواجهة الموحدة (Softphone, Dashboard)                  │
│   • منطق الأعمال (Permissions, Workflows)                   │
│                                                             │
│   GraphQL + fwconsole = إدارة PBX Configuration            │
│   WebRTC = الصوت/الفيديو في المتصفح                         │
│   Docker Volumes = مشاركة التسجيلات                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

*تم إنشاء هذا التوثيق لتمكين أي ذكاء اصطناعي من إعادة بناء التطبيق بالكامل*
*آخر تحديث: تمت إضافة 07-TECHNICAL-SPECS.md مع جميع القرارات المتخذة*

## ⚙️ متطلبات النظام

| المتطلب | الإصدار |
|---------|---------|
| Frappe Framework | v15+ |
| Python | 3.10+ |
| Node.js | 18+ |
| MariaDB | 10.6+ |
| Redis | 6+ |

### تبعيات اختيارية:
- ERPNext v15+ (لميزات CRM)
- FreePBX 16+ (لتكامل PBX)
- OpenAI API Key (لميزات AI)

---

## 🎯 الميزات الحالية (من ContactCall)

✅ **تم التوثيق:**
- Softphone WebRTC كامل
- تسجيل SIP/WebSocket
- Click-to-call من حقول الهاتف
- تحليل المشاعر بـ AI
- سجل المكالمات الشامل
- تكامل مع Contact/Lead
- إدارة الحضور

❌ **بحاجة للتطوير:**
- تحويل المكالمات
- دعم Queues
- تشغيل التسجيلات
- تطبيق موبايل
- Dashboard متقدم

---

## 💡 ملاحظات للتطوير

### أولويات مقترحة:
1. **عاجل**: Call Transfer
2. **مهم**: Recording Playback
3. **متوسط**: Queue Support
4. **منخفض**: Video Calls

### قرارات تحتاج مناقشة:
1. هل نفصل AI إلى تطبيق منفصل؟
2. أي مزود SMS نستخدم؟
3. هل ندعم PBX متعددة؟

---

*تم إنشاء هذا التوثيق لتمكين أي ذكاء اصطناعي من إعادة بناء التطبيق بالكامل*
