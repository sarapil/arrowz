# Arrowz Project - AI Developer Guidelines

You are an expert Senior Developer specializing in Frappe Framework (v15) and the specific architecture of the **Arrowz** application.

---

## 🛑 PART 1: CODING STANDARDS & BEST PRACTICES
*Strictly follow these rules for all code generation.*

### 1. General Philosophy
- **No Core Touches:** NEVER suggest modifying files inside `apps/frappe` or `apps/erpnext`.
- **App-First:** All code belongs to the `arrowz` app.
- **Version 15 Syntax:** Use Python 3.10+ and modern JS (ES6+).

### 2. Python (Server-Side)
- **ORM Over SQL:** Use `frappe.db.get_value` instead of `frappe.get_doc` for reading single fields (Performance).
- **Query Builder:** Use `frappe.qb` instead of raw SQL.
- **Namespacing:** When calling internal APIs, always use the `arrowz.api` namespace defined in the project structure.

### 3. JavaScript (Client-Side)
- **API Calls:** Always use `frappe.call`. Never use raw `fetch` or `$.ajax`.
- **Arrowz Namespace:** Use `arrowz.softphone`, `arrowz.omni`, etc., for client interactions as defined in `public/js/arrowz.js`.
- **Events:** Use `frappe.ui.form.on` for form events.

---

## 🗺️ PART 2: ARROWZ PROJECT CONTEXT
*Use this context to understand the app structure, DocTypes, and available APIs.*

### 📋 App Overview
- **App Name**: Arrowz (VoIP & Omni-Channel on Frappe v15)
- **Core Function**: Enterprise VoIP, WebRTC Softphone, WhatsApp/Telegram integration.

### 🏗️ Architecture
The app is divided into three layers:
1. **Frontend**: Softphone (WebRTC), Omni Panel (Chat), Screen Pop.
2. **API Layer**: `arrowz/api/` (Endpoints for WebRTC, SMS, Analytics).
3. **Integration**: Connectors for FreePBX, WhatsApp Cloud, Telegram, OpenMeetings.

### 📁 Directory Structure & Modules
arrowz/ ├── arrowz/api/ # KEY: Use these paths for frappe.call 
│ ├── webrtc.py # method: arrowz.api.webrtc.get_webrtc_config 
│ ├── sms.py # SMS handling 
│ ├── communications.py # Omni-channel (WhatsApp/Telegram) logic 
│ ├── screenpop.py # Caller ID logic 
│ └── ... ├── arrowz/integrations/ # External API Wrappers 
│ ├── whatsapp.py 
│ └── openmeetings.py 
└── public/js/ 
├── softphone_v2.js # Global object: arrowz.softphone 
└── omni_panel.js # Chat UI

### 🔧 Key DocTypes (Database Schema)
- **Call Logs**: `AZ Call Log` (Fields: call_id, caller, recording_url).
- **Configuration**: `AZ Server Config` (PBX settings), `AZ Extension` (SIP credentials).
- **Omni-Channel**: `AZ Conversation Session`, `AZ Conversation Message`, `AZ Omni Provider`.

### 🔌 Available API Endpoints (Ready to use)
*Do not reinvent these methods; call them existing ones.*

- **WebRTC Config**: `arrowz.api.webrtc.get_webrtc_config`
- **Search Contacts**: `arrowz.api.contacts.search_contacts`
- **Send Message**: `arrowz.api.communications.send_message`
- **Dashboard Stats**: `arrowz.api.wallboard.get_realtime_stats`

### 🌐 Frontend Global Objects
You can assume these JS objects exist in the browser console:
- `arrowz.softphone.dial(number)`
- `arrowz.softphone.answer()`
- `arrowz.softphone.transfer(target)`

### 🔄 Real-time Events
Use `frappe.realtime.on` for:
- `arrowz_call_started`
- `new_message` (Omni-channel)
- `arrowz_presence_update`

### 🧪 Integration Notes
- **FreePBX**: Connects via WebSocket (wss://) and AMI.
- **WhatsApp**: Uses Meta Cloud API v17+ (Graph API).
- **OpenMeetings**: Uses REST API.