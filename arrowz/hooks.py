"""
Arrowz Hooks Configuration

This file defines how Arrowz integrates with Frappe Framework.
"""

app_name = "arrowz"
app_title = "Arrowz"
app_publisher = "Arrowz Team"
app_description = "Enterprise VoIP Call Management with AI"
app_version = "1.0.0"
app_icon = "octicon octicon-broadcast"
app_color = "#5e35b1"
app_email = "support@arrowz.io"
app_license = "MIT"

# Required Apps
required_apps = ["frappe"]

# Optional: Recommended apps for full functionality
# required_apps = ["frappe", "erpnext"]

# -----------------------------------------------------------------------------
# Assets to include in every page
# -----------------------------------------------------------------------------

# Include JS in all pages
app_include_js = [
    "/assets/arrowz/js/lib/jssip.min.js",
    "/assets/arrowz/js/arrowz.js",
    "/assets/arrowz/js/phone_actions.js",
    "/assets/arrowz/js/softphone_v2.js",
    "/assets/arrowz/js/screen_pop.js",
    "/assets/arrowz/js/omni_panel.js",
    "/assets/arrowz/js/omni_doctype_extension.js"
]

# Include CSS in all pages
app_include_css = [
    "/assets/arrowz/css/arrowz.css",
    "/assets/arrowz/css/phone_actions.css",
    "/assets/arrowz/css/softphone.css",
    "/assets/arrowz/css/screen_pop.css",
    "/assets/arrowz/css/omni_panel.css"
]

# -----------------------------------------------------------------------------
# DocType-specific JavaScript
# -----------------------------------------------------------------------------

doctype_js = {
    "Contact": "public/js/contact.js",
    "Lead": "public/js/lead.js",
    "Customer": "public/js/customer.js",
    "Opportunity": "public/js/opportunity.js",
    "Issue": "public/js/issue.js",
    "Prospect": "public/js/prospect.js",
    "Supplier": "public/js/supplier.js",
    "Sales Order": "public/js/sales_order.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Quotation": "public/js/quotation.js",
    "Employee": "public/js/employee.js",
    "Address": "public/js/address.js",
    "Sales Partner": "public/js/sales_partner.js",
    "Project": "public/js/project.js",
    "Task": "public/js/task.js"
}

# -----------------------------------------------------------------------------
# Website
# -----------------------------------------------------------------------------

# website_route_rules = [
#     {"from_route": "/arrowz/<path:app_path>", "to_route": "arrowz"}
# ]

# Home Pages
# home_page = "arrowz"
# role_home_page = {
#     "Call Center Agent": "arrowz-agent-dashboard",
#     "Call Center Manager": "arrowz-manager-dashboard"
# }

# -----------------------------------------------------------------------------
# Permissions & Roles
# -----------------------------------------------------------------------------

# Custom roles to create
# roles = ["Call Center Agent", "Call Center Manager"]

# Permission Query Conditions
# permission_query_conditions = {
#     "Arrowz Universal Call Log": "arrowz.permissions.get_call_log_query"
# }

# has_permission = {
#     "Arrowz Universal Call Log": "arrowz.permissions.has_call_log_permission"
# }

# -----------------------------------------------------------------------------
# Document Events
# -----------------------------------------------------------------------------

doc_events = {
    # Log when Contact is created to associate with calls
    "Contact": {
        "after_insert": "arrowz.events.contact.after_insert",
        "on_update": "arrowz.events.contact.on_update"
    },
    # Auto-link leads to calls
    "Lead": {
        "after_insert": "arrowz.events.lead.after_insert"
    },
    # Omni-Channel Session Events
    "AZ Conversation Session": {
        "on_update": "arrowz.events.conversation.on_session_update",
        "after_insert": "arrowz.events.conversation.on_session_create"
    },
    # Meeting Room Events
    "AZ Meeting Room": {
        "before_insert": "arrowz.events.meeting.before_room_create",
        "after_insert": "arrowz.events.meeting.after_room_create",
        "on_update": "arrowz.events.meeting.on_room_update"
    }
}

# -----------------------------------------------------------------------------
# Scheduled Tasks
# -----------------------------------------------------------------------------

scheduler_events = {
    # Every minute - presence heartbeat cleanup
    "cron": {
        "*/5 * * * *": [
            "arrowz.tasks.cleanup_stale_presence"
        ],
        # Every 10 minutes - cleanup stale calls
        "*/10 * * * *": [
            "arrowz.tasks.cleanup_stale_calls"
        ],
        # Check for expired WhatsApp 24h windows
        "*/15 * * * *": [
            "arrowz.tasks.check_window_expiry"
        ]
    },
    # Hourly - sync with PBX
    "hourly": [
        "arrowz.tasks.sync_pbx_status",
        "arrowz.tasks.sync_openmeetings_status"
    ],
    # Daily - cleanup and reporting
    "daily": [
        "arrowz.tasks.cleanup_old_presence_logs",
        "arrowz.tasks.generate_daily_report",
        "arrowz.tasks.cleanup_ended_conversations",
        "arrowz.tasks.cleanup_temporary_rooms"
    ],
    # Weekly - analytics
    "weekly": [
        "arrowz.tasks.generate_weekly_analytics",
        "arrowz.tasks.generate_omni_channel_report"
    ]
}

# -----------------------------------------------------------------------------
# Jinja Filters/Methods
# -----------------------------------------------------------------------------

# jinja = {
#     "methods": ["arrowz.utils.jinja_methods"]
# }

# -----------------------------------------------------------------------------
# Installation Hooks
# -----------------------------------------------------------------------------

before_install = "arrowz.install.before_install"
after_install = "arrowz.install.after_install"
after_migrate = "arrowz.install.after_migrate"

# Uninstall cleanup
before_uninstall = "arrowz.uninstall.before_uninstall"

# -----------------------------------------------------------------------------
# Fixtures (data to export with app)
# -----------------------------------------------------------------------------

fixtures = [
    # Export custom fields
    {
        "doctype": "Custom Field",
        "filters": [["module", "=", "Arrowz"]]
    },
    # Export property setters
    {
        "doctype": "Property Setter",
        "filters": [["module", "=", "Arrowz"]]
    }
]

# -----------------------------------------------------------------------------
# Override Methods
# -----------------------------------------------------------------------------

# override_whitelisted_methods = {
#     "frappe.desk.doctype.event.event.get_events": "arrowz.overrides.get_events"
# }

# -----------------------------------------------------------------------------
# Boot Session
# -----------------------------------------------------------------------------

# Values to inject into frappe.boot
boot_session = "arrowz.boot.boot_session"

# -----------------------------------------------------------------------------
# User Data Protection (GDPR)
# -----------------------------------------------------------------------------

# user_data_fields = [
#     {
#         "doctype": "Arrowz Universal Call Log",
#         "filter_by": "extension",
#         "partial": True
#     }
# ]

# -----------------------------------------------------------------------------
# Desk Notifications
# -----------------------------------------------------------------------------

notification_config = "arrowz.notifications.get_notification_config"

# -----------------------------------------------------------------------------
# Realtime Events
# -----------------------------------------------------------------------------

# Socket.IO events to publish
# These are handled in the JavaScript client

# Events published:
# - arrowz_call_started
# - arrowz_call_ended
# - arrowz_presence_update
# - arrowz_ai_suggestion
# - arrowz_sentiment_update
# - new_message (Omni-Channel)
# - message_status (Omni-Channel)
# - conversation_update (Omni-Channel)
# - meeting_user_joined (OpenMeetings)
# - meeting_user_left (OpenMeetings)
# - meeting_ended (OpenMeetings)
# - recording_ready (OpenMeetings)

# -----------------------------------------------------------------------------
# Whitelisted Methods for API
# -----------------------------------------------------------------------------

# Webhook endpoints (allow guest access for external services)
# These are defined in arrowz/api/webhooks.py
# - arrowz.api.webhooks.whatsapp_cloud_webhook
# - arrowz.api.webhooks.whatsapp_onprem_webhook
# - arrowz.api.webhooks.telegram_webhook
# - arrowz.api.webhooks.openmeetings_callback
