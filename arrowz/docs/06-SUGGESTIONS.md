# Arrowz Suggestions & Future Enhancements
## المقترحات المستقبلية (الميزات المنفذة في 07-TECHNICAL-SPECS.md)

---

## 🎯 Status Summary

| Feature | Status | Document |
|---------|--------|----------|
| ~~Call Transfer~~ | ✅ منقول للتنفيذ | `07-TECHNICAL-SPECS.md` |
| ~~Recording Playback~~ | ✅ منقول للتنفيذ | `07-TECHNICAL-SPECS.md` |
| ~~Softphone UI (Navbar)~~ | ✅ منقول للتنفيذ | `07-TECHNICAL-SPECS.md` |
| ~~Click-to-Dial & Screen Pop~~ | ✅ منقول للتنفيذ | `07-TECHNICAL-SPECS.md` |
| ~~FreePBX GraphQL~~ | ✅ منقول للتنفيذ | `07-TECHNICAL-SPECS.md` |
| ~~SMS Integration~~ | ✅ منقول للتنفيذ | `07-TECHNICAL-SPECS.md` |
| ~~Audio Controls~~ | ✅ منقول للتنفيذ | `07-TECHNICAL-SPECS.md` |
| ~~Video Calls~~ | ✅ منقول للتنفيذ | `07-TECHNICAL-SPECS.md` |
| ~~Advanced Dashboards~~ | ✅ منقول للتنفيذ | `07-TECHNICAL-SPECS.md` |
| Queue Support | 📋 مقترح مستقبلي | هذا الملف |
| AI Features | 📋 مقترح مستقبلي | هذا الملف |
| Mobile App | 📋 مقترح مستقبلي | هذا الملف |

---

## 1️⃣ Call Queue & ACD Integration 📋 مقترح مستقبلي

### Current Limitation
The current system handles direct calls but doesn't integrate with call center queues (ACD - Automatic Call Distribution).

### Proposed Enhancement

#### Queue Status Dashboard
```javascript
// Show real-time queue status
class ArrowzQueuePanel {
    constructor() {
        this.queues = [];
        this.agents = [];
    }
    
    displayQueueStatus() {
        // Queue metrics: waiting calls, avg wait time, agents available
        return `
            <div class="queue-panel">
                <div class="queue-card">
                    <h4>Sales Queue</h4>
                    <div class="metric">Waiting: <strong>3</strong></div>
                    <div class="metric">Avg Wait: <strong>2:30</strong></div>
                    <div class="metric">Agents: <strong>5/8</strong></div>
                </div>
            </div>
        `;
    }
}
```

#### Agent State Control
```python
# API for queue agent states
@frappe.whitelist()
def set_agent_state(state):
    """
    Set agent queue state
    States: available, busy, wrap_up, break, lunch, offline
    """
    # AMI command to FreePBX queue
    pass
```

### Decision Points for Discussion
1. **Should queue management be a separate app or integrated into Arrowz?**
   - Option A: Integrated (simpler, one app)
   - Option B: Separate app (cleaner separation, reusable)

2. **Agent state source of truth**
   - Option A: Frappe as primary (sync to PBX)
   - Option B: PBX as primary (read from AMI)

---

## ~~2️⃣ Enhanced Call Transfer~~ ✅ منقول للتنفيذ

> **تم نقل هذا القسم إلى `07-TECHNICAL-SPECS.md`**
> 
> القرار: Attended Transfer كافتراضي، Blind Transfer للـ Supervisors فقط

---

## ~~3️⃣ Call Recording Management~~ ✅ منقول للتنفيذ

> **تم نقل هذا القسم إلى `07-TECHNICAL-SPECS.md`**
> 
> القرار: Docker Shared Volume بين FreePBX و ERPNext

---

## ~~4️⃣ SMS/WhatsApp Integration~~ ✅ منقول للتنفيذ

> **تم نقل هذا القسم إلى `07-TECHNICAL-SPECS.md`**
> 
> القرار: Provider-agnostic architecture (حرية اختيار المزود)

---

## ~~5️⃣ Video Call Support~~ ✅ منقول للتنفيذ

> **تم نقل هذا القسم إلى `07-TECHNICAL-SPECS.md`**
> 
> القرار: عبر PBX (PJSIP + WebRTC)

---

## 6️⃣ Enhanced AI Features 📋 مقترح مستقبلي

### Proposed Enhancements

#### Real-time Script Assistance
```python
@frappe.whitelist()
def get_script_suggestion(context):
    """
    Suggest responses based on:
    - Current conversation
    - Customer history
    - Product knowledge base
    - Best practice scripts
    """
    prompt = f"""
    Customer said: {context['last_statement']}
    Customer type: {context['customer_type']}
    Previous issues: {context['history']}
    
    Suggest a professional response focusing on:
    1. Acknowledge their concern
    2. Provide solution
    3. Confirm satisfaction
    """
    
    return openai_completion(prompt)
```

#### Automated Call Summary
```python
@frappe.whitelist()
def generate_call_summary(call_id):
    """Auto-generate call summary for CRM notes"""
    transcript = get_full_transcript(call_id)
    
    prompt = """
    Summarize this call in 3-5 bullet points:
    - Key issues discussed
    - Actions agreed
    - Follow-up required
    - Customer sentiment
    """
    
    summary = openai_completion(prompt, transcript)
    
    # Auto-add to linked opportunity/lead
    update_linked_record_notes(call_id, summary)
```

#### Predictive Insights
```javascript
// Show before answering
class ArrowzPreCallInsights {
    async getInsights(callerNumber) {
        const response = await frappe.call({
            method: 'arrowz.api.ai.get_caller_insights',
            args: { phone: callerNumber }
        });
        
        // Display: 
        // - Last call summary
        // - Open issues
        // - Recommended approach
        // - Sentiment trend
    }
}
```

---

## 7️⃣ Mobile App

### Options

#### Option A: PWA (Progressive Web App)
```javascript
// service-worker.js
self.addEventListener('push', (event) => {
    // Handle incoming call push notification
    self.registration.showNotification('Incoming Call', {
        body: event.data.text(),
        icon: '/assets/arrowz/images/icon.png',
        actions: [
            { action: 'answer', title: 'Answer' },
            { action: 'decline', title: 'Decline' }
        ]
    });
});
```

**Pros**: Single codebase, easy updates
**Cons**: Limited background capabilities

#### Option B: Native App (Flutter/React Native)
**Pros**: Better push notifications, background audio
**Cons**: Separate codebase, app store approval

### Recommendation
Start with PWA, consider native for advanced features later.

---

## ~~8️⃣ Dashboard & Analytics~~ ✅ منقول للتنفيذ

> **تم نقل هذا القسم إلى `07-TECHNICAL-SPECS.md`**
>
> يتضمن:
> - Real-time Wallboard
> - Historical Analytics Dashboard
> - Agent Leaderboard
> - Hourly Heatmap (ECharts)
> - Scheduled Reports

---

## ~~9️⃣ Advanced Dashboards~~ ✅ منقول للتنفيذ

### Real-time Wallboard

لوحة عرض كبيرة للـ Call Center تعرض الإحصائيات الفورية:

```javascript
// arrowz/public/js/wallboard.js
class ArrowzWallboard {
    constructor(container) {
        this.container = container;
        this.refreshInterval = 5000; // 5 seconds
        this.widgets = [];
    }
    
    async init() {
        this.setupFullscreen();
        this.createLayout();
        this.startRealTimeUpdates();
    }
    
    createLayout() {
        this.container.innerHTML = `
            <div class="wallboard-grid">
                <!-- Row 1: Key Metrics -->
                <div class="wb-widget wb-large" id="active-calls">
                    <div class="wb-value">0</div>
                    <div class="wb-label">Active Calls</div>
                </div>
                <div class="wb-widget wb-large" id="waiting-queue">
                    <div class="wb-value">0</div>
                    <div class="wb-label">Waiting in Queue</div>
                </div>
                <div class="wb-widget wb-large" id="agents-available">
                    <div class="wb-value">0/0</div>
                    <div class="wb-label">Agents Available</div>
                </div>
                
                <!-- Row 2: SLA & Performance -->
                <div class="wb-widget wb-gauge" id="sla-gauge">
                    <canvas id="sla-chart"></canvas>
                    <div class="wb-label">SLA Compliance</div>
                </div>
                <div class="wb-widget wb-chart" id="hourly-chart">
                    <canvas id="volume-chart"></canvas>
                </div>
                
                <!-- Row 3: Agent Status Grid -->
                <div class="wb-widget wb-full" id="agent-grid">
                    <div class="agent-cards"></div>
                </div>
            </div>
        `;
    }
    
    startRealTimeUpdates() {
        // Initial load
        this.fetchAndUpdate();
        
        // Socket.IO for real-time
        frappe.realtime.on('wallboard_update', (data) => {
            this.updateWidgets(data);
        });
        
        // Fallback polling
        setInterval(() => this.fetchAndUpdate(), this.refreshInterval);
    }
    
    async fetchAndUpdate() {
        const data = await frappe.call({
            method: 'arrowz.api.dashboard.get_wallboard_data'
        });
        this.updateWidgets(data.message);
    }
    
    updateWidgets(data) {
        // Active Calls with animation
        this.animateValue('#active-calls .wb-value', data.active_calls);
        
        // Queue with color coding
        const queueEl = document.querySelector('#waiting-queue');
        queueEl.querySelector('.wb-value').textContent = data.queue_depth;
        queueEl.classList.toggle('wb-warning', data.queue_depth > 5);
        queueEl.classList.toggle('wb-danger', data.queue_depth > 10);
        
        // Agents
        document.querySelector('#agents-available .wb-value').textContent = 
            `${data.agents_available}/${data.agents_total}`;
        
        // SLA Gauge
        this.updateSLAGauge(data.sla_percentage);
        
        // Agent Grid
        this.updateAgentGrid(data.agents);
    }
    
    updateAgentGrid(agents) {
        const grid = document.querySelector('#agent-grid .agent-cards');
        grid.innerHTML = agents.map(agent => `
            <div class="agent-card status-${agent.status}">
                <img src="${agent.avatar}" class="agent-avatar">
                <div class="agent-name">${agent.name}</div>
                <div class="agent-status">${agent.status}</div>
                <div class="agent-duration">${agent.current_duration || ''}</div>
            </div>
        `).join('');
    }
}
```

### Backend API for Wallboard
```python
# arrowz/api/dashboard.py

@frappe.whitelist()
def get_wallboard_data():
    """Get all wallboard metrics in single call"""
    return {
        'active_calls': get_active_call_count(),
        'queue_depth': get_queue_depth(),
        'agents_available': count_available_agents(),
        'agents_total': count_total_agents(),
        'sla_percentage': calculate_sla_percentage(),
        'avg_wait_time': get_avg_wait_time(),
        'avg_handle_time': get_avg_handle_time(),
        'calls_today': get_today_call_count(),
        'hourly_data': get_hourly_breakdown(),
        'agents': get_agent_status_list()
    }

def get_agent_status_list():
    """Get all agents with their current status"""
    agents = frappe.get_all('AZ Extension',
        filters={'is_active': 1},
        fields=['user', 'extension', 'status', 'current_call']
    )
    
    result = []
    for agent in agents:
        user = frappe.get_doc('User', agent.user)
        result.append({
            'extension': agent.extension,
            'name': user.full_name,
            'avatar': user.user_image or '/assets/frappe/images/default-avatar.png',
            'status': agent.status,  # available, on_call, wrap_up, break, offline
            'current_duration': get_current_call_duration(agent.current_call)
        })
    
    return result
```

### Historical Analytics Dashboard

```python
# arrowz/arrowz/page/call_analytics/call_analytics.py

@frappe.whitelist()
def get_analytics_data(filters):
    """
    Comprehensive analytics for call center performance
    
    Args:
        filters: {
            'from_date': '2026-01-01',
            'to_date': '2026-01-13',
            'agent': None,  # or specific user
            'queue': None   # or specific queue
        }
    """
    return {
        # Volume Metrics
        'total_calls': get_total_calls(filters),
        'inbound_calls': get_inbound_calls(filters),
        'outbound_calls': get_outbound_calls(filters),
        'missed_calls': get_missed_calls(filters),
        
        # Time Metrics
        'avg_talk_time': get_avg_talk_time(filters),
        'avg_wait_time': get_avg_wait_time(filters),
        'avg_handle_time': get_avg_handle_time(filters),
        
        # Quality Metrics
        'sla_percentage': calculate_sla_for_period(filters),
        'first_call_resolution': get_fcr_rate(filters),
        'avg_sentiment': get_avg_sentiment_score(filters),
        
        # Charts Data
        'daily_volume': get_daily_volume_chart(filters),
        'hourly_heatmap': get_hourly_heatmap(filters),
        'agent_performance': get_agent_leaderboard(filters),
        'disposition_breakdown': get_disposition_pie(filters),
        'sentiment_trend': get_sentiment_trend(filters)
    }

def get_hourly_heatmap(filters):
    """
    Returns data for day-of-week vs hour-of-day heatmap
    Shows call volume patterns
    """
    data = frappe.db.sql("""
        SELECT 
            DAYOFWEEK(start_time) as day,
            HOUR(start_time) as hour,
            COUNT(*) as count
        FROM `tabAZ Call Log`
        WHERE start_time BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY DAYOFWEEK(start_time), HOUR(start_time)
    """, filters, as_dict=1)
    
    # Format for heatmap visualization
    return format_heatmap_data(data)

def get_agent_leaderboard(filters):
    """Top performing agents by various metrics"""
    return frappe.db.sql("""
        SELECT 
            user,
            COUNT(*) as total_calls,
            AVG(duration) as avg_duration,
            AVG(sentiment_score) as avg_sentiment,
            SUM(CASE WHEN disposition = 'ANSWERED' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as answer_rate
        FROM `tabAZ Call Log`
        WHERE start_time BETWEEN %(from_date)s AND %(to_date)s
        GROUP BY user
        ORDER BY total_calls DESC
        LIMIT 10
    """, filters, as_dict=1)
```

### Dashboard Page (Frappe Page)

```javascript
// arrowz/arrowz/page/call_analytics/call_analytics.js
frappe.pages['call-analytics'].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Call Analytics'),
        single_column: true
    });
    
    // Date Range Filter
    page.add_field({
        fieldtype: 'DateRange',
        fieldname: 'date_range',
        label: __('Date Range'),
        default: [frappe.datetime.add_days(frappe.datetime.get_today(), -30), 
                  frappe.datetime.get_today()],
        change: () => refreshDashboard()
    });
    
    // Agent Filter
    page.add_field({
        fieldtype: 'Link',
        fieldname: 'agent',
        label: __('Agent'),
        options: 'User',
        change: () => refreshDashboard()
    });
    
    const dashboard = new ArrowzAnalyticsDashboard(page);
    
    function refreshDashboard() {
        const filters = {
            from_date: page.fields_dict.date_range.value[0],
            to_date: page.fields_dict.date_range.value[1],
            agent: page.fields_dict.agent.value
        };
        dashboard.refresh(filters);
    }
    
    refreshDashboard();
};

class ArrowzAnalyticsDashboard {
    constructor(page) {
        this.page = page;
        this.charts = {};
    }
    
    async refresh(filters) {
        const data = await frappe.call({
            method: 'arrowz.arrowz.page.call_analytics.call_analytics.get_analytics_data',
            args: { filters }
        });
        
        this.renderKPICards(data.message);
        this.renderCharts(data.message);
    }
    
    renderKPICards(data) {
        const kpiSection = this.page.main.find('.kpi-section');
        kpiSection.html(`
            <div class="kpi-grid">
                <div class="kpi-card">
                    <div class="kpi-value">${data.total_calls}</div>
                    <div class="kpi-label">${__('Total Calls')}</div>
                    <div class="kpi-trend ${data.calls_trend > 0 ? 'up' : 'down'}">
                        ${data.calls_trend}%
                    </div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${this.formatDuration(data.avg_talk_time)}</div>
                    <div class="kpi-label">${__('Avg Talk Time')}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${data.sla_percentage}%</div>
                    <div class="kpi-label">${__('SLA Compliance')}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-value">${(data.avg_sentiment * 100).toFixed(0)}%</div>
                    <div class="kpi-label">${__('Positive Sentiment')}</div>
                </div>
            </div>
        `);
    }
    
    renderCharts(data) {
        // Daily Volume Chart
        this.charts.volume = new frappe.Chart('.volume-chart', {
            type: 'line',
            data: {
                labels: data.daily_volume.map(d => d.date),
                datasets: [
                    { name: 'Inbound', values: data.daily_volume.map(d => d.inbound) },
                    { name: 'Outbound', values: data.daily_volume.map(d => d.outbound) }
                ]
            },
            colors: ['#2490ef', '#98d85b']
        });
        
        // Disposition Pie
        this.charts.disposition = new frappe.Chart('.disposition-chart', {
            type: 'pie',
            data: {
                labels: data.disposition_breakdown.map(d => d.disposition),
                datasets: [{ values: data.disposition_breakdown.map(d => d.count) }]
            }
        });
        
        // Hourly Heatmap
        this.renderHeatmap(data.hourly_heatmap);
    }
    
    renderHeatmap(data) {
        // Use Apache ECharts for heatmap
        const chart = echarts.init(document.querySelector('.heatmap-chart'));
        chart.setOption({
            tooltip: { position: 'top' },
            xAxis: {
                type: 'category',
                data: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            },
            yAxis: {
                type: 'category',
                data: Array.from({length: 24}, (_, i) => `${i}:00`)
            },
            visualMap: {
                min: 0,
                max: Math.max(...data.map(d => d.count)),
                calculable: true,
                orient: 'horizontal',
                left: 'center',
                bottom: '0%'
            },
            series: [{
                type: 'heatmap',
                data: data.map(d => [d.day, d.hour, d.count]),
                emphasis: {
                    itemStyle: { shadowBlur: 10 }
                }
            }]
        });
    }
}
```

### Scheduled Reports

```python
# arrowz/tasks.py

def daily_report():
    """Send daily call center report"""
    yesterday = add_days(today(), -1)
    
    data = get_analytics_data({
        'from_date': yesterday,
        'to_date': yesterday
    })
    
    # Generate report
    report_html = frappe.render_template(
        'arrowz/templates/daily_report.html',
        {'data': data, 'date': yesterday}
    )
    
    # Send to managers
    managers = frappe.get_all('User',
        filters={'role': 'Arrowz Manager'},
        pluck='email'
    )
    
    frappe.sendmail(
        recipients=managers,
        subject=f'Call Center Daily Report - {yesterday}',
        message=report_html
    )

def weekly_report():
    """Send weekly summary with trends"""
    # Similar to daily but with week comparison
    pass
```

### Decision Points for Discussion

1. **Visualization Library**
   - Frappe Charts (simple, built-in)
   - Chart.js (more options)
   - Apache ECharts (advanced, heatmaps)
   - D3.js (maximum flexibility)

2. **Real-time Updates**
   - Socket.IO push (lower latency)
   - Polling (simpler, fallback)
   - Hybrid approach

3. **Data Retention**
   - How long to keep detailed call logs?
   - Aggregate vs detailed reporting

---

## 🤔 Questions Resolved

> **تم اتخاذ القرارات التالية - راجع `07-TECHNICAL-SPECS.md` للتفاصيل**

| Question | Decision |
|----------|----------|
| Architecture | تطبيق واحد متكامل (Arrowz) |
| PBX Flexibility | FreePBX 17 عبر GraphQL + AMI |
| Softphone UI | Navbar + Multi-tab popup |
| Call Transfer | Attended default, Blind للـ Supervisors |
| Recording Storage | Docker shared volume |
| SMS Provider | Provider-agnostic architecture |
| Video Calls | عبر PBX (PJSIP) |
| Audio | Native browser + optional RNNoise |

---

## 📋 Remaining Questions (للمستقبل)

1. **Queue Support**
   - تكامل مع FreePBX Queues؟
   - Agent state management؟

2. **AI Features**
   - مستوى الاعتماد على AI؟
   - تكلفة OpenAI للاستخدام المكثف؟

3. **Mobile App**
   - PWA أم Native؟
   - Push notifications للمكالمات الواردة؟

---

## 📋 Implementation Status

### ✅ منقول للتنفيذ (07-TECHNICAL-SPECS.md)
- [x] Softphone UI (Navbar Multi-tab)
- [x] Call Transfer (Attended/Blind)
- [x] Recording Playback
- [x] Click-to-Dial & Screen Pop
- [x] FreePBX Integration (GraphQL + AMI)
- [x] SMS Integration (Provider-agnostic)
- [x] Audio Controls & Noise Cancellation
- [x] Video Calls (via PBX)
- [x] Advanced Dashboards (Wallboard, Analytics, Heatmaps)

### 📋 مقترحات مستقبلية
- [ ] Queue Support
- [ ] Enhanced AI Features
- [ ] Mobile PWA/App

---

*هذه الوثيقة الآن تحتوي فقط على المقترحات المستقبلية - راجع `07-TECHNICAL-SPECS.md` للمواصفات التنفيذية*
