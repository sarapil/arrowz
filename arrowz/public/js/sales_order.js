// Arrowz - Sales Order DocType Extension
// Adds communication panel and quick actions

frappe.ui.form.on('Sales Order', {
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
            frm.add_custom_button(__('Send Update'), function() {
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
