"""
Main RAG service implementation using LangChain vector stores.
Greatly simplified from the previous keyword-based approach.
"""

import logging
import time
from typing import Any, List, Optional

from app.core.ai_interfaces import IKnowledgeBase, IRAGService
from app.models.game_state.main import GameStateModel
from app.models.rag import EventMetadataModel, QueryType, RAGQuery, RAGResults
from app.settings import get_settings
from app.utils.knowledge_loader import load_lore_info

from .knowledge_base import KnowledgeBaseManager
from .query_engine import RAGQueryEngineImpl

logger = logging.getLogger(__name__)


class RAGService(IRAGService):
    """
    Simplified RAG service using LangChain vector stores for semantic search.
    """

    def __init__(
        self,
        game_state_repo: Optional[Any] = None,
        ruleset_repo: Optional[Any] = None,
        lore_repo: Optional[Any] = None,
    ) -> None:
        """Initialize the RAG service with optional repository dependencies."""
        # Mark unused parameters that are kept for interface compatibility
        _ = ruleset_repo
        _ = lore_repo

        self.kb_manager: IKnowledgeBase = KnowledgeBaseManager()
        self.query_engine = RAGQueryEngineImpl()

        # Configuration from environment
        settings = get_settings()
        self.max_results_per_query = settings.rag.max_results_per_query
        self.max_total_results = settings.rag.max_total_results
        self.score_threshold = settings.rag.score_threshold

        # Repository dependencies (for future campaign-specific knowledge)
        self.game_state_repo = game_state_repo
        # Note: ruleset_repo and lore_repo are deprecated - using utility functions instead

        # Track current campaign context
        self.current_campaign_id: str | None = None

        logger.info("Simplified LangChain-based RAG Service initialized")

    def get_relevant_knowledge(
        self,
        action: str,
        game_state: GameStateModel,
        content_pack_priority: Optional[List[str]] = None,
    ) -> RAGResults:
        """
        Get relevant knowledge for a player action using semantic search.

        Args:
            action: The player's action text
            game_state: Current game state object
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            RAGResults with semantically relevant knowledge
        """
        start_time = time.time()

        try:
            # Ensure campaign-specific knowledge is loaded
            self._ensure_campaign_knowledge(game_state)

            # Analyze the action to determine what to search for
            queries = self.query_engine.analyze_action(action, game_state)

            if not queries:
                logger.debug(f"No queries generated for action: {action}")
                return RAGResults(execution_time_ms=(time.time() - start_time) * 1000)

            logger.debug(
                f"Generated {len(queries)} queries for action: '{action[:50]}...'"
            )

            # Execute semantic search for each query
            all_results = []
            seen_content = set()  # Track content to prevent duplicates

            for query in queries:
                # Determine which knowledge bases to search
                kb_types = (
                    query.knowledge_base_types if query.knowledge_base_types else None
                )

                # For spell queries, prioritize exact spell name matches
                if query.query_type == QueryType.SPELL_CASTING and query.context.get(
                    "spell_name"
                ):
                    spell_name = query.context["spell_name"]
                    # Search for the specific spell first
                    spell_results = self.kb_manager.search(
                        query=spell_name,  # Just the spell name for better matching
                        kb_types=["spells"],
                        k=2,
                        score_threshold=0.1,  # Lower threshold for specific searches
                        content_pack_priority=content_pack_priority,
                    )
                    for result in spell_results.results:
                        content_key = f"{result.source}:{result.content[:100]}"
                        if content_key not in seen_content:
                            seen_content.add(content_key)
                            all_results.append(result)

                # For any queries with creatures (including spell casting), search for the creature
                if query.context.get("creature"):
                    creature_name = query.context["creature"]
                    creature_results = self.kb_manager.search(
                        query=creature_name,  # Just the creature name
                        kb_types=["monsters"],
                        k=2,
                        score_threshold=0.1,
                        content_pack_priority=content_pack_priority,
                    )
                    for result in creature_results.results:
                        content_key = f"{result.source}:{result.content[:100]}"
                        if content_key not in seen_content:
                            seen_content.add(content_key)
                            all_results.append(result)

                # Also perform the general semantic search
                search_results = self.kb_manager.search(
                    query=query.query_text,
                    kb_types=kb_types,
                    k=self.max_results_per_query,
                    score_threshold=self.score_threshold,
                    content_pack_priority=content_pack_priority,
                )

                # Merge results with deduplication
                for result in search_results.results:
                    content_key = f"{result.source}:{result.content[:100]}"
                    if content_key not in seen_content:
                        seen_content.add(content_key)
                        all_results.append(result)

            # Boost scores for exact entity matches
            for result in all_results:
                # Boost spell matches
                for query in queries:
                    if query.context.get("spell_name") and result.source == "spells":
                        spell_name_lower = query.context["spell_name"].lower()
                        if spell_name_lower in result.content.lower():
                            result.relevance_score += 0.5  # Boost exact spell matches

                    # Boost creature matches
                    if query.context.get("creature") and result.source == "monsters":
                        creature_name_lower = query.context["creature"].lower()
                        if creature_name_lower in result.content.lower():
                            result.relevance_score += (
                                0.5  # Boost exact creature matches
                            )

            # Sort by relevance and limit total results
            all_results.sort(key=lambda r: r.relevance_score, reverse=True)
            final_results = all_results[: self.max_total_results]

            execution_time = (time.time() - start_time) * 1000

            if final_results:
                logger.info(
                    f"RAG retrieved {len(final_results)} results in {execution_time:.1f}ms"
                )
                logger.debug(
                    f"Top scores: {[round(r.relevance_score, 3) for r in final_results[:3]]}"
                )

            return RAGResults(
                results=final_results,
                total_queries=len(queries),
                execution_time_ms=execution_time,
            )

        except Exception as e:
            logger.error(f"Error in RAG knowledge retrieval: {e}", exc_info=True)
            return RAGResults(execution_time_ms=(time.time() - start_time) * 1000)

    def analyze_action(self, action: str, game_state: GameStateModel) -> List[RAGQuery]:
        """
        Analyze a player action and generate relevant queries.
        Exposed for testing and direct use.
        """
        return self.query_engine.analyze_action(action, game_state)

    def _ensure_campaign_knowledge(self, game_state: GameStateModel) -> None:
        """Load campaign-specific knowledge if available."""
        if not game_state or not hasattr(game_state, "campaign_id"):
            return

        campaign_id = game_state.campaign_id
        if campaign_id == self.current_campaign_id:
            return  # Already loaded

        self.current_campaign_id = campaign_id

        # Load campaign-specific lore if available
        if (
            hasattr(game_state, "active_lore_id")
            and game_state.active_lore_id
            and campaign_id
        ):
            lore_info = load_lore_info(game_state.active_lore_id)
            if lore_info:
                # lore_info is a LoreDataModel (Pydantic model)
                self.kb_manager.add_campaign_lore(campaign_id, lore_info)
                logger.info(f"Loaded campaign-specific lore for {campaign_id}")

    def add_event(
        self,
        campaign_id: str,
        event_summary: str,
        keywords: Optional[List[str]] = None,
        metadata: Optional[EventMetadataModel] = None,
    ) -> None:
        """Add an event to the campaign's event log."""
        # Convert EventMetadataModel to Dict[str, str] for knowledge base
        metadata_dict = None
        if metadata:
            metadata_dict = {
                "timestamp": metadata.timestamp,
                "location": metadata.location or "",
                "combat_active": str(metadata.combat_active)
                if metadata.combat_active is not None
                else "",
            }
            # Add participants if present
            if metadata.participants:
                metadata_dict["participants"] = ", ".join(metadata.participants)

        self.kb_manager.add_event(campaign_id, event_summary, keywords, metadata_dict)

    def configure_filtering(
        self, max_results: Optional[int] = None, score_threshold: Optional[float] = None
    ) -> None:
        """Configure search parameters."""
        if max_results is not None:
            self.max_total_results = max_results
            logger.info(f"Set max total results to {max_results}")

        if score_threshold is not None:
            self.score_threshold = score_threshold
            logger.info(f"Set score threshold to {score_threshold}")
