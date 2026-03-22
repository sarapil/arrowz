# Test AZ Call Log DocType

import pytest
import frappe
from frappe.utils import now_datetime, add_to_date


class TestAZCallLog:
    """Test cases for AZ Call Log DocType."""
    
    def test_create_call_log(self, frappe_site, test_extension):
        """Test creating a call log."""
        call = frappe.get_doc({
            "doctype": "AZ Call Log",
            "extension": test_extension.extension,
            "phone_number": "+1234567890",
            "direction": "outbound",
            "status": "Initiated"
        })
        call.insert(ignore_permissions=True)
        
        assert call.name is not None
        assert call.name.startswith("CALL-")
        
        call.delete()
    
    def test_call_log_naming(self, frappe_site, test_extension):
        """Test call log naming format."""
        call = frappe.get_doc({
            "doctype": "AZ Call Log",
            "extension": test_extension.extension,
            "phone_number": "+1234567890",
            "direction": "inbound",
            "status": "Ringing"
        })
        call.insert(ignore_permissions=True)
        
        # Name should be CALL-YYYY-#####
        assert call.name.startswith("CALL-")
        
        call.delete()
    
    def test_call_date_auto_set(self, frappe_site, test_extension):
        """Test call date is automatically set."""
        call = frappe.get_doc({
            "doctype": "AZ Call Log",
            "extension": test_extension.extension,
            "phone_number": "+1234567890",
            "direction": "outbound",
            "status": "Initiated"
        })
        call.insert(ignore_permissions=True)
        
        assert call.call_date is not None
        
        call.delete()
    
    def test_duration_calculation(self, frappe_site, test_extension):
        """Test duration is calculated from start/end times."""
        start_time = now_datetime()
        end_time = add_to_date(start_time, seconds=180)
        
        call = frappe.get_doc({
            "doctype": "AZ Call Log",
            "extension": test_extension.extension,
            "phone_number": "+1234567890",
            "direction": "outbound",
            "status": "Completed",
            "call_start": start_time,
            "call_end": end_time
        })
        call.insert(ignore_permissions=True)
        
        # Duration should be 180 seconds
        assert call.duration == 180
        
        call.delete()
    
    def test_direction_validation(self, frappe_site, test_extension):
        """Test direction must be valid value."""
        # Valid directions: inbound, outbound, internal
        call = frappe.get_doc({
            "doctype": "AZ Call Log",
            "extension": test_extension.extension,
            "phone_number": "+1234567890",
            "direction": "inbound",
            "status": "Completed"
        })
        call.insert(ignore_permissions=True)
        
        assert call.direction == "inbound"
        
        call.delete()
    
    def test_status_transitions(self, frappe_site, test_extension):
        """Test call status transitions."""
        call = frappe.get_doc({
            "doctype": "AZ Call Log",
            "extension": test_extension.extension,
            "phone_number": "+1234567890",
            "direction": "outbound",
            "status": "Initiated"
        })
        call.insert(ignore_permissions=True)
        
        # Transition to Ringing
        call.status = "Ringing"
        call.save()
        assert call.status == "Ringing"
        
        # Transition to Answered
        call.status = "Answered"
        call.answer_time = now_datetime()
        call.save()
        assert call.status == "Answered"
        
        # Transition to Completed
        call.status = "Completed"
        call.call_end = now_datetime()
        call.save()
        assert call.status == "Completed"
        
        call.delete()
    
    def test_crm_linking(self, frappe_site, test_extension):
        """Test linking call to CRM document."""
        # Create a test contact
        contact = frappe.get_doc({
            "doctype": "Contact",
            "first_name": "Test",
            "last_name": "Contact"
        })
        contact.insert(ignore_permissions=True)
        
        call = frappe.get_doc({
            "doctype": "AZ Call Log",
            "extension": test_extension.extension,
            "phone_number": "+1234567890",
            "direction": "outbound",
            "status": "Completed",
            "party_type": "Contact",
            "party": contact.name
        })
        call.insert(ignore_permissions=True)
        
        assert call.party_type == "Contact"
        assert call.party == contact.name
        
        call.delete()
        contact.delete()
    
    def test_recording_fields(self, frappe_site, test_extension):
        """Test recording-related fields."""
        call = frappe.get_doc({
            "doctype": "AZ Call Log",
            "extension": test_extension.extension,
            "phone_number": "+1234567890",
            "direction": "outbound",
            "status": "Completed",
            "has_recording": 1,
            "recording_url": "/recordings/call-123.wav",
            "recording_duration": 120
        })
        call.insert(ignore_permissions=True)
        
        assert call.has_recording == 1
        assert call.recording_url == "/recordings/call-123.wav"
        
        call.delete()


class TestAZCallLogQueries:
    """Test cases for call log queries and filters."""
    
    def test_get_today_calls(self, frappe_site, test_call_log):
        """Test getting today's calls."""
        from frappe.utils import today
        
        calls = frappe.get_all("AZ Call Log",
            filters={"call_date": today()},
            fields=["name"]
        )
        
        assert len(calls) >= 1
    
    def test_get_calls_by_extension(self, frappe_site, test_call_log):
        """Test filtering calls by extension."""
        calls = frappe.get_all("AZ Call Log",
            filters={"extension": test_call_log.extension},
            fields=["name"]
        )
        
        assert len(calls) >= 1
    
    def test_get_missed_calls(self, frappe_site, test_extension):
        """Test getting missed calls."""
        # Create a missed call
        call = frappe.get_doc({
            "doctype": "AZ Call Log",
            "extension": test_extension.extension,
            "phone_number": "+9876543210",
            "direction": "inbound",
            "status": "Missed"
        })
        call.insert(ignore_permissions=True)
        
        missed = frappe.get_all("AZ Call Log",
            filters={"status": "Missed"},
            fields=["name"]
        )
        
        assert len(missed) >= 1
        
        call.delete()
