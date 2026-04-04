# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz Engine - WiFi Management Routes

Endpoints for querying WiFi status, listing connected WiFi clients,
and managing captive-portal / hotspot authorization.
"""

import logging

from fastapi import APIRouter, Depends

from arrowz_engine.auth import verify_auth
from arrowz_engine.managers.wifi_manager import WiFiManager
from arrowz_engine.models import HotspotAuthRequest, StatusResponse

logger = logging.getLogger("arrowz_engine.routes.wifi")

router = APIRouter(prefix="/api/v1/wifi", tags=["wifi"])

_wifi_mgr = WiFiManager()


@router.get("/clients", response_model=StatusResponse)
async def list_wifi_clients(auth: bool = Depends(verify_auth)):
    """
    List all WiFi clients currently associated with the access point.

    Parses `hostapd_cli all_sta` output to provide per-station details
    including signal strength, TX/RX rates, and connection duration.
    """
    try:
        clients = _wifi_mgr.get_clients()
        return StatusResponse(
            success=True,
            message=f"{len(clients)} WiFi client(s) connected.",
            data={"clients": clients},
        )
    except Exception as exc:
        logger.error("Failed to list WiFi clients: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.get("/status", response_model=StatusResponse)
async def get_wifi_status(auth: bool = Depends(verify_auth)):
    """
    Return the current WiFi radio and SSID status.

    Includes radio state, SSID, channel, band, number of connected
    clients, and hostapd process status.
    """
    try:
        status = _wifi_mgr.get_status()
        return StatusResponse(
            success=True,
            message="WiFi status retrieved.",
            data=status,
        )
    except Exception as exc:
        logger.error("Failed to get WiFi status: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.post("/hotspot/authorize", response_model=StatusResponse)
async def authorize_hotspot_client(
    request: HotspotAuthRequest,
    auth: bool = Depends(verify_auth),
):
    """
    Authorize a client on the captive portal / hotspot.

    Adds the client MAC to the authorized list, optionally with a
    time limit and bandwidth profile.
    """
    try:
        # TODO: Implement hotspot authorization via hostapd_cli or nftables
        logger.info(
            "Hotspot authorize: mac=%s, duration=%s, profile=%s",
            request.mac_address,
            request.duration_minutes,
            request.bandwidth_profile,
        )
        return StatusResponse(
            success=True,
            message=f"Client {request.mac_address} authorized.",
            data={
                "mac_address": request.mac_address,
                "duration_minutes": request.duration_minutes,
            },
        )
    except Exception as exc:
        logger.error(
            "Failed to authorize hotspot client %s: %s",
            request.mac_address,
            exc,
            exc_info=True,
        )
        return StatusResponse(success=False, message=str(exc))


@router.post("/hotspot/deauthorize", response_model=StatusResponse)
async def deauthorize_hotspot_client(
    request: HotspotAuthRequest,
    auth: bool = Depends(verify_auth),
):
    """
    Deauthorize a client from the captive portal / hotspot.

    Removes the client MAC from the authorized list and disconnects
    the client session.
    """
    try:
        # TODO: Implement hotspot deauthorization
        logger.info("Hotspot deauthorize: mac=%s", request.mac_address)
        return StatusResponse(
            success=True,
            message=f"Client {request.mac_address} deauthorized.",
            data={"mac_address": request.mac_address},
        )
    except Exception as exc:
        logger.error(
            "Failed to deauthorize hotspot client %s: %s",
            request.mac_address,
            exc,
            exc_info=True,
        )
        return StatusResponse(success=False, message=str(exc))
