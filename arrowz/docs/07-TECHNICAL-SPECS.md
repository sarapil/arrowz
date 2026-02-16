# Arrowz Technical Specifications
## المواصفات الفنية التنفيذية - القرارات المُتخذة

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ERPNext/Frappe                           │
│                    (العقل المدبر - Orchestrator)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Arrowz UI   │  │ Call Logs   │  │ CRM Integration         │ │
│  │ (Navbar)    │  │ & Analytics │  │ (Contact/Lead/Customer) │ │
│  └──────┬──────┘  └─────────────┘  └─────────────────────────┘ │
│         │                                                       │
│  ┌──────▼──────────────────────────────────────────────────┐   │
│  │              Arrowz Backend APIs                         │   │
│  │  webrtc.py │ ai.py │ crm.py │ pbx.py │ sms.py          │   │
│  └──────┬─────────────────┬────────────────────────────────┘   │
└─────────┼─────────────────┼─────────────────────────────────────┘
          │                 │
          │ WebRTC/WSS      │ GraphQL + AMI
          │                 │
┌─────────▼─────────────────▼─────────────────────────────────────┐
│                     Asterisk/FreePBX 17                         │
│                    (محرك الاتصال - Engine)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ PJSIP       │  │ AMI Events  │  │ GraphQL API             │ │
│  │ (WebRTC)    │  │ (Real-time) │  │ (Configuration)         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Recordings (/var/spool/asterisk/monitor) ──► Docker Vol │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principles
| Component | Role | Protocol |
|-----------|------|----------|
| **Asterisk** | محرك الاتصال | AMI (السرعة) + PJSIP (المرونة) |
| **ERPNext** | العقل المدبر | REST + Socket.IO |
| **GraphQL** | تكوين PBX | HTTP/HTTPS |
| **WebRTC** | الصوت/الفيديو | WSS + SRTP |

---

## 1️⃣ Softphone UI - Navbar Multi-Tab

### 1.1 Navbar Integration
```javascript
// File: arrowz/public/js/navbar_phone.js

class ArrowzNavbarPhone {
    constructor() {
        this.popup = null;
        this.currentTab = 'dialer';
        this.lines = [];
        this.activeLine = null;
    }
    
    init() {
        this.addNavbarIcon();
        this.createPopup();
        this.loadUserLines();
        this.subscribeToEvents();
    }
    
    addNavbarIcon() {
        const navbarRight = document.querySelector('.navbar-right');
        if (!navbarRight) return;
        
        const phoneItem = document.createElement('li');
        phoneItem.className = 'nav-item arrowz-phone-nav';
        phoneItem.innerHTML = `
            <a class="nav-link" href="#" id="arrowz-phone-trigger" title="Softphone">
                <svg class="icon icon-sm">
                    <use href="#icon-call"></use>
                </svg>
                <span class="arrowz-badge hidden" id="arrowz-call-badge"></span>
            </a>
        `;
        
        // Insert before settings
        const settingsItem = navbarRight.querySelector('.dropdown');
        navbarRight.insertBefore(phoneItem, settingsItem);
        
        // Bind click
        document.getElementById('arrowz-phone-trigger').addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.togglePopup();
        });
    }
    
    createPopup() {
        this.popup = new ArrowzSoftphonePopup(this);
        document.body.appendChild(this.popup.element);
    }
    
    togglePopup() {
        this.popup.toggle();
    }
    
    showTab(tabName) {
        this.currentTab = tabName;
        this.popup.showTab(tabName);
    }
    
    async loadUserLines() {
        try {
            const result = await frappe.call({
                method: 'arrowz.api.sip.get_user_lines'
            });
            this.lines = result.message || [];
            this.activeLine = this.lines[0] || null;
            this.popup.updateLineSelector(this.lines);
        } catch (e) {
            console.error('Failed to load lines:', e);
        }
    }
    
    subscribeToEvents() {
        // Incoming call event from AMI
        frappe.realtime.on('arrowz_incoming_call', (data) => {
            this.handleIncomingCall(data);
        });
        
        // Call state changes
        frappe.realtime.on('arrowz_call_state', (data) => {
            this.popup.updateCallState(data);
        });
    }
    
    handleIncomingCall(data) {
        this.popup.show();
        this.showTab('incoming');
        this.popup.setIncomingCaller(data.caller_id, data.caller_name);
    }
}

// Initialize on page load
frappe.ready(() => {
    if (frappe.session.user !== 'Guest') {
        window.arrowzPhone = new ArrowzNavbarPhone();
        window.arrowzPhone.init();
    }
});
```

### 1.2 Multi-Tab Popup
```javascript
// File: arrowz/public/js/softphone_popup.js

class ArrowzSoftphonePopup {
    constructor(parent) {
        this.parent = parent;
        this.element = this.createElement();
        this.visible = false;
        this.callTimer = null;
        this.callStartTime = null;
    }
    
    createElement() {
        const popup = document.createElement('div');
        popup.className = 'arrowz-softphone-popup hidden';
        popup.id = 'arrowz-softphone-popup';
        popup.innerHTML = this.getHTML();
        this.bindEvents(popup);
        return popup;
    }
    
    getHTML() {
        return `
            <!-- Header -->
            <div class="arrowz-popup-header">
                <div class="arrowz-line-selector">
                    <select id="arrowz-line-select">
                        <option value="">Loading lines...</option>
                    </select>
                </div>
                <button class="arrowz-popup-close" id="arrowz-popup-close">
                    <svg class="icon icon-xs"><use href="#icon-close"></use></svg>
                </button>
            </div>
            
            <!-- Tabs -->
            <div class="arrowz-popup-tabs">
                <button class="arrowz-tab active" data-tab="dialer">
                    <svg class="icon icon-sm"><use href="#icon-grid"></use></svg>
                    <span>Dialer</span>
                </button>
                <button class="arrowz-tab" data-tab="active">
                    <svg class="icon icon-sm"><use href="#icon-call"></use></svg>
                    <span>Call</span>
                </button>
                <button class="arrowz-tab" data-tab="history">
                    <svg class="icon icon-sm"><use href="#icon-history"></use></svg>
                    <span>History</span>
                </button>
                <button class="arrowz-tab hidden" data-tab="incoming" id="arrowz-incoming-tab">
                    <svg class="icon icon-sm"><use href="#icon-incoming-call"></use></svg>
                    <span>Incoming</span>
                </button>
            </div>
            
            <!-- Tab Panels -->
            <div class="arrowz-tab-content">
                ${this.getDialerTabHTML()}
                ${this.getActiveTabHTML()}
                ${this.getHistoryTabHTML()}
                ${this.getIncomingTabHTML()}
            </div>
        `;
    }
    
    getDialerTabHTML() {
        return `
            <div class="arrowz-tab-panel active" id="arrowz-panel-dialer">
                <div class="arrowz-dialer">
                    <div class="arrowz-phone-input-wrap">
                        <input type="tel" 
                               id="arrowz-phone-input" 
                               class="arrowz-phone-input"
                               placeholder="Enter number..."
                               inputmode="tel"
                               autocomplete="tel">
                        <button class="arrowz-keypad-toggle" id="arrowz-keypad-toggle" 
                                title="Show Keypad">
                            <svg class="icon icon-sm"><use href="#icon-grid"></use></svg>
                        </button>
                    </div>
                    
                    <div class="arrowz-keypad hidden" id="arrowz-keypad">
                        <div class="arrowz-keypad-row">
                            <button class="arrowz-key" data-digit="1">1</button>
                            <button class="arrowz-key" data-digit="2">2</button>
                            <button class="arrowz-key" data-digit="3">3</button>
                        </div>
                        <div class="arrowz-keypad-row">
                            <button class="arrowz-key" data-digit="4">4</button>
                            <button class="arrowz-key" data-digit="5">5</button>
                            <button class="arrowz-key" data-digit="6">6</button>
                        </div>
                        <div class="arrowz-keypad-row">
                            <button class="arrowz-key" data-digit="7">7</button>
                            <button class="arrowz-key" data-digit="8">8</button>
                            <button class="arrowz-key" data-digit="9">9</button>
                        </div>
                        <div class="arrowz-keypad-row">
                            <button class="arrowz-key" data-digit="*">*</button>
                            <button class="arrowz-key" data-digit="0">0</button>
                            <button class="arrowz-key" data-digit="#">#</button>
                        </div>
                    </div>
                    
                    <button class="arrowz-call-btn" id="arrowz-call-btn">
                        <svg class="icon icon-sm"><use href="#icon-call"></use></svg>
                        Call
                    </button>
                </div>
            </div>
        `;
    }
    
    getActiveTabHTML() {
        return `
            <div class="arrowz-tab-panel" id="arrowz-panel-active">
                <div class="arrowz-active-call">
                    <div class="arrowz-call-info">
                        <div class="arrowz-caller-name" id="arrowz-active-name">--</div>
                        <div class="arrowz-caller-number" id="arrowz-active-number">--</div>
                    </div>
                    
                    <div class="arrowz-call-state" id="arrowz-call-state">No Active Call</div>
                    <div class="arrowz-call-timer hidden" id="arrowz-call-timer">00:00</div>
                    
                    <div class="arrowz-call-controls">
                        <button class="arrowz-control-btn" id="arrowz-mute-btn" disabled>
                            <svg class="icon icon-sm"><use href="#icon-mic"></use></svg>
                            <span>Mute</span>
                        </button>
                        <button class="arrowz-control-btn" id="arrowz-hold-btn" disabled>
                            <svg class="icon icon-sm"><use href="#icon-pause"></use></svg>
                            <span>Hold</span>
                        </button>
                        <button class="arrowz-control-btn" id="arrowz-transfer-btn" disabled>
                            <svg class="icon icon-sm"><use href="#icon-share"></use></svg>
                            <span>Transfer</span>
                        </button>
                    </div>
                    
                    <!-- In-Call Actions (WhatsApp/SMS) -->
                    <div class="arrowz-incall-actions hidden" id="arrowz-incall-actions">
                        <button class="arrowz-action-btn" id="arrowz-whatsapp-btn" title="WhatsApp">
                            <i class="fab fa-whatsapp"></i>
                        </button>
                        <button class="arrowz-action-btn" id="arrowz-sms-btn" title="SMS">
                            <svg class="icon icon-sm"><use href="#icon-message"></use></svg>
                        </button>
                    </div>
                    
                    <button class="arrowz-hangup-btn" id="arrowz-hangup-btn" disabled>
                        <svg class="icon icon-sm"><use href="#icon-call-end"></use></svg>
                        End Call
                    </button>
                </div>
            </div>
        `;
    }
    
    getHistoryTabHTML() {
        return `
            <div class="arrowz-tab-panel" id="arrowz-panel-history">
                <div class="arrowz-history">
                    <div class="arrowz-history-filters">
                        <select id="arrowz-filter-type">
                            <option value="all">All Calls</option>
                            <option value="outbound">Outbound</option>
                            <option value="inbound">Inbound</option>
                            <option value="missed">Missed</option>
                        </select>
                        <select id="arrowz-filter-line">
                            <option value="all">All Lines</option>
                        </select>
                    </div>
                    <div class="arrowz-history-list" id="arrowz-history-list">
                        <div class="arrowz-loading">Loading...</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    getIncomingTabHTML() {
        return `
            <div class="arrowz-tab-panel" id="arrowz-panel-incoming">
                <div class="arrowz-incoming">
                    <div class="arrowz-incoming-avatar">
                        <svg class="icon icon-lg"><use href="#icon-user"></use></svg>
                    </div>
                    <div class="arrowz-incoming-info">
                        <div class="arrowz-incoming-name" id="arrowz-incoming-name">Unknown</div>
                        <div class="arrowz-incoming-number" id="arrowz-incoming-number">+966...</div>
                    </div>
                    <div class="arrowz-incoming-actions">
                        <button class="arrowz-answer-btn" id="arrowz-answer-btn">
                            <svg class="icon icon-sm"><use href="#icon-call"></use></svg>
                            Answer
                        </button>
                        <button class="arrowz-reject-btn" id="arrowz-reject-btn">
                            <svg class="icon icon-sm"><use href="#icon-call-end"></use></svg>
                            Reject
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    // ... Event binding and methods continue
}
```

### 1.3 Mobile Optimization
```css
/* File: arrowz/public/css/softphone.css */

/* Mobile-first responsive design */
@media (max-width: 768px) {
    .arrowz-softphone-popup {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        top: auto;
        width: 100%;
        max-height: 75vh;
        border-radius: 16px 16px 0 0;
        animation: slideUp 0.3s ease;
    }
    
    @keyframes slideUp {
        from { transform: translateY(100%); }
        to { transform: translateY(0); }
    }
    
    .arrowz-phone-input {
        font-size: 1.5rem;
        text-align: center;
        padding: 1rem;
    }
    
    .arrowz-keypad {
        display: grid !important; /* Always show on mobile */
    }
    
    .arrowz-key {
        width: 70px;
        height: 70px;
        font-size: 1.75rem;
    }
}

/* Ensure numeric input on mobile */
.arrowz-phone-input {
    -webkit-appearance: none;
    -moz-appearance: textfield;
}
```

---

## 2️⃣ Call Transfer - Policy & Implementation

### 2.1 Transfer Policy
| Role | Attended Transfer | Blind Transfer |
|------|-------------------|----------------|
| Agent | ✅ Enabled (Default) | ❌ Disabled |
| Supervisor | ✅ Enabled | ✅ Enabled |
| Manager | ✅ Enabled | ✅ Enabled |

### 2.2 FreePBX Configuration
```ini
# Feature Codes for Agents (restrict blind transfer)
# Applications > Feature Codes

# In-Call Attended Transfer: *2 (enabled)
# In-Call Blind Transfer: ## (disabled for agents via Class of Service)
```

### 2.3 Transfer Implementation
```javascript
// File: arrowz/public/js/transfer.js

class ArrowzTransfer {
    constructor(softphone) {
        this.softphone = softphone;
        this.transferDialog = null;
    }
    
    canDoBlindTransfer() {
        return frappe.user_roles.some(role => 
            ['Supervisor', 'System Manager', 'Call Center Manager'].includes(role)
        );
    }
    
    async showTransferDialog() {
        // Get lead info before transfer
        const leadInfo = await this.getPreTransferInfo();
        
        const dialog = new frappe.ui.Dialog({
            title: __('Transfer Call'),
            fields: [
                {
                    fieldtype: 'HTML',
                    fieldname: 'lead_info',
                    options: this.renderLeadInfo(leadInfo)
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'target',
                    label: __('Transfer To'),
                    placeholder: 'Extension or number...',
                    reqd: 1
                },
                {
                    fieldtype: 'Section Break',
                    label: __('Quick Transfer')
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'quick_buttons',
                    options: this.renderQuickTransferButtons()
                }
            ],
            primary_action_label: __('Attended Transfer'),
            primary_action: (values) => {
                this.attendedTransfer(values.target);
                dialog.hide();
            },
            secondary_action_label: this.canDoBlindTransfer() ? __('Blind Transfer') : null,
            secondary_action: this.canDoBlindTransfer() ? (values) => {
                this.blindTransfer(values.target);
                dialog.hide();
            } : null
        });
        
        dialog.show();
        this.transferDialog = dialog;
    }
    
    async getPreTransferInfo() {
        const phoneNumber = this.softphone.currentCallNumber;
        const result = await frappe.call({
            method: 'arrowz.api.crm.get_lead_transfer_info',
            args: { phone: phoneNumber }
        });
        return result.message || {};
    }
    
    renderLeadInfo(info) {
        if (!info.found) return '';
        
        return `
            <div class="arrowz-pre-transfer-info">
                <div class="info-row">
                    <strong>Lead Status:</strong> 
                    <span class="badge">${info.status || 'N/A'}</span>
                </div>
                <div class="info-row">
                    <strong>Last Objection:</strong> 
                    <span>${info.last_objection || 'None'}</span>
                </div>
                <div class="info-row">
                    <strong>Offer Code:</strong> 
                    <span>${info.offer_code || 'N/A'}</span>
                </div>
            </div>
        `;
    }
    
    async attendedTransfer(target) {
        // 1. Hold current call
        this.softphone.holdCall();
        
        // 2. Call target
        const consultSession = await this.softphone.makeConsultCall(target);
        
        // 3. Show confirm dialog
        this.showTransferConfirmation(consultSession, target);
    }
    
    blindTransfer(target) {
        if (!this.canDoBlindTransfer()) {
            frappe.msgprint(__('Blind transfer is only available for supervisors'));
            return;
        }
        
        this.softphone.currentSession.refer(`sip:${target}@${this.softphone.domain}`);
        this.logTransfer('Blind', target);
    }
    
    async logTransfer(type, target) {
        await frappe.call({
            method: 'arrowz.api.call_log.log_transfer',
            args: {
                call_id: this.softphone.currentCallId,
                transfer_type: type,
                target_extension: target,
                source_agent: frappe.session.user
            }
        });
    }
}
```

### 2.4 Transfer Log DocType
```python
# DocType: Arrowz Transfer Log
{
    "doctype": "Arrowz Transfer Log",
    "fields": [
        {"fieldname": "call_log", "fieldtype": "Link", "options": "Arrowz Universal Call Log"},
        {"fieldname": "transfer_type", "fieldtype": "Select", "options": "Attended\nBlind"},
        {"fieldname": "transfer_status", "fieldtype": "Select", "options": "Success\nFailed\nCancelled"},
        {"fieldname": "time_to_close", "fieldtype": "Duration"},
        {"fieldname": "source_agent", "fieldtype": "Link", "options": "User"},
        {"fieldname": "target_closer", "fieldtype": "Link", "options": "User"},
        {"fieldname": "campaign_id", "fieldtype": "Data"},
        {"fieldname": "lead_status_before", "fieldtype": "Data"},
        {"fieldname": "lead_status_after", "fieldtype": "Data"}
    ]
}
```

---

## 3️⃣ Recording Playback - Docker Shared Volume

### 3.1 Docker Configuration
```yaml
# docker-compose.override.yml

services:
  frappe:
    volumes:
      - pbx_recordings:/home/frappe/frappe-bench/sites/recordings:ro
      
  freepbx:
    volumes:
      - pbx_recordings:/var/spool/asterisk/monitor:rw

volumes:
  pbx_recordings:
    driver: local
```

### 3.2 Recording API
```python
# File: arrowz/api/recordings.py

import frappe
import os
from frappe.utils import get_files_path

RECORDINGS_PATH = '/home/frappe/frappe-bench/sites/recordings'

@frappe.whitelist()
def get_recording_url(call_id):
    """Get streaming URL for a call recording"""
    call_log = frappe.get_doc("Arrowz Universal Call Log", call_id)
    
    if not call_log.recording_path:
        return {"error": "No recording found"}
    
    # Verify file exists
    full_path = os.path.join(RECORDINGS_PATH, call_log.recording_path)
    if not os.path.exists(full_path):
        return {"error": "Recording file not found"}
    
    # Generate temporary token
    token = frappe.generate_hash(length=32)
    frappe.cache().set_value(f"recording_token:{token}", call_id, expires_in_sec=3600)
    
    return {
        "url": f"/api/method/arrowz.api.recordings.stream?token={token}",
        "duration": call_log.duration,
        "filename": os.path.basename(call_log.recording_path)
    }

@frappe.whitelist(allow_guest=True)
def stream(token):
    """Stream recording file"""
    call_id = frappe.cache().get_value(f"recording_token:{token}")
    if not call_id:
        frappe.throw("Invalid or expired token", frappe.AuthenticationError)
    
    call_log = frappe.get_doc("Arrowz Universal Call Log", call_id)
    full_path = os.path.join(RECORDINGS_PATH, call_log.recording_path)
    
    if not os.path.exists(full_path):
        frappe.throw("Recording not found")
    
    # Return file response
    with open(full_path, 'rb') as f:
        content = f.read()
    
    frappe.local.response.filename = os.path.basename(full_path)
    frappe.local.response.filecontent = content
    frappe.local.response.type = "download"
```

### 3.3 Recording Player Component
```javascript
// File: arrowz/public/js/recording_player.js

class ArrowzRecordingPlayer {
    constructor(callId, container) {
        this.callId = callId;
        this.container = container;
        this.audio = null;
        this.playbackRate = 1;
    }
    
    async load() {
        const result = await frappe.call({
            method: 'arrowz.api.recordings.get_recording_url',
            args: { call_id: this.callId }
        });
        
        if (result.message.error) {
            this.showError(result.message.error);
            return;
        }
        
        this.render(result.message);
    }
    
    render(data) {
        this.container.innerHTML = `
            <div class="arrowz-recording-player">
                <audio id="arrowz-audio-${this.callId}" preload="metadata">
                    <source src="${data.url}" type="audio/wav">
                </audio>
                
                <div class="arrowz-player-controls">
                    <button class="arrowz-play-btn" id="play-${this.callId}">
                        <svg class="icon"><use href="#icon-play"></use></svg>
                    </button>
                    
                    <div class="arrowz-progress">
                        <input type="range" class="arrowz-progress-bar" 
                               id="progress-${this.callId}" value="0" min="0" max="100">
                        <span class="arrowz-time" id="time-${this.callId}">00:00 / ${data.duration}</span>
                    </div>
                    
                    <div class="arrowz-speed-controls">
                        <button class="arrowz-speed-btn" data-speed="0.75">0.75x</button>
                        <button class="arrowz-speed-btn active" data-speed="1">1x</button>
                        <button class="arrowz-speed-btn" data-speed="1.5">1.5x</button>
                        <button class="arrowz-speed-btn" data-speed="2">2x</button>
                    </div>
                    
                    <div class="arrowz-skip-controls">
                        <button class="arrowz-skip-btn" data-skip="-10">
                            <svg class="icon"><use href="#icon-skip-back"></use></svg>
                            10s
                        </button>
                        <button class="arrowz-skip-btn" data-skip="10">
                            10s
                            <svg class="icon"><use href="#icon-skip-forward"></use></svg>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        this.bindEvents();
    }
    
    bindEvents() {
        this.audio = document.getElementById(`arrowz-audio-${this.callId}`);
        
        // Play/Pause
        document.getElementById(`play-${this.callId}`).addEventListener('click', () => {
            if (this.audio.paused) {
                this.audio.play();
            } else {
                this.audio.pause();
            }
        });
        
        // Speed buttons
        this.container.querySelectorAll('.arrowz-speed-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.setSpeed(parseFloat(btn.dataset.speed));
            });
        });
        
        // Skip buttons
        this.container.querySelectorAll('.arrowz-skip-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.audio.currentTime += parseInt(btn.dataset.skip);
            });
        });
    }
    
    setSpeed(speed) {
        this.audio.playbackRate = speed;
        this.playbackRate = speed;
    }
}
```

---

## 4️⃣ FreePBX Integration

### 4.1 GraphQL Client
```python
# File: arrowz/api/pbx_graphql.py

import frappe
import requests
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

class FreePBXGraphQL:
    def __init__(self):
        self.settings = frappe.get_single("Arrowz PBX Settings")
        self._client = None
    
    @property
    def client(self):
        if not self._client:
            transport = RequestsHTTPTransport(
                url=f"{self.settings.pbx_url}/admin/api/api/gql",
                headers={
                    'Authorization': f'Bearer {self.settings.get_password("api_token")}'
                },
                verify=self.settings.verify_ssl
            )
            self._client = Client(transport=transport, fetch_schema_from_transport=True)
        return self._client
    
    # Extensions
    def get_all_extensions(self):
        query = gql("""
            query {
                fetchAllExtensions {
                    status
                    totalCount
                    extension {
                        id
                        extensionId
                        user {
                            name
                            displayName
                            email
                        }
                        coreDevice {
                            deviceId
                            dial
                        }
                    }
                }
            }
        """)
        return self.client.execute(query)
    
    def create_extension(self, extension_id, name, password, email=None, vm_enabled=True):
        mutation = gql("""
            mutation CreateExtension($input: ExtensionInput!) {
                addExtension(input: $input) {
                    status
                    message
                    id
                }
            }
        """)
        variables = {
            "input": {
                "extensionId": extension_id,
                "name": name,
                "tech": "pjsip",
                "password": password,
                "email": email,
                "vmEnable": vm_enabled
            }
        }
        return self.client.execute(mutation, variable_values=variables)
    
    def update_extension(self, ext_id, **kwargs):
        mutation = gql("""
            mutation UpdateExtension($id: ID!, $input: ExtensionInput!) {
                updateExtension(id: $id, input: $input) {
                    status
                    message
                }
            }
        """)
        return self.client.execute(mutation, variable_values={"id": ext_id, "input": kwargs})
    
    def delete_extension(self, ext_id):
        mutation = gql("""
            mutation DeleteExtension($id: ID!) {
                removeExtension(id: $id) {
                    status
                    message
                }
            }
        """)
        return self.client.execute(mutation, variable_values={"id": ext_id})
    
    # Inbound Routes
    def create_inbound_route(self, did, description, dest_type, dest_id):
        mutation = gql("""
            mutation CreateInboundRoute($input: InboundRouteInput!) {
                addInboundRoute(input: $input) {
                    status
                    message
                    id
                }
            }
        """)
        return self.client.execute(mutation, variable_values={
            "input": {
                "didNumber": did,
                "description": description,
                "destination": {"type": dest_type, "id": dest_id}
            }
        })


# API Endpoints
@frappe.whitelist()
def sync_extensions():
    """Sync extensions from FreePBX to Frappe"""
    client = FreePBXGraphQL()
    result = client.get_all_extensions()
    
    synced = 0
    for ext in result.get('fetchAllExtensions', {}).get('extension', []):
        frappe.get_doc({
            "doctype": "Arrowz Unified Extension",
            "extension": ext['extensionId'],
            "display_name": ext['user']['displayName'] if ext.get('user') else ext['extensionId'],
            "pbx_id": ext['id']
        }).insert(ignore_if_duplicate=True)
        synced += 1
    
    return {"synced": synced}

@frappe.whitelist()
def create_pbx_extension(extension_id, name, password, email=None):
    """Create extension in FreePBX"""
    client = FreePBXGraphQL()
    return client.create_extension(extension_id, name, password, email)
```

### 4.2 AMI Integration
```python
# File: arrowz/api/ami.py

import frappe
from asterisk.ami import AMIClient, SimpleAction
import asyncio

class ArrowzAMI:
    def __init__(self):
        self.settings = frappe.get_single("Arrowz PBX Settings")
        self.client = None
    
    def connect(self):
        self.client = AMIClient(
            address=self.settings.ami_host,
            port=int(self.settings.ami_port)
        )
        self.client.login(
            username=self.settings.ami_user,
            secret=self.settings.get_password("ami_secret")
        )
        return self
    
    def originate_call(self, extension, destination, context="from-internal"):
        """Originate a call (click-to-dial)"""
        action = SimpleAction(
            'Originate',
            Channel=f'PJSIP/{extension}',
            Exten=destination,
            Context=context,
            Priority=1,
            CallerID=extension,
            Async='yes'
        )
        return self.client.send_action(action)
    
    def get_extension_status(self, extension):
        """Get extension registration status"""
        action = SimpleAction(
            'PJSIPShowEndpoint',
            Endpoint=extension
        )
        return self.client.send_action(action)
    
    def listen_events(self, event_handlers):
        """Listen for AMI events"""
        for event_name, handler in event_handlers.items():
            self.client.register_event(event_name, handler)


# Event Handlers
def on_new_channel(event):
    """Handle new channel (incoming/outgoing call)"""
    caller_id = event.get('CallerIDNum')
    extension = event.get('Exten')
    channel = event.get('Channel')
    
    # Determine direction
    if 'from-trunk' in event.get('Context', ''):
        direction = 'inbound'
    else:
        direction = 'outbound'
    
    # Get user for this extension
    user = get_user_by_extension(extension)
    
    if user and direction == 'inbound':
        # Publish to Socket.IO for screen pop
        frappe.publish_realtime(
            'arrowz_incoming_call',
            {
                'caller_id': caller_id,
                'extension': extension,
                'channel': channel,
                'direction': direction
            },
            user=user
        )

def on_hangup(event):
    """Handle call hangup"""
    channel = event.get('Channel')
    cause = event.get('Cause')
    
    frappe.publish_realtime(
        'arrowz_call_ended',
        {'channel': channel, 'cause': cause}
    )

def get_user_by_extension(extension):
    """Get Frappe user by SIP extension"""
    ext_doc = frappe.db.get_value(
        "Arrowz Unified Extension",
        {"extension": extension, "is_active": 1},
        "user"
    )
    return ext_doc


# Background job to run AMI listener
def start_ami_listener():
    """Start AMI event listener (run as background job)"""
    ami = ArrowzAMI().connect()
    ami.listen_events({
        'Newchannel': on_new_channel,
        'Hangup': on_hangup,
        'Bridge': lambda e: frappe.publish_realtime('arrowz_call_bridged', e),
        'AttendedTransfer': lambda e: frappe.publish_realtime('arrowz_transfer', e)
    })
    
    # Keep running
    import time
    while True:
        time.sleep(1)
```

### 4.3 fwconsole for Trunks (غير مدعوم في GraphQL)
```python
# File: arrowz/api/pbx_fwconsole.py

import frappe
import subprocess
import json

class FreePBXConsole:
    def __init__(self):
        self.settings = frappe.get_single("Arrowz PBX Settings")
    
    def _run_command(self, command):
        """Execute fwconsole command via SSH"""
        ssh_cmd = [
            'ssh', '-i', self.settings.ssh_key_path,
            '-o', 'StrictHostKeyChecking=no',
            f'{self.settings.ssh_user}@{self.settings.pbx_host}',
            f'docker exec freepbx fwconsole {command}'
        ]
        
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
        return result.stdout, result.stderr, result.returncode
    
    def list_trunks(self):
        stdout, _, _ = self._run_command('trunks --list --json')
        try:
            return json.loads(stdout)
        except:
            return []
    
    def add_trunk(self, name, tech, host, username, secret):
        cmd = f'trunks add {tech} --name="{name}" --host={host} --username={username} --secret={secret}'
        return self._run_command(cmd)
    
    def reload_dialplan(self):
        return self._run_command('reload')


@frappe.whitelist()
def sync_trunks():
    """Sync trunks from FreePBX"""
    console = FreePBXConsole()
    trunks = console.list_trunks()
    
    for trunk in trunks:
        frappe.get_doc({
            "doctype": "Arrowz SIP Trunk",
            "trunk_id": trunk.get('id'),
            "name": trunk.get('name'),
            "technology": trunk.get('tech')
        }).insert(ignore_if_duplicate=True)
    
    return {"synced": len(trunks)}
```

---

## 5️⃣ Audio Controls & Noise Cancellation

### 5.1 Native Browser (Default)
```javascript
// File: arrowz/public/js/audio_controls.js

class ArrowzAudioControls {
    constructor() {
        this.speakerVolume = 0.8;
        this.ringtoneVolume = 1.0;
        this.noiseCancellationMode = 'native';
    }
    
    getAudioConstraints() {
        const base = {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
            sampleRate: 48000,
            channelCount: 1
        };
        
        // Chrome-specific optimizations
        if (navigator.userAgent.includes('Chrome')) {
            Object.assign(base, {
                googEchoCancellation: true,
                googNoiseSuppression: true,
                googHighpassFilter: true,
                googAutoGainControl: true
            });
        }
        
        return base;
    }
    
    async getProcessedStream() {
        const constraints = {
            audio: this.getAudioConstraints(),
            video: false
        };
        
        let stream = await navigator.mediaDevices.getUserMedia(constraints);
        
        // Apply advanced noise cancellation if enabled
        if (this.noiseCancellationMode === 'rnnoise' && window.ArrowzRNNoise) {
            stream = await ArrowzRNNoise.processStream(stream);
        }
        
        return stream;
    }
    
    setVolume(type, level) {
        level = Math.max(0, Math.min(1, level));
        
        if (type === 'speaker') {
            this.speakerVolume = level;
            const audio = document.getElementById('arrowz-remote-audio');
            if (audio) audio.volume = level;
        } else if (type === 'ringtone') {
            this.ringtoneVolume = level;
            const ringtone = document.getElementById('arrowz-ringtone');
            if (ringtone) ringtone.volume = level;
        }
        
        // Save preference
        localStorage.setItem(`arrowz_${type}_volume`, level);
    }
    
    loadPreferences() {
        this.speakerVolume = parseFloat(localStorage.getItem('arrowz_speaker_volume') || 0.8);
        this.ringtoneVolume = parseFloat(localStorage.getItem('arrowz_ringtone_volume') || 1.0);
        this.noiseCancellationMode = localStorage.getItem('arrowz_noise_mode') || 'native';
    }
    
    renderSettingsUI() {
        return `
            <div class="arrowz-audio-settings">
                <div class="setting-group">
                    <label>Speaker Volume</label>
                    <input type="range" id="arrowz-speaker-vol" 
                           min="0" max="100" value="${this.speakerVolume * 100}">
                    <span class="vol-label">${Math.round(this.speakerVolume * 100)}%</span>
                </div>
                
                <div class="setting-group">
                    <label>Ringtone Volume</label>
                    <input type="range" id="arrowz-ringtone-vol" 
                           min="0" max="100" value="${this.ringtoneVolume * 100}">
                    <span class="vol-label">${Math.round(this.ringtoneVolume * 100)}%</span>
                </div>
                
                <div class="setting-group">
                    <label>Noise Cancellation</label>
                    <select id="arrowz-noise-mode">
                        <option value="native" ${this.noiseCancellationMode === 'native' ? 'selected' : ''}>
                            Browser Native
                        </option>
                        <option value="rnnoise" ${this.noiseCancellationMode === 'rnnoise' ? 'selected' : ''}>
                            RNNoise (Advanced)
                        </option>
                        <option value="off" ${this.noiseCancellationMode === 'off' ? 'selected' : ''}>
                            Off
                        </option>
                    </select>
                </div>
            </div>
        `;
    }
}
```

### 5.2 RNNoise Integration (Optional)
```javascript
// File: arrowz/public/js/rnnoise.js

class ArrowzRNNoise {
    static async init() {
        // Load RNNoise WebAssembly module
        if (!this.module) {
            this.module = await import('/assets/arrowz/js/lib/rnnoise-wasm.js');
            await this.module.default();
        }
    }
    
    static async processStream(inputStream) {
        await this.init();
        
        const audioContext = new AudioContext({ sampleRate: 48000 });
        const source = audioContext.createMediaStreamSource(inputStream);
        
        // Load AudioWorklet processor
        await audioContext.audioWorklet.addModule('/assets/arrowz/js/lib/rnnoise-processor.js');
        const processorNode = new AudioWorkletNode(audioContext, 'rnnoise-processor');
        
        source.connect(processorNode);
        
        const destination = audioContext.createMediaStreamDestination();
        processorNode.connect(destination);
        
        return destination.stream;
    }
}
```

---

## 6️⃣ SMS Integration - Provider Agnostic

### 6.1 Provider Interface
```python
# File: arrowz/sms/base.py

from abc import ABC, abstractmethod

class SMSProvider(ABC):
    """Abstract base class for SMS providers"""
    
    @abstractmethod
    def send(self, to: str, message: str, sender: str = None) -> dict:
        """Send SMS and return result with message_id"""
        pass
    
    @abstractmethod
    def get_status(self, message_id: str) -> str:
        """Get delivery status"""
        pass
    
    @abstractmethod
    def get_balance(self) -> float:
        """Get account balance"""
        pass
```

### 6.2 Provider Implementations
```python
# File: arrowz/sms/providers/twilio.py

from arrowz.sms.base import SMSProvider
from twilio.rest import Client

class TwilioProvider(SMSProvider):
    def __init__(self, account_sid, auth_token, from_number):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number
    
    def send(self, to, message, sender=None):
        msg = self.client.messages.create(
            body=message,
            from_=sender or self.from_number,
            to=to
        )
        return {"message_id": msg.sid, "status": msg.status}
    
    def get_status(self, message_id):
        msg = self.client.messages(message_id).fetch()
        return msg.status
    
    def get_balance(self):
        return self.client.balance.fetch().balance


# File: arrowz/sms/providers/vonage.py

class VonageProvider(SMSProvider):
    def __init__(self, api_key, api_secret, from_number):
        import vonage
        self.client = vonage.Client(key=api_key, secret=api_secret)
        self.from_number = from_number
    
    def send(self, to, message, sender=None):
        response = self.client.sms.send_message({
            "from": sender or self.from_number,
            "to": to,
            "text": message
        })
        msg = response["messages"][0]
        return {"message_id": msg["message-id"], "status": msg["status"]}


# File: arrowz/sms/providers/local.py

class LocalProvider(SMSProvider):
    """Template for local/country-specific providers"""
    
    def __init__(self, api_url, api_key, from_number):
        self.api_url = api_url
        self.api_key = api_key
        self.from_number = from_number
    
    def send(self, to, message, sender=None):
        import requests
        response = requests.post(
            f"{self.api_url}/send",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"to": to, "message": message, "from": sender or self.from_number}
        )
        return response.json()
```

### 6.3 SMS API
```python
# File: arrowz/api/sms.py

import frappe
from arrowz.sms.providers import get_provider

def get_provider():
    settings = frappe.get_single("Arrowz SMS Settings")
    
    if settings.provider == "Twilio":
        from arrowz.sms.providers.twilio import TwilioProvider
        return TwilioProvider(
            settings.get_password("api_key"),
            settings.get_password("api_secret"),
            settings.from_number
        )
    elif settings.provider == "Vonage":
        from arrowz.sms.providers.vonage import VonageProvider
        return VonageProvider(
            settings.get_password("api_key"),
            settings.get_password("api_secret"),
            settings.from_number
        )
    elif settings.provider == "Local":
        from arrowz.sms.providers.local import LocalProvider
        return LocalProvider(
            settings.api_url,
            settings.get_password("api_key"),
            settings.from_number
        )
    
    frappe.throw(f"Unknown SMS provider: {settings.provider}")

@frappe.whitelist()
def send_sms(to, message, linked_doctype=None, linked_docname=None):
    """Send SMS using configured provider"""
    provider = get_provider()
    result = provider.send(to, message)
    
    # Log the message
    frappe.get_doc({
        "doctype": "Arrowz SMS Log",
        "to_number": to,
        "message": message,
        "status": result.get("status", "Sent"),
        "message_id": result.get("message_id"),
        "linked_doctype": linked_doctype,
        "linked_docname": linked_docname,
        "sent_by": frappe.session.user
    }).insert(ignore_permissions=True)
    
    return result
```

---

## 7️⃣ Click-to-Dial & Screen Pop

### 7.1 Click-to-Dial
```javascript
// File: arrowz/public/js/click_to_dial.js

class ArrowzClickToDial {
    constructor() {
        this.enabled = true;
    }
    
    init() {
        this.observeDOM();
        this.addDialButtons();
        
        // Re-add buttons on page change
        $(document).on('page-change', () => this.addDialButtons());
        
        // Handle click events
        $(document).on('click', '.arrowz-dial-btn', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const phone = $(e.currentTarget).data('phone');
            this.dial(phone);
        });
    }
    
    addDialButtons() {
        // Find all phone fields
        $('[data-fieldtype="Phone"] .like-disabled-input, [data-fieldtype="Data"][data-fieldname*="phone"] .like-disabled-input, [data-fieldtype="Data"][data-fieldname*="mobile"] .like-disabled-input').each((i, el) => {
            const $el = $(el);
            const phone = $el.text().trim();
            
            if (phone && !$el.next('.arrowz-dial-btn').length) {
                $el.after(`
                    <button class="btn btn-xs btn-default arrowz-dial-btn" 
                            data-phone="${phone}" 
                            title="Click to Dial">
                        <svg class="icon icon-xs">
                            <use href="#icon-call"></use>
                        </svg>
                    </button>
                `);
            }
        });
    }
    
    observeDOM() {
        // Watch for dynamic content
        const observer = new MutationObserver(() => {
            this.addDialButtons();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    dial(phoneNumber) {
        if (!phoneNumber) return;
        
        // Clean number
        const cleaned = phoneNumber.replace(/[^\d+]/g, '');
        
        // Open softphone and dial
        window.arrowzPhone.popup.show();
        window.arrowzPhone.showTab('dialer');
        document.getElementById('arrowz-phone-input').value = cleaned;
        
        // Auto-dial after short delay
        setTimeout(() => {
            window.arrowzPhone.softphone.makeCall(cleaned);
        }, 500);
    }
}

// Initialize
frappe.ready(() => {
    if (frappe.session.user !== 'Guest') {
        window.arrowzClickToDial = new ArrowzClickToDial();
        window.arrowzClickToDial.init();
    }
});
```

### 7.2 Screen Pop
```javascript
// File: arrowz/public/js/screen_pop.js

class ArrowzScreenPop {
    constructor() {
        this.subscribeToEvents();
    }
    
    subscribeToEvents() {
        frappe.realtime.on('arrowz_incoming_call', (data) => {
            this.handleIncomingCall(data);
        });
    }
    
    async handleIncomingCall(data) {
        // Lookup caller in CRM
        const callerInfo = await this.lookupCaller(data.caller_id);
        
        // Show incoming call in softphone
        window.arrowzPhone.handleIncomingCall({
            ...data,
            ...callerInfo
        });
        
        // Show notification
        this.showNotification(callerInfo);
        
        // Auto-open record if configured
        if (callerInfo.found && callerInfo.auto_open) {
            frappe.set_route('Form', callerInfo.doctype, callerInfo.name);
        }
    }
    
    async lookupCaller(phoneNumber) {
        const result = await frappe.call({
            method: 'arrowz.api.crm.lookup_by_phone',
            args: { phone: phoneNumber }
        });
        return result.message || { found: false };
    }
    
    showNotification(callerInfo) {
        // Desktop notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('Incoming Call', {
                body: callerInfo.found 
                    ? `${callerInfo.name} (${callerInfo.doctype})`
                    : callerInfo.phone,
                icon: '/assets/arrowz/images/phone-ring.png',
                tag: 'arrowz-incoming'
            });
        }
        
        // Frappe alert
        frappe.show_alert({
            message: callerInfo.found 
                ? `📞 ${callerInfo.name}` 
                : `📞 ${callerInfo.phone}`,
            indicator: 'blue'
        }, 10);
    }
}

// Initialize
frappe.ready(() => {
    if (frappe.session.user !== 'Guest') {
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
        
        window.arrowzScreenPop = new ArrowzScreenPop();
    }
});
```

---

## 🔟 Advanced Dashboards

### 10.1 Real-time Wallboard

لوحة عرض كبيرة للـ Call Center تعرض الإحصائيات الفورية على شاشات TV:

```javascript
// File: arrowz/public/js/wallboard.js

class ArrowzWallboard {
    constructor(container) {
        this.container = container;
        this.refreshInterval = 5000; // 5 seconds
        this.widgets = [];
        this.charts = {};
    }
    
    async init() {
        this.setupFullscreen();
        this.createLayout();
        this.initCharts();
        this.startRealTimeUpdates();
    }
    
    setupFullscreen() {
        // F11 or button to toggle fullscreen
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F11') {
                e.preventDefault();
                this.toggleFullscreen();
            }
        });
    }
    
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            this.container.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }
    
    createLayout() {
        this.container.innerHTML = `
            <div class="wallboard-grid">
                <!-- Row 1: Key Metrics -->
                <div class="wb-row wb-metrics">
                    <div class="wb-widget wb-metric" id="active-calls">
                        <div class="wb-icon">📞</div>
                        <div class="wb-value">0</div>
                        <div class="wb-label">Active Calls</div>
                    </div>
                    <div class="wb-widget wb-metric" id="waiting-queue">
                        <div class="wb-icon">⏳</div>
                        <div class="wb-value">0</div>
                        <div class="wb-label">Waiting in Queue</div>
                        <div class="wb-sublabel">Avg Wait: <span id="avg-wait">0:00</span></div>
                    </div>
                    <div class="wb-widget wb-metric" id="agents-available">
                        <div class="wb-icon">👥</div>
                        <div class="wb-value">0/0</div>
                        <div class="wb-label">Agents Available</div>
                    </div>
                    <div class="wb-widget wb-metric" id="calls-today">
                        <div class="wb-icon">📊</div>
                        <div class="wb-value">0</div>
                        <div class="wb-label">Calls Today</div>
                    </div>
                </div>
                
                <!-- Row 2: SLA & Charts -->
                <div class="wb-row wb-charts">
                    <div class="wb-widget wb-gauge" id="sla-widget">
                        <div class="wb-label">SLA Compliance</div>
                        <canvas id="sla-gauge"></canvas>
                        <div class="wb-value" id="sla-value">0%</div>
                    </div>
                    <div class="wb-widget wb-chart" id="hourly-widget">
                        <div class="wb-label">Hourly Volume</div>
                        <canvas id="hourly-chart"></canvas>
                    </div>
                </div>
                
                <!-- Row 3: Agent Status Grid -->
                <div class="wb-row wb-agents">
                    <div class="wb-widget wb-full" id="agent-grid">
                        <div class="wb-label">Agent Status</div>
                        <div class="agent-cards"></div>
                    </div>
                </div>
            </div>
        `;
    }
    
    initCharts() {
        // SLA Gauge using Chart.js doughnut
        this.charts.sla = new Chart(document.getElementById('sla-gauge'), {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [0, 100],
                    backgroundColor: ['#28a745', '#e9ecef'],
                    borderWidth: 0
                }]
            },
            options: {
                circumference: 180,
                rotation: -90,
                cutout: '80%',
                plugins: { legend: { display: false } }
            }
        });
        
        // Hourly Volume using Chart.js bar
        this.charts.hourly = new Chart(document.getElementById('hourly-chart'), {
            type: 'bar',
            data: {
                labels: Array.from({length: 24}, (_, i) => `${i}:00`),
                datasets: [{
                    label: 'Calls',
                    data: new Array(24).fill(0),
                    backgroundColor: '#2490ef'
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
    
    startRealTimeUpdates() {
        // Initial load
        this.fetchAndUpdate();
        
        // Socket.IO for real-time push
        frappe.realtime.on('wallboard_update', (data) => {
            this.updateWidgets(data);
        });
        
        // Fallback polling every 5 seconds
        setInterval(() => this.fetchAndUpdate(), this.refreshInterval);
    }
    
    async fetchAndUpdate() {
        try {
            const response = await frappe.call({
                method: 'arrowz.api.dashboard.get_wallboard_data'
            });
            this.updateWidgets(response.message);
        } catch (error) {
            console.error('Wallboard fetch error:', error);
        }
    }
    
    updateWidgets(data) {
        // Active Calls
        this.animateValue('#active-calls .wb-value', data.active_calls);
        
        // Queue with color coding
        const queueWidget = document.querySelector('#waiting-queue');
        this.animateValue('#waiting-queue .wb-value', data.queue_depth);
        document.querySelector('#avg-wait').textContent = this.formatDuration(data.avg_wait_time);
        queueWidget.classList.remove('wb-normal', 'wb-warning', 'wb-danger');
        if (data.queue_depth > 10) {
            queueWidget.classList.add('wb-danger');
        } else if (data.queue_depth > 5) {
            queueWidget.classList.add('wb-warning');
        } else {
            queueWidget.classList.add('wb-normal');
        }
        
        // Agents
        document.querySelector('#agents-available .wb-value').textContent = 
            `${data.agents_available}/${data.agents_total}`;
        
        // Calls Today
        this.animateValue('#calls-today .wb-value', data.calls_today);
        
        // SLA Gauge
        this.updateSLAGauge(data.sla_percentage);
        
        // Hourly Chart
        this.updateHourlyChart(data.hourly_data);
        
        // Agent Grid
        this.updateAgentGrid(data.agents);
    }
    
    updateSLAGauge(percentage) {
        this.charts.sla.data.datasets[0].data = [percentage, 100 - percentage];
        
        // Color based on threshold
        const color = percentage >= 90 ? '#28a745' : percentage >= 70 ? '#ffc107' : '#dc3545';
        this.charts.sla.data.datasets[0].backgroundColor[0] = color;
        
        this.charts.sla.update();
        document.getElementById('sla-value').textContent = `${percentage}%`;
    }
    
    updateHourlyChart(hourlyData) {
        const now = new Date().getHours();
        this.charts.hourly.data.datasets[0].data = hourlyData;
        
        // Highlight current hour
        this.charts.hourly.data.datasets[0].backgroundColor = hourlyData.map((_, i) => 
            i === now ? '#1a73e8' : '#2490ef'
        );
        
        this.charts.hourly.update();
    }
    
    updateAgentGrid(agents) {
        const grid = document.querySelector('#agent-grid .agent-cards');
        grid.innerHTML = agents.map(agent => `
            <div class="agent-card status-${agent.status}">
                <img src="${agent.avatar}" class="agent-avatar" alt="${agent.name}">
                <div class="agent-info">
                    <div class="agent-name">${agent.name}</div>
                    <div class="agent-ext">${agent.extension}</div>
                </div>
                <div class="agent-status-badge">${this.getStatusLabel(agent.status)}</div>
                ${agent.current_duration ? `<div class="agent-duration">${agent.current_duration}</div>` : ''}
            </div>
        `).join('');
    }
    
    getStatusLabel(status) {
        const labels = {
            'available': '🟢 Available',
            'on_call': '🔴 On Call',
            'wrap_up': '🟡 Wrap Up',
            'break': '☕ Break',
            'offline': '⚫ Offline'
        };
        return labels[status] || status;
    }
    
    animateValue(selector, newValue) {
        const el = document.querySelector(selector);
        const current = parseInt(el.textContent) || 0;
        if (current === newValue) return;
        
        el.classList.add('value-changed');
        el.textContent = newValue;
        setTimeout(() => el.classList.remove('value-changed'), 500);
    }
    
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}
```

### 10.2 Wallboard CSS
```css
/* File: arrowz/public/css/wallboard.css */

.wallboard-grid {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: white;
    padding: 20px;
    gap: 20px;
}

.wb-row {
    display: flex;
    gap: 20px;
}

.wb-metrics {
    flex: 0 0 auto;
}

.wb-charts {
    flex: 1;
}

.wb-agents {
    flex: 1;
}

.wb-widget {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px;
    backdrop-filter: blur(10px);
}

.wb-metric {
    flex: 1;
    text-align: center;
}

.wb-metric .wb-icon {
    font-size: 2em;
    margin-bottom: 10px;
}

.wb-metric .wb-value {
    font-size: 4em;
    font-weight: bold;
    line-height: 1;
    transition: all 0.3s ease;
}

.wb-metric .wb-label {
    font-size: 1.2em;
    opacity: 0.8;
    margin-top: 10px;
}

.wb-metric.wb-warning {
    background: rgba(255, 193, 7, 0.2);
    border: 2px solid #ffc107;
}

.wb-metric.wb-danger {
    background: rgba(220, 53, 69, 0.2);
    border: 2px solid #dc3545;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.wb-gauge {
    flex: 0 0 300px;
    text-align: center;
}

.wb-chart {
    flex: 1;
}

.wb-full {
    width: 100%;
}

.agent-cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
    max-height: 300px;
    overflow-y: auto;
}

.agent-card {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 15px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    border-left: 4px solid;
}

.agent-card.status-available { border-color: #28a745; }
.agent-card.status-on_call { border-color: #dc3545; }
.agent-card.status-wrap_up { border-color: #ffc107; }
.agent-card.status-break { border-color: #6c757d; }
.agent-card.status-offline { border-color: #343a40; opacity: 0.5; }

.agent-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
}

.agent-info {
    flex: 1;
}

.agent-name {
    font-weight: 500;
}

.agent-ext {
    font-size: 0.85em;
    opacity: 0.7;
}

.value-changed {
    animation: valueChange 0.5s ease;
}

@keyframes valueChange {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); color: #4CAF50; }
    100% { transform: scale(1); }
}
```

### 10.3 Wallboard Backend API
```python
# File: arrowz/api/dashboard.py

import frappe
from frappe.utils import now_datetime, get_datetime, add_days, today

@frappe.whitelist()
def get_wallboard_data():
    """Get all wallboard metrics in single optimized call"""
    current_hour = now_datetime().hour
    
    return {
        'active_calls': get_active_call_count(),
        'queue_depth': get_queue_depth(),
        'avg_wait_time': get_avg_wait_time(),
        'agents_available': count_available_agents(),
        'agents_total': count_total_agents(),
        'sla_percentage': calculate_sla_percentage(),
        'calls_today': get_today_call_count(),
        'hourly_data': get_hourly_breakdown(),
        'agents': get_agent_status_list()
    }

def get_active_call_count():
    """Count currently active calls"""
    return frappe.db.count('AZ Call Log', {
        'status': 'In Progress'
    })

def get_queue_depth():
    """Get number of calls waiting in queue"""
    # This would come from AMI or cached queue data
    queue_data = frappe.cache().get_value('arrowz_queue_depth')
    return queue_data or 0

def get_avg_wait_time():
    """Average wait time in seconds for today's calls"""
    result = frappe.db.sql("""
        SELECT AVG(TIMESTAMPDIFF(SECOND, start_time, answer_time)) as avg_wait
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) = CURDATE()
        AND answer_time IS NOT NULL
    """, as_dict=1)
    return int(result[0].avg_wait or 0) if result else 0

def count_available_agents():
    """Count agents with available status"""
    return frappe.db.count('AZ Extension', {
        'is_active': 1,
        'status': 'available'
    })

def count_total_agents():
    """Count total active agents"""
    return frappe.db.count('AZ Extension', {
        'is_active': 1
    })

def calculate_sla_percentage():
    """Calculate SLA compliance (answered within threshold)"""
    settings = frappe.get_single('Arrowz Settings')
    threshold = settings.sla_threshold_seconds or 20
    
    result = frappe.db.sql("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE 
                WHEN answer_time IS NOT NULL 
                AND TIMESTAMPDIFF(SECOND, start_time, answer_time) <= %(threshold)s 
                THEN 1 ELSE 0 
            END) as within_sla
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) = CURDATE()
        AND direction = 'Inbound'
    """, {'threshold': threshold}, as_dict=1)
    
    if result and result[0].total > 0:
        return round((result[0].within_sla / result[0].total) * 100)
    return 100

def get_today_call_count():
    """Total calls today"""
    return frappe.db.count('AZ Call Log', {
        'start_time': ['>=', today()]
    })

def get_hourly_breakdown():
    """Get call count per hour for today"""
    result = frappe.db.sql("""
        SELECT HOUR(start_time) as hour, COUNT(*) as count
        FROM `tabAZ Call Log`
        WHERE DATE(start_time) = CURDATE()
        GROUP BY HOUR(start_time)
    """, as_dict=1)
    
    # Fill all 24 hours
    hourly = [0] * 24
    for row in result:
        hourly[row.hour] = row.count
    
    return hourly

def get_agent_status_list():
    """Get all agents with their current status"""
    agents = frappe.get_all('AZ Extension',
        filters={'is_active': 1},
        fields=['user', 'extension', 'status', 'current_call']
    )
    
    result = []
    for agent in agents:
        user = frappe.get_cached_doc('User', agent.user)
        
        current_duration = None
        if agent.current_call:
            call = frappe.get_doc('AZ Call Log', agent.current_call)
            if call.start_time:
                duration = (now_datetime() - get_datetime(call.start_time)).seconds
                current_duration = f"{duration // 60}:{(duration % 60):02d}"
        
        result.append({
            'extension': agent.extension,
            'name': user.full_name,
            'avatar': user.user_image or '/assets/frappe/images/default-avatar.png',
            'status': agent.status or 'offline',
            'current_duration': current_duration
        })
    
    # Sort: on_call first, then available, then others
    status_order = {'on_call': 0, 'available': 1, 'wrap_up': 2, 'break': 3, 'offline': 4}
    result.sort(key=lambda x: status_order.get(x['status'], 5))
    
    return result

# ═══════════════════════════════════════════════════════════
# BROADCAST WALLBOARD UPDATES
# ═══════════════════════════════════════════════════════════

def broadcast_wallboard_update():
    """Push wallboard update to all connected clients"""
    data = get_wallboard_data()
    frappe.publish_realtime('wallboard_update', data)

# Call this from AMI event handlers or scheduled job
```

### 10.4 Historical Analytics Dashboard

```python
# File: arrowz/arrowz/page/call_analytics/call_analytics.py

import frappe
from frappe.utils import add_days, today, getdate

@frappe.whitelist()
def get_analytics_data(filters):
    """Comprehensive analytics for call center performance"""
    filters = frappe.parse_json(filters)
    from_date = filters.get('from_date', add_days(today(), -30))
    to_date = filters.get('to_date', today())
    agent = filters.get('agent')
    
    base_filters = {
        'start_time': ['between', [from_date, to_date]]
    }
    if agent:
        base_filters['user'] = agent
    
    return {
        # Volume Metrics
        'total_calls': get_call_count(base_filters),
        'inbound_calls': get_call_count({**base_filters, 'direction': 'Inbound'}),
        'outbound_calls': get_call_count({**base_filters, 'direction': 'Outbound'}),
        'missed_calls': get_call_count({**base_filters, 'disposition': 'NO ANSWER'}),
        
        # Time Metrics
        'avg_talk_time': get_avg_duration(base_filters, 'duration'),
        'avg_wait_time': get_avg_wait(base_filters),
        'avg_handle_time': get_avg_duration(base_filters, 'handle_time'),
        
        # Quality Metrics
        'sla_percentage': calculate_period_sla(base_filters),
        'answer_rate': calculate_answer_rate(base_filters),
        'avg_sentiment': get_avg_sentiment(base_filters),
        
        # Charts Data
        'daily_volume': get_daily_volume(from_date, to_date, agent),
        'hourly_heatmap': get_hourly_heatmap(from_date, to_date),
        'agent_performance': get_agent_leaderboard(from_date, to_date),
        'disposition_breakdown': get_disposition_breakdown(base_filters),
        'sentiment_trend': get_sentiment_trend(from_date, to_date)
    }

def get_hourly_heatmap(from_date, to_date):
    """Returns data for day-of-week vs hour-of-day heatmap"""
    data = frappe.db.sql("""
        SELECT 
            DAYOFWEEK(start_time) - 1 as day,
            HOUR(start_time) as hour,
            COUNT(*) as count
        FROM `tabAZ Call Log`
        WHERE start_time BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY DAYOFWEEK(start_time), HOUR(start_time)
    """, {'from_date': from_date, 'to_date': to_date}, as_dict=1)
    
    return [{'day': d.day, 'hour': d.hour, 'count': d.count} for d in data]

def get_agent_leaderboard(from_date, to_date):
    """Top performing agents"""
    return frappe.db.sql("""
        SELECT 
            user,
            COUNT(*) as total_calls,
            ROUND(AVG(duration), 0) as avg_duration,
            ROUND(AVG(sentiment_score) * 100, 0) as sentiment_pct,
            ROUND(SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as answer_rate
        FROM `tabAZ Call Log`
        WHERE start_time BETWEEN %(from_date)s AND %(to_date)s
        AND user IS NOT NULL
        GROUP BY user
        ORDER BY total_calls DESC
        LIMIT 10
    """, {'from_date': from_date, 'to_date': to_date}, as_dict=1)

def get_daily_volume(from_date, to_date, agent=None):
    """Daily call volume breakdown"""
    agent_filter = "AND user = %(agent)s" if agent else ""
    
    return frappe.db.sql(f"""
        SELECT 
            DATE(start_time) as date,
            SUM(CASE WHEN direction = 'Inbound' THEN 1 ELSE 0 END) as inbound,
            SUM(CASE WHEN direction = 'Outbound' THEN 1 ELSE 0 END) as outbound
        FROM `tabAZ Call Log`
        WHERE start_time BETWEEN %(from_date)s AND %(to_date)s
        {agent_filter}
        GROUP BY DATE(start_time)
        ORDER BY date
    """, {'from_date': from_date, 'to_date': to_date, 'agent': agent}, as_dict=1)
```

### 10.5 Analytics Dashboard Page

```javascript
// File: arrowz/arrowz/page/call_analytics/call_analytics.js

frappe.pages['call-analytics'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Call Analytics'),
        single_column: true
    });
    
    // Create page layout
    page.main.html(`
        <div class="analytics-dashboard">
            <div class="analytics-filters"></div>
            <div class="analytics-kpis"></div>
            <div class="analytics-charts">
                <div class="chart-row">
                    <div class="chart-container volume-chart"></div>
                    <div class="chart-container disposition-chart"></div>
                </div>
                <div class="chart-row">
                    <div class="chart-container heatmap-chart"></div>
                </div>
                <div class="chart-row">
                    <div class="chart-container leaderboard"></div>
                </div>
            </div>
        </div>
    `);
    
    // Add filters
    const filterArea = page.main.find('.analytics-filters');
    
    page.date_range = frappe.ui.form.make_control({
        parent: filterArea,
        df: {
            fieldtype: 'DateRange',
            fieldname: 'date_range',
            label: __('Date Range'),
            default: [frappe.datetime.add_days(frappe.datetime.get_today(), -30), 
                      frappe.datetime.get_today()]
        },
        render_input: true
    });
    
    page.agent_filter = frappe.ui.form.make_control({
        parent: filterArea,
        df: {
            fieldtype: 'Link',
            fieldname: 'agent',
            label: __('Agent'),
            options: 'User',
            get_query: () => ({
                filters: { 'user_type': 'System User' }
            })
        },
        render_input: true
    });
    
    // Refresh button
    page.set_primary_action(__('Refresh'), () => refreshDashboard());
    
    // Export button
    page.set_secondary_action(__('Export'), () => exportReport());
    
    const dashboard = new ArrowzAnalyticsDashboard(page);
    
    function refreshDashboard() {
        const filters = {
            from_date: page.date_range.get_value()?.[0],
            to_date: page.date_range.get_value()?.[1],
            agent: page.agent_filter.get_value()
        };
        dashboard.refresh(filters);
    }
    
    // Initial load
    setTimeout(refreshDashboard, 500);
};

class ArrowzAnalyticsDashboard {
    constructor(page) {
        this.page = page;
        this.charts = {};
    }
    
    async refresh(filters) {
        frappe.show_progress(__('Loading...'), 0, 100);
        
        try {
            const response = await frappe.call({
                method: 'arrowz.arrowz.page.call_analytics.call_analytics.get_analytics_data',
                args: { filters }
            });
            
            frappe.show_progress(__('Loading...'), 100, 100);
            frappe.hide_progress();
            
            this.renderKPICards(response.message);
            this.renderCharts(response.message);
            this.renderLeaderboard(response.message.agent_performance);
            
        } catch (error) {
            frappe.hide_progress();
            frappe.msgprint(__('Error loading analytics'));
        }
    }
    
    renderKPICards(data) {
        const kpiContainer = this.page.main.find('.analytics-kpis');
        kpiContainer.html(`
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-icon">📞</div>
                    <div class="kpi-value">${data.total_calls.toLocaleString()}</div>
                    <div class="kpi-label">${__('Total Calls')}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">📥</div>
                    <div class="kpi-value">${data.inbound_calls.toLocaleString()}</div>
                    <div class="kpi-label">${__('Inbound')}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">📤</div>
                    <div class="kpi-value">${data.outbound_calls.toLocaleString()}</div>
                    <div class="kpi-label">${__('Outbound')}</div>
                </div>
                <div class="kpi-card ${data.answer_rate < 80 ? 'kpi-warning' : ''}">
                    <div class="kpi-icon">✅</div>
                    <div class="kpi-value">${data.answer_rate}%</div>
                    <div class="kpi-label">${__('Answer Rate')}</div>
                </div>
                <div class="kpi-card ${data.sla_percentage < 80 ? 'kpi-warning' : ''}">
                    <div class="kpi-icon">⏱️</div>
                    <div class="kpi-value">${data.sla_percentage}%</div>
                    <div class="kpi-label">${__('SLA Compliance')}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-icon">⏳</div>
                    <div class="kpi-value">${this.formatDuration(data.avg_talk_time)}</div>
                    <div class="kpi-label">${__('Avg Talk Time')}</div>
                </div>
            </div>
        `);
    }
    
    renderCharts(data) {
        // Daily Volume Line Chart
        this.renderVolumeChart(data.daily_volume);
        
        // Disposition Pie Chart
        this.renderDispositionChart(data.disposition_breakdown);
        
        // Hourly Heatmap
        this.renderHeatmap(data.hourly_heatmap);
    }
    
    renderVolumeChart(dailyData) {
        const container = this.page.main.find('.volume-chart');
        container.html('<h4>Daily Call Volume</h4><div id="volume-chart-canvas"></div>');
        
        if (this.charts.volume) {
            this.charts.volume.destroy();
        }
        
        this.charts.volume = new frappe.Chart('#volume-chart-canvas', {
            type: 'line',
            height: 250,
            data: {
                labels: dailyData.map(d => frappe.datetime.str_to_user(d.date)),
                datasets: [
                    { name: __('Inbound'), values: dailyData.map(d => d.inbound) },
                    { name: __('Outbound'), values: dailyData.map(d => d.outbound) }
                ]
            },
            colors: ['#2490ef', '#98d85b'],
            lineOptions: { regionFill: 1 }
        });
    }
    
    renderHeatmap(heatmapData) {
        const container = this.page.main.find('.heatmap-chart');
        container.html('<h4>Call Volume Heatmap (Day vs Hour)</h4><div id="heatmap-canvas" style="height:300px"></div>');
        
        // Using Apache ECharts for heatmap
        if (typeof echarts !== 'undefined') {
            const chart = echarts.init(document.getElementById('heatmap-canvas'));
            
            const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            const hours = Array.from({length: 24}, (_, i) => `${i}:00`);
            
            chart.setOption({
                tooltip: {
                    position: 'top',
                    formatter: (p) => `${days[p.data[0]]} ${hours[p.data[1]]}: ${p.data[2]} calls`
                },
                grid: { left: 60, right: 20, top: 20, bottom: 60 },
                xAxis: { type: 'category', data: days },
                yAxis: { type: 'category', data: hours },
                visualMap: {
                    min: 0,
                    max: Math.max(...heatmapData.map(d => d.count), 1),
                    calculable: true,
                    orient: 'horizontal',
                    left: 'center',
                    bottom: 0,
                    inRange: {
                        color: ['#f0f0f0', '#2490ef', '#1a5fb4']
                    }
                },
                series: [{
                    type: 'heatmap',
                    data: heatmapData.map(d => [d.day, d.hour, d.count]),
                    emphasis: { itemStyle: { shadowBlur: 10 } }
                }]
            });
        }
    }
    
    renderLeaderboard(agents) {
        const container = this.page.main.find('.leaderboard');
        container.html(`
            <h4>${__('Agent Performance')}</h4>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>${__('Agent')}</th>
                        <th>${__('Calls')}</th>
                        <th>${__('Avg Duration')}</th>
                        <th>${__('Answer Rate')}</th>
                        <th>${__('Sentiment')}</th>
                    </tr>
                </thead>
                <tbody>
                    ${agents.map((a, i) => `
                        <tr>
                            <td>${i + 1}</td>
                            <td>${a.user}</td>
                            <td>${a.total_calls}</td>
                            <td>${this.formatDuration(a.avg_duration)}</td>
                            <td>${a.answer_rate}%</td>
                            <td>
                                <span class="sentiment-badge ${a.sentiment_pct >= 70 ? 'positive' : a.sentiment_pct >= 40 ? 'neutral' : 'negative'}">
                                    ${a.sentiment_pct}%
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `);
    }
    
    formatDuration(seconds) {
        if (!seconds) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.round(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}
```

### 10.6 Scheduled Reports

```python
# File: arrowz/tasks.py

import frappe
from frappe.utils import today, add_days, formatdate
from arrowz.arrowz.page.call_analytics.call_analytics import get_analytics_data

def daily():
    """Daily scheduled tasks"""
    send_daily_report()

def send_daily_report():
    """Send daily call center performance report"""
    yesterday = add_days(today(), -1)
    
    data = get_analytics_data({
        'from_date': yesterday,
        'to_date': yesterday
    })
    
    # Render email template
    report_html = frappe.render_template(
        'arrowz/templates/emails/daily_report.html',
        {
            'data': data,
            'date': formatdate(yesterday),
            'company': frappe.defaults.get_global_default('company')
        }
    )
    
    # Get managers
    managers = frappe.get_all('User',
        filters={
            'enabled': 1,
            'name': ['in', frappe.get_all('Has Role',
                filters={'role': 'Arrowz Manager'},
                pluck='parent'
            )]
        },
        pluck='email'
    )
    
    if managers:
        frappe.sendmail(
            recipients=managers,
            subject=f'📊 Call Center Report - {formatdate(yesterday)}',
            message=report_html,
            delayed=False
        )

# Add to hooks.py:
# scheduler_events = {
#     "daily": [
#         "arrowz.tasks.daily"
#     ]
# }
```

---

## 📋 Implementation Roadmap

### Phase 1: Core UI (Weeks 1-2)
- [ ] Navbar softphone integration
- [ ] Multi-tab popup (Dialer, Active, History, Incoming)
- [ ] Multi-line support
- [ ] Mobile optimization

### Phase 2: Call Features (Weeks 3-4)
- [ ] Call Transfer (Attended default)
- [ ] Recording Playback
- [ ] Click-to-Dial
- [ ] Screen Pop

### Phase 3: Integration (Weeks 5-6)
- [ ] FreePBX GraphQL client
- [ ] AMI event listener
- [ ] Docker shared volume setup
- [ ] SMS integration (provider-agnostic)

### Phase 4: Audio & Polish (Weeks 7-8)
- [ ] Audio controls UI
- [ ] Noise cancellation (native + optional RNNoise)
- [ ] In-call WhatsApp/SMS actions
- [ ] Video calls (via PBX)

### Phase 5: Dashboards (Weeks 9-10)
- [ ] Real-time Wallboard
- [ ] Historical Analytics Dashboard
- [ ] Agent Leaderboard
- [ ] Hourly Heatmap (ECharts)
- [ ] Daily/Weekly Scheduled Reports

---

## ✅ القرارات المُتخذة

| Feature | Decision | Priority |
|---------|----------|----------|
| Softphone UI | Navbar + Multi-tab popup | 🔴 High |
| Call Transfer | Attended default, Blind للـ Supervisors | 🔴 High |
| Recording | Docker shared volume | 🔴 High |
| FreePBX Integration | GraphQL + AMI + fwconsole | 🟡 Medium |
| SMS | Provider-agnostic | 🟡 Medium |
| Audio | Native + optional RNNoise | 🟡 Medium |
| Video | Via PBX | 🟢 Low |
| **Advanced Dashboards** | Wallboard + Analytics + Heatmaps | 🟡 Medium |
| Queue | مؤجل للمستقبل | 📋 Future |

---

*جاهز للتنفيذ ✅*
