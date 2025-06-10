"""
LangChain-based knowledge base implementation for the RAG system.
Uses vector stores for semantic search instead of keyword matching.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import Config
from app.core.rag_interfaces import KnowledgeResult, RAGResults
from app.models.models import LoreDataModel

if TYPE_CHECKING:
    from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """
    Manages all knowledge bases using LangChain vector stores.
    Provides semantic search capabilities across different knowledge domains.
    """

    def __init__(self, embeddings_model: Optional[str] = None):
        """Initialize with specified embeddings model."""
        # Use configured model or default
        self.embeddings_model: str = embeddings_model or Config.RAG_EMBEDDINGS_MODEL
        self.embeddings: Optional[Embeddings] = None
        self._embeddings_initialized: bool = False
        self.vector_stores: Dict[str, InMemoryVectorStore] = {}

    def _ensure_embeddings_initialized(self) -> None:
        """Lazily initialize embeddings when first needed."""
        if self._embeddings_initialized:
            return

        # Import HuggingFaceEmbeddings here to avoid import issues when RAG is disabled
        try:
            from langchain_huggingface import HuggingFaceEmbeddings

            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embeddings_model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            self._embeddings_initialized = True
            logger.info(
                f"Initialized HuggingFace embeddings with model: {self.embeddings_model}"
            )
        except Exception as e:
            # Fallback without deprecated parameters
            logger.warning(f"Failed to initialize {self.embeddings_model}: {e}")
            try:
                from langchain_huggingface import HuggingFaceEmbeddings

                self.embeddings = HuggingFaceEmbeddings(
                    model_name=self.embeddings_model
                )
                self._embeddings_initialized = True
                logger.info(
                    f"Initialized HuggingFace embeddings (fallback) with model: {self.embeddings_model}"
                )
            except Exception as e2:
                logger.error(f"Failed to initialize embeddings: {e2}")
                raise
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.RAG_CHUNK_SIZE,
            chunk_overlap=Config.RAG_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._initialize_knowledge_bases()

    def _initialize_knowledge_bases(self) -> None:
        """Load all knowledge bases from JSON files."""
        knowledge_files = {
            "rules": "knowledge/rules/dnd5e_standard_rules.json",
            "spells": "knowledge/spells.json",
            "monsters": "knowledge/monsters.json",
            "equipment": "knowledge/equipment.json",
            "lore": "knowledge/lore/generic_fantasy_lore.json",
        }

        for kb_type, file_path in knowledge_files.items():
            self._load_knowledge_base(kb_type, file_path)

    def _load_knowledge_base(self, kb_type: str, file_path: str) -> None:
        """Load a single knowledge base from JSON and create vector store."""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Knowledge base file not found: {file_path}")
                return

            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Convert JSON data to documents
            documents = self._json_to_documents(data, kb_type)

            # Create vector store
            self._ensure_embeddings_initialized()
            if self.embeddings is None:
                logger.error(
                    f"Embeddings not initialized for knowledge base '{kb_type}'"
                )
                return
            vector_store = InMemoryVectorStore(self.embeddings)

            # Add documents if any
            if documents:
                # Split documents that are too long
                split_docs = []
                for doc in documents:
                    if len(doc.page_content) > 500:
                        splits = self.text_splitter.split_documents([doc])
                        split_docs.extend(splits)
                    else:
                        split_docs.append(doc)

                vector_store.add_documents(split_docs)
                self.vector_stores[kb_type] = vector_store
                logger.info(
                    f"Loaded {len(split_docs)} documents into '{kb_type}' knowledge base"
                )

        except Exception as e:
            logger.error(
                f"Error loading knowledge base '{kb_type}' from {file_path}: {e}"
            )

    def _json_to_documents(
        self, data: Dict[str, Any], source: str
    ) -> List[Document]:  # JUSTIFIED: handles various JSON structures
        """Convert JSON data to LangChain documents."""
        documents = []

        for key, value in data.items():
            # Format content based on value type
            if isinstance(value, str):
                content = f"{key}: {value}"
                metadata = {"key": key, "source": source, "type": "text"}

            elif isinstance(value, dict):
                # Format dict entries as structured text
                # If there's a 'name' field, use it as the primary identifier
                if "name" in value:
                    content_parts = [f"{value['name']}:"]
                else:
                    content_parts = [f"{key.replace('_', ' ').title()}:"]

                important_fields = [
                    "name",
                    "level",
                    "damage",
                    "range",
                    "duration",
                    "description",
                    "armor_class",
                    "hit_points",
                    "challenge",
                    "abilities",
                    "casting_time",
                    "components",
                ]

                # Add important fields first
                for field in important_fields:
                    if (
                        field in value and field != "name"
                    ):  # Skip name since it's already in header
                        content_parts.append(f"  {field}: {value[field]}")

                # Add other fields
                for k, v in value.items():
                    if k not in important_fields:
                        if isinstance(v, (str, int, float, bool)):
                            content_parts.append(f"  {k}: {v}")
                        elif isinstance(v, list) and len(v) <= 5:
                            content_parts.append(
                                f"  {k}: {', '.join(str(item) for item in v)}"
                            )

                content = "\n".join(content_parts)
                metadata = {
                    "key": key,
                    "source": source,
                    "type": "structured",
                    "name": value.get("name", key),
                }

            elif isinstance(value, list):
                content = f"{key}: {', '.join(str(item) for item in value[:10])}"
                metadata = {"key": key, "source": source, "type": "list"}

            else:
                content = f"{key}: {value!s}"
                metadata = {"key": key, "source": source, "type": "other"}

            documents.append(Document(page_content=content, metadata=metadata))

        return documents

    def search(
        self,
        query: str,
        kb_types: Optional[List[str]] = None,
        k: int = 3,
        score_threshold: float = 0.3,
    ) -> RAGResults:
        """
        Search across specified knowledge bases using semantic similarity.

        Args:
            query: Search query text
            kb_types: List of knowledge base types to search (None = all)
            k: Number of results per knowledge base
            score_threshold: Minimum similarity score threshold

        Returns:
            RAGResults containing the most relevant knowledge
        """
        import time

        start_time = time.time()

        # Ensure embeddings are initialized before searching
        self._ensure_embeddings_initialized()

        # Determine which knowledge bases to search
        search_kbs = kb_types if kb_types else list(self.vector_stores.keys())

        all_results = []
        total_queries = 0

        for kb_type in search_kbs:
            if kb_type not in self.vector_stores:
                continue

            vector_store = self.vector_stores[kb_type]
            total_queries += 1

            try:
                # Perform similarity search with scores
                docs_with_scores = vector_store.similarity_search_with_score(query, k=k)

                # Convert to KnowledgeResult format
                for doc, score in docs_with_scores:
                    # Convert distance to similarity score (lower distance = higher similarity)
                    # For cosine similarity, score is typically 0-2, with 0 being most similar
                    # Convert to 0-1 scale where 1 is most similar
                    similarity_score = max(0.0, 1.0 - (score / 2.0))

                    if similarity_score >= score_threshold:
                        result = KnowledgeResult(
                            content=doc.page_content,
                            source=kb_type,
                            relevance_score=similarity_score,
                            metadata=doc.metadata,
                        )
                        all_results.append(result)

            except Exception as e:
                logger.error(f"Error searching {kb_type} knowledge base: {e}")

        # Sort by relevance score and limit total results
        all_results.sort(key=lambda r: r.relevance_score, reverse=True)

        # Remove duplicates based on content similarity
        unique_results = []
        seen_content = set()

        for result in all_results:
            content_key = f"{result.source}:{result.content[:100]}"
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_results.append(result)

        # Take top results across all knowledge bases
        top_results = unique_results[:5]

        execution_time = (time.time() - start_time) * 1000

        return RAGResults(
            results=top_results,
            total_queries=total_queries,
            execution_time_ms=execution_time,
        )

    def add_campaign_lore(self, campaign_id: str, lore_data: LoreDataModel) -> None:
        """Add campaign-specific lore to a dedicated vector store."""
        kb_type = f"lore_{campaign_id}"

        # Create vector store if it doesn't exist
        if kb_type not in self.vector_stores:
            self._ensure_embeddings_initialized()
            if self.embeddings is None:
                logger.error("Embeddings not initialized")
                return
            self.vector_stores[kb_type] = InMemoryVectorStore(self.embeddings)

        # Convert lore data to documents
        lore_data_dict = lore_data.model_dump(
            mode="json"
        )  # Convert Pydantic model to dict
        documents = self._json_to_documents(lore_data_dict, kb_type)

        if documents:
            self.vector_stores[kb_type].add_documents(documents)
            logger.info(
                f"Added {len(documents)} lore entries for campaign {campaign_id}"
            )

    def add_event(
        self,
        campaign_id: str,
        event_summary: str,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add an event to campaign event log."""
        kb_type = f"events_{campaign_id}"

        # Create vector store if it doesn't exist
        if kb_type not in self.vector_stores:
            self._ensure_embeddings_initialized()
            if self.embeddings is None:
                logger.error("Embeddings not initialized")
                return
            self.vector_stores[kb_type] = InMemoryVectorStore(self.embeddings)

        # Create event document
        timestamp = datetime.now(timezone.utc).isoformat()
        content = f"[{timestamp[:10]}] {event_summary}"
        if keywords:
            content += f"\nKeywords: {', '.join(keywords)}"

        doc_metadata = {
            "timestamp": timestamp,
            "keywords": keywords or [],
            "source": kb_type,
            "type": "event",
        }
        if metadata:
            doc_metadata.update(metadata)

        document = Document(page_content=content, metadata=doc_metadata)
        self.vector_stores[kb_type].add_documents([document])

        logger.info(f"Added event to campaign {campaign_id}: {event_summary[:50]}...")
