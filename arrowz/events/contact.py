# Copyright (c) 2024, Arrowz Team
# License: MIT

"""
Contact Document Events

Handle events when Contact documents are created/updated.

NOTE (v16): Document event hooks must NOT call frappe.db.commit().
Use frappe.enqueue() for background processing if needed.
"""

import frappe


def after_insert(doc, method):
    """Called after a new Contact is created"""
    # Enqueue call linking to run after commit
    frappe.enqueue(
        "arrowz.events.contact.link_existing_calls_async",
        queue="short",
        contact_name=doc.name,
        enqueue_after_commit=True
    )


def on_update(doc, method):
    """Called when Contact is updated"""
    # If phone number changed, re-link calls
    if doc.has_value_changed("phone") or doc.has_value_changed("mobile_no"):
        frappe.enqueue(
            "arrowz.events.contact.link_existing_calls_async",
            queue="short",
            contact_name=doc.name,
            enqueue_after_commit=True
        )


def link_existing_calls_async(contact_name: str):
    """
    Link existing call logs to this contact.
    
    Runs as background job after document commit.
    
    Args:
        contact_name: Name of the Contact document
    """
    contact = frappe.get_doc("Contact", contact_name)
    link_existing_calls(contact)
    # Can commit in background job (not in hook)
    frappe.db.commit()


def link_existing_calls(contact):
    """
    Link existing call logs to this contact.
    
    Args:
        contact: Contact document
    """
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
            limit=50,
            order_by="creation desc"  # v16: explicit ordering
        )
        
        for call_name in unlinked_calls:
            frappe.db.set_value("AZ Call Log", call_name, {
                "party_type": "Contact",
                "party": contact.name
            }, update_modified=False)


def clean_phone(number: str) -> str:
    """
    Remove non-digit characters from phone number.
    
    Args:
        number: Phone number string
        
    Returns:
        Cleaned phone number with only digits
    """
    import re
    return re.sub(r'\D', '', number or '')
