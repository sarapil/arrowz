# FreePBX Setup Guide for Arrowz

> دليل شامل لإعداد FreePBX للعمل مع نظام Arrowz WebRTC Softphone

---

## جدول المحتويات

1. [المتطلبات الأساسية](#المتطلبات-الأساسية)
2. [إعداد شهادة SSL/TLS](#إعداد-شهادة-ssltls)
3. [إعداد PJSIP WebSocket](#إعداد-pjsip-websocket)
4. [إعداد Extensions للـ WebRTC](#إعداد-extensions-للـ-webrtc)
5. [إعداد NAT و ICE](#إعداد-nat-و-ice)
6. [إعداد AMI (Asterisk Manager Interface)](#إعداد-ami)
7. [إعداد Firewall](#إعداد-firewall)
8. [إعدادات Asterisk المتقدمة](#إعدادات-asterisk-المتقدمة)
9. [اختبار الإعدادات](#اختبار-الإعدادات)
10. [استكشاف الأخطاء](#استكشاف-الأخطاء)

---

## المتطلبات الأساسية

### إصدارات مدعومة
| المكون | الإصدار الأدنى | الإصدار الموصى |
|--------|---------------|----------------|
| FreePBX | 15 | 16+ |
| Asterisk | 16 | 18+ |
| PJSIP | مُفعّل | مُفعّل |
| PHP | 7.4 | 8.1+ |

### المنافذ المطلوبة
| المنفذ | البروتوكول | الغرض |
|--------|-----------|-------|
| 8089 | TCP/WSS | WebSocket Secure (PJSIP) |
| 5061 | TCP/TLS | SIP over TLS |
| 5060 | UDP/TCP | SIP (اختياري) |
| 10000-20000 | UDP | RTP Media |
| 5038 | TCP | AMI |
| 443 | TCP | HTTPS |

---

## إعداد شهادة SSL/TLS

### الخيار 1: Let's Encrypt (موصى به)

```bash
# تثبيت certbot
yum install certbot -y

# الحصول على شهادة
certbot certonly --standalone -d pbx.yourdomain.com

# موقع الشهادات
# /etc/letsencrypt/live/pbx.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/pbx.yourdomain.com/privkey.pem
```

### الخيار 2: استخدام FreePBX Certificate Manager

1. **الوصول للوحة التحكم:**
   ```
   Admin → Certificate Management
   ```

2. **إنشاء شهادة جديدة:**
   - اضغط على `New Certificate`
   - اختر `Generate Let's Encrypt Certificate`
   - أدخل اسم الـ Domain: `pbx.yourdomain.com`
   - اضغط `Generate`

3. **تعيين الشهادة كافتراضية:**
   - اختر الشهادة الجديدة
   - اضغط على `Set as Default`

### نسخ الشهادات لـ Asterisk

```bash
# إنشاء مجلد الشهادات
mkdir -p /etc/asterisk/keys

# نسخ الشهادات
cp /etc/letsencrypt/live/pbx.yourdomain.com/fullchain.pem /etc/asterisk/keys/
cp /etc/letsencrypt/live/pbx.yourdomain.com/privkey.pem /etc/asterisk/keys/

# تعيين الصلاحيات
chown asterisk:asterisk /etc/asterisk/keys/*
chmod 600 /etc/asterisk/keys/*
```

---

## إعداد PJSIP WebSocket

### 1. تفعيل WebSocket في FreePBX

**المسار:** `Settings → Asterisk SIP Settings → PJSIP Settings`

#### إعدادات TLS/SSL:
| الإعداد | القيمة |
|---------|--------|
| Certificate Manager | اختر شهادتك |
| SSL Method | tlsv1_2 |
| Verify Client | No |
| Verify Server | No |

#### إعدادات Transport:

اضغط على `Add Transport` وأضف:

**Transport 1: WSS (WebSocket Secure)**
| الإعداد | القيمة |
|---------|--------|
| Transport Name | transport-wss |
| Protocol | wss |
| Bind | 0.0.0.0 |
| Port | 8089 |
| Certificate | اختر شهادتك |
| Local Networks | شبكاتك المحلية |
| External Address | عنوان IP العام أو FQDN |

**Transport 2: TLS (اختياري)**
| الإعداد | القيمة |
|---------|--------|
| Transport Name | transport-tls |
| Protocol | tls |
| Bind | 0.0.0.0 |
| Port | 5061 |
| Certificate | اختر شهادتك |

### 2. تحرير ملف pjsip.transports.conf

```bash
nano /etc/asterisk/pjsip.transports_custom.conf
```

أضف:

```ini
; WebSocket Secure Transport for WebRTC
[transport-wss]
type=transport
protocol=wss
bind=0.0.0.0:8089
cert_file=/etc/asterisk/keys/fullchain.pem
priv_key_file=/etc/asterisk/keys/privkey.pem
method=tlsv1_2
local_net=192.168.0.0/16
local_net=10.0.0.0/8
local_net=172.16.0.0/12
external_media_address=YOUR_PUBLIC_IP
external_signaling_address=YOUR_PUBLIC_IP
```

### 3. إعادة تحميل PJSIP

```bash
asterisk -rx "pjsip reload"
asterisk -rx "pjsip show transports"
```

---

## إعداد Extensions للـ WebRTC

### 1. إنشاء Extension جديد

**المسار:** `Applications → Extensions → Add Extension → Add New PJSIP Extension`

### 2. الإعدادات العامة (General)

| الإعداد | القيمة | الوصف |
|---------|--------|-------|
| User Extension | 1001 | رقم التحويلة |
| Display Name | John Doe | اسم العرض |
| Secret | كلمة مرور قوية | كلمة مرور SIP |

### 3. إعدادات Advanced (مهمة جداً)

| الإعداد | القيمة | الوصف |
|---------|--------|-------|
| Transport | 0-transport-wss | **مهم:** اختر WSS |
| DTLS Enable | Yes | **مطلوب لـ WebRTC** |
| DTLS Verify | Fingerprint | التحقق من البصمة |
| DTLS Setup | Actpass | Active/Passive |
| DTLS Certificate File | /etc/asterisk/keys/fullchain.pem | مسار الشهادة |
| DTLS CA File | /etc/asterisk/keys/fullchain.pem | مسار CA |
| DTLS Private Key | /etc/asterisk/keys/privkey.pem | مسار المفتاح |
| Media Encryption | DTLS | **مطلوب** |
| Media Use Received Transport | Yes | استخدام نفس الـ transport |
| *RTP Symmetric | Yes | للعمل خلف NAT |
| *Force RPort | Yes | للعمل خلف NAT |
| *Rewrite Contact | Yes | للعمل خلف NAT |
| ICE Support | Yes | **مطلوب لـ WebRTC** |
| *Trust RPID | Yes | الثقة بـ Remote Party ID |
| Send RPID | Yes | إرسال Remote Party ID |
| Max Contacts | 5 | عدد التسجيلات المتزامنة |
| *Qualify Frequency | 60 | فحص الاتصال كل 60 ثانية |

### 4. إعدادات Codecs

**المسار:** `Advanced → Codec Preferences`

قم بتفعيل الـ Codecs التالية بالترتيب:

| الترتيب | Codec | ملاحظات |
|---------|-------|---------|
| 1 | opus | **الأفضل لـ WebRTC** |
| 2 | g722 | HD Voice |
| 3 | ulaw | G.711 μ-law |
| 4 | alaw | G.711 A-law |

### 5. مثال على ملف PJSIP Endpoint

```bash
nano /etc/asterisk/pjsip.endpoint_custom.conf
```

```ini
; WebRTC Extension Template
[webrtc-endpoint](!)
type=endpoint
transport=transport-wss
context=from-internal
disallow=all
allow=opus
allow=g722
allow=ulaw
allow=alaw
webrtc=yes; WebRTC Extension Template
[webrtc-endpoint](!)
type=endpoint
transport=transport-wss
context=from-internal
disallow=all
allow=opus
allow=g722
allow=ulaw
allow=alaw
webrtc=yes
dtls_auto_generate_cert=yes
media_encryption=dtls
media_encryption_optimistic=no
ice_support=yes
use_avpf=yes
bundle=yes
max_audio_streams=1
max_video_streams=1
rtp_symmetric=yes
force_rport=yes
rewrite_contact=yes
direct_media=no
trust_id_inbound=yes
send_pai=yes
send_rpid=yes

; Extension 1001 (WebRTC)
[1001](webrtc-endpoint)
aors=1001
auth=1001-auth
callerid="John Doe" <1001>

[1001-auth]
type=auth
auth_type=userpass
username=1001
password=YourSecurePassword123!

[1001-aor]
type=aor
max_contacts=5
remove_existing=yes
qualify_frequency=60
dtls_auto_generate_cert=yes
media_encryption=dtls
media_encryption_optimistic=no
ice_support=yes
use_avpf=yes
bundle=yes
max_audio_streams=1
max_video_streams=1
rtp_symmetric=yes
force_rport=yes
rewrite_contact=yes
direct_media=no
trust_id_inbound=yes
send_pai=yes
send_rpid=yes

; Extension 1001 (WebRTC)
[1001](webrtc-endpoint)
aors=1001
auth=1001-auth
callerid="John Doe" <1001>

[1001-auth]
type=auth
auth_type=userpass
username=1001
password=YourSecurePassword123!

[1001-aor]
type=aor
max_contacts=5
remove_existing=yes
qualify_frequency=60
```

### 6. تطبيق الإعدادات

```bash
# إعادة تحميل الإعدادات
fwconsole reload

# أو من Asterisk CLI
asterisk -rx "pjsip reload"
asterisk -rx "dialplan reload"
```

---

## إعداد NAT و ICE

### 1. STUN/TURN Server

#### الخيار 1: استخدام STUN عام

للاختبار فقط، يمكن استخدام خوادم STUN العامة:

```
stun.l.google.com:19302
stun1.l.google.com:19302
stun2.l.google.com:19302
```

#### الخيار 2: تثبيت coturn (موصى به للإنتاج)

```bash
# تثبيت coturn
yum install coturn -y

# تحرير الإعدادات
nano /etc/turnserver.conf
```

**محتوى turnserver.conf:**

```ini
# Network Settings
listening-port=3478
tls-listening-port=5349
listening-ip=0.0.0.0
external-ip=YOUR_PUBLIC_IP

# Authentication
lt-cred-mech
user=arrowz:YourTurnPassword123

# Realm
realm=pbx.yourdomain.com

# TLS Certificates
cert=/etc/letsencrypt/live/pbx.yourdomain.com/fullchain.pem
pkey=/etc/letsencrypt/live/pbx.yourdomain.com/privkey.pem

# Logging
log-file=/var/log/turnserver.log
verbose

# Security
no-multicast-peers
no-cli
fingerprint
```

```bash
# تشغيل coturn
systemctl enable coturn
systemctl start coturn
```

### 2. إعداد RTP.conf

```bash
nano /etc/asterisk/rtp_custom.conf
```

```ini
[general]
rtpstart=10000
rtpend=20000
icesupport=yes
stunaddr=stun.l.google.com:19302
; أو خادم TURN الخاص بك
; turnaddr=turn.yourdomain.com:3478
; turnusername=arrowz
; turnpassword=YourTurnPassword123
```

### 3. إعدادات NAT في FreePBX

**المسار:** `Settings → Asterisk SIP Settings → General SIP Settings`

| الإعداد | القيمة |
|---------|--------|
| External Address | عنوان IP العام |
| Local Networks | 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12 |
| NAT | Yes |
| IP Configuration | Static IP أو Auto Configure |

---

## إعداد AMI

### 1. تفعيل AMI

**المسار:** `Settings → Advanced Settings`

| الإعداد | القيمة |
|---------|--------|
| Enable the ARI Framework | Yes |
| Asterisk Manager User Settings | Enabled |

### 2. إنشاء مستخدم AMI

```bash
nano /etc/asterisk/manager_custom.conf
```

```ini
[arrowz]
; AMI User for Arrowz Application
secret=YourAMISecurePassword123!
deny=0.0.0.0/0.0.0.0
permit=127.0.0.1/255.255.255.0
permit=192.168.1.0/255.255.255.0  ; شبكتك المحلية
read=system,call,log,verbose,command,agent,user,config,dtmf,reporting,cdr,dialplan,originate
write=system,call,log,verbose,command,agent,user,config,dtmf,reporting,cdr,dialplan,originate
writetimeout=5000
eventfilter=!Event: RTCPSent
eventfilter=!Event: RTCPReceived
eventfilter=!Event: VarSet
```

### 3. إعداد manager.conf

```bash
nano /etc/asterisk/manager.conf
```

تأكد من وجود:

```ini
[general]
enabled=yes
port=5038
bindaddr=0.0.0.0
displayconnects=yes
allowmultiplelogin=yes
webenabled=yes
httptimeout=60
```

### 4. إعادة تحميل AMI

```bash
asterisk -rx "manager reload"
asterisk -rx "manager show users"
```

### 5. اختبار اتصال AMI

```bash
# من نفس الخادم
telnet 127.0.0.1 5038

# ثم أدخل:
Action: Login
Username: arrowz
Secret: YourAMISecurePassword123!

# يجب أن يظهر:
# Response: Success
# Message: Authentication accepted
```

---

## إعداد Firewall

### 1. إعدادات iptables

```bash
# منفذ WebSocket
iptables -A INPUT -p tcp --dport 8089 -j ACCEPT

# منفذ SIP/TLS
iptables -A INPUT -p tcp --dport 5061 -j ACCEPT

# منفذ SIP (إذا لزم)
iptables -A INPUT -p udp --dport 5060 -j ACCEPT
iptables -A INPUT -p tcp --dport 5060 -j ACCEPT

# منفذ AMI (محدود للشبكة المحلية)
iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 5038 -j ACCEPT

# منافذ RTP
iptables -A INPUT -p udp --dport 10000:20000 -j ACCEPT

# منفذ TURN (إذا تم تثبيته)
iptables -A INPUT -p tcp --dport 3478 -j ACCEPT
iptables -A INPUT -p udp --dport 3478 -j ACCEPT
iptables -A INPUT -p tcp --dport 5349 -j ACCEPT

# حفظ القواعد
service iptables save
```

### 2. إعدادات firewalld (CentOS/RHEL 7+)

```bash
# WebSocket
firewall-cmd --permanent --add-port=8089/tcp

# SIP
firewall-cmd --permanent --add-port=5060/udp
firewall-cmd --permanent --add-port=5060/tcp
firewall-cmd --permanent --add-port=5061/tcp

# RTP
firewall-cmd --permanent --add-port=10000-20000/udp

# TURN
firewall-cmd --permanent --add-port=3478/tcp
firewall-cmd --permanent --add-port=3478/udp
firewall-cmd --permanent --add-port=5349/tcp

# تطبيق التغييرات
firewall-cmd --reload
```

### 3. إعدادات FreePBX Firewall Module

**المسار:** `Connectivity → Firewall`

1. تأكد من تفعيل `Responsive Firewall`
2. أضف عناوين IP موثوقة في `Trusted Zone`
3. تأكد من السماح بالخدمات:
   - WebRTC
   - SIP
   - AMI (للعناوين الموثوقة فقط)

---

## إعدادات Asterisk المتقدمة

### 1. http.conf (لـ WebSocket)

```bash
nano /etc/asterisk/http_custom.conf
```

```ini
[general]
enabled=yes
bindaddr=0.0.0.0
bindport=8088
tlsenable=yes
tlsbindaddr=0.0.0.0:8089
tlscertfile=/etc/asterisk/keys/fullchain.pem
tlsprivatekey=/etc/asterisk/keys/privkey.pem
tlscafile=/etc/asterisk/keys/fullchain.pem
```

### 2. pjsip.conf إعدادات عامة

```bash
nano /etc/asterisk/pjsip_custom.conf
```

```ini
[global]
type=global
max_forwards=70
keep_alive_interval=30
contact_expiration_check_interval=30
default_voicemail_extension=*97
unidentified_request_count=3
unidentified_request_period=5
unidentified_request_prune_interval=30
mwi_tps_queue_high=500
mwi_tps_queue_low=-1
mwi_disable_initial_unsolicited=no
send_contact_status_on_update_registration=yes
taskprocessor_overload_trigger=global
norefersub=yes
```

### 3. إعدادات Codec (codecs.conf)

```bash
nano /etc/asterisk/codecs_custom.conf
```

```ini
[opus]
type=opus
packet_loss=10
complexity=10
signal=voice
application=voip
max_playback_rate=48000
max_bandwidth=fullband
fec=yes
dtx=no
```

### 4. إعدادات musiconhold.conf

```bash
nano /etc/asterisk/musiconhold_custom.conf
```

```ini
[default]
mode=files
directory=/var/lib/asterisk/moh
format=ulaw,alaw,opus,wav
```

---

## اختبار الإعدادات

### 1. اختبار WebSocket

```bash
# من المتصفح (Developer Console)
var ws = new WebSocket('wss://pbx.yourdomain.com:8089/ws');
ws.onopen = function() { console.log('Connected!'); };
ws.onerror = function(e) { console.log('Error:', e); };
```

### 2. اختبار تسجيل Extension

```bash
# من Asterisk CLI
asterisk -rx "pjsip show endpoints"
asterisk -rx "pjsip show endpoint 1001"
asterisk -rx "pjsip show contacts"
asterisk -rx "pjsip show registrations"
```

### 3. اختبار AMI

```python
#!/usr/bin/env python3
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('127.0.0.1', 5038))

# Read banner
print(sock.recv(1024).decode())

# Login
sock.send(b"Action: Login\r\nUsername: arrowz\r\nSecret: YourAMISecurePassword123!\r\n\r\n")
print(sock.recv(1024).decode())

# Ping
sock.send(b"Action: Ping\r\n\r\n")
print(sock.recv(1024).decode())

sock.close()
```

### 4. اختبار مكالمة

```bash
# من Asterisk CLI - إجراء مكالمة اختبار
asterisk -rx "channel originate PJSIP/1001 extension 1002@from-internal"

# مراقبة المكالمات
asterisk -rx "core show channels"
```

### 5. اختبار Codecs

```bash
asterisk -rx "core show translation"
asterisk -rx "pjsip show endpoint 1001" | grep -i codec
```

---

## استكشاف الأخطاء

### مشكلة: WebSocket لا يتصل

**الأعراض:**
- خطأ `WebSocket connection failed`
- خطأ `SSL handshake failed`

**الحلول:**

1. **تأكد من صحة الشهادة:**
```bash
openssl s_client -connect pbx.yourdomain.com:8089 -servername pbx.yourdomain.com
```

2. **تأكد من تشغيل الـ transport:**
```bash
asterisk -rx "pjsip show transports"
```

3. **راجع ملفات السجل:**
```bash
tail -f /var/log/asterisk/full
```

---

### مشكلة: التسجيل يفشل

**الأعراض:**
- `Registration failed`
- `401 Unauthorized`

**الحلول:**

1. **تأكد من صحة كلمة المرور:**
```bash
asterisk -rx "pjsip show auth 1001-auth"
```

2. **تأكد من الـ Transport:**
```bash
asterisk -rx "pjsip show endpoint 1001" | grep transport
# يجب أن يظهر: transport-wss
```

3. **تفعيل debug:**
```bash
asterisk -rx "pjsip set logger on"
asterisk -rx "pjsip set logger verbose on"
```

---

### مشكلة: لا يوجد صوت (One-way audio)

**الأعراض:**
- المكالمة تتصل لكن بدون صوت
- صوت من اتجاه واحد فقط

**الحلول:**

1. **تأكد من إعدادات NAT:**
```bash
asterisk -rx "pjsip show endpoint 1001" | grep -E "rtp_symmetric|force_rport|rewrite_contact"
```

2. **تأكد من منافذ RTP مفتوحة:**
```bash
netstat -ulnp | grep asterisk
```

3. **تأكد من ICE:**
```bash
asterisk -rx "pjsip show endpoint 1001" | grep ice
```

4. **تأكد من STUN/TURN:**
```bash
asterisk -rx "rtp show settings"
```

---

### مشكلة: RTCP-MUX is not enabled when it is required

**الأعراض:**
- خطأ في console المتصفح: `Failed to execute 'setRemoteDescription' on 'RTCPeerConnection': RTCP-MUX is not enabled when it is required`
- المكالمة تفشل عند محاولة الرد
- WebRTC لا يستطيع إنشاء اتصال

**السبب:**
متصفحات الويب الحديثة (Chrome 75+, Firefox 68+) تتطلب RTCP-MUX إجبارياً. إذا لم يكن Asterisk/FreePBX مُعداً لإرسال `rtcp-mux` في SDP، سيفشل الاتصال.

**الحل:**

1. **تفعيل RTCP-MUX في FreePBX:**

   **عبر واجهة الويب:**
   - اذهب إلى `Settings → Asterisk SIP Settings → PJSIP Settings → Advanced`
   - ابحث عن `RTCP MUX` وفعّله على `Yes`
   - اضغط `Submit` ثم `Apply Config`

2. **تعديل إعدادات PJSIP يدوياً:**

   ```bash
   # تعديل ملف الإعدادات
   nano /etc/asterisk/pjsip_endpoint_custom.conf
   ```

   أضف التالي للـ endpoint template:
   ```ini
   [webrtc-endpoint](!)
   rtcp_mux=yes
   ```

3. **للـ Extensions الموجودة:**

   ```bash
   # تأكد من الإعداد الحالي
   asterisk -rx "pjsip show endpoint 1001" | grep rtcp_mux
   
   # إذا كان الناتج فارغ أو rtcp_mux=no، تحتاج لتفعيله
   ```

4. **إضافة rtcp_mux لجميع extensions:**

   أنشئ ملف `/etc/asterisk/pjsip_endpoint_custom_post.conf`:
   ```ini
   ; Force RTCP-MUX for all WebRTC endpoints
   [webrtc-addon](!)
   rtcp_mux=yes
   bundle=yes
   max_audio_streams=1
   ```

5. **إعادة تحميل PJSIP:**
   ```bash
   asterisk -rx "module reload res_pjsip.so"
   asterisk -rx "pjsip reload"
   ```

6. **التحقق من التفعيل:**
   ```bash
   asterisk -rx "pjsip show endpoint 1001" | grep rtcp_mux
   # يجب أن يظهر: rtcp_mux : true
   ```

**ملاحظة هامة:** تأكد من أن الـ Extension يستخدم template يحتوي على `rtcp_mux=yes`. في FreePBX 16+، يمكنك تعيين هذا من خلال:
- `Applications → Extensions → [Extension] → Advanced → RTCP Mux`

---

### مشكلة: Called with SDP without DTLS fingerprint

**الأعراض:**
- خطأ في console: `Failed to set remote offer sdp: Called with SDP without DTLS fingerprint`
- المكالمة ترسل `488 Not Acceptable Here`
- SDP الوارد يستخدم `RTP/AVP` بدلاً من `UDP/TLS/RTP/SAVP`

**السبب:**
الـ Extension في FreePBX غير مُعد للـ WebRTC بشكل صحيح. متصفحات الويب تتطلب DTLS-SRTP للتشفير.

**التشخيص:**
```bash
# تحقق من إعدادات الـ Extension
asterisk -rx "pjsip show endpoint 2211" | grep -E "dtls|media_encryption|webrtc|ice"

# يجب أن ترى:
# dtls_auto_generate_cert : yes
# dtls_setup            : actpass
# media_encryption      : dtls
# ice_support           : yes
# webrtc               : yes
```

**الحل:**

1. **في FreePBX GUI:**
   
   اذهب إلى `Applications → Extensions → [رقم الامتداد] → Advanced`
   
   | الإعداد | القيمة |
   |---------|--------|
   | Transport | 0-transport-wss |
   | DTLS Enable | Yes |
   | DTLS Verify | Fingerprint |
   | DTLS Setup | Actpass |
   | DTLS Auto Generate Certificate | Yes |
   | Media Encryption | DTLS |
   | ICE Support | Yes |
   | AVPF | Yes |
   | WebRTC | Yes |
   | RTCP Mux | Yes |
   | Bundle | Yes |

2. **أو عبر ملف الإعدادات:**
   
   ```bash
   nano /etc/asterisk/pjsip.endpoint_custom_post.conf
   ```
   
   أضف:
   ```ini
   ; WebRTC Settings for Extension 2211
   [2211](+)
   transport=transport-wss
   dtls_auto_generate_cert=yes
   dtls_setup=actpass
   media_encryption=dtls
   ice_support=yes
   use_avpf=yes
   webrtc=yes
   rtcp_mux=yes
   bundle=yes
   max_audio_streams=1
   force_rport=yes
   rewrite_contact=yes
   rtp_symmetric=yes
   ```

3. **تأكد من وجود الشهادات:**
   ```bash
   ls -la /etc/asterisk/keys/
   # يجب أن ترى: fullchain.pem, privkey.pem
   
   # أو استخدم auto-generate
   asterisk -rx "pjsip show endpoint 2211" | grep dtls_auto
   ```

4. **إعادة تحميل الإعدادات:**
   ```bash
   asterisk -rx "dialplan reload"
   asterisk -rx "pjsip reload"
   fwconsole reload
   ```

5. **التحقق من SDP:**
   بعد التعديل، يجب أن يحتوي SDP على:
   - `UDP/TLS/RTP/SAVP` أو `UDP/TLS/RTP/SAVPF` (بدلاً من RTP/AVP)
   - `a=fingerprint:SHA-256 xx:xx:xx:...`
   - `a=setup:actpass`
   - `a=ice-ufrag:...`
   - `a=ice-pwd:...`

---

### مشكلة: Codec غير مدعوم

**الأعراض:**
- `No common codec found`
- جودة صوت سيئة

**الحلول:**

1. **تأكد من Codecs المفعلة:**
```bash
asterisk -rx "pjsip show endpoint 1001" | grep allow
```

2. **تأكد من وجود Opus:**
```bash
asterisk -rx "core show codecs audio"
```

3. **ثبت codec_opus إذا لزم:**
```bash
yum install asterisk-opus
fwconsole reload
```

---

### مشكلة: AMI لا يتصل

**الأعراض:**
- `Connection refused`
- `Authentication failed`

**الحلول:**

1. **تأكد من تشغيل AMI:**
```bash
netstat -tlnp | grep 5038
```

2. **تأكد من صلاحيات المستخدم:**
```bash
asterisk -rx "manager show user arrowz"
```

3. **تأكد من إعدادات permit/deny:**
```bash
cat /etc/asterisk/manager_custom.conf
```

---

## ملخص الإعدادات لنسخها إلى Arrowz

بعد إكمال جميع الإعدادات، قم بإدخال البيانات التالية في Arrowz:

### AZ Server Config

| الإعداد | القيمة |
|---------|--------|
| PBX Host | pbx.yourdomain.com |
| WebSocket URL | wss://pbx.yourdomain.com:8089/ws |
| AMI Port | 5038 |
| AMI Username | arrowz |
| AMI Password | YourAMISecurePassword123! |

### JsSIP Configuration (في softphone)

```javascript
{
    uri: 'sip:1001@pbx.yourdomain.com',
    password: 'ExtensionPassword',
    ws_servers: 'wss://pbx.yourdomain.com:8089/ws',
    display_name: 'John Doe',
    register: true,
    session_timers: false,
    use_preloaded_route: false,
    pcConfig: {
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            // أو خادم TURN الخاص بك
            // { 
            //     urls: 'turn:turn.yourdomain.com:3478',
            //     username: 'arrowz',
            //     credential: 'YourTurnPassword123'
            // }
        ]
    }
}
```

---

## قائمة فحص ما قبل الإنتاج

- [ ] شهادة SSL صالحة ومثبتة
- [ ] WebSocket Transport (WSS) على منفذ 8089
- [ ] PJSIP Extensions مع إعدادات WebRTC صحيحة
- [ ] DTLS مُفعّل للتشفير
- [ ] ICE Support مُفعّل
- [ ] Opus Codec مثبت ومُفعّل
- [ ] AMI مُفعّل مع مستخدم آمن
- [ ] منافذ Firewall مفتوحة
- [ ] NAT settings صحيحة
- [ ] STUN/TURN server مُعد
- [ ] اختبار مكالمة ناجح
- [ ] اختبار WebSocket ناجح
- [ ] اختبار AMI ناجح

---

## المراجع

- [Asterisk WebRTC Documentation](https://wiki.asterisk.org/wiki/display/AST/WebRTC)
- [FreePBX Wiki](https://wiki.freepbx.org/)
- [JsSIP Documentation](https://jssip.net/documentation/)
- [PJSIP Documentation](https://www.pjsip.org/pjsip/docs/html/)
