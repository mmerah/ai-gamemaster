"""Configuration routes for exposing safe-to-view settings - FastAPI version."""

import os
from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.api.dependencies_fastapi import get_settings
from app.settings import Settings

# Create router for config API routes
router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
async def get_configuration(
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Get safe-to-view configuration settings."""
    # Define which configuration keys are safe to expose
    safe_config_keys = [
        # AI Settings
        "AI_PROVIDER",
        "AI_RESPONSE_PARSING_MODE",
        "AI_MAX_RETRIES",
        "AI_RETRY_DELAY",
        "AI_REQUEST_TIMEOUT",
        "AI_RETRY_CONTEXT_TIMEOUT",
        "AI_TEMPERATURE",
        "AI_MAX_TOKENS",
        "LLAMA_SERVER_URL",
        "OPENROUTER_MODEL_NAME",
        "OPENROUTER_BASE_URL",
        # Token Budget
        "MAX_PROMPT_TOKENS_BUDGET",
        "LAST_X_HISTORY_MESSAGES",
        "MAX_AI_CONTINUATION_DEPTH",
        "TOKENS_PER_MESSAGE_OVERHEAD",
        # Storage Settings
        "GAME_STATE_REPO_TYPE",
        "CHARACTER_TEMPLATES_DIR",
        "CAMPAIGN_TEMPLATES_DIR",
        "CAMPAIGNS_DIR",
        # Feature Flags
        "RAG_ENABLED",
        "TTS_PROVIDER",
        "TTS_CACHE_DIR_NAME",
        "KOKORO_LANG_CODE",
        "FLASK_DEBUG",
        # RAG Settings
        "RAG_MAX_RESULTS_PER_QUERY",
        "RAG_EMBEDDINGS_MODEL",
        "RAG_SCORE_THRESHOLD",
        "RAG_MAX_TOTAL_RESULTS",
        "RAG_CHUNK_SIZE",
        "RAG_CHUNK_OVERLAP",
        "RAG_COLLECTION_NAME_PREFIX",
        "RAG_METADATA_FILTERING_ENABLED",
        "RAG_RELEVANCE_FEEDBACK_ENABLED",
        "RAG_CACHE_TTL",
        # SSE Settings
        "SSE_HEARTBEAT_INTERVAL",
        "SSE_EVENT_TIMEOUT",
        "EVENT_QUEUE_MAX_SIZE",
        # Logging
        "LOG_LEVEL",
        "LOG_FILE",
    ]

    # Extract safe configuration values
    config_data: Dict[str, Any] = {}

    # Map settings attributes to the legacy environment variable names
    settings_mapping = {
        # AI Settings
        "AI_PROVIDER": settings.ai.provider,
        "AI_RESPONSE_PARSING_MODE": settings.ai.response_parsing_mode,
        "AI_MAX_RETRIES": settings.ai.max_retries,
        "AI_RETRY_DELAY": settings.ai.retry_delay,
        "AI_REQUEST_TIMEOUT": settings.ai.request_timeout,
        "AI_RETRY_CONTEXT_TIMEOUT": settings.ai.retry_context_timeout,
        "AI_TEMPERATURE": settings.ai.temperature,
        "AI_MAX_TOKENS": settings.ai.max_tokens,
        "LLAMA_SERVER_URL": settings.ai.llama_server_url,
        "OPENROUTER_MODEL_NAME": settings.ai.openrouter_model_name,
        "OPENROUTER_BASE_URL": settings.ai.openrouter_base_url,
        # Token Budget (from prompt settings)
        "MAX_PROMPT_TOKENS_BUDGET": settings.prompt.max_tokens_budget,
        "LAST_X_HISTORY_MESSAGES": settings.prompt.last_x_history_messages,
        "MAX_AI_CONTINUATION_DEPTH": settings.ai.max_continuation_depth,
        "TOKENS_PER_MESSAGE_OVERHEAD": settings.prompt.tokens_per_message_overhead,
        # Storage Settings
        "GAME_STATE_REPO_TYPE": settings.storage.game_state_repo_type,
        "CHARACTER_TEMPLATES_DIR": settings.storage.character_templates_dir,
        "CAMPAIGN_TEMPLATES_DIR": settings.storage.campaign_templates_dir,
        "CAMPAIGNS_DIR": settings.storage.campaigns_dir,
        # Feature Flags
        "RAG_ENABLED": settings.rag.enabled,
        "TTS_PROVIDER": settings.tts.provider,
        "TTS_CACHE_DIR_NAME": settings.tts.cache_dir_name,
        "KOKORO_LANG_CODE": settings.tts.kokoro_lang_code,
        "FLASK_DEBUG": settings.flask.flask_debug,
        # RAG Settings
        "RAG_MAX_RESULTS_PER_QUERY": settings.rag.max_results_per_query,
        "RAG_EMBEDDINGS_MODEL": settings.rag.embeddings_model,
        "RAG_SCORE_THRESHOLD": settings.rag.score_threshold,
        "RAG_MAX_TOTAL_RESULTS": settings.rag.max_total_results,
        "RAG_CHUNK_SIZE": settings.rag.chunk_size,
        "RAG_CHUNK_OVERLAP": settings.rag.chunk_overlap,
        "RAG_COLLECTION_NAME_PREFIX": settings.rag.collection_name_prefix,
        "RAG_METADATA_FILTERING_ENABLED": settings.rag.metadata_filtering_enabled,
        "RAG_RELEVANCE_FEEDBACK_ENABLED": settings.rag.relevance_feedback_enabled,
        "RAG_CACHE_TTL": settings.rag.cache_ttl,
        # SSE Settings
        "SSE_HEARTBEAT_INTERVAL": settings.sse.heartbeat_interval,
        "SSE_EVENT_TIMEOUT": settings.sse.event_timeout,
        "EVENT_QUEUE_MAX_SIZE": settings.system.event_queue_max_size,
        # Logging
        "LOG_LEVEL": settings.system.log_level,
        "LOG_FILE": settings.system.log_file,
    }

    for key in safe_config_keys:
        if key in settings_mapping:
            value = settings_mapping[key]
            # Convert Path objects to strings for JSON serialization
            if hasattr(value, "__fspath__"):
                value = str(value)
            config_data[key] = value
        # Also check environment variables directly for values not in settings
        elif key in os.environ:
            config_data[key] = os.environ[key]

    # Add some computed/derived values
    config_data["VERSION"] = "1.0.0"  # Could be read from a VERSION file
    config_data["ENVIRONMENT"] = (
        "development" if settings.flask.flask_debug else "production"
    )

    return {"success": True, "config": config_data}
