# AI Game Master

A web-based Dungeons & Dragons 5e game powered by AI. This Flask application acts as an AI-powered Game Master, supporting both local LLMs via llamacpp and cloud-based models through OpenRouter.

This application provides a work-in-progress D&D-like experience with:
- **(WIP) Character Management**: Create and manage D&D 5e characters with full stat tracking
- **(WIP) Campaign System**: Create, save, and manage multiple campaigns
- **Combat System**: Turn-based combat with initiative tracking and status effects. With bugs.
- **Dice Rolling**: Integrated dice rolling system with advantage/disadvantage support
- **AI-Powered Storytelling**: Dynamic narrative generation with structured JSON responses
- **(WIP) Persistent Game State**: Save/load game sessions with complete state preservation

![alt text](./docs/State-Of-Play-23-May-2025.png "State of Play (23 May 2025)")

## Architecture Overview

- **Backend**: Python Flask with dependency injection container
- **Frontend**: JavaScript, HTML, CSS (served by Flask)
- **AI Integration**: Supports both local llama.cpp servers and OpenRouter API
- **Game State**: Pydantic models with JSON file persistence
- **Core Logic**: Service-oriented architecture with clear separation of concerns

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/mmerah/ai-gamemaster.git
    cd ai-gamemaster
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure your AI Provider:**
    Create a `.env` file in the project root (copy from `.env.example`):
    ```bash
    cp .env.example .env
    ```
    
    **Option A: Local Llama.cpp Server (Default)**
    ```env
    AI_PROVIDER=llamacpp_http
    LLAMA_SERVER_URL=http://127.0.0.1:8080
    AI_RESPONSE_PARSING_MODE=strict
    ```
    
    **Option B: OpenRouter (Cloud API)**
    ```env
    AI_PROVIDER=openrouter
    OPENROUTER_API_KEY=your_openrouter_api_key_here
    OPENROUTER_MODEL_NAME=google/gemini-pro-1.5
    OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
    AI_RESPONSE_PARSING_MODE=strict
    ```

4.  **AI Response Parsing Modes:**
    - `strict` (Default): Uses `instructor` library for guaranteed JSON schema compliance
    - `flexible`: Extracts JSON from mixed text responses (for models struggling with JSON mode)

5.  **Local Llama.cpp Server Setup (if using `llamacpp_http`):**
    
    **Prerequisites:**
    - Compiled llama.cpp with server support
    - `llama-server` executable in your system PATH
    
    **Configure Models:**
    Edit `models.yaml` to point to your model files. The configuration uses YAML anchors for easy management:
    ```yaml
    # Add a new model by inheriting from defaults
    my_custom_model:
      <<: *qwen_defaults  # Inherit Qwen-specific settings
      model_path: "C:\\path\\to\\your\\model.gguf"
    ```
    
    **Launch Server:**
    ```bash
    # Launch with a specific model configuration
    python launch_server.py qwen_14b_q6
    
    # Use custom YAML file
    python launch_server.py -f my_models.yaml phi_4_q6
    
    # See available configurations
    python launch_server.py --help
    ```

6.  **Run the Application:**
    ```bash
    python run.py
    # Or: flask run
    ```
    The application will be available at `http://127.0.0.1:5000`

## Available Model Configurations

The `models.yaml` file includes pre-configured setups for various models:
- **Qwen Models**: `qwen_14b_q6`, `qwen_4b_q6`, `qwen_30b_a3b_q4`, `qwen_32b_q4`
- **Phi Models**: `phi_4_q6`
- **Mistral Models**: `mistral_24b_instruct_q5`
- **Gemma Models**: `gemma_3_27b_q4`
- **GLM Models**: `glm_4_9b_q8`

Each configuration inherits sensible defaults and can be easily customized.

# Trying out models
Turns out that being a dungeon master is an interesting task to measure model performance. Here, the AI must create an engaging narative that make sense with the initial starting point and send JSON outputs that the app can use to progress the game:

- GLM-4 9B 0414 Q8_0: Maybe I have wrong settings for this one but it was really bad. Outside of structured output, it made repetitions, asked for nonsense rolls or conditions/hp-changes, occasionally put a chinese character here and there ... Hopefully it was just bad settings on my side.
- Qwen3 4B Q6_K_XL: Structured output but just cannot manage beyond a few turns. Does track things well until above 10k tokens. Not a great experience.
- Qwen3 14B Q6_K: I can progress through the initial narrative (a fight with 2 goblins) and continue without issues until context is a bit filled. Basically, above ~10k tokens, it is a bit unreliable and only gets less reliable as the context fills. Still playable until context limit though. In addition, it is not the most engaging/fun, just decent in the 'imagination' area. Overall, it is a good experience for a model that size!
- Qwen3 30B A3B Q4_K_XL: Can't make it work with Instructor, did not investigate why. Had to use `AI_RESPONSE_PARSING_MODE=flexible` and manually parse the JSON produced. Thankfully it always did produce correct JSONs even when filling the context. It's slightly below Qwen3 32B but is so much faster which makes for a better experience. Makes a small amount of mistakes that 32B does not.
- Qwen3 32B Q4_K_XL: Good tracking of things, quite a bit better than 14B in that aspect. Also decently fun and engaging. Was slow on my machine so I didn't experiment a lot. But if you can run it fast ? That's a really good experience.
- Phi4 Q6_K_XL: Structured output solid. It's not bad but very quickly makes small mistakes that Qwen3 never does.
- Mistral-Small-3.1 24B Instruct 2503 Q5_K_XL: Very very good. Outside of not being very 'fun'/'rp'/'imaginative' it just goes through battles and adventures and keeps track of things incredibly well for a 24B model. Went to the context limit, no issues. Very token-efficient. Main issue is that it just follows what you say, it never surprises you. But I was blown away by it, great fun despite it being not very imaginative.
- Gemma 3 27B QAT Q4_0: Just great. Goes through things very well. No issues over the growing context. Quite decent 'RP'/'Fun' factor, good writing style.
- Gemini 2.5 Pro: Absolute beast at DMing, remains on track throughout anything you might throw at it. I can't stress enough how good it is. It will not let you do things that don't correspond to your level and ask for clarification if something does not make sense (using cunning action to attack for example). Just incredible knowledge. Creates engaging stories, you can feed entire campaigns to it and it will go through them impressively well. And as opposed to most models, it feels like it has its own agency. If I tell it that I want to follow a path, it might surprise me with something different that just a description of the path. No other smaller model does that. IMO, it might be the only one that can DM at an average level. If you use the paying API, cost me 1.4$ for a small quest (up to 25k tokens, fight with 2 goblins, a couple of moments in a cave, pretty challenging fight agains a boss, return back to claim reward).
- Gemini 2.5 Flash: You can feel that it is a much smaller model than 2.5 Pro but it is quite decent at handling itself throughout quests and adventures. But it has a massive advantage over most other models: it is blazing fast and insanely cheap. Cost me 0.1$ for a small quest (up to 26k tokens, fight 2 goblins, a few investigation checks in a cave, challenging fight against boss, return to village, claim reward). Instant responses is just very addictive. It does not feel like it degrades as much as smaller local models over a growing context, quite nice.
