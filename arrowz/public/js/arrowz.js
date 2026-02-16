/**
 * Arrowz Main JavaScript
 * Core utilities and integrations
 */

(function() {
    'use strict';
    
    // Arrowz namespace
    window.arrowz = window.arrowz || {};
    
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
                    icon: '/assets/arrowz/images/logo.png',
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
        
        // Request notification permission
        if (frappe.session.user !== 'Guest' && "Notification" in window) {
            Notification.requestPermission();
        }
        
        console.log('Arrowz: Click to Call enabled');
    });
    
    // Global helper functions
    window.arrowz_call = arrowz.call.dial;
    window.arrowz_sms = arrowz.sms.showSendDialog;
    window.arrowz_show_dialer = () => arrowz.softphone && arrowz.softphone.show();
    
})();
