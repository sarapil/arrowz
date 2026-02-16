# Arrowz - Development Environment Context

## Quick Start for New Developers

This document provides essential context for developers joining the Arrowz project.

## Environment Details

| Attribute | Value |
|-----------|-------|
| **Container OS** | Debian GNU/Linux 12 (bookworm) |
| **Python** | 3.10+ |
| **Node.js** | 18+ |
| **Frappe** | v15 |
| **Database** | MariaDB 10.6+ |
| **Cache** | Redis |

## Directory Layout

```
/workspace/development/
├── frappe-bench/                    # Main bench directory
│   ├── apps/                        # All installed apps
│   │   ├── frappe/                  # Core framework
│   │   ├── erpnext/                 # ERPNext ERP
│   │   ├── arrowz/                  # ★ THIS APPLICATION ★
│   │   ├── hrms/                    # HR Management
│   │   └── ...                      # Other apps
│   │
│   ├── sites/
│   │   ├── dev.localhost/           # Development site
│   │   │   └── site_config.json     # Site configuration
│   │   └── common_site_config.json  # Shared config
│   │
│   ├── logs/                        # Application logs
│   ├── config/                      # Bench configuration
│   └── env/                         # Python virtual environment
│
└── .github/
    └── copilot-instructions.md      # AI assistant context
```

## Arrowz App Structure

```
/workspace/development/frappe-bench/apps/arrowz/
├── arrowz/                          # Main Python package
│   ├── api/                         # REST API endpoints
│   │   ├── webrtc.py               # JsSIP configuration
│   │   ├── contacts.py             # Contact search
│   │   ├── notifications.py        # Pending notifications
│   │   ├── communications.py       # Omni-channel messaging
│   │   ├── sms.py                  # SMS operations
│   │   ├── call_log.py             # Call history
│   │   ├── wallboard.py            # Dashboard stats
│   │   ├── analytics.py            # Reports
│   │   └── webhooks.py             # External webhooks
│   │
│   ├── arrowz/                      # Module directory
│   │   ├── doctype/                 # DocType definitions
│   │   ├── workspace/               # Workspace JSON
│   │   └── page/                    # Custom pages
│   │
│   ├── integrations/                # External connectors
│   │   ├── whatsapp.py             # WhatsApp Cloud API
│   │   ├── telegram.py             # Telegram Bot API
│   │   └── openmeetings.py         # Video conferencing
│   │
│   ├── public/                      # Static assets
│   │   ├── js/                      # JavaScript files
│   │   │   ├── softphone_v2.js     # WebRTC softphone
│   │   │   ├── omni_panel.js       # Chat panel
│   │   │   ├── phone_actions.js    # Click-to-call
│   │   │   └── screen_pop.js       # Caller ID popup
│   │   └── css/                     # Stylesheets
│   │
│   ├── events/                      # Document event handlers
│   ├── hooks.py                     # Frappe hooks
│   ├── tasks.py                     # Scheduled jobs
│   ├── boot.py                      # Session boot data
│   └── notifications.py             # Notification config
│
├── docs/                            # Documentation
├── CONTEXT.md                       # Technical context
├── INTEGRATIONS.md                  # Integration map
├── CLAUDE.md                        # Claude AI instructions
├── .cursorrules                     # Cursor AI rules
├── .github/copilot-instructions.md  # Copilot instructions
├── README.md                        # Overview
└── pyproject.toml                   # Python package config
```

## Common Commands

### Development
```bash
# Start development server
cd /workspace/development/frappe-bench
bench start

# Build Arrowz assets
bench build --app arrowz

# Watch for changes (auto-rebuild)
bench watch --app arrowz

# Clear cache
bench --site dev.localhost clear-cache
```

### Database & Migrations
```bash
# Run migrations after DocType changes
bench --site dev.localhost migrate

# Access database console
bench --site dev.localhost mariadb

# Backup
bench --site dev.localhost backup
```

### Testing & Debugging
```bash
# Run tests
bench --site dev.localhost run-tests --app arrowz

# Python console
bench --site dev.localhost console

# Check errors
tail -f logs/frappe.log
tail -f logs/worker.error.log
```

### Server Management
```bash
# Restart all processes
bench restart

# List installed apps
bench --site dev.localhost list-apps
```

## Key DocTypes Reference

### Call Management
- `AZ Call Log` - Call records
- `AZ Extension` - SIP extensions
- `AZ Server Config` - PBX servers

### Messaging
- `AZ SMS Message` - SMS log
- `AZ SMS Provider` - SMS gateways
- `AZ Omni Provider` - WhatsApp/Telegram config
- `AZ Conversation Session` - Chat sessions
- `AZ Conversation Message` - Chat messages

### Video Meetings
- `AZ Meeting Room` - Conference rooms
- `AZ Meeting Participant` - Attendees
- `AZ Meeting Recording` - Recordings

### Configuration
- `Arrowz Settings` - Global settings

## API Patterns

### Creating an API Endpoint
```python
# arrowz/api/mymodule.py
import frappe

@frappe.whitelist()
def my_function(param1: str, param2: int = 10) -> dict:
    """
    API documentation.
    
    Args:
        param1: Description
        param2: Optional description
        
    Returns:
        dict: Result
    """
    # Permission check
    frappe.only_for(['System Manager', 'Call Center Agent'])
    
    # Implementation
    result = frappe.get_all("AZ Call Log", 
        filters={"caller": param1},
        limit=param2
    )
    
    return {"data": result}
```

### Calling from JavaScript
```javascript
const { message } = await frappe.call({
    method: 'arrowz.api.mymodule.my_function',
    args: { param1: 'value', param2: 20 }
});
console.log(message.data);
```

## Real-time Communication

### Publishing Events (Python)
```python
frappe.publish_realtime(
    event="arrowz_custom_event",
    message={"key": "value"},
    user=frappe.session.user
)
```

### Subscribing (JavaScript)
```javascript
frappe.realtime.on("arrowz_custom_event", (data) => {
    console.log(data.key);
});
```

## Integration Quick Reference

| Service | Type | Config DocType |
|---------|------|----------------|
| FreePBX | WebSocket + AMI | `AZ Server Config` |
| WhatsApp | REST + Webhooks | `AZ Omni Provider` |
| Telegram | REST + Webhooks | `AZ Omni Provider` |
| OpenMeetings | REST | `AZ Server Config` |
| OpenAI | REST | `Arrowz Settings` |

## Troubleshooting

### Softphone Not Showing
1. Check browser console for JS errors
2. Verify navbar selector in softphone_v2.js
3. Ensure user has AZ Extension assigned

### WebRTC Not Connecting
1. Check WebSocket URL (must be wss://)
2. Verify SIP credentials
3. Confirm PBX WebSocket enabled

### Webhooks Not Working
1. Ensure URL is publicly accessible
2. Check webhook signature validation
3. Review Error Log in Frappe

## Documentation Files

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Full technical context |
| `INTEGRATIONS.md` | Integration architecture |
| `CLAUDE.md` | Claude AI quick reference |
| `.cursorrules` | Cursor AI rules |
| `.github/copilot-instructions.md` | GitHub Copilot context |
| `docs/DEVELOPER-GUIDE.md` | Detailed developer guide |

---

*For questions, check the docs/ directory or create an issue.*
