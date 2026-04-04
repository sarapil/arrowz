# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz Engine - FastAPI Application Entry Point

A system-level agent that runs on Linux boxes and receives
configuration from the Frappe Interface Layer.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from arrowz_engine.routes import health, config, clients, network, wifi, services

logger = logging.getLogger("arrowz_engine")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle handler."""
    # --- Startup ---
    logger.info("Arrowz Engine starting up...")
    # TODO: Load configuration from /etc/arrowz/engine.json
    # TODO: Initialize manager singletons
    # TODO: Start telemetry collection background task
    # TODO: Verify system dependencies (nftables, hostapd, tc, wg, etc.)
    logger.info("Arrowz Engine ready.")
    yield
    # --- Shutdown ---
    logger.info("Arrowz Engine shutting down...")
    # TODO: Gracefully stop background tasks
    # TODO: Flush any pending telemetry
    logger.info("Arrowz Engine stopped.")


app = FastAPI(
    title="Arrowz Engine",
    version="1.0.0",
    description="System-level configuration agent for Arrowz network appliances.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to Frappe server origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router Registration
# ---------------------------------------------------------------------------
app.include_router(health.router)
app.include_router(config.router)
app.include_router(clients.router)
app.include_router(network.router)
app.include_router(wifi.router)
app.include_router(services.router)


# ---------------------------------------------------------------------------
# Root Health Endpoint
# ---------------------------------------------------------------------------
@app.get("/", tags=["root"])
async def root():
    """Root health-check endpoint."""
    return {
        "service": "arrowz-engine",
        "version": "1.0.0",
        "status": "running",
    }
