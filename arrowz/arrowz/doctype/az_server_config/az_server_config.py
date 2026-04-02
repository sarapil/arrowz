# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class AZServerConfig(Document):
    def validate(self):
        # Build websocket URL if not provided
        if not self.websocket_url and self.host:
            protocol = "wss" if self.protocol == "WSS" else "ws"
            self.websocket_url = f"{protocol}://{self.host}:{self.port}/ws"
        
        # Set AMI host same as main host if not specified
        if self.ami_enabled and not self.ami_host:
            self.ami_host = self.host
        
        # Set SSH host same as main host if not specified
        if self.ssh_enabled and not self.ssh_host:
            self.ssh_host = self.host
    
    def before_save(self):
        # Ensure only one default server
        if self.is_default:
            frappe.db.sql("""
                UPDATE `tabAZ Server Config` 
                SET is_default = 0 
                WHERE name != %s
            """, self.name)
    
    @frappe.whitelist()
    def test_connection(self):
        """Test connection to the PBX server"""
        frappe.only_for(["System Manager"])

        import socket
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                self.connection_status = "Connected"
                self.last_health_check = now_datetime()
                self.last_error = None
                self.save()
                return {"success": True, "message": f"Successfully connected to {self.host}:{self.port}"}
            else:
                raise Exception(f"Port {self.port} is not reachable")
                
        except Exception as e:
            self.connection_status = "Error"
            self.last_health_check = now_datetime()
            self.last_error = str(e)
            self.save()
            return {"success": False, "message": str(e)}
    
    @frappe.whitelist()
    def test_ami_connection(self):
        """Test AMI connection"""
        frappe.only_for(["AZ User", "AZ Manager", "System Manager"])

        if not self.ami_enabled:
            return {"success": False, "message": "AMI is not enabled"}
        
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.ami_host, self.ami_port))
            
            # Read banner
            banner = sock.recv(1024).decode()
            sock.close()
            
            if "Asterisk" in banner:
                return {"success": True, "message": f"AMI connected: {banner.strip()}"}
            else:
                return {"success": True, "message": f"Connected, response: {banner.strip()}"}
                
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def get_websocket_config(self):
        """Get WebSocket configuration for JsSIP"""
        return {
            "websocket_url": self.websocket_url,
            "sip_domain": self.sip_domain or self.host,
            "stun_server": self.stun_server,
            "turn_server": self.turn_server,
            "turn_username": self.turn_username,
            "turn_password": self.get_password("turn_password") if self.turn_password else None
        }


def get_default_server():
    """Get the default server configuration"""
    server = frappe.db.get_value("AZ Server Config", 
        {"is_default": 1, "is_active": 1}, 
        "name"
    )
    
    if not server:
        # Get first active server
        server = frappe.db.get_value("AZ Server Config", 
            {"is_active": 1}, 
            "name",
            order_by="priority asc"
        )
    
    if server:
        return frappe.get_doc("AZ Server Config", server)
    
    return None
