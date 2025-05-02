import logging
from typing import Dict, List, Optional
import tiktoken
from flask import current_app
from . import initial_data
from .models import GameState, KnownNPC, Quest

logger = logging.getLogger(__name__)

try:
    # Using cl100k_base as it's common for GPT-3.5/4 and compatible models
    # Adjust if your specific model uses a different encoding
    tokenizer = tiktoken.get_encoding("cl100k_base")
    logger.info("Tiktoken tokenizer 'cl100k_base' loaded successfully.")
except Exception as e:
    logger.warning(f"Could not load tiktoken tokenizer: {e}. Token count logging will be disabled.")
    tokenizer = None

def format_character_for_prompt(char_instance):
    """Formats a CharacterInstance for the AI prompt context."""
    # Include key dynamic info
    status = f"HP: {char_instance.current_hp}/{char_instance.max_hp}, AC: {char_instance.armor_class}"
    if char_instance.temporary_hp > 0:
        status += f", Temp HP: {char_instance.temporary_hp}"
    if char_instance.conditions:
        status += f", Conditions: {', '.join(char_instance.conditions)}"
    # Add spell slots if applicable? Be mindful of token count.
    return f"- ID: {char_instance.id}, Name: {char_instance.name} ({char_instance.race} {char_instance.char_class} {char_instance.level}) | Status: {status}"

def format_combat_state_for_prompt(combat_state, game_manager):
    """Formats the CombatState for the AI prompt context."""
    if not combat_state.is_active:
        return "Combat Status: Not Active"

    lines = ["Combat Status: Active", f"Round: {combat_state.round_number}"]

    if not combat_state.combatants:
        lines.append("Combatants: None (Error or Pre-Initiative?)")
        if combat_state.monster_stats:
            lines.append("Known Monsters (Pre-Initiative?):")
            for npc_id, npc_data in combat_state.monster_stats.items():
                lines.append(f"  - {npc_data.get('name', npc_id)} (ID: {npc_id}, HP: {npc_data.get('hp','?')}, AC: {npc_data.get('ac','?')})")
        return "\n".join(lines)

    # Ensure index is valid
    current_index = combat_state.current_turn_index
    if not (0 <= current_index < len(combat_state.combatants)):
        logger.error(f"Invalid combat index {current_index} in format_combat_state_for_prompt. Resetting to 0.")
        current_index = 0

    # Check again after potential reset
    if 0 <= current_index < len(combat_state.combatants):
        current_combatant = combat_state.combatants[current_index]
        lines.append(f"Current Turn: {current_combatant.name} (ID: {current_combatant.id})")
    else:
        lines.append("Current Turn: Error - Invalid Index")

    lines.append("Turn Order (Highest Initiative First):")
    for i, c in enumerate(combat_state.combatants):
        prefix = "-> " if i == current_index else "   "
        status_parts = []
        is_defeated = False

        player = game_manager.get_character_instance(c.id)
        if player:
            status_parts.append(f"HP: {player.current_hp}/{player.max_hp}")
            if player.conditions: status_parts.append(f"Cond: {', '.join(player.conditions)}")
            if player.current_hp <= 0: is_defeated = True
        elif c.id in combat_state.monster_stats:
            m_stat = combat_state.monster_stats[c.id]
            hp = m_stat.get('hp', '?')
            initial_hp = m_stat.get('initial_hp', '?')
            conditions = m_stat.get('conditions', [])

            status_parts.append(f"HP: {hp}/{initial_hp}")
            active_conditions = [cond for cond in conditions if cond != "Defeated"]
            if active_conditions: status_parts.append(f"Cond: {', '.join(active_conditions)}")

            if hp <= 0 or "Defeated" in conditions:
                is_defeated = True
                status_parts.append("[Defeated]")

        status_string = f"({', '.join(status_parts)})" if status_parts else ""
        lines.append(f"{prefix}{c.name} (ID: {c.id}, Init: {c.initiative}) {status_string}")

    return "\n".join(lines)

def format_known_npcs(npcs: Dict[str, KnownNPC]) -> str:
    if not npcs: return "Known NPCs: None"
    lines = ["Known NPCs:"]
    for npc in npcs.values():
        lines.append(f"- {npc.name} (ID: {npc.id}): {npc.description} (Last Seen: {npc.last_location or 'Unknown'})")
    return "\n".join(lines)

def format_active_quests(quests: Dict[str, Quest]) -> str:
    active = [q for q in quests.values() if q.status == 'active']
    if not active: return "Active Quests: None"
    lines = ["Active Quests:"]
    for quest in active:
        lines.append(f"- {quest.title} (ID: {quest.id}): {quest.description}")
    return "\n".join(lines)

def format_list_context(title: str, items: List[str]) -> str:
    if not items: return f"{title}: None"
    lines = [f"{title}:"]
    lines.extend([f"- {item}" for item in items])
    return "\n".join(lines)

def build_ai_prompt_context(game_state: GameState, game_manager, initial_instruction: Optional[str] = None):
    """
    Builds the list of messages to send to the AI based on the current GameState model.
    Can include an optional final instruction message (e.g., for triggering NPC turns).
    """
    logger.debug("Building AI prompt context from GameState model...")
    
    # System Prompt
    messages = [{"role": "system", "content": initial_data.SYSTEM_PROMPT}]

    # Context Injection
    context_injections = [
        f"Campaign Goal: {game_state.campaign_goal}",
        format_list_context("World Lore", game_state.world_lore),
        format_active_quests(game_state.active_quests),
        format_known_npcs(game_state.known_npcs),
        format_list_context("Event Summary", game_state.event_summary),
        # Party and Location are still dynamic and important
        "Party Members & Status:\n" + "\n".join([format_character_for_prompt(pc) for pc in game_state.party.values()]),
        f"Current Location: {game_state.current_location['name']}\nDescription: {game_state.current_location['description']}",
        format_combat_state_for_prompt(game_state.combat, game_manager)
    ]
    for injection in context_injections:
        if injection: # Avoid adding empty context messages
            messages.append({"role": "user", "content": f"CONTEXT INJECTION:\n{injection}"})

    # Chat History
    history_messages = []
    for msg in game_state.chat_history:
        # Use the full AI JSON response if available for assistant messages
        content_to_use = msg.get("ai_response_json") if msg["role"] == "assistant" and "ai_response_json" in msg else msg["content"]
        if content_to_use:
            history_messages.append({"role": msg["role"], "content": content_to_use})
        else:
            logger.warning(f"Skipping history message with empty content: Role={msg['role']}")

    messages.extend(history_messages)
    logger.debug(f"Added {len(history_messages)} messages from chat history to prompt context.")

    # Append Initial Instruction if provided
    if initial_instruction:
        logger.debug(f"Appending initial instruction: {initial_instruction}")
        messages.append({"role": "user", "content": initial_instruction})

    # Token Counting
    token_count = "N/A"
    if tokenizer:
        try:
            # Encode each message content and sum tokens
            # Add small overhead per message (e.g., 4 tokens for role/name/etc.)
            num_tokens = 0
            for message in messages:
                num_tokens += 4 # Approximation for message overhead
                num_tokens += len(tokenizer.encode(message["content"]))
            token_count = num_tokens
            logger.debug(f"Estimated prompt token count: {token_count}")
        except Exception as e:
            logger.warning(f"Error calculating token count: {e}")

    # Log the full prompt being sent if log level is DEBUG
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"----- Full AI Prompt ({len(messages)} messages | Tokens: {token_count}) -----")
        for i, msg in enumerate(messages):
            logger.debug(f"{i}. ROLE: {msg['role']}")
            content_preview = msg['content'][:500].replace('\n', '\\n') + ('...' if len(msg['content']) > 500 else '')
            logger.debug(f"   CONTENT (Preview): {content_preview}")
        logger.debug(f"----- End AI Prompt -----")
    else:
        logger.info(f"Built context with {len(messages)} messages for AI (Tokens: {token_count}).")

    return messages