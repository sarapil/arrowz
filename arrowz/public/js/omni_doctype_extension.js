// Arrowz Omni-Channel DocType Extension
// Injects communication panel into supported DocTypes

frappe.provide("arrowz.omni");

// List of supported DocTypes
arrowz.omni.supported_doctypes = [
    "Lead",
    "Customer",
    "Contact",
    "Opportunity",
    "Prospect",
    "Supplier",
    "Sales Order",
    "Purchase Order",
    "Quotation",
    "Employee",
    "Address",
    "Sales Partner",
    "Issue",
    "Project",
    "Task"
];

// Initialize panel for each DocType
arrowz.omni.init = function(frm) {
    if (!arrowz.omni.supported_doctypes.includes(frm.doctype)) {
        return;
    }
    
    // Don't show for new documents
    if (frm.is_new()) {
        return;
    }
    
    // Add Omni-Channel section to sidebar or main form
    arrowz.omni.add_panel_section(frm);
    
    // Initialize the panel
    if (frm.omni_panel_wrapper) {
        frm.omni_panel = new arrowz.omni.CommunicationPanel({
            wrapper: frm.omni_panel_wrapper,
            frm: frm,
            doctype: frm.doctype,
            docname: frm.docname
        });
    }
};

arrowz.omni.add_panel_section = function(frm) {
    // Check if section already exists
    if (frm.omni_panel_wrapper) {
        return;
    }
    
    // Create a new section in the form
    const section = frm.dashboard.add_section(
        `<div class="omni-panel-container"></div>`,
        __("Communications")
    );
    
    if (section) {
        frm.omni_panel_wrapper = section.find('.omni-panel-container')[0];
    } else {
        // Fallback: Add after the form fields
        const wrapper = $('<div class="omni-panel-section frappe-control"></div>');
        wrapper.append(`
            <div class="section-head">${__("Communications")}</div>
            <div class="omni-panel-container"></div>
        `);
        
        frm.fields_dict[Object.keys(frm.fields_dict).pop()].$wrapper.after(wrapper);
        frm.omni_panel_wrapper = wrapper.find('.omni-panel-container')[0];
    }
};

// Refresh panel when document is refreshed
arrowz.omni.refresh = function(frm) {
    if (frm.omni_panel && !frm.is_new()) {
        frm.omni_panel.load_data();
    }
};

// Global DocType event handlers
$(document).on('app_ready', function() {
    // Hook into form events for all supported DocTypes
    arrowz.omni.supported_doctypes.forEach(doctype => {
        frappe.ui.form.on(doctype, {
            refresh: function(frm) {
                arrowz.omni.init(frm);
            },
            after_save: function(frm) {
                arrowz.omni.refresh(frm);
            }
        });
    });
});

// Communication stats indicator in list views
arrowz.omni.add_list_indicator = function(listview) {
    // Add unread count indicator to list items
    listview.page.add_inner_button(__("Unread Messages"), function() {
        // Filter by documents with unread messages
        frappe.call({
            method: "arrowz.api.communications.get_documents_with_unread",
            args: {
                doctype: listview.doctype
            },
            callback: function(r) {
                if (r.message && r.message.length) {
                    listview.filter_area.add([
                        [listview.doctype, "name", "in", r.message]
                    ]);
                } else {
                    frappe.msgprint(__("No documents with unread messages"));
                }
            }
        });
    });
};

// Quick communication actions for list view
arrowz.omni.list_actions = {
    whatsapp: function(doctype, docnames) {
        if (docnames.length !== 1) {
            frappe.msgprint(__("Please select exactly one document"));
            return;
        }
        
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: doctype,
                name: docnames[0],
                fieldname: ["mobile_no", "phone", "contact_mobile"]
            },
            callback: function(r) {
                if (r.message) {
                    const phone = r.message.mobile_no || r.message.phone || r.message.contact_mobile;
                    if (phone) {
                        // Open WhatsApp dialog
                        arrowz.omni.open_whatsapp_quick(phone, doctype, docnames[0]);
                    } else {
                        frappe.msgprint(__("No phone number found"));
                    }
                }
            }
        });
    },
    
    telegram: function(doctype, docnames) {
        frappe.msgprint(__("Telegram bulk messaging coming soon"));
    },
    
    call: function(doctype, docnames) {
        if (docnames.length !== 1) {
            frappe.msgprint(__("Please select exactly one document"));
            return;
        }
        
        frappe.call({
            method: "frappe.client.get_value",
            args: {
                doctype: doctype,
                name: docnames[0],
                fieldname: ["mobile_no", "phone"]
            },
            callback: function(r) {
                if (r.message) {
                    const phone = r.message.mobile_no || r.message.phone;
                    if (phone && window.arrowz && window.arrowz.softphone) {
                        window.arrowz.softphone.makeCall(phone);
                    } else {
                        frappe.msgprint(__("Softphone not available or no phone number found"));
                    }
                }
            }
        });
    }
};

arrowz.omni.open_whatsapp_quick = function(phone, doctype, docname) {
    const dialog = new frappe.ui.Dialog({
        title: __("Send WhatsApp Message"),
        fields: [
            {
                fieldname: "phone",
                fieldtype: "Data",
                label: __("Phone Number"),
                default: phone,
                read_only: 1
            },
            {
                fieldname: "template",
                fieldtype: "Link",
                label: __("Template"),
                options: "WhatsApp Templates",
                description: __("Template required for new conversations")
            },
            {
                fieldname: "message",
                fieldtype: "Small Text",
                label: __("Message (for active conversations)")
            }
        ],
        primary_action_label: __("Send"),
        primary_action: function(values) {
            frappe.call({
                method: "arrowz.api.communications.send_message",
                args: {
                    channel: "WhatsApp",
                    recipient: values.phone,
                    message: values.message,
                    message_type: values.template ? "template" : "text",
                    template_name: values.template,
                    reference_doctype: doctype,
                    reference_name: docname
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("Message sent"),
                            indicator: "green"
                        });
                        dialog.hide();
                    } else {
                        frappe.msgprint(r.message.message || __("Failed to send"));
                    }
                }
            });
        }
    });
    
    dialog.show();
};

// Notification badge in navbar
arrowz.omni.NotificationBadge = class NotificationBadge {
    constructor() {
        this.unread_count = 0;
        this.init();
    }
    
    init() {
        this.render();
        this.setup_realtime();
        this.fetch_count();
    }
    
    render() {
        // Add to navbar - Frappe v15 uses .navbar-nav inside .collapse.navbar-collapse
        let navbar = document.querySelector('.navbar .navbar-collapse .navbar-nav');
        if (!navbar) {
            navbar = document.querySelector('.navbar-right') || document.querySelector('.navbar-nav');
        }
        if (!navbar) return;
        
        this.badge_wrapper = document.createElement('li');
        this.badge_wrapper.className = 'nav-item dropdown omni-notification-badge';
        this.badge_wrapper.innerHTML = `
            <a class="nav-link" href="#" data-toggle="dropdown">
                <span class="omni-bell">💬</span>
                <span class="omni-badge" style="display: none;">0</span>
            </a>
            <div class="dropdown-menu dropdown-menu-right omni-notifications-dropdown">
                <div class="dropdown-header">${__("Messages")}</div>
                <div class="omni-notifications-list">
                    <div class="text-center text-muted p-3">${__("No new messages")}</div>
                </div>
                <div class="dropdown-divider"></div>
                <a class="dropdown-item text-center" href="/app/az-conversation-session">
                    ${__("View All Conversations")}
                </a>
            </div>
        `;
        
        navbar.insertBefore(this.badge_wrapper, navbar.firstChild);
        
        this.badge_el = this.badge_wrapper.querySelector('.omni-badge');
        this.notifications_list = this.badge_wrapper.querySelector('.omni-notifications-list');
    }
    
    setup_realtime() {
        frappe.realtime.on("new_message", (data) => {
            this.fetch_count();
            this.show_notification(data);
        });
        
        frappe.realtime.on("conversation_update", () => {
            this.fetch_count();
        });
    }
    
    async fetch_count() {
        try {
            const response = await frappe.call({
                method: "arrowz.api.communications.get_active_conversations",
                args: { 
                    user: frappe.session.user,
                    limit: 5 
                }
            });
            
            if (response.message) {
                const conversations = response.message;
                let total_unread = 0;
                
                conversations.forEach(c => {
                    total_unread += c.unread_count || 0;
                });
                
                this.update_badge(total_unread);
                this.update_list(conversations);
            }
        } catch (error) {
            console.error("Error fetching notification count:", error);
        }
    }
    
    update_badge(count) {
        this.unread_count = count;
        
        if (!this.badge_el) return;
        
        if (count > 0) {
            this.badge_el.textContent = count > 99 ? '99+' : count;
            this.badge_el.style.display = 'inline-block';
        } else {
            this.badge_el.style.display = 'none';
        }
    }
    
    update_list(conversations) {
        if (!this.notifications_list) return;
        
        if (!conversations || conversations.length === 0) {
            this.notifications_list.innerHTML = `
                <div class="text-center text-muted p-3">${__("No new messages")}</div>
            `;
            return;
        }
        
        let html = '';
        
        for (const conv of conversations) {
            const icon = conv.channel_type === 'WhatsApp' ? '💬' : 
                        conv.channel_type === 'Telegram' ? '✈️' : '📱';
            const badge = conv.unread_count > 0 ? 
                `<span class="badge badge-primary">${conv.unread_count}</span>` : '';
            
            html += `
                <a class="dropdown-item omni-notification-item" 
                   href="/app/az-conversation-session/${conv.name}">
                    <span class="notification-icon">${icon}</span>
                    <div class="notification-content">
                        <div class="notification-title">
                            ${conv.contact_name || conv.contact_number}
                            ${badge}
                        </div>
                        <div class="notification-preview">${conv.last_message || ''}</div>
                    </div>
                </a>
            `;
        }
        
        this.notifications_list.innerHTML = html;
    }
    
    show_notification(data) {
        if (Notification.permission === 'granted') {
            new Notification(`New ${data.channel} message`, {
                body: data.preview,
                icon: '/assets/arrowz/images/omni-icon.png',
                tag: data.session_id
            });
        }
        
        // Also show frappe notification
        frappe.show_alert({
            message: `${data.contact_name || data.contact_number}: ${data.preview}`,
            indicator: 'blue'
        }, 5);
    }
};

// Initialize notification badge on page load
$(document).on('app_ready', function() {
    if (frappe.session.user !== 'Guest') {
        new arrowz.omni.NotificationBadge();
    }
});

// Styles for notification badge
$('<style>')
    .text(`
        .omni-notification-badge .omni-bell {
            font-size: 18px;
        }
        
        .omni-notification-badge .omni-badge {
            position: absolute;
            top: 5px;
            right: 5px;
            background: var(--red);
            color: white;
            font-size: 10px;
            padding: 2px 5px;
            border-radius: 10px;
            min-width: 16px;
            text-align: center;
        }
        
        .omni-notifications-dropdown {
            width: 320px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .omni-notification-item {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 10px 15px !important;
            border-bottom: 1px solid var(--border-color);
        }
        
        .notification-icon {
            font-size: 24px;
        }
        
        .notification-content {
            flex: 1;
            min-width: 0;
        }
        
        .notification-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: 500;
        }
        
        .notification-preview {
            font-size: var(--text-sm);
            color: var(--text-muted);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
    `)
    .appendTo('head');
