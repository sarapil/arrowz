# Arrowz - Complete Features Guide

> **Last Updated:** February 17, 2026  
> **Version:** 1.0.0  
> **Status:** Production Ready

---

## 📋 Table of Contents

1. [WebRTC Softphone](#1-webrtc-softphone)
2. [Call Management](#2-call-management)
3. [SMS Features](#3-sms-features)
4. [Omni-Channel Messaging](#4-omni-channel-messaging)
5. [Video Conferencing](#5-video-conferencing-openmeetings)
6. [Analytics & Reporting](#6-analytics--reporting)
7. [Agent Dashboard](#7-agent-dashboard)
8. [Manager Wallboard](#8-manager-wallboard)
9. [Screen Pop & CRM Integration](#9-screen-pop--crm-integration)
10. [PBX Integration](#10-pbx-integration)
11. [Phone Actions](#11-phone-actions)
12. [Real-Time Events](#12-real-time-events)
13. [Security Features](#13-security-features)
14. [Admin Configuration](#14-admin-configuration)
15. [Scheduled Tasks](#15-scheduled-tasks)
16. [DocTypes Reference](#16-doctypes-reference)
17. [API Endpoints Reference](#17-api-endpoints-reference)

---

## 1. WebRTC Softphone

### 1.1 Overview
Full-featured browser-based SIP softphone using **JsSIP 3.x** library, integrated directly into the Frappe navbar for instant access from any page.

### 1.2 Core Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Navbar Integration** | Dropdown softphone accessible from navbar on any page | ✅ Active |
| **Modal View** | Fullscreen modal for mobile devices | ✅ Active |
| **Make Calls** | Dial external numbers and internal extensions | ✅ Active |
| **Receive Calls** | Accept/reject incoming calls with caller ID | ✅ Active |
| **Call Hold** | Put calls on hold and resume | ✅ Active |
| **Call Mute** | Mute/unmute microphone during call | ✅ Active |
| **Blind Transfer** | Transfer call directly to another extension | ✅ Active |
| **Attended Transfer** | Consult before transferring | ✅ Active |
| **DTMF Support** | Dial pad for IVR navigation during calls | ✅ Active |
| **Auto-Registration** | Automatic SIP registration with retry logic | ✅ Active |
| **Microphone Pre-grant** | Pre-request mic permissions for faster connection | ✅ Active |
| **Video Calls** | Optional video calling support | ✅ Active |

### 1.3 Technical Specifications

```yaml
Library: JsSIP 3.x
Protocol: WebSocket SIP (WSS/WS)
Supported Codecs: OPUS, G.722, PCMU (G.711μ), PCMA (G.711A)
JavaScript File: softphone_v2.js (2365 lines)
Namespace: arrowz.softphone
```

### 1.4 UI Components

| Component | Description |
|-----------|-------------|
| **Status Indicator** | Shows registration status (Registered, Connecting, Offline) |
| **Extension Switcher** | Switch between multiple extensions (if assigned) |
| **Dial Pad** | Full numeric keypad with * and # |
| **Contact Search** | Autocomplete search for contacts/leads |
| **Call Timer** | Live duration counter during calls |
| **Action Buttons** | Hold, Mute, Transfer, Hangup, Keypad |
| **Volume Control** | Adjust speaker volume |
| **Recent Calls** | Quick access to recent numbers |

### 1.5 Configuration Options

| Option | Description | Location |
|--------|-------------|----------|
| WSS Server | WebSocket SIP server URL | AZ Server Config |
| SIP Domain | SIP registration domain | AZ Server Config |
| STUN Server | STUN server for NAT traversal | AZ Server Config |
| TURN Server | TURN server for NAT traversal | AZ Server Config |
| Auto-Register | Auto-register on page load | Per Extension |
| Enable Video | Allow video calls | Per Extension |

### 1.6 Multi-Extension Support
Users can be assigned multiple SIP extensions and switch between them dynamically:

- **Primary Extension**: Default extension for outbound calls
- **Secondary Extensions**: Additional extensions (e.g., department lines)
- **Extension Switcher**: UI dropdown to change active extension
- **Per-Extension Settings**: Each extension can have different configurations

### 1.7 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `arrowz.api.webrtc.get_server_config` | GET | Get SIP server configuration |
| `arrowz.api.webrtc.get_user_extension` | GET | Get current user's extension |
| `arrowz.api.webrtc.get_user_extensions` | GET | Get all user's extensions |
| `arrowz.api.webrtc.register_webrtc` | POST | Register WebRTC client |
| `arrowz.api.webrtc.unregister_webrtc` | POST | Unregister WebRTC client |
| `arrowz.api.webrtc.make_call` | POST | Initiate outbound call |
| `arrowz.api.webrtc.hangup_call` | POST | End active call |
| `arrowz.api.webrtc.transfer_call` | POST | Transfer active call |
| `arrowz.api.webrtc.hold_call` | POST | Hold/resume call |
| `arrowz.api.webrtc.send_dtmf` | POST | Send DTMF tones |

---

## 2. Call Management

### 2.1 Call Logging

Comprehensive automatic logging of all inbound and outbound calls with full metadata.

#### Captured Information

| Field | Description | Auto-Populated |
|-------|-------------|----------------|
| **Direction** | Inbound or Outbound | ✅ |
| **Caller ID** | Calling party number | ✅ |
| **Callee ID** | Called party number | ✅ |
| **Contact Name** | Resolved from CRM | ✅ |
| **Start Time** | When call initiated | ✅ |
| **Answer Time** | When call answered | ✅ |
| **End Time** | When call ended | ✅ |
| **Duration** | Total call duration (seconds) | ✅ |
| **Ring Duration** | Time before answer | ✅ |
| **Disposition** | ANSWERED, NO ANSWER, BUSY, FAILED, VOICEMAIL | ✅ |
| **Extension** | Extension that handled call | ✅ |
| **Server** | PBX server used | ✅ |
| **Recording Path** | Path to call recording | ✅ |
| **Recording URL** | Playback URL | ✅ |
| **CRM Party Type** | Lead, Customer, Contact, Supplier | ✅ |
| **CRM Party** | Link to CRM document | ✅ |
| **Sentiment Label** | AI-analyzed sentiment | Optional |
| **Sentiment Score** | Sentiment confidence (0-1) | Optional |
| **AI Transcript** | Speech-to-text transcript | Optional |

### 2.2 Call Recording

Full recording management with streaming playback and download.

| Feature | Description |
|---------|-------------|
| **Streaming Playback** | Play recordings in browser |
| **Download** | Download as MP3/WAV |
| **Permission Control** | Role-based access to recordings |
| **Configurable Path** | Custom recording storage path |
| **Delete Capability** | Remove old recordings |

**Supported Formats:** audio/mpeg, audio/wav, audio/ogg, audio/x-gsm

#### Recording API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `arrowz.api.recording.stream_recording` | GET | Stream recording audio |
| `arrowz.api.recording.download_recording` | GET | Download recording file |
| `arrowz.api.recording.get_recording_url` | GET | Get playback URL |
| `arrowz.api.recording.delete_recording` | DELETE | Delete recording |

### 2.3 Call Transfer Logging

Track all call transfers with details:

| Field | Description |
|-------|-------------|
| Transfer Type | Blind or Attended |
| Source Extension | Who initiated transfer |
| Target Extension | Transfer destination |
| Timestamp | When transfer occurred |
| Outcome | Success, Failed, Rejected |

### 2.4 Call Disposition Management

| Disposition | Description |
|-------------|-------------|
| **ANSWERED** | Call was answered and conversation occurred |
| **NO ANSWER** | Ring timeout, no answer |
| **BUSY** | Destination was busy |
| **FAILED** | Call failed (network, invalid number, etc.) |
| **VOICEMAIL** | Call went to voicemail |
| **CANCELLED** | Caller hung up before answer |

---

## 3. SMS Features

### 3.1 SMS Messaging

Full SMS send/receive capability with multiple provider support.

#### Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Send SMS** | Send text messages to any number | ✅ Active |
| **Receive SMS** | Receive incoming messages via webhook | ✅ Active |
| **Delivery Reports** | Track message delivery status | ✅ Active |
| **Character Count** | Real-time character/segment counting | ✅ Active |
| **Unicode Detection** | Auto-detect GSM vs UCS-2 encoding | ✅ Active |
| **CRM Linking** | Link SMS to CRM records | ✅ Active |
| **Real-time Notifications** | Notify users on incoming SMS | ✅ Active |
| **Templates** | Pre-defined message templates | ✅ Active |

### 3.2 SMS Providers

| Provider | Status | Features |
|----------|--------|----------|
| **Twilio** | ✅ Supported | Full features, delivery reports |
| **Vonage** | ✅ Supported | Full features |
| **MessageBird** | ✅ Supported | Full features |
| **Generic Webhook** | ✅ Supported | Custom integration |

### 3.3 SMS Character Limits

| Encoding | Single SMS | Concatenated |
|----------|-----------|--------------|
| GSM-7 (ASCII) | 160 chars | 153 chars/segment |
| UCS-2 (Unicode) | 70 chars | 67 chars/segment |

### 3.4 SMS API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `arrowz.api.sms.send_sms` | POST | Send SMS message |
| `arrowz.api.sms.get_sms_history` | GET | Get SMS history for number |
| `arrowz.api.sms.get_sms_templates` | GET | List message templates |
| `arrowz.api.sms.webhook_handler` | POST | Handle delivery webhooks |

### 3.5 SMS DocTypes

| DocType | Purpose |
|---------|---------|
| `AZ SMS Provider` | Provider configuration |
| `AZ SMS Message` | Individual SMS records |

---

## 4. Omni-Channel Messaging

### 4.1 Overview

Unified messaging platform supporting multiple channels through a single interface.

### 4.2 Supported Channels

| Channel | Status | Message Types |
|---------|--------|---------------|
| **WhatsApp Cloud API** | ✅ Active | Text, Media, Templates, Interactive |
| **WhatsApp On-Premise** | ✅ Active | Text, Media, Templates |
| **Telegram** | ✅ Active | Text, Media, Buttons, Commands |
| **SMS** | ✅ Active | Text |
| **Facebook Messenger** | 🔄 Planned | - |
| **Viber** | 🔄 Planned | - |

### 4.3 WhatsApp Integration

#### Message Types

| Type | Description | Supported |
|------|-------------|-----------|
| **Text** | Plain text with URL preview | ✅ |
| **Image** | Photos with caption | ✅ |
| **Video** | Videos with caption | ✅ |
| **Audio** | Voice messages | ✅ |
| **Document** | PDF, Word, Excel files | ✅ |
| **Template** | Pre-approved business templates | ✅ |
| **Interactive - Buttons** | Up to 3 quick reply buttons | ✅ |
| **Interactive - List** | Menu with sections | ✅ |
| **Location** | GPS coordinates | ✅ |
| **Contact** | Contact cards | ✅ |

#### Features

| Feature | Description |
|---------|-------------|
| **Webhook Verification** | Secure HMAC SHA-256 signature verification |
| **Template Management** | Fetch and manage templates from Meta Business |
| **Media Download** | Download and store incoming media |
| **Read Receipts** | Mark messages as read |
| **24-Hour Window** | Track conversation window for free messages |
| **Business Profile** | Display business info |

#### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `arrowz.api.whatsapp.send_message` | Send WhatsApp message |
| `arrowz.api.whatsapp.send_template` | Send template message |
| `arrowz.api.whatsapp.get_templates` | Fetch available templates |
| `arrowz.api.whatsapp.webhook` | Handle incoming webhooks |
| `arrowz.api.whatsapp.verify_webhook` | Webhook verification (GET) |

### 4.4 Telegram Integration

#### Message Types

| Type | Description | Supported |
|------|-------------|-----------|
| **Text** | Plain/HTML/Markdown text | ✅ |
| **Photo** | Images with caption | ✅ |
| **Video** | Videos with caption | ✅ |
| **Audio** | Audio files | ✅ |
| **Document** | Files with caption | ✅ |
| **Voice** | Voice messages | ✅ |
| **Animation** | GIFs | ✅ |
| **Inline Keyboard** | Button rows | ✅ |
| **Contact** | Contact cards | ✅ |
| **Location** | GPS coordinates | ✅ |

#### Features

| Feature | Description |
|---------|-------------|
| **Multi-Bot Support** | Configure multiple Telegram bots |
| **Callback Queries** | Handle button clicks |
| **Message Editing** | Edit sent messages |
| **Message Deletion** | Delete messages |
| **Webhook Management** | Auto-configure Telegram webhooks |
| **Secret Token** | Secure webhook verification |

#### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `arrowz.api.telegram.send_message` | Send Telegram message |
| `arrowz.api.telegram.send_media` | Send media message |
| `arrowz.api.telegram.webhook` | Handle incoming updates |
| `arrowz.api.telegram.set_webhook` | Configure bot webhook |

### 4.5 Conversation Sessions

Unified conversation management across all channels.

#### Session Fields

| Field | Description |
|-------|-------------|
| **Channel** | WhatsApp, Telegram, SMS |
| **Contact Identifier** | Phone number or chat ID |
| **Contact Name** | Resolved name |
| **Status** | Active, Pending, Resolved, Expired |
| **Assigned To** | Agent handling conversation |
| **CRM Link** | Contact, Lead, Customer, or Supplier |
| **Last Message Time** | Most recent message timestamp |
| **Unread Count** | Number of unread messages |
| **24h Window Expiry** | WhatsApp session window end time |
| **Response Time** | First response time metrics |

#### Session Statuses

| Status | Description |
|--------|-------------|
| **Active** | Ongoing conversation |
| **Pending** | Waiting for agent response |
| **Resolved** | Conversation closed |
| **Expired** | WhatsApp 24h window expired |

#### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `arrowz.api.conversation.get_sessions` | List conversation sessions |
| `arrowz.api.conversation.get_session_messages` | Get messages for session |
| `arrowz.api.conversation.send_message` | Send message in session |
| `arrowz.api.conversation.assign_session` | Assign to agent |
| `arrowz.api.conversation.resolve_session` | Mark as resolved |

### 4.6 Omni-Channel Panel

Unified communication panel displayed on CRM DocTypes.

#### Supported DocTypes

| DocType | Phone Fields Used |
|---------|-------------------|
| Lead | mobile_no, phone |
| Customer | mobile_no, phone |
| Contact | mobile_no, phone |
| Supplier | mobile_no, phone |
| Opportunity | contact_mobile |
| Prospect | mobile_no |
| Sales Order | contact_mobile |
| Purchase Order | contact_mobile |
| Quotation | contact_mobile |
| Employee | cell_number |
| Sales Partner | mobile_no |
| Issue | contact_mobile |
| Project | - |
| Task | - |
| Address | phone |

#### Panel Features

| Feature | Description |
|---------|-------------|
| **Channel Tabs** | Switch between WhatsApp, Telegram, SMS, Calls |
| **Unread Badges** | Count of unread messages per channel |
| **Message History** | Scrollable chat view |
| **Quick Actions** | Send WhatsApp, Telegram, SMS, Call, Meeting |
| **Quick Replies** | Pre-defined response templates |
| **Assignment** | Assign conversation to agent |
| **Real-time Updates** | Live message delivery via WebSocket |

#### Quick Reply Templates

Default templates available per channel:
- Greeting
- Thank you
- Please wait
- Request to call
- Request email

---

## 5. Video Conferencing (OpenMeetings)

### 5.1 Overview

Full integration with **Apache OpenMeetings** for video conferencing, webinars, and screen sharing.

### 5.2 Room Types

| Type | Description | Use Case |
|------|-------------|----------|
| **Conference** | All participants can share audio/video | Team meetings |
| **Webinar** | Host controls, participants view | Presentations |
| **Interview** | Two-party private room | Interviews, 1:1 |
| **Presentation** | Host presents, Q&A enabled | Training |
| **Restricted** | Moderated access | Secure meetings |

### 5.3 Room Features

| Feature | Description | Configurable |
|---------|-------------|--------------|
| **Recording** | Record meeting for playback | ✅ Yes |
| **Chat** | Text chat during meeting | ✅ Yes |
| **Whiteboard** | Collaborative drawing board | ✅ Yes |
| **File Sharing** | Share documents in meeting | ✅ Yes |
| **Screen Share** | Share screen/window | ✅ Yes |
| **Max Participants** | Limit room capacity | ✅ Yes |
| **Moderation** | Require moderator approval | ✅ Yes |
| **Password** | Optional room password | ✅ Yes |

### 5.4 Room Settings

| Setting | Description |
|---------|-------------|
| **Permanent** | Room persists after meeting ends |
| **Temporary** | Auto-delete after meeting |
| **Scheduled** | Specific start/end times |
| **Instant** | Start immediately |

### 5.5 Access URLs

| URL Type | Description |
|----------|-------------|
| **Moderator URL** | Full control access |
| **Participant URL** | Standard participant access |
| **Per-User URL** | Unique link per invited participant |

All URLs use secure hash-based authentication.

### 5.6 Participant Tracking

| Field | Description |
|-------|-------------|
| **Name** | Participant name |
| **Email** | Contact email |
| **Role** | Moderator or Participant |
| **Join Time** | When joined |
| **Leave Time** | When left |
| **Attended** | Whether actually joined |

### 5.7 Recordings

| Feature | Description |
|---------|-------------|
| **Auto-Record** | Start recording automatically |
| **List Recordings** | View all meeting recordings |
| **Download** | Download recording files |
| **Delete** | Remove old recordings |
| **Share** | Generate shareable links |

### 5.8 CRM Integration

Link meetings to CRM documents:
- Lead
- Customer
- Contact
- Supplier
- Opportunity
- Project
- Task

### 5.9 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `arrowz.api.meeting.create_room` | Create meeting room |
| `arrowz.api.meeting.get_room` | Get room details |
| `arrowz.api.meeting.get_join_url` | Generate join URL |
| `arrowz.api.meeting.add_participant` | Add participant |
| `arrowz.api.meeting.remove_participant` | Remove participant |
| `arrowz.api.meeting.start_recording` | Start recording |
| `arrowz.api.meeting.stop_recording` | Stop recording |
| `arrowz.api.meeting.get_recordings` | List recordings |
| `arrowz.api.meeting.end_room` | End meeting |
| `arrowz.api.meeting.webhook` | Handle OM webhooks |

### 5.10 Real-time Events

| Event | Description |
|-------|-------------|
| `meeting_user_joined` | User entered room |
| `meeting_user_left` | User left room |
| `meeting_ended` | Meeting concluded |
| `recording_ready` | Recording available |

---

## 6. Analytics & Reporting

### 6.1 Call Analytics Dashboard

Comprehensive call statistics and performance metrics.

#### Available Metrics

| Metric | Description |
|--------|-------------|
| **Total Calls** | Count of all calls |
| **Inbound Calls** | Incoming call count |
| **Outbound Calls** | Outgoing call count |
| **Answered Calls** | Successfully answered |
| **Missed Calls** | Unanswered calls |
| **Average Duration** | Mean call length |
| **Average Wait Time** | Mean time before answer |
| **Total Talk Time** | Sum of all durations |

#### Date Ranges

- Today
- This Week
- This Month
- This Year
- Custom Range

### 6.2 Analytics Views

#### Daily Trend Chart
Line/bar chart showing call volume over time:
- Inbound vs Outbound comparison
- Day-by-day breakdown
- Trend line

#### Disposition Breakdown
Pie/bar chart showing call outcomes:
- Answered %
- No Answer %
- Busy %
- Failed %
- Voicemail %

#### Hourly Heatmap
7x24 matrix showing call patterns:
- Day of week vs Hour
- Color intensity = call volume
- Peak hours identification

#### Sentiment Distribution
Breakdown of AI-analyzed call sentiment:
- Positive calls %
- Neutral calls %
- Negative calls %
- Trend over time

### 6.3 Agent Performance

| Metric | Description |
|--------|-------------|
| **Total Calls** | Calls handled by agent |
| **Answered** | Calls answered |
| **Missed** | Calls missed |
| **Answer Rate** | % of answered calls |
| **Avg Duration** | Average call length |
| **Total Talk Time** | Time on calls |
| **Avg Sentiment** | Mean sentiment score |

### 6.4 Analytics API Endpoints

| Endpoint | Description |
|----------|-------------|
| `arrowz.api.analytics.get_call_stats` | Overall statistics |
| `arrowz.api.analytics.get_daily_trend` | Daily call trend |
| `arrowz.api.analytics.get_disposition_breakdown` | Call outcomes |
| `arrowz.api.analytics.get_agent_performance` | Agent metrics |
| `arrowz.api.analytics.get_hourly_heatmap` | Hour/day matrix |
| `arrowz.api.analytics.get_sentiment_distribution` | Sentiment breakdown |
| `arrowz.api.analytics.export_report` | Export to Excel (async) |

### 6.5 Automated Reports

#### Daily Report
Sent every morning to managers:
- Yesterday's statistics
- Top agents
- Notable calls

#### Weekly Report
Sent every Monday:
- Week-over-week comparison
- Agent performance ranking
- Trend analysis
- Recommendations

#### Omni-Channel Report
Weekly channel performance:
- Messages by channel
- Response times
- Resolution rates

---

## 7. Agent Dashboard

### 7.1 Overview

Personal dashboard for call center agents showing status, stats, and quick actions.

### 7.2 Agent Statuses

| Status | Color | Description |
|--------|-------|-------------|
| **Available** | 🟢 Green | Ready to take calls |
| **Busy** | 🟡 Yellow | On a call or task |
| **Away** | 🟠 Orange | Temporarily away |
| **DND** | 🔴 Red | Do not disturb |
| **Offline** | ⚫ Gray | Not logged in |

### 7.3 Dashboard Components

| Component | Description |
|-----------|-------------|
| **Extension Info** | Current extension, registration status |
| **Status Selector** | Change current status |
| **Today's Stats** | Calls taken, duration, answer rate |
| **Recent Calls** | Last 10 calls with quick actions |
| **Recent Contacts** | Frequently called contacts |
| **Queue Status** | Calls waiting (if applicable) |

### 7.4 Agent API Endpoints

| Endpoint | Description |
|----------|-------------|
| `arrowz.api.agent.get_agent_status` | Get current status |
| `arrowz.api.agent.set_agent_status` | Update status |
| `arrowz.api.agent.get_extension_info` | Extension details |
| `arrowz.api.agent.get_today_stats` | Today's metrics |
| `arrowz.api.agent.get_recent_calls` | Recent call list |
| `arrowz.api.agent.get_recent_contacts` | Quick dial list |
| `arrowz.api.agent.heartbeat` | Keep-alive ping |
| `arrowz.api.agent.register_presence` | Register online |

### 7.5 Agent Heartbeat

Agents send periodic heartbeat to maintain "online" status:
- Heartbeat interval: 30 seconds
- Timeout threshold: 2 minutes
- Auto-offline after timeout

---

## 8. Manager Wallboard

### 8.1 Overview

Real-time dashboard for call center managers showing live operations.

### 8.2 Wallboard Displays

| Display | Description |
|---------|-------------|
| **Active Calls** | Currently ongoing calls with duration |
| **Agent Grid** | All agents with current status |
| **Queue Metrics** | Calls waiting, longest wait |
| **Today's Summary** | Total, answered, abandoned |
| **SLA Gauge** | Current SLA performance |
| **Hourly Chart** | Calls per hour today |

### 8.3 SLA Metrics

| Metric | Description | Configurable |
|--------|-------------|--------------|
| **Threshold** | Target answer time (seconds) | ✅ |
| **Warning Level** | Warning threshold | ✅ |
| **Current Rate** | % answered within threshold | Auto |
| **Trend** | Improving/declining indicator | Auto |

### 8.4 Queue Information

| Metric | Description |
|--------|-------------|
| **Waiting Calls** | Calls in queue |
| **Longest Wait** | Oldest call in queue |
| **Average Wait** | Mean wait time |
| **Abandoned** | Calls abandoned while waiting |

### 8.5 Manager Actions

| Action | Description |
|--------|-------------|
| **Barge** | Join an active call |
| **Whisper** | Speak to agent only |
| **Monitor** | Listen silently |
| **Force Logout** | Logout offline agent |

### 8.6 Wallboard API Endpoints

| Endpoint | Description |
|----------|-------------|
| `arrowz.api.wallboard.get_active_calls` | Current calls |
| `arrowz.api.wallboard.get_agent_status_grid` | All agent statuses |
| `arrowz.api.wallboard.get_hourly_stats` | Hourly breakdown |
| `arrowz.api.wallboard.get_sla_metrics` | SLA performance |
| `arrowz.api.wallboard.get_queue_status` | Queue details |
| `arrowz.api.wallboard.get_today_summary` | Summary stats |
| `arrowz.api.wallboard.barge_call` | Join call |

---

## 9. Screen Pop & CRM Integration

### 9.1 Screen Pop

Automatic popup showing caller information on incoming calls.

#### Display Modes

| Mode | Description |
|------|-------------|
| **Sidebar** | Slide-in panel from right |
| **Modal** | Center popup dialog |
| **New Tab** | Open in new browser tab |

#### Information Displayed

| Field | Description |
|-------|-------------|
| **Contact Name** | Matched CRM record name |
| **Company** | Associated company |
| **Contact Type** | Customer, Lead, Contact, Supplier |
| **Phone Numbers** | All associated numbers |
| **Last Contact** | Most recent interaction date |
| **Open Tickets** | Pending support issues |
| **Outstanding Amount** | For customers with balances |
| **Recent Orders** | Last 5 orders |

#### Screen Pop Actions

| Action | Description |
|--------|-------------|
| **Open Record** | Navigate to full CRM record |
| **Add Note** | Quick note on record |
| **Create Lead** | For unknown callers |
| **Create Contact** | For unknown callers |
| **View History** | Show all interactions |

### 9.2 Contact Resolution

Phone number matching across DocTypes:

| Priority | DocType | Fields Checked |
|----------|---------|----------------|
| 1 | Contact | mobile_no, phone |
| 2 | Lead | mobile_no, phone |
| 3 | Customer | mobile_no, phone |
| 4 | Supplier | mobile_no, phone |
| 5 | Employee | cell_number |

### 9.3 Screen Pop API Endpoints

| Endpoint | Description |
|----------|-------------|
| `arrowz.api.screenpop.resolve_caller` | Find caller in CRM |
| `arrowz.api.screenpop.get_caller_info` | Full caller details |
| `arrowz.api.screenpop.get_recent_interactions` | Interaction history |
| `arrowz.api.screenpop.create_lead_from_call` | Quick lead creation |
| `arrowz.api.screenpop.add_note` | Add note to record |

---

## 10. PBX Integration

### 10.1 FreePBX/Asterisk Integration

Full integration with FreePBX for extension management and call control.

#### Integration Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| **GraphQL API** | Modern API for extension management | Primary |
| **SSH/fwconsole** | Command-line fallback | Backup |
| **AMI** | Asterisk Manager Interface | Call control |

### 10.2 Auto-Provisioning

Automatic extension synchronization:

| Action | Description |
|--------|-------------|
| **Create** | When new AZ Extension created |
| **Update** | When extension settings changed |
| **Delete** | When extension trashed |

#### Synced Settings

- Extension number
- Display name
- SIP password
- Voicemail settings
- WebRTC configuration
- Call waiting
- Follow me

### 10.3 Server Configuration

| Setting | Description |
|---------|-------------|
| **PBX Hostname** | FreePBX server address |
| **PBX Port** | Web port (usually 443) |
| **Protocol** | WSS or WS |
| **SIP Domain** | SIP registration domain |
| **STUN Server** | NAT traversal server |
| **TURN Server** | NAT traversal with relay |
| **AMI Host** | Asterisk Manager host |
| **AMI Port** | AMI port (5038) |
| **AMI Username** | AMI credentials |
| **AMI Password** | AMI credentials |
| **SSH Host** | SSH server address |
| **SSH Port** | SSH port (22) |
| **SSH Username** | SSH credentials |
| **SSH Password** | SSH credentials |
| **GraphQL Endpoint** | GraphQL API URL |
| **GraphQL Client ID** | OAuth2 client ID |
| **GraphQL Client Secret** | OAuth2 secret |

### 10.4 Routing Configuration

#### Inbound Routes (`AZ Inbound Route`)
- DID matching patterns
- Destination types (extension, ring group, IVR)
- Time conditions
- Caller ID manipulation

#### Outbound Routes (`AZ Outbound Route`)
- Dial patterns
- Trunk selection
- Caller ID settings
- Emergency routes

#### Trunks (`AZ Trunk`)
- Trunk name and type
- Provider credentials
- Codec selection
- Registration settings

---

## 11. Phone Actions

### 11.1 Click-to-Action

Enhance all phone fields with action icons throughout the system.

### 11.2 Available Actions

| Icon | Action | Description |
|------|--------|-------------|
| 📱 | **Show Number** | Copy number to clipboard |
| 💬 | **SMS** | Open SMS composer |
| 🟢 | **WhatsApp** | Send WhatsApp message |
| ✈️ | **Telegram** | Send Telegram message |
| 📞 | **Call** | Dial via softphone |

### 11.3 Enhanced DocTypes

Actions added to phone fields in:
- Lead, Contact, Customer, Supplier
- Opportunity, Prospect
- Sales Order, Purchase Order, Quotation
- Employee, Address, Sales Partner
- Issue, Project, Task

### 11.4 Phone Field Names

Fields that get action icons:
- `mobile_no`, `phone`, `phone_no`
- `contact_mobile`, `contact_phone`
- `mobile`, `cell_number`
- `whatsapp_no`, `alternate_phone`
- `secondary_phone`

---

## 12. Real-Time Events

### 12.1 Published Events

All events use Frappe's `publish_realtime` system.

#### Call Events

| Event | Target | Data |
|-------|--------|------|
| `call_initiated` | User | extension, number, direction |
| `call_answered` | User | extension, call_id, duration |
| `call_ended` | User | call_id, duration, disposition |
| `call_hold_changed` | User | call_id, on_hold |
| `dtmf_sent` | User | call_id, digits |
| `transfer_initiated` | User | call_id, target |
| `incoming_call` | User | caller_id, caller_name |
| `arrowz_incoming_call` | User | caller details |
| `arrowz_missed_call` | User | caller_id, call_id |

#### SMS Events

| Event | Target | Data |
|-------|--------|------|
| `sms_received` | Global | sender, message |
| `sms_status_update` | Global | message_id, status |
| `arrowz_new_sms` | User | sms details |

#### Omni-Channel Events

| Event | Target | Data |
|-------|--------|------|
| `new_message` | DocType | message details |
| `message_status` | Global | message_id, status |
| `conversation_update` | Global | session details |
| `arrowz_conversation_update` | User | session details |
| `arrowz_session_assigned` | User | session_id, agent |
| `conversation_assigned` | User | session details |

#### Meeting Events

| Event | Target | Data |
|-------|--------|------|
| `meeting_user_joined` | DocType | room_id, user |
| `meeting_user_left` | DocType | room_id, user |
| `meeting_ended` | DocType | room_id |
| `recording_ready` | DocType | room_id, url |

#### Agent/System Events

| Event | Target | Data |
|-------|--------|------|
| `agent_status_changed` | Global | agent, status |
| `arrowz_agent_status_changed` | Global | extension, status |
| `extension_status_change` | Global | extension, status |
| `report_ready` | User | report_url |

---

## 13. Security Features

### 13.1 Authentication & Authorization

| Feature | Implementation |
|---------|----------------|
| **Webhook Signatures** | HMAC SHA-256 for WhatsApp |
| **Telegram Secret** | Secret token verification |
| **Permission Checks** | `frappe.has_permission()` on recordings |
| **Role-Based Access** | Call Center Agent, Manager roles |
| **Secure Password Storage** | `frappe.utils.password.get_decrypted_password()` |

### 13.2 Session Security

| Feature | Description |
|---------|-------------|
| **OpenMeetings SID** | Cached with TTL, auto-refresh |
| **Meeting URLs** | Hash-based authentication |
| **Token Refresh** | Automatic OAuth2 token refresh |
| **API Rate Limiting** | Configurable request limits |

### 13.3 Data Protection

| Feature | Description |
|---------|-------------|
| **Call Recording Access** | Permission-based playback |
| **CRM Data Filtering** | Role-based record visibility |
| **Audit Trail** | All actions logged |
| **Data Retention** | Automatic cleanup of old records |

---

## 14. Admin Configuration

### 14.1 Arrowz Settings (Singleton)

Global application configuration.

| Setting | Description | Default |
|---------|-------------|---------|
| **Enable Screen Pop** | Show caller info popup | ✅ On |
| **Enable Call Recording** | Record all calls | ✅ On |
| **Enable SMS** | SMS feature toggle | ✅ On |
| **Enable AI Features** | AI sentiment/transcript | ❌ Off |
| **OpenAI API Key** | For AI features | - |
| **Recording Base Path** | Storage location | /var/spool/asterisk/monitor |
| **SLA Threshold** | Answer time target (seconds) | 30 |
| **SLA Warning** | Warning threshold | 45 |
| **CRM Integration** | Link calls to CRM | ✅ On |

### 14.2 Server Configuration (`AZ Server Config`)

Per-server PBX settings (see section 10.3).

### 14.3 Omni Provider Configuration (`AZ Omni Provider`)

| Field | Description |
|-------|-------------|
| **Provider Type** | WhatsApp Cloud, WhatsApp On-Prem, Telegram |
| **API Base URL** | Provider API endpoint |
| **Access Token** | Authentication token |
| **Enabled** | Active/inactive toggle |

### 14.4 Omni Channel Configuration (`AZ Omni Channel`)

| Field | Description |
|-------|-------------|
| **Provider** | Link to AZ Omni Provider |
| **Channel Name** | Display name |
| **Phone Number ID** | WhatsApp phone number ID |
| **Business Account ID** | WhatsApp business account |
| **Bot Token** | Telegram bot token |
| **Webhook Secret** | Verification secret |
| **Default** | Default channel for type |

---

## 15. Scheduled Tasks

### 15.1 Cron Schedule

| Task | Frequency | Description |
|------|-----------|-------------|
| `mark_offline_agents` | */5 * * * * | Mark agents offline if no heartbeat |
| `update_stale_calls` | */10 * * * * | Update orphaned Ringing/InProgress calls |
| `check_whatsapp_window_expiry` | */15 * * * * | Check 24h window expiry |
| `sync_extension_status` | Hourly | Sync status with PBX |
| `sync_meeting_room_status` | Hourly | Sync room status with OpenMeetings |

### 15.2 Daily Tasks

| Task | Description |
|------|-------------|
| `cleanup_old_logs` | Delete logs older than 30 days |
| `send_daily_stats` | Email daily statistics to managers |
| `archive_old_conversations` | Archive resolved conversations |
| `cleanup_temp_meeting_rooms` | Delete expired temporary rooms |

### 15.3 Weekly Tasks

| Task | Description |
|------|-------------|
| `generate_weekly_report` | Generate and email weekly summary |
| `send_omni_channel_report` | Channel performance report |

---

## 16. DocTypes Reference

### 16.1 Core DocTypes

| DocType | Purpose |
|---------|---------|
| `Arrowz Settings` | Global app configuration (Singleton) |
| `AZ Server Config` | PBX/OpenMeetings server settings |
| `AZ Extension` | User SIP extension mappings |

### 16.2 Call Management DocTypes

| DocType | Purpose |
|---------|---------|
| `AZ Call Log` | Call records with full metadata |
| `AZ Call Transfer Log` | Transfer records |
| `AZ Inbound Route` | Inbound routing rules |
| `AZ Outbound Route` | Outbound routing rules |
| `AZ Trunk` | SIP trunk configuration |

### 16.3 SMS DocTypes

| DocType | Purpose |
|---------|---------|
| `AZ SMS Provider` | SMS provider configuration |
| `AZ SMS Message` | Individual SMS records |

### 16.4 Omni-Channel DocTypes

| DocType | Purpose |
|---------|---------|
| `AZ Omni Provider` | WhatsApp/Telegram provider config |
| `AZ Omni Channel` | Channel instance configuration |
| `AZ Conversation Session` | Chat sessions |
| `AZ Conversation Message` | Individual messages |

### 16.5 Meeting DocTypes

| DocType | Purpose |
|---------|---------|
| `AZ Meeting Room` | Video conference rooms |
| `AZ Meeting Participant` | Meeting participants |
| `AZ Meeting Recording` | Meeting recordings |

---

## 17. API Endpoints Reference

### 17.1 API Files

| File | Purpose |
|------|---------|
| `webrtc.py` | Softphone and call control |
| `sms.py` | SMS send/receive |
| `whatsapp.py` | WhatsApp integration |
| `telegram.py` | Telegram integration |
| `conversation.py` | Omni-channel sessions |
| `meeting.py` | Video conferencing |
| `analytics.py` | Statistics and reports |
| `agent.py` | Agent dashboard |
| `wallboard.py` | Manager wallboard |
| `screenpop.py` | Caller identification |
| `recording.py` | Call recordings |
| `contacts.py` | Contact search |
| `omni.py` | Unified messaging |

### 17.2 Webhook Endpoints

| Endpoint | Provider |
|----------|----------|
| `/api/method/arrowz.api.whatsapp.webhook` | WhatsApp |
| `/api/method/arrowz.api.telegram.webhook` | Telegram |
| `/api/method/arrowz.api.sms.webhook_handler` | SMS providers |
| `/api/method/arrowz.api.meeting.webhook` | OpenMeetings |

---

## 18. Boot Session Data

Data injected into `frappe.boot` for client-side access:

```json
{
  "arrowz": {
    "enabled": true,
    "has_extension": true,
    "extension": "1001",
    "sip_username": "1001",
    "features": {
      "screen_pop": true,
      "recording": true,
      "sms": true,
      "ai": false
    },
    "is_agent": true,
    "is_manager": false
  }
}
```

---

## 19. User Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| **Call Center Agent** | Front-line staff | Make/receive calls, view own stats |
| **Call Center Manager** | Supervisors | View all stats, wallboard, reports |
| **System Manager** | Administrators | Full configuration access |

---

## 20. Installation & Dependencies

### 20.1 Python Dependencies
- `requests` (HTTP client)
- `paramiko` (SSH)
- `openai` (optional, for AI features)

### 20.2 JavaScript Dependencies
- JsSIP 3.x (via CDN)
- Frappe UI components

### 20.3 External Services
- FreePBX 17+
- Apache OpenMeetings 5+
- Redis (for caching)
- MariaDB

---

*Last updated: February 17, 2026*
