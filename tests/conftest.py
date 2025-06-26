"""
Test configuration to reduce logging noise and provide shared test fixtures.
"""

import logging
import os
import sys
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.system_interfaces import IEventQueue
from app.models.common import MessageDict
from app.providers.ai.base import BaseAIService
from app.providers.ai.schemas import AIResponse
from app.settings import (
    AISettings,
    DatabaseSettings,
    PromptSettings,
    RAGSettings,
    Settings,
    SSESettings,
    StorageSettings,
    SystemSettings,
    TTSSettings,
)

# Register our pytest plugins
pytest_plugins = ["tests.pytest_plugins"]


@pytest.fixture(scope="session", autouse=True)
def clear_sentence_transformer_cache() -> Generator[None, None, None]:
    """Clear the global SentenceTransformer cache before running tests."""
    try:
        from app.content.rag.db_knowledge_base_manager import (
            clear_sentence_transformer_cache,
        )

        clear_sentence_transformer_cache()
    except ImportError:
        pass  # RAG module not available
    yield


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


def get_test_settings(
    *,
    ai: Optional[AISettings] = None,
    prompt: Optional[PromptSettings] = None,
    database: Optional[DatabaseSettings] = None,
    rag: Optional[RAGSettings] = None,
    tts: Optional[TTSSettings] = None,
    storage: Optional[StorageSettings] = None,
    sse: Optional[SSESettings] = None,
    system: Optional[SystemSettings] = None,
) -> Settings:
    """Creates a Settings object with test-friendly defaults.

    Pass complete Settings objects for each configuration group you want to override.
    Any groups not provided will use test-appropriate defaults created via environment variables.

    Args:
        ai: AI settings (defaults to empty provider for mock usage)
        prompt: Prompt settings (defaults to standard test values)
        database: Database settings (defaults to test SQLite)
        rag: RAG settings (defaults to disabled)
        tts: TTS settings (defaults to disabled)
        storage: Storage settings (defaults to memory repos)
        sse: SSE settings (defaults to test values)
        system: System settings (defaults to ERROR logging)

    Returns:
        Settings configured for testing with the provided overrides applied.

    Example:
        # Create settings objects with environment variables
        from pydantic import SecretStr

        settings = get_test_settings(
            ai=AISettings(
                AI_PROVIDER="openrouter",
                OPENROUTER_API_KEY=SecretStr("test-key")
            ),
            rag=RAGSettings(RAG_ENABLED="true"),
            storage=StorageSettings(GAME_STATE_REPO_TYPE="file")
        )
    """
    import tempfile

    temp_dir = tempfile.mkdtemp(prefix="ai_gamemaster_test_")

    # Set up environment for default values
    old_env = dict(os.environ)
    try:
        # Set test defaults in environment
        test_env = {
            "AI_PROVIDER": "llamacpp_http",  # Valid default for tests
            "AI_MAX_CONTINUATION_DEPTH": "5",
            "AI_REQUEST_TIMEOUT": "10",
            "AI_MAX_RETRIES": "1",
            "GAME_STATE_REPO_TYPE": "memory",
            "SAVES_DIR": temp_dir,
            "CAMPAIGNS_DIR": os.path.join(temp_dir, "campaigns"),
            "CHARACTER_TEMPLATES_DIR": os.path.join(temp_dir, "character_templates"),
            "CAMPAIGN_TEMPLATES_DIR": os.path.join(temp_dir, "campaign_templates"),
            "TTS_PROVIDER": "disabled",
            "RAG_ENABLED": "false",
            "RAG_MAX_RESULTS_PER_QUERY": "1",
            "RAG_MAX_TOTAL_RESULTS": "2",
            "SECRET_KEY": "test-secret-key",
            "TESTING": "true",
            "DEBUG": "false",
            "LOG_LEVEL": "ERROR",
            "SSE_EVENT_TIMEOUT": "0.05",  # Speed up SSE tests
            "SSE_HEARTBEAT_INTERVAL": "60",  # Longer heartbeat for tests
        }
        os.environ.update(test_env)

        # Create default settings for any missing groups
        default_ai = ai if ai is not None else AISettings()
        default_prompt = prompt if prompt is not None else PromptSettings()
        default_database = database if database is not None else DatabaseSettings()
        default_rag = rag if rag is not None else RAGSettings()
        default_tts = tts if tts is not None else TTSSettings()
        default_storage = storage if storage is not None else StorageSettings()
        default_sse = sse if sse is not None else SSESettings()
        default_system = system if system is not None else SystemSettings()

        # Create Settings with all groups
        return Settings(
            ai=default_ai,
            prompt=default_prompt,
            database=default_database,
            rag=default_rag,
            tts=default_tts,
            storage=default_storage,
            sse=default_sse,
            system=default_system,
        )
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(old_env)


def create_mock_event_queue() -> Mock:
    """Create a properly configured mock event queue for testing."""
    mock_event_queue = Mock(spec=IEventQueue)
    mock_event_queue.put_event = Mock()
    return mock_event_queue


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


class MockAIService(BaseAIService):
    """Mock AI service that returns predefined responses in sequence."""

    def __init__(self) -> None:
        self.responses: List[AIResponse] = []
        self.call_index = 0
        # Create a Mock object for get_response that delegates to _get_response_impl
        self.get_response = Mock(side_effect=self._get_response_impl)  # type: ignore[method-assign]
        self.get_structured_response = Mock(side_effect=self._get_structured_response)

    def add_response(self, response: AIResponse) -> None:
        """Add a response to the queue for the mock to return."""
        self.responses.append(response)

    def get_response(self, messages: List[MessageDict]) -> Optional[AIResponse]:
        """Override the abstract method - will be replaced by Mock in __init__."""
        # This will never be called because it's replaced by a Mock in __init__
        return self._get_response_impl(messages)

    def _get_response_impl(self, messages: List[MessageDict]) -> Optional[AIResponse]:
        """Implementation of get_response that returns the next queued response."""
        if self.call_index >= len(self.responses):
            raise ValueError(
                f"MockAIService exhausted. It was called {self.call_index + 1} times, "
                f"but only {len(self.responses)} responses were configured."
            )
        response = self.responses[self.call_index]
        self.call_index += 1
        return response

    def _get_structured_response(
        self, messages: List[MessageDict], response_format: Any, **kwargs: Any
    ) -> AIResponse:
        """Return the next queued response, same as get_response."""
        result = self._get_response_impl(messages)
        if result is None:
            raise ValueError("get_response returned None")
        return result

    def reset(self) -> None:
        """Reset the mock service state."""
        self.responses = []
        self.call_index = 0
        # Reset mocks with new side effects
        self.get_response = Mock(side_effect=self._get_response_impl)  # type: ignore[method-assign]
        self.get_structured_response = Mock(side_effect=self._get_structured_response)


from unittest.mock import patch

import pytest

from app.core.container import reset_container

# Create a module-level mock instance that persists
_mock_ai_service_instance = None
logger = logging.getLogger(__name__)


def _get_mock_ai_service(settings: Settings) -> BaseAIService:
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
def app(mock_ai_service: MockAIService) -> Generator[FastAPI, None, None]:
    """
    Creates a FastAPI app with the AI Service properly mocked *before* initialization.
    Note: This now creates a FastAPI app for all tests during migration.
    """
    reset_container()

    # Get test settings
    settings = get_test_settings()

    # Import and create the FastAPI app with Settings
    from app import create_app

    app = create_app(settings)
    # The mock AI service is already injected via the patched get_ai_service

    # Force the container to use our mock AI service
    from app.core.container import get_container

    container = get_container()
    if hasattr(container, "_ai_service"):
        # Replace any existing AI service with our mock
        container._ai_service = mock_ai_service

    yield app

    # Cleanup after test
    reset_container()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client - now returns FastAPI TestClient."""
    return TestClient(app)


# Keep these for backward compatibility during migration
@pytest.fixture
def fastapi_app(app: FastAPI) -> FastAPI:
    """Alias for app fixture - for backward compatibility."""
    return app


@pytest.fixture
def fastapi_client(client: TestClient) -> TestClient:
    """Alias for client fixture - for backward compatibility."""
    return client
