# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, time_diff_in_seconds


class AZCallLog(Document):
    """
    AZ Call Log DocType
    Records all call activities with CRM integration, recordings, and AI analysis.
    """
    
    def before_save(self):
        """Calculate durations and update CRM info before saving."""
        self.calculate_durations()
        self.resolve_crm_contact()
        self.generate_recording_url()
    
    def calculate_durations(self):
        """Calculate call duration, ring duration, and hold duration."""
        if self.start_time and self.end_time:
            self.duration = int(time_diff_in_seconds(self.end_time, self.start_time))
        
        if self.start_time and self.answer_time:
            self.ring_duration = int(time_diff_in_seconds(self.answer_time, self.start_time))
    
    def resolve_crm_contact(self):
        """Resolve caller/callee to CRM contact."""
        if self.party and self.party_type:
            # Already linked, get the display name
            try:
                doc = frappe.get_doc(self.party_type, self.party)
                if hasattr(doc, 'customer_name'):
                    self.contact_name = doc.customer_name
                elif hasattr(doc, 'lead_name'):
                    self.contact_name = doc.lead_name
                elif hasattr(doc, 'name'):
                    self.contact_name = doc.name
            except Exception:
                pass
            return
        
        # Try to find matching contact
        phone = self.caller_id if self.direction == "Inbound" else self.callee_id
        if not phone:
            return
        
        # Clean phone number
        phone_clean = self.clean_phone_number(phone)
        
        # Search in configured DocTypes
        settings = frappe.get_single("Arrowz Settings")
        if not settings.enable_crm_integration:
            return
        
        search_doctypes = ["Lead", "Customer", "Contact"]
        
        for doctype in search_doctypes:
            try:
                result = self.search_by_phone(doctype, phone_clean)
                if result:
                    self.party_type = doctype
                    self.party = result.get("name")
                    self.contact_name = result.get("display_name", result.get("name"))
                    break
            except Exception:
                continue
    
    def clean_phone_number(self, phone):
        """Clean phone number for matching."""
        import re
        return re.sub(r'[^\d]', '', phone)[-10:]
    
    def search_by_phone(self, doctype, phone):
        """Search for a record by phone number."""
        phone_fields = {
            "Lead": ["mobile_no", "phone"],
            "Customer": ["mobile_no", "phone"],
            "Contact": ["mobile_no", "phone"]
        }
        
        fields = phone_fields.get(doctype, ["mobile_no", "phone"])
        
        for field in fields:
            try:
                results = frappe.db.sql("""
                    SELECT name, 
                           COALESCE({title_field}, name) as display_name
                    FROM `tab{doctype}`
                    WHERE REPLACE(REPLACE(REPLACE({field}, '-', ''), ' ', ''), '+', '') LIKE %s
                    LIMIT 1
                """.format(
                    doctype=doctype,
                    field=field,
                    title_field="lead_name" if doctype == "Lead" else ("customer_name" if doctype == "Customer" else "first_name")
                ), (f"%{phone}",), as_dict=True)
                
                if results:
                    return results[0]
            except Exception:
                continue
        
        return None
    
    def generate_recording_url(self):
        """Generate internal URL for recording playback."""
        if self.has_recording and self.recording_path and not self.recording_url:
            self.recording_url = f"/api/method/arrowz.api.recording.stream?call_log={self.name}"
    
    def end_call(self, disposition="ANSWERED"):
        """Mark call as ended with final disposition."""
        self.end_time = now_datetime()
        self.status = "Completed"
        self.disposition = disposition
        self.save(ignore_permissions=True)
        
        # Emit event for real-time updates
        frappe.publish_realtime(
            "call_ended",
            {
                "call_log": self.name,
                "duration": self.duration,
                "disposition": self.disposition
            },
            user=frappe.session.user
        )
    
    def update_from_ami_event(self, event_data):
        """Update call log from AMI event data."""
        # Map AMI event fields to DocType fields
        field_mapping = {
            "CallerIDNum": "caller_id",
            "CallerIDName": "contact_name",
            "Exten": "callee_id",
            "Channel": "channel_id",
            "LinkedChannel": "linked_channel_id",
            "Uniqueid": "call_id"
        }
        
        for ami_field, doc_field in field_mapping.items():
            if ami_field in event_data and event_data[ami_field]:
                setattr(self, doc_field, event_data[ami_field])
        
        self.save(ignore_permissions=True)
    
    @frappe.whitelist()
    def request_ai_analysis(self):
        """Request AI analysis for this call (sentiment, summary, transcript)."""
        if not self.has_recording:
            frappe.throw("No recording available for AI analysis")
        
        # Queue background job
        frappe.enqueue(
            "arrowz.api.ai.analyze_call",
            call_log=self.name,
            queue="long"
        )
        
        return {"status": "queued", "message": "AI analysis has been queued"}
    
    @frappe.whitelist()
    def play_recording(self):
        """Get recording playback URL."""
        if not self.has_recording:
            frappe.throw("No recording available")
        
        return {
            "url": self.recording_url or f"/api/method/arrowz.api.recording.stream?call_log={self.name}",
            "duration": self.recording_duration,
            "format": "mp3"
        }


@frappe.whitelist()
def create_call_log(direction, caller_id, callee_id, extension=None, server=None):
    """Create a new call log entry."""
    doc = frappe.get_doc({
        "doctype": "AZ Call Log",
        "direction": direction,
        "caller_id": caller_id,
        "callee_id": callee_id,
        "extension": extension,
        "server": server,
        "start_time": now_datetime(),
        "status": "Ringing"
    })
    doc.insert(ignore_permissions=True)
    return doc


@frappe.whitelist()
def get_call_history(party_type=None, party=None, extension=None, limit=20):
    """Get call history for a party or extension."""
    filters = {}
    
    if party_type and party:
        filters["party_type"] = party_type
        filters["party"] = party
    
    if extension:
        filters["extension"] = extension
    
    calls = frappe.get_all(
        "AZ Call Log",
        filters=filters,
        fields=[
            "name", "direction", "status", "disposition",
            "caller_id", "callee_id", "contact_name",
            "start_time", "duration", "has_recording",
            "sentiment_label"
        ],
        order_by="start_time desc",
        limit=limit
    )
    
    return calls


@frappe.whitelist()
def get_call_statistics(date_from=None, date_to=None, extension=None):
    """Get call statistics for reporting."""
    from frappe.utils import getdate, today
    
    if not date_from:
        date_from = today()
    if not date_to:
        date_to = today()
    
    filters = {
        "start_time": ["between", [date_from, date_to]]
    }
    
    if extension:
        filters["extension"] = extension
    
    # Total calls
    total = frappe.db.count("AZ Call Log", filters=filters)
    
    # By direction
    inbound = frappe.db.count("AZ Call Log", {**filters, "direction": "Inbound"})
    outbound = frappe.db.count("AZ Call Log", {**filters, "direction": "Outbound"})
    
    # By disposition
    answered = frappe.db.count("AZ Call Log", {**filters, "disposition": "ANSWERED"})
    missed = frappe.db.count("AZ Call Log", {**filters, "disposition": "NO ANSWER"})
    
    # Average duration
    avg_duration = frappe.db.sql("""
        SELECT AVG(duration) as avg_duration
        FROM `tabAZ Call Log`
        WHERE start_time BETWEEN %s AND %s
        AND duration > 0
    """, (date_from, date_to))[0][0] or 0
    
    return {
        "total_calls": total,
        "inbound": inbound,
        "outbound": outbound,
        "answered": answered,
        "missed": missed,
        "answer_rate": round((answered / total * 100) if total > 0 else 0, 1),
        "avg_duration_seconds": round(avg_duration, 0)
    }
