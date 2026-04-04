// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Arrowz Agent Dashboard - Professional Multi-Color Design
 * A beautiful, modern dashboard for call center agents
 */

frappe.pages['arrowz-agent-dashboard'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Agent Dashboard'),
        single_column: true
    });
    
    // Add custom page styling
    wrapper.classList.add('arrowz-dashboard-page');
    
    wrapper.agent_dashboard = new ArrowzAgentDashboard(page);
};

frappe.pages['arrowz-agent-dashboard'].on_page_show = function(wrapper) {
    if (wrapper.agent_dashboard) {
        wrapper.agent_dashboard.refresh();
    }
};

class ArrowzAgentDashboard {
    constructor(page) {
        this.page = page;
        this.data = {};
        this.init();
    }
    
    init() {
        this.add_styles();
        this.setup_page_actions();
        this.render_layout();
        this.setup_realtime();
        this.refresh();
        this.start_auto_refresh();
    }
    
    add_styles() {
        if (document.getElementById('arrowz-agent-dashboard-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'arrowz-agent-dashboard-styles';
        styles.textContent = `
            .arrowz-dashboard-page .page-content {
                background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
                min-height: calc(100vh - 60px);
            }
            
            .arrowz-agent-dashboard {
                padding: 24px;
            }
            
            /* Dashboard Header */
            .az-dash-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 20px;
                padding: 32px;
                margin-bottom: 24px;
                color: white;
                position: relative;
                overflow: hidden;
            }
            
            .az-dash-header::before {
                content: '';
                position: absolute;
                top: -50%;
                right: -10%;
                width: 300px;
                height: 300px;
                background: rgba(255,255,255,0.1);
                border-radius: 50%;
            }
            
            .az-dash-header::after {
                content: '';
                position: absolute;
                bottom: -30%;
                left: 10%;
                width: 200px;
                height: 200px;
                background: rgba(255,255,255,0.05);
                border-radius: 50%;
            }
            
            .az-dash-header h2 {
                margin: 0 0 8px 0;
                font-size: 28px;
                font-weight: 700;
                position: relative;
                z-index: 1;
            }
            
            .az-dash-header p {
                margin: 0;
                opacity: 0.9;
                font-size: 16px;
                position: relative;
                z-index: 1;
            }
            
            .az-agent-status-badge {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: rgba(255,255,255,0.2);
                padding: 8px 16px;
                border-radius: 50px;
                font-weight: 600;
                margin-top: 16px;
                backdrop-filter: blur(10px);
                position: relative;
                z-index: 1;
            }
            
            .az-status-dot {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }
            
            .az-status-dot.available { background: #00ff88; }
            .az-status-dot.busy { background: #ffd700; }
            .az-status-dot.offline { background: #ff6b6b; }
            .az-status-dot.break { background: #f39c12; }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.2); opacity: 0.7; }
            }
            
            /* Stats Grid */
            .az-stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 24px;
            }
            
            .az-stat-card {
                background: white;
                border-radius: 16px;
                padding: 24px;
                position: relative;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.05);
                transition: all 0.3s ease;
            }
            
            .az-stat-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 30px rgba(0,0,0,0.1);
            }
            
            .az-stat-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 4px;
            }
            
            .az-stat-card.calls::before { background: linear-gradient(90deg, #667eea, #764ba2); }
            .az-stat-card.duration::before { background: linear-gradient(90deg, #11998e, #38ef7d); }
            .az-stat-card.missed::before { background: linear-gradient(90deg, #ff416c, #ff4b2b); }
            .az-stat-card.queue::before { background: linear-gradient(90deg, #f7971e, #ffd200); }
            .az-stat-card.rating::before { background: linear-gradient(90deg, #4facfe, #00f2fe); }
            
            .az-stat-icon {
                width: 48px;
                height: 48px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                margin-bottom: 16px;
            }
            
            .az-stat-card.calls .az-stat-icon { background: linear-gradient(135deg, #667eea20, #764ba220); color: #667eea; }
            .az-stat-card.duration .az-stat-icon { background: linear-gradient(135deg, #11998e20, #38ef7d20); color: #11998e; }
            .az-stat-card.missed .az-stat-icon { background: linear-gradient(135deg, #ff416c20, #ff4b2b20); color: #ff416c; }
            .az-stat-card.queue .az-stat-icon { background: linear-gradient(135deg, #f7971e20, #ffd20020); color: #f7971e; }
            .az-stat-card.rating .az-stat-icon { background: linear-gradient(135deg, #4facfe20, #00f2fe20); color: #4facfe; }
            
            .az-stat-value {
                font-size: 32px;
                font-weight: 700;
                color: #1a1a2e;
                line-height: 1;
                margin-bottom: 8px;
            }
            
            .az-stat-label {
                font-size: 14px;
                color: #666;
                font-weight: 500;
            }
            
            .az-stat-trend {
                position: absolute;
                bottom: 16px;
                right: 20px;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 8px;
                border-radius: 6px;
            }
            
            .az-stat-trend.up { background: #e8f5e9; color: #2e7d32; }
            .az-stat-trend.down { background: #ffebee; color: #c62828; }
            
            /* Main Content Grid */
            .az-main-grid {
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 24px;
            }
            
            @media (max-width: 992px) {
                .az-main-grid { grid-template-columns: 1fr; }
            }
            
            .az-card {
                background: white;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            }
            
            .az-card-header {
                padding: 20px 24px;
                border-bottom: 1px solid #f0f0f0;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .az-card-title {
                font-size: 18px;
                font-weight: 700;
                color: #1a1a2e;
                margin: 0;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .az-card-title svg {
                width: 24px;
                height: 24px;
            }
            
            .az-card-body {
                padding: 24px;
            }
            
            /* Active Call Panel */
            .az-active-call {
                background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%);
                border-radius: 16px;
                padding: 24px;
                color: white;
                text-align: center;
                margin-bottom: 24px;
            }
            
            .az-active-call.ringing {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                animation: ring-pulse 1s infinite;
            }
            
            @keyframes ring-pulse {
                0%, 100% { box-shadow: 0 0 0 0 rgba(245, 87, 108, 0.4); }
                50% { box-shadow: 0 0 0 20px rgba(245, 87, 108, 0); }
            }
            
            .az-no-call {
                text-align: center;
                padding: 40px 24px;
                color: #999;
            }
            
            .az-no-call svg {
                width: 64px;
                height: 64px;
                margin-bottom: 16px;
                opacity: 0.3;
            }
            
            .az-call-phone {
                font-size: 28px;
                font-weight: 700;
                margin: 8px 0;
            }
            
            .az-call-name {
                font-size: 16px;
                opacity: 0.9;
                margin-bottom: 8px;
            }
            
            .az-call-timer {
                font-size: 36px;
                font-weight: 300;
                font-family: monospace;
                margin: 16px 0;
            }
            
            .az-call-actions {
                display: flex;
                justify-content: center;
                gap: 12px;
                margin-top: 20px;
            }
            
            .az-call-btn {
                width: 56px;
                height: 56px;
                border-radius: 50%;
                border: none;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.2s ease;
                font-size: 20px;
            }
            
            .az-call-btn:hover { transform: scale(1.1); }
            .az-call-btn.hold { background: rgba(255,255,255,0.2); color: white; }
            .az-call-btn.mute { background: rgba(255,255,255,0.2); color: white; }
            .az-call-btn.transfer { background: rgba(255,255,255,0.2); color: white; }
            .az-call-btn.hangup { background: #ff4757; color: white; }
            .az-call-btn.answer { background: #2ed573; color: white; }
            
            /* Recent Calls List */
            .az-call-item {
                display: flex;
                align-items: center;
                padding: 16px 0;
                border-bottom: 1px solid #f5f5f5;
            }
            
            .az-call-item:last-child { border-bottom: none; }
            
            .az-call-item-icon {
                width: 44px;
                height: 44px;
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 16px;
                font-size: 18px;
            }
            
            .az-call-item-icon.inbound { background: #e3f2fd; color: #1976d2; }
            .az-call-item-icon.outbound { background: #e8f5e9; color: #388e3c; }
            .az-call-item-icon.missed { background: #ffebee; color: #d32f2f; }
            
            .az-call-item-info { flex: 1; }
            .az-call-item-phone { font-weight: 600; color: #1a1a2e; margin-bottom: 4px; }
            .az-call-item-time { font-size: 12px; color: #999; }
            .az-call-item-duration { font-size: 14px; color: #666; font-weight: 500; }
            
            /* Quick Actions */
            .az-quick-actions {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
            }
            
            .az-quick-btn {
                background: linear-gradient(135deg, #f5f7fa 0%, #e8ebed 100%);
                border: none;
                border-radius: 12px;
                padding: 16px;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
                font-size: 14px;
                font-weight: 500;
                color: #444;
            }
            
            .az-quick-btn:hover {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                transform: scale(1.02);
            }
            
            .az-quick-btn svg {
                width: 28px;
                height: 28px;
            }
            
            /* Status Selector */
            .az-status-selector {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            
            .az-status-btn {
                padding: 10px 20px;
                border: 2px solid #e0e0e0;
                border-radius: 50px;
                background: white;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .az-status-btn:hover { border-color: #667eea; }
            .az-status-btn.active { border-color: #667eea; background: #667eea; color: white; }
            .az-status-btn .dot { width: 10px; height: 10px; border-radius: 50%; }
            .az-status-btn .dot.available { background: #2ed573; }
            .az-status-btn .dot.busy { background: #ffa502; }
            .az-status-btn .dot.break { background: #ff6b6b; }
            .az-status-btn .dot.offline { background: #a4a4a4; }
        `;
        document.head.appendChild(styles);
    }
    
    setup_page_actions() {
        this.page.set_primary_action(__('Make Call'), () => {
            if (typeof arrowz !== 'undefined' && arrowz.softphone) {
                arrowz.softphone.show();
            }
        }, 'call');
        
        this.page.set_secondary_action(__('Refresh'), () => this.refresh(), 'refresh');
    }
    
    render_layout() {
        this.$container = $(`
            <div class="arrowz-agent-dashboard">
                <!-- Dashboard Header -->
                <div class="az-dash-header">
                    <h2>👋 ${__('Welcome back')}, <span class="agent-name">Agent</span></h2>
                    <p>${__('Here\'s your performance overview for today')}</p>
                    <div class="az-agent-status-badge">
                        <span class="az-status-dot available"></span>
                        <span class="status-text">${__('Available')}</span>
                    </div>
                </div>
                
                <!-- Stats Grid -->
                <div class="az-stats-grid">
                    <div class="az-stat-card calls">
                        <div class="az-stat-icon">📞</div>
                        <div class="az-stat-value stat-calls-handled">0</div>
                        <div class="az-stat-label">${__('Calls Handled')}</div>
                        <div class="az-stat-trend up">+12%</div>
                    </div>
                    <div class="az-stat-card duration">
                        <div class="az-stat-icon">⏱️</div>
                        <div class="az-stat-value stat-avg-duration">0:00</div>
                        <div class="az-stat-label">${__('Avg Call Duration')}</div>
                    </div>
                    <div class="az-stat-card missed">
                        <div class="az-stat-icon">📵</div>
                        <div class="az-stat-value stat-missed">0</div>
                        <div class="az-stat-label">${__('Missed Calls')}</div>
                    </div>
                    <div class="az-stat-card queue">
                        <div class="az-stat-icon">📋</div>
                        <div class="az-stat-value stat-queue">0</div>
                        <div class="az-stat-label">${__('In Queue')}</div>
                    </div>
                    <div class="az-stat-card rating">
                        <div class="az-stat-icon">⭐</div>
                        <div class="az-stat-value stat-rating">-</div>
                        <div class="az-stat-label">${__('Customer Rating')}</div>
                    </div>
                </div>
                
                <!-- Main Grid -->
                <div class="az-main-grid">
                    <!-- Left Column -->
                    <div class="az-left-column">
                        <!-- Active Call Panel -->
                        <div class="az-card" style="margin-bottom: 24px;">
                            <div class="az-card-header">
                                <h3 class="az-card-title">
                                    <svg fill="currentColor" viewBox="0 0 24 24"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
                                    ${__('Current Call')}
                                </h3>
                            </div>
                            <div class="az-card-body active-call-container">
                                <div class="az-no-call">
                                    <svg fill="currentColor" viewBox="0 0 24 24"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
                                    <p>${__('No active call')}</p>
                                    <p style="font-size: 14px; margin-top: 8px;">${__('Click "Make Call" to start a new call')}</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Recent Calls -->
                        <div class="az-card">
                            <div class="az-card-header">
                                <h3 class="az-card-title">
                                    <svg fill="currentColor" viewBox="0 0 24 24"><path d="M13 3a9 9 0 00-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0013 21a9 9 0 000-18zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/></svg>
                                    ${__('Recent Calls')}
                                </h3>
                                <a href="/desk/az-call-log" class="btn btn-sm btn-light">${__('View All')}</a>
                            </div>
                            <div class="az-card-body recent-calls-list">
                                <p class="text-muted text-center">${__('Loading...')}</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Right Column -->
                    <div class="az-right-column">
                        <!-- Quick Actions -->
                        <div class="az-card" style="margin-bottom: 24px;">
                            <div class="az-card-header">
                                <h3 class="az-card-title">
                                    <svg fill="currentColor" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                                    ${__('Quick Actions')}
                                </h3>
                            </div>
                            <div class="az-card-body">
                                <div class="az-quick-actions">
                                    <button class="az-quick-btn" onclick="arrowz.softphone && arrowz.softphone.show()">
                                        <svg fill="currentColor" viewBox="0 0 24 24"><path d="M20.01 15.38c-1.23 0-2.42-.2-3.53-.56-.35-.12-.74-.03-1.01.24l-1.57 1.97c-2.83-1.35-5.48-3.9-6.89-6.83l1.95-1.66c.27-.28.35-.67.24-1.02-.37-1.11-.56-2.3-.56-3.53 0-.54-.45-.99-.99-.99H4.19C3.65 3 3 3.24 3 3.99 3 13.28 10.73 21 20.01 21c.71 0 .99-.63.99-1.18v-3.45c0-.54-.45-.99-.99-.99z"/></svg>
                                        ${__('New Call')}
                                    </button>
                                    <button class="az-quick-btn" onclick="frappe.new_doc('AZ SMS Message')">
                                        <svg fill="currentColor" viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
                                        ${__('Send SMS')}
                                    </button>
                                    <button class="az-quick-btn" onclick="frappe.set_route('List', 'AZ Call Log')">
                                        <svg fill="currentColor" viewBox="0 0 24 24"><path d="M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z"/></svg>
                                        ${__('Call Log')}
                                    </button>
                                    <button class="az-quick-btn" onclick="frappe.set_route('List', 'AZ Conversation Session')">
                                        <svg fill="currentColor" viewBox="0 0 24 24"><path d="M21 6h-2v9H6v2c0 .55.45 1 1 1h11l4 4V7c0-.55-.45-1-1-1zm-4 6V3c0-.55-.45-1-1-1H3c-.55 0-1 .45-1 1v14l4-4h10c.55 0 1-.45 1-1z"/></svg>
                                        ${__('Chats')}
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Status Selector -->
                        <div class="az-card">
                            <div class="az-card-header">
                                <h3 class="az-card-title">
                                    <svg fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                                    ${__('My Status')}
                                </h3>
                            </div>
                            <div class="az-card-body">
                                <div class="az-status-selector">
                                    <button class="az-status-btn active" data-status="available">
                                        <span class="dot available"></span> ${__('Available')}
                                    </button>
                                    <button class="az-status-btn" data-status="busy">
                                        <span class="dot busy"></span> ${__('Busy')}
                                    </button>
                                    <button class="az-status-btn" data-status="break">
                                        <span class="dot break"></span> ${__('Break')}
                                    </button>
                                    <button class="az-status-btn" data-status="offline">
                                        <span class="dot offline"></span> ${__('Offline')}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).appendTo(this.page.main);
        
        this.setup_events();
    }
    
    setup_events() {
        // Status selector
        this.$container.find('.az-status-btn').on('click', (e) => {
            const $btn = $(e.currentTarget);
            const status = $btn.data('status');
            this.set_agent_status(status);
            
            this.$container.find('.az-status-btn').removeClass('active');
            $btn.addClass('active');
        });
    }
    
    setup_realtime() {
        frappe.realtime.on('arrowz_call_event', (data) => {
            this.handle_call_event(data);
        });
        
        frappe.realtime.on('arrowz_agent_update', (data) => {
            this.refresh();
        });
    }
    
    start_auto_refresh() {
        this.refresh_interval = setInterval(() => this.refresh(), 30000);
    }
    
    async refresh() {
        try {
            const r = await frappe.call({
                method: 'arrowz.api.agent.get_agent_dashboard_data'
            });
            
            if (r.message) {
                this.update_dashboard(r.message);
            }
        } catch (e) {
            console.error('Error refreshing agent dashboard:', e);
            // Use fallback data
            this.update_dashboard({
                agent_name: frappe.session.user_fullname || 'Agent',
                calls_handled: 0,
                avg_duration: 0,
                missed_calls: 0,
                queue_count: 0,
                recent_calls: []
            });
        }
    }
    
    update_dashboard(data) {
        // Update agent name
        this.$container.find('.agent-name').text(data.agent_name || frappe.session.user_fullname || 'Agent');
        
        // Update stats
        this.$container.find('.stat-calls-handled').text(data.calls_handled || 0);
        this.$container.find('.stat-avg-duration').text(this.format_duration(data.avg_duration || 0));
        this.$container.find('.stat-missed').text(data.missed_calls || 0);
        this.$container.find('.stat-queue').text(data.queue_count || 0);
        this.$container.find('.stat-rating').text(data.avg_rating ? data.avg_rating.toFixed(1) : '-');
        
        // Update recent calls
        this.render_recent_calls(data.recent_calls || []);
        
        // Update active call if any
        if (data.active_call) {
            this.render_active_call(data.active_call);
        }
    }
    
    render_recent_calls(calls) {
        const $list = this.$container.find('.recent-calls-list').empty();
        
        if (!calls.length) {
            $list.html(`<p class="text-muted text-center">${__('No recent calls')}</p>`);
            return;
        }
        
        calls.slice(0, 5).forEach(call => {
            const iconClass = call.direction === 'Inbound' ? 'inbound' : 
                             call.status === 'Missed' ? 'missed' : 'outbound';
            const icon = call.direction === 'Inbound' ? '📥' : '📤';
            
            $list.append(`
                <div class="az-call-item">
                    <div class="az-call-item-icon ${iconClass}">${icon}</div>
                    <div class="az-call-item-info">
                        <div class="az-call-item-phone">${call.phone || call.contact_number || '-'}</div>
                        <div class="az-call-item-time">${frappe.datetime.prettyDate(call.start_time)}</div>
                    </div>
                    <div class="az-call-item-duration">${this.format_duration(call.duration || 0)}</div>
                </div>
            `);
        });
    }
    
    render_active_call(call) {
        const $container = this.$container.find('.active-call-container');
        const isRinging = call.status === 'Ringing';
        
        $container.html(`
            <div class="az-active-call ${isRinging ? 'ringing' : ''}">
                <div class="az-call-direction">${call.direction === 'Inbound' ? '📥 Incoming' : '📤 Outgoing'}</div>
                <div class="az-call-phone">${call.phone || '-'}</div>
                <div class="az-call-name">${call.contact_name || ''}</div>
                <div class="az-call-timer">${this.format_duration(call.duration || 0)}</div>
                <div class="az-call-actions">
                    ${isRinging ? `
                        <button class="az-call-btn answer" onclick="arrowz.softphone.answer()">📞</button>
                        <button class="az-call-btn hangup" onclick="arrowz.softphone.reject()">📵</button>
                    ` : `
                        <button class="az-call-btn hold" onclick="arrowz.softphone.hold()">⏸️</button>
                        <button class="az-call-btn mute" onclick="arrowz.softphone.mute()">🔇</button>
                        <button class="az-call-btn transfer" onclick="arrowz.softphone.transfer()">↗️</button>
                        <button class="az-call-btn hangup" onclick="arrowz.softphone.hangup()">📵</button>
                    `}
                </div>
            </div>
        `);
    }
    
    handle_call_event(data) {
        if (data.type === 'incoming' || data.type === 'outgoing') {
            this.render_active_call(data);
        } else if (data.type === 'ended') {
            this.$container.find('.active-call-container').html(`
                <div class="az-no-call">
                    <svg fill="currentColor" viewBox="0 0 24 24"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
                    <p>${__('No active call')}</p>
                </div>
            `);
            this.refresh();
        }
    }
    
    async set_agent_status(status) {
        try {
            await frappe.call({
                method: 'arrowz.api.agent.set_agent_status',
                args: { status }
            });
            
            // Update UI
            const statusDot = this.$container.find('.az-agent-status-badge .az-status-dot');
            statusDot.removeClass('available busy break offline').addClass(status);
            
            const statusText = {
                available: __('Available'),
                busy: __('Busy'),
                break: __('On Break'),
                offline: __('Offline')
            };
            this.$container.find('.status-text').text(statusText[status] || status);
            
            frappe.show_alert({ message: __('Status updated'), indicator: 'green' });
        } catch (e) {
            console.error('Error setting status:', e);
        }
    }
    
    format_duration(seconds) {
        if (!seconds) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${String(secs).padStart(2, '0')}`;
    }
    
    destroy() {
        if (this.refresh_interval) {
            clearInterval(this.refresh_interval);
        }
    }
}
