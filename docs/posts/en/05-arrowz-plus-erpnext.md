<!-- Post Type: Multi-App Integration | Platform: discuss.frappe.io, ERPNext Community -->
<!-- Target: ERPNext users, Frappe developers -->
<!-- Last Updated: 2026-04-04 -->

# 🔗 Arrowz + ERPNext: The Communication Layer Your ERP is Missing

> **How to add VoIP, WhatsApp, and video meetings to your existing ERPNext setup in under an hour**

---

## The Gap in ERPNext

ERPNext is incredible for managing your business operations — accounting, inventory, HR, manufacturing. But when it comes to **communication**, there's a gap:

- You create a Sales Order but call the customer from a separate phone app
- A supplier sends a WhatsApp message but you copy-paste details into ERPNext
- Team meetings happen on Zoom but the agenda/minutes live elsewhere
- Network is managed from a completely different tool

**Arrowz fills this gap natively.**

## Integration Points

### 📞 Sales Workflow
```
Lead → Opportunity → Quotation → Sales Order → Invoice
  ↕        ↕           ↕           ↕           ↕
 Call     Call        Call        WhatsApp    WhatsApp
 Log      Log        Schedule    Confirm     Receipt
```

Every communication touchpoint is automatically logged against the relevant ERPNext document.

### 💬 Customer Support
```
Customer Issue (WhatsApp/Telegram/Call)
    → Auto-create Issue in ERPNext
    → Assign to Support Team
    → Track resolution via Omni-Channel
    → Close & send satisfaction survey via WhatsApp
```

### 🏗️ Project Communication
```
Project → Task → Meeting (OpenMeetings)
    → Record meeting → Attach to Task
    → Send action items via WhatsApp
    → Team notification via Telegram
```

### 🌐 IT Infrastructure
```
ERPNext Asset Management
    + Arrowz Network Management
    = Complete IT asset + network visibility
```

MikroTik routers registered as ERPNext Assets. Network status visible alongside asset details.

## Works With Other Arkan Lab Apps

| App | Integration |
|-----|-------------|
| **Vertex** (Construction) | Site communication, subcontractor calls, project WhatsApp groups |
| **Velara** (Hotel) | Guest messaging, housekeeping coordination, front desk calls |
| **AuraCRM** | Enriched contact profiles with call history + message timeline |
| **Candela** (Restaurant) | Order confirmations, delivery driver coordination |
| **ARKSpace** (Coworking) | Member communication, visitor notifications |
| **CAPS** | Role-based communication permissions |

## Quick Setup Guide

### 1. Install
```bash
bench get-app https://github.com/sarapil/arrowz
bench --site your-site install-app arrowz
bench --site your-site migrate
```

### 2. Configure PBX (AZ Server Config)
- Navigate to **AZ Server Config**
- Enter your FreePBX AMI credentials
- WebSocket URL for browser calling
- Test connection ✅

### 3. Enable WhatsApp
- Create Meta Business Account
- Get WhatsApp Cloud API token
- Configure in **AZ Omni Provider**
- Map phone number to ERPNext user

### 4. Enable Telegram (Optional)
- Create bot via @BotFather
- Add token to **AZ Omni Provider**
- Set webhook URL

### 5. Start Calling!
- Softphone icon appears in navbar
- Click any phone number in ERPNext to call
- All calls auto-logged in **AZ Call Log**

## Technical Details for Developers

**Hooks into ERPNext events:**
```python
# hooks.py
doc_events = {
    "Contact": {"after_insert": "arrowz.events.contact.after_insert"},
    "Lead": {"after_insert": "arrowz.events.lead.after_insert"},
}
```

**Real-time events:**
```javascript
// Listen for incoming calls
frappe.realtime.on("incoming_call", (data) => {
    arrowz.softphone.showIncomingCall(data);
});
```

**REST API:**
```
POST /api/method/arrowz.api.make_call
POST /api/method/arrowz.api.send_whatsapp
GET  /api/method/arrowz.api.get_call_history
```

## Community Feedback Welcome!

We'd love to hear from the Frappe/ERPNext community:
- What communication integrations do you need most?
- Are you currently using any VoIP integration with ERPNext?
- What's your biggest communication pain point?

---

*Arrowz is open source (MIT). Install it today and let us know what you think!*

**🔗 GitHub:** https://github.com/sarapil/arrowz
**📖 Docs:** https://arkan.it.com/arrowz/docs
**🏪 Marketplace:** Frappe Cloud Marketplace
