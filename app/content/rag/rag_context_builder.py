"""
RAG Context Builder - Handles extraction and building of context for RAG queries.
Separated from prompts.py for better organization and testability.
"""

import logging
import re
from typing import List, Optional

from app.core.interfaces import IRAGService
from app.models.game_state import GameStateModel
from app.models.shared import ChatMessageModel

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
        rag_service: IRAGService,
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
            # Get content pack priority from game state
            content_pack_priority = getattr(game_state, "content_pack_priority", None)
            results = rag_service.get_relevant_knowledge(
                query, game_state, content_pack_priority
            )

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
