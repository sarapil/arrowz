# Copyright (c) 2026, Arrowz Team and contributors
# For license information, please see license.txt

"""
ProviderFactory — Creates the correct device provider based on device_type.

Routes Arrowz Box documents to their matching provider implementation:
  - "Linux Box"  → LinuxProvider  (wraps existing BoxConnector REST API)
  - "MikroTik"   → MikroTikProvider (RouterOS API via librouteros)

Usage:
    from arrowz.device_providers import ProviderFactory

    # From a box document
    provider = ProviderFactory.get_provider(box_doc=box_doc)

    # From a box name (fetches doc automatically)
    provider = ProviderFactory.get_provider(box_name="router-1")

    # As a context manager (auto-connects and disconnects)
    with ProviderFactory.connect(box_name="router-1") as provider:
        info = provider.get_system_info()
"""

from __future__ import annotations

import importlib
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Dict, Optional, Type

import frappe

if TYPE_CHECKING:
    from .base_provider import BaseProvider


# Registry of provider type identifiers → module paths
# Lazy-loaded to avoid circular imports and unnecessary imports
_PROVIDER_REGISTRY: Dict[str, str] = {
    "Linux Box": "arrowz.device_providers.linux.linux_provider.LinuxProvider",
    "MikroTik": "arrowz.device_providers.mikrotik.mikrotik_provider.MikroTikProvider",
}

# Cache of already-imported provider classes
_provider_classes: Dict[str, Type["BaseProvider"]] = {}


class ProviderFactory:
    """Factory for creating device provider instances."""

    @staticmethod
    def register(device_type: str, provider_class_path: str):
        """Register a new provider type.

        Args:
            device_type: The device_type Select value in Arrowz Box
            provider_class_path: Full dotted path to the provider class
        """
        _PROVIDER_REGISTRY[device_type] = provider_class_path
        _provider_classes.pop(device_type, None)  # Clear cache

    @staticmethod
    def get_provider_class(device_type: str) -> Type["BaseProvider"]:
        """Get the provider class for a device type.

        Args:
            device_type: The device type string (e.g. "MikroTik", "Linux Box")

        Returns:
            The provider class (not instantiated)

        Raises:
            ValueError: If device_type is not registered
        """
        if device_type not in _PROVIDER_REGISTRY:
            available = ", ".join(sorted(_PROVIDER_REGISTRY.keys()))
            frappe.throw(
                f"Unknown device type: {device_type}. "
                f"Available providers: {available}",
                title="Provider Not Found",
            )

        if device_type not in _provider_classes:
            class_path = _PROVIDER_REGISTRY[device_type]
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            _provider_classes[device_type] = getattr(module, class_name)

        return _provider_classes[device_type]

    @staticmethod
    def get_provider(
        box_doc: Optional[Any] = None,
        box_name: Optional[str] = None,
    ) -> "BaseProvider":
        """Create a provider instance for an Arrowz Box.

        Args:
            box_doc: An Arrowz Box document (already fetched)
            box_name: Name of an Arrowz Box document (will be fetched)

        Returns:
            An initialized (but not yet connected) provider instance

        Raises:
            ValueError: If neither box_doc nor box_name is provided
        """
        if box_doc is None and box_name is None:
            frappe.throw("Either box_doc or box_name must be provided")

        if box_doc is None:
            box_doc = frappe.get_doc("Arrowz Box", box_name)

        device_type = getattr(box_doc, "device_type", None) or "Linux Box"
        provider_class = ProviderFactory.get_provider_class(device_type)

        return provider_class(box_doc)

    @staticmethod
    @contextmanager
    def connect(
        box_doc: Optional[Any] = None,
        box_name: Optional[str] = None,
    ):
        """Create and connect a provider as a context manager.

        Automatically connects on entry and disconnects on exit.

        Usage:
            with ProviderFactory.connect(box_name="router-1") as provider:
                info = provider.get_system_info()
        """
        provider = ProviderFactory.get_provider(box_doc=box_doc, box_name=box_name)

        try:
            provider.connect()
            yield provider
        finally:
            try:
                provider.disconnect()
            except Exception:
                pass  # Don't raise on cleanup

    @staticmethod
    def list_providers() -> Dict[str, dict]:
        """List all registered providers with their capabilities.

        Returns:
            Dict mapping device_type → provider info dict
        """
        result = {}
        for device_type, class_path in _PROVIDER_REGISTRY.items():
            try:
                cls = ProviderFactory.get_provider_class(device_type)
                result[device_type] = {
                    "class": class_path,
                    "type": cls.PROVIDER_TYPE,
                    "version": cls.PROVIDER_VERSION,
                    "features": list(cls.SUPPORTED_FEATURES),
                }
            except Exception as e:
                result[device_type] = {
                    "class": class_path,
                    "error": str(e),
                }
        return result

    @staticmethod
    def test_connection(
        box_doc: Optional[Any] = None,
        box_name: Optional[str] = None,
    ) -> dict:
        """Test connection to a device through its provider.

        Returns:
            dict with 'success', 'message', 'system_info' keys
        """
        from .error_tracker import ErrorTracker

        if box_doc is None and box_name:
            box_doc = frappe.get_doc("Arrowz Box", box_name)

        box_name = box_doc.name if box_doc else "unknown"
        device_type = getattr(box_doc, "device_type", None) or "Linux Box"
        tracker = ErrorTracker.instance()

        with tracker.trace("test_connection", box_name=box_name, provider_type=device_type) as t:
            with t.span("provider", "create"):
                provider = ProviderFactory.get_provider(box_doc=box_doc)

            with t.span("transport", "connect"):
                provider.connect()

            try:
                with t.span("command", "test_connection"):
                    result = provider.test_connection()

                with t.span("command", "get_system_info"):
                    sys_info = provider.get_system_info()

                return {
                    "success": result,
                    "message": "Connection successful",
                    "system_info": sys_info,
                    "trace_id": t.trace_id,
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": str(e),
                    "system_info": {},
                    "trace_id": t.trace_id,
                }
            finally:
                try:
                    provider.disconnect()
                except Exception:
                    pass
