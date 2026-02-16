# Arrowz - Glossary / قاموس المصطلحات

> Technical terms and abbreviations used in the Arrowz project.

---

## A

### AMI (Asterisk Manager Interface)
Protocol for controlling Asterisk PBX. Used for call origination, hangup, and event monitoring.
```
بروتوكول للتحكم في Asterisk PBX. يُستخدم لإجراء المكالمات وإنهائها ومراقبة الأحداث.
```

### API Endpoint
A URL that accepts HTTP requests and returns data. In Frappe, decorated with `@frappe.whitelist()`.
```
عنوان URL يقبل طلبات HTTP ويُرجع بيانات. في Frappe، يُزين بـ @frappe.whitelist()
```

---

## B

### Bench
Frappe's CLI tool for managing sites and apps. All commands start with `bench`.
```
أداة سطر الأوامر لـ Frappe لإدارة المواقع والتطبيقات. جميع الأوامر تبدأ بـ bench
```

### Boot Session
Data sent to browser when user logs in. Defined in `boot.py`.
```
البيانات المُرسلة للمتصفح عند تسجيل الدخول. تُعرّف في boot.py
```

---

## C

### CDR (Call Detail Record)
Record of a phone call containing caller, receiver, duration, status, etc. Stored in `AZ Call Log`.
```
سجل مكالمة هاتفية يحتوي على المتصل والمستقبل والمدة والحالة. يُخزن في AZ Call Log
```

### Contact Session
A conversation thread with a specific contact across messaging channels.
```
سلسلة محادثات مع جهة اتصال معينة عبر قنوات المراسلة.
```

---

## D

### DocType
Frappe's data model definition. Combines database schema with UI form.
```
تعريف نموذج البيانات في Frappe. يجمع بين مخطط قاعدة البيانات ونموذج الواجهة.
```

### DTMF (Dual-Tone Multi-Frequency)
The tones produced when pressing phone keypad buttons.
```
النغمات المنتجة عند الضغط على أزرار لوحة مفاتيح الهاتف.
```

---

## E

### Extension
A SIP phone line assigned to a user (e.g., extension 1001).
```
خط هاتف SIP مُعين لمستخدم (مثل تحويلة 1001).
```

---

## F

### Frappe
Python web framework used by ERPNext. Provides ORM, REST API, real-time, and UI components.
```
إطار عمل Python للويب يستخدمه ERPNext. يوفر ORM وREST API والوقت الحقيقي ومكونات الواجهة.
```

### FreePBX
Open-source GUI for managing Asterisk PBX.
```
واجهة مستخدم مفتوحة المصدر لإدارة Asterisk PBX.
```

---

## G

### Graph API
Meta's API for WhatsApp Business (Cloud API).
```
واجهة برمجة تطبيقات Meta لـ WhatsApp Business (Cloud API).
```

---

## H

### Hooks
Frappe's mechanism for app integration. Defined in `hooks.py`.
```
آلية Frappe لتكامل التطبيقات. تُعرّف في hooks.py.
```

---

## I

### ICE (Interactive Connectivity Establishment)
Protocol for NAT traversal in WebRTC. Uses STUN/TURN servers.
```
بروتوكول لتجاوز NAT في WebRTC. يستخدم خوادم STUN/TURN.
```

---

## J

### JsSIP
JavaScript SIP library for WebRTC-based VoIP calls.
```
مكتبة JavaScript SIP لمكالمات VoIP المبنية على WebRTC.
```

---

## L

### Lead
A potential customer in CRM. Can be linked to calls and messages.
```
عميل محتمل في CRM. يمكن ربطه بالمكالمات والرسائل.
```

---

## M

### Mute
Disable microphone during a call.
```
تعطيل الميكروفون أثناء المكالمة.
```

---

## N

### Navbar
The top navigation bar in Frappe Desk. Contains softphone dropdown and notification badges.
```
شريط التنقل العلوي في Frappe Desk. يحتوي على قائمة السوفت فون وشارات الإشعارات.
```

---

## O

### Omni-Channel
Unified communication across multiple channels (voice, WhatsApp, Telegram, etc.).
```
اتصال موحد عبر قنوات متعددة (صوت، WhatsApp، Telegram، إلخ).
```

### OpenMeetings
Apache open-source video conferencing solution.
```
حل مؤتمرات الفيديو مفتوح المصدر من Apache.
```

---

## P

### PBX (Private Branch Exchange)
Phone system for managing internal and external calls.
```
نظام هاتف لإدارة المكالمات الداخلية والخارجية.
```

### Publish Realtime
Frappe's method to send real-time events to browsers via Socket.IO.
```python
frappe.publish_realtime("event", data, user=user)
```

---

## Q

### Queue
Redis-based job queue for background tasks.
```
طابور مهام قائم على Redis للمهام الخلفية.
```

---

## R

### RQ (Redis Queue)
Python library for background job processing.
```
مكتبة Python لمعالجة المهام الخلفية.
```

### RTP (Real-time Transport Protocol)
Protocol for delivering audio/video over IP.
```
بروتوكول لتوصيل الصوت/الفيديو عبر IP.
```

---

## S

### Screen Pop
Popup showing caller information when a call is received.
```
نافذة منبثقة تعرض معلومات المتصل عند استقبال مكالمة.
```

### SDP (Session Description Protocol)
Protocol describing multimedia sessions. Used in WebRTC signaling.
```
بروتوكول يصف جلسات الوسائط المتعددة. يُستخدم في WebRTC.
```

### SIP (Session Initiation Protocol)
Protocol for initiating, modifying, and terminating VoIP sessions.
```
بروتوكول لبدء جلسات VoIP وتعديلها وإنهائها.
```

### Socket.IO
Real-time bidirectional communication library.
```
مكتبة اتصال ثنائي الاتجاه في الوقت الحقيقي.
```

### Softphone
Software-based phone running in browser (WebRTC).
```
هاتف برمجي يعمل في المتصفح (WebRTC).
```

### STUN (Session Traversal Utilities for NAT)
Server helping WebRTC clients discover their public IP.
```
خادم يساعد عملاء WebRTC على اكتشاف عنوان IP العام الخاص بهم.
```

---

## T

### Template Message
Pre-approved WhatsApp message format for business communication.
```
تنسيق رسالة WhatsApp معتمد مسبقًا للتواصل التجاري.
```

### Transfer
Move an active call to another extension or number.
```
نقل مكالمة نشطة إلى تحويلة أو رقم آخر.
```

### TURN (Traversal Using Relays around NAT)
Server relaying media when direct P2P connection fails.
```
خادم لترحيل الوسائط عند فشل الاتصال المباشر P2P.
```

---

## U

### UA (User Agent)
JsSIP's SIP client object managing calls.
```
كائن عميل SIP في JsSIP لإدارة المكالمات.
```

---

## V

### VoIP (Voice over IP)
Technology for voice calls over internet.
```
تقنية لإجراء المكالمات الصوتية عبر الإنترنت.
```

---

## W

### Wallboard
Real-time dashboard showing call center statistics.
```
لوحة معلومات في الوقت الحقيقي تعرض إحصائيات مركز الاتصال.
```

### Webhook
HTTP callback for receiving real-time notifications from external services.
```
استدعاء HTTP لاستقبال إشعارات الوقت الحقيقي من الخدمات الخارجية.
```

### WebRTC (Web Real-Time Communication)
Browser API for peer-to-peer audio/video communication.
```
واجهة برمجة تطبيقات المتصفح للاتصال الصوتي/المرئي من نظير إلى نظير.
```

### Whitelist
Frappe decorator allowing method to be called via API.
```python
@frappe.whitelist()
def my_api_function():
    pass
```

### WSS (WebSocket Secure)
Encrypted WebSocket protocol for SIP signaling.
```
بروتوكول WebSocket مشفر لإشارات SIP.
```

---

## DocType Quick Reference

| DocType | Arabic | Purpose |
|---------|--------|---------|
| AZ Call Log | سجل المكالمات | Call records |
| AZ Extension | التحويلة | SIP extension mapping |
| AZ Server Config | إعدادات الخادم | PBX/OM configuration |
| AZ SMS Message | رسالة SMS | SMS history |
| AZ Omni Provider | مزود القناة | WhatsApp/Telegram config |
| AZ Conversation Session | جلسة المحادثة | Chat threads |
| AZ Message | الرسالة | Individual messages |
| AZ Meeting Room | غرفة الاجتماع | Video conference room |
| Arrowz Settings | إعدادات Arrowz | Global app settings |

---

## API Module Reference

| Module | Endpoint Prefix | Purpose |
|--------|-----------------|---------|
| webrtc | `arrowz.api.webrtc.*` | JsSIP configuration |
| calls | `arrowz.api.calls.*` | Call operations |
| sms | `arrowz.api.sms.*` | SMS operations |
| communications | `arrowz.api.communications.*` | Omni-channel |
| contacts | `arrowz.api.contacts.*` | Contact search |
| wallboard | `arrowz.api.wallboard.*` | Live statistics |
| analytics | `arrowz.api.analytics.*` | Reports |
| webhooks | `arrowz.api.webhooks.*` | External callbacks |
