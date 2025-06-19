"""
D5e-integrated knowledge base implementation for the RAG system.
Enhances the existing KnowledgeBaseManager to use D5e data instead of static JSON files.
"""

import logging
from typing import TYPE_CHECKING, List, Optional

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore

from app.content.rag.d5e_document_converters import D5eDocumentConverters
from app.content.rag.knowledge_base import KnowledgeBaseManager
from app.content.service import ContentService
from app.models.rag import RAGResults

if TYPE_CHECKING:
    from app.content.repositories.db_repository_hub import D5eDbRepositoryHub

logger = logging.getLogger(__name__)


class D5eKnowledgeBaseManager(KnowledgeBaseManager):
    """
    Enhanced knowledge base manager that integrates D5e data.
    Extends the base KnowledgeBaseManager to load from D5e repositories.
    """

    def __init__(
        self,
        d5e_service: ContentService,
        embeddings_model: Optional[str] = None,
    ):
        """
        Initialize with D5e data service.

        Args:
            d5e_service: The D5e data service instance
            embeddings_model: Optional embeddings model name
        """
        # Initialize our attributes first before calling super
        self.d5e_service = d5e_service
        self.d5e_hub: D5eDbRepositoryHub = d5e_service._hub
        self._d5e_loaded = False

        # Now call parent init which will call our _initialize_knowledge_bases
        super().__init__(embeddings_model)

    def _initialize_knowledge_bases(self) -> None:
        """Load knowledge bases from D5e data and lore."""
        # Load D5e data
        self._load_d5e_knowledge_bases()

        # Also load lore from parent class (only remaining static file)
        super()._initialize_knowledge_bases()

    def _load_d5e_knowledge_bases(self) -> None:
        """Load all D5e data into separate vector stores."""
        if self._d5e_loaded:
            return

        logger.info("Loading D5e knowledge bases...")

        # Create separate knowledge bases for major categories
        knowledge_mappings = {
            # Core rules and mechanics
            "rules": self._load_rules_knowledge_base,
            # Character options
            "character_options": self._load_character_options_knowledge_base,
            # Spells
            "spells": self._load_spells_knowledge_base,
            # Monsters
            "monsters": self._load_monsters_knowledge_base,
            # Equipment and items
            "equipment": self._load_equipment_knowledge_base,
            # Game mechanics (conditions, damage types, etc.)
            "mechanics": self._load_mechanics_knowledge_base,
        }

        for kb_type, loader_func in knowledge_mappings.items():
            try:
                loader_func(kb_type)
            except Exception as e:
                logger.error(f"Error loading D5e knowledge base '{kb_type}': {e}")

        self._d5e_loaded = True
        logger.info("D5e knowledge bases loaded successfully")

    def _load_rules_knowledge_base(self, kb_type: str) -> None:
        """Load rules and rule sections into knowledge base."""
        documents = []

        # Load rules
        rules = self.d5e_hub.rules.list_all()
        for rule in rules:
            converter = D5eDocumentConverters.get_converter_for_category("rules")
            if converter:
                doc = converter(rule.model_dump())
                documents.append(doc)

        # Load rule sections
        rule_sections = self.d5e_hub.rule_sections.list_all()
        for section in rule_sections:
            converter = D5eDocumentConverters.get_converter_for_category(
                "rule-sections"
            )
            if converter:
                doc = converter(section.model_dump())
                documents.append(doc)

        self._create_vector_store(kb_type, documents)

    def _load_character_options_knowledge_base(self, kb_type: str) -> None:
        """Load all character creation options."""
        documents = []

        # Classes and subclasses
        for cls in self.d5e_hub.classes.list_all():
            doc = D5eDocumentConverters.class_to_document(cls)
            documents.append(doc)

        for subclass in self.d5e_hub.subclasses.list_all():
            doc = D5eDocumentConverters.subclass_to_document(subclass)
            documents.append(doc)

        # Races and subraces
        for race in self.d5e_hub.races.list_all():
            doc = D5eDocumentConverters.race_to_document(race)
            documents.append(doc)

        for subrace in self.d5e_hub.subraces.list_all():
            doc = D5eDocumentConverters.race_to_document(
                subrace
            )  # Same converter accepts Union[D5eRace, D5eSubrace]
            documents.append(doc)

        # Backgrounds
        for background in self.d5e_hub.backgrounds.list_all():
            doc = D5eDocumentConverters.background_to_document(background)
            documents.append(doc)

        # Feats and traits
        for feat in self.d5e_hub.feats.list_all():
            doc = D5eDocumentConverters.feat_to_document(feat)
            documents.append(doc)

        for trait in self.d5e_hub.traits.list_all():
            doc = D5eDocumentConverters.trait_to_document(trait)
            documents.append(doc)

        self._create_vector_store(kb_type, documents)

    def _load_spells_knowledge_base(self, kb_type: str) -> None:
        """Load all spells into dedicated knowledge base."""
        documents = []

        for spell in self.d5e_hub.spells.list_all():
            doc = D5eDocumentConverters.spell_to_document(spell)
            documents.append(doc)

        self._create_vector_store(kb_type, documents)
        logger.info(f"Loaded {len(documents)} spells into knowledge base")

    def _load_monsters_knowledge_base(self, kb_type: str) -> None:
        """Load all monsters into dedicated knowledge base."""
        documents = []

        for monster in self.d5e_hub.monsters.list_all():
            doc = D5eDocumentConverters.monster_to_document(monster)
            documents.append(doc)

        self._create_vector_store(kb_type, documents)
        logger.info(f"Loaded {len(documents)} monsters into knowledge base")

    def _load_equipment_knowledge_base(self, kb_type: str) -> None:
        """Load all equipment and magic items."""
        documents = []

        # Regular equipment
        for equipment in self.d5e_hub.equipment.list_all():
            doc = D5eDocumentConverters.equipment_to_document(equipment)
            documents.append(doc)

        # Magic items
        for item in self.d5e_hub.magic_items.list_all():
            doc = D5eDocumentConverters.magic_item_to_document(item)
            documents.append(doc)

        # Weapon properties
        for prop in self.d5e_hub.weapon_properties.list_all():
            converter = D5eDocumentConverters.get_converter_for_category(
                "weapon-properties"
            )
            if converter:
                doc = converter(prop.model_dump())
                documents.append(doc)

        self._create_vector_store(kb_type, documents)

    def _load_mechanics_knowledge_base(self, kb_type: str) -> None:
        """Load game mechanics: abilities, skills, conditions, etc."""
        documents = []

        # Ability scores
        for ability in self.d5e_hub.ability_scores.list_all():
            doc = D5eDocumentConverters.ability_score_to_document(ability)
            documents.append(doc)

        # Skills
        for skill in self.d5e_hub.skills.list_all():
            doc = D5eDocumentConverters.skill_to_document(skill)
            documents.append(doc)

        # Proficiencies
        for prof in self.d5e_hub.proficiencies.list_all():
            doc = D5eDocumentConverters.proficiency_to_document(prof)
            documents.append(doc)

        # Conditions
        for condition in self.d5e_hub.conditions.list_all():
            doc = D5eDocumentConverters.condition_to_document(condition)
            documents.append(doc)

        # Damage types
        for damage_type in self.d5e_hub.damage_types.list_all():
            doc = D5eDocumentConverters.damage_type_to_document(damage_type)
            documents.append(doc)

        # Languages
        for language in self.d5e_hub.languages.list_all():
            doc = D5eDocumentConverters.language_to_document(language)
            documents.append(doc)

        # Alignments
        for alignment in self.d5e_hub.alignments.list_all():
            doc = D5eDocumentConverters.alignment_to_document(alignment)
            documents.append(doc)

        self._create_vector_store(kb_type, documents)

    def _create_vector_store(self, kb_type: str, documents: List[Document]) -> None:
        """Create a vector store from documents."""
        if not documents:
            logger.warning(f"No documents to load for knowledge base '{kb_type}'")
            return

        # Ensure embeddings are initialized
        self._ensure_embeddings_initialized()
        if self.embeddings is None:
            logger.error(f"Embeddings not initialized for knowledge base '{kb_type}'")
            return

        # Create vector store
        vector_store = InMemoryVectorStore(self.embeddings)

        # Split documents that are too long
        split_docs = []
        for doc in documents:
            if len(doc.page_content) > 500:
                splits = self.text_splitter.split_documents([doc])
                split_docs.extend(splits)
            else:
                split_docs.append(doc)

        # Add documents to vector store
        vector_store.add_documents(split_docs)
        self.vector_stores[kb_type] = vector_store

        logger.info(
            f"Created '{kb_type}' knowledge base with {len(split_docs)} documents "
            f"(from {len(documents)} original)"
        )

    def search_d5e(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        k: int = 5,
        score_threshold: float = 0.3,
    ) -> RAGResults:
        """
        Search D5e knowledge bases with category filtering.

        Args:
            query: Search query
            categories: Optional list of categories to search
                       (e.g., ['spells', 'monsters', 'character_options'])
            k: Number of results per category
            score_threshold: Minimum relevance score

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

        return self.search(query, kb_types, k, score_threshold)

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
        try:
            # Handle each entity type with proper typing
            # Note: mypy has trouble inferring types through the repository property chain,
            # but the repositories are properly typed and return the correct model types
            if entity_type == "spell":
                spell = self.d5e_hub.spells.get_by_index(entity_index)
                if spell:
                    return D5eDocumentConverters.spell_to_document(spell)
            elif entity_type == "monster":
                monster = self.d5e_hub.monsters.get_by_index(entity_index)
                if monster:
                    return D5eDocumentConverters.monster_to_document(monster)
            elif entity_type == "class":
                cls = self.d5e_hub.classes.get_by_index(entity_index)
                if cls:
                    return D5eDocumentConverters.class_to_document(cls)
            elif entity_type == "race":
                race = self.d5e_hub.races.get_by_index(entity_index)
                if race:
                    return D5eDocumentConverters.race_to_document(race)
            elif entity_type == "background":
                background = self.d5e_hub.backgrounds.get_by_index(entity_index)
                if background:
                    return D5eDocumentConverters.background_to_document(background)
            elif entity_type == "feat":
                feat = self.d5e_hub.feats.get_by_index(entity_index)
                if feat:
                    return D5eDocumentConverters.feat_to_document(feat)
            elif entity_type == "equipment":
                equipment = self.d5e_hub.equipment.get_by_index(entity_index)
                if equipment:
                    return D5eDocumentConverters.equipment_to_document(equipment)
            elif entity_type == "magic-item":
                item = self.d5e_hub.magic_items.get_by_index(entity_index)
                if item:
                    return D5eDocumentConverters.magic_item_to_document(item)
            elif entity_type == "condition":
                condition = self.d5e_hub.conditions.get_by_index(entity_index)
                if condition:
                    return D5eDocumentConverters.condition_to_document(condition)
            elif entity_type == "skill":
                skill = self.d5e_hub.skills.get_by_index(entity_index)
                if skill:
                    return D5eDocumentConverters.skill_to_document(skill)
            else:
                logger.warning(f"Unknown entity type: {entity_type}")
                return None

            logger.warning(f"Entity not found: {entity_type}/{entity_index}")
            return None

        except Exception as e:
            logger.error(f"Error getting entity details: {e}")
            return None
