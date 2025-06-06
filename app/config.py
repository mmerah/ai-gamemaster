import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"Warning: .env file not found at {dotenv_path}")

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'you-should-change-this')
    FLASK_APP = os.getenv('FLASK_APP', 'run.py')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

    # AI Configuration
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'llamacpp_http')
    # Parsing mode ('strict' uses instructor JSON mode, 'flexible' extracts JSON from text)
    AI_RESPONSE_PARSING_MODE = os.getenv('AI_RESPONSE_PARSING_MODE', 'strict').lower()
    # Temperature setting for AI responses (0.0-2.0, higher = more creative)
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', '0.7'))
    # Maximum tokens for AI responses
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', '4096'))
    
    # AI Retry Configuration
    AI_MAX_RETRIES = int(os.getenv('AI_MAX_RETRIES', '3'))
    AI_RETRY_DELAY = float(os.getenv('AI_RETRY_DELAY', '5.0'))
    AI_REQUEST_TIMEOUT = float(os.getenv('AI_REQUEST_TIMEOUT', '60.0'))
    AI_RETRY_CONTEXT_TIMEOUT = int(os.getenv('AI_RETRY_CONTEXT_TIMEOUT', '300'))

    # OpenRouter Config
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_MODEL_NAME = os.getenv('OPENROUTER_MODEL_NAME')
    OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')

    # Llama.cpp HTTP Server Config
    LLAMA_SERVER_URL = os.getenv('LLAMA_SERVER_URL', 'http://127.0.0.1:8080')

    # Prompt Builder Configuration
    MAX_PROMPT_TOKENS_BUDGET = int(os.getenv('MAX_PROMPT_TOKENS_BUDGET', '128000'))
    LAST_X_HISTORY_MESSAGES = int(os.getenv('LAST_X_HISTORY_MESSAGES', '4'))
    TOKENS_PER_MESSAGE_OVERHEAD = int(os.getenv('TOKENS_PER_MESSAGE_OVERHEAD', '4'))
    
    # Auto-continuation Configuration
    MAX_AI_CONTINUATION_DEPTH = int(os.getenv('MAX_AI_CONTINUATION_DEPTH', '20'))
    
    # Repository Configuration
    # Controls which repository implementation to use for game state persistence
    # Options: 'memory' (in-memory, lost on restart), 'file' (JSON files), 'database' (future)
    GAME_STATE_REPO_TYPE = os.getenv('GAME_STATE_REPO_TYPE', 'memory')
    CAMPAIGNS_DIR = os.getenv('CAMPAIGNS_DIR', 'saves/campaigns')
    CHARACTER_TEMPLATES_DIR = os.getenv('CHARACTER_TEMPLATES_DIR', 'saves/character_templates')
    CAMPAIGN_TEMPLATES_DIR = os.getenv('CAMPAIGN_TEMPLATES_DIR', 'saves/campaign_templates')
    
    # RAG Configuration
    RAG_ENABLED = os.getenv('RAG_ENABLED', 'true').lower() in ('true', '1', 't', 'yes')
    RAG_MAX_RESULTS_PER_QUERY = int(os.getenv('RAG_MAX_RESULTS_PER_QUERY', '3'))
    RAG_MAX_TOTAL_RESULTS = int(os.getenv('RAG_MAX_TOTAL_RESULTS', '8'))
    RAG_SCORE_THRESHOLD = float(os.getenv('RAG_SCORE_THRESHOLD', '0.2'))
    RAG_EMBEDDINGS_MODEL = os.getenv('RAG_EMBEDDINGS_MODEL', 'all-MiniLM-L6-v2')
    RAG_CHUNK_SIZE = int(os.getenv('RAG_CHUNK_SIZE', '500'))
    RAG_CHUNK_OVERLAP = int(os.getenv('RAG_CHUNK_OVERLAP', '50'))
    RAG_COLLECTION_NAME_PREFIX = os.getenv('RAG_COLLECTION_NAME_PREFIX', 'ai_gamemaster')
    RAG_METADATA_FILTERING_ENABLED = os.getenv('RAG_METADATA_FILTERING_ENABLED', 'false').lower() in ('true', '1', 't', 'yes')
    RAG_RELEVANCE_FEEDBACK_ENABLED = os.getenv('RAG_RELEVANCE_FEEDBACK_ENABLED', 'false').lower() in ('true', '1', 't', 'yes')
    RAG_CACHE_TTL = int(os.getenv('RAG_CACHE_TTL', '3600'))

    # TTS Configuration
    TTS_PROVIDER = os.getenv('TTS_PROVIDER', 'kokoro')  # 'kokoro', 'none', etc.
    KOKORO_LANG_CODE = os.getenv('KOKORO_LANG_CODE', 'a')  # 'a' for American English, 'b' for British etc.
    TTS_CACHE_DIR_NAME = os.getenv('TTS_CACHE_DIR_NAME', 'tts_cache')  # Subdirectory within static folder
    
    # Server-Sent Events (SSE) Configuration
    SSE_HEARTBEAT_INTERVAL = int(os.getenv('SSE_HEARTBEAT_INTERVAL', '30'))
    SSE_EVENT_TIMEOUT = float(os.getenv('SSE_EVENT_TIMEOUT', '1.0'))
    
    # Event Queue Configuration
    EVENT_QUEUE_MAX_SIZE = int(os.getenv('EVENT_QUEUE_MAX_SIZE', '0'))

    # Basic validation
    if AI_PROVIDER == 'openrouter':
        if not OPENROUTER_API_KEY:
            print("Warning: AI_PROVIDER is 'openrouter' but OPENROUTER_API_KEY is not set.")
        if not OPENROUTER_MODEL_NAME:
            print("Warning: AI_PROVIDER is 'openrouter' but OPENROUTER_MODEL_NAME is not set.")
    if AI_PROVIDER == 'llamacpp_http' and not LLAMA_SERVER_URL:
        print("Warning: AI_PROVIDER is 'llamacpp_http' but LLAMA_SERVER_URL is not set.")
    if AI_RESPONSE_PARSING_MODE not in ['strict', 'flexible']:
        print(f"Warning: Invalid AI_RESPONSE_PARSING_MODE '{AI_RESPONSE_PARSING_MODE}'. Defaulting to 'strict'.")
        AI_RESPONSE_PARSING_MODE = 'strict'

    # Logging Configuration
    # Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'dnd_ai_poc.log')
