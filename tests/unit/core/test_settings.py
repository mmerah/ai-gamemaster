"""
Unit tests for the new pydantic-settings configuration.
"""

import os
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import patch

import pytest
from pydantic import ValidationError

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
    get_settings,
)


@pytest.fixture
def clean_environment() -> Generator[None, None, None]:
    """Fixture to ensure a clean environment for each test."""
    # Save current environment
    old_env = dict(os.environ)

    # Clear all relevant environment variables
    env_vars = [
        "AI_PROVIDER",
        "AI_RESPONSE_PARSING_MODE",
        "AI_TEMPERATURE",
        "AI_MAX_TOKENS",
        "AI_MAX_RETRIES",
        "AI_RETRY_DELAY",
        "AI_REQUEST_TIMEOUT",
        "AI_RETRY_CONTEXT_TIMEOUT",
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL_NAME",
        "OPENROUTER_BASE_URL",
        "LLAMA_SERVER_URL",
        "MAX_AI_CONTINUATION_DEPTH",
        "MAX_PROMPT_TOKENS_BUDGET",
        "LAST_X_HISTORY_MESSAGES",
        "TOKENS_PER_MESSAGE_OVERHEAD",
        "DATABASE_URL",
        "DATABASE_ECHO",
        "DATABASE_POOL_SIZE",
        "DATABASE_MAX_OVERFLOW",
        "DATABASE_POOL_TIMEOUT",
        "DATABASE_POOL_RECYCLE",
        "ENABLE_SQLITE_VEC",
        "SQLITE_BUSY_TIMEOUT",
        "RAG_ENABLED",
        "RAG_MAX_RESULTS_PER_QUERY",
        "RAG_MAX_TOTAL_RESULTS",
        "RAG_SCORE_THRESHOLD",
        "RAG_EMBEDDINGS_MODEL",
        "RAG_CHUNK_SIZE",
        "RAG_CHUNK_OVERLAP",
        "RAG_COLLECTION_NAME_PREFIX",
        "RAG_METADATA_FILTERING_ENABLED",
        "RAG_RELEVANCE_FEEDBACK_ENABLED",
        "RAG_CACHE_TTL",
        "TTS_PROVIDER",
        "TTS_VOICE",
        "KOKORO_LANG_CODE",
        "TTS_CACHE_DIR_NAME",
        "GAME_STATE_REPO_TYPE",
        "CAMPAIGNS_DIR",
        "CHARACTER_TEMPLATES_DIR",
        "CAMPAIGN_TEMPLATES_DIR",
        "SAVES_DIR",
        "SECRET_KEY",
        "TESTING",
        "SSE_HEARTBEAT_INTERVAL",
        "SSE_EVENT_TIMEOUT",
        "DEBUG",
        "LOG_LEVEL",
        "LOG_FILE",
        "EVENT_QUEUE_MAX_SIZE",
    ]

    for var in env_vars:
        os.environ.pop(var, None)

    # Reset the singleton
    from app import settings as settings_module

    settings_module._settings = None

    yield

    # Restore environment
    os.environ.clear()
    os.environ.update(old_env)
    settings_module._settings = None


class TestAISettings:
    """Test AI configuration settings."""

    def test_default_values(self, clean_environment: None) -> None:
        """Test default AI settings values."""
        settings = AISettings()
        assert settings.provider == "llamacpp_http"
        assert settings.response_parsing_mode == "strict"
        assert settings.temperature == 0.7
        assert settings.max_tokens == 4096
        assert settings.max_retries == 3
        assert settings.retry_delay == 5.0
        assert settings.request_timeout == 60.0
        assert settings.retry_context_timeout == 300
        assert settings.openrouter_api_key is None
        assert settings.openrouter_model_name is None
        assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"
        assert settings.llama_server_url == "http://127.0.0.1:8080"
        assert settings.max_continuation_depth == 20

    def test_environment_variables(self, clean_environment: None) -> None:
        """Test loading AI settings from environment variables."""
        os.environ["AI_PROVIDER"] = "openrouter"
        os.environ["AI_RESPONSE_PARSING_MODE"] = "flexible"
        os.environ["AI_TEMPERATURE"] = "1.5"
        os.environ["AI_MAX_TOKENS"] = "8192"
        os.environ["OPENROUTER_API_KEY"] = "test-key"
        os.environ["OPENROUTER_MODEL_NAME"] = "test-model"

        settings = AISettings()
        assert settings.provider == "openrouter"
        assert settings.response_parsing_mode == "flexible"
        assert settings.temperature == 1.5
        assert settings.max_tokens == 8192
        assert settings.openrouter_api_key is not None
        assert settings.openrouter_api_key.get_secret_value() == "test-key"
        assert settings.openrouter_model_name == "test-model"

    def test_validation(self, clean_environment: None) -> None:
        """Test AI settings validation."""
        # Valid provider
        os.environ["AI_PROVIDER"] = "llamacpp_http"
        settings = AISettings()
        assert settings.provider == "llamacpp_http"

        # Invalid provider should raise error
        os.environ["AI_PROVIDER"] = "invalid_provider"
        from pydantic import ValidationError

        with pytest.raises(
            ValidationError, match="Input should be 'llamacpp_http' or 'openrouter'"
        ):
            AISettings()

        # Valid parsing mode
        os.environ["AI_PROVIDER"] = "llamacpp_http"
        os.environ["AI_RESPONSE_PARSING_MODE"] = "flexible"
        settings = AISettings()
        assert settings.response_parsing_mode == "flexible"

        # Invalid parsing mode
        os.environ["AI_RESPONSE_PARSING_MODE"] = "invalid_mode"
        with pytest.raises(
            ValidationError, match="Input should be 'strict' or 'flexible'"
        ):
            AISettings()

    def test_temperature_bounds(self, clean_environment: None) -> None:
        """Test temperature validation bounds."""
        # Valid temperatures
        os.environ["AI_TEMPERATURE"] = "0.0"
        settings = AISettings()
        assert settings.temperature == 0.0

        os.environ["AI_TEMPERATURE"] = "2.0"
        settings = AISettings()
        assert settings.temperature == 2.0

        # Invalid temperatures
        os.environ["AI_TEMPERATURE"] = "-0.1"
        with pytest.raises(ValidationError):
            AISettings()

        os.environ["AI_TEMPERATURE"] = "2.1"
        with pytest.raises(ValidationError):
            AISettings()


class TestDatabaseSettings:
    """Test database configuration settings."""

    def test_default_values(self, clean_environment: None) -> None:
        """Test default database settings values."""
        settings = DatabaseSettings()
        assert settings.url.get_secret_value() == "sqlite:///data/content.db"
        assert settings.echo is False
        assert settings.pool_size == 5
        assert settings.max_overflow == 10
        assert settings.pool_timeout == 30
        assert settings.pool_recycle == 3600
        assert settings.enable_sqlite_vec is True
        assert settings.sqlite_busy_timeout == 5000

    def test_environment_variables(self, clean_environment: None) -> None:
        """Test loading database settings from environment variables."""
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"
        os.environ["DATABASE_ECHO"] = "true"
        os.environ["DATABASE_POOL_SIZE"] = "10"
        os.environ["SQLITE_BUSY_TIMEOUT"] = "10000"

        settings = DatabaseSettings()
        assert settings.url.get_secret_value() == "postgresql://user:pass@localhost/db"
        assert settings.echo is True
        assert settings.pool_size == 10
        assert settings.sqlite_busy_timeout == 10000


class TestRAGSettings:
    """Test RAG configuration settings."""

    def test_default_values(self, clean_environment: None) -> None:
        """Test default RAG settings values."""
        settings = RAGSettings()
        assert settings.enabled is True
        assert settings.max_results_per_query == 3
        assert settings.max_total_results == 8
        assert settings.score_threshold == 0.2
        assert settings.embeddings_model == "all-MiniLM-L6-v2"
        assert settings.chunk_size == 500
        assert settings.chunk_overlap == 50
        assert settings.collection_name_prefix == "ai_gamemaster"
        assert settings.metadata_filtering_enabled is False
        assert settings.relevance_feedback_enabled is False
        assert settings.cache_ttl == 3600

    def test_environment_variables(self, clean_environment: None) -> None:
        """Test loading RAG settings from environment variables."""
        os.environ["RAG_ENABLED"] = "false"
        os.environ["RAG_MAX_RESULTS_PER_QUERY"] = "5"
        os.environ["RAG_SCORE_THRESHOLD"] = "0.5"
        os.environ["RAG_EMBEDDINGS_MODEL"] = "custom-model"

        settings = RAGSettings()
        assert settings.enabled is False
        assert settings.max_results_per_query == 5
        assert settings.score_threshold == 0.5
        assert settings.embeddings_model == "custom-model"


class TestMainSettings:
    """Test the main Settings class that aggregates all settings."""

    def test_default_initialization(self, clean_environment: None) -> None:
        """Test that Settings initializes all sub-settings with defaults."""
        settings = Settings()

        # Check that all sub-settings are initialized
        assert isinstance(settings.ai, AISettings)
        assert isinstance(settings.prompt, PromptSettings)
        assert isinstance(settings.database, DatabaseSettings)
        assert isinstance(settings.rag, RAGSettings)
        assert isinstance(settings.tts, TTSSettings)
        assert isinstance(settings.storage, StorageSettings)
        assert isinstance(settings.sse, SSESettings)
        assert isinstance(settings.system, SystemSettings)

        # Spot check some values
        assert settings.ai.provider == "llamacpp_http"
        assert settings.database.url.get_secret_value() == "sqlite:///data/content.db"
        assert settings.rag.enabled is True

    def test_environment_override(self, clean_environment: None) -> None:
        """Test that environment variables override defaults."""
        os.environ["AI_PROVIDER"] = "openrouter"
        os.environ["DATABASE_URL"] = "postgresql://test"
        os.environ["RAG_ENABLED"] = "false"

        settings = Settings()
        assert settings.ai.provider == "openrouter"
        assert settings.database.url.get_secret_value() == "postgresql://test"
        assert settings.rag.enabled is False

    def test_validate_config(self, clean_environment: None, capsys: Any) -> None:
        """Test configuration validation warnings."""
        # Test openrouter without API key
        os.environ["AI_PROVIDER"] = "openrouter"
        settings = Settings()
        settings.validate_config()
        captured = capsys.readouterr()
        assert "OPENROUTER_API_KEY is not set" in captured.out

        # Test openrouter without model name
        os.environ["OPENROUTER_API_KEY"] = "test-key"
        settings = Settings()
        settings.validate_config()
        captured = capsys.readouterr()
        assert "OPENROUTER_MODEL_NAME is not set" in captured.out

        # Test llamacpp without server URL
        os.environ["AI_PROVIDER"] = "llamacpp_http"
        os.environ["LLAMA_SERVER_URL"] = ""
        settings = Settings()
        settings.validate_config()
        captured = capsys.readouterr()
        assert "LLAMA_SERVER_URL is not set" in captured.out


class TestGetSettings:
    """Test the get_settings singleton function."""

    def test_singleton_behavior(self, clean_environment: None) -> None:
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_environment_changes(self, clean_environment: None) -> None:
        """Test that settings are cached after first creation."""
        # First call creates settings with defaults
        settings1 = get_settings()
        assert settings1.ai.provider == "llamacpp_http"

        # Change environment after settings created
        os.environ["AI_PROVIDER"] = "openrouter"

        # Should still return the cached instance with old values
        settings2 = get_settings()
        assert settings2 is settings1
        assert settings2.ai.provider == "llamacpp_http"  # Still the old value


class TestServiceContainerIntegration:
    """Test ServiceContainer integration with new Settings."""

    def test_container_with_settings(self, clean_environment: None) -> None:
        """Test that ServiceContainer can accept Settings object."""
        from app.core.container import ServiceContainer

        settings = Settings()
        container = ServiceContainer(settings)

        # Test that settings are properly stored
        assert container.settings.ai.provider == "llamacpp_http"
        assert (
            container.settings.database.url.get_secret_value()
            == "sqlite:///data/content.db"
        )
        assert container.settings.rag.enabled is True

    def test_container_settings_override(self, clean_environment: None) -> None:
        """Test that ServiceContainer uses provided settings."""
        from app.core.container import ServiceContainer

        # Create custom settings
        os.environ["AI_PROVIDER"] = "openrouter"
        os.environ["DATABASE_URL"] = "postgresql://test"
        os.environ["RAG_ENABLED"] = "false"

        settings = Settings()
        container = ServiceContainer(settings)

        assert container.settings.ai.provider == "openrouter"
        assert container.settings.database.url.get_secret_value() == "postgresql://test"
        assert container.settings.rag.enabled is False
