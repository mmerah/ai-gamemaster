"""Helper for creating test configurations consistently."""

from typing import Any

from app.models.models import ServiceConfigModel


def create_test_service_config(**overrides: Any) -> ServiceConfigModel:
    """
    Create a ServiceConfigModel for tests with sensible defaults.

    Args:
        **overrides: Any fields to override from defaults

    Returns:
        ServiceConfigModel configured for testing
    """
    defaults = {
        "GAME_STATE_REPO_TYPE": "memory",
        "TTS_PROVIDER": "disabled",
        "RAG_ENABLED": False,
        "TESTING": True,
        "AI_PROVIDER": "",  # Empty to ensure mock is used
        "LOG_LEVEL": "WARNING",
        "MAX_AI_CONTINUATION_DEPTH": 5,
        "AI_REQUEST_TIMEOUT": 10,
        "AI_MAX_RETRIES": 1,
    }

    # Apply overrides
    config_data = {**defaults, **overrides}

    return ServiceConfigModel(**config_data)
