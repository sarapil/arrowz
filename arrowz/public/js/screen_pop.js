// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Arrowz Screen Pop
 * CRM Screen Pop Integration
 */

frappe.provide('arrowz.screenpop');

(function() {
    'use strict';
    
    arrowz.screenpop = {
        // Configuration
        config: {
            enabled: true,
            popup_mode: 'sidebar', // sidebar, modal, newtab
            auto_link: true,
            search_doctypes: ['Customer', 'Lead', 'Contact', 'Supplier']
        },
        
        // Current popup state
        current: null,
        
        // Initialize
        init() {
            this.loadConfig();
            this.bindEvents();
        },
        
        // Load config from settings
        loadConfig() {
            frappe.db.get_single_value('Arrowz Settings', 'enable_screen_pop').then(enabled => {
                this.config.enabled = enabled;
            });
        },
        
        // Bind real-time events
        bindEvents() {
            // Incoming call event
            frappe.realtime.on('arrowz_incoming_call', (data) => {
                if (this.config.enabled) {
                    this.show(data.caller_id, data.call_id, 'incoming');
                }
            });
            
            // Outgoing call answered
            frappe.realtime.on('arrowz_call_connected', (data) => {
                if (this.config.enabled && data.remote_number) {
                    this.show(data.remote_number, data.call_id, 'connected');
                }
            });
        },
        
        // Show screen pop for a number
        async show(phone_number, call_id, event_type) {
            if (!phone_number) return;
            
            const result = await this.search(phone_number);
            
            if (result.found) {
                this.displayResult(result, call_id, event_type);
            } else {
                this.displayNotFound(phone_number, call_id, event_type);
            }
        },
        
        // Search for caller in CRM
        async search(phone_number) {
            const result = {
                found: false,
                matches: [],
                phone_number: phone_number
            };
            
            try {
                const response = await frappe.call({
                    method: 'arrowz.api.screenpop.search_caller',
                    args: { phone_number }
                });
                
                if (response.message && response.message.matches) {
                    result.found = response.message.matches.length > 0;
                    result.matches = response.message.matches;
                }
            } catch (error) {
                console.error('Screen pop search failed:', error);
            }
            
            return result;
        },
        
        // Display found result
        displayResult(result, call_id, event_type) {
            const mode = this.config.popup_mode;
            
            if (mode === 'sidebar') {
                this.showSidebar(result, call_id, event_type);
            } else if (mode === 'modal') {
                this.showModal(result, call_id, event_type);
            } else if (mode === 'newtab') {
                this.openInNewTab(result);
            }
        },
        
        // Display not found
        displayNotFound(phone_number, call_id, event_type) {
            const mode = this.config.popup_mode;
            
            if (mode === 'sidebar') {
                this.showSidebarUnknown(phone_number, call_id, event_type);
            } else if (mode === 'modal') {
                this.showModalUnknown(phone_number, call_id, event_type);
            }
        },
        
        // Show sidebar screen pop
        showSidebar(result, call_id, event_type) {
            // Remove existing sidebar
            this.closeSidebar();
            
            const match = result.matches[0];
            
            const sidebar = $(`
                <div class="screenpop-sidebar arrowz-fade-in">
                    <div class="screenpop-header">
                        <div class="screenpop-title">
                            <span class="event-icon">${event_type === 'incoming' ? '📞' : '📱'}</span>
                            <span>${event_type === 'incoming' ? __('Incoming Call') : __('Connected')}</span>
                        </div>
                        <button class="screenpop-close">&times;</button>
                    </div>
                    
                    <div class="screenpop-body">
                        <div class="caller-card">
                            <div class="caller-avatar">
                                ${match.name ? match.name.charAt(0).toUpperCase() : '?'}
                            </div>
                            <div class="caller-details">
                                <h3 class="caller-name">${match.name || __('Unknown')}</h3>
                                <div class="caller-type">${match.doctype}</div>
                                <div class="caller-phone">${arrowz.utils.formatPhone(result.phone_number)}</div>
                            </div>
                        </div>
                        
                        ${result.matches.length > 1 ? `
                            <div class="other-matches">
                                <div class="matches-title">${__('Other Matches')}</div>
                                ${result.matches.slice(1).map(m => `
                                    <div class="match-item" data-doctype="${m.doctype}" data-name="${m.name}">
                                        <span class="match-name">${m.name}</span>
                                        <span class="match-type">${m.doctype}</span>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                        
                        <div class="quick-info">
                            ${match.info ? `
                                <div class="info-row">
                                    <span class="info-label">${__('Company')}</span>
                                    <span class="info-value">${match.info.company || '-'}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">${__('Last Contact')}</span>
                                    <span class="info-value">${match.info.last_contact || '-'}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">${__('Open Tickets')}</span>
                                    <span class="info-value">${match.info.open_tickets || '0'}</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <div class="screenpop-actions">
                        <button class="btn btn-primary btn-sm open-record">
                            ${__('Open Record')}
                        </button>
                        <button class="btn btn-secondary btn-sm add-note">
                            ${__('Add Note')}
                        </button>
                    </div>
                </div>
            `);
            
            // Bind events
            sidebar.find('.screenpop-close').on('click', () => this.closeSidebar());
            sidebar.find('.open-record').on('click', () => {
                frappe.set_route('Form', match.doctype, match.name);
                this.closeSidebar();
            });
            sidebar.find('.add-note').on('click', () => this.showNoteDialog(match, call_id));
            sidebar.find('.match-item').on('click', function() {
                frappe.set_route('Form', $(this).data('doctype'), $(this).data('name'));
            });
            
            $('body').append(sidebar);
            this.current = { sidebar, call_id };
        },
        
        // Show sidebar for unknown caller
        showSidebarUnknown(phone_number, call_id, event_type) {
            this.closeSidebar();
            
            const sidebar = $(`
                <div class="screenpop-sidebar arrowz-fade-in">
                    <div class="screenpop-header">
                        <div class="screenpop-title">
                            <span class="event-icon">${event_type === 'incoming' ? '📞' : '📱'}</span>
                            <span>${event_type === 'incoming' ? __('Incoming Call') : __('Connected')}</span>
                        </div>
                        <button class="screenpop-close">&times;</button>
                    </div>
                    
                    <div class="screenpop-body">
                        <div class="caller-card unknown">
                            <div class="caller-avatar">?</div>
                            <div class="caller-details">
                                <h3 class="caller-name">${__('Unknown Caller')}</h3>
                                <div class="caller-phone">${arrowz.utils.formatPhone(phone_number)}</div>
                            </div>
                        </div>
                        
                        <div class="unknown-actions">
                            <p class="text-muted">${__('No matching records found')}</p>
                        </div>
                    </div>
                    
                    <div class="screenpop-actions">
                        <button class="btn btn-primary btn-sm create-lead">
                            ${__('Create Lead')}
                        </button>
                        <button class="btn btn-secondary btn-sm create-contact">
                            ${__('Create Contact')}
                        </button>
                    </div>
                </div>
            `);
            
            // Bind events
            sidebar.find('.screenpop-close').on('click', () => this.closeSidebar());
            sidebar.find('.create-lead').on('click', () => {
                frappe.new_doc('Lead', { mobile_no: phone_number });
                this.closeSidebar();
            });
            sidebar.find('.create-contact').on('click', () => {
                frappe.new_doc('Contact', { phone: phone_number });
                this.closeSidebar();
            });
            
            $('body').append(sidebar);
            this.current = { sidebar, call_id };
        },
        
        // Close sidebar
        closeSidebar() {
            if (this.current && this.current.sidebar) {
                this.current.sidebar.remove();
                this.current = null;
            }
            $('.screenpop-sidebar').remove();
        },
        
        // Show modal screen pop
        showModal(result, call_id, event_type) {
            const match = result.matches[0];
            
            const dialog = new frappe.ui.Dialog({
                title: event_type === 'incoming' ? __('Incoming Call') : __('Call Connected'),
                indicator: 'green',
                fields: [
                    {
                        fieldtype: 'HTML',
                        options: `
                            <div class="screenpop-modal-content">
                                <div class="caller-card">
                                    <div class="caller-avatar">
                                        ${match.name ? match.name.charAt(0).toUpperCase() : '?'}
                                    </div>
                                    <div class="caller-details">
                                        <h3>${match.name}</h3>
                                        <p>${match.doctype}</p>
                                        <p>${arrowz.utils.formatPhone(result.phone_number)}</p>
                                    </div>
                                </div>
                            </div>
                        `
                    }
                ],
                primary_action_label: __('Open Record'),
                primary_action: () => {
                    frappe.set_route('Form', match.doctype, match.name);
                    dialog.hide();
                },
                secondary_action_label: __('Add Note'),
                secondary_action: () => {
                    this.showNoteDialog(match, call_id);
                    dialog.hide();
                }
            });
            
            dialog.show();
        },
        
        // Show modal for unknown
        showModalUnknown(phone_number, call_id, event_type) {
            const dialog = new frappe.ui.Dialog({
                title: event_type === 'incoming' ? __('Incoming Call') : __('Call Connected'),
                indicator: 'yellow',
                fields: [
                    {
                        fieldtype: 'HTML',
                        options: `
                            <div class="screenpop-modal-content">
                                <div class="caller-card unknown">
                                    <div class="caller-avatar">?</div>
                                    <div class="caller-details">
                                        <h3>${__('Unknown Caller')}</h3>
                                        <p>${arrowz.utils.formatPhone(phone_number)}</p>
                                    </div>
                                </div>
                                <p class="text-muted">${__('No matching records found')}</p>
                            </div>
                        `
                    }
                ],
                primary_action_label: __('Create Lead'),
                primary_action: () => {
                    frappe.new_doc('Lead', { mobile_no: phone_number });
                    dialog.hide();
                },
                secondary_action_label: __('Create Contact'),
                secondary_action: () => {
                    frappe.new_doc('Contact', { phone: phone_number });
                    dialog.hide();
                }
            });
            
            dialog.show();
        },
        
        // Open in new tab
        openInNewTab(result) {
            const match = result.matches[0];
            const url = `/desk/${frappe.router.slug(match.doctype)}/${match.name}`;
            window.open(url, '_blank');
        },
        
        // Show note dialog
        showNoteDialog(match, call_id) {
            const dialog = new frappe.ui.Dialog({
                title: __('Add Call Note'),
                fields: [
                    {
                        fieldname: 'note',
                        label: __('Note'),
                        fieldtype: 'Text',
                        reqd: 1
                    }
                ],
                primary_action_label: __('Save'),
                primary_action: (values) => {
                    frappe.call({
                        method: 'arrowz.api.call.add_call_note',
                        args: {
                            call_id: call_id,
                            note: values.note
                        },
                        callback: () => {
                            frappe.show_alert({
                                message: __('Note saved'),
                                indicator: 'green'
                            });
                            dialog.hide();
                        }
                    });
                }
            });
            
            dialog.show();
        },
        
        // Manual trigger
        trigger(phone_number) {
            if (phone_number) {
                this.show(phone_number, null, 'manual');
            }
        }
    };
    
    // Initialize on ready
    $(document).ready(function() {
        arrowz.screenpop.init();
    });
    
})();
