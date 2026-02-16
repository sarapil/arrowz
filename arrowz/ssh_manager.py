# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
SSH Manager for FreePBX fwconsole operations.

This module provides SSH connectivity to FreePBX for operations not supported
by GraphQL API, such as:
- Trunks management
- Outbound Routes management
- System commands (fwconsole)
- Asterisk CLI commands
"""

import frappe
from frappe.utils import now_datetime
import json
import re

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False


class SSHManager:
    """
    Manages SSH connections to FreePBX servers for fwconsole operations.
    """
    
    def __init__(self, server_name: str):
        """
        Initialize SSH manager for a server.
        
        Args:
            server_name: Name of AZ Server Config document
        """
        if not HAS_PARAMIKO:
            frappe.throw("paramiko library is not installed. Run: pip install paramiko")
        
        self.server_name = server_name
        self.server = frappe.get_doc("AZ Server Config", server_name)
        self.client = None
        
        if not self.server.ssh_enabled:
            frappe.throw(f"SSH is not enabled for server: {server_name}")
    
    def connect(self) -> bool:
        """
        Establish SSH connection to the server.
        
        Returns:
            bool: True if connected successfully
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh_host = self.server.ssh_host or self.server.host
            ssh_port = self.server.ssh_port or 22
            ssh_username = self.server.ssh_username
            
            if not ssh_host:
                frappe.throw("SSH Host is not configured")
            if not ssh_username:
                frappe.throw("SSH Username is not configured")
            
            connect_kwargs = {
                "hostname": ssh_host,
                "port": int(ssh_port),
                "username": ssh_username,
                "timeout": 30,
                "allow_agent": False,
                "look_for_keys": False
            }
            
            if self.server.ssh_auth_type == "Password":
                password = self.server.get_password("ssh_password")
                if not password:
                    frappe.throw("SSH Password is not configured")
                connect_kwargs["password"] = password
            else:
                # Private Key authentication
                private_key_str = self.server.ssh_private_key
                if private_key_str:
                    import io
                    
                    # Clean up the key string (remove extra whitespace/newlines)
                    private_key_str = private_key_str.strip()
                    
                    pkey = None
                    last_error = None
                    
                    # Try different key types and formats
                    key_classes = [
                        (paramiko.RSAKey, "RSA"),
                        (paramiko.Ed25519Key, "Ed25519"),
                        (paramiko.ECDSAKey, "ECDSA"),
                    ]
                    
                    for key_class, key_name in key_classes:
                        try:
                            key_file = io.StringIO(private_key_str)
                            pkey = key_class.from_private_key(key_file)
                            break
                        except Exception as e:
                            last_error = str(e)
                            continue
                    
                    if not pkey:
                        error_msg = f"Could not parse SSH private key. Last error: {last_error[:50] if last_error else 'Unknown'}"
                        frappe.log_error(error_msg, "SSH Key Parse Error")
                        frappe.throw(error_msg)
                    
                    connect_kwargs["pkey"] = pkey
                else:
                    frappe.throw("SSH Private Key is required for key-based authentication")
            
            self.client.connect(**connect_kwargs)
            
            # Update server status
            self.server.db_set('connection_status', 'Connected')
            self.server.db_set('last_health_check', now_datetime())
            self.server.db_set('last_error', None)
            
            return True
            
        except paramiko.AuthenticationException as e:
            auth_type = self.server.ssh_auth_type or "Password"
            if auth_type == "RSA Key":
                error_msg = f"SSH Key Authentication failed for {ssh_username}@{ssh_host}. Ensure the public key is added to ~/.ssh/authorized_keys on the server."
            else:
                error_msg = f"SSH Authentication failed for {ssh_username}@{ssh_host}. Check username/password."
            self.server.db_set('connection_status', 'Error')
            self.server.db_set('last_error', error_msg)
            frappe.log_error(error_msg, "SSH Manager")
            raise Exception(error_msg)
            
        except paramiko.SSHException as e:
            error_msg = f"SSH error: {str(e)[:100]}"
            self.server.db_set('connection_status', 'Error')
            self.server.db_set('last_error', error_msg)
            frappe.log_error(error_msg, "SSH Manager")
            raise
            
        except Exception as e:
            error_msg = str(e)[:200]
            self.server.db_set('connection_status', 'Error')
            self.server.db_set('last_error', error_msg)
            frappe.log_error(f"SSH connection failed: {error_msg}", "SSH Manager")
            raise
    
    def disconnect(self):
        """Close SSH connection."""
        if self.client:
            self.client.close()
            self.client = None
    
    def execute(self, command: str, timeout: int = 60) -> dict:
        """
        Execute a command on the remote server.
        
        Args:
            command: Command to execute
            timeout: Command timeout in seconds
        
        Returns:
            dict: {success, stdout, stderr, exit_code}
        """
        if not self.client:
            self.connect()
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            exit_code = stdout.channel.recv_exit_status()
            
            return {
                "success": exit_code == 0,
                "stdout": stdout.read().decode('utf-8', errors='replace'),
                "stderr": stderr.read().decode('utf-8', errors='replace'),
                "exit_code": exit_code
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1
            }
    
    def fwconsole(self, command: str, args: str = "") -> dict:
        """
        Execute fwconsole command.
        
        Args:
            command: fwconsole command (e.g., 'reload', 'ma list')
            args: Additional arguments
        
        Returns:
            dict: Command result
        """
        full_command = f"fwconsole {command}"
        if args:
            full_command += f" {args}"
        
        return self.execute(full_command)
    
    def asterisk_cli(self, command: str) -> dict:
        """
        Execute Asterisk CLI command.
        
        Args:
            command: Asterisk CLI command
        
        Returns:
            dict: Command result
        """
        return self.execute(f'asterisk -rx "{command}"')
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# ==================== fwconsole Operations ====================

def test_ssh_connection(server_name: str) -> dict:
    """
    Test SSH connection to a server.
    
    Args:
        server_name: Name of AZ Server Config
    
    Returns:
        dict: Test results
    """
    try:
        with SSHManager(server_name) as ssh:
            result = ssh.execute("echo 'SSH Connection OK'")
            return {
                "success": True,
                "message": "SSH connection successful",
                "output": result.get("stdout", "").strip()
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"SSH connection failed: {str(e)[:100]}"
        }


def reload_asterisk(server_name: str) -> dict:
    """
    Reload Asterisk configuration (fwconsole reload).
    
    Args:
        server_name: Name of AZ Server Config
    
    Returns:
        dict: Reload result
    """
    try:
        with SSHManager(server_name) as ssh:
            result = ssh.fwconsole("reload")
            return {
                "success": result["success"],
                "message": "Asterisk reloaded" if result["success"] else "Reload failed",
                "output": result.get("stdout", "")
            }
    except Exception as e:
        return {"success": False, "message": str(e)[:100]}


def apply_config(server_name: str) -> dict:
    """
    Apply FreePBX configuration (fwconsole reload).
    Same as clicking "Apply Config" in FreePBX GUI.
    
    Args:
        server_name: Name of AZ Server Config
    
    Returns:
        dict: Apply result
    """
    return reload_asterisk(server_name)


# ==================== Trunk Operations ====================

def list_trunks(server_name: str) -> dict:
    """
    List all SIP trunks.
    
    Args:
        server_name: Name of AZ Server Config
    
    Returns:
        dict: List of trunks
    """
    try:
        with SSHManager(server_name) as ssh:
            # Get trunk list using MySQL query
            result = ssh.execute(
                "mysql -N -e \"SELECT trunkid, name, tech, channelid FROM asterisk.trunks ORDER BY trunkid\""
            )
            
            if not result["success"]:
                return {"success": False, "message": result.get("stderr", "Failed to list trunks")}
            
            trunks = []
            for line in result["stdout"].strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        trunks.append({
                            "id": parts[0],
                            "name": parts[1],
                            "tech": parts[2],
                            "channelid": parts[3]
                        })
            
            return {"success": True, "trunks": trunks}
            
    except Exception as e:
        return {"success": False, "message": str(e)[:100]}


def get_trunk_status(server_name: str) -> dict:
    """
    Get registration status of all PJSIP trunks.
    
    Args:
        server_name: Name of AZ Server Config
    
    Returns:
        dict: Trunk statuses
    """
    try:
        with SSHManager(server_name) as ssh:
            result = ssh.asterisk_cli("pjsip show registrations")
            
            if not result["success"]:
                return {"success": False, "message": "Failed to get trunk status"}
            
            # Parse registration output
            registrations = []
            lines = result["stdout"].split('\n')
            for line in lines:
                if 'Registered' in line or 'Unregistered' in line:
                    registrations.append(line.strip())
            
            return {
                "success": True,
                "registrations": registrations,
                "raw_output": result["stdout"]
            }
            
    except Exception as e:
        return {"success": False, "message": str(e)[:100]}


def create_trunk(server_name: str, trunk_data: dict) -> dict:
    """
    Create a new SIP trunk using fwconsole.
    
    Args:
        server_name: Name of AZ Server Config
        trunk_data: Trunk configuration
            - name: Trunk name
            - host: SIP provider host
            - username: SIP username
            - password: SIP password
            - context: Dial context (default: from-pstn)
    
    Returns:
        dict: Creation result
    """
    try:
        name = trunk_data.get("name")
        host = trunk_data.get("host")
        username = trunk_data.get("username", "")
        password = trunk_data.get("password", "")
        context = trunk_data.get("context", "from-pstn")
        
        if not name or not host:
            return {"success": False, "message": "Trunk name and host are required"}
        
        with SSHManager(server_name) as ssh:
            # Create PJSIP trunk using MySQL (fwconsole doesn't have direct trunk creation)
            # This is a simplified example - real implementation would be more complex
            
            # First, get the next trunk ID
            result = ssh.execute(
                "mysql -N -e \"SELECT COALESCE(MAX(trunkid), 0) + 1 FROM asterisk.trunks\""
            )
            next_id = result["stdout"].strip() or "1"
            
            # Insert trunk
            sql = f"""
            INSERT INTO asterisk.trunks (trunkid, name, tech, channelid, outcid, maxchans, dialoutprefix, disabled)
            VALUES ({next_id}, '{name}', 'pjsip', '{name}', '', 0, '', 'off')
            """
            result = ssh.execute(f'mysql -e "{sql}"')
            
            if not result["success"]:
                return {"success": False, "message": f"Failed to create trunk: {result.get('stderr', '')[:80]}"}
            
            # Reload to apply
            reload_result = ssh.fwconsole("reload")
            
            return {
                "success": True,
                "message": f"Trunk '{name}' created successfully",
                "trunk_id": next_id
            }
            
    except Exception as e:
        return {"success": False, "message": str(e)[:100]}


def delete_trunk(server_name: str, trunk_id: str) -> dict:
    """
    Delete a SIP trunk.
    
    Args:
        server_name: Name of AZ Server Config
        trunk_id: Trunk ID to delete
    
    Returns:
        dict: Deletion result
    """
    try:
        with SSHManager(server_name) as ssh:
            result = ssh.execute(
                f'mysql -e "DELETE FROM asterisk.trunks WHERE trunkid = {trunk_id}"'
            )
            
            if result["success"]:
                ssh.fwconsole("reload")
                return {"success": True, "message": f"Trunk {trunk_id} deleted"}
            else:
                return {"success": False, "message": result.get("stderr", "Delete failed")[:80]}
                
    except Exception as e:
        return {"success": False, "message": str(e)[:100]}


# ==================== Outbound Route Operations ====================

def list_outbound_routes(server_name: str) -> dict:
    """
    List all outbound routes.
    
    Args:
        server_name: Name of AZ Server Config
    
    Returns:
        dict: List of outbound routes
    """
    try:
        with SSHManager(server_name) as ssh:
            result = ssh.execute(
                "mysql -N -e \"SELECT route_id, name, outcid, seq FROM asterisk.outbound_routes ORDER BY seq\""
            )
            
            if not result["success"]:
                return {"success": False, "message": result.get("stderr", "Failed to list routes")}
            
            routes = []
            for line in result["stdout"].strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        routes.append({
                            "id": parts[0],
                            "name": parts[1],
                            "caller_id": parts[2],
                            "sequence": parts[3]
                        })
            
            return {"success": True, "routes": routes}
            
    except Exception as e:
        return {"success": False, "message": str(e)[:100]}


# ==================== System Commands ====================

def get_system_status(server_name: str) -> dict:
    """
    Get FreePBX system status.
    
    Args:
        server_name: Name of AZ Server Config
    
    Returns:
        dict: System status information
    """
    try:
        with SSHManager(server_name) as ssh:
            status = {}
            
            # Get Asterisk version
            result = ssh.asterisk_cli("core show version")
            if result["success"]:
                status["asterisk_version"] = result["stdout"].split('\n')[0].strip()
            
            # Get active channels
            result = ssh.asterisk_cli("core show channels count")
            if result["success"]:
                status["channels_info"] = result["stdout"].strip()
            
            # Get uptime
            result = ssh.asterisk_cli("core show uptime")
            if result["success"]:
                status["uptime"] = result["stdout"].strip()
            
            # Get fwconsole version
            result = ssh.fwconsole("--version")
            if result["success"]:
                status["freepbx_version"] = result["stdout"].strip()
            
            return {"success": True, "status": status}
            
    except Exception as e:
        return {"success": False, "message": str(e)[:100]}


def get_active_calls(server_name: str) -> dict:
    """
    Get list of active calls.
    
    Args:
        server_name: Name of AZ Server Config
    
    Returns:
        dict: Active calls information
    """
    try:
        with SSHManager(server_name) as ssh:
            result = ssh.asterisk_cli("core show channels concise")
            
            if not result["success"]:
                return {"success": False, "message": "Failed to get active calls"}
            
            calls = []
            for line in result["stdout"].strip().split('\n'):
                if line and not line.startswith('!'):
                    parts = line.split('!')
                    if len(parts) >= 5:
                        calls.append({
                            "channel": parts[0],
                            "context": parts[1] if len(parts) > 1 else "",
                            "extension": parts[2] if len(parts) > 2 else "",
                            "state": parts[4] if len(parts) > 4 else ""
                        })
            
            return {
                "success": True,
                "call_count": len(calls),
                "calls": calls
            }
            
    except Exception as e:
        return {"success": False, "message": str(e)[:100]}


def restart_asterisk(server_name: str) -> dict:
    """
    Restart Asterisk service.
    WARNING: This will drop all active calls!
    
    Args:
        server_name: Name of AZ Server Config
    
    Returns:
        dict: Restart result
    """
    try:
        with SSHManager(server_name) as ssh:
            result = ssh.fwconsole("restart")
            return {
                "success": result["success"],
                "message": "Asterisk restarted" if result["success"] else "Restart failed",
                "output": result.get("stdout", "")
            }
    except Exception as e:
        return {"success": False, "message": str(e)[:100]}


# ==================== Frappe API Endpoints ====================

@frappe.whitelist()
def test_ssh(server_name: str) -> dict:
    """API endpoint to test SSH connection."""
    return test_ssh_connection(server_name)


@frappe.whitelist()
def ssh_reload(server_name: str) -> dict:
    """API endpoint to reload Asterisk via SSH."""
    return reload_asterisk(server_name)


@frappe.whitelist()
def ssh_get_trunks(server_name: str) -> dict:
    """API endpoint to list trunks."""
    return list_trunks(server_name)


@frappe.whitelist()
def ssh_get_trunk_status(server_name: str) -> dict:
    """API endpoint to get trunk registration status."""
    return get_trunk_status(server_name)


@frappe.whitelist()
def ssh_get_routes(server_name: str) -> dict:
    """API endpoint to list outbound routes."""
    return list_outbound_routes(server_name)


@frappe.whitelist()
def ssh_get_status(server_name: str) -> dict:
    """API endpoint to get system status."""
    return get_system_status(server_name)


@frappe.whitelist()
def ssh_get_calls(server_name: str) -> dict:
    """API endpoint to get active calls."""
    return get_active_calls(server_name)


@frappe.whitelist()
def ssh_debug_key(server_name: str) -> dict:
    """
    API endpoint to debug SSH key configuration.
    Returns information about the stored key for troubleshooting.
    """
    try:
        server = frappe.get_doc("AZ Server Config", server_name)
        
        result = {
            "ssh_enabled": server.ssh_enabled,
            "ssh_auth_type": server.ssh_auth_type,
            "ssh_host": server.ssh_host or server.host,
            "ssh_port": server.ssh_port or 22,
            "ssh_username": server.ssh_username,
            "has_private_key": bool(server.ssh_private_key),
        }
        
        if server.ssh_private_key:
            key_str = server.ssh_private_key.strip()
            lines = key_str.split('\n')
            
            result["key_info"] = {
                "first_line": lines[0] if lines else "",
                "last_line": lines[-1] if lines else "",
                "total_lines": len(lines),
                "total_chars": len(key_str),
            }
            
            # Try to parse the key
            import io
            import paramiko
            
            parse_results = []
            for key_class, key_name in [
                (paramiko.RSAKey, "RSA"),
                (paramiko.Ed25519Key, "Ed25519"),
                (paramiko.ECDSAKey, "ECDSA"),
            ]:
                try:
                    key_file = io.StringIO(key_str)
                    pkey = key_class.from_private_key(key_file)
                    parse_results.append({
                        "type": key_name,
                        "success": True,
                        "fingerprint": pkey.get_fingerprint().hex()[:32],
                        "bits": pkey.get_bits() if hasattr(pkey, 'get_bits') else "N/A"
                    })
                except Exception as e:
                    parse_results.append({
                        "type": key_name,
                        "success": False,
                        "error": str(e)[:100]
                    })
            
            result["parse_results"] = parse_results
            
            # Check if any parsing succeeded
            successful = [p for p in parse_results if p["success"]]
            if successful:
                result["key_valid"] = True
                result["key_type"] = successful[0]["type"]
                result["key_fingerprint"] = successful[0]["fingerprint"]
            else:
                result["key_valid"] = False
        
        return {"success": True, "data": result}
        
    except Exception as e:
        return {"success": False, "message": str(e)[:200]}
