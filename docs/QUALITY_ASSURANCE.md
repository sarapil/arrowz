# Arrowz Quality Assurance Guide

> **Last Updated:** February 17, 2026  
> **Version:** 1.0.0

---

## 📋 Quality Standards

### Code Quality Metrics
| Metric | Target | Current |
|--------|--------|---------|
| Test Coverage | >80% | ~40% |
| Code Duplication | <5% | ~8% |
| Cyclomatic Complexity | <15 | ~12 |
| Documentation Coverage | 100% | 60% |

### Performance Targets
| Metric | Target | Current |
|--------|--------|---------|
| API Response Time | <200ms | ~500ms |
| Call Setup Time | <3s | ~30s (issue) |
| Page Load Time | <2s | ~1.5s |
| WebSocket Latency | <100ms | ~50ms |

---

## 🧪 Testing Strategy

### Test Pyramid
```
         /\
        /  \
       / E2E \        (10%)  - Full user flows
      /--------\
     / Integration \  (30%)  - API, integrations
    /--------------\
   /     Unit       \ (60%)  - Functions, DocTypes
  /------------------\
```

### Test Categories

#### 1. Unit Tests
- DocType validation
- Utility functions
- Business logic
- Data transformations

#### 2. Integration Tests
- FreePBX API sync
- WhatsApp webhook processing
- Database operations
- Redis cache operations

#### 3. End-to-End Tests
- Softphone registration flow
- Complete call lifecycle
- Message sending flow
- Meeting creation flow

---

## 📁 Test File Structure

```
arrowz/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── test_doctypes/
│   │   ├── test_az_call_log.py
│   │   ├── test_az_extension.py
│   │   └── test_az_server_config.py
│   ├── test_api/
│   │   ├── test_webrtc_api.py
│   │   ├── test_sms_api.py
│   │   └── test_analytics_api.py
│   ├── test_integrations/
│   │   ├── test_freepbx.py
│   │   ├── test_whatsapp.py
│   │   └── test_telegram.py
│   └── test_e2e/
│       ├── test_call_flow.py
│       └── test_message_flow.py
```

---

## 🔧 Test Configuration

### conftest.py
```python
import pytest
import frappe

@pytest.fixture(scope="module")
def test_site():
    """Setup test site context."""
    frappe.init(site="test_site")
    frappe.connect()
    yield
    frappe.destroy()

@pytest.fixture
def test_extension():
    """Create test extension."""
    ext = frappe.get_doc({
        "doctype": "AZ Extension",
        "extension": "9999",
        "display_name": "Test Extension",
        "sip_password": "test123",
        "is_active": 1
    })
    ext.insert(ignore_permissions=True)
    yield ext
    ext.delete()

@pytest.fixture
def mock_freepbx(mocker):
    """Mock FreePBX API responses."""
    return mocker.patch("arrowz.freepbx_token.execute_graphql")
```

---

## 📝 Test Examples

### DocType Test
```python
# tests/test_doctypes/test_az_call_log.py

import pytest
import frappe

class TestAZCallLog:
    
    def test_create_call_log(self, test_site):
        """Test creating a call log."""
        call = frappe.get_doc({
            "doctype": "AZ Call Log",
            "extension": "1001",
            "phone_number": "+1234567890",
            "direction": "outbound",
            "status": "Initiated"
        })
        call.insert(ignore_permissions=True)
        
        assert call.name is not None
        assert call.call_date is not None
        
        call.delete()
    
    def test_call_duration_calculation(self, test_site):
        """Test duration is calculated correctly."""
        from frappe.utils import now_datetime, add_to_date
        
        call = frappe.get_doc({
            "doctype": "AZ Call Log",
            "extension": "1001",
            "phone_number": "+1234567890",
            "direction": "inbound",
            "status": "Completed",
            "call_start": now_datetime(),
            "call_end": add_to_date(now_datetime(), seconds=120)
        })
        call.insert(ignore_permissions=True)
        
        assert call.duration == 120
        
        call.delete()
    
    def test_invalid_direction_fails(self, test_site):
        """Test that invalid direction raises error."""
        with pytest.raises(frappe.exceptions.ValidationError):
            call = frappe.get_doc({
                "doctype": "AZ Call Log",
                "extension": "1001",
                "direction": "invalid"
            })
            call.insert()
```

### API Test
```python
# tests/test_api/test_webrtc_api.py

import pytest
import frappe

class TestWebRTCAPI:
    
    def test_get_sip_credentials_authenticated(self, test_site, test_extension):
        """Test getting SIP credentials for logged in user."""
        frappe.set_user("Administrator")
        
        from arrowz.api.webrtc import get_sip_credentials
        result = get_sip_credentials()
        
        assert result.get("success") is True
        assert "extension" in result.get("data", {})
    
    def test_get_sip_credentials_no_extension(self, test_site):
        """Test error when user has no extension."""
        # Create user without extension
        frappe.set_user("guest@example.com")
        
        from arrowz.api.webrtc import get_sip_credentials
        result = get_sip_credentials()
        
        assert result.get("success") is False
    
    def test_make_call_validates_number(self, test_site, test_extension):
        """Test that make_call validates phone number."""
        from arrowz.api.webrtc import make_call
        
        with pytest.raises(frappe.exceptions.ValidationError):
            make_call(extension="9999", phone_number="invalid")
```

### Integration Test
```python
# tests/test_integrations/test_freepbx.py

import pytest
from unittest.mock import MagicMock

class TestFreePBXIntegration:
    
    def test_graphql_token_refresh(self, test_site, mock_freepbx):
        """Test token refresh on 401."""
        from arrowz.freepbx_token import FreePBXTokenManager
        
        # First call returns 401, second succeeds
        mock_freepbx.side_effect = [
            Exception("401 Unauthorized"),
            {"data": {"success": True}}
        ]
        
        # Test token refresh logic
        # ...
    
    def test_ssh_fallback_on_graphql_failure(self, test_site, mocker):
        """Test SSH fallback when GraphQL fails."""
        # Mock GraphQL failure
        mocker.patch(
            "arrowz.freepbx_token.execute_graphql",
            side_effect=Exception("401 Unauthorized")
        )
        
        # Mock SSH success
        mock_ssh = mocker.patch("arrowz.pbx_monitor.PBXMonitor._ssh_cmd")
        mock_ssh.return_value = ("success", "", 0)
        
        # Test extension sync uses SSH
        # ...
```

---

## 🔄 Continuous Integration

### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml

name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mariadb:
        image: mariadb:10.6
        env:
          MYSQL_ROOT_PASSWORD: root
        ports:
          - 3306:3306
      
      redis:
        image: redis:alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Dependencies
        run: |
          pip install frappe-bench
          bench init --frappe-branch version-15 frappe-bench
          cd frappe-bench
          bench get-app arrowz $GITHUB_WORKSPACE
          bench new-site test_site --db-root-password root --admin-password admin
          bench --site test_site install-app arrowz
      
      - name: Run Tests
        run: |
          cd frappe-bench
          bench --site test_site run-tests --app arrowz --coverage
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
```

---

## 📊 Code Review Checklist

### Before Submitting PR

- [ ] All tests pass locally
- [ ] New code has tests
- [ ] No console.log or print statements
- [ ] Docstrings added for new functions
- [ ] Type hints added (Python)
- [ ] Error handling implemented
- [ ] Security considerations checked
- [ ] Performance impact assessed

### Review Criteria

| Category | Criteria |
|----------|----------|
| Functionality | Works as expected |
| Tests | Adequate coverage |
| Security | No vulnerabilities |
| Performance | No degradation |
| Code Style | Follows conventions |
| Documentation | Updated if needed |

---

## 🔒 Security Testing

### OWASP Top 10 Checks
- [ ] SQL Injection
- [ ] XSS Prevention
- [ ] CSRF Protection
- [ ] Authentication Bypass
- [ ] Sensitive Data Exposure
- [ ] Access Control
- [ ] Security Misconfiguration

### Security Test Examples
```python
def test_sql_injection_prevention(test_site):
    """Test that SQL injection is prevented."""
    malicious_input = "'; DROP TABLE tabAZ Call Log; --"
    
    # This should not execute the DROP statement
    result = frappe.db.get_list("AZ Call Log",
        filters={"phone_number": malicious_input}
    )
    
    # Table should still exist
    assert frappe.db.table_exists("tabAZ Call Log")

def test_xss_prevention(test_site):
    """Test that XSS is prevented in display name."""
    xss_payload = "<script>alert('xss')</script>"
    
    ext = frappe.get_doc({
        "doctype": "AZ Extension",
        "extension": "9998",
        "display_name": xss_payload
    })
    ext.insert(ignore_permissions=True)
    
    # Script tags should be escaped
    assert "<script>" not in ext.display_name
```

---

## 📈 Performance Testing

### Load Test Configuration
```python
# locustfile.py

from locust import HttpUser, task, between

class ArrowzUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_call_logs(self):
        self.client.get("/api/resource/AZ Call Log?limit=20")
    
    @task(2)
    def get_analytics(self):
        self.client.post("/api/method/arrowz.api.analytics.get_dashboard_data")
    
    @task(1)
    def send_sms(self):
        self.client.post("/api/method/arrowz.api.sms.send_sms",
            json={"to": "+1234567890", "message": "Test"})
```

### Running Load Tests
```bash
locust -f locustfile.py --host=http://localhost:8001
```

---

## 🐛 Bug Tracking

### Issue Template
```markdown
## Bug Report

**Description:**
Clear description of the bug

**Steps to Reproduce:**
1. Step 1
2. Step 2
3. ...

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- Frappe Version:
- Arrowz Version:
- Browser:
- OS:

**Screenshots/Logs:**
Attach relevant screenshots or error logs
```

### Severity Levels
| Level | Description | Response Time |
|-------|-------------|---------------|
| Critical | System down | 4 hours |
| High | Major feature broken | 24 hours |
| Medium | Feature impaired | 1 week |
| Low | Minor issue | 2 weeks |

---

## 📚 Documentation Standards

### Docstring Format
```python
def send_sms(to: str, message: str, provider: str = None) -> dict:
    """
    Send an SMS message.
    
    Args:
        to: Recipient phone number (E.164 format)
        message: Message content (max 160 chars)
        provider: SMS provider name (optional, uses default)
    
    Returns:
        dict: {
            "success": bool,
            "message_id": str,
            "status": str
        }
    
    Raises:
        ValidationError: If phone number is invalid
        ProviderError: If SMS gateway fails
    
    Example:
        >>> send_sms("+1234567890", "Hello!")
        {"success": True, "message_id": "SMS-001", "status": "sent"}
    """
```

---

*Quality is not an act, it's a habit. - Aristotle*
