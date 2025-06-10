"""
Unit tests for CharacterTemplateModel field validation.
Tests that unified model properly validates field constraints.
"""

import unittest
from datetime import datetime, timezone
from typing import Any, Dict

from pydantic import ValidationError

from app.models.models import (
    BaseStatsModel,
    CharacterTemplateModel,
)


class TestCharacterTemplateValidation(unittest.TestCase):
    """Test field validation for CharacterTemplateModel."""

    def get_minimal_valid_character(self) -> Dict[str, Any]:
        """Get minimal valid character data for testing."""
        return {
            "id": "test_char",
            "name": "Test Character",
            "race": "Human",
            "char_class": "Fighter",
            "level": 1,
            "background": "Soldier",
            "alignment": "Neutral",
            "base_stats": {
                "STR": 10,
                "DEX": 10,
                "CON": 10,
                "INT": 10,
                "WIS": 10,
                "CHA": 10,
            },
            "proficiencies": {
                "armor": [],
                "weapons": [],
                "tools": [],
                "saving_throws": [],
                "skills": [],
            },
            "languages": ["Common"],
            "racial_traits": [],
            "class_features": [],
            "feats": [],
            "spells_known": [],
            "cantrips_known": [],
            "starting_equipment": [],
            "starting_gold": 0,
            "personality_traits": [],
            "ideals": [],
            "bonds": [],
            "flaws": [],
        }

    def test_level_validation(self) -> None:
        """Test that level must be between 1 and 20."""
        # Test valid levels
        for level in [1, 10, 20]:
            char_data = self.get_minimal_valid_character()
            char_data["level"] = level
            character = CharacterTemplateModel(**char_data)
            self.assertEqual(character.level, level)

        # Test invalid levels
        for invalid_level in [0, -1, 21, 100]:
            char_data = self.get_minimal_valid_character()
            char_data["level"] = invalid_level
            with self.assertRaises(ValidationError) as cm:
                CharacterTemplateModel(**char_data)
            self.assertIn("level", str(cm.exception))

    def test_stat_validation(self) -> None:
        """Test that ability scores must be between 1 and 30."""
        # Test valid stats
        valid_stats = BaseStatsModel(STR=8, DEX=16, CON=14, INT=12, WIS=13, CHA=10)
        char_data = self.get_minimal_valid_character()
        char_data["base_stats"] = valid_stats.model_dump()
        character = CharacterTemplateModel(**char_data)
        self.assertEqual(character.base_stats.STR, 8)
        self.assertEqual(character.base_stats.DEX, 16)

        # Test boundary values
        boundary_stats = BaseStatsModel(STR=1, DEX=30, CON=1, INT=30, WIS=1, CHA=30)
        char_data["base_stats"] = boundary_stats.model_dump()
        character = CharacterTemplateModel(**char_data)
        self.assertEqual(character.base_stats.STR, 1)
        self.assertEqual(character.base_stats.DEX, 30)

        # Test invalid stats - too low
        char_data = self.get_minimal_valid_character()
        char_data["base_stats"]["STR"] = 0
        with self.assertRaises(ValidationError) as cm:
            CharacterTemplateModel(**char_data)
        self.assertIn("STR", str(cm.exception))

        # Test invalid stats - too high
        char_data = self.get_minimal_valid_character()
        char_data["base_stats"]["INT"] = 31
        with self.assertRaises(ValidationError) as cm:
            CharacterTemplateModel(**char_data)
        self.assertIn("INT", str(cm.exception))

    def test_starting_gold_validation(self) -> None:
        """Test that starting gold cannot be negative."""
        # Test valid gold amounts
        for gold in [0, 50, 1000, 99999]:
            char_data = self.get_minimal_valid_character()
            char_data["starting_gold"] = gold
            character = CharacterTemplateModel(**char_data)
            self.assertEqual(character.starting_gold, gold)

        # Test negative gold
        char_data = self.get_minimal_valid_character()
        char_data["starting_gold"] = -1
        with self.assertRaises(ValidationError) as cm:
            CharacterTemplateModel(**char_data)
        self.assertIn("starting_gold", str(cm.exception))

    def test_personality_traits_max_length(self) -> None:
        """Test that personality traits list has maximum length of 2."""
        char_data = self.get_minimal_valid_character()

        # Test valid lengths
        char_data["personality_traits"] = ["Trait 1"]
        character = CharacterTemplateModel(**char_data)
        self.assertEqual(len(character.personality_traits), 1)

        char_data["personality_traits"] = ["Trait 1", "Trait 2"]
        character = CharacterTemplateModel(**char_data)
        self.assertEqual(len(character.personality_traits), 2)

        # Test exceeding max length
        char_data["personality_traits"] = ["Trait 1", "Trait 2", "Trait 3"]
        with self.assertRaises(ValidationError) as cm:
            CharacterTemplateModel(**char_data)
        self.assertIn("personality_traits", str(cm.exception))

    def test_item_quantity_validation(self) -> None:
        """Test that item quantities must be positive."""
        char_data = self.get_minimal_valid_character()

        # Test valid quantities
        char_data["starting_equipment"] = [
            {"id": "sword", "name": "Sword", "description": "A blade", "quantity": 1},
            {"id": "arrows", "name": "Arrows", "description": "Ammo", "quantity": 50},
        ]
        character = CharacterTemplateModel(**char_data)
        self.assertEqual(character.starting_equipment[0].quantity, 1)
        self.assertEqual(character.starting_equipment[1].quantity, 50)

        # Test zero quantity
        char_data["starting_equipment"] = [
            {"id": "sword", "name": "Sword", "description": "A blade", "quantity": 0}
        ]
        with self.assertRaises(ValidationError) as cm:
            CharacterTemplateModel(**char_data)
        self.assertIn("quantity", str(cm.exception))

        # Test negative quantity
        char_data["starting_equipment"] = [
            {"id": "sword", "name": "Sword", "description": "A blade", "quantity": -1}
        ]
        with self.assertRaises(ValidationError) as cm:
            CharacterTemplateModel(**char_data)
        self.assertIn("quantity", str(cm.exception))

    def test_class_feature_level_validation(self) -> None:
        """Test that class feature level_acquired must be positive."""
        char_data = self.get_minimal_valid_character()

        # Test valid levels
        char_data["class_features"] = [
            {"name": "Feature 1", "description": "Desc", "level_acquired": 1},
            {"name": "Feature 2", "description": "Desc", "level_acquired": 20},
        ]
        character = CharacterTemplateModel(**char_data)
        self.assertEqual(character.class_features[0].level_acquired, 1)
        self.assertEqual(character.class_features[1].level_acquired, 20)

        # Test zero level
        char_data["class_features"] = [
            {"name": "Feature", "description": "Desc", "level_acquired": 0}
        ]
        with self.assertRaises(ValidationError) as cm:
            CharacterTemplateModel(**char_data)
        self.assertIn("level_acquired", str(cm.exception))

    def test_nested_model_validation(self) -> None:
        """Test validation of nested models like TraitModel and ItemModel."""
        char_data = self.get_minimal_valid_character()

        # Test missing required fields in nested models
        char_data["racial_traits"] = [
            {"name": "Trait"}  # Missing description
        ]
        with self.assertRaises(ValidationError) as cm:
            CharacterTemplateModel(**char_data)
        self.assertIn("description", str(cm.exception))

        # Test extra fields in nested models
        char_data["racial_traits"] = [
            {"name": "Trait", "description": "Desc", "extra": "Not allowed"}
        ]
        with self.assertRaises(ValidationError) as cm:
            CharacterTemplateModel(**char_data)
        self.assertIn("extra", str(cm.exception))

    def test_datetime_fields_timezone_aware(self) -> None:
        """Test that datetime fields handle timezone properly."""
        char_data = self.get_minimal_valid_character()

        # Test with timezone-aware datetime
        now_utc = datetime.now(timezone.utc)
        char_data["created_date"] = now_utc
        char_data["last_modified"] = now_utc

        character = CharacterTemplateModel(**char_data)
        self.assertEqual(character.created_date, now_utc)
        self.assertEqual(character.last_modified, now_utc)

        # Test with ISO string
        char_data["created_date"] = now_utc.isoformat()
        char_data["last_modified"] = now_utc.isoformat()

        character = CharacterTemplateModel(**char_data)
        self.assertIsInstance(character.created_date, datetime)
        self.assertIsInstance(character.last_modified, datetime)


if __name__ == "__main__":
    unittest.main()
