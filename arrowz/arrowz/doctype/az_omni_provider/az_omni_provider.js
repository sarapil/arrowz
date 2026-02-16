// Copyright (c) 2026, Arrowz Team
// License: MIT

frappe.ui.form.on('AZ Omni Provider', {
    refresh: function(frm) {
        // Add Test Connection button
        if (!frm.is_new()) {
            frm.add_custom_button(__('Test Connection'), function() {
                frm.call({
                    method: 'test_connection',
                    doc: frm.doc,
                    freeze: true,
                    freeze_message: __('Testing connection...'),
                    callback: function(r) {
                        if (r.message) {
                            if (r.message.status === 'success') {
                                frappe.msgprint({
                                    title: __('Connection Successful'),
                                    message: r.message.message || __('Provider connection is working'),
                                    indicator: 'green'
                                });
                            } else {
                                frappe.msgprint({
                                    title: __('Connection Failed'),
                                    message: r.message.message || __('Provider connection failed'),
                                    indicator: 'red'
                                });
                            }
                        }
                    }
                });
            }, __('Actions'));
            
            // Copy webhook URL button
            if (frm.doc.webhook_endpoint) {
                frm.add_custom_button(__('Copy Webhook URL'), function() {
                    frappe.utils.copy_to_clipboard(frm.doc.webhook_endpoint);
                    frappe.show_alert({
                        message: __('Webhook URL copied to clipboard'),
                        indicator: 'green'
                    });
                }, __('Actions'));
            }
        }
        
        // Set icon preview
        if (frm.doc.icon) {
            frm.get_field('icon').$wrapper.find('.like-disabled-input').html(
                `<i class="${frm.doc.icon}" style="font-size: 24px; color: ${frm.doc.color || '#333'}"></i> ${frm.doc.icon}`
            );
        }
    },
    
    provider_type: function(frm) {
        // Auto-set driver class based on provider type
        const driver_map = {
            'WhatsApp Cloud API': 'arrowz.integrations.whatsapp.WhatsAppCloudDriver',
            'WhatsApp On-Premise': 'arrowz.integrations.whatsapp.WhatsAppOnPremDriver',
            'Telegram Bot': 'arrowz.integrations.telegram.TelegramDriver',
            'Facebook Messenger': 'arrowz.integrations.facebook.MessengerDriver',
            'Instagram Direct': 'arrowz.integrations.instagram.InstagramDriver',
            'Viber': 'arrowz.integrations.viber.ViberDriver',
            'LINE': 'arrowz.integrations.line.LineDriver',
            'WeChat': 'arrowz.integrations.wechat.WeChatDriver',
            'Signal': 'arrowz.integrations.signal.SignalDriver',
            'SMS Gateway': 'arrowz.integrations.sms.SMSDriver',
            'Email': 'arrowz.integrations.email.EmailDriver',
            'Push Notification': 'arrowz.integrations.push.PushDriver',
            'VoIP': 'arrowz.integrations.voip.VoIPDriver',
            'Video Conference': 'arrowz.integrations.openmeetings.OpenMeetingsDriver'
        };
        
        if (frm.doc.provider_type && driver_map[frm.doc.provider_type]) {
            frm.set_value('driver_class', driver_map[frm.doc.provider_type]);
        }
        
        // Set default icons
        const icon_map = {
            'WhatsApp Cloud API': 'fa fa-whatsapp',
            'WhatsApp On-Premise': 'fa fa-whatsapp',
            'Telegram Bot': 'fa fa-telegram',
            'Facebook Messenger': 'fa fa-facebook-messenger',
            'Instagram Direct': 'fa fa-instagram',
            'Viber': 'fa fa-phone',
            'LINE': 'fa fa-comment',
            'WeChat': 'fa fa-wechat',
            'Signal': 'fa fa-lock',
            'SMS Gateway': 'fa fa-sms',
            'Email': 'fa fa-envelope',
            'Push Notification': 'fa fa-bell',
            'VoIP': 'fa fa-phone',
            'Video Conference': 'fa fa-video-camera'
        };
        
        const color_map = {
            'WhatsApp Cloud API': '#25D366',
            'WhatsApp On-Premise': '#25D366',
            'Telegram Bot': '#0088cc',
            'Facebook Messenger': '#0084FF',
            'Instagram Direct': '#E1306C',
            'Viber': '#665CAC',
            'LINE': '#00B900',
            'WeChat': '#7BB32E',
            'Signal': '#3A76F0',
            'SMS Gateway': '#5e35b1',
            'Email': '#EA4335',
            'Push Notification': '#FF6B00',
            'VoIP': '#5e35b1',
            'Video Conference': '#FF5722'
        };
        
        if (frm.doc.provider_type) {
            if (icon_map[frm.doc.provider_type]) {
                frm.set_value('icon', icon_map[frm.doc.provider_type]);
            }
            if (color_map[frm.doc.provider_type]) {
                frm.set_value('color', color_map[frm.doc.provider_type]);
            }
        }
    }
});
