# AI Game Master

Load whatever LLM supported by llamacpp and ... hope for the best.
This is a 2-day old proof-of-concept. There is an endless list of issues and features missing.

![alt text](./docs/State-Of-Play-02-May-2025.png "State of Play (02 May 2025)")

# Trying out models
Turns out that being a dungeon master is an interesting task to measure model performance. Here, the AI must create an engaging narative that make sense with the initial starting point and send JSON outputs that the app can use to progress the game:
- Qwen3 4B Q6_K_XL: Structured output but just cannot manage beyond a few turns. Does track things well until above 10k tokens. Not a great experience.
- Qwen3 14B Q6_K: I can progress through the initial narrative (a fight with 2 goblins) and continue without issues until context is a bit filled. Basically, above ~10k tokens, it is a bit unreliable and only gets less reliable as the context fills. Still playable until context limit though. In addition, it is not the most engaging/fun, just decent in the 'imagination' area. Overall, it is a good experience for a model that size!
- Qwen3 30B A3B Q4_K_XL: Can't make it work with Instructor, did not investigate why.
- Qwen3 32B Q4_K_XL: Good tracking of things, quite a bit better than 14B in that aspect. Also decently fun and engaging. Was slow on my machine so I didn't experiment a lot. But if you can run it fast ? That's a really good experience.
- Phi4 Q6_K_XL: Structured output solid. It's not bad but very quickly makes small mistakes that Qwen3 never does.
- Mistral-Small-3.1 24B Instruct 2503 Q5_K_XL: Very very good. Outside of not being very 'fun'/'rp'/'imaginative' it just goes through battles and adventures and keeps track of things incredibly well for a 24B model. Went to the context limit, no issues. Very token-efficient. Main issue is that it just follows what you say, it never surprises you. But I was blown away by it, great fun despite it being not very imaginative.
- Gemini 2.5 Pro: Absolute beast at DMing, remains on track throughout anything you might throw at it. Creates engaging stories, you can feed entire campaigns to it and it will go through them impressively well. And as opposed to most models, it feels like it has its own agency. If I tell it that I want to follow a path, it might surprise me with something different that just a description of the path. No other smaller model does that. IMO, it might be the only one that can DM at an average level.
