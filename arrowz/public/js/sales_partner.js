// Arrowz - Sales Partner DocType Extension
// Adds communication panel and quick actions

frappe.ui.form.on('Sales Partner', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Add phone actions
            arrowz.phone_actions.add_to_form(frm);
            
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
