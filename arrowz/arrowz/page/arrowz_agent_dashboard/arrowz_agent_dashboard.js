/**
 * Arrowz Agent Dashboard
 * Real-time agent monitoring and call management
 */

frappe.pages['arrowz-agent-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Agent Dashboard'),
        single_column: true
    });
    
    wrapper.arrowz_dashboard = new ArrowzAgentDashboard(page);
};

frappe.pages['arrowz-agent-dashboard'].on_page_show = function(wrapper) {
    if (wrapper.arrowz_dashboard) {
        wrapper.arrowz_dashboard.refresh();
    }
};

class ArrowzAgentDashboard {
    constructor(page) {
        this.page = page;
        this.current_user = frappe.session.user;
        this.make();
        this.setup_realtime();
        this.refresh();
    }
    
    make() {
        this.$container = $(`
            <div class="arrowz-agent-dashboard">
                <div class="agent-status-bar card mb-3">
                    <div class="card-body d-flex justify-content-between align-items-center">
                        <div class="agent-info">
                            <h5 class="mb-0">${this.current_user}</h5>
                            <small class="text-muted">Extension: <span class="agent-extension">-</span></small>
                        </div>
                        <div class="agent-status-controls d-flex align-items-center gap-3">
                            <div class="btn-group">
                                <button class="btn btn-sm btn-success btn-status active" data-status="available">Available</button>
                                <button class="btn btn-sm btn-warning btn-status" data-status="busy">Busy</button>
                                <button class="btn btn-sm btn-secondary btn-status" data-status="away">Away</button>
                                <button class="btn btn-sm btn-danger btn-status" data-status="dnd">DND</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mb-3">
                    <div class="col-md-3">
                        <div class="stat-card card h-100">
                            <div class="card-body text-center">
                                <h3 class="stat-value calls-today">0</h3>
                                <p class="stat-label mb-0">Calls Today</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card card h-100">
                            <div class="card-body text-center">
                                <h3 class="stat-value avg-duration">0:00</h3>
                                <p class="stat-label mb-0">Avg Duration</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card card h-100">
                            <div class="card-body text-center">
                                <h3 class="stat-value inbound-count">0</h3>
                                <p class="stat-label mb-0">Inbound</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card card h-100">
                            <div class="card-body text-center">
                                <h3 class="stat-value outbound-count">0</h3>
                                <p class="stat-label mb-0">Outbound</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-4">
                        <div class="card active-call-panel">
                            <div class="card-header"><h6 class="mb-0">Active Call</h6></div>
                            <div class="card-body">
                                <div class="no-active-call text-center text-muted py-4">
                                    <p>No active call</p>
                                </div>
                                <div class="active-call-info d-none">
                                    <div class="caller-info text-center mb-3">
                                        <h5 class="caller-name">Unknown</h5>
                                        <p class="caller-number text-muted">-</p>
                                        <span class="badge bg-success call-status">Connected</span>
                                        <p class="call-duration mt-2 fs-4">00:00</p>
                                    </div>
                                    <div class="call-actions d-flex justify-content-center gap-2">
                                        <button class="btn btn-warning btn-hold">Hold</button>
                                        <button class="btn btn-info btn-mute">Mute</button>
                                        <button class="btn btn-primary btn-transfer">Transfer</button>
                                        <button class="btn btn-danger btn-hangup">Hang Up</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card mt-3">
                            <div class="card-header"><h6 class="mb-0">Quick Dial</h6></div>
                            <div class="card-body">
                                <div class="input-group mb-3">
                                    <input type="text" class="form-control dial-number" placeholder="Enter number">
                                    <button class="btn btn-success btn-dial">Dial</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-8">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h6 class="mb-0">Recent Calls</h6>
                                <button class="btn btn-sm btn-outline-primary btn-refresh">Refresh</button>
                            </div>
                            <div class="card-body p-0">
                                <div class="table-responsive">
                                    <table class="table table-hover mb-0">
                                        <thead>
                                            <tr>
                                                <th>Direction</th>
                                                <th>Number</th>
                                                <th>Contact</th>
                                                <th>Duration</th>
                                                <th>Time</th>
                                                <th>Status</th>
                                            </tr>
                                        </thead>
                                        <tbody class="recent-calls-body">
                                            <tr><td colspan="6" class="text-center text-muted py-4">Loading...</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).appendTo(this.page.main);
        
        this.setup_handlers();
    }
    
    setup_handlers() {
        const me = this;
        
        this.$container.find('.btn-status').on('click', function() {
            me.set_agent_status($(this).data('status'));
        });
        
        this.$container.find('.btn-dial').on('click', function() {
            const number = me.$container.find('.dial-number').val();
            if (number) me.make_call(number);
        });
        
        this.$container.find('.btn-hold').on('click', () => me.toggle_hold());
        this.$container.find('.btn-mute').on('click', () => me.toggle_mute());
        this.$container.find('.btn-transfer').on('click', () => me.show_transfer_dialog());
        this.$container.find('.btn-hangup').on('click', () => me.hangup());
        this.$container.find('.btn-refresh').on('click', () => me.refresh());
    }
    
    setup_realtime() {
        frappe.realtime.on('arrowz_call_event', (data) => this.handle_call_event(data));
    }
    
    async refresh() {
        await this.load_agent_info();
        await this.load_stats();
        await this.load_recent_calls();
    }
    
    async load_agent_info() {
        try {
            const r = await frappe.call({ method: 'arrowz.api.agent.get_agent_info' });
            if (r.message) {
                this.$container.find('.agent-extension').text(r.message.extension || '-');
            }
        } catch (e) { console.error('Error loading agent info:', e); }
    }
    
    async load_stats() {
        try {
            const r = await frappe.call({ method: 'arrowz.api.agent.get_agent_stats' });
            if (r.message) {
                this.$container.find('.calls-today').text(r.message.total_calls || 0);
                this.$container.find('.avg-duration').text(this.format_duration(r.message.avg_duration || 0));
                this.$container.find('.inbound-count').text(r.message.inbound || 0);
                this.$container.find('.outbound-count').text(r.message.outbound || 0);
            }
        } catch (e) { console.error('Error loading stats:', e); }
    }
    
    async load_recent_calls() {
        try {
            const r = await frappe.call({ method: 'arrowz.api.agent.get_recent_calls', args: { limit: 20 } });
            const $tbody = this.$container.find('.recent-calls-body');
            $tbody.empty();
            
            if (r.message && r.message.length > 0) {
                r.message.forEach(call => {
                    const dirIcon = call.direction === 'inbound' ? '↓' : '↑';
                    const statusBadge = call.status === 'answered' 
                        ? '<span class="badge bg-success">Answered</span>'
                        : '<span class="badge bg-danger">Missed</span>';
                    
                    $tbody.append(`
                        <tr>
                            <td>${dirIcon}</td>
                            <td>${call.caller_id || call.callee_id || '-'}</td>
                            <td>${call.contact_name || '-'}</td>
                            <td>${this.format_duration(call.duration || 0)}</td>
                            <td>${frappe.datetime.prettyDate(call.start_time)}</td>
                            <td>${statusBadge}</td>
                        </tr>
                    `);
                });
            } else {
                $tbody.append('<tr><td colspan="6" class="text-center text-muted py-4">No recent calls</td></tr>');
            }
        } catch (e) { console.error('Error loading recent calls:', e); }
    }
    
    async set_agent_status(status) {
        try {
            await frappe.call({ method: 'arrowz.api.agent.set_status', args: { status } });
            this.$container.find('.btn-status').removeClass('active');
            this.$container.find(`.btn-status[data-status="${status}"]`).addClass('active');
            frappe.show_alert({ message: __('Status updated'), indicator: 'green' });
        } catch (e) { frappe.show_alert({ message: __('Failed to update status'), indicator: 'red' }); }
    }
    
    make_call(number) {
        if (window.arrowz && window.arrowz.softphone) {
            window.arrowz.softphone.call(number);
        }
    }
    
    toggle_hold() {
        if (window.arrowz && window.arrowz.softphone) window.arrowz.softphone.toggleHold();
    }
    
    toggle_mute() {
        if (window.arrowz && window.arrowz.softphone) window.arrowz.softphone.toggleMute();
    }
    
    hangup() {
        if (window.arrowz && window.arrowz.softphone) window.arrowz.softphone.hangup();
    }
    
    show_transfer_dialog() {
        const d = new frappe.ui.Dialog({
            title: __('Transfer Call'),
            fields: [
                { fieldname: 'transfer_type', label: __('Type'), fieldtype: 'Select', options: 'Blind\nAttended', default: 'Blind' },
                { fieldname: 'target', label: __('Target'), fieldtype: 'Data', reqd: 1 }
            ],
            primary_action_label: __('Transfer'),
            primary_action: (values) => {
                if (window.arrowz && window.arrowz.softphone) {
                    window.arrowz.softphone.transfer(values.target, values.transfer_type.toLowerCase());
                }
                d.hide();
            }
        });
        d.show();
    }
    
    handle_call_event(data) {
        if (data.event === 'ringing' || data.event === 'connected') {
            this.$container.find('.no-active-call').addClass('d-none');
            this.$container.find('.active-call-info').removeClass('d-none');
            this.$container.find('.caller-name').text(data.contact_name || 'Unknown');
            this.$container.find('.caller-number').text(data.caller_id || '-');
        } else if (data.event === 'hangup') {
            this.$container.find('.no-active-call').removeClass('d-none');
            this.$container.find('.active-call-info').addClass('d-none');
            this.refresh();
        }
    }
    
    format_duration(seconds) {
        if (!seconds) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}
