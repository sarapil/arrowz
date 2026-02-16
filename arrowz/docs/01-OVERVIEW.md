# Arrowz Communication Platform
## Enterprise VoIP & AI-Powered Communication System for ERPNext/Frappe

---

## 📌 Executive Summary

**Arrowz** is a comprehensive enterprise communication platform that integrates VoIP telephony, AI-powered call analytics, and CRM functionality into ERPNext/Frappe. It provides a complete solution for businesses to manage voice communications, analyze customer interactions, and improve sales and support performance.

---

## 🏛️ Architecture Philosophy

> **Asterisk** هو محرك الاتصال القوي - يتم التعامل معه عبر **AMI** للسرعة و **PJSIP** للمرونة
> 
> **ERPNext** هو العقل المدبر - يدير البيانات ويعرض الواجهة الموحدة
> 
> من خلال تجاوز واجهة REST القديمة وتبني **GraphQL** للتكوين و **WebRTC** للصوت، نحصل على نظام متكامل، قابل للتوسع، ومبني على أحدث المعايير التقنية المفتوحة المصدر.

| Component | Role | Protocol |
|-----------|------|----------|
| **Asterisk/FreePBX** | محرك الاتصال (Engine) | AMI + PJSIP + WebSocket |
| **ERPNext/Frappe** | العقل المدبر (Orchestrator) | REST + Socket.IO |
| **GraphQL API** | تكوين PBX | HTTP/HTTPS |
| **WebRTC** | الصوت والفيديو | WSS + SRTP/DTLS |

---

## 🎯 Core Value Propositions

1. **Unified Communications** - Single platform for all voice communications
2. **AI-Powered Insights** - Real-time sentiment analysis and call coaching
3. **CRM Integration** - Seamless connection with ERPNext CRM modules
4. **WebRTC Softphone** - Browser-based calling without external software
5. **Real-time Presence** - Team availability and status management

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ERPNext/Frappe                           │
│                    (العقل المدبر - Orchestrator)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   WebRTC     │  │     AI       │  │     CRM      │          │
│  │  Softphone   │  │   Engine     │  │ Integration  │          │
│  │  (Navbar)    │  │   (OpenAI)   │  │ (ERPNext)    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│  ┌──────┴──────────────────┴──────────────────┴───────┐        │
│  │              Unified API Layer                      │        │
│  │   (webrtc.py, ai.py, crm.py, pbx.py, sms.py)       │        │
│  └─────────────────────┬──────────────────────────────┘        │
│                        │                                        │
│  ┌─────────────────────┴──────────────────────────────┐        │
│  │              Data Layer (DocTypes)                  │        │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │        │
│  │  │Settings │ │Extension│ │Call Log │ │Server   │  │        │
│  │  │         │ │         │ │         │ │Config   │  │        │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘  │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   FreePBX/   │  │   OpenAI    │  │   ERPNext   │
│   Asterisk   │  │   API       │  │   CRM       │
│  ─────────── │  └──────────────┘  └──────────────┘
│  GraphQL +   │
│  AMI + WSS   │
└──────────────┘
```

---

## 📊 Feature Categories

### 1. Voice Communication (VoIP)
- Browser-based WebRTC softphone
- SIP/WebSocket connectivity to PBX
- Click-to-call from any phone field
- Incoming call popup with caller info
- Call hold, transfer, conference

### 2. AI & Analytics
- Real-time sentiment analysis
- Live call transcription
- AI-powered call coaching
- Post-call summary generation
- Predictive insights

### 3. CRM Integration
- Contact/Lead auto-lookup
- Call history linking
- Opportunity tracking
- Auto-create leads from unknown callers
- Customer popup on incoming calls

### 4. Team Management
- Real-time presence (online/busy/away)
- Agent availability dashboard
- Call queue management
- Performance metrics

### 5. Quality Monitoring
- Call quality metrics (jitter, packet loss)
- Audio quality scoring
- Network diagnostics
- Alert thresholds

---

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Python/Frappe | API, Business Logic |
| Frontend | JavaScript/jQuery | UI Components |
| VoIP Client | JsSIP (WebRTC) | Browser Calling |
| PBX Integration | Asterisk/FreePBX | Telephony Backend |
| AI | OpenAI API | NLP, Sentiment |
| Database | MariaDB | Data Storage |
| Real-time | Socket.IO | Presence, Events |

---

## 📁 Application Structure

```
arrowz/
├── arrowz/
│   ├── __init__.py
│   ├── hooks.py                 # App configuration
│   ├── modules.txt              # Module list
│   │
│   ├── api/                     # Backend APIs
│   │   ├── __init__.py
│   │   ├── webrtc.py           # WebRTC/SIP config
│   │   ├── ai.py               # AI analysis
│   │   ├── crm.py              # CRM integration
│   │   ├── call_log.py         # Call logging
│   │   ├── presence.py         # User presence
│   │   └── settings.py         # Settings API
│   │
│   ├── doctype/                 # Single module doctypes
│   │   └── call_event_log/
│   │
│   ├── arrowz/                  # Main module
│   │   ├── doctype/
│   │   │   ├── arrowz_settings/     # System settings
│   │   │   ├── az_server_config/    # PBX servers
│   │   │   ├── az_extension/        # SIP extensions
│   │   │   ├── az_call_log/         # Call records
│   │   │   └── az_sentiment_log/    # Sentiment data
│   │   │
│   │   ├── workspace/
│   │   └── page/
│   │
│   ├── public/
│   │   ├── js/
│   │   │   ├── softphone.js    # Main softphone
│   │   │   ├── ai_assistant.js # AI features
│   │   │   ├── presence.js     # Presence manager
│   │   │   └── dashboard.js    # Dashboard
│   │   │
│   │   └── css/
│   │       ├── softphone.css
│   │       └── dashboard.css
│   │
│   ├── templates/
│   └── www/
│
├── pyproject.toml
└── README.md
```

---

## 🔗 External Dependencies

### Required
- **Frappe Framework** (v15+)
- **ERPNext** (optional, for full CRM)
- **FreePBX/Asterisk** (PBX server)

### Optional
- **OpenAI API** (for AI features)
- **Redis** (for presence)
- **STUN/TURN servers** (for NAT traversal)

---

## 📈 Success Metrics

| Metric | Description |
|--------|-------------|
| Call Completion Rate | % of calls successfully connected |
| Average Handle Time | Average duration of calls |
| Sentiment Score | Average customer sentiment |
| Quality Score | Audio/video quality rating |
| Agent Availability | % time agents are available |

---

## 🚀 Getting Started

See the following documentation:
- `02-DATABASE-SCHEMA.md` - DocType specifications
- `03-API-REFERENCE.md` - API endpoints
- `04-FRONTEND-GUIDE.md` - JavaScript components
- `05-INTEGRATION-GUIDE.md` - PBX/AI setup
- `06-ENHANCEMENTS.md` - Improvement suggestions

---

*Arrowz Communication Platform - Built for ERPNext/Frappe*
