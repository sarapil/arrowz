// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

// License: MIT

frappe.ui.form.on('AZ Meeting Room', {
    refresh: function(frm) {
        // Show status indicator
        if (frm.doc.status) {
            const colors = {
                'Draft': 'gray',
                'Scheduled': 'blue',
                'Active': 'green',
                'Completed': 'purple',
                'Cancelled': 'red'
            };
            frm.page.set_indicator(__(frm.doc.status), colors[frm.doc.status] || 'gray');
        }
        
        if (!frm.is_new()) {
            // Action buttons based on status
            if (frm.doc.status === 'Scheduled') {
                frm.add_custom_button(__('Start Meeting'), function() {
                    frm.call({
                        method: 'start_meeting',
                        doc: frm.doc,
                        freeze: true,
                        freeze_message: __('Starting meeting...'),
                        callback: function(r) {
                            if (r.message && r.message.status === 'success') {
                                frappe.show_alert({
                                    message: __('Meeting started'),
                                    indicator: 'green'
                                });
                                if (r.message.moderator_url) {
                                    window.open(r.message.moderator_url, '_blank');
                                }
                                frm.reload_doc();
                            }
                        }
                    });
                }).addClass('btn-primary');
                
                frm.add_custom_button(__('Send Invitations'), function() {
                    frm.call({
                        method: 'send_invitations',
                        doc: frm.doc,
                        freeze: true,
                        freeze_message: __('Sending invitations...'),
                        callback: function(r) {
                            if (r.message) {
                                frappe.show_alert({
                                    message: __('Sent {0} invitations', [r.message.sent_count]),
                                    indicator: 'green'
                                });
                                frm.reload_doc();
                            }
                        }
                    });
                }, __('Actions'));
            }
            
            if (frm.doc.status === 'Active') {
                frm.add_custom_button(__('Join as Moderator'), function() {
                    if (frm.doc.moderator_url) {
                        window.open(frm.doc.moderator_url, '_blank');
                    }
                }).addClass('btn-primary');
                
                frm.add_custom_button(__('End Meeting'), function() {
                    frappe.confirm(
                        __('Are you sure you want to end this meeting?'),
                        function() {
                            frm.call({
                                method: 'end_meeting',
                                doc: frm.doc,
                                callback: function(r) {
                                    if (r.message && r.message.status === 'success') {
                                        frappe.show_alert({
                                            message: __('Meeting ended'),
                                            indicator: 'green'
                                        });
                                        frm.reload_doc();
                                    }
                                }
                            });
                        }
                    );
                }, __('Actions'));
            }
            
            // Add participant button
            if (frm.doc.status !== 'Completed' && frm.doc.status !== 'Cancelled') {
                frm.add_custom_button(__('Add Participant'), function() {
                    show_add_participant_dialog(frm);
                }, __('Actions'));
            }
            
            // Copy URLs
            if (frm.doc.participant_url) {
                frm.add_custom_button(__('Copy Participant URL'), function() {
                    frappe.utils.copy_to_clipboard(frm.doc.participant_url);
                    frappe.show_alert({
                        message: __('URL copied to clipboard'),
                        indicator: 'green'
                    });
                }, __('Share'));
            }
            
            if (frm.doc.moderator_url) {
                frm.add_custom_button(__('Copy Moderator URL'), function() {
                    frappe.utils.copy_to_clipboard(frm.doc.moderator_url);
                    frappe.show_alert({
                        message: __('URL copied to clipboard'),
                        indicator: 'green'
                    });
                }, __('Share'));
            }
        }
    },
    
    status: function(frm) {
        if (frm.doc.status === 'Scheduled' && !frm.doc.external_room_id) {
            frappe.show_alert({
                message: __('Room will be created in OpenMeetings when saved'),
                indicator: 'blue'
            });
        }
    }
});

function show_add_participant_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Add Participant'),
        fields: [
            {
                label: 'Participant Type',
                fieldname: 'participant_type',
                fieldtype: 'Select',
                options: 'Contact\nLead\nCustomer\nUser\nExternal',
                default: 'External',
                reqd: 1
            },
            {
                label: 'Select Contact',
                fieldname: 'contact',
                fieldtype: 'Link',
                options: 'Contact',
                depends_on: "eval:doc.participant_type=='Contact'"
            },
            {
                label: 'Select Lead',
                fieldname: 'lead',
                fieldtype: 'Link',
                options: 'Lead',
                depends_on: "eval:doc.participant_type=='Lead'"
            },
            {
                label: 'Select Customer',
                fieldname: 'customer',
                fieldtype: 'Link',
                options: 'Customer',
                depends_on: "eval:doc.participant_type=='Customer'"
            },
            {
                label: 'Select User',
                fieldname: 'user',
                fieldtype: 'Link',
                options: 'User',
                depends_on: "eval:doc.participant_type=='User'"
            },
            {
                label: 'Name',
                fieldname: 'name',
                fieldtype: 'Data',
                depends_on: "eval:doc.participant_type=='External'",
                mandatory_depends_on: "eval:doc.participant_type=='External'"
            },
            {
                label: 'Email',
                fieldname: 'email',
                fieldtype: 'Data',
                depends_on: "eval:doc.participant_type=='External'",
                mandatory_depends_on: "eval:doc.participant_type=='External'"
            },
            {
                fieldtype: 'Section Break'
            },
            {
                label: 'Is Moderator',
                fieldname: 'is_moderator',
                fieldtype: 'Check',
                default: 0
            }
        ],
        primary_action_label: __('Add'),
        primary_action: function(values) {
            let doctype = null;
            let docname = null;
            
            switch(values.participant_type) {
                case 'Contact':
                    doctype = 'Contact';
                    docname = values.contact;
                    break;
                case 'Lead':
                    doctype = 'Lead';
                    docname = values.lead;
                    break;
                case 'Customer':
                    doctype = 'Customer';
                    docname = values.customer;
                    break;
                case 'User':
                    doctype = 'User';
                    docname = values.user;
                    break;
            }
            
            frm.call({
                method: 'add_participant',
                doc: frm.doc,
                args: {
                    doctype: doctype,
                    docname: docname,
                    email: values.email,
                    name: values.name,
                    is_moderator: values.is_moderator
                },
                freeze: true,
                freeze_message: __('Adding participant...'),
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('Participant added'),
                            indicator: 'green'
                        });
                        d.hide();
                        frm.reload_doc();
                    }
                }
            });
        }
    });
    d.show();
}
