// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

// Arrowz - Project DocType Extension
// Adds communication panel and quick actions

frappe.ui.form.on('Project', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            // Initialize Omni-Channel panel
            if (typeof arrowz.omni !== 'undefined') {
                arrowz.omni.init(frm);
            }
            
            // Add meeting scheduler button
            frm.add_custom_button(__('Schedule Meeting'), function() {
                const dialog = new frappe.ui.Dialog({
                    title: __('Schedule Project Meeting'),
                    fields: [
                        {
                            fieldname: 'room_name',
                            fieldtype: 'Data',
                            label: __('Meeting Name'),
                            default: `${frm.doc.project_name} - Meeting`,
                            reqd: 1
                        },
                        {
                            fieldname: 'scheduled_start',
                            fieldtype: 'Datetime',
                            label: __('Start Time'),
                            default: frappe.datetime.now_datetime(),
                            reqd: 1
                        },
                        {
                            fieldname: 'scheduled_end',
                            fieldtype: 'Datetime',
                            label: __('End Time')
                        },
                        {
                            fieldname: 'invite_team',
                            fieldtype: 'Check',
                            label: __('Invite Project Team'),
                            default: 1
                        }
                    ],
                    primary_action_label: __('Schedule'),
                    primary_action: async function(values) {
                        // Get project users if invite_team is checked
                        let participants = [];
                        
                        if (values.invite_team && frm.doc.users) {
                            for (const user of frm.doc.users) {
                                const user_doc = await frappe.db.get_value('User', user.user, 'email');
                                if (user_doc.message && user_doc.message.email) {
                                    participants.push({
                                        name: user.full_name || user.user,
                                        email: user_doc.message.email,
                                        is_moderator: user.user === frappe.session.user ? 1 : 0
                                    });
                                }
                            }
                        }
                        
                        frappe.call({
                            method: 'arrowz.api.communications.schedule_meeting',
                            args: {
                                reference_doctype: frm.doctype,
                                reference_name: frm.docname,
                                room_name: values.room_name,
                                scheduled_start: values.scheduled_start,
                                scheduled_end: values.scheduled_end,
                                participants: participants
                            },
                            callback: function(r) {
                                if (r.message && r.message.success) {
                                    frappe.show_alert({
                                        message: __('Meeting scheduled'),
                                        indicator: 'green'
                                    });
                                    dialog.hide();
                                    frappe.set_route('Form', 'AZ Meeting Room', r.message.room_id);
                                }
                            }
                        });
                    }
                });
                dialog.show();
            }, __('Communication'));
        }
    },
    
    after_save: function(frm) {
        if (typeof arrowz.omni !== 'undefined') {
            arrowz.omni.refresh(frm);
        }
    }
});
