"""
Prompt builder implementation using LangChain for token-aware message truncation.
Uses ChatPromptTemplate and trim_messages for intelligent context management.
"""

import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Protocol

import tiktoken
from langchain_core.messages import BaseMessage, SystemMessage, trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.models import (
    CharacterInstanceModel,
    ChatMessageModel,
    CombatStateModel,
    GameStateModel,
    NPCModel,
    QuestModel,
)
from app.repositories.character_template_repository import CharacterTemplateRepository
from app.settings import get_settings
from app.utils.message_converter import MessageConverter

from . import initial_data

# Avoid circular import by using TYPE_CHECKING
if TYPE_CHECKING:
    from app.core.interfaces import CharacterService
    from app.core.rag_interfaces import RAGService
    from app.services.campaign_service import CampaignService


class EventHandlerProtocol(Protocol):
    """Protocol for event handler to avoid circular imports."""

    character_service: "CharacterService"
    campaign_service: "CampaignService"
    rag_service: Optional["RAGService"]


logger = logging.getLogger(__name__)

# Constants for prompt refactoring (from configuration)
settings = get_settings()
LAST_X_HISTORY_MESSAGES = settings.prompt.last_x_history_messages
MAX_PROMPT_TOKENS_BUDGET = settings.prompt.max_tokens_budget
TOKENS_PER_MESSAGE_OVERHEAD = settings.prompt.tokens_per_message_overhead

try:
    # Using cl100k_base as it's common for GPT-3.5/4 and compatible models
    tokenizer = tiktoken.get_encoding("cl100k_base")
    logger.info("Tiktoken tokenizer 'cl100k_base' loaded successfully.")
except Exception as e:
    logger.warning(
        f"Could not load tiktoken tokenizer: {e}. Token count logging will be disabled."
    )
    tokenizer = None  # type: ignore[assignment]


class PromptBuilder:
    """
    Prompt builder using LangChain's ChatPromptTemplate and message utilities.
    Maintains exact compatibility with the original prompts.py functionality.
    """

    def __init__(self) -> None:
        """Initialize the LangChain-based prompt builder."""
        # Create the prompt template with placeholders for different sections
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                MessagesPlaceholder("main_history", optional=True),
                MessagesPlaceholder("static_context", optional=True),
                MessagesPlaceholder("dynamic_context", optional=True),
                MessagesPlaceholder("rag_context", optional=True),
                MessagesPlaceholder("recent_history", optional=True),
            ]
        )

        logger.info("Initialized PromptBuilder")

    def format_character_for_prompt(
        self,
        char_id: str,
        char_instance: CharacterInstanceModel,
        template_repo: CharacterTemplateRepository,
    ) -> str:
        """Formats a CharacterInstanceModel for the AI prompt context."""
        # Get template for static data
        template = template_repo.get_template(char_instance.template_id)
        if not template:
            logger.warning(
                f"Template {char_instance.template_id} not found for character {char_id}"
            )
            return f"Character {char_id} (template not found)"
        # Include key dynamic info
        status = f"HP: {char_instance.current_hp}/{char_instance.max_hp}"
        if char_instance.temp_hp > 0:
            status += f", Temp HP: {char_instance.temp_hp}"
        if char_instance.conditions:
            status += f", Conditions: {', '.join(char_instance.conditions)}"

        # Use template for static data
        return f"- ID: {char_id}, Name: {template.name} ({template.race} {template.char_class} {char_instance.level}) | Status: {status}"

    def format_combat_state_for_prompt(
        self, combat_state: CombatStateModel, event_handler: EventHandlerProtocol
    ) -> str:
        """Formats the CombatStateModel for the AI prompt context."""
        if not combat_state.is_active:
            return "Combat Status: Not Active"

        lines = ["Combat Status: Active", f"Round: {combat_state.round_number}"]

        if not combat_state.combatants:
            lines.append("Combatants: None (Error or Pre-Initiative?)")
            return "\n".join(lines)

        # Ensure index is valid
        current_index = combat_state.current_turn_index
        if not (0 <= current_index < len(combat_state.combatants)):
            logger.error(
                f"Invalid combat index {current_index} in format_combat_state_for_prompt. Resetting to 0."
            )
            current_index = 0

        # Check again after potential reset
        if 0 <= current_index < len(combat_state.combatants):
            current_combatant = combat_state.combatants[current_index]
            lines.append(
                f"Current Turn: {current_combatant.name} (ID: {current_combatant.id})"
            )
        else:
            lines.append("Current Turn: Error - Invalid Index")

        lines.append("Turn Order (Highest Initiative First):")
        for i, c in enumerate(combat_state.combatants):
            prefix = "-> " if i == current_index else "   "
            status_parts = []

            char_data = event_handler.character_service.get_character(c.id)
            if char_data and char_data.instance:
                # Access the instance for dynamic state
                instance = char_data.instance
                status_parts.append(f"HP: {instance.current_hp}/{instance.max_hp}")
                if instance.conditions:
                    status_parts.append(f"Cond: {', '.join(instance.conditions)}")
            else:
                # NPC combatant - get data directly from combatant
                hp = c.current_hp
                max_hp = c.max_hp  # max_hp serves as initial_hp for NPCs
                conditions = c.conditions

                status_parts.append(f"HP: {hp}/{max_hp}")
                active_conditions = [
                    cond for cond in conditions if cond.lower() != "defeated"
                ]
                if active_conditions:
                    status_parts.append(f"Cond: {', '.join(active_conditions)}")

                if (isinstance(hp, (int, float)) and hp <= 0) or any(
                    c.lower() == "defeated" for c in conditions
                ):
                    status_parts.append("[Defeated]")

            status_string = f"({', '.join(status_parts)})" if status_parts else ""
            lines.append(
                f"{prefix}{c.name} (ID: {c.id}, Init: {c.initiative}) {status_string}"
            )

        return "\n".join(lines)

    def format_known_npcs(self, npcs: Dict[str, NPCModel]) -> str:
        """Format known NPCs for prompt."""
        if not npcs:
            return "Known NPCs: None"
        lines = ["Known NPCs:"]
        for npc in npcs.values():
            lines.append(
                f"- {npc.name} (ID: {npc.id}): {npc.description} (Last Seen: {npc.last_location or 'Unknown'})"
            )
        return "\n".join(lines)

    def format_active_quests(self, quests: Dict[str, QuestModel]) -> str:
        """Format active quests for prompt."""
        active = [q for q in quests.values() if q.status == "active"]
        if not active:
            return "Active Quests: None"
        lines = ["Active Quests:"]
        for quest in active:
            lines.append(f"- {quest.title} (ID: {quest.id}): {quest.description}")
        return "\n".join(lines)

    def format_list_context(self, title: str, items: List[str]) -> str:
        """Format a list of items for context."""
        if not items:
            return f"{title}: None"
        lines = [f"{title}:"]
        lines.extend([f"- {item}" for item in items])
        return "\n".join(lines)

    def _format_message_for_history(
        self, msg: ChatMessageModel
    ) -> Optional[BaseMessage]:
        """Format a single chat history message to LangChain format."""
        # ChatMessageModel object (from app.ai_services.schemas)
        role = msg.role
        content = msg.content
        is_dice_result = msg.is_dice_result or False
        ai_response_json = msg.ai_response_json

        # Skip system error messages to prevent them from being sent to AI
        if role == "system" and is_dice_result and content.strip().startswith("(Error"):
            logger.debug(
                f"Excluding system error message from AI prompt: {content[:50]}..."
            )
            return None

        # Use the full AI JSON response if available for assistant messages
        content_to_use = (
            ai_response_json if role == "assistant" and ai_response_json else content
        )
        if not content_to_use:
            logger.warning(f"Skipping history message with empty content: Role={role}")
            return None

        # Convert to LangChain message
        try:
            # Use to_langchain method which expects a list
            messages = MessageConverter.to_langchain(
                [{"role": role, "content": content_to_use}]
            )
            return messages[0] if messages else None
        except ValueError as e:
            logger.warning(f"Failed to convert message to LangChain format: {e}")
            return None

    def _calculate_message_tokens(self, message: BaseMessage) -> int:
        """Calculate token count for a single LangChain message."""
        if not tokenizer:
            return 0
        try:
            content = message.content
            if isinstance(content, str):
                return len(tokenizer.encode(content)) + TOKENS_PER_MESSAGE_OVERHEAD
            else:
                # Convert non-string content to string
                return len(tokenizer.encode(str(content))) + TOKENS_PER_MESSAGE_OVERHEAD
        except Exception as e:
            logger.warning(f"Error calculating token count for message: {e}")
            return 0

    def build_ai_prompt_context(
        self,
        game_state: GameStateModel,
        event_handler: EventHandlerProtocol,
        player_action_for_rag_query: Optional[str] = None,
        initial_instruction: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """
        Builds the list of messages to send to the AI based on the current GameStateModel model.

        Args:
            game_state: Current game state
            event_handler: Event handler instance (for accessing services)
            player_action_for_rag_query: Raw player action text used solely for RAG query generation
            initial_instruction: System-generated instruction to guide AI for the current step

        Returns messages in dict format for compatibility with existing AI services.
        Uses LangChain internally for message management and token budgeting.
        """
        from langchain_core.messages import HumanMessage

        # 1. System Prompt
        system_prompt = initial_data.SYSTEM_PROMPT

        # 2. Process chat history
        all_chat_history = game_state.chat_history.copy()
        num_last_x_messages = min(LAST_X_HISTORY_MESSAGES, len(all_chat_history))

        if num_last_x_messages > 0:
            main_history_block = all_chat_history[:-num_last_x_messages]
            last_x_history_block = all_chat_history[-num_last_x_messages:]
        else:
            main_history_block = all_chat_history
            last_x_history_block = []

        # Convert main history to LangChain messages
        main_history_messages: List[BaseMessage] = []
        for msg in main_history_block:
            formatted_msg = self._format_message_for_history(msg)
            if formatted_msg:
                main_history_messages.append(formatted_msg)

        # 3. Build static context
        static_context_parts: List[str] = []
        static_context_parts.append(f"Campaign Goal: {game_state.campaign_goal}")
        logger.debug(f"Campaign goal: {game_state.campaign_goal}")

        world_lore_formatted = self.format_list_context(
            "World Lore", game_state.world_lore
        )
        if world_lore_formatted != "World Lore: None":
            static_context_parts.append(world_lore_formatted)
            logger.debug(f"Added world lore: {len(game_state.world_lore)} items")

        quests_formatted = self.format_active_quests(game_state.active_quests)
        if quests_formatted != "Active Quests: None":
            static_context_parts.append(quests_formatted)

        npcs_formatted = self.format_known_npcs(game_state.known_npcs)
        if npcs_formatted != "Known NPCs: None":
            static_context_parts.append(npcs_formatted)

        event_summary_formatted = self.format_list_context(
            "Event Summary", game_state.event_summary
        )
        if event_summary_formatted != "Event Summary: None":
            static_context_parts.append(event_summary_formatted)

        static_context_messages: List[HumanMessage] = []
        if static_context_parts:
            static_context_content = "\n\n".join(static_context_parts)
            static_context_messages.append(
                HumanMessage(content=f"CONTEXT INJECTION:\n{static_context_content}")
            )
            logger.debug(
                f"Created static context message with {len(static_context_parts)} parts"
            )
        else:
            logger.debug("No static context parts to include")

        # 4. Build dynamic context
        dynamic_context_parts: List[str] = []
        # Get template repository from handler's container
        template_repo = event_handler.campaign_service.character_template_repo
        party_status = "Party Members & Status:\n" + "\n".join(
            [
                self.format_character_for_prompt(char_id, char_instance, template_repo)
                for char_id, char_instance in game_state.party.items()
            ]
        )
        dynamic_context_parts.append(party_status)

        location_info = f"Current Location: {game_state.current_location.name}\nDescription: {game_state.current_location.description}"
        dynamic_context_parts.append(location_info)

        combat_status = self.format_combat_state_for_prompt(
            game_state.combat, event_handler
        )
        dynamic_context_parts.append(combat_status)

        dynamic_context_content = "\n\n".join(dynamic_context_parts)
        dynamic_context_messages = [
            HumanMessage(content=f"CURRENT STATUS:\n{dynamic_context_content}")
        ]
        logger.debug(
            f"Created dynamic context message with {len(dynamic_context_parts)} parts"
        )

        # 5. RAG Context
        # Import here to avoid circular imports
        from app.services.rag.rag_context_builder import rag_context_builder

        force_new_query = player_action_for_rag_query is not None
        rag_context_content = ""
        if event_handler.rag_service:
            rag_context_content = rag_context_builder.get_rag_context_for_prompt(
                game_state,
                event_handler.rag_service,
                player_action_for_rag_query,
                all_chat_history,
                force_new_query,
            )

        rag_context_messages: List[HumanMessage] = []
        if rag_context_content:
            rag_context_messages.append(HumanMessage(content=rag_context_content))

        # 6. Convert last X history to LangChain messages
        recent_history_messages: List[BaseMessage] = []
        for msg in last_x_history_block:
            formatted_msg = self._format_message_for_history(msg)
            if formatted_msg:
                recent_history_messages.append(formatted_msg)

        # Calculate tokens for fixed components
        fixed_messages = (
            [SystemMessage(content=system_prompt)]
            + static_context_messages
            + dynamic_context_messages
            + rag_context_messages
            + recent_history_messages
        )

        fixed_token_count: int = sum(
            self._calculate_message_tokens(msg) for msg in fixed_messages
        )

        # Calculate remaining budget for main history
        remaining_budget: int = MAX_PROMPT_TOKENS_BUDGET - fixed_token_count

        # Use LangChain's trim_messages for token-aware truncation of main history
        if main_history_messages and remaining_budget > 0:
            try:
                # Trim messages to fit within budget, keeping most recent
                trimmed_main_history: List[BaseMessage] = trim_messages(
                    main_history_messages,
                    max_tokens=remaining_budget,
                    token_counter=self._calculate_message_tokens,
                    strategy="last",  # Keep most recent messages
                    allow_partial=False,  # Don't split messages
                )
            except Exception as e:
                logger.warning(
                    f"Error trimming messages with LangChain, falling back to manual trimming: {e}"
                )
                # Fallback to manual trimming
                trimmed_main_history = []
                current_tokens = 0
                history_msg: BaseMessage
                for history_msg in reversed(main_history_messages):
                    msg_tokens = self._calculate_message_tokens(history_msg)
                    if current_tokens + msg_tokens <= remaining_budget:
                        trimmed_main_history.insert(0, history_msg)
                        current_tokens += msg_tokens
                    else:
                        break
        else:
            trimmed_main_history = []

        # Format the final prompt using the template
        prompt_values = {
            "system_prompt": system_prompt,
            "main_history": trimmed_main_history,
            "static_context": static_context_messages,
            "dynamic_context": dynamic_context_messages,
            "rag_context": rag_context_messages,
            "recent_history": recent_history_messages,
        }

        # Log what we're passing to the template
        logger.debug(
            f"Prompt template inputs - main_history: {len(trimmed_main_history)} msgs, "
            f"static_context: {len(static_context_messages)} msgs, "
            f"dynamic_context: {len(dynamic_context_messages)} msgs, "
            f"rag_context: {len(rag_context_messages)} msgs, "
            f"recent_history: {len(recent_history_messages)} msgs"
        )

        # Generate the final messages
        prompt_value = self.prompt_template.invoke(prompt_values)
        final_messages = prompt_value.to_messages()

        # Log what came out of the template
        logger.debug(f"Template generated {len(final_messages)} messages")

        # If initial_instruction is provided, append it as the final message
        # This is for system-generated instructions (e.g., NPC turns, continuations)
        if initial_instruction:
            final_messages.append(HumanMessage(content=initial_instruction))
            logger.debug(
                f"Appended system instruction to prompt: {initial_instruction[:100]}..."
            )

        # Convert back to dict format for compatibility
        logger.debug(
            f"Converting {len(final_messages)} LangChain messages to dict format"
        )
        final_dict_messages = MessageConverter.from_langchain(final_messages)
        logger.debug(f"After conversion: {len(final_dict_messages)} dict messages")

        # Calculate final token count for logging
        total_tokens: int = sum(
            self._calculate_message_tokens(msg) for msg in final_messages
        )

        # Log the final prompt construction
        logger.info(
            f"Built AI prompt with {len(final_dict_messages)} messages (~{total_tokens} tokens)"
        )

        # Log prompt info
        history_truncated = len(main_history_messages) - len(trimmed_main_history)
        if history_truncated > 0:
            logger.debug(
                f"Truncated {history_truncated} older history messages due to token budget"
            )

        # Log individual messages with better detection of context messages
        logger.debug(
            "================================================================================="
        )
        msg_dict: Dict[str, str]
        for i, msg_dict in enumerate(final_dict_messages):
            content = str(msg_dict.get("content", ""))
            role = msg_dict["role"]

            # Identify message type
            msg_type = "unknown"
            if i == 0 and role == "system":
                msg_type = "system_prompt"
                logger.debug(
                    f"Prompt Message [{i}] ({role}) [SYSTEM PROMPT]: [CONTENT NOT LOGGED]"
                )
                continue
            elif content.startswith("CONTEXT INJECTION:"):
                msg_type = "static_context"
            elif content.startswith("CURRENT STATUS:"):
                msg_type = "dynamic_context"
            elif content.startswith("RELEVANT KNOWLEDGE:"):
                msg_type = "rag_context"
            else:
                msg_type = "chat_history"

            content_preview = content
            if len(content_preview) > 1000:
                content_preview = content_preview[:1000] + "..."
            logger.debug(
                f"Prompt Message [{i}] ({role}) [{msg_type}]: {content_preview}"
            )
        logger.debug(
            "================================================================================="
        )

        return final_dict_messages


# Module-level function for backward compatibility
def build_ai_prompt_context(
    game_state: GameStateModel,
    event_handler: EventHandlerProtocol,
    player_action_for_rag_query: Optional[str] = None,
    initial_instruction: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Module-level function that maintains backward compatibility.
    Creates a PromptBuilder instance and delegates to it.
    """
    builder: PromptBuilder = PromptBuilder()
    return builder.build_ai_prompt_context(
        game_state, event_handler, player_action_for_rag_query, initial_instruction
    )
