# Arrowz Frontend Guide
## JavaScript Components & UI Specifications

---

## 📱 Component Overview

| Component | File | Purpose |
|-----------|------|---------|
| ArrowzNavbarPhone | navbar_phone.js | Navbar softphone integration |
| ArrowzSoftphonePopup | softphone_popup.js | Multi-tab popup UI |
| ArrowzSoftphone | softphone.js | WebRTC/SIP core |
| ArrowzTransfer | transfer.js | Call transfer logic |
| ArrowzClickToDial | click_to_dial.js | Click-to-dial buttons |
| ArrowzScreenPop | screen_pop.js | Incoming call popup |
| ArrowzAI | ai_assistant.js | AI analysis features |
| ArrowzPresence | presence.js | Presence management |
| ArrowzLogger | call_logger.js | Call logging |
| ArrowzRecordingPlayer | recording_player.js | Recording playback |
| ArrowzAudioControls | audio_controls.js | Volume & noise settings |

> **ملاحظة:** للمواصفات الفنية التفصيلية، راجع `07-TECHNICAL-SPECS.md`

---

## 🆕 Navbar Softphone Integration

### Navbar Phone Button
```javascript
/**
 * ArrowzNavbarPhone - Navbar integration for softphone
 * 
 * Features:
 * - Phone icon in navbar
 * - Call badge for incoming calls
 * - Toggle popup on click
 */
class ArrowzNavbarPhone {
    constructor() {
        this.popup = null;
        this.softphone = null;
        this.lines = [];
    }
    
    init() {
        this.addNavbarIcon();
        this.createPopup();
        this.loadUserLines();
        this.subscribeToEvents();
    }
    
    addNavbarIcon() {
        const navbarRight = document.querySelector('.navbar-right');
        const phoneItem = document.createElement('li');
        phoneItem.className = 'nav-item arrowz-phone-nav';
        phoneItem.innerHTML = `
            <a class="nav-link" href="#" id="arrowz-phone-trigger">
                <svg class="icon icon-sm"><use href="#icon-call"></use></svg>
                <span class="arrowz-badge hidden" id="arrowz-call-badge"></span>
            </a>
        `;
        navbarRight.prepend(phoneItem);
    }
}
```

### Multi-Tab Popup Structure
```javascript
/**
 * ArrowzSoftphonePopup - Multi-tab popup from navbar
 * 
 * Tabs:
 * - Dialer: Phone number input + optional keypad
 * - Active: Current call status + controls
 * - History: Call history with filters
 * - Incoming: Incoming call UI (auto-shown)
 */
class ArrowzSoftphonePopup {
    constructor(parent) {
        this.parent = parent;
        this.tabs = ['dialer', 'active', 'history', 'incoming'];
        this.currentTab = 'dialer';
    }
    
    showTab(tabName) {
        this.currentTab = tabName;
        this.tabs.forEach(tab => {
            document.getElementById(`arrowz-panel-${tab}`)
                .classList.toggle('active', tab === tabName);
            document.querySelector(`[data-tab="${tab}"]`)
                .classList.toggle('active', tab === tabName);
        });
    }
}
```

### Multi-Line Support
```javascript
/**
 * Multi-line support - Select outbound line
 */
async loadUserLines() {
    const result = await frappe.call({
        method: 'arrowz.api.sip.get_user_lines'
    });
    this.lines = result.message || [];
    this.updateLineSelector(this.lines);
}

selectLine(lineId) {
    this.activeLine = this.lines.find(l => l.id === lineId);
    this.softphone.updateCredentials(this.activeLine);
}
```

### In-Call WhatsApp/SMS Actions
```javascript
/**
 * Show messaging buttons during active call (based on permissions)
 */
async checkInCallActions() {
    const result = await frappe.call({
        method: 'arrowz.api.permissions.get_in_call_actions'
    });
    const perms = result.message || {};
    
    if (perms.can_send_whatsapp && perms.has_whatsapp_account) {
        document.getElementById('arrowz-whatsapp-btn').classList.remove('hidden');
    }
    if (perms.can_send_sms) {
        document.getElementById('arrowz-sms-btn').classList.remove('hidden');
    }
}
```

---

## 1️⃣ ArrowzSoftphone Class

### Class Structure
```javascript
/**
 * ArrowzSoftphone - WebRTC Softphone for Frappe
 * 
 * Dependencies:
 * - JsSIP (WebRTC/SIP library)
 * - jQuery (DOM manipulation)
 * - Frappe (API calls)
 */
class ArrowzSoftphone {
    constructor() {
        this.ua = null;              // JsSIP User Agent
        this.currentSession = null;   // Active call session
        this.isRegistered = false;    // SIP registration status
        this.config = null;           // Server configuration
        this.aiAssistant = null;      // AI integration
        this.callLog = null;          // Call logger
        this.presence = null;         // Presence manager
        
        // Call state
        this.callState = {
            status: 'idle',           // idle/ringing/active/hold
            direction: null,          // inbound/outbound
            startTime: null,
            remoteParty: null,
            isMuted: false,
            isOnHold: false
        };
        
        // Audio elements
        this.localAudio = null;
        this.remoteAudio = null;
        this.ringtone = null;
        
        this.init();
    }
```

### Initialization Flow
```javascript
    async init() {
        console.log('🚀 Initializing Arrowz Softphone...');
        
        // 1. Load configuration from backend
        await this.loadConfiguration();
        
        // 2. Initialize JsSIP
        this.initializeJsSIP();
        
        // 3. Create UI elements
        this.createWidget();
        
        // 4. Setup event handlers
        this.setupEventHandlers();
        
        // 5. Initialize AI Assistant (if enabled)
        if (this.config.ai_enabled) {
            this.aiAssistant = new ArrowzAI(this.config);
        }
        
        // 6. Initialize presence
        this.presence = new ArrowzPresence();
        
        // 7. Initialize call logger
        this.callLog = new ArrowzLogger();
        
        console.log('✅ Arrowz Softphone ready');
    }
```

### Configuration Loading
```javascript
    async loadConfiguration() {
        try {
            const response = await frappe.call({
                method: 'arrowz.api.webrtc.get_webrtc_config',
                args: { user: frappe.session.user }
            });
            
            this.config = response.message;
            
            if (!this.config || this.config.error) {
                throw new Error(this.config?.message || 'Configuration failed');
            }
            
            // Validate required fields
            const required = ['extension', 'sip_uri', 'sip_password', 'websocket_servers'];
            for (const field of required) {
                if (!this.config[field]) {
                    console.warn(`Missing config: ${field}`);
                }
            }
            
        } catch (error) {
            console.error('Config load failed:', error);
            this.showError('Failed to load softphone configuration');
            throw error;
        }
    }
```

### JsSIP Initialization
```javascript
    initializeJsSIP() {
        // Skip if no WebSocket servers configured
        if (!this.config.websocket_servers?.length) {
            console.warn('No WebSocket servers - softphone disabled');
            return;
        }
        
        // Wait for JsSIP to be available
        if (typeof JsSIP === 'undefined') {
            setTimeout(() => this.initializeJsSIP(), 500);
            return;
        }
        
        try {
            // Create WebSocket connection
            const socket = new JsSIP.WebSocketInterface(
                this.config.websocket_servers[0]
            );
            
            // JsSIP configuration
            const configuration = {
                sockets: [socket],
                uri: this.config.sip_uri,
                password: this.config.sip_password,
                display_name: this.config.display_name,
                register: true,
                register_expires: 120,
                no_answer_timeout: 30,
                session_timers: false,
                connection_recovery_min_interval: 2,
                connection_recovery_max_interval: 30
            };
            
            // Create User Agent
            this.ua = new JsSIP.UA(configuration);
            
            // Setup events
            this.setupJsSIPEvents();
            
            // Start
            this.ua.start();
            
        } catch (error) {
            console.error('JsSIP init failed:', error);
            this.showError('Failed to initialize phone');
        }
    }
```

### JsSIP Events
```javascript
    setupJsSIPEvents() {
        // Connection
        this.ua.on('connecting', () => {
            this.updateStatus('connecting', 'Connecting...');
        });
        
        this.ua.on('connected', () => {
            this.updateStatus('connected', 'Connected');
        });
        
        this.ua.on('disconnected', () => {
            this.updateStatus('disconnected', 'Disconnected');
            this.isRegistered = false;
            this.presence?.setStatus('offline');
        });
        
        // Registration
        this.ua.on('registered', () => {
            this.isRegistered = true;
            this.updateStatus('registered', 'Ready');
            this.presence?.setStatus('online');
            
            // Log successful registration
            this.logEvent('sip_registration', {success: true});
        });
        
        this.ua.on('unregistered', () => {
            this.isRegistered = false;
            this.updateStatus('unregistered', 'Unregistered');
        });
        
        this.ua.on('registrationFailed', (e) => {
            this.updateStatus('error', 'Registration Failed');
            this.showError('SIP registration failed');
            this.logEvent('sip_registration_failed', {error: e.cause});
        });
        
        // Incoming calls
        this.ua.on('newRTCSession', (e) => {
            this.handleNewSession(e.session);
        });
    }
```

### Making Calls
```javascript
    /**
     * Initiate outbound call
     * @param {string} phoneNumber - Number to call
     * @param {object} options - Call options
     */
    makeCall(phoneNumber, options = {}) {
        // Validation
        if (!this.isRegistered) {
            frappe.msgprint(__('Phone not ready. Please wait.'));
            return;
        }
        
        if (this.currentSession) {
            frappe.msgprint(__('Call already in progress'));
            return;
        }
        
        // Clean number
        const cleanNumber = this.cleanPhoneNumber(phoneNumber);
        
        // Build SIP URI
        const target = `sip:${cleanNumber}@${this.config.sip_domain}`;
        
        console.log(`📞 Calling: ${cleanNumber}`);
        
        // Call options
        const callOptions = {
            mediaConstraints: {
                audio: true,
                video: false
            },
            rtcConfiguration: {
                iceServers: this.getIceServers()
            },
            pcConfig: {
                iceTransportPolicy: 'all'
            }
        };
        
        // Make call
        const session = this.ua.call(target, callOptions);
        
        // Store context
        session._callContext = {
            direction: 'outbound',
            phoneNumber: cleanNumber,
            contact: options.contact,
            opportunity: options.opportunity,
            startTime: new Date()
        };
        
        this.handleNewSession(session);
    }
```

### Handling Incoming Calls
```javascript
    async handleIncomingCall(session) {
        const callerNumber = session.remote_identity.uri.user;
        
        console.log(`📞 Incoming call from: ${callerNumber}`);
        
        // Update state
        this.callState = {
            status: 'ringing',
            direction: 'inbound',
            remoteParty: callerNumber,
            startTime: new Date()
        };
        
        // Play ringtone
        this.playRingtone();
        
        // Lookup caller in CRM
        const callerInfo = await this.lookupCaller(callerNumber);
        
        // Show incoming call popup
        this.showIncomingCallPopup(session, callerInfo);
        
        // Desktop notification
        this.showDesktopNotification('Incoming Call', 
            callerInfo?.name || callerNumber);
        
        // AI pre-analysis (if enabled)
        if (this.aiAssistant && callerInfo) {
            this.aiAssistant.prepareForCall(callerInfo);
        }
        
        // Auto-popup customer (if enabled)
        if (this.config.auto_popup_customer && callerInfo?.contact) {
            frappe.set_route('Form', 'Contact', callerInfo.contact);
        }
    }
```

### Widget UI
```javascript
    createWidget() {
        // Remove existing
        $('.arrowz-softphone').remove();
        
        // HTML structure
        const html = `
            <div class="arrowz-softphone" id="arrowz-softphone">
                <!-- Header -->
                <div class="softphone-header">
                    <div class="softphone-title">
                        <i class="fa fa-phone"></i> Arrowz
                    </div>
                    <div class="softphone-status" id="sip-status">
                        Initializing...
                    </div>
                    <div class="softphone-controls">
                        <button class="btn-minimize" title="Minimize">−</button>
                        <button class="btn-close" title="Close">×</button>
                    </div>
                </div>
                
                <!-- Body -->
                <div class="softphone-body">
                    <!-- Dial Pad View -->
                    <div class="view-dialpad active">
                        <input type="tel" class="phone-input" 
                               id="phone-number" 
                               placeholder="Enter number...">
                        
                        <div class="dial-pad">
                            ${this.createDialPadButtons()}
                        </div>
                        
                        <div class="call-actions">
                            <button class="btn-call" id="btn-call">
                                <i class="fa fa-phone"></i> Call
                            </button>
                        </div>
                    </div>
                    
                    <!-- Active Call View -->
                    <div class="view-call">
                        <div class="call-info">
                            <div class="caller-name" id="caller-name">
                                Unknown
                            </div>
                            <div class="call-timer" id="call-timer">
                                00:00
                            </div>
                            <div class="call-status" id="call-status">
                                Calling...
                            </div>
                        </div>
                        
                        <div class="call-controls">
                            <button class="btn-mute" id="btn-mute">
                                <i class="fa fa-microphone"></i>
                            </button>
                            <button class="btn-hold" id="btn-hold">
                                <i class="fa fa-pause"></i>
                            </button>
                            <button class="btn-transfer" id="btn-transfer">
                                <i class="fa fa-exchange"></i>
                            </button>
                            <button class="btn-hangup" id="btn-hangup">
                                <i class="fa fa-phone"></i>
                            </button>
                        </div>
                        
                        <!-- AI Panel (if enabled) -->
                        <div class="ai-panel" id="ai-panel">
                            <div class="ai-sentiment" id="ai-sentiment">
                                Sentiment: --
                            </div>
                            <div class="ai-suggestions" id="ai-suggestions">
                            </div>
                        </div>
                    </div>
                    
                    <!-- History View -->
                    <div class="view-history">
                        <div class="call-history-list" id="call-history">
                        </div>
                    </div>
                </div>
                
                <!-- Footer/Tabs -->
                <div class="softphone-footer">
                    <button class="tab-btn active" data-view="dialpad">
                        <i class="fa fa-th"></i>
                    </button>
                    <button class="tab-btn" data-view="history">
                        <i class="fa fa-history"></i>
                    </button>
                    <button class="tab-btn" data-view="settings">
                        <i class="fa fa-cog"></i>
                    </button>
                </div>
                
                <!-- Audio Elements -->
                <audio id="remote-audio" autoplay></audio>
                <audio id="local-audio" muted></audio>
                <audio id="ringtone" loop>
                    <source src="/assets/arrowz/sounds/ringtone.mp3">
                </audio>
            </div>
        `;
        
        $('body').append(html);
        
        // Make draggable
        this.makeDraggable();
        
        // Bind events
        this.bindUIEvents();
    }
```

---

## 2️⃣ ArrowzAI Class

### Class Structure
```javascript
/**
 * ArrowzAI - AI-powered call assistance
 */
class ArrowzAI {
    constructor(config) {
        this.config = config;
        this.isActive = false;
        this.currentCallData = null;
        
        // Analysis state
        this.sentimentHistory = [];
        this.transcripts = [];
        this.suggestions = [];
        this.coachingTips = [];
        
        // Browser speech recognition
        this.recognition = null;
        this.isTranscribing = false;
    }
```

### Real-time Transcription
```javascript
    /**
     * Start live transcription using Web Speech API
     */
    startTranscription() {
        if (!('webkitSpeechRecognition' in window)) {
            console.warn('Speech recognition not supported');
            return;
        }
        
        this.recognition = new webkitSpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = this.config.transcription_language || 'en-US';
        
        this.recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            if (finalTranscript) {
                this.processTranscript(finalTranscript);
            }
            
            this.updateTranscriptUI(finalTranscript, interimTranscript);
        };
        
        this.recognition.start();
        this.isTranscribing = true;
    }
```

### Sentiment Analysis
```javascript
    /**
     * Analyze sentiment of transcript segment
     */
    async analyzeSentiment(text) {
        try {
            const response = await frappe.call({
                method: 'arrowz.api.ai.analyze_sentiment',
                args: {
                    text: text,
                    context: this.getRecentContext()
                }
            });
            
            const result = response.message;
            
            // Store in history
            this.sentimentHistory.push({
                timestamp: new Date(),
                text: text,
                sentiment: result.sentiment,
                score: result.score
            });
            
            // Update UI
            this.updateSentimentUI(result);
            
            // Check for alerts
            this.checkSentimentAlerts(result);
            
            return result;
            
        } catch (error) {
            console.error('Sentiment analysis failed:', error);
        }
    }
```

### Coaching Suggestions
```javascript
    /**
     * Get real-time coaching suggestions
     */
    async getCoachingSuggestions() {
        if (!this.config.enable_coaching) return;
        
        try {
            const response = await frappe.call({
                method: 'arrowz.api.ai.get_coaching_suggestions',
                args: {
                    transcript: this.getRecentTranscript(),
                    sentiment: this.getCurrentSentiment(),
                    context: this.currentCallData
                }
            });
            
            const suggestions = response.message?.suggestions || [];
            
            // Display suggestions
            this.displaySuggestions(suggestions);
            
        } catch (error) {
            console.error('Coaching suggestions failed:', error);
        }
    }
```

---

## 3️⃣ ArrowzPresence Class

```javascript
/**
 * ArrowzPresence - Real-time presence management
 */
class ArrowzPresence {
    constructor() {
        this.currentStatus = 'offline';
        this.heartbeatInterval = null;
        this.teamMembers = [];
    }
    
    /**
     * Initialize presence management
     */
    initialize() {
        // Set initial status
        this.setStatus('online');
        
        // Start heartbeat
        this.startHeartbeat();
        
        // Subscribe to realtime updates
        this.subscribeToUpdates();
        
        // Load team presence
        this.loadTeamPresence();
    }
    
    /**
     * Update user status
     */
    async setStatus(status) {
        try {
            await frappe.call({
                method: 'arrowz.api.presence.update_user_status',
                args: { status: status }
            });
            
            this.currentStatus = status;
            this.updateStatusUI(status);
            
        } catch (error) {
            console.error('Status update failed:', error);
        }
    }
    
    /**
     * Send heartbeat to maintain presence
     */
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            frappe.call({
                method: 'arrowz.api.presence.send_presence_heartbeat',
                async: true
            });
        }, 60000); // Every minute
    }
    
    /**
     * Subscribe to realtime presence updates
     */
    subscribeToUpdates() {
        frappe.realtime.on('presence_update', (data) => {
            this.handlePresenceUpdate(data);
        });
    }
}
```

---

## 4️⃣ Click-to-Call Integration

### DocType Integration
```javascript
/**
 * Add click-to-call to ERPNext DocTypes
 * File: doctype_integrations.js
 */

// Contact integration
frappe.ui.form.on('Contact', {
    refresh(frm) {
        if (!frm.is_new()) {
            // Add Call button
            frm.add_custom_button(__('Call'), () => {
                const phone = frm.doc.mobile_no || frm.doc.phone;
                if (phone && window.arrowzSoftphone) {
                    window.arrowzSoftphone.makeCall(phone, {
                        contact: frm.doc.name,
                        contactName: `${frm.doc.first_name} ${frm.doc.last_name}`
                    });
                }
            }, __('Arrowz'));
            
            // Add View Calls button
            frm.add_custom_button(__('Call History'), () => {
                showCallHistory(frm.doc.name);
            }, __('Arrowz'));
        }
    }
});

// Lead integration
frappe.ui.form.on('Lead', {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.mobile_no) {
            frm.add_custom_button(__('Call'), () => {
                window.arrowzSoftphone?.makeCall(frm.doc.mobile_no, {
                    lead: frm.doc.name,
                    leadName: frm.doc.lead_name
                });
            }, __('Arrowz'));
        }
    }
});

// Opportunity integration  
frappe.ui.form.on('Opportunity', {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Call Contact'), async () => {
                const contact = await getOpportunityContact(frm.doc.name);
                if (contact?.phone) {
                    window.arrowzSoftphone?.makeCall(contact.phone, {
                        opportunity: frm.doc.name
                    });
                }
            }, __('Arrowz'));
        }
    }
});
```

### Phone Field Click Handler
```javascript
/**
 * Make phone fields clickable globally
 */
$(document).on('click', '[data-fieldtype="Phone"] .like-disabled-input, [data-fieldtype="Data"] .phone-link', function(e) {
    e.preventDefault();
    
    const phone = $(this).text().trim();
    if (phone && window.arrowzSoftphone) {
        window.arrowzSoftphone.makeCall(phone);
    }
});
```

---

## 🎨 CSS Specifications

### Softphone Styles
```css
/* softphone.css */

.arrowz-softphone {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 320px;
    min-height: 400px;
    background: var(--card-bg, #ffffff);
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
    z-index: 9999;
    font-family: var(--font-stack, -apple-system, BlinkMacSystemFont, sans-serif);
    overflow: hidden;
    transition: all 0.3s ease;
}

/* Dark mode support */
[data-theme="dark"] .arrowz-softphone {
    background: var(--card-bg, #1e1e1e);
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
}

/* Minimized state */
.arrowz-softphone.minimized {
    height: 50px;
    min-height: 50px;
}

/* Header */
.softphone-header {
    background: linear-gradient(135deg, #5e35b1 0%, #3949ab 100%);
    color: white;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: move;
}

/* Status indicator */
.softphone-status {
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 12px;
    background: rgba(255,255,255,0.2);
}

.softphone-status.registered {
    background: rgba(76, 175, 80, 0.4);
}

.softphone-status.error {
    background: rgba(244, 67, 54, 0.4);
}

/* Dial pad */
.dial-pad {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    padding: 16px;
}

.dial-btn {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    border: 1px solid var(--border-color);
    background: var(--btn-default-bg);
    font-size: 24px;
    cursor: pointer;
    transition: all 0.2s;
}

.dial-btn:hover {
    background: var(--btn-primary);
    color: white;
}

/* Call button */
.btn-call {
    width: 100%;
    padding: 12px;
    background: #4caf50;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
}

.btn-hangup {
    background: #f44336;
}

/* AI Panel */
.ai-panel {
    background: var(--subtle-bg, #f8f9fa);
    padding: 12px;
    margin-top: 12px;
    border-radius: 8px;
}

.ai-sentiment {
    font-size: 12px;
    margin-bottom: 8px;
}

.ai-sentiment.positive { color: #4caf50; }
.ai-sentiment.negative { color: #f44336; }
.ai-sentiment.neutral { color: #ff9800; }
```

---

## 🔧 hooks.py Integration

```python
# hooks.py

app_include_js = [
    "/assets/arrowz/js/lib/jssip.min.js",
    "/assets/arrowz/js/presence.js",
    "/assets/arrowz/js/ai_assistant.js",
    "/assets/arrowz/js/call_logger.js",
    "/assets/arrowz/js/softphone.js",
    "/assets/arrowz/js/doctype_integrations.js"
]

app_include_css = [
    "/assets/arrowz/css/softphone.css",
    "/assets/arrowz/css/dashboard.css"
]

doctype_js = {
    "Contact": "public/js/contact.js",
    "Lead": "public/js/lead.js",
    "Opportunity": "public/js/opportunity.js",
    "Customer": "public/js/customer.js"
}
```

---

*Next: See `05-INTEGRATION-GUIDE.md` for PBX/AI setup*
