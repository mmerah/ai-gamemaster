"""
Pytest plugins for proper test isolation.
"""

import os
import shutil
import tempfile
from typing import Generator, Optional
from unittest.mock import _patch

import pytest


class EarlyMockAIService:
    """Simple mock that will be replaced by the real mock later."""

    def __init__(self) -> None:
        pass


# Module-level variable to store patcher
_ai_service_patcher: Optional[_patch] = None  # type: ignore[type-arg]


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with proper test environment."""
    # Apply early patch for AI service to prevent real API calls
    # This MUST happen before any imports that might create an app
    from unittest.mock import patch

    def _early_get_mock_ai_service(config: pytest.Config) -> EarlyMockAIService:
        """Early factory that returns a basic mock."""
        import logging

        logging.getLogger(__name__).warning(
            "EARLY MOCK: Preventing real AI service creation"
        )
        return EarlyMockAIService()

    global _ai_service_patcher
    _ai_service_patcher = patch(
        "app.ai_services.manager.get_ai_service", side_effect=_early_get_mock_ai_service
    )
    _ai_service_patcher.start()

    # Set environment variables early
    if "RAG_ENABLED" not in os.environ:
        os.environ["RAG_ENABLED"] = "false"
    if "TTS_PROVIDER" not in os.environ:
        os.environ["TTS_PROVIDER"] = "disabled"
    if "GAME_STATE_REPO_TYPE" not in os.environ:
        os.environ["GAME_STATE_REPO_TYPE"] = "memory"

    # Set test save directories to temp location to prevent real saves
    temp_base = tempfile.mkdtemp(prefix="ai_gamemaster_test_")
    os.environ["SAVES_DIR"] = os.path.join(temp_base, "saves")
    os.environ["CAMPAIGNS_DIR"] = os.path.join(temp_base, "campaigns")
    os.environ["CHARACTER_TEMPLATES_DIR"] = os.path.join(
        temp_base, "character_templates"
    )
    os.environ["CAMPAIGN_TEMPLATES_DIR"] = os.path.join(temp_base, "campaign_templates")

    # Store temp dir for cleanup
    setattr(config, "_temp_test_dir", temp_base)


def pytest_unconfigure(config: pytest.Config) -> None:
    """Clean up after all tests."""
    if hasattr(config, "_temp_test_dir"):
        shutil.rmtree(getattr(config, "_temp_test_dir"), ignore_errors=True)

    # Stop the AI service patcher
    global _ai_service_patcher
    if _ai_service_patcher is not None:
        _ai_service_patcher.stop()


@pytest.fixture(autouse=True, scope="function")
def reset_modules_between_tests() -> Generator[None, None, None]:
    """
    Reset problematic modules between tests to avoid the _has_torch_function error.
    This fixture runs automatically before each test.
    """
    # Ensure container is reset before each test
    from app.core.container import reset_container

    reset_container()

    yield

    # Note: We no longer try to remove torch/numpy modules as this causes more problems
    # The global RAG service cache in container.py handles the reimport issue instead
