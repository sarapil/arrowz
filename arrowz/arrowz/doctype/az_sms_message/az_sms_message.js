// Copyright (c) 2026, Arrowz and contributors
// For license information, please see license.txt

frappe.ui.form.on('AZ SMS Message', {
    refresh: function(frm) {
        // Status indicator
        const colors = {
            'Pending': 'yellow',
            'Sent': 'blue',
            'Delivered': 'green',
            'Failed': 'red',
            'Received': 'cyan'
        };
        frm.page.set_indicator(frm.doc.status, colors[frm.doc.status] || 'gray');
        
        // Resend failed messages
        if (frm.doc.status === 'Failed' && frm.doc.direction === 'Outbound') {
            frm.add_custom_button(__('Retry Send'), function() {
                retry_send(frm);
            });
        }
        
        // Reply button for inbound
        if (frm.doc.direction === 'Inbound') {
            frm.add_custom_button(__('Reply'), function() {
                reply_to_message(frm);
            });
        }
        
        // View CRM record
        if (frm.doc.party_type && frm.doc.party) {
            frm.add_custom_button(__('View ' + frm.doc.party_type), function() {
                frappe.set_route('Form', frm.doc.party_type, frm.doc.party);
            }, __('CRM'));
        }
        
        // View related call
        if (frm.doc.related_call) {
            frm.add_custom_button(__('View Call'), function() {
                frappe.set_route('Form', 'AZ Call Log', frm.doc.related_call);
            });
        }
        
        // Character count indicator
        update_character_count(frm);
    },
    
    message_content: function(frm) {
        update_character_count(frm);
    }
});

function update_character_count(frm) {
    const content = frm.doc.message_content || '';
    const charCount = content.length;
    
    // Check if Unicode
    const isUnicode = /[^\x00-\x7F]/.test(content);
    const charsPerSegment = isUnicode ? (charCount <= 70 ? 70 : 67) : (charCount <= 160 ? 160 : 153);
    const segments = Math.max(1, Math.ceil(charCount / charsPerSegment));
    
    frm.set_df_property('message_content', 'description', 
        `${charCount} characters | ${segments} segment(s) | ${isUnicode ? 'Unicode' : 'GSM'}`
    );
}

function retry_send(frm) {
    frappe.confirm(
        __('Retry sending this message?'),
        function() {
            frappe.call({
                method: 'send',
                doc: frm.doc,
                freeze: true,
                freeze_message: __('Sending...'),
                callback: function(r) {
                    frm.reload_doc();
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Message sent successfully'),
                            indicator: 'green'
                        });
                    }
                }
            });
        }
    );
}

function reply_to_message(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Reply to') + ' ' + (frm.doc.contact_name || frm.doc.phone_number),
        fields: [
            {
                label: __('Message'),
                fieldname: 'message',
                fieldtype: 'Small Text',
                reqd: 1
            }
        ],
        primary_action_label: __('Send Reply'),
        primary_action: function(values) {
            frappe.call({
                method: 'arrowz.arrowz.doctype.az_sms_message.az_sms_message.send_sms',
                args: {
                    to_number: frm.doc.phone_number,
                    message: values.message,
                    party_type: frm.doc.party_type,
                    party: frm.doc.party
                },
                freeze: true,
                freeze_message: __('Sending reply...'),
                callback: function(r) {
                    d.hide();
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Reply sent successfully'),
                            indicator: 'green'
                        });
                    } else {
                        frappe.msgprint({
                            title: __('Failed'),
                            message: r.message ? r.message.error : __('Unknown error'),
                            indicator: 'red'
                        });
                    }
                }
            });
        }
    });
    d.show();
}
