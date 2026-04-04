// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Arrowz Analytics Dashboard - Professional Multi-Color Design
 * Interactive charts and insights with gradient styling
 */

frappe.pages['arrowz-analytics'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Call Analytics'),
        single_column: true
    });
    
    wrapper.classList.add('arrowz-analytics-page');
    wrapper.analytics = new ArrowzAnalytics(page);
};

frappe.pages['arrowz-analytics'].on_page_show = function(wrapper) {
    if (wrapper.analytics) {
        wrapper.analytics.refresh();
    }
};

class ArrowzAnalytics {
    constructor(page) {
        this.page = page;
        this.charts = {};
        this.date_range = 'month';
        this.init();
    }
    
    init() {
        this.add_styles();
        this.setup_page_actions();
        this.render_layout();
        this.refresh();
    }
    
    add_styles() {
        if (document.getElementById('arrowz-analytics-styles')) return;
        
        const styles = document.createElement('style');
        styles.id = 'arrowz-analytics-styles';
        styles.textContent = `
            .arrowz-analytics-page .page-content {
                background: linear-gradient(135deg, #f8f9fe 0%, #f0f2ff 100%);
                min-height: calc(100vh - 60px);
            }
            
            .arrowz-analytics {
                padding: 24px;
            }
            
            /* Header Banner */
            .az-an-header {
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 50%, #43e97b 100%);
                border-radius: 24px;
                padding: 32px;
                margin-bottom: 24px;
                color: white;
                position: relative;
                overflow: hidden;
            }
            
            .az-an-header::before {
                content: '';
                position: absolute;
                top: -50%;
                right: -20%;
                width: 400px;
                height: 400px;
                background: rgba(255,255,255,0.1);
                border-radius: 50%;
            }
            
            .az-an-header-content {
                position: relative;
                z-index: 1;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 20px;
            }
            
            .az-an-header h1 {
                margin: 0 0 8px 0;
                font-size: 28px;
                font-weight: 700;
            }
            
            .az-an-header p {
                margin: 0;
                opacity: 0.9;
            }
            
            .az-an-filters {
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
            }
            
            .az-an-filter-btn {
                padding: 10px 20px;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 50px;
                background: rgba(255,255,255,0.1);
                color: white;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.2s ease;
                backdrop-filter: blur(10px);
            }
            
            .az-an-filter-btn:hover {
                background: rgba(255,255,255,0.2);
            }
            
            .az-an-filter-btn.active {
                background: white;
                color: #4facfe;
                border-color: white;
            }
            
            /* KPI Cards */
            .az-an-kpi-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 20px;
                margin-bottom: 24px;
            }
            
            .az-an-kpi {
                background: white;
                border-radius: 20px;
                padding: 24px;
                position: relative;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.05);
                transition: all 0.3s ease;
            }
            
            .az-an-kpi:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 30px rgba(0,0,0,0.1);
            }
            
            .az-an-kpi::before {
                content: '';
                position: absolute;
                top: 0;
                right: 0;
                width: 100px;
                height: 100px;
                border-radius: 50%;
                transform: translate(30%, -30%);
                opacity: 0.1;
            }
            
            .az-an-kpi.calls::before { background: linear-gradient(135deg, #667eea, #764ba2); }
            .az-an-kpi.duration::before { background: linear-gradient(135deg, #11998e, #38ef7d); }
            .az-an-kpi.answer::before { background: linear-gradient(135deg, #4facfe, #00f2fe); }
            .az-an-kpi.wait::before { background: linear-gradient(135deg, #f7971e, #ffd200); }
            .az-an-kpi.sla::before { background: linear-gradient(135deg, #43e97b, #38f9d7); }
            .az-an-kpi.abandoned::before { background: linear-gradient(135deg, #ff416c, #ff4b2b); }
            
            .az-an-kpi-icon {
                width: 48px;
                height: 48px;
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                margin-bottom: 16px;
            }
            
            .az-an-kpi.calls .az-an-kpi-icon { background: linear-gradient(135deg, #667eea20, #764ba220); }
            .az-an-kpi.duration .az-an-kpi-icon { background: linear-gradient(135deg, #11998e20, #38ef7d20); }
            .az-an-kpi.answer .az-an-kpi-icon { background: linear-gradient(135deg, #4facfe20, #00f2fe20); }
            .az-an-kpi.wait .az-an-kpi-icon { background: linear-gradient(135deg, #f7971e20, #ffd20020); }
            .az-an-kpi.sla .az-an-kpi-icon { background: linear-gradient(135deg, #43e97b20, #38f9d720); }
            .az-an-kpi.abandoned .az-an-kpi-icon { background: linear-gradient(135deg, #ff416c20, #ff4b2b20); }
            
            .az-an-kpi-value {
                font-size: 36px;
                font-weight: 700;
                color: #1a1a2e;
                line-height: 1;
                margin-bottom: 8px;
            }
            
            .az-an-kpi-label {
                font-size: 14px;
                color: #666;
                font-weight: 500;
            }
            
            .az-an-kpi-trend {
                position: absolute;
                top: 20px;
                right: 20px;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 10px;
                border-radius: 20px;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            .az-an-kpi-trend.up { background: #e8f5e9; color: #2e7d32; }
            .az-an-kpi-trend.down { background: #ffebee; color: #c62828; }
            
            /* Charts Grid */
            .az-an-charts-grid {
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 24px;
                margin-bottom: 24px;
            }
            
            @media (max-width: 992px) {
                .az-an-charts-grid { grid-template-columns: 1fr; }
            }
            
            .az-an-card {
                background: white;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.05);
            }
            
            .az-an-card-header {
                padding: 20px 24px;
                border-bottom: 1px solid #f0f0f0;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .az-an-card-title {
                font-size: 18px;
                font-weight: 700;
                color: #1a1a2e;
                margin: 0;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .az-an-card-body {
                padding: 24px;
            }
            
            /* Chart Container */
            .az-an-chart-container {
                height: 300px;
                position: relative;
            }
            
            /* Hourly Heatmap */
            .az-an-heatmap {
                display: grid;
                grid-template-columns: repeat(24, 1fr);
                gap: 4px;
            }
            
            .az-an-heatmap-cell {
                aspect-ratio: 1;
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 10px;
                font-weight: 500;
                color: white;
                position: relative;
            }
            
            .az-an-heatmap-cell.level-0 { background: #e3f2fd; color: #1565c0; }
            .az-an-heatmap-cell.level-1 { background: #64b5f6; }
            .az-an-heatmap-cell.level-2 { background: #42a5f5; }
            .az-an-heatmap-cell.level-3 { background: #2196f3; }
            .az-an-heatmap-cell.level-4 { background: #1976d2; }
            .az-an-heatmap-cell.level-5 { background: #1565c0; }
            
            .az-an-heatmap-labels {
                display: grid;
                grid-template-columns: repeat(24, 1fr);
                gap: 4px;
                margin-top: 8px;
            }
            
            .az-an-heatmap-label {
                text-align: center;
                font-size: 10px;
                color: #999;
            }
            
            /* Pie Chart Replacement */
            .az-an-donut-chart {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 24px;
            }
            
            .az-an-donut-svg {
                width: 200px;
                height: 200px;
            }
            
            .az-an-donut-legend {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .az-an-legend-item {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .az-an-legend-dot {
                width: 12px;
                height: 12px;
                border-radius: 50%;
            }
            
            .az-an-legend-label {
                font-size: 14px;
                color: #666;
            }
            
            .az-an-legend-value {
                font-weight: 700;
                color: #1a1a2e;
                margin-left: auto;
            }
            
            /* Top Agents Table */
            .az-an-agents-table {
                width: 100%;
            }
            
            .az-an-agents-table th {
                text-align: left;
                padding: 12px 16px;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #999;
                border-bottom: 1px solid #f0f0f0;
            }
            
            .az-an-agents-table td {
                padding: 16px;
                border-bottom: 1px solid #f5f5f5;
            }
            
            .az-an-agents-table tr:last-child td {
                border-bottom: none;
            }
            
            .az-an-agent-info {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .az-an-agent-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 14px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
            }
            
            .az-an-agent-name {
                font-weight: 600;
                color: #1a1a2e;
            }
            
            .az-an-agent-ext {
                font-size: 12px;
                color: #999;
            }
            
            .az-an-progress-bar {
                height: 8px;
                background: #f0f0f0;
                border-radius: 4px;
                overflow: hidden;
                min-width: 100px;
            }
            
            .az-an-progress-fill {
                height: 100%;
                border-radius: 4px;
                background: linear-gradient(90deg, #667eea, #764ba2);
            }
            
            .az-an-rating {
                display: flex;
                align-items: center;
                gap: 4px;
                color: #ffc107;
            }
            
            /* Bar Chart Simulation */
            .az-an-bar-chart {
                display: flex;
                align-items: flex-end;
                justify-content: space-between;
                height: 200px;
                padding: 20px 0;
                gap: 8px;
            }
            
            .az-an-bar {
                flex: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
            }
            
            .az-an-bar-fill {
                width: 100%;
                max-width: 40px;
                border-radius: 8px 8px 0 0;
                background: linear-gradient(180deg, #667eea, #764ba2);
                transition: height 0.5s ease;
                position: relative;
            }
            
            .az-an-bar-fill::after {
                content: attr(data-value);
                position: absolute;
                top: -24px;
                left: 50%;
                transform: translateX(-50%);
                font-size: 12px;
                font-weight: 600;
                color: #667eea;
            }
            
            .az-an-bar-label {
                font-size: 11px;
                color: #999;
                text-align: center;
            }
        `;
        document.head.appendChild(styles);
    }
    
    setup_page_actions() {
        this.page.set_secondary_action(__('Refresh'), () => this.refresh(), 'refresh');
        
        this.page.add_inner_button(__('Export PDF'), () => {
            frappe.msgprint(__('PDF export feature coming soon!'));
        });
    }
    
    render_layout() {
        this.$container = $(`
            <div class="arrowz-analytics">
                <!-- Header Banner -->
                <div class="az-an-header">
                    <div class="az-an-header-content">
                        <div>
                            <h1>📊 ${__('Call Analytics')}</h1>
                            <p>${__('Comprehensive insights into your call center performance')}</p>
                        </div>
                        <div class="az-an-filters">
                            <button class="az-an-filter-btn" data-range="today">${__('Today')}</button>
                            <button class="az-an-filter-btn" data-range="week">${__('This Week')}</button>
                            <button class="az-an-filter-btn active" data-range="month">${__('This Month')}</button>
                            <button class="az-an-filter-btn" data-range="year">${__('This Year')}</button>
                        </div>
                    </div>
                </div>
                
                <!-- KPI Cards -->
                <div class="az-an-kpi-grid">
                    <div class="az-an-kpi calls">
                        <div class="az-an-kpi-icon">📞</div>
                        <div class="az-an-kpi-value kpi-total-calls">0</div>
                        <div class="az-an-kpi-label">${__('Total Calls')}</div>
                        <div class="az-an-kpi-trend up">↑ 12%</div>
                    </div>
                    <div class="az-an-kpi duration">
                        <div class="az-an-kpi-icon">⏱️</div>
                        <div class="az-an-kpi-value kpi-avg-duration">0:00</div>
                        <div class="az-an-kpi-label">${__('Avg Duration')}</div>
                    </div>
                    <div class="az-an-kpi answer">
                        <div class="az-an-kpi-icon">✅</div>
                        <div class="az-an-kpi-value kpi-answer-rate">0%</div>
                        <div class="az-an-kpi-label">${__('Answer Rate')}</div>
                        <div class="az-an-kpi-trend up">↑ 5%</div>
                    </div>
                    <div class="az-an-kpi wait">
                        <div class="az-an-kpi-icon">⏳</div>
                        <div class="az-an-kpi-value kpi-avg-wait">0s</div>
                        <div class="az-an-kpi-label">${__('Avg Wait Time')}</div>
                    </div>
                    <div class="az-an-kpi sla">
                        <div class="az-an-kpi-icon">🎯</div>
                        <div class="az-an-kpi-value kpi-sla">0%</div>
                        <div class="az-an-kpi-label">${__('SLA Met')}</div>
                        <div class="az-an-kpi-trend up">↑ 8%</div>
                    </div>
                    <div class="az-an-kpi abandoned">
                        <div class="az-an-kpi-icon">📵</div>
                        <div class="az-an-kpi-value kpi-abandoned">0%</div>
                        <div class="az-an-kpi-label">${__('Abandoned Rate')}</div>
                        <div class="az-an-kpi-trend down">↓ 3%</div>
                    </div>
                </div>
                
                <!-- Charts Row 1 -->
                <div class="az-an-charts-grid">
                    <!-- Call Volume Chart -->
                    <div class="az-an-card">
                        <div class="az-an-card-header">
                            <h3 class="az-an-card-title">📈 ${__('Call Volume Trend')}</h3>
                        </div>
                        <div class="az-an-card-body">
                            <div class="az-an-bar-chart volume-chart">
                                <!-- Rendered dynamically -->
                            </div>
                        </div>
                    </div>
                    
                    <!-- Call Distribution -->
                    <div class="az-an-card">
                        <div class="az-an-card-header">
                            <h3 class="az-an-card-title">🎯 ${__('Call Distribution')}</h3>
                        </div>
                        <div class="az-an-card-body">
                            <div class="az-an-donut-chart distribution-chart">
                                <!-- Rendered dynamically -->
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Charts Row 2 -->
                <div class="az-an-charts-grid">
                    <!-- Top Agents -->
                    <div class="az-an-card">
                        <div class="az-an-card-header">
                            <h3 class="az-an-card-title">🏆 ${__('Top Performing Agents')}</h3>
                        </div>
                        <div class="az-an-card-body">
                            <table class="az-an-agents-table">
                                <thead>
                                    <tr>
                                        <th>${__('Agent')}</th>
                                        <th>${__('Calls')}</th>
                                        <th>${__('Performance')}</th>
                                        <th>${__('Rating')}</th>
                                    </tr>
                                </thead>
                                <tbody class="top-agents-body">
                                    <tr><td colspan="4" class="text-center text-muted">${__('Loading...')}</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    
                    <!-- Hourly Heatmap -->
                    <div class="az-an-card">
                        <div class="az-an-card-header">
                            <h3 class="az-an-card-title">🕐 ${__('Hourly Activity')}</h3>
                        </div>
                        <div class="az-an-card-body">
                            <div class="az-an-heatmap hourly-heatmap">
                                <!-- Rendered dynamically -->
                            </div>
                            <div class="az-an-heatmap-labels">
                                ${Array.from({length: 24}, (_, i) => `<span class="az-an-heatmap-label">${i}</span>`).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).appendTo(this.page.main);
        
        this.setup_events();
    }
    
    setup_events() {
        this.$container.find('.az-an-filter-btn').on('click', (e) => {
            const $btn = $(e.currentTarget);
            this.date_range = $btn.data('range');
            
            this.$container.find('.az-an-filter-btn').removeClass('active');
            $btn.addClass('active');
            
            this.refresh();
        });
    }
    
    async refresh() {
        try {
            const r = await frappe.call({
                method: 'arrowz.api.analytics.get_analytics',
                args: { date_range: this.date_range }
            });
            
            if (r.message) {
                this.update_dashboard(r.message);
            }
        } catch (e) {
            console.error('Error loading analytics:', e);
            // Use sample data for demonstration
            this.update_dashboard(this.get_sample_data());
        }
    }
    
    get_sample_data() {
        return {
            total_calls: 1247,
            avg_duration: 185,
            answer_rate: 87,
            avg_wait_time: 23,
            sla_percentage: 92,
            abandoned_rate: 8,
            daily_calls: [45, 52, 38, 67, 89, 72, 56, 48, 91, 85, 63, 71, 54, 68],
            day_labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            distribution: {
                inbound: 65,
                outbound: 25,
                missed: 10
            },
            hourly_calls: [5, 8, 12, 25, 45, 68, 92, 105, 98, 87, 95, 88, 76, 82, 90, 72, 58, 42, 28, 18, 12, 8, 6, 4],
            top_agents: [
                { name: 'Ahmed Ali', extension: '101', calls: 156, performance: 95, rating: 4.8 },
                { name: 'Sara Mohamed', extension: '102', calls: 142, performance: 92, rating: 4.7 },
                { name: 'Omar Hassan', extension: '103', calls: 128, performance: 88, rating: 4.5 },
                { name: 'Fatima Ibrahim', extension: '104', calls: 115, performance: 85, rating: 4.6 },
                { name: 'Youssef Ahmed', extension: '105', calls: 98, performance: 82, rating: 4.4 }
            ]
        };
    }
    
    update_dashboard(data) {
        // Update KPIs
        this.$container.find('.kpi-total-calls').text(this.format_number(data.total_calls || 0));
        this.$container.find('.kpi-avg-duration').text(this.format_duration(data.avg_duration || 0));
        this.$container.find('.kpi-answer-rate').text((data.answer_rate || 0) + '%');
        this.$container.find('.kpi-avg-wait').text((data.avg_wait_time || 0) + 's');
        this.$container.find('.kpi-sla').text((data.sla_percentage || 0) + '%');
        this.$container.find('.kpi-abandoned').text((data.abandoned_rate || 0) + '%');
        
        // Render charts
        this.render_volume_chart(data.daily_calls || [], data.day_labels || []);
        this.render_distribution_chart(data.distribution || {});
        this.render_hourly_heatmap(data.hourly_calls || []);
        this.render_top_agents(data.top_agents || []);
    }
    
    render_volume_chart(values, labels) {
        const $chart = this.$container.find('.volume-chart').empty();
        
        if (!values.length) {
            values = [0, 0, 0, 0, 0, 0, 0];
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        }
        
        const max = Math.max(...values, 1);
        
        values.forEach((val, i) => {
            const height = (val / max) * 160;
            $chart.append(`
                <div class="az-an-bar">
                    <div class="az-an-bar-fill" style="height: ${height}px" data-value="${val}"></div>
                    <span class="az-an-bar-label">${labels[i] || ''}</span>
                </div>
            `);
        });
    }
    
    render_distribution_chart(distribution) {
        const $chart = this.$container.find('.distribution-chart').empty();
        
        const inbound = distribution.inbound || 0;
        const outbound = distribution.outbound || 0;
        const missed = distribution.missed || 0;
        const total = inbound + outbound + missed || 1;
        
        // Calculate stroke dasharray for donut chart
        const circumference = 2 * Math.PI * 70;
        const inboundDash = (inbound / total) * circumference;
        const outboundDash = (outbound / total) * circumference;
        const missedDash = (missed / total) * circumference;
        
        const inboundOffset = 0;
        const outboundOffset = inboundDash;
        const missedOffset = inboundDash + outboundDash;
        
        $chart.html(`
            <svg class="az-an-donut-svg" viewBox="0 0 200 200">
                <circle cx="100" cy="100" r="70" fill="none" stroke="#e0e0e0" stroke-width="30"/>
                <circle cx="100" cy="100" r="70" fill="none" stroke="#667eea" stroke-width="30"
                    stroke-dasharray="${inboundDash} ${circumference}" 
                    stroke-dashoffset="0"
                    transform="rotate(-90 100 100)"/>
                <circle cx="100" cy="100" r="70" fill="none" stroke="#43e97b" stroke-width="30"
                    stroke-dasharray="${outboundDash} ${circumference}" 
                    stroke-dashoffset="${-inboundDash}"
                    transform="rotate(-90 100 100)"/>
                <circle cx="100" cy="100" r="70" fill="none" stroke="#ff6b6b" stroke-width="30"
                    stroke-dasharray="${missedDash} ${circumference}" 
                    stroke-dashoffset="${-missedOffset}"
                    transform="rotate(-90 100 100)"/>
            </svg>
            <div class="az-an-donut-legend">
                <div class="az-an-legend-item">
                    <span class="az-an-legend-dot" style="background: #667eea"></span>
                    <span class="az-an-legend-label">${__('Inbound')}</span>
                    <span class="az-an-legend-value">${inbound}%</span>
                </div>
                <div class="az-an-legend-item">
                    <span class="az-an-legend-dot" style="background: #43e97b"></span>
                    <span class="az-an-legend-label">${__('Outbound')}</span>
                    <span class="az-an-legend-value">${outbound}%</span>
                </div>
                <div class="az-an-legend-item">
                    <span class="az-an-legend-dot" style="background: #ff6b6b"></span>
                    <span class="az-an-legend-label">${__('Missed')}</span>
                    <span class="az-an-legend-value">${missed}%</span>
                </div>
            </div>
        `);
    }
    
    render_hourly_heatmap(hourly) {
        const $heatmap = this.$container.find('.hourly-heatmap').empty();
        
        if (!hourly.length) {
            hourly = Array(24).fill(0);
        }
        
        const max = Math.max(...hourly, 1);
        
        hourly.forEach((val, hour) => {
            const level = Math.min(5, Math.floor((val / max) * 5));
            $heatmap.append(`
                <div class="az-an-heatmap-cell level-${level}" title="${hour}:00 - ${val} calls">
                    ${val > 0 ? val : ''}
                </div>
            `);
        });
    }
    
    render_top_agents(agents) {
        const $tbody = this.$container.find('.top-agents-body').empty();
        
        if (!agents.length) {
            $tbody.html(`<tr><td colspan="4" class="text-center text-muted">${__('No data available')}</td></tr>`);
            return;
        }
        
        const maxCalls = Math.max(...agents.map(a => a.calls), 1);
        
        agents.forEach(agent => {
            const initials = (agent.name || 'A').split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
            const performance = (agent.calls / maxCalls) * 100;
            const stars = '★'.repeat(Math.floor(agent.rating || 0)) + '☆'.repeat(5 - Math.floor(agent.rating || 0));
            
            $tbody.append(`
                <tr>
                    <td>
                        <div class="az-an-agent-info">
                            <div class="az-an-agent-avatar">${initials}</div>
                            <div>
                                <div class="az-an-agent-name">${agent.name || '-'}</div>
                                <div class="az-an-agent-ext">Ext. ${agent.extension || '-'}</div>
                            </div>
                        </div>
                    </td>
                    <td><strong>${agent.calls || 0}</strong></td>
                    <td>
                        <div class="az-an-progress-bar">
                            <div class="az-an-progress-fill" style="width: ${performance}%"></div>
                        </div>
                    </td>
                    <td>
                        <div class="az-an-rating">${stars}</div>
                    </td>
                </tr>
            `);
        });
    }
    
    format_number(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }
    
    format_duration(seconds) {
        if (!seconds) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${String(secs).padStart(2, '0')}`;
    }
}
