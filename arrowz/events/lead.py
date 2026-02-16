# Copyright (c) 2024, Arrowz Team
# License: MIT

"""
Lead Document Events

Handle events when Lead documents are created/updated.
"""

import frappe


def after_insert(doc, method):
    """Called after a new Lead is created"""
    # Check for recent calls from this lead's phone numbers
    link_existing_calls(doc)


def link_existing_calls(lead):
    """Link existing call logs to this lead"""
    phone_numbers = []
    
    if lead.phone:
        phone_numbers.append(clean_phone(lead.phone))
    if lead.mobile_no:
        phone_numbers.append(clean_phone(lead.mobile_no))
    
    if not phone_numbers:
        return
    
    # Find unlinked calls from these numbers
    for phone in phone_numbers:
        if len(phone) < 7:
            continue
        
        # Get last 10 digits for matching
        search_pattern = phone[-10:] if len(phone) >= 10 else phone
        
        unlinked_calls = frappe.db.get_all(
            "AZ Call Log",
            filters={
                "caller_id": ["like", f"%{search_pattern}%"],
                "party_type": ["is", "not set"]
            },
            pluck="name",
            limit=50
        )
        
        for call_name in unlinked_calls:
            frappe.db.set_value("AZ Call Log", call_name, {
                "party_type": "Lead",
                "party": lead.name
            })
    
    if unlinked_calls:
        frappe.db.commit()


def clean_phone(number):
    """Remove non-digit characters from phone number"""
    import re
    return re.sub(r'\D', '', number or '')
