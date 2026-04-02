#!/usr/bin/env python3

import frappe

def fix_contactcall_workspace():
    frappe.init('dev.localhost')
    frappe.connect()
    
    # حذف workspace القديم
    try:
        frappe.delete_doc('Workspace', 'ContactCall Central', force=True)
        print('Old workspace deleted')
    except:
        print('Workspace not found, creating new')
    
    # إنشاء workspace جديد
    workspace_content = """[
        {"id":"_header1","type":"header","data":{"text":"<span class=\\"h2\\">📞 ContactCall Central</span>","col":12}},
        {"id":"_subtitle1","type":"paragraph","data":{"text":"مركز إدارة المكالمات المتكامل","col":12}},
        {"id":"_shortcut1","type":"shortcut","data":{"shortcut_name":"Call Log","col":3}},
        {"id":"_shortcut2","type":"shortcut","data":{"shortcut_name":"Dashboard","col":3}},
        {"id":"_shortcut3","type":"shortcut","data":{"shortcut_name":"Settings","col":3}},
        {"id":"_shortcut4","type":"shortcut","data":{"shortcut_name":"Sentiment","col":3}}
    ]"""

    new_workspace = frappe.get_doc({
        'doctype': 'Workspace',
        'name': 'ContactCall Central',
        'label': 'ContactCall Central',
        'title': 'ContactCall Central',
        'module': 'ContactCall',
        'icon': 'star',
        'content': workspace_content,
        'public': 1,
        'links': [
            {
                'label': '📞 Call Log',
                'link_type': 'DocType',
                'link_to': 'CC Universal Call Log',
                'type': 'Link'
            },
            {
                'label': '📊 Dashboard',
                'link_type': 'Page',
                'link_to': 'contactcall-dashboard',
                'type': 'Link'
            },
            {
                'label': '⚙️ Settings',
                'link_type': 'DocType',
                'link_to': 'ContactCall Settings',
                'type': 'Link'
            },
            {
                'label': '💭 Sentiment',
                'link_type': 'DocType',
                'link_to': 'CC Sentiment Log',
                'type': 'Link'
            }
        ],
        'shortcuts': [
            {
                'label': 'Call Log',
                'link_to': 'CC Universal Call Log',
                'type': 'DocType',
                'color': 'Blue',
                'doc_view': 'List'
            },
            {
                'label': 'Dashboard',
                'link_to': 'contactcall-dashboard',
                'type': 'Page',
                'color': 'Orange'
            },
            {
                'label': 'Settings',
                'link_to': 'ContactCall Settings',
                'type': 'DocType',
                'color': 'Purple',
                'doc_view': 'List'
            },
            {
                'label': 'Sentiment',
                'link_to': 'CC Sentiment Log',
                'type': 'DocType',
                'color': 'Green',
                'doc_view': 'List'
            }
        ]
    })
    
    new_workspace.insert(ignore_permissions=True)
    frappe.db.commit()
    print('New workspace created successfully!')

if __name__ == '__main__':
    fix_contactcall_workspace()