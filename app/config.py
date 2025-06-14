"""
Configuration module for backward compatibility.

This module now simply re-exports from the new settings module.
All new code should import directly from app.settings instead.
"""

from typing import Any, Dict

from app.models.config import ServiceConfigModel
from app.settings import get_settings


def create_service_config_from_flask(
    flask_config: Dict[str, Any],
) -> ServiceConfigModel:
    """Convert Flask config dictionary to ServiceConfigModel for type safety."""
    # Use the settings instance to get the config data
    settings = get_settings()
    config_data = settings.to_service_config_dict()

    # Override with any values from flask_config if present
    for key in config_data:
        if key in flask_config:
            config_data[key] = flask_config[key]

    # Add any Flask-specific settings
    config_data["TESTING"] = flask_config.get("TESTING", False)
    config_data["DEBUG"] = flask_config.get("DEBUG", False)

    return ServiceConfigModel(**config_data)
