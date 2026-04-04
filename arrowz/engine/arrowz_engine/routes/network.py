# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz Engine - Network Information Routes

Provides read-only endpoints for querying network state: interfaces,
DHCP leases, ARP table, and routing table.
"""

import logging

from fastapi import APIRouter, Depends

from arrowz_engine.auth import verify_auth
from arrowz_engine.managers.network_manager import NetworkManager
from arrowz_engine.models import StatusResponse

logger = logging.getLogger("arrowz_engine.routes.network")

router = APIRouter(prefix="/api/v1/network", tags=["network"])

_network_mgr = NetworkManager()


@router.get("/interfaces", response_model=StatusResponse)
async def list_interfaces(auth: bool = Depends(verify_auth)):
    """
    List all network interfaces with their current status.

    Returns interface name, state, MAC address, IP addresses,
    and traffic counters.
    """
    try:
        interfaces = _network_mgr.get_interfaces()
        return StatusResponse(
            success=True,
            message=f"{len(interfaces)} interface(s) found.",
            data={"interfaces": interfaces},
        )
    except Exception as exc:
        logger.error("Failed to list interfaces: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.get("/dhcp/leases", response_model=StatusResponse)
async def get_dhcp_leases(auth: bool = Depends(verify_auth)):
    """
    Return current DHCP leases from dnsmasq.

    Parses /var/lib/misc/dnsmasq.leases or the configured lease file.
    """
    try:
        leases = _network_mgr.get_dhcp_leases()
        return StatusResponse(
            success=True,
            message=f"{len(leases)} lease(s) found.",
            data={"leases": leases},
        )
    except Exception as exc:
        logger.error("Failed to get DHCP leases: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.get("/arp", response_model=StatusResponse)
async def get_arp_table(auth: bool = Depends(verify_auth)):
    """
    Return the current ARP table.

    Parses /proc/net/arp for IP-to-MAC mappings.
    """
    try:
        entries = _network_mgr.get_arp_table()
        return StatusResponse(
            success=True,
            message=f"{len(entries)} ARP entry(ies) found.",
            data={"arp_table": entries},
        )
    except Exception as exc:
        logger.error("Failed to get ARP table: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.get("/routes", response_model=StatusResponse)
async def get_routing_table(auth: bool = Depends(verify_auth)):
    """
    Return the current routing table.

    Parses output of `ip route show`.
    """
    try:
        routes = _network_mgr.get_routing_table()
        return StatusResponse(
            success=True,
            message=f"{len(routes)} route(s) found.",
            data={"routes": routes},
        )
    except Exception as exc:
        logger.error("Failed to get routing table: %s", exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))
