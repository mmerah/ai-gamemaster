"""
Unit tests for the RAG service implementation.
Tests the RAG service interface and result formatting with database-backed implementation.
"""

import os
import tempfile
import unittest
from typing import Any, ClassVar, Optional
from unittest.mock import MagicMock, Mock, patch

import numpy as np

# Skip entire module if RAG is disabled
import pytest

pytestmark = pytest.mark.requires_rag

if os.environ.get("RAG_ENABLED", "true").lower() == "false":
    pytest.skip("RAG is disabled", allow_module_level=True)

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.content.connection import DatabaseManager
from app.content.models import Base, ContentPack, Equipment, Monster, Spell
from app.content.rag.db_knowledge_base_manager import (
    DbKnowledgeBaseManager,
    DummySentenceTransformer,
)
from app.content.rag.service import RAGServiceImpl
from app.content.types import Vector
from app.core.interfaces import KnowledgeResult, QueryType, RAGQuery, RAGResults
from app.models.game_state import GameStateModel
from app.models.rag import EventMetadataModel, LoreDataModel


class TestRAGResults(unittest.TestCase):
    """Test RAGResults formatting methods."""

    def test_format_for_prompt_with_results(self) -> None:
        """Test formatting results for prompt inclusion."""
        results = RAGResults(
            results=[
                KnowledgeResult(
                    content="Fireball: 8d6 fire damage in 20ft radius",
                    source="spells",
                    relevance_score=0.9,
                ),
                KnowledgeResult(
                    content="Fire damage ignites flammable objects",
                    source="rules",
                    relevance_score=0.7,
                ),
                KnowledgeResult(
                    content="Goblin: Small humanoid, 7 HP",
                    source="monsters",
                    relevance_score=0.8,
                ),
            ]
        )

        formatted = results.format_for_prompt()
        self.assertIn("Fireball", formatted)
        self.assertIn("Fire damage", formatted)
        self.assertIn("Goblin", formatted)

    def test_format_for_prompt_empty(self) -> None:
        """Test formatting with no results."""
        results = RAGResults(results=[])
        formatted = results.format_for_prompt()
        self.assertEqual(formatted, "")

    def test_has_results(self) -> None:
        """Test has_results property."""
        # With results
        results = RAGResults(
            results=[
                KnowledgeResult(content="test", source="test", relevance_score=0.5)
            ]
        )
        self.assertTrue(results.has_results())

        # Without results
        empty_results = RAGResults(results=[])
        self.assertFalse(empty_results.has_results())

    def test_debug_format(self) -> None:
        """Test debug formatting."""
        results = RAGResults(
            results=[
                KnowledgeResult(
                    content="Fireball spell description",
                    source="spells",
                    relevance_score=0.9,
                )
            ],
            total_queries=1,
            execution_time_ms=150.5,
        )

        debug = results.debug_format()
        self.assertIn("RAG Retrieved 1 results in 150.5ms", debug)
        self.assertIn("[spells] Fireball", debug)


class TestDbKnowledgeBaseManager(unittest.TestCase):
    """Test the database-backed knowledge base manager."""

    def setUp(self) -> None:
        """Set up test fixtures with in-memory database."""
        # Create in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

        # Create database manager
        self.db_manager = DatabaseManager("sqlite:///:memory:")
        self.db_manager._engine = self.engine

        # Create knowledge base manager with mocked sentence transformer
        with patch("sentence_transformers.SentenceTransformer"):
            self.kb_manager = DbKnowledgeBaseManager(self.db_manager)

            # Mock the sentence transformer to return predictable embeddings
            mock_transformer = MagicMock()
            mock_transformer.encode = MagicMock(side_effect=self._mock_encode)
            mock_transformer.embedding_dimension = 384
            self.kb_manager._sentence_transformer = mock_transformer

        # Populate test data
        self._populate_test_data()

    def _mock_encode(self, texts: Any, **kwargs: Any) -> Vector:
        """Mock embedding generation with semantic similarity."""
        if isinstance(texts, str):
            texts = [texts]

        # Generate embeddings that preserve semantic similarity
        embeddings = []
        for text in texts:
            # Create base embedding from text features
            text_lower = text.lower()
            embedding: Vector = np.zeros(384, dtype=np.float32)

            # Add features for common terms to create semantic similarity
            keywords = {
                # Spell-related keywords
                "fireball": (0, 1.0),
                "fire": (0, 0.8),
                "spell": (10, 0.5),
                "magic missile": (20, 1.0),
                "missile": (20, 0.8),
                "evocation": (30, 0.6),
                "level 3": (40, 0.7),
                "level 1": (50, 0.7),
                # Monster-related keywords
                "goblin": (60, 1.0),
                "humanoid": (70, 0.7),
                "small": (80, 0.6),
                "creature": (90, 0.5),
                "monster": (100, 0.5),
                # Equipment-related keywords
                "longsword": (110, 1.0),
                "sword": (110, 0.8),
                "weapon": (120, 0.7),
                "equipment": (130, 0.5),
                "combat": (140, 0.4),
            }

            for keyword, (base_idx, weight) in keywords.items():
                if keyword in text_lower:
                    # Add weighted features
                    for i in range(10):
                        if base_idx + i < 384:
                            embedding[base_idx + i] = weight * (1.0 - i * 0.1)

            # Add some random noise to make embeddings unique
            seed = hash(text) % 1000
            np.random.seed(seed)
            noise = np.random.randn(384).astype(np.float32) * 0.1
            embedding = embedding + noise

            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            else:
                # Fallback to random if no features found
                embedding = np.random.randn(384).astype(np.float32)
                embedding = embedding / np.linalg.norm(embedding)

            embeddings.append(embedding)

        return np.array(embeddings, dtype=np.float32)

    def _populate_test_data(self) -> None:
        """Populate the database with test data."""
        with self.db_manager.get_session() as session:
            # Create test content pack first
            test_pack = ContentPack(
                id="test_pack",
                name="Test Content Pack",
                description="Test data for unit tests",
                version="1.0.0",
                author="Test Suite",
                is_active=True,
            )
            session.add(test_pack)
            session.commit()

            # Add test spells
            fireball = Spell(
                index="fireball",
                name="Fireball",
                desc=[
                    "A bright streak flashes from your pointing finger to a point you choose within range and then blossoms with a low roar into an explosion of flame."
                ],
                level=3,
                school={"name": "Evocation"},
                range="150 feet",
                components=["V", "S", "M"],
                material="A tiny ball of bat guano and sulfur",
                ritual=False,
                duration="Instantaneous",
                concentration=False,
                casting_time="1 action",
                damage={
                    "damage_type": {"name": "Fire"},
                    "damage_at_slot_level": {"3": "8d6"},
                },
                url="/api/spells/fireball",
                content_pack_id="test_pack",
            )

            magic_missile = Spell(
                index="magic-missile",
                name="Magic Missile",
                desc=["You create three glowing darts of magical force."],
                level=1,
                school={"name": "Evocation"},
                range="120 feet",
                components=["V", "S"],
                ritual=False,
                duration="Instantaneous",
                concentration=False,
                casting_time="1 action",
                damage={
                    "damage_type": {"name": "Force"},
                    "damage_at_slot_level": {"1": "3d4+3"},
                },
                url="/api/spells/magic-missile",
                content_pack_id="test_pack",
            )

            # Add test monsters
            goblin = Monster(
                index="goblin",
                name="Goblin",
                size="Small",
                type="humanoid",
                subtype="goblinoid",
                alignment="neutral evil",
                armor_class=[{"value": 15, "type": "leather armor, shield"}],
                hit_points=7,
                hit_dice="2d6",
                speed={"walk": "30 ft."},
                strength=8,
                dexterity=14,
                constitution=10,
                intelligence=10,
                wisdom=8,
                charisma=8,
                challenge_rating=0.25,
                xp=50,
                url="/api/monsters/goblin",
                content_pack_id="test_pack",
            )

            # Add test equipment
            sword = Equipment(
                index="longsword",
                name="Longsword",
                equipment_category={"name": "Weapon"},
                weapon_category="Martial",
                weapon_range="Melee",
                cost={"quantity": 15, "unit": "gp"},
                damage={"damage_dice": "1d8", "damage_type": {"name": "Slashing"}},
                weight=3,
                url="/api/equipment/longsword",
                content_pack_id="test_pack",
            )

            # Generate embeddings for all entities
            fireball.embedding = self._mock_encode(
                f"Spell: Fireball Level 3 School: Evocation {fireball.desc[0]}"
            )[0]
            magic_missile.embedding = self._mock_encode(
                f"Spell: Magic Missile Level 1 School: Evocation {magic_missile.desc[0]}"
            )[0]
            goblin.embedding = self._mock_encode(
                "Monster: Goblin Type: humanoid CR: 0.25 HP: 7"
            )[0]
            sword.embedding = self._mock_encode(
                "Equipment: Longsword Category: Weapon Cost: 15 gp"
            )[0]

            session.add_all([fireball, magic_missile, goblin, sword])
            session.commit()

    def tearDown(self) -> None:
        """Clean up test resources."""
        self.engine.dispose()
        self.db_manager.dispose()

    def test_search_spells(self) -> None:
        """Test searching for spell content."""
        results = self.kb_manager.search(
            query="fireball spell", kb_types=["spells"], k=2, score_threshold=0.1
        )

        self.assertGreater(len(results.results), 0)
        self.assertEqual(results.results[0].source, "spells")
        self.assertIn("Fireball", results.results[0].content)

    def test_search_monsters(self) -> None:
        """Test searching for monster content."""
        results = self.kb_manager.search(
            query="small humanoid creature",
            kb_types=["monsters"],
            k=2,
            score_threshold=0.1,
        )

        self.assertGreater(len(results.results), 0)
        self.assertEqual(results.results[0].source, "monsters")
        self.assertIn("Goblin", results.results[0].content)

    def test_search_multiple_knowledge_bases(self) -> None:
        """Test searching across multiple knowledge bases."""
        results = self.kb_manager.search(
            query="combat", kb_types=["spells", "equipment"], k=3, score_threshold=0.1
        )

        # Should find results from both spells and equipment
        sources = {r.source for r in results.results}
        self.assertTrue(len(sources) > 0)

    def test_add_campaign_lore(self) -> None:
        """Test adding campaign-specific lore."""
        lore_data = LoreDataModel(
            id="test_lore",
            name="Test Lore",
            description="Test description",
            content="The ancient dragon sleeps in the mountain.",
            tags=["dragon", "mountain"],
            category="location",
        )

        self.kb_manager.add_campaign_lore("test_campaign", lore_data)

        # Verify lore was added
        self.assertIn("lore_test_campaign", self.kb_manager.campaign_data)
        self.assertGreater(len(self.kb_manager.campaign_data["lore_test_campaign"]), 0)

    def test_add_event(self) -> None:
        """Test adding campaign events."""
        self.kb_manager.add_event(
            campaign_id="test_campaign",
            event_summary="The party defeated a dragon",
            keywords=["dragon", "victory"],
            metadata={"location": "Dragon's Lair"},
        )

        # Verify event was added
        self.assertIn("events_test_campaign", self.kb_manager.campaign_data)
        events = self.kb_manager.campaign_data["events_test_campaign"]
        self.assertEqual(len(events), 1)
        self.assertIn("defeated a dragon", events[0].page_content)


class TestRAGService(unittest.TestCase):
    """Test the main RAG service interface with database backend."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Create in-memory database
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

        # Create database manager
        self.db_manager = DatabaseManager("sqlite:///:memory:")
        self.db_manager._engine = self.engine

        # Set up persistent patches for HuggingFace embeddings to prevent hanging
        # Both patches are needed: one for the global variable, one for the import
        embeddings_patcher1 = patch(
            "app.content.rag.knowledge_base._HuggingFaceEmbeddings", None
        )
        embeddings_patcher2 = patch("langchain_huggingface.HuggingFaceEmbeddings")

        # Start patches and register cleanup
        embeddings_patcher1.start()
        self.addCleanup(embeddings_patcher1.stop)

        mock_hf_embeddings = embeddings_patcher2.start()
        self.addCleanup(embeddings_patcher2.stop)

        # Configure the mock to return a simple object with encode method
        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.embed_documents = MagicMock(
            side_effect=lambda texts: [self._mock_encode(text) for text in texts]
        )
        mock_embeddings_instance.embed_query = MagicMock(side_effect=self._mock_encode)
        mock_hf_embeddings.return_value = mock_embeddings_instance

        # Create RAG service with mocked dependencies
        self.mock_game_state_repo = Mock()
        self.rag_service = RAGServiceImpl(game_state_repo=self.mock_game_state_repo)

        # Replace knowledge base manager with database-backed version
        with patch("sentence_transformers.SentenceTransformer"):
            self.db_kb_manager = DbKnowledgeBaseManager(self.db_manager)

            # Mock the sentence transformer
            mock_transformer = MagicMock()
            mock_transformer.encode = MagicMock(side_effect=self._mock_encode)
            mock_transformer.embedding_dimension = 384
            self.db_kb_manager._sentence_transformer = mock_transformer

        self.rag_service.kb_manager = self.db_kb_manager

        # Mock the query engine
        self.mock_query_engine = Mock()
        self.rag_service.query_engine = self.mock_query_engine

        # Populate test data
        self._populate_test_data()

    def _mock_encode(self, texts: Any, **kwargs: Any) -> Vector:
        """Mock embedding generation (same as in TestDbKnowledgeBaseManager)."""
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for text in texts:
            seed = hash(text) % 1000
            np.random.seed(seed)
            embedding = np.random.randn(384).astype(np.float32)
            embedding = embedding / np.linalg.norm(embedding)
            embeddings.append(embedding)

        return np.array(embeddings, dtype=np.float32)

    def _populate_test_data(self) -> None:
        """Populate the database with test data."""
        with self.db_manager.get_session() as session:
            # Create test content pack first
            test_pack = ContentPack(
                id="test_pack",
                name="Test Content Pack",
                description="Test data for unit tests",
                version="1.0.0",
                author="Test Suite",
                is_active=True,
            )
            session.add(test_pack)
            session.commit()

            # Add a test spell
            fireball = Spell(
                index="fireball",
                name="Fireball",
                desc=["8d6 fire damage in 20ft radius"],
                level=3,
                school={"name": "Evocation"},
                url="/api/spells/fireball",
                content_pack_id="test_pack",
            )
            fireball.embedding = self._mock_encode(
                "Spell: Fireball Level 3 School: Evocation 8d6 fire damage in 20ft radius"
            )[0]

            session.add(fireball)
            session.commit()

    def tearDown(self) -> None:
        """Clean up test resources."""
        # Clean up database resources
        self.engine.dispose()
        self.db_manager.dispose()

    def test_get_relevant_knowledge_no_queries(self) -> None:
        """Test when no queries are generated."""
        # Mock query engine to return no queries
        self.mock_query_engine.analyze_action.return_value = []

        game_state = GameStateModel()
        results = self.rag_service.get_relevant_knowledge("test action", game_state)

        self.assertIsNotNone(results)
        self.assertEqual(len(results.results), 0)
        self.assertEqual(results.total_queries, 0)

    def test_get_relevant_knowledge_with_results(self) -> None:
        """Test when queries return results from database."""
        # Mock query generation
        mock_queries = [
            RAGQuery(
                query_text="fireball spell",
                query_type=QueryType.SPELL_CASTING,
                knowledge_base_types=["spells"],
            )
        ]
        self.mock_query_engine.analyze_action.return_value = mock_queries

        game_state = GameStateModel()
        results = self.rag_service.get_relevant_knowledge("cast fireball", game_state)

        # Should find the fireball spell in the database
        self.assertGreater(len(results.results), 0)
        self.assertIn("Fireball", results.results[0].content)
        self.assertEqual(results.results[0].source, "spells")

    def test_configure_filtering(self) -> None:
        """Test configuration of filtering parameters."""
        self.rag_service.configure_filtering(
            max_results=10,
            score_threshold=0.5,
        )

        # Verify the RAG service parameters were updated
        self.assertEqual(self.rag_service.max_total_results, 10)
        self.assertEqual(self.rag_service.score_threshold, 0.5)

    def test_ensure_campaign_knowledge(self) -> None:
        """Test campaign knowledge loading with database backend."""
        game_state = GameStateModel(
            campaign_id="test_campaign",
            active_lore_id="test_lore",
        )

        # Mock lore loading
        with patch("app.content.rag.service.load_lore_info") as mock_load_lore:
            mock_lore = LoreDataModel(
                id="test_lore",
                name="Test Lore",
                description="Test description",
                content="Test lore content data",
                tags=["test"],
                category="test",
            )
            mock_load_lore.return_value = mock_lore

            # Call the method indirectly through get_relevant_knowledge
            self.mock_query_engine.analyze_action.return_value = []
            self.rag_service.get_relevant_knowledge("test", game_state)

            # Verify campaign lore was added to the database-backed manager
            self.assertIn("lore_test_campaign", self.db_kb_manager.campaign_data)

    def test_add_event(self) -> None:
        """Test adding an event to campaign history."""
        from datetime import datetime, timezone

        campaign_id = "test_campaign"
        event_summary = "The party defeated a dragon"
        keywords = ["dragon", "victory"]

        metadata = EventMetadataModel(
            timestamp=datetime.now(timezone.utc).isoformat(),
            location="Dragon's Lair",
            participants=["party"],
            combat_active=True,
        )

        self.rag_service.add_event(campaign_id, event_summary, keywords, metadata)

        # Verify event was added to the database-backed knowledge base
        self.assertIn("events_test_campaign", self.db_kb_manager.campaign_data)
        events = self.db_kb_manager.campaign_data["events_test_campaign"]
        self.assertEqual(len(events), 1)
        self.assertIn("defeated a dragon", events[0].page_content)

    def test_fallback_vector_search(self) -> None:
        """Test fallback search when sqlite-vec is not available."""
        # This tests the fallback path in _vector_search when sqlite-vec extension is not loaded
        # Mock the session's execute method to simulate missing sqlite-vec
        with self.db_manager.get_session() as session:
            original_execute = session.execute

            def mock_execute(statement: Any, *args: Any, **kwargs: Any) -> Any:
                if "vec_distance_l2" in str(statement):
                    raise Exception("vec_distance_l2 not found")
                return original_execute(statement, *args, **kwargs)

            with patch.object(session, "execute", side_effect=mock_execute):
                results = self.db_kb_manager.search(
                    query="fireball", kb_types=["spells"], k=1, score_threshold=0.1
                )

                # Should still return results using the fallback method
                self.assertGreater(len(results.results), 0)


class TestDummySentenceTransformer(unittest.TestCase):
    """Test the fallback sentence transformer."""

    def test_dummy_transformer_consistency(self) -> None:
        """Test that dummy transformer produces consistent embeddings."""

        transformer = DummySentenceTransformer()

        # Same text should produce same embedding
        text = "test text"
        embedding1 = transformer.encode(text)
        embedding2 = transformer.encode(text)

        np.testing.assert_array_equal(embedding1, embedding2)

        # Different texts should produce different embeddings
        embedding3 = transformer.encode("different text")
        self.assertFalse(np.array_equal(embedding1, embedding3))

        # Embeddings should be normalized
        norm_value = float(np.linalg.norm(embedding1))
        self.assertAlmostEqual(norm_value, 1.0, places=5)


if __name__ == "__main__":
    unittest.main()
