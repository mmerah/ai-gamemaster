# AI Game Master

> **A complete D&D 5e experience powered by AI**

Transform your tabletop gaming with an AI-powered Game Master that brings D&D adventures to life. Whether you're a solo player or managing a group, this web application delivers immersive storytelling, intelligent combat management, and seamless character progression.

It is a massive work in progress as I started working on it a month ago. There is a myriad of bugs and missing features.

![Game Screenshot](./docs/State-Of-Play-24-May-2025.png)

## What You Get

- **🧙‍♂️ AI Dungeon Master**: Storytelling using an LLM that adapts to your choices. Check out [LangChain](https://github.com/langchain-ai/langchain)
- **⚔️ Smart Combat**: Turn-based battles with initiative tracking and status effects  
- **🎯 Character Management**: Complete D&D 5e character sheets with automatic calculations
- **🗺️ Campaign System**: Create, save, and manage multiple adventures
- **🎲 Integrated Dice**: Roll with advantage/disadvantage (hopefully, the AI decides), automated skill checks
- **🔄 Error Recovery**: Retry system for handling AI hiccups (most used feature...)
- **💾 Persistent State**: Your progress is automatically saved
- **🎤 Voice Narration**: Optional text-to-speech using [Kokoro](https://github.com/hexgrad/kokoro) for immersive storytelling
- **🧠 Knowledge-Enhanced AI**: Experimental RAG system provides context-aware D&D 5e rules and lore

## Quick Start

**Just want to play? One command does it all:**

```bash
# Windows
launch.bat

# macOS/Linux  
./launch.sh
```

The basic launcher handles some things automatically:
- Checks prerequisites (Python 3.8+, Node.js 16+)
- Sets up virtual environment  
- Installs all dependencies (if you have npm/python installed)
- Builds frontend
- Launches app and opens browser

📖 **Need help?** See [docs/Launcher-Guide.md](docs/Launcher-Guide.md)

## Configuration

### AI Provider Setup

Create `.env` from template and configure your AI provider:

```bash
cp .env.example .env
```

**Option A: Local Llama.cpp Server (Default)**
```env
AI_PROVIDER=llamacpp_http
LLAMA_SERVER_URL=http://127.0.0.1:8080
AI_RESPONSE_PARSING_MODE=strict  # or 'flexible' for some models
```

**Option B: OpenRouter (Cloud API)**
```env
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL_NAME=google/gemini-2.5-pro  # or gemini-2.5-flash
AI_RESPONSE_PARSING_MODE=strict
```

### Local Llama.cpp Server

You don't need to use launch_server.py, just have an OpenAI endpoint somewhere.

**Launch a model:**
```bash
# Example: Start Qwen 14B model
python launch_server.py qwen_14b_q6

# See available models
python launch_server.py --help
```

**Configure models** by editing `models.yaml`

### Voice Narration (Optional)

Install `espeak-ng` for text-to-speech narration:
- **Linux**: `sudo apt-get install espeak-ng`
- **macOS**: `brew install espeak-ng`  
- **Windows**: Download from [espeak-ng releases](https://github.com/espeak-ng/espeak-ng/releases)

### Performance Optimization

**Disable RAG for faster startup (useful for testing):**
```env
RAG_ENABLED=false  # Skips loading embeddings and knowledge bases
```

**Additional configuration options:**
- `GAME_STATE_REPO_TYPE`: `memory` (fast, volatile) or `file` (persistent)
- `CAMPAIGNS_DIR`: Custom directory for campaign files
- `CHARACTER_TEMPLATES_DIR`: Custom directory for character templates

See [docs/Configuration.md](docs/Configuration.md) for all options.

## Manual Setup (Advanced)

<details>
<summary>Click to expand manual setup instructions</summary>

1. **Clone repository:**
   ```bash
   git clone https://github.com/mmerah/ai-gamemaster.git
   cd ai-gamemaster
   ```

2. **Backend setup:**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env  # Configure your AI provider
   ```

3. **Frontend setup:**
   ```bash
   npm --prefix frontend install
   cp frontend/.env.example frontend/.env
   ```

4. **Development mode:**
   ```bash
   # Terminal 1: Backend (http://127.0.0.1:5000)
   python run.py
   
   # Terminal 2: Frontend (http://localhost:5173)  
   npm --prefix frontend run dev
   ```

5. **Production build:**
   ```bash
   npm --prefix frontend run build
   python run.py  # Serves built frontend
   ```

</details>

## Architecture

- **Backend**: Python Flask with dependency injection container
- **Frontend**: Vue.js 3 with Composition API, Pinia state management, and Tailwind CSS
- **Build System**: Vite for fast development and optimized production builds
- **AI Integration**: Supports both local llama.cpp servers and OpenRouter API using LangChain framework
- **Game State**: Pydantic models with JSON file persistence (configurable via GAME_STATE_REPO_TYPE)
- **Core Logic**: Service-oriented architecture with dependency injection container
- **Event System**: Event-driven game logic with specialized handlers
- **Knowledge System**: Experimental RAG (Retrieval-Augmented Generation) for D&D 5e rules and lore

## Game Features

### Game Interface
- **📜 Chat History**: Message history with role distinction and auto-scroll
- **🎛️ Input Controls**: Message input with dice rolling and quick actions
- **👥 Party Management**: Character display with health bars and status effects
- **⚔️ Combat System**: Initiative tracking and combat state display
- **🗺️ Map Integration**: Visual map display with player markers
- **🎲 Dice Requests**: Handle GM-requested dice rolls with advantage/disadvantage

### Campaign Manager
- **📚 Campaign CRUD**: Create, edit, delete campaigns with party selection
- **📄 Template System**: Character template management with full D&D 5e stats
- **🎨 Grid Layouts**: Beautiful card-based displays
- **📝 Modal Forms**: Professional forms for content creation
- **📊 Status Management**: Campaign lifecycle tracking

## Development

### Backend Commands
```bash
python run.py                    # Development server

# Testing (fast mode with RAG disabled)
python tests/run_all_tests.py   # Run all tests
python tests/run_all_tests.py unit      # Unit tests only
python tests/run_all_tests.py coverage  # With coverage report

# See docs/Testing.md for more testing options
```

### Frontend Commands
```bash
npm --prefix frontend run dev      # Development server with hot reload
npm --prefix frontend run build    # Production build
npm --prefix frontend run preview  # Preview production build
npm --prefix frontend run lint     # Lint code
```

## AI Model Performance

> See [docs/Model-Performance.md](docs/Model-Performance.md) for detailed AI model testing results

**Quick recommendations:**
- **🏆 Best overall**: Gemini 2.5 Pro (cloud API)
- **💰 Best value**: Gemini 2.5 Flash (cloud API)  
- **🏠 Best local**: Qwen3 32B or Mistral-Small 24B
- **⚡ Fast local**: Qwen3 30B A3B
- **🎯 Entry-level**: Qwen3 14B

## License

This project is licensed under the MIT License - see the LICENSE file for details.
