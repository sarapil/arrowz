# Copyright (c) 2024, Arrowz Team
# License: MIT

"""
Lead Document Events

Handle events when Lead documents are created/updated.

NOTE (v16): Document event hooks must NOT call frappe.db.commit().
Use frappe.enqueue() for background processing if needed.
"""

import frappe


def after_insert(doc, method):
    """Called after a new Lead is created"""
    # Enqueue call linking to run after commit
    # This avoids issues with v16's prohibition on commit() in hooks
    frappe.enqueue(
        "arrowz.events.lead.link_existing_calls_async",
        queue="short",
        lead_name=doc.name,
        enqueue_after_commit=True
    )


def link_existing_calls_async(lead_name: str):
    """
    Link existing call logs to this lead.
    
    Runs as background job after document commit.
    
    Args:
        lead_name: Name of the Lead document
    """
    lead = frappe.get_doc("Lead", lead_name)
    link_existing_calls(lead)
    # Can commit in background job (not in hook)
    frappe.db.commit()


def link_existing_calls(lead):
    """
    Link existing call logs to this lead.
    
    Args:
        lead: Lead document
    """
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
            limit=50,
            order_by="creation desc"  # v16: explicit ordering
        )
        
        for call_name in unlinked_calls:
            frappe.db.set_value("AZ Call Log", call_name, {
                "party_type": "Lead",
                "party": lead.name
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
