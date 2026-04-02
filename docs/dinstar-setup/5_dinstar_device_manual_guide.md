# دليل ضبط جهاز Dinstar UC2000-VE-8G — خطوة بخطوة
# Dinstar UC2000-VE-8G Physical Device Configuration Guide

> ⚠️ هذا الدليل للخطوات التي تُنفذ **يدوياً على جهاز الـ Dinstar** عبر واجهة الويب.
> كل إعدادات السيرفر (VPN + Asterisk + Extensions) تم تنفيذها بالفعل.

---

## المتطلبات قبل البدء

- [x] ✅ VPN Server شغال على `tun1: 10.10.1.1/24` (UDP 51821)
- [x] ✅ 8 PJSIP endpoints (gsm-port1..8) جاهزين على Asterisk
- [x] ✅ 8 Extensions (7001-7008) مُنشأة في FreePBX
- [x] ✅ Dialplan جاهز (inbound + outbound round-robin)
- [x] ✅ ملف .ovpn جاهز للتحميل
- [ ] ⬜ ضبط الـ Dinstar (هذا الدليل)

---

## الخطوة 1: الوصول لواجهة الويب

1. **وصّل كابل إيثرنت** بين الكمبيوتر والـ Dinstar
2. **العنوان الافتراضي**: `http://192.168.1.1`
3. **بيانات الدخول**: `admin` / `admin`
4. ⚠️ **غيّر كلمة المرور فوراً** بعد أول دخول

> إذا لم تعرف الـ IP: اضغط على زر Reset لمدة 10 ثوانٍ لإرجاع الإعدادات الافتراضية

---

## الخطوة 2: إعدادات الشبكة

**المسار**: System Configuration → Network → LAN Setting

```
┌─────────────────────────────────────┐
│  IP Address    : 192.168.X.50       │  ← IP ثابت في شبكتك المحلية
│  Subnet Mask   : 255.255.255.0      │
│  Gateway       : 192.168.X.1        │  ← الراوتر
│  DNS Server    : 8.8.8.8            │
└─────────────────────────────────────┘
```

> ⚠️ **مهم جداً**: استخدم IP ثابت (Static). الـ DHCP ممكن يغيّر الـ IP ويقطع الـ VPN.

اضغط **Save** ثم **Apply**.

---

## الخطوة 3: ضبط OpenVPN

**المسار**: System Configuration → Network → VPN (أو System → OpenVPN)

### الطريقة الأولى: رفع ملف .ovpn (الأسهل)

1. حمّل الملف من السيرفر:
   ```
   الملف موجود على: /opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn
   أو: scp -P 1352 root@157.173.125.136:/opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn .
   ```

2. في واجهة الـ Dinstar:
   - Enable VPN: ✅
   - Upload الملف `dinstar-tls.ovpn`
   - اضغط **Save** ثم **Apply**

### الطريقة الثانية: إدخال يدوي (إذا الواجهة لا تدعم .ovpn)

| الإعداد | القيمة | ملاحظات |
|---------|--------|---------|
| **Enable VPN** | ✅ مفعّل | |
| **VPN Type** | OpenVPN | |
| **Server Address** | `157.173.125.136` | IP السيرفر |
| **Server Port** | `51821` | |
| **Protocol** | `UDP` | |
| **Device** | `TUN` | |
| **Cipher** | `AES-256-CBC` | |
| **Auth/HMAC** | ⚠️ `SHA1` | **ليس SHA256!** |
| **TLS Auth** | مفعّل، Direction = `1` | 1 = client |

**الشهادات** (انسخ من ملف dinstar-tls.ovpn):
- **CA Certificate**: المحتوى بين `<ca>` و `</ca>`
- **Client Certificate**: المحتوى بين `<cert>` و `</cert>`
- **Client Key**: المحتوى بين `<key>` و `</key>`
- **TLS Auth Key**: المحتوى بين `<tls-auth>` و `</tls-auth>`

### التحقق من الـ VPN:

بعد الحفظ انتظر 10-30 ثانية:
- **System Status → VPN Status** → يجب أن يظهر **Connected**
- الـ Dinstar يحصل على IP: `10.10.1.2`

**التحقق من السيرفر**:
```bash
# من الـ VPS
docker exec initpbx-freepbx-1 ping -c 3 10.10.1.2
docker exec initpbx-freepbx-1 tail -5 /var/log/openvpn-dinstar-tls.log
```

---

## الخطوة 4: ضبط SIP — 8 حسابات منفصلة (حساب لكل بورت)

**المسار**: System Configuration → SIP → SIP Parameter (أو Trunk → SIP Trunk)

### 4.1 الإعدادات العامة لـ SIP

| الإعداد | القيمة | ملاحظات |
|---------|--------|---------|
| **Local SIP Port** | `5060` | المنفذ المحلي على الـ Dinstar |
| **SIP Transport** | `UDP` | |
| **DTMF Mode** | `RFC2833` | |
| **DTMF Payload** | `101` | |
| **NAT Traversal** | ❌ `Disable` | ★ مباشر عبر VPN، لا حاجة لـ NAT |
| **PRACK** | `Disable` | |
| **Session Timer** | `Disable` | |
| **Register Retry** | `30` ثانية | |

### 4.2 إنشاء 8 حسابات SIP

**المسار**: قد يكون SIP Trunk، أو SIP Account، أو Port → SIP Settings

> 💡 الهدف: كل بورت GSM يسجّل بحساب SIP مستقل على Asterisk

---

#### ⬛ بورت 1

| الإعداد | القيمة |
|---------|--------|
| **SIP Server** | `10.10.1.1` |
| **SIP Port** | `51600` |
| **Username/Account** | `gsm-port1` |
| **Password** | `Gsm1@Arwz2026` |
| **Register** | ✅ Yes |
| **Assigned Port** | Port 1 |

---

#### ⬛ بورت 2

| الإعداد | القيمة |
|---------|--------|
| **SIP Server** | `10.10.1.1` |
| **SIP Port** | `51600` |
| **Username/Account** | `gsm-port2` |
| **Password** | `Gsm2@Arwz2026` |
| **Register** | ✅ Yes |
| **Assigned Port** | Port 2 |

---

#### ⬛ بورت 3

| الإعداد | القيمة |
|---------|--------|
| **SIP Server** | `10.10.1.1` |
| **SIP Port** | `51600` |
| **Username/Account** | `gsm-port3` |
| **Password** | `Gsm3@Arwz2026` |
| **Register** | ✅ Yes |
| **Assigned Port** | Port 3 |

---

#### ⬛ بورت 4

| الإعداد | القيمة |
|---------|--------|
| **SIP Server** | `10.10.1.1` |
| **SIP Port** | `51600` |
| **Username/Account** | `gsm-port4` |
| **Password** | `Gsm4@Arwz2026` |
| **Register** | ✅ Yes |
| **Assigned Port** | Port 4 |

---

#### ⬛ بورت 5

| الإعداد | القيمة |
|---------|--------|
| **SIP Server** | `10.10.1.1` |
| **SIP Port** | `51600` |
| **Username/Account** | `gsm-port5` |
| **Password** | `Gsm5@Arwz2026` |
| **Register** | ✅ Yes |
| **Assigned Port** | Port 5 |

---

#### ⬛ بورت 6

| الإعداد | القيمة |
|---------|--------|
| **SIP Server** | `10.10.1.1` |
| **SIP Port** | `51600` |
| **Username/Account** | `gsm-port6` |
| **Password** | `Gsm6@Arwz2026` |
| **Register** | ✅ Yes |
| **Assigned Port** | Port 6 |

---

#### ⬛ بورت 7

| الإعداد | القيمة |
|---------|--------|
| **SIP Server** | `10.10.1.1` |
| **SIP Port** | `51600` |
| **Username/Account** | `gsm-port7` |
| **Password** | `Gsm7@Arwz2026` |
| **Register** | ✅ Yes |
| **Assigned Port** | Port 7 |

---

#### ⬛ بورت 8

| الإعداد | القيمة |
|---------|--------|
| **SIP Server** | `10.10.1.1` |
| **SIP Port** | `51600` |
| **Username/Account** | `gsm-port8` |
| **Password** | `Gsm8@Arwz2026` |
| **Register** | ✅ Yes |
| **Assigned Port** | Port 8 |

---

## الخطوة 5: إعدادات الكودك

**المسار**: System Configuration → SIP → Codec

| الأولوية | الكودك | ملاحظات |
|----------|--------|---------|
| 1 | **G.711A (alaw)** | ★ الأفضل — بدون تحويل |
| 2 | **G.711U (ulaw)** | احتياطي |
| 3 | **GSM** | بديل (جودة أقل) |

> 💡 الـ Dinstar يحوّل GSM → PCM داخلياً. استخدام alaw يعني أن Asterisk لا يحتاج لأي تحويل = أفضل جودة صوت.

---

## الخطوة 6: إعدادات بورتات الـ GSM

**المسار**: Port Configuration → GSM/CDMA

### تركيب شرائح SIM

1. أدخل شرائح SIM في الفتحات (اضغط حتى تسمع صوت click)
2. انتظر ~30 ثانية للتسجيل على شبكة المحمول
3. تحقق من **System Status**:

| البورت | حالة SIM | حالة GSM | الإشارة |
|--------|----------|----------|---------|
| Port 1 | ✅ Ready | ✅ Registered | ≥ -85 dBm |
| Port 2 | ✅ Ready | ✅ Registered | ≥ -85 dBm |
| Port 3 | ✅ Ready | ✅ Registered | ≥ -85 dBm |
| Port 4 | ✅ Ready | ✅ Registered | ≥ -85 dBm |
| Port 5 | ✅ Ready | ✅ Registered | ≥ -85 dBm |
| Port 6 | ✅ Ready | ✅ Registered | ≥ -85 dBm |
| Port 7 | ✅ Ready | ✅ Registered | ≥ -85 dBm |
| Port 8 | ✅ Ready | ✅ Registered | ≥ -85 dBm |

### ربط كل بورت بحساب SIP الخاص به

| البورت | حساب SIP | رقم SIM (CallerID) |
|--------|----------|---------------------|
| Port 1 | `gsm-port1` | رقم الشريحة |
| Port 2 | `gsm-port2` | رقم الشريحة |
| Port 3 | `gsm-port3` | رقم الشريحة |
| Port 4 | `gsm-port4` | رقم الشريحة |
| Port 5 | `gsm-port5` | رقم الشريحة |
| Port 6 | `gsm-port6` | رقم الشريحة |
| Port 7 | `gsm-port7` | رقم الشريحة |
| Port 8 | `gsm-port8` | رقم الشريحة |

---

## الخطوة 7: قواعد التوجيه (Routing Rules)

### 7أ. المكالمات الواردة (GSM → FreePBX)

**المسار**: Routing Configuration → Tel→IP Route

**لكل بورت (1-8):**

| الإعداد | القيمة | ملاحظات |
|---------|--------|---------|
| **Enable** | ✅ | |
| **Route Name** | `GSM-Port-N-In` | استبدل N برقم البورت |
| **Source Port** | `Port N` | البورت المادي |
| **Destination** | حساب SIP `gsm-portN` | |
| **Caller ID Mode** | `Transparent` | تمرير رقم المتصل |
| **Called Number** | فارغ أو `s` | Asterisk يتولى التوجيه |

> 💡 **مهم**: كل بورت لازم يستخدم حساب SIP الخاص به.
> هكذا يعرف Asterisk من أي بورت جاءت المكالمة ويوجهها للامتداد الصحيح:
> - بورت 1 → امتداد 7001
> - بورت 2 → امتداد 7002
> - وهكذا...

### 7ب. المكالمات الصادرة (FreePBX → GSM)

**المسار**: Routing Configuration → IP→Tel Route

**لكل بورت (1-8):**

| الإعداد | القيمة | ملاحظات |
|---------|--------|---------|
| **Route Name** | `PBX-to-Port-N` | |
| **Source** | حساب SIP `gsm-portN` | المكالمات القادمة لهذا الحساب |
| **Destination Port** | `Port N` | توجيه للبورت المادي |
| **Strip Digits** | `0` | لا تحذف أرقام |

> 💡 **كيف يعمل التوزيع المتساوي (Round-Robin)**:
> Asterisk يختار بورت (مثلاً gsm-port5) ويرسل المكالمة.
> الـ Dinstar يستقبلها على حساب gsm-port5 ويوجهها لبورت 5.
> إذا كان البورت مشغول، Asterisk يجرب البورت التالي تلقائياً.

---

## الخطوة 8: التحقق من التسجيل

### على الـ Dinstar:
**المسار**: System Status → SIP Status

| البورت | الحالة المتوقعة |
|--------|-----------------|
| gsm-port1 | ✅ **Registered** |
| gsm-port2 | ✅ **Registered** |
| gsm-port3 | ✅ **Registered** |
| gsm-port4 | ✅ **Registered** |
| gsm-port5 | ✅ **Registered** |
| gsm-port6 | ✅ **Registered** |
| gsm-port7 | ✅ **Registered** |
| gsm-port8 | ✅ **Registered** |

### على Asterisk (من السيرفر):
```bash
# التحقق من كل الـ contacts المسجلة
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show contacts" | grep gsm

# المتوقع:
#   gsm-port1/sip:gsm-port1@10.10.1.2:5060  Avail
#   gsm-port2/sip:gsm-port2@10.10.1.2:5060  Avail
#   ... (8 سطور)

# التحقق من endpoint محدد
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show endpoint gsm-port1"
```

### حل مشاكل التسجيل:

| المشكلة | الحل |
|---------|------|
| **Trying** مستمر | تحقق من VPN أولاً (`VPN Status = Connected`?) |
| **403 Forbidden** | كلمة المرور خطأ - تأكد من المطابقة الحرفية |
| **Transport Error** | تأكد: Server = `10.10.1.1`، Port = `51600`، Protocol = UDP |
| **بعض البورتات فقط** | تأكد أن كل بورت مربوط بحساب SIP مختلف |

---

## الخطوة 9: اختبار المكالمات

### اختبار الوارد (GSM → امتداد):
1. اتصل على **رقم SIM في بورت 1** من موبايل
2. يجب أن يرن **امتداد 7001**
3. رد من ARKAN PHONE أو هاتف IP
4. كرر لكل بورت → تأكد أن الامتداد الصحيح يرن

### اختبار الصادر (امتداد → GSM):
1. من أي امتداد (مثل 2210)، اتصل بـ `01XXXXXXXXX` (رقم موبايل يبدأ بـ 0)
2. المكالمة تخرج عبر `gsm-outbound` بالتوزيع المتساوي
3. تحقق من أي بورت استُخدم في لوجات Asterisk
4. اعمل عدة مكالمات → تأكد أنها تتوزع على بورتات مختلفة

### اختبار التوزيع المتساوي:
```bash
# عداد الـ round-robin الحالي
docker exec initpbx-freepbx-1 asterisk -rx "database show gsm"
# المتوقع: /gsm/rr : N (حيث N = 1-8, البورت التالي)
```

---

## حل المشاكل الشائعة

| المشكلة | التحقق |
|---------|--------|
| VPN لا يتصل | لوجات الـ Dinstar، فايروول بورت 51821/UDP، Auth=SHA1 |
| SIP registration فشل | تحقق من VPN أولاً، ثم Server/Port/Credentials |
| بعض البورتات فقط مسجلة | تأكد أن كل بورت مربوط بحساب SIP مختلف |
| صوت باتجاه واحد | عطّل NAT Traversal على الـ Dinstar |
| بدون صوت | تأكد من VPN متصل، وتحقق من RTP ports |
| الوارد يروح لامتداد خطأ | تأكد أن كل بورت مربوط بحساب SIP الصحيح |
| الصادر لا يتوزع | `database show gsm` على Asterisk CLI |
| صدى أو جودة سيئة | تحقق من قوة الإشارة GSM (≥ -85 dBm) |
| المكالمة تقطع بعد 30ث | تحقق من keepalive = 30 ثانية |
| CHANUNAVAIL في الصادر | البورت مش مسجل، الراوند روبن يتخطاه |

---

## بطاقة مرجعية سريعة

```
╔══════════════════════════════════════════════════════╗
║           DINSTAR UC2000-VE-8G — مرجع سريع          ║
╠══════════════════════════════════════════════════════╣
║  VPN Server:  157.173.125.136:51821/udp             ║
║  VPN Tunnel:  10.10.1.2 → 10.10.1.1                ║
║  Auth: SHA1 | Cipher: AES-256-CBC | TLS-Auth: dir 1 ║
╠══════════════════════════════════════════════════════╣
║  SIP Server:  10.10.1.1:51600 (UDP, عبر VPN)        ║
║  NAT:         معطّل (نفق VPN مباشر)                 ║
║  Codecs:      alaw > ulaw > gsm                     ║
║  DTMF:        RFC2833                                ║
╠══════════════════════════════════════════════════════╣
║  Port 1: gsm-port1 / Gsm1@Arwz2026 → Ext 7001     ║
║  Port 2: gsm-port2 / Gsm2@Arwz2026 → Ext 7002     ║
║  Port 3: gsm-port3 / Gsm3@Arwz2026 → Ext 7003     ║
║  Port 4: gsm-port4 / Gsm4@Arwz2026 → Ext 7004     ║
║  Port 5: gsm-port5 / Gsm5@Arwz2026 → Ext 7005     ║
║  Port 6: gsm-port6 / Gsm6@Arwz2026 → Ext 7006     ║
║  Port 7: gsm-port7 / Gsm7@Arwz2026 → Ext 7007     ║
║  Port 8: gsm-port8 / Gsm8@Arwz2026 → Ext 7008     ║
╠══════════════════════════════════════════════════════╣
║  الصادر: أي امتداد يتصل بـ 0XX.. → توزيع متساوي    ║
║  الوارد: مكالمة على بورت N → يرن امتداد 700N       ║
╚══════════════════════════════════════════════════════╝
```
