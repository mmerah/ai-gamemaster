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
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'llamacpp_http') # Default to http server

    # OpenRouter Config
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_MODEL_NAME = os.getenv('OPENROUTER_MODEL_NAME', 'mistralai/mistral-7b-instruct')

    # Llama.cpp HTTP Server Config
    LLAMA_SERVER_URL = os.getenv('LLAMA_SERVER_URL', 'http://127.0.0.1:8080')

    # Game Config
    MAX_HISTORY_TURNS = int(os.getenv('MAX_HISTORY_TURNS', 10))

    # Basic validation
    if AI_PROVIDER == 'openrouter' and not OPENROUTER_API_KEY:
        print("Warning: AI_PROVIDER is 'openrouter' but OPENROUTER_API_KEY is not set.")
    if AI_PROVIDER == 'llamacpp_http' and not LLAMA_SERVER_URL:
        print("Warning: AI_PROVIDER is 'llamacpp_http' but LLAMA_SERVER_URL is not set.")

    # Logging Configuration
    # Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    LOG_FILE = os.getenv('LOG_FILE', 'dnd_ai_poc.log')