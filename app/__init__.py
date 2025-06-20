import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from flask import Flask

from app.settings import Settings, get_settings


def setup_logging(app: Flask, settings: Settings) -> None:
    """Configures logging for the Flask application."""
    log_level_str = settings.system.log_level.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    log_file = settings.system.log_file

    # Basic Console Handler
    logging.basicConfig(
        level=log_level, format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    app.logger.setLevel(log_level)

    # File Handler (Optional but Recommended)
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        try:
            # Use RotatingFileHandler for larger applications, 1MB per file, 10 backups
            file_handler = RotatingFileHandler(
                log_file, maxBytes=1024000, backupCount=10
            )
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            file_handler.setLevel(log_level)
            app.logger.addHandler(file_handler)
            app.logger.info(
                f"Logging configured. Level: {log_level_str}. File: {log_file}"
            )
        except Exception as e:
            app.logger.error(f"Failed to set up file logging to {log_file}: {e}")

    app.logger.info("D&D AI PoC application starting up...")


def create_app(test_settings: Optional[Settings] = None) -> Flask:
    """Flask application factory."""

    # Explicitly tell Flask where the templates and static folders are,
    # relative to the 'app' package directory where __init__.py resides.
    app = Flask(
        __name__,
        instance_relative_config=False,
        template_folder="../templates",
        static_folder="../static",
    )

    # Use test settings if provided, otherwise get default settings
    settings = test_settings or get_settings()

    # Setup logging BEFORE other components
    setup_logging(app, settings)

    with app.app_context():
        # Initialize service container
        from .core.container import initialize_container

        # Always pass settings to container
        initialize_container(settings)
        app.logger.info("Service container initialized.")

        # Initialize routes
        from .api import initialize_routes

        initialize_routes(app)

        app.logger.info("Flask App Created and Configured.")
        app.logger.info(f"Debug mode: {settings.flask.flask_debug}")

        return app
