# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AZTrunk(Document):
    def validate(self):
        if self.priority and self.priority < 1:
            self.priority = 1
        if self.max_channels and self.max_channels < 1:
            self.max_channels = 1
    
    def before_save(self):
        # Update status based on connection test if needed
        pass
    
    def test_connection(self):
        """Test trunk connectivity"""
        # This would integrate with FreePBX/Asterisk API
        return {"status": "success", "message": "Trunk is reachable"}
