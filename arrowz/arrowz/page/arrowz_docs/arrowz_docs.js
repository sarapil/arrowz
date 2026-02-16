/**
 * Arrowz Documentation Page
 * Complete documentation and page listing
 */

frappe.pages['arrowz-docs'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Arrowz Documentation'),
        single_column: true
    });
    
    wrapper.docs = new ArrowzDocs(page);
};

class ArrowzDocs {
    constructor(page) {
        this.page = page;
        this.make();
    }
    
    make() {
        this.page.set_secondary_action(__('Refresh'), () => this.render(), 'refresh');
        
        this.$container = $(`
            <div class="arrowz-docs">
                <style>
                    .arrowz-docs { padding: 20px; }
                    .docs-hero { 
                        background: linear-gradient(135deg, #5e35b1 0%, #7c4dff 100%);
                        color: white;
                        padding: 40px;
                        border-radius: 12px;
                        margin-bottom: 30px;
                    }
                    .docs-hero h1 { margin: 0 0 10px 0; }
                    .docs-hero p { margin: 0; opacity: 0.9; }
                    .docs-section { margin-bottom: 30px; }
                    .docs-section h3 { 
                        border-bottom: 2px solid #5e35b1;
                        padding-bottom: 10px;
                        margin-bottom: 20px;
                    }
                    .page-grid { 
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                        gap: 15px;
                    }
                    .page-card {
                        background: var(--card-bg);
                        border: 1px solid var(--border-color);
                        border-radius: 8px;
                        padding: 15px;
                        transition: all 0.2s;
                    }
                    .page-card:hover {
                        border-color: #5e35b1;
                        box-shadow: 0 4px 12px rgba(94, 53, 177, 0.15);
                    }
                    .page-card .icon { font-size: 24px; margin-bottom: 10px; }
                    .page-card h5 { margin: 0 0 5px 0; }
                    .page-card p { margin: 0; color: var(--text-muted); font-size: 13px; }
                    .page-card a { text-decoration: none; color: inherit; display: block; }
                    .doctype-table { width: 100%; }
                    .doctype-table th { background: var(--bg-color); }
                    .badge-count { 
                        background: #5e35b1;
                        color: white;
                        padding: 2px 8px;
                        border-radius: 10px;
                        font-size: 12px;
                    }
                </style>
                
                <!-- Hero Section -->
                <div class="docs-hero">
                    <h1>📚 Arrowz Documentation</h1>
                    <p>Complete reference for Arrowz Communications Platform</p>
                </div>
                
                <!-- Quick Links -->
                <div class="docs-section">
                    <h3>🚀 Quick Links</h3>
                    <div class="page-grid">
                        <div class="page-card">
                            <a href="/app/arrowz">
                                <div class="icon">📡</div>
                                <h5>Dashboard</h5>
                                <p>Main communications hub with stats and quick actions</p>
                            </a>
                        </div>
                        <div class="page-card">
                            <a href="/app/arrowz-agent-dashboard">
                                <div class="icon">🎧</div>
                                <h5>Agent Dashboard</h5>
                                <p>Agent workspace for handling calls and tracking performance</p>
                            </a>
                        </div>
                        <div class="page-card">
                            <a href="/app/arrowz-wallboard">
                                <div class="icon">📊</div>
                                <h5>Manager Wallboard</h5>
                                <p>Real-time call center monitoring and metrics</p>
                            </a>
                        </div>
                        <div class="page-card">
                            <a href="/app/arrowz-analytics">
                                <div class="icon">📈</div>
                                <h5>Analytics</h5>
                                <p>Advanced reporting and call analytics</p>
                            </a>
                        </div>
                    </div>
                </div>
                
                <!-- All Pages -->
                <div class="docs-section">
                    <h3>📄 All Application Pages</h3>
                    <div class="page-grid" id="pages-grid"></div>
                </div>
                
                <!-- DocTypes -->
                <div class="docs-section">
                    <h3>📋 DocTypes Reference</h3>
                    <div class="table-responsive">
                        <table class="table doctype-table">
                            <thead>
                                <tr>
                                    <th>DocType</th>
                                    <th>Description</th>
                                    <th>Records</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody id="doctypes-table"></tbody>
                        </table>
                    </div>
                </div>
                
                <!-- API Reference -->
                <div class="docs-section">
                    <h3>🔌 API Endpoints</h3>
                    <div class="table-responsive">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Endpoint</th>
                                    <th>Method</th>
                                    <th>Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><code>arrowz.api.webrtc.get_webrtc_config</code></td>
                                    <td>GET</td>
                                    <td>Get WebRTC configuration for softphone</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.webrtc.initiate_call</code></td>
                                    <td>POST</td>
                                    <td>Initiate an outbound call</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.call_log.get_call_history</code></td>
                                    <td>GET</td>
                                    <td>Get call history with filters</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.call_log.get_call_statistics</code></td>
                                    <td>GET</td>
                                    <td>Get call statistics for dashboard</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.wallboard.get_wallboard_data</code></td>
                                    <td>GET</td>
                                    <td>Get real-time wallboard data</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.agent.get_agent_stats</code></td>
                                    <td>GET</td>
                                    <td>Get agent performance statistics</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.sms.send_sms</code></td>
                                    <td>POST</td>
                                    <td>Send SMS message</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.recording.get_recording_url</code></td>
                                    <td>GET</td>
                                    <td>Get call recording URL</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.screenpop.get_caller_info</code></td>
                                    <td>GET</td>
                                    <td>Get caller information for screen pop</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `).appendTo(this.page.main);
        
        this.render();
    }
    
    async render() {
        await Promise.all([
            this.loadPages(),
            this.loadDocTypes()
        ]);
    }
    
    loadPages() {
        const pages = [
            { name: 'arrowz', icon: '📡', title: 'Communications Hub', desc: 'Main dashboard with all features' },
            { name: 'arrowz-dashboard', icon: '🏠', title: 'Overview Dashboard', desc: 'Quick overview of call center' },
            { name: 'arrowz-agent-dashboard', icon: '🎧', title: 'Agent Dashboard', desc: 'Agent workspace for calls' },
            { name: 'arrowz-wallboard', icon: '📊', title: 'Manager Wallboard', desc: 'Real-time monitoring' },
            { name: 'arrowz-analytics', icon: '📈', title: 'Analytics', desc: 'Reports and insights' },
            { name: 'arrowz-communications', icon: '💬', title: 'Communications', desc: 'Calls, SMS, Recordings' },
            { name: 'arrowz-docs', icon: '📚', title: 'Documentation', desc: 'This page - full reference' },
            { name: 'az-call-log', icon: '📞', title: 'Call Logs List', desc: 'All call records', doctype: true },
            { name: 'az-sms-message', icon: '💬', title: 'SMS Messages', desc: 'All SMS records', doctype: true },
            { name: 'az-extension', icon: '👤', title: 'Extensions', desc: 'PBX extensions', doctype: true },
            { name: 'az-server-config', icon: '🖥️', title: 'PBX Servers', desc: 'Server configurations', doctype: true },
            { name: 'az-trunk', icon: '🔗', title: 'Trunks', desc: 'SIP trunks', doctype: true },
            { name: 'az-inbound-route', icon: '📥', title: 'Inbound Routes', desc: 'Incoming call routing', doctype: true },
            { name: 'az-outbound-route', icon: '📤', title: 'Outbound Routes', desc: 'Outgoing call routing', doctype: true },
            { name: 'arrowz-settings', icon: '⚙️', title: 'Settings', desc: 'App configuration', doctype: true }
        ];
        
        const $grid = this.$container.find('#pages-grid').empty();
        
        pages.forEach(page => {
            const href = page.doctype ? `/app/${page.name}` : `/app/${page.name}`;
            $grid.append(`
                <div class="page-card">
                    <a href="${href}">
                        <div class="icon">${page.icon}</div>
                        <h5>${page.title}</h5>
                        <p>${page.desc}</p>
                    </a>
                </div>
            `);
        });
    }
    
    async loadDocTypes() {
        const doctypes = [
            { name: 'AZ Call Log', desc: 'Call records with details, duration, recordings' },
            { name: 'AZ Call Transfer Log', desc: 'Call transfer history' },
            { name: 'AZ SMS Message', desc: 'SMS messages sent and received' },
            { name: 'AZ SMS Provider', desc: 'SMS gateway configurations' },
            { name: 'AZ Extension', desc: 'PBX extensions linked to users' },
            { name: 'AZ Server Config', desc: 'FreePBX/Asterisk server settings' },
            { name: 'AZ Trunk', desc: 'SIP trunk configurations' },
            { name: 'AZ Inbound Route', desc: 'Inbound call routing rules' },
            { name: 'AZ Outbound Route', desc: 'Outbound call routing rules' },
            { name: 'Arrowz Settings', desc: 'Global application settings' }
        ];
        
        const $tbody = this.$container.find('#doctypes-table').empty();
        
        for (const dt of doctypes) {
            let count = 0;
            try {
                const r = await frappe.call({
                    method: 'frappe.client.get_count',
                    args: { doctype: dt.name }
                });
                count = r.message || 0;
            } catch (e) {
                count = '-';
            }
            
            const slug = dt.name.toLowerCase().replace(/ /g, '-');
            $tbody.append(`
                <tr>
                    <td><strong>${dt.name}</strong></td>
                    <td>${dt.desc}</td>
                    <td><span class="badge-count">${count}</span></td>
                    <td><a href="/app/${slug}" class="btn btn-xs btn-default">View</a></td>
                </tr>
            `);
        }
    }
}
