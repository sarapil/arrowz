// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Arrowz Manager Wallboard - Professional Real-time Dashboard
 * Multi-color gradient design with live updates
 */

frappe.pages['arrowz-wallboard'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Call Center Wallboard'),
        single_column: true
    });
    
    wrapper.classList.add('arrowz-wallboard-page');
    wrapper.wallboard = new ArrowzWallboard(page);
};

frappe.pages['arrowz-wallboard'].on_page_show = function(wrapper) {
    if (wrapper.wallboard) {
        wrapper.wallboard.refresh();
    }
};

class ArrowzWallboard {
    constructor(page) {
        this.page = page;
        this.charts = {};
        this.init();
    }
    
    init() {
        this.add_styles();
        this.setup_page_actions();
        this.render_layout();
        this.setup_realtime();
        this.refresh();
        this.start_auto_refresh();
        this.start_clock();
    }
    
    add_styles() {
        if (document.getElementById('arrowz-wallboard-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'arrowz-wallboard-styles';
        styles.textContent = `
            .arrowz-wallboard-page .page-content {
                background: linear-gradient(135deg, #0c0c1e 0%, #1a1a3e 50%, #2d1b4e 100%);
                min-height: calc(100vh - 60px);
            }
            
            .arrowz-wallboard {
                padding: 24px;
                color: white;
            }
            
            /* Header */
            .az-wb-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 32px;
                padding-bottom: 24px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            
            .az-wb-title {
                display: flex;
                align-items: center;
                gap: 16px;
            }
            
            .az-wb-title h1 {
                margin: 0;
                font-size: 32px;
                font-weight: 700;
                background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .az-wb-logo {
                width: 48px;
                height: 48px;
            }
            
            .az-wb-clock {
                text-align: right;
            }
            
            .az-wb-time {
                font-size: 42px;
                font-weight: 300;
                font-family: monospace;
                letter-spacing: 2px;
            }
            
            .az-wb-date {
                font-size: 14px;
                opacity: 0.7;
            }
            
            /* Stats Row */
            .az-wb-stats {
                display: grid;
                grid-template-columns: repeat(5, 1fr);
                gap: 20px;
                margin-bottom: 32px;
            }
            
            @media (max-width: 1200px) {
                .az-wb-stats { grid-template-columns: repeat(3, 1fr); }
            }
            
            @media (max-width: 768px) {
                .az-wb-stats { grid-template-columns: repeat(2, 1fr); }
            }
            
            .az-wb-stat {
                background: rgba(255,255,255,0.05);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 20px;
                padding: 24px;
                position: relative;
                overflow: hidden;
                transition: all 0.3s ease;
            }
            
            .az-wb-stat:hover {
                transform: translateY(-5px);
                background: rgba(255,255,255,0.08);
            }
            
            .az-wb-stat::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 4px;
            }
            
            .az-wb-stat.active::before { background: linear-gradient(90deg, #00ff87, #60efff); }
            .az-wb-stat.agents::before { background: linear-gradient(90deg, #667eea, #764ba2); }
            .az-wb-stat.waiting::before { background: linear-gradient(90deg, #f7971e, #ffd200); }
            .az-wb-stat.today::before { background: linear-gradient(90deg, #4facfe, #00f2fe); }
            .az-wb-stat.answered::before { background: linear-gradient(90deg, #43e97b, #38f9d7); }
            
            .az-wb-stat-icon {
                font-size: 32px;
                margin-bottom: 12px;
            }
            
            .az-wb-stat-value {
                font-size: 48px;
                font-weight: 700;
                line-height: 1;
                margin-bottom: 8px;
            }
            
            .az-wb-stat.active .az-wb-stat-value { color: #00ff87; }
            .az-wb-stat.agents .az-wb-stat-value { color: #a78bfa; }
            .az-wb-stat.waiting .az-wb-stat-value { color: #ffd200; }
            .az-wb-stat.today .az-wb-stat-value { color: #60efff; }
            .az-wb-stat.answered .az-wb-stat-value { color: #43e97b; }
            
            .az-wb-stat-label {
                font-size: 14px;
                opacity: 0.7;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .az-wb-stat-change {
                position: absolute;
                top: 16px;
                right: 16px;
                font-size: 12px;
                padding: 4px 8px;
                border-radius: 6px;
            }
            
            .az-wb-stat-change.up { background: rgba(67, 233, 123, 0.2); color: #43e97b; }
            .az-wb-stat-change.down { background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }
            
            /* Main Grid */
            .az-wb-grid {
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 24px;
            }
            
            @media (max-width: 992px) {
                .az-wb-grid { grid-template-columns: 1fr; }
            }
            
            .az-wb-card {
                background: rgba(255,255,255,0.05);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 20px;
                overflow: hidden;
            }
            
            .az-wb-card-header {
                padding: 20px 24px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .az-wb-card-title {
                font-size: 18px;
                font-weight: 600;
                margin: 0;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .az-wb-card-title span {
                font-size: 20px;
            }
            
            .az-wb-card-body {
                padding: 24px;
            }
            
            /* Agent Grid */
            .az-wb-agent-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                gap: 16px;
            }
            
            .az-wb-agent {
                background: rgba(255,255,255,0.03);
                border-radius: 16px;
                padding: 20px;
                text-align: center;
                transition: all 0.3s ease;
                position: relative;
            }
            
            .az-wb-agent:hover {
                background: rgba(255,255,255,0.08);
            }
            
            .az-wb-agent-avatar {
                width: 56px;
                height: 56px;
                border-radius: 50%;
                margin: 0 auto 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                font-weight: 600;
                position: relative;
            }
            
            .az-wb-agent.available .az-wb-agent-avatar { 
                background: linear-gradient(135deg, #43e97b, #38f9d7); 
                color: #0c0c1e;
            }
            .az-wb-agent.busy .az-wb-agent-avatar { 
                background: linear-gradient(135deg, #ffd200, #f7971e); 
                color: #0c0c1e;
            }
            .az-wb-agent.offline .az-wb-agent-avatar { 
                background: linear-gradient(135deg, #636363, #a2a2a2); 
                color: white;
            }
            .az-wb-agent.break .az-wb-agent-avatar { 
                background: linear-gradient(135deg, #ff6b6b, #ff8e8e); 
                color: white;
            }
            
            .az-wb-agent-status-dot {
                position: absolute;
                bottom: 2px;
                right: 2px;
                width: 14px;
                height: 14px;
                border-radius: 50%;
                border: 2px solid #1a1a3e;
            }
            
            .az-wb-agent.available .az-wb-agent-status-dot { background: #43e97b; }
            .az-wb-agent.busy .az-wb-agent-status-dot { background: #ffd200; }
            .az-wb-agent.offline .az-wb-agent-status-dot { background: #666; }
            .az-wb-agent.break .az-wb-agent-status-dot { background: #ff6b6b; }
            
            .az-wb-agent-name {
                font-weight: 600;
                margin-bottom: 4px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .az-wb-agent-ext {
                font-size: 12px;
                opacity: 0.6;
                margin-bottom: 8px;
            }
            
            .az-wb-agent-status {
                font-size: 11px;
                padding: 4px 10px;
                border-radius: 20px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .az-wb-agent.available .az-wb-agent-status { background: rgba(67, 233, 123, 0.2); color: #43e97b; }
            .az-wb-agent.busy .az-wb-agent-status { background: rgba(255, 210, 0, 0.2); color: #ffd200; }
            .az-wb-agent.offline .az-wb-agent-status { background: rgba(255, 255, 255, 0.1); color: #999; }
            .az-wb-agent.break .az-wb-agent-status { background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }
            
            /* Active Calls Table */
            .az-wb-calls-table {
                width: 100%;
            }
            
            .az-wb-calls-table th {
                text-align: left;
                padding: 12px 16px;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                opacity: 0.6;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
            
            .az-wb-calls-table td {
                padding: 16px;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
            
            .az-wb-calls-table tr:last-child td {
                border-bottom: none;
            }
            
            .az-wb-call-status {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
            }
            
            .az-wb-call-status.ringing {
                background: rgba(240, 147, 251, 0.2);
                color: #f093fb;
                animation: blink 1s infinite;
            }
            
            .az-wb-call-status.active {
                background: rgba(67, 233, 123, 0.2);
                color: #43e97b;
            }
            
            .az-wb-call-status.hold {
                background: rgba(255, 210, 0, 0.2);
                color: #ffd200;
            }
            
            @keyframes blink {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            .az-wb-call-timer {
                font-family: monospace;
                font-size: 14px;
            }
            
            .az-wb-no-data {
                text-align: center;
                padding: 40px;
                opacity: 0.5;
            }
            
            .az-wb-no-data svg {
                width: 48px;
                height: 48px;
                margin-bottom: 12px;
                opacity: 0.3;
            }
            
            /* Queue Bars */
            .az-wb-queue-item {
                margin-bottom: 20px;
            }
            
            .az-wb-queue-item:last-child {
                margin-bottom: 0;
            }
            
            .az-wb-queue-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
            }
            
            .az-wb-queue-name {
                font-weight: 500;
            }
            
            .az-wb-queue-count {
                font-weight: 700;
            }
            
            .az-wb-queue-bar {
                height: 8px;
                background: rgba(255,255,255,0.1);
                border-radius: 4px;
                overflow: hidden;
            }
            
            .az-wb-queue-fill {
                height: 100%;
                border-radius: 4px;
                transition: width 0.5s ease;
            }
            
            .az-wb-queue-fill.low { background: linear-gradient(90deg, #43e97b, #38f9d7); }
            .az-wb-queue-fill.medium { background: linear-gradient(90deg, #ffd200, #f7971e); }
            .az-wb-queue-fill.high { background: linear-gradient(90deg, #ff6b6b, #ff4757); }
            
            /* SLA Gauge */
            .az-wb-sla-container {
                display: flex;
                justify-content: center;
                padding: 20px;
            }
            
            .az-wb-sla-gauge {
                width: 180px;
                height: 180px;
                position: relative;
            }
            
            .az-wb-sla-circle {
                fill: none;
                stroke: rgba(255,255,255,0.1);
                stroke-width: 12;
            }
            
            .az-wb-sla-progress {
                fill: none;
                stroke-width: 12;
                stroke-linecap: round;
                transform: rotate(-90deg);
                transform-origin: center;
                transition: stroke-dashoffset 1s ease;
            }
            
            .az-wb-sla-text {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                text-align: center;
            }
            
            .az-wb-sla-value {
                font-size: 36px;
                font-weight: 700;
            }
            
            .az-wb-sla-label {
                font-size: 12px;
                opacity: 0.7;
            }
        `;
        document.head.appendChild(styles);
    }
    
    setup_page_actions() {
        this.page.set_secondary_action(__('Refresh'), () => this.refresh(), 'refresh');
        
        this.page.add_inner_button(__('Fullscreen'), () => {
            const elem = document.documentElement;
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            }
        });
    }
    
    render_layout() {
        this.$container = $(`
            <div class="arrowz-wallboard">
                <!-- Header -->
                <div class="az-wb-header">
                    <div class="az-wb-title">
                        <img src="/assets/arrowz/images/arrowz-icon-animated.svg" class="az-wb-logo" alt="Arrowz">
                        <h1>${__('Call Center Wallboard')}</h1>
                    </div>
                    <div class="az-wb-clock">
                        <div class="az-wb-time">--:--:--</div>
                        <div class="az-wb-date">--</div>
                    </div>
                </div>
                
                <!-- Stats Row -->
                <div class="az-wb-stats">
                    <div class="az-wb-stat active">
                        <div class="az-wb-stat-icon">📞</div>
                        <div class="az-wb-stat-value stat-active">0</div>
                        <div class="az-wb-stat-label">${__('Active Calls')}</div>
                    </div>
                    <div class="az-wb-stat agents">
                        <div class="az-wb-stat-icon">👥</div>
                        <div class="az-wb-stat-value stat-agents">0</div>
                        <div class="az-wb-stat-label">${__('Available Agents')}</div>
                    </div>
                    <div class="az-wb-stat waiting">
                        <div class="az-wb-stat-icon">⏳</div>
                        <div class="az-wb-stat-value stat-waiting">0</div>
                        <div class="az-wb-stat-label">${__('Waiting in Queue')}</div>
                    </div>
                    <div class="az-wb-stat today">
                        <div class="az-wb-stat-icon">📊</div>
                        <div class="az-wb-stat-value stat-today">0</div>
                        <div class="az-wb-stat-label">${__('Calls Today')}</div>
                    </div>
                    <div class="az-wb-stat answered">
                        <div class="az-wb-stat-icon">✅</div>
                        <div class="az-wb-stat-value stat-answered">0%</div>
                        <div class="az-wb-stat-label">${__('Answer Rate')}</div>
                    </div>
                </div>
                
                <!-- Main Grid -->
                <div class="az-wb-grid">
                    <!-- Left Column -->
                    <div>
                        <!-- Active Calls -->
                        <div class="az-wb-card" style="margin-bottom: 24px;">
                            <div class="az-wb-card-header">
                                <h3 class="az-wb-card-title"><span>📞</span> ${__('Active Calls')}</h3>
                            </div>
                            <div class="az-wb-card-body active-calls-container">
                                <div class="az-wb-no-data">
                                    <svg fill="currentColor" viewBox="0 0 24 24"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
                                    <p>${__('No active calls')}</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Agent Status -->
                        <div class="az-wb-card">
                            <div class="az-wb-card-header">
                                <h3 class="az-wb-card-title"><span>👥</span> ${__('Agent Status')}</h3>
                            </div>
                            <div class="az-wb-card-body">
                                <div class="az-wb-agent-grid agent-grid-container">
                                    <p class="text-center" style="opacity: 0.5;">${__('Loading...')}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Right Column -->
                    <div>
                        <!-- SLA -->
                        <div class="az-wb-card" style="margin-bottom: 24px;">
                            <div class="az-wb-card-header">
                                <h3 class="az-wb-card-title"><span>🎯</span> ${__('SLA Performance')}</h3>
                            </div>
                            <div class="az-wb-card-body">
                                <div class="az-wb-sla-container">
                                    <div class="az-wb-sla-gauge">
                                        <svg width="180" height="180" viewBox="0 0 180 180">
                                            <circle class="az-wb-sla-circle" cx="90" cy="90" r="78"/>
                                            <circle class="az-wb-sla-progress" cx="90" cy="90" r="78" 
                                                stroke="url(#slaGradient)" 
                                                stroke-dasharray="490" 
                                                stroke-dashoffset="490"/>
                                            <defs>
                                                <linearGradient id="slaGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                                    <stop offset="0%" style="stop-color:#43e97b"/>
                                                    <stop offset="100%" style="stop-color:#38f9d7"/>
                                                </linearGradient>
                                            </defs>
                                        </svg>
                                        <div class="az-wb-sla-text">
                                            <div class="az-wb-sla-value sla-value">--%</div>
                                            <div class="az-wb-sla-label">${__('SLA Met')}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Queue Status -->
                        <div class="az-wb-card">
                            <div class="az-wb-card-header">
                                <h3 class="az-wb-card-title"><span>📋</span> ${__('Queue Status')}</h3>
                            </div>
                            <div class="az-wb-card-body queue-container">
                                <p class="text-center" style="opacity: 0.5;">${__('No queues configured')}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).appendTo(this.page.main);
    }
    
    setup_realtime() {
        frappe.realtime.on('arrowz_wallboard_update', (data) => {
            this.update_stats(data);
        });
        
        frappe.realtime.on('arrowz_call_event', () => {
            this.refresh();
        });
    }
    
    start_auto_refresh() {
        this.refresh_interval = setInterval(() => this.refresh(), 10000);
    }
    
    start_clock() {
        const updateClock = () => {
            const now = new Date();
            const time = now.toLocaleTimeString('en-US', { hour12: false });
            const date = now.toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            
            this.$container.find('.az-wb-time').text(time);
            this.$container.find('.az-wb-date').text(date);
        };
        
        updateClock();
        setInterval(updateClock, 1000);
    }
    
    async refresh() {
        try {
            const r = await frappe.call({ 
                method: 'arrowz.api.wallboard.get_wallboard_data' 
            });
            if (r.message) {
                this.update_stats(r.message);
            }
        } catch (e) { 
            console.error('Error refreshing wallboard:', e);
        }
    }
    
    update_stats(data) {
        // Update main stats
        this.$container.find('.stat-active').text(data.active_calls || 0);
        this.$container.find('.stat-agents').text(data.available_agents || 0);
        this.$container.find('.stat-waiting').text(data.waiting_calls || 0);
        this.$container.find('.stat-today').text(data.calls_today || 0);
        this.$container.find('.stat-answered').text((data.answer_rate || 0) + '%');
        
        // Update SLA gauge
        this.update_sla_gauge(data.sla_percentage || 0);
        
        // Update agents grid
        this.render_agents(data.agents || []);
        
        // Update active calls
        this.render_active_calls(data.active_call_list || []);
        
        // Update queues
        this.render_queues(data.queues || []);
    }
    
    update_sla_gauge(percentage) {
        const circumference = 490;
        const offset = circumference - (percentage / 100) * circumference;
        
        this.$container.find('.az-wb-sla-progress').attr('stroke-dashoffset', offset);
        this.$container.find('.sla-value').text(percentage + '%');
        
        // Change color based on percentage
        const gradient = this.$container.find('#slaGradient');
        if (percentage >= 90) {
            gradient.find('stop:first').css('stop-color', '#43e97b');
            gradient.find('stop:last').css('stop-color', '#38f9d7');
        } else if (percentage >= 70) {
            gradient.find('stop:first').css('stop-color', '#ffd200');
            gradient.find('stop:last').css('stop-color', '#f7971e');
        } else {
            gradient.find('stop:first').css('stop-color', '#ff6b6b');
            gradient.find('stop:last').css('stop-color', '#ff4757');
        }
    }
    
    render_agents(agents) {
        const $grid = this.$container.find('.agent-grid-container').empty();
        
        if (!agents.length) {
            $grid.html(`<p class="text-center" style="opacity: 0.5; grid-column: 1/-1;">${__('No agents online')}</p>`);
            return;
        }
        
        agents.forEach(agent => {
            const initials = (agent.name || 'A').split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
            const status = (agent.status || 'offline').toLowerCase();
            
            $grid.append(`
                <div class="az-wb-agent ${status}">
                    <div class="az-wb-agent-avatar">
                        ${initials}
                        <div class="az-wb-agent-status-dot"></div>
                    </div>
                    <div class="az-wb-agent-name">${agent.name || '-'}</div>
                    <div class="az-wb-agent-ext">${agent.extension || '-'}</div>
                    <span class="az-wb-agent-status">${agent.status || 'Offline'}</span>
                </div>
            `);
        });
    }
    
    render_active_calls(calls) {
        const $container = this.$container.find('.active-calls-container').empty();
        
        if (!calls.length) {
            $container.html(`
                <div class="az-wb-no-data">
                    <svg fill="currentColor" viewBox="0 0 24 24"><path d="M6.62 10.79c1.44 2.83 3.76 5.14 6.59 6.59l2.2-2.2c.27-.27.67-.36 1.02-.24 1.12.37 2.33.57 3.57.57.55 0 1 .45 1 1V20c0 .55-.45 1-1 1-9.39 0-17-7.61-17-17 0-.55.45-1 1-1h3.5c.55 0 1 .45 1 1 0 1.25.2 2.45.57 3.57.11.35.03.74-.25 1.02l-2.2 2.2z"/></svg>
                    <p>${__('No active calls')}</p>
                </div>
            `);
            return;
        }
        
        let html = `
            <table class="az-wb-calls-table">
                <thead>
                    <tr>
                        <th>${__('Caller')}</th>
                        <th>${__('Agent')}</th>
                        <th>${__('Duration')}</th>
                        <th>${__('Status')}</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        calls.forEach(call => {
            const statusClass = call.status === 'Ringing' ? 'ringing' : 
                               call.status === 'On Hold' ? 'hold' : 'active';
            html += `
                <tr>
                    <td><strong>${call.caller || '-'}</strong></td>
                    <td>${call.agent || '-'}</td>
                    <td><span class="az-wb-call-timer">${this.format_duration(call.duration || 0)}</span></td>
                    <td><span class="az-wb-call-status ${statusClass}">● ${call.status || '-'}</span></td>
                </tr>
            `;
        });
        
        html += '</tbody></table>';
        $container.html(html);
    }
    
    render_queues(queues) {
        const $container = this.$container.find('.queue-container').empty();
        
        if (!queues.length) {
            $container.html(`<p class="text-center" style="opacity: 0.5;">${__('No queues configured')}</p>`);
            return;
        }
        
        queues.forEach(queue => {
            const percentage = Math.min(100, (queue.waiting / 10) * 100);
            const level = queue.waiting > 5 ? 'high' : queue.waiting > 2 ? 'medium' : 'low';
            
            $container.append(`
                <div class="az-wb-queue-item">
                    <div class="az-wb-queue-header">
                        <span class="az-wb-queue-name">${queue.name || '-'}</span>
                        <span class="az-wb-queue-count">${queue.waiting || 0}</span>
                    </div>
                    <div class="az-wb-queue-bar">
                        <div class="az-wb-queue-fill ${level}" style="width: ${percentage}%"></div>
                    </div>
                </div>
            `);
        });
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
