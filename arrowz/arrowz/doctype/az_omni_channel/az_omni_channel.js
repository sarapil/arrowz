// Copyright (c) 2026, Arrowz Team
// License: MIT

frappe.ui.form.on('AZ Omni Channel', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Sync Templates button
            frm.add_custom_button(__('Sync Templates'), function() {
                frm.call({
                    method: 'sync_templates',
                    doc: frm.doc,
                    freeze: true,
                    freeze_message: __('Syncing templates...'),
                    callback: function(r) {
                        if (r.message) {
                            if (r.message.status === 'success') {
                                frappe.msgprint({
                                    title: __('Templates Synced'),
                                    message: __('Synced {0} templates', [r.message.templates_synced]),
                                    indicator: 'green'
                                });
                            } else {
                                frappe.msgprint({
                                    title: __('Sync Failed'),
                                    message: r.message.message,
                                    indicator: 'red'
                                });
                            }
                        }
                    }
                });
            }, __('Actions'));
            
            // Test Message button
            frm.add_custom_button(__('Send Test Message'), function() {
                let d = new frappe.ui.Dialog({
                    title: __('Send Test Message'),
                    fields: [
                        {
                            label: 'Recipient',
                            fieldname: 'recipient',
                            fieldtype: 'Data',
                            reqd: 1,
                            description: __('Phone number with country code (e.g., +201234567890)')
                        },
                        {
                            label: 'Message',
                            fieldname: 'message',
                            fieldtype: 'Small Text',
                            reqd: 1,
                            default: 'This is a test message from Arrowz'
                        }
                    ],
                    primary_action_label: __('Send'),
                    primary_action: function(values) {
                        frm.call({
                            method: 'test_send_message',
                            doc: frm.doc,
                            args: {
                                recipient: values.recipient,
                                message: values.message
                            },
                            freeze: true,
                            freeze_message: __('Sending...'),
                            callback: function(r) {
                                if (r.message) {
                                    if (r.message.status === 'success') {
                                        frappe.msgprint({
                                            title: __('Message Sent'),
                                            message: __('Message ID: {0}', [r.message.message_id]),
                                            indicator: 'green'
                                        });
                                        d.hide();
                                    } else {
                                        frappe.msgprint({
                                            title: __('Send Failed'),
                                            message: r.message.message,
                                            indicator: 'red'
                                        });
                                    }
                                }
                            }
                        });
                    }
                });
                d.show();
            }, __('Actions'));
            
            // View Conversations button
            frm.add_custom_button(__('View Conversations'), function() {
                frappe.set_route('List', 'AZ Conversation Session', {
                    channel: frm.doc.name
                });
            });
            
            // Show statistics
            show_channel_stats(frm);
        }
        
        // Show webhook URL
        if (frm.doc.provider) {
            frappe.db.get_value('AZ Omni Provider', frm.doc.provider, 'webhook_endpoint')
                .then(r => {
                    if (r.message && r.message.webhook_endpoint) {
                        frm.dashboard.add_comment(
                            __('Webhook URL: {0}', [r.message.webhook_endpoint]),
                            'blue'
                        );
                    }
                });
        }
    },
    
    provider: function(frm) {
        // Load provider info when selected
        if (frm.doc.provider) {
            frappe.db.get_value('AZ Omni Provider', frm.doc.provider, 
                ['provider_type', 'icon', 'color'])
                .then(r => {
                    if (r.message) {
                        frm.set_df_property('provider', 'description', 
                            `<i class="${r.message.icon}" style="color: ${r.message.color}"></i> ${r.message.provider_type}`
                        );
                    }
                });
        }
    }
});

function show_channel_stats(frm) {
    frappe.call({
        method: 'arrowz.arrowz.doctype.az_omni_channel.az_omni_channel.get_channel_statistics',
        args: {
            channel_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let stats = r.message;
                frm.dashboard.add_indicator(
                    __('Total: {0}', [stats.total_conversations]), 'blue'
                );
                frm.dashboard.add_indicator(
                    __('Active: {0}', [stats.active_conversations]), 'green'
                );
                frm.dashboard.add_indicator(
                    __('Today: {0}', [stats.today_conversations]), 'orange'
                );
                if (stats.avg_response_time) {
                    frm.dashboard.add_indicator(
                        __('Avg Response: {0} min', [stats.avg_response_time.toFixed(1)]), 'gray'
                    );
                }
            }
        }
    });
}
