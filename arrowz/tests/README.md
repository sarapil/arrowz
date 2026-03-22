# Arrowz Test Suite

> **Last Updated:** February 17, 2026

---

## Test Files Structure

```
tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures
├── test_doctypes/
│   ├── __init__.py
│   ├── test_az_extension.py       # Extension tests
│   ├── test_az_call_log.py        # Call log tests
│   └── test_az_server_config.py   # Server config tests
├── test_api/
│   ├── __init__.py
│   ├── test_webrtc_api.py         # WebRTC API tests
│   ├── test_sms_api.py            # SMS API tests
│   └── test_analytics_api.py      # Analytics tests
├── test_integrations/
│   ├── __init__.py
│   ├── test_freepbx.py            # FreePBX tests
│   └── test_graphql_token.py      # Token manager tests
└── test_utils/
    ├── __init__.py
    └── test_validators.py         # Validation tests
```

---

## Running Tests

```bash
# All tests
bench --site dev.localhost run-tests --app arrowz

# Specific module
bench --site dev.localhost run-tests --app arrowz --module arrowz.tests.test_doctypes

# With coverage
bench --site dev.localhost run-tests --app arrowz --coverage

# Specific test file
bench --site dev.localhost run-tests --app arrowz --doctype "AZ Extension"
```

---

## Test Coverage Goals

| Module | Current | Target |
|--------|---------|--------|
| DocTypes | 35% | 80% |
| API | 25% | 80% |
| Integrations | 20% | 70% |
| Utils | 50% | 90% |
| **Overall** | **~35%** | **80%** |

---

*Run tests frequently to maintain quality.*
