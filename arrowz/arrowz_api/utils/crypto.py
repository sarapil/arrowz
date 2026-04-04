# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Cryptographic utilities for Arrowz API communication.

Handles HMAC-SHA256 signing, token generation, and verification
between the Frappe Interface Layer and Engine agents.
"""

import hashlib
import hmac
import secrets
import time

import frappe
from frappe import _


def generate_token(length: int = 48) -> str:
	"""Generate a cryptographically secure URL-safe token.

	Args:
		length: Number of random bytes (output is longer due to base64)

	Returns:
		URL-safe token string
	"""
	return secrets.token_urlsafe(length)


def generate_hmac_secret(length: int = 32) -> str:
	"""Generate a hex-encoded HMAC secret key.

	Args:
		length: Number of random bytes

	Returns:
		Hex-encoded secret string
	"""
	return secrets.token_hex(length)


def sign_request(secret: str, timestamp: str, payload: str) -> str:
	"""Create HMAC-SHA256 signature for a request.

	Args:
		secret: HMAC shared secret
		timestamp: Unix timestamp string
		payload: JSON body string

	Returns:
		Hex-encoded HMAC signature
	"""
	message = f"{timestamp}:{payload}"
	return hmac.new(
		secret.encode(),
		message.encode(),
		hashlib.sha256,
	).hexdigest()


def verify_signature(secret: str, timestamp: str, payload: str, signature: str) -> bool:
	"""Verify an HMAC-SHA256 signature.

	Also checks timestamp freshness (within 5 minutes).

	Args:
		secret: HMAC shared secret
		timestamp: Unix timestamp string from request
		payload: JSON body string
		signature: Hex-encoded signature to verify

	Returns:
		True if signature is valid and timestamp is fresh
	"""
	# Check timestamp freshness (5 minute window)
	try:
		request_time = int(timestamp)
		current_time = int(time.time())
		if abs(current_time - request_time) > 300:
			return False
	except (ValueError, TypeError):
		return False

	expected = sign_request(secret, timestamp, payload)
	return hmac.compare_digest(expected, signature)


def hash_config(config_dict: dict) -> str:
	"""Generate SHA256 hash of a configuration dict.

	Used to detect config changes and verify sync state.

	Args:
		config_dict: Configuration dictionary

	Returns:
		Hex-encoded SHA256 hash (first 16 chars)
	"""
	import json

	config_json = json.dumps(config_dict, sort_keys=True, default=str)
	return hashlib.sha256(config_json.encode()).hexdigest()[:16]


def encrypt_sensitive_field(value: str) -> str:
	"""Encrypt a sensitive field value for storage/transport.

	Uses Frappe's built-in encryption.

	Args:
		value: Plaintext value to encrypt

	Returns:
		Encrypted value string
	"""
	from cryptography.fernet import Fernet

	key = _get_encryption_key()
	f = Fernet(key)
	return f.encrypt(value.encode()).decode()


def decrypt_sensitive_field(encrypted_value: str) -> str:
	"""Decrypt a sensitive field value.

	Args:
		encrypted_value: Encrypted value string

	Returns:
		Decrypted plaintext string
	"""
	from cryptography.fernet import Fernet

	key = _get_encryption_key()
	f = Fernet(key)
	return f.decrypt(encrypted_value.encode()).decode()


def _get_encryption_key() -> bytes:
	"""Get or generate the Fernet encryption key from site config.

	Returns:
		Fernet-compatible base64 key
	"""
	import base64

	key = frappe.conf.get("arrowz_encryption_key")
	if not key:
		# Generate and store a new key
		key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
		frappe.conf.arrowz_encryption_key = key
		# Note: Caller should persist this to site_config.json

	return key.encode()
