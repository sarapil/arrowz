"""
Arrowz Engine - Client Management Routes

Endpoints for listing, blocking, unblocking, and disconnecting
connected network clients.
"""

import logging

from fastapi import APIRouter, Depends

from arrowz_engine.auth import verify_auth
from arrowz_engine.managers.client_manager import ClientManager
from arrowz_engine.models import ClientAction, ClientActionType, StatusResponse

logger = logging.getLogger("arrowz_engine.routes.clients")

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])

_client_mgr = ClientManager()


@router.get("", response_model=StatusResponse)
async def list_connected_clients(auth: bool = Depends(verify_auth)):
    """
    List all currently connected clients.

    Merges data from ARP table, DHCP leases, and hostapd station list
    to build a comprehensive view of connected devices.
    """
    try:
        clients = _client_mgr.get_connected()
        return StatusResponse(
            success=True,
            message=f"{len(clients)} client(s) found.",
            data={"clients": clients},
        )
    except Exception as exc:
        logger.error("Failed to list clients: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.post("/block", response_model=StatusResponse)
async def block_client(
    action: ClientAction,
    auth: bool = Depends(verify_auth),
):
    """
    Block a client by MAC address.

    Adds the MAC to the firewall block list and optionally disconnects
    the client if currently connected.
    """
    try:
        result = _client_mgr.block(action.mac_address)
        return StatusResponse(
            success=True,
            message=f"Client {action.mac_address} blocked.",
            data=result,
        )
    except Exception as exc:
        logger.error("Failed to block client %s: %s", action.mac_address, exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.post("/unblock", response_model=StatusResponse)
async def unblock_client(
    action: ClientAction,
    auth: bool = Depends(verify_auth),
):
    """
    Unblock a previously blocked client by MAC address.

    Removes the MAC from the firewall block list.
    """
    try:
        result = _client_mgr.unblock(action.mac_address)
        return StatusResponse(
            success=True,
            message=f"Client {action.mac_address} unblocked.",
            data=result,
        )
    except Exception as exc:
        logger.error("Failed to unblock client %s: %s", action.mac_address, exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.post("/disconnect", response_model=StatusResponse)
async def disconnect_client(
    action: ClientAction,
    auth: bool = Depends(verify_auth),
):
    """
    Forcefully disconnect a client by MAC address.

    Sends a deauthentication frame via hostapd and/or clears ARP entry.
    """
    try:
        result = _client_mgr.disconnect(action.mac_address)
        return StatusResponse(
            success=True,
            message=f"Client {action.mac_address} disconnected.",
            data=result,
        )
    except Exception as exc:
        logger.error(
            "Failed to disconnect client %s: %s", action.mac_address, exc, exc_info=True
        )
        return StatusResponse(success=False, message=str(exc))
