# Arrowz - AI Coding Guidelines

> Specific guidelines for AI assistants when generating or modifying Arrowz code.

## 🎯 Purpose

This document ensures consistent, high-quality code generation by AI assistants.

---

## ✅ DO's

### Python Code

```python
# ✅ DO: Use type hints
def get_extension(user: str) -> dict:
    ...

# ✅ DO: Use frappe utilities
frappe.get_doc("DocType", name)
frappe.db.get_value("DocType", filters, fields)
frappe.enqueue(method, queue="long")

# ✅ DO: Proper error handling
try:
    result = frappe.get_doc("AZ Extension", name)
except frappe.DoesNotExistError:
    frappe.throw(_("Extension not found"))

# ✅ DO: Use @frappe.whitelist() for APIs
@frappe.whitelist()
def my_api_method(param: str) -> dict:
    """Docstring with description."""
    frappe.only_for(["System Manager"])
    return {"status": "success"}

# ✅ DO: Use translations
frappe.throw(_("Error message"))
frappe.msgprint(_("Success message"))

# ✅ DO: Log with proper levels
frappe.log_error(message=str(e), title="Arrowz Error")
frappe.logger("arrowz").info("Action completed")
```

### JavaScript Code

```javascript
// ✅ DO: Use arrowz.* namespace
arrowz.myFeature = {
    init() { ... },
    cleanup() { ... }
};

// ✅ DO: Use frappe.call for APIs
const { message } = await frappe.call({
    method: 'arrowz.api.module.function',
    args: { param: value }
});

// ✅ DO: Use frappe.realtime for Socket.IO
frappe.realtime.on('event_name', (data) => {
    console.log('Received:', data);
});

// ✅ DO: Check for null/undefined
if (this.container && this.container.innerHTML) {
    this.container.innerHTML = html;
}

// ✅ DO: Use template literals
const html = `<div class="arrowz-item">${content}</div>`;

// ✅ DO: Handle promise errors
frappe.call({...}).catch(err => {
    console.error('Arrowz error:', err);
    frappe.throw(__('Operation failed'));
});
```

---

## ❌ DON'Ts

### Python Code

```python
# ❌ DON'T: Use raw SQL without parameterization
frappe.db.sql(f"SELECT * FROM tabX WHERE name='{user_input}'")  # SQL INJECTION!

# ✅ DO: Use parameterized queries
frappe.db.sql("SELECT * FROM tabX WHERE name=%s", (user_input,))

# ❌ DON'T: Use print() for logging
print("Debug message")

# ✅ DO: Use frappe logging
frappe.logger("arrowz").debug("Debug message")

# ❌ DON'T: Hardcode sensitive data
api_key = "sk-abc123..."

# ✅ DO: Use site config or DocType
api_key = frappe.db.get_single_value("Arrowz Settings", "api_key")

# ❌ DON'T: Block on synchronous calls in background
import time
time.sleep(60)  # Never in main thread!

# ✅ DO: Use frappe background jobs
frappe.enqueue(method, queue="long", timeout=3600)
```

### JavaScript Code

```javascript
// ❌ DON'T: Use global namespace pollution
window.myFunction = function() {...}

// ✅ DO: Use arrowz namespace
arrowz.myFunction = function() {...}

// ❌ DON'T: Use raw fetch for Frappe APIs
fetch('/api/method/...')

// ✅ DO: Use frappe.call
frappe.call({method: '...'})

// ❌ DON'T: Ignore async errors
frappe.call({...})  // No error handling!

// ✅ DO: Handle errors properly
frappe.call({...}).catch(err => console.error(err))

// ❌ DON'T: Use innerHTML with user data (XSS risk)
element.innerHTML = user_input

// ✅ DO: Sanitize or use textContent
element.textContent = user_input
// Or
element.innerHTML = frappe.utils.escape_html(user_input)
```

---

## 🏗️ Code Structure Patterns

### Creating a New API Endpoint

```python
# arrowz/api/my_feature.py

import frappe
from frappe import _

@frappe.whitelist()
def my_feature_action(param1: str, param2: int = None) -> dict:
    """
    Perform my feature action.
    
    Args:
        param1: Description of param1
        param2: Optional, description of param2
        
    Returns:
        dict: Result with status and data
        
    Raises:
        frappe.ValidationError: If param1 is invalid
    """
    frappe.only_for(["Arrowz User", "System Manager"])
    
    if not param1:
        frappe.throw(_("param1 is required"), frappe.MandatoryError)
    
    try:
        # Business logic here
        result = process_feature(param1, param2)
        return {"status": "success", "data": result}
    except Exception as e:
        frappe.log_error(message=str(e), title="my_feature_action Error")
        frappe.throw(_("Operation failed: {0}").format(str(e)))
```

### Creating a New Frontend Component

```javascript
// arrowz/public/js/my_component.js

arrowz.my_component = {
    container: null,
    
    init() {
        this.render();
        this.bindEvents();
        this.subscribeToRealtime();
    },
    
    render() {
        this.container = document.createElement('div');
        this.container.className = 'arrowz-my-component';
        this.container.innerHTML = this.getTemplate();
        document.body.appendChild(this.container);
    },
    
    getTemplate() {
        return `
            <div class="arrowz-my-component-inner">
                <h3>${__('My Component')}</h3>
                <div class="content"></div>
            </div>
        `;
    },
    
    bindEvents() {
        if (!this.container) return;
        
        this.container.querySelector('.btn-action')?.addEventListener('click', 
            () => this.handleAction()
        );
    },
    
    subscribeToRealtime() {
        frappe.realtime.on('my_event', (data) => {
            this.handleRealtimeEvent(data);
        });
    },
    
    async handleAction() {
        try {
            const { message } = await frappe.call({
                method: 'arrowz.api.my_feature.my_action',
                args: { param: this.getValue() }
            });
            this.updateUI(message);
        } catch (err) {
            console.error('Arrowz my_component error:', err);
            frappe.throw(__('Action failed'));
        }
    },
    
    handleRealtimeEvent(data) {
        console.log('Arrowz realtime:', data);
        this.updateUI(data);
    },
    
    updateUI(data) {
        if (!this.container) return;
        const content = this.container.querySelector('.content');
        if (content) {
            content.textContent = JSON.stringify(data);
        }
    },
    
    cleanup() {
        if (this.container) {
            this.container.remove();
            this.container = null;
        }
        frappe.realtime.off('my_event');
    }
};

// Initialize when document ready
$(document).ready(() => {
    arrowz.my_component.init();
});
```

### Creating a New DocType Controller

```python
# arrowz/arrowz/doctype/az_my_doctype/az_my_doctype.py

import frappe
from frappe import _
from frappe.model.document import Document

class AZMyDoctype(Document):
    def validate(self):
        """Validate document before save."""
        self.validate_required_fields()
        self.set_computed_fields()
    
    def validate_required_fields(self):
        if not self.some_field:
            frappe.throw(_("Some Field is required"))
    
    def set_computed_fields(self):
        if self.start_time and self.end_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
    
    def before_save(self):
        """Hook before document is saved."""
        if self.is_new():
            self.set_defaults()
    
    def after_insert(self):
        """Hook after new document is inserted."""
        self.notify_users()
        self.create_related_records()
    
    def on_update(self):
        """Hook when document is updated."""
        self.publish_realtime_event()
    
    def on_trash(self):
        """Hook before document is deleted."""
        self.cleanup_related_records()
    
    def notify_users(self):
        frappe.publish_realtime(
            event="az_my_doctype_created",
            message={"name": self.name, "type": self.doctype},
            user=frappe.session.user
        )
    
    def publish_realtime_event(self):
        frappe.publish_realtime(
            event="az_my_doctype_updated",
            message={"name": self.name, "data": self.as_dict()}
        )
```

---

## 🔒 Security Guidelines

### API Security

```python
# Always check permissions
@frappe.whitelist()
def sensitive_operation(doc_name: str):
    # Method 1: Role-based
    frappe.only_for(["System Manager", "Arrowz Admin"])
    
    # Method 2: Document-based
    if not frappe.has_permission("AZ Extension", "write", doc_name):
        frappe.throw(_("No permission"), frappe.PermissionError)
    
    # Method 3: Custom logic
    user = frappe.session.user
    if not is_authorized_for_action(user, doc_name):
        frappe.throw(_("Not authorized"))
```

### Input Validation

```python
# Always validate and sanitize inputs
@frappe.whitelist()
def process_data(phone: str, extension: str):
    # Validate phone format
    import re
    if not re.match(r'^\+?[0-9]{10,15}$', phone):
        frappe.throw(_("Invalid phone number format"))
    
    # Check extension exists
    if not frappe.db.exists("AZ Extension", extension):
        frappe.throw(_("Extension not found"))
    
    # Sanitize for database
    phone = frappe.db.escape(phone)
```

### Secret Management

```python
# Never hardcode secrets
# ❌ Bad
api_key = "sk-abc123..."

# ✅ Good - use site config
api_key = frappe.conf.get("arrowz_api_key")

# ✅ Good - use DocType with Password field
api_key = frappe.utils.password.get_decrypted_password(
    "Arrowz Settings", 
    "Arrowz Settings",
    "api_key"
)
```

---

## 📝 Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| DocType | `AZ <Name>` | `AZ Call Log`, `AZ Extension` |
| Python module | snake_case | `call_log.py`, `webrtc.py` |
| Python function | snake_case | `get_extension()`, `make_call()` |
| Python class | PascalCase | `AZCallLog`, `VoIPManager` |
| JavaScript namespace | `arrowz.*` | `arrowz.softphone` |
| JavaScript function | camelCase | `initSoftphone()`, `handleCall()` |
| CSS class | `arrowz-*` | `arrowz-softphone`, `arrowz-panel` |
| Events | snake_case | `call_received`, `session_updated` |

---

## 🧪 Testing Patterns

### Python Tests

```python
# arrowz/tests/test_call_log.py

import frappe
import unittest

class TestCallLog(unittest.TestCase):
    def setUp(self):
        self.extension = frappe.get_doc({
            "doctype": "AZ Extension",
            "extension": "1001",
            "user": frappe.session.user
        }).insert()
    
    def tearDown(self):
        frappe.delete_doc("AZ Extension", self.extension.name, force=True)
    
    def test_create_call_log(self):
        call = frappe.get_doc({
            "doctype": "AZ Call Log",
            "caller": "1001",
            "receiver": "1002",
            "status": "Answered"
        }).insert()
        
        self.assertEqual(call.status, "Answered")
        self.assertIsNotNone(call.name)
    
    def test_call_duration_calculation(self):
        # Test logic
        pass
```

### JavaScript Tests (Manual)

```javascript
// Test in browser console
(async function testSoftphone() {
    console.log('=== Arrowz Softphone Tests ===');
    
    // Test 1: Softphone loaded
    console.assert(
        typeof arrowz.softphone !== 'undefined',
        'Softphone module should be loaded'
    );
    
    // Test 2: JsSIP loaded
    console.assert(
        typeof JsSIP !== 'undefined',
        'JsSIP library should be loaded'
    );
    
    // Test 3: API connectivity
    try {
        const { message } = await frappe.call({
            method: 'arrowz.api.webrtc.get_extension_config'
        });
        console.assert(message, 'API should return config');
        console.log('✅ All tests passed');
    } catch (e) {
        console.error('❌ API test failed:', e);
    }
})();
```

---

## 🔄 Common Modifications

### Adding a New Field to DocType

1. **Update JSON**: `az_call_log.json`
2. **Update Controller**: `az_call_log.py`
3. **Run migration**: `bench migrate`
4. **Update frontend** if needed

### Adding a New API Endpoint

1. **Create function** in `arrowz/api/`
2. **Add `@frappe.whitelist()`** decorator
3. **Call via JS**: `frappe.call({method: 'arrowz.api.module.function'})`

### Adding New Realtime Event

```python
# Server side
frappe.publish_realtime(
    event="new_event_name",
    message={"key": "value"},
    user=frappe.session.user
)
```

```javascript
// Client side
frappe.realtime.on("new_event_name", (data) => {
    console.log("Received:", data);
});
```

---

## 📚 Reference Links

- [Frappe Framework Docs](https://frappeframework.com/docs)
- [ERPNext Developer Docs](https://docs.erpnext.com)
- [JsSIP Documentation](https://jssip.net/documentation/)
- [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenMeetings REST API](https://openmeetings.apache.org/RestAPIsample.html)
