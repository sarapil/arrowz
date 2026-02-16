# Copyright (c) 2026, Arrowz Team
# License: MIT

"""
AZ Meeting Room - Video Conference Room Management

Integrates with OpenMeetings to provide:
- Permanent and temporary meeting rooms
- Scheduled meetings with calendar integration
- Secure hash-based access URLs
- Recording management
- Participant tracking

Supports integration with:
- Lead, Opportunity, Customer, Contact
- Employee, Sales Partner
- Event (calendar integration)
- Any custom DocType
"""

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import now_datetime, get_datetime, add_to_date
import secrets


class AZMeetingRoom(Document):
    """Video Conference Meeting Room"""
    
    def validate(self):
        """Validate room configuration"""
        self.validate_schedule()
        self.set_default_organizer()
    
    def before_insert(self):
        """Before creating room"""
        if not self.status:
            self.status = "Draft"
    
    def after_insert(self):
        """After room is created"""
        if self.status == "Scheduled":
            self.create_external_room()
    
    def validate_schedule(self):
        """Validate scheduling"""
        if self.scheduled_start and self.scheduled_end:
            if get_datetime(self.scheduled_start) >= get_datetime(self.scheduled_end):
                frappe.throw(_("Scheduled end must be after scheduled start"))
    
    def set_default_organizer(self):
        """Set current user as organizer if not set"""
        if not self.organizer:
            self.organizer = frappe.session.user
    
    def create_external_room(self):
        """Create room in OpenMeetings"""
        try:
            connector = self.get_connector()
            
            room_config = {
                "name": self.room_name,
                "room_type": self.get_room_type_code(),
                "is_moderated": self.is_moderated,
                "allow_recording": self.allow_recording,
                "max_participants": self.max_participants,
                "enable_chat": self.enable_chat,
                "enable_whiteboard": self.enable_whiteboard,
                "external_id": self.name
            }
            
            result = connector.create_room(room_config)
            
            if result.get("room_id"):
                self.external_room_id = result["room_id"]
                self.db_set("external_room_id", result["room_id"], update_modified=False)
                
                # Generate access URLs
                self.generate_access_urls()
                
        except Exception as e:
            frappe.log_error(f"Failed to create room in OpenMeetings: {str(e)}", "Meeting Room Error")
            frappe.throw(_("Failed to create meeting room: {0}").format(str(e)))
    
    def get_connector(self):
        """Get OpenMeetings connector"""
        from arrowz.integrations.openmeetings import OpenMeetingsConnector
        
        server_config = None
        if self.server_config:
            server_config = frappe.get_doc("AZ Server Config", self.server_config)
        else:
            # Get default OpenMeetings server
            server_config = frappe.db.get_value(
                "AZ Server Config",
                {"server_type": "OpenMeetings", "is_default": 1},
                "name"
            )
            if server_config:
                server_config = frappe.get_doc("AZ Server Config", server_config)
        
        if not server_config:
            frappe.throw(_("No OpenMeetings server configured"))
        
        return OpenMeetingsConnector(server_config)
    
    def get_room_type_code(self):
        """Convert room type to OpenMeetings code"""
        type_map = {
            "Conference": 1,
            "Webinar": 3,
            "Interview": 2,
            "Presentation": 4,
            "Restricted": 5
        }
        return type_map.get(self.room_type, 1)
    
    def generate_access_urls(self):
        """Generate secure access URLs"""
        try:
            connector = self.get_connector()
            
            # Moderator URL
            moderator_hash = connector.generate_hash_link(
                user_context={
                    "firstname": frappe.db.get_value("User", self.organizer, "first_name") or "Moderator",
                    "lastname": frappe.db.get_value("User", self.organizer, "last_name") or "",
                    "email": self.organizer,
                    "externalId": self.organizer,
                    "externalType": "frappe_user"
                },
                room_id=self.external_room_id,
                is_moderator=True
            )
            self.moderator_url = moderator_hash
            
            # Participant URL (generic)
            participant_hash = connector.generate_hash_link(
                user_context={
                    "firstname": "Guest",
                    "lastname": "",
                    "email": "",
                    "externalId": f"guest_{secrets.token_hex(8)}",
                    "externalType": "frappe_guest"
                },
                room_id=self.external_room_id,
                is_moderator=False
            )
            self.participant_url = participant_hash
            
            self.db_set({
                "moderator_url": self.moderator_url,
                "participant_url": self.participant_url
            }, update_modified=False)
            
        except Exception as e:
            frappe.log_error(f"Failed to generate access URLs: {str(e)}", "Meeting Room Error")
    
    @frappe.whitelist()
    def generate_participant_link(self, participant_data):
        """Generate a unique link for a specific participant"""
        try:
            connector = self.get_connector()
            
            hash_link = connector.generate_hash_link(
                user_context={
                    "firstname": participant_data.get("firstname", "Guest"),
                    "lastname": participant_data.get("lastname", ""),
                    "email": participant_data.get("email", ""),
                    "externalId": participant_data.get("external_id") or secrets.token_hex(8),
                    "externalType": participant_data.get("external_type", "frappe_contact")
                },
                room_id=self.external_room_id,
                is_moderator=participant_data.get("is_moderator", False)
            )
            
            return {
                "status": "success",
                "url": hash_link
            }
            
        except Exception as e:
            frappe.log_error(f"Failed to generate participant link: {str(e)}", "Meeting Room Error")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @frappe.whitelist()
    def add_participant(self, doctype=None, docname=None, email=None, name=None, is_moderator=False):
        """Add a participant to the meeting"""
        participant = {
            "participant_type": "External" if not doctype else "Internal",
            "email": email,
            "participant_name": name,
            "is_moderator": is_moderator
        }
        
        if doctype and docname:
            participant["link_doctype"] = doctype
            participant["link_name"] = docname
            
            # Get name and email from linked document
            if doctype == "Contact":
                contact = frappe.get_doc("Contact", docname)
                participant["participant_name"] = contact.name
                participant["email"] = contact.email_id
            elif doctype == "Lead":
                lead = frappe.get_doc("Lead", docname)
                participant["participant_name"] = lead.lead_name
                participant["email"] = lead.email_id
            elif doctype == "Customer":
                customer = frappe.get_doc("Customer", docname)
                participant["participant_name"] = customer.customer_name
            elif doctype == "User":
                user = frappe.get_doc("User", docname)
                participant["participant_name"] = user.full_name
                participant["email"] = user.email
        
        # Generate unique join link
        link_result = self.generate_participant_link({
            "firstname": participant.get("participant_name", "").split()[0] if participant.get("participant_name") else "Guest",
            "lastname": " ".join(participant.get("participant_name", "").split()[1:]) if participant.get("participant_name") else "",
            "email": participant.get("email", ""),
            "external_id": f"{doctype}_{docname}" if doctype else email,
            "external_type": "frappe_" + (doctype.lower() if doctype else "external"),
            "is_moderator": is_moderator
        })
        
        if link_result.get("status") == "success":
            participant["join_url"] = link_result["url"]
        
        self.append("participants", participant)
        self.save(ignore_permissions=True)
        
        return {
            "status": "success",
            "participant": participant
        }
    
    @frappe.whitelist()
    def start_meeting(self):
        """Start the meeting"""
        self.status = "Active"
        
        if not self.external_room_id:
            self.create_external_room()
        
        self.save(ignore_permissions=True)
        
        # Broadcast to participants
        frappe.publish_realtime(
            "arrowz_meeting_started",
            {
                "room": self.name,
                "room_name": self.room_name,
                "moderator_url": self.moderator_url,
                "participant_url": self.participant_url
            }
        )
        
        return {
            "status": "success",
            "moderator_url": self.moderator_url
        }
    
    @frappe.whitelist()
    def end_meeting(self):
        """End the meeting"""
        self.status = "Completed"
        self.save(ignore_permissions=True)
        
        # If not permanent, schedule deletion in OpenMeetings
        if not self.is_permanent and self.external_room_id:
            frappe.enqueue(
                "arrowz.integrations.openmeetings.delete_room",
                room_id=self.external_room_id,
                server_config=self.server_config,
                queue="short"
            )
        
        return {"status": "success"}
    
    @frappe.whitelist()
    def send_invitations(self):
        """Send email invitations to all participants"""
        from frappe.core.doctype.communication.email import make
        
        for participant in self.participants:
            if participant.email and participant.join_url:
                try:
                    # Create email
                    subject = _("Meeting Invitation: {0}").format(self.room_name)
                    
                    message = frappe.render_template(
                        "arrowz/templates/emails/meeting_invitation.html",
                        {
                            "room_name": self.room_name,
                            "scheduled_start": self.scheduled_start,
                            "scheduled_end": self.scheduled_end,
                            "organizer": frappe.db.get_value("User", self.organizer, "full_name"),
                            "join_url": participant.join_url,
                            "is_moderator": participant.is_moderator
                        }
                    )
                    
                    make(
                        recipients=participant.email,
                        subject=subject,
                        content=message,
                        doctype=self.doctype,
                        name=self.name,
                        send_email=True
                    )
                    
                    participant.invitation_sent = 1
                    participant.invitation_sent_on = now_datetime()
                    
                except Exception as e:
                    frappe.log_error(
                        f"Failed to send invitation to {participant.email}: {str(e)}",
                        "Meeting Invitation Error"
                    )
        
        self.save(ignore_permissions=True)
        
        return {"status": "success", "sent_count": sum(1 for p in self.participants if p.invitation_sent)}


@frappe.whitelist()
def create_instant_meeting(room_name=None, link_doctype=None, link_name=None):
    """Create an instant meeting room"""
    room = frappe.get_doc({
        "doctype": "AZ Meeting Room",
        "room_name": room_name or _("Instant Meeting - {0}").format(now_datetime().strftime("%Y-%m-%d %H:%M")),
        "room_type": "Conference",
        "status": "Scheduled",
        "scheduled_start": now_datetime(),
        "scheduled_end": add_to_date(now_datetime(), hours=1),
        "is_permanent": 0,
        "link_doctype": link_doctype,
        "link_name": link_name
    })
    room.insert(ignore_permissions=True)
    
    # Start immediately
    result = room.start_meeting()
    
    return {
        "room_name": room.name,
        "moderator_url": result.get("moderator_url"),
        "participant_url": room.participant_url
    }


@frappe.whitelist()
def get_upcoming_meetings(user=None, limit=10):
    """Get upcoming meetings for a user"""
    filters = {
        "status": ["in", ["Scheduled", "Active"]],
        "scheduled_start": [">=", now_datetime()]
    }
    
    if user:
        filters["organizer"] = user
    
    meetings = frappe.get_all(
        "AZ Meeting Room",
        filters=filters,
        fields=[
            "name", "room_name", "room_type", "status",
            "scheduled_start", "scheduled_end", "organizer",
            "link_doctype", "link_name"
        ],
        order_by="scheduled_start asc",
        limit=limit
    )
    
    return meetings
