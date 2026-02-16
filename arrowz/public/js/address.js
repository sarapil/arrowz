// Arrowz - Address DocType Extension
// Adds communication panel for addresses linked to contacts

frappe.ui.form.on('Address', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Add phone actions if phone number available
            if (frm.doc.phone || frm.doc.fax) {
                arrowz.phone_actions.add_to_form(frm);
            }
            
            // Initialize Omni-Channel panel
            if (typeof arrowz.omni !== 'undefined') {
                arrowz.omni.init(frm);
            }
        }
    },
    
    after_save: function(frm) {
        if (typeof arrowz.omni !== 'undefined') {
            arrowz.omni.refresh(frm);
        }
    }
});
