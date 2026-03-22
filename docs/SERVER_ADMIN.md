# Arrowz Server Administration Guide

> **Version:** 16.0.0  
> **Compatible With:** Frappe v16+ / ERPNext v16+  
> **Last Updated:** February 17, 2026

---

## 📋 Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [FreePBX Integration](#4-freepbx-integration)
5. [Omni-Channel Setup](#5-omni-channel-setup)
6. [Video Conferencing](#6-video-conferencing)
7. [SSL and Security](#7-ssl-and-security)
8. [Backup and Recovery](#8-backup-and-recovery)
9. [Monitoring](#9-monitoring)
10. [Troubleshooting](#10-troubleshooting)
11. [Maintenance](#11-maintenance)
12. [Scaling](#12-scaling)

---

## 1. System Requirements

### 1.1 Frappe Server

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 40 GB | 100+ GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Python | 3.11 | 3.12 |
| Node.js | 18 | 20+ |
| MariaDB | 10.6 | 10.11 |
| Redis | 6.0 | 7.0 |

### 1.2 FreePBX Server

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| FreePBX | 16 | 17 |
| Asterisk | 18 | 20+ |
| RAM | 2 GB | 4+ GB |

### 1.3 Network Requirements

| Port | Service | Direction |
|------|---------|-----------|
| 8000 | Frappe Web | Inbound |
| 9000 | Frappe SocketIO | Inbound |
| 5060/5061 | SIP (UDP/TCP) | Bidirectional |
| 8089 | WebSocket (WSS) | Inbound |
| 10000-20000 | RTP Media | Bidirectional |
| 443 | HTTPS | Inbound |
| 22 | SSH (management) | Inbound |

---

## 2. Installation

### 2.1 Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-dev python3.11-venv \
    git redis-server mariadb-server libmariadb-dev \
    nodejs npm curl wget

# Install bench
pip3 install frappe-bench

# Create bench
bench init --frappe-branch version-16 frappe-bench
cd frappe-bench
```

### 2.2 Install Arrowz App

```bash
# Get the app
bench get-app arrowz --branch version-16
# Or from custom repository:
# bench get-app https://your-repo.git --branch version-16

# Create new site (if needed)
bench new-site yoursite.com --db-name arrowz_db

# Install on site
bench --site yoursite.com install-app arrowz

# Run migrations
bench --site yoursite.com migrate
```

### 2.3 Production Setup

```bash
# Setup production
sudo bench setup production $USER

# Enable SSL (Let's Encrypt)
sudo bench setup lets-encrypt yoursite.com

# Setup supervisor
sudo bench setup supervisor
sudo supervisorctl reload

# Setup nginx
sudo bench setup nginx
sudo nginx -t && sudo systemctl reload nginx
```

### 2.4 Verify Installation

```bash
# Check app is installed
bench --site yoursite.com list-apps

# Check version
bench --site yoursite.com console
>>> frappe.get_installed_app_version("arrowz")
'16.0.0'
>>> exit()
```

---

## 3. Configuration

### 3.1 Site Configuration

**sites/yoursite.com/site_config.json:**
```json
{
    "db_name": "arrowz_db",
    "db_password": "your_db_password",
    "db_type": "mariadb",
    "mail_server": "smtp.example.com",
    "mail_port": 587,
    "mail_login": "notifications@example.com",
    "mail_password": "your_email_password",
    "auto_email_id": "notifications@example.com",
    "use_ssl": 1,
    "encryption_key": "your_encryption_key"
}
```

### 3.2 Arrowz Settings

Navigate to: **Arrowz > Settings > Arrowz Settings**

| Field | Description |
|-------|-------------|
| **Default Server** | Primary FreePBX server |
| **Enable Softphone** | Enable browser-based softphone |
| **Enable Omni-Channel** | Enable WhatsApp/Telegram |
| **Enable Video** | Enable video conferencing |
| **Default Outbound CID** | Default caller ID |
| **Recording Storage** | Path to recording files |

### 3.3 Server Config (AZ Server Config)

Navigate to: **Arrowz > Settings > Server Config**

**Create a new server:**

```
Server Name: main-pbx
Server Host: pbx.yourcompany.com
Server Port: 5060
WebSocket URL: wss://pbx.yourcompany.com:8089/ws
SIP Domain: pbx.yourcompany.com

AMI Settings:
- AMI Host: pbx.yourcompany.com
- AMI Port: 5038
- AMI Username: arrowz
- AMI Secret: [encrypted]

GraphQL Settings:
- GraphQL URL: https://pbx.yourcompany.com/admin/api/api/gql
- GraphQL Client ID: [your_client_id]
- GraphQL Client Secret: [encrypted]

SSH Settings (optional):
- SSH Host: pbx.yourcompany.com
- SSH Port: 22
- SSH Username: root
- SSH Password: [encrypted]
```

### 3.4 Environment Variables

**/etc/supervisor/conf.d/frappe-bench.conf:**
```ini
[program:frappe-bench-web]
environment=
    PBX_HOST="pbx.yourcompany.com",
    REDIS_CACHE="redis://localhost:13000",
    REDIS_QUEUE="redis://localhost:11000"
```

---

## 4. FreePBX Integration

### 4.1 AMI User Setup

On FreePBX server, create AMI user:

**Edit `/etc/asterisk/manager.conf`:**
```ini
[arrowz]
secret = secure_password_here
deny = 0.0.0.0/0.0.0.0
permit = YOUR_FRAPPE_SERVER_IP/255.255.255.255
read = all
write = all
writetimeout = 5000
```

Reload Asterisk:
```bash
asterisk -rx "manager reload"
```

### 4.2 GraphQL API Setup

1. Go to FreePBX Admin → API → GraphQL
2. Create new application:
   - Name: Arrowz
   - Redirect URI: https://yoursite.com/api/method/arrowz.freepbx_token.oauth_callback
3. Note the Client ID and Client Secret
4. Configure in Arrowz Server Config

### 4.3 WebRTC/WebSocket Setup

**FreePBX WebRTC Configuration:**

1. Navigate to FreePBX → Settings → Asterisk SIP Settings
2. Under "WebRTC" section:
   - Enable WebRTC: Yes
   - WebSocket Port: 8089
   - Enable TLS for WebSocket: Yes

3. Generate certificates or configure Let's Encrypt:
```bash
# On FreePBX
fwconsole certificates --generate
fwconsole certificates --default=0  # Select your cert
```

4. Restart Asterisk:
```bash
fwconsole restart
```

### 4.4 SIP Extensions

Create PJSIP extensions with WebRTC support:

1. Go to Applications → Extensions → Add Extension → Add New PJSIP
2. Configure:
   - Extension: 1001
   - Display Name: John Doe
   - Secret: [strong_password]
   
3. Under "Advanced" tab:
   - Transport: All (PJSIP)
   - Media Encryption: SRTP via in-SDP
   - NAT: Force RPort, Yes (checked)
   - ICE Support: Yes
   - AVPF: Yes
   - Force AVP: Yes

### 4.5 TURN Server (for NAT traversal)

Install coturn:
```bash
sudo apt install coturn

# Edit /etc/turnserver.conf
listening-port=3478
tls-listening-port=5349
fingerprint
lt-cred-mech
use-auth-secret
static-auth-secret=YOUR_TURN_SECRET
realm=yourdomain.com
cert=/etc/letsencrypt/live/turn.yourdomain.com/fullchain.pem
pkey=/etc/letsencrypt/live/turn.yourdomain.com/privkey.pem
no-loopback-peers
no-multicast-peers
```

Configure in Arrowz Server Config:
```
TURN Server: turn:turn.yourdomain.com:3478
TURN Username: (leave empty for time-limited credentials)
TURN Secret: YOUR_TURN_SECRET
```

---

## 5. Omni-Channel Setup

### 5.1 WhatsApp Cloud API

**Step 1: Meta Business Setup**

1. Create Meta Business account at business.facebook.com
2. Create WhatsApp Business App in developers.facebook.com
3. Add WhatsApp product to your app
4. Get permanent access token

**Step 2: Configure Webhook**

Set webhook URL:
```
https://yoursite.com/api/method/arrowz.integrations.whatsapp.webhook
```

Subscribe to events:
- messages
- message_status
- message_template_status

**Step 3: Arrowz Configuration**

Create AZ Omni Provider:
```
Provider Name: Meta WhatsApp
Platform: WhatsApp
Access Token: [your_permanent_token]
App Secret: [for webhook verification]
```

Create AZ Omni Channel:
```
Channel Name: Main WhatsApp
Provider: Meta WhatsApp
Phone Number ID: [from Meta dashboard]
Business Account ID: [your_business_id]
Webhook Verify Token: [your_verify_token]
```

### 5.2 Telegram Bot

**Step 1: Create Bot**

1. Message @BotFather on Telegram
2. Create new bot: /newbot
3. Get bot token

**Step 2: Configure Webhook**

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
    -d "url=https://yoursite.com/api/method/arrowz.integrations.telegram.webhook"
```

**Step 3: Arrowz Configuration**

Create AZ Omni Provider:
```
Provider Name: Telegram
Platform: Telegram
Bot Token: [your_bot_token]
```

Create AZ Omni Channel:
```
Channel Name: Support Telegram
Provider: Telegram
```

### 5.3 Channel Routing

Configure routing rules in AZ Omni Routing:
```
Name: Support Queue
Channel: Main WhatsApp
Routing Type: Round Robin
Agents: [select users]
Working Hours: 09:00-18:00
Auto Response: "Thank you for contacting us..."
```

---

## 6. Video Conferencing

### 6.1 OpenMeetings Setup

**Install OpenMeetings:**
```bash
# Download OpenMeetings
wget https://downloads.apache.org/openmeetings/7.2.0/bin/apache-openmeetings-7.2.0.tar.gz
tar -xzf apache-openmeetings-7.2.0.tar.gz
cd apache-openmeetings-7.2.0

# Install dependencies
sudo apt install -y openjdk-17-jdk maven

# Configure and start
./bin/startup.sh
```

**Configure in Arrowz:**

AZ Video Settings:
```
Provider: OpenMeetings
Server URL: https://om.yourcompany.com
Admin User: admin
Admin Password: [encrypted]
Default Room Type: Conference
Max Participants: 25
```

### 6.2 Jitsi Integration (Alternative)

Install Jitsi:
```bash
curl https://download.jitsi.org/jitsi-key.gpg.key | sudo apt-key add -
echo 'deb https://download.jitsi.org stable/' | sudo tee /etc/apt/sources.list.d/jitsi.list
sudo apt update && sudo apt install jitsi-meet
```

Configure in Arrowz:
```
Provider: Jitsi
Server URL: https://meet.yourcompany.com
JWT Secret: [for authentication]
```

---

## 7. SSL and Security

### 7.1 SSL Certificates

**Let's Encrypt (recommended):**
```bash
# For Frappe
sudo bench setup lets-encrypt yoursite.com

# For FreePBX
certbot certonly --standalone -d pbx.yourcompany.com

# Renew automatically
echo "0 0 1 * * root certbot renew" >> /etc/crontab
```

### 7.2 Firewall Configuration

```bash
# UFW setup
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH
sudo ufw allow 22/tcp

# HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Frappe
sudo ufw allow 8000/tcp
sudo ufw allow 9000/tcp

# SIP (only from PBX)
sudo ufw allow from PBX_IP to any port 5060:5061 proto udp
sudo ufw allow from PBX_IP to any port 5060:5061 proto tcp

# Enable
sudo ufw enable
```

### 7.3 Security Best Practices

1. **Change default passwords** - All services
2. **Use strong passwords** - 16+ characters
3. **Enable 2FA** - For admin accounts
4. **Limit SSH access** - Key-based only
5. **Regular updates** - Security patches
6. **Monitor logs** - Set up alerts
7. **Backup regularly** - Test restores

### 7.4 API Security

Configure rate limiting in nginx:
```nginx
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    server {
        location /api/ {
            limit_req zone=api burst=20 nodelay;
        }
    }
}
```

---

## 8. Backup and Recovery

### 8.1 Database Backup

**Automated backup:**
```bash
# Create backup script
cat > /opt/backup-arrowz.sh << 'EOF'
#!/bin/bash
SITE="yoursite.com"
BACKUP_DIR="/opt/backups/arrowz"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
cd /home/frappe/frappe-bench
bench --site $SITE backup --with-files

# Move to backup directory
mv sites/$SITE/private/backups/* $BACKUP_DIR/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -type f -mtime +30 -delete
EOF

chmod +x /opt/backup-arrowz.sh

# Schedule daily backup
echo "0 2 * * * root /opt/backup-arrowz.sh" >> /etc/crontab
```

### 8.2 Files Backup

```bash
# Backup files
rsync -avz /home/frappe/frappe-bench/sites/yoursite.com/public/files/ \
    /opt/backups/files/

# Backup recordings
rsync -avz /path/to/recordings/ /opt/backups/recordings/
```

### 8.3 Restore Procedure

```bash
# Restore database
bench --site yoursite.com restore \
    /opt/backups/arrowz/20240217_020000-yoursite_database.sql.gz

# Restore files
bench --site yoursite.com restore \
    /opt/backups/arrowz/20240217_020000-yoursite_files.tar

# Run migrations
bench --site yoursite.com migrate

# Clear cache
bench --site yoursite.com clear-cache
```

### 8.4 Offsite Backup

```bash
# Sync to S3
aws s3 sync /opt/backups/arrowz/ s3://your-bucket/arrowz-backups/

# Sync to remote server
rsync -avz -e ssh /opt/backups/ backup-server:/backups/arrowz/
```

---

## 9. Monitoring

### 9.1 System Monitoring

**Install monitoring stack:**
```bash
# Install Prometheus
sudo apt install prometheus prometheus-node-exporter

# Install Grafana
sudo apt install grafana
```

### 9.2 Application Monitoring

**Frappe logs:**
```bash
# View logs
tail -f /home/frappe/frappe-bench/logs/web.log
tail -f /home/frappe/frappe-bench/logs/worker.log
tail -f /home/frappe/frappe-bench/logs/schedule.log
```

**Configure log rotation:**
```bash
cat > /etc/logrotate.d/frappe-bench << 'EOF'
/home/frappe/frappe-bench/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
}
EOF
```

### 9.3 Arrowz Monitoring Dashboard

Enable monitoring in Arrowz Settings:
- Real-time agent status
- Call queue metrics
- Channel message counts
- System health checks

Access at: `/app/arrowz-monitoring`

### 9.4 Health Checks

**Create health check endpoint:**

Arrowz provides a health check endpoint:
```
GET /api/method/arrowz.api.health.check
```

Response:
```json
{
    "status": "healthy",
    "database": "connected",
    "redis": "connected",
    "pbx": "connected",
    "version": "16.0.0"
}
```

**Monitor with cron:**
```bash
*/5 * * * * curl -s https://yoursite.com/api/method/arrowz.api.health.check | jq -e '.message.status == "healthy"' || echo "Arrowz unhealthy!" | mail -s "Alert" admin@example.com
```

---

## 10. Troubleshooting

### 10.1 Common Issues

#### WebRTC Not Connecting

**Symptoms:** Softphone shows "Connecting..." indefinitely

**Check:**
```bash
# Test WebSocket connectivity
wscat -c wss://pbx.yourcompany.com:8089/ws

# Check FreePBX WebSocket
asterisk -rx "pjsip show transports"

# Verify certificates
openssl s_client -connect pbx.yourcompany.com:8089
```

**Solutions:**
1. Verify SSL certificate is valid
2. Check firewall allows port 8089
3. Ensure TURN server is configured for NAT
4. Check browser console for errors

#### Calls Dropping

**Symptoms:** Calls connect but drop after a few seconds

**Check:**
```bash
# Check RTP ports are open
netstat -ulnp | grep asterisk

# Check for NAT issues
asterisk -rx "rtp show channels"
```

**Solutions:**
1. Configure TURN server
2. Enable ICE in extension settings
3. Open RTP port range (10000-20000)
4. Check for symmetric NAT

#### WhatsApp Messages Not Arriving

**Symptoms:** No incoming messages from WhatsApp

**Check:**
```bash
# Check webhook configuration
curl -I https://yoursite.com/api/method/arrowz.integrations.whatsapp.webhook

# View webhook logs
bench --site yoursite.com --logs
```

**Solutions:**
1. Verify webhook URL in Meta dashboard
2. Check verify token matches
3. Ensure app is subscribed to message events
4. Check SSL certificate is valid

### 10.2 Logs Analysis

**Key log locations:**
```bash
# Frappe web server
/home/frappe/frappe-bench/logs/web.log

# Background workers
/home/frappe/frappe-bench/logs/worker.log
/home/frappe/frappe-bench/logs/worker.error.log

# Scheduler
/home/frappe/frappe-bench/logs/schedule.log

# Nginx
/var/log/nginx/error.log
/var/log/nginx/access.log

# FreePBX/Asterisk
/var/log/asterisk/full
/var/log/asterisk/messages
```

**Search for errors:**
```bash
# Find Arrowz errors
grep -i "arrowz" /home/frappe/frappe-bench/logs/web.log | grep -i error

# Find WebRTC issues
grep -i "websocket\|webrtc\|ice" /var/log/asterisk/full
```

### 10.3 Debug Mode

**Enable debug mode:**
```bash
bench --site yoursite.com set-config developer_mode 1
bench restart
```

**Python debugging:**
```python
# Add to problematic code
import frappe
frappe.log_error("Debug message", "Arrowz Debug")
frappe.log_error(str(variable), "Variable Debug")
```

**JavaScript debugging:**
```javascript
// In browser console
frappe.debug_show = true;

// Log all realtime events
frappe.realtime.on("*", function(event, data) {
    console.log("Realtime:", event, data);
});
```

---

## 11. Maintenance

### 11.1 Regular Maintenance Tasks

**Daily:**
- Review error logs
- Check backup completion
- Monitor queue lengths

**Weekly:**
- Review failed background jobs
- Check disk space
- Review call quality metrics

**Monthly:**
- Security updates
- Database optimization
- Clear old data

### 11.2 Database Maintenance

```bash
# Optimize tables
bench --site yoursite.com backup
mysqlcheck -o yoursite_db -u root -p

# Clear old logs
bench --site yoursite.com execute \
    "frappe.db.sql('DELETE FROM tabError Log WHERE creation < DATE_SUB(NOW(), INTERVAL 30 DAY)')"

# Clear old error snapshots
bench --site yoursite.com execute \
    "frappe.db.sql('DELETE FROM tabError Snapshot WHERE creation < DATE_SUB(NOW(), INTERVAL 7 DAY)')"
```

### 11.3 Updates

```bash
# Update Frappe/ERPNext
bench update --pull

# Update Arrowz only
bench get-app arrowz --branch version-16 --overwrite
bench --site yoursite.com migrate
bench build --app arrowz
bench restart
```

### 11.4 Clear Cache

```bash
# Clear all cache
bench --site yoursite.com clear-cache
bench --site yoursite.com clear-website-cache

# Rebuild assets
bench build --force
```

---

## 12. Scaling

### 12.1 Horizontal Scaling

**Multi-server setup:**

```
┌──────────────┐     ┌──────────────┐
│  Nginx Load  │────▶│  Web Server  │
│  Balancer    │     │      #1      │
└──────────────┘     └──────────────┘
        │            ┌──────────────┐
        └───────────▶│  Web Server  │
                     │      #2      │
                     └──────────────┘
                            │
                     ┌──────────────┐
                     │    Redis     │
                     │   Cluster    │
                     └──────────────┘
                            │
                     ┌──────────────┐
                     │   MariaDB    │
                     │   Galera     │
                     └──────────────┘
```

### 12.2 Worker Configuration

**Increase workers for high load:**

Edit Procfile:
```
default: bench start
web: bench serve --port 8000
socketio: node apps/frappe/socketio.js
watch: bench watch
schedule: bench schedule
worker_default: bench worker --queue default --nativefork
worker_short: bench worker --queue short --nativefork
worker_long: bench worker --queue long --nativefork
worker_heavy: bench worker --queue heavy --nativefork
```

**Or use supervisor:**
```ini
[program:frappe-bench-worker-default]
command=/home/frappe/frappe-bench/env/bin/bench worker --queue default
numprocs=4
process_name=%(program_name)s-%(process_num)s
```

### 12.3 Database Optimization

**MariaDB tuning for high load:**
```ini
# /etc/mysql/mariadb.conf.d/99-arrowz.cnf
[mysqld]
innodb_buffer_pool_size = 4G
innodb_log_file_size = 512M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT
max_connections = 500
thread_cache_size = 50
query_cache_type = 0
```

### 12.4 Redis Cluster

**For high availability:**
```bash
# Setup Redis Sentinel
redis-sentinel /etc/redis/sentinel.conf

# Configure in site_config.json
{
    "redis_cache": "sentinel://master-name@sentinel1:26379,sentinel2:26379/0",
    "redis_queue": "sentinel://master-name@sentinel1:26379,sentinel2:26379/1"
}
```

---

## Quick Reference

### Useful Commands

```bash
# Service management
sudo supervisorctl status frappe-bench:
sudo supervisorctl restart frappe-bench:

# Site management
bench --site yoursite.com console
bench --site yoursite.com mariadb
bench --site yoursite.com backup

# Logs
tail -f ~/frappe-bench/logs/web.log
bench --site yoursite.com --logs

# Updates
bench update
bench migrate
bench build
bench restart

# Cache
bench clear-cache
bench clear-website-cache
```

### Configuration Files

| File | Purpose |
|------|---------|
| `sites/common_site_config.json` | Shared configuration |
| `sites/yoursite.com/site_config.json` | Site-specific config |
| `Procfile` | Process definitions |
| `/etc/supervisor/conf.d/` | Supervisor config |
| `/etc/nginx/conf.d/` | Nginx config |

### Support Contacts

- **Documentation:** https://docs.arrowz.app
- **Issues:** https://github.com/your-org/arrowz/issues
- **Email:** support@arrowz.app

---

*Last updated: February 17, 2026*
