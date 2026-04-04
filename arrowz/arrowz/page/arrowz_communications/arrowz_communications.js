// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Arrowz Communications Hub
 * Professional unified communications dashboard with gradient design
 */

frappe.pages['arrowz-communications'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Communications Hub'),
        single_column: true
    });
    
    wrapper.classList.add('arrowz-communications-page');
    wrapper.comms = new ArrowzCommunications(page);
};

class ArrowzCommunications {
    constructor(page) {
        this.page = page;
        this.active_tab = 'calls';
        this.init();
    }
    
    init() {
        this.add_styles();
        this.render_layout();
        this.setup_events();
        this.refresh();
    }
    
    add_styles() {
        if (document.getElementById('arrowz-comms-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'arrowz-comms-styles';
        styles.textContent = `
            .arrowz-communications-page .page-content {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                min-height: calc(100vh - 60px);
            }
            
            .az-comms {
                padding: 24px;
            }
            
            /* Header Banner */
            .az-comms-header {
                background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 100%);
                border-radius: 20px;
                padding: 32px;
                margin-bottom: 24px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
            }
            
            .az-comms-title {
                display: flex;
                align-items: center;
                gap: 16px;
            }
            
            .az-comms-icon {
                width: 64px;
                height: 64px;
                background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                border-radius: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
            }
            
            .az-comms-title h1 {
                margin: 0;
                color: white;
                font-size: 28px;
            }
            
            .az-comms-title p {
                margin: 4px 0 0;
                color: rgba(255,255,255,0.7);
            }
            
            /* Stats Row */
            .az-comms-stats {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                margin-bottom: 24px;
            }
            
            .az-comms-stat {
                background: rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                backdrop-filter: blur(5px);
            }
            
            .az-comms-stat-value {
                font-size: 32px;
                font-weight: 700;
                color: white;
            }
            
            .az-comms-stat-label {
                font-size: 12px;
                color: rgba(255,255,255,0.7);
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            /* Tabs */
            .az-comms-tabs {
                display: flex;
                gap: 8px;
                margin-bottom: 24px;
                background: rgba(0,0,0,0.2);
                padding: 8px;
                border-radius: 12px;
            }
            
            .az-comms-tab {
                flex: 1;
                padding: 12px 20px;
                border: none;
                border-radius: 8px;
                background: transparent;
                color: rgba(255,255,255,0.6);
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }
            
            .az-comms-tab:hover {
                color: white;
                background: rgba(255,255,255,0.1);
            }
            
            .az-comms-tab.active {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .az-comms-tab-icon {
                font-size: 20px;
            }
            
            .az-comms-tab-badge {
                background: rgba(255,255,255,0.2);
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 12px;
            }
            
            /* Content Area */
            .az-comms-content {
                background: white;
                border-radius: 16px;
                min-height: 400px;
                overflow: hidden;
            }
            
            .az-comms-pane {
                display: none;
                padding: 24px;
            }
            
            .az-comms-pane.active {
                display: block;
            }
            
            /* Search Bar */
            .az-comms-search {
                display: flex;
                gap: 12px;
                margin-bottom: 20px;
            }
            
            .az-comms-search input {
                flex: 1;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                font-size: 14px;
                transition: border-color 0.2s;
            }
            
            .az-comms-search input:focus {
                border-color: #667eea;
                outline: none;
            }
            
            .az-comms-search button {
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: 500;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            .az-comms-search button:hover {
                transform: scale(1.02);
            }
            
            /* List Items */
            .az-comms-list {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .az-comms-item {
                display: flex;
                align-items: center;
                padding: 16px;
                border-radius: 12px;
                background: #f8f9fa;
                transition: all 0.2s;
                cursor: pointer;
            }
            
            .az-comms-item:hover {
                background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
                transform: translateX(4px);
            }
            
            .az-comms-item-icon {
                width: 48px;
                height: 48px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                margin-right: 16px;
            }
            
            .az-comms-item-icon.inbound {
                background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            }
            
            .az-comms-item-icon.outbound {
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            }
            
            .az-comms-item-icon.missed {
                background: linear-gradient(135deg, #ff6b6b 0%, #ff4757 100%);
            }
            
            .az-comms-item-icon.sms {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            }
            
            .az-comms-item-icon.recording {
                background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
                color: #333;
            }
            
            .az-comms-item-info {
                flex: 1;
            }
            
            .az-comms-item-title {
                font-weight: 600;
                color: #1a1a2e;
                margin-bottom: 4px;
            }
            
            .az-comms-item-subtitle {
                font-size: 12px;
                color: #666;
            }
            
            .az-comms-item-meta {
                text-align: right;
            }
            
            .az-comms-item-time {
                font-size: 12px;
                color: #999;
            }
            
            .az-comms-item-duration {
                font-size: 11px;
                color: #667eea;
                font-weight: 500;
            }
            
            .az-comms-item-actions {
                display: flex;
                gap: 8px;
                margin-left: 16px;
            }
            
            .az-comms-item-btn {
                width: 36px;
                height: 36px;
                border: none;
                border-radius: 8px;
                background: #e0e0e0;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .az-comms-item-btn:hover {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            /* Empty State */
            .az-comms-empty {
                text-align: center;
                padding: 60px 20px;
                color: #999;
            }
            
            .az-comms-empty-icon {
                font-size: 64px;
                margin-bottom: 16px;
                opacity: 0.5;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .az-comms-stats {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .az-comms-tabs {
                    flex-wrap: wrap;
                }
                
                .az-comms-tab {
                    flex: 1 1 45%;
                }
            }
        `;
        document.head.appendChild(styles);
    }
    
    render_layout() {
        this.$container = $(`
            <div class="az-comms">
                <!-- Header Banner -->
                <div class="az-comms-header">
                    <div class="az-comms-title">
                        <div class="az-comms-icon">📡</div>
                        <div>
                            <h1>${__('Communications Hub')}</h1>
                            <p>${__('Manage all your calls, SMS, and recordings in one place')}</p>
                        </div>
                    </div>
                </div>
                
                <!-- Stats Row -->
                <div class="az-comms-stats">
                    <div class="az-comms-stat">
                        <div class="az-comms-stat-value calls-count">-</div>
                        <div class="az-comms-stat-label">${__('Total Calls')}</div>
                    </div>
                    <div class="az-comms-stat">
                        <div class="az-comms-stat-value sms-count">-</div>
                        <div class="az-comms-stat-label">${__('SMS Messages')}</div>
                    </div>
                    <div class="az-comms-stat">
                        <div class="az-comms-stat-value recordings-count">-</div>
                        <div class="az-comms-stat-label">${__('Recordings')}</div>
                    </div>
                    <div class="az-comms-stat">
                        <div class="az-comms-stat-value missed-count">-</div>
                        <div class="az-comms-stat-label">${__('Missed Calls')}</div>
                    </div>
                </div>
                
                <!-- Tabs -->
                <div class="az-comms-tabs">
                    <button class="az-comms-tab active" data-tab="calls">
                        <span class="az-comms-tab-icon">📞</span>
                        <span>${__('Calls')}</span>
                        <span class="az-comms-tab-badge calls-badge">0</span>
                    </button>
                    <button class="az-comms-tab" data-tab="sms">
                        <span class="az-comms-tab-icon">💬</span>
                        <span>${__('SMS')}</span>
                        <span class="az-comms-tab-badge sms-badge">0</span>
                    </button>
                    <button class="az-comms-tab" data-tab="recordings">
                        <span class="az-comms-tab-icon">🎙️</span>
                        <span>${__('Recordings')}</span>
                        <span class="az-comms-tab-badge recordings-badge">0</span>
                    </button>
                </div>
                
                <!-- Content -->
                <div class="az-comms-content">
                    <!-- Calls Pane -->
                    <div class="az-comms-pane active" id="calls-pane">
                        <div class="az-comms-search">
                            <input type="text" placeholder="${__('Search calls...')}" class="calls-search">
                            <button>${__('Search')}</button>
                        </div>
                        <div class="az-comms-list calls-list">
                            <div class="az-comms-empty">
                                <div class="az-comms-empty-icon">📞</div>
                                <p>${__('Loading calls...')}</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- SMS Pane -->
                    <div class="az-comms-pane" id="sms-pane">
                        <div class="az-comms-search">
                            <input type="text" placeholder="${__('Search messages...')}" class="sms-search">
                            <button>${__('Search')}</button>
                        </div>
                        <div class="az-comms-list sms-list">
                            <div class="az-comms-empty">
                                <div class="az-comms-empty-icon">💬</div>
                                <p>${__('Loading messages...')}</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Recordings Pane -->
                    <div class="az-comms-pane" id="recordings-pane">
                        <div class="az-comms-search">
                            <input type="text" placeholder="${__('Search recordings...')}" class="recordings-search">
                            <button>${__('Search')}</button>
                        </div>
                        <div class="az-comms-list recordings-list">
                            <div class="az-comms-empty">
                                <div class="az-comms-empty-icon">🎙️</div>
                                <p>${__('Loading recordings...')}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).appendTo(this.page.main);
    }
    
    setup_events() {
        // Tab switching
        this.$container.find('.az-comms-tab').on('click', (e) => {
            const tab = $(e.currentTarget).data('tab');
            this.switch_tab(tab);
        });
        
        // Search
        this.$container.find('.az-comms-search button').on('click', () => {
            this.refresh();
        });
        
        this.$container.find('.az-comms-search input').on('keyup', (e) => {
            if (e.key === 'Enter') this.refresh();
        });
    }
    
    switch_tab(tab) {
        this.active_tab = tab;
        this.$container.find('.az-comms-tab').removeClass('active');
        this.$container.find(`.az-comms-tab[data-tab="${tab}"]`).addClass('active');
        this.$container.find('.az-comms-pane').removeClass('active');
        this.$container.find(`#${tab}-pane`).addClass('active');
        this.refresh();
    }
    
    async refresh() {
        this.load_stats();
        
        switch (this.active_tab) {
            case 'calls':
                await this.load_calls();
                break;
            case 'sms':
                await this.load_sms();
                break;
            case 'recordings':
                await this.load_recordings();
                break;
        }
    }
    
    async load_stats() {
        try {
            const r = await frappe.call({
                method: 'arrowz.api.dashboard.get_communications_stats'
            });
            
            const stats = r.message || {};
            this.$container.find('.calls-count').text(stats.total_calls || 0);
            this.$container.find('.sms-count').text(stats.total_sms || 0);
            this.$container.find('.recordings-count').text(stats.total_recordings || 0);
            this.$container.find('.missed-count').text(stats.missed_calls || 0);
            this.$container.find('.calls-badge').text(stats.total_calls || 0);
            this.$container.find('.sms-badge').text(stats.total_sms || 0);
            this.$container.find('.recordings-badge').text(stats.total_recordings || 0);
        } catch (e) {
            console.error('Error loading stats:', e);
        }
    }
    
    async load_calls() {
        const $list = this.$container.find('.calls-list').empty();
        const search = this.$container.find('.calls-search').val();
        
        try {
            const r = await frappe.call({
                method: 'arrowz.api.agent.get_recent_calls',
                args: { limit: 50, search: search }
            });
            
            const calls = r.message || [];
            
            if (!calls.length) {
                $list.html(`
                    <div class="az-comms-empty">
                        <div class="az-comms-empty-icon">📞</div>
                        <p>${__('No calls found')}</p>
                    </div>
                `);
                return;
            }
            
            calls.forEach(call => {
                const direction = call.direction || 'Outbound';
                const iconClass = call.status === 'Missed' ? 'missed' : 
                                  direction === 'Inbound' ? 'inbound' : 'outbound';
                const icon = call.status === 'Missed' ? '📵' : 
                             direction === 'Inbound' ? '📥' : '📤';
                
                $list.append(`
                    <div class="az-comms-item" data-name="${call.name}">
                        <div class="az-comms-item-icon ${iconClass}">${icon}</div>
                        <div class="az-comms-item-info">
                            <div class="az-comms-item-title">${call.contact_name || call.caller_id || call.callee_id || __('Unknown')}</div>
                            <div class="az-comms-item-subtitle">${call.caller_id || ''} → ${call.callee_id || ''}</div>
                        </div>
                        <div class="az-comms-item-meta">
                            <div class="az-comms-item-time">${frappe.datetime.prettyDate(call.start_time)}</div>
                            <div class="az-comms-item-duration">${this.format_duration(call.duration)}</div>
                        </div>
                        <div class="az-comms-item-actions">
                            <button class="az-comms-item-btn callback-btn" data-phone="${call.caller_id || call.callee_id}" title="${__('Call back')}">📞</button>
                            <button class="az-comms-item-btn view-btn" data-name="${call.name}" title="${__('View details')}">👁️</button>
                        </div>
                    </div>
                `);
            });
            
            this.setup_call_actions($list);
        } catch (e) {
            console.error('Error loading calls:', e);
            $list.html(`<div class="az-comms-empty"><p>${__('Error loading calls')}</p></div>`);
        }
    }
    
    async load_sms() {
        const $list = this.$container.find('.sms-list').empty();
        const search = this.$container.find('.sms-search').val();
        
        try {
            const r = await frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'AZ SMS Message',
                    fields: ['name', 'phone_number', 'message', 'direction', 'sent_time', 'status'],
                    order_by: 'sent_time desc',
                    limit_page_length: 50,
                    filters: search ? [['phone_number', 'like', `%${search}%`]] : []
                }
            });
            
            const messages = r.message || [];
            
            if (!messages.length) {
                $list.html(`
                    <div class="az-comms-empty">
                        <div class="az-comms-empty-icon">💬</div>
                        <p>${__('No messages found')}</p>
                    </div>
                `);
                return;
            }
            
            messages.forEach(msg => {
                $list.append(`
                    <div class="az-comms-item" data-name="${msg.name}">
                        <div class="az-comms-item-icon sms">💬</div>
                        <div class="az-comms-item-info">
                            <div class="az-comms-item-title">${msg.phone_number}</div>
                            <div class="az-comms-item-subtitle">${(msg.message || '').substring(0, 50)}...</div>
                        </div>
                        <div class="az-comms-item-meta">
                            <div class="az-comms-item-time">${frappe.datetime.prettyDate(msg.sent_time)}</div>
                            <div class="az-comms-item-duration">${msg.direction}</div>
                        </div>
                        <div class="az-comms-item-actions">
                            <button class="az-comms-item-btn view-btn" data-name="${msg.name}" data-doctype="AZ SMS Message" title="${__('View')}">👁️</button>
                        </div>
                    </div>
                `);
            });
            
            this.setup_sms_actions($list);
        } catch (e) {
            console.error('Error loading SMS:', e);
            $list.html(`<div class="az-comms-empty"><p>${__('Error loading messages')}</p></div>`);
        }
    }
    
    async load_recordings() {
        const $list = this.$container.find('.recordings-list').empty();
        const search = this.$container.find('.recordings-search').val();
        
        try {
            const r = await frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'AZ Call Log',
                    fields: ['name', 'caller_id', 'callee_id', 'start_time', 'duration', 'recording_url'],
                    filters: [['recording_url', 'is', 'set']],
                    order_by: 'start_time desc',
                    limit_page_length: 50
                }
            });
            
            const recordings = r.message || [];
            
            if (!recordings.length) {
                $list.html(`
                    <div class="az-comms-empty">
                        <div class="az-comms-empty-icon">🎙️</div>
                        <p>${__('No recordings found')}</p>
                    </div>
                `);
                return;
            }
            
            recordings.forEach(rec => {
                $list.append(`
                    <div class="az-comms-item" data-name="${rec.name}">
                        <div class="az-comms-item-icon recording">🎙️</div>
                        <div class="az-comms-item-info">
                            <div class="az-comms-item-title">${rec.caller_id || ''} → ${rec.callee_id || ''}</div>
                            <div class="az-comms-item-subtitle">${frappe.datetime.prettyDate(rec.start_time)}</div>
                        </div>
                        <div class="az-comms-item-meta">
                            <div class="az-comms-item-time">${this.format_duration(rec.duration)}</div>
                        </div>
                        <div class="az-comms-item-actions">
                            <button class="az-comms-item-btn play-btn" data-url="${rec.recording_url}" title="${__('Play')}">▶️</button>
                            <button class="az-comms-item-btn download-btn" data-url="${rec.recording_url}" title="${__('Download')}">⬇️</button>
                        </div>
                    </div>
                `);
            });
            
            this.setup_recording_actions($list);
        } catch (e) {
            console.error('Error loading recordings:', e);
            $list.html(`<div class="az-comms-empty"><p>${__('Error loading recordings')}</p></div>`);
        }
    }
    
    setup_call_actions($list) {
        $list.find('.callback-btn').on('click', (e) => {
            e.stopPropagation();
            const phone = $(e.currentTarget).data('phone');
            if (phone && typeof arrowz !== 'undefined' && arrowz.softphone) {
                arrowz.softphone.call(phone);
            } else {
                frappe.set_route('/desk/make-call');
            }
        });
        
        $list.find('.view-btn').on('click', (e) => {
            e.stopPropagation();
            const name = $(e.currentTarget).data('name');
            frappe.set_route('Form', 'AZ Call Log', name);
        });
    }
    
    setup_sms_actions($list) {
        $list.find('.view-btn').on('click', (e) => {
            e.stopPropagation();
            const name = $(e.currentTarget).data('name');
            const doctype = $(e.currentTarget).data('doctype') || 'AZ SMS Message';
            frappe.set_route('Form', doctype, name);
        });
    }
    
    setup_recording_actions($list) {
        $list.find('.play-btn').on('click', (e) => {
            e.stopPropagation();
            const url = $(e.currentTarget).data('url');
            if (url) {
                // Show audio player modal
                const d = new frappe.ui.Dialog({
                    title: __('Play Recording'),
                    fields: [{
                        fieldtype: 'HTML',
                        options: `<audio controls style="width:100%"><source src="${url}" type="audio/wav"></audio>`
                    }]
                });
                d.show();
            }
        });
        
        $list.find('.download-btn').on('click', (e) => {
            e.stopPropagation();
            const url = $(e.currentTarget).data('url');
            if (url) {
                window.open(url, '_blank');
            }
        });
    }
    
    format_duration(seconds) {
        if (!seconds) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}
