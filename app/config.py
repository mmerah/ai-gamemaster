import os
from typing import TYPE_CHECKING, Any, Dict, Optional

from dotenv import load_dotenv

if TYPE_CHECKING:
    from app.models import ServiceConfigModel

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}")


class Config:
    # AI Configuration
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "llamacpp_http")
    # Parsing mode ('strict' uses instructor JSON mode, 'flexible' extracts JSON from text)
    AI_RESPONSE_PARSING_MODE: str = os.getenv(
        "AI_RESPONSE_PARSING_MODE", "strict"
    ).lower()
    # Temperature setting for AI responses (0.0-2.0, higher = more creative)
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    # Maximum tokens for AI responses
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "4096"))

    # AI Retry Configuration
    AI_MAX_RETRIES: int = int(os.getenv("AI_MAX_RETRIES", "3"))
    AI_RETRY_DELAY: float = float(os.getenv("AI_RETRY_DELAY", "5.0"))
    AI_REQUEST_TIMEOUT: float = float(os.getenv("AI_REQUEST_TIMEOUT", "60.0"))
    AI_RETRY_CONTEXT_TIMEOUT: int = int(os.getenv("AI_RETRY_CONTEXT_TIMEOUT", "300"))

    # OpenRouter Config
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL_NAME: Optional[str] = os.getenv("OPENROUTER_MODEL_NAME")
    OPENROUTER_BASE_URL: str = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )

    # Llama.cpp HTTP Server Config
    LLAMA_SERVER_URL: str = os.getenv("LLAMA_SERVER_URL", "http://127.0.0.1:8080")

    # Prompt Builder Configuration
    MAX_PROMPT_TOKENS_BUDGET: int = int(os.getenv("MAX_PROMPT_TOKENS_BUDGET", "128000"))
    LAST_X_HISTORY_MESSAGES: int = int(os.getenv("LAST_X_HISTORY_MESSAGES", "4"))
    TOKENS_PER_MESSAGE_OVERHEAD: int = int(
        os.getenv("TOKENS_PER_MESSAGE_OVERHEAD", "4")
    )

    # Auto-continuation Configuration
    MAX_AI_CONTINUATION_DEPTH: int = int(os.getenv("MAX_AI_CONTINUATION_DEPTH", "20"))

    # RAG Settings
    RAG_ENABLED: bool = os.getenv("RAG_ENABLED", "true").lower() in (
        "true",
        "1",
        "t",
        "yes",
    )
    RAG_MAX_RESULTS_PER_QUERY: int = int(os.getenv("RAG_MAX_RESULTS_PER_QUERY", "3"))
    RAG_MAX_TOTAL_RESULTS: int = int(os.getenv("RAG_MAX_TOTAL_RESULTS", "8"))
    RAG_SCORE_THRESHOLD: float = float(os.getenv("RAG_SCORE_THRESHOLD", "0.2"))
    RAG_EMBEDDINGS_MODEL: str = os.getenv("RAG_EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
    RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "500"))
    RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
    RAG_COLLECTION_NAME_PREFIX: str = os.getenv(
        "RAG_COLLECTION_NAME_PREFIX", "ai_gamemaster"
    )
    RAG_METADATA_FILTERING_ENABLED: bool = os.getenv(
        "RAG_METADATA_FILTERING_ENABLED", "false"
    ).lower() in ("true", "1", "t", "yes")
    RAG_RELEVANCE_FEEDBACK_ENABLED: bool = os.getenv(
        "RAG_RELEVANCE_FEEDBACK_ENABLED", "false"
    ).lower() in ("true", "1", "t", "yes")
    RAG_CACHE_TTL: int = int(os.getenv("RAG_CACHE_TTL", "3600"))

    # TTS Settings
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "kokoro")  # 'kokoro', 'none', etc.
    TTS_VOICE: str = os.getenv("TTS_VOICE", "default")  # Default TTS voice
    KOKORO_LANG_CODE: str = os.getenv(
        "KOKORO_LANG_CODE", "a"
    )  # 'a' for American English, 'b' for British etc.
    TTS_CACHE_DIR_NAME: str = os.getenv(
        "TTS_CACHE_DIR_NAME", "tts_cache"
    )  # Subdirectory within static folder

    # Repository Configuration
    # Controls which repository implementation to use for game state persistence
    # Options: 'memory' (in-memory, lost on restart), 'file' (JSON files), 'database' (future)
    GAME_STATE_REPO_TYPE: str = os.getenv("GAME_STATE_REPO_TYPE", "memory")
    CAMPAIGNS_DIR: str = os.getenv("CAMPAIGNS_DIR", "saves/campaigns")
    CHARACTER_TEMPLATES_DIR: str = os.getenv(
        "CHARACTER_TEMPLATES_DIR", "saves/character_templates"
    )
    CAMPAIGN_TEMPLATES_DIR: str = os.getenv(
        "CAMPAIGN_TEMPLATES_DIR", "saves/campaign_templates"
    )
    SAVES_DIR: str = os.getenv("SAVES_DIR", "saves")

    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/content.db")
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "False").lower() in (
        "true",
        "1",
        "t",
        "yes",
    )
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    DATABASE_POOL_TIMEOUT: int = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
    ENABLE_SQLITE_VEC: bool = os.getenv("ENABLE_SQLITE_VEC", "true").lower() in (
        "true",
        "1",
        "t",
        "yes",
    )
    SQLITE_BUSY_TIMEOUT: int = int(os.getenv("SQLITE_BUSY_TIMEOUT", "5000"))

    # Event Queue Configuration
    EVENT_QUEUE_MAX_SIZE: int = int(os.getenv("EVENT_QUEUE_MAX_SIZE", "0"))

    # Flask Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "you-should-change-this")
    FLASK_APP: str = os.getenv("FLASK_APP", "run.py")
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1", "t")

    # Server-Sent Events (SSE) Configuration
    SSE_HEARTBEAT_INTERVAL: int = int(os.getenv("SSE_HEARTBEAT_INTERVAL", "30"))
    SSE_EVENT_TIMEOUT: float = float(os.getenv("SSE_EVENT_TIMEOUT", "1.0"))

    # Basic validation
    if AI_PROVIDER == "openrouter":
        if not OPENROUTER_API_KEY:
            print(
                "Warning: AI_PROVIDER is 'openrouter' but OPENROUTER_API_KEY is not set."
            )
        if not OPENROUTER_MODEL_NAME:
            print(
                "Warning: AI_PROVIDER is 'openrouter' but OPENROUTER_MODEL_NAME is not set."
            )
    if AI_PROVIDER == "llamacpp_http" and not LLAMA_SERVER_URL:
        print(
            "Warning: AI_PROVIDER is 'llamacpp_http' but LLAMA_SERVER_URL is not set."
        )
    if AI_RESPONSE_PARSING_MODE not in ["strict", "flexible"]:
        print(
            f"Warning: Invalid AI_RESPONSE_PARSING_MODE '{AI_RESPONSE_PARSING_MODE}'. Defaulting to 'strict'."
        )
        AI_RESPONSE_PARSING_MODE = "strict"

    # Logging Configuration
    # Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "dnd_ai_poc.log")


def create_service_config_from_flask(
    flask_config: Dict[str, Any],
) -> "ServiceConfigModel":
    """Convert Flask config dictionary to ServiceConfigModel for type safety."""
    # Extract all relevant config values from Flask config
    config_data = {
        # AI Provider Settings
        "AI_PROVIDER": flask_config.get("AI_PROVIDER", "llamacpp_http"),
        "AI_RESPONSE_PARSING_MODE": flask_config.get(
            "AI_RESPONSE_PARSING_MODE", "strict"
        ),
        "AI_TEMPERATURE": flask_config.get("AI_TEMPERATURE", 0.7),
        "AI_MAX_TOKENS": flask_config.get("AI_MAX_TOKENS", 4096),
        # AI Retry Configuration
        "AI_MAX_RETRIES": flask_config.get("AI_MAX_RETRIES", 3),
        "AI_RETRY_DELAY": flask_config.get("AI_RETRY_DELAY", 5.0),
        "AI_REQUEST_TIMEOUT": flask_config.get("AI_REQUEST_TIMEOUT", 60),
        "AI_RETRY_CONTEXT_TIMEOUT": flask_config.get("AI_RETRY_CONTEXT_TIMEOUT", 300),
        # OpenRouter
        "OPENROUTER_API_KEY": flask_config.get("OPENROUTER_API_KEY"),
        "OPENROUTER_MODEL_NAME": flask_config.get("OPENROUTER_MODEL_NAME"),
        "OPENROUTER_BASE_URL": flask_config.get(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        # Llama.cpp HTTP Server
        "LLAMA_SERVER_URL": flask_config.get(
            "LLAMA_SERVER_URL", "http://127.0.0.1:8080"
        ),
        # Prompt Builder Configuration
        "MAX_PROMPT_TOKENS_BUDGET": flask_config.get(
            "MAX_PROMPT_TOKENS_BUDGET", 128000
        ),
        "LAST_X_HISTORY_MESSAGES": flask_config.get("LAST_X_HISTORY_MESSAGES", 4),
        "TOKENS_PER_MESSAGE_OVERHEAD": flask_config.get(
            "TOKENS_PER_MESSAGE_OVERHEAD", 4
        ),
        # Auto-continuation Configuration
        "MAX_AI_CONTINUATION_DEPTH": flask_config.get("MAX_AI_CONTINUATION_DEPTH", 20),
        # RAG Settings
        "RAG_ENABLED": flask_config.get("RAG_ENABLED", True),
        "RAG_MAX_RESULTS_PER_QUERY": flask_config.get("RAG_MAX_RESULTS_PER_QUERY", 3),
        "RAG_MAX_TOTAL_RESULTS": flask_config.get("RAG_MAX_TOTAL_RESULTS", 8),
        "RAG_SCORE_THRESHOLD": flask_config.get("RAG_SCORE_THRESHOLD", 0.2),
        "RAG_EMBEDDINGS_MODEL": flask_config.get(
            "RAG_EMBEDDINGS_MODEL", "all-MiniLM-L6-v2"
        ),
        "RAG_CHUNK_SIZE": flask_config.get("RAG_CHUNK_SIZE", 500),
        "RAG_CHUNK_OVERLAP": flask_config.get("RAG_CHUNK_OVERLAP", 50),
        "RAG_COLLECTION_NAME_PREFIX": flask_config.get(
            "RAG_COLLECTION_NAME_PREFIX", "ai_gamemaster"
        ),
        "RAG_METADATA_FILTERING_ENABLED": flask_config.get(
            "RAG_METADATA_FILTERING_ENABLED", False
        ),
        "RAG_RELEVANCE_FEEDBACK_ENABLED": flask_config.get(
            "RAG_RELEVANCE_FEEDBACK_ENABLED", False
        ),
        "RAG_CACHE_TTL": flask_config.get("RAG_CACHE_TTL", 3600),
        # TTS Settings
        "TTS_PROVIDER": flask_config.get("TTS_PROVIDER", "kokoro"),
        "TTS_VOICE": flask_config.get("TTS_VOICE", "default"),
        "KOKORO_LANG_CODE": flask_config.get("KOKORO_LANG_CODE", "a"),
        "TTS_CACHE_DIR_NAME": flask_config.get("TTS_CACHE_DIR_NAME", "tts_cache"),
        # Repository and Directory Settings
        "GAME_STATE_REPO_TYPE": flask_config.get("GAME_STATE_REPO_TYPE", "memory"),
        "CAMPAIGNS_DIR": flask_config.get("CAMPAIGNS_DIR", "saves/campaigns"),
        "CHARACTER_TEMPLATES_DIR": flask_config.get(
            "CHARACTER_TEMPLATES_DIR", "saves/character_templates"
        ),
        "CAMPAIGN_TEMPLATES_DIR": flask_config.get(
            "CAMPAIGN_TEMPLATES_DIR", "saves/campaign_templates"
        ),
        "SAVES_DIR": flask_config.get("SAVES_DIR", "saves"),
        # Database Configuration
        "DATABASE_URL": flask_config.get("DATABASE_URL", "sqlite:///data/content.db"),
        "DATABASE_ECHO": flask_config.get("DATABASE_ECHO", False),
        "DATABASE_POOL_SIZE": flask_config.get("DATABASE_POOL_SIZE", 5),
        "DATABASE_MAX_OVERFLOW": flask_config.get("DATABASE_MAX_OVERFLOW", 10),
        "DATABASE_POOL_TIMEOUT": flask_config.get("DATABASE_POOL_TIMEOUT", 30),
        "DATABASE_POOL_RECYCLE": flask_config.get("DATABASE_POOL_RECYCLE", 3600),
        "ENABLE_SQLITE_VEC": flask_config.get("ENABLE_SQLITE_VEC", True),
        "SQLITE_BUSY_TIMEOUT": flask_config.get("SQLITE_BUSY_TIMEOUT", 5000),
        # Event Queue Settings
        "EVENT_QUEUE_MAX_SIZE": flask_config.get("EVENT_QUEUE_MAX_SIZE", 0),
        # Flask Configuration
        "SECRET_KEY": flask_config.get("SECRET_KEY", "you-should-change-this"),
        "FLASK_APP": flask_config.get("FLASK_APP", "run.py"),
        "FLASK_DEBUG": flask_config.get("FLASK_DEBUG", False),
        "TESTING": flask_config.get("TESTING", False),
        # Server-Sent Events (SSE) Configuration
        "SSE_HEARTBEAT_INTERVAL": flask_config.get("SSE_HEARTBEAT_INTERVAL", 30),
        "SSE_EVENT_TIMEOUT": flask_config.get("SSE_EVENT_TIMEOUT", 1.0),
        # System Settings
        "DEBUG": flask_config.get("DEBUG", False),
        "LOG_LEVEL": flask_config.get("LOG_LEVEL", "INFO"),
        "LOG_FILE": flask_config.get("LOG_FILE", "dnd_ai_poc.log"),
    }

    # Import here to avoid circular import
    from app.models import ServiceConfigModel

    return ServiceConfigModel(**config_data)
