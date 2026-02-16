# OpenMeetings Setup Guide for Arrowz

> دليل شامل لإعداد Apache OpenMeetings للعمل مع نظام Arrowz للمؤتمرات المرئية

---

## جدول المحتويات

1. [نظرة عامة على OpenMeetings](#نظرة-عامة-على-openmeetings)
2. [المتطلبات الأساسية](#المتطلبات-الأساسية)
3. [تثبيت OpenMeetings](#تثبيت-openmeetings)
4. [إعداد OpenMeetings](#إعداد-openmeetings)
5. [إنشاء مستخدم API](#إنشاء-مستخدم-api)
6. [إعداد SSL/TLS](#إعداد-ssltls)
7. [تكوين Arrowz](#تكوين-arrowz)
8. [إنشاء غرف الاجتماعات](#إنشاء-غرف-الاجتماعات)
9. [دعوة المشاركين](#دعوة-المشاركين)
10. [التسجيل](#التسجيل)
11. [استكشاف الأخطاء](#استكشاف-الأخطاء)
12. [REST API Reference](#rest-api-reference)

---

## نظرة عامة على OpenMeetings

Apache OpenMeetings هو حل مفتوح المصدر لمؤتمرات الفيديو يوفر:

- ✅ مؤتمرات فيديو عالية الجودة (WebRTC)
- ✅ مشاركة الشاشة
- ✅ السبورة البيضاء التفاعلية
- ✅ تسجيل الاجتماعات
- ✅ الدردشة النصية
- ✅ مشاركة الملفات
- ✅ REST API للتكامل

### أنواع الغرف

| النوع | الوصف | الاستخدام |
|------|-------|---------|
| Conference (1) | غرفة مؤتمرات عادية | اجتماعات الفريق |
| Presentation (2) | غرفة عرض تقديمي | ندوات ودورات |
| Interview (3) | غرفة مقابلات | مقابلات العمل |
| Restricted (4) | غرفة مقيدة | جلسات خاصة |

---

## المتطلبات الأساسية

### متطلبات الأجهزة

| المكون | الحد الأدنى | الموصى |
|--------|------------|--------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 20 GB | 100+ GB (للتسجيلات) |
| Network | 100 Mbps | 1 Gbps |

### متطلبات البرمجيات

| المكون | الإصدار |
|--------|--------|
| Java (OpenJDK) | 17+ |
| MySQL/MariaDB أو PostgreSQL | 8+ / 10+ |
| LibreOffice | 7+ (لتحويل الملفات) |
| ImageMagick | 6+ |
| FFmpeg | 4+ |
| SoX | 14+ |

### المنافذ المطلوبة

| المنفذ | البروتوكول | الغرض |
|--------|-----------|-------|
| 5443 | TCP/HTTPS | Web Interface & API |
| 1935 | TCP | RTMP (اختياري) |
| 8888 | TCP | Kurento Media Server |
| 8889 | TCP | Kurento WebSocket |

---

## تثبيت OpenMeetings

### الخيار 1: Docker (الأسهل)

```bash
# إنشاء شبكة Docker
docker network create openmeetings-net

# تشغيل MariaDB
docker run -d --name om-mariadb \
  --network openmeetings-net \
  -e MYSQL_ROOT_PASSWORD=secret123 \
  -e MYSQL_DATABASE=openmeetings \
  -e MYSQL_USER=om_user \
  -e MYSQL_PASSWORD=om_pass123 \
  mariadb:10.6

# تشغيل Kurento Media Server
docker run -d --name kurento \
  --network openmeetings-net \
  kurento/kurento-media-server:latest

# تشغيل OpenMeetings
docker run -d --name openmeetings \
  --network openmeetings-net \
  -p 5443:5443 \
  -e OM_DB_HOST=om-mariadb \
  -e OM_DB_PORT=3306 \
  -e OM_DB_USER=om_user \
  -e OM_DB_PASS=om_pass123 \
  -e OM_DB_NAME=openmeetings \
  -e OM_KURENTO_WS=ws://kurento:8888/kurento \
  apache/openmeetings:latest
```

### الخيار 2: Docker Compose (موصى به للإنتاج)

إنشاء ملف `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mariadb:
    image: mariadb:10.6
    container_name: om-mariadb
    environment:
      MYSQL_ROOT_PASSWORD: secret123
      MYSQL_DATABASE: openmeetings
      MYSQL_USER: om_user
      MYSQL_PASSWORD: om_pass123
    volumes:
      - om-db-data:/var/lib/mysql
    networks:
      - om-network
    restart: unless-stopped

  kurento:
    image: kurento/kurento-media-server:latest
    container_name: kurento
    networks:
      - om-network
    restart: unless-stopped

  openmeetings:
    image: apache/openmeetings:latest
    container_name: openmeetings
    ports:
      - "5443:5443"
    environment:
      OM_DB_HOST: mariadb
      OM_DB_PORT: 3306
      OM_DB_USER: om_user
      OM_DB_PASS: om_pass123
      OM_DB_NAME: openmeetings
      OM_KURENTO_WS: ws://kurento:8888/kurento
      OM_ALLOW_FRONTEND_REGISTER: "0"
      OM_DEFAULT_LANG_ID: "1"
    volumes:
      - om-data:/opt/om
      - om-recordings:/opt/om/webapps/openmeetings/data
    networks:
      - om-network
    depends_on:
      - mariadb
      - kurento
    restart: unless-stopped

volumes:
  om-db-data:
  om-data:
  om-recordings:

networks:
  om-network:
    driver: bridge
```

```bash
# تشغيل
docker-compose up -d

# مراقبة السجلات
docker-compose logs -f openmeetings
```

### الخيار 3: تثبيت يدوي (Linux)

```bash
# تثبيت المتطلبات (Ubuntu/Debian)
sudo apt update
sudo apt install -y openjdk-17-jdk mariadb-server \
  libreoffice imagemagick ffmpeg sox

# تنزيل OpenMeetings
wget https://downloads.apache.org/openmeetings/7.2.0/bin/apache-openmeetings-7.2.0.tar.gz
tar -xzf apache-openmeetings-7.2.0.tar.gz
mv apache-openmeetings-7.2.0 /opt/openmeetings

# إنشاء قاعدة البيانات
sudo mysql -e "CREATE DATABASE openmeetings DEFAULT CHARACTER SET utf8mb4;"
sudo mysql -e "CREATE USER 'om_user'@'localhost' IDENTIFIED BY 'om_pass123';"
sudo mysql -e "GRANT ALL PRIVILEGES ON openmeetings.* TO 'om_user'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# تشغيل معالج التثبيت
cd /opt/openmeetings
./admin.sh -i -v
# ثم افتح https://localhost:5443/openmeetings/install
```

---

## إعداد OpenMeetings

### 1. الإعداد الأولي

1. افتح متصفحك على: `https://your-server:5443/openmeetings/install`

2. اتبع خطوات المعالج:

   **الخطوة 1 - اختيار قاعدة البيانات:**
   - Database Type: MySQL
   - Host: localhost (أو اسم container)
   - Port: 3306
   - Database: openmeetings
   - Username: om_user
   - Password: om_pass123

   **الخطوة 2 - إعداد المدير:**
   - Username: admin
   - Password: كلمة مرور قوية
   - Email: admin@example.com

   **الخطوة 3 - إعدادات النظام:**
   - SIP/SRTP: تخطى (نستخدم Arrowz للمكالمات)
   - Default Language: English (أو Arabic)

   **الخطوة 4 - إعدادات المحولات:**
   ```
   ImageMagick Path: /usr/bin
   FFmpeg Path: /usr/bin
   SoX Path: /usr/bin
   LibreOffice Path: /usr/lib/libreoffice/program
   ```

3. اضغط **Install** وانتظر الانتهاء

### 2. إعدادات الإدارة

بعد تسجيل الدخول كـ admin:

**المسار:** `Administration → Configuration`

| الإعداد | القيمة | الوصف |
|---------|--------|-------|
| allow.frontend.register | false | منع التسجيل العام |
| default.lang.id | 1 | اللغة الافتراضية |
| default.timezone | Asia/Riyadh | المنطقة الزمنية |
| max.upload.size | 104857600 | حجم الملفات (100MB) |
| recording.enabled | true | تفعيل التسجيل |
| sip.enabled | false | تعطيل SIP المدمج |

---

## إنشاء مستخدم API

### 1. إنشاء مستخدم للتكامل

**المسار:** `Administration → Users → Add User`

| الحقل | القيمة |
|-------|--------|
| Login | arrowz-api |
| Password | APISecurePassword123! |
| Email | api@yourdomain.com |
| First Name | Arrowz |
| Last Name | API |
| Type | Admin |
| Rights | Admin |

### 2. الحصول على معرف المستخدم

```bash
# من خلال REST API
curl -k "https://your-server:5443/openmeetings/services/user/login" \
  -H "Content-Type: application/json" \
  -d '{"user":"arrowz-api","pass":"APISecurePassword123!"}'
```

**الاستجابة:**
```json
{
  "serviceResult": {
    "code": 0,
    "type": "SUCCESS"
  },
  "sid": "SESSION_ID_HERE"
}
```

### 3. التحقق من معرف المستخدم

```bash
curl -k "https://your-server:5443/openmeetings/services/user/get?sid=SESSION_ID_HERE"
```

**ملاحظة:** احفظ `id` من الاستجابة - ستحتاجه في Arrowz كـ `om_moderator_id`

---

## إعداد SSL/TLS

### الخيار 1: Let's Encrypt

```bash
# تثبيت certbot
sudo apt install certbot

# الحصول على شهادة
sudo certbot certonly --standalone -d meetings.yourdomain.com

# نسخ الشهادات لـ OpenMeetings
sudo cp /etc/letsencrypt/live/meetings.yourdomain.com/fullchain.pem /opt/openmeetings/conf/
sudo cp /etc/letsencrypt/live/meetings.yourdomain.com/privkey.pem /opt/openmeetings/conf/

# تحويل إلى keystore
cd /opt/openmeetings/conf
openssl pkcs12 -export -in fullchain.pem -inkey privkey.pem -out keystore.p12 -name openmeetings -password pass:changeit

keytool -importkeystore \
  -deststorepass changeit \
  -destkeypass changeit \
  -destkeystore keystore \
  -srckeystore keystore.p12 \
  -srcstoretype PKCS12 \
  -srcstorepass changeit \
  -alias openmeetings
```

### الخيار 2: شهادة ذاتية التوقيع (للاختبار)

```bash
cd /opt/openmeetings/conf

keytool -genkey -alias openmeetings \
  -keyalg RSA -keysize 2048 \
  -keystore keystore \
  -storepass changeit \
  -keypass changeit \
  -validity 365 \
  -dname "CN=meetings.yourdomain.com, OU=IT, O=Company, L=City, ST=State, C=SA"
```

### تحديث server.xml

```bash
nano /opt/openmeetings/conf/server.xml
```

تأكد من وجود:

```xml
<Connector port="5443" protocol="org.apache.coyote.http11.Http11NioProtocol"
    maxThreads="150" SSLEnabled="true">
    <SSLHostConfig>
        <Certificate certificateKeystoreFile="conf/keystore"
                     certificateKeystorePassword="changeit"
                     type="RSA" />
    </SSLHostConfig>
</Connector>
```

---

## تكوين Arrowz

### 1. إضافة Server Config جديد

**المسار:** `Arrowz → AZ Server Config → New`

| الحقل | القيمة |
|-------|--------|
| **Server Name** | openmeetings-main |
| **Server Type** | OpenMeetings |
| **Is Active** | ✓ |
| **Is Default** | ✓ (إذا كان الخادم الوحيد) |
| **Display Name** | خادم المؤتمرات |
| **Host** | meetings.yourdomain.com |
| **Port** | 5443 |
| **Protocol** | WSS |

### إعدادات OpenMeetings:

| الحقل | القيمة |
|-------|--------|
| **Enable OpenMeetings** | ✓ |
| **OpenMeetings URL** | https://meetings.yourdomain.com:5443 |
| **Admin Username** | arrowz-api |
| **Admin Password** | APISecurePassword123! |
| **Webapp Path** | /openmeetings |
| **Default Room Type** | Conference |
| **Default Moderator ID** | 1 (أو ID المستخدم الذي أنشأته) |
| **Verify SSL** | ✓ (أو ❌ للشهادات الذاتية) |

### 2. اختبار الاتصال

```python
# من Frappe Console
bench --site dev.localhost console

>>> from arrowz.integrations.openmeetings import OpenMeetingsClient
>>> config = frappe.get_doc("AZ Server Config", "openmeetings-main")
>>> client = OpenMeetingsClient(config)
>>> sid = client.get_session_id()
>>> print("Session ID:", sid)  # يجب أن يُرجع session صالح
```

---

## إنشاء غرف الاجتماعات

### من واجهة Arrowz

**المسار:** `Arrowz → AZ Meeting Room → New`

| الحقل | القيمة |
|-------|--------|
| Room Name | Weekly Team Meeting |
| Room Type | Conference |
| Server Config | openmeetings-main |
| Is Public | ❌ |
| Max Participants | 20 |
| Is Moderated | ✓ |
| Allow Recording | ✓ |

### من خلال API

```python
import frappe

@frappe.whitelist()
def create_meeting_room(name, room_type="Conference", max_participants=20):
    """إنشاء غرفة اجتماع جديدة"""
    from arrowz.integrations.openmeetings import OpenMeetingsClient
    
    config = frappe.get_doc("AZ Server Config", {"server_type": "OpenMeetings", "is_default": 1})
    client = OpenMeetingsClient(config)
    
    # إنشاء الغرفة في OpenMeetings
    room_id = client.create_room(
        name=name,
        room_type=room_type,
        capacity=max_participants,
        is_public=False,
        is_moderated=True
    )
    
    # إنشاء السجل في Frappe
    room = frappe.get_doc({
        "doctype": "AZ Meeting Room",
        "room_name": name,
        "om_room_id": room_id,
        "room_type": room_type,
        "server_config": config.name,
        "max_participants": max_participants
    })
    room.insert()
    
    return room.name
```

### أنواع الغرف

```python
ROOM_TYPES = {
    "Conference": 1,      # غرفة مؤتمرات عادية
    "Presentation": 2,    # غرفة عرض تقديمي
    "Interview": 3,       # غرفة مقابلات (شخصين)
    "Restricted": 4       # غرفة مقيدة
}
```

---

## دعوة المشاركين

### إنشاء رابط دعوة

```python
@frappe.whitelist()
def get_join_url(room_name, user_email, user_name, is_moderator=False):
    """الحصول على رابط الانضمام للغرفة"""
    from arrowz.integrations.openmeetings import OpenMeetingsClient
    
    room = frappe.get_doc("AZ Meeting Room", room_name)
    config = frappe.get_doc("AZ Server Config", room.server_config)
    client = OpenMeetingsClient(config)
    
    # الحصول على hash آمن
    secure_hash = client.get_user_hash(
        room_id=room.om_room_id,
        user_email=user_email,
        user_name=user_name,
        is_moderator=is_moderator,
        external_type="arrowz",
        external_id=frappe.session.user
    )
    
    join_url = f"{config.om_url}{config.om_webapp_path}/?secureHash={secure_hash}"
    
    return {
        "url": join_url,
        "hash": secure_hash
    }
```

### إرسال دعوة بالبريد

```python
@frappe.whitelist()
def invite_to_meeting(room_name, participants):
    """دعوة مشاركين للاجتماع"""
    room = frappe.get_doc("AZ Meeting Room", room_name)
    
    for participant in participants:
        join_info = get_join_url(
            room_name=room_name,
            user_email=participant.get("email"),
            user_name=participant.get("name"),
            is_moderator=participant.get("is_moderator", False)
        )
        
        # إرسال البريد
        frappe.sendmail(
            recipients=[participant.get("email")],
            subject=f"دعوة لاجتماع: {room.room_name}",
            message=f"""
            <p>مرحباً {participant.get("name")},</p>
            <p>تم دعوتك للانضمام إلى اجتماع: <strong>{room.room_name}</strong></p>
            <p><a href="{join_info['url']}" style="background:#4CAF50;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;">
                انضم الآن
            </a></p>
            """
        )
        
        # إنشاء سجل المشارك
        frappe.get_doc({
            "doctype": "AZ Meeting Participant",
            "room": room_name,
            "email": participant.get("email"),
            "name1": participant.get("name"),
            "is_moderator": participant.get("is_moderator", False),
            "invitation_sent": 1
        }).insert()
```

---

## التسجيل

### تفعيل التسجيل

```python
@frappe.whitelist()
def start_recording(room_name):
    """بدء تسجيل الاجتماع"""
    from arrowz.integrations.openmeetings import OpenMeetingsClient
    
    room = frappe.get_doc("AZ Meeting Room", room_name)
    config = frappe.get_doc("AZ Server Config", room.server_config)
    client = OpenMeetingsClient(config)
    
    recording_id = client.start_recording(room.om_room_id)
    
    room.is_recording = 1
    room.current_recording_id = recording_id
    room.save()
    
    return recording_id

@frappe.whitelist()
def stop_recording(room_name):
    """إيقاف التسجيل"""
    room = frappe.get_doc("AZ Meeting Room", room_name)
    config = frappe.get_doc("AZ Server Config", room.server_config)
    client = OpenMeetingsClient(config)
    
    client.stop_recording(room.current_recording_id)
    
    room.is_recording = 0
    room.save()
```

### الحصول على التسجيلات

```python
@frappe.whitelist()
def get_recordings(room_name):
    """الحصول على قائمة التسجيلات"""
    from arrowz.integrations.openmeetings import OpenMeetingsClient
    
    room = frappe.get_doc("AZ Meeting Room", room_name)
    config = frappe.get_doc("AZ Server Config", room.server_config)
    client = OpenMeetingsClient(config)
    
    recordings = client.get_recordings(room.om_room_id)
    
    return recordings
```

---

## استكشاف الأخطاء

### مشكلة: فشل الاتصال بـ OpenMeetings

**الأعراض:**
- خطأ "Connection refused"
- خطأ "SSL handshake failed"

**الحلول:**

1. **تأكد من تشغيل OpenMeetings:**
```bash
# Docker
docker ps | grep openmeetings

# Native
ps aux | grep openmeetings
```

2. **تأكد من صحة URL:**
```bash
curl -k https://meetings.yourdomain.com:5443/openmeetings/services/info/version
```

3. **تأكد من Firewall:**
```bash
# فتح المنفذ
firewall-cmd --add-port=5443/tcp --permanent
firewall-cmd --reload
```

---

### مشكلة: فشل تسجيل الدخول API

**الأعراض:**
- خطأ "Invalid credentials"
- خطأ "User not found"

**الحلول:**

1. **تأكد من صحة بيانات الدخول:**
```bash
curl -k "https://meetings.yourdomain.com:5443/openmeetings/services/user/login" \
  -H "Content-Type: application/json" \
  -d '{"user":"arrowz-api","pass":"YOUR_PASSWORD"}'
```

2. **تأكد من أن المستخدم Admin:**
- يجب أن يكون نوع المستخدم `Admin`
- يجب أن يكون لديه صلاحيات `Admin`

---

### مشكلة: لا يمكن إنشاء غرفة

**الأعراض:**
- خطأ "Permission denied"
- خطأ "Invalid room type"

**الحلول:**

1. **تأكد من Session صالح:**
```python
client = OpenMeetingsClient(config)
sid = client.get_session_id()
print("SID Valid:", sid is not None)
```

2. **تأكد من نوع الغرفة صحيح:**
```python
# الأنواع الصالحة: 1, 2, 3, 4
room_type_id = {"Conference": 1, "Presentation": 2, "Interview": 3, "Restricted": 4}
```

---

### مشكلة: فشل انضمام المستخدمين

**الأعراض:**
- خطأ "Invalid hash"
- صفحة فارغة عند الانضمام

**الحلول:**

1. **تأكد من صلاحية Hash:**
- الـ Hash له وقت انتهاء
- أنشئ hash جديد لكل محاولة انضمام

2. **تأكد من إعدادات الغرفة:**
```python
# الغرفة يجب أن تكون موجودة ونشطة
room_info = client.get_room(room_id)
print("Room exists:", room_info is not None)
```

---

### مشكلة: مشاكل الفيديو/الصوت

**الأعراض:**
- لا يوجد فيديو
- صوت متقطع

**الحلول:**

1. **تأكد من Kurento:**
```bash
docker logs kurento | tail -50
```

2. **تأكد من إعدادات WebRTC:**
- يجب أن يكون المتصفح يدعم WebRTC
- يجب السماح بصلاحيات الكاميرا والميكروفون

3. **تأكد من المنافذ:**
```bash
# تأكد من أن المنافذ مفتوحة
netstat -tlnp | grep -E "8888|8889"
```

---

## REST API Reference

### Authentication

```bash
# Login
POST /services/user/login
Body: {"user": "username", "pass": "password"}
Response: {"serviceResult": {"code": 0}, "sid": "SESSION_ID"}
```

### Rooms

```bash
# Get all rooms
GET /services/room/?sid={SID}

# Create room
POST /services/room/?sid={SID}
Body: {
  "name": "Room Name",
  "roomType": 1,
  "capacity": 20,
  "isPublic": false,
  "isModerated": true
}

# Get room by ID
GET /services/room/{ROOM_ID}?sid={SID}

# Delete room
DELETE /services/room/{ROOM_ID}?sid={SID}
```

### User Hash

```bash
# Generate secure hash for user
GET /services/user/hash?sid={SID}&roomId={ROOM_ID}&email={EMAIL}&firstName={FIRST}&lastName={LAST}&moderator={true|false}
```

### Recordings

```bash
# Get recordings for room
GET /services/record/?sid={SID}&roomId={ROOM_ID}

# Get recording by ID
GET /services/record/{RECORDING_ID}?sid={SID}
```

---

## قائمة فحص ما قبل الإنتاج

- [ ] OpenMeetings مثبت ويعمل
- [ ] شهادة SSL صالحة
- [ ] Kurento Media Server يعمل
- [ ] مستخدم API مُنشأ بصلاحيات Admin
- [ ] AZ Server Config مُعد في Arrowz
- [ ] اختبار إنشاء غرفة ناجح
- [ ] اختبار انضمام مستخدم ناجح
- [ ] اختبار الفيديو/الصوت ناجح
- [ ] التسجيل يعمل (إذا مطلوب)
- [ ] Firewall مُعد بشكل صحيح
- [ ] نسخ احتياطي لقاعدة البيانات

---

## المراجع

- [Apache OpenMeetings Documentation](https://openmeetings.apache.org/docs/)
- [OpenMeetings REST API](https://openmeetings.apache.org/RestAPISample.html)
- [Kurento Media Server](https://www.kurento.org/documentation)
