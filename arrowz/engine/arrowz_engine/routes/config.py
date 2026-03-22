"""
Arrowz Engine - Configuration Routes

Receives configuration payloads from the Frappe Interface Layer and
delegates to the appropriate manager for each subsystem.
"""

import logging

from fastapi import APIRouter, Depends

from arrowz_engine.auth import verify_auth
from arrowz_engine.managers.bandwidth_manager import BandwidthManager
from arrowz_engine.managers.client_manager import ClientManager
from arrowz_engine.managers.firewall_manager import FirewallManager
from arrowz_engine.managers.network_manager import NetworkManager
from arrowz_engine.managers.vpn_manager import VPNManager
from arrowz_engine.managers.wifi_manager import WiFiManager
from arrowz_engine.models import (
    BandwidthConfig,
    ClientConfig,
    ConfigPayload,
    DNSConfig,
    FirewallConfig,
    NetworkConfig,
    StatusResponse,
    VPNConfig,
    WiFiConfig,
)

logger = logging.getLogger("arrowz_engine.routes.config")

router = APIRouter(prefix="/api/v1/config", tags=["config"])

# ---------------------------------------------------------------------------
# Manager singletons
# ---------------------------------------------------------------------------
_network_mgr = NetworkManager()
_firewall_mgr = FirewallManager()
_wifi_mgr = WiFiManager()
_bandwidth_mgr = BandwidthManager()
_client_mgr = ClientManager()
_vpn_mgr = VPNManager()


# ---------------------------------------------------------------------------
# Full Configuration
# ---------------------------------------------------------------------------

@router.post("/apply", response_model=StatusResponse)
async def apply_full_config(
    payload: ConfigPayload,
    auth: bool = Depends(verify_auth),
):
    """
    Apply a full configuration payload.

    Delegates each subsystem config to its respective manager in the
    correct order: network → firewall → bandwidth → wifi → clients → vpn → dns.
    """
    results = {}

    try:
        if payload.network:
            results["network"] = _network_mgr.apply_config(payload.network)
        if payload.firewall:
            results["firewall"] = _firewall_mgr.apply_config(payload.firewall)
        if payload.bandwidth:
            results["bandwidth"] = _bandwidth_mgr.apply_config(payload.bandwidth)
        if payload.wifi:
            results["wifi"] = _wifi_mgr.apply_config(payload.wifi)
        if payload.clients:
            results["clients"] = _client_mgr.apply_config(payload.clients)
        if payload.vpn:
            results["vpn"] = _vpn_mgr.apply_config(payload.vpn)
        if payload.dns:
            # TODO: Implement DNSManager
            results["dns"] = {"status": "not_implemented"}

        logger.info("Full configuration applied successfully.")
        return StatusResponse(
            success=True,
            message="Full configuration applied.",
            data=results,
        )
    except Exception as exc:
        logger.error("Failed to apply full configuration: %s", exc, exc_info=True)
        return StatusResponse(
            success=False,
            message=f"Configuration apply failed: {exc}",
            data=results,
        )


# ---------------------------------------------------------------------------
# Individual Subsystem Endpoints
# ---------------------------------------------------------------------------

@router.post("/network", response_model=StatusResponse)
async def apply_network_config(
    config: NetworkConfig,
    auth: bool = Depends(verify_auth),
):
    """Apply network interface and routing configuration."""
    try:
        result = _network_mgr.apply_config(config)
        return StatusResponse(success=True, message="Network config applied.", data=result)
    except Exception as exc:
        logger.error("Network config failed: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.post("/firewall", response_model=StatusResponse)
async def apply_firewall_config(
    config: FirewallConfig,
    auth: bool = Depends(verify_auth),
):
    """Apply firewall (nftables) configuration."""
    try:
        result = _firewall_mgr.apply_config(config)
        return StatusResponse(success=True, message="Firewall config applied.", data=result)
    except Exception as exc:
        logger.error("Firewall config failed: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.post("/wifi", response_model=StatusResponse)
async def apply_wifi_config(
    config: WiFiConfig,
    auth: bool = Depends(verify_auth),
):
    """Apply WiFi (hostapd) configuration."""
    try:
        result = _wifi_mgr.apply_config(config)
        return StatusResponse(success=True, message="WiFi config applied.", data=result)
    except Exception as exc:
        logger.error("WiFi config failed: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.post("/bandwidth", response_model=StatusResponse)
async def apply_bandwidth_config(
    config: BandwidthConfig,
    auth: bool = Depends(verify_auth),
):
    """Apply bandwidth shaping (tc) configuration."""
    try:
        result = _bandwidth_mgr.apply_config(config)
        return StatusResponse(success=True, message="Bandwidth config applied.", data=result)
    except Exception as exc:
        logger.error("Bandwidth config failed: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.post("/clients", response_model=StatusResponse)
async def apply_client_config(
    config: ClientConfig,
    auth: bool = Depends(verify_auth),
):
    """Apply client management configuration (reservations, blocks)."""
    try:
        result = _client_mgr.apply_config(config)
        return StatusResponse(success=True, message="Client config applied.", data=result)
    except Exception as exc:
        logger.error("Client config failed: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.post("/vpn", response_model=StatusResponse)
async def apply_vpn_config(
    config: VPNConfig,
    auth: bool = Depends(verify_auth),
):
    """Apply VPN (WireGuard) configuration."""
    try:
        result = _vpn_mgr.apply_config(config)
        return StatusResponse(success=True, message="VPN config applied.", data=result)
    except Exception as exc:
        logger.error("VPN config failed: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.post("/dns", response_model=StatusResponse)
async def apply_dns_config(
    config: DNSConfig,
    auth: bool = Depends(verify_auth),
):
    """Apply DNS (dnsmasq) configuration."""
    # TODO: Implement DNSManager and delegate
    logger.info("DNS config received (not yet implemented).")
    return StatusResponse(
        success=False,
        message="DNS manager not yet implemented.",
        data={"config_received": config.model_dump()},
    )
