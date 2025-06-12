"""
Protocol definition for knowledge base managers.
"""

from typing import Dict, List, Optional, Protocol

from langchain_core.documents import Document

from app.core.rag_interfaces import RAGResults
from app.models import LoreDataModel


class KnowledgeBaseProtocol(Protocol):
    """Protocol for knowledge base managers."""

    def search(
        self,
        query: str,
        kb_types: Optional[List[str]] = None,
        k: int = 3,
        score_threshold: float = 0.3,
    ) -> RAGResults:
        """Search across knowledge bases."""
        ...

    def add_campaign_lore(self, campaign_id: str, lore_data: LoreDataModel) -> None:
        """Add campaign-specific lore."""
        ...

    def add_event(
        self,
        campaign_id: str,
        event_summary: str,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add an event to campaign event log."""
        ...
