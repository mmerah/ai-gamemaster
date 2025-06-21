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
    from .campaign_template_fastapi import router as campaign_template_router
    from .character_fastapi import router as character_router
    from .config_fastapi import router as config_router
    from .content_fastapi import router as content_router
    from .d5e_fastapi import router as d5e_router
    from .frontend_fastapi import router as frontend_router
    from .game_fastapi import router as game_router
    from .sse_fastapi import router as sse_router
    from .tts_fastapi import router as tts_router

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

    # Note: Root route is now handled by frontend_router

    # Add more routers as they're converted
    # app.include_router(campaign_router)
    # app.include_router(game_router)
    # etc.

    logger.info("FastAPI route initialization completed")
