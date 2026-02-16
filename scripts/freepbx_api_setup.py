#!/usr/bin/env python3
"""
FreePBX API Client Setup Helper
================================
Helps diagnose and fix GraphQL API authentication issues.

Usage:
    python3 freepbx_api_setup.py check
    python3 freepbx_api_setup.py test-token <client_id> <client_secret>
"""

import sys
import requests
from urllib.parse import urljoin
import urllib3

# Disable SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_graphql_requirements():
    """Print requirements for FreePBX GraphQL API."""
    print_header("FreePBX GraphQL API Requirements")
    print("""
To use GraphQL API with FreePBX 17, you need:

1. ✅ FreePBX 17 or higher
2. ✅ API Module installed and enabled
3. ✅ GraphQL API enabled in Admin > API

Steps to create API Client:
---------------------------

1. Log into FreePBX Admin Panel
   https://pbx.tavira-group.com/admin

2. Go to: Admin → API → Add API Application

3. Fill in the details:
   - Application Name: Arrowz
   - Application Description: Arrowz VoIP Integration
   - Client ID: (auto-generated or custom, e.g., arrowz_client)
   - Client Secret: (auto-generated, COPY THIS!)
   - Redirect URI: Leave empty (not needed for client_credentials)
   - Token Expiration: 3600 (1 hour) or more
   
4. Enable Scopes:
   ✅ gql              - GraphQL Access
   ✅ write:extensions - Create/Update Extensions
   ✅ read:extensions  - Read Extensions
   ✅ write:users      - Create/Update Users (optional)
   ✅ read:users       - Read Users (optional)

5. Save and copy the Client ID and Client Secret

6. Update AZ Server Config in ERPNext:
   - GraphQL URL: https://pbx.tavira-group.com/admin/api/api/gql
   - GraphQL Client ID: <your_client_id>
   - GraphQL Client Secret: <your_client_secret>
   - Verify SSL: Uncheck if using self-signed cert

Common 401 Error Causes:
------------------------
1. Wrong Client ID or Secret
2. Client Secret was regenerated in FreePBX
3. API Application was deleted or disabled
4. Scopes not properly set
5. Token endpoint URL is wrong
""")


def test_token(base_url, client_id, client_secret, verify_ssl=False):
    """Test token generation with provided credentials."""
    print_header(f"Testing Token for {base_url}")
    
    # Build token URL
    token_url = f"{base_url.rstrip('/')}/admin/api/api/token"
    
    print(f"\n📍 Token URL: {token_url}")
    print(f"📍 Client ID: {client_id}")
    print(f"📍 Client Secret: {'*' * 10}...{client_secret[-4:]}")
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    try:
        print("\n🔄 Sending token request...")
        response = requests.post(
            token_url,
            headers=headers,
            data=data,
            verify=verify_ssl,
            timeout=30
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("\n✅ SUCCESS! Token obtained!")
            print(f"   Token Type: {token_data.get('token_type', 'Bearer')}")
            print(f"   Expires In: {token_data.get('expires_in', 'unknown')} seconds")
            print(f"   Access Token: {token_data.get('access_token', '')[:50]}...")
            
            # Test GraphQL endpoint
            test_graphql(base_url, token_data.get('access_token'), verify_ssl)
            
            return True
        elif response.status_code == 401:
            print("\n❌ ERROR 401: Unauthorized")
            print("   Possible causes:")
            print("   1. Wrong Client ID")
            print("   2. Wrong Client Secret")
            print("   3. Client was deleted or disabled in FreePBX")
            print("   4. API module not enabled")
            
            try:
                error_body = response.json()
                print(f"\n   Error details: {error_body}")
            except:
                print(f"\n   Error body: {response.text[:200]}")
            
            return False
        else:
            print(f"\n❌ ERROR {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"\n❌ SSL Error: {e}")
        print("   Try with verify_ssl=False or fix certificate")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("   Check if FreePBX is accessible")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_graphql(base_url, token, verify_ssl=False):
    """Test GraphQL endpoint with token."""
    print("\n🔄 Testing GraphQL endpoint...")
    
    graphql_url = f"{base_url.rstrip('/')}/admin/api/api/gql"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Simple query to test
    query = """
    query {
        fetchAllExtensions {
            status
            message
            totalCount
        }
    }
    """
    
    try:
        response = requests.post(
            graphql_url,
            headers=headers,
            json={"query": query},
            verify=verify_ssl,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"⚠️ GraphQL errors: {data['errors']}")
            else:
                result = data.get("data", {}).get("fetchAllExtensions", {})
                print(f"✅ GraphQL works!")
                print(f"   Total extensions: {result.get('totalCount', 'unknown')}")
        else:
            print(f"❌ GraphQL failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ GraphQL test error: {e}")


def print_freepbx_commands():
    """Print commands to run on FreePBX to check API status."""
    print_header("FreePBX Diagnostic Commands")
    print("""
Run these on FreePBX server to diagnose API issues:

# Check if API module is installed
fwconsole ma list | grep api

# Check Apache configuration
apachectl -S | grep -i api

# Check API logs
tail -50 /var/log/httpd/access_log | grep -i api
tail -50 /var/log/httpd/error_log | grep -i api

# Check if GraphQL endpoint responds
curl -k https://localhost/admin/api/api/gql -X OPTIONS

# List OAuth clients (requires DB access)
mysql asterisk -e "SELECT * FROM api_applications;"

# Check API module settings
fwconsole setting API_ENABLED
fwconsole setting GRAPHQL_ENABLED

# Restart services
fwconsole restart
""")


def main():
    if len(sys.argv) < 2:
        print("""
FreePBX API Setup Helper
========================

Usage:
    python3 freepbx_api_setup.py check
        - Show requirements and setup instructions
    
    python3 freepbx_api_setup.py test <base_url> <client_id> <client_secret>
        - Test token generation with credentials
    
    python3 freepbx_api_setup.py commands
        - Show FreePBX diagnostic commands

Examples:
    python3 freepbx_api_setup.py check
    python3 freepbx_api_setup.py test https://pbx.tavira-group.com my_client_id my_secret
    python3 freepbx_api_setup.py commands
""")
        return
    
    command = sys.argv[1].lower()
    
    if command == "check":
        check_graphql_requirements()
    elif command == "test":
        if len(sys.argv) < 5:
            print("Usage: python3 freepbx_api_setup.py test <base_url> <client_id> <client_secret>")
            return
        base_url = sys.argv[2]
        client_id = sys.argv[3]
        client_secret = sys.argv[4]
        test_token(base_url, client_id, client_secret)
    elif command == "commands":
        print_freepbx_commands()
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
