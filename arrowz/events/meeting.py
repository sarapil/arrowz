# -*- coding: utf-8 -*-

# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Meeting Room Event Handlers

Handles events for AZ Meeting Room DocType:
- Room creation with OpenMeetings integration
- Participant management
- Meeting lifecycle events
- Recording notifications
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime


def before_room_create(doc, method):
    """
    Before creating a meeting room
    
    - Validate scheduled times
    - Generate room configuration
    """
    # Validate times
    if doc.scheduled_end and doc.scheduled_start:
        if get_datetime(doc.scheduled_end) <= get_datetime(doc.scheduled_start):
            frappe.throw(_("End time must be after start time"))
    
    # Set default duration if not specified
    if doc.scheduled_start and not doc.scheduled_end:
        from frappe.utils import add_to_date
        doc.scheduled_end = add_to_date(doc.scheduled_start, hours=1)


def after_room_create(doc, method):
    """
    After creating a meeting room
    
    - Create room in OpenMeetings
    - Generate participant join links
    - Send invitations if configured
    """
    # Check if OpenMeetings provider is configured
    provider = get_openmeetings_provider()
    if not provider:
        frappe.log_error(
            title="OpenMeetings Not Configured",
            message=f"Meeting room {doc.name} created but OpenMeetings is not configured"
        )
        return
    
    try:
        from arrowz.integrations.openmeetings import OpenMeetingsConnector
        
        connector = OpenMeetingsConnector(
            server_url=provider.endpoint_url,
            admin_user=provider.get_password("username"),
            admin_pass=provider.get_password("api_key")
        )
        
        # Create room in OpenMeetings
        is_permanent = doc.room_type == "Permanent"
        room_data = connector.create_room(
            name=doc.room_name,
            room_type="conference" if doc.allow_recording else "presentation",
            capacity=doc.max_participants or 25,
            is_permanent=is_permanent,
            allow_recording=doc.allow_recording,
            auto_start_recording=doc.auto_start_recording
        )
        
        if room_data.get("success"):
            doc.external_room_id = room_data.get("room_id")
            doc.host_url = room_data.get("moderator_url")
            doc.guest_url = room_data.get("guest_url")
            doc.save(ignore_permissions=True)
            
            # Generate individual participant links
            generate_participant_links(doc, connector)
            
            # Send invitations
            if doc.send_invitations:
                send_meeting_invitations(doc)
        else:
            frappe.log_error(
                title="Failed to Create OpenMeetings Room",
                message=f"Room: {doc.name}, Error: {room_data.get('error')}"
            )
            
    except Exception as e:
        frappe.log_error(
            title="OpenMeetings Integration Error",
            message=f"Room: {doc.name}, Error: {str(e)}"
        )


def on_room_update(doc, method):
    """
    Handle meeting room updates
    
    - Sync changes with OpenMeetings
    - Handle status changes
    - Notify participants of changes
    """
    # Check if status changed
    if doc.has_value_changed("status"):
        handle_status_change(doc)
    
    # Check if participants changed
    if doc.has_value_changed("participants"):
        handle_participant_change(doc)
    
    # Check if schedule changed
    if doc.has_value_changed("scheduled_start") or doc.has_value_changed("scheduled_end"):
        notify_schedule_change(doc)


def handle_status_change(doc):
    """
    Handle meeting status changes
    """
    if doc.status == "In Progress":
        doc.actual_start_time = now_datetime()
        
        frappe.publish_realtime(
            "meeting_started",
            {
                "room": doc.name,
                "room_name": doc.room_name,
                "host_url": doc.host_url
            },
            doctype="AZ Meeting Room",
            docname=doc.name,
            after_commit=True
        )
        
    elif doc.status == "Ended":
        doc.actual_end_time = now_datetime()
        
        frappe.publish_realtime(
            "meeting_ended",
            {
                "room": doc.name,
                "room_name": doc.room_name
            },
            doctype="AZ Meeting Room",
            docname=doc.name,
            after_commit=True
        )
        
        # Cleanup temporary rooms
        if doc.room_type == "Temporary":
            frappe.enqueue(
                cleanup_temporary_room,
                queue="long",
                timeout=300,
                room_name=doc.name,
                delay=3600  # Wait 1 hour before cleanup
            )
    
    elif doc.status == "Cancelled":
        # Notify all participants
        for p in doc.participants:
            if p.email:
                frappe.sendmail(
                    recipients=[p.email],
                    subject=f"Meeting Cancelled: {doc.room_name}",
                    message=f"""
                        <p>The meeting "{doc.room_name}" has been cancelled.</p>
                        <p>If you have any questions, please contact the organizer.</p>
                    """
                )


def handle_participant_change(doc):
    """
    Handle participant list changes
    
    - Generate links for new participants
    - Send invitations to new participants
    """
    provider = get_openmeetings_provider()
    if not provider or not doc.external_room_id:
        return
    
    from arrowz.integrations.openmeetings import OpenMeetingsConnector
    
    connector = OpenMeetingsConnector(
        server_url=provider.endpoint_url,
        admin_user=provider.get_password("username"),
        admin_pass=provider.get_password("api_key")
    )
    
    # Find new participants (those without join_url)
    for p in doc.participants:
        if not p.join_url and p.email:
            link_data = connector.generate_hash_link(
                room_id=doc.external_room_id,
                first_name=p.participant_name.split()[0] if p.participant_name else "Guest",
                last_name=p.participant_name.split()[-1] if p.participant_name and len(p.participant_name.split()) > 1 else "",
                email=p.email,
                is_moderator=p.is_moderator
            )
            
            if link_data.get("success"):
                p.join_url = link_data.get("url")
            
            # Send invitation
            if doc.send_invitations:
                send_participant_invitation(doc, p)


def notify_schedule_change(doc):
    """
    Notify participants when meeting schedule changes
    """
    for p in doc.participants:
        if p.email and p.invitation_sent:
            frappe.sendmail(
                recipients=[p.email],
                subject=f"Meeting Rescheduled: {doc.room_name}",
                message=f"""
                    <p>The meeting "{doc.room_name}" has been rescheduled.</p>
                    <p><strong>New Time:</strong> {frappe.format(doc.scheduled_start, "Datetime")} - {frappe.format(doc.scheduled_end, "Datetime")}</p>
                    <p><a href="{p.join_url}">Join Meeting</a></p>
                """
            )


def generate_participant_links(doc, connector):
    """
    Generate individual join links for all participants
    """
    if not doc.external_room_id:
        return
    
    for p in doc.participants:
        if not p.join_url and p.email:
            link_data = connector.generate_hash_link(
                room_id=doc.external_room_id,
                first_name=p.participant_name.split()[0] if p.participant_name else "Guest",
                last_name=p.participant_name.split()[-1] if p.participant_name and len(p.participant_name.split()) > 1 else "",
                email=p.email,
                is_moderator=p.is_moderator
            )
            
            if link_data.get("success"):
                p.join_url = link_data.get("url")
    
    doc.save(ignore_permissions=True)


def send_meeting_invitations(doc):
    """
    Send meeting invitations to all participants
    """
    for p in doc.participants:
        if p.email and not p.invitation_sent:
            send_participant_invitation(doc, p)
            p.invitation_sent = 1
    
    doc.save(ignore_permissions=True)


def send_participant_invitation(doc, participant):
    """
    Send invitation email to a single participant
    """
    subject = f"Meeting Invitation: {doc.room_name}"
    
    role_text = "Moderator" if participant.is_moderator else "Participant"
    
    message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">Meeting Invitation</h2>
            
            <p>You are invited to join the following meeting:</p>
            
            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">{doc.room_name}</h3>
                <p><strong>Date:</strong> {frappe.format(doc.scheduled_start, "Date")}</p>
                <p><strong>Time:</strong> {frappe.format(doc.scheduled_start, "Time")} - {frappe.format(doc.scheduled_end, "Time")}</p>
                <p><strong>Your Role:</strong> {role_text}</p>
            </div>
            
            <p style="text-align: center;">
                <a href="{participant.join_url}" 
                   style="display: inline-block; background: #5e35b1; color: white; 
                          padding: 12px 30px; text-decoration: none; border-radius: 4px;
                          font-weight: bold;">
                    Join Meeting
                </a>
            </p>
            
            <p style="color: #666; font-size: 12px;">
                This link is unique to you. Please do not share it with others.
            </p>
        </div>
    """
    
    # Create calendar event attachment
    ical = generate_ical_event(doc, participant)
    
    frappe.sendmail(
        recipients=[participant.email],
        subject=subject,
        message=message,
        attachments=[{
            "fname": "meeting.ics",
            "fcontent": ical
        }] if ical else None
    )


def generate_ical_event(doc, participant):
    """
    Generate iCal event for calendar integration
    """
    try:
        from datetime import datetime
        import uuid
        
        start = get_datetime(doc.scheduled_start)
        end = get_datetime(doc.scheduled_end)
        
        ical = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Arrowz//Meeting Room//EN
BEGIN:VEVENT
UID:{uuid.uuid4()}
DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:{doc.room_name}
DESCRIPTION:Join the meeting: {participant.join_url}
URL:{participant.join_url}
ORGANIZER:MAILTO:{doc.owner}
ATTENDEE:MAILTO:{participant.email}
END:VEVENT
END:VCALENDAR"""
        
        return ical.encode()
    except Exception:
        return None


def cleanup_temporary_room(room_name):
    """
    Cleanup temporary meeting room after meeting ends
    
    - Delete room from OpenMeetings
    - Mark room as deleted in Frappe
    """
    doc = frappe.get_doc("AZ Meeting Room", room_name)
    
    if doc.status != "Ended" or doc.room_type != "Temporary":
        return
    
    provider = get_openmeetings_provider()
    if provider and doc.external_room_id:
        try:
            from arrowz.integrations.openmeetings import OpenMeetingsConnector
            
            connector = OpenMeetingsConnector(
                server_url=provider.endpoint_url,
                admin_user=provider.get_password("username"),
                admin_pass=provider.get_password("api_key")
            )
            
            connector.delete_room(doc.external_room_id)
        except Exception as e:
            frappe.log_error(
                title="Failed to Delete OpenMeetings Room",
                message=f"Room: {room_name}, Error: {str(e)}"
            )


def get_openmeetings_provider():
    """
    Get the active OpenMeetings provider configuration
    """
    providers = frappe.get_all(
        "AZ Omni Provider",
        filters={
            "provider_type": "OpenMeetings",
            "enabled": 1
        },
        fields=["name"],
        limit=1
    )
    
    if providers:
        return frappe.get_doc("AZ Omni Provider", providers[0].name)
    return None


def sync_openmeetings_status():
    """
    Scheduled task to sync meeting room status with OpenMeetings
    """
    provider = get_openmeetings_provider()
    if not provider:
        return
    
    from arrowz.integrations.openmeetings import OpenMeetingsConnector
    
    connector = OpenMeetingsConnector(
        server_url=provider.endpoint_url,
        admin_user=provider.get_password("username"),
        admin_pass=provider.get_password("api_key")
    )
    
    # Get all active/scheduled rooms
    rooms = frappe.get_all(
        "AZ Meeting Room",
        filters={
            "status": ["in", ["Scheduled", "In Progress"]],
            "external_room_id": ["is", "set"]
        },
        fields=["name", "external_room_id", "status"]
    )
    
    for room in rooms:
        try:
            room_info = connector.get_room_info(room.external_room_id)
            
            if room_info.get("success"):
                participant_count = room_info.get("participant_count", 0)
                
                # Update status based on participants
                doc = frappe.get_doc("AZ Meeting Room", room.name)
                
                if participant_count > 0 and doc.status == "Scheduled":
                    doc.status = "In Progress"
                    doc.actual_start_time = now_datetime()
                    doc.save(ignore_permissions=True)
                    
                elif participant_count == 0 and doc.status == "In Progress":
                    # Check if meeting should end
                    # (e.g., 10 minutes with no participants)
                    pass
                    
        except Exception as e:
            frappe.log_error(
                title="OpenMeetings Sync Error",
                message=f"Room: {room.name}, Error: {str(e)}"
            )
