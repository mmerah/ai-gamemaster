"""
Test configuration to reduce logging noise and provide shared test fixtures.
"""

import logging
import os
import sys
from typing import Any, Dict, Generator, List
from unittest.mock import Mock

from app.models.config import ServiceConfigModel
from app.providers.ai.schemas import AIResponse

# Register our pytest plugins
pytest_plugins = ["tests.pytest_plugins"]


def setup_test_logging() -> None:
    """Configure logging for tests to reduce noise."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
    verbose_loggers = [
        "app.services.rag",
        "app.ai_services",
        "app.services.action_handlers",
        "app.repositories",
        "urllib3",
        "requests",
    ]
    for logger_name in verbose_loggers:
        logging.getLogger(logger_name).setLevel(logging.ERROR)


def get_test_config(**overrides: Any) -> ServiceConfigModel:
    """Creates a ServiceConfigModel with test-friendly defaults.

    Args:
        **overrides: Keyword arguments to override default test configuration values.
                    Any valid ServiceConfigModel field can be overridden.

    Returns:
        ServiceConfigModel configured for testing with the provided overrides applied.

    Example:
        # Use defaults
        config = get_test_config()

        # Enable RAG for a specific test
        config = get_test_config(RAG_ENABLED=True)

        # Use a different game state repo type
        config = get_test_config(GAME_STATE_REPO_TYPE='file')
    """
    # Use temp directory for tests to avoid polluting the real saves directory
    import tempfile

    temp_dir = tempfile.mkdtemp(prefix="ai_gamemaster_test_")

    # Import ServiceConfigModel to ensure proper typing
    from app.models.config import ServiceConfigModel

    config_data = {
        "GAME_STATE_REPO_TYPE": "memory",
        "TTS_PROVIDER": "disabled",
        "RAG_ENABLED": False,
        "SECRET_KEY": "test-secret-key",
        "TESTING": True,
        "FLASK_DEBUG": False,
        "LOG_LEVEL": "ERROR",  # Keep test logs clean
        "SAVES_DIR": temp_dir,
        "CAMPAIGNS_DIR": os.path.join(temp_dir, "campaigns"),
        "CHARACTER_TEMPLATES_DIR": os.path.join(temp_dir, "character_templates"),
        "CAMPAIGN_TEMPLATES_DIR": os.path.join(temp_dir, "campaign_templates"),
        # Set AI provider to empty to ensure mock is used
        "AI_PROVIDER": "",
        # Disable RAG for faster tests unless explicitly enabled
        "RAG_MAX_RESULTS_PER_QUERY": 1,
        "RAG_MAX_TOTAL_RESULTS": 2,
        # Set other important test configs
        "MAX_AI_CONTINUATION_DEPTH": 5,  # Prevent infinite loops in tests
        "AI_REQUEST_TIMEOUT": 10,  # Shorter timeout for tests
        "AI_MAX_RETRIES": 1,  # Fewer retries in tests
    }

    # Apply any overrides
    config_data.update(overrides)

    return ServiceConfigModel(**config_data)


# Automatically set up logging when this module is imported
if "unittest" in sys.modules or "pytest" in sys.modules or "test" in sys.argv[0]:
    setup_test_logging()
    # Set environment variables early to prevent ML library imports
    os.environ.setdefault("TESTING", "true")  # Prevent run.py from creating app
    os.environ.setdefault("RAG_ENABLED", "false")
    os.environ.setdefault("TTS_PROVIDER", "disabled")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

    import warnings

    warnings.filterwarnings("ignore", message=".*NumPy module was reloaded.*")
    warnings.filterwarnings("ignore", message=".*deprecat.*")

# --- Centralized AI Mocking Fixtures ---


class MockAIService:
    """Mock AI service that returns predefined responses in sequence."""

    def __init__(self) -> None:
        self.responses: List[AIResponse] = []
        self.call_index = 0
        # Support for side_effect assignment
        self.get_response = Mock(side_effect=self._get_response)
        self.get_structured_response = Mock(side_effect=self._get_structured_response)

    def add_response(self, response: AIResponse) -> None:
        """Add a response to the queue for the mock to return."""
        self.responses.append(response)

    def _get_response(
        self, messages: List[Dict[str, str]], **kwargs: Any
    ) -> AIResponse:
        """Return the next queued response, raising an error if none are left."""
        if self.call_index >= len(self.responses):
            raise ValueError(
                f"MockAIService exhausted. It was called {self.call_index + 1} times, "
                f"but only {len(self.responses)} responses were configured."
            )
        response = self.responses[self.call_index]
        self.call_index += 1
        return response

    def _get_structured_response(
        self, messages: List[Dict[str, str]], response_format: Any, **kwargs: Any
    ) -> AIResponse:
        """Return the next queued response, same as get_response."""
        return self._get_response(messages, **kwargs)

    def reset(self) -> None:
        """Reset the mock service state."""
        self.responses = []
        self.call_index = 0
        # Reset mocks to use the original methods
        self.get_response = Mock(side_effect=self._get_response)
        self.get_structured_response = Mock(side_effect=self._get_structured_response)


from unittest.mock import patch

import pytest

from app.core.container import reset_container

# Create a module-level mock instance that persists
_mock_ai_service_instance = None
logger = logging.getLogger(__name__)


def _get_mock_ai_service(config: ServiceConfigModel) -> MockAIService:
    """Factory function that returns our mock service."""
    global _mock_ai_service_instance
    if _mock_ai_service_instance is None:
        _mock_ai_service_instance = MockAIService()
    logger.warning("MOCK AI SERVICE: Returning mock AI service instead of real one")
    return _mock_ai_service_instance


# Apply the patch at module level to catch any imports
# This needs to happen before ANY other imports that might create an app
import sys

if "pytest" in sys.modules or "test" in sys.argv[0]:
    _patcher = patch(
        "app.providers.ai.manager.get_ai_service", side_effect=_get_mock_ai_service
    )
    _patcher.start()


@pytest.fixture
def mock_ai_service() -> Generator[MockAIService, None, None]:
    """Provides the shared MockAIService instance for each test."""
    global _mock_ai_service_instance
    if _mock_ai_service_instance is None:
        _mock_ai_service_instance = MockAIService()
    # Reset it for each test
    _mock_ai_service_instance.reset()
    yield _mock_ai_service_instance


@pytest.fixture
def app(mock_ai_service: MockAIService) -> Generator[Any, None, None]:
    """
    Creates a Flask app with the AI Service properly mocked *before* initialization.
    This is the key to preventing real API calls during tests.
    """
    reset_container()

    # Get test config as ServiceConfigModel
    config = get_test_config()
    # Set the AI service in the config
    config.AI_SERVICE = mock_ai_service

    # Import and create the app with ServiceConfigModel
    from app import create_app

    app = create_app(config)

    # Ensure the app context is available for tests that need it
    with app.app_context():
        yield app

    # Cleanup after test
    reset_container()
