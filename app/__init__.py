"""
FastAPI application factory.

This module creates and configures the FastAPI application instance.
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from app.core.container import get_container, initialize_container
from app.settings import Settings, get_settings


def setup_logging(settings: Settings) -> None:
    """Configure application logging."""
    log_level = getattr(logging, settings.system.log_level.upper())

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if settings.system.log_file:
        handlers.append(logging.FileHandler(settings.system.log_file))

    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        handlers=handlers,
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured. Level: {settings.system.log_level}")


def create_app(test_config: Optional[Settings] = None) -> FastAPI:
    """Create and configure FastAPI application."""

    # Load settings
    settings = test_config or get_settings()

    # Create FastAPI app
    app = FastAPI(
        title="AI Game Master",
        description="AI-powered D&D 5e game master",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # Store settings in app state (type-safe via AppState protocol)
    app.state.settings = settings

    # Setup logging
    setup_logging(settings)

    # Register custom exception handlers for consistent error format
    from app.api.exception_handlers import (
        application_exception_handler,
        http_exception_handler,
        pydantic_validation_exception_handler,
        validation_exception_handler,
    )
    from app.exceptions import ApplicationError

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(ApplicationError, application_exception_handler)

    # Initialize service container
    initialize_container(settings)
    app.state.container = get_container()

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Mount assets directory for Vite-generated files, if it exists
    assets_dir = Path("static/dist/assets")
    if assets_dir.exists() and assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        logging.info(f"Mounted assets directory: {assets_dir}")
    else:
        logging.warning(f"Assets directory not found, skipping mount: {assets_dir}")

    # Initialize routes (will be populated as routes are converted)
    try:
        from app.api import initialize_fastapi_routes

        initialize_fastapi_routes(app)
    except ImportError:
        # Routes not yet converted, this is expected during migration
        logging.info("FastAPI routes not yet available, continuing with setup")

    logging.info("FastAPI application created and configured")
    return app
