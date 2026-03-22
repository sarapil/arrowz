# Arrowz Developer Guide

> **Version:** 16.0.0  
> **Compatible With:** Frappe v16+ / ERPNext v16+  
> **Last Updated:** February 17, 2026

---

## 📋 Table of Contents

1. [Getting Started](#1-getting-started)
2. [Development Environment](#2-development-environment)
3. [App Architecture](#3-app-architecture)
4. [DocType Development](#4-doctype-development)
5. [API Development](#5-api-development)
6. [JavaScript Development](#6-javascript-development)
7. [Integrations](#7-integrations)
8. [Testing](#8-testing)
9. [Debugging](#9-debugging)
10. [Best Practices](#10-best-practices)
11. [Contributing](#11-contributing)

---

## 1. Getting Started

### 1.1 Prerequisites

| Component | Version |
|-----------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| MariaDB | 10.6+ |
| Redis | 6.0+ |
| Frappe | v16+ |

### 1.2 Installation for Development

```bash
# Create a new bench (if not exists)
bench init --frappe-branch version-16 frappe-bench
cd frappe-bench

# Create a new site
bench new-site dev.localhost --db-name arrowz_dev

# Get Arrowz app
bench get-app arrowz --branch version-16

# Install on site
bench --site dev.localhost install-app arrowz

# Enable developer mode
bench --site dev.localhost set-config developer_mode 1

# Start development server
bench start
```

### 1.3 Development Setup

```bash
# Install development dependencies
cd apps/arrowz
pip install -e ".[dev]"

# Set up pre-commit hooks
pip install pre-commit
pre-commit install
```

---

## 2. Development Environment

### 2.1 VS Code Setup

Recommended extensions:
- Python
- Pylance
- ESLint
- Prettier

**settings.json:**
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/env/bin/python",
    "python.analysis.typeCheckingMode": "basic",
    "editor.formatOnSave": true,
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff"
    }
}
```

### 2.2 Debug Configuration

**.vscode/launch.json:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Bench Web",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/env/bin/bench",
            "args": ["serve", "--port", "8000"],
            "cwd": "${workspaceFolder}",
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
```

### 2.3 Environment Variables

Create `.env` in bench folder:
```bash
# Development settings
FRAPPE_SITE=dev.localhost
DEVELOPER_MODE=1

# FreePBX settings (for testing)
PBX_HOST=your-pbx.example.com
PBX_SSH_USER=root
PBX_SSH_PASS=your_password

# OpenMeetings (for testing)
OM_HOST=your-om.example.com
OM_ADMIN_USER=admin
OM_ADMIN_PASS=your_password
```

---

## 3. App Architecture

### 3.1 Directory Structure

```
arrowz/
├── arrowz/
│   ├── __init__.py
│   ├── hooks.py              # Frappe hooks configuration
│   ├── boot.py               # Boot session data
│   ├── install.py            # Installation hooks
│   ├── uninstall.py          # Uninstallation hooks
│   ├── tasks.py              # Scheduled tasks
│   ├── permissions.py        # Permission functions
│   ├── notifications.py      # Notification config
│   ├── freepbx_token.py      # FreePBX OAuth2 manager
│   │
│   ├── api/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── webrtc.py         # WebRTC/Softphone API
│   │   ├── sms.py            # SMS API
│   │   ├── whatsapp.py       # WhatsApp API
│   │   ├── telegram.py       # Telegram API
│   │   ├── conversation.py   # Omni-channel API
│   │   ├── meeting.py        # Video meeting API
│   │   ├── analytics.py      # Analytics API
│   │   ├── agent.py          # Agent dashboard API
│   │   ├── wallboard.py      # Wallboard API
│   │   ├── screenpop.py      # Screen pop API
│   │   ├── recording.py      # Recording API
│   │   ├── contacts.py       # Contact search API
│   │   └── omni.py           # Unified messaging API
│   │
│   ├── arrowz/               # Main module with DocTypes
│   │   └── doctype/
│   │       ├── arrowz_settings/
│   │       ├── az_server_config/
│   │       ├── az_extension/
│   │       ├── az_call_log/
│   │       └── ... (other doctypes)
│   │
│   ├── integrations/         # External integrations
│   │   ├── whatsapp.py
│   │   ├── telegram.py
│   │   └── openmeetings.py
│   │
│   ├── events/               # Document event handlers
│   │   ├── contact.py
│   │   ├── lead.py
│   │   ├── conversation.py
│   │   └── meeting.py
│   │
│   ├── tests/                # Test suite
│   │   ├── conftest.py
│   │   ├── test_doctypes/
│   │   ├── test_api/
│   │   └── test_integrations/
│   │
│   └── public/               # Static assets
│       ├── js/
│       │   ├── arrowz.js
│       │   ├── softphone_v2.js
│       │   └── ...
│       └── css/
│           ├── arrowz.css
│           └── ...
│
├── docs/                     # Documentation
├── pyproject.toml            # Python project config
└── README.md
```

### 3.2 Module Organization

| Module | Purpose |
|--------|---------|
| `api/` | HTTP API endpoints (whitelisted methods) |
| `arrowz/doctype/` | DocType definitions and controllers |
| `integrations/` | External service integrations |
| `events/` | Document event handlers |
| `tests/` | Automated tests |
| `public/` | Frontend assets (JS/CSS) |

---

## 4. DocType Development

### 4.1 Creating a New DocType

```bash
bench --site dev.localhost make-app arrowz

# Or manually create structure:
mkdir -p arrowz/arrowz/doctype/az_new_doctype
```

### 4.2 DocType Controller Pattern (v16)

```python
# az_new_doctype.py

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.types import DF
from typing import Optional


class AZNewDoctype(Document):
    """
    DocType for managing new feature.
    
    Attributes:
        name: Unique identifier
        title: Display title
        status: Current status
        amount: Currency amount
    """
    
    # Type hints for fields (v16 recommended)
    name: DF.Data
    title: DF.Data
    status: DF.Literal["Draft", "Active", "Completed", "Cancelled"]
    amount: DF.Currency
    user: DF.Link["User"]
    
    def validate(self):
        """Validate document before save."""
        self.validate_amount()
        self.set_defaults()
    
    def validate_amount(self):
        """Ensure amount is positive."""
        if self.amount and self.amount < 0:
            frappe.throw(_("Amount cannot be negative"))
    
    def set_defaults(self):
        """Set default values."""
        if not self.status:
            self.status = "Draft"
    
    def before_save(self):
        """Actions before saving to database."""
        self.modified_by = frappe.session.user
    
    def after_insert(self):
        """Actions after document is created."""
        self.notify_users()
    
    def on_update(self):
        """Actions after document is updated."""
        # NOTE: Do NOT call frappe.db.commit() here in v16
        pass
    
    def on_submit(self):
        """Actions when document is submitted."""
        self.status = "Active"
    
    def on_cancel(self):
        """Actions when document is cancelled."""
        self.status = "Cancelled"
    
    def notify_users(self):
        """Send notification to relevant users."""
        frappe.publish_realtime(
            event="arrowz_new_doctype_created",
            message={"name": self.name, "title": self.title},
            user=self.user
        )
    
    # Whitelisted method on controller (callable from client)
    @frappe.whitelist()
    def custom_action(self) -> dict:
        """
        Perform custom action on this document.
        
        Returns:
            dict: Result of the action
        """
        self.status = "Completed"
        self.save()
        return {"status": "success", "message": _("Action completed")}


# Standalone whitelisted function
@frappe.whitelist(methods=["POST"])
def create_new_doctype(title: str, amount: float) -> str:
    """
    Create a new AZ New Doctype.
    
    Args:
        title: Document title
        amount: Currency amount
        
    Returns:
        str: Name of created document
    """
    doc = frappe.new_doc("AZ New Doctype")
    doc.title = title
    doc.amount = amount
    doc.insert()
    
    return doc.name
```

### 4.3 Permission Functions (v16)

```python
# permissions.py

import frappe
from typing import Optional


def has_app_permission() -> bool:
    """Check if user can access Arrowz app."""
    return frappe.has_permission("Arrowz Settings", "read")


def get_call_log_query(user: Optional[str] = None) -> str:
    """
    Get permission query for call logs.
    
    Args:
        user: User to check permissions for
        
    Returns:
        str: SQL WHERE clause
    """
    if not user:
        user = frappe.session.user
    
    if "System Manager" in frappe.get_roles(user):
        return ""
    
    if "Call Center Manager" in frappe.get_roles(user):
        return ""
    
    extension = get_user_extension(user)
    if extension:
        return f"`tabAZ Call Log`.`extension` = '{extension}'"
    
    return "1=0"  # No access


def has_call_log_permission(doc, ptype: str, user: Optional[str] = None) -> bool:
    """
    Check if user has permission on specific call log.
    
    IMPORTANT: In v16, must return True explicitly, not None.
    
    Args:
        doc: Document to check
        ptype: Permission type (read, write, etc.)
        user: User to check
        
    Returns:
        bool: True if permitted, False otherwise
    """
    if not user:
        user = frappe.session.user
    
    roles = frappe.get_roles(user)
    
    # Managers can see everything
    if "System Manager" in roles or "Call Center Manager" in roles:
        return True  # MUST return True explicitly in v16
    
    # Agents can only see their own calls
    extension = get_user_extension(user)
    if extension and doc.extension == extension:
        return True
    
    return False  # Explicit denial


def get_user_extension(user: str) -> Optional[str]:
    """Get primary extension for user."""
    return frappe.db.get_value(
        "AZ Extension",
        {"user": user, "enabled": 1},
        "extension_number"
    )
```

---

## 5. API Development

### 5.1 API Endpoint Pattern (v16)

```python
# api/my_feature.py

import frappe
from frappe import _
from typing import Optional, Any


@frappe.whitelist(methods=["GET"])
def get_data(
    filters: Optional[dict] = None,
    limit: int = 20,
    offset: int = 0
) -> dict[str, Any]:
    """
    Get data with pagination.
    
    Args:
        filters: Optional filter conditions
        limit: Number of records to return
        offset: Starting position
        
    Returns:
        dict: Data with pagination info
    """
    query_filters = filters or {}
    
    data = frappe.get_all(
        "AZ Call Log",
        filters=query_filters,
        fields=["name", "caller_id", "callee_id", "duration", "disposition"],
        order_by="creation desc",  # Explicit in v16
        limit_start=offset,
        limit_page_length=limit
    )
    
    total = frappe.db.count("AZ Call Log", query_filters)
    
    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@frappe.whitelist(methods=["POST"])
def create_record(
    caller_id: str,
    callee_id: str,
    direction: str = "Outbound"
) -> dict[str, str]:
    """
    Create a new call log record.
    
    Args:
        caller_id: Caller phone number
        callee_id: Callee phone number
        direction: Call direction (Inbound/Outbound)
        
    Returns:
        dict: Created record info
    """
    doc = frappe.new_doc("AZ Call Log")
    doc.caller_id = caller_id
    doc.callee_id = callee_id
    doc.direction = direction
    doc.insert()
    
    return {
        "status": "success",
        "name": doc.name,
        "message": _("Record created")
    }


@frappe.whitelist(methods=["POST"])
def update_status(name: str, status: str) -> dict[str, str]:
    """
    Update record status.
    
    Args:
        name: Document name
        status: New status
        
    Returns:
        dict: Update result
    """
    doc = frappe.get_doc("AZ Call Log", name)
    doc.status = status
    doc.save()
    
    return {"status": "success", "message": _("Status updated")}


@frappe.whitelist(methods=["DELETE"])
def delete_record(name: str) -> dict[str, str]:
    """
    Delete a record.
    
    Args:
        name: Document name
        
    Returns:
        dict: Delete result
    """
    frappe.delete_doc("AZ Call Log", name)
    
    return {"status": "success", "message": _("Record deleted")}


# Guest-accessible endpoint (e.g., webhooks)
@frappe.whitelist(allow_guest=True, methods=["POST"])
def webhook_handler() -> dict[str, str]:
    """
    Handle external webhook.
    
    Security: Validate webhook signature before processing.
    """
    data = frappe.request.get_json()
    
    # Validate signature
    if not validate_webhook_signature(data):
        frappe.throw(_("Invalid signature"), frappe.AuthenticationError)
    
    # Process webhook
    process_webhook_data(data)
    
    return {"status": "received"}


def validate_webhook_signature(data: dict) -> bool:
    """Validate webhook signature."""
    import hmac
    import hashlib
    
    signature = frappe.request.headers.get("X-Signature")
    secret = frappe.get_single_value("Arrowz Settings", "webhook_secret")
    
    if not signature or not secret:
        return False
    
    expected = hmac.new(
        secret.encode(),
        frappe.request.data,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)


def process_webhook_data(data: dict):
    """Process webhook data in background."""
    frappe.enqueue(
        "arrowz.api.my_feature.process_webhook_async",
        queue="default",
        data=data
    )


def process_webhook_async(data: dict):
    """Async webhook processing."""
    # Process data
    # Can use frappe.db.commit() here (not in document hooks)
    frappe.db.commit()
```

### 5.2 Query Builder Examples (v16)

```python
from frappe.query_builder import DocType, Field
from frappe.query_builder.functions import Sum, Count, Avg, IfNull


def get_call_statistics(from_date: str, to_date: str) -> dict:
    """Get call statistics using query builder."""
    
    log = DocType("AZ Call Log")
    
    # Basic aggregation
    stats = (frappe.qb.from_(log)
        .select(
            Count("*").as_("total_calls"),
            Sum(log.duration).as_("total_duration"),
            Avg(log.duration).as_("avg_duration")
        )
        .where(log.creation >= from_date)
        .where(log.creation <= to_date)
        .run(as_dict=True)[0])
    
    # Group by disposition
    by_disposition = (frappe.qb.from_(log)
        .select(
            log.disposition,
            Count("*").as_("count")
        )
        .where(log.creation >= from_date)
        .where(log.creation <= to_date)
        .groupby(log.disposition)
        .run(as_dict=True))
    
    return {
        "summary": stats,
        "by_disposition": by_disposition
    }


def get_agent_performance(agent_extension: str) -> dict:
    """Get agent performance metrics."""
    
    log = DocType("AZ Call Log")
    
    # Using IfNull for null handling
    results = (frappe.qb.from_(log)
        .select(
            Count("*").as_("total_calls"),
            Sum(IfNull(log.duration, 0)).as_("total_duration")
        )
        .where(log.extension == agent_extension)
        .where(log.disposition == "ANSWERED")
        .run(as_dict=True)[0])
    
    return results
```

---

## 6. JavaScript Development

### 6.1 Module Pattern (v16 Compatible)

```javascript
// arrowz.js

// Use frappe.provide for namespace
frappe.provide("arrowz");

// Initialize on app ready
$(document).on("app_ready", function() {
    arrowz.init();
});

arrowz.init = function() {
    // Initialize components
    arrowz.setup_realtime();
    arrowz.check_extension();
};

arrowz.setup_realtime = function() {
    // Subscribe to realtime events
    frappe.realtime.on("arrowz_call_event", function(data) {
        arrowz.handle_call_event(data);
    });
};

arrowz.handle_call_event = function(data) {
    console.log("Call event:", data);
    // Handle event
};

arrowz.check_extension = function() {
    if (!frappe.boot.arrowz || !frappe.boot.arrowz.has_extension) {
        return;
    }
    
    // User has extension, initialize softphone
    arrowz.softphone.init();
};

// API call helper
arrowz.call_api = function(method, args, callback) {
    frappe.call({
        method: `arrowz.api.${method}`,
        type: "POST",  // Always use POST for state-changing
        args: args,
        callback: function(r) {
            if (callback) callback(r.message);
        }
    });
};

// Export for global access (v16 IIFE compatibility)
window.arrowz = arrowz;
```

### 6.2 Form Script Pattern

```javascript
// public/js/contact.js

frappe.ui.form.on("Contact", {
    refresh: function(frm) {
        // Add Arrowz actions
        if (frappe.boot.arrowz && frappe.boot.arrowz.enabled) {
            arrowz.form.add_phone_actions(frm);
        }
    },
    
    mobile_no: function(frm) {
        // Field change handler
        arrowz.form.validate_phone(frm, "mobile_no");
    }
});

// Namespace for form utilities
frappe.provide("arrowz.form");

arrowz.form.add_phone_actions = function(frm) {
    if (!frm.doc.mobile_no) return;
    
    frm.add_custom_button(__("Call"), function() {
        arrowz.softphone.dial(frm.doc.mobile_no);
    }, __("Arrowz"));
    
    frm.add_custom_button(__("WhatsApp"), function() {
        arrowz.omni.send_whatsapp(frm.doc.mobile_no);
    }, __("Arrowz"));
};

arrowz.form.validate_phone = function(frm, fieldname) {
    const phone = frm.doc[fieldname];
    if (phone && !arrowz.utils.is_valid_phone(phone)) {
        frappe.msgprint(__("Invalid phone number format"));
    }
};
```

### 6.3 Custom Page/Report

```javascript
// pages/agent_dashboard.js

frappe.pages["arrowz-agent-dashboard"].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Agent Dashboard"),
        single_column: true
    });
    
    // Store page reference
    wrapper.page = page;
    
    // Initialize dashboard
    new arrowz.AgentDashboard(page);
};

// Use class pattern
arrowz.AgentDashboard = class AgentDashboard {
    constructor(page) {
        this.page = page;
        this.init();
    }
    
    init() {
        this.setup_ui();
        this.load_data();
        this.setup_realtime();
    }
    
    setup_ui() {
        this.page.main.html(`
            <div class="arrowz-dashboard">
                <div class="status-panel"></div>
                <div class="stats-panel"></div>
                <div class="calls-panel"></div>
            </div>
        `);
    }
    
    async load_data() {
        const response = await frappe.call({
            method: "arrowz.api.agent.get_dashboard_data",
            type: "GET"
        });
        
        this.render_data(response.message);
    }
    
    render_data(data) {
        // Render dashboard components
    }
    
    setup_realtime() {
        frappe.realtime.on("agent_status_changed", (data) => {
            this.handle_status_change(data);
        });
    }
    
    handle_status_change(data) {
        // Update UI
    }
};
```

---

## 7. Integrations

### 7.1 FreePBX Integration

```python
# integrations/freepbx.py

import frappe
from arrowz.freepbx_token import FreePBXTokenManager, execute_graphql


def create_extension(extension: str, name: str, password: str) -> dict:
    """Create extension in FreePBX via GraphQL."""
    
    server = frappe.get_single_value("Arrowz Settings", "default_server")
    
    mutation = """
    mutation AddExtension($input: ExtensionInput!) {
        addExtension(input: $input) {
            status
            message
            id
        }
    }
    """
    
    variables = {
        "input": {
            "extensionId": extension,
            "name": name,
            "email": f"{extension}@local.domain",
            "umPassword": password,
            "tech": "pjsip",
            "outboundCid": extension
        }
    }
    
    result = execute_graphql(server, mutation, variables)
    
    if result.get("errors"):
        frappe.throw(str(result["errors"]))
    
    return result["data"]["addExtension"]


def originate_call(extension: str, number: str) -> dict:
    """Originate call via AMI."""
    
    import socket
    
    server = frappe.get_doc("AZ Server Config", 
        frappe.get_single_value("Arrowz Settings", "default_server"))
    
    ami_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ami_socket.connect((server.ami_host, server.ami_port))
    
    # Login
    ami_socket.send(f"""Action: Login
Username: {server.ami_username}
Secret: {frappe.utils.password.get_decrypted_password(
    "AZ Server Config", server.name, "ami_password")}

""".encode())
    
    # Originate
    ami_socket.send(f"""Action: Originate
Channel: PJSIP/{extension}
Context: from-internal
Exten: {number}
Priority: 1
CallerID: {extension}
Async: true

""".encode())
    
    response = ami_socket.recv(4096).decode()
    ami_socket.close()
    
    return {"status": "success", "response": response}
```

### 7.2 WhatsApp Integration

```python
# integrations/whatsapp.py

import frappe
import requests
import hmac
import hashlib
from typing import Optional


class WhatsAppClient:
    """WhatsApp Cloud API client."""
    
    def __init__(self, channel_name: str):
        self.channel = frappe.get_doc("AZ Omni Channel", channel_name)
        self.provider = frappe.get_doc("AZ Omni Provider", self.channel.provider)
        self.base_url = f"https://graph.facebook.com/v17.0/{self.channel.phone_number_id}"
    
    def send_message(self, to: str, text: str) -> dict:
        """Send text message."""
        
        response = requests.post(
            f"{self.base_url}/messages",
            headers={
                "Authorization": f"Bearer {self.provider.access_token}",
                "Content-Type": "application/json"
            },
            json={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"body": text}
            }
        )
        
        response.raise_for_status()
        return response.json()
    
    def send_template(self, to: str, template_name: str, 
                      language: str = "en", components: list = None) -> dict:
        """Send template message."""
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language}
            }
        }
        
        if components:
            payload["template"]["components"] = components
        
        response = requests.post(
            f"{self.base_url}/messages",
            headers={
                "Authorization": f"Bearer {self.provider.access_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def verify_webhook(request_data: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature."""
        
        expected = hmac.new(
            secret.encode(),
            request_data,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## 8. Testing

### 8.1 Test Configuration

```python
# tests/conftest.py

import pytest
import frappe


@pytest.fixture(scope="session")
def frappe_site():
    """Initialize Frappe site for testing."""
    frappe.init(site="test_site")
    frappe.connect()
    yield
    frappe.destroy()


@pytest.fixture
def test_extension(frappe_site):
    """Create test extension."""
    doc = frappe.get_doc({
        "doctype": "AZ Extension",
        "extension_number": "9999",
        "display_name": "Test Extension",
        "user": "Administrator",
        "server": get_test_server()
    })
    doc.insert(ignore_permissions=True)
    yield doc
    doc.delete(ignore_permissions=True)
```

### 8.2 Writing Tests

```python
# tests/test_api/test_webrtc.py

import pytest
import frappe
from unittest.mock import patch, MagicMock


class TestWebRTCAPI:
    """Tests for WebRTC API endpoints."""
    
    def test_get_server_config(self, frappe_site, test_extension):
        """Test server config retrieval."""
        from arrowz.api.webrtc import get_server_config
        
        with patch("frappe.session") as mock_session:
            mock_session.user = "Administrator"
            
            config = get_server_config()
            
            assert config is not None
            assert "wsServers" in config
    
    @patch("arrowz.integrations.freepbx.originate_call")
    def test_make_call(self, mock_originate, frappe_site, test_extension):
        """Test making a call."""
        from arrowz.api.webrtc import make_call
        
        mock_originate.return_value = {"status": "success"}
        
        result = make_call("1234567890")
        
        assert result["status"] == "success"
        mock_originate.assert_called_once()
    
    def test_make_call_invalid_number(self, frappe_site, test_extension):
        """Test making call with invalid number."""
        from arrowz.api.webrtc import make_call
        
        with pytest.raises(frappe.ValidationError):
            make_call("")
```

### 8.3 Running Tests

```bash
# Run all tests
bench --site dev.localhost run-tests --app arrowz

# Run specific test file
bench --site dev.localhost run-tests --app arrowz \
    --module arrowz.tests.test_api.test_webrtc

# Run with coverage
bench --site dev.localhost run-tests --app arrowz --coverage

# Run specific test class
pytest apps/arrowz/arrowz/tests/test_api/test_webrtc.py::TestWebRTCAPI -v
```

---

## 9. Debugging

### 9.1 Server-Side Debugging

```python
# Add debug logging
import frappe

frappe.log_error("Debug message", "Arrowz Debug")

# Use print (shows in bench console)
print("Debug:", variable)

# Use frappe.logger
import logging
logger = logging.getLogger(__name__)
logger.info("Debug message")
```

### 9.2 Client-Side Debugging

```javascript
// Console logging
console.log("Debug:", data);

// Frappe debug helpers
frappe.debug_show = true;  // Show all API calls

// Network inspection
frappe.call({
    method: "...",
    callback: function(r) {
        console.log("Response:", r);
    },
    error: function(r) {
        console.error("Error:", r);
    }
});
```

### 9.3 VS Code Debugging

1. Set breakpoint in Python code
2. Run "Bench Web" debug configuration
3. Trigger the code path in browser

---

## 10. Best Practices

### 10.1 Python

```python
# ✅ Good: Type hints and docstrings
def get_call_stats(from_date: str, to_date: str) -> dict:
    """Get call statistics for date range."""
    pass

# ✅ Good: Explicit ordering in v16
frappe.get_all("AZ Call Log", order_by="creation desc")

# ✅ Good: Use query builder for complex queries
from frappe.query_builder import DocType
log = DocType("AZ Call Log")
frappe.qb.from_(log).select("*").run()

# ❌ Bad: frappe.db.commit() in document hooks
def on_update(doc, method):
    frappe.db.commit()  # Don't do this in v16

# ✅ Good: Use enqueue for background processing
def on_update(doc, method):
    frappe.enqueue("arrowz.tasks.process_update", doc_name=doc.name)
```

### 10.2 JavaScript

```javascript
// ✅ Good: Use namespace
frappe.provide("arrowz");
arrowz.myFunction = function() {};

// ✅ Good: Explicit POST for state-changing
frappe.call({
    method: "arrowz.api.webrtc.make_call",
    type: "POST",
    args: { number: "123" }
});

// ❌ Bad: Global variables without namespace
var myGlobal = {};  // Gets wrapped in IIFE in v16

// ✅ Good: Use window for global access
window.arrowz = arrowz;
```

### 10.3 Security

```python
# ✅ Always validate permissions
frappe.only_for(["System Manager", "Call Center Manager"])

# ✅ Sanitize user input
number = frappe.utils.escape_html(number)

# ✅ Use secure password storage
password = frappe.utils.password.get_decrypted_password(
    "AZ Server Config", server_name, "ami_password")

# ✅ Verify webhook signatures
if not verify_signature(request):
    frappe.throw("Invalid signature", frappe.AuthenticationError)
```

---

## 11. Contributing

### 11.1 Development Workflow

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes with tests
4. Run linting: `ruff check arrowz`
5. Run tests: `bench run-tests --app arrowz`
6. Commit with conventional commits
7. Create pull request

### 11.2 Commit Messages

```
feat: Add new WebRTC hold feature
fix: Resolve call log duration calculation
docs: Update API documentation
test: Add SMS API tests
refactor: Improve query performance
```

### 11.3 Code Style

- Use `ruff` for Python linting
- Use `prettier` for JavaScript formatting
- Follow Frappe coding conventions
- Add type hints to all functions
- Write docstrings for public APIs

---

*Last updated: February 17, 2026*
