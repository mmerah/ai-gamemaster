"""
FastAPI route initialization.

This module registers all FastAPI routers with the application.
"""

import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def initialize_fastapi_routes(app: FastAPI) -> None:
    """Initialize all FastAPI routes."""
    logger.info("FastAPI route initialization started")

    # Import routers
    from .campaign_routes import router as campaign_router
    from .campaign_template_routes import router as campaign_template_router
    from .character_routes import router as character_router
    from .config_routes import router as config_router
    from .content_routes import router as content_router
    from .d5e_routes import router as d5e_router
    from .frontend_routes import router as frontend_router
    from .game_routes import router as game_router
    from .sse_routes import router as sse_router
    from .tts_routes import router as tts_router

    # Include routers
    app.include_router(character_router)
    app.include_router(config_router)
    app.include_router(tts_router)
    app.include_router(campaign_router)
    app.include_router(campaign_template_router)
    app.include_router(content_router)
    app.include_router(d5e_router)
    app.include_router(game_router)
    app.include_router(sse_router)

    # Frontend router must be included last due to catch-all route
    app.include_router(frontend_router)

    logger.info("FastAPI route initialization completed")
