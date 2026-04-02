# Copyright (c) 2026, Arrowz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, time_diff_in_seconds


class AZCallTransferLog(Document):
    """
    AZ Call Transfer Log DocType
    Tracks all call transfers with full audit trail for attended and blind transfers.
    """
    
    def before_save(self):
        """Calculate consultation duration for attended transfers."""
        if self.transfer_type == "Attended":
            if self.consultation_start and self.consultation_ended:
                self.consultation_duration = int(
                    time_diff_in_seconds(self.consultation_ended, self.consultation_start)
                )
    
    def complete_transfer(self, new_call_log=None):
        """Mark transfer as completed."""
        self.status = "Completed"
        self.result = "Transferred"
        self.transfer_completed = now_datetime()
        
        if new_call_log:
            self.new_call_log = new_call_log
        
        self.save(ignore_permissions=True)
        
        # Update original call log
        if self.call_log:
            frappe.db.set_value("AZ Call Log", self.call_log, {
                "was_transferred": 1,
                "transfer_type": self.transfer_type,
                "transferred_from": self.from_extension,
                "transferred_to": self.to_extension or self.to_external_number,
                "transfer_time": self.transfer_completed
            })
        
        # Emit real-time event
        frappe.publish_realtime(
            "transfer_completed",
            {
                "transfer_log": self.name,
                "call_log": self.call_log,
                "to_extension": self.to_extension
            }
        )
    
    def fail_transfer(self, reason=None):
        """Mark transfer as failed."""
        self.status = "Failed"
        self.result = "No Answer"
        self.failure_reason = reason
        self.save(ignore_permissions=True)
        
        frappe.publish_realtime(
            "transfer_failed",
            {
                "transfer_log": self.name,
                "call_log": self.call_log,
                "reason": reason
            },
            user=self.initiated_by
        )
    
    def cancel_transfer(self):
        """Cancel an in-progress transfer."""
        self.status = "Cancelled"
        self.result = "Cancelled"
        self.save(ignore_permissions=True)


@frappe.whitelist()
def initiate_transfer(call_log, transfer_type, to_extension=None, to_external=None):
    """Initiate a new call transfer."""
    frappe.only_for(["AZ Manager", "System Manager"])

    call = frappe.get_doc("AZ Call Log", call_log)
    
    doc = frappe.get_doc({
        "doctype": "AZ Call Transfer Log",
        "call_log": call_log,
        "transfer_type": transfer_type,
        "status": "Initiated",
        "initiated_by": frappe.session.user,
        "initiated_at": now_datetime(),
        "from_extension": call.extension,
        "from_user": frappe.session.user,
        "to_extension": to_extension,
        "to_external_number": to_external
    })
    doc.insert(ignore_permissions=True)
    
    return doc


@frappe.whitelist()
def start_consultation(transfer_log):
    """Start attended transfer consultation phase."""
    frappe.only_for(["AZ Manager", "System Manager"])

    doc = frappe.get_doc("AZ Call Transfer Log", transfer_log)
    doc.status = "Consulting"
    doc.consultation_start = now_datetime()
    doc.save(ignore_permissions=True)
    return doc


@frappe.whitelist()
def complete_attended_transfer(transfer_log, new_call_log=None):
    """Complete an attended transfer after consultation."""
    frappe.only_for(["AZ Manager", "System Manager"])

    doc = frappe.get_doc("AZ Call Transfer Log", transfer_log)
    doc.consultation_ended = now_datetime()
    doc.complete_transfer(new_call_log)
    return doc
