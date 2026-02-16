// Arrowz Omni-Channel Communication Panel
// Vue.js component for unified communications view across all DocTypes

frappe.provide("arrowz.omni");

arrowz.omni.CommunicationPanel = class CommunicationPanel {
    constructor(opts) {
        this.wrapper = opts.wrapper;
        this.frm = opts.frm;
        this.doctype = opts.doctype;
        this.docname = opts.docname;
        
        this.channels = ["WhatsApp", "Telegram", "Email", "Phone", "Video"];
        this.active_channel = null;
        this.active_session = null;
        this.communications = [];
        this.stats = {};
        
        this.setup();
    }
    
    setup() {
        this.render_panel();
        this.setup_realtime();
        this.load_data();
    }
    
    render_panel() {
        this.wrapper.innerHTML = `
            <div class="arrowz-omni-panel">
                <!-- Channel Tabs -->
                <div class="omni-channel-tabs">
                    <div class="channel-tab active" data-channel="all">
                        <span class="channel-icon">📱</span>
                        <span class="channel-name">${__("All")}</span>
                        <span class="channel-badge total-badge">0</span>
                    </div>
                    <div class="channel-tab" data-channel="WhatsApp">
                        <span class="channel-icon">💬</span>
                        <span class="channel-name">WhatsApp</span>
                        <span class="channel-badge whatsapp-badge">0</span>
                    </div>
                    <div class="channel-tab" data-channel="Telegram">
                        <span class="channel-icon">✈️</span>
                        <span class="channel-name">Telegram</span>
                        <span class="channel-badge telegram-badge">0</span>
                    </div>
                    <div class="channel-tab" data-channel="Email">
                        <span class="channel-icon">📧</span>
                        <span class="channel-name">${__("Email")}</span>
                        <span class="channel-badge email-badge">0</span>
                    </div>
                    <div class="channel-tab" data-channel="Phone">
                        <span class="channel-icon">📞</span>
                        <span class="channel-name">${__("Phone")}</span>
                        <span class="channel-badge phone-badge">0</span>
                    </div>
                    <div class="channel-tab" data-channel="Video">
                        <span class="channel-icon">🎥</span>
                        <span class="channel-name">${__("Video")}</span>
                        <span class="channel-badge video-badge">0</span>
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div class="omni-quick-actions">
                    <button class="btn btn-xs btn-primary action-whatsapp" title="Send WhatsApp">
                        <i class="fa fa-whatsapp"></i>
                    </button>
                    <button class="btn btn-xs btn-info action-telegram" title="Send Telegram">
                        <i class="fa fa-telegram"></i>
                    </button>
                    <button class="btn btn-xs btn-default action-email" title="Send Email">
                        <i class="fa fa-envelope"></i>
                    </button>
                    <button class="btn btn-xs btn-success action-call" title="Make Call">
                        <i class="fa fa-phone"></i>
                    </button>
                    <button class="btn btn-xs btn-warning action-meeting" title="Schedule Meeting">
                        <i class="fa fa-video-camera"></i>
                    </button>
                </div>
                
                <!-- Communications List -->
                <div class="omni-communications-list">
                    <div class="loading-indicator">
                        <i class="fa fa-spinner fa-spin"></i> ${__("Loading...")}
                    </div>
                </div>
                
                <!-- Chat View (Hidden by default) -->
                <div class="omni-chat-view" style="display: none;">
                    <div class="chat-header">
                        <button class="btn btn-xs btn-default chat-back">
                            <i class="fa fa-arrow-left"></i>
                        </button>
                        <div class="chat-contact-info">
                            <div class="chat-contact-name"></div>
                            <div class="chat-contact-number"></div>
                        </div>
                        <div class="chat-actions">
                            <button class="btn btn-xs btn-default chat-assign" title="${__("Assign")}">
                                <i class="fa fa-user-plus"></i>
                            </button>
                            <button class="btn btn-xs btn-danger chat-close" title="${__("Close")}">
                                <i class="fa fa-times"></i>
                            </button>
                        </div>
                    </div>
                    <div class="chat-messages"></div>
                    <div class="chat-input">
                        <div class="chat-quick-replies"></div>
                        <div class="chat-input-row">
                            <button class="btn btn-xs btn-default chat-attach">
                                <i class="fa fa-paperclip"></i>
                            </button>
                            <input type="text" class="form-control chat-message-input" 
                                   placeholder="${__("Type a message...")}" />
                            <button class="btn btn-primary chat-send">
                                <i class="fa fa-send"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.bind_events();
    }
    
    bind_events() {
        const panel = this.wrapper.querySelector('.arrowz-omni-panel');
        
        // Channel tab switching
        panel.querySelectorAll('.channel-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.switch_channel(tab.dataset.channel);
            });
        });
        
        // Quick actions
        panel.querySelector('.action-whatsapp').addEventListener('click', () => {
            this.open_whatsapp_dialog();
        });
        
        panel.querySelector('.action-telegram').addEventListener('click', () => {
            this.open_telegram_dialog();
        });
        
        panel.querySelector('.action-email').addEventListener('click', () => {
            this.open_email_composer();
        });
        
        panel.querySelector('.action-call').addEventListener('click', () => {
            this.initiate_call();
        });
        
        panel.querySelector('.action-meeting').addEventListener('click', () => {
            this.schedule_meeting();
        });
        
        // Chat view events
        panel.querySelector('.chat-back').addEventListener('click', () => {
            this.close_chat_view();
        });
        
        panel.querySelector('.chat-send').addEventListener('click', () => {
            this.send_chat_message();
        });
        
        panel.querySelector('.chat-message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.send_chat_message();
            }
        });
        
        panel.querySelector('.chat-assign').addEventListener('click', () => {
            this.assign_conversation();
        });
        
        panel.querySelector('.chat-close').addEventListener('click', () => {
            this.close_conversation();
        });
    }
    
    setup_realtime() {
        // Listen for new messages
        frappe.realtime.on("new_message", (data) => {
            if (data.reference_doctype === this.doctype && 
                data.reference_name === this.docname) {
                this.handle_new_message(data);
            }
        });
        
        // Listen for message status updates
        frappe.realtime.on("message_status", (data) => {
            this.update_message_status(data);
        });
        
        // Listen for conversation updates
        frappe.realtime.on("conversation_update", (data) => {
            this.load_data();
        });
    }
    
    async load_data() {
        try {
            const response = await frappe.call({
                method: "arrowz.api.communications.get_communication_history",
                args: {
                    doctype: this.doctype,
                    docname: this.docname,
                    channels: this.active_channel === 'all' ? null : [this.active_channel]
                }
            });
            
            if (response.message) {
                this.communications = response.message.communications;
                this.stats = response.message.stats;
                this.render_communications();
                this.update_badges();
            }
        } catch (error) {
            console.error("Error loading communications:", error);
            this.show_error(__("Failed to load communications"));
        }
    }
    
    render_communications() {
        const list = this.wrapper.querySelector('.omni-communications-list');
        
        if (!this.communications || this.communications.length === 0) {
            list.innerHTML = `
                <div class="empty-state">
                    <i class="fa fa-comments-o fa-3x"></i>
                    <p>${__("No communications yet")}</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        for (const comm of this.communications) {
            html += this.render_communication_item(comm);
        }
        
        list.innerHTML = html;
        
        // Bind click events
        list.querySelectorAll('.comm-item').forEach(item => {
            item.addEventListener('click', () => {
                this.open_communication(item.dataset);
            });
        });
    }
    
    render_communication_item(comm) {
        const icon = this.get_channel_icon(comm.channel);
        const time = frappe.datetime.prettyDate(comm.last_activity);
        const unread = comm.unread_count > 0 ? `<span class="unread-badge">${comm.unread_count}</span>` : '';
        
        let preview = '';
        let subtitle = '';
        
        switch (comm.type) {
            case 'conversation':
                preview = comm.messages && comm.messages[0] ? 
                    this.truncate(comm.messages[0].content, 50) : '';
                subtitle = comm.contact_name || comm.contact_number;
                break;
            case 'email':
                preview = comm.subject;
                subtitle = comm.direction === 'outgoing' ? `To: ${comm.to}` : `From: ${comm.from}`;
                break;
            case 'call':
                preview = `${comm.call_type} - ${this.format_duration(comm.duration)}`;
                subtitle = comm.direction === 'outgoing' ? comm.receiver : comm.caller;
                break;
            case 'meeting':
                preview = comm.room_name;
                subtitle = `${comm.participants} participants`;
                break;
        }
        
        return `
            <div class="comm-item ${comm.unread_count > 0 ? 'unread' : ''}" 
                 data-type="${comm.type}" 
                 data-channel="${comm.channel}"
                 data-id="${comm.session_id || comm.id}">
                <div class="comm-icon">${icon}</div>
                <div class="comm-content">
                    <div class="comm-header">
                        <span class="comm-subtitle">${subtitle}</span>
                        <span class="comm-time">${time}</span>
                    </div>
                    <div class="comm-preview">${preview}</div>
                </div>
                <div class="comm-status">
                    ${unread}
                    ${this.get_status_icon(comm.status)}
                </div>
            </div>
        `;
    }
    
    get_channel_icon(channel) {
        const icons = {
            'WhatsApp': '💬',
            'Telegram': '✈️',
            'Email': '📧',
            'Phone': '📞',
            'Video': '🎥'
        };
        return icons[channel] || '📱';
    }
    
    get_status_icon(status) {
        const icons = {
            'Active': '<i class="fa fa-circle text-success"></i>',
            'Pending': '<i class="fa fa-circle text-warning"></i>',
            'Closed': '<i class="fa fa-circle text-muted"></i>',
            'Scheduled': '<i class="fa fa-clock-o text-info"></i>',
            'In Progress': '<i class="fa fa-spinner text-primary"></i>',
            'Ended': '<i class="fa fa-check text-success"></i>'
        };
        return icons[status] || '';
    }
    
    update_badges() {
        const channels = this.stats.channels || {};
        
        // Total badge
        this.wrapper.querySelector('.total-badge').textContent = 
            this.stats.total_unread || 0;
        
        // WhatsApp badge
        if (channels.whatsapp) {
            this.wrapper.querySelector('.whatsapp-badge').textContent = 
                channels.whatsapp.unread || 0;
        }
        
        // Telegram badge
        if (channels.telegram) {
            this.wrapper.querySelector('.telegram-badge').textContent = 
                channels.telegram.unread || 0;
        }
        
        // Email badge
        if (channels.email) {
            this.wrapper.querySelector('.email-badge').textContent = 
                channels.email.unread || 0;
        }
        
        // Phone badge (missed calls)
        if (channels.phone) {
            this.wrapper.querySelector('.phone-badge').textContent = 
                channels.phone.missed || 0;
        }
        
        // Video badge (upcoming meetings)
        if (channels.video) {
            this.wrapper.querySelector('.video-badge').textContent = 
                channels.video.upcoming || 0;
        }
    }
    
    switch_channel(channel) {
        // Update active tab
        this.wrapper.querySelectorAll('.channel-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.channel === channel);
        });
        
        this.active_channel = channel === 'all' ? null : channel;
        this.load_data();
    }
    
    open_communication(data) {
        if (data.type === 'conversation') {
            this.open_chat_view(data.id);
        } else if (data.type === 'email') {
            frappe.set_route('Form', 'Communication', data.id);
        } else if (data.type === 'call') {
            frappe.set_route('Form', 'Call Log', data.id);
        } else if (data.type === 'meeting') {
            frappe.set_route('Form', 'AZ Meeting Room', data.id);
        }
    }
    
    async open_chat_view(session_id) {
        this.active_session = session_id;
        
        // Hide list, show chat
        this.wrapper.querySelector('.omni-communications-list').style.display = 'none';
        this.wrapper.querySelector('.omni-quick-actions').style.display = 'none';
        this.wrapper.querySelector('.omni-chat-view').style.display = 'flex';
        
        // Load messages
        try {
            const response = await frappe.call({
                method: "arrowz.api.communications.get_conversation_messages",
                args: { session_id }
            });
            
            if (response.message) {
                this.render_chat(response.message);
                this.load_quick_replies(response.message.session.channel_type);
                
                // Mark as read
                frappe.call({
                    method: "arrowz.api.communications.mark_messages_read",
                    args: { session_id }
                });
            }
        } catch (error) {
            console.error("Error loading chat:", error);
            frappe.msgprint(__("Failed to load conversation"));
        }
    }
    
    render_chat(data) {
        const session = data.session;
        const messages = data.messages;
        
        // Update header
        this.wrapper.querySelector('.chat-contact-name').textContent = 
            session.contact_name || __("Unknown");
        this.wrapper.querySelector('.chat-contact-number').textContent = 
            session.contact_number;
        
        // Render messages
        const container = this.wrapper.querySelector('.chat-messages');
        let html = '';
        
        for (const msg of messages) {
            html += this.render_chat_message(msg);
        }
        
        container.innerHTML = html;
        container.scrollTop = container.scrollHeight;
    }
    
    render_chat_message(msg) {
        const direction = msg.direction.toLowerCase();
        const time = frappe.datetime.str_to_user(msg.timestamp, true);
        const status = this.get_message_status_icon(msg.status);
        
        let content = '';
        
        switch (msg.message_type.toLowerCase()) {
            case 'text':
                content = `<div class="msg-text">${frappe.utils.escape_html(msg.content)}</div>`;
                break;
            case 'image':
                content = `
                    <div class="msg-image">
                        <img src="${msg.media_url}" alt="Image" />
                        ${msg.content ? `<div class="msg-caption">${msg.content}</div>` : ''}
                    </div>
                `;
                break;
            case 'document':
                content = `
                    <div class="msg-document">
                        <i class="fa fa-file"></i>
                        <a href="${msg.media_url}" target="_blank">${msg.media_filename || 'Document'}</a>
                    </div>
                `;
                break;
            case 'audio':
                content = `
                    <div class="msg-audio">
                        <audio controls src="${msg.media_url}"></audio>
                    </div>
                `;
                break;
            case 'video':
                content = `
                    <div class="msg-video">
                        <video controls src="${msg.media_url}"></video>
                    </div>
                `;
                break;
            case 'location':
                content = `
                    <div class="msg-location">
                        <i class="fa fa-map-marker"></i>
                        <a href="${msg.content}" target="_blank">${__("View Location")}</a>
                    </div>
                `;
                break;
            default:
                content = `<div class="msg-text">${msg.content || `[${msg.message_type}]`}</div>`;
        }
        
        return `
            <div class="chat-message ${direction}" data-id="${msg.message_id}">
                ${content}
                <div class="msg-meta">
                    <span class="msg-time">${time}</span>
                    ${direction === 'outgoing' ? `<span class="msg-status">${status}</span>` : ''}
                </div>
            </div>
        `;
    }
    
    get_message_status_icon(status) {
        const icons = {
            'Sent': '✓',
            'Delivered': '✓✓',
            'Read': '<span class="text-primary">✓✓</span>',
            'Failed': '<span class="text-danger">!</span>'
        };
        return icons[status] || '';
    }
    
    async load_quick_replies(channel_type) {
        try {
            const response = await frappe.call({
                method: "arrowz.api.communications.get_quick_replies",
                args: { channel_type }
            });
            
            if (response.message) {
                const container = this.wrapper.querySelector('.chat-quick-replies');
                container.innerHTML = response.message.map(reply => 
                    `<button class="btn btn-xs btn-default quick-reply" data-message="${reply.message}">
                        ${reply.label}
                    </button>`
                ).join('');
                
                container.querySelectorAll('.quick-reply').forEach(btn => {
                    btn.addEventListener('click', () => {
                        this.wrapper.querySelector('.chat-message-input').value = btn.dataset.message;
                    });
                });
            }
        } catch (error) {
            console.error("Error loading quick replies:", error);
        }
    }
    
    async send_chat_message() {
        const input = this.wrapper.querySelector('.chat-message-input');
        const message = input.value.trim();
        
        if (!message || !this.active_session) return;
        
        input.value = '';
        
        try {
            // Get session details
            const session = await frappe.db.get_doc("AZ Conversation Session", this.active_session);
            
            const response = await frappe.call({
                method: "arrowz.api.communications.send_message",
                args: {
                    channel: session.channel_type,
                    recipient: session.contact_number,
                    message: message,
                    reference_doctype: this.doctype,
                    reference_name: this.docname
                }
            });
            
            if (response.message && response.message.success) {
                // Refresh chat
                this.open_chat_view(this.active_session);
            } else {
                frappe.msgprint(__("Failed to send message"));
            }
        } catch (error) {
            console.error("Error sending message:", error);
            frappe.msgprint(__("Failed to send message"));
        }
    }
    
    close_chat_view() {
        this.active_session = null;
        
        // Show list, hide chat
        this.wrapper.querySelector('.omni-communications-list').style.display = 'block';
        this.wrapper.querySelector('.omni-quick-actions').style.display = 'flex';
        this.wrapper.querySelector('.omni-chat-view').style.display = 'none';
        
        // Reload data
        this.load_data();
    }
    
    handle_new_message(data) {
        if (this.active_session === data.session_id) {
            // Append message to chat
            const container = this.wrapper.querySelector('.chat-messages');
            container.innerHTML += this.render_chat_message(data.message);
            container.scrollTop = container.scrollHeight;
        } else {
            // Update badges
            this.load_data();
        }
    }
    
    update_message_status(data) {
        const msgEl = this.wrapper.querySelector(`[data-id="${data.message_id}"]`);
        if (msgEl) {
            const statusEl = msgEl.querySelector('.msg-status');
            if (statusEl) {
                statusEl.innerHTML = this.get_message_status_icon(data.status);
            }
        }
    }
    
    // Quick Actions
    
    open_whatsapp_dialog() {
        const phone = this.get_contact_phone();
        
        const dialog = new frappe.ui.Dialog({
            title: __("Send WhatsApp Message"),
            fields: [
                {
                    fieldname: "phone",
                    fieldtype: "Data",
                    label: __("Phone Number"),
                    default: phone,
                    reqd: 1
                },
                {
                    fieldname: "use_template",
                    fieldtype: "Check",
                    label: __("Use Template (required if 24h window expired)")
                },
                {
                    fieldname: "template_section",
                    fieldtype: "Section Break",
                    depends_on: "eval:doc.use_template"
                },
                {
                    fieldname: "template",
                    fieldtype: "Link",
                    label: __("Template"),
                    options: "WhatsApp Templates",
                    depends_on: "eval:doc.use_template"
                },
                {
                    fieldname: "message_section",
                    fieldtype: "Section Break",
                    depends_on: "eval:!doc.use_template"
                },
                {
                    fieldname: "message",
                    fieldtype: "Small Text",
                    label: __("Message"),
                    depends_on: "eval:!doc.use_template"
                }
            ],
            primary_action_label: __("Send"),
            primary_action: async (values) => {
                try {
                    const response = await frappe.call({
                        method: "arrowz.api.communications.send_message",
                        args: {
                            channel: "WhatsApp",
                            recipient: values.phone,
                            message: values.message,
                            message_type: values.use_template ? "template" : "text",
                            template_name: values.template,
                            reference_doctype: this.doctype,
                            reference_name: this.docname
                        }
                    });
                    
                    if (response.message && response.message.success) {
                        frappe.show_alert({
                            message: __("Message sent successfully"),
                            indicator: "green"
                        });
                        dialog.hide();
                        this.load_data();
                    } else {
                        frappe.msgprint(response.message.message || __("Failed to send message"));
                    }
                } catch (error) {
                    frappe.msgprint(__("Failed to send message"));
                }
            }
        });
        
        dialog.show();
    }
    
    open_telegram_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: __("Send Telegram Message"),
            fields: [
                {
                    fieldname: "chat_id",
                    fieldtype: "Data",
                    label: __("Chat ID / Username"),
                    reqd: 1
                },
                {
                    fieldname: "message",
                    fieldtype: "Small Text",
                    label: __("Message"),
                    reqd: 1
                }
            ],
            primary_action_label: __("Send"),
            primary_action: async (values) => {
                try {
                    const response = await frappe.call({
                        method: "arrowz.api.communications.send_message",
                        args: {
                            channel: "Telegram",
                            recipient: values.chat_id,
                            message: values.message,
                            reference_doctype: this.doctype,
                            reference_name: this.docname
                        }
                    });
                    
                    if (response.message && response.message.success) {
                        frappe.show_alert({
                            message: __("Message sent successfully"),
                            indicator: "green"
                        });
                        dialog.hide();
                        this.load_data();
                    }
                } catch (error) {
                    frappe.msgprint(__("Failed to send message"));
                }
            }
        });
        
        dialog.show();
    }
    
    open_email_composer() {
        const email = this.get_contact_email();
        
        new frappe.views.CommunicationComposer({
            doc: this.frm.doc,
            frm: this.frm,
            subject: `${this.frm.doc.doctype}: ${this.frm.doc.name}`,
            recipients: email,
            attach_document_print: false
        });
    }
    
    initiate_call() {
        const phone = this.get_contact_phone();
        
        if (phone && window.arrowz && window.arrowz.softphone) {
            window.arrowz.softphone.makeCall(phone);
        } else {
            frappe.msgprint(__("Softphone not available or no phone number found"));
        }
    }
    
    schedule_meeting() {
        const dialog = new frappe.ui.Dialog({
            title: __("Schedule Video Meeting"),
            fields: [
                {
                    fieldname: "room_name",
                    fieldtype: "Data",
                    label: __("Meeting Name"),
                    default: `Meeting - ${this.frm.doc.name}`,
                    reqd: 1
                },
                {
                    fieldname: "scheduled_start",
                    fieldtype: "Datetime",
                    label: __("Start Time"),
                    default: frappe.datetime.now_datetime(),
                    reqd: 1
                },
                {
                    fieldname: "scheduled_end",
                    fieldtype: "Datetime",
                    label: __("End Time")
                },
                {
                    fieldname: "participants_section",
                    fieldtype: "Section Break",
                    label: __("Participants")
                },
                {
                    fieldname: "participants",
                    fieldtype: "Table",
                    label: __("Participants"),
                    fields: [
                        {
                            fieldname: "name",
                            fieldtype: "Data",
                            label: __("Name"),
                            in_list_view: 1
                        },
                        {
                            fieldname: "email",
                            fieldtype: "Data",
                            label: __("Email"),
                            in_list_view: 1,
                            reqd: 1
                        },
                        {
                            fieldname: "is_moderator",
                            fieldtype: "Check",
                            label: __("Moderator"),
                            in_list_view: 1
                        }
                    ]
                }
            ],
            primary_action_label: __("Schedule"),
            primary_action: async (values) => {
                try {
                    const response = await frappe.call({
                        method: "arrowz.api.communications.schedule_meeting",
                        args: {
                            reference_doctype: this.doctype,
                            reference_name: this.docname,
                            room_name: values.room_name,
                            scheduled_start: values.scheduled_start,
                            scheduled_end: values.scheduled_end,
                            participants: values.participants
                        }
                    });
                    
                    if (response.message && response.message.success) {
                        frappe.show_alert({
                            message: __("Meeting scheduled successfully"),
                            indicator: "green"
                        });
                        dialog.hide();
                        this.load_data();
                        
                        // Open the meeting room
                        frappe.set_route('Form', 'AZ Meeting Room', response.message.room_id);
                    }
                } catch (error) {
                    frappe.msgprint(__("Failed to schedule meeting"));
                }
            }
        });
        
        dialog.show();
    }
    
    assign_conversation() {
        if (!this.active_session) return;
        
        const dialog = new frappe.ui.Dialog({
            title: __("Assign Conversation"),
            fields: [
                {
                    fieldname: "user",
                    fieldtype: "Link",
                    label: __("Assign To"),
                    options: "User",
                    reqd: 1
                }
            ],
            primary_action_label: __("Assign"),
            primary_action: async (values) => {
                try {
                    await frappe.call({
                        method: "arrowz.api.communications.assign_conversation",
                        args: {
                            session_id: this.active_session,
                            user: values.user
                        }
                    });
                    
                    frappe.show_alert({
                        message: __("Conversation assigned"),
                        indicator: "green"
                    });
                    dialog.hide();
                } catch (error) {
                    frappe.msgprint(__("Failed to assign conversation"));
                }
            }
        });
        
        dialog.show();
    }
    
    close_conversation() {
        if (!this.active_session) return;
        
        frappe.confirm(
            __("Are you sure you want to close this conversation?"),
            async () => {
                try {
                    await frappe.call({
                        method: "arrowz.api.communications.close_conversation",
                        args: { session_id: this.active_session }
                    });
                    
                    frappe.show_alert({
                        message: __("Conversation closed"),
                        indicator: "green"
                    });
                    
                    this.close_chat_view();
                } catch (error) {
                    frappe.msgprint(__("Failed to close conversation"));
                }
            }
        );
    }
    
    // Helpers
    
    get_contact_phone() {
        const doc = this.frm.doc;
        
        // Try to find phone number from different fields
        const phone_fields = ['mobile_no', 'phone', 'contact_mobile', 'contact_phone', 
                             'cell_number', 'mobile', 'whatsapp_number'];
        
        for (const field of phone_fields) {
            if (doc[field]) {
                return doc[field];
            }
        }
        
        return '';
    }
    
    get_contact_email() {
        const doc = this.frm.doc;
        
        // Try to find email from different fields
        const email_fields = ['email_id', 'email', 'contact_email', 'personal_email',
                             'company_email', 'email_address'];
        
        for (const field of email_fields) {
            if (doc[field]) {
                return doc[field];
            }
        }
        
        return '';
    }
    
    truncate(str, length) {
        if (!str) return '';
        return str.length > length ? str.substring(0, length) + '...' : str;
    }
    
    format_duration(seconds) {
        if (!seconds) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    show_error(message) {
        this.wrapper.querySelector('.omni-communications-list').innerHTML = `
            <div class="error-state">
                <i class="fa fa-exclamation-triangle text-danger"></i>
                <p>${message}</p>
                <button class="btn btn-xs btn-default" onclick="this.parentElement.parentElement.querySelector('.omni-panel').load_data()">
                    ${__("Retry")}
                </button>
            </div>
        `;
    }
};
