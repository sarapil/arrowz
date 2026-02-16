# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AZInboundRoute(Document):
    def validate(self):
        if not self.did_pattern:
            frappe.throw("DID Pattern is required")
        
        if self.priority and self.priority < 1:
            self.priority = 1
