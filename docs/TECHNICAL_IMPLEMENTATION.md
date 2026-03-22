# 🛠️ Arrowz Technical Implementation Details

> **تفاصيل التنفيذ التقني - للاستمرار في التطوير بدون الرجوع للمحادثات السابقة**
> **Last Updated:** February 17, 2026

---

## 📞 WebRTC Softphone Implementation

### File: `arrowz/public/js/softphone_v2.js`

#### Core Object Structure
```javascript
arrowz.softphone = {
    // === SIP/WebRTC ===
    ua: null,                    // JsSIP UserAgent instance
    remoteAudio: null,           // <audio> element for remote stream
    
    // === Multi-Line Support (NEW) ===
    sessions: [],                // Array of RTCSession objects
    activeLineIndex: 0,          // Currently focused line (0-3)
    maxLines: 4,                 // Maximum concurrent calls
    callStartTimes: {},          // { sessionId: Date } - for duration
    _callNumbers: {},            // { lineIndex: phoneNumber }
    
    // === UI State ===
    isDropdownOpen: false,
    isMuted: false,
    isOnHold: false,
    currentNumber: '',
    
    // === Configuration ===
    config: {
        wsServer: '',            // wss://pbx:8089/ws
        sipUri: '',              // sip:ext@pbx
        password: '',
        realm: '',
        displayName: ''
    }
};
```

#### Key Methods Explained

##### 1. `initSoftphone()`
```javascript
// Initializes JsSIP UserAgent and registers with PBX
// Called on page load if user has extension assigned
async initSoftphone() {
    // 1. Fetch config from server
    const config = await frappe.call({ 
        method: 'arrowz.api.webrtc.get_webrtc_config' 
    });
    
    // 2. Create UserAgent
    const socket = new JsSIP.WebSocketInterface(config.wsServer);
    this.ua = new JsSIP.UA({
        sockets: [socket],
        uri: config.sipUri,
        password: config.password,
        // ... other options
    });
    
    // 3. Setup event handlers
    this.ua.on('newRTCSession', (data) => this.handleNewSession(data));
    
    // 4. Start registration
    this.ua.start();
}
```

##### 2. `makeCall(number)` - Multi-Line Version
```javascript
makeCall(number) {
    // Find available line
    const lineIndex = this.findAvailableLine();
    if (lineIndex === -1) {
        frappe.msgprint(__('All lines busy'));
        return;
    }
    
    // Create call session
    const session = this.ua.call(`sip:${number}@${this.config.realm}`, {
        mediaConstraints: { audio: true, video: false },
        rtcOfferConstraints: { offerToReceiveAudio: true }
    });
    
    // Store in sessions array
    this.sessions[lineIndex] = session;
    this._callNumbers[lineIndex] = number;
    
    // Setup events for this session
    this.setupSessionEvents(session, lineIndex);
    
    // Switch to this line
    this.switchToLine(lineIndex);
}
```

##### 3. `handleNewSession(data)` - Incoming Calls
```javascript
handleNewSession(data) {
    if (data.originator === 'remote') {
        // Incoming call
        const lineIndex = this.findAvailableLine();
        if (lineIndex === -1) {
            data.session.terminate();
            return;
        }
        
        this.sessions[lineIndex] = data.session;
        this._callNumbers[lineIndex] = data.request.from.display_name;
        
        this.setupSessionEvents(data.session, lineIndex);
        this.showIncomingCallUI(this._callNumbers[lineIndex]);
    }
}
```

##### 4. `switchToLine(index)` - Line Switching
```javascript
switchToLine(index) {
    if (index < 0 || index >= this.maxLines) return;
    if (!this.sessions[index]) return;
    
    // Hold all other lines
    this.holdAllExcept(index);
    
    // Unhold the selected line
    if (this.sessions[index] && !this.sessions[index].isEnded()) {
        this.sessions[index].unhold();
    }
    
    this.activeLineIndex = index;
    this.updateUI();
}
```

##### 5. UI Methods
```javascript
showDialerUI()          // Dialpad with active calls indicator
showActiveCallUI()      // In-call screen (single call or redirects to multi)
showIncomingCallUI()    // Incoming call with answer/reject
showMultiLineCallUI()   // Multi-line management UI
```

#### CSS Inline Styles Pattern
Due to CSS specificity issues, we use inline styles:
```javascript
// Instead of relying on class styles
dropdown.innerHTML = `
    <div class="sp-call-screen" style="padding:12px;">
        <button style="width:48px;height:48px;border-radius:50%;">
            ...
        </button>
    </div>
`;
```

---

## 💬 Omni-Channel Implementation

### WhatsApp Cloud API

#### File: `arrowz/api/omni.py`
```python
@frappe.whitelist()
def send_whatsapp_message(recipient, message, message_type='text', 
                          media_url=None, template_name=None):
    """
    Send WhatsApp message via Cloud API
    
    Args:
        recipient: Phone number with country code
        message: Text content
        message_type: 'text', 'image', 'document', 'template'
        media_url: URL for media messages
        template_name: For template messages
    """
    settings = frappe.get_single('Arrowz Settings')
    
    headers = {
        'Authorization': f'Bearer {settings.whatsapp_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'messaging_product': 'whatsapp',
        'to': recipient,
        'type': message_type
    }
    
    if message_type == 'text':
        payload['text'] = {'body': message}
    elif message_type == 'template':
        payload['template'] = {
            'name': template_name,
            'language': {'code': 'en'}
        }
    
    response = requests.post(
        f'https://graph.facebook.com/v18.0/{settings.whatsapp_phone_id}/messages',
        headers=headers,
        json=payload
    )
    
    return response.json()
```

### Telegram Bot API

```python
@frappe.whitelist()
def send_telegram_message(chat_id, message, message_type='text', 
                          media_url=None, reply_markup=None):
    """
    Send Telegram message via Bot API
    """
    settings = frappe.get_single('Arrowz Settings')
    
    if message_type == 'text':
        endpoint = 'sendMessage'
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
    elif message_type == 'photo':
        endpoint = 'sendPhoto'
        payload = {
            'chat_id': chat_id,
            'photo': media_url,
            'caption': message
        }
    
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    
    response = requests.post(
        f'https://api.telegram.org/bot{settings.telegram_token}/{endpoint}',
        json=payload
    )
    
    return response.json()
```

---

## 🎥 OpenMeetings Integration

### File: `arrowz/integrations/openmeetings/api.py`

```python
class OpenMeetingsAPI:
    def __init__(self):
        settings = frappe.get_single('Arrowz Settings')
        self.base_url = settings.openmeetings_url
        self.admin_user = settings.openmeetings_user
        self.admin_pass = settings.openmeetings_password
        self.sid = None
    
    def login(self):
        """Get session ID"""
        response = requests.get(
            f'{self.base_url}/services/user/login',
            params={'user': self.admin_user, 'pass': self.admin_pass}
        )
        self.sid = response.json().get('serviceResult', {}).get('message')
        return self.sid
    
    def create_room(self, name, room_type='conference', capacity=25):
        """Create a new meeting room"""
        payload = {
            'sid': self.sid,
            'room': {
                'name': name,
                'type': room_type,
                'capacity': capacity,
                'isPublic': False
            }
        }
        return requests.post(
            f'{self.base_url}/services/room/add',
            json=payload
        ).json()
    
    def get_room_hash(self, room_id, user_name, is_moderator=False):
        """Generate secure hash for room entry"""
        payload = {
            'sid': self.sid,
            'roomId': room_id,
            'user': {
                'firstname': user_name,
                'moderator': is_moderator
            }
        }
        return requests.post(
            f'{self.base_url}/services/user/hash',
            json=payload
        ).json()
```

---

## 📋 Lead Form Extension

### File: `arrowz/public/js/lead.js`

```javascript
frappe.ui.form.on("Lead", {
    refresh: function(frm) {
        if (frm.is_new()) return;
        arrowz.lead.add_communication_buttons(frm);
    }
});

arrowz.lead.add_communication_buttons = function(frm) {
    const phone = frm.doc.mobile_no || frm.doc.phone;
    if (!phone) return;
    
    // WhatsApp with brand SVG icon
    frm.add_custom_button(
        `<span class="flex items-center gap-2">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="#25D366">
                <path d="M17.472 14.382c-.297-.149..."/>
            </svg>
            <span>WhatsApp</span>
        </span>`,
        () => arrowz.lead.open_whatsapp(frm),
        __("Arrowz")
    );
    
    // Telegram with brand SVG icon
    frm.add_custom_button(
        `<span class="flex items-center gap-2">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="#0088cc">
                <path d="M11.944 0A12 12 0 0 0..."/>
            </svg>
            <span>Telegram</span>
        </span>`,
        () => arrowz.lead.open_telegram(frm),
        __("Arrowz")
    );
};
```

---

## 🔗 hooks.py Configuration

### Key Sections:
```python
# App includes
app_include_js = [
    "/assets/arrowz/js/softphone_v2.js",
    "/assets/arrowz/js/phone_actions.js",
    "/assets/arrowz/js/omni_panel.js",
]

app_include_css = "/assets/arrowz/css/arrowz.css"

# DocType form extensions
doctype_js = {
    "Lead": "public/js/lead.js",
    "Customer": "public/js/customer.js",
    "Contact": "public/js/contact.js",
}

# Scheduled tasks
scheduler_events = {
    "cron": {
        "*/1 * * * *": [
            "arrowz.tasks.process_telegram_updates"
        ]
    },
    "daily": [
        "arrowz.tasks.cleanup_old_sessions"
    ]
}

# Realtime events
has_permission = {
    "AZ Call Log": "arrowz.permissions.az_call_log_permission"
}
```

---

## 🗄️ Database Schema Notes

### AZ Call Log
```
- name: Primary key (AUTO)
- uniqueid: Asterisk unique ID
- extension: Caller extension
- caller_id: Caller number
- callee_id: Called number
- direction: Inbound/Outbound
- status: Ringing/In Progress/Answered/Missed/Ended
- start_time: datetime
- end_time: datetime
- duration: seconds
- recording_url: Link to recording
```

### AZ Conversation Session
```
- name: Primary key
- contact: Link to Contact
- channel: whatsapp/telegram/sms
- provider: Link to AZ Omni Provider
- status: Open/Closed
- last_message_time: datetime
- unread_count: int
```

---

## 🔧 Troubleshooting Guide

### WebRTC Issues
1. **No audio**: Check microphone permissions in browser
2. **Registration failed**: Verify WebSocket URL and credentials
3. **Call drops**: Check NAT/firewall settings, enable STUN

### CSS Not Applying
- Use inline styles in template strings
- Check browser cache (Ctrl+Shift+R)
- Run `bench build --app arrowz --force`

### API Errors
```python
# Enable debug logging
frappe.logger().debug(f"API call: {params}")

# Check permissions
frappe.has_permission("DocType", "read")
```

---

*This document contains implementation details for continuing development without referring to chat history.*
