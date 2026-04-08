// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Arrowz Softphone V2 - Professional Navbar Integration
 * Features:
 * - Dropdown on desktop, modal on mobile
 * - Multi-extension support with quick switcher
 * - Real-time status indicators (SMS, Calls, Line status)
 * - Contact search across all linked DocTypes
 * - Responsive design
 *
 * BUILD: 2024-02-24-v3-openrelay-turn
 */

(function() {
    'use strict';

    // Version check - helps confirm browser has latest code
    console.log('%c[Arrowz Softphone] BUILD: 2024-02-24-v3-openrelay-turn', 'color: #00ff00; font-weight: bold;');

    // Arrowz namespace
    window.arrowz = window.arrowz || {};

    // ========== Cross-Tab Leader Election ==========
    // Ensures only ONE tab registers with Asterisk at a time.
    // Uses BroadcastChannel + localStorage for leader election.
    const TAB_LEADER_KEY = 'arrowz_softphone_leader';
    const TAB_HEARTBEAT_KEY = 'arrowz_softphone_heartbeat';
    const TAB_ID = Math.random().toString(36).substring(2, 10) + '_' + Date.now();
    const HEARTBEAT_INTERVAL = 2000; // ms
    const LEADER_TIMEOUT = 6000; // ms - if no heartbeat for this long, leader is dead

    let _tabChannel = null;
    let _heartbeatTimer = null;
    let _isLeader = false;

    function _initTabChannel() {
        try {
            _tabChannel = new BroadcastChannel('arrowz_softphone');
            _tabChannel.onmessage = function(ev) {
                if (ev.data.type === 'leader_claim' && ev.data.tabId !== TAB_ID) {
                    // Another tab claimed leadership
                    if (_isLeader) {
                        // We were leader, yield if their claim is newer
                        console.log('Arrowz Tab: Another tab claimed leadership, yielding');
                        _isLeader = false;
                        _stopHeartbeat();
                        // Stop our UA registration
                        if (arrowz.softphone.ua) {
                            try {
                                arrowz.softphone.ua.unregister({ all: true });
                                arrowz.softphone.ua.stop();
                            } catch(e) {}
                            arrowz.softphone.ua = null;
                            arrowz.softphone.registered = false;
                            arrowz.softphone.updateNavbarStatus('follower', __('Standby'));
                        }
                    }
                } else if (ev.data.type === 'leader_release') {
                    // Leader tab is closing, try to become leader
                    console.log('Arrowz Tab: Leader released, attempting to claim');
                    setTimeout(() => _tryBecomeLeader(), Math.random() * 500);
                } else if (ev.data.type === 'call_event' && !_isLeader) {
                    // Forward call events to non-leader tabs for UI updates
                    if (ev.data.event === 'incoming') {
                        arrowz.softphone.showNotification('call', ev.data.data);
                    }
                }
            };
        } catch (e) {
            // BroadcastChannel not supported, act as leader always
            console.warn('Arrowz Tab: BroadcastChannel not supported, assuming leader');
            _isLeader = true;
        }
    }

    function _tryBecomeLeader() {
        const now = Date.now();
        const stored = localStorage.getItem(TAB_LEADER_KEY);
        const heartbeat = parseInt(localStorage.getItem(TAB_HEARTBEAT_KEY) || '0');

        // Become leader if: no leader, or leader heartbeat expired
        if (!stored || stored === TAB_ID || (now - heartbeat > LEADER_TIMEOUT)) {
            localStorage.setItem(TAB_LEADER_KEY, TAB_ID);
            localStorage.setItem(TAB_HEARTBEAT_KEY, String(now));

            // Verify we won (check again after a small delay for race conditions)
            setTimeout(() => {
                if (localStorage.getItem(TAB_LEADER_KEY) === TAB_ID) {
                    _isLeader = true;
                    _startHeartbeat();
                    console.log('Arrowz Tab: Became leader (tab=' + TAB_ID + ')');
                    if (_tabChannel) {
                        _tabChannel.postMessage({ type: 'leader_claim', tabId: TAB_ID });
                    }
                    // If softphone is initialized but UA not started, start it now
                    if (arrowz.softphone.initialized && !arrowz.softphone.ua && arrowz.softphone.config) {
                        arrowz.softphone.setupJsSIP();
                    }
                }
            }, 50 + Math.random() * 100);
        }
    }

    function _startHeartbeat() {
        _stopHeartbeat();
        _heartbeatTimer = setInterval(() => {
            if (_isLeader) {
                localStorage.setItem(TAB_HEARTBEAT_KEY, String(Date.now()));
            }
        }, HEARTBEAT_INTERVAL);
    }

    function _stopHeartbeat() {
        if (_heartbeatTimer) {
            clearInterval(_heartbeatTimer);
            _heartbeatTimer = null;
        }
    }

    function _releaseLeadership() {
        if (_isLeader) {
            _isLeader = false;
            _stopHeartbeat();
            localStorage.removeItem(TAB_LEADER_KEY);
            localStorage.removeItem(TAB_HEARTBEAT_KEY);
            if (_tabChannel) {
                try {
                    _tabChannel.postMessage({ type: 'leader_release', tabId: TAB_ID });
                } catch(e) {}
            }
        }
    }

    // Initialize leader election immediately
    _initTabChannel();
    _tryBecomeLeader();
    // ========== End Cross-Tab Leader Election ==========

    // Softphone V2
    arrowz.softphone = {
        initialized: false,
        registered: false,
        ua: null,  // JsSIP User Agent
        sessions: [],  // Array of active call sessions (multi-line support)
        session: null,  // Current/primary call session (backwards compatibility)
        activeLineIndex: 0,  // Currently selected line index
        maxLines: 4,  // Maximum concurrent lines
        config: null,
        allExtensions: [],  // All user's extensions
        activeExtension: null,  // Current active extension
        audioPlayer: null,
        localStream: null,
        remoteStream: null,
        callTimer: null,
        callStartTime: null,
        callStartTimes: {},  // Track start times per session
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

                // Register cleanup on page unload to prevent stale registrations
                this.setupUnloadCleanup();

                this.initialized = true;

                // If not leader, don't start JsSIP (loadExtensions calls setupJsSIP)
                // The leader election will trigger setupJsSIP when this tab becomes leader
                if (!_isLeader) {
                    console.log('Arrowz Softphone V2 initialized (standby mode - another tab is leader)');
                    this.updateNavbarStatus('follower', __('Standby'));
                    // Stop the UA that loadExtensions may have started
                    if (this.ua) {
                        try {
                            this.ua.unregister({ all: true });
                            this.ua.stop();
                        } catch(e) {}
                        this.ua = null;
                    }
                } else {
                    console.log('Arrowz Softphone V2 initialized (leader)');
                }

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

                // Resolve PBX public IP for SDP rewriting (Docker NAT workaround)
                // Extract host from websocket URL or SIP domain
                if (r.message.sip_domain) {
                    this._pbxHost = r.message.sip_domain;
                }
                // Store public IP if provided, or use the SIP domain
                if (r.message.pbx_public_ip) {
                    this._pbxPublicIP = r.message.pbx_public_ip;
                }

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

            // Only the leader tab should register with Asterisk
            if (!_isLeader) {
                console.log('Arrowz: Not leader tab, skipping JsSIP setup');
                return;
            }

            // Stop any existing UA before creating a new one
            if (this.ua) {
                try {
                    this.ua.unregister({ all: true });
                    this.ua.stop();
                } catch(e) {}
                this.ua = null;
            }

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

            this.ua.on('disconnected', (e) => {
                if (!checkCurrentUA()) {
                    console.log('Arrowz: Ignoring disconnected event from old UA');
                    return;
                }
                console.log('Arrowz: WebSocket disconnected', e);
                this.registered = false;
                this.updateNavbarStatus('disconnected', __('Offline'));

                // Track disconnection count for SSL certificate warning
                this._disconnectCount = (this._disconnectCount || 0) + 1;
                if (this._disconnectCount >= 3 && !this._sslWarningShown) {
                    this._sslWarningShown = true;
                    const wsUrl = this.config?.websocket_servers?.[0];
                    if (wsUrl) {
                        const pbxHost = wsUrl.replace('wss://', 'https://').replace('/ws', '');
                        frappe.msgprint({
                            title: __('WebSocket Connection Failed'),
                            message: __('Unable to connect to PBX. This may be caused by a self-signed SSL certificate.<br><br>To fix this:<br>1. <a href="{0}" target="_blank">Click here to open the PBX URL</a><br>2. Accept the certificate warning in your browser<br>3. Refresh this page', [pbxHost]),
                            indicator: 'orange'
                        });
                    }
                }
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

        // Cleanup on page unload to prevent stale SIP registrations
        setupUnloadCleanup() {
            window.addEventListener('beforeunload', () => {
                // Release leadership so another tab can take over
                _releaseLeadership();

                if (this.ua) {
                    try {
                        this.ua.unregister({ all: true });
                        this.ua.stop();
                    } catch (e) {
                        // Ignore errors during cleanup
                    }
                }
                // Close any active streams
                if (this.localStream) {
                    this.localStream.getTracks().forEach(t => t.stop());
                }
                if (this._preGrantedStream) {
                    this._preGrantedStream.getTracks().forEach(t => t.stop());
                }
            });
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

            // Priority 1: Theme topbar (.topbar-right from tavira/flux theme)
            let navbarContainer = document.querySelector('.topbar-right');
            let insertMode = 'topbar';

            // Priority 2: Frappe v16 desktop navbar
            if (!navbarContainer) {
                navbarContainer = document.querySelector('.navbar-container .flex');
                insertMode = 'desktop';
            }

            // Priority 3: Legacy navbar selectors for older Frappe versions
            if (!navbarContainer) {
                navbarContainer = document.querySelector('.navbar .navbar-collapse .navbar-nav') ||
                                  document.querySelector('.navbar-right') ||
                                  document.querySelector('.navbar-nav') ||
                                  document.querySelector('#navbar-user')?.parentElement;
                insertMode = 'legacy';
            }

            if (!navbarContainer) {
                // Retry with a limit to prevent infinite loops (e.g., on setup wizard page)
                this._navRetryCount = (this._navRetryCount || 0) + 1;
                if (this._navRetryCount < 10) {
                    setTimeout(() => this.renderNavbarWidget(), 500);
                }
                return;
            }
            this._navRetryCount = 0;

            // Create widget
            let widget = document.createElement('div');
            widget.id = 'arrowz-softphone-widget';
            widget.className = 'arrowz-softphone-desktop';
            widget.innerHTML = `
                <div class="arrowz-sp-trigger" onclick="arrowz.softphone.toggleDropdown()">
                    <div class="sp-icon-wrapper">
                        <img class="sp-icon arrowz-logo-animated" src="/assets/arrowz/images/arrowz-icon-animated.svg" alt="Arrowz" />
                        <span class="sp-status-dot"></span>
                    </div>
                    <span class="sp-badge" style="display: none;"></span>
                    <span class="sp-call-timer" style="display: none;">00:00</span>
                </div>
                <div class="arrowz-sp-dropdown" id="arrowz-sp-dropdown">
                    <!-- Content loaded dynamically -->
                </div>
            `;

            if (insertMode === 'topbar') {
                // Insert as first child of .topbar-right (before avatar/notifications)
                navbarContainer.insertBefore(widget, navbarContainer.firstChild);

                // Move dropdown to document.body to escape topbar's
                // overflow:hidden + backdrop-filter containing block
                const dropdown = widget.querySelector('#arrowz-sp-dropdown');
                if (dropdown) {
                    dropdown.remove();
                    dropdown.classList.add('arrowz-sp-dropdown-portal');
                    document.body.appendChild(dropdown);
                }
            } else if (insertMode === 'desktop') {
                // Insert before desktop-notifications
                const notifications = navbarContainer.querySelector('.desktop-notifications');
                if (notifications) {
                    navbarContainer.insertBefore(widget, notifications);
                } else {
                    navbarContainer.insertBefore(widget, navbarContainer.firstChild);
                }
            } else {
                navbarContainer.insertBefore(widget, navbarContainer.firstChild);
            }

            // Add styles
            this.addStyles();

            // Close dropdown on outside click
            document.addEventListener('click', (e) => {
                if (!e.target.closest('#arrowz-softphone-widget') && !e.target.closest('#arrowz-sp-dropdown')) {
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
            if (this._isIncomingRinging && this.session) {
                // Incoming call ringing - show answer/reject UI
                const caller = this._currentCallee || this.session.remote_identity?.display_name || this.session.remote_identity?.uri?.user || __('Unknown');
                this.showIncomingCallUI(caller);
            } else if (this.session) {
                // Active call - show call controls
                this.showActiveCallUI();
            } else {
                // No call - show dialer
                this.showDialerUI();
            }

            const dropdown = document.getElementById('arrowz-sp-dropdown');
            const widget = document.getElementById('arrowz-softphone-widget');
            if (dropdown) {
                // Portal mode: dropdown lives in document.body, position it under trigger
                if (dropdown.classList.contains('arrowz-sp-dropdown-portal') && widget) {
                    const trigger = widget.querySelector('.arrowz-sp-trigger');
                    if (trigger) {
                        const rect = trigger.getBoundingClientRect();
                        dropdown.style.position = 'fixed';
                        dropdown.style.top = (rect.bottom + 8) + 'px';
                        dropdown.style.right = (window.innerWidth - rect.right) + 'px';
                        dropdown.style.left = 'auto';
                    }
                }

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
                    <div class="sp-extension-selector" style="padding:4px 10px;background:var(--bg-color);border-bottom:1px solid var(--border-color);">
                        <div class="sp-ext-buttons" style="display:flex;gap:4px;flex-wrap:wrap;">
                            ${this.allExtensions.map(ext => `
                                <button class="sp-ext-btn ${ext.name === this.activeExtension ? 'active' : ''}"
                                        onclick="arrowz.softphone.switchExtension('${ext.name}')"
                                        title="${ext.display_name || ext.extension}"
                                        style="padding:3px 8px;font-size:10px;">
                                    ${ext.extension}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `;
            }

            // Active calls indicator
            const activeCount = this.getActiveSessionCount();
            let activeCallsIndicator = '';
            if (activeCount > 0) {
                activeCallsIndicator = `
                    <div style="padding:4px 10px;background:rgba(76,175,80,0.1);border-bottom:1px solid var(--border-color);display:flex;align-items:center;justify-content:space-between;">
                        <span style="font-size:10px;color:#4CAF50;font-weight:500;">
                            📞 ${activeCount} ${__('active')}
                        </span>
                        <button onclick="arrowz.softphone.showMultiLineCallUI()"
                                style="padding:2px 6px;font-size:10px;background:#4CAF50;color:white;border:none;border-radius:3px;cursor:pointer;">
                            ${__('View')}
                        </button>
                    </div>
                `;
            }

            dropdown.innerHTML = `
                <div class="sp-header" style="padding:6px 10px;">
                    <div class="sp-header-info">
                        <span class="sp-status-indicator ${this.registered ? 'online' : 'offline'}"></span>
                        <span class="sp-ext-number" style="font-size:13px;">${this.config?.extension || '---'}</span>
                        <span class="sp-status-label" style="font-size:11px;">${this.registered ? __('Ready') : __('Offline')}</span>
                    </div>
                    <button class="sp-close-btn" onclick="arrowz.softphone.closeDropdown()" style="font-size:20px;">×</button>
                </div>

                ${activeCallsIndicator}

                <div class="sp-content">
                    ${extensionButtons}

                    <div class="sp-dial-display" style="padding:6px 10px;gap:4px;">
                        <input type="tel" class="sp-dial-input" id="sp-dial-input"
                               placeholder="${__('Number or search...')}"
                               style="padding:6px;font-size:15px;"
                               oninput="arrowz.softphone.handleSearchInput(this.value)"
                               onkeypress="if(event.key==='Enter')arrowz.softphone.dial()">
                        <button class="sp-backspace" onclick="arrowz.softphone.backspace()" style="padding:6px 10px;font-size:13px;">⌫</button>
                    </div>
                    <div class="sp-search-results" id="sp-search-results" style="margin:0 10px;"></div>

                    <div class="sp-dialpad" style="gap:3px;padding:4px 10px 6px;">
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('1')">1</button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('2')">2</button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('3')">3</button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('4')">4</button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('5')">5</button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('6')">6</button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('7')">7</button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('8')">8</button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('9')">9</button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('*')">*</button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('0')">0</button>
                        <button class="sp-key" onclick="arrowz.softphone.pressKey('#')">#</button>
                    </div>

                    <div class="sp-actions" style="padding:4px 10px 6px;">
                        <button class="sp-call-btn ${!this.registered ? 'disabled' : ''}"
                                onclick="arrowz.softphone.dial()" ${!this.registered ? 'disabled' : ''}
                                style="width:42px;height:42px;">
                            <svg viewBox="0 0 24 24" fill="currentColor" style="width:20px;height:20px;">
                                <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/>
                            </svg>
                        </button>
                    </div>
                </div>

                <div class="sp-footer" style="padding:0;">
                    <button class="sp-footer-btn" onclick="arrowz.softphone.showHistory()" style="padding:5px;font-size:9px;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        ${__('History')}
                    </button>
                    <button class="sp-footer-btn" onclick="arrowz.softphone.showSettings()" style="padding:5px;font-size:9px;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
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
            const activeCount = this.getActiveSessionCount();

            // If more than one call, show multi-line UI
            if (activeCount > 1) {
                this.showMultiLineCallUI();
                return;
            }

            dropdown.innerHTML = `
                <div class="sp-call-screen" style="padding:10px;">
                    <div class="sp-call-header" style="margin-bottom:8px;display:flex;align-items:center;gap:10px;">
                        <div class="sp-call-avatar" style="width:40px;height:40px;border-radius:50%;background:#5e35b1;color:white;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                            <svg viewBox="0 0 24 24" fill="currentColor" style="width:20px;height:20px;">
                                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                            </svg>
                        </div>
                        <div class="sp-call-info" style="flex:1;min-width:0;">
                            <div class="sp-callee-number" style="font-size:14px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${callee}</div>
                            <div style="display:flex;align-items:center;gap:6px;">
                                <span class="sp-call-status" id="sp-call-status" style="font-size:11px;color:var(--text-muted);">${__('Connecting...')}</span>
                                <span class="sp-call-duration" id="sp-call-duration" style="font-size:13px;font-weight:600;color:#4CAF50;font-family:monospace;">00:00</span>
                            </div>
                        </div>
                    </div>

                    <div class="sp-call-actions" style="display:flex;justify-content:center;gap:6px;margin-bottom:8px;">
                        <button class="sp-call-action" onclick="arrowz.softphone.toggleMute()" id="sp-mute-btn"
                                style="padding:6px;width:44px;display:flex;flex-direction:column;align-items:center;gap:1px;border:none;border-radius:6px;background:var(--bg-color);cursor:pointer;">
                            <svg viewBox="0 0 24 24" fill="currentColor" class="unmuted" style="width:16px;height:16px;">
                                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                            </svg>
                            <span style="font-size:8px;">${__('Mute')}</span>
                        </button>
                        <button class="sp-call-action" onclick="arrowz.softphone.toggleHold()" id="sp-hold-btn"
                                style="padding:6px;width:44px;display:flex;flex-direction:column;align-items:center;gap:1px;border:none;border-radius:6px;background:var(--bg-color);cursor:pointer;">
                            <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;">
                                <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                            </svg>
                            <span style="font-size:8px;">${__('Hold')}</span>
                        </button>
                        <button class="sp-call-action" onclick="arrowz.softphone.toggleKeypad()"
                                style="padding:6px;width:44px;display:flex;flex-direction:column;align-items:center;gap:1px;border:none;border-radius:6px;background:var(--bg-color);cursor:pointer;">
                            <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;">
                                <path d="M12 19c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zM6 1c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm12-8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm-6 8c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm6 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm-6 0c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
                            </svg>
                            <span style="font-size:8px;">${__('DTMF')}</span>
                        </button>
                        <button class="sp-call-action" onclick="arrowz.softphone.showDialerForNewCall()"
                                style="padding:6px;width:44px;display:flex;flex-direction:column;align-items:center;gap:1px;border:none;border-radius:6px;background:var(--bg-color);cursor:pointer;">
                            <svg viewBox="0 0 24 24" fill="currentColor" style="width:16px;height:16px;">
                                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                            </svg>
                            <span style="font-size:8px;">${__('Add')}</span>
                        </button>
                    </div>

                    <div class="sp-keypad-overlay" id="sp-keypad-overlay" style="display:none;padding:6px;border-top:1px solid var(--border-color);">
                        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:3px;">
                            <button onclick="arrowz.softphone.sendDTMF('1')" style="padding:6px;font-size:12px;border:none;border-radius:4px;background:var(--bg-color);cursor:pointer;">1</button>
                            <button onclick="arrowz.softphone.sendDTMF('2')" style="padding:6px;font-size:12px;border:none;border-radius:4px;background:var(--bg-color);cursor:pointer;">2</button>
                            <button onclick="arrowz.softphone.sendDTMF('3')" style="padding:6px;font-size:12px;border:none;border-radius:4px;background:var(--bg-color);cursor:pointer;">3</button>
                            <button onclick="arrowz.softphone.sendDTMF('4')" style="padding:6px;font-size:12px;border:none;border-radius:4px;background:var(--bg-color);cursor:pointer;">4</button>
                            <button onclick="arrowz.softphone.sendDTMF('5')" style="padding:6px;font-size:12px;border:none;border-radius:4px;background:var(--bg-color);cursor:pointer;">5</button>
                            <button onclick="arrowz.softphone.sendDTMF('6')" style="padding:6px;font-size:12px;border:none;border-radius:4px;background:var(--bg-color);cursor:pointer;">6</button>
                            <button onclick="arrowz.softphone.sendDTMF('7')" style="padding:6px;font-size:12px;border:none;border-radius:4px;background:var(--bg-color);cursor:pointer;">7</button>
                            <button onclick="arrowz.softphone.sendDTMF('8')" style="padding:6px;font-size:12px;border:none;border-radius:4px;background:var(--bg-color);cursor:pointer;">8</button>
                            <button onclick="arrowz.softphone.sendDTMF('9')" style="padding:6px;font-size:12px;border:none;border-radius:4px;background:var(--bg-color);cursor:pointer;">9</button>
                            <button onclick="arrowz.softphone.sendDTMF('*')" style="padding:6px;font-size:12px;border:none;border-radius:4px;background:var(--bg-color);cursor:pointer;">*</button>
                            <button onclick="arrowz.softphone.sendDTMF('0')" style="padding:6px;font-size:12px;border:none;border-radius:4px;background:var(--bg-color);cursor:pointer;">0</button>
                            <button onclick="arrowz.softphone.sendDTMF('#')" style="padding:6px;font-size:12px;border:none;border-radius:4px;background:var(--bg-color);cursor:pointer;">#</button>
                        </div>
                    </div>

                    <div class="sp-hangup-section" style="display:flex;justify-content:center;padding:6px 0;">
                        <button class="sp-hangup-btn" onclick="arrowz.softphone.hangup()"
                                style="width:42px;height:42px;border-radius:50%;border:none;background:#f44336;color:white;cursor:pointer;display:flex;align-items:center;justify-content:center;">
                            <svg viewBox="0 0 24 24" fill="currentColor" style="width:20px;height:20px;transform:rotate(135deg);">
                                <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/>
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
                <div class="sp-incoming-screen" style="padding:12px;text-align:center;">
                    <div class="sp-incoming-animation" style="position:relative;width:56px;height:56px;margin:0 auto 10px;">
                        <div class="sp-pulse-ring" style="position:absolute;width:100%;height:100%;border-radius:50%;border:2px solid #2196F3;animation:pulse-ring 1.5s infinite;"></div>
                        <div class="sp-caller-avatar" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:40px;height:40px;border-radius:50%;background:#2196F3;color:white;display:flex;align-items:center;justify-content:center;">
                            <svg viewBox="0 0 24 24" fill="currentColor" style="width:20px;height:20px;">
                                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                            </svg>
                        </div>
                    </div>
                    <div class="sp-caller-info">
                        <div class="sp-caller-id" style="font-size:15px;font-weight:600;">${caller}</div>
                        <div class="sp-incoming-label" style="font-size:11px;color:var(--text-muted);margin-bottom:12px;">${__('Incoming Call')}</div>
                    </div>
                    <div class="sp-incoming-actions" style="display:flex;justify-content:center;gap:24px;">
                        <button class="sp-reject-btn" onclick="arrowz.softphone.rejectCall()"
                                style="width:42px;height:42px;border-radius:50%;border:none;background:#f44336;color:white;cursor:pointer;display:flex;align-items:center;justify-content:center;">
                            <svg viewBox="0 0 24 24" fill="currentColor" style="width:20px;height:20px;transform:rotate(135deg);">
                                <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"/>
                            </svg>
                        </button>
                        <button class="sp-answer-btn" onclick="arrowz.softphone.answerCall()"
                                style="width:42px;height:42px;border-radius:50%;border:none;background:#4CAF50;color:white;cursor:pointer;display:flex;align-items:center;justify-content:center;animation:pulse-answer 1s infinite;">
                            <svg viewBox="0 0 24 24" fill="currentColor" style="width:20px;height:20px;">
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

        // Get active session count
        getActiveSessionCount() {
            return this.sessions.filter(s => s && !s.isEnded()).length;
        },

        // Get session by index
        getSession(index) {
            return this.sessions[index] || null;
        },

        // Find first available line slot
        findAvailableLine() {
            for (let i = 0; i < this.maxLines; i++) {
                if (!this.sessions[i] || this.sessions[i].isEnded()) {
                    return i;
                }
            }
            return -1;
        },

        // Switch to specific line
        switchToLine(index) {
            if (index < 0 || index >= this.maxLines) return;
            const session = this.sessions[index];
            if (!session || session.isEnded()) return;

            // Put current line on hold if different
            const currentSession = this.sessions[this.activeLineIndex];
            if (currentSession && !currentSession.isEnded() && this.activeLineIndex !== index) {
                if (!currentSession.isOnHold().local) {
                    currentSession.hold();
                }
            }

            // Unhold new line
            this.activeLineIndex = index;
            this.session = session;
            if (session.isOnHold().local) {
                session.unhold();
            }

            // Update UI
            if (this.isDropdownOpen) {
                this.showMultiLineCallUI();
            }
            this.updateNavbarStatus('in-call', this._callNumbers[index] || __('Line') + ' ' + (index + 1));
        },

        // Hold all lines except specified
        holdAllExcept(exceptIndex) {
            this.sessions.forEach((s, i) => {
                if (s && !s.isEnded() && i !== exceptIndex && !s.isOnHold().local) {
                    s.hold();
                }
            });
        },

        // Initialize call number tracking
        _callNumbers: {},

        // Make outgoing call
        async makeCall(number) {
            if (!this.registered) {
                frappe.show_alert({
                    message: __('Softphone not registered'),
                    indicator: 'red'
                });
                return;
            }

            // Check for available line
            const lineIndex = this.findAvailableLine();
            if (lineIndex === -1) {
                frappe.show_alert({
                    message: __('All lines busy (max {0})', [this.maxLines]),
                    indicator: 'yellow'
                });
                return;
            }

            // Put current calls on hold
            this.holdAllExcept(-1);

            try {
                this._currentCallee = number;

                // Get microphone access with optimized constraints for WebRTC/VoIP
                this.localStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        sampleRate: 48000,
                        channelCount: 1
                    },
                    video: false
                });

                // Show call UI immediately
                this.showActiveCallUI(number);
                this.updateNavbarStatus('calling', number);

                // Build ICE servers - include both STUN and TURN for NAT traversal
                // Start with reliable public TURN servers
                let iceServers = [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' },
                    // OpenRelay TURN servers (free, reliable)
                    {
                        urls: 'turn:openrelay.metered.ca:80',
                        username: 'openrelayproject',
                        credential: 'openrelayproject'
                    },
                    {
                        urls: 'turn:openrelay.metered.ca:443',
                        username: 'openrelayproject',
                        credential: 'openrelayproject'
                    },
                    {
                        urls: 'turn:openrelay.metered.ca:443?transport=tcp',
                        username: 'openrelayproject',
                        credential: 'openrelayproject'
                    }
                ];

                // Add configured ICE servers from backend (prepend for priority)
                if (this.config.ice_servers && this.config.ice_servers.length > 0) {
                    // Filter out non-working TURN servers
                    const configuredServers = this.config.ice_servers.filter(s => {
                        if (s.urls && s.urls.startsWith('stun:')) return true;
                        if (s.urls && s.urls.includes('157.173.125.136:3478')) {
                            console.warn('Arrowz: Skipping non-responsive TURN server:', s.urls);
                            return false;
                        }
                        return true;
                    });
                    iceServers = [...configuredServers, ...iceServers];
                }

                console.log('Arrowz: Using ICE servers:', JSON.stringify(iceServers.map(s => s.urls)));

                // WebRTC call options - use 'negotiate' for FreePBX compatibility
                // FreePBX may not always support RTCP-MUX or BUNDLE strictly
                const options = {
                    mediaConstraints: { audio: true, video: false },
                    mediaStream: this.localStream,
                    pcConfig: {
                        iceServers: iceServers,
                        rtcpMuxPolicy: 'negotiate',    // Negotiate - FreePBX may not support 'require'
                        bundlePolicy: 'balanced',      // Balanced - don't force bundling
                        iceTransportPolicy: 'all',     // Allow both relay and direct
                        iceCandidatePoolSize: 0        // Disable pre-gathering
                    },
                    rtcOfferConstraints: {
                        offerToReceiveAudio: true,
                        offerToReceiveVideo: false
                    },
                    // Session timers for call keep-alive
                    sessionTimersExpires: 1800
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

                // Store pending line index BEFORE calling ua.call()
                // (newRTCSession event fires synchronously inside ua.call())
                this._pendingOutgoingLineIndex = lineIndex;

                // Make the call
                const newSession = this.ua.call(targetUri, options);

                // Clear pending line index
                this._pendingOutgoingLineIndex = undefined;

                // These are now set in handleNewSession, but set them here too for safety
                newSession._lineIndex = lineIndex;
                this.sessions[lineIndex] = newSession;
                this.session = newSession;
                this.activeLineIndex = lineIndex;
                this._callNumbers[lineIndex] = number;
                this.callStartTimes[lineIndex] = null;

                // Safety net: if handleNewSession didn't attach events, do it now
                if (!newSession._eventsAttached) {
                    newSession._eventsAttached = true;
                    this.setupSessionEvents(newSession, lineIndex);
                }
                console.log('Arrowz: Call session created on line', lineIndex + 1);

            } catch (error) {
                this._pendingOutgoingLineIndex = undefined;  // Clear on error
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

            // Determine line index based on call direction
            let lineIndex;

            if (session.direction === 'outgoing') {
                // For outgoing calls, use the pending line index we stored before ua.call()
                lineIndex = this._pendingOutgoingLineIndex;
                if (lineIndex === undefined) {
                    console.warn('Arrowz: No pending line index for outgoing call, skipping');
                    return;
                }
                // Store line index on session (events will be attached below)
                session._lineIndex = lineIndex;
            } else {
                // For incoming calls, find available line
                lineIndex = this.findAvailableLine();
            }

            if (lineIndex === -1 || lineIndex === undefined) {
                // All lines busy - reject with busy signal
                session.terminate({ status_code: 486, reason_phrase: 'Busy Here' });
                frappe.show_alert({
                    message: __('Incoming call rejected - all lines busy'),
                    indicator: 'orange'
                }, 5);
                return;
            }

            // Store session in array
            session._lineIndex = lineIndex;
            this.sessions[lineIndex] = session;
            this.session = session;
            this.activeLineIndex = lineIndex;

            if (session.direction === 'incoming') {
                const caller = session.remote_identity.display_name || session.remote_identity.uri.user;
                this._currentCallee = caller;
                this._callNumbers[lineIndex] = caller;
                this.callStartTimes[lineIndex] = null;
                this._isIncomingRinging = true;  // Track ringing state for UI

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

            // Only setup events if not already done (avoid duplicate handlers)
            if (!session._eventsAttached) {
                session._eventsAttached = true;
                this.setupSessionEvents(session, lineIndex);
            }
        },

        // Setup session events
        setupSessionEvents(targetSession, lineIndex) {
            const session = targetSession || this.session;
            if (!session) return;

            const idx = lineIndex !== undefined ? lineIndex : this.activeLineIndex;
            console.log('Arrowz: Setting up session events for line', idx + 1);

            // Log SDP for debugging + fix Docker NAT IPs
            session.on('sdp', (e) => {
                console.log('Arrowz: SDP event -', e.originator, 'type:', e.type);

                // Fix remote SDP: Replace Docker internal IPs with public IP
                // Asterisk inside Docker sends 172.x.x.x as ICE candidates and c= address
                // These are unreachable from external WebRTC clients
                if (e.originator === 'remote' && e.sdp) {
                    const originalSdp = e.sdp;

                    // Get public IP from SIP domain config
                    // The PBX public IP is resolved from the SIP domain or external_media_address
                    const pbxPublicIP = this._pbxPublicIP || '157.173.125.136';

                    // Detect Docker/private IPs in the SDP
                    const privateIPRegex = /\b(172\.\d{1,3}\.\d{1,3}\.\d{1,3})\b/g;
                    const privateIPs = [...new Set((originalSdp.match(privateIPRegex) || []))];

                    if (privateIPs.length > 0) {
                        console.warn('Arrowz: ⚠️ Remote SDP contains Docker/private IPs:', privateIPs.join(', '));
                        console.log('Arrowz: Rewriting SDP to use public IP:', pbxPublicIP);

                        // Replace private IPs in connection line (c=) and ICE candidates (a=candidate:)
                        let fixedSdp = originalSdp;
                        privateIPs.forEach(privateIP => {
                            fixedSdp = fixedSdp.split(privateIP).join(pbxPublicIP);
                        });

                        e.sdp = fixedSdp;

                        // Log the changes
                        const newCandidates = fixedSdp.split('\n').filter(l => l.startsWith('a=candidate:'));
                        console.log('Arrowz: ✅ SDP rewritten - new ICE candidates:');
                        newCandidates.forEach(c => console.log('  ', c.trim()));
                    }

                    // Log original candidates for debugging
                    const candidateLines = e.sdp.split('\n').filter(line => line.startsWith('a=candidate:'));
                    if (candidateLines.length > 0) {
                        console.log('Arrowz: Remote ICE candidates:');
                        candidateLines.forEach(c => console.log('  ', c.trim()));
                    } else {
                        console.warn('Arrowz: No ICE candidates in remote SDP - FreePBX may not have ICE enabled');
                    }

                    // Check connection address
                    const connectionLine = e.sdp.split('\n').find(line => line.startsWith('c='));
                    if (connectionLine) {
                        const match = connectionLine.match(/IN IP4 ([^\s\r]+)/);
                        if (match) {
                            console.log('Arrowz: Remote connection IP:', match[1]);
                        }
                    }
                }

                console.log('Arrowz: SDP content (first 500 chars):', e.sdp?.substring(0, 500));
            });

            session.on('peerconnection', (e) => {
                console.log('Arrowz: Peerconnection event received for line', idx + 1);
                const pc = e.peerconnection;
                let iceFailureTimeout = null;
                let hostCandidateReceived = false;
                let relayCandidateReceived = false;
                let srflxCandidateReceived = false;

                pc.onicecandidate = (event) => {
                    if (event.candidate) {
                        const c = event.candidate;
                        console.log('Arrowz: ICE candidate:', c.type, c.address + ':' + c.port,
                            c.protocol, 'priority:', c.priority,
                            c.relatedAddress ? 'relayed from ' + c.relatedAddress : '');
                        if (c.type === 'host') hostCandidateReceived = true;
                        if (c.type === 'srflx') srflxCandidateReceived = true;
                        if (c.type === 'relay') {
                            relayCandidateReceived = true;
                            console.log('Arrowz: ✅ TURN relay candidate available - NAT traversal should work');
                        }
                    } else {
                        console.log('Arrowz: ICE gathering complete - host:', hostCandidateReceived,
                            'srflx:', srflxCandidateReceived, 'relay:', relayCandidateReceived);
                        if (!relayCandidateReceived) {
                            console.warn('Arrowz: ⚠️ No TURN relay candidates - TURN server may be down or credentials wrong');
                            console.warn('Arrowz: Without TURN relay, calls may fail if direct connectivity is not possible');
                        }
                        if (!hostCandidateReceived) {
                            console.warn('Arrowz: No host ICE candidates - may have connectivity issues');
                        }
                    }
                };

                pc.oniceconnectionstatechange = () => {
                    const state = pc.iceConnectionState;
                    console.log('Arrowz: ICE connection state:', state);

                    // Log selected candidate pair when connected
                    if ((state === 'connected' || state === 'completed') && pc.getStats) {
                        pc.getStats().then(stats => {
                            stats.forEach(report => {
                                if (report.type === 'candidate-pair' && report.state === 'succeeded') {
                                    console.log('Arrowz: Connected via candidate pair:',
                                        'local:', report.localCandidateId,
                                        'remote:', report.remoteCandidateId);
                                }
                                if (report.type === 'local-candidate') {
                                    console.log('Arrowz: Local candidate:', report.candidateType, report.address);
                                }
                                if (report.type === 'remote-candidate') {
                                    console.log('Arrowz: Remote candidate:', report.candidateType, report.address);
                                }
                            });
                        }).catch(() => {});
                    }

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
                            console.error('Arrowz: ICE connection failed - terminating call on line', idx + 1);
                            // Log stats to understand why it failed
                            if (pc.getStats) {
                                pc.getStats().then(stats => {
                                    let candidatePairs = [];
                                    stats.forEach(report => {
                                        if (report.type === 'candidate-pair') {
                                            candidatePairs.push({
                                                state: report.state,
                                                local: report.localCandidateId,
                                                remote: report.remoteCandidateId
                                            });
                                        }
                                    });
                                    console.error('Arrowz: ICE failed candidate pairs:', JSON.stringify(candidatePairs));
                                }).catch(() => {});
                            }
                            frappe.show_alert({
                                message: __('Connection failed - please check your network'),
                                indicator: 'red'
                            }, 7);
                            this.endCallOnLine(idx, 'ICE Connection Failed');
                            break;

                        case 'disconnected':
                            console.warn('Arrowz: ICE disconnected on line', idx + 1, '- waiting 5s for recovery');
                            iceFailureTimeout = setTimeout(() => {
                                if (pc.iceConnectionState === 'disconnected') {
                                    console.error('Arrowz: ICE still disconnected after timeout');
                                    this.endCallOnLine(idx, 'Connection Lost');
                                }
                            }, 5000);
                            break;

                        case 'closed':
                            if (iceFailureTimeout) {
                                clearTimeout(iceFailureTimeout);
                            }
                            break;

                        case 'checking':
                            console.log('Arrowz: ICE checking - attempting to connect...');
                            break;
                    }
                };

                pc.onicegatheringstatechange = () => {
                    console.log('Arrowz: ICE gathering state:', pc.iceGatheringState);
                };

                pc.onconnectionstatechange = () => {
                    const state = pc.connectionState;
                    console.log('Arrowz: Connection state on line', idx + 1, ':', state);

                    if (state === 'failed') {
                        console.error('Arrowz: PeerConnection failed on line', idx + 1);
                        if (!this._callConfirmed) {
                            this.endCallOnLine(idx, 'Connection Failed');
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

            session.on('connecting', () => {
                console.log('Arrowz: Session connecting on line', idx + 1);
            });

            session.on('sending', (e) => {
                console.log('Arrowz: Session sending INVITE on line', idx + 1);
            });

            session.on('progress', () => {
                this.updateCallStatus(__('Ringing...'));
                this.updateNavbarStatus('ringing', this._callNumbers[idx] || this._currentCallee);
            });

            // 'accepted' fires when answer is sent (for incoming) or received (for outgoing)
            session.on('accepted', () => {
                console.log('Arrowz: Session accepted on line', idx + 1);
                this.stopRingtone();  // Stop ringtone immediately on accept
            });

            session.on('confirmed', () => {
                console.log('Arrowz: Session confirmed on line', idx + 1);
                this._callConfirmed = true;   // Mark call as fully connected
                this._isAnswering = false;    // No longer in answering phase
                this._isIncomingRinging = false;  // Definitely not ringing anymore
                this.stopRingtone();  // Also stop here as backup
                this.callStartTime = new Date();
                this.callStartTimes[idx] = new Date();
                this.startCallTimer();
                this.updateCallStatus(__('Connected'));
                this.updateNavbarStatus('in-call', this._callNumbers[idx] || this._currentCallee);

                // Show multi-line UI if more than one call
                if (this.getActiveSessionCount() > 1 && this.isDropdownOpen) {
                    this.showMultiLineCallUI();
                }

                // Update call log as answered in database
                if (this._currentCallLog) {
                    frappe.call({
                        method: 'arrowz.api.webrtc.update_call_answered',
                        args: { call_log: this._currentCallLog },
                        async: true
                    }).catch(() => console.warn('Failed to update call answered status'));
                }
            });

            session.on('ended', () => {
                console.log('Arrowz: Session ended on line', idx + 1);
                this._isIncomingRinging = false;
                // Update call log in database
                if (this._currentCallLog) {
                    frappe.call({
                        method: 'arrowz.api.webrtc.update_call_ended',
                        args: { call_log: this._currentCallLog, duration: this.getCallDurationForLine(idx) },
                        async: true
                    }).catch(() => {});
                }
                this.endCallOnLine(idx);
            });

            // Handle call rejection by remote party
            session.on('rejected', (e) => {
                console.warn('Arrowz: Call rejected on line', idx + 1, ':', e.cause);
                this._isAnswering = false;
                this._isIncomingRinging = false;
                this._callConfirmed = false;
                this.stopRingtone();

                let reason = 'Call Rejected';
                if (e.cause === 'Busy Here' || e.message?.status_code === 486) {
                    reason = __('Busy');
                } else if (e.message?.status_code === 603) {
                    reason = __('Declined');
                }
                this.endCallOnLine(idx, reason);
            });

            // Handle call cancellation (FreePBX sends CANCEL before answer)
            session.on('cancel', () => {
                console.warn('Arrowz: Call cancelled on line', idx + 1);
                this._isAnswering = false;
                this._isIncomingRinging = false;
                this._callConfirmed = false;
                this.stopRingtone();
                this.endCallOnLine(idx, __('Call Cancelled'));
            });

            // Handle call redirect
            session.on('redirected', (e) => {
                console.warn('Arrowz: Call redirected on line', idx + 1);
                this._isAnswering = false;
                this._callConfirmed = false;
                this.endCallOnLine(idx, __('Call Redirected'));
            });

            // Handle SIP request timeout
            session.on('transporterror', () => {
                console.error('Arrowz: Transport error on line', idx + 1);
                this._isAnswering = false;
                this._callConfirmed = false;
                this.endCallOnLine(idx, __('Connection Error'));
            });

            session.on('failed', (e) => {
                console.error('Arrowz: Call failed on line', idx + 1, ':', e.cause);
                console.error('Arrowz: Failure details:', JSON.stringify({
                    cause: e.cause,
                    originator: e.originator,
                    status_code: e.message?.status_code,
                    reason_phrase: e.message?.reason_phrase
                }));
                this._isAnswering = false;    // Reset answering flag
                this._isIncomingRinging = false;  // Reset ringing flag
                this._callConfirmed = false;  // Reset confirmed flag
                this.stopRingtone();  // Stop ringtone immediately on failure

                // Map common causes to user-friendly messages
                let errorMessage = e.cause;
                if (e.cause === 'SIP Failure Code') {
                    const statusCode = e.message?.status_code;
                    if (statusCode === 486) errorMessage = __('Busy');
                    else if (statusCode === 480) errorMessage = __('Temporarily Unavailable');
                    else if (statusCode === 487) errorMessage = __('Request Terminated');
                    else if (statusCode === 503) errorMessage = __('Extension not registered - check if target phone is online');
                    else if (statusCode === 408) errorMessage = __('Request Timeout');
                    else if (statusCode === 404) errorMessage = __('Extension not found');
                    else if (statusCode === 401 || statusCode === 407) errorMessage = __('Authentication failed');
                    else errorMessage = e.message?.reason_phrase || e.cause;
                } else if (e.cause === 'RTP Timeout') {
                    errorMessage = __('Connection timeout - no audio');
                } else if (e.cause === 'User Denied Media Access') {
                    errorMessage = __('Microphone access denied');
                } else if (e.cause === 'WebRTC Error') {
                    errorMessage = __('WebRTC Error - FreePBX endpoint needs webrtc=yes');
                } else if (e.cause === 'Incompatible SDP') {
                    errorMessage = __('Incompatible SDP - Target extension not WebRTC enabled');
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

                this.endCallOnLine(idx, errorMessage);
            });

            session.on('hold', () => {
                console.log('Arrowz: Line', idx + 1, 'on hold');
                if (idx === this.activeLineIndex) {
                    this.updateCallStatus(__('On Hold'));
                    document.getElementById('sp-hold-btn')?.classList.add('active');
                }
            });

            session.on('unhold', () => {
                console.log('Arrowz: Line', idx + 1, 'resumed');
                if (idx === this.activeLineIndex) {
                    this.updateCallStatus(__('Connected'));
                    document.getElementById('sp-hold-btn')?.classList.remove('active');
                }
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

                // Build ICE servers - include TURN if available for NAT traversal
                // Start with reliable public STUN/TURN servers as fallback
                let iceServers = [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' },
                    // OpenRelay TURN servers (free, reliable)
                    {
                        urls: 'turn:openrelay.metered.ca:80',
                        username: 'openrelayproject',
                        credential: 'openrelayproject'
                    },
                    {
                        urls: 'turn:openrelay.metered.ca:443',
                        username: 'openrelayproject',
                        credential: 'openrelayproject'
                    },
                    {
                        urls: 'turn:openrelay.metered.ca:443?transport=tcp',
                        username: 'openrelayproject',
                        credential: 'openrelayproject'
                    }
                ];

                // Add configured ICE servers from backend (prepend for priority)
                if (this.config.ice_servers && this.config.ice_servers.length > 0) {
                    // Filter out non-working TURN servers, keep STUN
                    const configuredServers = this.config.ice_servers.filter(s => {
                        // Keep all STUN servers
                        if (s.urls && s.urls.startsWith('stun:')) return true;
                        // For TURN, only keep if it's not the non-existent local TURN
                        if (s.urls && s.urls.includes('157.173.125.136:3478')) {
                            console.warn('Arrowz: Skipping non-responsive TURN server:', s.urls);
                            return false;
                        }
                        return true;
                    });
                    // Prepend configured servers
                    iceServers = [...configuredServers, ...iceServers];
                }

                // Log ICE configuration for debugging
                console.log('Arrowz: Using ICE servers:', JSON.stringify(iceServers.map(s => s.urls)));

                // Log the remote SDP (offer from FreePBX) for debugging
                const remoteDesc = this.session._request?.body;
                if (remoteDesc) {
                    console.log('Arrowz: Incoming SDP (remote offer):', remoteDesc.substring(0, 800));
                    // Check for common WebRTC issues in the SDP
                    if (!remoteDesc.includes('ICE') && !remoteDesc.includes('candidate')) {
                        console.warn('Arrowz: Remote SDP has no ICE candidates - FreePBX endpoint may need ice_support=yes');
                    }
                    if (!remoteDesc.includes('fingerprint')) {
                        console.warn('Arrowz: Remote SDP has no DTLS fingerprint - FreePBX endpoint may need media_encryption=dtls');
                    }
                    if (!remoteDesc.includes('setup:')) {
                        console.warn('Arrowz: Remote SDP has no DTLS setup - not WebRTC compatible');
                    }
                }

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
                    // Log the problematic SDP
                    const sdp = this.session._request?.body;
                    if (sdp) {
                        console.error('Arrowz: Problematic SDP from FreePBX:', sdp);
                    }
                    if (e.error?.message?.includes('RTCP-MUX')) {
                        frappe.show_alert({
                            message: __('Call failed: FreePBX needs RTCP-MUX enabled in PJSIP settings'),
                            indicator: 'red'
                        }, 10);
                    }
                });

                // Mark that we're answering (prevents accidental hangup before confirmed)
                this._isAnswering = true;
                this._isIncomingRinging = false;  // No longer ringing

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
            this._isIncomingRinging = false;  // No longer ringing

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

        // End call on specific line
        endCallOnLine(lineIndex, reason) {
            const session = this.sessions[lineIndex];

            // Clean up this specific line
            this.sessions[lineIndex] = null;
            this.callStartTimes[lineIndex] = null;
            delete this._callNumbers[lineIndex];

            // If this was the active line, find another active line
            if (lineIndex === this.activeLineIndex) {
                const nextActiveLine = this.sessions.findIndex(s => s && !s.isEnded());
                if (nextActiveLine !== -1) {
                    this.activeLineIndex = nextActiveLine;
                    this.session = this.sessions[nextActiveLine];
                    // Update UI for new active line
                    if (this.isDropdownOpen) {
                        if (this.getActiveSessionCount() > 1) {
                            this.showMultiLineCallUI();
                        } else {
                            this.showActiveCallUI(this._callNumbers[nextActiveLine]);
                        }
                    }
                    this.updateNavbarStatus('in-call', this._callNumbers[nextActiveLine] || __('On Call'));
                } else {
                    // No more active calls
                    this.session = null;
                    this.activeLineIndex = 0;
                    this.endCall(reason);
                    return;
                }
            }

            // Update multi-line UI if still have calls
            if (this.getActiveSessionCount() > 0 && this.isDropdownOpen) {
                if (this.getActiveSessionCount() > 1) {
                    this.showMultiLineCallUI();
                } else {
                    this.showActiveCallUI(this._callNumbers[this.activeLineIndex]);
                }
            }

            if (reason) {
                frappe.show_alert({
                    message: __('Line {0}: {1}', [lineIndex + 1, reason]),
                    indicator: 'orange'
                }, 3);
            }
        },

        // Get call duration for specific line
        getCallDurationForLine(lineIndex) {
            const startTime = this.callStartTimes[lineIndex];
            if (!startTime) return 0;
            return Math.floor((new Date() - startTime) / 1000);
        },

        // End call cleanup (all lines)
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

            // Clear all sessions
            this.sessions = [];
            this.session = null;
            this.callStartTime = null;
            this.callStartTimes = {};
            this._callNumbers = {};
            this._isIncomingRinging = false;
            this.activeLineIndex = 0;
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

        // Show multi-line call UI
        showMultiLineCallUI() {
            const dropdown = document.getElementById('arrowz-sp-dropdown');
            if (!dropdown) return;

            const activeCount = this.getActiveSessionCount();

            // Build lines status HTML
            let linesHtml = '';
            this.sessions.forEach((session, idx) => {
                if (!session || session.isEnded()) return;

                const number = this._callNumbers[idx] || __('Unknown');
                const isActive = idx === this.activeLineIndex;
                const isHeld = session.isOnHold()?.local;
                const startTime = this.callStartTimes[idx];
                let duration = '00:00';
                if (startTime) {
                    const elapsed = Math.floor((new Date() - startTime) / 1000);
                    const mins = Math.floor(elapsed / 60);
                    const secs = elapsed % 60;
                    duration = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
                }

                linesHtml += `
                    <div class="sp-line-item ${isActive ? 'active' : ''} ${isHeld ? 'held' : ''}"
                         onclick="arrowz.softphone.switchToLine(${idx})">
                        <div class="sp-line-indicator">${idx + 1}</div>
                        <div class="sp-line-info">
                            <div class="sp-line-number">${number}</div>
                            <div class="sp-line-status">${isHeld ? __('On Hold') : __('Active')}</div>
                        </div>
                        <div class="sp-line-duration">${duration}</div>
                        <button class="sp-line-hangup" onclick="event.stopPropagation(); arrowz.softphone.hangupLine(${idx})">
                            ✕
                        </button>
                    </div>
                `;
            });

            dropdown.innerHTML = `
                <div class="sp-header">
                    <div class="sp-header-info">
                        <span class="sp-status-indicator online"></span>
                        <span class="sp-ext-number">${activeCount} ${__('Active Calls')}</span>
                    </div>
                    <button class="sp-close-btn" onclick="arrowz.softphone.closeDropdown()">×</button>
                </div>

                <div class="sp-content sp-multiline">
                    <div class="sp-lines-container">
                        ${linesHtml}
                    </div>

                    <div class="sp-multiline-actions">
                        <button class="sp-action-compact" onclick="arrowz.softphone.toggleMute()" id="sp-mute-btn" title="${__('Mute')}">
                            <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                            </svg>
                        </button>
                        <button class="sp-action-compact" onclick="arrowz.softphone.toggleHold()" id="sp-hold-btn" title="${__('Hold')}">
                            <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                                <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                            </svg>
                        </button>
                        <button class="sp-action-compact" onclick="arrowz.softphone.showDialerForNewCall()" title="${__('New Call')}">
                            <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                            </svg>
                        </button>
                        <button class="sp-action-compact danger" onclick="arrowz.softphone.hangupAll()" title="${__('Hangup All')}">
                            <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                                <path d="M12 9c-1.6 0-3.15.25-4.6.72v3.1c0 .39-.23.74-.56.9-.98.49-1.87 1.12-2.66 1.85-.18.18-.43.28-.7.28-.28 0-.53-.11-.71-.29L.29 13.08c-.18-.17-.29-.42-.29-.7 0-.28.11-.53.29-.71C3.34 8.78 7.46 7 12 7s8.66 1.78 11.71 4.67c.18.18.29.43.29.71 0 .28-.11.53-.29.71l-2.48 2.48c-.18.18-.43.29-.71.29-.27 0-.52-.11-.7-.28-.79-.74-1.69-1.36-2.67-1.85-.33-.16-.56-.5-.56-.9v-3.1C15.15 9.25 13.6 9 12 9z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            `;

            dropdown.classList.add('open');
            this.isDropdownOpen = true;
        },

        // Hangup specific line
        hangupLine(lineIndex) {
            const session = this.sessions[lineIndex];
            if (session && !session.isEnded()) {
                try {
                    session.terminate();
                } catch (e) {
                    console.error('Error terminating line', lineIndex + 1, e);
                }
            }
        },

        // Hangup all lines
        hangupAll() {
            this.sessions.forEach((session, idx) => {
                if (session && !session.isEnded()) {
                    try {
                        session.terminate();
                    } catch (e) {
                        console.error('Error terminating line', idx + 1, e);
                    }
                }
            });
        },

        // Show dialer for adding new call
        showDialerForNewCall() {
            // Put current call on hold first
            if (this.session && !this.session.isOnHold().local) {
                this.session.hold();
            }
            this.showDialerUI();
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
                /* Frappe v16 Desktop Style Widget */
                .arrowz-softphone-desktop {
                    position: relative;
                    display: flex;
                    align-items: center;
                }

                .arrowz-softphone-desktop .arrowz-sp-trigger {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    padding: 8px;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s;
                    background: transparent;
                }

                .arrowz-softphone-desktop .arrowz-sp-trigger:hover {
                    background: var(--bg-dark-gray, rgba(0,0,0,0.05));
                }

                .arrowz-softphone-desktop .sp-icon {
                    width: 20px;
                    height: 20px;
                    color: var(--text-muted, #6c757d);
                }

                .arrowz-softphone-desktop .arrowz-sp-dropdown {
                    position: absolute;
                    top: calc(100% + 8px);
                    right: 0;
                    z-index: 1050;
                }

                /* Legacy Navbar Widget */
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
                    width: 260px;
                    background: var(--card-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 10px;
                    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
                    opacity: 0;
                    visibility: hidden;
                    transform: translateY(-10px);
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    z-index: 1050;
                    overflow: hidden;
                    display: flex;
                    flex-direction: column;
                }

                /* Portal mode: dropdown appended to body to escape topbar overflow */
                .arrowz-sp-dropdown.arrowz-sp-dropdown-portal {
                    position: fixed;
                    z-index: 1060;
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
                    padding: 8px 12px;
                    background: #333333;
                    color: white;
                    flex-shrink: 0;
                    border-radius: 10px 10px 0 0;
                }

                /* Content wrapper */
                .sp-content {
                    flex: 1;
                    overflow: visible;
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
                    padding: 6px 10px;
                    gap: 6px;
                }

                .sp-dial-input {
                    flex: 1;
                    padding: 8px;
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    font-size: 14px;
                    text-align: center;
                    letter-spacing: 1px;
                    font-family: monospace;
                    background: var(--fg-color);
                }

                .sp-dial-input:focus {
                    outline: none;
                    border-color: #5e35b1;
                }

                .sp-backspace {
                    padding: 8px 12px;
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    background: var(--fg-color);
                    font-size: 14px;
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
                    gap: 4px;
                    padding: 4px 10px 8px;
                }

                .sp-key {
                    height: 32px;
                    border: none;
                    border-radius: 6px;
                    background: var(--bg-color);
                    font-size: 15px;
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

                /* ======================================
                   COMPACT UI - No Scroll Required
                   ====================================== */

                /* Compact Dialpad */
                .sp-dialpad {
                    gap: 4px !important;
                    padding: 0 12px 8px !important;
                }

                .sp-key {
                    aspect-ratio: 1.5 !important;
                    font-size: 18px !important;
                    padding: 4px !important;
                }

                .sp-key span {
                    font-size: 7px !important;
                    display: none;
                }

                /* Compact Search */
                .sp-search-container {
                    padding: 8px 12px !important;
                }

                .sp-search-input {
                    padding: 8px 12px !important;
                    font-size: 13px !important;
                }

                /* Compact Dial Display */
                .sp-dial-display {
                    padding: 0 12px 8px !important;
                }

                .sp-dial-input {
                    padding: 8px !important;
                    font-size: 18px !important;
                }

                .sp-backspace {
                    padding: 8px 12px !important;
                    font-size: 16px !important;
                }

                /* Compact Header */
                .sp-header {
                    padding: 8px 12px !important;
                }

                .sp-ext-number {
                    font-size: 14px !important;
                }

                /* Compact Call Button */
                .sp-actions {
                    padding: 0 12px 8px !important;
                }

                .sp-call-btn {
                    width: 52px !important;
                    height: 52px !important;
                }

                .sp-call-btn svg {
                    width: 24px !important;
                    height: 24px !important;
                }

                /* Compact Footer */
                .sp-footer {
                    padding: 0 !important;
                }

                .sp-footer-btn {
                    padding: 8px !important;
                    font-size: 11px !important;
                }

                .sp-footer-btn svg {
                    width: 14px !important;
                    height: 14px !important;
                }

                /* Compact Extension Selector */
                .sp-extension-selector {
                    padding: 6px 12px !important;
                }

                .sp-ext-btn {
                    padding: 4px 10px !important;
                    font-size: 11px !important;
                }

                /* Dropdown max height reduced */
                .arrowz-sp-dropdown {
                    max-height: 420px !important;
                }

                .sp-content {
                    max-height: calc(420px - 90px) !important;
                }

                /* ======================================
                   MULTI-LINE UI Styles
                   ====================================== */

                .sp-content.sp-multiline {
                    padding: 8px;
                }

                .sp-lines-container {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                    margin-bottom: 10px;
                }

                .sp-line-item {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 10px 12px;
                    background: var(--bg-color);
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s;
                    border: 2px solid transparent;
                }

                .sp-line-item:hover {
                    background: var(--border-color);
                }

                .sp-line-item.active {
                    border-color: #4CAF50;
                    background: rgba(76, 175, 80, 0.1);
                }

                .sp-line-item.held {
                    opacity: 0.7;
                }

                .sp-line-indicator {
                    width: 28px;
                    height: 28px;
                    border-radius: 50%;
                    background: #5e35b1;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    font-weight: 600;
                }

                .sp-line-item.active .sp-line-indicator {
                    background: #4CAF50;
                }

                .sp-line-item.held .sp-line-indicator {
                    background: #ff9800;
                }

                .sp-line-info {
                    flex: 1;
                    min-width: 0;
                }

                .sp-line-number {
                    font-size: 14px;
                    font-weight: 500;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                .sp-line-status {
                    font-size: 11px;
                    color: var(--text-muted);
                }

                .sp-line-item.active .sp-line-status {
                    color: #4CAF50;
                }

                .sp-line-item.held .sp-line-status {
                    color: #ff9800;
                }

                .sp-line-duration {
                    font-size: 12px;
                    font-family: monospace;
                    color: var(--text-muted);
                }

                .sp-line-hangup {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    border: none;
                    background: #f44336;
                    color: white;
                    font-size: 12px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }

                .sp-line-hangup:hover {
                    background: #d32f2f;
                    transform: scale(1.1);
                }

                .sp-multiline-actions {
                    display: flex;
                    justify-content: center;
                    gap: 12px;
                    padding: 8px 0;
                }

                .sp-action-compact {
                    width: 44px;
                    height: 44px;
                    border-radius: 50%;
                    border: none;
                    background: var(--bg-color);
                    color: var(--text-color);
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }

                .sp-action-compact:hover {
                    background: var(--border-color);
                    transform: scale(1.05);
                }

                .sp-action-compact.danger {
                    background: #f44336;
                    color: white;
                }

                .sp-action-compact.danger:hover {
                    background: #d32f2f;
                }

                .sp-action-compact.active {
                    background: #ff9800;
                    color: white;
                }

                /* Compact Call Screen */
                .sp-call-screen {
                    padding: 12px !important;
                }

                .sp-call-header {
                    margin-bottom: 12px !important;
                }

                .sp-call-avatar {
                    width: 60px !important;
                    height: 60px !important;
                    margin-bottom: 8px !important;
                }

                .sp-call-avatar svg {
                    width: 30px !important;
                    height: 30px !important;
                }

                .sp-callee-number {
                    font-size: 18px !important;
                }

                #sp-call-duration {
                    font-size: 22px !important;
                    margin-top: 4px !important;
                }

                .sp-call-actions {
                    gap: 8px !important;
                    margin-bottom: 12px !important;
                }

                .sp-call-action {
                    padding: 8px 6px !important;
                }

                .sp-call-action svg {
                    width: 20px !important;
                    height: 20px !important;
                }

                .sp-call-action span {
                    font-size: 10px !important;
                }

                .sp-hangup-btn {
                    width: 52px !important;
                    height: 52px !important;
                }

                .sp-hangup-btn svg {
                    width: 24px !important;
                    height: 24px !important;
                }

                /* Compact Incoming Call */
                .sp-incoming-screen {
                    padding: 16px !important;
                }

                .sp-incoming-animation {
                    width: 80px !important;
                    height: 80px !important;
                    margin-bottom: 12px !important;
                }

                .sp-caller-avatar {
                    width: 56px !important;
                    height: 56px !important;
                }

                .sp-caller-id {
                    font-size: 20px !important;
                }

                .sp-incoming-label {
                    margin-bottom: 16px !important;
                }

                .sp-incoming-actions {
                    gap: 30px !important;
                }

                .sp-reject-btn, .sp-answer-btn {
                    width: 52px !important;
                    height: 52px !important;
                }

                .sp-reject-btn svg, .sp-answer-btn svg {
                    width: 24px !important;
                    height: 24px !important;
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
