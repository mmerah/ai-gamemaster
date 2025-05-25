# AI Model Performance Testing

Being a dungeon master is an interesting task to measure model performance. The AI must create an engaging narrative that makes sense with the initial starting point and send JSON outputs that the app can use to progress the game.

## Test Methodology

Each model was tested with the same scenario:
- Initial narrative with 2 goblins fight
- Several investigation checks in a cave
- Challenging boss fight
- Return to village and claim reward
- Context window usage up to 25k+ tokens

## Model Performance Results

### Local Models

#### **GLM-4 9B 0414 Q8_0** ❌ Poor
**Issues:**
- Very poor structured output compliance
- Frequent repetitions and nonsensical roll requests
- Occasional Chinese characters in output
- Unreliable condition/HP changes

**Verdict:** Not recommended. May be due to configuration issues (hopefully).

#### **Qwen3 4B Q6_K_XL** ⚠️ Limited
**Performance:**
- Decent structured output initially
- Cannot manage beyond a few turns
- Good tracking until ~10k tokens
- Degrades quickly with context growth

**Verdict:** Not suitable for extended gameplay.

#### **Qwen3 14B Q6_K** ✅ Good
**Performance:**
- Reliable through initial scenarios
- Decent until ~10k tokens, then becomes unreliable
- Adequate imagination and storytelling
- Playable until context limit

**Verdict:** Good experience for a model this size. Best entry-level local option.

#### **Qwen3 30B A3B Q4_K_XL** ✅ Very Good
**Performance:**
- Cannot work with Instructor (requires `AI_RESPONSE_PARSING_MODE=flexible`)
- Always produces correct JSON even at context limit
- Slightly below 32B but much faster
- Makes small mistakes that 32B avoids

**Verdict:** Excellent speed/quality balance for local deployment.

#### **Qwen3 32B Q4_K_XL** ✅ Excellent
**Performance:**
- Superior tracking compared to 14B
- Engaging and fun storytelling
- Reliable throughout extended sessions
- Resource intensive

**Verdict:** Best local experience if you have the hardware.

#### **Phi4 Q6_K_XL** ⚠️ Moderate
**Performance:**
- Solid structured output
- Makes small mistakes quickly
- Less reliable than Qwen3 models
- Decent but not outstanding

**Verdict:** Functional but not recommended over Qwen alternatives.

#### **Mistral-Small-3.1 24B Instruct 2503 Q5_K_XL** ✅ Excellent
**Performance:**
- Outstanding tracking and reliability
- Goes to context limit without issues
- Very token-efficient
- Follows instructions precisely
- **Limitation:** Not very imaginative or surprising

**Verdict:** Best for tactical/mechanical gameplay. Lacks creative flair.

#### **Gemma 3 27B QAT Q4_0** ✅ Excellent
**Performance:**
- Excellent reliability throughout
- No context degradation issues
- Good roleplay and fun factor
- Solid writing style

**Verdict:** Great all-around local model.

### Cloud Models (OpenRouter)

#### **Gemini 2.5 Pro** 🏆 Outstanding
**Performance:**
- Absolute best at DMing
- Maintains perfect tracking throughout any scenario
- Incredible D&D knowledge and rule enforcement
- Asks for clarification when actions don't make sense
- Creates engaging, surprising stories
- Has its own agency - surprises players
- **Cost:** ~$1.40 for a full quest (25k tokens)

**Verdict:** The only model that truly feels like an experienced DM. Gold standard.

#### **Gemini 2.5 Flash** ⚡ Excellent Value
**Performance:**
- Noticeably smaller than Pro but very capable
- Good at handling quests and adventures
- **Major advantage:** Blazing fast and very cheap
- Less context degradation than local models
- **Cost:** ~$0.10 for a full quest (26k tokens)

**Verdict:** Best value proposition. Fast responses are addictive. I end up using it the most for quick testing.

## Configuration Notes

### AI Response Parsing
- **Strict mode** (default): Uses `instructor` library for guaranteed JSON compliance
- **Flexible mode**: Required for some models (like Qwen3 30B A3B) that can't work with instructor. It **seems** like models perform better in flexible mode (maybe just imagination)

### Performance Tips
1. Use quantization for best quality/speed balance
2. Adjust context window based on available memory
3. Monitor token usage to prevent context overflow
4. Consider using `AI_RESPONSE_PARSING_MODE=flexible` if strict mode fails

---

*Last updated: May 2025*
