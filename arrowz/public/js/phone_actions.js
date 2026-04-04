// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Arrowz Phone Actions
 * Smart phone number handling with action icons
 * Applies to all phone fields across CRM doctypes
 */

(function() {
    'use strict';
    
    // Phone Actions Module
    arrowz.phoneActions = {
        // Configuration
        config: {
            // DocTypes to apply phone actions to
            targetDocTypes: [
                'Lead', 'Contact', 'Customer', 'Supplier', 'Opportunity',
                'Prospect', 'Sales Order', 'Purchase Order', 'Quotation',
                'Employee', 'Address', 'Sales Partner', 'Issue'
            ],
            // Phone field names to look for
            phoneFields: [
                'mobile_no', 'phone', 'phone_no', 'contact_mobile', 
                'contact_phone', 'mobile', 'cell_number', 'whatsapp_no',
                'alternate_phone', 'secondary_phone'
            ],
            // Icons configuration - using SVG for brand icons
            icons: {
                phone_label: { emoji: '📱', title: 'Show Number', color: '#6c757d' },
                sms: { emoji: '💬', title: 'Send SMS', color: '#28a745' },
                whatsapp: { 
                    emoji: '<svg viewBox="0 0 24 24" width="14" height="14" fill="#25D366" style="vertical-align:middle;"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>', 
                    title: 'WhatsApp', 
                    color: '#25D366' 
                },
                telegram: { 
                    emoji: '<svg viewBox="0 0 24 24" width="14" height="14" fill="#0088cc" style="vertical-align:middle;"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>', 
                    title: 'Telegram', 
                    color: '#0088cc' 
                },
                call: { emoji: '📞', title: 'Call via PBX', color: '#007bff' }
            }
        },
        
        /**
         * Initialize phone actions
         */
        init() {
            this.setupFormHooks();
            this.setupListHooks();
            this.setupGlobalClickHandler();
            console.log('Arrowz: Phone Actions initialized');
        },
        
        /**
         * Setup hooks for form views
         */
        setupFormHooks() {
            const self = this;
            
            // Hook into form refresh
            $(document).on('form-refresh', function(e, frm) {
                if (self.config.targetDocTypes.includes(frm.doctype)) {
                    setTimeout(() => self.enhanceFormPhoneFields(frm), 100);
                }
            });
            
            // Also apply on page load
            if (cur_frm && self.config.targetDocTypes.includes(cur_frm.doctype)) {
                setTimeout(() => self.enhanceFormPhoneFields(cur_frm), 500);
            }
        },
        
        /**
         * Setup hooks for list views
         */
        setupListHooks() {
            const self = this;
            
            // Hook into list render
            $(document).on('list-loaded', function() {
                setTimeout(() => self.enhanceListPhoneFields(), 100);
            });
        },
        
        /**
         * Setup global click handler for phone action buttons
         */
        setupGlobalClickHandler() {
            const self = this;
            
            $(document).on('click', '.arrowz-phone-action', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const action = $(this).data('action');
                const number = $(this).data('number');
                const doctype = $(this).data('doctype');
                const docname = $(this).data('docname');
                
                self.executeAction(action, number, doctype, docname);
            });
        },
        
        /**
         * Enhance phone fields in a form
         */
        enhanceFormPhoneFields(frm) {
            const self = this;
            
            this.config.phoneFields.forEach(fieldName => {
                const field = frm.fields_dict[fieldName];
                if (!field || !frm.doc[fieldName]) return;
                
                const $wrapper = field.$wrapper;
                const number = frm.doc[fieldName];
                
                // Check if already enhanced
                if ($wrapper.find('.arrowz-phone-actions').length) return;
                
                // Create action buttons
                const $actions = self.createActionButtons(number, frm.doctype, frm.doc.name);
                
                // Add to field
                const $controlValue = $wrapper.find('.control-value, .like-disabled-input');
                if ($controlValue.length) {
                    $controlValue.css('display', 'flex').css('align-items', 'center').css('gap', '8px');
                    $controlValue.append($actions);
                } else {
                    // For editable fields, add after input
                    const $input = $wrapper.find('.control-input');
                    $input.css('display', 'flex').css('align-items', 'center').css('gap', '8px');
                    $input.append($actions);
                }
            });
        },
        
        /**
         * Enhance phone fields in list views
         */
        enhanceListPhoneFields() {
            const self = this;
            
            // Find phone-like columns in lists
            $('.list-row [data-field]').each(function() {
                const $cell = $(this);
                const fieldName = $cell.data('field');
                
                if (!self.config.phoneFields.includes(fieldName)) return;
                
                const number = $cell.text().trim();
                if (!number || !self.isPhoneNumber(number)) return;
                
                // Check if already enhanced
                if ($cell.find('.arrowz-phone-actions').length) return;
                
                // Get doctype and name from row
                const $row = $cell.closest('.list-row');
                const doctype = $row.data('doctype');
                const docname = $row.data('name');
                
                // Create mini action buttons
                const $actions = self.createMiniActionButtons(number, doctype, docname);
                $cell.append($actions);
            });
        },
        
        /**
         * Create action buttons for a phone number
         */
        createActionButtons(number, doctype, docname) {
            const cleanNumber = this.cleanPhoneNumber(number);
            
            return $(`
                <span class="arrowz-phone-actions" style="display: inline-flex; gap: 4px; margin-left: 8px;">
                    <button class="btn btn-xs arrowz-phone-action" 
                            data-action="show_number" 
                            data-number="${cleanNumber}"
                            data-doctype="${doctype || ''}"
                            data-docname="${docname || ''}"
                            title="${this.config.icons.phone_label.title}"
                            style="padding: 2px 6px; font-size: 14px;">
                        ${this.config.icons.phone_label.emoji}
                    </button>
                    <button class="btn btn-xs arrowz-phone-action" 
                            data-action="sms" 
                            data-number="${cleanNumber}"
                            data-doctype="${doctype || ''}"
                            data-docname="${docname || ''}"
                            title="${this.config.icons.sms.title}"
                            style="padding: 2px 6px; font-size: 14px;">
                        ${this.config.icons.sms.emoji}
                    </button>
                    <button class="btn btn-xs arrowz-phone-action" 
                            data-action="whatsapp" 
                            data-number="${cleanNumber}"
                            data-doctype="${doctype || ''}"
                            data-docname="${docname || ''}"
                            title="${this.config.icons.whatsapp.title}"
                            style="padding: 2px 6px; font-size: 14px;">
                        ${this.config.icons.whatsapp.emoji}
                    </button>
                    <button class="btn btn-xs arrowz-phone-action" 
                            data-action="telegram" 
                            data-number="${cleanNumber}"
                            data-doctype="${doctype || ''}"
                            data-docname="${docname || ''}"
                            title="${this.config.icons.telegram.title}"
                            style="padding: 2px 6px; font-size: 14px;">
                        ${this.config.icons.telegram.emoji}
                    </button>
                    <button class="btn btn-xs btn-primary arrowz-phone-action" 
                            data-action="call" 
                            data-number="${cleanNumber}"
                            data-doctype="${doctype || ''}"
                            data-docname="${docname || ''}"
                            title="${this.config.icons.call.title}"
                            style="padding: 2px 6px; font-size: 14px;">
                        ${this.config.icons.call.emoji}
                    </button>
                </span>
            `);
        },
        
        /**
         * Create mini action buttons for list views
         */
        createMiniActionButtons(number, doctype, docname) {
            const cleanNumber = this.cleanPhoneNumber(number);
            
            return $(`
                <span class="arrowz-phone-actions arrowz-phone-actions-mini" 
                      style="display: inline-flex; gap: 2px; margin-left: 4px; opacity: 0.7;">
                    <span class="arrowz-phone-action" 
                          data-action="whatsapp" 
                          data-number="${cleanNumber}"
                          data-doctype="${doctype || ''}"
                          data-docname="${docname || ''}"
                          title="${this.config.icons.whatsapp.title}"
                          style="cursor: pointer; font-size: 12px;">
                        ${this.config.icons.whatsapp.emoji}
                    </span>
                    <span class="arrowz-phone-action" 
                          data-action="call" 
                          data-number="${cleanNumber}"
                          data-doctype="${doctype || ''}"
                          data-docname="${docname || ''}"
                          title="${this.config.icons.call.title}"
                          style="cursor: pointer; font-size: 12px;">
                        ${this.config.icons.call.emoji}
                    </span>
                </span>
            `);
        },
        
        /**
         * Execute action based on button clicked
         */
        executeAction(action, number, doctype, docname) {
            switch(action) {
                case 'show_number':
                    this.showNumberPopup(number);
                    break;
                case 'sms':
                    this.sendSMS(number, doctype, docname);
                    break;
                case 'whatsapp':
                    this.openWhatsApp(number);
                    break;
                case 'telegram':
                    this.openTelegram(number);
                    break;
                case 'call':
                    this.makeCall(number);
                    break;
            }
        },
        
        /**
         * Show number in a popup with copy option
         */
        showNumberPopup(number) {
            const formattedNumber = this.formatPhoneNumber(number);
            
            const dialog = new frappe.ui.Dialog({
                title: __('Phone Number'),
                fields: [
                    {
                        fieldtype: 'HTML',
                        options: `
                            <div class="text-center">
                                <h2 style="font-family: monospace; margin: 20px 0;">${formattedNumber}</h2>
                                <p class="text-muted">${number}</p>
                            </div>
                        `
                    }
                ],
                primary_action_label: __('Copy'),
                primary_action: () => {
                    navigator.clipboard.writeText(number).then(() => {
                        frappe.show_alert({message: __('Number copied!'), indicator: 'green'}, 2);
                        dialog.hide();
                    });
                }
            });
            dialog.show();
        },
        
        /**
         * Open SMS dialog
         */
        sendSMS(number, doctype, docname) {
            if (arrowz.sms && arrowz.sms.showSendDialog) {
                arrowz.sms.showSendDialog(number, doctype, docname);
            } else {
                // Fallback to basic SMS dialog
                const dialog = new frappe.ui.Dialog({
                    title: __('Send SMS'),
                    fields: [
                        {
                            fieldname: 'to_number',
                            label: __('To'),
                            fieldtype: 'Data',
                            default: number,
                            read_only: 1
                        },
                        {
                            fieldname: 'message',
                            label: __('Message'),
                            fieldtype: 'Small Text',
                            reqd: 1
                        }
                    ],
                    primary_action_label: __('Send'),
                    primary_action: (values) => {
                        frappe.call({
                            method: 'arrowz.api.sms.send_sms',
                            args: {
                                to_number: number,
                                message: values.message,
                                party_type: doctype,
                                party: docname
                            },
                            callback: (r) => {
                                if (!r.exc) {
                                    frappe.show_alert({message: __('SMS sent!'), indicator: 'green'});
                                    dialog.hide();
                                }
                            }
                        });
                    }
                });
                dialog.show();
            }
        },
        
        /**
         * Open WhatsApp with the number
         */
        openWhatsApp(number) {
            // Clean number and ensure international format
            let cleanNumber = (number || '').toString().replace(/[^\d+]/g, '');
            // Remove leading + if present for WhatsApp API
            if (cleanNumber.startsWith('+')) {
                cleanNumber = cleanNumber.substring(1);
            }
            // Open WhatsApp
            const url = `https://wa.me/${cleanNumber}`;
            window.open(url, '_blank');
        },
        
        /**
         * Open Telegram with the number
         */
        openTelegram(number) {
            // Clean number
            let cleanNumber = (number || '').toString().replace(/[^\d+]/g, '');
            // Open Telegram
            const url = `https://t.me/${cleanNumber}`;
            window.open(url, '_blank');
        },
        
        /**
         * Make a call via PBX
         */
        makeCall(number) {
            console.log('Arrowz phoneActions: makeCall called with:', number);
            
            // Clean the number first
            let cleanNumber = (number || '').toString().replace(/[^\d+]/g, '');
            if (!cleanNumber) {
                frappe.show_alert({
                    message: __('Invalid phone number'),
                    indicator: 'red'
                });
                return;
            }
            
            console.log('Arrowz phoneActions: cleaned number:', cleanNumber);
            console.log('Arrowz phoneActions: softphone available:', !!(arrowz.softphone && arrowz.softphone.makeCall));
            console.log('Arrowz phoneActions: softphone registered:', arrowz.softphone?.registered);
            
            if (arrowz.call && arrowz.call.dial) {
                console.log('Arrowz phoneActions: Using arrowz.call.dial');
                arrowz.call.dial(cleanNumber);
            } else if (arrowz.softphone) {
                console.log('Arrowz phoneActions: Using arrowz.softphone');
                // Show softphone first
                arrowz.softphone.show();
                // Wait for dialog to be ready, then make call
                setTimeout(() => {
                    if (arrowz.softphone.registered) {
                        // Set number in input and show active call UI
                        const input = document.getElementById('arrowz-dial-input');
                        if (input) {
                            input.value = cleanNumber;
                        }
                        arrowz.softphone.showActiveCallUI(cleanNumber);
                        arrowz.softphone.makeCall(cleanNumber);
                    } else {
                        frappe.show_alert({
                            message: __('Softphone not registered. Please wait and try again.'),
                            indicator: 'yellow'
                        });
                    }
                }, 500);
            } else {
                frappe.show_alert({
                    message: __('Softphone not available'),
                    indicator: 'yellow'
                });
            }
        },
        
        /**
         * Check if text looks like a phone number
         */
        isPhoneNumber(text) {
            if (!text) return false;
            const digits = text.replace(/[\s\-\(\)\+\.]/g, '');
            return /^\d{7,15}$/.test(digits);
        },
        
        /**
         * Clean phone number to digits only
         */
        cleanPhoneNumber(number) {
            if (!number) return '';
            return number.replace(/[^\d+]/g, '');
        },
        
        /**
         * Format phone number for display
         */
        formatPhoneNumber(number) {
            if (!number) return '';
            const digits = number.replace(/\D/g, '');
            
            // Format based on length
            if (digits.length === 10) {
                return `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`;
            } else if (digits.length === 11 && digits[0] === '1') {
                return `+1 (${digits.slice(1,4)}) ${digits.slice(4,7)}-${digits.slice(7)}`;
            }
            
            return number;
        }
    };
    
    // Initialize when document is ready
    $(document).ready(function() {
        // Wait for frappe to be ready
        if (typeof frappe !== 'undefined' && frappe.session.user !== 'Guest') {
            arrowz.phoneActions.init();
        }
    });
    
})();
