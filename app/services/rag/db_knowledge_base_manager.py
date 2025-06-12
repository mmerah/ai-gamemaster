"""
Database-backed knowledge base implementation for the RAG system.
Uses SQLite vector search instead of in-memory vector stores.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, Union

import numpy as np
from langchain_core.documents import Document
from numpy.typing import NDArray
from sqlalchemy import text
from sqlalchemy.orm import Session

# Lazy import for sentence_transformers to avoid torch reimport issues
SentenceTransformer: Any = None

from app.config import Config
from app.core.rag_interfaces import KnowledgeResult, RAGResults
from app.database.connection import DatabaseManager
from app.database.models import (
    AbilityScore,
    Alignment,
    Background,
    Base,
    BaseContent,
    CharacterClass,
    Condition,
    DamageType,
    Equipment,
    Feat,
    Feature,
    Language,
    MagicItem,
    Monster,
    Proficiency,
    Race,
    Rule,
    RuleSection,
    Skill,
    Spell,
    Subclass,
    Subrace,
    Trait,
)
from app.models import LoreDataModel

logger = logging.getLogger(__name__)


class DummySentenceTransformer:
    """Fallback sentence transformer for when the real one can't be loaded."""

    def __init__(self) -> None:
        """Initialize dummy transformer."""
        logger.warning("Using DummySentenceTransformer - embeddings will be random!")
        self.embedding_dimension = 384  # Default dimension for all-MiniLM-L6-v2

    def encode(
        self, texts: Union[str, List[str]], convert_to_numpy: bool = True, **kwargs: Any
    ) -> NDArray[np.float32]:
        """Generate random embeddings as a fallback."""
        if isinstance(texts, str):
            texts = [texts]

        # Generate consistent random embeddings based on text hash
        embeddings = []
        for text_item in texts:
            # Use hash of text as seed for consistency
            seed = hash(text_item) % (2**32)
            rng = np.random.RandomState(seed)
            embedding = rng.randn(self.embedding_dimension).astype(np.float32)
            # Normalize to unit length
            embedding = embedding / np.linalg.norm(embedding)
            embeddings.append(embedding)

        result = np.array(embeddings, dtype=np.float32)
        return result[0] if len(texts) == 1 else result


# Mapping of source names to table models
SOURCE_TO_MODEL: Dict[str, Type[BaseContent]] = {
    "spells": Spell,
    "monsters": Monster,
    "equipment": Equipment,
    "classes": CharacterClass,
    "features": Feature,
    "backgrounds": Background,
    "races": Race,
    "feats": Feat,
    "magic_items": MagicItem,
    "traits": Trait,
    "conditions": Condition,
    "skills": Skill,
    "rules": Rule,
    "rule_sections": RuleSection,
    "proficiencies": Proficiency,
    "damage_types": DamageType,
    "languages": Language,
    "alignments": Alignment,
    "ability_scores": AbilityScore,
    "subclasses": Subclass,
    "subraces": Subrace,
}

# Map knowledge base types to table names
KB_TYPE_TO_TABLES = {
    "rules": ["rules", "rule_sections"],
    "character_options": [
        "classes",
        "subclasses",
        "races",
        "subraces",
        "backgrounds",
        "feats",
        "traits",
    ],
    "spells": ["spells"],
    "monsters": ["monsters"],
    "equipment": ["equipment", "magic_items"],
    "mechanics": [
        "conditions",
        "skills",
        "proficiencies",
        "damage_types",
        "languages",
        "alignments",
        "ability_scores",
    ],
}


class DbKnowledgeBaseManager:
    """
    Database-backed knowledge base manager using SQLite vector search.
    Much faster than loading all data into memory with embeddings.
    """

    def __init__(
        self, db_manager: DatabaseManager, embeddings_model: Optional[str] = None
    ):
        """Initialize with database manager."""
        self.db_manager = db_manager
        self.embeddings_model: str = embeddings_model or Config.RAG_EMBEDDINGS_MODEL
        self._sentence_transformer: Optional[Any] = None

        # Cache for campaign-specific data (still needs in-memory storage)
        self.campaign_data: Dict[str, List[Document]] = {}

        # Lore data loaded from JSON (temporary until migrated to DB)
        self.lore_documents: List[Document] = []
        self._load_lore_knowledge_base()

    def _get_sentence_transformer(self) -> Any:
        """Lazily load sentence transformer model."""
        if self._sentence_transformer is None:
            # Use a dummy transformer for testing when import fails
            try:
                # Import only when needed to avoid torch reimport issues
                global SentenceTransformer
                if SentenceTransformer is None:
                    import importlib.util
                    import subprocess
                    import sys

                    # Check if it's already imported and working
                    if "sentence_transformers" in sys.modules:
                        try:
                            ST = sys.modules[
                                "sentence_transformers"
                            ].SentenceTransformer
                            # Test if we can instantiate it
                            test_model = ST("sentence-transformers/all-MiniLM-L6-v2")
                            del test_model  # Clean up test instance
                            SentenceTransformer = ST
                            logger.debug("Using already-imported SentenceTransformer")
                        except Exception:
                            # Module exists but is broken, remove it
                            del sys.modules["sentence_transformers"]
                            logger.debug("Removed broken sentence_transformers module")

                    if SentenceTransformer is None:
                        # Try a subprocess-based import to isolate the import
                        try:
                            # Test if we can import in a subprocess
                            result = subprocess.run(
                                [
                                    sys.executable,
                                    "-c",
                                    'import sentence_transformers; print("OK")',
                                ],
                                capture_output=True,
                                text=True,
                                timeout=5,
                            )
                            if result.returncode == 0 and "OK" in result.stdout:
                                # Safe to import
                                from sentence_transformers import (
                                    SentenceTransformer as ST,
                                )

                                SentenceTransformer = ST
                                logger.debug(
                                    "Successfully imported SentenceTransformer"
                                )
                            else:
                                raise ImportError("Subprocess import test failed")
                        except Exception as e:
                            logger.warning(f"Subprocess import test failed: {e}")
                            # Use fallback implementation
                            raise ImportError(
                                "Cannot safely import sentence_transformers"
                            )

                logger.info(
                    f"Loading sentence transformer model: {self.embeddings_model}"
                )
                self._sentence_transformer = SentenceTransformer(self.embeddings_model)

            except (ImportError, Exception) as e:
                logger.warning(
                    f"Failed to load SentenceTransformer, using fallback: {e}"
                )
                # Use a fallback that generates random embeddings for testing
                self._sentence_transformer = DummySentenceTransformer()

        return self._sentence_transformer

    def _load_lore_knowledge_base(self) -> None:
        """Load lore from JSON file (temporary until migrated to DB)."""
        file_path = "knowledge/lore/generic_fantasy_lore.json"
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Lore file not found: {file_path}")
                return

            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Convert to documents
            self.lore_documents = self._json_to_documents(data, "lore")
            logger.info(f"Loaded {len(self.lore_documents)} lore documents")
        except Exception as e:
            logger.error(f"Error loading lore: {e}")

    def _json_to_documents(self, data: Dict[str, Any], source: str) -> List[Document]:
        """Convert JSON data to documents (for lore and campaign data)."""
        documents = []

        for key, value in data.items():
            if isinstance(value, str):
                content = f"{key}: {value}"
                metadata = {"key": key, "source": source, "type": "text"}
            elif isinstance(value, dict):
                content_parts = [f"{key.replace('_', ' ').title()}:"]
                for k, v in value.items():
                    if isinstance(v, (str, int, float, bool)):
                        content_parts.append(f"  {k}: {v}")
                content = "\n".join(content_parts)
                metadata = {"key": key, "source": source, "type": "structured"}
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
        Search across specified knowledge bases using database vector search.

        Args:
            query: Search query text
            kb_types: List of knowledge base types to search (None = all)
            k: Number of results per knowledge base
            score_threshold: Minimum similarity score threshold

        Returns:
            RAGResults containing the most relevant knowledge
        """
        start_time = time.time()

        # Generate embedding for query
        try:
            model = self._get_sentence_transformer()
            query_embedding = model.encode(query, convert_to_numpy=True).astype(
                np.float32
            )
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            # Return empty results if embedding generation fails
            return RAGResults(
                results=[],
                total_queries=0,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Determine which tables to search
        tables_to_search = set()
        search_kbs = kb_types if kb_types else list(KB_TYPE_TO_TABLES.keys())

        for kb_type in search_kbs:
            if kb_type in KB_TYPE_TO_TABLES:
                tables_to_search.update(KB_TYPE_TO_TABLES[kb_type])

        all_results = []
        total_queries = 0

        # Search database tables
        with self.db_manager.get_session() as session:
            for table_name in tables_to_search:
                if table_name not in SOURCE_TO_MODEL:
                    continue

                model_class = SOURCE_TO_MODEL[table_name]
                total_queries += 1

                try:
                    # Use vector similarity search
                    results = self._vector_search(
                        session, model_class, table_name, query_embedding, k
                    )

                    for entity, distance in results:
                        # Convert distance to similarity score
                        # For L2 distance, smaller is better
                        # Normalize to 0-1 where 1 is most similar
                        similarity_score = 1.0 / (1.0 + distance)

                        if similarity_score >= score_threshold:
                            # Convert entity to document format
                            content = self._entity_to_text(entity, table_name)
                            result = KnowledgeResult(
                                content=content,
                                source=table_name,
                                relevance_score=similarity_score,
                                metadata={
                                    "index": entity.index,
                                    "name": entity.name,
                                    "table": table_name,
                                },
                            )
                            all_results.append(result)

                except Exception as e:
                    logger.error(f"Error searching {table_name}: {e}")

        # Also search lore (until migrated to DB)
        if "lore" in search_kbs or not kb_types:
            lore_results = self._search_lore_documents(
                query, query_embedding, k, score_threshold
            )
            all_results.extend(lore_results)
            total_queries += 1

        # Search campaign-specific data if any
        for campaign_id, docs in self.campaign_data.items():
            if (
                f"lore_{campaign_id}" in search_kbs
                or f"events_{campaign_id}" in search_kbs
            ):
                campaign_results = self._search_documents(
                    docs, query_embedding, k, score_threshold
                )
                all_results.extend(campaign_results)
                total_queries += 1

        # Sort by relevance and limit
        all_results.sort(key=lambda r: r.relevance_score, reverse=True)

        # Remove duplicates
        unique_results = []
        seen_content = set()

        for result in all_results:
            content_key = f"{result.source}:{result.content[:100]}"
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_results.append(result)

        top_results = unique_results[:5]
        execution_time = (time.time() - start_time) * 1000

        return RAGResults(
            results=top_results,
            total_queries=total_queries,
            execution_time_ms=execution_time,
        )

    def _vector_search(
        self,
        session: Session,
        model_class: Type[BaseContent],
        table_name: str,
        query_embedding: NDArray[np.float32],
        k: int,
    ) -> List[tuple[BaseContent, float]]:
        """
        Perform vector similarity search on a specific table.

        Returns list of (entity, distance) tuples.
        """
        # Convert embedding to bytes for SQL
        query_bytes = query_embedding.astype(np.float32).tobytes()

        # Use raw SQL for vector search since SQLAlchemy doesn't have native support
        # Note: sqlite-vec uses vec_distance_l2 for L2 distance
        sql = text(f"""
            SELECT *, vec_distance_l2(embedding, :query_vec) as distance
            FROM {table_name}
            WHERE embedding IS NOT NULL
            ORDER BY distance
            LIMIT :k
        """)

        results = []
        try:
            rows = session.execute(sql, {"query_vec": query_bytes, "k": k}).fetchall()

            for row in rows:
                # Reconstruct entity from row
                entity_data = dict(row._mapping)
                distance = entity_data.pop("distance")

                # Create instance using model class
                entity = model_class(**entity_data)
                results.append((entity, distance))

        except Exception as e:
            # Fallback to non-vector search if sqlite-vec not available
            logger.warning(
                f"Vector search failed for {table_name}, using fallback: {e}"
            )
            # For tests, we need to search all entities to ensure correct results
            # In production, sqlite-vec should always be available
            entities = (
                session.query(model_class)
                .filter(model_class.embedding.isnot(None))
                .all()
            )

            # Compute distances for all entities
            for entity in entities:
                if entity.embedding is not None:
                    # Use cosine similarity instead of L2 distance for better results
                    dot_product = np.dot(query_embedding, entity.embedding)
                    norm_product = np.linalg.norm(query_embedding) * np.linalg.norm(
                        entity.embedding
                    )
                    similarity = dot_product / norm_product if norm_product > 0 else 0
                    # Convert similarity to distance (lower is better)
                    distance = 1.0 - similarity
                    # Ensure distance is a Python float, not numpy scalar
                    distance_float = float(
                        distance.item() if hasattr(distance, "item") else distance
                    )
                    results.append((entity, distance_float))

            # Sort by distance and take top k
            results.sort(key=lambda x: x[1])
            results = results[:k]

        return results

    def _entity_to_text(self, entity: BaseContent, entity_type: str) -> str:
        """Convert a database entity to text representation."""
        parts = [f"{entity_type.rstrip('s').title()}: {entity.name}"]

        # Add type-specific information based on entity type
        if isinstance(entity, Spell):
            if hasattr(entity, "level"):
                parts.append(f"Level {entity.level}")
            if hasattr(entity, "school") and entity.school:
                parts.append(f"School: {entity.school.get('name', 'Unknown')}")
            if hasattr(entity, "desc") and entity.desc:
                # Handle both JSON (list) and Text (string) desc fields
                desc_val: Any = entity.desc
                if isinstance(desc_val, list):
                    desc_text = " ".join(str(item) for item in desc_val)
                else:
                    desc_text = str(desc_val)
                parts.append(desc_text[:500])  # Limit description length

        elif isinstance(entity, Monster):
            if hasattr(entity, "type"):
                parts.append(f"Type: {entity.type}")
            if hasattr(entity, "challenge_rating"):
                parts.append(f"CR: {entity.challenge_rating}")
            if hasattr(entity, "hit_points"):
                parts.append(f"HP: {entity.hit_points}")

        elif isinstance(entity, Equipment):
            if hasattr(entity, "equipment_category") and entity.equipment_category:
                parts.append(
                    f"Category: {entity.equipment_category.get('name', 'Unknown')}"
                )
            if hasattr(entity, "cost") and entity.cost:
                parts.append(
                    f"Cost: {entity.cost.get('quantity', 0)} {entity.cost.get('unit', 'gp')}"
                )

        elif isinstance(entity, CharacterClass):
            if hasattr(entity, "hit_die"):
                parts.append(f"Hit Die: d{entity.hit_die}")

        # Add description for any entity that has it
        elif hasattr(entity, "desc") and entity.desc:
            # Handle both JSON (list) and Text (string) desc fields
            desc_value: Any = entity.desc
            if isinstance(desc_value, list):
                desc_text = " ".join(str(item) for item in desc_value)
            else:
                desc_text = str(desc_value)
            parts.append(desc_text[:500])

        return " ".join(parts)

    def _search_lore_documents(
        self,
        query: str,
        query_embedding: NDArray[np.float32],
        k: int,
        score_threshold: float,
    ) -> List[KnowledgeResult]:
        """Search lore documents in memory."""
        return self._search_documents(
            self.lore_documents, query_embedding, k, score_threshold
        )

    def _search_documents(
        self,
        documents: List[Document],
        query_embedding: NDArray[np.float32],
        k: int,
        score_threshold: float,
    ) -> List[KnowledgeResult]:
        """Search a list of documents using embeddings."""
        if not documents:
            return []

        results = []
        model = self._get_sentence_transformer()

        # Get embeddings for all documents
        doc_texts = [doc.page_content for doc in documents]
        doc_embeddings = model.encode(doc_texts, convert_to_numpy=True)

        # Compute similarities
        for i, (doc, doc_embedding) in enumerate(zip(documents, doc_embeddings)):
            # Cosine similarity
            similarity = np.dot(query_embedding, doc_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
            )

            if similarity >= score_threshold:
                result = KnowledgeResult(
                    content=doc.page_content,
                    source=doc.metadata.get("source", "unknown"),
                    relevance_score=float(similarity),
                    metadata=doc.metadata,
                )
                results.append(result)

        # Sort by relevance and return top k
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:k]

    def add_campaign_lore(self, campaign_id: str, lore_data: LoreDataModel) -> None:
        """Add campaign-specific lore."""
        kb_type = f"lore_{campaign_id}"

        # Convert lore data to documents
        lore_data_dict = lore_data.model_dump(mode="json")
        documents = self._json_to_documents(lore_data_dict, kb_type)

        # Store in memory for now
        self.campaign_data[kb_type] = documents
        logger.info(f"Added {len(documents)} lore entries for campaign {campaign_id}")

    def add_event(
        self,
        campaign_id: str,
        event_summary: str,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add an event to campaign event log."""
        kb_type = f"events_{campaign_id}"

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

        # Add to campaign data
        if kb_type not in self.campaign_data:
            self.campaign_data[kb_type] = []
        self.campaign_data[kb_type].append(document)

        logger.info(f"Added event to campaign {campaign_id}: {event_summary[:50]}...")
