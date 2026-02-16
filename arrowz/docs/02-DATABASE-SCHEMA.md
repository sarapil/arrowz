# Arrowz Database Schema
## Complete DocType Specifications

---

## 📊 DocType Overview

| DocType | Type | Purpose |
|---------|------|---------|
| Arrowz Settings | Single | Global configuration |
| AZ Server Config | Regular | PBX server connections |
| AZ Extension | Regular | SIP extensions per user |
| AZ Call Log | Regular | Call records |
| AZ Sentiment Log | Regular | Sentiment data points |
| AZ Presence Log | Regular | User presence history |

---

## 1️⃣ Arrowz Settings (Single DocType)

**Purpose**: Store global application settings

### Field Specifications

```yaml
doctype: Arrowz Settings
is_single: true
module: Arrowz

sections:
  - AI Configuration
  - Call Quality Monitoring
  - CRM Integration
  - Notifications
  - Recording Settings

fields:
  # === AI Configuration ===
  - fieldname: enable_ai_features
    fieldtype: Check
    label: Enable AI Features
    default: 0
    description: Master switch for all AI functionality
    
  - fieldname: openai_api_key
    fieldtype: Password
    label: OpenAI API Key
    depends_on: enable_ai_features
    mandatory_depends_on: enable_ai_features
    length: 200
    
  - fieldname: ai_model
    fieldtype: Select
    label: AI Model
    options:
      - gpt-4o
      - gpt-4o-mini
      - gpt-4
      - gpt-3.5-turbo
    default: gpt-4o-mini
    depends_on: enable_ai_features
    
  - fieldname: enable_transcription
    fieldtype: Check
    label: Enable Live Transcription
    default: 0
    depends_on: enable_ai_features
    
  - fieldname: transcription_language
    fieldtype: Select
    label: Transcription Language
    options:
      - en-US
      - ar-SA
      - es-ES
      - fr-FR
      - de-DE
      # Add more as needed
    default: en-US
    depends_on: enable_transcription
    
  - fieldname: enable_sentiment
    fieldtype: Check
    label: Enable Sentiment Analysis
    default: 0
    depends_on: enable_ai_features
    
  - fieldname: sentiment_update_interval
    fieldtype: Int
    label: Sentiment Update Interval (seconds)
    default: 5
    depends_on: enable_sentiment
    description: How often to analyze sentiment during call
    
  - fieldname: enable_coaching
    fieldtype: Check
    label: Enable Call Coaching
    default: 0
    depends_on: enable_ai_features
    
  - fieldname: max_coaching_suggestions
    fieldtype: Int
    label: Max Coaching Suggestions per Call
    default: 5
    depends_on: enable_coaching

  # === Call Quality Monitoring ===
  - fieldname: enable_quality_monitoring
    fieldtype: Check
    label: Enable Quality Monitoring
    default: 1
    
  - fieldname: min_quality_threshold
    fieldtype: Int
    label: Minimum Quality Score (%)
    default: 70
    depends_on: enable_quality_monitoring
    
  - fieldname: packet_loss_threshold
    fieldtype: Float
    label: Packet Loss Alert Threshold (%)
    default: 5.0
    depends_on: enable_quality_monitoring
    
  - fieldname: jitter_threshold
    fieldtype: Float
    label: Jitter Alert Threshold (ms)
    default: 30.0
    depends_on: enable_quality_monitoring

  # === CRM Integration ===
  - fieldname: enable_crm_integration
    fieldtype: Check
    label: Enable CRM Integration
    default: 1
    
  - fieldname: auto_create_leads
    fieldtype: Check
    label: Auto-create Leads from Unknown Callers
    default: 0
    depends_on: enable_crm_integration
    
  - fieldname: auto_link_contacts
    fieldtype: Check
    label: Auto-link Calls to Contacts
    default: 1
    depends_on: enable_crm_integration
    
  - fieldname: auto_popup_customer_info
    fieldtype: Check
    label: Show Customer Popup on Incoming Calls
    default: 1
    depends_on: enable_crm_integration

  # === Notifications ===
  - fieldname: enable_call_notifications
    fieldtype: Check
    label: Enable Call Notifications
    default: 1
    
  - fieldname: notification_sound
    fieldtype: Select
    label: Notification Sound
    options:
      - default
      - bell
      - chime
      - silent
    default: default
    
  - fieldname: alert_on_negative_sentiment
    fieldtype: Check
    label: Alert on Negative Sentiment
    default: 1
    depends_on: enable_sentiment

  # === Recording ===
  - fieldname: enable_call_recording
    fieldtype: Check
    label: Enable Call Recording
    default: 0
    
  - fieldname: recording_storage
    fieldtype: Select
    label: Recording Storage Location
    options:
      - Local
      - S3
      - Google Cloud
      - Azure
    default: Local
    depends_on: enable_call_recording
    
  - fieldname: recording_retention_days
    fieldtype: Int
    label: Recording Retention (Days)
    default: 90
    depends_on: enable_call_recording
```

---

## 2️⃣ AZ Server Config

**Purpose**: Configure connections to PBX servers

### Field Specifications

```yaml
doctype: AZ Server Config
autoname: field:server_name
module: Arrowz

sections:
  - Basic Information
  - Connection Settings
  - Authentication
  - FreePBX/Asterisk Settings
  - SIP Settings
  - AI Configuration
  - Security
  - Status

fields:
  # === Basic Information ===
  - fieldname: server_name
    fieldtype: Data
    label: Server Name
    reqd: 1
    unique: 1
    in_list_view: 1
    
  - fieldname: server_type
    fieldtype: Select
    label: Server Type
    reqd: 1
    in_list_view: 1
    options:
      - FreePBX
      - Asterisk
      - Twilio
      - Vonage
      - Custom SIP
    
  - fieldname: display_name
    fieldtype: Data
    label: Display Name
    
  - fieldname: is_active
    fieldtype: Check
    label: Is Active
    default: 1
    in_list_view: 1
    
  - fieldname: is_default
    fieldtype: Check
    label: Is Default Server
    
  - fieldname: priority
    fieldtype: Int
    label: Priority (lower = higher priority)
    default: 5

  # === Connection Settings ===
  - fieldname: host
    fieldtype: Data
    label: Host/IP Address
    reqd: 1
    
  - fieldname: port
    fieldtype: Int
    label: Port
    default: 8089
    
  - fieldname: protocol
    fieldtype: Select
    label: Protocol
    options:
      - WSS
      - WS
      - HTTPS
      - HTTP
    default: WSS
    
  - fieldname: websocket_url
    fieldtype: Data
    label: WebSocket URL
    description: "Full URL e.g., wss://pbx.example.com:8089/ws"
    
  - fieldname: stun_server
    fieldtype: Data
    label: STUN Server
    default: "stun:stun.l.google.com:19302"
    
  - fieldname: turn_server
    fieldtype: Data
    label: TURN Server (optional)
    
  - fieldname: turn_username
    fieldtype: Data
    label: TURN Username
    depends_on: turn_server
    
  - fieldname: turn_password
    fieldtype: Password
    label: TURN Password
    depends_on: turn_server

  # === FreePBX/AMI Settings ===
  - fieldname: ami_enabled
    fieldtype: Check
    label: Enable AMI
    default: 0
    
  - fieldname: ami_host
    fieldtype: Data
    label: AMI Host
    depends_on: ami_enabled
    
  - fieldname: ami_port
    fieldtype: Int
    label: AMI Port
    default: 5038
    depends_on: ami_enabled
    
  - fieldname: ami_username
    fieldtype: Data
    label: AMI Username
    depends_on: ami_enabled
    
  - fieldname: ami_password
    fieldtype: Password
    label: AMI Password
    depends_on: ami_enabled

  # === SIP Settings ===
  - fieldname: sip_domain
    fieldtype: Data
    label: SIP Domain
    
  - fieldname: sip_proxy
    fieldtype: Data
    label: SIP Proxy (optional)
    
  - fieldname: sip_transport
    fieldtype: Select
    label: SIP Transport
    options:
      - WSS
      - WS
      - TLS
      - UDP
      - TCP
    default: WSS
    
  - fieldname: webrtc_enabled
    fieldtype: Check
    label: WebRTC Enabled
    default: 1

  # === Status (Read-only) ===
  - fieldname: connection_status
    fieldtype: Select
    label: Connection Status
    options:
      - Unknown
      - Connected
      - Disconnected
      - Error
    default: Unknown
    read_only: 1
    
  - fieldname: last_health_check
    fieldtype: Datetime
    label: Last Health Check
    read_only: 1
    
  - fieldname: last_error
    fieldtype: Small Text
    label: Last Error Message
    read_only: 1
```

---

## 3️⃣ AZ Extension

**Purpose**: Configure SIP extensions for users

### Field Specifications

```yaml
doctype: AZ Extension
autoname: field:extension
module: Arrowz

sections:
  - Basic Information
  - Authentication
  - Features
  - Advanced Settings
  - Statistics

fields:
  # === Basic Information ===
  - fieldname: extension
    fieldtype: Data
    label: Extension Number
    reqd: 1
    unique: 1
    in_list_view: 1
    description: "e.g., 1001, 2050"
    
  - fieldname: extension_name
    fieldtype: Data
    label: Display Name
    in_list_view: 1
    
  - fieldname: user
    fieldtype: Link
    label: Assigned User
    options: User
    in_list_view: 1
    
  - fieldname: status
    fieldtype: Select
    label: Status
    options:
      - Active
      - Inactive
      - Suspended
    default: Active
    in_list_view: 1
    
  - fieldname: extension_type
    fieldtype: Select
    label: Extension Type
    options:
      - WebRTC
      - SIP
      - IAX2
    default: WebRTC
    
  - fieldname: server
    fieldtype: Link
    label: Server
    options: AZ Server Config

  # === Authentication ===
  - fieldname: secret
    fieldtype: Password
    label: SIP Secret/Password
    reqd: 1
    
  - fieldname: encryption_type
    fieldtype: Select
    label: Password Encryption
    options:
      - DTLS-SRTP
      - SDES
      - None
    default: DTLS-SRTP
    
  - fieldname: transport
    fieldtype: Select
    label: Transport Protocol
    options:
      - WSS
      - WS
      - TLS
      - UDP
      - TCP
    default: WSS

  # === Features ===
  - fieldname: enable_recording
    fieldtype: Check
    label: Enable Call Recording
    default: 0
    
  - fieldname: enable_voicemail
    fieldtype: Check
    label: Enable Voicemail
    default: 1
    
  - fieldname: enable_call_waiting
    fieldtype: Check
    label: Enable Call Waiting
    default: 1
    
  - fieldname: enable_call_forwarding
    fieldtype: Check
    label: Enable Call Forwarding
    default: 0
    
  - fieldname: forward_number
    fieldtype: Data
    label: Forward To Number
    depends_on: enable_call_forwarding
    
  - fieldname: max_concurrent_calls
    fieldtype: Int
    label: Max Concurrent Calls
    default: 2

  # === Advanced ===
  - fieldname: codecs
    fieldtype: Data
    label: Codec Preferences
    default: "opus,ulaw,alaw"
    description: "Comma-separated codec list"
    
  - fieldname: dtmf_mode
    fieldtype: Select
    label: DTMF Mode
    options:
      - rfc2833
      - inband
      - info
      - auto
    default: rfc2833
    
  - fieldname: ring_timeout
    fieldtype: Int
    label: Ring Timeout (seconds)
    default: 30

  # === Statistics (Read-only) ===
  - fieldname: total_calls_inbound
    fieldtype: Int
    label: Total Inbound Calls
    read_only: 1
    default: 0
    
  - fieldname: total_calls_outbound
    fieldtype: Int
    label: Total Outbound Calls
    read_only: 1
    default: 0
    
  - fieldname: total_duration
    fieldtype: Int
    label: Total Call Duration (seconds)
    read_only: 1
    default: 0
    
  - fieldname: last_call_time
    fieldtype: Datetime
    label: Last Call Time
    read_only: 1
    
  - fieldname: registration_status
    fieldtype: Select
    label: Registration Status
    options:
      - Unknown
      - Registered
      - Unregistered
      - Failed
    default: Unknown
    read_only: 1
```

---

## 4️⃣ AZ Call Log

**Purpose**: Store detailed call records

### Field Specifications

```yaml
doctype: AZ Call Log
autoname: naming_series
naming_series: CALL-.YYYY.-.#####
module: Arrowz

sections:
  - Call Information
  - Timing
  - Parties
  - AI Analysis
  - Quality Metrics
  - CRM Links
  - Notes

fields:
  # === Call Information ===
  - fieldname: session_id
    fieldtype: Data
    label: Session ID
    unique: 1
    
  - fieldname: direction
    fieldtype: Select
    label: Direction
    options:
      - Inbound
      - Outbound
      - Internal
    reqd: 1
    in_list_view: 1
    
  - fieldname: status
    fieldtype: Select
    label: Status
    options:
      - Completed
      - Missed
      - Busy
      - Failed
      - Voicemail
      - Transferred
    default: Completed
    in_list_view: 1
    
  - fieldname: call_type
    fieldtype: Select
    label: Call Type
    options:
      - Voice
      - Video
      - Conference
    default: Voice

  # === Timing ===
  - fieldname: start_time
    fieldtype: Datetime
    label: Start Time
    reqd: 1
    in_list_view: 1
    
  - fieldname: answer_time
    fieldtype: Datetime
    label: Answer Time
    
  - fieldname: end_time
    fieldtype: Datetime
    label: End Time
    
  - fieldname: duration
    fieldtype: Int
    label: Duration (seconds)
    in_list_view: 1
    
  - fieldname: ring_duration
    fieldtype: Int
    label: Ring Duration (seconds)
    
  - fieldname: hold_duration
    fieldtype: Int
    label: Hold Duration (seconds)

  # === Parties ===
  - fieldname: caller_number
    fieldtype: Data
    label: Caller Number
    in_list_view: 1
    
  - fieldname: callee_id
    fieldtype: Data
    label: Callee ID
    in_list_view: 1
    
  - fieldname: caller_name
    fieldtype: Data
    label: Caller Name
    
  - fieldname: called_name
    fieldtype: Data
    label: Called Name
    
  - fieldname: user
    fieldtype: Link
    label: Agent/User
    options: User
    in_list_view: 1
    
  - fieldname: extension
    fieldtype: Link
    label: Extension
    options: AZ Extension

  # === AI Analysis ===
  - fieldname: ai_sentiment
    fieldtype: Select
    label: Call Sentiment
    options:
      - positive
      - neutral
      - negative
      - mixed
    in_list_view: 1
    
  - fieldname: sentiment_score
    fieldtype: Float
    label: Sentiment Score (0-1)
    
  - fieldname: ai_summary
    fieldtype: Text
    label: AI-Generated Summary
    
  - fieldname: ai_key_topics
    fieldtype: Data
    label: Key Topics
    description: "Comma-separated topics"
    
  - fieldname: ai_action_items
    fieldtype: Small Text
    label: Action Items
    
  - fieldname: call_transcript
    fieldtype: Long Text
    label: Call Transcript

  # === Quality Metrics ===
  - fieldname: quality_score
    fieldtype: Float
    label: Quality Score (0-100)
    
  - fieldname: packet_loss
    fieldtype: Float
    label: Packet Loss (%)
    
  - fieldname: jitter
    fieldtype: Float
    label: Jitter (ms)
    
  - fieldname: latency
    fieldtype: Float
    label: Latency (ms)

  # === CRM Links ===
  - fieldname: contact
    fieldtype: Link
    label: Contact
    options: Contact
    
  - fieldname: lead
    fieldtype: Link
    label: Lead
    options: Lead
    
  - fieldname: customer
    fieldtype: Link
    label: Customer
    options: Customer
    
  - fieldname: opportunity
    fieldtype: Link
    label: Opportunity
    options: Opportunity
    
  - fieldname: company
    fieldtype: Data
    label: Company Name

  # === Notes ===
  - fieldname: notes
    fieldtype: Text
    label: Agent Notes
    
  - fieldname: outcome
    fieldtype: Select
    label: Call Outcome
    options:
      - ""
      - Successful
      - Callback Required
      - Not Interested
      - Wrong Number
      - Voicemail Left
      - Transferred
```

---

## 5️⃣ AZ Sentiment Log

**Purpose**: Track sentiment changes during calls

```yaml
doctype: AZ Sentiment Log
autoname: hash
module: Arrowz

fields:
  - fieldname: call_log
    fieldtype: Link
    label: Call Log
    options: AZ Call Log
    reqd: 1
    
  - fieldname: timestamp
    fieldtype: Datetime
    label: Timestamp
    reqd: 1
    
  - fieldname: sentiment_label
    fieldtype: Select
    label: Sentiment
    options:
      - positive
      - neutral
      - negative
    reqd: 1
    
  - fieldname: sentiment_score
    fieldtype: Float
    label: Score (0-1)
    
  - fieldname: speaker
    fieldtype: Select
    label: Speaker
    options:
      - agent
      - customer
      - unknown
    
  - fieldname: text_sample
    fieldtype: Data
    label: Text Sample
```

---

## 🔗 Relationships Diagram

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   User ─────────────┐                                     │
│     │               │                                     │
│     ▼               ▼                                     │
│   AZ Extension ─── AZ Call Log ─── AZ Sentiment Log      │
│     │               │                                     │
│     ▼               │                                     │
│   AZ Server Config  │                                     │
│                     │                                     │
│                     ├──► Contact                          │
│                     ├──► Lead                             │
│                     ├──► Customer                         │
│                     └──► Opportunity                      │
│                                                            │
│   Arrowz Settings (Single - Global Configuration)         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 📝 Database Indexes

### Recommended Indexes

```sql
-- AZ Call Log
CREATE INDEX idx_call_log_start_time ON `tabAZ Call Log` (start_time);
CREATE INDEX idx_call_log_user ON `tabAZ Call Log` (user);
CREATE INDEX idx_call_log_contact ON `tabAZ Call Log` (contact);
CREATE INDEX idx_call_log_caller ON `tabAZ Call Log` (caller_number);
CREATE INDEX idx_call_log_callee ON `tabAZ Call Log` (callee_id);

-- AZ Extension
CREATE INDEX idx_extension_user ON `tabAZ Extension` (user);
CREATE INDEX idx_extension_status ON `tabAZ Extension` (status);

-- AZ Sentiment Log
CREATE INDEX idx_sentiment_call ON `tabAZ Sentiment Log` (call_log);
CREATE INDEX idx_sentiment_time ON `tabAZ Sentiment Log` (timestamp);

-- AZ SMS Message
CREATE INDEX idx_sms_timestamp ON `tabAZ SMS Message` (timestamp);
CREATE INDEX idx_sms_direction ON `tabAZ SMS Message` (direction);
CREATE INDEX idx_sms_status ON `tabAZ SMS Message` (status);
```

---

## 7️⃣ AZ SMS Message (جديد)

**Purpose**: Store SMS messages sent and received

### Field Specifications

```yaml
doctype: AZ SMS Message
autoname: format:SMS-{####}
module: Arrowz

sections:
  - Message Details
  - Routing
  - Status
  - Linked Records

fields:
  # === Message Details ===
  - fieldname: direction
    fieldtype: Select
    label: Direction
    options:
      - Outbound
      - Inbound
    reqd: 1
    in_list_view: 1
    
  - fieldname: from_number
    fieldtype: Data
    label: From Number
    reqd: 1
    in_list_view: 1
    
  - fieldname: to_number
    fieldtype: Data
    label: To Number
    reqd: 1
    in_list_view: 1
    
  - fieldname: message_body
    fieldtype: Text
    label: Message Body
    reqd: 1
    
  - fieldname: timestamp
    fieldtype: Datetime
    label: Timestamp
    default: now
    reqd: 1
    in_list_view: 1

  # === Routing ===
  - fieldname: sms_provider
    fieldtype: Link
    label: SMS Provider
    options: AZ SMS Provider
    
  - fieldname: provider_message_id
    fieldtype: Data
    label: Provider Message ID
    description: External ID from provider
    
  - fieldname: server
    fieldtype: Link
    label: Server
    options: AZ Server Config

  # === Status ===
  - fieldname: status
    fieldtype: Select
    label: Status
    options:
      - Pending
      - Sent
      - Delivered
      - Failed
      - Received
    default: Pending
    in_list_view: 1
    
  - fieldname: error_message
    fieldtype: Small Text
    label: Error Message
    depends_on: eval:doc.status=='Failed'
    
  - fieldname: delivered_at
    fieldtype: Datetime
    label: Delivered At

  # === Linked Records ===
  - fieldname: linked_doctype
    fieldtype: Link
    label: Linked DocType
    options: DocType
    
  - fieldname: linked_docname
    fieldtype: Dynamic Link
    label: Linked Record
    options: linked_doctype
    
  - fieldname: user
    fieldtype: Link
    label: User
    options: User
    default: __user
```

---

## 8️⃣ AZ SMS Provider (جديد)

**Purpose**: Configure SMS provider connections (provider-agnostic)

### Field Specifications

```yaml
doctype: AZ SMS Provider
autoname: field:provider_name
module: Arrowz

sections:
  - Basic Information
  - API Configuration
  - Sender Settings
  - Status

fields:
  # === Basic Information ===
  - fieldname: provider_name
    fieldtype: Data
    label: Provider Name
    reqd: 1
    unique: 1
    in_list_view: 1
    
  - fieldname: provider_type
    fieldtype: Select
    label: Provider Type
    options:
      - Twilio
      - MessageBird
      - Nexmo/Vonage
      - Plivo
      - AWS SNS
      - Custom HTTP
    reqd: 1
    in_list_view: 1
    
  - fieldname: is_active
    fieldtype: Check
    label: Is Active
    default: 1
    in_list_view: 1
    
  - fieldname: is_default
    fieldtype: Check
    label: Is Default Provider

  # === API Configuration ===
  - fieldname: api_endpoint
    fieldtype: Data
    label: API Endpoint URL
    description: Required for Custom HTTP provider
    
  - fieldname: api_key
    fieldtype: Password
    label: API Key / Account SID
    reqd: 1
    
  - fieldname: api_secret
    fieldtype: Password
    label: API Secret / Auth Token
    reqd: 1
    
  - fieldname: webhook_url
    fieldtype: Data
    label: Webhook URL (auto-generated)
    read_only: 1
    description: URL for delivery receipts

  # === Sender Settings ===
  - fieldname: default_sender_id
    fieldtype: Data
    label: Default Sender ID / From Number
    reqd: 1
    
  - fieldname: sender_ids
    fieldtype: Table
    label: Additional Sender IDs
    options: AZ SMS Sender ID

  # === Status ===
  - fieldname: last_used
    fieldtype: Datetime
    label: Last Used
    read_only: 1
    
  - fieldname: messages_sent
    fieldtype: Int
    label: Messages Sent (Total)
    read_only: 1
    default: 0
```

---

## 9️⃣ AZ Call Transfer Log (جديد)

**Purpose**: Track call transfers for reporting and auditing

### Field Specifications

```yaml
doctype: AZ Call Transfer Log
autoname: format:TRF-{####}
module: Arrowz

fields:
  - fieldname: call_log
    fieldtype: Link
    label: Original Call
    options: AZ Call Log
    reqd: 1
    in_list_view: 1
    
  - fieldname: transfer_type
    fieldtype: Select
    label: Transfer Type
    options:
      - Attended
      - Blind
    reqd: 1
    in_list_view: 1
    
  - fieldname: from_extension
    fieldtype: Data
    label: From Extension
    reqd: 1
    
  - fieldname: from_user
    fieldtype: Link
    label: From User
    options: User
    
  - fieldname: to_extension
    fieldtype: Data
    label: To Extension
    reqd: 1
    in_list_view: 1
    
  - fieldname: to_user
    fieldtype: Link
    label: To User
    options: User
    
  - fieldname: transfer_time
    fieldtype: Datetime
    label: Transfer Time
    default: now
    in_list_view: 1
    
  - fieldname: was_successful
    fieldtype: Check
    label: Successful
    default: 1
    
  - fieldname: failure_reason
    fieldtype: Data
    label: Failure Reason
    depends_on: eval:!doc.was_successful
    
  - fieldname: consult_duration
    fieldtype: Duration
    label: Consultation Duration
    description: For attended transfers only
    depends_on: eval:doc.transfer_type=='Attended'
```

---

## 🔟 AZ Server Config - Additional Fields for GraphQL

**Purpose**: Extend AZ Server Config with GraphQL/fwconsole settings

### Additional Fields (add to existing AZ Server Config)

```yaml
# Add to AZ Server Config under new section "FreePBX API"

  # === FreePBX GraphQL API ===
  - fieldname: graphql_section
    fieldtype: Section Break
    label: FreePBX GraphQL API
    
  - fieldname: graphql_enabled
    fieldtype: Check
    label: Enable GraphQL API
    default: 0
    
  - fieldname: graphql_url
    fieldtype: Data
    label: GraphQL Endpoint URL
    depends_on: graphql_enabled
    description: "e.g., https://pbx.example.com/admin/api/api/gql"
    
  - fieldname: graphql_client_id
    fieldtype: Data
    label: OAuth2 Client ID
    depends_on: graphql_enabled
    description: "Client ID from FreePBX API Applications"
    
  - fieldname: graphql_client_secret
    fieldtype: Password
    label: OAuth2 Client Secret
    depends_on: graphql_enabled
    description: "Client Secret (stored securely)"
    
  - fieldname: verify_ssl
    fieldtype: Check
    label: Verify SSL Certificate
    default: 0
    depends_on: graphql_enabled
    description: "Disable for self-signed certificates"
    
  - fieldname: token_status
    fieldtype: Data
    label: Token Status
    read_only: 1
    description: "Auto-updated by system"
    
  - fieldname: token_expires_at
    fieldtype: Datetime
    label: Token Expires At
    read_only: 1
    
  # === fwconsole SSH Access ===
  - fieldname: fwconsole_section
    fieldtype: Section Break
    label: fwconsole SSH Access
    
  - fieldname: ssh_enabled
    fieldtype: Check
    label: Enable SSH for fwconsole
    default: 0
    description: Used for Trunks/Outbound Routes (not in GraphQL)
    
  - fieldname: ssh_host
    fieldtype: Data
    label: SSH Host
    depends_on: ssh_enabled
    
  - fieldname: ssh_port
    fieldtype: Int
    label: SSH Port
    default: 22
    depends_on: ssh_enabled
    
  - fieldname: ssh_username
    fieldtype: Data
    label: SSH Username
    depends_on: ssh_enabled
    
  - fieldname: ssh_auth_type
    fieldtype: Select
    label: SSH Authentication
    options:
      - Password
      - Private Key
    default: Private Key
    depends_on: ssh_enabled
    
  - fieldname: ssh_password
    fieldtype: Password
    label: SSH Password
    depends_on: eval:doc.ssh_enabled && doc.ssh_auth_type=='Password'
    
  - fieldname: ssh_private_key
    fieldtype: Code
    label: SSH Private Key
    options: text
    depends_on: eval:doc.ssh_enabled && doc.ssh_auth_type=='Private Key'
```

---

## 🔗 Updated Relationships Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   User ─────────────┐                                                  │
│     │               │                                                  │
│     ▼               ▼                                                  │
│   AZ Extension ─── AZ Call Log ─── AZ Sentiment Log                   │
│     │               │       │                                          │
│     ▼               │       └───► AZ Call Transfer Log                │
│   AZ Server Config  │                                                  │
│     │               ├──► Contact                                       │
│     │               ├──► Lead                                          │
│     │               ├──► Customer                                      │
│     │               └──► Opportunity                                   │
│     │                                                                  │
│     └── GraphQL API + fwconsole (SSH)                                  │
│                                                                         │
│   AZ SMS Provider ──► AZ SMS Message ──► Contact/Lead/Customer        │
│                                                                         │
│   Arrowz Settings (Single - Global Configuration)                      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*Next: See `03-API-REFERENCE.md` for API specifications*



*Next: See `03-API-REFERENCE.md` for API specifications*
