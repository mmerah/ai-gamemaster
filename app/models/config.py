"""
Configuration models.

This module contains all configuration-related models.
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ServiceConfigModel(BaseModel):
    """Complete service configuration structure."""

    # AI Provider Settings
    AI_PROVIDER: str = Field(default="llamacpp_http")
    AI_RESPONSE_PARSING_MODE: str = Field(default="strict")
    AI_TEMPERATURE: float = Field(default=0.7)
    AI_MAX_TOKENS: int = Field(default=4096)

    # AI Retry Configuration
    AI_MAX_RETRIES: int = Field(default=3)
    AI_RETRY_DELAY: float = Field(default=5.0)
    AI_REQUEST_TIMEOUT: int = Field(default=60)
    AI_RETRY_CONTEXT_TIMEOUT: int = Field(default=300)

    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL_NAME: Optional[str] = None
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")

    # Llama.cpp HTTP Server
    LLAMA_SERVER_URL: str = Field(default="http://127.0.0.1:8080")

    # Prompt Builder Configuration
    MAX_PROMPT_TOKENS_BUDGET: int = Field(default=128000)
    LAST_X_HISTORY_MESSAGES: int = Field(default=4)
    TOKENS_PER_MESSAGE_OVERHEAD: int = Field(default=4)

    # Auto-continuation Configuration
    MAX_AI_CONTINUATION_DEPTH: int = Field(default=20)

    # RAG Settings
    RAG_ENABLED: bool = Field(default=True)
    RAG_MAX_RESULTS_PER_QUERY: int = Field(default=3)
    RAG_MAX_TOTAL_RESULTS: int = Field(default=8)
    RAG_SCORE_THRESHOLD: float = Field(default=0.2)
    RAG_EMBEDDINGS_MODEL: str = Field(default="all-MiniLM-L6-v2")
    RAG_CHUNK_SIZE: int = Field(default=500)
    RAG_CHUNK_OVERLAP: int = Field(default=50)
    RAG_COLLECTION_NAME_PREFIX: str = Field(default="ai_gamemaster")
    RAG_METADATA_FILTERING_ENABLED: bool = Field(default=False)
    RAG_RELEVANCE_FEEDBACK_ENABLED: bool = Field(default=False)
    RAG_CACHE_TTL: int = Field(default=3600)

    # TTS Settings
    TTS_PROVIDER: str = Field(default="kokoro")
    TTS_VOICE: str = Field(default="default")
    KOKORO_LANG_CODE: str = Field(default="a")
    TTS_CACHE_DIR_NAME: str = Field(default="tts_cache")

    # Repository and Directory Settings
    GAME_STATE_REPO_TYPE: str = Field(default="memory")
    CAMPAIGNS_DIR: str = Field(default="saves/campaigns")
    CHARACTER_TEMPLATES_DIR: str = Field(default="saves/character_templates")
    CAMPAIGN_TEMPLATES_DIR: str = Field(default="saves/campaign_templates")
    SAVES_DIR: str = Field(default="saves")

    # Database Configuration
    DATABASE_URL: str = Field(default="sqlite:///data/content.db")
    DATABASE_ECHO: bool = Field(default=False)
    DATABASE_POOL_SIZE: int = Field(default=5)
    DATABASE_MAX_OVERFLOW: int = Field(default=10)
    DATABASE_POOL_TIMEOUT: int = Field(default=30)
    DATABASE_POOL_RECYCLE: int = Field(default=3600)
    ENABLE_SQLITE_VEC: bool = Field(default=True)

    # Event Queue Settings
    EVENT_QUEUE_MAX_SIZE: int = Field(default=0)

    # Flask Configuration
    SECRET_KEY: str = Field(default="you-should-change-this")
    FLASK_APP: str = Field(default="run.py")
    FLASK_DEBUG: bool = Field(default=False)
    TESTING: bool = Field(default=False)

    # Server-Sent Events (SSE) Configuration
    SSE_HEARTBEAT_INTERVAL: int = Field(default=30)
    SSE_EVENT_TIMEOUT: float = Field(default=1.0)

    # System Settings
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="dnd_ai_poc.log")

    # Special field for tests - not serialized
    AI_SERVICE: Optional[Any] = Field(default=None, exclude=True)

    model_config = ConfigDict(extra="ignore")
