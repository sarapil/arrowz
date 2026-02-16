frappe.pages['arrowz-communications'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Communications Hub'),
        single_column: true
    });
    
    wrapper.comms = new ArrowzCommunications(page);
};

class ArrowzCommunications {
    constructor(page) {
        this.page = page;
        this.make();
        this.refresh();
    }
    
    make() {
        this.$container = $('<div class="arrowz-communications">' +
            '<ul class="nav nav-tabs mb-3">' +
                '<li class="nav-item"><a class="nav-link active" data-tab="calls" href="#">Calls</a></li>' +
                '<li class="nav-item"><a class="nav-link" data-tab="sms" href="#">SMS</a></li>' +
                '<li class="nav-item"><a class="nav-link" data-tab="recordings" href="#">Recordings</a></li>' +
            '</ul>' +
            '<div class="tab-content">' +
                '<div class="tab-pane active" id="calls-tab"><div class="calls-list"></div></div>' +
                '<div class="tab-pane" id="sms-tab"><div class="sms-list"></div></div>' +
                '<div class="tab-pane" id="recordings-tab"><div class="recordings-list"></div></div>' +
            '</div>' +
        '</div>').appendTo(this.page.main);
        
        this.$container.find('.nav-link').on('click', (e) => {
            e.preventDefault();
            this.$container.find('.nav-link').removeClass('active');
            $(e.target).addClass('active');
            this.$container.find('.tab-pane').removeClass('active');
            this.$container.find('#' + $(e.target).data('tab') + '-tab').addClass('active');
        });
    }
    
    async refresh() {
        try {
            const r = await frappe.call({ method: 'arrowz.api.agent.get_recent_calls', args: { limit: 50 } });
            const $list = this.$container.find('.calls-list').empty();
            if (r.message && r.message.length) {
                r.message.forEach(c => {
                    $list.append('<div class="card mb-2"><div class="card-body p-2 d-flex justify-content-between">' +
                        '<span>' + (c.caller_id || c.callee_id || '-') + '</span>' +
                        '<span class="text-muted">' + frappe.datetime.prettyDate(c.start_time) + '</span></div></div>');
                });
            } else {
                $list.html('<p class="text-muted">No calls found</p>');
            }
        } catch (e) { console.error('Error:', e); }
    }
}
