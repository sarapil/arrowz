# Arrowz - Claude AI Instructions

## Quick Context

You are working with **Arrowz**, a Frappe Framework application for enterprise VoIP and omni-channel communications.

### Key Facts
- Framework: Frappe v15+ (Python/JavaScript)
- Purpose: WebRTC softphone, WhatsApp, Telegram, OpenMeetings integration
- Location: `/workspace/development/frappe-bench/apps/arrowz/`

## Project Structure Summary

```
arrowz/arrowz/
├── api/              # Python API endpoints (@frappe.whitelist)
├── arrowz/doctype/   # DocType definitions (database models)
├── integrations/     # External service connectors
├── public/js/        # Frontend JavaScript
├── public/css/       # Stylesheets
├── hooks.py          # Frappe integration hooks
└── tasks.py          # Background scheduled jobs
```

## Core DocTypes

| Name | Purpose |
|------|---------|
| `AZ Call Log` | Call records with caller, receiver, duration, status |
| `AZ Extension` | Maps Frappe users to SIP extensions |
| `AZ Server Config` | PBX/OpenMeetings server settings |
| `AZ SMS Message` | SMS history |
| `AZ Omni Provider` | WhatsApp/Telegram configuration |
| `AZ Conversation Session` | Chat sessions |
| `AZ Meeting Room` | Video conference rooms |

## Main Frontend Components

| File | Purpose |
|------|---------|
| `softphone_v2.js` | WebRTC softphone in navbar |
| `omni_panel.js` | Chat panel UI |
| `phone_actions.js` | Click-to-call buttons |
| `screen_pop.js` | Caller ID popup |
| `omni_doctype_extension.js` | Notification badge |

## Key APIs

```python
# WebRTC config for JsSIP
arrowz.api.webrtc.get_webrtc_config()

# Search contacts across DocTypes
arrowz.api.contacts.search_contacts(query, limit)

# Send omni-channel message
arrowz.api.communications.send_message(session, message)

# Dashboard stats
arrowz.api.wallboard.get_realtime_stats()
```

## Development Commands

```bash
bench build --app arrowz      # Build assets
bench watch --app arrowz      # Watch mode
bench --site dev.localhost clear-cache
bench --site dev.localhost migrate
bench restart
```

## Coding Patterns

### Python API
```python
@frappe.whitelist()
def my_api(param: str) -> dict:
    """Description."""
    frappe.only_for(['System Manager'])
    return {"data": result}
```

### JavaScript
```javascript
arrowz.feature = {
    async load() {
        const { message } = await frappe.call({
            method: 'arrowz.api.module.function'
        });
    }
};
```

### Real-time Events
```python
# Python: Publish
frappe.publish_realtime("arrowz_event", {"data": value}, user=user)
```
```javascript
// JavaScript: Subscribe
frappe.realtime.on("arrowz_event", (data) => { });
```

## Current State Notes

### Recent Changes (January 2026)
1. Softphone V2 with navbar integration
2. Multi-extension support
3. Contact search API
4. Notifications API for pending SMS/missed calls
5. OpenMeetings workspace section

### Known Integration Points
- FreePBX: WebSocket (wss://) + AMI
- WhatsApp: Graph API v17+ with webhooks
- Telegram: Bot API with webhooks
- OpenMeetings: REST API

## When Making Changes

1. **Python API changes**: Restart bench or `bench restart`
2. **JavaScript changes**: `bench build --app arrowz`
3. **DocType JSON changes**: `bench migrate`
4. **Workspace changes**: `bench migrate` + clear cache

## Reference Files

- [CONTEXT.md](CONTEXT.md) - Full technical context
- [INTEGRATIONS.md](INTEGRATIONS.md) - Integration details
- [README.md](README.md) - Overview and setup
- [.cursorrules](.cursorrules) - Cursor AI rules
- [.github/copilot-instructions.md](.github/copilot-instructions.md) - GitHub Copilot context
