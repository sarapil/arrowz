frappe.get_doc("Workspace", "ContactCall Central").reload()
ws = frappe.get_doc("Workspace", "ContactCall Central")
print(f"Links: {[l.label for l in ws.links]}")
print(f"Shortcuts: {[s.label for s in ws.shortcuts]}")