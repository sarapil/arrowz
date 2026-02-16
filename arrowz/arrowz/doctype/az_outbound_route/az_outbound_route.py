# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AZOutboundRoute(Document):
    def validate(self):
        if not self.dial_pattern:
            frappe.throw("Dial Pattern is required")
        
        if self.priority and self.priority < 1:
            self.priority = 1
        
        if self.strip_digits and self.strip_digits < 0:
            self.strip_digits = 0
