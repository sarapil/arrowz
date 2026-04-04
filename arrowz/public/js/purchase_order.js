// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

// Arrowz - Purchase Order DocType Extension
// Adds communication panel and quick actions

frappe.ui.form.on('Purchase Order', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Add phone actions if contact info available
            if (frm.doc.contact_mobile || frm.doc.contact_phone) {
                arrowz.phone_actions.add_to_form(frm);
            }
            
            // Initialize Omni-Channel panel
            if (typeof arrowz.omni !== 'undefined') {
                arrowz.omni.init(frm);
            }
            
            // Add quick communication button
            frm.add_custom_button(__('Contact Supplier'), function() {
                arrowz.omni.open_whatsapp_quick(
                    frm.doc.contact_mobile,
                    frm.doctype,
                    frm.docname
                );
            }, __('Communication'));
        }
    },
    
    after_save: function(frm) {
        if (typeof arrowz.omni !== 'undefined') {
            arrowz.omni.refresh(frm);
        }
    }
});
