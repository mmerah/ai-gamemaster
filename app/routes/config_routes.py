"""Configuration routes for exposing safe-to-view settings."""
from flask import Blueprint, jsonify, current_app
import os

config_bp = Blueprint('config', __name__, url_prefix='/api')

@config_bp.route('/config', methods=['GET'])
def get_configuration():
    """Get safe-to-view configuration settings."""
    # Define which configuration keys are safe to expose
    safe_config_keys = [
        # AI Settings
        'AI_PROVIDER',
        'AI_RESPONSE_PARSING_MODE',
        'AI_MAX_RETRIES',
        'AI_RETRY_DELAY',
        'AI_REQUEST_TIMEOUT',
        'AI_RETRY_CONTEXT_TIMEOUT',
        'AI_TEMPERATURE',
        'AI_MAX_TOKENS',
        'LLAMA_SERVER_URL',
        'OPENROUTER_MODEL_NAME',
        'OPENROUTER_BASE_URL',
        
        # Token Budget
        'MAX_PROMPT_TOKENS_BUDGET',
        'LAST_X_HISTORY_MESSAGES',
        'MAX_AI_CONTINUATION_DEPTH',
        'TOKENS_PER_MESSAGE_OVERHEAD',
        
        # Storage Settings
        'GAME_STATE_REPO_TYPE',
        'CHARACTER_TEMPLATES_DIR',
        'CAMPAIGN_TEMPLATES_DIR',
        'CAMPAIGNS_DIR',
        
        # Feature Flags
        'RAG_ENABLED',
        'TTS_PROVIDER',
        'TTS_CACHE_DIR_NAME',
        'KOKORO_LANG_CODE',
        'FLASK_DEBUG',
        
        # RAG Settings
        'RAG_MAX_RESULTS_PER_QUERY',
        'RAG_EMBEDDINGS_MODEL',
        'RAG_SCORE_THRESHOLD',
        'RAG_MAX_TOTAL_RESULTS',
        'RAG_CHUNK_SIZE',
        'RAG_CHUNK_OVERLAP',
        'RAG_COLLECTION_NAME_PREFIX',
        'RAG_METADATA_FILTERING_ENABLED',
        'RAG_RELEVANCE_FEEDBACK_ENABLED',
        'RAG_CACHE_TTL',
        
        # SSE Settings
        'SSE_HEARTBEAT_INTERVAL',
        'SSE_EVENT_TIMEOUT',
        'EVENT_QUEUE_MAX_SIZE',
        
        # Logging
        'LOG_LEVEL',
        'LOG_FILE',
    ]
    
    # Extract safe configuration values
    config_data = {}
    for key in safe_config_keys:
        # Check if the key exists in Flask config
        if key in current_app.config:
            value = current_app.config[key]
            # Convert Path objects to strings for JSON serialization
            if hasattr(value, '__fspath__'):
                value = str(value)
            config_data[key] = value
        # Also check environment variables directly for values not in Flask config
        elif key in os.environ:
            config_data[key] = os.environ[key]
    
    # Add some computed/derived values
    config_data['VERSION'] = '1.0.0'  # Could be read from a VERSION file
    config_data['ENVIRONMENT'] = 'development' if current_app.config.get('FLASK_DEBUG') else 'production'
    
    return jsonify({
        'success': True,
        'config': config_data
    })