# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

# License: MIT

"""
OpenMeetings Integration Connector

Provides integration with Apache OpenMeetings video conferencing server.

Features:
- Room creation (permanent and temporary)
- Secure hash-based access URLs
- Recording management
- File sharing
- Calendar integration

API Reference: https://openmeetings.apache.org/swagger/
"""

import frappe
from frappe import _
from typing import Dict, List, Optional, Any
import requests
from requests.exceptions import RequestException, Timeout
import json


class OpenMeetingsConnector:
    """
    OpenMeetings REST API Connector
    
    Manages connection to OpenMeetings server and provides
    methods for room and user management.
    """
    
    def __init__(self, server_config):
        """
        Initialize connector with server configuration.
        
        Args:
            server_config: AZ Server Config document with OpenMeetings settings
        """
        self.server_config = server_config
        self.base_url = server_config.get("om_url", "").rstrip("/")
        self.username = server_config.get("om_username")
        self.password = server_config.get_password("om_password") if hasattr(server_config, 'get_password') else server_config.get("om_password")
        self.session = requests.Session()
        self.sid = None
        self._session_key = f"openmeetings_sid_{self.server_config.name}"
    
    def _login(self) -> str:
        """
        Login to OpenMeetings and get session ID.
        
        Returns:
            Session ID (SID)
        """
        # Check cache first
        cached_sid = frappe.cache().get_value(self._session_key)
        if cached_sid:
            self.sid = cached_sid
            return cached_sid
        
        url = f"{self.base_url}/services/user/login"
        
        try:
            response = self.session.post(
                url,
                data={
                    "user": self.username,
                    "pass": self.password
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("serviceResult", {}).get("type") == "SUCCESS":
                self.sid = result.get("serviceResult", {}).get("message")
                
                # Cache for 15 minutes
                frappe.cache().set_value(self._session_key, self.sid, expires_in_sec=900)
                
                return self.sid
            else:
                raise Exception("OpenMeetings login failed: " + result.get("serviceResult", {}).get("message", "Unknown error"))
        
        except Timeout:
            frappe.throw(_("OpenMeetings server timeout"))
        except RequestException as e:
            frappe.log_error(f"OpenMeetings login error: {str(e)}", "OpenMeetings Error")
            frappe.throw(_("Failed to connect to OpenMeetings: {0}").format(str(e)))
    
    def get_session(self) -> str:
        """Get current session ID, logging in if necessary."""
        if not self.sid:
            self._login()
        return self.sid
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict] = None,
                     params: Optional[Dict] = None) -> Dict:
        """
        Make an authenticated request to OpenMeetings API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (relative to /services/)
            data: Request body
            params: Query parameters
        """
        sid = self.get_session()
        
        url = f"{self.base_url}/services/{endpoint}"
        
        # Add SID to params
        if params is None:
            params = {}
        params["sid"] = sid
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=30
            )
            
            # Check for session expiry
            if response.status_code == 401:
                # Clear cache and retry
                frappe.cache().delete_value(self._session_key)
                self.sid = None
                return self._make_request(method, endpoint, data, params)
            
            response.raise_for_status()
            
            return response.json() if response.content else {}
        
        except RequestException as e:
            frappe.log_error(f"OpenMeetings API error: {str(e)}", "OpenMeetings Error")
            frappe.throw(_("OpenMeetings API error: {0}").format(str(e)))
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to OpenMeetings server."""
        try:
            self._login()
            return {
                "status": "success",
                "message": "Connected to OpenMeetings successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def create_room(self, room_config: Dict) -> Dict[str, Any]:
        """
        Create a new room in OpenMeetings.
        
        Args:
            room_config: Room configuration with:
                - name: Room name
                - room_type: 1=Conference, 2=Restricted, 3=Interview, 4=Presentation
                - is_moderated: Whether room is moderated
                - allow_recording: Allow recording
                - max_participants: Maximum participants (default 50)
                - external_id: External reference ID
                
        Returns:
            Dict with room_id
        """
        room_dto = {
            "name": room_config.get("name"),
            "type": room_config.get("room_type", 1),
            "isPublic": False,
            "isModeratedRoom": room_config.get("is_moderated", True),
            "allowRecording": room_config.get("allow_recording", True),
            "numberOfPartizipants": room_config.get("max_participants", 50),
            "externalId": room_config.get("external_id"),
            "externalType": "frappe",
            "allowUserQuestions": True,
            "chatModerated": False,
            "chatOpened": room_config.get("enable_chat", True),
            "filesOpened": room_config.get("enable_file_share", True),
            "hideWhiteboard": not room_config.get("enable_whiteboard", True),
            "hideActivitiesAndActions": False,
            "audioOnly": False,
            "closed": False
        }
        
        result = self._make_request("POST", "room/add", data=room_dto)
        
        if result.get("id"):
            return {
                "room_id": result["id"],
                "details": result
            }
        else:
            frappe.throw(_("Failed to create room in OpenMeetings"))
    
    def update_room(self, room_id: int, room_config: Dict) -> Dict[str, Any]:
        """Update an existing room."""
        room_dto = {
            "id": room_id,
            **room_config
        }
        
        result = self._make_request("POST", "room/update", data=room_dto)
        
        return {"status": "success", "details": result}
    
    def delete_room(self, room_id: int) -> Dict[str, Any]:
        """Delete a room."""
        result = self._make_request("DELETE", f"room/{room_id}")
        
        return {"status": "success" if result else "error"}
    
    def get_room(self, room_id: int) -> Dict[str, Any]:
        """Get room details."""
        result = self._make_request("GET", f"room/{room_id}")
        
        return result
    
    def generate_hash_link(self, user_context: Dict, room_id: int,
                          is_moderator: bool = False) -> str:
        """
        Generate a secure hash-based access link for a user.
        
        This is the primary method for granting access to external users
        without requiring them to create OpenMeetings accounts.
        
        Args:
            user_context: User information:
                - firstname: First name
                - lastname: Last name
                - email: Email address
                - externalId: Unique external identifier
                - externalType: External system type (e.g., 'frappe_lead')
            room_id: Room ID to grant access to
            is_moderator: Whether user should be a moderator
            
        Returns:
            Complete URL with hash for direct access
        """
        # Build ExternalUserDTO
        external_user = {
            "firstname": user_context.get("firstname", "Guest"),
            "lastname": user_context.get("lastname", ""),
            "externalId": user_context.get("externalId", ""),
            "externalType": user_context.get("externalType", "frappe"),
            "email": user_context.get("email", "")
        }
        
        # Build RoomOptionsDTO
        room_options = {
            "roomId": room_id,
            "moderator": is_moderator,
            "showAudioVideoTest": True,
            "allowSameURLMultipleTimes": False,
            "allowRecording": is_moderator  # Only moderators can record by default
        }
        
        # Make request to generate hash
        result = self._make_request(
            "POST",
            "user/hash",
            data={
                "user": external_user,
                "options": room_options
            }
        )
        
        if result.get("message"):
            hash_value = result["message"]
            return f"{self.base_url}/hash?secure={hash_value}"
        else:
            frappe.throw(_("Failed to generate access link"))
    
    def get_recordings(self, room_id: int) -> List[Dict]:
        """Get recordings for a room."""
        result = self._make_request("GET", f"record/room/{room_id}")
        
        recordings = []
        for rec in result if isinstance(result, list) else []:
            recordings.append({
                "id": rec.get("id"),
                "name": rec.get("name"),
                "duration": rec.get("duration"),
                "start": rec.get("recordStart"),
                "end": rec.get("recordEnd"),
                "download_url": f"{self.base_url}/services/record/download/{rec.get('id')}"
            })
        
        return recordings
    
    def download_recording(self, recording_id: int) -> bytes:
        """Download a recording file."""
        url = f"{self.base_url}/services/record/download/{recording_id}"
        params = {"sid": self.get_session()}
        
        response = self.session.get(url, params=params, timeout=120)
        response.raise_for_status()
        
        return response.content
    
    def upload_file(self, room_id: int, file_path: str, file_name: str) -> Dict[str, Any]:
        """
        Upload a file to a room.
        
        Args:
            room_id: Room ID
            file_path: Local file path
            file_name: Name for the file in OpenMeetings
        """
        # Get room folder ID
        room = self.get_room(room_id)
        
        # Read file
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Upload via multipart
        files = {
            "file": (file_name, file_content)
        }
        
        url = f"{self.base_url}/services/file/upload"
        params = {"sid": self.get_session()}
        
        response = self.session.post(
            url,
            params=params,
            files=files,
            data={"parentId": room_id},
            timeout=120
        )
        response.raise_for_status()
        
        return response.json() if response.content else {"status": "success"}
    
    def get_active_users(self, room_id: int) -> List[Dict]:
        """Get list of users currently in a room."""
        result = self._make_request("GET", f"room/users/{room_id}")
        
        return result if isinstance(result, list) else []
    
    def kick_user(self, room_id: int, user_public_sid: str) -> Dict[str, Any]:
        """Kick a user from a room."""
        result = self._make_request(
            "DELETE",
            f"room/{room_id}/kick/{user_public_sid}"
        )
        
        return {"status": "success"}
    
    def close_room(self, room_id: int) -> Dict[str, Any]:
        """Close a room (prevent new users from joining)."""
        result = self._make_request("POST", f"room/{room_id}/close")
        
        return {"status": "success"}
    
    def open_room(self, room_id: int) -> Dict[str, Any]:
        """Reopen a closed room."""
        result = self._make_request("POST", f"room/{room_id}/open")
        
        return {"status": "success"}


# Frappe API Functions

@frappe.whitelist()
def create_meeting_room(room_name: str, room_type: str = "Conference",
                       scheduled_start: str = None, scheduled_end: str = None,
                       link_doctype: str = None, link_name: str = None) -> Dict:
    """
    Create a new meeting room from API.
    
    Args:
        room_name: Name of the meeting
        room_type: Type (Conference, Webinar, Interview, Presentation)
        scheduled_start: Start datetime
        scheduled_end: End datetime
        link_doctype: DocType to link to
        link_name: Document name to link to
    """
    frappe.only_for(["System Manager"])
    room = frappe.get_doc({
        "doctype": "AZ Meeting Room",
        "room_name": room_name,
        "room_type": room_type,
        "scheduled_start": scheduled_start,
        "scheduled_end": scheduled_end,
        "link_doctype": link_doctype,
        "link_name": link_name,
        "status": "Scheduled" if scheduled_start else "Draft"
    })
    room.insert(ignore_permissions=True)
    
    return {
        "room": room.name,
        "moderator_url": room.moderator_url,
        "participant_url": room.participant_url
    }


@frappe.whitelist()
def generate_meeting_link(room_name: str, participant_name: str,
                         participant_email: str = None,
                         is_moderator: bool = False) -> Dict:
    """
    Generate a meeting link for a participant.
    
    Args:
        room_name: AZ Meeting Room name
        participant_name: Name of the participant
        participant_email: Email of the participant
        is_moderator: Whether to grant moderator privileges
    """
    frappe.only_for(["System Manager", "Arrowz Manager", "Arrowz User"])
    room = frappe.get_doc("AZ Meeting Room", room_name)
    
    result = room.generate_participant_link({
        "firstname": participant_name.split()[0] if participant_name else "Guest",
        "lastname": " ".join(participant_name.split()[1:]) if participant_name and len(participant_name.split()) > 1 else "",
        "email": participant_email or "",
        "external_id": participant_email or frappe.generate_hash()[:10],
        "is_moderator": is_moderator
    })
    
    return result


def delete_room(room_id: int, server_config: str = None):
    """
    Background job to delete a room from OpenMeetings.
    
    Called when a temporary meeting ends.
    """
    if server_config:
        config = frappe.get_doc("AZ Server Config", server_config)
    else:
        config = frappe.get_doc("AZ Server Config", {
            "server_type": "OpenMeetings",
            "is_default": 1
        })
    
    if config:
        connector = OpenMeetingsConnector(config)
        connector.delete_room(room_id)
