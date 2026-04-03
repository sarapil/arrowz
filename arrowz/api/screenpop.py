# Copyright (c) 2024, Arrowz Team
# License: MIT

"""
Screen Pop API

Search and display caller information from CRM
"""

import frappe
from frappe import _
from frappe.utils import getdate, nowdate


@frappe.whitelist()
def search_caller(phone_number: str) -> dict:
    """
    Search for caller in CRM doctypes
    
    Args:
        phone_number: Phone number to search
        
    Returns:
        dict with matches found
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not phone_number:
        return {"matches": []}
    
    # Clean phone number for search
    clean_number = clean_phone_number(phone_number)
    search_patterns = generate_search_patterns(clean_number)
    
    matches = []
    
    # Search in Contact
    contacts = search_in_doctype(
        "Contact",
        ["phone", "mobile_no"],
        search_patterns
    )
    for c in contacts:
        info = get_contact_info(c.name)
        matches.append({
            "doctype": "Contact",
            "name": c.name,
            "display_name": c.full_name or c.name,
            "info": info
        })
    
    # Search in Lead
    leads = search_in_doctype(
        "Lead",
        ["phone", "mobile_no"],
        search_patterns
    )
    for l in leads:
        info = get_lead_info(l.name)
        matches.append({
            "doctype": "Lead",
            "name": l.name,
            "display_name": l.lead_name or l.name,
            "info": info
        })
    
    # Search in Customer
    customers = search_in_doctype(
        "Customer",
        ["mobile_no"],
        search_patterns
    )
    for c in customers:
        info = get_customer_info(c.name)
        matches.append({
            "doctype": "Customer",
            "name": c.name,
            "display_name": c.customer_name or c.name,
            "info": info
        })
    
    # Search in Supplier
    suppliers = search_in_doctype(
        "Supplier",
        ["mobile_no"],
        search_patterns
    )
    for s in suppliers:
        matches.append({
            "doctype": "Supplier",
            "name": s.name,
            "display_name": s.supplier_name or s.name,
            "info": {}
        })
    
    return {
        "matches": matches,
        "phone_number": phone_number
    }


def clean_phone_number(number: str) -> str:
    """Remove non-digits from phone number"""
    import re
    return re.sub(r'\D', '', number)


def generate_search_patterns(clean_number: str) -> list:
    """Generate patterns to search for phone number"""
    patterns = [clean_number]
    
    # Last 10 digits
    if len(clean_number) >= 10:
        patterns.append(clean_number[-10:])
    
    # Last 9 digits
    if len(clean_number) >= 9:
        patterns.append(clean_number[-9:])
    
    # With common prefixes
    if len(clean_number) >= 10:
        patterns.append(f"+{clean_number}")
        patterns.append(f"+1{clean_number[-10:]}")
    
    return list(set(patterns))


def search_in_doctype(doctype: str, fields: list, patterns: list) -> list:
    """Search in a doctype for phone patterns using parameterized queries."""
    results = []

    # Check if doctype exists
    if not frappe.db.exists("DocType", doctype):
        return results

    # Validate doctype name against meta (prevents table name injection)
    try:
        meta = frappe.get_meta(doctype)
    except Exception:
        return results

    # Build parameterized conditions
    conditions = []
    params = []
    valid_fields = []
    for field in fields:
        if not meta.has_field(field):
            continue
        valid_fields.append(field)
        for pattern in patterns:
            conditions.append(f"`{field}` LIKE %s")
            params.append(f"%{pattern}%")

    if not conditions or not valid_fields:
        return results

    # Build safe SELECT field list from validated meta fields
    select_fields = ", ".join(f"`{f}`" for f in valid_fields)

    try:
        results = frappe.db.sql(
            "SELECT `name`, {select_fields} FROM `tab{doctype}` WHERE {where} LIMIT 5".format(
                select_fields=select_fields,
                doctype=doctype.replace("`", ""),
                where=" OR ".join(conditions),
            ),
            params,
            as_dict=True,
        )
    except Exception:
        pass

    return results


def get_contact_info(contact_name: str) -> dict:
    """Get additional info for a contact"""
    info = {}
    
    try:
        contact = frappe.get_doc("Contact", contact_name)
        
        # Get linked company
        for link in contact.links or []:
            if link.link_doctype == "Customer":
                info["company"] = link.link_name
                break
        
        # Get last call
        last_call = frappe.db.get_value(
            "AZ Call Log",
            {"party": contact_name, "party_type": "Contact"},
            ["call_datetime"],
            order_by="call_datetime desc"
        )
        if last_call:
            info["last_contact"] = frappe.utils.pretty_date(last_call)
        
        # Get open issues
        if frappe.db.exists("DocType", "Issue"):
            open_issues = frappe.db.count("Issue", {
                "contact": contact_name,
                "status": ["not in", ["Closed", "Resolved"]]
            })
            info["open_tickets"] = open_issues
    except Exception:
        pass
    
    return info


def get_lead_info(lead_name: str) -> dict:
    """Get additional info for a lead"""
    info = {}
    
    try:
        lead = frappe.get_doc("Lead", lead_name)
        
        info["company"] = lead.company_name or ""
        info["status"] = lead.status
        
        # Get last call
        last_call = frappe.db.get_value(
            "AZ Call Log",
            {"party": lead_name, "party_type": "Lead"},
            ["call_datetime"],
            order_by="call_datetime desc"
        )
        if last_call:
            info["last_contact"] = frappe.utils.pretty_date(last_call)
    except Exception:
        pass
    
    return info


def get_customer_info(customer_name: str) -> dict:
    """Get additional info for a customer"""
    info = {}
    
    try:
        customer = frappe.get_doc("Customer", customer_name)
        
        info["company"] = customer.customer_name
        info["customer_group"] = customer.customer_group
        
        # Get outstanding amount if ERPNext installed
        if frappe.db.exists("DocType", "Sales Invoice"):
            outstanding = frappe.db.sql("""
                SELECT SUM(outstanding_amount) as total
                FROM `tabSales Invoice`
                WHERE customer = %s AND docstatus = 1
            """, customer_name, as_dict=True)
            
            if outstanding and outstanding[0].total:
                info["outstanding"] = frappe.format_value(
                    outstanding[0].total, 
                    {"fieldtype": "Currency"}
                )
        
        # Get open tickets
        if frappe.db.exists("DocType", "Issue"):
            open_issues = frappe.db.count("Issue", {
                "customer": customer_name,
                "status": ["not in", ["Closed", "Resolved"]]
            })
            info["open_tickets"] = open_issues
    except Exception:
        pass
    
    return info


@frappe.whitelist()
def get_caller_history(phone_number: str, limit: int = 10) -> list:
    """
    Get call history for a phone number
    
    Args:
        phone_number: Phone number to search
        limit: Max number of records
        
    Returns:
        List of call log records
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    clean_number = clean_phone_number(phone_number)
    
    calls = frappe.db.get_all(
        "AZ Call Log",
        filters={
            "caller_id": ["like", f"%{clean_number[-10:]}%"]
        },
        fields=[
            "name", "call_datetime", "direction", "duration_seconds",
            "status", "agent", "recording_url"
        ],
        order_by="call_datetime desc",
        limit=limit
    )
    
    return calls


@frappe.whitelist()
def get_caller_tickets(party_type: str, party: str) -> list:
    """
    Get open tickets/issues for a party
    
    Args:
        party_type: Customer, Lead, Contact
        party: Party name
        
    Returns:
        List of open tickets
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not frappe.db.exists("DocType", "Issue"):
        return []
    
    field_map = {
        "Customer": "customer",
        "Lead": "lead",
        "Contact": "contact"
    }
    
    field = field_map.get(party_type)
    if not field:
        return []
    
    tickets = frappe.db.get_all(
        "Issue",
        filters={
            field: party,
            "status": ["not in", ["Closed", "Resolved"]]
        },
        fields=["name", "subject", "status", "priority", "creation"],
        order_by="creation desc",
        limit=5
    )
    
    return tickets


@frappe.whitelist()
def get_caller_orders(party_type: str, party: str) -> list:
    """
    Get recent orders for a party
    
    Args:
        party_type: Customer, Lead
        party: Party name
        
    Returns:
        List of recent orders
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not frappe.db.exists("DocType", "Sales Order"):
        return []
    
    if party_type != "Customer":
        return []
    
    orders = frappe.db.get_all(
        "Sales Order",
        filters={
            "customer": party,
            "docstatus": 1
        },
        fields=[
            "name", "transaction_date", "grand_total", "status",
            "delivery_status", "per_delivered"
        ],
        order_by="transaction_date desc",
        limit=5
    )
    
    return orders


@frappe.whitelist()
def link_call_to_party(call_log: str, party_type: str, party: str) -> bool:
    """
    Link a call log to a CRM party
    
    Args:
        call_log: Call Log document name
        party_type: Customer, Lead, Contact, Supplier
        party: Party name
        
    Returns:
        Success status
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not frappe.db.exists("AZ Call Log", call_log):
        frappe.throw(_("Call Log not found"))
    
    if not frappe.db.exists(party_type, party):
        frappe.throw(_(f"{party_type} not found"))
    
    frappe.db.set_value("AZ Call Log", call_log, {
        "party_type": party_type,
        "party": party
    })
    
    frappe.db.commit()
    
    return True
