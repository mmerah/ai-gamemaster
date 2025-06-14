import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from flask import Flask

from app.models.config import ServiceConfigModel
from app.providers.ai.manager import get_ai_service
from app.settings import get_settings


def setup_logging(app: Flask) -> None:
    """Configures logging for the Flask application."""
    log_level_str = app.config.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    log_file = app.config.get("LOG_FILE", "app.log")

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


def create_app(test_config: Optional[ServiceConfigModel] = None) -> Flask:
    """Flask application factory."""

    # Explicitly tell Flask where the templates and static folders are,
    # relative to the 'app' package directory where __init__.py resides.
    app = Flask(
        __name__,
        instance_relative_config=False,
        template_folder="../templates",
        static_folder="../static",
    )

    # Load configuration from Settings
    settings = get_settings()
    # Convert settings to dict for Flask config
    settings_dict = settings.to_service_config_dict()
    app.config.update(settings_dict)

    # Override with test configuration if provided
    if test_config:
        # Convert ServiceConfigModel to dict for Flask config
        test_config_dict = test_config.model_dump()
        app.config.update(test_config_dict)

        # Special handling for AI_SERVICE which is excluded from model_dump
        if hasattr(test_config, "AI_SERVICE") and test_config.AI_SERVICE is not None:
            app.config["AI_SERVICE"] = test_config.AI_SERVICE

    # Setup logging BEFORE other components
    setup_logging(app)

    # Initialize AI Service
    try:
        # In testing mode, check if AI_SERVICE is already set
        if app.config.get("TESTING") and app.config.get("AI_SERVICE") is not None:
            app.logger.info(
                f"Using pre-configured AI Service: {type(app.config['AI_SERVICE']).__name__}"
            )
        else:
            # Create ServiceConfigModel from settings
            service_config = ServiceConfigModel(**settings.to_service_config_dict())
            ai_service = get_ai_service(service_config)
            app.config["AI_SERVICE"] = ai_service
            if ai_service:
                app.logger.info(f"AI Service Initialized: {type(ai_service).__name__}")
            else:
                app.logger.error("AI Service returned None - check configuration")
                app.config["AI_SERVICE"] = None
    except Exception as e:
        app.logger.critical(
            f"FATAL: Failed to initialize AI Service: {e}", exc_info=True
        )  # Log traceback
        app.config["AI_SERVICE"] = None
        app.logger.warning("AI Service could not be initialized. API calls will fail.")

    with app.app_context():
        # Initialize service container
        from .core.container import initialize_container

        # Pass settings or test config to container
        if not app.config.get("TESTING"):
            initialize_container(settings)
        else:
            # In testing, use the test config directly
            initialize_container(app.config)  # type: ignore[arg-type]
        app.logger.info("Service container initialized.")

        # Initialize routes
        from .api import initialize_routes

        initialize_routes(app)

        app.logger.info("Flask App Created and Configured.")
        app.logger.info(f"Debug mode: {app.config['FLASK_DEBUG']}")
        app.logger.info(f"Using AI Provider: {app.config.get('AI_PROVIDER')}")

        return app
