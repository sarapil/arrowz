/**
 * Arrowz Main Dashboard
 * Overview of call center operations
 */

frappe.pages['arrowz-dashboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Arrowz Dashboard'),
        single_column: true
    });
    
    wrapper.dashboard = new ArrowzMainDashboard(page);
};

frappe.pages['arrowz-dashboard'].on_page_show = function(wrapper) {
    if (wrapper.dashboard) {
        wrapper.dashboard.refresh();
    }
};

class ArrowzMainDashboard {
    constructor(page) {
        this.page = page;
        this.make();
        this.refresh();
    }
    
    make() {
        this.page.set_secondary_action(__('Refresh'), () => this.refresh(), 'refresh');
        
        this.$container = $(`
            <div class="arrowz-main-dashboard">
                <!-- Quick Stats Row -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card stat-card bg-primary text-white">
                            <div class="card-body text-center">
                                <h2 class="stat-active-calls mb-0">0</h2>
                                <p class="mb-0"><i class="fa fa-phone"></i> Active Calls</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stat-card bg-success text-white">
                            <div class="card-body text-center">
                                <h2 class="stat-agents-online mb-0">0</h2>
                                <p class="mb-0"><i class="fa fa-users"></i> Agents Online</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stat-card bg-info text-white">
                            <div class="card-body text-center">
                                <h2 class="stat-calls-today mb-0">0</h2>
                                <p class="mb-0"><i class="fa fa-history"></i> Calls Today</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card stat-card bg-warning text-dark">
                            <div class="card-body text-center">
                                <h2 class="stat-avg-duration mb-0">0:00</h2>
                                <p class="mb-0"><i class="fa fa-clock-o"></i> Avg Duration</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div class="row mb-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header"><h6 class="mb-0">Quick Actions</h6></div>
                            <div class="card-body">
                                <div class="btn-group">
                                    <a href="/app/arrowz-agent-dashboard" class="btn btn-outline-primary">
                                        <i class="fa fa-headphones"></i> Agent Dashboard
                                    </a>
                                    <a href="/app/arrowz-wallboard" class="btn btn-outline-success">
                                        <i class="fa fa-desktop"></i> Wallboard
                                    </a>
                                    <a href="/app/arrowz-analytics" class="btn btn-outline-info">
                                        <i class="fa fa-bar-chart"></i> Analytics
                                    </a>
                                    <a href="/app/arrowz-communications" class="btn btn-outline-warning">
                                        <i class="fa fa-comments"></i> Communications
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Main Content Row -->
                <div class="row">
                    <div class="col-md-8">
                        <div class="card">
                            <div class="card-header"><h6 class="mb-0">Recent Calls</h6></div>
                            <div class="card-body p-0">
                                <div class="table-responsive">
                                    <table class="table table-hover mb-0">
                                        <thead>
                                            <tr>
                                                <th>Direction</th>
                                                <th>Number</th>
                                                <th>Agent</th>
                                                <th>Duration</th>
                                                <th>Time</th>
                                            </tr>
                                        </thead>
                                        <tbody class="recent-calls-body">
                                            <tr><td colspan="5" class="text-center text-muted py-4">Loading...</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header"><h6 class="mb-0">Agent Status</h6></div>
                            <div class="card-body agent-status-list">
                                <p class="text-muted">Loading agents...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).appendTo(this.page.main);
    }
    
    async refresh() {
        await Promise.all([
            this.loadStats(),
            this.loadRecentCalls(),
            this.loadAgentStatus()
        ]);
    }
    
    async loadStats() {
        try {
            const r = await frappe.call({ method: 'arrowz.api.wallboard.get_wallboard_data' });
            if (r.message) {
                this.$container.find('.stat-active-calls').text(r.message.active_calls || 0);
                this.$container.find('.stat-agents-online').text(r.message.available_agents || 0);
                this.$container.find('.stat-calls-today').text(r.message.calls_today || 0);
                this.$container.find('.stat-avg-duration').text(this.formatDuration(r.message.avg_duration || 0));
            }
        } catch (e) { console.error('Error loading stats:', e); }
    }
    
    async loadRecentCalls() {
        try {
            const r = await frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'AZ Call Log',
                    fields: ['name', 'direction', 'caller_id', 'callee_id', 'extension', 'duration', 'start_time'],
                    order_by: 'start_time desc',
                    limit_page_length: 10
                }
            });
            
            const $tbody = this.$container.find('.recent-calls-body').empty();
            
            if (r.message && r.message.length) {
                r.message.forEach(call => {
                    const icon = call.direction === 'Inbound' ? '↓' : '↑';
                    const number = call.direction === 'Inbound' ? call.caller_id : call.callee_id;
                    $tbody.append(`
                        <tr>
                            <td>${icon} ${call.direction}</td>
                            <td>${number || '-'}</td>
                            <td>${call.extension || '-'}</td>
                            <td>${this.formatDuration(call.duration || 0)}</td>
                            <td>${frappe.datetime.prettyDate(call.start_time)}</td>
                        </tr>
                    `);
                });
            } else {
                $tbody.append('<tr><td colspan="5" class="text-center text-muted py-4">No recent calls</td></tr>');
            }
        } catch (e) { console.error('Error loading calls:', e); }
    }
    
    async loadAgentStatus() {
        try {
            const r = await frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'AZ Extension',
                    fields: ['extension', 'display_name', 'status', 'user'],
                    filters: { is_active: 1 },
                    limit_page_length: 20
                }
            });
            
            const $list = this.$container.find('.agent-status-list').empty();
            
            if (r.message && r.message.length) {
                r.message.forEach(agent => {
                    const statusClass = agent.status === 'Available' ? 'success' : 
                                       agent.status === 'On Call' ? 'warning' : 'secondary';
                    $list.append(`
                        <div class="d-flex justify-content-between align-items-center mb-2 p-2 border-bottom">
                            <div>
                                <strong>${agent.display_name || agent.extension}</strong>
                                <br><small class="text-muted">Ext: ${agent.extension}</small>
                            </div>
                            <span class="badge bg-${statusClass}">${agent.status || 'Offline'}</span>
                        </div>
                    `);
                });
            } else {
                $list.html('<p class="text-muted">No agents configured</p>');
            }
        } catch (e) { console.error('Error loading agents:', e); }
    }
    
    formatDuration(seconds) {
        if (!seconds) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}
