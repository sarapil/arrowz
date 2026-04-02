"""
Arrowz — API Tests
Tests for all @frappe.whitelist() endpoints.
"""

import frappe
from frappe.tests import IntegrationTestCase


class TestAZAPI(IntegrationTestCase):
    """API endpoint tests for Arrowz."""

    def test_response_format(self):
        """All API responses follow standard format."""
        pass  # TODO: Test each whitelisted method
