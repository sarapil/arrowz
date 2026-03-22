# تثبيت coturn على FreePBX Server

## المشكلة
WebRTC softphone لا يستطيع الاتصال لأن TURN server غير موجود.
بدون TURN، المكالمات لا تعمل عبر NAT/Firewall.

## الحل: تثبيت coturn

### 1. SSH إلى FreePBX Server
```bash
ssh root@157.173.125.136
```

### 2. تثبيت coturn
```bash
# For CentOS/RHEL (FreePBX default)
yum install -y epel-release
yum install -y coturn

# Or for Debian/Ubuntu
# apt-get update && apt-get install -y coturn
```

### 3. إعداد coturn
```bash
cat > /etc/turnserver.conf << 'EOF'
# Network settings
listening-port=3478
tls-listening-port=5349
listening-ip=0.0.0.0

# Public IP of this server
external-ip=157.173.125.136

# Realm (use your domain)
realm=pbx.tavira-group.com
server-name=pbx.tavira-group.com

# Authentication
lt-cred-mech
user=webrtc:Arrowz2024!

# Additional users (optional)
# user=user2:password2

# Logging
log-file=/var/log/turnserver.log
verbose

# Security
fingerprint
no-multicast-peers
no-cli

# Allowed peer addresses (Asterisk)
allowed-peer-ip=172.23.0.0-172.23.255.255
allowed-peer-ip=10.0.0.0-10.255.255.255
allowed-peer-ip=192.168.0.0-192.168.255.255

# Performance
total-quota=100
bps-capacity=0
stale-nonce=600

# WebRTC compatibility
no-stdout-log
EOF
```

### 4. تشغيل coturn
```bash
# Enable and start service
systemctl enable coturn
systemctl start coturn

# Or run directly for testing
turnserver -c /etc/turnserver.conf
```

### 5. فتح المنافذ في Firewall
```bash
# For firewalld (CentOS)
firewall-cmd --permanent --add-port=3478/udp
firewall-cmd --permanent --add-port=3478/tcp
firewall-cmd --permanent --add-port=5349/udp
firewall-cmd --permanent --add-port=5349/tcp
firewall-cmd --permanent --add-port=49152-65535/udp  # RTP range
firewall-cmd --reload

# For iptables
iptables -A INPUT -p udp --dport 3478 -j ACCEPT
iptables -A INPUT -p tcp --dport 3478 -j ACCEPT
iptables -A INPUT -p udp --dport 5349 -j ACCEPT
iptables -A INPUT -p tcp --dport 5349 -j ACCEPT
iptables -A INPUT -p udp --dport 49152:65535 -j ACCEPT
```

### 6. اختبار TURN
```bash
# From any machine with curl
curl -v telnet://157.173.125.136:3478

# Or use turnutils_uclient (comes with coturn)
turnutils_uclient -t -u webrtc -w Arrowz2024! 157.173.125.136
```

### 7. التحقق من الإعدادات في Asterisk
الإعدادات موجودة بالفعل في `/etc/asterisk/rtp_custom.conf`:
```ini
turnaddr=157.173.125.136
turnusername=webrtc
turnpassword=Arrowz2024!
```

### 8. إعادة تحميل Asterisk
```bash
asterisk -rx "core reload"
# أو
asterisk -rx "module reload res_rtp_asterisk.so"
```

## التحقق من العمل
بعد التثبيت، في المتصفح console يجب أن ترى:
```
Arrowz: ICE candidate: relay 157.173.125.136:xxxxx udp
```

إذا ظهر `relay` candidate، TURN يعمل!

## مشاكل شائعة

### coturn لا يبدأ
```bash
# Check logs
journalctl -u coturn -f
cat /var/log/turnserver.log

# Check if port is in use
ss -tulpn | grep 3478
```

### لا يوجد relay candidates
1. تأكد من فتح المنافذ في firewall
2. تأكد من أن external-ip صحيح
3. جرب: `turnserver -c /etc/turnserver.conf -v` لرؤية الـ debug output

### Authentication failed
تأكد من تطابق username/password في:
- `/etc/turnserver.conf`
- `rtp_custom.conf` في Asterisk
- إعدادات AZ Server Config في Frappe
