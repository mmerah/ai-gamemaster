"""Tests for the IndexingService."""

from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.content.connection import DatabaseManager
from app.content.models import Equipment, Monster, Spell
from app.content.services.indexing_service import IndexingService
from app.exceptions import DatabaseError


class TestIndexingService:
    """Test the IndexingService class."""

    @pytest.fixture
    def mock_database_manager(self) -> Mock:
        """Create a mock DatabaseManager."""
        return Mock(spec=DatabaseManager)

    @pytest.fixture
    def mock_session(self) -> Mock:
        """Create a mock Session."""
        return Mock(spec=Session)

    @pytest.fixture
    def context_manager(self, mock_session: Mock) -> Mock:
        """Create a mock context manager for database sessions."""
        context = Mock()
        context.__enter__ = Mock(return_value=mock_session)
        context.__exit__ = Mock(return_value=None)
        return context

    @pytest.fixture
    def service(self, mock_database_manager: Mock) -> IndexingService:
        """Create an IndexingService instance."""
        return IndexingService(mock_database_manager)

    @pytest.fixture
    def sample_spell(self) -> Mock:
        """Create a sample spell entity."""
        spell = Mock(spec=Spell)
        spell.index = "fireball"
        spell.name = "Fireball"
        spell.level = 3
        spell.school = "evocation"
        spell.classes = ["wizard", "sorcerer"]
        spell.desc = ["A bright streak flashes from your pointing finger..."]
        spell.higher_level = [
            "When you cast this spell using a spell slot of 4th level..."
        ]
        spell.embedding = None
        spell.content_pack_id = "test-pack"
        return spell

    @pytest.fixture
    def sample_monster(self) -> Mock:
        """Create a sample monster entity."""
        monster = Mock(spec=Monster)
        monster.index = "goblin"
        monster.name = "Goblin"
        monster.type = "humanoid"
        monster.size = "Small"
        monster.challenge_rating = 0.25
        monster.hit_points = 7
        monster.desc = None
        monster.embedding = None
        monster.content_pack_id = "test-pack"
        return monster

    @pytest.fixture
    def sample_equipment(self) -> Mock:
        """Create a sample equipment entity."""
        equipment = Mock(spec=Equipment)
        equipment.index = "longsword"
        equipment.name = "Longsword"
        equipment.equipment_category = "weapon"
        equipment.weapon_category = "martial"
        equipment.armor_category = None
        equipment.desc = ["Versatile weapon"]
        equipment.embedding = None
        equipment.content_pack_id = "test-pack"
        return equipment

    @patch("app.content.services.indexing_service.SentenceTransformer")
    def test_index_content_pack_success(
        self,
        mock_sentence_transformer_class: Mock,
        service: IndexingService,
        mock_database_manager: Mock,
        mock_session: Mock,
        context_manager: Mock,
        sample_spell: Mock,
        sample_monster: Mock,
    ) -> None:
        """Test indexing a content pack successfully."""
        # Setup
        mock_model = Mock()
        mock_sentence_transformer_class.return_value = mock_model
        mock_database_manager.get_session.return_value = context_manager

        # Mock embeddings - model.encode returns a 2D array (batch of embeddings)
        def encode_side_effect(
            texts: List[str], **kwargs: Any
        ) -> np.ndarray[Any, np.dtype[np.float32]]:
            # Return one embedding per text
            embeddings = []
            for text in texts:
                if "Spell" in text:
                    embeddings.append([0.1, 0.2, 0.3])
                else:
                    embeddings.append([0.4, 0.5, 0.6])
            return np.array(embeddings, dtype=np.float32)

        mock_model.encode.side_effect = encode_side_effect

        # Mock queries with proper chaining
        spell_query = Mock()
        spell_filter_by = Mock()
        spell_filter = Mock()
        spell_filter.all.return_value = [sample_spell]
        spell_filter_by.filter.return_value = spell_filter
        spell_query.filter_by.return_value = spell_filter_by

        monster_query = Mock()
        monster_filter_by = Mock()
        monster_filter = Mock()
        monster_filter.all.return_value = [sample_monster]
        monster_filter_by.filter.return_value = monster_filter
        monster_query.filter_by.return_value = monster_filter_by

        equipment_query = Mock()
        equipment_filter_by = Mock()
        equipment_filter = Mock()
        equipment_filter.all.return_value = []
        equipment_filter_by.filter.return_value = equipment_filter
        equipment_query.filter_by.return_value = equipment_filter_by

        # Map entity types to queries
        def query_side_effect(entity_type: Any) -> Mock:
            if entity_type.__name__ == "Spell":
                return spell_query
            elif entity_type.__name__ == "Monster":
                return monster_query
            else:
                return equipment_query

        mock_session.query.side_effect = query_side_effect

        # Execute
        result = service.index_content_pack("test-pack")

        # Verify
        assert "spells" in result
        assert result["spells"] == 1
        assert "monsters" in result
        assert result["monsters"] == 1

        # Verify embeddings were set (checking that something was set, not exact value)
        assert sample_spell.embedding is not None
        assert sample_monster.embedding is not None
        assert isinstance(sample_spell.embedding, bytes)
        assert isinstance(sample_monster.embedding, bytes)

        mock_session.commit.assert_called_once()

    @patch("app.content.services.indexing_service.SentenceTransformer")
    def test_index_content_type_success(
        self,
        mock_sentence_transformer_class: Mock,
        service: IndexingService,
        mock_database_manager: Mock,
        mock_session: Mock,
        context_manager: Mock,
        sample_spell: Mock,
    ) -> None:
        """Test indexing a specific content type."""
        # Setup
        mock_model = Mock()
        mock_sentence_transformer_class.return_value = mock_model
        mock_database_manager.get_session.return_value = context_manager

        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        mock_model.encode.return_value = np.array([embedding])

        # Mock query chain with proper chaining
        query = Mock()
        filter_by_result = Mock()
        filter_result = Mock()
        filter_result.all.return_value = [sample_spell]
        filter_by_result.filter.return_value = filter_result
        query.filter_by.return_value = filter_by_result
        mock_session.query.return_value = query

        # Execute
        result = service.index_content_type("spells", "test-pack")

        # Verify
        assert result == 1
        assert sample_spell.embedding == embedding.tobytes()

    def test_index_content_type_invalid_type(
        self,
        service: IndexingService,
        mock_database_manager: Mock,
    ) -> None:
        """Test indexing with invalid content type."""
        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            service.index_content_type("invalid_type")
        assert "Unknown content type" in str(exc_info.value)

    @patch("app.content.services.indexing_service.SentenceTransformer")
    def test_update_entity_embedding_success(
        self,
        mock_sentence_transformer_class: Mock,
        service: IndexingService,
        mock_database_manager: Mock,
        mock_session: Mock,
        context_manager: Mock,
        sample_spell: Mock,
    ) -> None:
        """Test updating a single entity embedding."""
        # Setup
        mock_model = Mock()
        mock_sentence_transformer_class.return_value = mock_model
        mock_database_manager.get_session.return_value = context_manager

        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        mock_model.encode.return_value = embedding

        query = Mock()
        query.filter_by.return_value.first.return_value = sample_spell
        mock_session.query.return_value = query

        # Execute
        result = service.update_entity_embedding(Spell, "fireball")

        # Verify
        assert result is True
        assert sample_spell.embedding == embedding.tobytes()
        mock_session.commit.assert_called_once()

    @patch("app.content.services.indexing_service.SentenceTransformer")
    def test_update_entity_embedding_not_found(
        self,
        mock_sentence_transformer_class: Mock,
        service: IndexingService,
        mock_database_manager: Mock,
        mock_session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test updating embedding for non-existent entity."""
        # Setup
        mock_database_manager.get_session.return_value = context_manager
        query = Mock()
        query.filter_by.return_value.first.return_value = None
        mock_session.query.return_value = query

        # Execute
        result = service.update_entity_embedding(Spell, "non-existent")

        # Verify
        assert result is False

    def test_create_content_text_spell(
        self,
        service: IndexingService,
        sample_spell: Mock,
    ) -> None:
        """Test creating text representation for a spell."""
        # Execute
        result = service._create_content_text(sample_spell)

        # Verify
        assert "Name: Fireball" in result
        assert "Level: 3" in result
        assert "School: evocation" in result
        assert "Classes: wizard, sorcerer" in result
        assert "Description:" in result
        assert "Higher Level:" in result

    def test_create_content_text_monster(
        self,
        service: IndexingService,
        sample_monster: Mock,
    ) -> None:
        """Test creating text representation for a monster."""
        # Execute
        result = service._create_content_text(sample_monster)

        # Verify
        assert "Name: Goblin" in result
        assert "Type: humanoid" in result
        assert "Size: Small" in result
        assert "Challenge Rating: 0.25" in result
        assert "Hit Points: 7" in result

    def test_create_content_text_equipment(
        self,
        service: IndexingService,
        sample_equipment: Mock,
    ) -> None:
        """Test creating text representation for equipment."""
        # Execute
        result = service._create_content_text(sample_equipment)

        # Verify
        assert "Name: Longsword" in result
        assert "Category: weapon" in result
        assert "Description: Versatile weapon" in result
        assert "Weapon Category: martial" in result

    def test_database_error_handling(
        self,
        service: IndexingService,
        mock_database_manager: Mock,
        mock_session: Mock,
        context_manager: Mock,
    ) -> None:
        """Test handling of database errors."""
        # Setup
        mock_database_manager.get_session.return_value = context_manager
        mock_session.query.side_effect = SQLAlchemyError("Database error")

        # Execute & Verify
        with pytest.raises(DatabaseError) as exc_info:
            service.index_content_pack("test-pack")
        assert "Failed to index content pack" in str(exc_info.value)

    @patch("app.content.services.indexing_service.SentenceTransformer")
    def test_model_lazy_loading(
        self,
        mock_sentence_transformer_class: Mock,
        service: IndexingService,
    ) -> None:
        """Test that the model is loaded lazily."""
        # Verify model not loaded initially
        assert service._model is None

        # Access model
        model = service._get_model()

        # Verify model loaded
        assert model is not None
        mock_sentence_transformer_class.assert_called_once_with(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        # Access again - should return same instance
        model2 = service._get_model()
        assert model is model2
        # Still only called once
        mock_sentence_transformer_class.assert_called_once()
