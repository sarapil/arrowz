# Arrowz Integration Guide
## PBX, AI & Third-Party Integrations

---

## 📞 PBX Integration

### Supported Platforms
| Platform | Tested | Features |
|----------|--------|----------|
| FreePBX + Asterisk | ✅ | Full support |
| Issabel | ✅ | Full support |
| 3CX | 🔶 | WebRTC only |
| FusionPBX | 🔶 | WebRTC only |
| VitalPBX | 🔶 | WebRTC only |

---

## 🔧 FreePBX/Asterisk Setup

### Step 1: Enable WebRTC in Asterisk

#### 1.1 SSL Certificate
```bash
# Generate self-signed certificate (for testing)
cd /etc/asterisk/keys
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout asterisk.key \
    -out asterisk.crt \
    -subj "/CN=pbx.company.com"

# Combine for Asterisk
cat asterisk.key asterisk.crt > asterisk.pem

# Set permissions
chown asterisk:asterisk asterisk.*
chmod 600 asterisk.*
```

#### 1.2 http.conf
```ini
[general]
enabled=yes
bindaddr=0.0.0.0
bindport=8088
tlsenable=yes
tlsbindaddr=0.0.0.0:8089
tlscertfile=/etc/asterisk/keys/asterisk.crt
tlsprivatekey=/etc/asterisk/keys/asterisk.key
```

#### 1.3 pjsip.conf - WebSocket Transport
```ini
[transport-wss]
type=transport
protocol=wss
bind=0.0.0.0:8089
cert_file=/etc/asterisk/keys/asterisk.crt
priv_key_file=/etc/asterisk/keys/asterisk.key
```

#### 1.4 pjsip.conf - WebRTC Endpoint Template
```ini
[webrtc-endpoint](!)
type=endpoint
transport=transport-wss
context=from-internal
disallow=all
allow=opus
allow=ulaw
allow=alaw
webrtc=yes
dtls_auto_generate_cert=yes
use_avpf=yes
media_encryption=dtls
dtls_verify=fingerprint
dtls_setup=actpass
ice_support=yes
rtcp_mux=yes
```

### Step 2: Create WebRTC Extensions

#### FreePBX GUI Method
1. Navigate to **Applications → Extensions**
2. Click **Add Extension → Add New PJSIP Extension**
3. Extension Options:
   - **User Extension**: 9001 (for WebRTC users)
   - **Display Name**: User Name
   - **Secret**: Strong password
4. **Advanced** tab:
   - Transport: `WSS Only`
   - AVPF: `Yes`
   - ICE Support: `Yes`
   - Force rport: `Yes`
5. Apply Config

#### CLI Method
```bash
# Add to pjsip_custom.conf
asterisk -rx "dialplan reload"
asterisk -rx "pjsip reload"
```

### Step 3: Firewall Configuration
```bash
# Required ports
firewall-cmd --permanent --add-port=8089/tcp  # WSS
firewall-cmd --permanent --add-port=10000-20000/udp  # RTP
firewall-cmd --reload
```

### Step 4: Asterisk Manager Interface (AMI)

#### manager.conf
```ini
[general]
enabled = yes
port = 5038
bindaddr = 0.0.0.0

[arrowz]
secret = SecurePassword123!
deny = 0.0.0.0/0.0.0.0
permit = 10.0.0.0/255.0.0.0  # Your network
read = call,cdr,user
write = call,originate
eventfilter=!Event: RTCPSent
eventfilter=!Event: RTCPReceived
eventfilter=!Event: VarSet
```

#### AMI Events for Real-time Features

| Event | Purpose | Used For |
|-------|---------|----------|
| `Newchannel` | New call initiated | Click-to-Dial confirmation |
| `Hangup` | Call ended | Call log update |
| `Bridge` | Two channels connected | Call answered detection |
| `BlindTransfer` | Blind transfer executed | Transfer confirmation |
| `AttendedTransfer` | Attended transfer completed | Transfer confirmation |
| `Hold` / `Unhold` | Call hold status | UI state update |
| `OriginateResponse` | Click-to-Dial result | Success/failure feedback |

#### AMI Event Listener Service (Python)
```python
# arrowz/services/ami_listener.py
import asyncio
from panoramisk import Manager

class AMIEventListener:
    def __init__(self, config):
        self.manager = Manager(
            host=config.ami_host,
            port=config.ami_port,
            username=config.ami_username,
            secret=config.ami_secret
        )
        
    async def start(self):
        await self.manager.connect()
        # Subscribe to relevant events
        self.manager.register_event('Newchannel', self.on_new_channel)
        self.manager.register_event('Hangup', self.on_hangup)
        self.manager.register_event('Bridge', self.on_bridge)
        self.manager.register_event('OriginateResponse', self.on_originate)
        
    async def on_new_channel(self, manager, event):
        """Handle new channel - notify UI via Socket.IO"""
        channel_data = {
            'channel': event.Channel,
            'caller_id': event.CallerIDNum,
            'extension': event.Exten,
            'uniqueid': event.Uniqueid
        }
        # Publish to Socket.IO
        frappe.publish_realtime('ami_new_channel', channel_data)
        
    async def on_originate(self, manager, event):
        """Handle Click-to-Dial response"""
        success = event.Response == 'Success'
        frappe.publish_realtime('click_to_dial_result', {
            'success': success,
            'action_id': event.ActionID,
            'reason': event.get('Reason', '')
        })
```

---

## 🌐 FreePBX GraphQL API Integration

### Overview
FreePBX 17+ provides a GraphQL API for configuration management. We use this for Extensions and Inbound Routes, with fwconsole fallback for Trunks and Outbound Routes.

### GraphQL Endpoint Configuration
```python
# CC Server Config additional fields
graphql_url = "https://pbx.company.com/admin/api/api/gql"
graphql_token = "(encrypted Bearer token)"
```

### Supported Operations via GraphQL

| Entity | List | Get | Create | Update | Delete |
|--------|------|-----|--------|--------|--------|
| Extensions | ✅ | ✅ | ✅ | ✅ | ✅ |
| Inbound Routes | ✅ | ✅ | ✅ | ✅ | ✅ |
| Trunks | ❌ | ❌ | ❌ | ❌ | ❌ |
| Outbound Routes | ❌ | ❌ | ❌ | ❌ | ❌ |

### GraphQL Client Implementation
```python
# arrowz/integrations/freepbx_graphql.py
import requests

class FreePBXGraphQL:
    def __init__(self, server_config):
        self.url = server_config.graphql_url
        self.token = server_config.get_password('graphql_token')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def execute(self, query, variables=None):
        """Execute GraphQL query"""
        response = requests.post(
            self.url,
            json={'query': query, 'variables': variables or {}},
            headers=self.headers,
            verify=True  # SSL verification
        )
        result = response.json()
        if 'errors' in result:
            raise Exception(result['errors'][0]['message'])
        return result['data']
    
    # ═══════════════════════════════════════
    # EXTENSIONS
    # ═══════════════════════════════════════
    
    def list_extensions(self):
        """Get all PJSIP extensions"""
        query = """
        query {
            fetchAllExtensions {
                status
                message
                extension {
                    extensionId
                    user {
                        name
                        displayName
                    }
                    coreDevice {
                        deviceId
                        tech
                    }
                }
            }
        }
        """
        return self.execute(query)
    
    def get_extension(self, ext_id):
        """Get single extension details"""
        query = """
        query GetExtension($id: ID!) {
            fetchExtension(extensionId: $id) {
                status
                extension {
                    extensionId
                    user { name, displayName, password }
                    coreDevice { deviceId, tech }
                    extPjsip { 
                        transport
                        maxContacts
                        iceSupport
                    }
                }
            }
        }
        """
        return self.execute(query, {'id': ext_id})
    
    def create_extension(self, ext_data):
        """Create new PJSIP extension"""
        mutation = """
        mutation CreateExtension($input: ExtensionInput!) {
            addExtension(input: $input) {
                status
                message
                extension { extensionId }
            }
        }
        """
        return self.execute(mutation, {'input': ext_data})
    
    # ═══════════════════════════════════════
    # INBOUND ROUTES
    # ═══════════════════════════════════════
    
    def list_inbound_routes(self):
        """Get all inbound routes"""
        query = """
        query {
            fetchAllInboundRoutes {
                status
                inboundRoute {
                    id
                    description
                    did
                    cidnum
                    destination
                }
            }
        }
        """
        return self.execute(query)
    
    def create_inbound_route(self, route_data):
        """Create inbound route (DID to Extension/Queue)"""
        mutation = """
        mutation CreateInboundRoute($input: InboundRouteInput!) {
            addInboundRoute(input: $input) {
                status
                message
                id
            }
        }
        """
        return self.execute(mutation, {'input': route_data})
```

### fwconsole Fallback for Trunks/Outbound Routes
```python
# arrowz/integrations/freepbx_fwconsole.py
import subprocess
import paramiko

class FreePBXConsole:
    """SSH-based fwconsole for operations not in GraphQL"""
    
    def __init__(self, server_config):
        self.host = server_config.ami_host
        self.ssh_user = server_config.ssh_username or 'root'
        self.ssh_key = server_config.get_password('ssh_private_key')
    
    def _execute(self, command):
        """Execute fwconsole command via SSH"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, username=self.ssh_user, pkey=self.ssh_key)
        
        stdin, stdout, stderr = ssh.exec_command(f'fwconsole {command}')
        result = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()
        
        if error:
            raise Exception(f"fwconsole error: {error}")
        return result
    
    def list_trunks(self):
        """List all trunks"""
        output = self._execute('trunks --list')
        # Parse output into structured data
        return self._parse_trunk_list(output)
    
    def create_trunk(self, trunk_data):
        """Create PJSIP trunk"""
        cmd = f"trunks --add pjsip '{trunk_data['name']}' " \
              f"--host '{trunk_data['host']}' " \
              f"--username '{trunk_data['username']}' " \
              f"--secret '{trunk_data['secret']}'"
        return self._execute(cmd)
    
    def reload_config(self):
        """Apply configuration changes"""
        return self._execute('reload')
```

---

## 📼 Recording Playback via Docker Volumes

### Architecture Overview
```
┌─────────────────────┐    ┌─────────────────────┐
│  FreePBX Container  │    │  ERPNext Container  │
│                     │    │                     │
│  /var/spool/        │    │  /recordings/       │
│  asterisk/monitor/  │────│  freepbx/           │
│                     │    │                     │
└─────────────────────┘    └─────────────────────┘
          │                          │
          └──────────────────────────┘
                Docker Shared Volume
                (recordings-data)
```

### Docker Compose Configuration
```yaml
# docker-compose.yml
version: '3.8'

volumes:
  recordings-data:
    driver: local

services:
  freepbx:
    image: tiredofit/freepbx:latest
    volumes:
      - recordings-data:/var/spool/asterisk/monitor
    # ... other config
  
  erpnext:
    image: frappe/erpnext:v15
    volumes:
      - recordings-data:/home/frappe/recordings/freepbx:ro
    # ... other config
```

### Recording Path Configuration
```python
# Arrowz Settings
recording_source = "docker_volume"  # or "http_api"
recording_base_path = "/home/frappe/recordings/freepbx"
recording_url_pattern = "/api/method/arrowz.api.recordings.stream"
```

### Recording API Endpoints
```python
# arrowz/api/recordings.py

@frappe.whitelist()
def stream(call_id):
    """Stream recording file to browser"""
    call_log = frappe.get_doc("Arrowz Universal Call Log", call_id)
    
    # Verify permission
    if not frappe.has_permission("Arrowz Universal Call Log", "read", call_log):
        frappe.throw("No permission to access recording")
    
    # Get file path from Docker volume
    settings = frappe.get_single("Arrowz Settings")
    file_path = os.path.join(
        settings.recording_base_path,
        call_log.recording_filename
    )
    
    if not os.path.exists(file_path):
        frappe.throw("Recording file not found")
    
    # Stream with proper headers
    frappe.local.response.filename = call_log.recording_filename
    frappe.local.response.filecontent = open(file_path, 'rb').read()
    frappe.local.response.type = 'binary'
    frappe.local.response.headers['Content-Type'] = 'audio/wav'

@frappe.whitelist()
def get_recording_url(call_id):
    """Get secure URL for recording playback"""
    call_log = frappe.get_doc("Arrowz Universal Call Log", call_id)
    
    # Generate time-limited token
    token = frappe.generate_hash(length=32)
    cache_key = f"recording_token:{token}"
    frappe.cache().set_value(cache_key, call_id, expires_in_sec=3600)
    
    return {
        'url': f'/api/method/arrowz.api.recordings.stream_secure?token={token}',
        'expires_in': 3600
    }

@frappe.whitelist(allow_guest=True)
def stream_secure(token):
    """Stream recording with token-based auth"""
    cache_key = f"recording_token:{token}"
    call_id = frappe.cache().get_value(cache_key)
    
    if not call_id:
        frappe.throw("Invalid or expired token")
    
    return stream(call_id)
```

### Frontend Recording Player
```javascript
// In Call Log form
frappe.ui.form.on('Arrowz Universal Call Log', {
    refresh(frm) {
        if (frm.doc.has_recording) {
            frm.add_custom_button(__('Play Recording'), () => {
                frm.call('get_recording_url', {
                    call_id: frm.doc.name
                }).then(r => {
                    const dialog = new frappe.ui.Dialog({
                        title: __('Call Recording'),
                        fields: [{
                            fieldtype: 'HTML',
                            fieldname: 'player',
                            options: `
                                <audio controls autoplay style="width:100%">
                                    <source src="${r.message.url}" type="audio/wav">
                                </audio>
                            `
                        }]
                    });
                    dialog.show();
                });
            });
        }
    }
});
```

---

## 🔌 Arrowz Server Configuration

### CC Server Config DocType

| Field | Value | Description |
|-------|-------|-------------|
| Server Name | pbx-01 | Identifier |
| Server Type | FreePBX | Platform |
| SIP Domain | pbx.company.com | SIP realm |
| WebSocket URL | wss://pbx.company.com:8089/ws | WS endpoint |
| AMI Host | pbx.company.com | AMI IP/hostname |
| AMI Port | 5038 | AMI port |
| AMI Username | arrowz | AMI user |
| AMI Secret | (encrypted) | AMI password |
| Is Default | ✅ | Default server |

### Extension Mapping (CC Unified Extension)

| Field | Value |
|-------|-------|
| User | john@company.com |
| Extension | 9001 |
| Server | pbx-01 |
| SIP Username | 9001 |
| SIP Password | (encrypted) |
| Display Name | John Smith |
| Is Active | ✅ |

---

## 🧠 AI Integration (OpenAI)

### Setup Steps

1. **Get OpenAI API Key**
   - Visit https://platform.openai.com/api-keys
   - Create new secret key
   - Copy key (shown only once)

2. **Configure in Arrowz**
   ```
   ContactCall Settings > AI Tab:
   - OpenAI API Key: sk-proj-xxxxx...
   - AI Model: gpt-4o-mini (recommended)
   - Enable Sentiment Analysis: ✅
   - Enable Transcription: ✅
   - Enable Coaching Suggestions: ✅
   ```

3. **Model Selection Guide**

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| gpt-4o-mini | Fast | Low | Production use |
| gpt-4o | Medium | Medium | Complex analysis |
| gpt-4-turbo | Slower | High | Maximum quality |

### Sentiment Analysis Flow

```
1. User speaks → Browser Speech API transcribes
2. Transcript sent to backend
3. arrowz.api.ai.analyze_sentiment called
4. OpenAI analyzes with prompt
5. Response: {sentiment: "positive", score: 0.85, emotion: "happy"}
6. UI updated with sentiment indicator
7. Stored in Arrowz Sentiment Log
```

### Custom AI Prompts

Edit in Arrowz Settings:
```
Sentiment Prompt:
"Analyze the following customer service conversation segment for sentiment. 
Return JSON: {sentiment: positive|negative|neutral, score: 0-1, emotion: string}"

Coaching Prompt:
"Based on this conversation, suggest 1-2 brief coaching tips for the agent.
Focus on empathy, clarity, and resolution."
```

---

## 🔗 CRM Integration

### Automatic Linking

Arrowz automatically links calls to CRM records:

```
Incoming Call Flow:
1. Call received → extract caller number
2. Search Contact.phone, Contact.mobile_no
3. Search Lead.mobile_no, Lead.phone
4. Search Customer → linked Contact
5. If found → popup form, link to call log
6. If not found → offer to create new Contact/Lead
```

### Search Priority
1. Contact (exact match on mobile_no)
2. Contact (exact match on phone)
3. Lead (exact match on mobile_no)
4. Customer (via linked contacts)
5. Supplier (via linked contacts)

### Auto-Create Options

```python
# In Arrowz Settings
auto_create_on_new_call = True
default_doctype = "Lead"  # or "Contact"
default_lead_source = "Phone Call"
```

---

## 🌐 WebSocket/Socket.IO

### Architecture
```
Browser ←→ Socket.IO (port 9000) ←→ Frappe/Redis ←→ Backend
   ↓
JsSIP ←→ Asterisk WebSocket (port 8089)
```

### Events Published

| Event | Direction | Data |
|-------|-----------|------|
| `call_started` | Server→Client | call_id, direction, party |
| `call_ended` | Server→Client | call_id, duration, disposition |
| `presence_update` | Bidirectional | user, status |
| `ai_suggestion` | Server→Client | suggestion_text, priority |
| `sentiment_update` | Server→Client | sentiment, score |

### Example Handler
```javascript
frappe.realtime.on('call_started', (data) => {
    console.log('Call started:', data);
    // Handle incoming call notification
});
```

---

## 📊 Reporting Integration

### Call Log Schema

All calls logged to `Arrowz Universal Call Log`:

```
- uniqueid (primary key from Asterisk)
- extension, phone_number
- direction (inbound/outbound/internal)
- start_time, answer_time, end_time
- duration, billable_duration
- disposition (ANSWERED/NO ANSWER/BUSY/FAILED)
- linked_doctype, linked_docname
- recording_url (if enabled)
- sentiment_score, ai_summary
```

### Standard Reports

1. **Call Volume Report** - Calls by hour/day/week
2. **Agent Performance** - Calls per agent, avg duration
3. **Missed Calls** - Unanswered incoming calls
4. **Sentiment Trends** - Customer sentiment over time

### Custom Script Reports

```python
# Example: Calls by Customer
def get_data(filters):
    return frappe.db.sql("""
        SELECT 
            linked_docname as customer,
            COUNT(*) as total_calls,
            AVG(duration) as avg_duration
        FROM `tabArrowz Universal Call Log`
        WHERE linked_doctype = 'Customer'
        GROUP BY linked_docname
        ORDER BY total_calls DESC
    """, as_dict=1)
```

---

## 🔒 Security Considerations

### SIP Security
- Always use WSS (encrypted WebSocket)
- Use strong SIP passwords
- Limit AMI access by IP
- Enable SIP ALG bypass if needed

### API Security
- All API endpoints require login
- Role-based permissions
- API key rotation for OpenAI
- Call recordings access control

### Data Privacy
- Recording consent notices
- Transcription data retention policy
- GDPR-compliant data deletion

---

*Next: See `06-SUGGESTIONS.md` for improvement proposals*
