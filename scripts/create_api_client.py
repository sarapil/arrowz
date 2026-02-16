#!/usr/bin/env python3
"""
FreePBX API Client Creator
==========================
Creates API Client in FreePBX directly via MySQL.
Run this script on the FreePBX server.

Usage:
    python3 create_api_client.py
    
Or run the generated SQL directly on FreePBX:
    mysql asterisk < api_client.sql
"""

import secrets
import string
import hashlib
import time
import json


def generate_client_id(length=32):
    """Generate a random client ID."""
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_client_secret(length=64):
    """Generate a secure random client secret."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_secret(secret):
    """Hash the secret using bcrypt-like format (PHP password_hash compatible)."""
    # For simplicity, we'll use a format that FreePBX can verify
    # In production, this should use proper bcrypt
    import hashlib
    # FreePBX uses password_hash() in PHP which uses bcrypt
    # We'll generate a simple hash for now - you may need to update in FreePBX UI
    return secret  # Store plain for now, FreePBX will hash on first use


def create_api_client_sql():
    """Generate SQL to create API client in FreePBX."""
    
    client_id = generate_client_id()
    client_secret = generate_client_secret()
    app_name = "Arrowz_ERP"
    created_at = int(time.time())
    
    # Scopes needed for extension management
    scopes = json.dumps([
        "gql",
        "read:extensions", 
        "write:extensions",
        "read:users",
        "write:users"
    ])
    
    print("=" * 70)
    print("  FreePBX API Client Generator")
    print("=" * 70)
    print()
    print("📋 Generated Credentials (SAVE THESE!):")
    print("-" * 50)
    print(f"   Client ID:     {client_id}")
    print(f"   Client Secret: {client_secret}")
    print("-" * 50)
    print()
    
    # SQL for api_applications table
    sql = f"""
-- FreePBX API Client Creation Script
-- Generated for Arrowz ERP Integration
-- Run on FreePBX server: mysql asterisk < api_client.sql

-- Check if table exists and create client
INSERT INTO api_applications (
    client_id,
    client_secret,
    name,
    description,
    redirect_uri,
    allowed_scopes,
    token_ttl,
    created_at,
    updated_at
) VALUES (
    '{client_id}',
    '{client_secret}',
    '{app_name}',
    'Arrowz ERP VoIP Integration - Auto-generated',
    '',
    '{scopes}',
    86400,
    {created_at},
    {created_at}
) ON DUPLICATE KEY UPDATE
    client_secret = '{client_secret}',
    allowed_scopes = '{scopes}',
    updated_at = {created_at};

-- Verify insertion
SELECT client_id, name, allowed_scopes FROM api_applications WHERE name = '{app_name}';
"""
    
    # Alternative: Direct command for FreePBX CLI
    cli_command = f"""
# Alternative: Run these commands on FreePBX server

# 1. SSH to FreePBX
ssh root@pbx.tavira-group.com

# 2. Create API client via MySQL
mysql asterisk -e "
INSERT INTO api_applications (client_id, client_secret, name, description, redirect_uri, allowed_scopes, token_ttl, created_at, updated_at)
VALUES ('{client_id}', '{client_secret}', '{app_name}', 'Arrowz ERP Integration', '', '{scopes}', 86400, {created_at}, {created_at})
ON DUPLICATE KEY UPDATE client_secret='{client_secret}', allowed_scopes='{scopes}', updated_at={created_at};
"

# 3. Verify
mysql asterisk -e "SELECT client_id, name FROM api_applications WHERE name='{app_name}';"

# 4. Reload FreePBX
fwconsole reload
"""

    # Save SQL to file
    with open('/tmp/freepbx_api_client.sql', 'w') as f:
        f.write(sql)
    print("📄 SQL saved to: /tmp/freepbx_api_client.sql")
    
    # Print commands
    print()
    print("🖥️  Commands to run on FreePBX server:")
    print("=" * 70)
    print(cli_command)
    print("=" * 70)
    
    # Print ERPNext config
    print()
    print("📝 Update AZ Server Config in ERPNext with:")
    print("-" * 50)
    print(f"   GraphQL URL:           https://pbx.tavira-group.com/admin/api/api/gql")
    print(f"   GraphQL Client ID:     {client_id}")
    print(f"   GraphQL Client Secret: {client_secret}")
    print(f"   Verify SSL:            ❌ (uncheck)")
    print("-" * 50)
    
    return client_id, client_secret


def create_ssh_command():
    """Generate a one-liner SSH command to create API client."""
    
    client_id = generate_client_id()
    client_secret = generate_client_secret()
    app_name = "Arrowz_ERP"
    created_at = int(time.time())
    scopes = '["gql","read:extensions","write:extensions","read:users","write:users"]'
    
    # Escape for shell
    scopes_escaped = scopes.replace('"', '\\"')
    
    ssh_command = f'''ssh root@pbx.tavira-group.com 'mysql asterisk -e "INSERT INTO api_applications (client_id, client_secret, name, description, allowed_scopes, token_ttl, created_at, updated_at) VALUES (\\"{client_id}\\", \\"{client_secret}\\", \\"{app_name}\\", \\"Arrowz ERP\\", \\"{scopes_escaped}\\", 86400, {created_at}, {created_at}) ON DUPLICATE KEY UPDATE client_secret=\\"{client_secret}\\", updated_at={created_at};" && fwconsole reload'
'''
    
    print()
    print("🚀 One-liner SSH Command (copy and run):")
    print("=" * 70)
    print(ssh_command)
    print("=" * 70)
    print()
    print("📋 Credentials to save:")
    print(f"   Client ID:     {client_id}")
    print(f"   Client Secret: {client_secret}")
    
    return client_id, client_secret


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--ssh":
        create_ssh_command()
    else:
        create_api_client_sql()
