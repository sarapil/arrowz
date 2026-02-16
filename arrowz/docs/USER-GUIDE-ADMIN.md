# دليل مستخدم Arrowz - مدير النظام
## Admin User Guide

<div dir="rtl">

# مرحباً بك كمدير نظام Arrowz! ⚙️

هذا الدليل الشامل يغطي جميع إعدادات وتكوينات النظام.

---

## 🏗️ البنية العامة للنظام

```
┌─────────────────────────────────────────────────────┐
│                    Arrowz App                        │
├─────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │
│  │Softphone│  │Dashboard│  │Analytics│  │Settings│ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬───┘ │
│       │            │            │             │      │
│  ┌────┴────────────┴────────────┴─────────────┴───┐ │
│  │                  Frappe API                     │ │
│  └────────────────────┬───────────────────────────┘ │
│                       │                              │
│  ┌────────────────────┴───────────────────────────┐ │
│  │             FreePBX / Asterisk                  │ │
│  │        (AMI + GraphQL + WebSocket)              │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 الإعداد الأولي

### الخطوة 1: تثبيت التطبيق
```bash
# تثبيت التطبيق
bench get-app arrowz
bench --site your-site install-app arrowz

# تشغيل الترحيل
bench --site your-site migrate
```

### الخطوة 2: إعدادات التطبيق
1. اذهب إلى **Arrowz Settings**
2. املأ الإعدادات الأساسية:
   - تمكين الميزات المطلوبة
   - إعدادات AI (إن وجدت)
   - إعدادات التسجيل

### الخطوة 3: تكوين خادم PBX
1. اذهب إلى **AZ Server Config**
2. أنشئ تكويناً جديداً
3. أدخل بيانات الاتصال

---

## 📡 تكوين خادم PBX

### AZ Server Config

#### البيانات المطلوبة:

| الحقل | الوصف | مثال |
|-------|-------|------|
| Server Name | اسم مميز للخادم | PBX-Main |
| Host | عنوان IP أو اسم النطاق | 172.21.0.2 |
| AMI Port | منفذ AMI | 5038 |
| AMI Username | مستخدم AMI | arrowz |
| AMI Password | كلمة مرور AMI | ******* |
| GraphQL URL | رابط API | https://172.21.0.2/admin/api/api/gql |
| Client ID | معرّف OAuth2 | abc123xyz... |
| Client Secret | سر OAuth2 | def456uvw... |
| Verify SSL | للشهادات الذاتية | ❌ غير مفعل |

> **ملاحظة**: النظام يدير OAuth Token تلقائياً - لا حاجة لإدخاله يدوياً!

#### الحصول على Client ID و Secret:
1. افتح FreePBX: `https://YOUR_PBX_IP/admin`
2. اذهب إلى: **Admin** → **API** → **GraphQL** → **Applications**
3. انقر **Add Application**
4. اختر Type: **Machine-to-Machine**
5. أدخل اسم: `Arrowz Integration`
6. احفظ وانسخ **Client ID** و **Client Secret**

#### اختبار الاتصال:
1. بعد إدخال البيانات، انقر **Test Connection**
2. تأكد من ظهور رسالة نجاح
3. إذا فشل، راجع:
   - صحة البيانات
   - إعدادات الجدار الناري
   - تشغيل خدمة AMI

---

## 📞 إعداد التحويلات

### AZ Extension

#### لكل مستخدم:
1. اذهب إلى **AZ Extension**
2. أنشئ سجلاً جديداً
3. اربط المستخدم بالتحويلة

#### الحقول:

| الحقل | الوصف |
|-------|-------|
| User | مستخدم Frappe |
| Extension | رقم التحويلة |
| SIP Username | اسم مستخدم SIP |
| SIP Password | كلمة مرور SIP |
| Server Config | الخادم المرتبط |
| WebSocket URL | رابط WebSocket لـ WebRTC |
| STUN/TURN | إعدادات NAT |

#### إعدادات WebRTC:
```
WebSocket URL: wss://pbx.example.com:8089/ws
STUN Server: stun:stun.l.google.com:19302
```

---

## 💬 إعداد SMS

### AZ SMS Provider

#### مزودي الخدمة المدعومين:
- Twilio
- MessageBird
- Vonage (Nexmo)
- مخصص (Custom API)

#### تكوين Twilio:
```
Provider Name: Twilio
API Endpoint: https://api.twilio.com/2010-04-01
Account SID: ACxxxxxxxxx
Auth Token: xxxxxxxxxx
From Number: +1234567890
```

#### اختبار الإرسال:
1. انقر **Test Connection**
2. أدخل رقم اختبار
3. تأكد من وصول الرسالة

---

## 🎙️ إعداد التسجيلات

### تخزين التسجيلات:

#### الخيار 1: Docker Volume (موصى به)
```python
# في site_config.json
"recording_storage": "docker_volume",
"recording_path": "/var/spool/asterisk/monitor"
```

#### الخيار 2: تخزين سحابي
```python
# في Arrowz Settings
storage_type = "S3"
aws_access_key = "AKIA..."
aws_secret_key = "..."
s3_bucket = "arrowz-recordings"
```

### صلاحيات الوصول:
- **Agent**: تسجيلاته فقط
- **Manager**: تسجيلات فريقه
- **Admin**: جميع التسجيلات

---

## 🤖 إعداد الذكاء الاصطناعي

### OpenAI Integration:
1. احصل على API Key من OpenAI
2. في **Arrowz Settings**:
   - Enable AI Features ✓
   - OpenAI API Key: sk-xxxxx
   - Model: gpt-4 (أو gpt-3.5-turbo)

### الميزات المتاحة:
- 📝 ملخص المكالمات تلقائياً
- 💭 تحليل المشاعر
- 🏷️ تصنيف أسباب الاتصال
- 💡 اقتراحات للوكيل

---

## 👥 إدارة الأدوار والصلاحيات

### الأدوار المدمجة:

#### Call Center Agent
```
- AZ Call Log: Read, Create (own)
- AZ Extension: Read (own)
- AZ SMS Message: Read, Create
- Pages: Agent Dashboard
```

#### Call Center Manager
```
- AZ Call Log: Read all
- AZ Extension: Read all
- AZ SMS Message: Read all
- Pages: Wallboard, Analytics
- Can Monitor Calls: Yes
```

#### System Admin
```
- Full Access to all Arrowz doctypes
- Arrowz Settings: Read, Write
- AZ Server Config: Read, Write
- Can configure system
```

### إنشاء دور مخصص:
1. اذهب إلى **Role**
2. أنشئ دوراً جديداً
3. في **Role Permissions Manager**:
   - أضف صلاحيات Arrowz doctypes
   - حدد المستوى المطلوب

---

## 🔄 المهام المجدولة

### المهام التلقائية:

| المهمة | التردد | الوصف |
|--------|--------|-------|
| cleanup_stale_presence | كل 5 دقائق | تنظيف حالات التوفر القديمة |
| sync_pbx_status | كل ساعة | مزامنة مع PBX |
| generate_daily_report | يومياً | إنشاء تقرير يومي |
| cleanup_old_presence_logs | يومياً | حذف سجلات التوفر القديمة |
| generate_weekly_analytics | أسبوعياً | إنشاء تحليلات أسبوعية |

### تخصيص المهام:
في `hooks.py`:
```python
scheduler_events = {
    "cron": {
        "*/5 * * * *": ["arrowz.tasks.custom_task"]
    }
}
```

---

## 📊 إعداد التقارير

### تقارير مخصصة:
1. اذهب إلى **Report Builder**
2. اختر DocType: AZ Call Log
3. أضف الحقول المطلوبة
4. أضف الفلاتر
5. احفظ التقرير

### تقارير مجدولة:
1. افتح التقرير
2. انقر **Menu** ← **Add to Auto Email Report**
3. حدد:
   - التردد (يومي، أسبوعي، شهري)
   - المستلمين
   - الوقت

---

## 🔐 الأمان

### أفضل الممارسات:

#### 1. حماية API Keys
```python
# لا تضع في الكود مباشرة
# استخدم site_config.json
frappe.conf.get("openai_api_key")
```

#### 2. تشفير كلمات المرور
- جميع كلمات مرور SIP مشفرة
- استخدم حقول Password

#### 3. تقييد الوصول
```python
# في DocType
permissions:
  - role: System Manager
    read: 1
    write: 1
```

#### 4. تدقيق العمليات
- جميع العمليات مسجلة في Log
- راجع **Error Log** و **Activity Log**

---

## 🔧 استكشاف الأخطاء

### مشاكل الاتصال بـ PBX:

#### الخطأ: Connection Refused
```bash
# تحقق من الخدمة
ssh user@pbx-server
systemctl status asterisk

# تحقق من المنفذ
netstat -tlnp | grep 5038
```

#### الخطأ: Authentication Failed
- تحقق من اسم المستخدم وكلمة المرور
- راجع `/etc/asterisk/manager.conf`

### مشاكل WebRTC:

#### لا يعمل الصوت
1. تحقق من HTTPS (مطلوب لـ WebRTC)
2. راجع إعدادات STUN/TURN
3. تحقق من الجدار الناري

#### انقطاع الاتصال
- تحقق من WebSocket URL
- راجع إعدادات timeout

### مشاكل التسجيلات:

#### لا تظهر التسجيلات
1. تحقق من المسار في الإعدادات
2. تأكد من الصلاحيات على المجلد
3. راجع إعدادات Docker volume

---

## 📝 ملفات السجلات

### مواقع السجلات:
```
frappe-bench/logs/
├── frappe.log        # سجل عام
├── worker.log        # سجل المهام الخلفية
└── scheduler.log     # سجل المهام المجدولة

/var/log/asterisk/
├── full              # سجل Asterisk الكامل
├── messages          # رسائل النظام
└── queue_log         # سجل الطوابير
```

### تتبع المشاكل:
```bash
# مراقبة السجل
tail -f frappe-bench/logs/frappe.log | grep arrowz

# البحث عن خطأ
grep "Error" logs/frappe.log | grep arrowz
```

---

## 🔄 النسخ الاحتياطي

### ما يجب نسخه:
1. قاعدة البيانات
2. التسجيلات الصوتية
3. site_config.json
4. الملفات المرفقة

### أوامر النسخ:
```bash
# نسخ قاعدة البيانات
bench --site your-site backup

# نسخ التسجيلات
rsync -av /recording/path/ /backup/recordings/
```

---

## 🔄 التحديث

### تحديث التطبيق:
```bash
cd frappe-bench/apps/arrowz
git pull origin main
bench --site your-site migrate
bench build
```

### ما بعد التحديث:
1. اختبر الاتصال بـ PBX
2. تحقق من عمل السوفت فون
3. راجع الإعدادات الجديدة

---

## 📞 الدعم الفني المتقدم

**للمشاكل التقنية:**
- 📧 tech-support@arrowz.io
- 📱 خط ساخن: 1234-567-892

**موارد إضافية:**
- 📚 التوثيق: docs.arrowz.io
- 💻 GitHub: github.com/arrowz/arrowz
- 💬 Discord: discord.gg/arrowz

---

**شكراً لإدارتك لنظام Arrowz! 🛠️**

</div>
