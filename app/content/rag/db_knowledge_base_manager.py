"""
Database-backed knowledge base implementation for the RAG system.
Uses SQLite vector search instead of in-memory vector stores.
"""

import logging
import re
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional, Type

import numpy as np
from langchain_core.documents import Document
from sqlalchemy import text

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer as _SentenceTransformer

from app.content.models import (
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
from app.content.protocols import DatabaseManagerProtocol
from app.content.rag.hybrid_search import MultiTableHybridSearch
from app.content.rag.semantic_mapper import SemanticMapper
from app.content.types import Vector
from app.core.ai_interfaces import IKnowledgeBase
from app.models.rag import KnowledgeResult, LoreDataModel, RAGResults
from app.settings import get_settings

from .interfaces import IChunker

logger = logging.getLogger(__name__)

# Global cache for SentenceTransformer to avoid torch reimport issues
_global_sentence_transformer_cache: Optional["_SentenceTransformer"] = None


def clear_sentence_transformer_cache() -> None:
    """Clear the global sentence transformer cache. Useful for test cleanup."""
    global _global_sentence_transformer_cache
    _global_sentence_transformer_cache = None
    logger.info("Cleared global sentence transformer cache")


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
    ],
    "character_stats": [
        "ability_scores",
        "alignments",
        "languages",
    ],
}


class DbKnowledgeBaseManager(IKnowledgeBase):
    """
    Database-backed knowledge base manager using SQLite vector search.
    Much faster than loading all data into memory with embeddings.
    """

    # Whitelist of allowed table names for security
    ALLOWED_TABLE_NAMES = set(SOURCE_TO_MODEL.keys())

    def __init__(
        self,
        db_manager: DatabaseManagerProtocol,
        embeddings_model: Optional[str] = None,
        chunker: Optional[IChunker] = None,
    ):
        """Initialize with database manager.

        Args:
            db_manager: Database manager for vector searches
            embeddings_model: Optional embeddings model name
            chunker: Optional document chunker (defaults to MarkdownChunker)
        """
        self.db_manager = db_manager
        settings = get_settings()
        self.embeddings_model: str = embeddings_model or settings.rag.embeddings_model
        self._sentence_transformer: Optional["_SentenceTransformer"] = None

        # Initialize semantic mapper
        self.semantic_mapper = SemanticMapper()

        # Initialize chunker - default to MarkdownChunker if not provided
        if chunker is None:
            from .chunkers import MarkdownChunker

            self.chunker: IChunker = MarkdownChunker()
        else:
            self.chunker = chunker

        # Cache for campaign-specific data (still needs in-memory storage)
        self.campaign_data: Dict[str, List[Document]] = {}

        # Lore data loaded from JSON (temporary until migrated to DB)
        self.lore_documents: List[Document] = []
        self._load_lore_knowledge_base()

        # Initialize hybrid search
        self.hybrid_search_alpha = settings.rag.hybrid_search_alpha

        # Hybrid search needs the sentence transformer for embeddings
        self.hybrid_search = MultiTableHybridSearch(
            db_manager=db_manager,
            embedding_model=None,  # Will be set when transformer is loaded
            rrf_k=settings.rag.rrf_k,
        )

    def _get_sentence_transformer(self) -> "_SentenceTransformer":
        """Lazily load sentence transformer model."""
        global _global_sentence_transformer_cache

        # First check instance cache
        if self._sentence_transformer is not None:
            return self._sentence_transformer

        # Then check global cache to avoid reimport issues
        if _global_sentence_transformer_cache is not None:
            logger.info("Using globally cached SentenceTransformer instance")
            self._sentence_transformer = _global_sentence_transformer_cache
            return self._sentence_transformer

        try:
            # Import only when needed to avoid torch reimport issues
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading sentence transformer model: {self.embeddings_model}")
            self._sentence_transformer = SentenceTransformer(self.embeddings_model)

            # Cache globally to avoid reimport issues in tests
            _global_sentence_transformer_cache = self._sentence_transformer

            # Update hybrid search with the loaded model
            if self.hybrid_search.embedding_model is None:
                self.hybrid_search.embedding_model = self._sentence_transformer

        except ImportError as e:
            raise ImportError(
                "The 'sentence-transformers' and 'torch' packages are required for RAG. "
                "Please install them or set RAG_ENABLED=false in your .env file."
            ) from e
        except RuntimeError as e:
            if "already has a docstring" in str(e):
                # This happens when torch/numpy is reimported in tests
                # Try to use SentenceTransformer directly if it's already imported
                try:
                    import sys

                    if "sentence_transformers" in sys.modules:
                        from sentence_transformers import SentenceTransformer

                        logger.warning(
                            "Torch reimport issue detected. Using already-imported SentenceTransformer."
                        )
                        self._sentence_transformer = SentenceTransformer(
                            self.embeddings_model
                        )
                        _global_sentence_transformer_cache = self._sentence_transformer

                        # Update hybrid search with the loaded model
                        if self.hybrid_search.embedding_model is None:
                            self.hybrid_search.embedding_model = (
                                self._sentence_transformer
                            )
                    else:
                        raise
                except Exception:
                    logger.error(
                        "Torch reimport issue detected and recovery failed. "
                        "Consider running RAG tests in isolation."
                    )
                    raise e
            else:
                raise
        except Exception as e:
            logger.error(
                f"Failed to load SentenceTransformer model '{self.embeddings_model}': {e}"
            )
            raise

        return self._sentence_transformer

    def _sanitize_table_name(self, table_name: str) -> str:
        """
        Sanitize table name to prevent SQL injection.

        Only allows whitelisted table names that exist in SOURCE_TO_MODEL.

        Args:
            table_name: The table name to sanitize

        Returns:
            The sanitized table name

        Raises:
            ValueError: If the table name is not in the whitelist
        """
        # Check if table name is in whitelist
        if table_name not in self.ALLOWED_TABLE_NAMES:
            raise ValueError(f"Invalid table name: {table_name}")

        # Additional safety: ensure table name matches safe pattern
        # Only alphanumeric and underscores allowed
        if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
            raise ValueError(f"Invalid table name format: {table_name}")

        return table_name

    def _load_lore_knowledge_base(self) -> None:
        """Load available lores metadata (actual lore loaded per campaign)."""
        # We don't preload any lore - it's loaded per campaign
        # This is just a placeholder to maintain the interface
        self.lore_documents = []
        logger.info("Lore loading deferred to campaign-specific context")

    def _json_to_documents(
        self, data: Dict[str, object], source: str
    ) -> List[Document]:
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
        content_pack_priority: Optional[List[str]] = None,
    ) -> RAGResults:
        """
        Search across specified knowledge bases using database vector search.

        Args:
            query: Search query text
            kb_types: List of knowledge base types to search (None = all)
            k: Number of results per knowledge base
            score_threshold: Minimum similarity score threshold
            content_pack_priority: List of content pack IDs in priority order

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

        # Determine which tables to search using semantic mapping
        search_kbs = kb_types if kb_types else list(KB_TYPE_TO_TABLES.keys())

        # Use semantic mapper to translate conceptual to concrete types
        concrete_kb_types = self.semantic_mapper.map_to_concrete_types(search_kbs)

        # Map concrete types to actual database tables
        tables_to_search = set()
        for kb_type in concrete_kb_types:
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
                    # Use hybrid search
                    # Ensure embedding model is loaded
                    if self.hybrid_search.embedding_model is None:
                        self.hybrid_search.embedding_model = (
                            self._get_sentence_transformer()
                        )

                    # Get hybrid search instance for this table
                    search_instance = self.hybrid_search.get_search_instance(table_name)

                    # Perform hybrid search
                    hybrid_results = search_instance.hybrid_search(
                        query, query_embedding, k, self.hybrid_search_alpha
                    )

                    # Convert results to entity objects
                    results = []
                    for entity_id, score in hybrid_results:
                        entity = (
                            session.query(model_class)
                            .filter_by(index=entity_id)
                            .first()
                        )
                        if entity:
                            # Convert score to distance (inverse for compatibility)
                            distance = 1.0 / score if score > 0 else float("inf")
                            results.append((entity, distance))

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
                    # Avoid formatting issues with numpy arrays in error messages
                    error_msg = str(e)
                    if "unsupported format string" in error_msg:
                        logger.error(
                            f"Error searching {table_name}: Format string error with embeddings"
                        )
                    else:
                        logger.error(f"Error searching {table_name}: {error_msg}")
                    # Don't completely fail - continue with other searches
                    continue

        # Search campaign-specific lore if available
        # Check if lore was requested either directly or through conceptual mapping
        should_search_lore = (
            "lore" in search_kbs
            or not kb_types
            or any(
                kb_type in ["lore", "adventure", "story", "exploration"]
                for kb_type in search_kbs
            )
        )

        if should_search_lore:
            # Search all campaign-specific lore data
            for campaign_id, docs in self.campaign_data.items():
                if campaign_id.startswith("lore_"):
                    campaign_results = self._search_documents(
                        docs, query_embedding, k, score_threshold
                    )
                    all_results.extend(campaign_results)
                    total_queries += 1

            # If no campaign lore loaded, search default lore documents
            if not any(cid.startswith("lore_") for cid in self.campaign_data):
                lore_results = self._search_lore_documents(
                    query, query_embedding, k, score_threshold
                )
                all_results.extend(lore_results)
                total_queries += 1

        # Search campaign-specific events if any
        for campaign_id, docs in self.campaign_data.items():
            if (
                campaign_id.startswith("events_")
                and f"events_{campaign_id[7:]}" in search_kbs
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

    def _entity_to_text(self, entity: BaseContent, entity_type: str) -> str:
        """Convert a database entity to text representation."""
        parts = [f"{entity_type.rstrip('s').title()}: {entity.name}"]

        # Add type-specific information based on entity type
        if isinstance(entity, Spell):
            if hasattr(entity, "level"):
                parts.append(f"Level {entity.level}")
            if hasattr(entity, "school") and entity.school is not None:
                # SQLAlchemy JSON columns are deserialized at runtime
                school_data = getattr(entity, "school")
                if isinstance(school_data, dict):
                    school_name = school_data.get("name", "Unknown")
                else:
                    school_name = str(school_data)
                parts.append(f"School: {school_name}")
            if hasattr(entity, "desc") and entity.desc:
                # Handle both JSON (list) and Text (string) desc fields
                desc_val = getattr(entity, "desc")
                if isinstance(desc_val, list):
                    desc_text = " ".join(str(item) for item in desc_val)
                else:
                    desc_text = str(desc_val)
                parts.append(desc_text[:500])  # Limit description length

        elif isinstance(entity, Monster):
            # Basic info
            if hasattr(entity, "type"):
                parts.append(f"Type: {entity.type}")
            if hasattr(entity, "size"):
                parts.append(f"Size: {entity.size}")
            if hasattr(entity, "alignment"):
                parts.append(f"Alignment: {entity.alignment}")
            if hasattr(entity, "challenge_rating"):
                parts.append(f"CR: {entity.challenge_rating}")
            if hasattr(entity, "xp"):
                parts.append(f"XP: {entity.xp}")

            # Defensive stats
            if hasattr(entity, "armor_class") and entity.armor_class:
                ac_info = getattr(entity, "armor_class")
                if isinstance(ac_info, list) and ac_info:
                    ac_val = (
                        ac_info[0].get("value", 0)
                        if isinstance(ac_info[0], dict)
                        else ac_info[0]
                    )
                    parts.append(f"AC: {ac_val}")
            if hasattr(entity, "hit_points"):
                parts.append(f"HP: {entity.hit_points}")
            if hasattr(entity, "hit_dice"):
                parts.append(f"Hit Dice: {entity.hit_dice}")

            # Ability scores
            if all(
                hasattr(entity, attr)
                for attr in [
                    "strength",
                    "dexterity",
                    "constitution",
                    "intelligence",
                    "wisdom",
                    "charisma",
                ]
            ):
                parts.append(
                    f"STR: {entity.strength}, DEX: {entity.dexterity}, CON: {entity.constitution}, INT: {entity.intelligence}, WIS: {entity.wisdom}, CHA: {entity.charisma}"
                )

            # Speed
            if hasattr(entity, "speed") and entity.speed:
                speed_info = getattr(entity, "speed")
                if isinstance(speed_info, dict):
                    speed_parts = []
                    if "walk" in speed_info:
                        speed_parts.append(f"Walk {speed_info['walk']}")
                    for move_type, dist in speed_info.items():
                        if move_type != "walk":
                            speed_parts.append(f"{move_type.capitalize()} {dist}")
                    if speed_parts:
                        parts.append(f"Speed: {', '.join(speed_parts)}")

            # Damage immunities/resistances/vulnerabilities
            if hasattr(entity, "damage_immunities") and entity.damage_immunities:
                damage_immunities = getattr(entity, "damage_immunities")
                parts.append(f"Damage Immunities: {', '.join(damage_immunities)}")
            if hasattr(entity, "damage_resistances") and entity.damage_resistances:
                damage_resistances = getattr(entity, "damage_resistances")
                parts.append(f"Damage Resistances: {', '.join(damage_resistances)}")
            if (
                hasattr(entity, "damage_vulnerabilities")
                and entity.damage_vulnerabilities
            ):
                damage_vulnerabilities = getattr(entity, "damage_vulnerabilities")
                parts.append(
                    f"Damage Vulnerabilities: {', '.join(damage_vulnerabilities)}"
                )

            # Condition immunities
            if hasattr(entity, "condition_immunities") and entity.condition_immunities:
                condition_immunities = getattr(entity, "condition_immunities")
                conditions = [
                    c.get("name", c) if isinstance(c, dict) else str(c)
                    for c in condition_immunities
                ]
                parts.append(f"Condition Immunities: {', '.join(conditions)}")

            # Senses
            if hasattr(entity, "senses") and entity.senses:
                senses_info = getattr(entity, "senses")
                if isinstance(senses_info, dict):
                    sense_parts = []
                    for sense, value in senses_info.items():
                        if sense != "passive_perception":
                            sense_parts.append(
                                f"{sense.replace('_', ' ').title()} {value}"
                            )
                    if "passive_perception" in senses_info:
                        sense_parts.append(
                            f"Passive Perception {senses_info['passive_perception']}"
                        )
                    if sense_parts:
                        parts.append(f"Senses: {', '.join(sense_parts)}")

            # Languages
            if hasattr(entity, "languages") and entity.languages:
                parts.append(f"Languages: {entity.languages}")

            # Special abilities
            if hasattr(entity, "special_abilities") and entity.special_abilities:
                special_abilities = getattr(entity, "special_abilities")
                ability_texts = []
                for ability in special_abilities[:3]:  # Limit to first 3 abilities
                    if isinstance(ability, dict):
                        name = ability.get("name", "Unknown")
                        desc = ability.get("desc", "")
                        ability_texts.append(f"{name}: {desc[:200]}...")
                if ability_texts:
                    parts.append(f"Special Abilities: {'; '.join(ability_texts)}")

            # Actions (summarized)
            if hasattr(entity, "actions") and entity.actions:
                actions = getattr(entity, "actions")
                action_names = []
                for action in actions:
                    if isinstance(action, dict):
                        action_names.append(action.get("name", "Unknown"))
                if action_names:
                    parts.append(f"Actions: {', '.join(action_names)}")

            # Legendary actions
            if hasattr(entity, "legendary_actions") and entity.legendary_actions:
                parts.append(f"Has Legendary Actions ({len(entity.legendary_actions)})")

            # Reactions
            if hasattr(entity, "reactions") and entity.reactions:
                reactions = getattr(entity, "reactions")
                reaction_names = []
                for reaction in reactions:
                    if isinstance(reaction, dict):
                        reaction_names.append(reaction.get("name", "Unknown"))
                if reaction_names:
                    parts.append(f"Reactions: {', '.join(reaction_names)}")

        elif isinstance(entity, Equipment):
            if hasattr(entity, "equipment_category") and entity.equipment_category:
                # Handle both dict and string formats
                equipment_category = getattr(entity, "equipment_category")
                if isinstance(equipment_category, dict):
                    category_name = equipment_category.get("name", "Unknown")
                else:
                    category_name = str(equipment_category)
                parts.append(f"Category: {category_name}")
            if hasattr(entity, "cost") and entity.cost:
                # Handle both dict and other formats
                cost_data = getattr(entity, "cost")
                if isinstance(cost_data, dict):
                    cost_text = (
                        f"{cost_data.get('quantity', 0)} {cost_data.get('unit', 'gp')}"
                    )
                else:
                    cost_text = str(cost_data)
                parts.append(f"Cost: {cost_text}")

        elif isinstance(entity, CharacterClass):
            if hasattr(entity, "hit_die"):
                parts.append(f"Hit Die: d{entity.hit_die}")

        # Add description for any entity that has it
        elif hasattr(entity, "desc") and entity.desc:
            # Handle both JSON (list) and Text (string) desc fields
            desc_value = getattr(entity, "desc")
            if isinstance(desc_value, list):
                desc_text = " ".join(str(item) for item in desc_value)
            else:
                desc_text = str(desc_value)
            parts.append(desc_text[:500])

        return " ".join(parts)

    def _search_lore_documents(
        self,
        query: str,
        query_embedding: Vector,
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
        query_embedding: Vector,
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

        # Convert lore data to documents using the chunker
        documents = []

        if lore_data.content:
            # Base metadata for all chunks
            base_metadata = {
                "source": kb_type,
                "lore_id": lore_data.id,
                "lore_name": lore_data.name,
            }

            # Use the chunker to split the content into manageable pieces
            # The chunker handles markdown structure (##, ###) and creates appropriate chunks
            documents = self.chunker.chunk(
                content=lore_data.content,
                metadata=base_metadata,
                chunk_size=500,
                chunk_overlap=50,
            )

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
