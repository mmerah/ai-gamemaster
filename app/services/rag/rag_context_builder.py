"""
RAG Context Builder - Handles extraction and building of context for RAG queries.
Separated from prompts.py for better organization and testability.
"""

import logging
import re
from typing import List, Optional

from app.core.rag_interfaces import RAGService
from app.models import ChatMessageModel, GameStateModel
from app.models.rag import RAGContextDataModel

logger = logging.getLogger(__name__)


class RAGContextBuilder:
    """Builds context for RAG queries by extracting entities and information from player actions and game state."""

    def __init__(self) -> None:
        # Common D&D spells for better matching
        self.common_spells = [
            "fireball",
            "magic missile",
            "cure wounds",
            "healing word",
            "shield",
            "mage armor",
            "detect magic",
            "light",
            "prestidigitation",
            "eldritch blast",
            "sacred flame",
            "guidance",
            "thaumaturgy",
            "minor illusion",
            "toll the dead",
            "ice knife",
            "burning hands",
            "thunderwave",
            "misty step",
            "counterspell",
        ]

        # D&D 5e skills
        self.d5e_skills = [
            "acrobatics",
            "animal handling",
            "arcana",
            "athletics",
            "deception",
            "history",
            "insight",
            "intimidation",
            "investigation",
            "medicine",
            "nature",
            "perception",
            "performance",
            "persuasion",
            "religion",
            "sleight of hand",
            "stealth",
            "survival",
        ]

    def extract_spells_from_text(self, text: str) -> List[str]:
        """Extract spell names from text using common patterns."""
        spell_patterns = [
            r"cast(?:s|ing)?\s+([A-Z][a-z\s]+)",
            r"spell\s+([A-Z][a-z\s]+)",
            r"use(?:s|ing)?\s+([A-Z][a-z\s]+)",
            r"I\s+(?:cast|use)\s+([A-Z][a-z\s]+)",
        ]

        matches = []
        text_lower = text.lower()

        # Direct spell name matching
        for spell in self.common_spells:
            if spell in text_lower:
                matches.append(spell.title())

        # Pattern-based extraction
        for pattern in spell_patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            matches.extend([match.strip() for match in found if len(match.strip()) > 2])

        return list(set(matches))[:3]  # Return unique matches, limit to 3

    def extract_creatures_from_text(self, text: str) -> List[str]:
        """Extract creature names from text."""
        creature_patterns = [
            r"attack(?:s|ing)?\s+(?:the\s+)?([A-Z][a-z\s]+)",
            r"fight(?:s|ing)?\s+(?:the\s+)?([A-Z][a-z\s]+)",
            r"(?:the\s+)?([A-Z][a-z]+)\s+attacks?",
        ]

        matches = []
        for pattern in creature_patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            matches.extend([match.strip() for match in found if len(match.strip()) > 2])

        return list(set(matches))[:2]  # Return unique matches, limit to 2

    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skill names from text."""
        text_lower = text.lower()
        matches = []

        for skill in self.d5e_skills:
            if skill in text_lower:
                matches.append(skill.title())

        # Pattern for skill checks
        skill_patterns = [
            r"make\s+(?:a\s+)?([A-Z][a-z\s]+)\s+check",
            r"roll\s+(?:for\s+)?([A-Z][a-z\s]+)",
            r"([A-Z][a-z\s]+)\s+check",
        ]

        for pattern in skill_patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            for match in found:
                match = match.strip().lower()
                if match in self.d5e_skills:
                    matches.append(match.title())

        return list(set(matches))[:2]  # Return unique matches, limit to 2

    def extract_npcs_from_messages(self, messages: List[ChatMessageModel]) -> List[str]:
        """Extract NPC names from recent conversation."""
        npc_patterns = [
            r"([A-Z][a-z]+)\s+says?",
            r"([A-Z][a-z]+)\s+tells?",
            r"([A-Z][a-z]+)\s+(?:nods|shakes|smiles|frowns)",
            r"talk(?:s|ing)?\s+to\s+([A-Z][a-z]+)",
            r"speak(?:s|ing)?\s+(?:to|with)\s+([A-Z][a-z]+)",
        ]

        matches = []
        # Look at recent assistant and user messages
        recent_messages = [
            msg.content for msg in messages[-10:] if msg.role in ["assistant", "user"]
        ]

        for message in recent_messages:
            for pattern in npc_patterns:
                found = re.findall(pattern, message, re.IGNORECASE)
                matches.extend(
                    [
                        match.strip()
                        for match in found
                        if len(match.strip()) > 2
                        and match.strip() not in ["You", "The", "And"]
                    ]
                )

        # Remove duplicates while preserving order (most recent first)
        seen = set()
        unique_matches = []
        for match in reversed(matches):  # Reverse to get most recent first
            if match not in seen:
                seen.add(match)
                unique_matches.append(match)

        return unique_matches[:3]  # Return most recent unique matches, limit to 3

    def build_rag_context_data_for_query(
        self, query: str, game_state: GameStateModel, messages: List[ChatMessageModel]
    ) -> RAGContextDataModel:
        """Build context dictionary for RAG queries."""
        context_dict = {"action": query.lower()}

        # Add location context
        if game_state.current_location:
            context_dict["location"] = game_state.current_location.name

        # Extract specific entities from query using regex patterns
        spell_matches = self.extract_spells_from_text(query)
        if spell_matches:
            # Use first match
            context_dict["spell_name"] = spell_matches[0]

        creature_matches = self.extract_creatures_from_text(query)
        if creature_matches:
            # Use first match
            context_dict["creature"] = creature_matches[0]

        skill_matches = self.extract_skills_from_text(query)
        if skill_matches:
            # Use first match
            context_dict["skill"] = skill_matches[0]

        # Extract NPC names from recent conversation
        npc_matches = self.extract_npcs_from_messages(messages)
        if npc_matches:
            # Use most recent
            context_dict["npc_name"] = npc_matches[0]

        # Add recent events context
        recent_messages = [
            msg.content for msg in messages[-5:] if msg.role == "assistant"
        ]
        if recent_messages:
            context_dict["recent_events"] = " ".join(recent_messages)

        # Add combat context if active
        if hasattr(game_state, "combat") and game_state.combat:
            if game_state.combat.is_active:
                context_dict["in_combat"] = "true"
                current_index = game_state.combat.current_turn_index
                if 0 <= current_index < len(game_state.combat.combatants):
                    current_combatant = game_state.combat.combatants[current_index]
                    context_dict["current_combatant"] = current_combatant.name

        # Add action type context
        context_dict["action"] = query.lower()

        return RAGContextDataModel(**context_dict)

    def extract_rag_query(
        self, player_action_input: Optional[str], messages: List["ChatMessageModel"]
    ) -> str:
        """Extract query string from player action or messages."""
        # Primary query source - prioritize player_action_input, then last user message
        query = ""
        if player_action_input:
            query = player_action_input
            logger.debug(f"Using player_action_input as RAG query: {query[:50]}...")
        else:
            # Get the last user message as fallback - ChatMessageModel objects
            user_messages: List[str] = []
            for msg in messages:
                if msg.role == "user":
                    user_messages.append(msg.content)

            if user_messages:
                last_user_msg = user_messages[-1]
                # Extract raw content from formatted message
                query = self._extract_raw_content_from_formatted_message(last_user_msg)
                logger.debug(
                    f"Using extracted content from last user message as RAG query: {query[:50]}..."
                )

        if not query:
            logger.debug("No RAG query found from any source")

        return query

    def _extract_raw_content_from_formatted_message(
        self, formatted_message: str
    ) -> str:
        """Extract raw content from a formatted chat message.

        Handles formats like:
        - "I attack the goblin"
        - Thorin: "I attack the goblin"
        - Player: "Cast fireball"
        """
        message = formatted_message.strip()

        # Remove character name prefix if present
        if ": " in message:
            parts = message.split(": ", 1)
            if len(parts) == 2:
                message = parts[1].strip()

        # Remove surrounding quotes
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]

        return message.strip()

    def get_rag_context_for_prompt(
        self,
        game_state: GameStateModel,
        rag_service: RAGService,
        player_action_input: Optional[str],
        messages: List[ChatMessageModel],
        force_new_query: bool = False,
    ) -> str:
        """Get RAG context using LangChain semantic search with persistence."""
        if not rag_service:
            return ""

        # Check if we should reuse stored RAG context
        if (
            not force_new_query
            and not player_action_input
            and hasattr(game_state, "_last_rag_context")
            and game_state._last_rag_context
        ):
            # We're likely processing a dice roll submission - reuse stored context
            logger.info("=== REUSING STORED RAG CONTEXT ===")
            logger.info(f"Context preview: {game_state._last_rag_context[:200]}...")
            logger.info("=== END REUSED RAG CONTEXT ===")
            return game_state._last_rag_context

        # Extract query and context information
        query = self.extract_rag_query(player_action_input, messages)
        if not query:
            # Clear stored context if no query can be extracted
            if hasattr(game_state, "_last_rag_context"):
                game_state._last_rag_context = None
            return ""

        # Get relevant knowledge using semantic search
        try:
            results = rag_service.get_relevant_knowledge(query, game_state)

            if results.has_results():
                # Format results for prompt inclusion
                formatted_context = results.format_for_prompt()

                # Store the context for future use (e.g., during dice roll submission)
                if hasattr(game_state, "_last_rag_context"):
                    game_state._last_rag_context = formatted_context

                logger.info("=== LANGCHAIN RAG CONTEXT ===")
                logger.info(f"Query: {query[:100]}{'...' if len(query) > 100 else ''}")
                logger.info(
                    f"Retrieved {len(results.results)} results in {results.execution_time_ms:.1f}ms"
                )
                logger.info(f"Context preview: {formatted_context[:200]}...")
                logger.info("=== END RAG CONTEXT ===")

                return formatted_context
            else:
                # Clear stored context if no results found
                if hasattr(game_state, "_last_rag_context"):
                    game_state._last_rag_context = None
                logger.debug(f"No RAG context found for query: {query[:50]}...")
                return ""

        except Exception as e:
            logger.error(f"Error retrieving RAG context: {e}", exc_info=True)
            # Clear stored context on error
            if hasattr(game_state, "_last_rag_context"):
                game_state._last_rag_context = None
            return ""

    def clear_stored_rag_context(self, game_state: GameStateModel) -> None:
        """Clear stored RAG context when starting a new player action."""
        if hasattr(game_state, "_last_rag_context"):
            game_state._last_rag_context = None
            logger.debug("Cleared stored RAG context for new player action")


# Global instance for easy importing
rag_context_builder = RAGContextBuilder()
