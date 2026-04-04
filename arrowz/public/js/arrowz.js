// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Arrowz Main JavaScript
 * Core utilities and integrations
 */

(function() {
    'use strict';
    
    // Arrowz namespace
    window.arrowz = window.arrowz || {};

    // Centralized debug logger — silent in production
    arrowz.debug = {
        _enabled: (window.dev_server || frappe?.boot?.developer_mode) ? true : false,
        log: function() { if (this._enabled) console.log('[Arrowz]', ...arguments); },
        warn: function() { if (this._enabled) console.warn('[Arrowz]', ...arguments); },
        error: function() { console.error('[Arrowz]', ...arguments); }, // always show errors
        info: function() { if (this._enabled) console.info('[Arrowz]', ...arguments); },
    };
    
    // Utilities
    arrowz.utils = {
        // Format phone number
        formatPhone(number) {
            if (!number) return '';
            
            // Remove non-digits
            const digits = number.replace(/\D/g, '');
            
            // Format based on length
            if (digits.length === 10) {
                return `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`;
            } else if (digits.length === 11 && digits[0] === '1') {
                return `+1 (${digits.slice(1,4)}) ${digits.slice(4,7)}-${digits.slice(7)}`;
            }
            
            return number;
        },
        
        // Format duration
        formatDuration(seconds) {
            if (!seconds || seconds <= 0) return '0:00';
            
            const hours = Math.floor(seconds / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            
            if (hours > 0) {
                return `${hours}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
            }
            return `${mins}:${String(secs).padStart(2, '0')}`;
        },
        
        // Play notification sound
        playSound(type) {
            const sounds = {
                'ring': '/assets/arrowz/sounds/ringtone.mp3',
                'message': '/assets/arrowz/sounds/message.mp3',
                'notification': '/assets/arrowz/sounds/notification.mp3'
            };
            
            const src = sounds[type];
            if (src) {
                const audio = new Audio(src);
                audio.play().catch(() => {});
            }
        },
        
        // Show browser notification
        showNotification(title, options = {}) {
            if (!("Notification" in window)) return;
            
            if (Notification.permission === "granted") {
                new Notification(title, {
                    icon: '/assets/arrowz/images/arrowz-icon-animated.svg',
                    ...options
                });
            } else if (Notification.permission !== "denied") {
                Notification.requestPermission().then(permission => {
                    if (permission === "granted") {
                        new Notification(title, options);
                    }
                });
            }
        }
    };
    
    // Call functions (global shortcuts)
    arrowz.call = {
        // Make a call to a number
        dial(number) {
            if (arrowz.softphone && arrowz.softphone.registered) {
                arrowz.softphone.makeCall(number);
            } else {
                frappe.show_alert({
                    message: __('Softphone not ready'),
                    indicator: 'yellow'
                });
            }
        },
        
        // Show call history for a number
        showHistory(number) {
            frappe.set_route('List', 'AZ Call Log', {
                caller_id: ['like', `%${number}%`]
            });
        },
        
        // Quick dial from doctype
        fromDoc(doctype, docname, field) {
            frappe.db.get_value(doctype, docname, field).then(r => {
                if (r.message && r.message[field]) {
                    arrowz.call.dial(r.message[field]);
                }
            });
        }
    };
    
    // SMS functions
    arrowz.sms = {
        // Send SMS dialog
        showSendDialog(to_number, party_type, party) {
            const dialog = new frappe.ui.Dialog({
                title: __('Send SMS'),
                fields: [
                    {
                        fieldname: 'to_number',
                        label: __('To'),
                        fieldtype: 'Data',
                        default: to_number || '',
                        reqd: 1
                    },
                    {
                        fieldname: 'message',
                        label: __('Message'),
                        fieldtype: 'Text',
                        reqd: 1,
                        max_length: 160
                    },
                    {
                        fieldname: 'char_count',
                        fieldtype: 'HTML',
                        options: '<div class="text-muted small">0 / 160 characters</div>'
                    }
                ],
                primary_action_label: __('Send'),
                primary_action: (values) => {
                    frappe.call({
                        method: 'arrowz.api.sms.send_sms',
                        args: {
                            to_number: values.to_number,
                            message: values.message,
                            party_type: party_type,
                            party: party
                        },
                        callback: (r) => {
                            if (r.message && r.message.status === 'sent') {
                                frappe.show_alert({
                                    message: __('SMS sent successfully'),
                                    indicator: 'green'
                                });
                                dialog.hide();
                            }
                        }
                    });
                }
            });
            
            // Character counter
            dialog.fields_dict.message.$input.on('input', function() {
                const len = $(this).val().length;
                dialog.fields_dict.char_count.$wrapper.html(
                    `<div class="text-muted small ${len > 160 ? 'text-danger' : ''}">${len} / 160 characters</div>`
                );
            });
            
            dialog.show();
        },
        
        // Show SMS history
        showHistory(phone_number) {
            frappe.set_route('List', 'AZ SMS Message', {
                phone_number: ['like', `%${phone_number}%`]
            });
        }
    };
    
    // Real-time event handlers
    arrowz.realtime = {
        init() {
            // Incoming call
            frappe.realtime.on('incoming_call', (data) => {
                arrowz.utils.showNotification(__('Incoming Call'), {
                    body: data.caller_id || __('Unknown Caller'),
                    tag: 'arrowz-call'
                });
            });
            
            // SMS received
            frappe.realtime.on('sms_received', (data) => {
                arrowz.utils.playSound('message');
                arrowz.utils.showNotification(__('New SMS'), {
                    body: `${data.from}: ${data.content || ''}`.substring(0, 100),
                    tag: 'arrowz-sms'
                });
            });
            
            // Call ended
            frappe.realtime.on('call_ended', (data) => {
                frappe.show_alert({
                    message: __('Call ended'),
                    indicator: 'blue'
                }, 3);
            });
        }
    };
    
    // Form integrations
    arrowz.forms = {
        // Add phone action buttons to forms
        addPhoneActions(frm, phone_field) {
            if (!frm.doc[phone_field]) return;
            
            const number = frm.doc[phone_field];
            
            // Add call button
            frm.add_custom_button(`📞 ${__('Call')}`, () => {
                arrowz.call.dial(number);
            }, __('Actions'));
            
            // Add SMS button
            frm.add_custom_button(`💬 ${__('SMS')}`, () => {
                arrowz.sms.showSendDialog(number, frm.doctype, frm.doc.name);
            }, __('Actions'));
            
            // Add history button
            frm.add_custom_button(`📋 ${__('Call History')}`, () => {
                arrowz.call.showHistory(number);
            }, __('Actions'));
        },
        
        // Add click-to-call to phone fields
        enableClickToCall(frm, phone_fields) {
            phone_fields.forEach(field => {
                const control = frm.fields_dict[field];
                if (control && control.$input) {
                    control.$input.css('cursor', 'pointer');
                    control.$input.attr('title', __('Click to call'));
                    
                    // Add phone icon
                    control.$wrapper.find('.control-input').append(`
                        <span class="arrowz-call-icon" onclick="arrowz.call.dial('${frm.doc[field] || ''}')">
                            📞
                        </span>
                    `);
                }
            });
        }
    };
    
    // Click to Call - Override phone link behavior
    arrowz.clickToCall = {
        init() {
            // Override default phone field click behavior
            $(document).on('click', '[data-fieldtype="Phone"] .like-disabled-input, [data-fieldtype="Phone"] .control-value, a[href^="tel:"]', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                let number = '';
                
                // Get number from tel: link
                if ($(this).is('a[href^="tel:"]')) {
                    number = $(this).attr('href').replace('tel:', '');
                } else {
                    // Get from field value
                    number = $(this).text().trim() || $(this).val();
                }
                
                if (number) {
                    arrowz.clickToCall.showCallOptions(number, e);
                }
            });
            
            // Override frappe's phone filter click in list views
            $(document).on('click', '.filterable[data-filter*="phone"], .filterable[data-filter*="mobile"], .filterable[data-filter*="Phone"], .filterable[data-filter*="Mobile"]', function(e) {
                // Check if it looks like a phone number
                const text = $(this).text().trim();
                if (arrowz.clickToCall.isPhoneNumber(text)) {
                    e.preventDefault();
                    e.stopPropagation();
                    arrowz.clickToCall.showCallOptions(text, e);
                }
            });
            
            // Add click handler to phone-like text in read-only mode
            $(document).on('click', '.frappe-control[data-fieldtype="Phone"] .control-value, .frappe-control[data-fieldtype="Phone"] .like-disabled-input', function(e) {
                e.preventDefault();
                e.stopPropagation();
                const number = $(this).text().trim();
                if (number) {
                    arrowz.clickToCall.showCallOptions(number, e);
                }
            });
        },
        
        // Check if string looks like a phone number
        isPhoneNumber(text) {
            if (!text) return false;
            // Remove common formatting
            const digits = text.replace(/[\s\-\(\)\+\.]/g, '');
            // Should be 7-15 digits
            return /^\d{7,15}$/.test(digits);
        },
        
        // Show call options popup
        showCallOptions(number, event) {
            // Clean the number
            const cleanNumber = number.replace(/[^\d\+]/g, '');
            
            // Create popup menu
            const $menu = $(`
                <div class="arrowz-call-menu dropdown-menu" style="display: block; position: fixed; z-index: 9999;">
                    <a class="dropdown-item arrowz-dial-option" data-number="${cleanNumber}">
                        <span style="margin-right: 8px;">📞</span> ${__('Call')} ${number}
                    </a>
                    <a class="dropdown-item arrowz-sms-option" data-number="${cleanNumber}">
                        <span style="margin-right: 8px;">💬</span> ${__('Send SMS')}
                    </a>
                    <a class="dropdown-item arrowz-copy-option" data-number="${cleanNumber}">
                        <span style="margin-right: 8px;">📋</span> ${__('Copy Number')}
                    </a>
                    <div class="dropdown-divider"></div>
                    <a class="dropdown-item arrowz-history-option" data-number="${cleanNumber}">
                        <span style="margin-right: 8px;">📜</span> ${__('Call History')}
                    </a>
                </div>
            `);
            
            // Position the menu
            const x = event.pageX || event.clientX;
            const y = event.pageY || event.clientY;
            $menu.css({
                top: y + 'px',
                left: x + 'px'
            });
            
            // Remove any existing menus
            $('.arrowz-call-menu').remove();
            
            // Add to body
            $('body').append($menu);
            
            // Handle menu item clicks
            $menu.find('.arrowz-dial-option').click(function() {
                const num = $(this).data('number');
                arrowz.call.dial(num);
                $menu.remove();
            });
            
            $menu.find('.arrowz-sms-option').click(function() {
                const num = $(this).data('number');
                arrowz.sms.showSendDialog(num);
                $menu.remove();
            });
            
            $menu.find('.arrowz-copy-option').click(function() {
                const num = $(this).data('number');
                navigator.clipboard.writeText(num).then(() => {
                    frappe.show_alert({message: __('Number copied'), indicator: 'green'}, 2);
                });
                $menu.remove();
            });
            
            $menu.find('.arrowz-history-option').click(function() {
                const num = $(this).data('number');
                arrowz.call.showHistory(num);
                $menu.remove();
            });
            
            // Close menu on click outside
            setTimeout(() => {
                $(document).one('click', function() {
                    $menu.remove();
                });
            }, 100);
        }
    };
    
    // Initialize on ready
    $(document).ready(function() {
        arrowz.realtime.init();
        arrowz.clickToCall.init();
        arrowz.topbar.init();
        
        // Request notification permission
        if (frappe.session.user !== 'Guest' && "Notification" in window) {
            Notification.requestPermission();
        }
        
        console.log('Arrowz: Click to Call enabled');
    });

    // Topbar shortcuts
    arrowz.topbar = {
        initialized: false,
        
        init() {
            if (this.initialized) return;
            if (frappe.session.user === 'Guest') return;
            
            // Wait for navbar to be ready
            setTimeout(() => {
                this.addTopbarShortcuts();
            }, 500);
            
            this.initialized = true;
        },
        
        addTopbarShortcuts() {
            // Find navbar-right or create container
            let $navbarRight = $('.navbar-right, .navbar-nav.ml-auto, .navbar-nav:last');
            
            if (!$navbarRight.length) {
                $navbarRight = $('.navbar .container, .navbar .container-fluid');
            }
            
            if (!$navbarRight.length) return;
            
            // Check if already added
            if ($('#arrowz-topbar-shortcuts').length) return;
            
            // Create shortcuts container
            const $shortcuts = $(`
                <div id="arrowz-topbar-shortcuts" class="arrowz-topbar-shortcuts">
                    <!-- Softphone -->
                    <button class="arrowz-topbar-btn arrowz-softphone-btn" title="${__('Softphone')}" data-action="softphone">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                        </svg>
                        <span class="arrowz-btn-label">${__('Call')}</span>
                    </button>
                    
                    <!-- WhatsApp Chat -->
                    <button class="arrowz-topbar-btn arrowz-whatsapp-btn" title="${__('WhatsApp')}" data-action="whatsapp">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                        </svg>
                        <span class="arrowz-btn-label">${__('WhatsApp')}</span>
                        <span class="arrowz-badge arrowz-whatsapp-badge" style="display:none;">0</span>
                    </button>
                    
                    <!-- Internal Messages -->
                    <button class="arrowz-topbar-btn arrowz-messages-btn" title="${__('Messages')}" data-action="messages">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        </svg>
                        <span class="arrowz-btn-label">${__('Messages')}</span>
                        <span class="arrowz-badge arrowz-messages-badge" style="display:none;">0</span>
                    </button>
                </div>
            `);
            
            // Add styles
            this.addStyles();
            
            // Insert before user menu or at the end
            const $userMenu = $navbarRight.find('.dropdown-user, .avatar-frame, .navbar-user').first().closest('.nav-item, .dropdown');
            if ($userMenu.length) {
                $userMenu.before($shortcuts);
            } else {
                $navbarRight.append($shortcuts);
            }
            
            // Setup click handlers
            this.setupHandlers();
            
            // Load unread counts
            this.loadUnreadCounts();
            
            // Subscribe to realtime updates
            this.subscribeToUpdates();
        },
        
        addStyles() {
            if ($('#arrowz-topbar-styles').length) return;
            
            $('head').append(`
                <style id="arrowz-topbar-styles">
                    .arrowz-topbar-shortcuts {
                        display: flex;
                        align-items: center;
                        gap: 4px;
                        margin-right: 12px;
                    }
                    
                    .arrowz-topbar-btn {
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        padding: 8px 12px;
                        background: rgba(255, 255, 255, 0.1);
                        border: none;
                        border-radius: 8px;
                        color: white;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        position: relative;
                        font-size: 13px;
                        font-weight: 500;
                    }
                    
                    .arrowz-topbar-btn:hover {
                        background: rgba(255, 255, 255, 0.2);
                        transform: translateY(-1px);
                    }
                    
                    .arrowz-topbar-btn:active {
                        transform: translateY(0);
                    }
                    
                    .arrowz-topbar-btn svg {
                        flex-shrink: 0;
                    }
                    
                    .arrowz-btn-label {
                        white-space: nowrap;
                    }
                    
                    /* Softphone button - green accent */
                    .arrowz-softphone-btn {
                        background: linear-gradient(135deg, rgba(67, 233, 123, 0.3) 0%, rgba(56, 249, 215, 0.3) 100%);
                    }
                    
                    .arrowz-softphone-btn:hover {
                        background: linear-gradient(135deg, rgba(67, 233, 123, 0.5) 0%, rgba(56, 249, 215, 0.5) 100%);
                        box-shadow: 0 4px 15px rgba(67, 233, 123, 0.3);
                    }
                    
                    .arrowz-softphone-btn.active,
                    .arrowz-softphone-btn.in-call {
                        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                        animation: pulse-call 1.5s infinite;
                    }
                    
                    @keyframes pulse-call {
                        0%, 100% { box-shadow: 0 0 0 0 rgba(67, 233, 123, 0.5); }
                        50% { box-shadow: 0 0 0 10px rgba(67, 233, 123, 0); }
                    }
                    
                    /* WhatsApp button - green */
                    .arrowz-whatsapp-btn {
                        background: linear-gradient(135deg, rgba(37, 211, 102, 0.3) 0%, rgba(18, 140, 126, 0.3) 100%);
                    }
                    
                    .arrowz-whatsapp-btn:hover {
                        background: linear-gradient(135deg, rgba(37, 211, 102, 0.5) 0%, rgba(18, 140, 126, 0.5) 100%);
                        box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3);
                    }
                    
                    /* Messages button - blue */
                    .arrowz-messages-btn {
                        background: linear-gradient(135deg, rgba(79, 172, 254, 0.3) 0%, rgba(0, 242, 254, 0.3) 100%);
                    }
                    
                    .arrowz-messages-btn:hover {
                        background: linear-gradient(135deg, rgba(79, 172, 254, 0.5) 0%, rgba(0, 242, 254, 0.5) 100%);
                        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
                    }
                    
                    /* Badge */
                    .arrowz-badge {
                        position: absolute;
                        top: -4px;
                        right: -4px;
                        min-width: 18px;
                        height: 18px;
                        background: linear-gradient(135deg, #ff6b6b 0%, #ff4757 100%);
                        color: white;
                        font-size: 10px;
                        font-weight: 700;
                        border-radius: 9px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        padding: 0 5px;
                        box-shadow: 0 2px 8px rgba(255, 71, 87, 0.4);
                        animation: badge-pop 0.3s ease;
                    }
                    
                    @keyframes badge-pop {
                        0% { transform: scale(0); }
                        50% { transform: scale(1.2); }
                        100% { transform: scale(1); }
                    }
                    
                    /* Responsive */
                    @media (max-width: 991px) {
                        .arrowz-btn-label {
                            display: none;
                        }
                        
                        .arrowz-topbar-btn {
                            padding: 8px 10px;
                        }
                    }
                    
                    @media (max-width: 576px) {
                        .arrowz-topbar-shortcuts {
                            gap: 2px;
                            margin-right: 8px;
                        }
                        
                        .arrowz-topbar-btn {
                            padding: 6px 8px;
                        }
                        
                        .arrowz-topbar-btn svg {
                            width: 18px;
                            height: 18px;
                        }
                    }
                </style>
            `);
        },
        
        setupHandlers() {
            // Softphone
            $(document).on('click', '.arrowz-softphone-btn', () => {
                if (arrowz.softphone && arrowz.softphone.show) {
                    arrowz.softphone.show();
                } else {
                    frappe.set_route('/desk/make-call');
                }
            });
            
            // WhatsApp
            $(document).on('click', '.arrowz-whatsapp-btn', () => {
                this.showWhatsAppPanel();
            });
            
            // Messages
            $(document).on('click', '.arrowz-messages-btn', () => {
                this.showMessagesPanel();
            });
        },
        
        showWhatsAppPanel() {
            // Try to use omni panel if available
            if (arrowz.omni_panel && arrowz.omni_panel.toggle) {
                arrowz.omni_panel.toggle();
                return;
            }
            
            // Otherwise show conversation list
            frappe.set_route('List', 'AZ Conversation Session', {
                channel_type: ['in', ['WhatsApp', 'whatsapp']]
            });
        },
        
        showMessagesPanel() {
            // Open internal chat or conversations
            if (frappe.boot.chat_enabled) {
                // Use Frappe's built-in chat
                frappe.chat.open();
            } else {
                // Open conversation sessions without channel filter (internal)
                frappe.set_route('List', 'AZ Conversation Session');
            }
        },
        
        loadUnreadCounts() {
            // Load WhatsApp unread count
            frappe.call({
                method: 'frappe.client.get_count',
                args: {
                    doctype: 'AZ Conversation Session',
                    filters: {
                        unread_count: ['>', 0],
                        channel_type: ['in', ['WhatsApp', 'whatsapp']]
                    }
                },
                async: true,
                callback: (r) => {
                    if (r.message) {
                        this.updateBadge('.arrowz-whatsapp-badge', r.message);
                    }
                }
            });
            
            // Load internal messages count
            frappe.call({
                method: 'frappe.client.get_count',
                args: {
                    doctype: 'AZ Conversation Session',
                    filters: {
                        unread_count: ['>', 0],
                        channel_type: ['not in', ['WhatsApp', 'whatsapp', 'Telegram', 'telegram']]
                    }
                },
                async: true,
                callback: (r) => {
                    if (r.message) {
                        this.updateBadge('.arrowz-messages-badge', r.message);
                    }
                }
            });
        },
        
        updateBadge(selector, count) {
            const $badge = $(selector);
            if (count > 0) {
                $badge.text(count > 99 ? '99+' : count).show();
            } else {
                $badge.hide();
            }
        },
        
        subscribeToUpdates() {
            // WhatsApp message received
            frappe.realtime.on('whatsapp_message', () => {
                this.loadUnreadCounts();
                arrowz.utils.playSound('message');
            });
            
            // Internal message received
            frappe.realtime.on('new_message', () => {
                this.loadUnreadCounts();
                arrowz.utils.playSound('notification');
            });
            
            // Call status changed
            frappe.realtime.on('call_started', () => {
                $('.arrowz-softphone-btn').addClass('in-call');
            });
            
            frappe.realtime.on('call_ended', () => {
                $('.arrowz-softphone-btn').removeClass('in-call');
            });
        }
    };
    
    // Global helper functions
    window.arrowz_call = arrowz.call.dial;
    window.arrowz_sms = arrowz.sms.showSendDialog;
    window.arrowz_show_dialer = () => arrowz.softphone && arrowz.softphone.show();
    
})();
