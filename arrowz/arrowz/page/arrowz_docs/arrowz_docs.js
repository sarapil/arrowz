// Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
// Developer Website: https://arkan.it.com
// License: MIT
// For license information, please see license.txt

/**
 * Arrowz Documentation Page
 * Complete documentation hub with all guides and references
 * Version: 16.0.0
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
                    .arrowz-docs { padding: 20px; max-width: 1400px; margin: 0 auto; }
                    .docs-hero {
                        background: linear-gradient(135deg, #5e35b1 0%, #7c4dff 100%);
                        color: white;
                        padding: 50px;
                        border-radius: 16px;
                        margin-bottom: 40px;
                        text-align: center;
                        position: relative;
                        overflow: hidden;
                    }
                    .docs-hero::before {
                        content: '';
                        position: absolute;
                        top: -50%;
                        right: -50%;
                        width: 100%;
                        height: 200%;
                        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                    }
                    .docs-hero h1 { margin: 0 0 10px 0; font-size: 2.5rem; position: relative; }
                    .docs-hero p { margin: 0; opacity: 0.9; font-size: 1.1rem; position: relative; }
                    .docs-hero .version-badge {
                        display: inline-block;
                        background: rgba(255,255,255,0.2);
                        padding: 4px 12px;
                        border-radius: 20px;
                        font-size: 14px;
                        margin-top: 15px;
                    }
                    .docs-section { margin-bottom: 40px; }
                    .section-header {
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        margin-bottom: 20px;
                        padding-bottom: 12px;
                        border-bottom: 2px solid var(--border-color);
                    }
                    .section-header h3 { margin: 0; font-size: 1.3rem; }
                    .section-icon {
                        width: 36px;
                        height: 36px;
                        border-radius: 8px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 18px;
                    }
                    .doc-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                        gap: 16px;
                    }
                    .doc-card {
                        background: var(--card-bg);
                        border: 1px solid var(--border-color);
                        border-radius: 12px;
                        padding: 20px;
                        transition: all 0.3s ease;
                        cursor: pointer;
                        text-decoration: none;
                        display: block;
                    }
                    .doc-card:hover {
                        border-color: #5e35b1;
                        box-shadow: 0 8px 24px rgba(94, 53, 177, 0.15);
                        transform: translateY(-2px);
                    }
                    .doc-card .card-icon {
                        width: 48px;
                        height: 48px;
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 24px;
                        margin-bottom: 12px;
                    }
                    .doc-card h5 { margin: 0 0 8px 0; color: var(--text-color); font-size: 1rem; }
                    .doc-card p { margin: 0; color: var(--text-muted); font-size: 13px; line-height: 1.5; }
                    .doc-card .card-badge {
                        display: inline-block;
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 11px;
                        text-transform: uppercase;
                        font-weight: 600;
                        margin-top: 10px;
                    }
                    .badge-new { background: #e8f5e9; color: #2e7d32; }
                    .badge-v16 { background: #e3f2fd; color: #1565c0; }
                    .badge-ar { background: #fff3e0; color: #e65100; }
                    .badge-en { background: #f3e5f5; color: #7b1fa2; }

                    /* Icon backgrounds */
                    .bg-blue { background: #e3f2fd; }
                    .bg-green { background: #e8f5e9; }
                    .bg-purple { background: #f3e5f5; }
                    .bg-orange { background: #fff3e0; }
                    .bg-red { background: #ffebee; }
                    .bg-cyan { background: #e0f7fa; }
                    .bg-yellow { background: #fffde7; }
                    .bg-gray { background: #f5f5f5; }
                    .bg-whatsapp { background: #dcf8c6; }
                    .bg-telegram { background: #e3f2fd; }

                    /* Quick stats */
                    .stats-row {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                        gap: 16px;
                        margin-bottom: 40px;
                    }
                    .stat-card {
                        background: var(--card-bg);
                        border: 1px solid var(--border-color);
                        border-radius: 12px;
                        padding: 20px;
                        text-align: center;
                    }
                    .stat-card .stat-icon { font-size: 28px; margin-bottom: 8px; }
                    .stat-card .stat-value { font-size: 28px; font-weight: 700; color: var(--text-color); }
                    .stat-card .stat-label { color: var(--text-muted); font-size: 13px; margin-top: 4px; }

                    /* API table */
                    .api-table { width: 100%; border-collapse: collapse; }
                    .api-table th { background: var(--bg-color); text-align: left; padding: 12px; font-weight: 600; }
                    .api-table td { padding: 12px; border-bottom: 1px solid var(--border-color); }
                    .api-table code { background: var(--bg-color); padding: 2px 6px; border-radius: 4px; font-size: 13px; }
                    .method-badge {
                        display: inline-block;
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: 600;
                    }
                    .method-get { background: #e3f2fd; color: #1565c0; }
                    .method-post { background: #e8f5e9; color: #2e7d32; }

                    /* Mobile */
                    @media (max-width: 768px) {
                        .docs-hero { padding: 30px 20px; }
                        .docs-hero h1 { font-size: 1.8rem; }
                        .doc-grid { grid-template-columns: 1fr; }
                    }
                </style>

                <!-- Hero Section -->
                <div class="docs-hero">
                    <h1>📚 Arrowz Documentation Hub</h1>
                    <p>Complete guides, references, and resources for developers & administrators</p>
                    <div class="version-badge">✨ Version 16.0.0 - Frappe v16 Compatible</div>
                </div>

                <!-- Quick Stats -->
                <div class="stats-row">
                    <div class="stat-card">
                        <div class="stat-icon">📄</div>
                        <div class="stat-value" id="doc-count">20</div>
                        <div class="stat-label">Documentation Files</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">📋</div>
                        <div class="stat-value" id="doctype-count">20+</div>
                        <div class="stat-label">DocTypes</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">🔌</div>
                        <div class="stat-value" id="api-count">50+</div>
                        <div class="stat-label">API Endpoints</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">🌐</div>
                        <div class="stat-value">2</div>
                        <div class="stat-label">Languages (EN/AR)</div>
                    </div>
                </div>

                <!-- Getting Started -->
                <div class="docs-section">
                    <div class="section-header">
                        <div class="section-icon bg-green">🚀</div>
                        <h3>Getting Started</h3>
                    </div>
                    <div class="doc-grid">
                        <a href="/assets/arrowz/docs/INDEX.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-purple">📑</div>
                            <h5>Documentation Index</h5>
                            <p>Complete index of all documentation files and quick navigation</p>
                        </a>
                        <a href="/assets/arrowz/docs/FEATURES_EN.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-blue">✨</div>
                            <h5>Features Guide (English)</h5>
                            <p>Complete 20-section guide covering all features with screenshots</p>
                            <span class="card-badge badge-en">English</span>
                        </a>
                        <a href="/assets/arrowz/docs/FEATURES_AR.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-orange">✨</div>
                            <h5>Features Guide (Arabic)</h5>
                            <p>Comprehensive 20-section guide covering all app features</p>
                            <span class="card-badge badge-ar">Arabic</span>
                        </a>
                        <a href="/assets/arrowz/docs/ROADMAP.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-cyan">🗺️</div>
                            <h5>Roadmap & Future Plans</h5>
                            <p>Upcoming features, proposals, and development timeline</p>
                        </a>
                    </div>
                </div>

                <!-- Developer Documentation -->
                <div class="docs-section">
                    <div class="section-header">
                        <div class="section-icon bg-blue">👨‍💻</div>
                        <h3>Developer Documentation</h3>
                    </div>
                    <div class="doc-grid">
                        <a href="/assets/arrowz/docs/DEVELOPER_GUIDE.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-blue">📖</div>
                            <h5>Developer Guide</h5>
                            <p>Complete guide for development: setup, patterns, testing, and best practices</p>
                            <span class="card-badge badge-v16">v16 Ready</span>
                        </a>
                        <a href="/assets/arrowz/docs/MIGRATION_V16.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-purple">⬆️</div>
                            <h5>v16 Migration Guide</h5>
                            <p>Complete guide for migrating to Frappe v16 with breaking changes</p>
                            <span class="card-badge badge-new">New</span>
                        </a>
                        <a href="/assets/arrowz/docs/API_REFERENCE.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-green">🔌</div>
                            <h5>API Reference</h5>
                            <p>Complete API documentation with endpoints, parameters, and examples</p>
                        </a>
                        <a href="/assets/arrowz/docs/DOCTYPES_REFERENCE.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-orange">📋</div>
                            <h5>DocTypes Reference</h5>
                            <p>All DocTypes with fields, relationships, and usage patterns</p>
                        </a>
                        <a href="/assets/arrowz/docs/AI_CONTEXT.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-purple">🤖</div>
                            <h5>AI Context Document</h5>
                            <p>Context file for AI assistants (Copilot, Claude, etc.)</p>
                        </a>
                        <a href="/assets/arrowz/docs/QUALITY_ASSURANCE.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-cyan">🧪</div>
                            <h5>Quality Assurance Guide</h5>
                            <p>Testing strategies, CI/CD setup, and QA procedures</p>
                        </a>
                        <a href="/assets/arrowz/docs/DEVELOPMENT_SESSION_SUMMARY.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-yellow">📋</div>
                            <h5>Development Session Summary</h5>
                            <p>Complete development history and decisions</p>
                            <span class="card-badge badge-new">New</span>
                        </a>
                        <a href="/assets/arrowz/docs/TECHNICAL_IMPLEMENTATION.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-red">🛠️</div>
                            <h5>Technical Implementation</h5>
                            <p>Code patterns and implementation details</p>
                            <span class="card-badge badge-new">New</span>
                        </a>
                    </div>
                </div>

                <!-- Server Administration -->
                <div class="docs-section">
                    <div class="section-header">
                        <div class="section-icon bg-red">🖥️</div>
                        <h3>Server Administration</h3>
                    </div>
                    <div class="doc-grid">
                        <a href="/assets/arrowz/docs/SERVER_ADMIN.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-red">🔧</div>
                            <h5>Server Admin Guide</h5>
                            <p>Complete server administration: installation, configuration, maintenance</p>
                            <span class="card-badge badge-new">New</span>
                        </a>
                        <a href="/assets/arrowz/docs/FREEPBX_SETUP.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-blue">📞</div>
                            <h5>FreePBX Setup</h5>
                            <p>FreePBX/Asterisk integration configuration guide</p>
                        </a>
                        <a href="/assets/arrowz/docs/OPENMEETINGS_SETUP.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-green">🎥</div>
                            <h5>OpenMeetings Setup</h5>
                            <p>Video conferencing server integration guide</p>
                        </a>
                    </div>
                </div>

                <!-- Integrations -->
                <div class="docs-section">
                    <div class="section-header">
                        <div class="section-icon bg-cyan">🔗</div>
                        <h3>Integrations</h3>
                    </div>
                    <div class="doc-grid">
                        <a href="/assets/arrowz/docs/omni_channel_platform.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-whatsapp">
                                <svg viewBox="0 0 24 24" width="24" height="24" fill="#25D366">
                                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>
                                </svg>
                            </div>
                            <h5>WhatsApp Integration</h5>
                            <p>WhatsApp Cloud API integration for omni-channel messaging</p>
                        </a>
                        <a href="/assets/arrowz/docs/omni_channel_platform.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-telegram">
                                <svg viewBox="0 0 24 24" width="24" height="24" fill="#0088cc">
                                    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
                                </svg>
                            </div>
                            <h5>Telegram Integration</h5>
                            <p>Telegram Bot API integration for messaging</p>
                        </a>
                        <a href="/assets/arrowz/docs/omni_channel_platform_ar.md" target="_blank" class="doc-card">
                            <div class="card-icon bg-orange">💬</div>
                            <h5>Omni-Channel Platform (Arabic)</h5>
                            <p>Comprehensive guide for WhatsApp and Telegram channel setup</p>
                            <span class="card-badge badge-ar">Arabic</span>
                        </a>
                    </div>
                </div>

                <!-- Application Pages -->
                <div class="docs-section">
                    <div class="section-header">
                        <div class="section-icon bg-purple">📱</div>
                        <h3>Application Pages</h3>
                    </div>
                    <div class="doc-grid" id="pages-grid"></div>
                </div>

                <!-- DocTypes Reference -->
                <div class="docs-section">
                    <div class="section-header">
                        <div class="section-icon bg-gray">📋</div>
                        <h3>DocTypes Reference</h3>
                    </div>
                    <div class="table-responsive">
                        <table class="api-table">
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
                    <div class="section-header">
                        <div class="section-icon bg-green">🔌</div>
                        <h3>Key API Endpoints</h3>
                    </div>
                    <div class="table-responsive">
                        <table class="api-table">
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
                                    <td><span class="method-badge method-get">GET</span></td>
                                    <td>Get WebRTC configuration for softphone</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.webrtc.initiate_call</code></td>
                                    <td><span class="method-badge method-post">POST</span></td>
                                    <td>Initiate an outbound call</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.omni.send_whatsapp_message</code></td>
                                    <td><span class="method-badge method-post">POST</span></td>
                                    <td>Send WhatsApp message via Cloud API</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.omni.send_telegram_message</code></td>
                                    <td><span class="method-badge method-post">POST</span></td>
                                    <td>Send Telegram message via Bot API</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.sms.send_sms</code></td>
                                    <td><span class="method-badge method-post">POST</span></td>
                                    <td>Send SMS message</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.wallboard.get_wallboard_data</code></td>
                                    <td><span class="method-badge method-get">GET</span></td>
                                    <td>Get real-time wallboard metrics</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.agent.get_agent_stats</code></td>
                                    <td><span class="method-badge method-get">GET</span></td>
                                    <td>Get agent performance statistics</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.recording.get_recording_url</code></td>
                                    <td><span class="method-badge method-get">GET</span></td>
                                    <td>Get call recording URL</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.screenpop.get_caller_info</code></td>
                                    <td><span class="method-badge method-get">GET</span></td>
                                    <td>Get caller information for screen pop</td>
                                </tr>
                                <tr>
                                    <td><code>arrowz.api.meeting.create_room</code></td>
                                    <td><span class="method-badge method-post">POST</span></td>
                                    <td>Create OpenMeetings video room</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Context Files (AI) -->
                <div class="docs-section">
                    <div class="section-header">
                        <div class="section-icon bg-yellow">🤖</div>
                        <h3>AI & IDE Context Files</h3>
                    </div>
                    <div class="doc-grid">
                        <div class="doc-card">
                            <div class="card-icon bg-blue">🔮</div>
                            <h5>CONTEXT.md</h5>
                            <p>Technical context for AI assistants (English)</p>
                        </div>
                        <div class="doc-card">
                            <div class="card-icon bg-orange">🔮</div>
                            <h5>CONTEXT-AR.md</h5>
                            <p>Technical context for AI assistants (Arabic)</p>
                        </div>
                        <div class="doc-card">
                            <div class="card-icon bg-purple">🧠</div>
                            <h5>CLAUDE.md</h5>
                            <p>Instructions for Claude AI assistant</p>
                        </div>
                        <div class="doc-card">
                            <div class="card-icon bg-cyan">📝</div>
                            <h5>.cursorrules</h5>
                            <p>Cursor IDE rules and patterns</p>
                        </div>
                        <div class="doc-card">
                            <div class="card-icon bg-green">📝</div>
                            <h5>.aider.rules</h5>
                            <p>Aider AI coding assistant rules</p>
                        </div>
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
            { name: 'arrowz', icon: '📡', title: 'Communications Hub', desc: 'Main workspace with stats and quick actions' },
            { name: 'arrowz-agent-dashboard', icon: '🎧', title: 'Agent Dashboard', desc: 'Agent workspace for calls' },
            { name: 'arrowz-wallboard', icon: '📊', title: 'Manager Wallboard', desc: 'Real-time monitoring' },
            { name: 'arrowz-analytics', icon: '📈', title: 'Analytics', desc: 'Reports and insights' },
            { name: 'arrowz-communications', icon: '💬', title: 'Communications', desc: 'Calls, SMS, Chat' },
            { name: 'arrowz-docs', icon: '📚', title: 'Documentation', desc: 'You are here!' },
        ];

        const $grid = this.$container.find('#pages-grid').empty();

        pages.forEach(page => {
            $grid.append(`
                <a href="/desk/${page.name}" class="doc-card">
                    <div class="card-icon bg-purple">${page.icon}</div>
                    <h5>${page.title}</h5>
                    <p>${page.desc}</p>
                </a>
            `);
        });
    }

    async loadDocTypes() {
        const doctypes = [
            { name: 'AZ Call Log', icon: '📞', desc: 'Call records with details' },
            { name: 'AZ SMS Message', icon: '💬', desc: 'SMS messages' },
            { name: 'AZ Extension', icon: '👤', desc: 'PBX extensions' },
            { name: 'AZ Server Config', icon: '🖥️', desc: 'PBX servers' },
            { name: 'AZ Conversation Session', icon: '🗨️', desc: 'Omni-channel sessions' },
            { name: 'AZ Omni Provider', icon: '🔗', desc: 'Channel providers' },
            { name: 'AZ Meeting Room', icon: '🎥', desc: 'Video rooms' },
            { name: 'Arrowz Settings', icon: '⚙️', desc: 'Global settings' }
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
                    <td><strong>${dt.icon} ${dt.name}</strong></td>
                    <td>${dt.desc}</td>
                    <td><span style="background: #5e35b1; color: white; padding: 2px 10px; border-radius: 10px;">${count}</span></td>
                    <td><a href="/desk/${slug}" class="btn btn-xs btn-primary">View</a></td>
                </tr>
            `);
        }
    }
}

// Export for global access (v16 IIFE compatibility)
window.ArrowzDocs = ArrowzDocs;
