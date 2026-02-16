# Arrowz Application - Complete Page Reference

This document contains a complete listing of all pages, DocTypes, and features in the Arrowz Communications Platform.

---

## 📡 Workspaces

| Workspace | URL | Description |
|-----------|-----|-------------|
| **Arrowz Communications Hub** | `/app/arrowz` | Main dashboard with real-time stats, quick actions, and navigation |

---

## 📄 Application Pages

| Page | URL | Icon | Description |
|------|-----|------|-------------|
| **Communications Hub** | `/app/arrowz` | 📡 | Main workspace with all features |
| **Dashboard** | `/app/arrowz-dashboard` | 🏠 | Overview of call center operations |
| **Agent Dashboard** | `/app/arrowz-agent-dashboard` | 🎧 | Agent workspace for handling calls |
| **Manager Wallboard** | `/app/arrowz-wallboard` | 📊 | Real-time call center monitoring |
| **Analytics** | `/app/arrowz-analytics` | 📈 | Advanced reporting and insights |
| **Communications** | `/app/arrowz-communications` | 💬 | Calls, SMS, Recordings hub |
| **Documentation** | `/app/arrowz-docs` | 📚 | Complete API and page reference |

---

## 📋 DocTypes

### Communications
| DocType | URL | Description |
|---------|-----|-------------|
| **AZ Call Log** | `/app/az-call-log` | All call records with details, duration, recordings |
| **AZ Call Transfer Log** | `/app/az-call-transfer-log` | Call transfer history |
| **AZ SMS Message** | `/app/az-sms-message` | SMS messages sent and received |

### Routing
| DocType | URL | Description |
|---------|-----|-------------|
| **AZ Inbound Route** | `/app/az-inbound-route` | Inbound call routing rules (DID → destination) |
| **AZ Outbound Route** | `/app/az-outbound-route` | Outbound call routing rules (dial patterns → trunk) |
| **AZ Trunk** | `/app/az-trunk` | SIP trunk configurations for external calls |

### Configuration
| DocType | URL | Description |
|---------|-----|-------------|
| **AZ Extension** | `/app/az-extension` | PBX extensions linked to Frappe users |
| **AZ Server Config** | `/app/az-server-config` | FreePBX/Asterisk server settings |
| **AZ SMS Provider** | `/app/az-sms-provider` | SMS gateway configurations |
| **Arrowz Settings** | `/app/arrowz-settings` | Global application settings |

---

## 🔌 API Endpoints

### WebRTC / Softphone
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `arrowz.api.webrtc.get_webrtc_config` | Get WebRTC configuration for softphone |
| POST | `arrowz.api.webrtc.initiate_call` | Initiate an outbound call |
| GET | `arrowz.api.webrtc.get_user_extensions` | Get user's assigned extensions |

### Call Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `arrowz.api.call_log.get_call_history` | Get call history with filters |
| GET | `arrowz.api.call_log.get_call_statistics` | Get call statistics for dashboard |
| GET | `arrowz.api.call_log.get_recent_calls` | Get recent calls quick list |

### Wallboard & Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `arrowz.api.wallboard.get_wallboard_data` | Get real-time wallboard data |
| GET | `arrowz.api.agent.get_agent_stats` | Get agent performance statistics |
| GET | `arrowz.api.analytics.get_analytics_data` | Get analytics and reports data |

### SMS
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `arrowz.api.sms.send_sms` | Send SMS message |
| GET | `arrowz.api.sms.get_sms_history` | Get SMS history |

### Recording
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `arrowz.api.recording.get_recording_url` | Get call recording URL |
| GET | `arrowz.api.recording.get_recording_transcript` | Get AI transcription |

### Screen Pop
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `arrowz.api.screenpop.get_caller_info` | Get caller information for screen pop |

---

## 🎨 Frontend Components

### JavaScript Files
| File | Description |
|------|-------------|
| `arrowz.js` | Main Arrowz module with click-to-call |
| `softphone.js` | WebRTC softphone integration |
| `phone_actions.js` | Phone field action buttons |
| `screen_pop.js` | Incoming call screen pop |

### CSS Files
| File | Description |
|------|-------------|
| `arrowz.css` | Main styles and workspace enhancements |
| `softphone.css` | Softphone UI styles |
| `phone_actions.css` | Phone action button styles |
| `screen_pop.css` | Screen pop dialog styles |

---

## ⚙️ Configuration

### Sidebar Links
The Arrowz module appears in the Frappe sidebar with the following structure:

```
📡 Arrowz
├── Communications
│   ├── Call Logs
│   ├── SMS Messages
│   └── Transfer Logs
├── Routing
│   ├── Inbound Routes
│   ├── Outbound Routes
│   └── Trunks
├── Configuration
│   ├── Extensions
│   ├── PBX Servers
│   ├── SMS Providers
│   └── Settings
└── Dashboards
    ├── Agent Dashboard
    ├── Manager Wallboard
    └── Analytics
```

---

## 🔗 Quick Access URLs

| Feature | URL |
|---------|-----|
| Make a Call | `javascript:arrowz.softphone.show()` |
| Call History | `/app/az-call-log` |
| Send SMS | `/app/az-sms-message/new` |
| Agent Dashboard | `/app/arrowz-agent-dashboard` |
| Wallboard | `/app/arrowz-wallboard` |
| Analytics | `/app/arrowz-analytics` |
| Settings | `/app/arrowz-settings` |
| Documentation | `/app/arrowz-docs` |

---

## 📊 Real-Time Features

- **Active Calls Counter**: Shows current ongoing calls
- **Missed Calls Alert**: Today's missed calls count
- **Agent Status**: Real-time agent availability
- **Call Duration Timer**: Live call duration display
- **SMS Counter**: Today's SMS count

---

*Last Updated: January 28, 2026*
*Version: 1.0.0*
