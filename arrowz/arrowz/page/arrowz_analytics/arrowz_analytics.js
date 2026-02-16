frappe.pages['arrowz-analytics'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Call Analytics'),
        single_column: true
    });
    
    wrapper.analytics = new ArrowzAnalytics(page);
};

class ArrowzAnalytics {
    constructor(page) {
        this.page = page;
        this.make();
        this.refresh();
    }
    
    make() {
        this.page.set_secondary_action(__('Refresh'), () => this.refresh());
        
        this.$container = $('<div class="arrowz-analytics">' +
            '<div class="row mb-3">' +
                '<div class="col-md-3"><label>Date Range</label><select class="form-control date-range">' +
                    '<option value="today">Today</option><option value="week">This Week</option>' +
                    '<option value="month" selected>This Month</option><option value="year">This Year</option></select></div>' +
            '</div>' +
            '<div class="row mb-3">' +
                '<div class="col-md-3"><div class="card"><div class="card-body text-center">' +
                    '<h3 class="total-calls">0</h3><p class="mb-0">Total Calls</p></div></div></div>' +
                '<div class="col-md-3"><div class="card"><div class="card-body text-center">' +
                    '<h3 class="avg-duration">0:00</h3><p class="mb-0">Avg Duration</p></div></div></div>' +
                '<div class="col-md-3"><div class="card"><div class="card-body text-center">' +
                    '<h3 class="answer-rate">0%</h3><p class="mb-0">Answer Rate</p></div></div></div>' +
                '<div class="col-md-3"><div class="card"><div class="card-body text-center">' +
                    '<h3 class="avg-wait">0s</h3><p class="mb-0">Avg Wait Time</p></div></div></div>' +
            '</div>' +
            '<div class="row"><div class="col-12"><div class="card"><div class="card-header"><h6>Call Volume</h6></div>' +
                '<div class="card-body chart-container" style="height:300px"></div></div></div></div>' +
        '</div>').appendTo(this.page.main);
        
        this.$container.find('.date-range').on('change', () => this.refresh());
    }
    
    async refresh() {
        const range = this.$container.find('.date-range').val();
        try {
            const r = await frappe.call({ method: 'arrowz.api.analytics.get_analytics', args: { date_range: range } });
            if (r.message) {
                this.$container.find('.total-calls').text(r.message.total_calls || 0);
                this.$container.find('.avg-duration').text(this.format_duration(r.message.avg_duration || 0));
                this.$container.find('.answer-rate').text((r.message.answer_rate || 0) + '%');
                this.$container.find('.avg-wait').text((r.message.avg_wait_time || 0) + 's');
            }
        } catch (e) { console.error('Error loading analytics:', e); }
    }
    
    format_duration(s) { return Math.floor(s/60) + ':' + String(Math.floor(s%60)).padStart(2,'0'); }
}
