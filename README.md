# AI Game Master

A web-based Dungeons & Dragons 5e game powered by AI. Load any LLM supported by llamacpp or use OpenRouter, and enjoy an interactive D&D experience with an AI Game Master.

This application provides a complete D&D-like experience with character management, combat systems, dice rolling, and dynamic storytelling powered by large language models.

![alt text](./docs/State-Of-Play-23-May-2025.png "State of Play (23 May 2025)")

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
    *   Create a `.env` file in the project root (copy `.env.example` if provided).
    *   Set the `AI_PROVIDER` variable:
        *   `AI_PROVIDER=llamacpp_http` (Default): For using a local Llama.cpp server.
            *   Ensure `LLAMA_SERVER_URL` is set (e.g., `LLAMA_SERVER_URL=http://127.0.0.1:8080`).
            *   Optionally set `LLAMA_SERVER_API_KEY` if your server requires one.
            *   Optionally set `LLAMA_SERVER_MODEL_PLACEHOLDER` (used internally, doesn't affect server model).
        *   `AI_PROVIDER=openrouter`: For using OpenRouter.
            *   Set `OPENROUTER_API_KEY` to your OpenRouter API key.
            *   Set `OPENROUTER_MODEL_NAME` to the desired model identifier (e.g., `google/gemini-pro-1.5`, `mistralai/mistral-large`).
            *   Optionally set `OPENROUTER_BASE_URL` if needed (defaults to `https://openrouter.ai/api/v1`).
    *   **Response Parsing Mode (Optional):**
        *   Set `AI_RESPONSE_PARSING_MODE=strict` (Default): Uses `instructor` to force the AI to output *only* valid JSON matching the expected format. This is generally more reliable if the model supports tool/function calling well.
        *   Set `AI_RESPONSE_PARSING_MODE=flexible`: The application will attempt to find a JSON block within the AI's potentially longer text response (e.g., if the model includes "thinking..." text). Any text outside the JSON block will be added to the internal "reasoning" field. This can be useful for models that struggle with strict JSON output modes.

4.  **(Optional) Configure Local Llama.cpp Server:**
    *   If using `llamacpp_http`, you need a running Llama.cpp server instance.
    *   Compile Llama.cpp with server support.
    *   Use the `launch_server.py` script to start the server with models defined in `models.yaml`:
        ```bash
        # Example: Launch server with the 'qwen_14b_q6' config from models.yaml
        python launch_server.py qwen_14b_q6
        ```
        *   Ensure the `llama-server` executable built by Llama.cpp is in your system's PATH or modify `LLAMA_SERVER_EXECUTABLE_NAME` in `launch_server.py`.
        *   Edit `models.yaml` to point to your model files and adjust server parameters.

5.  **Run the Flask Application:**
    ```bash
    flask run
    # Or: python run.py
    ```
    *   The application will be available at `http://127.0.0.1:5000`.

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
