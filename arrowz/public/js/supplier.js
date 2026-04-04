// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

// Arrowz - Supplier DocType Extension
// Adds communication panel and quick actions

frappe.ui.form.on('Supplier', {
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
