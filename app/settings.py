"""
Pydantic Settings for AI Game Master application.

This module uses pydantic-settings to provide type-safe configuration management
with environment variable support and validation.
"""

import os
from typing import Any, Dict, Literal, Optional

from pydantic import Field, SecretStr, field_validator, model_serializer
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


class Settings(BaseSettings):
    """Main settings class that aggregates all configuration groups."""

    ai: AISettings = Field(default_factory=lambda: AISettings())
    prompt: PromptSettings = Field(default_factory=lambda: PromptSettings())
    database: DatabaseSettings = Field(default_factory=lambda: DatabaseSettings())
    rag: RAGSettings = Field(default_factory=lambda: RAGSettings())
    tts: TTSSettings = Field(default_factory=lambda: TTSSettings())
    storage: StorageSettings = Field(default_factory=lambda: StorageSettings())
    sse: SSESettings = Field(default_factory=lambda: SSESettings())
    system: SystemSettings = Field(default_factory=lambda: SystemSettings())

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=True,
        extra="ignore",
        # Configure serialization to use field names, not aliases
        populate_by_name=True,
        use_enum_values=True,
    )

    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """Custom serializer to ensure all nested models use field names, not aliases."""
        return {
            "ai": self.ai.model_dump(by_alias=False),
            "prompt": self.prompt.model_dump(by_alias=False),
            "database": self.database.model_dump(by_alias=False),
            "rag": self.rag.model_dump(by_alias=False),
            "tts": self.tts.model_dump(by_alias=False),
            "storage": self.storage.model_dump(by_alias=False),
            "sse": self.sse.model_dump(by_alias=False),
            "system": self.system.model_dump(by_alias=False),
        }

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


# Create a singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.validate_config()
    return _settings
