"""
Arrowz Engine - Authentication Middleware

Provides Bearer token and HMAC-SHA256 signature verification for
securing the API against unauthorized access. Configuration is
loaded from /etc/arrowz/engine.json.
"""

import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger("arrowz_engine.auth")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ENGINE_CONFIG_PATH = Path("/etc/arrowz/engine.json")

_config_cache: Optional[dict] = None


def _load_config() -> dict:
    """Load engine configuration from disk (cached after first read)."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if not ENGINE_CONFIG_PATH.exists():
        logger.warning(
            "Engine config not found at %s – using environment fallback.",
            ENGINE_CONFIG_PATH,
        )
        _config_cache = {
            "api_token": os.getenv("ARROWZ_API_TOKEN", ""),
            "hmac_secret": os.getenv("ARROWZ_HMAC_SECRET", ""),
        }
        return _config_cache

    try:
        with open(ENGINE_CONFIG_PATH, "r") as f:
            _config_cache = json.load(f)
        return _config_cache
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load engine config: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Engine configuration error.",
        )


def reload_config() -> dict:
    """Force-reload engine configuration (e.g. after config push)."""
    global _config_cache
    _config_cache = None
    return _load_config()


# ---------------------------------------------------------------------------
# Bearer Token Verification
# ---------------------------------------------------------------------------
_bearer_scheme = HTTPBearer(auto_error=False)


def _verify_bearer_token(token: str) -> bool:
    """Compare the provided token against the configured API token."""
    cfg = _load_config()
    expected = cfg.get("api_token", "")
    if not expected:
        logger.warning("No api_token configured – rejecting all bearer tokens.")
        return False
    return hmac.compare_digest(token, expected)


# ---------------------------------------------------------------------------
# HMAC-SHA256 Signature Verification
# ---------------------------------------------------------------------------

def _verify_hmac_signature(body: bytes, signature: str) -> bool:
    """
    Verify the HMAC-SHA256 signature of the request body.

    The Frappe Interface Layer signs the raw request body using the
    shared secret and sends the hex-encoded digest in the
    X-Arrowz-Signature header.
    """
    cfg = _load_config()
    secret = cfg.get("hmac_secret", "")
    if not secret:
        logger.warning("No hmac_secret configured – HMAC verification skipped.")
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


# ---------------------------------------------------------------------------
# FastAPI Dependency
# ---------------------------------------------------------------------------

async def verify_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> bool:
    """
    FastAPI dependency that verifies incoming requests.

    Checks (in order):
    1. Bearer token in Authorization header
    2. HMAC-SHA256 signature in X-Arrowz-Signature header

    At least one method must succeed.
    """
    # --- Bearer token check ---
    if credentials and credentials.credentials:
        if _verify_bearer_token(credentials.credentials):
            return True
        logger.debug("Bearer token verification failed.")

    # --- HMAC signature check ---
    signature = request.headers.get("X-Arrowz-Signature")
    if signature:
        body = await request.body()
        if _verify_hmac_signature(body, signature):
            return True
        logger.debug("HMAC signature verification failed.")

    # --- No valid auth ---
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
