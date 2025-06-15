"""
Pydantic Settings for AI Game Master application.

This module uses pydantic-settings to provide type-safe configuration management
with environment variable support and validation.
"""

import os
from typing import Any, Dict, Literal, Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """AI service configuration settings."""

    provider: Literal["llamacpp_http", "openrouter"] = Field(
        default="llamacpp_http",
        description="AI provider to use",
        alias="AI_PROVIDER",
    )
    response_parsing_mode: Literal["strict", "flexible"] = Field(
        default="strict",
        description="JSON parsing mode",
        alias="AI_RESPONSE_PARSING_MODE",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for AI responses",
        alias="AI_TEMPERATURE",
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens for AI responses",
        alias="AI_MAX_TOKENS",
    )

    # Retry configuration
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retries for AI requests",
        alias="AI_MAX_RETRIES",
    )
    retry_delay: float = Field(
        default=5.0,
        ge=0,
        description="Delay between retries in seconds",
        alias="AI_RETRY_DELAY",
    )
    request_timeout: float = Field(
        default=60.0,
        gt=0,
        description="Request timeout in seconds",
        alias="AI_REQUEST_TIMEOUT",
    )
    retry_context_timeout: int = Field(
        default=300,
        gt=0,
        description="Retry context timeout in seconds",
        alias="AI_RETRY_CONTEXT_TIMEOUT",
    )

    # OpenRouter specific
    openrouter_api_key: Optional[SecretStr] = Field(
        default=None,
        description="OpenRouter API key",
        alias="OPENROUTER_API_KEY",
    )
    openrouter_model_name: Optional[str] = Field(
        default=None,
        description="OpenRouter model name",
        alias="OPENROUTER_MODEL_NAME",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter base URL",
        alias="OPENROUTER_BASE_URL",
    )

    # Llama.cpp specific
    llama_server_url: str = Field(
        default="http://127.0.0.1:8080",
        description="Llama.cpp HTTP server URL",
        alias="LLAMA_SERVER_URL",
    )

    # Auto-continuation
    max_continuation_depth: int = Field(
        default=20,
        gt=0,
        description="Maximum AI auto-continuation depth",
        alias="MAX_AI_CONTINUATION_DEPTH",
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=True,
        populate_by_name=True,
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Ensure provider is valid."""
        if v not in ["llamacpp_http", "openrouter"]:
            raise ValueError(f"Invalid AI provider: {v}")
        return v

    @field_validator("response_parsing_mode")
    @classmethod
    def validate_parsing_mode(cls, v: str) -> str:
        """Ensure parsing mode is valid."""
        if v not in ["strict", "flexible"]:
            raise ValueError(f"Invalid parsing mode: {v}")
        return v.lower()


class PromptSettings(BaseSettings):
    """Prompt builder configuration settings."""

    max_tokens_budget: int = Field(
        default=128000,
        gt=0,
        description="Maximum token budget for prompts",
        alias="MAX_PROMPT_TOKENS_BUDGET",
    )
    last_x_history_messages: int = Field(
        default=4,
        ge=0,
        description="Number of recent history messages to include",
        alias="LAST_X_HISTORY_MESSAGES",
    )
    tokens_per_message_overhead: int = Field(
        default=4,
        ge=0,
        description="Token overhead per message",
        alias="TOKENS_PER_MESSAGE_OVERHEAD",
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=True,
        populate_by_name=True,
    )


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: SecretStr = Field(
        default=SecretStr("sqlite:///data/content.db"),
        description="System database URL (read-only)",
        alias="DATABASE_URL",
    )
    user_url: SecretStr = Field(
        default=SecretStr("sqlite:///data/user_content.db"),
        description="User content database URL",
        alias="USER_DATABASE_URL",
    )
    echo: bool = Field(
        default=False,
        description="Enable SQL query logging",
        alias="DATABASE_ECHO",
    )
    pool_size: int = Field(
        default=5,
        gt=0,
        description="Connection pool size",
        alias="DATABASE_POOL_SIZE",
    )
    max_overflow: int = Field(
        default=10,
        ge=0,
        description="Maximum overflow connections",
        alias="DATABASE_MAX_OVERFLOW",
    )
    pool_timeout: int = Field(
        default=30,
        gt=0,
        description="Pool timeout in seconds",
        alias="DATABASE_POOL_TIMEOUT",
    )
    pool_recycle: int = Field(
        default=3600,
        gt=0,
        description="Connection recycle time in seconds",
        alias="DATABASE_POOL_RECYCLE",
    )
    enable_sqlite_vec: bool = Field(
        default=True,
        description="Enable sqlite-vec extension",
        alias="ENABLE_SQLITE_VEC",
    )
    sqlite_busy_timeout: int = Field(
        default=5000,
        gt=0,
        description="SQLite busy timeout in milliseconds",
        alias="SQLITE_BUSY_TIMEOUT",
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=True,
        populate_by_name=True,
    )


class RAGSettings(BaseSettings):
    """RAG (Retrieval-Augmented Generation) configuration settings."""

    enabled: bool = Field(
        default=True,
        description="Enable RAG system",
        alias="RAG_ENABLED",
    )
    max_results_per_query: int = Field(
        default=3,
        gt=0,
        description="Maximum results per query",
        alias="RAG_MAX_RESULTS_PER_QUERY",
    )
    max_total_results: int = Field(
        default=8,
        gt=0,
        description="Maximum total results",
        alias="RAG_MAX_TOTAL_RESULTS",
    )
    score_threshold: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold",
        alias="RAG_SCORE_THRESHOLD",
    )
    embeddings_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Embeddings model name",
        alias="RAG_EMBEDDINGS_MODEL",
    )
    chunk_size: int = Field(
        default=500,
        gt=0,
        description="Text chunk size",
        alias="RAG_CHUNK_SIZE",
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        description="Chunk overlap size",
        alias="RAG_CHUNK_OVERLAP",
    )
    collection_name_prefix: str = Field(
        default="ai_gamemaster",
        description="Collection name prefix",
        alias="RAG_COLLECTION_NAME_PREFIX",
    )
    metadata_filtering_enabled: bool = Field(
        default=False,
        description="Enable metadata filtering",
        alias="RAG_METADATA_FILTERING_ENABLED",
    )
    relevance_feedback_enabled: bool = Field(
        default=False,
        description="Enable relevance feedback",
        alias="RAG_RELEVANCE_FEEDBACK_ENABLED",
    )
    cache_ttl: int = Field(
        default=3600,
        ge=0,
        description="Cache TTL in seconds",
        alias="RAG_CACHE_TTL",
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=True,
        populate_by_name=True,
    )


class TTSSettings(BaseSettings):
    """Text-to-Speech configuration settings."""

    provider: str = Field(
        default="kokoro",
        description="TTS provider",
        alias="TTS_PROVIDER",
    )
    voice: str = Field(
        default="default",
        description="Default TTS voice",
        alias="TTS_VOICE",
    )
    kokoro_lang_code: str = Field(
        default="a",
        description="Kokoro language code",
        alias="KOKORO_LANG_CODE",
    )
    cache_dir_name: str = Field(
        default="tts_cache",
        description="TTS cache directory name",
        alias="TTS_CACHE_DIR_NAME",
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=True,
        populate_by_name=True,
    )


class StorageSettings(BaseSettings):
    """Storage and repository configuration settings."""

    game_state_repo_type: Literal["memory", "file"] = Field(
        default="memory",
        description="Game state repository type",
        alias="GAME_STATE_REPO_TYPE",
    )
    campaigns_dir: str = Field(
        default="saves/campaigns",
        description="Campaigns directory",
        alias="CAMPAIGNS_DIR",
    )
    character_templates_dir: str = Field(
        default="saves/character_templates",
        description="Character templates directory",
        alias="CHARACTER_TEMPLATES_DIR",
    )
    campaign_templates_dir: str = Field(
        default="saves/campaign_templates",
        description="Campaign templates directory",
        alias="CAMPAIGN_TEMPLATES_DIR",
    )
    saves_dir: str = Field(
        default="saves",
        description="Base saves directory",
        alias="SAVES_DIR",
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=True,
        populate_by_name=True,
    )


class FlaskSettings(BaseSettings):
    """Flask application settings."""

    secret_key: SecretStr = Field(
        default=SecretStr("you-should-change-this"),
        description="Flask secret key",
        alias="SECRET_KEY",
    )
    flask_app: str = Field(
        default="run.py",
        description="Flask application module",
        alias="FLASK_APP",
    )
    flask_debug: bool = Field(
        default=False,
        description="Enable Flask debug mode",
        alias="FLASK_DEBUG",
    )
    testing: bool = Field(
        default=False,
        description="Testing mode",
        alias="TESTING",
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=True,
        populate_by_name=True,
    )


class SSESettings(BaseSettings):
    """Server-Sent Events configuration settings."""

    heartbeat_interval: int = Field(
        default=30,
        gt=0,
        description="Heartbeat interval in seconds",
        alias="SSE_HEARTBEAT_INTERVAL",
    )
    event_timeout: float = Field(
        default=1.0,
        gt=0,
        description="Event timeout in seconds",
        alias="SSE_EVENT_TIMEOUT",
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=True,
        populate_by_name=True,
    )


class SystemSettings(BaseSettings):
    """System-level configuration settings."""

    debug: bool = Field(
        default=False,
        description="Enable debug mode",
        alias="DEBUG",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
        alias="LOG_LEVEL",
    )
    log_file: str = Field(
        default="dnd_ai_poc.log",
        description="Log file name",
        alias="LOG_FILE",
    )
    event_queue_max_size: int = Field(
        default=0,
        ge=0,
        description="Event queue maximum size (0=unlimited)",
        alias="EVENT_QUEUE_MAX_SIZE",
    )

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=True,
        populate_by_name=True,
    )


class Settings(BaseSettings):
    """Main settings class that aggregates all configuration groups."""

    ai: AISettings = Field(default_factory=AISettings)
    prompt: PromptSettings = Field(default_factory=PromptSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    flask: FlaskSettings = Field(default_factory=FlaskSettings)
    sse: SSESettings = Field(default_factory=SSESettings)
    system: SystemSettings = Field(default_factory=SystemSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AIGM_",  # AI GameMaster prefix
        env_nested_delimiter="__",
        case_sensitive=True,
        extra="ignore",
    )

    def __init__(self, **data: Any) -> None:
        """Initialize settings with nested configuration groups."""
        # Initialize each settings group separately to ensure proper env loading
        # Each group will also respect the AIGM_ prefix
        data["ai"] = AISettings()
        data["prompt"] = PromptSettings()
        data["database"] = DatabaseSettings()
        data["rag"] = RAGSettings()
        data["tts"] = TTSSettings()
        data["storage"] = StorageSettings()
        data["flask"] = FlaskSettings()
        data["sse"] = SSESettings()
        data["system"] = SystemSettings()
        super().__init__(**data)

    def validate_config(self) -> None:
        """Validate configuration and warn about potential issues."""
        if self.ai.provider == "openrouter":
            if not self.ai.openrouter_api_key:
                print(
                    "Warning: AI_PROVIDER is 'openrouter' but OPENROUTER_API_KEY is not set."
                )
            if not self.ai.openrouter_model_name:
                print(
                    "Warning: AI_PROVIDER is 'openrouter' but OPENROUTER_MODEL_NAME is not set."
                )
        elif self.ai.provider == "llamacpp_http" and not self.ai.llama_server_url:
            print(
                "Warning: AI_PROVIDER is 'llamacpp_http' but LLAMA_SERVER_URL is not set."
            )

    def to_service_config_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary format expected by ServiceConfigModel."""
        return {
            # AI Settings
            "AI_PROVIDER": self.ai.provider,
            "AI_RESPONSE_PARSING_MODE": self.ai.response_parsing_mode,
            "AI_TEMPERATURE": self.ai.temperature,
            "AI_MAX_TOKENS": self.ai.max_tokens,
            "AI_MAX_RETRIES": self.ai.max_retries,
            "AI_RETRY_DELAY": self.ai.retry_delay,
            "AI_REQUEST_TIMEOUT": int(self.ai.request_timeout),
            "AI_RETRY_CONTEXT_TIMEOUT": self.ai.retry_context_timeout,
            "OPENROUTER_API_KEY": self.ai.openrouter_api_key.get_secret_value()
            if self.ai.openrouter_api_key
            else None,
            "OPENROUTER_MODEL_NAME": self.ai.openrouter_model_name,
            "OPENROUTER_BASE_URL": self.ai.openrouter_base_url,
            "LLAMA_SERVER_URL": self.ai.llama_server_url,
            "MAX_AI_CONTINUATION_DEPTH": self.ai.max_continuation_depth,
            # Prompt Settings
            "MAX_PROMPT_TOKENS_BUDGET": self.prompt.max_tokens_budget,
            "LAST_X_HISTORY_MESSAGES": self.prompt.last_x_history_messages,
            "TOKENS_PER_MESSAGE_OVERHEAD": self.prompt.tokens_per_message_overhead,
            # Database Settings
            "DATABASE_URL": self.database.url.get_secret_value(),
            "DATABASE_ECHO": self.database.echo,
            "DATABASE_POOL_SIZE": self.database.pool_size,
            "DATABASE_MAX_OVERFLOW": self.database.max_overflow,
            "DATABASE_POOL_TIMEOUT": self.database.pool_timeout,
            "DATABASE_POOL_RECYCLE": self.database.pool_recycle,
            "ENABLE_SQLITE_VEC": self.database.enable_sqlite_vec,
            "SQLITE_BUSY_TIMEOUT": self.database.sqlite_busy_timeout,
            # RAG Settings
            "RAG_ENABLED": self.rag.enabled,
            "RAG_MAX_RESULTS_PER_QUERY": self.rag.max_results_per_query,
            "RAG_MAX_TOTAL_RESULTS": self.rag.max_total_results,
            "RAG_SCORE_THRESHOLD": self.rag.score_threshold,
            "RAG_EMBEDDINGS_MODEL": self.rag.embeddings_model,
            "RAG_CHUNK_SIZE": self.rag.chunk_size,
            "RAG_CHUNK_OVERLAP": self.rag.chunk_overlap,
            "RAG_COLLECTION_NAME_PREFIX": self.rag.collection_name_prefix,
            "RAG_METADATA_FILTERING_ENABLED": self.rag.metadata_filtering_enabled,
            "RAG_RELEVANCE_FEEDBACK_ENABLED": self.rag.relevance_feedback_enabled,
            "RAG_CACHE_TTL": self.rag.cache_ttl,
            # TTS Settings
            "TTS_PROVIDER": self.tts.provider,
            "TTS_VOICE": self.tts.voice,
            "KOKORO_LANG_CODE": self.tts.kokoro_lang_code,
            "TTS_CACHE_DIR_NAME": self.tts.cache_dir_name,
            # Storage Settings
            "GAME_STATE_REPO_TYPE": self.storage.game_state_repo_type,
            "CAMPAIGNS_DIR": self.storage.campaigns_dir,
            "CHARACTER_TEMPLATES_DIR": self.storage.character_templates_dir,
            "CAMPAIGN_TEMPLATES_DIR": self.storage.campaign_templates_dir,
            "SAVES_DIR": self.storage.saves_dir,
            # Flask Settings
            "SECRET_KEY": self.flask.secret_key.get_secret_value(),
            "FLASK_APP": self.flask.flask_app,
            "FLASK_DEBUG": self.flask.flask_debug,
            "TESTING": self.flask.testing,
            # SSE Settings
            "SSE_HEARTBEAT_INTERVAL": self.sse.heartbeat_interval,
            "SSE_EVENT_TIMEOUT": self.sse.event_timeout,
            # System Settings
            "DEBUG": self.system.debug,
            "LOG_LEVEL": self.system.log_level,
            "LOG_FILE": self.system.log_file,
            "EVENT_QUEUE_MAX_SIZE": self.system.event_queue_max_size,
        }


# Create a singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.validate_config()
    return _settings
