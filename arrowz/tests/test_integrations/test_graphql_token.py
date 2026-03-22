# Test FreePBX Token Manager

import pytest
import frappe
from unittest.mock import MagicMock, patch
import json


class TestFreePBXTokenManager:
    """Test cases for FreePBX OAuth2 token management."""
    
    def test_token_manager_init(self, frappe_site, test_server_config):
        """Test token manager initialization."""
        from arrowz.freepbx_token import FreePBXTokenManager
        
        manager = FreePBXTokenManager(test_server_config.name)
        
        assert manager.server.name == test_server_config.name
        assert manager.cache_key is not None
    
    def test_token_manager_with_doc(self, frappe_site, test_server_config):
        """Test token manager with doc object."""
        from arrowz.freepbx_token import FreePBXTokenManager
        
        manager = FreePBXTokenManager(test_server_config)
        
        assert manager.server.name == test_server_config.name
    
    @patch("requests.post")
    def test_fetch_new_token(self, mock_post, frappe_site, test_server_config):
        """Test fetching new token."""
        from arrowz.freepbx_token import FreePBXTokenManager
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token_12345",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response
        
        manager = FreePBXTokenManager(test_server_config)
        token = manager.get_token()
        
        assert token == "test_token_12345"
    
    @patch("requests.post")
    def test_token_cached(self, mock_post, frappe_site, test_server_config):
        """Test that token is cached."""
        from arrowz.freepbx_token import FreePBXTokenManager
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "cached_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response
        
        manager = FreePBXTokenManager(test_server_config)
        
        # First call
        token1 = manager.get_token()
        
        # Second call should use cache
        token2 = manager.get_token()
        
        # Should only call API once
        assert mock_post.call_count == 1
        assert token1 == token2
        
        # Cleanup cache
        manager.invalidate_token()
    
    def test_invalidate_token(self, frappe_site, test_server_config):
        """Test token invalidation."""
        from arrowz.freepbx_token import FreePBXTokenManager
        
        manager = FreePBXTokenManager(test_server_config)
        
        # Set a fake cached value
        frappe.cache().set_value(manager.cache_key, json.dumps({
            "access_token": "old_token",
            "expires_at": "2030-01-01 00:00:00"
        }))
        
        # Invalidate
        manager.invalidate_token()
        
        # Cache should be empty
        cached = frappe.cache().get_value(manager.cache_key)
        assert cached is None
    
    @patch("requests.post")
    def test_token_request_failure(self, mock_post, frappe_site, test_server_config):
        """Test handling of token request failure."""
        from arrowz.freepbx_token import FreePBXTokenManager
        
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "invalid_client"
        }
        mock_post.return_value = mock_response
        
        manager = FreePBXTokenManager(test_server_config)
        
        with pytest.raises(Exception) as exc_info:
            manager.get_token()
        
        assert "401" in str(exc_info.value) or "Token" in str(exc_info.value)
    
    def test_get_token_info(self, frappe_site, test_server_config):
        """Test getting token info."""
        from arrowz.freepbx_token import FreePBXTokenManager
        
        manager = FreePBXTokenManager(test_server_config)
        
        # No token yet
        info = manager.get_token_info()
        
        assert info["valid"] is False


class TestExecuteGraphQL:
    """Test cases for GraphQL execution."""
    
    @patch("requests.post")
    def test_execute_graphql_success(self, mock_post, frappe_site, test_server_config):
        """Test successful GraphQL execution."""
        from arrowz.freepbx_token import execute_graphql
        
        # Mock token response
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600
        }
        
        # Mock GraphQL response
        gql_response = MagicMock()
        gql_response.status_code = 200
        gql_response.json.return_value = {
            "data": {
                "fetchExtension": {
                    "status": True,
                    "extensionId": "1001"
                }
            }
        }
        gql_response.raise_for_status = MagicMock()
        
        # First call is token, second is GraphQL
        mock_post.side_effect = [token_response, gql_response]
        
        result = execute_graphql(
            test_server_config.name,
            "query { fetchExtension(extensionId: 1001) { status } }"
        )
        
        assert "data" in result
        
        # Cleanup
        from arrowz.freepbx_token import FreePBXTokenManager
        manager = FreePBXTokenManager(test_server_config)
        manager.invalidate_token()
    
    @patch("requests.post")
    def test_execute_graphql_with_variables(self, mock_post, frappe_site, test_server_config):
        """Test GraphQL execution with variables."""
        from arrowz.freepbx_token import execute_graphql
        
        # Mock responses
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600
        }
        
        gql_response = MagicMock()
        gql_response.status_code = 200
        gql_response.json.return_value = {"data": {"result": True}}
        gql_response.raise_for_status = MagicMock()
        
        mock_post.side_effect = [token_response, gql_response]
        
        result = execute_graphql(
            test_server_config.name,
            "mutation addExt($input: Input!) { addExt(input: $input) { status } }",
            {"input": {"extensionId": "1001"}}
        )
        
        assert "data" in result
        
        # Verify variables were sent
        call_args = mock_post.call_args_list[-1]
        assert "variables" in str(call_args)
        
        # Cleanup
        from arrowz.freepbx_token import FreePBXTokenManager
        manager = FreePBXTokenManager(test_server_config)
        manager.invalidate_token()
    
    @patch("requests.post")
    def test_execute_graphql_401_retry(self, mock_post, frappe_site, test_server_config):
        """Test automatic retry on 401."""
        from arrowz.freepbx_token import execute_graphql
        
        # Mock token response
        token_response = MagicMock()
        token_response.status_code = 200
        token_response.json.return_value = {
            "access_token": "new_token",
            "expires_in": 3600
        }
        
        # First GraphQL fails with 401, second succeeds
        gql_fail = MagicMock()
        gql_fail.status_code = 401
        
        gql_success = MagicMock()
        gql_success.status_code = 200
        gql_success.json.return_value = {"data": {"success": True}}
        gql_success.raise_for_status = MagicMock()
        
        mock_post.side_effect = [token_response, gql_fail, token_response, gql_success]
        
        result = execute_graphql(
            test_server_config.name,
            "query { test }"
        )
        
        assert "data" in result
        
        # Cleanup
        from arrowz.freepbx_token import FreePBXTokenManager
        manager = FreePBXTokenManager(test_server_config)
        manager.invalidate_token()
