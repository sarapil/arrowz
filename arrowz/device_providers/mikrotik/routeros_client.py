# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
RouterOSClient — Low-level RouterOS API wrapper around librouteros.

Handles:
  - Connection management (plain + SSL)
  - Credential retrieval from Arrowz Box doc
  - CRUD primitives: print, add, set, remove, command
  - Retry logic with exponential back-off
  - Detailed error wrapping into ProviderError subclasses

This is the only file that imports `librouteros` directly; all higher-level
code works through this wrapper.
"""

from __future__ import annotations

import ssl
import time
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

import frappe

try:
    import librouteros
    from librouteros import connect as ros_connect
    from librouteros.exceptions import (
        ConnectionClosed,
        FatalError,
        TrapError,
    )
    HAS_LIBROUTEROS = True
except ImportError:
    HAS_LIBROUTEROS = False
    # Provide stubs so the module can be imported even without the library
    class TrapError(Exception):  # type: ignore[no-redef]
        pass
    class FatalError(Exception):  # type: ignore[no-redef]
        pass
    class ConnectionClosed(Exception):  # type: ignore[no-redef]
        pass

from ..base_provider import (
    AuthenticationError,
    CommandError,
    ConnectionError,
    ProviderError,
)

# Default RouterOS API ports
DEFAULT_API_PORT = 8728
DEFAULT_API_SSL_PORT = 8729

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # seconds (multiplied by attempt number)


class RouterOSClient:
    """Low-level RouterOS API client.

    Usage:
        client = RouterOSClient(host="192.168.88.1", username="admin", password="")
        client.connect()

        interfaces = client.print("/interface")
        client.add("/ip/address", address="192.168.1.1/24", interface="ether2")
        client.set("/ip/address", id="*1", address="192.168.1.2/24")
        client.remove("/ip/address", id="*1")

        client.disconnect()
    """

    def __init__(
        self,
        host: str,
        username: str = "admin",
        password: str = "",
        port: int = 0,
        use_ssl: bool = False,
        verify_ssl: bool = False,
        timeout: float = 15.0,
    ):
        self.host = host
        self.username = username
        self.password = password
        self.port = port or (DEFAULT_API_SSL_PORT if use_ssl else DEFAULT_API_PORT)
        self.use_ssl = use_ssl
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self._api = None
        self._connected = False

    @classmethod
    def from_box_doc(cls, box_doc) -> "RouterOSClient":
        """Create a client from an Arrowz Box document.

        Reads MikroTik connection fields from the doc:
          - box_ip (required)
          - mikrotik_api_port (default 8728/8729)
          - mikrotik_username (default "admin")
          - mikrotik_password (Password field)
          - mikrotik_use_ssl (checkbox)
          - verify_ssl (checkbox)
        """
        host = box_doc.box_ip
        if not host:
            raise ConnectionError("Arrowz Box has no IP address configured")

        username = getattr(box_doc, "mikrotik_username", None) or "admin"
        password = getattr(box_doc, "mikrotik_password", None) or ""
        # Frappe Password fields need get_password()
        if hasattr(box_doc, "get_password") and box_doc.meta.get_field("mikrotik_password"):
            try:
                password = box_doc.get_password("mikrotik_password") or ""
            except Exception:
                password = password or ""

        use_ssl = bool(getattr(box_doc, "mikrotik_use_ssl", False))
        port = int(getattr(box_doc, "mikrotik_api_port", 0) or 0)
        verify = bool(getattr(box_doc, "verify_ssl", False))

        return cls(
            host=host,
            username=username,
            password=password,
            port=port,
            use_ssl=use_ssl,
            verify_ssl=verify,
        )

    # ───────────────────── Connection ─────────────────────

    def connect(self) -> None:
        """Establish API connection to the RouterOS device."""
        if not HAS_LIBROUTEROS:
            raise ConnectionError(
                "librouteros package is not installed. "
                "Install it with: pip install librouteros"
            )

        if self._connected and self._api:
            return

        kwargs: Dict[str, Any] = {
            "host": self.host,
            "username": self.username,
            "password": self.password,
            "port": self.port,
            "timeout": self.timeout,
        }

        if self.use_ssl:
            ctx = ssl.create_default_context()
            if not self.verify_ssl:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            kwargs["ssl_wrapper"] = ctx.wrap_socket

        try:
            self._api = ros_connect(**kwargs)
            self._connected = True
        except (OSError, TimeoutError) as e:
            raise ConnectionError(
                f"Cannot connect to {self.host}:{self.port} — {e}"
            ) from e
        except FatalError as e:
            msg = str(e)
            if "invalid user" in msg.lower() or "cannot log in" in msg.lower():
                raise AuthenticationError(
                    f"Authentication failed for {self.username}@{self.host}: {e}"
                ) from e
            raise ConnectionError(f"RouterOS connection error: {e}") from e
        except Exception as e:
            raise ConnectionError(
                f"Unexpected error connecting to {self.host}:{self.port}: {e}"
            ) from e

    def disconnect(self) -> None:
        """Close the API connection."""
        if self._api:
            try:
                self._api.close()
            except Exception:
                pass
        self._api = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._api is not None

    def _ensure_connected(self):
        if not self.is_connected:
            raise ConnectionError("Not connected to RouterOS device. Call connect() first.")

    # ───────────────────── CRUD Primitives ─────────────────────

    def _path(self, *path_parts: str):
        """Get an API path object for the given resource path.

        Examples:
            self._path("ip", "address")  → api.path("ip", "address")
            self._path("interface")      → api.path("interface")
        """
        self._ensure_connected()
        return self._api.path(*path_parts)

    def print(
        self,
        *path: str,
        where: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, str]]:
        """Fetch all entries at the given path (RouterOS /print).

        Args:
            *path: API path parts, e.g. ("ip", "address") or ("interface",)
            where: Optional filter dict e.g. {"interface": "ether1"}

        Returns:
            List of dicts with string keys/values
        """
        return self._retry(lambda: self._do_print(*path, where=where))

    def _do_print(self, *path: str, where: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
        p = self._path(*path)
        if where:
            # librouteros uses the Key class for filtering
            from librouteros.query import Key
            conditions = []
            for key, value in where.items():
                conditions.append(Key(key) == value)

            if conditions:
                query = p.select(*[Key(k) for k in []])  # Select all
                for cond in conditions:
                    query = query.where(cond)
                return list(query)

        return list(p)

    def add(self, *path: str, **kwargs) -> str:
        """Add a new entry (RouterOS /add).

        Args:
            *path: API path parts
            **kwargs: Fields for the new entry

        Returns:
            The new entry's .id
        """
        def _do():
            p = self._path(*path)
            # librouteros add() returns the .id of the new entry
            result = p.add(**self._clean_kwargs(kwargs))
            return result

        return self._retry(_do)

    def set(self, *path: str, id: str = "", **kwargs) -> None:
        """Update an existing entry (RouterOS /set).

        Args:
            *path: API path parts
            id: The .id of the entry to update
            **kwargs: Fields to update
        """
        def _do():
            p = self._path(*path)
            update_args = self._clean_kwargs(kwargs)
            update_args[".id"] = id
            p.update(**update_args)

        self._retry(_do)

    def remove(self, *path: str, id: str = "") -> None:
        """Remove an entry (RouterOS /remove).

        Args:
            *path: API path parts
            id: The .id of the entry to remove
        """
        def _do():
            p = self._path(*path)
            p.remove(id)

        self._retry(_do)

    def command(self, *path: str, **kwargs) -> List[Dict[str, str]]:
        """Execute a RouterOS command (e.g. /system/reboot, /export).

        Args:
            *path: Command path parts
            **kwargs: Command parameters

        Returns:
            Command output as list of dicts
        """
        def _do():
            self._ensure_connected()
            # For commands, we need to use the raw API
            cmd_path = "/" + "/".join(path)
            result = list(self._api.rawCmd(cmd_path, **self._clean_kwargs(kwargs)))
            return result

        return self._retry(_do)

    # ───────────────────── Helpers ─────────────────────

    def _clean_kwargs(self, kwargs: dict) -> dict:
        """Clean kwargs for RouterOS API.

        - Remove None values
        - Convert bool → "yes"/"no"
        - Convert int → str
        - Convert Python-style keys to RouterOS keys (underscore → dash)
        """
        result = {}
        for key, value in kwargs.items():
            if value is None:
                continue
            # Convert underscore to dash for RouterOS (e.g. max_limit → max-limit)
            # But preserve .id and other dot-prefixed keys
            ros_key = key if key.startswith(".") else key.replace("_", "-")

            if isinstance(value, bool):
                result[ros_key] = "yes" if value else "no"
            elif isinstance(value, (int, float)):
                result[ros_key] = str(value)
            else:
                result[ros_key] = str(value)
        return result

    def _retry(self, fn: Callable, max_retries: int = MAX_RETRIES) -> Any:
        """Execute a function with retry logic for transient errors.

        Retries on:
          - ConnectionClosed (reconnects automatically)
          - TimeoutError
          - OSError (network issues)

        Does NOT retry on:
          - TrapError (RouterOS command error — user error)
          - AuthenticationError
        """
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                return fn()
            except TrapError as e:
                # RouterOS-level error (e.g. "no such item", "already have")
                # Don't retry — it's a logic error
                raise CommandError(
                    str(e),
                    command=getattr(fn, "__name__", "unknown"),
                    details={"trap_message": str(e)},
                ) from e
            except (ConnectionClosed, TimeoutError, OSError) as e:
                last_error = e
                if attempt < max_retries:
                    time.sleep(RETRY_BACKOFF * attempt)
                    # Try to reconnect
                    try:
                        self.disconnect()
                        self.connect()
                    except Exception:
                        pass
                continue
            except (AuthenticationError, CommandError):
                raise
            except Exception as e:
                raise CommandError(
                    f"Unexpected RouterOS error: {e}",
                    details={"error_type": type(e).__name__},
                ) from e

        raise ConnectionError(
            f"Failed after {max_retries} retries: {last_error}"
        )

    # ───────────────────── Convenience ─────────────────────

    def get_identity(self) -> str:
        """Get the device hostname/identity."""
        result = self.print("system", "identity")
        if result:
            return result[0].get("name", "")
        return ""

    def get_resource(self) -> Dict[str, str]:
        """Get system resource info (CPU, RAM, etc.)."""
        result = self.print("system", "resource")
        return result[0] if result else {}

    def get_routerboard(self) -> Dict[str, str]:
        """Get RouterBOARD hardware info."""
        result = self.print("system", "routerboard")
        return result[0] if result else {}

    def export_config(self) -> str:
        """Get a full text export of the device configuration.

        Note: This runs /export and returns the config as a string.
        May not be available via API on all RouterOS versions.
        """
        try:
            result = self.command("export")
            if result:
                return result[0].get("ret", "")
        except Exception:
            pass
        return ""
