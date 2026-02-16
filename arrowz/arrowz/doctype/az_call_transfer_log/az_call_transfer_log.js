// Copyright (c) 2026, Arrowz and contributors
// For license information, please see license.txt

frappe.ui.form.on('AZ Call Transfer Log', {
    refresh: function(frm) {
        // Status indicator
        const colors = {
            'Initiated': 'yellow',
            'Consulting': 'blue',
            'Completed': 'green',
            'Failed': 'red',
            'Cancelled': 'gray'
        };
        frm.page.set_indicator(frm.doc.status, colors[frm.doc.status] || 'gray');
        
        // Actions for in-progress transfers
        if (frm.doc.status === 'Consulting') {
            frm.add_custom_button(__('Complete Transfer'), function() {
                complete_transfer(frm);
            }, __('Actions'));
            
            frm.add_custom_button(__('Cancel Transfer'), function() {
                cancel_transfer(frm);
            }, __('Actions'));
        }
        
        // View original call
        if (frm.doc.call_log) {
            frm.add_custom_button(__('View Original Call'), function() {
                frappe.set_route('Form', 'AZ Call Log', frm.doc.call_log);
            });
        }
        
        // View new call after transfer
        if (frm.doc.new_call_log) {
            frm.add_custom_button(__('View New Call'), function() {
                frappe.set_route('Form', 'AZ Call Log', frm.doc.new_call_log);
            });
        }
        
        // Timeline
        setup_transfer_timeline(frm);
    }
});

function complete_transfer(frm) {
    frappe.call({
        method: 'arrowz.arrowz.doctype.az_call_transfer_log.az_call_transfer_log.complete_attended_transfer',
        args: {
            transfer_log: frm.doc.name
        },
        callback: function(r) {
            frm.reload_doc();
            frappe.show_alert({
                message: __('Transfer completed successfully'),
                indicator: 'green'
            });
        }
    });
}

function cancel_transfer(frm) {
    frappe.confirm(
        __('Are you sure you want to cancel this transfer?'),
        function() {
            frm.call('cancel_transfer').then(() => {
                frm.reload_doc();
            });
        }
    );
}

function setup_transfer_timeline(frm) {
    let timeline_html = '<div class="transfer-timeline">';
    
    if (frm.doc.initiated_at) {
        timeline_html += `<div class="timeline-item">
            <span class="indicator green"></span>
            <strong>Initiated</strong> - ${frappe.datetime.str_to_user(frm.doc.initiated_at)}
            <br><small>By ${frm.doc.initiated_by || 'Unknown'}</small>
        </div>`;
    }
    
    if (frm.doc.consultation_start) {
        timeline_html += `<div class="timeline-item">
            <span class="indicator blue"></span>
            <strong>Consultation Started</strong> - ${frappe.datetime.str_to_user(frm.doc.consultation_start)}
        </div>`;
    }
    
    if (frm.doc.consultation_ended) {
        timeline_html += `<div class="timeline-item">
            <span class="indicator blue"></span>
            <strong>Consultation Ended</strong> - ${frappe.datetime.str_to_user(frm.doc.consultation_ended)}
            <br><small>Duration: ${frm.doc.consultation_duration || 0} seconds</small>
        </div>`;
    }
    
    if (frm.doc.transfer_completed) {
        timeline_html += `<div class="timeline-item">
            <span class="indicator green"></span>
            <strong>Transfer Completed</strong> - ${frappe.datetime.str_to_user(frm.doc.transfer_completed)}
        </div>`;
    }
    
    if (frm.doc.status === 'Failed') {
        timeline_html += `<div class="timeline-item">
            <span class="indicator red"></span>
            <strong>Failed</strong>
            <br><small>${frm.doc.failure_reason || 'Unknown reason'}</small>
        </div>`;
    }
    
    timeline_html += '</div>';
    
    // Could add this to the form dashboard or a custom section
}
