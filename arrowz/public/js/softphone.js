// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Arrowz Softphone - Navbar Integration
 * Provides WebRTC-based calling directly from the Frappe navbar
 */

(function() {
    'use strict';
    
    // Arrowz namespace
    window.arrowz = window.arrowz || {};
    
    // Softphone state
    arrowz.softphone = {
        initialized: false,
        registered: false,
        ua: null,  // JsSIP User Agent
        session: null,  // Active call session
        config: null,
        audioPlayer: null,
        localStream: null,
        remoteStream: null,
        callTimer: null,
        callStartTime: null,
        
        // Initialize softphone
        async init() {
            if (this.initialized) return;
            
            try {
                // Add navbar widget first (always show)
                this.renderNavbarWidget();
                
                // Load JsSIP if not available
                if (typeof JsSIP === 'undefined') {
                    await this.loadJsSIP();
                }
                
                // Get configuration
                this.config = await this.getConfig();
                
                if (!this.config) {
                    console.log('Arrowz: No extension configured');
                    this.updateStatus('no-config');
                    this.initialized = true;
                    return;
                }
                
                // Initialize audio
                this.initAudio();
                
                // Setup JsSIP
                await this.setupJsSIP();
                
                this.initialized = true;
                console.log('Arrowz Softphone initialized');
                
            } catch (error) {
                console.error('Arrowz Softphone init error:', error);
                this.updateStatus('error');
            }
        },
        
        // Load JsSIP library
        loadJsSIP() {
            return new Promise((resolve, reject) => {
                const script = document.createElement('script');
                script.src = '/assets/arrowz/js/jssip.min.js';
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            });
        },
        
        // Get WebRTC configuration
        async getConfig() {
            try {
                const r = await frappe.call({
                    method: 'arrowz.api.webrtc.get_webrtc_config'
                });
                return r.message;
            } catch (e) {
                return null;
            }
        },
        
        // Initialize audio elements
        initAudio() {
            // Remote audio (caller's voice)
            this.audioPlayer = document.createElement('audio');
            this.audioPlayer.id = 'arrowz-remote-audio';
            this.audioPlayer.autoplay = true;
            this.audioPlayer.playsInline = true;  // iOS Safari requirement
            this.audioPlayer.setAttribute('playsinline', '');
            document.body.appendChild(this.audioPlayer);
            
            // Ringtone
            this.ringtone = document.createElement('audio');
            this.ringtone.id = 'arrowz-ringtone';
            this.ringtone.loop = true;
            this.ringtone.playsInline = true;  // iOS Safari requirement
            this.ringtone.setAttribute('playsinline', '');
            this.ringtone.src = '/assets/arrowz/sounds/ringtone.mp3';
            // Preload for iOS
            this.ringtone.load();
            document.body.appendChild(this.ringtone);
            
            // iOS audio unlock - required for autoplay
            this.setupIOSAudioUnlock();
        },
        
        // iOS requires user interaction to unlock audio
        setupIOSAudioUnlock() {
            const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || 
                          (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
            
            if (isIOS) {
                console.log('Arrowz: iOS detected, setting up audio unlock');
                
                const unlockAudio = () => {
                    // Create a silent audio context to unlock audio
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    if (AudioContext) {
                        const audioCtx = new AudioContext();
                        const buffer = audioCtx.createBuffer(1, 1, 22050);
                        const source = audioCtx.createBufferSource();
                        source.buffer = buffer;
                        source.connect(audioCtx.destination);
                        source.start(0);
                    }
                    
                    // Also try to play and pause the ringtone
                    this.ringtone.play().then(() => {
                        this.ringtone.pause();
                        this.ringtone.currentTime = 0;
                        console.log('Arrowz: iOS audio unlocked');
                    }).catch(() => {});
                    
                    // Remove listeners after first interaction
                    document.removeEventListener('touchstart', unlockAudio);
                    document.removeEventListener('click', unlockAudio);
                };
                
                document.addEventListener('touchstart', unlockAudio, { once: true });
                document.addEventListener('click', unlockAudio, { once: true });
            }
        },
        
        // Modify SDP for FreePBX/Asterisk compatibility
        // This removes unsupported codecs and fixes common issues
        fixSDPForFreePBX(sdp) {
            let lines = sdp.split('\r\n');
            let newLines = [];
            
            for (let line of lines) {
                // Keep all lines, but we can modify specific ones if needed
                // FreePBX typically supports: PCMU (0), PCMA (8), opus (dynamic)
                newLines.push(line);
            }
            
            return newLines.join('\r\n');
        },
        
        // Setup JsSIP User Agent
        async setupJsSIP() {
            const socket = new JsSIP.WebSocketInterface(this.config.websocket_servers[0]);
            
            console.log('Arrowz: Setting up JsSIP with URI:', this.config.sip_uri);
            console.log('Arrowz: WebSocket server:', this.config.websocket_servers[0]);
            console.log('Arrowz: Password present:', !!this.config.sip_password);
            
            // Enable JsSIP debug for troubleshooting
            JsSIP.debug.enable('JsSIP:*');
            
            const configuration = {
                sockets: [socket],
                uri: this.config.sip_uri,
                password: this.config.sip_password,
                display_name: this.config.display_name,
                register: true,
                session_timers: false,  // Disable session timers to simplify SDP
                register_expires: 300,
                user_agent: 'Arrowz-WebRTC/1.0'
            };
            
            if (this.config.outbound_proxy) {
                configuration.outbound_proxy_set = this.config.outbound_proxy;
            }
            
            this.ua = new JsSIP.UA(configuration);
            
            // Event handlers
            this.ua.on('connected', () => {
                console.log('Arrowz: WebSocket connected');
            });
            
            this.ua.on('disconnected', () => {
                console.log('Arrowz: WebSocket disconnected');
                this.updateStatus('disconnected');
            });
            
            this.ua.on('registered', () => {
                console.log('Arrowz: SIP registered successfully');
                this.registered = true;
                this.updateStatus('registered');
            });
            
            this.ua.on('unregistered', () => {
                console.log('Arrowz: SIP unregistered');
                this.registered = false;
                this.updateStatus('unregistered');
            });
            
            this.ua.on('registrationFailed', (e) => {
                console.error('Arrowz: Registration failed -', e.cause);
                console.error('Arrowz: Check SIP credentials in AZ Extension');
                console.error('Arrowz: SIP URI used:', this.config.sip_uri);
                this.updateStatus('failed');
                
                // Show user-friendly error
                frappe.show_alert({
                    message: __('SIP Registration Failed: {0}. Please check your extension credentials.', [e.cause]),
                    indicator: 'red'
                }, 10);
            });
            
            this.ua.on('newRTCSession', (e) => {
                this.handleNewSession(e);
            });
            
            // Start
            this.ua.start();
        },
        
        // Handle new RTC session (incoming or outgoing)
        handleNewSession(e) {
            const session = e.session;
            
            // If we already have an active session, reject
            if (this.session) {
                session.terminate({ status_code: 486, reason_phrase: 'Busy Here' });
                return;
            }
            
            this.session = session;
            
            if (session.direction === 'incoming') {
                this.handleIncomingCall(session);
            } else {
                this.handleOutgoingCall(session);
            }
            
            // Session event handlers
            session.on('progress', () => {
                console.log('Arrowz: Call in progress');
                this.updateCallStatus('ringing');
            });
            
            session.on('confirmed', () => {
                console.log('Arrowz: Call confirmed');
                this.stopRingtone();
                this.callStartTime = new Date();
                this.startCallTimer();
                this.updateCallStatus('connected');
            });
            
            session.on('ended', () => {
                console.log('Arrowz: Call ended');
                this.endCall();
            });
            
            session.on('failed', (e) => {
                console.log('Arrowz: Call failed', e.cause);
                this.endCall(e.cause);
            });
            
            session.on('hold', () => {
                this.updateCallStatus('hold');
            });
            
            session.on('unhold', () => {
                this.updateCallStatus('connected');
            });
            
            session.on('muted', () => {
                this.updateMuteStatus(true);
            });
            
            session.on('unmuted', () => {
                this.updateMuteStatus(false);
            });
        },
        
        // Handle incoming call
        handleIncomingCall(session) {
            console.log('Arrowz: Incoming call received');
            const remoteIdentity = session.remote_identity;
            const caller = remoteIdentity.display_name || remoteIdentity.uri.user;
            console.log('Arrowz: Caller:', caller);
            
            this.playRingtone();
            this.showIncomingCallDialog(caller);
            
            // Try browser notifications for iOS/background support
            this.showBrowserNotification(caller);
            
            // Notify server about incoming call (for logging/screen pop)
            frappe.call({
                method: 'arrowz.api.webrtc.on_incoming_call',
                args: {
                    caller_id: caller,
                    call_id: session.id
                },
                async: true
            });
        },
        
        // Show browser notification (works on iOS if permission granted)
        showBrowserNotification(caller) {
            if ('Notification' in window) {
                if (Notification.permission === 'granted') {
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
                    
                    // Store reference to close later
                    this.currentNotification = notification;
                } else if (Notification.permission !== 'denied') {
                    // Request permission
                    Notification.requestPermission();
                }
            }
        },
        
        // Handle outgoing call
        handleOutgoingCall(session) {
            console.log('Arrowz: Outgoing call started');
            this.updateCallStatus('calling');
        },
        
        // Show incoming call dialog
        showIncomingCallDialog(caller) {
            if (this.incomingDialog) {
                this.incomingDialog.hide();
            }
            
            this.incomingDialog = new frappe.ui.Dialog({
                title: __('Incoming Call'),
                indicator: 'green',
                fields: [
                    {
                        fieldtype: 'HTML',
                        options: `
                            <div class="incoming-call-alert text-center">
                                <div class="caller-avatar">📞</div>
                                <h3 class="caller-id">${caller}</h3>
                                <p>${__('Incoming call...')}</p>
                            </div>
                        `
                    }
                ],
                primary_action_label: __('Answer'),
                primary_action: () => {
                    this.answerCall();
                    this.incomingDialog.hide();
                },
                secondary_action_label: __('Decline'),
                secondary_action: () => {
                    this.rejectCall();
                    this.incomingDialog.hide();
                }
            });
            
            this.incomingDialog.show();
            
            // Add custom styling
            this.incomingDialog.$wrapper.addClass('arrowz-incoming-dialog');
        },
        
        // Answer incoming call
        async answerCall() {
            if (!this.session) {
                console.log('Arrowz: answerCall - no session');
                return;
            }
            
            console.log('Arrowz: Answering call...');
            
            try {
                // Setup media stream handlers BEFORE answering
                this.setupMediaStreams();
                
                console.log('Arrowz: Requesting microphone access...');
                this.localStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    },
                    video: false
                });
                console.log('Arrowz: Microphone access granted for answer');
                
                // Simplified options for better FreePBX/Asterisk compatibility
                const options = {
                    mediaConstraints: { 
                        audio: true, 
                        video: false 
                    },
                    mediaStream: this.localStream,
                    pcConfig: {
                        iceServers: this.config.ice_servers || [
                            { urls: 'stun:stun.l.google.com:19302' }
                        ]
                    },
                    rtcAnswerConstraints: {
                        offerToReceiveAudio: true,
                        offerToReceiveVideo: false
                    }
                };
                
                console.log('Arrowz: Calling session.answer()...');
                this.session.answer(options);
                console.log('Arrowz: Answer sent');
                this.stopRingtone();
                
            } catch (error) {
                console.error('Arrowz: Failed to answer call', error);
                frappe.show_alert({
                    message: __('Failed to access microphone'),
                    indicator: 'red'
                });
            }
        },
        
        // Reject incoming call
        rejectCall() {
            this.stopRingtone();
            
            if (this.session) {
                try {
                    // Check if session is in a valid state to terminate
                    const status = this.session.status;
                    // JsSIP session statuses: 0=NULL, 1=INVITE_SENT, 2=1XX_RECEIVED, 3=INVITE_RECEIVED, 
                    // 4=WAITING_FOR_ANSWER, 5=ANSWERED, 6=WAITING_FOR_ACK, 7=CANCELED, 8=TERMINATED, 9=CONFIRMED
                    if (status < 7) {
                        this.session.terminate({ status_code: 603, reason_phrase: 'Decline' });
                    } else {
                        console.log('Arrowz: Session already terminated, status:', status);
                    }
                } catch (error) {
                    console.log('Arrowz: Error rejecting call:', error.message);
                }
                this.session = null;
            }
            
            if (this.incomingDialog) {
                this.incomingDialog.hide();
            }
        },
        
        // Make outgoing call
        async makeCall(number) {
            console.log('Arrowz: makeCall() called with:', number);
            
            if (!this.registered) {
                console.log('Arrowz: makeCall failed - not registered');
                frappe.show_alert({
                    message: __('Softphone not registered'),
                    indicator: 'red'
                });
                return;
            }
            
            if (this.session) {
                console.log('Arrowz: makeCall failed - already on a call');
                frappe.show_alert({
                    message: __('Already on a call'),
                    indicator: 'yellow'
                });
                return;
            }
            
            try {
                console.log('Arrowz: Requesting microphone access...');
                this.localStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    },
                    video: false
                });
                console.log('Arrowz: Microphone access granted');

                // Options for FreePBX/Asterisk WebRTC compatibility
                const options = {
                    mediaConstraints: { 
                        audio: true, 
                        video: false 
                    },
                    mediaStream: this.localStream,
                    pcConfig: {
                        iceServers: this.config.ice_servers || [
                            { urls: 'stun:stun.l.google.com:19302' }
                        ],
                        // Required for proper ICE handling
                        iceCandidatePoolSize: 0
                    },
                    rtcOfferConstraints: {
                        offerToReceiveAudio: true,
                        offerToReceiveVideo: false
                    },
                    // Session timers for FreePBX
                    sessionTimersExpires: 120,
                    sessionTimersExpires: 120
                };

                // Clean and format number for SIP
                let dialNumber = (number || '').toString().trim();
                // Remove any non-digit characters except + and *
                dialNumber = dialNumber.replace(/[^\d+*#]/g, '');
                
                // Only add + prefix for numbers that look like international (10+ digits without +)
                // Don't add + for short extension numbers (less than 7 digits)
                if (dialNumber.length >= 10 && /^\d+$/.test(dialNumber)) {
                    dialNumber = '+' + dialNumber;
                }
                
                // Build full SIP URI for the target
                const targetUri = `sip:${dialNumber}@${this.config.sip_domain}`;
                
                console.log('Arrowz: Dialing number:', dialNumber);
                console.log('Arrowz: Target URI:', targetUri);

                // Create call log server-side
                frappe.call({
                    method: 'arrowz.api.webrtc.initiate_call',
                    args: { number: dialNumber },
                    async: true
                });

                console.log('Arrowz: Calling ua.call()...');
                this.session = this.ua.call(targetUri, options);
                console.log('Arrowz: Session created:', this.session ? 'yes' : 'no');
                
                if (this.session) {
                    // Setup media streams IMMEDIATELY after creating session
                    this.setupMediaStreams();
                    
                    // Add debug event listeners
                    this.session.on('sdp', (e) => {
                        console.log('Arrowz: SDP type:', e.type);
                    });
                    
                    this.session.on('sending', (e) => {
                        console.log('Arrowz: Sending INVITE');
                    });
                }
                
                this.showCallWidget(dialNumber);

            } catch (error) {
                console.error('Arrowz: Failed to make call', error);
                frappe.show_alert({
                    message: __('Failed to access microphone: ') + error.message,
                    indicator: 'red'
                });
            }
        },
        
        // Alias for makeCall (for backward compatibility)
        call(number) {
            return this.makeCall(number);
        },
        
        // Setup media streams
        setupMediaStreams() {
            if (!this.session) {
                console.log('Arrowz: setupMediaStreams - no session');
                return;
            }
            
            console.log('Arrowz: Setting up media streams');
            
            // Listen for peerconnection event from JsSIP session
            this.session.on('peerconnection', (e) => {
                console.log('Arrowz: PeerConnection event received');
                const pc = e.peerconnection;
                
                // Log ICE candidates
                pc.onicecandidate = (event) => {
                    if (event.candidate) {
                        console.log('Arrowz: ICE candidate:', event.candidate.type, event.candidate.address);
                    } else {
                        console.log('Arrowz: ICE gathering complete');
                    }
                };
                
                // Handle remote track - this is the modern way
                pc.ontrack = (event) => {
                    console.log('Arrowz: Remote track received, kind:', event.track.kind);
                    if (event.streams && event.streams[0]) {
                        this.remoteStream = event.streams[0];
                        this.audioPlayer.srcObject = event.streams[0];
                        console.log('Arrowz: Remote stream attached to audio player');
                        
                        // Explicitly play audio
                        this.playRemoteAudio();
                    }
                };
                
                // Deprecated but still used by some browsers
                pc.onaddstream = (event) => {
                    console.log('Arrowz: Remote stream added (legacy)');
                    this.remoteStream = event.stream;
                    this.audioPlayer.srcObject = event.stream;
                    this.playRemoteAudio();
                };
                
                // Log ICE connection state changes
                pc.oniceconnectionstatechange = () => {
                    console.log('Arrowz: ICE connection state:', pc.iceConnectionState);
                    if (pc.iceConnectionState === 'connected' || pc.iceConnectionState === 'completed') {
                        console.log('Arrowz: ICE connected - audio should be flowing');
                    }
                    if (pc.iceConnectionState === 'failed') {
                        console.error('Arrowz: ICE connection failed');
                    }
                };
                
                // Log connection state
                pc.onconnectionstatechange = () => {
                    console.log('Arrowz: Connection state:', pc.connectionState);
                };
            });
            
            // Also check if connection already exists (for late setup)
            if (this.session.connection) {
                console.log('Arrowz: Connection already exists, attaching handlers directly');
                const pc = this.session.connection;
                
                // ICE candidate logging
                pc.onicecandidate = (event) => {
                    if (event.candidate) {
                        console.log('Arrowz: ICE candidate (direct):', event.candidate.type);
                    }
                };
                
                // ICE connection state
                pc.oniceconnectionstatechange = () => {
                    console.log('Arrowz: ICE connection state (direct):', pc.iceConnectionState);
                };
                
                pc.ontrack = (event) => {
                    console.log('Arrowz: Remote track received (direct), kind:', event.track.kind);
                    if (event.streams && event.streams[0]) {
                        this.remoteStream = event.streams[0];
                        this.audioPlayer.srcObject = event.streams[0];
                        this.playRemoteAudio();
                    }
                };
                
                pc.onaddstream = (event) => {
                    console.log('Arrowz: Remote stream added (direct legacy)');
                    this.remoteStream = event.stream;
                    this.audioPlayer.srcObject = event.stream;
                    this.playRemoteAudio();
                };
                
                // Check if tracks already exist
                const receivers = pc.getReceivers();
                if (receivers.length > 0) {
                    console.log('Arrowz: Tracks already exist:', receivers.length);
                    receivers.forEach(receiver => {
                        if (receiver.track && receiver.track.kind === 'audio') {
                            const stream = new MediaStream([receiver.track]);
                            this.remoteStream = stream;
                            this.audioPlayer.srcObject = stream;
                            this.playRemoteAudio();
                        }
                    });
                }
            }
        },
        
        // Play remote audio with proper error handling and debouncing
        playRemoteAudio() {
            if (!this.audioPlayer.srcObject) {
                console.log('Arrowz: No srcObject to play');
                return;
            }
            
            // Debounce - don't play if we just played
            if (this._lastPlayAttempt && (Date.now() - this._lastPlayAttempt) < 500) {
                console.log('Arrowz: Debouncing audio play');
                return;
            }
            this._lastPlayAttempt = Date.now();
            
            console.log('Arrowz: Attempting to play remote audio');
            
            // Make sure volume is up
            this.audioPlayer.volume = 1.0;
            this.audioPlayer.muted = false;
            
            // Small delay to let the stream settle
            setTimeout(() => {
                const playPromise = this.audioPlayer.play();
                if (playPromise !== undefined) {
                    playPromise.then(() => {
                        console.log('Arrowz: Remote audio playing successfully');
                    }).catch(error => {
                        console.error('Arrowz: Failed to play remote audio:', error.name);
                        // Don't retry immediately if it's an abort error
                        if (error.name !== 'AbortError') {
                            setTimeout(() => {
                                this.audioPlayer.play().catch(e => 
                                    console.log('Arrowz: Retry play failed:', e.name)
                                );
                            }, 200);
                        }
                    });
                }
            }, 100);
        },
        
        // Hang up current call
        hangup() {
            console.log('Arrowz: hangup() called, session:', this.session ? 'exists' : 'null');
            
            if (this.session) {
                try {
                    console.log('Arrowz: Terminating session...');
                    this.session.terminate();
                    console.log('Arrowz: Session terminated');
                } catch (error) {
                    console.error('Arrowz: Error terminating session:', error);
                    // Force cleanup even if terminate fails
                    this.endCall('Error');
                }
            } else {
                console.log('Arrowz: No active session to hangup');
                // Still cleanup UI
                this.endCall();
            }
            
            // Close any browser notification
            if (this.currentNotification) {
                this.currentNotification.close();
                this.currentNotification = null;
            }
        },
        
        // Toggle mute
        toggleMute() {
            if (!this.session) return;
            
            if (this.session.isMuted().audio) {
                this.session.unmute({ audio: true });
            } else {
                this.session.mute({ audio: true });
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
        
        // Send DTMF
        sendDTMF(digit) {
            if (this.session) {
                this.session.sendDTMF(digit);
            }
        },
        
        // Transfer call
        transfer(target) {
            if (!this.session) return;
            
            // Blind transfer
            this.session.refer(target);
        },
        
        // End call cleanup
        endCall(reason) {
            this.stopCallTimer();
            this.stopRingtone();
            
            if (this.localStream) {
                this.localStream.getTracks().forEach(track => track.stop());
                this.localStream = null;
            }
            
            this.session = null;
            this.callStartTime = null;
            
            // Reset to dialer view
            this.resetToDialer();
            this.updateStatus('registered');
            
            if (this.incomingDialog) {
                this.incomingDialog.hide();
            }
            
            if (reason) {
                frappe.show_alert({
                    message: __('Call ended: {0}', [reason]),
                    indicator: 'orange'
                }, 3);
            }
        },
        
        // Play ringtone with iOS support
        playRingtone() {
            try {
                this.ringtone.currentTime = 0;
                const playPromise = this.ringtone.play();
                
                if (playPromise !== undefined) {
                    playPromise.catch((error) => {
                        console.log('Arrowz: Ringtone autoplay blocked:', error.message);
                        // On iOS/Safari, we may need to show a notification instead
                        if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
                            // Use vibration API if available
                            if (navigator.vibrate) {
                                navigator.vibrate([200, 100, 200, 100, 200]);
                            }
                            // Show visual notification
                            frappe.show_alert({
                                message: __('📞 Incoming call!'),
                                indicator: 'green'
                            }, 10);
                        }
                    });
                }
            } catch (e) {
                console.log('Arrowz: Ringtone error:', e);
            }
        },
        
        // Stop ringtone
        stopRingtone() {
            try {
                this.ringtone.pause();
                this.ringtone.currentTime = 0;
            } catch (e) {}
        },
        
        // Start call timer
        startCallTimer() {
            this.callTimer = setInterval(() => {
                if (this.callStartTime) {
                    const elapsed = Math.floor((new Date() - this.callStartTime) / 1000);
                    this.updateCallDuration(elapsed);
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
        
        // Format duration
        formatDuration(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}:${String(secs).padStart(2, '0')}`;
        },
        
        // Render navbar widget
        renderNavbarWidget() {
            // Try different navbar selectors for compatibility
            const navbarSelectors = [
                '.navbar-right',
                '.navbar-nav.navbar-right',
                '#navbar-user',
                '.navbar .dropdown-navbar-user',
                '.standard-actions',
                'header .container-fluid nav'
            ];
            
            let navbar = null;
            for (const selector of navbarSelectors) {
                navbar = document.querySelector(selector);
                if (navbar) break;
            }
            
            if (!navbar) {
                // Fallback: try to find any suitable navbar location
                navbar = document.querySelector('.navbar-collapse') || 
                         document.querySelector('.navbar');
                if (!navbar) {
                    console.warn('Arrowz: Could not find navbar for widget');
                    return;
                }
            }
            
            // Check if widget already exists
            if (document.getElementById('arrowz-navbar-widget')) return;
            
            const widget = document.createElement('li');
            widget.id = 'arrowz-navbar-widget';
            widget.className = 'nav-item arrowz-phone-widget';
            widget.innerHTML = `
                <a class="nav-link arrowz-phone-btn" href="#" onclick="arrowz.softphone.show(); return false;" title="${__('Softphone')}">
                    <span class="phone-icon">📞</span>
                    <span class="status-dot disconnected"></span>
                    <span class="status-text"></span>
                </a>
            `;
            
            // Insert at appropriate location
            if (navbar.firstChild) {
                navbar.insertBefore(widget, navbar.firstChild);
            } else {
                navbar.appendChild(widget);
            }
            
            // Add styles
            this.addStyles();
            
            console.log('Arrowz: Navbar widget added');
        },
        
        // Update status indicator
        updateStatus(status) {
            const widget = document.querySelector('.arrowz-phone-widget');
            const dot = document.querySelector('.arrowz-phone-widget .status-dot');
            const text = document.querySelector('.arrowz-phone-widget .status-text');
            
            if (dot) {
                dot.className = `status-dot ${status}`;
            }
            
            if (text) {
                const statusTexts = {
                    'disconnected': '',
                    'connecting': '...',
                    'registered': '✓',
                    'failed': '✗',
                    'no-config': '⚙',
                    'error': '!'
                };
                text.textContent = statusTexts[status] || '';
            }
            
            if (widget) {
                widget.setAttribute('data-status', status);
            }
        },
        
        // Update call status
        updateCallStatus(status) {
            // Update the old class-based element if exists
            const statusEl = document.querySelector('.arrowz-call-status');
            if (statusEl) {
                statusEl.textContent = status;
                statusEl.className = `arrowz-call-status ${status}`;
            }
            
            // Update the new call status text in dialog
            const statusText = this.dialog?.$wrapper.find('.call-status-text');
            if (statusText && statusText.length) {
                const statusMessages = {
                    'calling': __('Calling...'),
                    'ringing': __('Ringing...'),
                    'connected': __('Connected'),
                    'hold': __('On Hold'),
                    'ended': __('Call Ended')
                };
                statusText.text(statusMessages[status] || status);
                statusText.removeClass('calling ringing connected hold ended').addClass(status);
            }
            
            // Update navbar status indicator
            if (status === 'connected' || status === 'ringing' || status === 'calling') {
                this.updateStatus('on-call');
            }
        },
        
        // Update call duration display
        updateCallDuration(seconds) {
            const durationEl = document.querySelector('.arrowz-call-duration');
            if (durationEl) {
                durationEl.textContent = this.formatDuration(seconds);
            }
        },
        
        // Update mute status
        updateMuteStatus(muted) {
            const muteBtn = document.querySelector('.arrowz-mute-btn');
            if (muteBtn) {
                muteBtn.classList.toggle('active', muted);
            }
        },
        
        // Show softphone dialog
        show() {
            if (this.dialog) {
                this.dialog.show();
                // Re-setup events in case dialog was hidden/shown
                setTimeout(() => this.setupDialerEvents(), 100);
                return;
            }
            
            this.dialog = new frappe.ui.Dialog({
                title: __('Softphone'),
                size: 'small',
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'softphone_html',
                        options: this.getSoftphoneHTML()
                    }
                ]
            });
            
            this.dialog.show();
            // Wait for DOM to be ready before setting up events
            setTimeout(() => this.setupDialerEvents(), 100);
        },
        
        // Get softphone HTML
        getSoftphoneHTML() {
            const status = this.registered ? 'registered' : 'disconnected';
            const extensionInfo = this.config ? 
                `${this.config.extension} (${this.config.extension_display_name || this.config.display_name})` : 
                __('Not configured');
            
            // Build extension selector if user has multiple extensions
            let extensionSelector = '';
            if (this.config && this.config.has_multiple_extensions && this.config.all_extensions) {
                const options = this.config.all_extensions.map(ext => 
                    `<option value="${ext.name}" ${ext.name === this.config.extension_name ? 'selected' : ''}>
                        ${ext.extension} - ${ext.display_name || ext.extension}
                    </option>`
                ).join('');
                
                extensionSelector = `
                    <div class="extension-selector">
                        <label>${__('Call from')}:</label>
                        <select id="arrowz-extension-select" class="form-control form-control-sm">
                            ${options}
                        </select>
                    </div>
                `;
            }
            
            return `
                <div class="arrowz-softphone">
                    <div class="softphone-header">
                        <div class="softphone-status ${status}">
                            <span class="status-indicator"></span>
                            <span class="status-text">${this.registered ? __('Ready') : __('Connecting...')}</span>
                        </div>
                        <div class="extension-info">
                            <i class="fa fa-phone"></i>
                            <span class="extension-number">${extensionInfo}</span>
                        </div>
                    </div>
                    
                    ${extensionSelector}
                    
                    <div class="dial-input-container">
                        <input type="tel" id="arrowz-dial-input" class="form-control" 
                               placeholder="${__('Enter number...')}" autocomplete="off">
                        <button class="btn btn-default backspace-btn" onclick="arrowz.softphone.backspace()">⌫</button>
                    </div>
                    
                    <div class="dial-pad">
                        <button class="dial-key" data-digit="1">1</button>
                        <button class="dial-key" data-digit="2">2<span>ABC</span></button>
                        <button class="dial-key" data-digit="3">3<span>DEF</span></button>
                        <button class="dial-key" data-digit="4">4<span>GHI</span></button>
                        <button class="dial-key" data-digit="5">5<span>JKL</span></button>
                        <button class="dial-key" data-digit="6">6<span>MNO</span></button>
                        <button class="dial-key" data-digit="7">7<span>PQRS</span></button>
                        <button class="dial-key" data-digit="8">8<span>TUV</span></button>
                        <button class="dial-key" data-digit="9">9<span>WXYZ</span></button>
                        <button class="dial-key" data-digit="*">*</button>
                        <button class="dial-key" data-digit="0">0<span>+</span></button>
                        <button class="dial-key" data-digit="#">#</button>
                    </div>
                    
                    <div class="call-actions">
                        <button class="btn btn-success btn-lg call-btn" onclick="arrowz.softphone.dial()">
                            <i class="fa fa-phone"></i>
                        </button>
                    </div>
                    
                    <div class="softphone-footer">
                        <button class="btn btn-default btn-sm softphone-history-btn" onclick="arrowz.softphone.showCallHistory()">
                            <i class="fa fa-history"></i> ${__('Call History')}
                        </button>
                    </div>
                </div>
            `;
        },
        
        // Setup dialer events
        setupDialerEvents() {
            const self = this;
            
            // Use event delegation on the dialog body for better reliability
            const dialogBody = this.dialog.$wrapper.find('.modal-body')[0];
            if (!dialogBody) {
                console.log('Arrowz: Dialog body not found, retrying...');
                setTimeout(() => this.setupDialerEvents(), 200);
                return;
            }
            
            // Remove existing listeners to avoid duplicates
            const keys = dialogBody.querySelectorAll('.dial-key');
            console.log('Arrowz: Setting up keypad with', keys.length, 'keys');
            
            keys.forEach(key => {
                // Clone to remove existing listeners
                const newKey = key.cloneNode(true);
                key.parentNode.replaceChild(newKey, key);
                
                newKey.addEventListener('click', function(e) {
                    e.preventDefault();
                    const digit = this.dataset.digit;
                    console.log('Arrowz: Key pressed:', digit);
                    self.pressKey(digit);
                });
            });
            
            // Keyboard support
            const input = document.getElementById('arrowz-dial-input');
            if (input) {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.dial();
                    }
                });
            }
            
            // Extension selector change event
            const extensionSelect = document.getElementById('arrowz-extension-select');
            if (extensionSelect) {
                extensionSelect.addEventListener('change', async (e) => {
                    const selectedExtension = e.target.value;
                    console.log('Arrowz: Switching to extension:', selectedExtension);
                    await this.switchExtension(selectedExtension);
                });
            }
        },
        
        // Switch to a different extension
        async switchExtension(extensionName) {
            try {
                // Disconnect current UA
                if (this.ua) {
                    this.ua.stop();
                }
                
                // Get new config for selected extension
                const r = await frappe.call({
                    method: 'arrowz.api.webrtc.get_webrtc_config',
                    args: { extension_name: extensionName }
                });
                
                if (r.message) {
                    this.config = r.message;
                    await this.setupJsSIP();
                    
                    // Update extension info display
                    const extInfo = this.dialog.$wrapper.find('.extension-number');
                    if (extInfo.length) {
                        extInfo.text(`${this.config.extension} (${this.config.extension_display_name || this.config.display_name})`);
                    }
                    
                    frappe.show_alert({
                        message: __('Switched to extension {0}', [this.config.extension]),
                        indicator: 'green'
                    });
                }
            } catch (error) {
                console.error('Arrowz: Error switching extension:', error);
                frappe.show_alert({
                    message: __('Failed to switch extension'),
                    indicator: 'red'
                });
            }
        },
        
        // Press dial key
        pressKey(digit) {
            const input = document.getElementById('arrowz-dial-input');
            if (input) {
                input.value += digit;
                // Focus the input so user can see the change
                input.focus();
            }
            
            // If in call, send DTMF
            if (this.session) {
                this.sendDTMF(digit);
            }
        },
        
        // Backspace
        backspace() {
            const input = document.getElementById('arrowz-dial-input');
            if (input) {
                input.value = input.value.slice(0, -1);
            }
        },
        
        // Dial number
        dial() {
            const input = document.getElementById('arrowz-dial-input');
            const number = input ? input.value.trim() : '';
            
            console.log('Arrowz: dial() called with number:', number);
            console.log('Arrowz: registered:', this.registered, 'session:', this.session);
            
            if (!number) {
                frappe.show_alert({
                    message: __('Please enter a number'),
                    indicator: 'yellow'
                });
                return;
            }
            
            if (!this.registered) {
                frappe.show_alert({
                    message: __('Softphone not registered. Please wait...'),
                    indicator: 'red'
                });
                return;
            }
            
            // Show UI first, then make call
            this.showActiveCallUI(number);
            this.makeCall(number);
        },
        
        // Show Active Call UI
        showActiveCallUI(number) {
            if (!this.dialog) return;
            
            const $body = this.dialog.$wrapper.find('.modal-body');
            $body.html(`
                <div class="arrowz-active-call">
                    <div class="call-status-header">
                        <div class="call-avatar">📞</div>
                        <div class="call-info">
                            <div class="call-number">${number}</div>
                            <div class="call-status-text">${__('Calling...')}</div>
                            <div class="call-timer" id="arrowz-call-timer">00:00</div>
                        </div>
                    </div>
                    
                    <div class="call-actions-grid">
                        <button class="call-action-btn" onclick="arrowz.softphone.toggleMute()" id="mute-btn">
                            <span class="action-icon">🔇</span>
                            <span class="action-label">${__('Mute')}</span>
                        </button>
                        <button class="call-action-btn" onclick="arrowz.softphone.toggleHold()" id="hold-btn">
                            <span class="action-icon">⏸️</span>
                            <span class="action-label">${__('Hold')}</span>
                        </button>
                        <button class="call-action-btn" onclick="arrowz.softphone.showDTMFPad()">
                            <span class="action-icon">🔢</span>
                            <span class="action-label">${__('Keypad')}</span>
                        </button>
                    </div>
                    
                    <div class="dtmf-pad" id="dtmf-pad" style="display: none;">
                        <div class="dial-pad">
                            <button class="dial-key" onclick="arrowz.softphone.sendDTMF('1')">1</button>
                            <button class="dial-key" onclick="arrowz.softphone.sendDTMF('2')">2</button>
                            <button class="dial-key" onclick="arrowz.softphone.sendDTMF('3')">3</button>
                            <button class="dial-key" onclick="arrowz.softphone.sendDTMF('4')">4</button>
                            <button class="dial-key" onclick="arrowz.softphone.sendDTMF('5')">5</button>
                            <button class="dial-key" onclick="arrowz.softphone.sendDTMF('6')">6</button>
                            <button class="dial-key" onclick="arrowz.softphone.sendDTMF('7')">7</button>
                            <button class="dial-key" onclick="arrowz.softphone.sendDTMF('8')">8</button>
                            <button class="dial-key" onclick="arrowz.softphone.sendDTMF('9')">9</button>
                            <button class="dial-key" onclick="arrowz.softphone.sendDTMF('*')">*</button>
                            <button class="dial-key" onclick="arrowz.softphone.sendDTMF('0')">0</button>
                            <button class="dial-key" onclick="arrowz.softphone.sendDTMF('#')">#</button>
                        </div>
                    </div>
                    
                    <div class="hangup-section">
                        <button class="btn btn-danger btn-lg hangup-btn" onclick="arrowz.softphone.hangup()">
                            <i class="fa fa-phone" style="transform: rotate(135deg);"></i>
                            ${__('End Call')}
                        </button>
                    </div>
                </div>
            `);
            
            this.dialog.set_title(__('On Call'));
        },
        
        // Show DTMF Pad
        showDTMFPad() {
            const pad = document.getElementById('dtmf-pad');
            if (pad) {
                pad.style.display = pad.style.display === 'none' ? 'block' : 'none';
            }
        },
        
        // Update call status text
        updateCallStatusText(text) {
            const statusEl = this.dialog?.$wrapper.find('.call-status-text');
            if (statusEl && statusEl.length) {
                statusEl.text(text);
            }
        },
        
        // Start call timer
        startCallTimer() {
            this.callStartTime = new Date();
            this.callTimer = setInterval(() => {
                const elapsed = Math.floor((new Date() - this.callStartTime) / 1000);
                const mins = Math.floor(elapsed / 60);
                const secs = elapsed % 60;
                const timerEl = document.getElementById('arrowz-call-timer');
                if (timerEl) {
                    timerEl.textContent = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
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
        
        // Reset to dialer after call ends
        resetToDialer() {
            this.stopCallTimer();
            if (this.dialog) {
                this.dialog.set_title(__('Softphone'));
                const $body = this.dialog.$wrapper.find('.modal-body');
                // Update the softphone_html field content
                const $control = $body.find('.frappe-control[data-fieldname="softphone_html"]');
                if ($control.length) {
                    $control.html(this.getSoftphoneHTML());
                } else {
                    // Fallback: replace entire body content
                    $body.html(`<div class="frappe-control" data-fieldname="softphone_html">${this.getSoftphoneHTML()}</div>`);
                }
                setTimeout(() => this.setupDialerEvents(), 100);
            }
        },
        
        // Show call widget
        showCallWidget(number) {
            // Update navbar status
            this.updateStatus('on-call');
            
            // Show or create dialog with active call UI
            if (!this.dialog) {
                // Create dialog if not exists
                this.dialog = new frappe.ui.Dialog({
                    title: __('On Call'),
                    size: 'small',
                    fields: [
                        {
                            fieldtype: 'HTML',
                            fieldname: 'softphone_html',
                            options: ''  // Will be set below
                        }
                    ]
                });
            }
            
            // Update to active call UI
            this.showActiveCallUI(number);
            this.dialog.set_title(__('On Call'));
            this.dialog.show();
        },
        
        // Hide call widget
        hideCallWidget() {
            // Cleanup call UI
        },
        
        // Add styles
        addStyles() {
            if (document.getElementById('arrowz-softphone-styles')) return;
            
            const style = document.createElement('style');
            style.id = 'arrowz-softphone-styles';
            style.textContent = `
                .arrowz-phone-widget {
                    position: relative;
                    margin-right: 10px;
                }
                
                .arrowz-phone-btn {
                    display: flex !important;
                    align-items: center;
                    gap: 6px;
                    padding: 6px 12px !important;
                    border-radius: 20px;
                    background: var(--fg-color);
                    transition: all 0.2s;
                }
                
                .arrowz-phone-btn:hover {
                    background: var(--bg-dark-gray);
                    text-decoration: none;
                }
                
                .phone-icon {
                    font-size: 16px;
                }
                
                .status-dot {
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    display: inline-block;
                    border: 2px solid var(--fg-color);
                    transition: background 0.3s;
                }
                
                .status-dot.disconnected { background: #9e9e9e; }
                .status-dot.connecting { background: #ff9800; animation: blink 1s infinite; }
                .status-dot.registered { background: #4CAF50; }
                .status-dot.failed { background: #f44336; }
                .status-dot.no-config { background: #2196F3; }
                .status-dot.error { background: #f44336; }
                .status-dot.on-call { background: #4CAF50; animation: pulse-call 1s infinite; }
                
                @keyframes blink {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.4; }
                }
                
                @keyframes pulse-call {
                    0%, 100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.7); }
                    50% { box-shadow: 0 0 0 6px rgba(76, 175, 80, 0); }
                }
                
                .status-text {
                    font-size: 12px;
                    font-weight: 500;
                }
                
                .arrowz-phone-widget[data-status="registered"] .arrowz-phone-btn {
                    background: rgba(76, 175, 80, 0.1);
                }
                
                .arrowz-phone-widget[data-status="on-call"] .arrowz-phone-btn {
                    background: rgba(76, 175, 80, 0.2);
                }
                
                .arrowz-softphone {
                    padding: 10px;
                }
                
                .softphone-header {
                    margin-bottom: 16px;
                }
                
                .softphone-status {
                    text-align: center;
                    padding: 8px;
                    border-radius: 8px;
                    background: var(--bg-color);
                }
                
                .extension-info {
                    text-align: center;
                    padding: 8px;
                    margin-top: 8px;
                    font-size: 14px;
                    color: var(--text-muted);
                    background: var(--bg-light-gray);
                    border-radius: 6px;
                }
                
                .extension-info i {
                    margin-right: 6px;
                    color: var(--primary);
                }
                
                .extension-info .extension-number {
                    font-weight: 500;
                    color: var(--text-color);
                }
                
                .extension-selector {
                    margin-bottom: 16px;
                    padding: 10px;
                    background: var(--bg-light-gray);
                    border-radius: 8px;
                }
                
                .extension-selector label {
                    display: block;
                    font-size: 12px;
                    font-weight: 500;
                    color: var(--text-muted);
                    margin-bottom: 6px;
                }
                
                .extension-selector select {
                    width: 100%;
                }
                
                .softphone-status.registered {
                    border-left: 3px solid #4CAF50;
                }
                
                .softphone-status .status-indicator {
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #999;
                    margin-right: 8px;
                }
                
                .softphone-status.registered .status-indicator {
                    background: #4CAF50;
                }
                
                .dial-input-container {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 16px;
                }
                
                .dial-input-container input {
                    flex: 1;
                    font-size: 18px;
                    text-align: center;
                    letter-spacing: 2px;
                }
                
                .backspace-btn {
                    padding: 8px 12px;
                }
                
                .dial-pad {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 8px;
                    margin-bottom: 16px;
                }
                
                .dial-key {
                    aspect-ratio: 1;
                    border: 1px solid var(--border-color);
                    border-radius: 50%;
                    background: var(--fg-color);
                    font-size: 22px;
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.1s;
                }
                
                .dial-key:hover {
                    background: var(--bg-color);
                }
                
                .dial-key:active {
                    transform: scale(0.95);
                }
                
                .dial-key span {
                    font-size: 9px;
                    letter-spacing: 1px;
                    color: var(--text-muted);
                }
                
                .call-actions {
                    text-align: center;
                }
                
                .call-btn {
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    font-size: 24px;
                }
                
                .arrowz-incoming-dialog .modal-dialog {
                    animation: shake 0.5s infinite;
                }
                
                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    25% { transform: translateX(-5px); }
                    75% { transform: translateX(5px); }
                }
                
                .incoming-call-alert {
                    padding: 20px;
                }
                
                .incoming-call-alert .caller-avatar {
                    font-size: 64px;
                    animation: pulse 1s infinite;
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.7; }
                }
                
                .caller-id {
                    margin: 16px 0 8px;
                }
            `;
            
            document.head.appendChild(style);
        },
        
        // Show Call History Dialog
        showCallHistory() {
            // Close softphone dialog if open
            if (this.dialog) {
                this.dialog.hide();
            }
            
            // Build extensions filter options
            let extensionOptions = '<option value="">' + __('All Extensions') + '</option>';
            if (this.config && this.config.all_extensions) {
                this.config.all_extensions.forEach(ext => {
                    extensionOptions += `<option value="${ext.extension}">${ext.extension} - ${ext.display_name || ext.extension}</option>`;
                });
            } else if (this.config && this.config.extension) {
                extensionOptions += `<option value="${this.config.extension}">${this.config.extension}</option>`;
            }
            
            const historyDialog = new frappe.ui.Dialog({
                title: __('Call History'),
                size: 'large',
                fields: [
                    {
                        fieldtype: 'HTML',
                        fieldname: 'call_history_html',
                        options: `
                            <div class="call-history-container">
                                <div class="call-history-filters">
                                    <select id="history-extension-filter" class="form-control form-control-sm" style="width: 180px;">
                                        ${extensionOptions}
                                    </select>
                                    <select id="history-type-filter" class="form-control form-control-sm" style="width: 150px;">
                                        <option value="">${__('All Types')}</option>
                                        <option value="outbound">${__('Outgoing')}</option>
                                        <option value="inbound">${__('Incoming')}</option>
                                        <option value="missed">${__('Missed')}</option>
                                    </select>
                                    <select id="history-date-filter" class="form-control form-control-sm" style="width: 150px;">
                                        <option value="today">${__('Today')}</option>
                                        <option value="week">${__('This Week')}</option>
                                        <option value="month">${__('This Month')}</option>
                                        <option value="all">${__('All Time')}</option>
                                    </select>
                                    <button class="btn btn-primary btn-sm" onclick="arrowz.softphone.loadCallHistory()">
                                        <i class="fa fa-refresh"></i> ${__('Refresh')}
                                    </button>
                                </div>
                                <div class="call-history-list" id="call-history-list">
                                    <div class="text-center text-muted py-4">
                                        <i class="fa fa-spinner fa-spin"></i> ${__('Loading...')}
                                    </div>
                                </div>
                            </div>
                        `
                    }
                ]
            });
            
            this.historyDialog = historyDialog;
            historyDialog.show();
            
            // Setup filter change events
            setTimeout(() => {
                $('#history-extension-filter, #history-type-filter, #history-date-filter').on('change', () => {
                    this.loadCallHistory();
                });
                this.loadCallHistory();
            }, 100);
        },
        
        // Load call history based on filters
        async loadCallHistory() {
            const extensionFilter = $('#history-extension-filter').val();
            const typeFilter = $('#history-type-filter').val();
            const dateFilter = $('#history-date-filter').val() || 'today';
            
            const $list = $('#call-history-list');
            $list.html(`
                <div class="text-center text-muted py-4">
                    <i class="fa fa-spinner fa-spin"></i> ${__('Loading...')}
                </div>
            `);
            
            try {
                const r = await frappe.call({
                    method: 'arrowz.api.call_log.get_call_history',
                    args: {
                        extension: extensionFilter,
                        call_type: typeFilter,
                        date_range: dateFilter,
                        limit: 50
                    }
                });
                
                const calls = r.message || [];
                
                if (calls.length === 0) {
                    $list.html(`
                        <div class="text-center text-muted py-4">
                            <i class="fa fa-phone-slash" style="font-size: 48px; opacity: 0.5;"></i>
                            <p class="mt-3">${__('No calls found')}</p>
                        </div>
                    `);
                    return;
                }
                
                let html = '';
                calls.forEach(call => {
                    const icon = this.getCallIcon(call.direction, call.status);
                    const iconClass = call.status === 'missed' ? 'missed' : (call.direction === 'inbound' ? 'incoming' : 'outgoing');
                    const duration = call.duration ? this.formatDuration(call.duration) : '-';
                    const time = frappe.datetime.prettyDate(call.call_datetime);
                    
                    html += `
                        <div class="call-history-item">
                            <div class="call-history-icon ${iconClass}">${icon}</div>
                            <div class="call-history-details">
                                <div class="call-history-number">
                                    ${call.caller_id || call.phone_number || __('Unknown')}
                                    ${call.contact_name ? `<span class="text-muted ml-2">(${call.contact_name})</span>` : ''}
                                </div>
                                <div class="call-history-time">
                                    <span>${time}</span>
                                    <span class="mx-2">•</span>
                                    <span>${call.extension || ''}</span>
                                </div>
                            </div>
                            <div class="call-history-duration">
                                ${duration}
                            </div>
                            <div class="call-history-actions">
                                <button class="btn btn-xs btn-success" onclick="arrowz.softphone.callFromHistory('${call.phone_number || call.caller_id}')" title="${__('Call')}">
                                    <i class="fa fa-phone"></i>
                                </button>
                            </div>
                        </div>
                    `;
                });
                
                $list.html(html);
                
            } catch (error) {
                console.error('Error loading call history:', error);
                $list.html(`
                    <div class="text-center text-danger py-4">
                        <i class="fa fa-exclamation-circle"></i> ${__('Error loading call history')}
                    </div>
                `);
            }
        },
        
        // Get call icon based on direction and status
        getCallIcon(direction, status) {
            if (status === 'missed') return '📵';
            if (direction === 'inbound') return '📲';
            return '📱';
        },
        
        // Format duration from seconds
        formatDuration(seconds) {
            if (!seconds || seconds <= 0) return '0:00';
            
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${String(secs).padStart(2, '0')}`;
        },
        
        // Call from history
        callFromHistory(number) {
            if (!number) return;
            
            // Close history dialog
            if (this.historyDialog) {
                this.historyDialog.hide();
            }
            
            // Make the call
            this.makeCall(number);
        }
    };
    
    // Initialize on page load
    $(document).ready(function() {
        // Only init if user is logged in
        if (frappe.session.user !== 'Guest') {
            setTimeout(() => {
                arrowz.softphone.init();
            }, 1000);
        }
    });
    
})();
