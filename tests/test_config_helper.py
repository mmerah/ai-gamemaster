"""Helper for creating test configurations consistently."""

from typing import Any

from app.models.config import ServiceConfigModel


def create_test_service_config(**overrides: Any) -> ServiceConfigModel:
    """
    Create a ServiceConfigModel for tests with sensible defaults.

    Args:
        **overrides: Any fields to override from defaults

    Returns:
        ServiceConfigModel configured for testing
    """
    import tempfile

    # Create a temporary directory for test files
    test_temp_dir = tempfile.mkdtemp(prefix="ai_gamemaster_test_")

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
        # Use temporary directories for all file-based repositories
        "SAVES_DIR": f"{test_temp_dir}/saves",
        "CAMPAIGN_TEMPLATES_DIR": f"{test_temp_dir}/saves/campaign_templates",
        "CHARACTER_TEMPLATES_DIR": f"{test_temp_dir}/saves/character_templates",
        "TTS_CACHE_DIR": f"{test_temp_dir}/tts_cache",
    }

    # Apply overrides
    config_data = {**defaults, **overrides}

    return ServiceConfigModel(**config_data)
