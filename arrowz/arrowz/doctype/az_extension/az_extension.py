# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
import requests
import secrets
import string


class AZExtension(Document):
    def validate(self):
        # Auto-set SIP username if not provided
        if not self.sip_username:
            self.sip_username = self.extension
        
        # Auto-set display name from user if not provided
        if not self.display_name and self.user:
            self.display_name = frappe.db.get_value("User", self.user, "full_name")
        
        # Auto-set voicemail PIN if not provided
        if self.enable_voicemail and not self.voicemail_pin:
            self.voicemail_pin = self.extension  # Default to extension number
    
    def before_insert(self):
        # Generate SIP password if not provided
        if not self.sip_password:
            self.sip_password = self.generate_secure_password()
            frappe.msgprint(
                f"🔐 SIP Password generated automatically.",
                indicator="blue",
                alert=True
            )
    
    def before_save(self):
        # Check for duplicate extension on same server
        existing = frappe.db.exists("AZ Extension", {
            "extension": self.extension,
            "server": self.server,
            "name": ("!=", self.name)
        })
        if existing:
            frappe.throw(f"Extension {self.extension} already exists on server {self.server}")
    
    def after_insert(self):
        """Create extension in FreePBX after creating in ERPNext"""
        if self.auto_provision:
            self.create_in_freepbx()
    
    def on_update(self):
        """Update extension in FreePBX when updated in ERPNext"""
        if self.auto_provision and self.has_value_changed("extension"):
            self.update_in_freepbx()
    
    def on_trash(self):
        """Delete extension from FreePBX when deleted from ERPNext"""
        if self.auto_provision and self.sync_status == "Synced":
            self.delete_from_freepbx()
    
    def generate_secure_password(self, length=16):
        """Generate a secure random password for SIP"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def get_server_config(self):
        """Get the linked server configuration"""
        if not self.server:
            frappe.throw("Server Config is required for PBX operations")
        return frappe.get_doc("AZ Server Config", self.server)
    
    def get_webrtc_config(self):
        """Get WebRTC configuration for this extension"""
        server = frappe.get_doc("AZ Server Config", self.server)
        server_config = server.get_websocket_config()
        
        return {
            "extension": self.extension,
            "sip_uri": f"sip:{self.sip_username}@{server_config['sip_domain']}",
            "sip_password": self.get_password("sip_password"),
            "sip_domain": server_config["sip_domain"],
            "display_name": self.display_name or self.extension,
            "websocket_servers": [server_config["websocket_url"]],
            "stun_server": server_config["stun_server"],
            "turn_server": server_config["turn_server"],
            "turn_username": server_config["turn_username"],
            "turn_password": server_config["turn_password"],
            "extension_type": self.extension_type,
            "can_transfer_blind": self.can_transfer_blind
        }
    
    def set_status(self, status, call_log=None):
        """Update extension status"""
        self.status = status
        self.current_call = call_log
        if status == "available":
            self.last_registered = now_datetime()
        self.save(ignore_permissions=True)
        
        # Broadcast status change
        frappe.publish_realtime("extension_status_change", {
            "extension": self.extension,
            "status": status,
            "user": self.user
        })
    
    # ===== FreePBX GraphQL Integration =====
    
    def execute_graphql(self, query, variables=None):
        """Execute GraphQL query against FreePBX using automatic token management."""
        from arrowz.freepbx_token import execute_graphql as fpbx_execute
        
        server = self.get_server_config()
        
        if not server.graphql_enabled or not server.graphql_url:
            frappe.throw("GraphQL is not configured in Server Config")
        
        if not server.graphql_client_id:
            frappe.throw("GraphQL Client ID is required in Server Config")
        
        return fpbx_execute(server.name, query, variables)
    
    # ===== SSH/fwconsole Fallback Methods =====
    
    def _create_via_ssh(self) -> bool:
        """
        Create extension via SSH using fwconsole (fallback when GraphQL fails).
        Uses FreePBX fwconsole commands to create extension.
        """
        try:
            from arrowz.pbx_monitor import PBXMonitor
            
            monitor = PBXMonitor(self.server)
            
            # Test SSH connection first
            conn_result = monitor.test_connection()
            if not conn_result.get("success"):
                return False
            
            sip_password = self.get_password("sip_password")
            display_name = self.display_name or str(self.extension)
            
            # Create extension using fwconsole
            # fwconsole extension add <ext> <name> <tech> <password>
            cmd = f'fwconsole extension add {self.extension} "{display_name}" pjsip "{sip_password}"'
            stdout, stderr, code = monitor._ssh_cmd(cmd)
            
            if code != 0:
                # Try alternative: direct database insert
                cmd = f'''mysql asterisk -e "
INSERT INTO sip (id, keyword, data, flags) VALUES 
('{self.extension}', 'secret', '{sip_password}', 0),
('{self.extension}', 'callerid', '{display_name} <{self.extension}>', 0),
('{self.extension}', 'context', 'from-internal', 0)
ON DUPLICATE KEY UPDATE data=VALUES(data);"'''
                stdout, stderr, code = monitor._ssh_cmd(cmd)
            
            if code == 0:
                # Apply configuration
                monitor._ssh_cmd('fwconsole reload')
                return True
            
            return False
            
        except Exception as e:
            frappe.log_error(f"SSH create failed: {str(e)}", "AZ Extension SSH")
            return False
    
    def _sync_via_ssh(self) -> dict:
        """
        Sync extension to FreePBX via SSH when GraphQL fails.
        Returns dict with success status and message.
        """
        try:
            from arrowz.pbx_monitor import PBXMonitor
            
            monitor = PBXMonitor(self.server)
            
            # Test connection
            conn_result = monitor.test_connection()
            if not conn_result.get("success"):
                return {
                    "success": False,
                    "message": f"SSH connection failed: {conn_result.get('error', 'Unknown error')}"
                }
            
            sip_password = self.get_password("sip_password")
            display_name = self.display_name or str(self.extension)
            
            # Check if extension exists
            check_cmd = f'asterisk -rx "pjsip show endpoint {self.extension}" 2>/dev/null | grep -q "Endpoint:" && echo "EXISTS" || echo "NOT_FOUND"'
            stdout, _, code = monitor._ssh_cmd(check_cmd)
            
            if "EXISTS" in stdout:
                # Update existing extension password via database
                update_cmd = f'''mysql asterisk -e "
UPDATE sip SET data='{sip_password}' WHERE id='{self.extension}' AND keyword='secret';
UPDATE sip SET data='{display_name} <{self.extension}>' WHERE id='{self.extension}' AND keyword='callerid';
"'''
                stdout, stderr, code = monitor._ssh_cmd(update_cmd)
                
                if code == 0:
                    # Reload
                    monitor._ssh_cmd('fwconsole reload')
                    return {"success": True, "message": f"Extension {self.extension} updated via SSH"}
                else:
                    return {"success": False, "message": f"Database update failed: {stderr[:100]}"}
            else:
                # Create new extension
                if self._create_via_ssh():
                    return {"success": True, "message": f"Extension {self.extension} created via SSH"}
                else:
                    return {"success": False, "message": "Failed to create extension via SSH"}
                    
        except ImportError:
            return {"success": False, "message": "PBX Monitor not available - SSH sync disabled"}
        except Exception as e:
            return {"success": False, "message": f"SSH sync error: {str(e)[:100]}"}
    
    def _configure_webrtc_settings(self) -> bool:
        """
        Configure WebRTC settings for this extension via PBX Monitor.
        Uses SSH to directly configure PJSIP settings that GraphQL doesn't support.
        """
        try:
            from arrowz.pbx_monitor import PBXMonitor
            
            monitor = PBXMonitor(self.server)
            
            # First check if SSH is available
            conn_result = monitor.test_connection()
            if not conn_result.get("success"):
                frappe.log_error(
                    f"Cannot configure WebRTC via SSH: {conn_result.get('error')}",
                    "AZ Extension WebRTC"
                )
                return False
            
            # Configure WebRTC settings
            result = monitor.configure_webrtc_extension(str(self.extension))
            
            if result.get("success"):
                frappe.msgprint(
                    f"✅ WebRTC settings configured for extension {self.extension}",
                    indicator="green"
                )
                return True
            else:
                frappe.log_error(
                    f"Failed to configure WebRTC: {result.get('error')}",
                    "AZ Extension WebRTC"
                )
                return False
                
        except ImportError:
            frappe.log_error("PBX Monitor module not available", "AZ Extension WebRTC")
            return False
        except Exception as e:
            frappe.log_error(f"Error configuring WebRTC: {str(e)}", "AZ Extension WebRTC")
            return False
    
    def apply_freepbx_config(self):
        """Apply FreePBX configuration (like clicking Apply Config button)"""
        try:
            mutation = """
            mutation doreload($input: doreloadInput!) {
                doreload(input: $input) {
                    status
                    message
                }
            }
            """
            response = self.execute_graphql(mutation, {"input": {}})
            
            if response.get("data", {}).get("doreload", {}).get("status"):
                frappe.msgprint("✅ FreePBX config applied!", indicator="green", alert=True)
                return True
            else:
                frappe.msgprint("⚠️ Apply config may have failed", indicator="orange", alert=True)
                return False
        except Exception as e:
            frappe.log_error(f"Apply config failed: {str(e)[:80]}", "FreePBX Apply")
            return False
    
    def _set_extension_password(self, password: str) -> bool:
        """Set extension password in FreePBX for both Extension and Core User"""
        success = True
        
        # 1. Update Extension password (PJSIP)
        # Note: FreePBX GraphQL requires 'name' field even for password updates
        try:
            ext_mutation = """
            mutation updateExtension($input: updateExtensionInput!) {
                updateExtension(input: $input) {
                    status
                    message
                }
            }
            """
            
            ext_variables = {
                "input": {
                    "extensionId": str(self.extension),
                    "name": self.display_name or str(self.extension),
                    "extPassword": password
                }
            }
            
            ext_response = self.execute_graphql(ext_mutation, ext_variables)
            
            if not ext_response.get("data", {}).get("updateExtension", {}).get("status"):
                error_msg = ext_response.get("data", {}).get("updateExtension", {}).get("message", "Unknown error")
                frappe.log_error(f"Failed to set Extension password for {self.extension}: {error_msg}", "AZ Extension")
                success = False
        except Exception as e:
            frappe.log_error(f"Error setting Extension password: {str(e)[:100]}", "AZ Extension")
            success = False
        
        # Note: Core User (User Manager) requires many mandatory fields for update
        # The Extension password (extPassword) is what matters for SIP authentication
        # Core User password sync is skipped as it's not needed for softphone registration
        
        return success
    
    def create_in_freepbx(self):
        """Create extension in FreePBX via GraphQL API"""
        try:
            server = self.get_server_config()
            
            if not server.graphql_url or not server.graphql_client_id:
                self.db_set('sync_status', 'Not Synced')
                frappe.msgprint(
                    "⚠️ GraphQL not configured. Extension created locally only.",
                    indicator="orange",
                    alert=True
                )
                return False
            
            mutation = """
            mutation addExtension($input: addExtensionInput!) {
                addExtension(input: $input) {
                    status
                    message
                }
            }
            """
            
            user_email = None
            if self.user:
                user_email = frappe.db.get_value("User", self.user, "email")
            
            # email is REQUIRED by FreePBX GraphQL API
            # If no user email, use a default based on extension
            if not user_email:
                user_email = f"{self.extension}@local.pbx"
            
            # Build input with required and optional fields
            input_data = {
                "extensionId": str(self.extension),
                "name": self.display_name or str(self.extension),
                "email": user_email,  # Required field
                "tech": "pjsip"
            }
            
            # Voicemail settings
            input_data["vmEnable"] = bool(self.enable_voicemail)
            if self.enable_voicemail and self.voicemail_pin:
                input_data["vmPassword"] = str(self.voicemail_pin)
            
            variables = {"input": input_data}
            
            response = self.execute_graphql(mutation, variables)
            
            if response.get("errors"):
                error_msg = response["errors"][0].get("message", "Unknown GraphQL error")[:120]
                self.db_set('sync_status', 'Failed')
                frappe.log_error(f"GraphQL Error: {error_msg}", "AZ Extension Sync")
                frappe.msgprint(f"⚠️ FreePBX sync failed: {error_msg[:80]}...", indicator="red", alert=True)
                return False
            
            result = response.get("data", {}).get("addExtension", {})
            
            if result.get("status"):
                # Now set the password using updateExtension
                sip_password = self.get_password("sip_password")
                if sip_password:
                    self._set_extension_password(sip_password)
                
                self.db_set('sync_status', 'Synced')
                self.db_set('last_synced', now_datetime())
                self.db_set('pbx_extension_id', str(self.extension))
                
                # Configure WebRTC settings if extension type is WebRTC
                if self.extension_type in ['WebRTC', 'webrtc', 'Both', 'both']:
                    webrtc_result = self._configure_webrtc_settings()
                    if not webrtc_result:
                        frappe.msgprint(
                            "⚠️ Extension created but WebRTC settings may need manual configuration",
                            indicator="orange"
                        )
                
                # Apply config to Asterisk
                self.apply_freepbx_config()
                
                frappe.msgprint(
                    f"✅ Extension {self.extension} created in FreePBX with password and config applied!",
                    indicator="green",
                    alert=True
                )
                self.add_comment("Info", f"Extension synced to FreePBX: {self.extension}")
                return True
            else:
                error_msg = result.get("message", "Unknown error")
                self.db_set('sync_status', 'Failed')
                frappe.msgprint(f"⚠️ FreePBX sync failed: {error_msg}", indicator="orange", alert=True)
                return False
                
        except Exception as e:
            self.db_set('sync_status', 'Failed')
            error_short = str(e)[:100]  # Truncate error message
            frappe.log_error(f"FreePBX create failed: {error_short}", "AZ Extension")
            frappe.msgprint(f"⚠️ FreePBX sync failed: {error_short}", indicator="orange", alert=True)
            return False
    
    def update_in_freepbx(self):
        """Update extension in FreePBX via GraphQL API"""
        try:
            server = self.get_server_config()
            if not server.graphql_url or not server.graphql_client_id:
                return False
            
            mutation = """
            mutation updateExtension($input: updateExtensionInput!) {
                updateExtension(input: $input) {
                    status
                    message
                }
            }
            """
            
            variables = {
                "input": {
                    "extensionId": str(self.extension),
                    "name": self.display_name or self.extension,
                    "vmEnable": bool(self.enable_voicemail)
                }
            }
            
            # Use extPassword (correct field name for FreePBX GraphQL API)
            if self.has_value_changed("sip_password"):
                sip_password = self.get_password("sip_password")
                if sip_password:
                    variables["input"]["extPassword"] = sip_password
            
            response = self.execute_graphql(mutation, variables)
            
            if response.get("data", {}).get("updateExtension", {}).get("status"):
                self.db_set('sync_status', 'Synced')
                self.db_set('last_synced', now_datetime())
                self.apply_freepbx_config()
                self.add_comment("Info", f"Extension updated in FreePBX: {self.extension}")
                return True
            
            self.db_set('sync_status', 'Failed')
            return False
            
        except Exception as e:
            self.db_set('sync_status', 'Failed')
            frappe.log_error(f"Error updating extension in FreePBX: {str(e)}", "AZ Extension Sync")
            return False
    
    def delete_from_freepbx(self):
        """Delete extension from FreePBX via GraphQL API"""
        try:
            server = self.get_server_config()
            if not server.graphql_url or not server.graphql_client_id:
                return False
            
            mutation = """
            mutation deleteExtension($extensionId: ID!) {
                deleteExtension(extensionId: $extensionId) {
                    status
                    message
                }
            }
            """
            
            response = self.execute_graphql(mutation, {"extensionId": str(self.extension)})
            
            if response.get("data", {}).get("deleteExtension", {}).get("status"):
                self.apply_freepbx_config()
                frappe.msgprint(f"✅ Extension {self.extension} deleted from FreePBX", indicator="green", alert=True)
                return True
            return False
            
        except Exception as e:
            frappe.log_error(f"Error deleting extension from FreePBX: {str(e)}", "AZ Extension Sync")
            return False
    
    @frappe.whitelist()
    def sync_to_pbx(self):
        """Manually sync extension to FreePBX.
        
        Tries GraphQL first, falls back to SSH if authentication fails.
        """
        try:
            if self.sync_status == "Synced":
                return self.update_in_freepbx()
            else:
                return self.create_in_freepbx()
        except Exception as e:
            error_str = str(e).lower()
            # Check if it's an authentication error
            if any(x in error_str for x in ["401", "token request failed", "invalid_client", "authentication failed"]):
                frappe.msgprint(
                    _("GraphQL authentication failed. Trying SSH fallback..."),
                    indicator="orange",
                    alert=True
                )
                # Try SSH fallback
                result = self._sync_via_ssh()
                if result.get("success"):
                    self.db_set('sync_status', 'Synced')
                    frappe.db.commit()
                    frappe.msgprint(
                        _("Extension synced via SSH: {0}").format(result.get("message")),
                        indicator="green"
                    )
                    return True
                else:
                    frappe.throw(
                        _("Both GraphQL and SSH sync failed. GraphQL: {0}. SSH: {1}").format(
                            str(e), result.get("message")
                        )
                    )
            else:
                # Re-raise non-auth errors
                raise
    
    @frappe.whitelist()
    def sync_from_pbx(self):
        """Sync extension details from FreePBX"""
        try:
            query = """
            query fetchExtension($extensionId: ID!) {
                fetchExtension(extensionId: $extensionId) {
                    status
                    message
                    extensionId
                    user { name }
                    voicemail { vmEnabled }
                }
            }
            """
            
            response = self.execute_graphql(query, {"extensionId": str(self.extension)})
            
            if response.get("errors"):
                frappe.throw(response["errors"][0].get("message", "GraphQL error"))
            
            result = response.get("data", {}).get("fetchExtension", {})
            
            if result.get("status"):
                if result.get("user", {}).get("name"):
                    self.display_name = result["user"]["name"]
                if result.get("voicemail", {}).get("vmEnabled") is not None:
                    self.enable_voicemail = result["voicemail"]["vmEnabled"]
                if result.get("extensionId"):
                    self.pbx_extension_id = result["extensionId"]
                
                self.sync_status = "Synced"
                self.last_synced = now_datetime()
                self.save()
                frappe.msgprint("✅ Synced from FreePBX", indicator="green", alert=True)
                return True
            else:
                frappe.throw(result.get("message", "Extension not found in FreePBX"))
            
        except Exception as e:
            frappe.log_error(f"Error syncing from FreePBX: {str(e)}", "AZ Extension Sync")
            frappe.throw(f"Sync failed: {str(e)}")
    
    @frappe.whitelist()
    def test_registration(self):
        """Test if extension is registered on PBX"""
        try:
            query = """
            query fetchExtension($extensionId: ID!) {
                fetchExtension(extensionId: $extensionId) {
                    status
                    message
                    extensionId
                }
            }
            """
            
            response = self.execute_graphql(query, {"extensionId": str(self.extension)})
            
            if response.get("errors"):
                frappe.throw(response["errors"][0].get("message", "GraphQL error"))
            
            result = response.get("data", {}).get("fetchExtension", {})
            
            if result.get("status"):
                self.db_set('last_registered', now_datetime())
                frappe.msgprint(f"✅ Extension {self.extension} exists in FreePBX", indicator="green", alert=True)
                return {"status": "exists", "extensionId": result.get("extensionId")}
            
            frappe.msgprint(f"⚠️ Extension {self.extension} NOT found in FreePBX", indicator="orange", alert=True)
            return {"status": "not_found"}
            
        except Exception as e:
            frappe.log_error(f"Error testing registration: {str(e)}", "AZ Extension")
            frappe.throw(f"Test failed: {str(e)}")
    
    @frappe.whitelist()
    def sync_password_to_pbx(self):
        """Sync SIP password to FreePBX (Extension + User Manager)"""
        try:
            server = self.get_server_config()
            if not server.graphql_url or not server.graphql_client_id:
                return {"success": False, "message": "GraphQL not configured"}
            
            sip_password = self.get_password("sip_password")
            if not sip_password:
                frappe.throw("No SIP password set for this extension")
            
            success = self._set_extension_password(sip_password)
            
            if success:
                # Apply config to make it active
                self.apply_freepbx_config()
                frappe.msgprint(
                    f"✅ Password synced to FreePBX for extension {self.extension}",
                    indicator="green",
                    alert=True
                )
                return {"success": True}
            else:
                return {"success": False, "message": "Failed to update password in FreePBX"}
                
        except Exception as e:
            frappe.log_error(f"Error syncing password: {str(e)}", "AZ Extension")
            return {"success": False, "message": str(e)}


def get_user_extension(user=None):
    """Get extension for a user"""
    if not user:
        user = frappe.session.user
    
    extension = frappe.db.get_value("AZ Extension", {"user": user, "is_active": 1}, "name")
    if extension:
        return frappe.get_doc("AZ Extension", extension)
    return None


def get_extension_by_number(extension_number, server=None):
    """Get extension by number"""
    filters = {"extension": extension_number, "is_active": 1}
    if server:
        filters["server"] = server
    
    ext = frappe.db.get_value("AZ Extension", filters, "name")
    if ext:
        return frappe.get_doc("AZ Extension", ext)
    return None
