"""Tests for D5e Knowledge Base Manager."""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore

from app.content.rag.d5e_knowledge_base_manager import D5eKnowledgeBaseManager
from app.content.repositories.db_repository_hub import D5eDbRepositoryHub
from app.content.schemas.base import APIReference
from app.content.schemas.character import D5eClass, D5eRace
from app.content.schemas.spells_monsters import D5eMonster, D5eSpell
from app.content.service import ContentService
from app.core.interfaces import RAGResults


class TestD5eKnowledgeBaseManager:
    """Test D5e Knowledge Base Manager functionality."""

    @pytest.fixture
    def mock_d5e_service(self) -> MagicMock:
        """Create a mock D5e data service."""
        service = MagicMock(spec=ContentService)

        # Mock the repository hub
        hub = MagicMock(spec=D5eDbRepositoryHub)
        service._hub = hub

        # Mock repositories
        hub.spells = MagicMock()
        hub.monsters = MagicMock()
        hub.classes = MagicMock()
        hub.races = MagicMock()
        hub.subclasses = MagicMock()
        hub.subraces = MagicMock()
        hub.backgrounds = MagicMock()
        hub.feats = MagicMock()
        hub.traits = MagicMock()
        hub.equipment = MagicMock()
        hub.magic_items = MagicMock()
        hub.weapon_properties = MagicMock()
        hub.ability_scores = MagicMock()
        hub.skills = MagicMock()
        hub.proficiencies = MagicMock()
        hub.conditions = MagicMock()
        hub.damage_types = MagicMock()
        hub.languages = MagicMock()
        hub.alignments = MagicMock()
        hub.rules = MagicMock()
        hub.rule_sections = MagicMock()

        return service

    @pytest.fixture
    def sample_spell(self) -> D5eSpell:
        """Create a sample spell."""
        return D5eSpell(
            index="magic-missile",
            name="Magic Missile",
            level=1,
            school=APIReference(
                index="evocation", name="Evocation", url="/api/magic-schools/evocation"
            ),
            casting_time="1 action",
            range="120 feet",
            components=["V", "S"],
            duration="Instantaneous",
            concentration=False,
            ritual=False,
            desc=["You create three glowing darts of magical force."],
            classes=[
                APIReference(index="wizard", name="Wizard", url="/api/classes/wizard")
            ],
            subclasses=[],
            url="/api/spells/magic-missile",
        )

    @pytest.fixture
    def sample_monster(self) -> D5eMonster:
        """Create a sample monster."""
        return D5eMonster(
            index="goblin",
            name="Goblin",
            size="Small",
            type="humanoid",
            alignment="neutral evil",
            armor_class=[{"type": "natural", "value": 15}],
            hit_points=7,
            hit_points_roll="2d6",
            hit_dice="2d6",
            speed={"walk": "30 ft."},
            strength=8,
            dexterity=14,
            constitution=10,
            intelligence=10,
            wisdom=8,
            charisma=8,
            proficiencies=[],
            damage_vulnerabilities=[],
            damage_resistances=[],
            damage_immunities=[],
            condition_immunities=[],
            senses={},
            languages="Common, Goblin",
            challenge_rating=0.25,
            xp=50,
            proficiency_bonus=2,
            actions=[],
            url="/api/monsters/goblin",
        )

    @patch("app.content.rag.d5e_knowledge_base_manager.logger")
    def test_initialization(
        self, mock_logger: MagicMock, mock_d5e_service: MagicMock
    ) -> None:
        """Test D5e knowledge base manager initialization."""
        manager = D5eKnowledgeBaseManager(mock_d5e_service)

        assert manager.d5e_service == mock_d5e_service
        assert manager.d5e_hub == mock_d5e_service._hub
        # After initialization, D5e data should be loaded
        assert manager._d5e_loaded

    @patch("langchain_huggingface.HuggingFaceEmbeddings")
    @patch("app.content.rag.d5e_knowledge_base_manager.logger")
    def test_load_spells_knowledge_base(
        self,
        mock_logger: MagicMock,
        mock_embeddings: MagicMock,
        mock_d5e_service: MagicMock,
        sample_spell: D5eSpell,
    ) -> None:
        """Test loading spells into knowledge base."""
        # Setup
        mock_d5e_service._hub.spells.list_all.return_value = [sample_spell]
        manager = D5eKnowledgeBaseManager(mock_d5e_service)

        # Mock embeddings initialization
        manager._embeddings_initialized = True
        manager.embeddings = mock_embeddings.return_value

        # Execute
        manager._load_spells_knowledge_base("spells")

        # Verify
        assert "spells" in manager.vector_stores
        mock_logger.info.assert_called_with("Loaded 1 spells into knowledge base")

    @patch("langchain_huggingface.HuggingFaceEmbeddings")
    @patch("app.content.rag.d5e_knowledge_base_manager.logger")
    def test_load_monsters_knowledge_base(
        self,
        mock_logger: MagicMock,
        mock_embeddings: MagicMock,
        mock_d5e_service: MagicMock,
        sample_monster: D5eMonster,
    ) -> None:
        """Test loading monsters into knowledge base."""
        # Setup
        mock_d5e_service._hub.monsters.list_all.return_value = [sample_monster]
        manager = D5eKnowledgeBaseManager(mock_d5e_service)

        # Mock embeddings initialization
        manager._embeddings_initialized = True
        manager.embeddings = mock_embeddings.return_value

        # Execute
        manager._load_monsters_knowledge_base("monsters")

        # Verify
        assert "monsters" in manager.vector_stores
        mock_logger.info.assert_called_with("Loaded 1 monsters into knowledge base")

    @patch("langchain_huggingface.HuggingFaceEmbeddings")
    def test_search_d5e_with_categories(
        self, mock_embeddings: MagicMock, mock_d5e_service: MagicMock
    ) -> None:
        """Test searching D5e knowledge with category filtering."""
        manager = D5eKnowledgeBaseManager(mock_d5e_service)

        # Mock vector stores
        manager.vector_stores = {
            "spells": MagicMock(spec=InMemoryVectorStore),
            "monsters": MagicMock(spec=InMemoryVectorStore),
            "character_options": MagicMock(spec=InMemoryVectorStore),
        }

        # Mock embeddings
        manager._embeddings_initialized = True
        manager.embeddings = mock_embeddings.return_value

        # Mock search results
        mock_doc = Document(
            page_content="Magic Missile spell",
            metadata={"source": "spells", "index": "magic-missile"},
        )
        mock_vector_store = MagicMock()
        mock_vector_store.similarity_search_with_score.return_value = [
            (mock_doc, 0.1)  # Low score means high similarity
        ]
        manager.vector_stores["spells"] = mock_vector_store

        # Execute search
        results = manager.search_d5e("magic missile", categories=["spells"])

        # Verify
        assert isinstance(results, RAGResults)
        assert len(results.results) == 1
        assert results.results[0].content == "Magic Missile spell"
        assert results.results[0].source == "spells"

    def test_search_d5e_category_mapping(self, mock_d5e_service: MagicMock) -> None:
        """Test category name mapping in search."""
        manager = D5eKnowledgeBaseManager(mock_d5e_service)

        # Mock the search method
        with patch.object(manager, "search") as mock_search:
            mock_search.return_value = RAGResults(
                results=[], total_queries=1, execution_time_ms=10.0
            )

            # Test various category mappings
            manager.search_d5e("query", categories=["classes", "items"])

            # Verify mapped categories
            mock_search.assert_called_once_with(
                "query", ["character_options", "equipment"], 5, 0.3
            )

    @patch("langchain_huggingface.HuggingFaceEmbeddings")
    def test_get_entity_details(
        self,
        mock_embeddings: MagicMock,
        mock_d5e_service: MagicMock,
        sample_spell: D5eSpell,
    ) -> None:
        """Test getting specific entity details."""
        manager = D5eKnowledgeBaseManager(mock_d5e_service)

        # Mock repository response
        mock_d5e_service._hub.spells.get_by_index.return_value = sample_spell

        # Execute
        doc = manager.get_entity_details("spell", "magic-missile")

        # Verify
        assert isinstance(doc, Document)
        assert "Magic Missile" in doc.page_content
        assert doc.metadata["index"] == "magic-missile"
        mock_d5e_service._hub.spells.get_by_index.assert_called_once_with(
            "magic-missile"
        )

    def test_get_entity_details_not_found(self, mock_d5e_service: MagicMock) -> None:
        """Test getting entity details when not found."""
        manager = D5eKnowledgeBaseManager(mock_d5e_service)

        # Mock repository response
        mock_d5e_service._hub.spells.get_by_index.return_value = None

        # Execute
        doc = manager.get_entity_details("spell", "nonexistent")

        # Verify
        assert doc is None

    @patch("langchain_huggingface.HuggingFaceEmbeddings")
    @patch("app.content.rag.d5e_knowledge_base_manager.logger")
    def test_load_all_knowledge_bases(
        self,
        mock_logger: MagicMock,
        mock_embeddings: MagicMock,
        mock_d5e_service: MagicMock,
    ) -> None:
        """Test loading all D5e knowledge bases."""
        # Setup - mock all repositories to return empty lists
        for repo_name in [
            "spells",
            "monsters",
            "classes",
            "races",
            "subclasses",
            "subraces",
            "backgrounds",
            "feats",
            "traits",
            "equipment",
            "magic_items",
            "weapon_properties",
            "ability_scores",
            "skills",
            "proficiencies",
            "conditions",
            "damage_types",
            "languages",
            "alignments",
            "rules",
            "rule_sections",
        ]:
            getattr(mock_d5e_service._hub, repo_name).list_all.return_value = []

        manager = D5eKnowledgeBaseManager(mock_d5e_service)

        # Mock embeddings
        manager._embeddings_initialized = True
        manager.embeddings = mock_embeddings.return_value

        # Execute
        manager._load_d5e_knowledge_bases()

        # Verify
        assert manager._d5e_loaded
        mock_logger.info.assert_any_call("Loading D5e knowledge bases...")
        mock_logger.info.assert_any_call("D5e knowledge bases loaded successfully")

    def test_d5e_only_mode(self, mock_d5e_service: MagicMock) -> None:
        """Test loading only D5e data without static files."""
        manager = D5eKnowledgeBaseManager(mock_d5e_service)

        # Mock D5e loading method
        with patch.object(manager, "_load_d5e_knowledge_bases") as mock_d5e:
            manager._initialize_knowledge_bases()

            # Verify only D5e method called
            mock_d5e.assert_called_once()
