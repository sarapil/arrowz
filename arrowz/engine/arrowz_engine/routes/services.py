# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz Engine - Service Management Routes

Endpoints for restarting and querying the status of managed system
services (hostapd, dnsmasq, nftables, wireguard, etc.).
"""

import logging

from fastapi import APIRouter, Depends

from arrowz_engine.auth import verify_auth
from arrowz_engine.models import StatusResponse
from arrowz_engine.utils.shell import run_command

logger = logging.getLogger("arrowz_engine.routes.services")

router = APIRouter(prefix="/api/v1/services", tags=["services"])

# Services that the engine is allowed to manage
ALLOWED_SERVICES = frozenset({
    "hostapd",
    "dnsmasq",
    "nftables",
    "wg-quick@wg0",
    "networking",
})


def _validate_service(service_name: str) -> str:
    """Validate that the service is in the allow-list."""
    if service_name not in ALLOWED_SERVICES:
        raise ValueError(
            f"Service '{service_name}' is not managed by Arrowz Engine. "
            f"Allowed: {', '.join(sorted(ALLOWED_SERVICES))}"
        )
    return service_name


@router.post("/{service_name}/restart", response_model=StatusResponse)
async def restart_service(
    service_name: str,
    auth: bool = Depends(verify_auth),
):
    """
    Restart a managed system service.

    Only services in the allow-list can be restarted for security.
    Uses `systemctl restart <service>`.
    """
    try:
        _validate_service(service_name)
        stdout, stderr, rc = run_command(f"systemctl restart {service_name}", timeout=30)

        if rc == 0:
            logger.info("Service '%s' restarted successfully.", service_name)
            return StatusResponse(
                success=True,
                message=f"Service '{service_name}' restarted.",
                data={"stdout": stdout, "stderr": stderr, "returncode": rc},
            )
        else:
            logger.warning(
                "Service '%s' restart returned code %d: %s", service_name, rc, stderr
            )
            return StatusResponse(
                success=False,
                message=f"Service '{service_name}' restart failed (rc={rc}).",
                data={"stdout": stdout, "stderr": stderr, "returncode": rc},
            )
    except ValueError as exc:
        return StatusResponse(success=False, message=str(exc))
    except Exception as exc:
        logger.error("Failed to restart service '%s': %s", service_name, exc, exc_info=True)
        return StatusResponse(success=False, message=str(exc))


@router.get("/{service_name}/status", response_model=StatusResponse)
async def get_service_status(
    service_name: str,
    auth: bool = Depends(verify_auth),
):
    """
    Query the status of a managed system service.

    Returns the output of `systemctl is-active <service>` and
    `systemctl status <service>`.
    """
    try:
        _validate_service(service_name)

        # Quick active check
        stdout_active, _, rc_active = run_command(
            f"systemctl is-active {service_name}", timeout=10
        )

        # Full status (may include recent logs)
        stdout_status, stderr_status, _ = run_command(
            f"systemctl status {service_name} --no-pager -l", timeout=10
        )

        is_active = stdout_active.strip() == "active"

        return StatusResponse(
            success=True,
            message=f"Service '{service_name}' is {'active' if is_active else stdout_active.strip()}.",
            data={
                "service": service_name,
                "active": is_active,
                "state": stdout_active.strip(),
                "status_output": stdout_status,
            },
        )
    except ValueError as exc:
        return StatusResponse(success=False, message=str(exc))
    except Exception as exc:
        logger.error(
            "Failed to get status for service '%s': %s", service_name, exc, exc_info=True
        )
        return StatusResponse(success=False, message=str(exc))
