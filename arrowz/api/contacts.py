# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# License: MIT

"""
Arrowz Contacts Search API
Provides unified contact search across multiple DocTypes
"""

import frappe
from frappe import _


@frappe.whitelist()
def search_contacts(query, limit=10):
    """
    Search for contacts across multiple DocTypes.
    
    Searches in:
    - Lead
    - Customer
    - Contact
    - Supplier
    - Employee
    
    Args:
        query: Search string (name or phone)
        limit: Maximum results to return
        
    Returns:
        List of contacts with name, phone, doctype
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not query or len(query) < 2:
        return []
    
    results = []
    limit = min(int(limit), 50)
    
    # Search pattern
    search = f"%{query}%"
    
    # Search in Lead
    try:
        leads = frappe.db.sql("""
            SELECT 
                name, lead_name as contact_name, mobile_no, phone
            FROM `tabLead`
            WHERE (lead_name LIKE %(search)s 
                   OR mobile_no LIKE %(search)s 
                   OR phone LIKE %(search)s)
            LIMIT %(limit)s
        """, {"search": search, "limit": limit}, as_dict=True)
        
        for lead in leads:
            phone = lead.mobile_no or lead.phone
            if phone:
                results.append({
                    "doctype": "Lead",
                    "docname": lead.name,
                    "name": lead.contact_name or lead.name,
                    "phone": phone
                })
    except Exception:
        pass
    
    # Search in Customer
    try:
        customers = frappe.db.sql("""
            SELECT 
                c.name, c.customer_name,
                dl.phone, dl.mobile_no
            FROM `tabCustomer` c
            LEFT JOIN `tabDynamic Link` dl_link ON dl_link.link_doctype = 'Customer' 
                AND dl_link.link_name = c.name 
                AND dl_link.parenttype = 'Contact'
            LEFT JOIN `tabContact` ct ON ct.name = dl_link.parent
            LEFT JOIN `tabContact Phone` dl ON dl.parent = ct.name
            WHERE (c.customer_name LIKE %(search)s 
                   OR dl.phone LIKE %(search)s 
                   OR dl.mobile_no LIKE %(search)s)
            LIMIT %(limit)s
        """, {"search": search, "limit": limit}, as_dict=True)
        
        for cust in customers:
            phone = cust.mobile_no or cust.phone
            if phone:
                results.append({
                    "doctype": "Customer",
                    "docname": cust.name,
                    "name": cust.customer_name or cust.name,
                    "phone": phone
                })
    except Exception:
        pass
    
    # Search in Contact
    try:
        contacts = frappe.db.sql("""
            SELECT 
                c.name, 
                CONCAT_WS(' ', c.first_name, c.last_name) as contact_name,
                c.mobile_no, c.phone
            FROM `tabContact` c
            WHERE (CONCAT_WS(' ', c.first_name, c.last_name) LIKE %(search)s 
                   OR c.mobile_no LIKE %(search)s 
                   OR c.phone LIKE %(search)s)
            LIMIT %(limit)s
        """, {"search": search, "limit": limit}, as_dict=True)
        
        for contact in contacts:
            phone = contact.mobile_no or contact.phone
            if phone:
                results.append({
                    "doctype": "Contact",
                    "docname": contact.name,
                    "name": contact.contact_name or contact.name,
                    "phone": phone
                })
    except Exception:
        pass
    
    # Search in Supplier
    try:
        suppliers = frappe.db.sql("""
            SELECT 
                name, supplier_name, phone
            FROM `tabSupplier`
            WHERE (supplier_name LIKE %(search)s 
                   OR phone LIKE %(search)s)
            LIMIT %(limit)s
        """, {"search": search, "limit": limit}, as_dict=True)
        
        for supplier in suppliers:
            if supplier.phone:
                results.append({
                    "doctype": "Supplier",
                    "docname": supplier.name,
                    "name": supplier.supplier_name or supplier.name,
                    "phone": supplier.phone
                })
    except Exception:
        pass
    
    # Search in Employee
    try:
        employees = frappe.db.sql("""
            SELECT 
                name, employee_name, cell_number, personal_email
            FROM `tabEmployee`
            WHERE (employee_name LIKE %(search)s 
                   OR cell_number LIKE %(search)s)
            LIMIT %(limit)s
        """, {"search": search, "limit": limit}, as_dict=True)
        
        for emp in employees:
            if emp.cell_number:
                results.append({
                    "doctype": "Employee",
                    "docname": emp.name,
                    "name": emp.employee_name or emp.name,
                    "phone": emp.cell_number
                })
    except Exception:
        pass
    
    # Remove duplicates based on phone number
    seen_phones = set()
    unique_results = []
    for r in results:
        phone_clean = r["phone"].replace(" ", "").replace("-", "").replace("+", "")
        if phone_clean not in seen_phones:
            seen_phones.add(phone_clean)
            unique_results.append(r)
    
    return unique_results[:limit]


@frappe.whitelist()
def get_contact_info(phone):
    """
    Get contact information for a phone number.
    Used for screen pop and caller ID lookup.
    
    Args:
        phone: Phone number to lookup
        
    Returns:
        Contact info if found, None otherwise
    """
    frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

    if not phone:
        return None
    
    # Clean phone number for search
    phone_clean = phone.replace(" ", "").replace("-", "")
    
    # Try different formats
    patterns = [
        phone_clean,
        phone_clean.lstrip("+"),
        phone_clean.lstrip("0"),
        "+" + phone_clean.lstrip("+"),
        "0" + phone_clean.lstrip("0")
    ]
    
    # Search in Lead
    for pattern in patterns:
        lead = frappe.db.get_value(
            "Lead",
            {"mobile_no": ["like", f"%{pattern}%"]},
            ["name", "lead_name", "mobile_no", "company_name", "status"],
            as_dict=True
        )
        if lead:
            return {
                "doctype": "Lead",
                "docname": lead.name,
                "name": lead.lead_name,
                "phone": lead.mobile_no,
                "company": lead.company_name,
                "extra": {"status": lead.status}
            }
    
    # Search in Contact
    for pattern in patterns:
        contact = frappe.db.get_value(
            "Contact",
            {"mobile_no": ["like", f"%{pattern}%"]},
            ["name", "first_name", "last_name", "mobile_no", "email_id"],
            as_dict=True
        )
        if contact:
            # Get linked doctypes
            links = frappe.get_all(
                "Dynamic Link",
                filters={"parent": contact.name, "parenttype": "Contact"},
                fields=["link_doctype", "link_name"]
            )
            
            return {
                "doctype": "Contact",
                "docname": contact.name,
                "name": f"{contact.first_name or ''} {contact.last_name or ''}".strip(),
                "phone": contact.mobile_no,
                "email": contact.email_id,
                "links": links
            }
    
    return None
