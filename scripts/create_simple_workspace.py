import frappe

def execute():
    """Create a simpler ContactCall Workspace"""
    
    # Delete existing workspace if exists
    if frappe.db.exists("Workspace", "ContactCall"):
        frappe.delete_doc("Workspace", "ContactCall", ignore_permissions=True)
        frappe.db.commit()
    
    # Create new simple workspace
    workspace = frappe.new_doc("Workspace")
    workspace.name = "ContactCall"
    workspace.label = "ContactCall"
    workspace.title = "ContactCall Enterprise"
    workspace.icon = "phone"
    workspace.public = 1
    workspace.is_hidden = 0
    
    # Add simple content
    content = [
        {
            "id": "_header",
            "type": "header",
            "data": {
                "text": "<span class=\"h3\">📞 ContactCall Enterprise</span>",
                "col": 12
            }
        },
        {
            "id": "_desc",
            "type": "paragraph", 
            "data": {
                "text": "AI-Powered Communication & Call Management System",
                "col": 12
            }
        },
        {
            "id": "_shortcuts",
            "type": "shortcut",
            "data": {
                "shortcut_name": "Call Logs",
                "col": 3
            }
        }
    ]
    
    workspace.content = frappe.as_json(content)
    
    # Add links
    workspace.append("links", {
        "label": "Call Management",
        "link_type": "DocType",
        "link_to": "CC Universal Call Log",
        "type": "Link",
        "hidden": 0
    })
    
    workspace.append("links", {
        "label": "Server Configuration",
        "link_type": "DocType", 
        "link_to": "CC Server Config",
        "type": "Link",
        "hidden": 0
    })
    
    workspace.append("links", {
        "label": "Extensions",
        "link_type": "DocType",
        "link_to": "CC Unified Extension", 
        "type": "Link",
        "hidden": 0
    })
    
    workspace.append("links", {
        "label": "Settings",
        "link_type": "DocType",
        "link_to": "ContactCall Settings",
        "type": "Link",
        "hidden": 0
    })
    
    workspace.append("links", {
        "label": "Sentiment Analysis",
        "link_type": "DocType",
        "link_to": "CC Sentiment Log",
        "type": "Link", 
        "hidden": 0
    })
    
    # Add shortcuts
    workspace.append("shortcuts", {
        "label": "Call Logs",
        "link_to": "CC Universal Call Log",
        "type": "DocType",
        "doc_view": "List"
    })
    
    workspace.append("shortcuts", {
        "label": "Settings", 
        "link_to": "ContactCall Settings",
        "type": "DocType",
        "doc_view": "List"
    })
    
    workspace.append("shortcuts", {
        "label": "Extensions",
        "link_to": "CC Unified Extension",
        "type": "DocType",
        "doc_view": "List"
    })
    
    workspace.insert(ignore_permissions=True)
    frappe.db.commit()
    
    print("✅ Simple ContactCall Workspace created!")

if __name__ == "__main__":
    execute()