# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# Pytest fixtures for Arrowz tests

import pytest
import frappe


def pytest_configure(config):
    """Configure pytest for Frappe tests."""
    pass


@pytest.fixture(scope="session")
def frappe_site():
    """Initialize Frappe for test session."""
    frappe.init(site="dev.localhost")
    frappe.connect()
    frappe.set_user("Administrator")
    yield
    frappe.destroy()


@pytest.fixture(scope="function")
def test_user(frappe_site):
    """Create a test user."""
    user_email = "test_arrowz@example.com"
    
    if not frappe.db.exists("User", user_email):
        user = frappe.get_doc({
            "doctype": "User",
            "email": user_email,
            "first_name": "Test",
            "last_name": "User",
            "enabled": 1,
            "roles": [{"role": "System Manager"}]
        })
        user.insert(ignore_permissions=True)
    else:
        user = frappe.get_doc("User", user_email)
    
    yield user
    
    # Cleanup
    if frappe.db.exists("User", user_email):
        frappe.delete_doc("User", user_email, force=True)


@pytest.fixture(scope="function")
def test_server_config(frappe_site):
    """Create a test server config."""
    server_name = "TEST_SERVER"
    
    if frappe.db.exists("AZ Server Config", server_name):
        frappe.delete_doc("AZ Server Config", server_name, force=True)
    
    server = frappe.get_doc({
        "doctype": "AZ Server Config",
        "server_name": server_name,
        "server_type": "freepbx",
        "is_active": 1,
        "host": "test.example.com",
        "port": 443,
        "protocol": "https",
        "websocket_url": "wss://test.example.com:8089/ws",
        "sip_domain": "test.example.com",
        "graphql_enabled": 1,
        "graphql_url": "https://test.example.com/admin/api/api/gql",
        "graphql_client_id": "test_client_id",
        "graphql_client_secret": "test_secret"
    })
    server.insert(ignore_permissions=True)
    
    yield server
    
    # Cleanup
    if frappe.db.exists("AZ Server Config", server_name):
        frappe.delete_doc("AZ Server Config", server_name, force=True)


@pytest.fixture(scope="function")
def test_extension(frappe_site, test_server_config, test_user):
    """Create a test extension."""
    ext_name = "EXT-9999"
    
    if frappe.db.exists("AZ Extension", ext_name):
        frappe.delete_doc("AZ Extension", ext_name, force=True)
    
    ext = frappe.get_doc({
        "doctype": "AZ Extension",
        "extension": "9999",
        "display_name": "Test Extension",
        "sip_password": "test_password_123",
        "extension_type": "WebRTC",
        "server": test_server_config.name,
        "user": test_user.name,
        "is_active": 1,
        "is_primary": 1
    })
    ext.insert(ignore_permissions=True)
    
    yield ext
    
    # Cleanup
    if frappe.db.exists("AZ Extension", ext.name):
        frappe.delete_doc("AZ Extension", ext.name, force=True)


@pytest.fixture(scope="function")
def test_call_log(frappe_site, test_extension):
    """Create a test call log."""
    from frappe.utils import now_datetime
    
    call = frappe.get_doc({
        "doctype": "AZ Call Log",
        "extension": test_extension.extension,
        "phone_number": "+1234567890",
        "direction": "outbound",
        "status": "Completed",
        "call_start": now_datetime(),
        "duration": 120
    })
    call.insert(ignore_permissions=True)
    
    yield call
    
    # Cleanup
    if frappe.db.exists("AZ Call Log", call.name):
        frappe.delete_doc("AZ Call Log", call.name, force=True)


@pytest.fixture
def mock_graphql_success(mocker):
    """Mock successful GraphQL response."""
    mock = mocker.patch("arrowz.freepbx_token.execute_graphql")
    mock.return_value = {
        "data": {
            "addExtension": {
                "status": True,
                "message": "Extension created"
            }
        }
    }
    return mock


@pytest.fixture
def mock_graphql_failure(mocker):
    """Mock failed GraphQL response."""
    mock = mocker.patch("arrowz.freepbx_token.execute_graphql")
    mock.side_effect = Exception("401 Unauthorized")
    return mock


@pytest.fixture
def mock_ssh_success(mocker):
    """Mock successful SSH command."""
    mock = mocker.patch("arrowz.pbx_monitor.PBXMonitor._ssh_cmd")
    mock.return_value = ("Success", "", 0)
    return mock


@pytest.fixture
def mock_requests(mocker):
    """Mock requests library."""
    return mocker.patch("requests.post")
