// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

frappe.ui.form.on('AZ Extension', {
    refresh: function(frm) {
        // Status indicator
        let status_colors = {
            'offline': 'gray',
            'available': 'green',
            'on_call': 'red',
            'wrap_up': 'orange',
            'break': 'blue',
            'busy': 'yellow'
        };
        
        let color = status_colors[frm.doc.status] || 'gray';
        frm.page.set_indicator(__(frm.doc.status || 'offline'), color);
        
        // Sync status indicator
        if (frm.doc.sync_status) {
            let sync_colors = {
                'Synced': 'green',
                'Pending': 'blue',
                'Failed': 'red',
                'Not Synced': 'orange'
            };
            frm.dashboard.set_headline(
                `<span class="indicator-pill ${sync_colors[frm.doc.sync_status] || 'gray'}">
                    PBX: ${frm.doc.sync_status}
                </span>`
            );
        }
        
        // ===== PBX Sync Buttons =====
        if (!frm.is_new()) {
            // Sync to PBX button
            frm.add_custom_button(__('Sync to PBX'), function() {
                frappe.confirm(
                    __('This will create or update this extension in FreePBX. Continue?'),
                    function() {
                        frappe.call({
                            method: 'sync_to_pbx',
                            doc: frm.doc,
                            freeze: true,
                            freeze_message: __('Syncing to FreePBX...'),
                            callback: function(r) {
                                frm.reload_doc();
                            }
                        });
                    }
                );
            }, __('PBX'));
            
            // Sync from PBX button
            frm.add_custom_button(__('Sync from PBX'), function() {
                frappe.call({
                    method: 'sync_from_pbx',
                    doc: frm.doc,
                    freeze: true,
                    freeze_message: __('Fetching from FreePBX...'),
                    callback: function(r) {
                        frm.reload_doc();
                    }
                });
            }, __('PBX'));
            
            // Test Registration button
            frm.add_custom_button(__('Test Registration'), function() {
                frappe.call({
                    method: 'test_registration',
                    doc: frm.doc,
                    freeze: true,
                    freeze_message: __('Checking registration status...'),
                    callback: function(r) {
                        frm.reload_doc();
                    }
                });
            }, __('PBX'));
            
            // Sync Password to PBX button
            frm.add_custom_button(__('Sync Password'), function() {
                frappe.confirm(
                    __('This will update the SIP password in FreePBX (Extension + User Manager). Continue?'),
                    function() {
                        frappe.call({
                            method: 'sync_password_to_pbx',
                            doc: frm.doc,
                            freeze: true,
                            freeze_message: __('Syncing password to FreePBX...'),
                            callback: function(r) {
                                if (r.message && r.message.success) {
                                    frappe.show_alert({
                                        message: __('Password synced to FreePBX successfully!'),
                                        indicator: 'green'
                                    });
                                } else {
                                    frappe.show_alert({
                                        message: __('Password sync failed. Check error log.'),
                                        indicator: 'red'
                                    });
                                }
                                frm.reload_doc();
                            }
                        });
                    }
                );
            }, __('PBX'));
        }
        
        // Copy SIP credentials button
        if (frm.doc.sip_username) {
            frm.add_custom_button(__('Copy SIP Config'), function() {
                frappe.call({
                    method: 'frappe.client.get_password',
                    args: {
                        doctype: 'AZ Extension',
                        name: frm.doc.name,
                        fieldname: 'sip_password'
                    },
                    callback: function(r) {
                        // Get server details
                        frappe.call({
                            method: 'frappe.client.get_value',
                            args: {
                                doctype: 'AZ Server Config',
                                name: frm.doc.server,
                                fieldname: ['host', 'sip_domain', 'websocket_url', 'websocket_port']
                            },
                            callback: function(server_r) {
                                const server = server_r.message || {};
                                const config = {
                                    extension: frm.doc.extension,
                                    username: frm.doc.sip_username,
                                    password: r.message,
                                    domain: server.sip_domain || server.host,
                                    websocket: server.websocket_url || `wss://${server.host}:${server.websocket_port || 8089}/ws`,
                                    display_name: frm.doc.display_name || frm.doc.extension
                                };
                                
                                const text = JSON.stringify(config, null, 2);
                                navigator.clipboard.writeText(text).then(() => {
                                    frappe.show_alert({
                                        message: __('SIP configuration copied to clipboard'),
                                        indicator: 'green'
                                    });
                                });
                            }
                        });
                    }
                });
            }, __('Actions'));
        }
        
        // Generate new password button
        frm.add_custom_button(__('Generate New Password'), function() {
            frappe.confirm(
                __('This will generate a new SIP password and sync it to FreePBX. Continue?'),
                function() {
                    // Generate random password
                    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789!@#$%^&*';
                    let password = '';
                    for (let i = 0; i < 16; i++) {
                        password += chars.charAt(Math.floor(Math.random() * chars.length));
                    }
                    
                    frm.set_value('sip_password', password);
                    frm.save().then(() => {
                        frappe.show_alert({
                            message: __('New password generated. Don\'t forget to update your phone!'),
                            indicator: 'green'
                        });
                    });
                }
            );
        }, __('Actions'));
        
        // View call history
        frm.add_custom_button(__('Call History'), function() {
            frappe.set_route('List', 'AZ Call Log', {
                extension: frm.doc.extension
            });
        }, __('View'));
    },
    
    user: function(frm) {
        // Auto-fill display name from user
        if (frm.doc.user && !frm.doc.display_name) {
            frappe.db.get_value('User', frm.doc.user, 'full_name', (r) => {
                if (r && r.full_name) {
                    frm.set_value('display_name', r.full_name);
                }
            });
        }
    },
    
    extension: function(frm) {
        // Auto-set SIP username and voicemail PIN
        if (frm.doc.extension) {
            if (!frm.doc.sip_username) {
                frm.set_value('sip_username', frm.doc.extension);
            }
            if (!frm.doc.voicemail_pin) {
                frm.set_value('voicemail_pin', frm.doc.extension);
            }
        }
    },
    
    auto_provision: function(frm) {
        if (frm.doc.auto_provision && !frm.is_new()) {
            frappe.show_alert({
                message: __('Auto provision enabled. Click "Sync to PBX" to create in FreePBX.'),
                indicator: 'blue'
            });
        }
    }
});
