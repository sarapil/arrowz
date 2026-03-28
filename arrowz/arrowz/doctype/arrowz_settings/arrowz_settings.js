// Copyright (c) 2026, Arrowz Team and contributors
// For license information, please see license.txt

frappe.ui.form.on('Arrowz Settings', {
    refresh: function(frm) {
        // Add Test OpenAI button
        if (frm.doc.enable_ai_features && frm.doc.openai_api_key) {
            frm.add_custom_button(__('Test OpenAI Connection'), function() {
                frm.call('test_openai_connection').then(r => {
                    if (r.message.success) {
                        frappe.msgprint({
                            title: __('Success'),
                            indicator: 'green',
                            message: r.message.message
                        });
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            indicator: 'red',
                            message: r.message.message
                        });
                    }
                });
            }, __('Actions'));
        }
        
        // Add quick links
        frm.add_custom_button(__('Open Dashboard'), function() {
            frappe.set_route('arrowz-topology');
        });
        
        frm.add_custom_button(__('View Call Logs'), function() {
            frappe.set_route('List', 'AZ Call Log');
        });
    },
    
    enable_ai_features: function(frm) {
        if (frm.doc.enable_ai_features && !frm.doc.openai_api_key) {
            frappe.show_alert({
                message: __('Please enter your OpenAI API Key'),
                indicator: 'orange'
            });
        }
    }
});
