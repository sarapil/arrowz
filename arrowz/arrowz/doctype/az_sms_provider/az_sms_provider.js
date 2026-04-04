// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

frappe.ui.form.on('AZ SMS Provider', {
    refresh: function(frm) {
        // Status indicator
        if (frm.doc.is_active) {
            frm.page.set_indicator(__('Active'), 'green');
        } else {
            frm.page.set_indicator(__('Inactive'), 'gray');
        }
        
        // Test connection button
        if (!frm.is_new()) {
            frm.add_custom_button(__('Test Connection'), function() {
                test_provider_connection(frm);
            });
            
            frm.add_custom_button(__('Send Test SMS'), function() {
                send_test_sms(frm);
            });
        }
        
        // Show usage info
        if (frm.doc.daily_limit > 0) {
            const usage_pct = Math.round((frm.doc.current_daily_usage / frm.doc.daily_limit) * 100);
            frm.dashboard.add_indicator(
                __('Daily Usage: {0}/{1} ({2}%)', [frm.doc.current_daily_usage, frm.doc.daily_limit, usage_pct]),
                usage_pct > 90 ? 'red' : (usage_pct > 70 ? 'orange' : 'green')
            );
        }
        
        // Copy webhook URL
        if (frm.doc.webhook_url) {
            frm.add_custom_button(__('Copy Webhook URL'), function() {
                frappe.utils.copy_to_clipboard(frm.doc.webhook_url);
                frappe.show_alert({
                    message: __('Webhook URL copied to clipboard'),
                    indicator: 'green'
                });
            });
        }
        
        // Provider-specific field visibility
        setup_provider_fields(frm);
    },
    
    provider_type: function(frm) {
        setup_provider_fields(frm);
    }
});

function setup_provider_fields(frm) {
    const provider = frm.doc.provider_type;
    
    // Twilio uses account_sid + auth_token
    frm.set_df_property('account_sid', 'hidden', provider !== 'Twilio');
    frm.set_df_property('auth_token', 'hidden', provider !== 'Twilio');
    
    // Custom API needs base URL
    frm.set_df_property('api_base_url', 'reqd', provider === 'Custom API');
    
    // Most providers use api_key/api_secret
    const uses_api_key = ['Vonage', 'MessageBird', 'Plivo', 'Infobip', 'ClickSend', 'Custom API'].includes(provider);
    frm.set_df_property('api_key', 'hidden', !uses_api_key && provider === 'Twilio');
    frm.set_df_property('api_secret', 'hidden', !uses_api_key && provider === 'Twilio');
}

function test_provider_connection(frm) {
    frappe.call({
        method: 'test_connection',
        doc: frm.doc,
        freeze: true,
        freeze_message: __('Testing connection...'),
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.msgprint({
                    title: __('Connection Successful'),
                    indicator: 'green',
                    message: __('Provider connection test passed.') + '<br><br>' +
                             '<pre>' + JSON.stringify(r.message, null, 2) + '</pre>'
                });
            } else {
                frappe.msgprint({
                    title: __('Connection Failed'),
                    indicator: 'red',
                    message: r.message ? r.message.error : __('Unknown error')
                });
            }
        }
    });
}

function send_test_sms(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Send Test SMS'),
        fields: [
            {
                label: __('Phone Number'),
                fieldname: 'phone',
                fieldtype: 'Data',
                reqd: 1,
                description: __('Include country code, e.g., +1234567890')
            },
            {
                label: __('Message'),
                fieldname: 'message',
                fieldtype: 'Small Text',
                default: 'This is a test message from Arrowz SMS integration.',
                reqd: 1
            }
        ],
        primary_action_label: __('Send'),
        primary_action: function(values) {
            frappe.call({
                method: 'arrowz.api.sms.send_sms',
                args: {
                    to_number: values.phone,
                    message: values.message,
                    provider: frm.doc.name
                },
                freeze: true,
                freeze_message: __('Sending SMS...'),
                callback: function(r) {
                    d.hide();
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __('Test SMS sent successfully!'),
                            indicator: 'green'
                        }, 5);
                    } else {
                        frappe.msgprint({
                            title: __('SMS Failed'),
                            indicator: 'red',
                            message: r.message ? r.message.error : __('Unknown error')
                        });
                    }
                }
            });
        }
    });
    d.show();
}
