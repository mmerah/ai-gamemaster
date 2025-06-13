"""
Routes package for the AI Game Master application.
"""

import logging
from typing import Tuple

from flask import Flask, Response, jsonify

from app.exceptions import HTTPException, map_to_http_exception

from .campaign_routes import campaign_bp
from .campaign_template_routes import campaign_template_bp
from .character_routes import character_bp
from .config_routes import config_bp
from .d5e_routes import d5e_bp
from .frontend_routes import frontend_bp
from .game_routes import game_bp
from .health import health_bp
from .sse_routes import sse_bp
from .tts_routes import tts_bp

logger = logging.getLogger(__name__)


def initialize_routes(app: Flask) -> None:
    """Initialize all routes with the Flask app."""
    # Register all blueprints
    app.register_blueprint(frontend_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(campaign_bp)
    app.register_blueprint(campaign_template_bp)
    app.register_blueprint(character_bp)
    app.register_blueprint(d5e_bp)
    app.register_blueprint(tts_bp)
    app.register_blueprint(sse_bp)
    app.register_blueprint(config_bp)
    app.register_blueprint(health_bp)

    # Register global error handlers
    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException) -> Tuple[Response, int]:
        """Handle HTTPException instances."""
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(Exception)
    def handle_generic_exception(error: Exception) -> Tuple[Response, int]:
        """Handle all other exceptions."""
        # Map to appropriate HTTP exception
        http_error = map_to_http_exception(error)

        # Log server errors
        if http_error.status_code >= 500:
            logger.error(
                f"Unhandled exception: {error}",
                exc_info=True,
                extra={"error_type": type(error).__name__},
            )

        return jsonify(http_error.to_dict()), http_error.status_code

    logger.info("All routes initialized.")
