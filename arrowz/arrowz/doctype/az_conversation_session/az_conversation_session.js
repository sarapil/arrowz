// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

// License: MIT

frappe.ui.form.on('AZ Conversation Session', {
    refresh: function(frm) {
        // Show status indicator
        if (frm.doc.status) {
            const colors = {
                'Active': 'green',
                'Pending': 'yellow',
                'Resolved': 'blue',
                'Expired': 'gray',
                'Escalated': 'red',
                'Transferred': 'orange'
            };
            frm.page.set_indicator(__(frm.doc.status), colors[frm.doc.status] || 'gray');
        }
        
        // Window status
        if (frm.doc.window_expires) {
            if (frm.doc.is_window_active) {
                const expires = moment(frm.doc.window_expires);
                const hours_left = expires.diff(moment(), 'hours');
                frm.dashboard.add_comment(
                    __('Window expires in {0} hours', [hours_left]),
                    hours_left < 4 ? 'red' : 'blue'
                );
            } else {
                frm.dashboard.add_comment(__('24-hour window expired'), 'red');
            }
        }
        
        if (!frm.is_new()) {
            // Action buttons
            if (frm.doc.status === 'Active' || frm.doc.status === 'Pending') {
                frm.add_custom_button(__('Resolve'), function() {
                    frm.call({
                        method: 'resolve',
                        doc: frm.doc,
                        callback: function(r) {
                            if (r.message && r.message.status === 'success') {
                                frappe.show_alert({
                                    message: __('Session resolved'),
                                    indicator: 'green'
                                });
                                frm.reload_doc();
                            }
                        }
                    });
                }, __('Actions'));
                
                frm.add_custom_button(__('Escalate'), function() {
                    frappe.prompt([
                        {
                            label: 'Reason',
                            fieldname: 'reason',
                            fieldtype: 'Small Text',
                            reqd: 1
                        }
                    ], function(values) {
                        frm.call({
                            method: 'escalate',
                            doc: frm.doc,
                            args: { reason: values.reason },
                            callback: function(r) {
                                if (r.message && r.message.status === 'success') {
                                    frappe.show_alert({
                                        message: __('Session escalated'),
                                        indicator: 'orange'
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                    }, __('Escalate Session'));
                }, __('Actions'));
                
                frm.add_custom_button(__('Assign'), function() {
                    frappe.prompt([
                        {
                            label: 'User',
                            fieldname: 'user',
                            fieldtype: 'Link',
                            options: 'User',
                            reqd: 1
                        }
                    ], function(values) {
                        frm.call({
                            method: 'assign_to_user',
                            doc: frm.doc,
                            args: { user: values.user },
                            callback: function(r) {
                                if (r.message && r.message.status === 'success') {
                                    frappe.show_alert({
                                        message: __('Session assigned'),
                                        indicator: 'green'
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                    }, __('Assign Session'));
                }, __('Actions'));
            }
            
            // Mark as read
            if (frm.doc.unread_count > 0) {
                frm.add_custom_button(__('Mark as Read'), function() {
                    frm.call({
                        method: 'mark_as_read',
                        doc: frm.doc,
                        callback: function(r) {
                            if (r.message && r.message.status === 'success') {
                                frm.reload_doc();
                            }
                        }
                    });
                });
            }
            
            // Send message button
            if (frm.doc.is_window_active && frm.doc.status !== 'Resolved') {
                frm.add_custom_button(__('Send Message'), function() {
                    show_send_message_dialog(frm);
                }).addClass('btn-primary');
            }
            
            // View linked documents
            if (frm.doc.contact) {
                frm.add_custom_button(__('View Contact'), function() {
                    frappe.set_route('Form', 'Contact', frm.doc.contact);
                }, __('Links'));
            }
            if (frm.doc.customer) {
                frm.add_custom_button(__('View Customer'), function() {
                    frappe.set_route('Form', 'Customer', frm.doc.customer);
                }, __('Links'));
            }
            if (frm.doc.lead) {
                frm.add_custom_button(__('View Lead'), function() {
                    frappe.set_route('Form', 'Lead', frm.doc.lead);
                }, __('Links'));
            }
        }
        
        // Setup real-time listener
        setup_realtime_listener(frm);
    },
    
    onload: function(frm) {
        // Setup messages section
        if (!frm.is_new()) {
            render_chat_interface(frm);
        }
    }
});

function show_send_message_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Send Message'),
        fields: [
            {
                label: 'Message Type',
                fieldname: 'message_type',
                fieldtype: 'Select',
                options: 'text\nimage\ndocument\naudio\nvideo',
                default: 'text'
            },
            {
                label: 'Message',
                fieldname: 'content',
                fieldtype: 'Small Text',
                reqd: 1,
                depends_on: "eval:doc.message_type=='text'"
            },
            {
                label: 'Media',
                fieldname: 'media',
                fieldtype: 'Attach',
                depends_on: "eval:doc.message_type!='text'"
            }
        ],
        primary_action_label: __('Send'),
        primary_action: function(values) {
            frm.call({
                method: 'send_message',
                doc: frm.doc,
                args: {
                    content: values.content,
                    message_type: values.message_type,
                    media_url: values.media
                },
                freeze: true,
                freeze_message: __('Sending...'),
                callback: function(r) {
                    if (r.message) {
                        frappe.show_alert({
                            message: __('Message sent'),
                            indicator: 'green'
                        });
                        d.hide();
                        frm.reload_doc();
                    }
                }
            });
        }
    });
    d.show();
}

function render_chat_interface(frm) {
    // Custom chat interface in the messages section
    const $wrapper = frm.get_field('messages').$wrapper;
    $wrapper.empty();
    
    if (!frm.doc.messages || frm.doc.messages.length === 0) {
        $wrapper.html('<div class="text-muted text-center p-4">' + __('No messages yet') + '</div>');
        return;
    }
    
    let html = '<div class="chat-messages" style="max-height: 400px; overflow-y: auto; padding: 10px;">';
    
    frm.doc.messages.forEach(msg => {
        const isOutbound = msg.direction === 'outbound';
        const align = isOutbound ? 'right' : 'left';
        const bgColor = isOutbound ? '#dcf8c6' : '#fff';
        const time = moment(msg.timestamp).format('HH:mm');
        
        html += `
            <div style="text-align: ${align}; margin-bottom: 10px;">
                <div style="display: inline-block; max-width: 70%; background: ${bgColor}; 
                            padding: 8px 12px; border-radius: 8px; text-align: left;
                            box-shadow: 0 1px 1px rgba(0,0,0,0.1);">
                    <div style="font-size: 13px;">${frappe.utils.escape_html(msg.content || '')}</div>
                    <div style="font-size: 10px; color: #888; margin-top: 4px;">
                        ${time}
                        ${msg.status ? '<span class="ml-2">' + get_status_icon(msg.status) + '</span>' : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    $wrapper.html(html);
    
    // Scroll to bottom
    $wrapper.find('.chat-messages').scrollTop($wrapper.find('.chat-messages')[0].scrollHeight);
}

function get_status_icon(status) {
    const icons = {
        'sent': '✓',
        'delivered': '✓✓',
        'read': '<span style="color: #34B7F1;">✓✓</span>',
        'failed': '<span style="color: red;">✗</span>'
    };
    return icons[status] || '';
}

function setup_realtime_listener(frm) {
    frappe.realtime.on('arrowz_conversation_update', function(data) {
        if (data.session === frm.doc.name) {
            frm.reload_doc();
        }
    });
}
