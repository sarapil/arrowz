/**
 * Arrowz Softphone V2 - Professional Navbar Integration
 * Features:
 * - Dropdown on desktop, modal on mobile
 * - Multi-extension support with quick switcher
 * - Real-time status indicators (SMS, Calls, Line status)
 * - Contact search across all linked DocTypes
 * - Responsive design
 */

(function() {
    'use strict';
    
    // Arrowz namespace
    window.arrowz = window.arrowz || {};
    
    // Softphone V2
    arrowz.softphone = {
        initialized: false,
        registered: false,
        ua: null,  // JsSIP User Agent
        session: null,  // Active call session
        config: null,
        allExtensions: [],  // All user's extensions
        activeExtension: null,  // Current active extension
        audioPlayer: null,
        localStream: null,
        remoteStream: null,
        callTimer: null,
        callStartTime: null,
        isDropdownOpen: false,
        pendingSMS: [],
        missedCalls: 0,
        
        // Initialize softphone
        async init() {
            if (this.initialized) return;
            
            try {
                // Add navbar widget first
                this.renderNavbarWidget();
                
                // Load JsSIP if not available
                if (typeof JsSIP === 'undefined') {
                    await this.loadJsSIP();
                }
                
                // Get all user extensions
                await this.loadExtensions();
                
                // Initialize audio
                this.initAudio();
                
                // Setup real-time listeners
                this.setupRealtimeListeners();
                
                // Check for missed calls/SMS
                this.checkNotifications();
                
                this.initialized = true;
                console.log('Arrowz Softphone V2 initialized');
                
            } catch (error) {
                console.error('Arrowz Softphone init error:', error);
                this.updateNavbarStatus('error', 'Error');
            }
        },
        
        // Load JsSIP library
        loadJsSIP() {
            return new Promise((resolve, reject) => {
                if (typeof JsSIP !== 'undefined') {
                    resolve();
                    return;
                }
                const script = document.createElement('script');
                script.src = '/assets/arrowz/js/jssip.min.js';
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
        },
        
        // Load user's extensions
        async loadExtensions() {
            try {
                const r = await frappe.call({
                    method: 'arrowz.api.webrtc.get_webrtc_config'
                });
                
                if (!r.message) {
                    this.updateNavbarStatus('no-config', __('No Extension'));
                    return;
                }
                
                this.config = r.message;
                this.activeExtension = r.message.extension_name;
                this.allExtensions = r.message.all_extensions || [];
                
                // Setup JsSIP with first/active extension
                await this.setupJsSIP();
                
            } catch (e) {
                console.error('Error loading extensions:', e);
                this.updateNavbarStatus('error', __('Error'));
            }
        },
        
        // Initialize audio elements
        initAudio() {
            // Remote audio
            if (!document.getElementById('arrowz-remote-audio')) {
                this.audioPlayer = document.createElement('audio');
                this.audioPlayer.id = 'arrowz-remote-audio';
                this.audioPlayer.autoplay = true;
                this.audioPlayer.playsInline = true;
                document.body.appendChild(this.audioPlayer);
            } else {
                this.audioPlayer = document.getElementById('arrowz-remote-audio');
            }
            
            // Ringtone
            if (!document.getElementById('arrowz-ringtone')) {
                this.ringtone = document.createElement('audio');
                this.ringtone.id = 'arrowz-ringtone';
                this.ringtone.loop = true;
                this.ringtone.playsInline = true;
                this.ringtone.src = '/assets/arrowz/sounds/ringtone.mp3';
                this.ringtone.load();
                document.body.appendChild(this.ringtone);
            } else {
                this.ringtone = document.getElementById('arrowz-ringtone');
            }
        },
        
        // Setup JsSIP User Agent
        async setupJsSIP() {
            if (!this.config) return;
            
            const socket = new JsSIP.WebSocketInterface(this.config.websocket_servers[0]);
            
            console.log('Arrowz: Setting up JsSIP with URI:', this.config.sip_uri);
            
            const configuration = {
                sockets: [socket],
                uri: this.config.sip_uri,
                password: this.config.sip_password,
                display_name: this.config.display_name,
                register: true,
                session_timers: false,
                register_expires: 300,
                user_agent: 'Arrowz-WebRTC/2.0'
            };
            
            if (this.config.outbound_proxy) {
                configuration.outbound_proxy_set = this.config.outbound_proxy;
            }
            
            // Create new UA with unique ID
            const newUA = new JsSIP.UA(configuration);
            const uaId = Date.now();
            newUA._arrowz_id = uaId;
            this._currentUAId = uaId;
            this.ua = newUA;
            
            // Event handlers - check if this is still the current UA
            const checkCurrentUA = () => this.ua && this.ua._arrowz_id === uaId;
            
            this.ua.on('connected', () => {
                if (!checkCurrentUA()) return;
                console.log('Arrowz: WebSocket connected');
                this.updateNavbarStatus('connecting', __('Connecting...'));
            });
            
            this.ua.on('disconnected', () => {
                if (!checkCurrentUA()) {
                    console.log('Arrowz: Ignoring disconnected event from old UA');
                    return;
                }
                console.log('Arrowz: WebSocket disconnected');
                this.registered = false;
                this.updateNavbarStatus('disconnected', __('Offline'));
            });
            
            this.ua.on('registered', () => {
                if (!checkCurrentUA()) return;
                console.log('Arrowz: SIP registered');
                this.registered = true;
                this.updateNavbarStatus('registered', this.config.extension);
            });
            
            this.ua.on('unregistered', () => {
                if (!checkCurrentUA()) {
                    console.log('Arrowz: Ignoring unregistered event from old UA');
                    return;
                }
                console.log('Arrowz: SIP unregistered');
                this.registered = false;
                this.updateNavbarStatus('unregistered', __('Unregistered'));
            });
            
            this.ua.on('registrationFailed', (e) => {
                if (!checkCurrentUA()) return;
                console.error('Arrowz: Registration failed:', e.cause);
                this.registered = false;
                this.updateNavbarStatus('failed', __('Failed'));
                frappe.show_alert({
                    message: __('SIP Registration Failed: {0}', [e.cause]),
                    indicator: 'red'
                }, 7);
            });
            
            this.ua.on('newRTCSession', (e) => {
                if (!checkCurrentUA()) return;
                this.handleNewSession(e);
            });
            
            this.ua.start();
        },
        
        // Setup real-time listeners for notifications
        setupRealtimeListeners() {
            // Listen for incoming SMS
            frappe.realtime.on('arrowz_new_sms', (data) => {
                this.pendingSMS.push(data);
                this.updateNavbarBadge();
                this.showNotification('sms', data);
            });
            
            // Listen for missed calls
            frappe.realtime.on('arrowz_missed_call', (data) => {
                this.missedCalls++;
                this.updateNavbarBadge();
            });
        },
        
        // Check for pending notifications
        async checkNotifications() {
            try {
                const r = await frappe.call({
                    method: 'arrowz.api.notifications.get_pending_notifications'
                });
                
                if (r.message) {
                    this.pendingSMS = r.message.pending_sms || [];
                    this.missedCalls = r.message.missed_calls || 0;
                    this.updateNavbarBadge();
                }
            } catch (e) {
                // Notifications API might not exist yet
            }
        },
        
        // Render navbar widget
        renderNavbarWidget() {
            // Remove existing widget
            const existing = document.getElementById('arrowz-softphone-widget');
            if (existing) existing.remove();
            
            // Find navbar - Frappe v15 uses .navbar-nav inside .collapse.navbar-collapse
            let navbar = document.querySelector('.navbar .navbar-collapse .navbar-nav');
            
            // Fallback selectors for different Frappe versions
            if (!navbar) {
                navbar = document.querySelector('.navbar-right') || 
                         document.querySelector('.navbar-nav') ||
                         document.querySelector('#navbar-user')?.parentElement;
            }
            
            if (!navbar) {
                // Retry after a short delay - navbar might not be rendered yet
                setTimeout(() => this.renderNavbarWidget(), 500);
                console.log('Arrowz: Navbar not found, will retry...');
                return;
            }
            
            // Create widget
            const widget = document.createElement('li');
            widget.id = 'arrowz-softphone-widget';
            widget.className = 'nav-item arrowz-softphone-nav';
            widget.innerHTML = `
                <div class="arrowz-sp-trigger" onclick="arrowz.softphone.toggleDropdown()">
                    <div class="sp-icon-wrapper">
                        <svg class="sp-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/>
                        </svg>
                        <span class="sp-status-dot"></span>
                    </div>
                    <span class="sp-badge" style="display: none;"></span>
                    <span class="sp-status-text">${__('Loading...')}</span>
                    <span class="sp-call-timer" style="display: none;">00:00</span>
                </div>
                <div class="arrowz-sp-dropdown" id="arrowz-sp-dropdown">
                    <!-- Content loaded dynamically -->
                </div>
            `;
            
            // Insert at appropriate position
            navbar.insertBefore(widget, navbar.firstChild);
            
            // Add styles
            this.addStyles();
            
            // Close dropdown on outside click
            document.addEventListener('click', (e) => {
                if (!e.target.closest('#arrowz-softphone-widget')) {
                    this.closeDropdown();
                }
            });
        },
        
        // Toggle dropdown/modal
        toggleDropdown() {
            if (this.isDropdownOpen) {
                this.closeDropdown();
            } else {
                this.openDropdown();
            }
        },
        
        // Open dropdown
        openDropdown() {
            if (this.session) {
                // If in call, show call UI
                this.showActiveCallUI();
            } else {
                // Show dialer
                this.showDialerUI();
            }
            
            const dropdown = document.getElementById('arrowz-sp-dropdown');
            if (dropdown) {
                dropdown.classList.add('open');
                
                // Check if mobile
                if (window.innerWidth < 768) {
                    dropdown.classList.add('mobile-modal');
                    document.body.classList.add('arrowz-modal-open');
                }
            }
            
            this.isDropdownOpen = true;
        },
        
        // Close dropdown
        closeDropdown() {
            const dropdown = document.getElementById('arrowz-sp-dropdown');
            if (dropdown) {
                dropdown.classList.remove('open');
                dropdown.classList.remove('mobile-modal');
                document.body.classList.remove('arrowz-modal-open');
            }
            this.isDropdownOpen = false;
        },
        
        // Show dialer UI
        showDialerUI() {
            const dropdown = document.getElementById('arrowz-sp-dropdown');
            if (!dropdown) return;
            
            // Build extension buttons if multiple
            let extensionButtons = '';
            if (this.allExtensions.length > 1) {
                extensionButtons = `
                    <div class="sp-extension-selector">
                        <div class="sp-ext-label">${__('Call from')}:</div>
                        <div class="sp-ext-buttons">
                            ${this.allExtensions.map(ext => `
                                <button class="sp-ext-btn ${ext.name === this.activeExtension ? 'active' : ''}"
                                        onclick="arrowz.softphone.switchExtension('${ext.name}')"
                                        title="${ext.display_name || ext.extension}">
                                    ${ext.extension}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            dropdown.innerHTML = `
                <div class="sp-header">
                    <div class="sp-header-info">
                        <span class="sp-status-indicator ${this.registered ? 'online' : 'offline'}"></span>
                        <span class="sp-ext-number">${this.config?.extension || '---'}</span>
                        <span class="sp-status-label">${this.registered ? __('Ready') : __('Offline')}</span>
                    </div>
                    <button class="sp-close-btn" onclick="arrowz.softphone.closeDropdown()">×</button>
                </div>
                
                <div class="sp-content">
                    ${extensionButtons}
                    
                    <div class="sp-search-container">
                        <input type="text" class="sp-search-input" id="sp-search-input" 
                               placeholder="${__('Search contacts or enter number...')}"
                               oninput="arrowz.softphone.handleSearchInput(this.value)">
                        <div class="sp-search-results" id="sp-search-results"></div>
                    </div>
                    
                    <div class="sp-dial-display">
                        <input type="tel" class="sp-dial-input" id="sp-dial-input" 
                               placeholder="${__('Enter number')}"
                               onkeypress="if(event.key==='Enter')arrowz.softphone.dial()">
                        <button class="sp-backspace" onclick="arrowz.softphone.backspace()">⌫</button>
                    </div>
                    
                    <div class="sp-dialpad">
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('1')">1<span></span></button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('2')">2<span>ABC</span></button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('3')">3<span>DEF</span></button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('4')">4<span>GHI</span></button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('5')">5<span>JKL</span></button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('6')">6<span>MNO</span></button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('7')">7<span>PQRS</span></button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('8')">8<span>TUV</span></button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('9')">9<span>WXYZ</span></button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('*')">*<span></span></button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('0')">0<span>+</span></button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('#')">#<span></span></button>
                    </div>
                    
                    <div class="sp-actions">
                        <button class="sp-call-btn ${!this.registered ? 'disabled' : ''}" 
                                onclick="arrowz.softphone.dial()" ${!this.registered ? 'disabled' : ''}>
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/>
                            </svg>
                        </button>
                    </div>
                </div>
                
                <div class="sp-footer">
                    <button class="sp-footer-btn" onclick="arrowz.softphone.showHistory()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        ${__('History')}
                    </button>
                    <button class="sp-footer-btn" onclick="arrowz.softphone.showSettings()">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
                        ${__('Settings')}
                    </button>
                </div>
            `;
        },
        
        // Show active call UI
        showActiveCallUI(number) {
            const dropdown = document.getElementById('arrowz-sp-dropdown');
            if (!dropdown) return;
            
            const callee = number || this._currentCallee || __('Unknown');
            
            dropdown.innerHTML = `
                <div class="sp-call-screen">
                    <div class="sp-call-header">
                        <div class="sp-call-avatar">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                            </svg>
                        </div>
                        <div class="sp-call-info">
                            <div class="sp-callee-number">${callee}</div>
                            <div class="sp-call-status" id="sp-call-status">${__('Connecting...')}</div>
                            <div class="sp-call-duration" id="sp-call-duration">00:00</div>
                        </div>
                    </div>
                    
                    <div class="sp-call-actions">
                        <button class="sp-call-action" onclick="arrowz.softphone.toggleMute()" id="sp-mute-btn">
                            <svg viewBox="0 0 24 24" fill="currentColor" class="unmuted">
                                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                            </svg>
                            <svg viewBox="0 0 24 24" fill="currentColor" class="muted" style="display:none">
                                <path d="M19 11h-1.7c0 .74-.16 1.43-.43 2.05l1.23 1.23c.56-.98.9-2.09.9-3.28zm-4.02.17c0-.06.02-.11.02-.17V5c0-1.66-1.34-3-3-3S9 3.34 9 5v.18l5.98 5.99zM4.27 3L3 4.27l6.01 6.01V11c0 1.66 1.33 3 2.99 3 .22 0 .44-.03.65-.08l1.66 1.66c-.71.33-1.5.52-2.31.52-2.76 0-5.3-2.1-5.3-5.1H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c.91-.13 1.77-.45 2.54-.9L19.73 21 21 19.73 4.27 3z"/>
                            </svg>
                            <span>${__('Mute')}</span>
                        </button>
                        <button class="sp-call-action" onclick="arrowz.softphone.toggleHold()" id="sp-hold-btn">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                            </svg>
                            <span>${__('Hold')}</span>
                        </button>
                        <button class="sp-call-action" onclick="arrowz.softphone.toggleKeypad()">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 19c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM6 1c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm12-8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm-6 8c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm6 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-6 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                            </svg>
                            <span>${__('Keypad')}</span>
                        </button>
                        <button class="sp-call-action" onclick="arrowz.softphone.transfer()">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/>
                            </svg>
                            <span>${__('Transfer')}</span>
                        </button>
                    </div>
                    
                    <div class="sp-keypad-overlay" id="sp-keypad-overlay" style="display:none;">
                        <div class="sp-dialpad compact">
                            <button class="sp-key" onclick="arrowz.softphone.sendDTMF('1')">1</button>
                            <button class="sp-key" onclick="arrowz.softphone.sendDTMF('2')">2</button>
                            <button class="sp-key" onclick="arrowz.softphone.sendDTMF('3')">3</button>
                            <button class="sp-key" onclick="arrowz.softphone.sendDTMF('4')">4</button>
                            <button class="sp-key" onclick="arrowz.softphone.sendDTMF('5')">5</button>
                            <button class="sp-key" onclick="arrowz.softphone.sendDTMF('6')">6</button>
                            <button class="sp-key" onclick="arrowz.softphone.sendDTMF('7')">7</button>
                            <button class="sp-key" onclick="arrowz.softphone.sendDTMF('8')">8</button>
                            <button class="sp-key" onclick="arrowz.softphone.sendDTMF('9')">9</button>
                            <button class="sp-key" onclick="arrowz.softphone.sendDTMF('*')">*</button>
                            <button class="sp-key" onclick="arrowz.softphone.sendDTMF('0')">0</button>
                            <button class="sp-key" onclick="arrowz.softphone.sendDTMF('#')">#</button>
                        </div>
                    </div>
                    
                    <div class="sp-hangup-section">
                        <button class="sp-hangup-btn" onclick="arrowz.softphone.hangup()">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28-.79-.74-1.69-1.36-2.67-1.85-.33-.16-.56-.5-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
            
            dropdown.classList.add('open');
            if (window.innerWidth < 768) {
                dropdown.classList.add('mobile-modal');
            }
            this.isDropdownOpen = true;
        },
        
        // Show incoming call UI
        showIncomingCallUI(caller) {
            const dropdown = document.getElementById('arrowz-sp-dropdown');
            if (!dropdown) return;
            
            dropdown.innerHTML = `
                <div class="sp-incoming-screen">
                    <div class="sp-incoming-animation">
                        <div class="sp-pulse-ring"></div>
                        <div class="sp-pulse-ring delay"></div>
                        <div class="sp-caller-avatar">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                            </svg>
                        </div>
                    </div>
                    <div class="sp-caller-info">
                        <div class="sp-caller-id">${caller}</div>
                        <div class="sp-incoming-label">${__('Incoming Call')}</div>
                    </div>
                    <div class="sp-incoming-actions">
                        <button class="sp-reject-btn" onclick="arrowz.softphone.rejectCall()">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28-.79-.74-1.69-1.36-2.67-1.85-.33-.16-.56-.5-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z"/>
                            </svg>
                        </button>
                        <button class="sp-answer-btn" onclick="arrowz.softphone.answerCall()">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
            
            dropdown.classList.add('open', 'incoming');
            if (window.innerWidth < 768) {
                dropdown.classList.add('mobile-modal');
            }
            this.isDropdownOpen = true;
        },
        
        // Handle search input
        async handleSearchInput(query) {
            const resultsContainer = document.getElementById('sp-search-results');
            if (!resultsContainer) return;
            
            if (query.length < 2) {
                resultsContainer.style.display = 'none';
                return;
            }
            
            try {
                const r = await frappe.call({
                    method: 'arrowz.api.contacts.search_contacts',
                    args: { query: query, limit: 10 }
                });
                
                const contacts = r.message || [];
                
                if (contacts.length === 0) {
                    resultsContainer.innerHTML = `
                        <div class="sp-no-results">${__('No contacts found')}</div>
                    `;
                } else {
                    resultsContainer.innerHTML = contacts.map(c => `
                        <div class="sp-contact-item" onclick="arrowz.softphone.selectContact('${c.phone}', '${c.name}')">
                            <div class="sp-contact-avatar">${(c.name || '?')[0].toUpperCase()}</div>
                            <div class="sp-contact-details">
                                <div class="sp-contact-name">${c.name || __('Unknown')}</div>
                                <div class="sp-contact-phone">${c.phone}</div>
                                <div class="sp-contact-type">${c.doctype}</div>
                            </div>
                        </div>
                    `).join('');
                }
                
                resultsContainer.style.display = 'block';
                
            } catch (e) {
                console.error('Search error:', e);
            }
        },
        
        // Select contact from search
        selectContact(phone, name) {
            const dialInput = document.getElementById('sp-dial-input');
            if (dialInput) {
                dialInput.value = phone;
            }
            
            const searchInput = document.getElementById('sp-search-input');
            if (searchInput) {
                searchInput.value = name;
            }
            
            const resultsContainer = document.getElementById('sp-search-results');
            if (resultsContainer) {
                resultsContainer.style.display = 'none';
            }
        },
        
        // Wait for registration with timeout
        waitForRegistration(timeout = 10000) {
            return new Promise((resolve, reject) => {
                // Check if already registered
                if (this.registered) {
                    resolve(true);
                    return;
                }
                
                const timeoutId = setTimeout(() => {
                    cleanup();
                    reject(new Error('Registration timeout'));
                }, timeout);
                
                const onRegistered = () => {
                    cleanup();
                    resolve(true);
                };
                
                const onFailed = (e) => {
                    cleanup();
                    reject(new Error(e?.cause || 'Registration failed'));
                };
                
                const cleanup = () => {
                    clearTimeout(timeoutId);
                    if (this.ua) {
                        this.ua.off('registered', onRegistered);
                        this.ua.off('registrationFailed', onFailed);
                    }
                };
                
                if (this.ua) {
                    this.ua.on('registered', onRegistered);
                    this.ua.on('registrationFailed', onFailed);
                } else {
                    reject(new Error('No UA available'));
                }
            });
        },
        
        // Switch extension
        async switchExtension(extensionName) {
            if (extensionName === this.activeExtension) return;
            
            try {
                // Stop current UA
                if (this.ua) {
                    this.ua.stop();
                    this.registered = false;
                }
                
                this.updateNavbarStatus('connecting', __('Switching...'));
                
                // Get new config
                const r = await frappe.call({
                    method: 'arrowz.api.webrtc.get_webrtc_config',
                    args: { extension_name: extensionName }
                });
                
                if (r.message) {
                    this.config = r.message;
                    this.activeExtension = extensionName;
                    await this.setupJsSIP();
                    
                    // Wait for registration to complete
                    try {
                        await this.waitForRegistration(10000);
                    } catch (regError) {
                        console.warn('Registration wait failed:', regError.message);
                        // Continue anyway, the UI will show offline status
                    }
                    
                    // Refresh dropdown
                    if (this.isDropdownOpen) {
                        this.showDialerUI();
                    }
                    
                    frappe.show_alert({
                        message: __('Switched to extension {0}', [r.message.extension]),
                        indicator: 'green'
                    }, 3);
                }
                
            } catch (e) {
                console.error('Switch extension error:', e);
                frappe.show_alert({
                    message: __('Failed to switch extension'),
                    indicator: 'red'
                });
            }
        },
        
        // Press key on dialpad
        pressKey(digit) {
            const input = document.getElementById('sp-dial-input');
            if (input) {
                input.value += digit;
            }
            
            // Send DTMF if in call
            if (this.session) {
                this.sendDTMF(digit);
            }
        },
        
        // Backspace
        backspace() {
            const input = document.getElementById('sp-dial-input');
            if (input) {
                input.value = input.value.slice(0, -1);
            }
        },
        
        // Make call
        async dial() {
            const input = document.getElementById('sp-dial-input');
            const number = input?.value.trim();
            
            if (!number) {
                frappe.show_alert({
                    message: __('Please enter a number'),
                    indicator: 'yellow'
                });
                return;
            }
            
            await this.makeCall(number);
        },
        
        // Make outgoing call
        async makeCall(number) {
            if (!this.registered) {
                frappe.show_alert({
                    message: __('Softphone not registered'),
                    indicator: 'red'
                });
                return;
            }
            
            if (this.session) {
                frappe.show_alert({
                    message: __('Already on a call'),
                    indicator: 'yellow'
                });
                return;
            }
            
            try {
                this._currentCallee = number;
                
                // Get microphone access
                this.localStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    },
                    video: false
                });
                
                // Show call UI immediately
                this.showActiveCallUI(number);
                this.updateNavbarStatus('calling', number);
                
                // Setup call options - use single STUN server to reduce ICE gathering time
                const iceServers = this.config.ice_servers && this.config.ice_servers.length > 0 
                    ? [this.config.ice_servers[0]]  // Use only first server
                    : [{ urls: 'stun:stun.l.google.com:19302' }];
                
                const options = {
                    mediaConstraints: { audio: true, video: false },
                    mediaStream: this.localStream,
                    pcConfig: {
                        iceServers: iceServers,
                        rtcpMuxPolicy: 'negotiate',
                        bundlePolicy: 'balanced',  // Use 'balanced' - FreePBX may not support BUNDLE
                        iceCandidatePoolSize: 0    // Disable pre-gathering for faster call setup
                    },
                    rtcOfferConstraints: {
                        offerToReceiveAudio: true,
                        offerToReceiveVideo: false
                    }
                };
                
                // Format number
                let dialNumber = number.replace(/[^\d+*#]/g, '');
                if (dialNumber.length >= 10 && /^\d+$/.test(dialNumber)) {
                    dialNumber = '+' + dialNumber;
                }
                
                const targetUri = `sip:${dialNumber}@${this.config.sip_domain}`;
                
                console.log('Arrowz: Making call to:', targetUri);
                console.log('Arrowz: Call options:', JSON.stringify(options.pcConfig));
                
                // Create call log and store reference
                frappe.call({
                    method: 'arrowz.api.webrtc.initiate_call',
                    args: { number: dialNumber },
                    async: true,
                    callback: (r) => {
                        if (r.message?.call_log) {
                            this._currentCallLog = r.message.call_log;
                            console.log('Arrowz: Outgoing call log created:', this._currentCallLog);
                        }
                    }
                });
                
                // Make the call
                this.session = this.ua.call(targetUri, options);
                console.log('Arrowz: Call session created');
                this.setupSessionEvents();
                
            } catch (error) {
                console.error('Make call error:', error);
                frappe.show_alert({
                    message: __('Failed to access microphone'),
                    indicator: 'red'
                });
                this.endCall();
            }
        },
        
        // Handle new RTC session
        handleNewSession(e) {
            const session = e.session;
            
            if (this.session) {
                session.terminate({ status_code: 486, reason_phrase: 'Busy Here' });
                return;
            }
            
            this.session = session;
            
            if (session.direction === 'incoming') {
                const caller = session.remote_identity.display_name || session.remote_identity.uri.user;
                this._currentCallee = caller;
                
                this.playRingtone();
                this.showIncomingCallUI(caller);
                this.updateNavbarStatus('incoming', caller);
                
                // Browser notification
                this.showBrowserNotification(caller);
                
                // CRITICAL: Pre-request microphone access immediately when call arrives
                // This reduces answer delay from ~15 seconds to ~1-2 seconds
                console.log('Arrowz: Pre-requesting microphone access for faster answer...');
                navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    },
                    video: false
                }).then(stream => {
                    console.log('Arrowz: Microphone pre-granted, ready for instant answer');
                    this._preGrantedStream = stream;  // Store for later use
                }).catch(error => {
                    console.warn('Arrowz: Microphone pre-request failed:', error.name);
                    // User will get prompted again when they click Answer
                    this._preGrantedStream = null;
                });
                
                frappe.call({
                    method: 'arrowz.api.webrtc.on_incoming_call',
                    args: { caller_id: caller, call_id: session.id },
                    async: true,
                    callback: (r) => {
                        if (r.message?.call_log) {
                            this._currentCallLog = r.message.call_log;
                            console.log('Arrowz: Incoming call log created:', this._currentCallLog);
                        }
                    }
                });
            }
            
            this.setupSessionEvents();
        },
        
        // Setup session events
        setupSessionEvents() {
            if (!this.session) return;
            
            console.log('Arrowz: Setting up session events');
            
            this.session.on('peerconnection', (e) => {
                console.log('Arrowz: Peerconnection event received');
                const pc = e.peerconnection;
                let iceFailureTimeout = null;
                let hostCandidateReceived = false;
                
                pc.onicecandidate = (event) => {
                    if (event.candidate) {
                        console.log('Arrowz: ICE candidate:', event.candidate.type, event.candidate.address);
                        if (event.candidate.type === 'host') {
                            hostCandidateReceived = true;
                        }
                    } else {
                        console.log('Arrowz: ICE gathering complete');
                        if (!hostCandidateReceived) {
                            console.warn('Arrowz: No host ICE candidates - may have connectivity issues');
                        }
                    }
                };
                
                pc.oniceconnectionstatechange = () => {
                    const state = pc.iceConnectionState;
                    console.log('Arrowz: ICE connection state:', state);
                    
                    switch (state) {
                        case 'connected':
                        case 'completed':
                            if (iceFailureTimeout) {
                                clearTimeout(iceFailureTimeout);
                                iceFailureTimeout = null;
                            }
                            console.log('Arrowz: ICE connection established successfully');
                            break;
                            
                        case 'failed':
                            console.error('Arrowz: ICE connection failed - terminating call');
                            frappe.show_alert({
                                message: __('Connection failed - please check your network'),
                                indicator: 'red'
                            }, 7);
                            this.endCall('ICE Connection Failed');
                            break;
                            
                        case 'disconnected':
                            console.warn('Arrowz: ICE disconnected - waiting 5s for recovery');
                            iceFailureTimeout = setTimeout(() => {
                                if (pc.iceConnectionState === 'disconnected') {
                                    console.error('Arrowz: ICE still disconnected after timeout');
                                    this.endCall('Connection Lost');
                                }
                            }, 5000);
                            break;
                            
                        case 'closed':
                            if (iceFailureTimeout) {
                                clearTimeout(iceFailureTimeout);
                            }
                            break;
                    }
                };
                
                pc.onicegatheringstatechange = () => {
                    console.log('Arrowz: ICE gathering state:', pc.iceGatheringState);
                };
                
                pc.onconnectionstatechange = () => {
                    const state = pc.connectionState;
                    console.log('Arrowz: Connection state:', state);
                    
                    if (state === 'failed') {
                        console.error('Arrowz: PeerConnection failed');
                        if (!this._callConfirmed) {
                            this.endCall('Connection Failed');
                        }
                    }
                };
                
                pc.ontrack = (event) => {
                    console.log('Arrowz: Track received:', event.track.kind);
                    if (event.streams && event.streams[0]) {
                        this.remoteStream = event.streams[0];
                        this.audioPlayer.srcObject = event.streams[0];
                        this.audioPlayer.play().catch(() => {});
                    }
                };
            });
            
            this.session.on('connecting', () => {
                console.log('Arrowz: Session connecting');
            });
            
            this.session.on('sending', (e) => {
                console.log('Arrowz: Session sending INVITE');
            });
            
            this.session.on('progress', () => {
                this.updateCallStatus(__('Ringing...'));
                this.updateNavbarStatus('ringing', this._currentCallee);
            });
            
            // 'accepted' fires when answer is sent (for incoming) or received (for outgoing)
            this.session.on('accepted', () => {
                console.log('Arrowz: Session accepted');
                this.stopRingtone();  // Stop ringtone immediately on accept
            });
            
            this.session.on('confirmed', () => {
                console.log('Arrowz: Session confirmed');
                this._callConfirmed = true;   // Mark call as fully connected
                this._isAnswering = false;    // No longer in answering phase
                this.stopRingtone();  // Also stop here as backup
                this.callStartTime = new Date();
                this.startCallTimer();
                this.updateCallStatus(__('Connected'));
                this.updateNavbarStatus('in-call', this._currentCallee);
                
                // Update call log as answered in database
                if (this._currentCallLog) {
                    frappe.call({
                        method: 'arrowz.api.webrtc.update_call_answered',
                        args: { call_log: this._currentCallLog },
                        async: true
                    }).catch(() => console.warn('Failed to update call answered status'));
                }
            });
            
            this.session.on('ended', () => {
                console.log('Arrowz: Session ended');
                // Update call log in database
                if (this._currentCallLog) {
                    frappe.call({
                        method: 'arrowz.api.webrtc.update_call_ended',
                        args: { call_log: this._currentCallLog, duration: this.getCallDuration() },
                        async: true
                    }).catch(() => {});
                }
                this.endCall();
            });
            
            // Handle call rejection by remote party
            this.session.on('rejected', (e) => {
                console.warn('Arrowz: Call rejected by remote:', e.cause);
                this._isAnswering = false;
                this._callConfirmed = false;
                this.stopRingtone();
                
                let reason = 'Call Rejected';
                if (e.cause === 'Busy Here' || e.message?.status_code === 486) {
                    reason = __('Busy');
                } else if (e.message?.status_code === 603) {
                    reason = __('Declined');
                }
                this.endCall(reason);
            });
            
            // Handle call cancellation (FreePBX sends CANCEL before answer)
            this.session.on('cancel', () => {
                console.warn('Arrowz: Call cancelled by remote (CANCEL received)');
                this._isAnswering = false;
                this._callConfirmed = false;
                this.stopRingtone();
                this.endCall(__('Call Cancelled'));
            });
            
            // Handle call redirect
            this.session.on('redirected', (e) => {
                console.warn('Arrowz: Call redirected to:', e.response?.getHeader('Contact'));
                this._isAnswering = false;
                this._callConfirmed = false;
                this.endCall(__('Call Redirected'));
            });
            
            // Handle SIP request timeout
            this.session.on('transporterror', () => {
                console.error('Arrowz: Transport error - WebSocket issue');
                this._isAnswering = false;
                this._callConfirmed = false;
                this.endCall(__('Connection Error'));
            });
            
            this.session.on('failed', (e) => {
                console.error('Arrowz: Call failed:', e.cause, e.message?.reason_phrase);
                this._isAnswering = false;    // Reset answering flag
                this._callConfirmed = false;  // Reset confirmed flag
                this.stopRingtone();  // Stop ringtone immediately on failure
                
                // Map common causes to user-friendly messages
                let errorMessage = e.cause;
                if (e.cause === 'SIP Failure Code') {
                    const statusCode = e.message?.status_code;
                    if (statusCode === 486) errorMessage = __('Busy');
                    else if (statusCode === 480) errorMessage = __('Temporarily Unavailable');
                    else if (statusCode === 487) errorMessage = __('Request Terminated');
                    else if (statusCode === 503) errorMessage = __('Service Unavailable');
                    else if (statusCode === 408) errorMessage = __('Request Timeout');
                    else errorMessage = e.message?.reason_phrase || e.cause;
                } else if (e.cause === 'RTP Timeout') {
                    errorMessage = __('Connection timeout - no audio');
                } else if (e.cause === 'User Denied Media Access') {
                    errorMessage = __('Microphone access denied');
                } else if (e.cause === 'WebRTC Error') {
                    errorMessage = __('WebRTC connection failed - check FreePBX RTCP-MUX');
                } else if (e.cause === 'Bad Media Description') {
                    errorMessage = __('Media negotiation failed - check FreePBX BUNDLE');
                } else if (e.cause === 'Canceled') {
                    errorMessage = __('Call Cancelled');
                } else if (e.cause === 'Request Timeout') {
                    errorMessage = __('No response from server');
                }
                
                // Update failed call in database
                if (this._currentCallLog) {
                    frappe.call({
                        method: 'arrowz.api.webrtc.update_call_failed',
                        args: { call_log: this._currentCallLog, reason: errorMessage },
                        async: true
                    }).catch(() => {});
                }
                
                this.endCall(errorMessage);
            });
            
            this.session.on('hold', () => {
                this.updateCallStatus(__('On Hold'));
                document.getElementById('sp-hold-btn')?.classList.add('active');
            });
            
            this.session.on('unhold', () => {
                this.updateCallStatus(__('Connected'));
                document.getElementById('sp-hold-btn')?.classList.remove('active');
            });
        },
        
        // Answer incoming call
        async answerCall() {
            if (!this.session) {
                console.error('Arrowz: No session to answer');
                return;
            }
            
            try {
                // Use pre-granted stream if available (instant answer), otherwise request now
                if (this._preGrantedStream) {
                    console.log('Arrowz: Using pre-granted microphone stream (instant answer)');
                    this.localStream = this._preGrantedStream;
                    this._preGrantedStream = null;  // Clear after use
                } else {
                    console.log('Arrowz: Getting microphone access...');
                    this.localStream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true
                        },
                        video: false
                    });
                }
                
                // Use single STUN server to reduce ICE gathering time
                // Build ICE servers - include TURN if available for NAT traversal
                let iceServers = [{ urls: 'stun:stun.l.google.com:19302' }];
                
                // Add configured ICE servers from backend
                if (this.config.ice_servers && this.config.ice_servers.length > 0) {
                    iceServers = this.config.ice_servers;
                }
                
                // Log ICE configuration for debugging
                console.log('Arrowz: Using ICE servers:', JSON.stringify(iceServers));
                
                const options = {
                    mediaConstraints: { audio: true, video: false },
                    mediaStream: this.localStream,
                    pcConfig: {
                        iceServers: iceServers,
                        rtcpMuxPolicy: 'negotiate',
                        bundlePolicy: 'balanced',  // Use 'balanced' - FreePBX may not support BUNDLE
                        iceCandidatePoolSize: 0    // Disable pre-gathering for faster call setup
                    },
                    // Important: Use Trickle ICE - send candidates as they are discovered
                    rtcAnswerConstraints: {
                        offerToReceiveAudio: true,
                        offerToReceiveVideo: false
                    }
                };
                
                console.log('Arrowz: Answering call with options:', JSON.stringify(options.pcConfig));
                
                // Listen for the peerconnection:setremotedescriptionfailed event
                this.session.on('peerconnection:setremotedescriptionfailed', (e) => {
                    console.error('Arrowz: setRemoteDescription failed:', e.error);
                    if (e.error?.message?.includes('RTCP-MUX')) {
                        frappe.show_alert({
                            message: __('Call failed: FreePBX needs RTCP-MUX enabled in PJSIP settings'),
                            indicator: 'red'
                        }, 10);
                    }
                });
                
                // Mark that we're answering (prevents accidental hangup before confirmed)
                this._isAnswering = true;
                
                // Answer the call with proper error handling
                try {
                    this.session.answer(options);
                    console.log('Arrowz: session.answer() called successfully');
                } catch (answerError) {
                    console.error('Arrowz: session.answer() threw error:', answerError);
                    this._isAnswering = false;
                    frappe.show_alert({
                        message: __('Failed to answer call: ') + answerError.message,
                        indicator: 'red'
                    }, 7);
                    return;
                }
                
                this.stopRingtone();
                this.showActiveCallUI(this._currentCallee);
                
            } catch (error) {
                console.error('Answer call error:', error);
                let errorMessage = __('Failed to access microphone');
                
                if (error.name === 'NotAllowedError') {
                    errorMessage = __('Microphone permission denied');
                } else if (error.name === 'NotFoundError') {
                    errorMessage = __('No microphone found');
                } else if (error.message) {
                    errorMessage = error.message;
                }
                
                frappe.show_alert({
                    message: errorMessage,
                    indicator: 'red'
                }, 7);
                
                // Don't close the call UI, let the user try again or reject
            }
        },
        
        // Reject call
        rejectCall() {
            this.stopRingtone();
            
            // Clean up pre-granted stream if user rejects the call
            if (this._preGrantedStream) {
                console.log('Arrowz: Cleaning up pre-granted stream after reject');
                this._preGrantedStream.getTracks().forEach(track => track.stop());
                this._preGrantedStream = null;
            }
            
            if (this.session) {
                try {
                    this.session.terminate({ status_code: 603, reason_phrase: 'Decline' });
                } catch (e) {}
                this.session = null;
            }
            this.closeDropdown();
            this.updateNavbarStatus('registered', this.config?.extension || '---');
        },
        
        // Hangup call
        hangup() {
            // Don't hangup if we're still in the process of answering
            if (this._isAnswering && !this._callConfirmed) {
                console.log('Arrowz: Ignoring hangup - call is being answered');
                return;
            }
            
            if (this.session) {
                try {
                    this.session.terminate();
                } catch (e) {
                    console.error('Arrowz: Error terminating session:', e);
                    this.endCall();
                }
            } else {
                this.endCall();
            }
        },
        
        // End call cleanup
        endCall(reason) {
            this.stopCallTimer();
            this.stopRingtone();
            
            // Reset call state flags
            this._isAnswering = false;
            this._callConfirmed = false;
            
            // Clean up pre-granted stream if it wasn't used
            if (this._preGrantedStream) {
                console.log('Arrowz: Cleaning up unused pre-granted stream');
                this._preGrantedStream.getTracks().forEach(track => track.stop());
                this._preGrantedStream = null;
            }
            
            if (this.localStream) {
                this.localStream.getTracks().forEach(t => t.stop());
                this.localStream = null;
            }
            
            this.session = null;
            this.callStartTime = null;
            this._currentCallee = null;
            this._currentCallLog = null;  // Reset call log reference
            
            this.updateNavbarStatus('registered', this.config?.extension || '---');
            
            if (this.isDropdownOpen) {
                this.showDialerUI();
            }
            
            if (reason) {
                frappe.show_alert({
                    message: __('Call ended: {0}', [reason]),
                    indicator: 'orange'
                }, 3);
            }
        },
        
        // Toggle mute
        toggleMute() {
            if (!this.session) return;
            
            const muteBtn = document.getElementById('sp-mute-btn');
            if (!muteBtn) return;
            
            const mutedIcon = muteBtn.querySelector('.muted');
            const unmutedIcon = muteBtn.querySelector('.unmuted');
            
            if (this.session.isMuted().audio) {
                this.session.unmute({ audio: true });
                muteBtn.classList.remove('muted');
                if (mutedIcon) mutedIcon.style.display = 'none';
                if (unmutedIcon) unmutedIcon.style.display = 'block';
            } else {
                this.session.mute({ audio: true });
                muteBtn.classList.add('muted');
                if (mutedIcon) mutedIcon.style.display = 'block';
                if (unmutedIcon) unmutedIcon.style.display = 'none';
            }
        },
        
        // Toggle hold
        toggleHold() {
            if (!this.session) return;
            
            if (this.session.isOnHold().local) {
                this.session.unhold();
            } else {
                this.session.hold();
            }
        },
        
        // Toggle keypad
        toggleKeypad() {
            const overlay = document.getElementById('sp-keypad-overlay');
            if (overlay) {
                overlay.style.display = overlay.style.display === 'none' ? 'block' : 'none';
            }
        },
        
        // Send DTMF
        sendDTMF(digit) {
            if (this.session) {
                this.session.sendDTMF(digit);
            }
        },
        
        // Transfer call
        transfer() {
            if (!this.session) return;
            
            frappe.prompt({
                fieldtype: 'Data',
                fieldname: 'target',
                label: __('Transfer to'),
                reqd: 1
            }, (values) => {
                if (values.target) {
                    this.session.refer(values.target);
                    frappe.show_alert({
                        message: __('Call transferred'),
                        indicator: 'green'
                    });
                }
            }, __('Transfer Call'));
        },
        
        // Update navbar status
        updateNavbarStatus(status, text) {
            const dot = document.querySelector('.arrowz-sp-trigger .sp-status-dot');
            const statusText = document.querySelector('.arrowz-sp-trigger .sp-status-text');
            const timer = document.querySelector('.arrowz-sp-trigger .sp-call-timer');
            const trigger = document.querySelector('.arrowz-sp-trigger');
            
            if (dot) {
                dot.className = 'sp-status-dot ' + status;
            }
            
            if (statusText && timer) {
                if (['calling', 'ringing', 'in-call', 'incoming'].includes(status)) {
                    statusText.style.display = 'none';
                    timer.style.display = 'inline';
                } else {
                    statusText.textContent = text || '';
                    statusText.style.display = 'inline';
                    timer.style.display = 'none';
                }
            }
            
            if (trigger) {
                trigger.setAttribute('data-status', status);
            }
        },
        
        // Update call status text
        updateCallStatus(text) {
            const el = document.getElementById('sp-call-status');
            if (el) el.textContent = text;
        },
        
        // Update navbar badge
        updateNavbarBadge() {
            const badge = document.querySelector('.arrowz-sp-trigger .sp-badge');
            const count = this.pendingSMS.length + this.missedCalls;
            
            if (badge) {
                if (count > 0) {
                    badge.textContent = count > 99 ? '99+' : count;
                    badge.style.display = 'block';
                } else {
                    badge.style.display = 'none';
                }
            }
        },
        
        // Start call timer
        startCallTimer() {
            const timerEl = document.getElementById('sp-call-duration');
            const navTimer = document.querySelector('.sp-call-timer');
            
            this.callTimer = setInterval(() => {
                if (this.callStartTime) {
                    const elapsed = Math.floor((new Date() - this.callStartTime) / 1000);
                    const mins = Math.floor(elapsed / 60);
                    const secs = elapsed % 60;
                    const formatted = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
                    
                    if (timerEl) timerEl.textContent = formatted;
                    if (navTimer) navTimer.textContent = formatted;
                }
            }, 1000);
        },
        
        // Stop call timer
        stopCallTimer() {
            if (this.callTimer) {
                clearInterval(this.callTimer);
                this.callTimer = null;
            }
        },
        
        // Get call duration in seconds
        getCallDuration() {
            if (!this.callStartTime) return 0;
            return Math.floor((new Date() - this.callStartTime) / 1000);
        },
        
        // Play ringtone
        playRingtone() {
            try {
                this.ringtone.currentTime = 0;
                this.ringtone.play().catch(() => {
                    frappe.show_alert({
                        message: __('📞 Incoming call!'),
                        indicator: 'green'
                    }, 10);
                });
            } catch (e) {}
        },
        
        // Stop ringtone
        stopRingtone() {
            try {
                this.ringtone.pause();
                this.ringtone.currentTime = 0;
            } catch (e) {}
        },
        
        // Show browser notification
        showBrowserNotification(caller) {
            if ('Notification' in window && Notification.permission === 'granted') {
                const notification = new Notification(__('Incoming Call'), {
                    body: caller,
                    icon: '/assets/frappe/images/frappe-favicon.svg',
                    requireInteraction: true,
                    tag: 'incoming-call'
                });
                
                notification.onclick = () => {
                    window.focus();
                    notification.close();
                };
                
                this.currentNotification = notification;
            }
        },
        
        // Show notification
        showNotification(type, data) {
            if (type === 'sms') {
                frappe.show_alert({
                    message: __('New SMS from {0}', [data.from || __('Unknown')]),
                    indicator: 'blue'
                }, 5);
            }
        },
        
        // Show call history
        showHistory() {
            frappe.set_route('List', 'AZ Call Log');
            this.closeDropdown();
        },
        
        // Show settings
        showSettings() {
            frappe.set_route('Form', 'AZ Extension', this.activeExtension);
            this.closeDropdown();
        },
        
        // Public show method
        show() {
            this.openDropdown();
        },
        
        // Add styles
        addStyles() {
            if (document.getElementById('arrowz-softphone-v2-styles')) return;
            
            const style = document.createElement('style');
            style.id = 'arrowz-softphone-v2-styles';
            style.textContent = `
                /* Navbar Widget */
                .arrowz-softphone-nav {
                    position: relative;
                    margin-right: 8px;
                }
                
                .arrowz-sp-trigger {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    padding: 6px 12px;
                    border-radius: 8px;
                    cursor: pointer;
                    background: var(--fg-color);
                    transition: all 0.2s;
                    user-select: none;
                }
                
                .arrowz-sp-trigger:hover {
                    background: var(--bg-dark-gray);
                }
                
                .arrowz-sp-trigger[data-status="in-call"],
                .arrowz-sp-trigger[data-status="calling"],
                .arrowz-sp-trigger[data-status="ringing"] {
                    background: rgba(76, 175, 80, 0.15);
                    animation: pulse-bg 2s infinite;
                }
                
                .arrowz-sp-trigger[data-status="incoming"] {
                    background: rgba(33, 150, 243, 0.15);
                    animation: shake-trigger 0.5s infinite;
                }
                
                @keyframes pulse-bg {
                    0%, 100% { background: rgba(76, 175, 80, 0.15); }
                    50% { background: rgba(76, 175, 80, 0.25); }
                }
                
                @keyframes shake-trigger {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-2px); }
                    75% { transform: translateX(2px); }
                }
                
                .sp-icon-wrapper {
                    position: relative;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .sp-icon {
                    width: 18px;
                    height: 18px;
                    color: var(--text-color);
                }
                
                .sp-status-dot {
                    position: absolute;
                    bottom: -2px;
                    right: -2px;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    border: 2px solid var(--fg-color);
                    background: #9e9e9e;
                    transition: background 0.3s;
                }
                
                .sp-status-dot.registered { background: #4CAF50; }
                .sp-status-dot.connecting { background: #ff9800; animation: blink 1s infinite; }
                .sp-status-dot.disconnected, .sp-status-dot.failed { background: #f44336; }
                .sp-status-dot.no-config { background: #2196F3; }
                .sp-status-dot.calling, .sp-status-dot.ringing { background: #4CAF50; animation: pulse-dot 1s infinite; }
                .sp-status-dot.in-call { background: #4CAF50; }
                .sp-status-dot.incoming { background: #2196F3; animation: pulse-dot 0.5s infinite; }
                
                @keyframes blink {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.4; }
                }
                
                @keyframes pulse-dot {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.3); }
                }
                
                .sp-badge {
                    position: absolute;
                    top: -4px;
                    right: -4px;
                    background: #f44336;
                    color: white;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 5px;
                    border-radius: 10px;
                    min-width: 16px;
                    text-align: center;
                }
                
                .sp-status-text {
                    font-size: 12px;
                    font-weight: 500;
                    color: var(--text-color);
                }
                
                .sp-call-timer {
                    font-size: 12px;
                    font-weight: 600;
                    color: #4CAF50;
                    font-family: monospace;
                }
                
                /* Dropdown */
                .arrowz-sp-dropdown {
                    position: absolute;
                    top: 100%;
                    right: 0;
                    width: 320px;
                    max-height: 500px;
                    background: var(--card-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.15);
                    opacity: 0;
                    visibility: hidden;
                    transform: translateY(-10px);
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    z-index: 1050;
                    overflow: visible;
                    display: flex;
                    flex-direction: column;
                }
                
                .arrowz-sp-dropdown.open {
                    opacity: 1;
                    visibility: visible;
                    transform: translateY(0);
                }
                
                /* Mobile Modal */
                .arrowz-sp-dropdown.mobile-modal {
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    right: auto;
                    transform: translate(-50%, -50%);
                    width: 90%;
                    max-width: 350px;
                    max-height: 90vh;
                }
                
                .arrowz-sp-dropdown.mobile-modal.open {
                    transform: translate(-50%, -50%);
                }
                
                body.arrowz-modal-open::before {
                    content: '';
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0,0,0,0.5);
                    z-index: 1040;
                }
                
                /* Header */
                .sp-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px 16px;
                    background: linear-gradient(135deg, #5e35b1, #7c4dff);
                    color: white;
                    flex-shrink: 0;
                    border-radius: 12px 12px 0 0;
                }
                
                /* Content wrapper - scrollable */
                .sp-content {
                    flex: 1;
                    overflow-y: auto;
                    max-height: calc(500px - 120px);
                }
                
                .sp-header-info {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .sp-status-indicator {
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    background: #f44336;
                }
                
                .sp-status-indicator.online { background: #4CAF50; }
                
                .sp-ext-number {
                    font-size: 16px;
                    font-weight: 600;
                }
                
                .sp-status-label {
                    font-size: 12px;
                    opacity: 0.8;
                }
                
                .sp-close-btn {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 24px;
                    cursor: pointer;
                    padding: 0;
                    line-height: 1;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                }
                
                .sp-close-btn:hover { opacity: 1; }
                
                /* Extension Selector */
                .sp-extension-selector {
                    padding: 10px 16px;
                    background: var(--bg-color);
                    border-bottom: 1px solid var(--border-color);
                }
                
                .sp-ext-label {
                    font-size: 11px;
                    color: var(--text-muted);
                    margin-bottom: 6px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                
                .sp-ext-buttons {
                    display: flex;
                    gap: 6px;
                    flex-wrap: wrap;
                }
                
                .sp-ext-btn {
                    padding: 6px 12px;
                    border: 1px solid var(--border-color);
                    border-radius: 20px;
                    background: var(--fg-color);
                    font-size: 12px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .sp-ext-btn:hover {
                    border-color: #5e35b1;
                    color: #5e35b1;
                }
                
                .sp-ext-btn.active {
                    background: #5e35b1;
                    border-color: #5e35b1;
                    color: white;
                }
                
                /* Search */
                .sp-search-container {
                    padding: 12px 16px;
                    position: relative;
                }
                
                .sp-search-input {
                    width: 100%;
                    padding: 10px 14px;
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    font-size: 14px;
                    background: var(--fg-color);
                    transition: border-color 0.2s;
                }
                
                .sp-search-input:focus {
                    outline: none;
                    border-color: #5e35b1;
                }
                
                .sp-search-results {
                    position: absolute;
                    top: 100%;
                    left: 16px;
                    right: 16px;
                    background: var(--card-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    max-height: 200px;
                    overflow-y: auto;
                    z-index: 10;
                    display: none;
                }
                
                .sp-contact-item {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 10px 12px;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                
                .sp-contact-item:hover {
                    background: var(--bg-color);
                }
                
                .sp-contact-avatar {
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    background: #5e35b1;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 600;
                    font-size: 14px;
                }
                
                .sp-contact-details {
                    flex: 1;
                    min-width: 0;
                }
                
                .sp-contact-name {
                    font-weight: 500;
                    font-size: 13px;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                
                .sp-contact-phone {
                    font-size: 12px;
                    color: var(--text-muted);
                }
                
                .sp-contact-type {
                    font-size: 10px;
                    color: #5e35b1;
                    text-transform: uppercase;
                }
                
                .sp-no-results {
                    padding: 16px;
                    text-align: center;
                    color: var(--text-muted);
                    font-size: 13px;
                }
                
                /* Dial Display */
                .sp-dial-display {
                    display: flex;
                    padding: 0 16px 12px;
                    gap: 8px;
                }
                
                .sp-dial-input {
                    flex: 1;
                    padding: 12px;
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    font-size: 20px;
                    text-align: center;
                    letter-spacing: 2px;
                    font-family: monospace;
                    background: var(--fg-color);
                }
                
                .sp-dial-input:focus {
                    outline: none;
                    border-color: #5e35b1;
                }
                
                .sp-backspace {
                    padding: 12px 16px;
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    background: var(--fg-color);
                    font-size: 18px;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .sp-backspace:hover {
                    background: var(--bg-color);
                }
                
                /* Dialpad */
                .sp-dialpad {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 8px;
                    padding: 0 16px 16px;
                }
                
                .sp-key {
                    aspect-ratio: 1.3;
                    border: none;
                    border-radius: 50%;
                    background: var(--bg-color);
                    font-size: 22px;
                    font-weight: 500;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.15s;
                }
                
                .sp-key:hover {
                    background: var(--border-color);
                }
                
                .sp-key:active {
                    transform: scale(0.95);
                    background: #5e35b1;
                    color: white;
                }
                
                .sp-key span {
                    font-size: 9px;
                    color: var(--text-muted);
                    letter-spacing: 1px;
                }
                
                .sp-key:active span {
                    color: rgba(255,255,255,0.7);
                }
                
                /* Compact dialpad for in-call */
                .sp-dialpad.compact {
                    padding: 10px;
                }
                
                .sp-dialpad.compact .sp-key {
                    aspect-ratio: 1.5;
                    font-size: 18px;
                    border-radius: 8px;
                }
                
                /* Actions */
                .sp-actions {
                    display: flex;
                    justify-content: center;
                    padding: 0 16px 16px;
                }
                
                .sp-call-btn {
                    width: 64px;
                    height: 64px;
                    border-radius: 50%;
                    border: none;
                    background: #4CAF50;
                    color: white;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }
                
                .sp-call-btn:hover {
                    background: #43a047;
                    transform: scale(1.05);
                }
                
                .sp-call-btn.disabled {
                    background: #9e9e9e;
                    cursor: not-allowed;
                }
                
                .sp-call-btn svg {
                    width: 28px;
                    height: 28px;
                }
                
                /* Footer */
                .sp-footer {
                    display: flex;
                    border-top: 1px solid var(--border-color);
                    background: var(--bg-color);
                    flex-shrink: 0;
                    border-radius: 0 0 12px 12px;
                }
                
                .sp-footer-btn {
                    flex: 1;
                    padding: 12px;
                    border: none;
                    background: none;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 6px;
                    font-size: 12px;
                    color: var(--text-muted);
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .sp-footer-btn:hover {
                    background: var(--fg-color);
                    color: #5e35b1;
                }
                
                .sp-footer-btn svg {
                    width: 16px;
                    height: 16px;
                }
                
                .sp-footer-btn:first-child {
                    border-right: 1px solid var(--border-color);
                }
                
                /* Call Screen */
                .sp-call-screen {
                    padding: 20px;
                    text-align: center;
                }
                
                .sp-call-header {
                    margin-bottom: 20px;
                }
                
                .sp-call-avatar {
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #5e35b1, #7c4dff);
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 16px;
                }
                
                .sp-call-avatar svg {
                    width: 40px;
                    height: 40px;
                }
                
                .sp-callee-number {
                    font-size: 22px;
                    font-weight: 600;
                }
                
                #sp-call-status {
                    font-size: 14px;
                    color: var(--text-muted);
                    margin-top: 4px;
                }
                
                #sp-call-duration {
                    font-size: 28px;
                    font-weight: 300;
                    font-family: monospace;
                    color: #4CAF50;
                    margin-top: 8px;
                }
                
                .sp-call-actions {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 12px;
                    margin-bottom: 20px;
                }
                
                .sp-call-action {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 6px;
                    padding: 12px 8px;
                    border: none;
                    border-radius: 12px;
                    background: var(--bg-color);
                    cursor: pointer;
                    transition: all 0.2s;
                }
                
                .sp-call-action:hover {
                    background: var(--border-color);
                }
                
                .sp-call-action.active {
                    background: #f44336;
                    color: white;
                }
                
                .sp-call-action svg {
                    width: 24px;
                    height: 24px;
                }
                
                .sp-call-action span {
                    font-size: 11px;
                }
                
                .sp-keypad-overlay {
                    margin-top: 10px;
                    padding-top: 10px;
                    border-top: 1px solid var(--border-color);
                }
                
                .sp-hangup-section {
                    margin-top: 10px;
                }
                
                .sp-hangup-btn {
                    width: 64px;
                    height: 64px;
                    border-radius: 50%;
                    border: none;
                    background: #f44336;
                    color: white;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }
                
                .sp-hangup-btn:hover {
                    background: #d32f2f;
                    transform: scale(1.05);
                }
                
                .sp-hangup-btn svg {
                    width: 28px;
                    height: 28px;
                    transform: rotate(135deg);
                }
                
                /* Incoming Call Screen */
                .sp-incoming-screen {
                    padding: 30px 20px;
                    text-align: center;
                }
                
                .sp-incoming-animation {
                    position: relative;
                    width: 100px;
                    height: 100px;
                    margin: 0 auto 20px;
                }
                
                .sp-pulse-ring {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    border-radius: 50%;
                    border: 3px solid #2196F3;
                    animation: pulse-ring 1.5s infinite;
                }
                
                .sp-pulse-ring.delay {
                    animation-delay: 0.5s;
                }
                
                @keyframes pulse-ring {
                    0% { transform: scale(0.8); opacity: 1; }
                    100% { transform: scale(1.5); opacity: 0; }
                }
                
                .sp-caller-avatar {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    width: 70px;
                    height: 70px;
                    border-radius: 50%;
                    background: #2196F3;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                
                .sp-caller-avatar svg {
                    width: 35px;
                    height: 35px;
                }
                
                .sp-caller-id {
                    font-size: 24px;
                    font-weight: 600;
                    margin-bottom: 4px;
                }
                
                .sp-incoming-label {
                    font-size: 14px;
                    color: var(--text-muted);
                    margin-bottom: 30px;
                }
                
                .sp-incoming-actions {
                    display: flex;
                    justify-content: center;
                    gap: 40px;
                }
                
                .sp-reject-btn, .sp-answer-btn {
                    width: 64px;
                    height: 64px;
                    border-radius: 50%;
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }
                
                .sp-reject-btn {
                    background: #f44336;
                    color: white;
                }
                
                .sp-reject-btn:hover {
                    background: #d32f2f;
                    transform: scale(1.05);
                }
                
                .sp-answer-btn {
                    background: #4CAF50;
                    color: white;
                    animation: pulse-answer 1s infinite;
                }
                
                .sp-answer-btn:hover {
                    background: #43a047;
                }
                
                @keyframes pulse-answer {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.08); }
                }
                
                .sp-reject-btn svg, .sp-answer-btn svg {
                    width: 28px;
                    height: 28px;
                }
                
                .sp-reject-btn svg {
                    transform: rotate(135deg);
                }
                
                /* Mobile Responsive */
                @media (max-width: 768px) {
                    .sp-status-text {
                        display: none;
                    }
                    
                    .arrowz-sp-dropdown {
                        width: calc(100vw - 40px);
                        max-height: calc(100vh - 100px);
                    }
                    
                    .sp-dialpad .sp-key {
                        aspect-ratio: 1.2;
                        font-size: 20px;
                    }
                    
                    .sp-call-actions {
                        grid-template-columns: repeat(2, 1fr);
                    }
                }
            `;
            
            document.head.appendChild(style);
        }
    };
    
    // Initialize on page load
    $(document).ready(function() {
        if (frappe.session.user !== 'Guest') {
            setTimeout(() => {
                arrowz.softphone.init();
            }, 1500);
        }
    });
    
})();
