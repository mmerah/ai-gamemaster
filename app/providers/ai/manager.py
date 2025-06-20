import logging
from typing import Optional, cast

from app.providers.ai.base import BaseAIService
from app.providers.ai.openai_service import OpenAIService
from app.settings import Settings

logger = logging.getLogger(__name__)


def get_ai_service(settings: Settings) -> Optional[BaseAIService]:
    """Factory function to get the configured AI service instance."""
    provider = settings.ai.provider.lower()
    parsing_mode = settings.ai.response_parsing_mode
    api_key = None
    base_url = None
    model_name = None

    logger.debug(
        f"Attempting to configure AI provider: '{provider}', Parsing Mode: '{parsing_mode}'"
    )

    if provider == "llamacpp_http":
        logger.info("Configuring OpenAIService for Llama.cpp HTTP Server...")
        # API key might not be needed for local server
        api_key = None  # Not in settings
        base_url = settings.ai.llama_server_url
        model_name = "local-llamacpp-model"  # Default placeholder
        if not base_url:
            logger.error(
                "LLAMA_SERVER_URL is not configured for llamacpp_http provider."
            )
            return None
        # Ensure v1 suffix for OpenAI compatibility if not already present
        if not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"
            logger.debug(f"Appended /v1 to LLAMA_SERVER_URL: {base_url}")

    elif provider == "openrouter":
        logger.info("Configuring OpenAIService for OpenRouter...")
        api_key = (
            settings.ai.openrouter_api_key.get_secret_value()
            if settings.ai.openrouter_api_key
            else None
        )
        base_url = settings.ai.openrouter_base_url
        model_name = settings.ai.openrouter_model_name
        if not api_key:
            logger.error(
                "OPENROUTER_API_KEY is not configured for openrouter provider."
            )
            return None
        if not model_name:
            logger.error(
                "OPENROUTER_MODEL_NAME is not configured for openrouter provider."
            )
            return None

    else:
        logger.error(
            f"Unknown or unsupported AI_PROVIDER '{provider}'. AI will be disabled."
        )
        return None

    try:
        # Get temperature from settings
        temperature = settings.ai.temperature
        return OpenAIService(
            settings=settings,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            parsing_mode=parsing_mode,
            temperature=temperature,
        )
    except Exception as e:
        logger.critical(
            f"Failed to initialize OpenAIService for provider '{provider}': {e}",
            exc_info=True,
        )
        return None
