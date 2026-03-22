"""
Arrowz Hooks Configuration

This file defines how Arrowz integrates with Frappe Framework.
Compatible with Frappe/ERPNext v16+
"""

app_name = "arrowz"
app_title = "Arrowz"
app_publisher = "Arrowz Team"
app_description = "Unified Network & WiFi Management Platform with VoIP"
app_version = "16.0.0"
app_icon = "/assets/arrowz/images/arrowz-icon-animated.svg"
app_logo_url = "/assets/arrowz/images/arrowz-logo-animated.svg"
app_color = "#8B5CF6"
app_email = "support@arrowz.io"
app_license = "MIT"

# Required Apps
required_apps = ["frappe", "frappe_visual"]

# Optional: Recommended apps for full functionality
# required_apps = ["frappe", "erpnext", "frappe_visual"]

# v16+: Export Python type annotations
export_python_type_annotations = True

# -----------------------------------------------------------------------------
# Apps Screen Configuration (v16+)
# -----------------------------------------------------------------------------

add_to_apps_screen = [
    {
        "name": "arrowz",
        "logo": "/assets/arrowz/images/arrowz-icon-animated.svg",
        "title": "Arrowz Communications",
        "route": "/desk/arrowz-topology",
        "has_permission": "arrowz.permissions.has_app_permission"
    }
]

# Route for the app icon on the /desk apps screen
# boot.py uses this (NOT add_to_apps_screen.route) to set app_route
app_home = "/desk/arrowz-topology"

# -----------------------------------------------------------------------------
# Assets to include in every page
# -----------------------------------------------------------------------------

# Include JS in all pages
app_include_js = [
    # --- WebRTC Adapter Layer (load order matters) ---
    "/assets/arrowz/js/webrtc_adapters/base_adapter.js",      # Abstract contract (must load first)
    "/assets/arrowz/js/lib/jssip.min.js",                     # JsSIP library
    "/assets/arrowz/js/webrtc_adapters/jssip_adapter.js",     # JsSIP concrete adapter
    "/assets/arrowz/js/webrtc_adapters/tab_leader.js",        # Cross-tab leader election
    "/assets/arrowz/js/webrtc_adapters/adapter_factory.js",   # Orchestration factory
    "/assets/arrowz/js/webrtc_adapters/softphone_bridge.js", # Bridge → softphone UI
    "/assets/arrowz/js/audio_visualizer.js",               # Audio signal visualizer
    # --- Core App ---
    "/assets/arrowz/js/arrowz.js",
    "/assets/arrowz/js/arrowz_theme.js",
    "/assets/arrowz/js/phone_actions.js",
    "/assets/arrowz/js/softphone_v3.js",
    "/assets/arrowz/js/screen_pop.js",
    "/assets/arrowz/js/omni_panel.js",
    "/assets/arrowz/js/omni_doctype_extension.js",
    # "/assets/arrowz/js/arrowz_desk_lcd.js"  # Disabled — TAVIRA theme provides LCD
]

# Include CSS in all pages
app_include_css = [
    "/assets/arrowz/css/arrowz_brand.css",
    "/assets/arrowz/css/arrowz_theme.css",
    "/assets/arrowz/css/arrowz.css",
    "/assets/arrowz/css/phone_actions.css",
    "/assets/arrowz/css/softphone_v2.css",
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
# home_page = "arrowz-topology"  # Removed: should not override global home page
role_home_page = {
    "System Manager": "arrowz-topology",
    "Call Center Agent": "arrowz-agent-dashboard",
    "Call Center Manager": "arrowz-wallboard"
}

# -----------------------------------------------------------------------------
# Permissions & Roles
# -----------------------------------------------------------------------------

# Custom roles to create
# roles = ["Call Center Agent", "Call Center Manager"]

# Permission Query Conditions
# permission_query_conditions = {
#     "Arrowz Universal Call Log": "arrowz.permissions.get_call_log_query"
# }

# NOTE: In v16+, has_permission MUST return True explicitly (not None)
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
    },
    # ── Network Management Events ────────────────────────────────────
    # Push config to Engine on save
    "WAN Connection": {
        "on_update": "arrowz.events.network.on_config_change",
        "on_trash": "arrowz.events.network.on_config_change"
    },
    "LAN Network": {
        "on_update": "arrowz.events.network.on_config_change",
        "on_trash": "arrowz.events.network.on_config_change"
    },
    "Static Route": {
        "on_update": "arrowz.events.network.on_config_change",
        "on_trash": "arrowz.events.network.on_config_change"
    },
    "DNS Entry": {
        "on_update": "arrowz.events.network.on_config_change",
        "on_trash": "arrowz.events.network.on_config_change"
    },
    # Firewall events
    "Firewall Rule": {
        "on_update": "arrowz.events.network.on_firewall_change",
        "on_trash": "arrowz.events.network.on_firewall_change"
    },
    "NAT Rule": {
        "on_update": "arrowz.events.network.on_firewall_change",
        "on_trash": "arrowz.events.network.on_firewall_change"
    },
    "Port Forward": {
        "on_update": "arrowz.events.network.on_firewall_change",
        "on_trash": "arrowz.events.network.on_firewall_change"
    },
    # Client management events
    "Network Client": {
        "on_update": "arrowz.events.network.on_client_change"
    },
    "MAC Blacklist": {
        "on_update": "arrowz.events.network.on_client_change",
        "after_insert": "arrowz.events.network.on_client_change",
        "on_trash": "arrowz.events.network.on_client_change"
    },
    "IP Reservation": {
        "on_update": "arrowz.events.network.on_client_change",
        "on_trash": "arrowz.events.network.on_client_change"
    },
    # Bandwidth events
    "Bandwidth Assignment": {
        "on_update": "arrowz.events.network.on_bandwidth_change",
        "on_trash": "arrowz.events.network.on_bandwidth_change"
    },
    # WiFi events
    "WiFi Network": {
        "on_update": "arrowz.events.network.on_wifi_change",
        "on_trash": "arrowz.events.network.on_wifi_change"
    },
    # VPN events
    "VPN Server": {
        "on_update": "arrowz.events.network.on_vpn_server_change",
        "on_trash": "arrowz.events.network.on_vpn_server_change"
    },
    "VPN Peer": {
        "on_update": "arrowz.events.network.on_vpn_change",
        "on_trash": "arrowz.events.network.on_vpn_change"
    },
    "VPN Access Policy": {
        "on_update": "arrowz.events.network.on_vpn_policy_change",
        "on_trash": "arrowz.events.network.on_vpn_policy_change"
    },
    "Site to Site Tunnel": {
        "on_update": "arrowz.events.network.on_vpn_change",
        "on_trash": "arrowz.events.network.on_vpn_change"
    }
}

# -----------------------------------------------------------------------------
# Scheduled Tasks
# -----------------------------------------------------------------------------

scheduler_events = {
    # Every minute - presence heartbeat cleanup
    "cron": {
        # ── Every minute ──
        "* * * * *": [
            "arrowz.tasks_network.check_box_health",
            "arrowz.tasks_network.check_wan_health",
            "arrowz.tasks_network.check_voucher_expiry",
        ],
        # ── Every 2 minutes ──
        "*/2 * * * *": [
            "arrowz.tasks_network.evaluate_alert_rules",
        ],
        # ── Every 5 minutes ──
        "*/5 * * * *": [
            "arrowz.tasks.cleanup_stale_presence",
            "arrowz.tasks_network.sync_bandwidth_stats",
            "arrowz.tasks_network.collect_wifi_analytics",
            "arrowz.tasks_network.collect_ip_accounting",
            "arrowz.tasks_network.check_quota_usage",
            "arrowz.device_providers.sync_engine.auto_sync_boxes",
        ],
        # ── Every 10 minutes ──
        "*/10 * * * *": [
            "arrowz.tasks.cleanup_stale_calls",
        ],
        # ── Every 15 minutes ──
        "*/15 * * * *": [
            "arrowz.tasks.check_window_expiry",
        ],
    },
    # Hourly - sync with PBX
    "hourly": [
        "arrowz.tasks.sync_pbx_status",
        "arrowz.tasks.sync_openmeetings_status",
        "arrowz.tasks_network.sync_client_list",
        "arrowz.tasks_network.cleanup_stale_sessions"
    ],
    # Daily - cleanup and reporting
    "daily": [
        "arrowz.tasks.cleanup_old_presence_logs",
        "arrowz.tasks.generate_daily_report",
        "arrowz.tasks.cleanup_ended_conversations",
        "arrowz.tasks.cleanup_temporary_rooms",
        "arrowz.tasks_network.cleanup_old_logs",
        "arrowz.tasks_network.cleanup_old_sessions",
        "arrowz.tasks_network.reset_daily_quotas",
        "arrowz.tasks_network.generate_daily_billing"
    ],
    # Weekly - analytics
    "weekly": [
        "arrowz.tasks.generate_weekly_analytics",
        "arrowz.tasks.generate_omni_channel_report",
        "arrowz.tasks_network.reset_weekly_quotas",
        "arrowz.tasks_network.generate_weekly_network_report"
    ],
    # Monthly
    "monthly": [
        "arrowz.tasks_network.reset_monthly_quotas",
        "arrowz.tasks_network.generate_monthly_invoices"
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
