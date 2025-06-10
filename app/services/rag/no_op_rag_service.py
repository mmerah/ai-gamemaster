"""
No-operation RAG service for testing purposes.
Returns empty results without loading embeddings or knowledge bases.
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.rag_interfaces import RAGQuery, RAGResults, RAGService
from app.models.models import GameStateModel

logger = logging.getLogger(__name__)


class NoOpRAGService(RAGService):
    """
    No-operation RAG service that returns empty results.
    Used for testing to avoid loading embeddings and knowledge bases.
    """

    def __init__(self) -> None:
        """Initialize no-op service."""
        logger.debug("NoOpRAGService initialized (testing mode)")

    def get_relevant_knowledge(
        self, action: str, game_state: GameStateModel
    ) -> RAGResults:
        """Return empty results without any processing."""
        return RAGResults(results=[], total_queries=0, execution_time_ms=0.0)

    def analyze_action(self, action: str, game_state: GameStateModel) -> List[RAGQuery]:
        """Return empty query list."""
        return []

    def add_event(
        self,
        campaign_id: str,
        event_summary: str,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """No-op for adding events."""
        logger.debug(f"NoOpRAGService: Ignoring event for campaign {campaign_id}")

    def configure_filtering(
        self, max_results: Optional[int] = None, score_threshold: Optional[float] = None
    ) -> None:
        """No-op for configuration."""
        logger.debug("NoOpRAGService: Ignoring configuration")

    def _ensure_campaign_kbs_loaded(self) -> None:
        """No-op for ensuring campaign knowledge bases are loaded."""
        logger.debug("NoOpRAGService: Ignoring campaign KB loading")
