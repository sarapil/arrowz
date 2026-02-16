# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
FreePBX OAuth Token Manager
===========================
Automatically manages OAuth2 tokens for FreePBX GraphQL API.
- Fetches new token when needed
- Caches token in Redis
- Checks expiry before each request
- Auto-refreshes expired tokens
"""

import frappe
from frappe.utils import now_datetime, get_datetime, add_to_date
import requests
import json
from datetime import datetime, timedelta

# Cache key prefix
CACHE_PREFIX = "freepbx_oauth_token:"

# Token refresh buffer (refresh 5 minutes before expiry)
REFRESH_BUFFER_SECONDS = 300


class FreePBXTokenManager:
    """Manages OAuth2 tokens for FreePBX GraphQL API."""
    
    def __init__(self, server_config):
        """
        Initialize with server config.
        
        Args:
            server_config: AZ Server Config document or name
        """
        if isinstance(server_config, str):
            self.server = frappe.get_doc("AZ Server Config", server_config)
        else:
            self.server = server_config
        
        self.cache_key = f"{CACHE_PREFIX}{self.server.name}"
    
    def get_token(self) -> str:
        """
        Get a valid access token, fetching new one if needed.
        
        Returns:
            str: Valid Bearer token
        
        Raises:
            Exception: If token cannot be obtained
        """
        # Check cache first
        cached = self._get_cached_token()
        if cached:
            return cached
        
        # Fetch new token
        return self._fetch_new_token()
    
    def _get_cached_token(self) -> str | None:
        """Get token from cache if valid."""
        try:
            cached_data = frappe.cache().get_value(self.cache_key)
            
            if not cached_data:
                return None
            
            # Parse cached data
            if isinstance(cached_data, str):
                cached_data = json.loads(cached_data)
            
            access_token = cached_data.get("access_token")
            expires_at = cached_data.get("expires_at")
            
            if not access_token or not expires_at:
                return None
            
            # Check if token is still valid (with buffer)
            expires_dt = get_datetime(expires_at)
            now = now_datetime()
            buffer = timedelta(seconds=REFRESH_BUFFER_SECONDS)
            
            if now + buffer >= expires_dt:
                # Token expired or about to expire
                frappe.cache().delete_value(self.cache_key)
                return None
            
            return access_token
            
        except Exception as e:
            frappe.log_error(f"Cache read error: {str(e)[:100]}", "FreePBX Token")
            return None
    
    def _fetch_new_token(self) -> str:
        """Fetch new OAuth2 token from FreePBX."""
        
        if not self.server.graphql_enabled:
            frappe.throw("GraphQL API is not enabled for this server")
        
        if not self.server.graphql_client_id:
            frappe.throw("GraphQL Client ID is required")
        
        client_secret = self.server.get_password("graphql_client_secret")
        if not client_secret:
            frappe.throw("GraphQL Client Secret is required")
        
        # Build token URL from GraphQL URL
        base_url = self.server.graphql_url.replace("/admin/api/api/gql", "").replace("/admin/api/gql", "")
        token_url = f"{base_url}/admin/api/api/token"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.server.graphql_client_id,
            "client_secret": client_secret
        }
        
        try:
            response = requests.post(
                token_url,
                headers=headers,
                data=data,
                verify=self.server.verify_ssl,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"Token request failed: HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = error_data.get("error", {}).get("message", error_msg)
                except:
                    pass
                frappe.throw(error_msg)
            
            token_data = response.json()
            
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
            
            if not access_token:
                frappe.throw("No access token in response")
            
            # Calculate expiry time
            expires_at = add_to_date(now_datetime(), seconds=expires_in)
            
            # Cache the token
            cache_data = {
                "access_token": access_token,
                "token_type": token_data.get("token_type", "Bearer"),
                "expires_in": expires_in,
                "expires_at": str(expires_at),
                "fetched_at": str(now_datetime())
            }
            
            # Store in cache (expire slightly before token expires)
            cache_ttl = max(expires_in - REFRESH_BUFFER_SECONDS, 60)
            frappe.cache().set_value(
                self.cache_key,
                json.dumps(cache_data),
                expires_in_sec=cache_ttl
            )
            
            # Update server status
            self._update_server_status("Valid", expires_at)
            
            frappe.log_error(
                f"New token obtained, expires in {expires_in}s",
                "FreePBX Token Success"
            )
            
            return access_token
            
        except requests.exceptions.RequestException as e:
            error_short = str(e)[:100]
            self._update_server_status(f"Error: {error_short[:50]}", None)
            frappe.throw(f"Token request failed: {error_short}")
    
    def _update_server_status(self, status: str, expires_at):
        """Update token status on server config."""
        try:
            if expires_at:
                status_text = f"✅ Valid until {expires_at.strftime('%Y-%m-%d %H:%M')}"
            else:
                status_text = f"❌ {status}"
            
            frappe.db.set_value(
                "AZ Server Config",
                self.server.name,
                "token_status",
                status_text,
                update_modified=False
            )
            frappe.db.commit()
        except:
            pass  # Don't fail on status update
    
    def invalidate_token(self):
        """Force invalidate cached token."""
        frappe.cache().delete_value(self.cache_key)
        self._update_server_status("Invalidated", None)
    
    def get_token_info(self) -> dict:
        """Get information about current token."""
        cached_data = frappe.cache().get_value(self.cache_key)
        
        if not cached_data:
            return {"status": "No token", "valid": False}
        
        if isinstance(cached_data, str):
            cached_data = json.loads(cached_data)
        
        expires_at = get_datetime(cached_data.get("expires_at"))
        now = now_datetime()
        
        remaining = (expires_at - now).total_seconds()
        
        return {
            "status": "Valid" if remaining > 0 else "Expired",
            "valid": remaining > 0,
            "expires_at": str(expires_at),
            "remaining_seconds": max(0, int(remaining)),
            "fetched_at": cached_data.get("fetched_at")
        }


def get_graphql_token(server_name: str) -> str:
    """
    Convenience function to get token for a server.
    
    Args:
        server_name: Name of AZ Server Config
    
    Returns:
        str: Valid access token
    """
    manager = FreePBXTokenManager(server_name)
    return manager.get_token()


def execute_graphql(server_name: str, query: str, variables: dict = None) -> dict:
    """
    Execute GraphQL query with automatic token management.
    
    Args:
        server_name: Name of AZ Server Config
        query: GraphQL query string
        variables: Optional query variables
    
    Returns:
        dict: GraphQL response
    """
    server = frappe.get_doc("AZ Server Config", server_name)
    
    if not server.graphql_enabled or not server.graphql_url:
        frappe.throw("GraphQL is not configured for this server")
    
    # Get token
    manager = FreePBXTokenManager(server)
    access_token = manager.get_token()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    try:
        response = requests.post(
            server.graphql_url,
            json=payload,
            headers=headers,
            verify=server.verify_ssl,
            timeout=30
        )
        
        # Check for auth error (token might have been invalidated)
        if response.status_code == 401:
            # Invalidate and retry once
            manager.invalidate_token()
            access_token = manager.get_token()
            headers["Authorization"] = f"Bearer {access_token}"
            
            response = requests.post(
                server.graphql_url,
                json=payload,
                headers=headers,
                verify=server.verify_ssl,
                timeout=30
            )
        
        # For 400 errors, try to get the actual error message from response
        if response.status_code == 400:
            try:
                error_data = response.json()
                if "errors" in error_data:
                    # Return GraphQL errors instead of raising HTTP error
                    return error_data
                else:
                    frappe.log_error(f"400 Error Response: {response.text[:500]}", "FreePBX GraphQL 400")
            except:
                frappe.log_error(f"400 Error (non-JSON): {response.text[:500]}", "FreePBX GraphQL 400")
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        frappe.log_error(f"GraphQL error: {str(e)[:100]}", "FreePBX GraphQL")
        raise


@frappe.whitelist()
def test_graphql_connection(server_name: str) -> dict:
    """
    Test GraphQL connection and token.
    
    Args:
        server_name: Name of AZ Server Config
    
    Returns:
        dict: Test results
    """
    try:
        # Test query
        result = execute_graphql(
            server_name,
            "{ fetchAllExtensions { status totalCount } }"
        )
        
        if "errors" in result:
            return {
                "success": False,
                "error": result["errors"][0].get("message", "Unknown error")
            }
        
        data = result.get("data", {}).get("fetchAllExtensions", {})
        
        # Get token info
        manager = FreePBXTokenManager(server_name)
        token_info = manager.get_token_info()
        
        return {
            "success": True,
            "extensions_count": data.get("totalCount", 0),
            "token_valid": token_info.get("valid", False),
            "token_expires_at": token_info.get("expires_at"),
            "token_remaining_seconds": token_info.get("remaining_seconds", 0)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)[:200]
        }


@frappe.whitelist()
def refresh_token(server_name: str) -> dict:
    """
    Force refresh the OAuth token.
    
    Args:
        server_name: Name of AZ Server Config
    
    Returns:
        dict: New token info
    """
    try:
        manager = FreePBXTokenManager(server_name)
        manager.invalidate_token()
        manager.get_token()  # This will fetch a new token
        
        return {
            "success": True,
            "message": "Token refreshed successfully",
            "token_info": manager.get_token_info()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)[:200]
        }
