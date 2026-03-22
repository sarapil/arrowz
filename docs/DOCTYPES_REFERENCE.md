# Arrowz DocType Reference

> **Last Updated:** February 17, 2026  
> **Total DocTypes:** 17

---

## Configuration DocTypes

### Arrowz Settings
**Type:** Single  
**Table:** `tabArrowz Settings`

Global application configuration.

| Field | Type | Description |
|-------|------|-------------|
| enable_webrtc | Check | Enable WebRTC softphone |
| enable_ai_features | Check | Enable AI transcription/sentiment |
| enable_crm_integration | Check | Enable CRM linking |
| enable_recording | Check | Enable call recording |
| enable_sms | Check | Enable SMS features |
| default_country_code | Data | Default phone country code |
| sla_answer_time | Int | SLA answer time (seconds) |
| sla_hold_time | Int | SLA max hold time (seconds) |
| missed_call_alert | Check | Alert on missed calls |
| voicemail_enabled | Check | Enable voicemail |

---

### AZ Server Config
**Type:** Standard  
**Table:** `tabAZ Server Config`  
**Naming:** `field:server_name`

PBX and meeting server configuration.

| Field | Type | Description |
|-------|------|-------------|
| server_name | Data | Unique server identifier |
| server_type | Select | freepbx, asterisk, issabel, 3cx, openmeetings |
| is_active | Check | Server is active |
| is_default | Check | Default server for this type |
| display_name | Data | Human-readable name |
| host | Data | Server hostname/IP |
| port | Int | Server port |
| protocol | Select | http, https |
| websocket_url | Data | WebSocket URL (wss://) |
| sip_domain | Data | SIP domain |
| **WebRTC Section** |
| webrtc_enabled | Check | Enable WebRTC |
| stun_server | Data | STUN server URL |
| turn_server | Data | TURN server URL |
| turn_username | Data | TURN username |
| turn_password | Password | TURN password |
| **AMI Section** |
| ami_enabled | Check | Enable AMI |
| ami_host | Data | AMI hostname |
| ami_port | Int | AMI port (5038) |
| ami_username | Data | AMI username |
| ami_password | Password | AMI secret |
| **GraphQL Section** |
| graphql_enabled | Check | Enable GraphQL API |
| graphql_url | Data | GraphQL endpoint URL |
| graphql_client_id | Data | OAuth2 client ID |
| graphql_client_secret | Password | OAuth2 client secret |
| verify_ssl | Check | Verify SSL certificate |
| token_status | Data | Current token status |
| **SSH Section** |
| ssh_enabled | Check | Enable SSH access |
| ssh_host | Data | SSH hostname |
| ssh_port | Int | SSH port (22) |
| ssh_username | Data | SSH username |
| ssh_auth_type | Select | Password, Key |
| ssh_password | Password | SSH password |
| ssh_private_key | Text | SSH private key |
| **OpenMeetings Section** |
| om_enabled | Check | Enable OpenMeetings |
| om_url | Data | OpenMeetings URL |
| om_admin_user | Data | Admin username |
| om_admin_password | Password | Admin password |

---

### AZ Extension
**Type:** Standard  
**Table:** `tabAZ Extension`  
**Naming:** `format:EXT-{extension}`

User SIP extension configuration.

| Field | Type | Description |
|-------|------|-------------|
| extension | Data | Extension number (e.g., 1001) |
| user | Link:User | Linked Frappe user |
| display_name | Data | Caller ID name |
| email | Data | Email address |
| sip_password | Password | SIP password |
| extension_type | Select | SIP, WebRTC, Both |
| server | Link:AZ Server Config | Associated server |
| is_active | Check | Extension is active |
| is_primary | Check | Primary extension for user |
| enable_voicemail | Check | Enable voicemail |
| voicemail_pin | Data | Voicemail PIN |
| max_contacts | Int | Max concurrent registrations |
| sync_status | Select | Synced, Not Synced, Failed |
| last_synced | Datetime | Last sync timestamp |
| pbx_extension_id | Data | Extension ID in PBX |

---

## Call Management DocTypes

### AZ Call Log
**Type:** Standard  
**Table:** `tabAZ Call Log`  
**Naming:** `format:CALL-{YYYY}-{#####}`

Call detail records.

| Field | Type | Description |
|-------|------|-------------|
| extension | Data | Extension involved |
| phone_number | Data | Remote phone number |
| direction | Select | inbound, outbound, internal |
| status | Select | Initiated, Ringing, Answered, Completed, Missed, Failed |
| call_date | Date | Call date |
| call_time | Time | Call time |
| call_start | Datetime | Call start timestamp |
| call_end | Datetime | Call end timestamp |
| ringing_start | Datetime | Ringing start |
| answer_time | Datetime | Answer timestamp |
| duration | Int | Call duration (seconds) |
| ring_duration | Int | Ring time (seconds) |
| disposition | Select | answered, no_answer, busy, failed, voicemail |
| hangup_cause | Data | Hangup cause code |
| **CRM Linking** |
| party_type | Link:DocType | Contact, Lead, Customer, etc. |
| party | Dynamic Link | Linked document |
| linked_document | Data | Linked document name |
| **Recording** |
| has_recording | Check | Recording exists |
| recording_url | Data | Recording file URL |
| recording_duration | Int | Recording duration |
| **AI Features** |
| transcription | Text | AI transcription |
| sentiment | Select | Positive, Neutral, Negative |
| sentiment_score | Float | Sentiment score (-1 to 1) |
| ai_summary | Text | AI call summary |
| **Agent Info** |
| agent | Link:User | Agent who handled |
| queue | Data | Queue name |
| wait_time | Int | Queue wait time |
| **Notes** |
| notes | Text | Call notes |
| tags | Table MultiSelect | Call tags |

---

### AZ Call Transfer Log
**Type:** Standard  
**Table:** `tabAZ Call Transfer Log`

Call transfer records.

| Field | Type | Description |
|-------|------|-------------|
| call_log | Link:AZ Call Log | Original call |
| transfer_type | Select | blind, attended |
| from_extension | Data | Source extension |
| to_extension | Data | Target extension |
| transfer_time | Datetime | Transfer timestamp |
| status | Select | Completed, Failed |
| consultation_duration | Int | Attended consult duration |

---

## Routing DocTypes

### AZ Trunk
**Type:** Standard  
**Table:** `tabAZ Trunk`

SIP trunk configuration.

| Field | Type | Description |
|-------|------|-------------|
| trunk_name | Data | Trunk identifier |
| trunk_type | Select | pjsip, sip, iax2, dahdi |
| server | Link:AZ Server Config | Associated server |
| host | Data | Provider hostname |
| username | Data | Auth username |
| password | Password | Auth password |
| port | Int | SIP port |
| codecs | Data | Allowed codecs |
| max_channels | Int | Concurrent channels |
| is_active | Check | Trunk is active |

---

### AZ Inbound Route
**Type:** Standard  
**Table:** `tabAZ Inbound Route`

Inbound call routing rules.

| Field | Type | Description |
|-------|------|-------------|
| route_name | Data | Route name |
| did_number | Data | DID number pattern |
| caller_id_pattern | Data | Caller ID pattern |
| destination_type | Select | extension, queue, ivr, voicemail |
| destination | Data | Destination value |
| time_condition | Data | Time-based routing |
| priority | Int | Route priority |
| is_active | Check | Route is active |

---

### AZ Outbound Route
**Type:** Standard  
**Table:** `tabAZ Outbound Route`

Outbound call routing rules.

| Field | Type | Description |
|-------|------|-------------|
| route_name | Data | Route name |
| dial_pattern | Data | Dial pattern |
| prefix | Data | Prefix to add |
| strip_digits | Int | Digits to strip |
| trunk | Link:AZ Trunk | Trunk to use |
| failover_trunk | Link:AZ Trunk | Failover trunk |
| priority | Int | Route priority |
| is_active | Check | Route is active |

---

## Omni-Channel DocTypes

### AZ Omni Provider
**Type:** Standard  
**Table:** `tabAZ Omni Provider`

Channel provider definitions.

| Field | Type | Description |
|-------|------|-------------|
| provider_name | Data | Provider identifier |
| provider_type | Select | whatsapp_cloud, telegram, facebook, viber |
| display_name | Data | Display name |
| capabilities | JSON | Supported features |
| rate_limit | Int | Messages per minute |
| is_active | Check | Provider is active |

---

### AZ Omni Channel
**Type:** Standard  
**Table:** `tabAZ Omni Channel`

Channel instance configuration.

| Field | Type | Description |
|-------|------|-------------|
| channel_name | Data | Channel identifier |
| provider | Link:AZ Omni Provider | Provider |
| phone_number | Data | Channel phone/ID |
| display_name | Data | Display name |
| api_key | Password | API key/token |
| api_secret | Password | API secret |
| webhook_url | Data | Webhook endpoint |
| webhook_secret | Password | Webhook verification |
| working_hours | JSON | Business hours |
| auto_reply | Check | Enable auto-reply |
| auto_reply_message | Text | Auto-reply text |
| is_active | Check | Channel is active |

---

### AZ Conversation Session
**Type:** Standard  
**Table:** `tabAZ Conversation Session`  
**Naming:** `format:CONV-{YYYY}-{#####}`

Conversation threads.

| Field | Type | Description |
|-------|------|-------------|
| channel | Link:AZ Omni Channel | Source channel |
| contact_phone | Data | Contact phone/ID |
| contact_name | Data | Contact name |
| status | Select | Active, Waiting, Closed |
| assigned_to | Link:User | Assigned agent |
| last_message | Datetime | Last message time |
| session_start | Datetime | Session start |
| session_end | Datetime | Session end |
| message_count | Int | Message count |
| unread_count | Int | Unread messages |
| **CRM Linking** |
| party_type | Link:DocType | Contact, Lead, etc. |
| party | Dynamic Link | Linked document |
| **SLA** |
| first_response_time | Int | First response (seconds) |
| resolution_time | Int | Total resolution time |
| sla_breached | Check | SLA was breached |
| **Messages** |
| messages | Table:AZ Conversation Message | Message list |

---

### AZ Conversation Message
**Type:** Child Table  
**Table:** `tabAZ Conversation Message`

Individual messages.

| Field | Type | Description |
|-------|------|-------------|
| message_id | Data | External message ID |
| direction | Select | inbound, outbound |
| message_type | Select | text, image, video, document, audio, template |
| content | Text | Message content |
| media_url | Data | Media URL |
| media_type | Data | Media MIME type |
| timestamp | Datetime | Message timestamp |
| status | Select | sent, delivered, read, failed |
| sender | Data | Sender identifier |
| error_message | Data | Error if failed |

---

## SMS DocTypes

### AZ SMS Provider
**Type:** Standard  
**Table:** `tabAZ SMS Provider`

SMS gateway configuration.

| Field | Type | Description |
|-------|------|-------------|
| provider_name | Data | Provider identifier |
| provider_type | Select | twilio, vonage, messagebird, plivo, infobip, clicksend, custom |
| display_name | Data | Display name |
| api_endpoint | Data | API URL |
| api_key | Password | API key |
| api_secret | Password | API secret |
| sender_id | Data | Default sender ID |
| is_default | Check | Default provider |
| is_active | Check | Provider is active |

---

### AZ SMS Message
**Type:** Standard  
**Table:** `tabAZ SMS Message`  
**Naming:** `format:SMS-{YYYY}-{#####}`

SMS message records.

| Field | Type | Description |
|-------|------|-------------|
| provider | Link:AZ SMS Provider | Provider used |
| direction | Select | outbound, inbound |
| from_number | Data | Sender number |
| to_number | Data | Recipient number |
| message | Text | Message content |
| status | Select | queued, sent, delivered, failed |
| external_id | Data | Provider message ID |
| sent_at | Datetime | Send timestamp |
| delivered_at | Datetime | Delivery timestamp |
| error_message | Data | Error if failed |
| **CRM Linking** |
| party_type | Link:DocType | Contact, Lead, etc. |
| party | Dynamic Link | Linked document |
| cost | Currency | Message cost |

---

## Meeting DocTypes

### AZ Meeting Room
**Type:** Standard  
**Table:** `tabAZ Meeting Room`  
**Naming:** `format:ROOM-{YYYY}-{#####}`

Video meeting rooms.

| Field | Type | Description |
|-------|------|-------------|
| room_name | Data | Room name |
| room_type | Select | conference, webinar, interview, presentation |
| server | Link:AZ Server Config | OpenMeetings server |
| external_room_id | Data | Room ID in OpenMeetings |
| status | Select | Active, Scheduled, Ended, Cancelled |
| scheduled_start | Datetime | Scheduled start time |
| scheduled_end | Datetime | Scheduled end time |
| actual_start | Datetime | Actual start |
| actual_end | Datetime | Actual end |
| max_participants | Int | Max allowed users |
| allow_recording | Check | Allow recording |
| is_public | Check | Public room |
| password | Password | Room password |
| join_url | Data | Join URL |
| moderator_url | Data | Moderator URL |
| **Linking** |
| reference_doctype | Link:DocType | Linked DocType |
| reference_name | Dynamic Link | Linked document |
| **Participants** |
| participants | Table:AZ Meeting Participant | Participant list |
| **Recordings** |
| recordings | Table:AZ Meeting Recording | Recording list |

---

### AZ Meeting Participant
**Type:** Child Table  
**Table:** `tabAZ Meeting Participant`

Meeting participants.

| Field | Type | Description |
|-------|------|-------------|
| user | Link:User | Frappe user |
| email | Data | Participant email |
| name | Data | Participant name |
| role | Select | moderator, presenter, attendee |
| invited_at | Datetime | Invitation time |
| joined_at | Datetime | Join time |
| left_at | Datetime | Leave time |
| status | Select | invited, joined, left, declined |

---

### AZ Meeting Recording
**Type:** Child Table  
**Table:** `tabAZ Meeting Recording`

Meeting recordings.

| Field | Type | Description |
|-------|------|-------------|
| recording_id | Data | Recording ID |
| recording_url | Data | Recording URL |
| duration | Int | Duration (seconds) |
| file_size | Int | File size (bytes) |
| format | Data | File format |
| created_at | Datetime | Recording timestamp |

---

*Reference document for Arrowz DocTypes.*
