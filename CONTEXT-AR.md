# Arrowz - سياق التطبيق للذكاء الاصطناعي

> هذا المستند يوفر السياق الشامل لنماذج الذكاء الاصطناعي للعمل مع تطبيق Arrowz.

## نظرة عامة سريعة

- **اسم التطبيق**: Arrowz
- **النوع**: تطبيق Frappe Framework
- **الغرض**: إدارة مكالمات VoIP المؤسسية والاتصالات متعددة القنوات
- **الإصدار**: 1.0.0
- **الإطار**: Frappe v15+
- **اللغات**: Python 3.10+, JavaScript ES6+

## القدرات الأساسية

1. **سوفت فون WebRTC** - اتصال من المتصفح عبر JsSIP
2. **رسائل متعددة القنوات** - WhatsApp, Telegram
3. **مؤتمرات الفيديو** - تكامل OpenMeetings
4. **تحليلات AI** - تحليل المشاعر والتدريب
5. **تكامل CRM** - تحديد جهات الاتصال والسجل

## البنية المعمارية

```
┌─────────────────────────────────────────────────────────────────┐
│                     منصة ARROWZ                                 │
├─────────────────────────────────────────────────────────────────┤
│  الواجهة الأمامية                                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │   سوفت فون  │ │  لوحة الدردشة│ │    نافذة المتصل         ││
│  │  (WebRTC)   │ │  (Omni Panel)│ │   (Screen Pop)          ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  طبقة API (arrowz/api/)                                        │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐│
│  │ WebRTC │ │  SMS   │ │المكالمات│ │التحليلات│ │  الاتصالات   ││
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  طبقة التكامل                                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │  WhatsApp    │ │  Telegram    │ │     OpenMeetings        ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  الأنظمة الخارجية                                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │   FreePBX   │ │  Asterisk    │ │   OpenMeetings Server   ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## هيكل المشروع

```
arrowz/
├── arrowz/                    # الوحدة الرئيسية
│   ├── api/                   # نقاط API
│   │   ├── webrtc.py         # إعدادات JsSIP
│   │   ├── sms.py            # إرسال/استقبال SMS
│   │   ├── call_log.py       # عمليات سجل المكالمات
│   │   ├── contacts.py       # البحث عن جهات الاتصال
│   │   ├── notifications.py  # الإشعارات المعلقة
│   │   ├── communications.py # محادثات Omni-Channel
│   │   ├── wallboard.py      # إحصائيات لوحة التحكم
│   │   ├── analytics.py      # التقارير
│   │   └── webhooks.py       # Webhooks خارجية
│   │
│   ├── arrowz/               # DocTypes والصفحات
│   │   ├── doctype/
│   │   │   ├── arrowz_settings/      # إعدادات التطبيق
│   │   │   ├── az_call_log/          # سجل المكالمات
│   │   │   ├── az_extension/         # تحويلات SIP
│   │   │   ├── az_server_config/     # إعدادات الخوادم
│   │   │   ├── az_sms_message/       # سجل SMS
│   │   │   ├── az_conversation_session/  # جلسات الدردشة
│   │   │   ├── az_omni_provider/     # إعدادات WhatsApp/Telegram
│   │   │   └── az_meeting_room/      # غرف المؤتمرات
│   │   │
│   │   ├── workspace/        # تعريف مساحة العمل
│   │   └── page/             # الصفحات المخصصة
│   │
│   ├── integrations/         # موصلات الخدمات
│   │   ├── whatsapp.py       # WhatsApp Cloud API
│   │   ├── telegram.py       # Telegram Bot API
│   │   └── openmeetings.py   # OpenMeetings REST API
│   │
│   ├── public/               # الأصول الثابتة
│   │   ├── js/
│   │   │   ├── softphone_v2.js   # سوفت فون WebRTC
│   │   │   ├── omni_panel.js     # لوحة الدردشة
│   │   │   └── phone_actions.js  # النقر للاتصال
│   │   └── css/
│   │
│   ├── hooks.py              # تكامل Frappe
│   ├── tasks.py              # المهام المجدولة
│   └── boot.py               # بيانات الجلسة
│
└── docs/                     # التوثيق
```

## DocTypes الرئيسية

| DocType | الغرض | الحقول الرئيسية |
|---------|-------|-----------------|
| `Arrowz Settings` | إعدادات التطبيق | `enable_ai`, `openai_api_key`, `default_server` |
| `AZ Call Log` | سجل المكالمات | `call_id`, `caller`, `receiver`, `status`, `duration` |
| `AZ Extension` | ربط التحويلات | `extension`, `user`, `sip_password`, `server` |
| `AZ Server Config` | إعدادات الخوادم | `server_type`, `host`, `websocket_url`, `username` |
| `AZ SMS Message` | سجل SMS | `phone`, `message`, `direction`, `status` |
| `AZ Omni Provider` | إعدادات القنوات | `channel_type`, `access_token`, `phone_number_id` |
| `AZ Conversation Session` | جلسات الدردشة | `contact_number`, `channel_type`, `status`, `assigned_agent` |
| `AZ Meeting Room` | غرف المؤتمرات | `room_name`, `external_room_id`, `moderator` |

## مرجع API

### الـ APIs الأساسية

```python
# الحصول على إعدادات WebRTC
arrowz.api.webrtc.get_webrtc_config()
# يُرجع: {extension, sip_uri, sip_password, websocket_servers[], display_name}

# البحث عن جهات الاتصال
arrowz.api.contacts.search_contacts(query, limit=10)
# يُرجع: [{doctype, name, full_name, phone, email}]

# الإشعارات المعلقة
arrowz.api.notifications.get_pending_notifications()
# يُرجع: {pending_sms: [], missed_calls: int}

# إحصائيات اللوحة
arrowz.api.wallboard.get_realtime_stats()
# يُرجع: {active_calls, waiting_queue, agents_online, avg_wait_time}

# إرسال رسالة
arrowz.api.communications.send_message(session, message, message_type)

# المحادثات النشطة
arrowz.api.communications.get_active_conversations(user, limit)
```

## مكونات الواجهة الأمامية

### السوفت فون (softphone_v2.js)
```javascript
arrowz.softphone = {
    dial(number),        // إجراء مكالمة
    answer(),            // الرد على مكالمة
    hangup(),            // إنهاء المكالمة
    toggleMute(),        // كتم/إلغاء كتم
    toggleHold(),        // انتظار/استئناف
    transfer(target),    // تحويل المكالمة
    switchExtension(ext) // تبديل التحويلة
};
```

### لوحة الدردشة (omni_panel.js)
```javascript
arrowz.omni.panel = {
    show(),              // إظهار اللوحة
    hide(),              // إخفاء اللوحة
    sendMessage(text),   // إرسال رسالة
    loadConversations()  // تحميل المحادثات
};
```

## التكاملات

### FreePBX/Asterisk
- **البروتوكول**: WebSocket (wss://) لـ WebRTC
- **المكتبة**: JsSIP
- **الإعداد**: `AZ Server Config`

### WhatsApp (Meta Cloud API)
- **نقطة النهاية**: Graph API v17+
- **Webhook**: `/api/method/arrowz.api.webhooks.whatsapp_cloud_webhook`
- **الإعداد**: `AZ Omni Provider` بنوع "WhatsApp"

### Telegram (Bot API)
- **نقطة النهاية**: Bot API
- **Webhook**: `/api/method/arrowz.api.webhooks.telegram_webhook`
- **الإعداد**: `AZ Omni Provider` بنوع "Telegram"

### OpenMeetings
- **البروتوكول**: REST API
- **الإعداد**: `AZ Server Config` بنوع "OpenMeetings"

## أحداث الوقت الحقيقي (Socket.IO)

| الحدث | الوصف |
|-------|-------|
| `arrowz_call_started` | بدء مكالمة جديدة |
| `arrowz_call_ended` | انتهاء المكالمة |
| `arrowz_new_sms` | رسالة SMS جديدة |
| `arrowz_missed_call` | مكالمة فائتة |
| `new_message` | رسالة Omni-Channel |
| `conversation_update` | تحديث المحادثة |

## أوامر التطوير

```bash
# بناء الأصول
bench build --app arrowz

# مراقبة التغييرات
bench watch --app arrowz

# مسح الكاش
bench --site dev.localhost clear-cache

# الهجرة
bench --site dev.localhost migrate

# إعادة التشغيل
bench restart

# اختبار API
bench --site dev.localhost console
>>> frappe.call('arrowz.api.webrtc.get_webrtc_config')
```

## أنماط الكود

### Python API
```python
@frappe.whitelist()
def my_function(param1: str, param2: int = None) -> dict:
    """وصف الدالة.
    
    Args:
        param1: الوصف
        param2: وصف اختياري
    
    Returns:
        dict: النتيجة
    """
    frappe.only_for(['System Manager', 'Call Center Agent'])
    # التنفيذ
    return {"status": "success"}
```

### JavaScript
```javascript
arrowz.myFeature = {
    async loadData() {
        const { message } = await frappe.call({
            method: 'arrowz.api.myfeature.get_data'
        });
        return message;
    }
};
```

## معالجة الأخطاء

### Python
```python
# خطأ للمستخدم
frappe.throw(_("رسالة الخطأ"), exc=frappe.ValidationError)

# تسجيل الخطأ في الخلفية
try:
    result = external_api_call()
except Exception as e:
    frappe.log_error(message=str(e), title="External API Error")
```

### JavaScript
```javascript
try {
    const { message } = await frappe.call({method: 'arrowz.api.mymethod'});
} catch (error) {
    frappe.show_alert({message: __('حدث خطأ'), indicator: 'red'});
}
```

## استكشاف الأخطاء

### السوفت فون لا يظهر
1. افحص console المتصفح لأخطاء JavaScript
2. تحقق من أن `softphone_v2.js` مضمن في `app_include_js`
3. تأكد من أن المستخدم لديه تحويلة

### فشل تسجيل WebRTC
1. تحقق من WebSocket URL (wss:// وليس ws://)
2. افحص بيانات SIP في `AZ Extension`
3. تأكد من تمكين WebSocket في PBX

### رسائل Omni-Channel لا تصل
1. تحقق من أن Webhook URL عام
2. افحص التحقق من التوقيع
3. راجع Error Log

---

*آخر تحديث: يناير 2026*
