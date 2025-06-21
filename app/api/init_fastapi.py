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
    logger.info("FastAPI route initialization started")

    # Import routers as they're converted
    from .campaign_fastapi import router as campaign_router
    from .character_fastapi import router as character_router
    from .config_fastapi import router as config_router
    from .health_fastapi import router as health_router
    from .tts_fastapi import router as tts_router

    # Include routers
    app.include_router(health_router)
    app.include_router(character_router)
    app.include_router(config_router)
    app.include_router(tts_router)
    app.include_router(campaign_router)

    # Add a simple root route for testing
    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint for testing FastAPI is working."""
        return {"message": "AI Game Master API (FastAPI)", "status": "migrating"}

    # Add more routers as they're converted
    # app.include_router(campaign_router)
    # app.include_router(game_router)
    # etc.

    logger.info("FastAPI route initialization completed")
