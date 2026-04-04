# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz Recording API
Handles call recording playback and download.
"""

import frappe
from frappe import _
import os


@frappe.whitelist(allow_guest=False)
def stream(call_log):
    """
    Stream call recording audio.
    """
    doc = frappe.get_doc("AZ Call Log", call_log)
    
    if not doc.has_recording or not doc.recording_path:
        frappe.throw(_("No recording available for this call"))
    
    # Check permissions
    if not frappe.has_permission("AZ Call Log", "read", doc.name):
        frappe.throw(_("You don't have permission to access this recording"))
    
    # Get settings for recording path
    settings = frappe.get_single("Arrowz Settings")
    base_path = settings.recording_base_path or "/var/spool/asterisk/monitor"
    
    file_path = os.path.join(base_path, doc.recording_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        # Try alternate location (Docker volume mapping)
        alt_path = os.path.join("/recordings", doc.recording_path)
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            frappe.throw(_("Recording file not found"))
    
    # Determine content type
    ext = os.path.splitext(file_path)[1].lower()
    content_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".gsm": "audio/x-gsm"
    }
    content_type = content_types.get(ext, "audio/mpeg")
    
    # Read and return file
    with open(file_path, "rb") as f:
        content = f.read()
    
    frappe.local.response.filename = f"recording_{call_log}{ext}"
    frappe.local.response.filecontent = content
    frappe.local.response.type = "binary"
    frappe.local.response.headers = {
        "Content-Type": content_type,
        "Content-Disposition": f"inline; filename=recording_{call_log}{ext}"
    }


@frappe.whitelist(allow_guest=False)
def download(call_log):
    """
    Download call recording.
    """
    doc = frappe.get_doc("AZ Call Log", call_log)
    
    if not doc.has_recording or not doc.recording_path:
        frappe.throw(_("No recording available for this call"))
    
    # Check permissions
    if not frappe.has_permission("AZ Call Log", "read", doc.name):
        frappe.throw(_("You don't have permission to access this recording"))
    
    settings = frappe.get_single("Arrowz Settings")
    base_path = settings.recording_base_path or "/var/spool/asterisk/monitor"
    
    file_path = os.path.join(base_path, doc.recording_path)
    
    if not os.path.exists(file_path):
        alt_path = os.path.join("/recordings", doc.recording_path)
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            frappe.throw(_("Recording file not found"))
    
    ext = os.path.splitext(file_path)[1].lower()
    
    with open(file_path, "rb") as f:
        content = f.read()
    
    # Format filename with date
    date_str = doc.start_time.strftime("%Y%m%d_%H%M%S") if doc.start_time else "unknown"
    filename = f"call_{doc.extension}_{date_str}{ext}"
    
    frappe.local.response.filename = filename
    frappe.local.response.filecontent = content
    frappe.local.response.type = "download"


@frappe.whitelist()
def get_recording_info(call_log):
    """
    Get recording metadata without downloading.
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    doc = frappe.get_doc("AZ Call Log", call_log)
    
    if not doc.has_recording:
        return {"has_recording": False}
    
    return {
        "has_recording": True,
        "duration": doc.recording_duration,
        "file_size": doc.recording_file_size,
        "stream_url": f"/api/method/arrowz.api.recording.stream?call_log={call_log}",
        "download_url": f"/api/method/arrowz.api.recording.download?call_log={call_log}"
    }


@frappe.whitelist()
def delete_recording(call_log):
    """
    Delete a call recording.
    """
    if not frappe.has_permission("AZ Call Log", "delete"):
        frappe.throw(_("You don't have permission to delete recordings"))
    
    doc = frappe.get_doc("AZ Call Log", call_log)
    
    if not doc.has_recording:
        return {"status": "no_recording"}
    
    settings = frappe.get_single("Arrowz Settings")
    base_path = settings.recording_base_path or "/var/spool/asterisk/monitor"
    
    file_path = os.path.join(base_path, doc.recording_path)
    
    # Delete file
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Update document
    doc.has_recording = 0
    doc.recording_path = None
    doc.recording_url = None
    doc.recording_duration = 0
    doc.recording_file_size = 0
    doc.save(ignore_permissions=True)
    
    return {"status": "deleted"}
