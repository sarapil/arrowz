// Copyright (c) 2026, Arrowz and contributors
// For license information, please see license.txt

frappe.ui.form.on('AZ Call Log', {
    refresh: function(frm) {
        // Add status indicator
        frm.page.set_indicator(get_status_indicator(frm.doc.status), get_status_color(frm.doc.status));
        
        // Format duration display
        if (frm.doc.duration) {
            frm.set_df_property('duration', 'description', format_duration(frm.doc.duration));
        }
        
        // Recording controls
        if (frm.doc.has_recording) {
            frm.add_custom_button(__('▶ Play Recording'), function() {
                play_recording(frm);
            }, __('Recording'));
            
            frm.add_custom_button(__('⬇ Download'), function() {
                download_recording(frm);
            }, __('Recording'));
        }
        
        // AI Analysis button
        if (frm.doc.has_recording && !frm.doc.ai_summary) {
            frm.add_custom_button(__('🤖 Request AI Analysis'), function() {
                request_ai_analysis(frm);
            });
        }
        
        // CRM Integration
        if (frm.doc.party_type && frm.doc.party) {
            frm.add_custom_button(__('View ' + frm.doc.party_type), function() {
                frappe.set_route('Form', frm.doc.party_type, frm.doc.party);
            }, __('CRM'));
        } else if (frm.doc.caller_id || frm.doc.callee_id) {
            frm.add_custom_button(__('Create Lead'), function() {
                create_lead_from_call(frm);
            }, __('CRM'));
        }
        
        // Show sentiment badge
        if (frm.doc.sentiment_label) {
            show_sentiment_badge(frm);
        }
        
        // Timeline for call events
        setup_call_timeline(frm);
    },
    
    onload: function(frm) {
        // Setup realtime listeners for active calls
        if (frm.doc.status === 'In Progress' || frm.doc.status === 'Ringing') {
            setup_realtime_listener(frm);
        }
    },
    
    party_type: function(frm) {
        // Clear party when type changes
        frm.set_value('party', '');
    }
});

function get_status_indicator(status) {
    const indicators = {
        'Ringing': __('Ringing'),
        'In Progress': __('In Progress'),
        'On Hold': __('On Hold'),
        'Completed': __('Completed'),
        'Missed': __('Missed'),
        'Failed': __('Failed')
    };
    return indicators[status] || status;
}

function get_status_color(status) {
    const colors = {
        'Ringing': 'yellow',
        'In Progress': 'blue',
        'On Hold': 'orange',
        'Completed': 'green',
        'Missed': 'red',
        'Failed': 'red'
    };
    return colors[status] || 'gray';
}

function format_duration(seconds) {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    const hrs = Math.floor(mins / 60);
    
    if (hrs > 0) {
        return `${hrs}:${String(mins % 60).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    return `${mins}:${String(secs).padStart(2, '0')}`;
}

function play_recording(frm) {
    // Create audio player modal
    let d = new frappe.ui.Dialog({
        title: __('Call Recording'),
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'player_html',
                options: `
                    <div class="recording-player">
                        <div class="call-info mb-3">
                            <strong>${frm.doc.direction}</strong> call with 
                            <strong>${frm.doc.contact_name || frm.doc.caller_id}</strong>
                            <br><small class="text-muted">${frappe.datetime.str_to_user(frm.doc.start_time)}</small>
                        </div>
                        <audio id="call-recording-audio" controls style="width: 100%;">
                            <source src="/api/method/arrowz.api.recording.stream?call_log=${frm.doc.name}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                        <div class="duration-info mt-2 text-center text-muted">
                            Duration: ${format_duration(frm.doc.recording_duration || frm.doc.duration)}
                        </div>
                    </div>
                `
            }
        ],
        primary_action_label: __('Close'),
        primary_action: function() {
            d.hide();
        }
    });
    
    d.show();
}

function download_recording(frm) {
    window.open(`/api/method/arrowz.api.recording.download?call_log=${frm.doc.name}`, '_blank');
}

function request_ai_analysis(frm) {
    frappe.call({
        method: 'request_ai_analysis',
        doc: frm.doc,
        freeze: true,
        freeze_message: __('Queuing AI Analysis...'),
        callback: function(r) {
            if (r.message && r.message.status === 'queued') {
                frappe.show_alert({
                    message: __('AI analysis has been queued. Results will appear shortly.'),
                    indicator: 'green'
                }, 5);
            }
        }
    });
}

function create_lead_from_call(frm) {
    const phone = frm.doc.direction === 'Inbound' ? frm.doc.caller_id : frm.doc.callee_id;
    
    frappe.new_doc('Lead', {
        mobile_no: phone,
        source: 'Phone Call',
        notes: `Created from call: ${frm.doc.name}\n\nCall Notes:\n${frm.doc.notes || '(No notes)'}`
    });
}

function show_sentiment_badge(frm) {
    const sentiment = frm.doc.sentiment_label;
    const score = frm.doc.sentiment_score;
    
    let badge_class = 'badge-secondary';
    let emoji = '😐';
    
    if (sentiment === 'Positive') {
        badge_class = 'badge-success';
        emoji = '😊';
    } else if (sentiment === 'Negative') {
        badge_class = 'badge-danger';
        emoji = '😞';
    }
    
    const badge_html = `
        <span class="badge ${badge_class}" style="font-size: 14px;">
            ${emoji} ${sentiment} (${score ? score.toFixed(2) : 'N/A'})
        </span>
    `;
    
    frm.dashboard.add_comment(badge_html, 'blue', true);
}

function setup_call_timeline(frm) {
    // Add timeline events for call progression
    let events = [];
    
    if (frm.doc.start_time) {
        events.push({
            time: frm.doc.start_time,
            label: frm.doc.direction === 'Inbound' ? 'Call Received' : 'Call Initiated'
        });
    }
    
    if (frm.doc.answer_time) {
        events.push({
            time: frm.doc.answer_time,
            label: 'Call Answered'
        });
    }
    
    if (frm.doc.was_transferred && frm.doc.transfer_time) {
        events.push({
            time: frm.doc.transfer_time,
            label: `Transferred (${frm.doc.transfer_type}) to ${frm.doc.transferred_to}`
        });
    }
    
    if (frm.doc.end_time) {
        events.push({
            time: frm.doc.end_time,
            label: 'Call Ended - ' + frm.doc.disposition
        });
    }
    
    // Timeline HTML would be rendered here if needed
}

function setup_realtime_listener(frm) {
    // Listen for call updates
    frappe.realtime.on('call_update_' + frm.doc.name, function(data) {
        if (data.status) {
            frm.doc.status = data.status;
        }
        if (data.duration) {
            frm.doc.duration = data.duration;
        }
        frm.refresh();
    });
    
    frappe.realtime.on('call_ended', function(data) {
        if (data.call_log === frm.doc.name) {
            frm.reload_doc();
        }
    });
}
