"""
Arrowz Engine - Health & Telemetry Routes

Provides endpoints for monitoring engine health, collecting system
telemetry, and querying service statuses.
"""

import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from arrowz_engine.auth import verify_auth
from arrowz_engine.collectors.telemetry import TelemetryCollector
from arrowz_engine.models import HealthResponse, StatusResponse, TelemetryResponse

logger = logging.getLogger("arrowz_engine.routes.health")

router = APIRouter(prefix="/api/v1", tags=["health"])

# Track startup time for uptime calculation
_start_time = time.monotonic()

# Singleton collector instance
_telemetry_collector = TelemetryCollector()


@router.get("/health", response_model=HealthResponse)
async def get_health(auth: bool = Depends(verify_auth)):
    """
    Return the current health status of the Arrowz Engine.

    Includes basic system info, uptime, and status of managed services.
    """
    import socket

    uptime = time.monotonic() - _start_time

    # TODO: Check actual service statuses (hostapd, dnsmasq, nftables, etc.)
    services = {
        "engine": "running",
        "nftables": "unknown",
        "hostapd": "unknown",
        "dnsmasq": "unknown",
        "wireguard": "unknown",
    }

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=round(uptime, 2),
        hostname=socket.gethostname(),
        box_id=None,  # TODO: Load from config
        services=services,
    )


@router.get("/telemetry", response_model=TelemetryResponse)
async def get_telemetry(auth: bool = Depends(verify_auth)):
    """
    Return a snapshot of system telemetry data.

    Includes CPU, memory, disk, network interface statistics, and
    system temperature where available.
    """
    data = await _telemetry_collector.collect()
    return data


@router.get("/status", response_model=StatusResponse)
async def get_status(auth: bool = Depends(verify_auth)):
    """
    Return a summary of all managed service statuses.

    Queries systemd / process status for each managed service.
    """
    # TODO: Implement actual service status checks
    service_statuses = {
        "nftables": "unknown",
        "hostapd": "unknown",
        "dnsmasq": "unknown",
        "wireguard": "unknown",
        "tc": "unknown",
    }

    return StatusResponse(
        success=True,
        message="Service statuses retrieved.",
        data={"services": service_statuses},
    )
