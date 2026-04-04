# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# License: MIT

"""
AZ Omni Provider - Communication Provider Registry

This DocType serves as a registry for all supported communication providers
following the Driver Pattern to abstract provider-specific logic.

Supported Providers:
- WhatsApp Cloud API (Meta)
- Telegram Bot API
- Facebook Messenger
- Instagram Direct
- Viber Business
- LINE Messaging
- WeChat Official Accounts
- Signal (via signal-cli)
- SMS Gateways
- Push Notifications (FCM, OneSignal)
- Video Conferencing (OpenMeetings)
"""

import frappe
from frappe.model.document import Document
from frappe import _
import importlib


class AZOmniProvider(Document):
    """Omni-Channel Communication Provider Registry"""
    
    def validate(self):
        """Validate provider configuration"""
        self.validate_driver_class()
        self.generate_webhook_endpoint()
        self.set_default_capabilities()
    
    def validate_driver_class(self):
        """Validate that the driver class exists and is importable"""
        if self.driver_class:
            try:
                module_path, class_name = self.driver_class.rsplit('.', 1)
                module = importlib.import_module(module_path)
                if not hasattr(module, class_name):
                    frappe.throw(
                        _("Driver class '{0}' not found in module '{1}'").format(
                            class_name, module_path
                        )
                    )
            except ImportError as e:
                frappe.throw(
                    _("Cannot import driver module: {0}").format(str(e))
                )
            except ValueError:
                frappe.throw(
                    _("Invalid driver class path. Use format: module.path.ClassName")
                )
    
    def generate_webhook_endpoint(self):
        """Generate unique webhook endpoint for this provider"""
        if not self.webhook_endpoint:
            site_url = frappe.utils.get_url()
            provider_slug = frappe.scrub(self.provider_name)
            self.webhook_endpoint = f"{site_url}/api/method/arrowz.api.webhooks.{provider_slug}"
    
    def set_default_capabilities(self):
        """Set default capabilities based on provider type"""
        capability_map = {
            "WhatsApp Cloud API": {
                "supports_text": 1,
                "supports_media": 1,
                "supports_templates": 1,
                "supports_buttons": 1,
                "supports_location": 1,
                "supports_contacts": 1,
                "supports_reactions": 1,
                "max_file_size": 100,
                "base_url": "https://graph.facebook.com",
                "api_version": "v18.0",
                "auth_type": "Bearer Token",
                "signature_header": "X-Hub-Signature-256"
            },
            "Telegram Bot": {
                "supports_text": 1,
                "supports_media": 1,
                "supports_templates": 0,
                "supports_buttons": 1,
                "supports_location": 1,
                "supports_contacts": 1,
                "supports_reactions": 1,
                "max_file_size": 2048,  # 2GB
                "base_url": "https://api.telegram.org",
                "auth_type": "Bearer Token",
                "signature_header": "X-Telegram-Bot-Api-Secret-Token"
            },
            "Facebook Messenger": {
                "supports_text": 1,
                "supports_media": 1,
                "supports_templates": 1,
                "supports_buttons": 1,
                "supports_location": 0,
                "supports_contacts": 0,
                "supports_reactions": 0,
                "max_file_size": 25,
                "base_url": "https://graph.facebook.com",
                "api_version": "v18.0",
                "auth_type": "Bearer Token",
                "signature_header": "X-Hub-Signature-256"
            },
            "Video Conference": {
                "supports_text": 0,
                "supports_media": 1,
                "supports_templates": 0,
                "supports_buttons": 0,
                "supports_location": 0,
                "supports_contacts": 0,
                "supports_reactions": 0,
                "max_file_size": 500,
                "auth_type": "Basic Auth"
            }
        }
        
        if self.get("__islocal") and self.provider_type in capability_map:
            defaults = capability_map[self.provider_type]
            for field, value in defaults.items():
                if not self.get(field):
                    self.set(field, value)
    
    def get_driver(self):
        """Get an instance of the provider driver"""
        if not self.driver_class:
            frappe.throw(_("No driver class configured for this provider"))
        
        try:
            module_path, class_name = self.driver_class.rsplit('.', 1)
            module = importlib.import_module(module_path)
            driver_class = getattr(module, class_name)
            return driver_class(self)
        except Exception as e:
            frappe.log_error(f"Failed to instantiate driver: {str(e)}", "Omni Provider Error")
            frappe.throw(_("Failed to load provider driver: {0}").format(str(e)))
    
    @frappe.whitelist()
    def test_connection(self):
        """Test connection to the provider"""
        frappe.only_for(["System Manager"])

        try:
            driver = self.get_driver()
            result = driver.test_connection()
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }


@frappe.whitelist()
def get_available_providers():
    """Get list of enabled providers"""
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    providers = frappe.get_all(
        "AZ Omni Provider",
        filters={"is_enabled": 1},
        fields=["name", "provider_name", "provider_type", "icon", "color"]
    )
    return providers


@frappe.whitelist()
def get_provider_capabilities(provider_name):
    """Get capabilities of a specific provider"""
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    provider = frappe.get_doc("AZ Omni Provider", provider_name)
    return {
        "supports_text": provider.supports_text,
        "supports_media": provider.supports_media,
        "supports_templates": provider.supports_templates,
        "supports_buttons": provider.supports_buttons,
        "supports_location": provider.supports_location,
        "supports_contacts": provider.supports_contacts,
        "supports_reactions": provider.supports_reactions,
        "max_file_size": provider.max_file_size
    }
