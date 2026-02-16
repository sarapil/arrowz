frappe.pages['arrowz-wallboard'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Call Center Wallboard'),
        single_column: true
    });
    
    wrapper.wallboard = new ArrowzWallboard(page);
};

class ArrowzWallboard {
    constructor(page) {
        this.page = page;
        this.make();
        this.setup_realtime();
        this.refresh();
        this.start_auto_refresh();
    }
    
    make() {
        this.$container = $('<div class="arrowz-wallboard">' +
            '<div class="row mb-3">' +
                '<div class="col-md-3"><div class="card bg-primary text-white"><div class="card-body text-center">' +
                    '<h2 class="stat-active-calls">0</h2><p class="mb-0">Active Calls</p></div></div></div>' +
                '<div class="col-md-3"><div class="card bg-success text-white"><div class="card-body text-center">' +
                    '<h2 class="stat-available-agents">0</h2><p class="mb-0">Available Agents</p></div></div></div>' +
                '<div class="col-md-3"><div class="card bg-warning text-dark"><div class="card-body text-center">' +
                    '<h2 class="stat-waiting-calls">0</h2><p class="mb-0">Waiting in Queue</p></div></div></div>' +
                '<div class="col-md-3"><div class="card bg-info text-white"><div class="card-body text-center">' +
                    '<h2 class="stat-calls-today">0</h2><p class="mb-0">Calls Today</p></div></div></div>' +
            '</div>' +
            '<div class="row"><div class="col-md-6"><div class="card"><div class="card-header"><h6>Agent Status</h6></div>' +
                '<div class="card-body agent-status-list"><p class="text-muted">Loading...</p></div></div></div>' +
                '<div class="col-md-6"><div class="card"><div class="card-header"><h6>Active Calls</h6></div>' +
                '<div class="card-body active-calls-list"><p class="text-muted">No active calls</p></div></div></div>' +
            '</div>' +
        '</div>').appendTo(this.page.main);
    }
    
    setup_realtime() {
        frappe.realtime.on('arrowz_wallboard_update', (data) => this.update_stats(data));
    }
    
    start_auto_refresh() {
        this.refresh_interval = setInterval(() => this.refresh(), 10000);
    }
    
    async refresh() {
        try {
            const r = await frappe.call({ method: 'arrowz.api.wallboard.get_wallboard_data' });
            if (r.message) this.update_stats(r.message);
        } catch (e) { console.error('Error refreshing wallboard:', e); }
    }
    
    update_stats(data) {
        this.$container.find('.stat-active-calls').text(data.active_calls || 0);
        this.$container.find('.stat-available-agents').text(data.available_agents || 0);
        this.$container.find('.stat-waiting-calls').text(data.waiting_calls || 0);
        this.$container.find('.stat-calls-today').text(data.calls_today || 0);
        
        if (data.agents) {
            const $list = this.$container.find('.agent-status-list').empty();
            data.agents.forEach(agent => {
                const statusClass = agent.status === 'available' ? 'success' : 
                                   agent.status === 'busy' ? 'warning' : 'secondary';
                $list.append('<div class="d-flex justify-content-between align-items-center mb-2">' +
                    '<span>' + agent.name + '</span>' +
                    '<span class="badge bg-' + statusClass + '">' + agent.status + '</span></div>');
            });
        }
    }
}
