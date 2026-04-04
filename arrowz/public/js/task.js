// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

// Arrowz - Task DocType Extension
// Adds communication panel and quick actions

frappe.ui.form.on('Task', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Initialize Omni-Channel panel
            if (typeof arrowz.omni !== 'undefined') {
                arrowz.omni.init(frm);
            }
            
            // Add notify assignee button
            if (frm.doc._assign && JSON.parse(frm.doc._assign).length > 0) {
                frm.add_custom_button(__('Notify Assignees'), function() {
                    const assignees = JSON.parse(frm.doc._assign);
                    
                    frappe.call({
                        method: 'frappe.core.doctype.user.user.get_users_email',
                        args: { users: assignees },
                        callback: function(r) {
                            if (r.message) {
                                new frappe.views.CommunicationComposer({
                                    doc: frm.doc,
                                    frm: frm,
                                    subject: `Task Update: ${frm.doc.subject}`,
                                    recipients: r.message.join(', ')
                                });
                            }
                        }
                    });
                }, __('Communication'));
            }
        }
    },
    
    after_save: function(frm) {
        if (typeof arrowz.omni !== 'undefined') {
            arrowz.omni.refresh(frm);
        }
    }
});
