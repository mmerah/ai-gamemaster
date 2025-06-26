"""
D5e-specific database-backed knowledge base implementation.
Uses direct database queries instead of loading all data into memory.
"""

import logging
from typing import TYPE_CHECKING, List, Optional

from langchain_core.documents import Document

from app.content.protocols import DatabaseManagerProtocol
from app.content.rag.db_knowledge_base_manager import DbKnowledgeBaseManager
from app.content.service import ContentService
from app.models.rag import RAGResults

if TYPE_CHECKING:
    from app.content.rag.interfaces import IChunker

logger = logging.getLogger(__name__)


class D5eDbKnowledgeBaseManager(DbKnowledgeBaseManager):
    """
    Enhanced database-backed knowledge base manager for D5e data.
    Much faster than the in-memory version since embeddings are pre-computed.
    """

    def __init__(
        self,
        d5e_service: ContentService,
        db_manager: DatabaseManagerProtocol,
        embeddings_model: Optional[str] = None,
        chunker: Optional["IChunker"] = None,
    ):
        """
        Initialize with D5e data service and database manager.

        Args:
            d5e_service: The D5e data service instance (for compatibility)
            db_manager: Database manager for vector searches
            embeddings_model: Optional embeddings model name
            chunker: Optional document chunker (defaults to MarkdownChunker)
        """
        super().__init__(db_manager, embeddings_model, chunker)

        # Keep reference for compatibility but we don't actually use it
        # since we query the database directly
        self.d5e_service = d5e_service

        logger.info("D5e database-backed knowledge base manager initialized")

    def search_d5e(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        k: int = 5,
        score_threshold: float = 0.3,
        content_pack_priority: Optional[List[str]] = None,
    ) -> RAGResults:
        """
        Search D5e knowledge bases with category filtering.

        Args:
            query: Search query
            categories: Optional list of categories to search
                       (e.g., ['spells', 'monsters', 'character_options'])
            k: Number of results per category
            score_threshold: Minimum relevance score
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            RAGResults with most relevant D5e content
        """
        # Map categories to knowledge base types
        if categories:
            kb_types = []
            category_mapping = {
                "spells": "spells",
                "monsters": "monsters",
                "equipment": "equipment",
                "items": "equipment",
                "classes": "character_options",
                "races": "character_options",
                "character": "character_options",
                "rules": "rules",
                "mechanics": "mechanics",
                "conditions": "mechanics",
                "skills": "mechanics",
            }

            for cat in categories:
                kb_type = category_mapping.get(cat.lower(), cat)
                if kb_type not in kb_types:
                    kb_types.append(kb_type)
        else:
            # Search all D5e knowledge bases
            kb_types = [
                "rules",
                "character_options",
                "spells",
                "monsters",
                "equipment",
                "mechanics",
            ]

        return self.search(query, kb_types, k, score_threshold, content_pack_priority)

    def get_entity_details(
        self, entity_type: str, entity_index: str
    ) -> Optional[Document]:
        """
        Get detailed information about a specific D5e entity.

        Args:
            entity_type: Type of entity (e.g., 'spell', 'monster', 'class')
            entity_index: The index/id of the entity

        Returns:
            Document with entity details or None if not found
        """
        # Map entity type to table name
        table_mapping = {
            "spell": "spells",
            "monster": "monsters",
            "class": "classes",
            "race": "races",
            "background": "backgrounds",
            "feat": "feats",
            "equipment": "equipment",
            "magic-item": "magic_items",
            "condition": "conditions",
            "skill": "skills",
        }

        table_name = table_mapping.get(entity_type)
        if not table_name:
            logger.warning(f"Unknown entity type: {entity_type}")
            return None

        # Get the entity from database
        from app.content.rag.db_knowledge_base_manager import SOURCE_TO_MODEL

        if table_name not in SOURCE_TO_MODEL:
            return None

        model_class = SOURCE_TO_MODEL[table_name]

        try:
            with self.db_manager.get_session() as session:
                entity = (
                    session.query(model_class).filter_by(index=entity_index).first()
                )

                if entity:
                    # Convert to document format
                    content = self._entity_to_text(entity, table_name)
                    return Document(
                        page_content=content,
                        metadata={
                            "index": entity.index,
                            "name": entity.name,
                            "table": table_name,
                            "type": entity_type,
                        },
                    )
                else:
                    logger.warning(f"Entity not found: {entity_type}/{entity_index}")
                    return None

        except Exception as e:
            logger.error(f"Error getting entity details: {e}")
            return None
