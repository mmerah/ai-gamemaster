"""AI and RAG system interfaces for the AI Game Master.

This module defines interfaces for AI response processing and
retrieval-augmented generation (RAG) systems.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from app.models.dice import DiceRequestModel
from app.models.game_state import GameStateModel
from app.models.rag import (
    LoreDataModel,
    RAGQuery,
    RAGResults,
)
from app.providers.ai.schemas import AIResponse


class IAIResponseProcessor(ABC):
    """Interface for processing AI responses."""

    @abstractmethod
    def process_response(
        self, ai_response: AIResponse, correlation_id: Optional[str] = None
    ) -> Tuple[List[DiceRequestModel], bool]:
        """Process an AI response and return pending requests and rerun flag."""
        pass

    @abstractmethod
    def find_combatant_id_by_name_or_id(self, identifier: str) -> Optional[str]:
        """Find combatant ID by name or direct ID match."""
        pass

    @abstractmethod
    def get_correlation_id(self) -> Optional[str]:
        """Get the current correlation ID for this processing session."""
        pass


class IRAGService(ABC):
    """Main RAG service interface - simplified with LangChain."""

    @abstractmethod
    def get_relevant_knowledge(
        self,
        action: str,
        game_state: GameStateModel,
        content_pack_priority: Optional[List[str]] = None,
    ) -> RAGResults:
        """Get relevant knowledge for a player action.

        Args:
            action: The player's action text
            game_state: Current game state
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            RAG results with relevant knowledge
        """
        pass

    @abstractmethod
    def analyze_action(self, action: str, game_state: GameStateModel) -> List[RAGQuery]:
        """Analyze a player action and generate relevant RAG queries."""
        pass


class IKnowledgeBase(ABC):
    """Protocol for knowledge base managers."""

    @abstractmethod
    def search(
        self,
        query: str,
        kb_types: Optional[List[str]] = None,
        k: int = 3,
        score_threshold: float = 0.3,
        content_pack_priority: Optional[List[str]] = None,
    ) -> RAGResults:
        """Search across knowledge bases.

        Args:
            query: Search query text
            kb_types: List of knowledge base types to search
            k: Number of results to return
            score_threshold: Minimum relevance score
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            RAG results with relevant knowledge
        """
        pass

    @abstractmethod
    def add_campaign_lore(self, campaign_id: str, lore_data: LoreDataModel) -> None:
        """Add campaign-specific lore."""
        pass

    @abstractmethod
    def add_event(
        self,
        campaign_id: str,
        event_summary: str,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add an event to campaign event log."""
        pass
