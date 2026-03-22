# Arrowz - Architecture Documentation

> Detailed architecture diagrams and technical specifications.

## System Overview

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                           ARROWZ COMMUNICATIONS PLATFORM                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │                         PRESENTATION LAYER                               │  ║
║  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │  ║
║  │  │  Softphone  │  │  Omni Panel │  │  Screen Pop │  │   Dashboard     │ │  ║
║  │  │  (JsSIP)    │  │  (Chat UI)  │  │ (Caller ID) │  │   (Charts)      │ │  ║
║  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │  ║
║  └─────────┼────────────────┼────────────────┼──────────────────┼──────────┘  ║
║            │                │                │                  │             ║
║            ▼                ▼                ▼                  ▼             ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │                          API GATEWAY LAYER                               │  ║
║  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────────┐  │  ║
║  │  │ webrtc  │  │  calls  │  │  sms    │  │ comms   │  │  wallboard    │  │  ║
║  │  │  .py    │  │   .py   │  │   .py   │  │  .py    │  │     .py       │  │  ║
║  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └───────┬───────┘  │  ║
║  └───────┼────────────┼───────────┼────────────┼────────────────┼──────────┘  ║
║          │            │           │            │                │             ║
║          ▼            ▼           ▼            ▼                ▼             ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │                       BUSINESS LOGIC LAYER                               │  ║
║  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │  ║
║  │  │  Call Manager   │  │ Message Handler │  │   Meeting Coordinator   │  │  ║
║  │  └────────┬────────┘  └────────┬────────┘  └───────────┬─────────────┘  │  ║
║  └───────────┼────────────────────┼───────────────────────┼────────────────┘  ║
║              │                    │                       │                   ║
║              ▼                    ▼                       ▼                   ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │                         DATA ACCESS LAYER                                │  ║
║  │  ┌──────────────────────────────────────────────────────────────────┐   │  ║
║  │  │                    FRAPPE ORM (DocTypes)                          │   │  ║
║  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │   │  ║
║  │  │  │ AZ Call  │ │   AZ     │ │   AZ     │ │   AZ     │ │   AZ    │ │   │  ║
║  │  │  │   Log    │ │Extension │ │ Message  │ │ Session  │ │ Meeting │ │   │  ║
║  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └─────────┘ │   │  ║
║  │  └──────────────────────────────────────────────────────────────────┘   │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║              │                    │                       │                   ║
║              ▼                    ▼                       ▼                   ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │                       INTEGRATION LAYER                                  │  ║
║  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │  ║
║  │  │   FreePBX   │  │  WhatsApp   │  │  Telegram   │  │  OpenMeetings  │  │  ║
║  │  │  Connector  │  │  Connector  │  │  Connector  │  │   Connector    │  │  ║
║  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └───────┬────────┘  │  ║
║  └─────────┼────────────────┼────────────────┼─────────────────┼───────────┘  ║
║            │                │                │                 │              ║
║            ▼                ▼                ▼                 ▼              ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │                    DEVICE PROVIDER LAYER                                 │  ║
║  │  ┌──────────────────────┐  ┌──────────────────────┐                     │  ║
║  │  │    LinuxProvider     │  │  MikroTikProvider    │     (Extensible)    │  ║
║  │  │   (BoxConnector)     │  │  (RouterOSClient)    │                     │  ║
║  │  │   HTTPS + HMAC       │  │  RouterOS API        │                     │  ║
║  │  └──────────┬───────────┘  └──────────┬───────────┘                     │  ║
║  │             │  ProviderFactory ──────> │  SyncEngine                     │  ║
║  │             │  ErrorTracker            │                                 │  ║
║  └─────────────┼──────────────────────────┼────────────────────────────────┘  ║
║                │                          │                                   ║
╚════════════════╪══════════════════════════╪═══════════════════════════════════╝
                 │                          │
                 ▼                          ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  ┌────────────┐
    │   FreePBX   │  │  WhatsApp   │  │  Telegram   │  │  OpenMeetings  │  │  MikroTik  │
    │   Server    │  │  Cloud API  │  │   Bot API   │  │    Server      │  │   Router   │
    └─────────────┘  └─────────────┘  └─────────────┘  └────────────────┘  └────────────┘
```

---

## Data Flow Diagrams

### 1. Incoming Call Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        INCOMING CALL SEQUENCE                             │
└──────────────────────────────────────────────────────────────────────────┘

PSTN/SIP          FreePBX           WebSocket         JsSIP           Frappe
  Call              PBX              Server          (Browser)         Server
   │                 │                  │               │                │
   │  SIP INVITE     │                  │               │                │
   │─────────────────>                  │               │                │
   │                 │                  │               │                │
   │                 │  SIP INVITE      │               │                │
   │                 │  (WebSocket)     │               │                │
   │                 │─────────────────>│               │                │
   │                 │                  │               │                │
   │                 │                  │  SIP INVITE   │                │
   │                 │                  │  (WS Frame)   │                │
   │                 │                  │───────────────>                │
   │                 │                  │               │                │
   │                 │                  │               │ API: identify  │
   │                 │                  │               │ caller         │
   │                 │                  │               │───────────────>│
   │                 │                  │               │                │
   │                 │                  │               │ Return: contact│
   │                 │                  │               │ data           │
   │                 │                  │               │<───────────────│
   │                 │                  │               │                │
   │                 │                  │               │ Show Screen Pop│
   │                 │                  │               │ + Ring UI      │
   │                 │                  │               │─────────────┐  │
   │                 │                  │               │             │  │
   │                 │                  │               │<────────────┘  │
   │                 │                  │               │                │
   │                 │                  │  User Answers │                │
   │                 │                  │  (200 OK)     │                │
   │                 │                  │<──────────────│                │
   │                 │  200 OK          │               │                │
   │                 │<─────────────────│               │                │
   │  200 OK         │                  │               │                │
   │<────────────────│                  │               │                │
   │                 │                  │               │                │
   │  ═══════════════════════  RTP AUDIO STREAM  ═══════════════════════ │
   │                 │                  │               │                │
   │                 │  AMI Event       │               │                │
   │                 │  (Call Start)    │               │                │
   │                 │───────────────────────────────────────────────────>│
   │                 │                  │               │                │
   │                 │                  │               │  Create        │
   │                 │                  │               │  AZ Call Log   │
   │                 │                  │               │<───────────────│
   │                 │                  │               │                │
```

### 2. Outgoing Call Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        OUTGOING CALL SEQUENCE                             │
└──────────────────────────────────────────────────────────────────────────┘

User              Frappe           JsSIP            WebSocket        FreePBX
Click             Server          (Browser)          Server            PBX
  │                 │                │                  │                │
  │ Click-to-Call   │                │                  │                │
  │ Button          │                │                  │                │
  │─────────────────>                │                  │                │
  │                 │                │                  │                │
  │                 │ Get Extension  │                  │                │
  │                 │ Config         │                  │                │
  │                 │───────────────>│                  │                │
  │                 │                │                  │                │
  │                 │ Return Config  │                  │                │
  │                 │<───────────────│                  │                │
  │                 │                │                  │                │
  │                 │ dial(number)   │                  │                │
  │                 │───────────────>│                  │                │
  │                 │                │                  │                │
  │                 │                │  SIP INVITE      │                │
  │                 │                │  (WS Frame)      │                │
  │                 │                │─────────────────>│                │
  │                 │                │                  │                │
  │                 │                │                  │  SIP INVITE    │
  │                 │                │                  │────────────────>
  │                 │                │                  │                │
  │                 │                │                  │  100 Trying    │
  │                 │                │                  │<────────────────
  │                 │                │                  │                │
  │                 │                │  100 Trying      │                │
  │                 │                │<─────────────────│                │
  │                 │                │                  │                │
  │                 │                │  Show "Calling"  │                │
  │                 │                │  UI State        │                │
  │                 │                │───────────────┐  │                │
  │                 │                │               │  │                │
  │                 │                │<──────────────┘  │                │
  │                 │                │                  │                │
  │                 │                │                  │  180 Ringing   │
  │                 │                │                  │<────────────────
  │                 │                │                  │                │
  │                 │                │  180 Ringing     │                │
  │                 │                │<─────────────────│                │
  │                 │                │                  │                │
  │                 │                │  Play Ringback   │                │
  │                 │                │  Tone            │                │
  │                 │                │                  │  200 OK        │
  │                 │                │                  │<────────────────
  │                 │                │                  │                │
  │                 │                │  200 OK          │                │
  │                 │                │<─────────────────│                │
  │                 │                │                  │                │
  │                 │                │  ACK             │                │
  │                 │                │─────────────────>│                │
  │                 │                │                  │                │
  │ ═══════════════════════════  RTP AUDIO STREAM  ═══════════════════════
  │                 │                │                  │                │
```

### 3. WhatsApp Message Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    WHATSAPP MESSAGE FLOW (INCOMING)                       │
└──────────────────────────────────────────────────────────────────────────┘

WhatsApp          Meta              Frappe            Redis            User
 User            Webhook            Server            Queue           Browser
  │                 │                  │                │                │
  │ Send Message    │                  │                │                │
  │─────────────────>                  │                │                │
  │                 │                  │                │                │
  │                 │ POST /webhook    │                │                │
  │                 │ (Message Data)   │                │                │
  │                 │─────────────────>│                │                │
  │                 │                  │                │                │
  │                 │                  │ Enqueue        │                │
  │                 │                  │ Processing     │                │
  │                 │                  │───────────────>│                │
  │                 │                  │                │                │
  │                 │ 200 OK           │                │                │
  │                 │<─────────────────│                │                │
  │                 │                  │                │                │
  │                 │                  │                │                │
  │                 │                  │     Worker     │                │
  │                 │                  │     Process    │                │
  │                 │                  │<───────────────│                │
  │                 │                  │                │                │
  │                 │                  │ Create         │                │
  │                 │                  │ AZ Message     │                │
  │                 │                  │ + Session      │                │
  │                 │                  │                │                │
  │                 │                  │ Find/Create    │                │
  │                 │                  │ Contact        │                │
  │                 │                  │                │                │
  │                 │                  │ Socket.IO      │                │
  │                 │                  │ "new_omni_msg" │                │
  │                 │                  │────────────────────────────────>│
  │                 │                  │                │                │
  │                 │                  │                │   Update UI    │
  │                 │                  │                │   Omni Panel   │
  │                 │                  │                │   + Badge      │
  │                 │                  │                │                │


┌──────────────────────────────────────────────────────────────────────────┐
│                    WHATSAPP MESSAGE FLOW (OUTGOING)                       │
└──────────────────────────────────────────────────────────────────────────┘

User              Frappe            WhatsApp          Meta             Phone
Browser           Server            Connector        Cloud API         User
  │                 │                  │                │                │
  │ Send Message    │                  │                │                │
  │ (via Omni Panel)│                  │                │                │
  │─────────────────>                  │                │                │
  │                 │                  │                │                │
  │                 │ send_message()   │                │                │
  │                 │─────────────────>│                │                │
  │                 │                  │                │                │
  │                 │                  │ POST /messages │                │
  │                 │                  │ (Graph API)    │                │
  │                 │                  │───────────────>│                │
  │                 │                  │                │                │
  │                 │                  │                │ Deliver        │
  │                 │                  │                │ Message        │
  │                 │                  │                │───────────────>│
  │                 │                  │                │                │
  │                 │                  │ 200 OK         │                │
  │                 │                  │ {message_id}   │                │
  │                 │                  │<───────────────│                │
  │                 │                  │                │                │
  │                 │ Create AZ        │                │                │
  │                 │ Message (sent)   │                │                │
  │                 │<─────────────────│                │                │
  │                 │                  │                │                │
  │ Socket.IO       │                  │                │                │
  │ "message_sent"  │                  │                │                │
  │<─────────────────                  │                │                │
  │                 │                  │                │                │
  │ Update UI       │                  │                │                │
  │ (show sent msg) │                  │                │                │
  │                 │                  │                │                │
```

### 4. OpenMeetings Video Conference Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    OPENMEETINGS CONFERENCE FLOW                           │
└──────────────────────────────────────────────────────────────────────────┘

Organizer         Frappe         OpenMeetings       Participant       OM
 Browser          Server           Server            Browser         Room
   │                │                │                   │             │
   │ Create Room    │                │                   │             │
   │───────────────>│                │                   │             │
   │                │                │                   │             │
   │                │ POST /room     │                   │             │
   │                │ (REST API)     │                   │             │
   │                │───────────────>│                   │             │
   │                │                │                   │             │
   │                │                │ Create Room       │             │
   │                │                │──────────────────────────────────>
   │                │                │                   │             │
   │                │ {room_id, hash}│                   │             │
   │                │<───────────────│                   │             │
   │                │                │                   │             │
   │                │ Create AZ      │                   │             │
   │                │ Meeting Room   │                   │             │
   │                │                │                   │             │
   │ Room Created   │                │                   │             │
   │<───────────────│                │                   │             │
   │                │                │                   │             │
   │                │                │                   │             │
   │ Invite         │                │                   │             │
   │ Participants   │                │                   │             │
   │───────────────>│                │                   │             │
   │                │                │                   │             │
   │                │ Email/SMS      │                   │             │
   │                │ with Link      │                   │             │
   │                │──────────────────────────────────> │             │
   │                │                │                   │             │
   │                │                │                   │ Click Link  │
   │                │                │                   │──────────────>
   │                │                │                   │             │
   │                │                │   Get Secure Hash │             │
   │                │<───────────────────────────────────│             │
   │                │                │                   │             │
   │                │ POST /user     │                   │             │
   │                │ /hash          │                   │             │
   │                │───────────────>│                   │             │
   │                │                │                   │             │
   │                │ {secure_url}   │                   │             │
   │                │<───────────────│                   │             │
   │                │                │                   │             │
   │                │ Redirect to OM │                   │             │
   │                │──────────────────────────────────> │             │
   │                │                │                   │             │
   │                │                │   Join Room       │             │
   │                │                │<──────────────────│             │
   │                │                │                   │             │
   │                │                │   WebRTC Stream   │             │
   │                │                │<═════════════════>│             │
   │                │                │                   │             │
```

---

## Component Diagrams

### Frontend Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND COMPONENT MAP                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ NAVBAR (frappe.desk)                                                     │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
│  │  SOFTPHONE       │  │  OMNI BADGE      │  │  SCREEN POP (Modal)   │  │
│  │  DROPDOWN        │  │  (Notifications) │  │                       │  │
│  │  ┌────────────┐  │  │  ┌────────────┐  │  │  ┌─────────────────┐  │  │
│  │  │  Status    │  │  │  │  Badge     │  │  │  │  Caller Info    │  │  │
│  │  │  Display   │  │  │  │  Counter   │  │  │  │                 │  │  │
│  │  ├────────────┤  │  │  │  (12)      │  │  │  │  Name: John Doe │  │  │
│  │  │  Dial Pad  │  │  │  └────────────┘  │  │  │  Phone: +1234.. │  │  │
│  │  │  ┌─┬─┬─┐   │  │  │                  │  │  │  Company: XYZ   │  │  │
│  │  │  │1│2│3│   │  │  └──────────────────┘  │  │                 │  │  │
│  │  │  ├─┼─┼─┤   │  │                        │  │  [Answer] [Reject]  │
│  │  │  │4│5│6│   │  │                        │  │                 │  │  │
│  │  │  ├─┼─┼─┤   │  │                        │  └─────────────────┘  │  │
│  │  │  │7│8│9│   │  │                        │                       │  │
│  │  │  ├─┼─┼─┤   │  │                        └───────────────────────┘  │
│  │  │  │*│0│#│   │  │                                                   │
│  │  │  └─┴─┴─┘   │  │                                                   │
│  │  ├────────────┤  │                                                   │
│  │  │  Controls  │  │                                                   │
│  │  │  [📞][🔇][⏸]│  │                                                   │
│  │  └────────────┘  │                                                   │
│  └──────────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ OMNI PANEL (Right Sidebar)                                               │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  HEADER                                                              ││
│  │  ┌─────────────────┐ ┌─────────┐ ┌─────────┐                        ││
│  │  │  Session Info   │ │ WhatsApp│ │Telegram │                        ││
│  │  │  John Doe       │ │   🟢    │ │   🔵    │                        ││
│  │  └─────────────────┘ └─────────┘ └─────────┘                        ││
│  ├─────────────────────────────────────────────────────────────────────┤│
│  │  MESSAGES                                                            ││
│  │  ┌─────────────────────────────────────────────────────────────────┐││
│  │  │  ┌───────────────────────────────────┐                          │││
│  │  │  │ 🟢 Hi, I need help with my order  │  10:30 AM               │││
│  │  │  └───────────────────────────────────┘                          │││
│  │  │                    ┌───────────────────────────────────┐        │││
│  │  │                    │ Sure! What's your order number?  │ 10:31  │││
│  │  │                    └───────────────────────────────────┘        │││
│  │  │  ┌───────────────────────────────────┐                          │││
│  │  │  │ 🟢 It's #12345                     │  10:32 AM               │││
│  │  │  └───────────────────────────────────┘                          │││
│  │  └─────────────────────────────────────────────────────────────────┘││
│  ├─────────────────────────────────────────────────────────────────────┤│
│  │  INPUT                                                               ││
│  │  ┌─────────────────────────────────────────┐ ┌────┐ ┌────────────┐  ││
│  │  │ Type a message...                       │ │ 📎 │ │   Send     │  ││
│  │  └─────────────────────────────────────────┘ └────┘ └────────────┘  ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

### Backend Module Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        BACKEND MODULE MAP                                │
└─────────────────────────────────────────────────────────────────────────┘

arrowz/arrowz/
│
├── api/                           ← @frappe.whitelist() endpoints
│   ├── webrtc.py                  │
│   │   ├── get_extension_config() │─── Returns JsSIP config
│   │   └── get_all_extensions()   │
│   │
│   ├── calls.py                   │
│   │   ├── make_call()            │─── Originate call via AMI
│   │   ├── hangup_call()          │
│   │   ├── transfer_call()        │
│   │   └── get_call_history()     │
│   │
│   ├── sms.py                     │
│   │   ├── send_sms()             │─── Send via provider
│   │   └── get_sms_history()      │
│   │
│   ├── communications.py          │
│   │   ├── send_omni_message()    │─── WhatsApp/Telegram
│   │   ├── get_sessions()         │
│   │   └── get_conversation()     │
│   │
│   ├── contacts.py                │
│   │   ├── search_contacts()      │─── Cross-DocType search
│   │   ├── get_contact_by_phone() │
│   │   └── create_quick_contact() │
│   │
│   ├── wallboard.py               │
│   │   ├── get_live_stats()       │─── Real-time metrics
│   │   ├── get_queue_stats()      │
│   │   └── get_agent_status()     │
│   │
│   └── analytics.py               │
│       ├── get_call_volume()      │─── Charts data
│       ├── get_agent_performance()│
│       └── get_sentiment_trends() │
│
├── integrations/                   ← External service connectors
│   ├── whatsapp.py                │
│   │   ├── send_message()         │─── Meta Cloud API
│   │   ├── send_template()        │
│   │   ├── download_media()       │
│   │   └── verify_webhook()       │
│   │
│   ├── telegram.py                │
│   │   ├── send_message()         │─── Telegram Bot API
│   │   ├── get_updates()          │─── Polling mode
│   │   └── set_webhook()          │
│   │
│   ├── openmeetings.py            │
│   │   ├── create_room()          │─── REST API
│   │   ├── get_room_hash()        │
│   │   ├── invite_user()          │
│   │   └── get_recordings()       │
│   │
│   └── openai_client.py           │
│       ├── analyze_sentiment()    │
│       ├── transcribe_audio()     │
│       └── generate_summary()     │
│
├── events/                         ← Document event handlers
│   ├── call_log.py                │
│   ├── extension.py               │
│   └── session.py                 │
│
├── hooks.py                        ← Frappe integration hooks
│   ├── app_include_js             │
│   ├── app_include_css            │
│   ├── boot_session               │
│   ├── scheduler_events           │
│   └── doc_events                 │
│
├── tasks.py                        ← Background jobs
│   ├── process_telegram_updates() │
│   ├── sync_call_logs()           │
│   ├── cleanup_old_sessions()     │
│   └── send_scheduled_messages()  │
│
└── boot.py                         ← Session boot data
    └── get_boot_data()            │─── Extension, settings
```

---

## Database Schema (Simplified ERD)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATABASE ENTITY DIAGRAM                           │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   AZ Extension   │       │   AZ Call Log    │       │  AZ SMS Message  │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ name (PK)        │       │ name (PK)        │       │ name (PK)        │
│ extension        │◄──────│ caller           │       │ from_number      │
│ user (FK→User)   │       │ receiver         │       │ to_number        │
│ server (FK)      │       │ direction        │       │ message          │
│ sip_password     │       │ status           │       │ direction        │
│ webrtc_enabled   │       │ duration         │       │ status           │
│ enabled          │       │ recording_url    │       │ sent_at          │
└──────────────────┘       │ start_time       │       └──────────────────┘
         │                 │ end_time         │
         │                 │ extension (FK)   │
         │                 └──────────────────┘
         │
         │                 ┌──────────────────┐       ┌──────────────────┐
         │                 │ AZ Omni Provider │       │AZ Conversation   │
         │                 ├──────────────────┤       │    Session       │
         │                 │ name (PK)        │       ├──────────────────┤
         │                 │ provider_type    │◄──────│ name (PK)        │
         │                 │ api_key          │       │ provider (FK)    │
         │                 │ webhook_url      │       │ remote_id        │
         │                 │ phone_number_id  │       │ contact_name     │
         │                 │ enabled          │       │ contact_phone    │
         │                 └──────────────────┘       │ status           │
         │                                            │ last_message_at  │
         │                                            │ unread_count     │
         │                                            └──────────────────┘
         │                                                     │
         │                                                     │
         ▼                                                     ▼
┌──────────────────┐                               ┌──────────────────┐
│ AZ Server Config │                               │   AZ Message     │
├──────────────────┤                               ├──────────────────┤
│ name (PK)        │                               │ name (PK)        │
│ pbx_host         │                               │ session (FK)     │
│ ami_port         │                               │ direction        │
│ ami_username     │                               │ message_type     │
│ ami_password     │                               │ content          │
│ websocket_url    │                               │ media_url        │
│ om_url           │                               │ status           │
│ om_user          │                               │ sent_at          │
│ om_password      │                               │ delivered_at     │
│ enabled          │                               │ read_at          │
└──────────────────┘                               └──────────────────┘


┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  AZ Meeting Room │       │AZ Meeting Partic.│       │AZ Meeting Record.│
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ name (PK)        │◄──────│ name (PK)        │       │ name (PK)        │
│ room_name        │       │ room (FK)        │       │ room (FK)        │
│ om_room_id       │       │ user (FK)        │       │ recording_url    │
│ room_type        │       │ email            │       │ duration         │
│ is_moderated     │       │ is_moderator     │       │ created_at       │
│ max_participants │       │ joined_at        │       └──────────────────┘
│ created_by       │       │ left_at          │
│ created_at       │       └──────────────────┘
└──────────────────┘
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION DEPLOYMENT                             │
└─────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────────┐
                              │   Load Balancer  │
                              │    (Nginx/HAProxy│
                              └────────┬─────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
    │   Web Server 1   │    │   Web Server 2   │    │   Web Server N   │
    │   (Gunicorn)     │    │   (Gunicorn)     │    │   (Gunicorn)     │
    │                  │    │                  │    │                  │
    │  ┌────────────┐  │    │  ┌────────────┐  │    │  ┌────────────┐  │
    │  │  Frappe    │  │    │  │  Frappe    │  │    │  │  Frappe    │  │
    │  │  + Arrowz  │  │    │  │  + Arrowz  │  │    │  │  + Arrowz  │  │
    │  └────────────┘  │    │  └────────────┘  │    │  └────────────┘  │
    └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
             │                       │                       │
             └───────────────────────┼───────────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │  MariaDB Cluster │  │   Redis Cluster  │  │  Socket.IO       │
    │  (Master-Slave)  │  │   (Cache+Queue)  │  │  (Real-time)     │
    └──────────────────┘  └──────────────────┘  └──────────────────┘

                              ┌──────────────────┐
                              │  Background      │
                              │  Workers         │
                              │  (RQ Workers)    │
                              └──────────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SECURITY LAYERS                                   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 1: Network Security                                                │
│  • HTTPS/TLS 1.3 for all connections                                    │
│  • WSS for WebSocket connections                                         │
│  • Firewall rules for internal services                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 2: Authentication                                                  │
│  • Frappe session authentication                                         │
│  • API key authentication for webhooks                                   │
│  • SIP authentication for WebRTC                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 3: Authorization                                                   │
│  • Role-based access control (RBAC)                                      │
│  • Document-level permissions                                            │
│  • @frappe.whitelist() for API endpoints                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 4: Data Protection                                                 │
│  • Encrypted password storage                                            │
│  • Parameterized SQL queries                                             │
│  • Input validation and sanitization                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Real-time Event Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        REAL-TIME EVENT FLOW                              │
└─────────────────────────────────────────────────────────────────────────┘

┌───────────────────┐          ┌───────────────────┐          ┌───────────────────┐
│   Event Source    │          │   Redis Pub/Sub   │          │    Socket.IO      │
│                   │          │                   │          │    Server         │
│  • API calls      │          │                   │          │                   │
│  • Webhooks       │  ──────> │  frappe_realtime  │  ──────> │  Port 9000        │
│  • Background     │          │                   │          │                   │
│    jobs           │          │                   │          │                   │
└───────────────────┘          └───────────────────┘          └─────────┬─────────┘
                                                                        │
                                                                        │
              ┌──────────────────────────────────────────────────────────┤
              │                        │                                 │
              ▼                        ▼                                 ▼
    ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
    │   Browser 1       │    │   Browser 2       │    │   Browser N       │
    │                   │    │                   │    │                   │
    │ frappe.realtime   │    │ frappe.realtime   │    │ frappe.realtime   │
    │   .on('event')    │    │   .on('event')    │    │   .on('event')    │
    └───────────────────┘    └───────────────────┘    └───────────────────┘


Event Types:
┌─────────────────────────────────────────────────────────────────────────┐
│ call_received      │ Incoming call notification                         │
│ call_ended         │ Call ended, update UI                              │
│ new_omni_message   │ New WhatsApp/Telegram message                      │
│ session_updated    │ Conversation session changed                       │
│ extension_status   │ SIP extension online/offline                       │
│ wallboard_update   │ Live statistics refresh                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File Reference

| File | Type | Purpose |
|------|------|---------|
| `README.md` | Documentation | Project overview |
| `CONTEXT.md` | Documentation | Full technical context |
| `CONTEXT-AR.md` | Documentation | Arabic context |
| `INTEGRATIONS.md` | Documentation | Integration details |
| `DEVELOPMENT.md` | Documentation | Dev environment guide |
| `AI_GUIDELINES.md` | Documentation | AI coding guidelines |
| `ARCHITECTURE.md` | Documentation | This file |
| `CLAUDE.md` | Documentation | Claude AI quick ref |
| `.cursorrules` | Config | Cursor AI rules |
| `.github/copilot-instructions.md` | Config | Copilot context |

---

## Device Provider Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    DEVICE PROVIDER LAYER                                │
└─────────────────────────────────────────────────────────────────────────┘

     ┌────────────────────────────────────────────────────┐
     │              ProviderFactory                       │
     │  Registry:                                         │
     │   "Linux Box" → LinuxProvider                     │
     │   "MikroTik"  → MikroTikProvider                  │
     │                                                    │
     │  Methods:                                          │
     │   get_provider(box_doc) → BaseProvider             │
     │   connect(box_doc) → ContextManager               │
     └────────────────────────┬───────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               │                             │
     ┌─────────▼─────────┐       ┌───────────▼───────────┐
     │   LinuxProvider   │       │  MikroTikProvider     │
     │                   │       │                       │
     │  BoxConnector     │       │  RouterOSClient       │
     │  HTTPS + HMAC     │       │  librouteros 4.0.0    │
     │  Bearer token     │       │  TCP port 8728/8729   │
     │                   │       │                       │
     │  Wraps existing   │       │  Supports:            │
     │  REST API agent   │       │  • RouterOS v6 + v7   │
     │                   │       │  • WiFi / CAPsMAN      │
     │  ConfigCompiler   │       │  • WireGuard VPN      │
     │  for push ops     │       │  • Full CRUD          │
     └───────────────────┘       └───────────────────────┘
```

## Sync Engine Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       SYNC ENGINE FLOW                                  │
└─────────────────────────────────────────────────────────────────────────┘

                    PULL (Device → Frappe)
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Arrowz   │    │   Provider   │    │   Mapper     │    │   Frappe     │
│   Box    │───>│ get_full_    │───>│ RouterOS →   │───>│  DocTypes    │
│ DocType  │    │  config()    │    │  Frappe fmt  │    │  (create/    │
│          │    │              │    │              │    │   update)    │
└──────────┘    └──────────────┘    └──────────────┘    └──────────────┘

                    PUSH (Frappe → Device)
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Frappe  │    │   Config     │    │   Provider   │    │   Device     │
│ DocTypes │───>│  Compiler    │───>│ push_full_   │───>│  (RouterOS   │
│          │    │              │    │  config()    │    │   or Linux)  │
└──────────┘    └──────────────┘    └──────────────┘    └──────────────┘

                    DIFF (Compare)
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│  Device  │    │   Compare    │    │   Diff       │
│  Config  │───>│   Engine     │───>│  Report      │
│          │    │              │    │  (JSON)      │
│  Frappe  │───>│              │    │              │
│  Config  │    │              │    │              │
└──────────┘    └──────────────┘    └──────────────┘

All operations logged to MikroTik Sync Log DocType via ErrorTracker.
```

## Local PBX Monitor Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    LOCAL PBX MONITOR (Dev Environment)                   │
└─────────────────────────────────────────────────────────────────────────┘

                    Docker Volume Mounts (read-only)
FreePBX Container                           Arrowz Dev Container
┌────────────────┐                         ┌────────────────────────────┐
│ /etc/asterisk/ │ ──── mount ──────────>  │ /mnt/pbx/etc/asterisk/    │
│ /var/log/      │ ──── mount ──────────>  │ /mnt/pbx/logs/            │
│ /var/spool/    │ ──── mount ──────────>  │ /mnt/pbx/recordings/      │
│ /var/spool/vm/ │ ──── mount ──────────>  │ /mnt/pbx/voicemail/       │
│ /backup/       │ ──── mount ──────────>  │ /mnt/pbx/db/              │
└────────────────┘                         └──────────┬─────────────────┘
                                                      │
                                           ┌──────────▼─────────────────┐
                                           │   LocalPBXMonitor          │
                                           │   (local_pbx_monitor.py)   │
                                           │                            │
                                           │   • read_log(file, lines)  │
                                           │   • get_pjsip_config()     │
                                           │   • diagnose_webrtc(ext)   │
                                           │   • get_call_quality()     │
                                           │   • list_recordings()      │
                                           │   • query_astdb()          │
                                           └────────────────────────────┘

Constants defined in: arrowz/dev_constants.py
```

---

*Last Updated: February 2026*
