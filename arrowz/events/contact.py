# Copyright (c) 2024, Arrowz Team
# License: MIT

"""
Contact Document Events

Handle events when Contact documents are created/updated.
"""

import frappe


def after_insert(doc, method):
    """Called after a new Contact is created"""
    # Check for recent calls from this contact's phone numbers
    link_existing_calls(doc)


def on_update(doc, method):
    """Called when Contact is updated"""
    # If phone number changed, re-link calls
    if doc.has_value_changed("phone") or doc.has_value_changed("mobile_no"):
        link_existing_calls(doc)


def link_existing_calls(contact):
    """Link existing call logs to this contact"""
    phone_numbers = []
    
    if contact.phone:
        phone_numbers.append(clean_phone(contact.phone))
    if contact.mobile_no:
        phone_numbers.append(clean_phone(contact.mobile_no))
    
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
                "party_type": "Contact",
                "party": contact.name
            })
    
    if unlinked_calls:
        frappe.db.commit()


def clean_phone(number):
    """Remove non-digit characters from phone number"""
    import re
    return re.sub(r'\D', '', number or '')
