#!/usr/bin/env python3
"""
FreePBX GraphQL Token Generator
===============================
This script generates a long-lived OAuth2 access token for FreePBX GraphQL API.

Usage:
    python get_freepbx_token.py

You will be prompted to enter:
    - FreePBX URL (e.g., https://172.21.0.2)
    - Client ID (from FreePBX API application)
    - Client Secret (from FreePBX API application)

The script will output the access token to use in AZ Server Config.
"""

import requests
import json
import urllib3
import sys
import getpass

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_access_token(base_url: str, client_id: str, client_secret: str) -> dict:
    """
    Get OAuth2 access token from FreePBX.
    
    Args:
        base_url: FreePBX base URL (e.g., https://172.21.0.2)
        client_id: OAuth2 Client ID
        client_secret: OAuth2 Client Secret
    
    Returns:
        dict with access_token, token_type, expires_in
    """
    token_url = f"{base_url.rstrip('/')}/admin/api/api/token"
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    print(f"\n🔄 Requesting token from: {token_url}")
    
    try:
        response = requests.post(
            token_url,
            headers=headers,
            data=data,
            verify=False,  # Skip SSL verification for self-signed certs
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"\n❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Connection error: {e}")
        return None


def test_token(base_url: str, access_token: str) -> bool:
    """Test if the token works with a simple GraphQL query."""
    
    gql_url = f"{base_url.rstrip('/')}/admin/api/api/gql"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    # Simple test query
    query = {
        "query": """
        {
            fetchAllExtensions {
                status
                message
                totalCount
            }
        }
        """
    }
    
    print(f"\n🧪 Testing token with GraphQL query...")
    
    try:
        response = requests.post(
            gql_url,
            headers=headers,
            json=query,
            verify=False,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" not in data:
                result = data.get("data", {}).get("fetchAllExtensions", {})
                print(f"   ✅ Token works! Found {result.get('totalCount', 0)} extensions")
                return True
            else:
                print(f"   ⚠️ GraphQL error: {data['errors']}")
                return False
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def calculate_expiry(expires_in: int) -> str:
    """Convert seconds to human-readable duration."""
    if expires_in >= 31536000:
        years = expires_in // 31536000
        return f"{years} year(s)"
    elif expires_in >= 86400:
        days = expires_in // 86400
        return f"{days} day(s)"
    elif expires_in >= 3600:
        hours = expires_in // 3600
        return f"{hours} hour(s)"
    else:
        return f"{expires_in} seconds"


def main():
    print("=" * 60)
    print("   FreePBX GraphQL Token Generator")
    print("=" * 60)
    print()
    print("This script will generate an OAuth2 access token for")
    print("FreePBX GraphQL API to use in Arrowz AZ Server Config.")
    print()
    print("Prerequisites:")
    print("  1. Create an Application in FreePBX:")
    print("     Admin → API → GraphQL → Applications → Add")
    print("  2. Choose 'Machine-to-Machine' type")
    print("  3. Note the Client ID and Client Secret")
    print()
    print("-" * 60)
    
    # Get input from user
    base_url = input("\n📍 FreePBX URL (e.g., https://172.21.0.2): ").strip()
    if not base_url:
        base_url = "https://172.21.0.2"
    
    if not base_url.startswith("http"):
        base_url = f"https://{base_url}"
    
    client_id = input("🔑 Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required!")
        sys.exit(1)
    
    client_secret = getpass.getpass("🔒 Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret is required!")
        sys.exit(1)
    
    # Get the token
    result = get_access_token(base_url, client_id, client_secret)
    
    if not result or "access_token" not in result:
        print("\n❌ Failed to get access token!")
        print("\nTroubleshooting:")
        print("  1. Verify Client ID and Secret are correct")
        print("  2. Check that the Application is active in FreePBX")
        print("  3. Ensure the Application type is 'Machine-to-Machine'")
        print("  4. Check FreePBX API module is enabled")
        sys.exit(1)
    
    access_token = result["access_token"]
    token_type = result.get("token_type", "Bearer")
    expires_in = result.get("expires_in", 0)
    
    # Test the token
    token_works = test_token(base_url, access_token)
    
    # Output results
    print("\n" + "=" * 60)
    print("   TOKEN GENERATED SUCCESSFULLY! ✅")
    print("=" * 60)
    
    print(f"\n📊 Token Details:")
    print(f"   • Type: {token_type}")
    print(f"   • Expires in: {calculate_expiry(expires_in)}")
    print(f"   • Token Length: {len(access_token)} characters")
    
    print("\n" + "-" * 60)
    print("📋 Copy this to AZ Server Config → GraphQL Token:")
    print("-" * 60)
    print(f"\nBearer {access_token}")
    print()
    print("-" * 60)
    
    print("\n📝 AZ Server Config Settings:")
    print(f"   GraphQL URL:   {base_url}/admin/api/api/gql")
    print(f"   GraphQL Token: Bearer {access_token[:50]}...")
    print(f"   Verify SSL:    ❌ (unchecked for self-signed certs)")
    
    # Save to file option
    save = input("\n💾 Save token to file? (y/N): ").strip().lower()
    if save == 'y':
        filename = "freepbx_token.txt"
        with open(filename, 'w') as f:
            f.write(f"# FreePBX GraphQL Token\n")
            f.write(f"# Generated for: {base_url}\n")
            f.write(f"# Expires in: {calculate_expiry(expires_in)}\n")
            f.write(f"# Client ID: {client_id}\n")
            f.write(f"\n")
            f.write(f"Bearer {access_token}\n")
        print(f"   ✅ Saved to: {filename}")
    
    print("\n✨ Done! Use this token in your AZ Server Config.")
    print()


if __name__ == "__main__":
    main()
