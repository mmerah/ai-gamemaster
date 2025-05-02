import logging
from app.ai_services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

def get_ai_service(config):
    """Factory function to get the configured AI service instance."""
    provider = config.get('AI_PROVIDER', '').lower()
    api_key = None
    base_url = None
    model_name = None

    if provider == 'llamacpp_http':
        logger.info("Configuring OpenAIService for Llama.cpp HTTP Server...")
        # API key might not be needed for local server
        api_key = config.get('LLAMA_SERVER_API_KEY') # Add if your server needs one
        base_url = config.get('LLAMA_SERVER_URL')
        # llama-server uses the path in the request, not a specific model name here
        # but instructor needs *a* model name, use a placeholder or config
        model_name = config.get('LLAMA_SERVER_MODEL_PLACEHOLDER', 'local-llamacpp-model')
        if not base_url:
            logger.error("LLAMA_SERVER_URL is not configured for llamacpp_http provider.")
            return None
        # Ensure v1 suffix for OpenAI compatibility if not already present
        if not base_url.endswith('/v1'):
            base_url = base_url.rstrip('/') + '/v1'
            logger.debug(f"Appended /v1 to LLAMA_SERVER_URL: {base_url}")


    elif provider == 'openrouter':
        logger.info("Configuring OpenAIService for OpenRouter...")
        api_key = config.get('OPENROUTER_API_KEY')
        base_url = config.get('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1') # Default OpenRouter URL
        model_name = config.get('OPENROUTER_MODEL_NAME')
        if not api_key:
            logger.error("OPENROUTER_API_KEY is not configured for openrouter provider.")
            return None
        if not model_name:
            logger.error("OPENROUTER_MODEL_NAME is not configured for openrouter provider.")
            return None

    elif provider == 'openai':
        logger.info("Configuring OpenAIService for OpenAI...")
        api_key = config.get('OPENAI_API_KEY') # Add OPENAI_API_KEY to config/.env
        base_url = config.get('OPENAI_BASE_URL') # Optional: for Azure etc. Defaults to OpenAI
        model_name = config.get('OPENAI_MODEL_NAME', 'gpt-4o-mini') # Add OPENAI_MODEL_NAME
        if not api_key:
            logger.error("OPENAI_API_KEY is not configured for openai provider.")
            return None

    else:
        logger.error(f"Unknown or unsupported AI_PROVIDER '{provider}'. AI will be disabled.")
        return None

    try:
        # Instantiate the single service type
        return OpenAIService(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )
    except Exception as e:
        logger.critical(f"Failed to initialize OpenAIService for provider '{provider}': {e}", exc_info=True)
        return None