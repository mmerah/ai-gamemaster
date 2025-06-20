"""
FastAPI route initialization.

This module registers all FastAPI routers with the application.
Routes are added incrementally as they are converted from Flask.
"""

import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def initialize_fastapi_routes(app: FastAPI) -> None:
    """Initialize all FastAPI routes."""

    # Routes will be added here as they are converted from Flask
    # Example:
    # from .health_fastapi import router as health_router
    # app.include_router(health_router)

    # For now, just log that routes are being initialized
    logger.info("FastAPI route initialization started")

    # Add a simple root route for testing
    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint for testing FastAPI is working."""
        return {"message": "AI Game Master API (FastAPI)", "status": "migrating"}

    logger.info("FastAPI route initialization completed")
