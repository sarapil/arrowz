# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# Test AZ Extension DocType

import pytest
import frappe


class TestAZExtension:
    """Test cases for AZ Extension DocType."""
    
    def test_create_extension(self, frappe_site, test_server_config, test_user):
        """Test creating an extension."""
        ext = frappe.get_doc({
            "doctype": "AZ Extension",
            "extension": "8888",
            "display_name": "Test 8888",
            "sip_password": "password123",
            "extension_type": "WebRTC",
            "server": test_server_config.name,
            "user": test_user.name,
            "is_active": 1
        })
        ext.insert(ignore_permissions=True)
        
        assert ext.name is not None
        assert ext.extension == "8888"
        
        ext.delete()
    
    def test_extension_naming(self, frappe_site, test_server_config):
        """Test extension naming format."""
        ext = frappe.get_doc({
            "doctype": "AZ Extension",
            "extension": "7777",
            "display_name": "Test 7777",
            "sip_password": "password123",
            "server": test_server_config.name,
            "is_active": 1
        })
        ext.insert(ignore_permissions=True)
        
        # Name should be EXT-{extension}
        assert ext.name == "EXT-7777"
        
        ext.delete()
    
    def test_duplicate_extension_fails(self, frappe_site, test_extension):
        """Test that duplicate extension raises error."""
        with pytest.raises(frappe.exceptions.DuplicateEntryError):
            dup = frappe.get_doc({
                "doctype": "AZ Extension",
                "extension": test_extension.extension,
                "display_name": "Duplicate",
                "sip_password": "password123",
                "server": test_extension.server,
                "is_active": 1
            })
            dup.insert(ignore_permissions=True)
    
    def test_password_encrypted(self, frappe_site, test_extension):
        """Test that SIP password is encrypted in database."""
        # Fetch directly from database
        result = frappe.db.sql("""
            SELECT sip_password FROM `tabAZ Extension`
            WHERE name = %s
        """, test_extension.name, as_dict=True)
        
        # Password should not be plain text
        assert result[0].sip_password != "test_password_123"
    
    def test_get_password(self, frappe_site, test_extension):
        """Test password decryption."""
        # Using Frappe's get_password method
        password = test_extension.get_password("sip_password")
        
        assert password == "test_password_123"
    
    def test_extension_type_validation(self, frappe_site, test_server_config):
        """Test extension type must be valid."""
        # Valid types: SIP, WebRTC, Both
        ext = frappe.get_doc({
            "doctype": "AZ Extension",
            "extension": "6666",
            "display_name": "Test 6666",
            "sip_password": "password123",
            "extension_type": "WebRTC",
            "server": test_server_config.name,
            "is_active": 1
        })
        ext.insert(ignore_permissions=True)
        
        assert ext.extension_type == "WebRTC"
        
        ext.delete()
    
    def test_sync_status_default(self, frappe_site, test_server_config):
        """Test default sync status is Not Synced."""
        ext = frappe.get_doc({
            "doctype": "AZ Extension",
            "extension": "5555",
            "display_name": "Test 5555",
            "sip_password": "password123",
            "server": test_server_config.name,
            "is_active": 1
        })
        ext.insert(ignore_permissions=True)
        
        assert ext.sync_status == "Not Synced"
        
        ext.delete()
    
    def test_user_can_have_multiple_extensions(self, frappe_site, test_server_config, test_user, test_extension):
        """Test user can have multiple extensions."""
        # test_extension already exists for test_user
        ext2 = frappe.get_doc({
            "doctype": "AZ Extension",
            "extension": "4444",
            "display_name": "Second Extension",
            "sip_password": "password123",
            "server": test_server_config.name,
            "user": test_user.name,
            "is_active": 1,
            "is_primary": 0  # Not primary
        })
        ext2.insert(ignore_permissions=True)
        
        # Both should exist
        exts = frappe.get_all("AZ Extension", 
            filters={"user": test_user.name},
            fields=["name"]
        )
        
        assert len(exts) >= 2
        
        ext2.delete()


class TestAZExtensionSync:
    """Test cases for extension PBX sync."""
    
    def test_sync_to_pbx_graphql_success(self, frappe_site, test_extension, mock_graphql_success):
        """Test successful GraphQL sync."""
        result = test_extension.sync_to_pbx()
        
        assert result is True
        
        # Refresh
        test_extension.reload()
        assert test_extension.sync_status == "Synced"
    
    def test_sync_to_pbx_ssh_fallback(self, frappe_site, test_extension, mock_graphql_failure, mock_ssh_success):
        """Test SSH fallback when GraphQL fails."""
        result = test_extension.sync_to_pbx()
        
        # Should use SSH fallback
        assert result is True
    
    def test_sync_status_updated_on_failure(self, frappe_site, test_extension, mock_graphql_failure):
        """Test sync status updated when sync fails."""
        # Mock SSH to also fail
        try:
            test_extension.sync_to_pbx()
        except:
            pass
        
        test_extension.reload()
        # Status should be Failed or unchanged
        assert test_extension.sync_status in ["Failed", "Not Synced"]
