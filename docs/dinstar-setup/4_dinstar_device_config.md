# Dinstar UC2000-VE-8G — دليل إعداد الجهاز (مبني على الدليل الرسمي)

> **مرجع**: Dinstar UC2000-VE/F/G User Manual V3.3 (76 صفحة)  
> **رابط المانيوال الرسمي**: https://www.manualslib.com/manual/3139164/Dinstar-Uc2000-Ve.html

---

## نظرة عامة على المعمارية (تسجيل فردي لكل بورت عبر VPN)

```
  مكتب مصر                               VPS (157.173.125.136)
┌─────────────────────┐                 ┌──────────────────────────────────┐
│                     │                 │  FreePBX Container               │
│  ┌────────────────┐ │                 │                                  │
│  │ Dinstar        │ │   OpenVPN TLS   │  ┌────────────────────┐          │
│  │ UC2000-VE-8G   │═╪═══(UDP 51821)══╪══│ OpenVPN TLS Server │          │
│  │                │ │   tls-auth      │  │ tun1: 10.10.1.1    │          │
│  │ tun: 10.10.1.2 │ │                 │  └─────────┬──────────┘          │
│  │                │ │                 │            │                      │
│  │ Port 1: gsm-port1 ─────────────────▶ Asterisk PJSIP (51600/udp)    │
│  │ Port 2: gsm-port2 ─────────────────▶   8 endpoints: gsm-port1..8   │
│  │ ...             │ │                 │   8 extensions: 7001-7008     │
│  │ Port 8: gsm-port8 ─────────────────▶                                │
│  │                │ │                 │  Inbound:  port N → ext 700N   │
│  │ 8× SIM Cards  │ │                 │  Outbound: round-robin all     │
│  └────────────────┘ │                 └──────────────────────────────────┘
└─────────────────────┘
```

## جدول ربط البورتات بالإكستنشنات

| GSM Port | SIP Username | Password | Extension | الغرض |
|----------|-------------|----------|-----------|-------|
| Port 1 | `gsm-port1` | `Gsm1@Arwz2026` | 7001 | SIM 1 |
| Port 2 | `gsm-port2` | `Gsm2@Arwz2026` | 7002 | SIM 2 |
| Port 3 | `gsm-port3` | `Gsm3@Arwz2026` | 7003 | SIM 3 |
| Port 4 | `gsm-port4` | `Gsm4@Arwz2026` | 7004 | SIM 4 |
| Port 5 | `gsm-port5` | `Gsm5@Arwz2026` | 7005 | SIM 5 |
| Port 6 | `gsm-port6` | `Gsm6@Arwz2026` | 7006 | SIM 6 |
| Port 7 | `gsm-port7` | `Gsm7@Arwz2026` | 7007 | SIM 7 |
| Port 8 | `gsm-port8` | `Gsm8@Arwz2026` | 7008 | SIM 8 |

**SIP Server**: `10.10.1.1` (عبر الـ VPN)  
**SIP Port**: `51600` (UDP)

---

## الخطوة 1: الدخول لواجهة الويب

1. وصّل كابل إيثرنت من الكمبيوتر إلى بورت LAN في الجهاز
2. الـ IP الافتراضي: `192.168.11.1`
3. افتح المتصفح على: `http://192.168.11.1`
4. الدخول الافتراضي: `admin` / `admin`

> ⚠️ **غيّر كلمة السر فوراً** من: **Tools → Username and Password** (القسم 4.11.6 في المانيوال)

---

## الخطوة 2: إعداد الشبكة (Network Configuration)

### المسار في القائمة: `Network Configuration → Local Network`
> (القسم 4.5.1 في المانيوال — صفحة 31)

| الحقل | القيمة | ملاحظة |
|-------|--------|--------|
| **Use the Following IP Address** | مفعّل ✅ | عشان يبقى Static مش DHCP |
| **IP Address** | `192.168.x.50` | حسب شبكتك المحلية |
| **Subnet Mask** | `255.255.255.0` | حسب الشبكة |
| **Default Gateway** | `192.168.x.1` | الراوتر بتاعك |
| **Use the Following DNS Server Addresses** | مفعّل ✅ | |
| **Primary DNS Server** | `8.8.8.8` | أو DNS محلي |
| **Secondary DNS Server** | `8.8.4.4` | احتياطي |

> ⚠️ **مهم**: لازم يبقى Static IP. لو DHCP ممكن الـ IP يتغير والـ VPN ينقطع.

اضغط **Save** بعد التعديل.

---

## الخطوة 3: إعداد OpenVPN

### المسار في القائمة: `Network Configuration → VPN Parameter`
> (القسم 4.5.3 في المانيوال — صفحة 34)

الـ UC2000-VE بيدعم OpenVPN فقط من خلال ملف `.ovpn` — الواجهة فيها 3 حقول بس:

| الحقل | القيمة | الوصف |
|-------|--------|-------|
| **VPN TYPE** | `OpenVPN` | النوع الوحيد المدعوم |
| **OpenVPN Enable** | ✅ (علامة صح) | تفعيل الـ VPN |
| **.ovpn file** | اختر ملف `dinstar-tls.ovpn` | رفع ملف الإعداد |

### طريقة تحضير ملف الـ .ovpn:

1. **نزّل الملف من السيرفر** على جهازك:
   ```bash
   scp -P 1352 root@157.173.125.136:/opt/proj/initpbx/vpn-clients/dinstar-tls.ovpn .
   ```

2. **ارفع الملف** في حقل `.ovpn file` واضغط **Save**

3. **فعّل** علامة الصح على **OpenVPN Enable** واضغط **Save**

### بعد التفعيل:
- استنى 10-30 ثانية للاتصال
- روح **System Information** (القسم 4.3.1) — هتلاقي حالة الـ VPN
- المفروض الجهاز ياخد IP: `10.10.1.2`
- دلوقتي يقدر يوصل FreePBX على: `10.10.1.1`

### التحقق من السيرفر:
```bash
# شوف لو الدينستار متوصل
docker exec initpbx-freepbx-1 tail -10 /var/log/openvpn-dinstar-tls.log

# Ping الدينستار عبر VPN
docker exec initpbx-freepbx-1 ping -c 3 10.10.1.2
```

> ⚠️ **مهم جداً**: الملف `.ovpn` معمول بإعدادات خاصة:
> - **Auth**: `SHA1` (مش SHA256) — عشان OpenVPN 2.3.6 اللي في الدينستار
> - **Cipher**: `AES-256-CBC`
> - **TLS Auth**: مفعّل بـ direction `1` (client)
> - **compat-mode**: 2.3.0
> 
> كل ده موجود جاهز في الملف، مش محتاج تعدل حاجة يدوياً.

---

## الخطوة 4: إعداد SIP — التسجيل في FreePBX

### 4أ. إعداد SIP Server الرئيسي

### المسار في القائمة: `Call Configuration → SIP Configuration`
> (القسم 4.8.1 في المانيوال — صفحة 58-69)

في الجزء العلوي من الصفحة هتلاقي إعدادات السيرفر:

| الحقل | القيمة | ملاحظة |
|-------|--------|--------|
| **SIP Server Address** | `10.10.1.1` | IP الـ FreePBX عبر VPN |
| **Port** | `51600` | بورت PJSIP المخصص |
| **Outbound Proxy** | فاضي (اتركه فارغ) | مش محتاج — VPN مباشر |
| **Check NET Status** | `No` | |
| **Register Interval** | `120` | ثانية |
| **DNS query type** | `A` | |
| **SIP Timer T1** | `500` (الافتراضي) | |
| **Keepalive Interval** | `30` | ثانية — للحفاظ على الاتصال |
| **Keepalive Retry Count** | `3` | |

#### إعدادات Local SIP Port:
| الحقل | القيمة |
|-------|--------|
| **Local SIP Port** | `Use the same SIP port` أو `5060` | |

#### Response Codes (اتركها افتراضية):
لا تحتاج تغيير — الإعدادات الافتراضية شغالة مع FreePBX.

اضغط **Save** بعد كل تعديل.

---

### 4ب. إعداد Port Configuration (حساب SIP لكل بورت)

### المسار في القائمة: `Call Configuration → Port Configuration`
> (القسم 4.8.4 في المانيوال — صفحة 72-74)

**هنا المكان الأساسي** — كل بورت GSM بيتسجل كحساب SIP مستقل.

#### الحقل المهم أولاً:

| الحقل | القيمة | ملاحظة |
|-------|--------|--------|
| **ALL ports register used same user ID** | **No** ❌ | ★★★ مهم جداً — لازم `No` عشان كل بورت يبقى مستقل |

#### إعداد كل بورت:

هتلاقي جدول فيه كل البورتات (Port 1 - Port 8). لكل بورت عدّل الحقول التالية:

##### **Port 1:**
| الحقل | القيمة |
|-------|--------|
| **SIP User ID** | `gsm-port1` |
| **Authenticate ID** | `gsm-port1` |
| **Authenticate Password** | `Gsm1@Arwz2026` |
| **Register to** | SIP Server 1 (الأساسي) |

##### **Port 2:**
| الحقل | القيمة |
|-------|--------|
| **SIP User ID** | `gsm-port2` |
| **Authenticate ID** | `gsm-port2` |
| **Authenticate Password** | `Gsm2@Arwz2026` |
| **Register to** | SIP Server 1 |

##### **Port 3:**
| الحقل | القيمة |
|-------|--------|
| **SIP User ID** | `gsm-port3` |
| **Authenticate ID** | `gsm-port3` |
| **Authenticate Password** | `Gsm3@Arwz2026` |
| **Register to** | SIP Server 1 |

##### **Port 4:**
| الحقل | القيمة |
|-------|--------|
| **SIP User ID** | `gsm-port4` |
| **Authenticate ID** | `gsm-port4` |
| **Authenticate Password** | `Gsm4@Arwz2026` |
| **Register to** | SIP Server 1 |

##### **Port 5:**
| الحقل | القيمة |
|-------|--------|
| **SIP User ID** | `gsm-port5` |
| **Authenticate ID** | `gsm-port5` |
| **Authenticate Password** | `Gsm5@Arwz2026` |
| **Register to** | SIP Server 1 |

##### **Port 6:**
| الحقل | القيمة |
|-------|--------|
| **SIP User ID** | `gsm-port6` |
| **Authenticate ID** | `gsm-port6` |
| **Authenticate Password** | `Gsm6@Arwz2026` |
| **Register to** | SIP Server 1 |

##### **Port 7:**
| الحقل | القيمة |
|-------|--------|
| **SIP User ID** | `gsm-port7` |
| **Authenticate ID** | `gsm-port7` |
| **Authenticate Password** | `Gsm7@Arwz2026` |
| **Register to** | SIP Server 1 |

##### **Port 8:**
| الحقل | القيمة |
|-------|--------|
| **SIP User ID** | `gsm-port8` |
| **Authenticate ID** | `gsm-port8` |
| **Authenticate Password** | `Gsm8@Arwz2026` |
| **Register to** | SIP Server 1 |

#### إعدادات إضافية لكل بورت (اختيارية):
| الحقل | القيمة | ملاحظة |
|-------|--------|--------|
| **Tx Gain** | `0` dB (افتراضي) | مستوى الصوت لجهة GSM |
| **Rx Gain** | `0` dB (افتراضي) | مستوى الصوت لجهة IP |
| **To VoIP Hotline** | فاضي | الدايلبلان في FreePBX بيتعامل مع التوجيه |
| **To PSTN Hotline** | فاضي | |

اضغط **Save** بعد إعداد كل البورتات.

---

## الخطوة 5: إعداد SIP Trunk

### المسار في القائمة: `Call Configuration → SIP Trunk Configuration`
> (القسم 4.8.2 في المانيوال — صفحة 69-71)

**أضف Trunk واحد** لسيرفر FreePBX:

| الحقل | القيمة | ملاحظة |
|-------|--------|--------|
| **SIP Trunk Index** | `0` | أول trunk |
| **Description** | `FreePBX-VPN` | اسم للتعريف |
| **IP** | `10.10.1.1` | IP الـ FreePBX عبر VPN |
| **Port** | `51600` | بورت PJSIP |
| **Keep alive** | `Yes` | للحفاظ على الاتصال |
| **SIP/RTP Encryption** | `No` | مش محتاج — VPN مشفّر أصلاً |

اضغط **Add** ثم **Save**.

---

## الخطوة 6: إعداد Routing (التوجيه)

### 6أ. IP→Tel Routing (المكالمات من FreePBX → GSM)

### المسار في القائمة: `Call Configuration → IP->Tel Routing`
> (القسم 4.8.5 في المانيوال — صفحة 73)

اضغط **Add** لإضافة قاعدة:

| الحقل | القيمة | ملاحظة |
|-------|--------|--------|
| **Source** | SIP Trunk `0` (FreePBX-VPN) | المكالمات الواردة من FreePBX |
| **Destination** | `Port Group` أو البورت المناسب | أو All Ports |
| **Call Restriction** | `Allow` | السماح بالمكالمات |
| **Source Prefix** | `Any` | أي رقم متصل |
| **Destination Prefix** | `x.` | أي رقم مطلوب |
| **Prefix to add** | فاضي | |
| **Digits to be deleted** | `0` | لا تحذف أرقام |

> 💡 **ملاحظة مهمة**: التوجيه الفعلي (أي بورت يستخدم) بيتحكم فيه الـ Asterisk.  
> لما Asterisk يرسل INVITE لـ `gsm-port3`، المكالمة بتوصل على account `gsm-port3`  
> والدينستار بيربطها بـ Port 3 تلقائياً لأن كل بورت مسجّل بحساب مختلف.

### 6ب. Tel→IP Routing (المكالمات من GSM → FreePBX)

### المسار في القائمة: `Call Configuration → Tel->IP Routing`
> (القسم 4.8.8 في المانيوال — صفحة 79)

اضغط **Add** لإضافة قاعدة:

| الحقل | القيمة | ملاحظة |
|-------|--------|--------|
| **Source** | `All Ports` أو Port Group | كل بورتات GSM |
| **Destination** | SIP Trunk `0` (FreePBX-VPN) | أرسل لـ FreePBX |
| **Call Restriction** | `Allow` | السماح |
| **Source Prefix** | `Any` | أي رقم متصل |
| **Destination Prefix** | `x.` | أي رقم مطلوب |
| **Prefix to add** | فاضي | |
| **Digits to be deleted** | `0` | |

> 💡 **كيف بيشتغل**: لما حد يتصل بـ SIM في Port 3، الدينستار بيرسل المكالمة لـ FreePBX  
> باستخدام حساب `gsm-port3`. الـ Asterisk بيعرف إن المكالمة جاية من Port 3  
> فيرسلها لإكستنشن 7003.

---

## الخطوة 7: إعداد Service Parameter

### المسار في القائمة: `Call Configuration → Service Parameter`
> (القسم 4.8.10 في المانيوال — صفحة 81)

| الحقل | القيمة | ملاحظة |
|-------|--------|--------|
| **IP to PSTN One Stage Dialing** | `Yes` ✅ | مهم — مكالمة مباشرة بدون IVR |
| **NAT Traversal** | `Disable` | ★ مش محتاج — VPN مباشر بدون NAT |
| **RTP Detect** | `90` ثانية (افتراضي) | يقطع المكالمة لو مفيش RTP |
| **Play Voice Prompt for PSTN Incoming Calls** | `No` | مش محتاج IVR |
| **Enable Auto Outgoing Routing** | `No` | الـ round-robin بيتعامل معاه Asterisk |

---

## الخطوة 8: إعداد Media Parameter

### المسار في القائمة: `Call Configuration → Media Parameter`
> (القسم 4.8.11 في المانيوال — صفحة 84)

### Codecs (الأولوية):

| الأولوية | الكودك | ملاحظة |
|---------|--------|--------|
| 1 | **PCMA (G.711A/alaw)** | ★ الأفضل — بدون تحويل |
| 2 | **PCMU (G.711U/ulaw)** | احتياطي |
| 3 | **GSM** | آخر خيار |

> 💡 **ليه alaw أولاً؟** الدينستار بيحول GSM → PCM داخلياً.  
> استخدام alaw يعني إن Asterisk مش هيحتاج يعمل transcoding = جودة أعلى + CPU أقل.

### إعدادات إضافية:
| الحقل | القيمة |
|-------|--------|
| **DTMF Mode** | `RFC2833` |
| **DTMF Payload** | `101` (افتراضي) |

---

## الخطوة 9: فحص الـ SIM Cards

### المسار في القائمة: `System Information → Mobile Information`
> (القسم 4.3.2 في المانيوال — صفحة 23)

لكل بورت تحقق من:
| الحقل | القيمة المتوقعة |
|-------|----------------|
| **Type** | GSM |
| **IMSI** | رقم مكون من 15 خانة |
| **Signal** | ≥ -85 dBm (جيد) |
| **SIM Status** | Ready ✅ |
| **GSM Status** | Registered ✅ |

> ⚠️ لو SIM مش Ready:
> 1. تحقق من تركيب الـ SIM صح (ادفع لحد ما تسمع كليك)
> 2. استنى 30 ثانية للتسجيل في الشبكة
> 3. تحقق إن الـ PIN معطّل أو أدخله من: **Mobile Configuration → IMEI** (القسم 4.6.4)

---

## الخطوة 10: التحقق من التسجيل

### على الدينستار:

### المسار في القائمة: `System Information → SIP Information`
> (القسم 4.3.3 في المانيوال — صفحة 24)

كل بورت المفروض يكون: **Registered** ✅

لو "Trying" أو "Failed":
1. تحقق إن الـ VPN متوصل (الخطوة 3)
2. تحقق إن SIP Server = `10.10.1.1` وPort = `51600`
3. تحقق إن الـ username/password مطابقين بالضبط
4. تحقق إن **ALL ports register used same user ID** = **No**

### على Asterisk CLI:
```bash
# شوف كل الـ contacts المسجلين
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show contacts"
# المفروض تلاقي 8 contacts:
#   gsm-port1/sip:gsm-port1@10.10.1.2:XXXX
#   gsm-port2/sip:gsm-port2@10.10.1.2:XXXX
#   ... (واحد لكل بورت)

# شوف endpoint معين
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show endpoint gsm-port1"

# شوف كل الـ GSM endpoints مرة واحدة
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show endpoints" | grep gsm

# شوف حالة تسجيل الـ AOR
docker exec initpbx-freepbx-1 asterisk -rx "pjsip show aors" | grep gsm
```

---

## الخطوة 11: اختبار المكالمات

### اختبار Inbound (GSM → Extension):
1. اتصل برقم الـ SIM في **Port 1** من موبايل
2. المفروض يرن إكستنشن **7001**
3. رد من ARKAN PHONE أو أي هاتف IP
4. كرر لكل بورت — تأكد إن الإكستنشن الصح بيرن

### اختبار Outbound (Extension → GSM):
1. من أي إكستنشن (مثلاً 2210)، اطلب `01XXXXXXXXX` (رقم موبايل يبدأ بـ 0)
2. المكالمة هتروح عبر `gsm-outbound` بنظام round-robin
3. شوف أي بورت اتستخدم من الـ logs
4. اعمل عدة مكالمات — تأكد إنها بتتوزع على بورتات مختلفة

### اختبار Round-Robin:
```bash
# شوف الـ counter الحالي
docker exec initpbx-freepbx-1 asterisk -rx "database show gsm"
# المفروض يطلع: /gsm/rr : N (حيث N من 1-8، البورت الجاي)
```

---

## حل المشاكل (Troubleshooting)

| المشكلة | الحل |
|---------|------|
| VPN مش بيتوصل | تحقق من الـ firewall، بورت 51821/UDP مفتوح؟ شوف لوجات: `System Information` |
| VPN بيتوصل ثم ينقطع | تحقق من الساعة على الجهاز (الشهادات حساسة للوقت) |
| SIP registration فشل | تحقق من VPN أولاً، ثم SIP server/port/credentials |
| بعض البورتات بس مسجلة | تحقق من إعداد كل بورت في **Call Configuration → Port Configuration** |
| صوت في اتجاه واحد | تحقق إن **NAT Traversal** = `Disable` في **Service Parameter** |
| مفيش صوت خالص | تحقق إن VPN متوصل، شوف RTP ports |
| المكالمة الواردة بتروح لإكستنشن غلط | تحقق إن كل بورت له الـ **SIP User ID** الصح في **Port Configuration** |
| المكالمات الصادرة مش بتتوزع | شوف `database show gsm` في Asterisk CLI |
| Echo أو جودة سيئة | شوف قوة إشارة GSM (≥ -85 dBm) في **System Information → Mobile Information** |
| المكالمة بتنقطع بعد 30 ثانية | تحقق من **Keepalive Interval** = `30` في **SIP Configuration** |
| CHANUNAVAIL في المكالمات الصادرة | البورت ده مش مسجل — الـ round-robin بيتخطاه |

---

## خريطة القوائم الكاملة (الأسماء الصحيحة)

### القوائم الرئيسية في واجهة الويب:

```
UC2000-VE Web Interface
├── System Information          (القسم 4.3)
│   ├── System Information      (4.3.1) — معلومات عامة + حالة VPN
│   ├── Mobile Information      (4.3.2) — حالة SIM + إشارة GSM
│   └── SIP Information         (4.3.3) — حالة تسجيل SIP لكل بورت
│
├── Statistics                  (القسم 4.4)
│   ├── TCP/UDP                 (4.4.1)
│   ├── RTP                     (4.4.2)
│   ├── SIP Call History        (4.4.3)
│   ├── IP to GSM Call History  (4.4.4)
│   ├── CDR Report              (4.4.5)
│   ├── Lock BCCH Report        (4.4.6)
│   ├── Current Call Status     (4.4.7)
│   ├── DBO State               (4.4.8)
│   └── GSM Event               (4.4.9)
│
├── Network Configuration       (القسم 4.5)
│   ├── Local Network           (4.5.1) — ★ إعداد IP
│   ├── ARP                     (4.5.2)
│   ├── VPN Parameter           (4.5.3) — ★ إعداد OpenVPN
│   └── Access Rules            (4.5.4)
│
├── Mobile Configuration        (القسم 4.6)
│   ├── Basic Configuration     (4.6.1)
│   ├── Mobile Configuration    (4.6.2)
│   ├── Phone Number Config     (4.6.3)
│   ├── IMEI                    (4.6.4)
│   ├── Operator                (4.6.5)
│   ├── Operator Configuration  (4.6.6)
│   ├── BCCH                    (4.6.7)
│   ├── Call Forwarding         (4.6.8)
│   ├── Call Waiting            (4.6.9)
│   ├── Cloud Server            (4.6.10)
│   ├── MBN Config              (4.6.11)
│   └── Call Conference         (4.6.12)
│
├── SMS and USSD                (القسم 4.7)
│   ├── SMS Send Overview       (4.7.1)
│   ├── SMS Send Limit Settings (4.7.2)
│   ├── SMS Routing             (4.7.3)
│   ├── SMSC Switch Setting     (4.7.4)
│   ├── Send SMS                (4.7.5)
│   ├── SMS Outbox              (4.7.6)
│   ├── SMS Inbox               (4.7.7)
│   ├── USSD                    (4.7.8)
│   └── SMS Settings            (4.7.9)
│
├── Call Configuration          (القسم 4.8) — ★★★ القسم الأهم
│   ├── SIP Configuration       (4.8.1) — ★ إعداد SIP Server
│   ├── SIP Trunk Configuration (4.8.2) — ★ إعداد Trunk
│   ├── SIP Trunk Group Config  (4.8.3)
│   ├── Port Configuration      (4.8.4) — ★★★ حساب SIP لكل بورت
│   ├── IP->Tel Routing         (4.8.5) — ★ توجيه الصادر
│   ├── IP->Tel Caller Manip.   (4.8.6)
│   ├── IP->Tel Called Manip.   (4.8.7)
│   ├── Tel->IP Routing         (4.8.8) — ★ توجيه الوارد
│   ├── Tel->IP Caller Manip.   (4.8.9)
│   ├── Service Parameter       (4.8.10) — ★ إعدادات الخدمة
│   ├── Media Parameter         (4.8.11) — ★ Codecs + DTMF
│   └── DBO Parameter           (4.8.12)
│
├── Advanced                    (القسم 4.9)
│   ├── Basic Configuration     (4.9.2)
│   ├── Phone Number Learning   (4.9.3)
│   ├── Balance Check           (4.9.4)
│   ├── Billing Setting         (4.9.5)
│   ├── Call Limit              (4.9.6)
│   ├── Exception Event Handling(4.9.7)
│   └── Auto Generation        (4.9.8)
│
├── Diagnostic                  (القسم 4.10)
│   ├── Syslog                  (4.10.1)
│   ├── Filelog                 (4.10.2)
│   ├── Summary                 (4.10.3)
│   ├── SIM Card Debug          (4.10.4)
│   ├── Ping Test               (4.10.5)
│   ├── Tracert Test            (4.10.6)
│   ├── Network Capture         (4.10.7)
│   ├── Mobile Network Test     (4.10.9)
│   ├── Module Recovery         (4.10.10)
│   ├── Module Log              (4.10.11)
│   └── Web Operation Log       (4.10.12)
│
└── Tools                       (القسم 4.11)
    ├── File Upload             (4.11.1)
    ├── Config Restore/Backup   (4.11.3)
    ├── Management Parameter    (4.11.4)
    ├── Email Account Setting   (4.11.5)
    ├── Username and Password   (4.11.6) — ★ تغيير كلمة السر
    └── Access Control          (4.11.7)
```

---

## ملخص سريع (Quick Reference Card)

```
╔══════════════════════════════════════════════════════╗
║       DINSTAR UC2000-VE-8G — QUICK REFERENCE        ║
╠══════════════════════════════════════════════════════╣
║  VPN Server:  157.173.125.136:51821/udp             ║
║  VPN Tunnel:  10.10.1.2 → 10.10.1.1                ║
║  VPN Type:    OpenVPN (.ovpn file upload)            ║
║  Auth: SHA1 | Cipher: AES-256-CBC | TLS-Auth: dir 1 ║
╠══════════════════════════════════════════════════════╣
║  SIP Server:  10.10.1.1:51600 (UDP, via VPN)        ║
║  NAT:         DISABLED (direct VPN tunnel)           ║
║  Codecs:      PCMA > PCMU > GSM                     ║
║  DTMF:        RFC2833                                ║
╠══════════════════════════════════════════════════════╣
║  Port Config: "ALL ports same user ID" = NO          ║
║  Port 1: gsm-port1 / Gsm1@Arwz2026 → Ext 7001     ║
║  Port 2: gsm-port2 / Gsm2@Arwz2026 → Ext 7002     ║
║  Port 3: gsm-port3 / Gsm3@Arwz2026 → Ext 7003     ║
║  Port 4: gsm-port4 / Gsm4@Arwz2026 → Ext 7004     ║
║  Port 5: gsm-port5 / Gsm5@Arwz2026 → Ext 7005     ║
║  Port 6: gsm-port6 / Gsm6@Arwz2026 → Ext 7006     ║
║  Port 7: gsm-port7 / Gsm7@Arwz2026 → Ext 7007     ║
║  Port 8: gsm-port8 / Gsm8@Arwz2026 → Ext 7008     ║
╠══════════════════════════════════════════════════════╣
║  Outbound: Any ext dials 0XX.. → round-robin ports   ║
║  Inbound:  GSM call on port N → rings ext 700N      ║
╚══════════════════════════════════════════════════════╝
```

---

## ترتيب الخطوات الصحيح (Checklist)

- [ ] 1. دخول الويب (`http://192.168.11.1` — admin/admin)
- [ ] 2. تغيير كلمة السر (**Tools → Username and Password**)
- [ ] 3. إعداد الشبكة (**Network Configuration → Local Network**)
- [ ] 4. رفع ملف VPN (**Network Configuration → VPN Parameter**)
- [ ] 5. تفعيل VPN والتأكد إنه Connected (**System Information**)
- [ ] 6. إعداد SIP Server (**Call Configuration → SIP Configuration**)
- [ ] 7. إعداد SIP Trunk (**Call Configuration → SIP Trunk Configuration**)
- [ ] 8. إعداد البورتات (**Call Configuration → Port Configuration**) — ★ الأهم
- [ ] 9. إعداد Media/Codecs (**Call Configuration → Media Parameter**)
- [ ] 10. إعداد Service Parameter (**Call Configuration → Service Parameter**)
- [ ] 11. إعداد Routing (**Call Configuration → IP->Tel Routing** + **Tel->IP Routing**)
- [ ] 12. فحص SIM Cards (**System Information → Mobile Information**)
- [ ] 13. فحص التسجيل (**System Information → SIP Information**)
- [ ] 14. اختبار مكالمات (inbound + outbound)
