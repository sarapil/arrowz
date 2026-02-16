# Copyright (c) 2026, Arrowz Team
# License: MIT

"""
Base Driver - Abstract Base Class for Communication Drivers

All integration drivers must inherit from BaseDriver and implement
the required methods for consistent API across different platforms.
"""

import frappe
from frappe import _
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import requests
from requests.exceptions import RequestException, Timeout


class BaseDriver(ABC):
    """
    Abstract base class for all communication drivers.
    
    Provides common functionality and defines the interface that
    all drivers must implement.
    """
    
    def __init__(self, provider):
        """
        Initialize the driver with provider configuration.
        
        Args:
            provider: AZ Omni Provider document
        """
        self.provider = provider
        self.channel = None
        self.base_url = provider.base_url
        self.api_version = provider.api_version
        self.timeout = provider.timeout or 30
        self.session = requests.Session()
    
    def set_channel(self, channel):
        """
        Set the channel for this driver instance.
        
        Args:
            channel: AZ Omni Channel document
        """
        self.channel = channel
        self._configure_auth()
    
    @abstractmethod
    def _configure_auth(self):
        """Configure authentication for the channel. Must be implemented by subclass."""
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the provider.
        
        Returns:
            Dict with 'status' and 'message' keys
        """
        pass
    
    @abstractmethod
    def send_text_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """
        Send a text message.
        
        Args:
            recipient: The recipient identifier (phone number, chat ID, etc.)
            message: The message content
            
        Returns:
            Dict with 'message_id' and other relevant info
        """
        pass
    
    @abstractmethod
    def send_media_message(self, recipient: str, media_url: str, 
                          media_type: str, caption: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a media message (image, video, document, etc.)
        
        Args:
            recipient: The recipient identifier
            media_url: URL or file path of the media
            media_type: Type of media (image, video, audio, document)
            caption: Optional caption for the media
            
        Returns:
            Dict with 'message_id' and other relevant info
        """
        pass
    
    def send_message(self, recipient: str, content: str, 
                    message_type: str = "text", media_url: Optional[str] = None,
                    **kwargs) -> Dict[str, Any]:
        """
        Generic send message method.
        
        Routes to appropriate method based on message_type.
        """
        if message_type == "text":
            return self.send_text_message(recipient, content)
        elif message_type in ["image", "video", "audio", "document"]:
            return self.send_media_message(recipient, media_url, message_type, content)
        else:
            return self.send_text_message(recipient, content)
    
    def fetch_templates(self) -> List[Dict]:
        """
        Fetch message templates from the provider.
        
        Override in subclass if provider supports templates.
        
        Returns:
            List of template dictionaries
        """
        return []
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict] = None, 
                     params: Optional[Dict] = None,
                     files: Optional[Dict] = None) -> Dict:
        """
        Make an HTTP request to the provider API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (will be appended to base_url)
            data: Request body data
            params: Query parameters
            files: Files for multipart upload
            
        Returns:
            Response data as dictionary
            
        Raises:
            frappe.ValidationError on API errors
        """
        url = f"{self.base_url}/{endpoint}".rstrip('/')
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data if data and not files else None,
                data=data if files else None,
                params=params,
                files=files,
                timeout=self.timeout
            )
            
            # Log the request for debugging
            if frappe.conf.get("developer_mode"):
                frappe.log_error(
                    f"API Request: {method} {url}\nResponse: {response.status_code}",
                    "Integration API Debug"
                )
            
            response.raise_for_status()
            
            return response.json() if response.content else {}
            
        except Timeout:
            frappe.log_error(f"Request timeout: {url}", "Integration Timeout")
            frappe.throw(_("Request timed out. Please try again."))
            
        except RequestException as e:
            error_msg = str(e)
            if hasattr(e.response, 'text'):
                error_msg = e.response.text
            
            frappe.log_error(
                f"API Error: {url}\nError: {error_msg}",
                "Integration API Error"
            )
            frappe.throw(_("API request failed: {0}").format(error_msg))
    
    def _normalize_phone_number(self, phone: str) -> str:
        """
        Normalize phone number to international format without + sign.
        
        Args:
            phone: Phone number in any format
            
        Returns:
            Phone number in format: country_code + number (e.g., 201234567890)
        """
        # Remove common prefixes and non-numeric characters
        phone = phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        
        # Remove leading zeros (except for country codes)
        if phone.startswith("00"):
            phone = phone[2:]
        
        return phone
    
    def log_message(self, direction: str, recipient: str, content: str, 
                   message_id: str, status: str = "sent"):
        """
        Log a message to the database.
        
        Args:
            direction: 'inbound' or 'outbound'
            recipient: The recipient/sender identifier
            content: Message content
            message_id: Provider's message ID
            status: Message status
        """
        try:
            # Create Communication record for tracking
            frappe.get_doc({
                "doctype": "Communication",
                "communication_type": "Chat",
                "communication_medium": self.provider.provider_type,
                "sent_or_received": "Sent" if direction == "outbound" else "Received",
                "subject": content[:100] if content else "Media Message",
                "content": content,
                "sender": frappe.session.user if direction == "outbound" else recipient,
                "recipients": recipient if direction == "outbound" else frappe.session.user,
                "message_id": message_id,
                "status": status
            }).insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Failed to log message: {str(e)}", "Message Log Error")
