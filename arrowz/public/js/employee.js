// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

// Arrowz - Employee DocType Extension
// Adds communication panel and quick actions

frappe.ui.form.on('Employee', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Add phone actions
            arrowz.phone_actions.add_to_form(frm);
            
            // Initialize Omni-Channel panel
            if (typeof arrowz.omni !== 'undefined') {
                arrowz.omni.init(frm);
            }
            
            // Add quick communication buttons
            if (frm.doc.cell_number) {
                frm.add_custom_button(__('WhatsApp'), function() {
                    arrowz.omni.open_whatsapp_quick(
                        frm.doc.cell_number,
                        frm.doctype,
                        frm.docname
                    );
                }, __('Contact'));
            }
            
            if (frm.doc.personal_email || frm.doc.company_email) {
                frm.add_custom_button(__('Email'), function() {
                    new frappe.views.CommunicationComposer({
                        doc: frm.doc,
                        frm: frm,
                        subject: `HR: ${frm.doc.employee_name}`,
                        recipients: frm.doc.personal_email || frm.doc.company_email
                    });
                }, __('Contact'));
            }
        }
    },
    
    after_save: function(frm) {
        if (typeof arrowz.omni !== 'undefined') {
            arrowz.omni.refresh(frm);
        }
    }
});
