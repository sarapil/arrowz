# Arrowz - Enterprise VoIP & Omni-Channel Communications

<p align="center">
  <img src="docs/images/arrowz-logo.png" alt="Arrowz Logo" width="200">
</p>

<p align="center">
  <strong>Next-Generation Call Center & Unified Communications for Frappe/ERPNext</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#architecture">Architecture</a>
</p>

---

## 🎯 What is Arrowz?

Arrowz is an enterprise-grade unified communications platform built for Frappe Framework and ERPNext. It provides:

- **WebRTC Softphone** - Browser-based calling with no plugins required
- **Omni-Channel Messaging** - WhatsApp, Telegram integration
- **Video Conferencing** - OpenMeetings integration
- **AI-Powered Insights** - Real-time sentiment analysis and coaching
- **CRM Integration** - Automatic caller identification and history
- **PBX Integration** - FreePBX, Asterisk, and more

## ✨ Features

### 📞 Softphone (WebRTC)
- Browser-based WebRTC calling via JsSIP
- Navbar-integrated dropdown (desktop) / modal (mobile)
- Multi-extension support with quick switcher
- Contact search across all linked DocTypes
- Click-to-call from any phone field
- Call controls: mute, hold, transfer, keypad
- Real-time call timer and status indicators

### 💬 Omni-Channel Messaging
- **WhatsApp Integration** (Cloud API & On-Premise)
- **Telegram Integration** (Bot API)
- Unified conversation panel
- Real-time message notifications
- Media attachments support
- 24-hour window tracking (WhatsApp)

### 🎥 Video Conferencing (OpenMeetings)
- Create meeting rooms
- Invite participants
- Screen sharing
- Recording support
- Moderator controls

### 🧠 AI Assistant
- Real-time sentiment analysis
- Live transcription
- Coaching suggestions
- Post-call summaries

### 📊 Analytics & Dashboards
- Real-time Wallboard for managers
- Agent performance dashboard
- Call volume reports
- Sentiment trends
- Queue statistics

### 🔗 Integrations
- ERPNext CRM (Contact, Lead, Customer, Supplier, Employee)
- FreePBX / Asterisk (AMI + WebSocket)
- OpenAI (GPT-4 for AI features)
- WhatsApp (Meta Cloud API)
- Telegram (Bot API)
- OpenMeetings (REST API)

## 📋 Requirements

- Frappe Framework v15+
- ERPNext v15+ (optional, for CRM features)
- FreePBX 16+ or compatible PBX
- Modern browser with WebRTC support
- Python 3.10+

## 🚀 Installation

```bash
# Get the app
bench get-app https://github.com/company/arrowz --branch main

# Install on your site
bench --site your-site.com install-app arrowz

# Run migrations
bench migrate

# Build assets
bench build --app arrowz
```

## ⚙️ Configuration

### 1. PBX Server Setup
Navigate to **Arrowz > Server Config**:
- Add your PBX server details (FreePBX/Asterisk)
- Configure WebSocket URL (wss://pbx.example.com:8089/ws)
- Set AMI credentials

### 2. Extension Mapping
Navigate to **Arrowz > Extensions**:
- Map Frappe users to SIP extensions
- Set SIP passwords
- Enable WebRTC for each extension

### 3. WhatsApp Setup
Navigate to **Arrowz > Omni Providers**:
- Select "WhatsApp" channel type
- Add Phone Number ID and Access Token
- Configure Webhook URL and Verify Token

### 4. Telegram Setup
Navigate to **Arrowz > Omni Providers**:
- Select "Telegram" channel type
- Add Bot Token
- Set Webhook URL

### 5. OpenMeetings Setup
Navigate to **Arrowz > Server Config**:
- Select "OpenMeetings" server type
- Add server URL
- Set admin credentials

### 6. AI Setup (Optional)
Navigate to **Arrowz Settings**:
- Add OpenAI API key
- Enable sentiment analysis
- Configure coaching options

## 📖 Documentation

Full documentation available in `/arrowz/docs/`:

| Document | Description |
|----------|-------------|
| [01-OVERVIEW.md](arrowz/docs/01-OVERVIEW.md) | System architecture |
| [02-DATABASE-SCHEMA.md](arrowz/docs/02-DATABASE-SCHEMA.md) | DocType specifications |
| [03-API-REFERENCE.md](arrowz/docs/03-API-REFERENCE.md) | Backend API endpoints |
| [04-FRONTEND-GUIDE.md](arrowz/docs/04-FRONTEND-GUIDE.md) | JavaScript components |
| [05-INTEGRATION-GUIDE.md](arrowz/docs/05-INTEGRATION-GUIDE.md) | External integrations |
| [07-TECHNICAL-SPECS.md](arrowz/docs/07-TECHNICAL-SPECS.md) | Technical specifications |

### User Guides
- [Admin Guide](arrowz/docs/USER-GUIDE-ADMIN.md) - System configuration
- [Manager Guide](arrowz/docs/USER-GUIDE-MANAGER.md) - Wallboard & analytics
- [Agent Guide](arrowz/docs/USER-GUIDE-AGENT.md) - Daily operations
- [Developer Guide](arrowz/docs/DEVELOPER-GUIDE.md) - Extending Arrowz

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ARROWZ PLATFORM                          │
├─────────────────────────────────────────────────────────────────┤
│  Frontend Layer                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │  Softphone   │ │  Omni Panel  │ │     Screen Pop           ││
│  │  (WebRTC)    │ │  (Chat UI)   │ │  (Caller ID Display)     ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  API Layer (arrowz/api/)                                        │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐│
│  │ WebRTC │ │  SMS   │ │ Calls  │ │Analytics│ │ Communications ││
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  Integration Layer                                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │  WhatsApp    │ │  Telegram    │ │     OpenMeetings         ││
│  │  (Cloud API) │ │   (Bot API)  │ │   (Video Conference)     ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  External Systems                                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │   FreePBX    │ │   Asterisk   │ │    OpenMeetings Server   ││
│  │   (AMI/WS)   │ │   (SIP/WS)   │ │      (REST API)          ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 Key DocTypes

| DocType | Purpose |
|---------|---------|
| `Arrowz Settings` | Global app configuration |
| `AZ Call Log` | Call history and recordings |
| `AZ Extension` | User-to-SIP extension mapping |
| `AZ Server Config` | PBX/OpenMeetings server settings |
| `AZ SMS Message` | SMS log |
| `AZ SMS Provider` | SMS gateway configuration |
| `AZ Omni Provider` | WhatsApp/Telegram configuration |
| `AZ Omni Channel` | Channel routing |
| `AZ Conversation Session` | Chat sessions |
| `AZ Conversation Message` | Chat messages |
| `AZ Meeting Room` | Video conference rooms |
| `AZ Meeting Participant` | Meeting attendees |
| `AZ Meeting Recording` | Meeting recordings |

## 🛠️ Development

```bash
# Setup development environment
cd frappe-bench

# Watch for changes
bench watch --app arrowz

# Build assets
bench build --app arrowz

# Run tests
bench run-tests --app arrowz

# Clear cache
bench --site dev.localhost clear-cache

# Migrate
bench --site dev.localhost migrate
```

## 📁 Project Structure

```
arrowz/
├── arrowz/
│   ├── api/                 # Backend API endpoints
│   │   ├── webrtc.py        # WebRTC/JsSIP configuration
│   │   ├── sms.py           # SMS operations
│   │   ├── call_log.py      # Call logging
│   │   ├── contacts.py      # Contact search
│   │   ├── notifications.py # Pending notifications
│   │   ├── communications.py# Omni-channel messaging
│   │   ├── wallboard.py     # Real-time stats
│   │   ├── analytics.py     # Reports
│   │   └── webhooks.py      # External webhooks
│   ├── arrowz/
│   │   ├── doctype/         # DocType definitions
│   │   ├── workspace/       # Workspace configuration
│   │   └── page/            # Custom pages
│   ├── integrations/        # External service connectors
│   │   ├── whatsapp.py      # WhatsApp Cloud API
│   │   ├── telegram.py      # Telegram Bot API
│   │   └── openmeetings.py  # OpenMeetings REST API
│   ├── public/
│   │   ├── js/              # JavaScript files
│   │   │   ├── softphone_v2.js  # WebRTC softphone
│   │   │   ├── omni_panel.js    # Chat panel
│   │   │   └── phone_actions.js # Click-to-call
│   │   └── css/             # Stylesheets
│   ├── docs/                # Documentation
│   ├── hooks.py             # Frappe integration
│   ├── tasks.py             # Scheduled jobs
│   └── boot.py              # Session data
├── pyproject.toml
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please read our [Developer Guide](arrowz/docs/DEVELOPER-GUIDE.md) before submitting pull requests.

## 📄 License

MIT License - See [LICENSE](LICENSE) file.

## 📞 Support

- 📧 Email: support@arrowz.io
- 📖 Docs: [/arrowz/docs/](arrowz/docs/)
- 🐛 Issues: GitHub Issues

---

<p align="center">
  Built with ❤️ for the Frappe community
</p>
