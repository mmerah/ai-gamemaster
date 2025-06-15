"""Tests for content pack priority functionality in ContentService."""

from typing import List, Optional
from unittest.mock import MagicMock, Mock

import pytest

from app.content.repositories.db_repository_hub import D5eDbRepositoryHub
from app.content.schemas import D5eClass, D5eSpell
from app.content.service import ContentService


class TestContentServicePriority:
    """Test content pack priority functionality in ContentService."""

    @pytest.fixture
    def mock_hub(self) -> Mock:
        """Create a mock repository hub."""
        return Mock(spec=D5eDbRepositoryHub)

    @pytest.fixture
    def service(self, mock_hub: Mock) -> ContentService:
        """Create a ContentService instance."""
        return ContentService(repository_hub=mock_hub)

    @pytest.fixture
    def sample_wizard_class(self) -> Mock:
        """Create a sample wizard class."""
        wizard = Mock(spec=D5eClass)
        wizard.index = "wizard"
        wizard.name = "Wizard"
        wizard.hit_die = 6
        wizard.spellcasting = Mock()
        wizard.multi_classing = Mock()
        wizard.model_dump.return_value = {
            "index": "wizard",
            "name": "Wizard",
            "hit_die": 6,
        }
        return wizard

    @pytest.fixture
    def sample_spell(self) -> Mock:
        """Create a sample spell."""
        spell = Mock(spec=D5eSpell)
        spell.index = "fireball"
        spell.name = "Fireball"
        spell.level = 3
        spell.classes = [Mock(index="wizard"), Mock(index="sorcerer")]
        return spell

    def test_get_class_at_level_with_priority(
        self,
        service: ContentService,
        mock_hub: Mock,
        sample_wizard_class: Mock,
    ) -> None:
        """Test getting class with content pack priority."""
        # Setup
        content_pack_priority = ["custom-pack", "dnd_5e_srd"]

        mock_hub.classes.get_by_name_with_options.return_value = sample_wizard_class
        mock_hub.classes.get_level_data.return_value = Mock(
            level=5,
            prof_bonus=3,
            spellcasting=Mock(),
            model_dump=Mock(return_value={"level": 5, "prof_bonus": 3}),
        )
        mock_hub.classes.get_class_features.return_value = []
        mock_hub.classes.get_proficiency_bonus.return_value = 3
        mock_hub.classes.get_spell_slots.return_value = {1: 4, 2: 3, 3: 2}

        # Execute
        result = service.get_class_at_level(
            "Wizard", 5, content_pack_priority=content_pack_priority
        )

        # Verify
        assert result is not None
        mock_hub.classes.get_by_name_with_options.assert_called_once_with(
            "Wizard", content_pack_priority=content_pack_priority
        )

    def test_get_class_at_level_fallback_to_index(
        self,
        service: ContentService,
        mock_hub: Mock,
        sample_wizard_class: Mock,
    ) -> None:
        """Test falling back to index search when name search fails."""
        # Setup
        content_pack_priority = ["custom-pack", "dnd_5e_srd"]

        # Name search returns None
        mock_hub.classes.get_by_name_with_options.return_value = None
        # Index search succeeds
        mock_hub.classes.get_by_index_with_options.return_value = sample_wizard_class
        mock_hub.classes.get_level_data.return_value = Mock(
            level=5,
            model_dump=Mock(return_value={"level": 5}),
        )
        mock_hub.classes.get_class_features.return_value = []
        mock_hub.classes.get_proficiency_bonus.return_value = 3

        # Execute
        result = service.get_class_at_level(
            "Wizard", 5, content_pack_priority=content_pack_priority
        )

        # Verify
        assert result is not None
        mock_hub.classes.get_by_index_with_options.assert_called_once_with(
            "wizard", content_pack_priority=content_pack_priority
        )

    def test_get_spells_for_class_with_priority(
        self,
        service: ContentService,
        mock_hub: Mock,
        sample_wizard_class: Mock,
        sample_spell: Mock,
    ) -> None:
        """Test getting spells for a class with content pack priority."""
        # Setup
        content_pack_priority = ["custom-spells", "dnd_5e_srd"]

        mock_hub.classes.get_by_name_with_options.return_value = sample_wizard_class
        mock_hub.spells.get_by_class_with_options.return_value = [sample_spell]

        # Execute
        result = service.get_spells_for_class(
            "Wizard", content_pack_priority=content_pack_priority
        )

        # Verify
        assert len(result) == 1
        assert result[0].index == "fireball"
        mock_hub.spells.get_by_class_with_options.assert_called_once_with(
            "wizard", content_pack_priority=content_pack_priority
        )

    def test_get_spells_for_class_with_level_filter(
        self,
        service: ContentService,
        mock_hub: Mock,
        sample_wizard_class: Mock,
        sample_spell: Mock,
    ) -> None:
        """Test filtering spells by level."""
        # Setup
        content_pack_priority = ["custom-spells", "dnd_5e_srd"]

        # Create spells of different levels
        spell1 = Mock(spec=D5eSpell, level=3, index="fireball")
        spell2 = Mock(spec=D5eSpell, level=1, index="magic-missile")
        spell3 = Mock(spec=D5eSpell, level=3, index="lightning-bolt")

        mock_hub.classes.get_by_name_with_options.return_value = sample_wizard_class
        mock_hub.spells.get_by_class_with_options.return_value = [
            spell1,
            spell2,
            spell3,
        ]

        # Execute - get only level 3 spells
        result = service.get_spells_for_class(
            "Wizard", spell_level=3, content_pack_priority=content_pack_priority
        )

        # Verify
        assert len(result) == 2
        assert all(spell.level == 3 for spell in result)

    def test_search_all_content_with_priority(
        self,
        service: ContentService,
        mock_hub: Mock,
    ) -> None:
        """Test searching all content with priority."""
        # Setup
        content_pack_priority = ["custom-pack", "dnd_5e_srd"]
        search_results = {
            "spells": [Mock(index="fireball")],
            "monsters": [Mock(index="goblin")],
        }
        mock_hub.search_all_with_options.return_value = search_results

        # Execute
        result = service.search_all_content(
            "fire", content_pack_priority=content_pack_priority
        )

        # Verify
        assert "spells" in result
        assert "monsters" in result
        mock_hub.search_all_with_options.assert_called_once_with(
            "fire", content_pack_priority=content_pack_priority
        )

    def test_search_specific_categories_with_priority(
        self,
        service: ContentService,
        mock_hub: Mock,
    ) -> None:
        """Test searching specific categories with priority."""
        # Setup
        content_pack_priority = ["custom-pack", "dnd_5e_srd"]
        categories = ["spells", "equipment"]

        # Mock repositories
        spell_repo = Mock()
        spell_repo.search_with_options.return_value = [Mock(index="fireball")]
        equipment_repo = Mock()
        equipment_repo.search_with_options.return_value = [Mock(index="fire-sword")]

        def get_repository_side_effect(category: str) -> Mock:
            if category == "spells":
                return spell_repo
            elif category == "equipment":
                return equipment_repo
            return Mock(search_with_options=Mock(return_value=[]))

        mock_hub.get_repository.side_effect = get_repository_side_effect

        # Execute
        result = service.search_all_content(
            "fire",
            categories=categories,
            content_pack_priority=content_pack_priority,
        )

        # Verify
        assert len(result) == 2
        assert "spells" in result
        assert "equipment" in result

        spell_repo.search_with_options.assert_called_once_with(
            "fire", content_pack_priority=content_pack_priority
        )
        equipment_repo.search_with_options.assert_called_once_with(
            "fire", content_pack_priority=content_pack_priority
        )

    def test_methods_without_priority_still_work(
        self,
        service: ContentService,
        mock_hub: Mock,
        sample_wizard_class: Mock,
    ) -> None:
        """Test that methods work without priority (backwards compatibility)."""
        # Setup
        mock_hub.classes.get_by_name_with_options.return_value = sample_wizard_class
        mock_hub.classes.get_level_data.return_value = Mock(
            level=5,
            model_dump=Mock(return_value={"level": 5}),
        )
        mock_hub.classes.get_class_features.return_value = []
        mock_hub.classes.get_proficiency_bonus.return_value = 3

        # Execute - no priority parameter
        result = service.get_class_at_level("Wizard", 5)

        # Verify
        assert result is not None
        # Should be called with None priority
        mock_hub.classes.get_by_name_with_options.assert_called_once_with(
            "Wizard", content_pack_priority=None
        )
