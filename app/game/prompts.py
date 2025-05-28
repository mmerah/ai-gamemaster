import logging
import re
from typing import Dict, List, Optional, Tuple, Any
import tiktoken
from flask import current_app
from . import initial_data
from .models import GameState, KnownNPC, Quest

logger = logging.getLogger(__name__)

# Constants for prompt refactoring
LAST_X_HISTORY_MESSAGES = 4
MAX_PROMPT_TOKENS_BUDGET = 128000
TOKENS_PER_MESSAGE_OVERHEAD = 4

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

        player = game_manager.character_service.get_character(c.id)
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

def _format_message_for_history(msg: Dict) -> Dict[str, str]:
    """Format a single chat history message."""
    # Use the full AI JSON response if available for assistant messages
    content_to_use = msg.get("ai_response_json") if msg["role"] == "assistant" and "ai_response_json" in msg else msg["content"]
    if content_to_use:
        return {"role": msg["role"], "content": content_to_use}
    else:
        logger.warning(f"Skipping history message with empty content: Role={msg['role']}")
        return None

def _calculate_message_tokens(message: Dict[str, str]) -> int:
    """Calculate token count for a single message."""
    if not tokenizer:
        return 0
    try:
        return len(tokenizer.encode(message["content"])) + TOKENS_PER_MESSAGE_OVERHEAD
    except Exception as e:
        logger.warning(f"Error calculating token count for message: {e}")
        return 0

def build_ai_prompt_context(game_state: GameState, handler_self: Any, player_action_input: Optional[str] = None):
    """
    Builds the list of messages to send to the AI based on the current GameState model.
    
    New order: system prompt, main chat history (truncated), static context, 
    dynamic context, RAG context, last X chat history, player action input (if not duplicate).
    """
    logger.debug("Building AI prompt context with new structure...")

    # 1. System Prompt (always first)
    messages = [{"role": "system", "content": initial_data.SYSTEM_PROMPT}]

    # 2. Main Chat History (All but Last X) - will be truncated later based on token budget
    all_chat_history = game_state.chat_history.copy()
    num_last_x_messages = min(LAST_X_HISTORY_MESSAGES, len(all_chat_history))
    
    if num_last_x_messages > 0:
        main_history_block = all_chat_history[:-num_last_x_messages]
        last_x_history_block = all_chat_history[-num_last_x_messages:]
    else:
        main_history_block = all_chat_history
        last_x_history_block = []

    # Format main history block (will be truncated later)
    formatted_main_history = []
    for msg in main_history_block:
        formatted_msg = _format_message_for_history(msg)
        if formatted_msg:
            formatted_main_history.append(formatted_msg)

    # 3. Static context (campaign info, world lore, etc.)
    static_context_parts = []
    static_context_parts.append(f"Campaign Goal: {game_state.campaign_goal}")
    world_lore_formatted = format_list_context("World Lore", game_state.world_lore)
    if world_lore_formatted != "World Lore: None":
        static_context_parts.append(world_lore_formatted)
    quests_formatted = format_active_quests(game_state.active_quests)
    if quests_formatted != "Active Quests: None":
        static_context_parts.append(quests_formatted)
    npcs_formatted = format_known_npcs(game_state.known_npcs)
    if npcs_formatted != "Known NPCs: None":
        static_context_parts.append(npcs_formatted)
    event_summary_formatted = format_list_context("Event Summary", game_state.event_summary)
    if event_summary_formatted != "Event Summary: None":
        static_context_parts.append(event_summary_formatted)
    
    static_context_message = None
    if static_context_parts:
        static_context_content = "\n\n".join(static_context_parts)
        static_context_message = {"role": "user", "content": f"CONTEXT INJECTION:\n{static_context_content}"}

    # 4. Dynamic context (party, location, combat status)
    dynamic_context_parts = []
    party_status = "Party Members & Status:\n" + "\n".join([format_character_for_prompt(pc) for pc in game_state.party.values()])
    dynamic_context_parts.append(party_status)
    location_info = f"Current Location: {game_state.current_location['name']}\nDescription: {game_state.current_location['description']}"
    dynamic_context_parts.append(location_info)
    combat_status = format_combat_state_for_prompt(game_state.combat, handler_self)
    dynamic_context_parts.append(combat_status)
    dynamic_context_content = "\n\n".join(dynamic_context_parts)
    dynamic_context_message = {"role": "user", "content": f"CURRENT STATUS:\n{dynamic_context_content}"}

    # 5. RAG Context - Use dedicated RAG context builder
    from app.services.rag.rag_context_builder import rag_context_builder
    
    # Determine if we should force a new RAG query or reuse stored context
    # Force new query if player_action_input is provided (new player action)
    # Otherwise, reuse stored context (likely dice roll submission)
    force_new_query = player_action_input is not None
    
    rag_context_content = rag_context_builder.get_rag_context_for_prompt(
        game_state, handler_self.rag_service, player_action_input, all_chat_history, force_new_query
    )
    rag_context_message = None
    if rag_context_content:
        rag_context_message = {"role": "user", "content": rag_context_content}

    # 6. Last X Chat History Messages
    formatted_last_x_history = []
    for msg in last_x_history_block:
        formatted_msg = _format_message_for_history(msg)
        if formatted_msg:
            formatted_last_x_history.append(formatted_msg)

    # 7. Player Action Input 
    # NOTE: We don't add player actions separately anymore because:
    # - Player actions are already added to chat history by PlayerActionHandler
    # - They appear in the last X messages that we include
    # - The RAG system can extract the raw content from formatted messages
    # This prevents duplication and simplifies the prompt structure

    # Now calculate fixed components and implement token-aware truncation
    fixed_messages = []
    if static_context_message:
        fixed_messages.append(static_context_message)
    fixed_messages.append(dynamic_context_message)
    if rag_context_message:
        fixed_messages.append(rag_context_message)
    fixed_messages.extend(formatted_last_x_history)

    # Calculate fixed components token count
    # System prompt
    fixed_token_count = _calculate_message_tokens(messages[0])
    for msg in fixed_messages:
        fixed_token_count += _calculate_message_tokens(msg)

    # Determine remaining budget for main history
    remaining_budget = MAX_PROMPT_TOKENS_BUDGET - fixed_token_count
    
    # Iteratively build truncated main history (from most recent to oldest)
    truncated_main_history = []
    current_main_history_tokens = 0
    
    # Start from most recent
    for msg in reversed(formatted_main_history):
        msg_tokens = _calculate_message_tokens(msg)
        if current_main_history_tokens + msg_tokens <= remaining_budget:
            # Insert at beginning to maintain order
            truncated_main_history.insert(0, msg)
            current_main_history_tokens += msg_tokens
        else:
            # Budget exceeded
            break
    
    # Final assembly: System prompt, Truncated Main History, Context (static, dynamic, RAG), Last X History
    final_messages = [messages[0]]
    final_messages.extend(truncated_main_history)
    if static_context_message:
        final_messages.append(static_context_message)
    final_messages.append(dynamic_context_message)
    if rag_context_message:
        final_messages.append(rag_context_message)
    final_messages.extend(formatted_last_x_history)

    # Calculate final token count for logging
    total_tokens = sum(_calculate_message_tokens(msg) for msg in final_messages)
    
    # Log prompt
    history_truncated = len(formatted_main_history) - len(truncated_main_history)
    logger.debug(f"Built AI prompt with {len(final_messages)} messages ({total_tokens} tokens)")
    if history_truncated > 0:
        logger.debug(f"Truncated {history_truncated} older history messages due to token budget")

    # Log individual messages, skipping the system prompt
    for i, msg in enumerate(final_messages):
        if i == 0 and msg["role"] == "system":
            logger.debug(f"Prompt Message [{i}] ({msg['role']}): [SYSTEM PROMPT CONTENT NOT LOGGED]")
            continue
        content_preview = str(msg.get("content", ""))
        if len(content_preview) > 300: # Truncate long messages
            content_preview = content_preview[:300] + "..."
        logger.debug(f"Prompt Message [{i}] ({msg['role']}): {content_preview}")
    
    return final_messages
