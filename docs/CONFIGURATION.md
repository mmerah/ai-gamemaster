# Configuration Guide

This document describes all available configuration options for the AI Game Master.

## Environment Variables

Copy `.env.example` to `.env` and customize as needed.

### AI Configuration

- **AI_PROVIDER**: AI backend to use
  - `llamacpp_http` (default) - Local Llama.cpp server
  - `openrouter` - OpenRouter cloud API

- **AI_RESPONSE_PARSING_MODE**: How to parse AI responses
  - `strict` (default) - Uses structured output for JSON (recommended for modern models)
  - `flexible` - Extracts JSON from free-form text (for older models)

- **AI_TEMPERATURE**: Temperature setting for AI responses
  - Range: 0.0-2.0 (default: 0.7)
  - Lower values (0.0-0.5) make responses more focused and deterministic
  - Higher values (0.5-2.0) make responses more creative and varied

- **OPENROUTER_API_KEY**: API key for OpenRouter (required if using OpenRouter)
- **OPENROUTER_MODEL_NAME**: Model to use on OpenRouter
  - Recommended: `google/gemini-2.5-pro`, `google/gemini-2.5-flash`
- **LLAMA_SERVER_URL**: URL for local Llama.cpp server (default: `http://127.0.0.1:8080`)

### Game Configuration

- **MAX_HISTORY_TURNS**: Number of conversation turns to keep in memory (default: 10)
- **RAG_ENABLED**: Enable/disable the RAG knowledge system
  - `true` (default) - Loads embeddings and knowledge bases
  - `false` - Disables RAG for faster startup (useful for testing)

### Storage Configuration

- **GAME_STATE_REPO_TYPE**: How to persist game state
  - `memory` (default) - In-memory only, lost on restart
  - `file` - Save to JSON files

- **GAME_STATE_FILE_PATH**: File path for game state (default: `saves/game_state.json`)
- **CAMPAIGNS_DIR**: Directory for campaign instance saves (default: `saves/campaigns`)
- **CHARACTER_TEMPLATES_DIR**: Directory for character templates (default: `saves/character_templates`)
- **CAMPAIGN_TEMPLATES_DIR**: Directory for campaign templates (default: `saves/campaign_templates`)

### Text-to-Speech Configuration

- **TTS_PROVIDER**: TTS backend to use
  - `kokoro` (default) - Kokoro TTS engine
  - `none`, `disabled`, `test` - Disable TTS

- **KOKORO_LANG_CODE**: Language variant for Kokoro
  - `a` (default) - American English
  - `b` - British English

- **TTS_CACHE_DIR_NAME**: Directory for TTS cache (default: `tts_cache`)

### Application Configuration

- **SECRET_KEY**: Flask secret key for sessions
- **FLASK_DEBUG**: Enable Flask debug mode (`true`/`false`)
- **LOG_LEVEL**: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- **LOG_FILE**: Log file path (default: `dnd_ai_poc.log`)

## Performance Optimization

### Disabling RAG for Tests

The RAG system loads HuggingFace embeddings on startup, which can take 10+ seconds. For faster test execution:

```bash
RAG_ENABLED=false python -m pytest tests/
```

Or in your test configuration:

```python
config = {
    'GAME_STATE_REPO_TYPE': 'memory',
    'TTS_PROVIDER': 'disabled',
    'RAG_ENABLED': False
}
```

### Memory vs File Persistence

- Use `memory` for development and testing (fastest)
- Use `file` for production to persist game state between restarts

## Directory Structure

Default directories (can be customized via environment variables):

```
ai-gamemaster/
├── saves/
│   ├── campaigns/         # Active campaign instances and game states
│   ├── campaign_templates/   # Reusable campaign templates
│   ├── character_templates/  # Reusable character templates
│   └── game_state.json    # Game state (if using file persistence)
├── static/
│   └── tts_cache/        # Cached TTS audio files
└── app/
    └── content/
        └── data/
            └── knowledge/    # RAG knowledge bases (not configurable)
```

### Templates vs Instances

- **Templates**: Reusable blueprints for campaigns and characters
  - Campaign templates define adventures with starting conditions
  - Character templates define pre-made characters for players
- **Instances**: Active game entities created from templates
  - Campaign instances track active game progress
  - Character instances track character state during gameplay
