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

from .interfaces import IQueryEngine, IReranker

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
        kb_manager: Optional[IKnowledgeBase] = None,
        reranker: Optional[IReranker] = None,
        query_engine: Optional[IQueryEngine] = None,
    ) -> None:
        """Initialize the RAG service with optional repository dependencies."""
        # Mark unused parameters that are kept for interface compatibility
        _ = ruleset_repo
        _ = lore_repo

        # Knowledge base manager will be injected by the container
        self._kb_manager: Optional[IKnowledgeBase] = kb_manager

        # Reranker will be injected by the container
        self._reranker: Optional[IReranker] = reranker

        # Configuration from environment
        settings = get_settings()

        # Query engine will be injected by the container
        self._query_engine: Optional[IQueryEngine] = query_engine
        self.max_results_per_query = settings.rag.max_results_per_query
        self.max_total_results = settings.rag.max_total_results
        self.score_threshold = settings.rag.score_threshold

        # Repository dependencies (for future campaign-specific knowledge)
        self.game_state_repo = game_state_repo
        # Note: ruleset_repo and lore_repo are deprecated - using utility functions instead

        # Track current campaign context
        self.current_campaign_id: str | None = None

        logger.info("Simplified LangChain-based RAG Service initialized")

    @property
    def kb_manager(self) -> IKnowledgeBase:
        """Get the knowledge base manager, raising error if not set."""
        if self._kb_manager is None:
            raise RuntimeError(
                "Knowledge base manager not initialized. "
                "RAGService requires a kb_manager to be injected."
            )
        return self._kb_manager

    @kb_manager.setter
    def kb_manager(self, value: IKnowledgeBase) -> None:
        """Set the knowledge base manager."""
        self._kb_manager = value

    @property
    def reranker(self) -> Optional[IReranker]:
        """Get the reranker if set."""
        return self._reranker

    @reranker.setter
    def reranker(self, value: IReranker) -> None:
        """Set the reranker."""
        self._reranker = value

    @property
    def query_engine(self) -> IQueryEngine:
        """Get the query engine, raising error if not set."""
        if self._query_engine is None:
            raise RuntimeError(
                "Query engine not initialized. "
                "RAGService requires a query_engine to be injected."
            )
        return self._query_engine

    @query_engine.setter
    def query_engine(self, value: IQueryEngine) -> None:
        """Set the query engine."""
        self._query_engine = value

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
            for i, query in enumerate(queries):
                logger.debug(
                    f"  Query {i + 1}: type={query.query_type}, text='{query.query_text}', context={query.context}"
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
                            # Add query context to metadata for reranking
                            result.metadata["query_context"] = query.context
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
                            # Add query context to metadata for reranking
                            result.metadata["query_context"] = query.context
                            all_results.append(result)

                # For character info queries, prioritize exact class/race name matches
                if query.query_type == QueryType.CHARACTER_INFO:
                    if query.context.get("class"):
                        class_name = query.context["class"]
                        class_results = self.kb_manager.search(
                            query=class_name,
                            kb_types=["character_options"],
                            k=3,
                            score_threshold=0.1,
                            content_pack_priority=content_pack_priority,
                        )
                        for result in class_results.results:
                            content_key = f"{result.source}:{result.content[:100]}"
                            if content_key not in seen_content:
                                seen_content.add(content_key)
                                result.metadata["query_context"] = query.context
                                all_results.append(result)

                    if query.context.get("race"):
                        race_name = query.context["race"]
                        race_results = self.kb_manager.search(
                            query=race_name,
                            kb_types=["character_options"],
                            k=3,
                            score_threshold=0.1,
                            content_pack_priority=content_pack_priority,
                        )
                        for result in race_results.results:
                            content_key = f"{result.source}:{result.content[:100]}"
                            if content_key not in seen_content:
                                seen_content.add(content_key)
                                result.metadata["query_context"] = query.context
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
                        # Add query context to metadata for reranking
                        result.metadata["query_context"] = query.context
                        all_results.append(result)

            # Apply reranking if available
            if self.reranker:
                all_results = self.reranker.rerank(action, all_results)
            else:
                # Default sorting if no reranker
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
