# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ArrowzSettings(Document):
    def validate(self):
        if self.enable_ai_features and not self.openai_api_key:
            frappe.throw("OpenAI API Key is required when AI features are enabled")
        
        if self.sla_warning_threshold >= self.sla_threshold_seconds:
            frappe.throw("SLA Warning Threshold must be less than SLA Threshold")
    
    @frappe.whitelist()
    def test_openai_connection(self):
        """Test OpenAI API connection"""
        frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

        if not self.openai_api_key:
            return {"success": False, "message": "API Key not configured"}
        
        try:
            import openai
            client = openai.OpenAI(api_key=self.get_password("openai_api_key"))
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return {"success": True, "message": "Connection successful"}
        except Exception as e:
            return {"success": False, "message": str(e)}


def get_settings():
    """Get Arrowz Settings singleton"""
    return frappe.get_single("Arrowz Settings")
