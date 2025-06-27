"""Unit tests for the ContentService."""

import unittest
from unittest.mock import MagicMock

from app.content.repositories.db_repository_hub import D5eDbRepositoryHub
from app.content.schemas import (
    APIReference,
    D5eAbilityScore,
    D5eClass,
    D5eEquipment,
    D5eLevel,
    D5eMonster,
    D5eSpell,
)
from app.content.service import ContentService


class TestContentService(unittest.TestCase):
    """Test the comprehensive content service."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Mock the repository hub
        self.mock_hub = MagicMock(spec=D5eDbRepositoryHub)

        # Create service with mocked repository hub
        self.service = ContentService(repository_hub=self.mock_hub)

        # Sample data - using MagicMock objects to avoid validation issues
        self.sample_wizard_class = MagicMock(spec=D5eClass)
        self.sample_wizard_class.index = "wizard"
        self.sample_wizard_class.name = "Wizard"
        self.sample_wizard_class.hit_die = 6
        self.sample_wizard_class.spellcasting = MagicMock()
        self.sample_wizard_class.multi_classing = MagicMock()
        self.sample_wizard_class.starting_equipment = []
        self.sample_wizard_class.model_dump.return_value = {
            "index": "wizard",
            "name": "Wizard",
            "hit_die": 6,
            "spellcasting": {"level": 1},
        }

        self.sample_level_data = MagicMock(spec=D5eLevel)
        self.sample_level_data.level = 5
        self.sample_level_data.prof_bonus = 3
        self.sample_level_data.spellcasting = MagicMock()
        self.sample_level_data.model_dump.return_value = {
            "level": 5,
            "prof_bonus": 3,
            "spellcasting": {
                "spell_slots_level_1": 4,
                "spell_slots_level_2": 3,
                "spell_slots_level_3": 2,
            },
        }


class TestCharacterCreationHelpers(TestContentService):
    """Test character creation helper methods."""

    def test_get_class_at_level_success(self) -> None:
        """Test getting class info at a specific level."""
        # Setup mocks
        self.mock_hub.classes.get_by_name_with_options.return_value = (
            self.sample_wizard_class
        )
        self.mock_hub.classes.get_level_data.return_value = self.sample_level_data
        self.mock_hub.classes.get_class_features.return_value = []
        self.mock_hub.classes.get_proficiency_bonus.return_value = 3
        self.mock_hub.classes.get_spell_slots.return_value = {1: 4, 2: 3, 3: 2}
        self.mock_hub.classes.get_multiclass_requirements.return_value = {
            "prerequisites": [{"ability": "int", "minimum": 13}]
        }

        result = self.service.get_class_at_level("Wizard", 5)

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing for mypy
        self.assertEqual(result["level"], 5)
        self.assertEqual(result["proficiency_bonus"], 3)
        self.assertEqual(result["hit_points"]["hit_die"], 6)
        self.assertEqual(result["hit_points"]["average_hp"], 22)  # 6 + 4*4
        self.assertIn("spell_slots", result)
        self.assertIn("multiclass_requirements", result)

    def test_get_class_at_level_not_found(self) -> None:
        """Test getting class info for non-existent class."""
        self.mock_hub.classes.get_by_name_with_options.return_value = None
        self.mock_hub.classes.get_by_index_with_options.return_value = None

        result = self.service.get_class_at_level("NonExistentClass", 5)

        self.assertIsNone(result)

    def test_calculate_ability_modifiers(self) -> None:
        """Test calculating ability modifiers."""
        # Mock ability scores
        mock_abilities = [
            D5eAbilityScore(
                index="str",
                name="STR",
                full_name="Strength",
                desc=[],
                skills=[],
                url="/api/ability-scores/str",
            ),
            D5eAbilityScore(
                index="dex",
                name="DEX",
                full_name="Dexterity",
                desc=[],
                skills=[],
                url="/api/ability-scores/dex",
            ),
        ]
        self.mock_hub.ability_scores.list_all.return_value = mock_abilities

        scores = {"STR": 16, "DEX": 14, "CON": 12, "INT": 8, "WIS": 10, "CHA": 13}
        modifiers = self.service.calculate_ability_modifiers(scores)

        self.assertEqual(modifiers["str"], 3)  # (16-10)//2 = 3
        self.assertEqual(modifiers["STR"], 3)
        self.assertEqual(modifiers["dex"], 2)  # (14-10)//2 = 2
        self.assertEqual(modifiers["DEX"], 2)

    def test_get_proficiency_bonus(self) -> None:
        """Test getting proficiency bonus."""
        self.mock_hub.classes.get_proficiency_bonus.return_value = 4

        result = self.service.get_proficiency_bonus(10)

        self.assertEqual(result, 4)
        self.mock_hub.classes.get_proficiency_bonus.assert_called_once_with(10)


class TestSpellManagement(TestContentService):
    """Test spell management methods."""

    def test_get_spells_for_class(self) -> None:
        """Test getting spells for a class."""
        # Mock spells
        mock_spells = [
            D5eSpell(
                index="fireball",
                name="Fireball",
                level=3,
                school=APIReference(
                    index="evocation",
                    name="Evocation",
                    url="/api/magic-schools/evocation",
                ),
                casting_time="1 action",
                range="150 feet",
                components=["V", "S", "M"],
                material="A tiny ball of bat guano and sulfur",
                duration="Instantaneous",
                concentration=False,
                ritual=False,
                desc=["A bright streak..."],
                classes=[
                    APIReference(
                        index="wizard", name="Wizard", url="/api/classes/wizard"
                    )
                ],
                subclasses=[],
                url="/api/spells/fireball",
            ),
            D5eSpell(
                index="identify",
                name="Identify",
                level=1,
                school=APIReference(
                    index="divination",
                    name="Divination",
                    url="/api/magic-schools/divination",
                ),
                casting_time="1 minute",
                range="Touch",
                components=["V", "S", "M"],
                material="A pearl worth at least 100 gp",
                duration="Instantaneous",
                concentration=False,
                ritual=True,
                desc=["You choose one object..."],
                classes=[
                    APIReference(
                        index="wizard", name="Wizard", url="/api/classes/wizard"
                    )
                ],
                subclasses=[],
                url="/api/spells/identify",
            ),
        ]

        self.mock_hub.classes.get_by_name_with_options.return_value = (
            self.sample_wizard_class
        )
        self.mock_hub.spells.get_by_class_with_options.return_value = mock_spells

        # Test without level filter
        result = self.service.get_spells_for_class("Wizard")
        self.assertEqual(len(result), 2)

        # Test with level filter
        result = self.service.get_spells_for_class("Wizard", spell_level=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Identify")

    def test_get_spell_slots(self) -> None:
        """Test getting spell slots."""
        self.mock_hub.classes.get_by_name_with_options.return_value = (
            self.sample_wizard_class
        )
        self.mock_hub.classes.get_spell_slots.return_value = {1: 4, 2: 3, 3: 2}

        result = self.service.get_spell_slots("Wizard", 5)

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing for mypy
        self.assertEqual(result[1], 4)
        self.assertEqual(result[2], 3)
        self.assertEqual(result[3], 2)


class TestCombatHelpers(TestContentService):
    """Test combat helper methods."""

    def test_get_monsters_by_cr(self) -> None:
        """Test getting monsters by CR range."""
        mock_monsters = [
            MagicMock(spec=D5eMonster, name="Goblin", challenge_rating=0.25),
            MagicMock(spec=D5eMonster, name="Orc", challenge_rating=0.5),
        ]
        self.mock_hub.monsters.get_by_cr_range.return_value = mock_monsters

        result = self.service.get_monsters_by_cr(0.0, 1.0)

        self.assertEqual(len(result), 2)
        self.mock_hub.monsters.get_by_cr_range.assert_called_once_with(0.0, 1.0)

    def test_get_encounter_xp_budget(self) -> None:
        """Test calculating encounter XP budget."""
        # Test medium encounter for level 5 party
        party_levels = [5, 5, 5, 5]

        budget = self.service.get_encounter_xp_budget(party_levels, "medium")
        self.assertEqual(budget, 2000)  # 4 * 500

        # Test hard encounter
        budget = self.service.get_encounter_xp_budget(party_levels, "hard")
        self.assertEqual(budget, 3000)  # 4 * 750

        # Test with mixed levels
        party_levels = [3, 4, 5, 6]
        budget = self.service.get_encounter_xp_budget(party_levels, "easy")
        self.assertEqual(budget, 750)  # 75 + 125 + 250 + 300


class TestEquipmentHelpers(TestContentService):
    """Test equipment helper methods."""

    def test_get_starting_equipment(self) -> None:
        """Test getting starting equipment."""
        # Mock equipment
        mock_longsword = D5eEquipment(
            index="longsword",
            name="Longsword",
            equipment_category=APIReference(
                index="weapon", name="Weapon", url="/api/equipment-categories/weapon"
            ),
            cost={"quantity": 15, "unit": "gp"},
            weight=3,
            url="/api/equipment/longsword",
        )

        self.mock_hub.classes.get_by_name_with_options.return_value = (
            self.sample_wizard_class
        )
        self.mock_hub.backgrounds.get_by_name.return_value = MagicMock()
        self.mock_hub.equipment.get_by_index.return_value = mock_longsword

        result = self.service.get_starting_equipment("Wizard", "Sage")

        self.assertIn("class_", result)
        self.assertIn("background", result)
        self.assertIsInstance(result["class_"], list)
        self.assertIsInstance(result["background"], list)

    def test_get_armor_ac(self) -> None:
        """Test calculating armor AC."""
        # Mock chain mail (heavy armor, no dex bonus)
        mock_armor = D5eEquipment(
            index="chain-mail",
            name="Chain Mail",
            equipment_category=APIReference(
                index="armor", name="Armor", url="/api/equipment-categories/armor"
            ),
            armor_category="Heavy",
            armor_class={"base": 16, "dex_bonus": False, "max_bonus": None},
            str_minimum=13,
            stealth_disadvantage=True,
            cost={"quantity": 75, "unit": "gp"},
            weight=55,
            url="/api/equipment/chain-mail",
        )

        self.mock_hub.equipment.get_by_name.return_value = mock_armor

        # Test with dexterity modifier (should be ignored for heavy armor)
        ac = self.service.get_armor_ac("Chain Mail", dexterity_modifier=2)
        self.assertEqual(ac, 16)

        # Create different armor for different tests
        # Mock leather armor (light armor, full dex bonus)
        leather_armor = MagicMock()
        leather_armor.armor_class = {"base": 11, "dex_bonus": True, "max_bonus": None}
        self.mock_hub.equipment.get_by_name.return_value = leather_armor
        ac = self.service.get_armor_ac("Leather", dexterity_modifier=3)
        self.assertEqual(ac, 14)  # 11 + 3

        # Mock medium armor (limited dex bonus)
        scale_armor = MagicMock()
        scale_armor.armor_class = {"base": 14, "dex_bonus": True, "max_bonus": 2}
        self.mock_hub.equipment.get_by_name.return_value = scale_armor
        ac = self.service.get_armor_ac("Scale Mail", dexterity_modifier=3)
        self.assertEqual(ac, 16)  # 14 + 2 (capped)


class TestRulesHelpers(TestContentService):
    """Test rules helper methods."""

    def test_get_rule_section(self) -> None:
        """Test getting rule section text."""
        # Mock rule sections and rules
        mock_section = MagicMock()
        mock_section.index = "combat"
        mock_section.name = "Combat"

        mock_rule = MagicMock()
        mock_rule.parent = APIReference(
            index="combat", name="Combat", url="/api/rule-sections/combat"
        )
        mock_rule.desc = ["Combat rules text...", "More combat rules..."]

        self.mock_hub.rule_sections.list_all.return_value = [mock_section]
        self.mock_hub.rules.list_all.return_value = [mock_rule]

        result = self.service.get_rule_section("combat")

        self.assertEqual(len(result), 2)
        self.assertIn("Combat rules text...", result)


class TestCharacterValidation(TestContentService):
    """Test character validation methods."""

    def test_validate_ability_scores_standard(self) -> None:
        """Test validating standard ability scores."""
        scores = {
            "str": 15,
            "dex": 14,
            "con": 13,
            "int": 12,
            "wis": 10,
            "cha": 8,
        }

        is_valid, errors = self.service.validate_ability_scores(scores, "standard")

        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_validate_ability_scores_missing(self) -> None:
        """Test validation with missing abilities."""
        scores = {
            "str": 15,
            "dex": 14,
            "con": 13,
        }

        is_valid, errors = self.service.validate_ability_scores(scores, "standard")

        self.assertFalse(is_valid)
        self.assertIn("Missing ability scores", errors[0])

    def test_validate_ability_scores_point_buy(self) -> None:
        """Test point buy validation."""
        # Valid point buy
        scores = {
            "str": 15,  # 9 points
            "dex": 14,  # 7 points
            "con": 13,  # 5 points
            "int": 12,  # 4 points
            "wis": 10,  # 2 points
            "cha": 8,  # 0 points
        }  # Total: 27 points

        is_valid, errors = self.service.validate_ability_scores(scores, "point-buy")
        self.assertTrue(is_valid)

        # Invalid point buy (too high)
        scores["str"] = 16  # Would exceed point limit
        is_valid, errors = self.service.validate_ability_scores(scores, "point-buy")
        self.assertFalse(is_valid)
        self.assertTrue(any("between 8 and 15" in e for e in errors))


class TestUtilityMethods(unittest.TestCase):
    """Test utility methods."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Mock the repository hub
        self.mock_hub = MagicMock(spec=D5eDbRepositoryHub)

        # Create service with mocked repository hub
        self.service = ContentService(repository_hub=self.mock_hub)

        # Sample data
        self.sample_wizard_class = MagicMock(spec=D5eClass)
        self.sample_wizard_class.index = "wizard"
        self.sample_wizard_class.name = "Wizard"
        self.sample_wizard_class.spellcasting = MagicMock()

    def test_search_all_content(self) -> None:
        """Test searching across content."""
        mock_results = {"spells": [MagicMock()], "monsters": [MagicMock()]}
        self.mock_hub.search_all_with_options.return_value = mock_results

        # Test without category filter
        results = self.service.search_all_content("fire")
        self.assertEqual(len(results), 2)
        self.assertIn("spells", results)
        self.assertIn("monsters", results)

        # Test with category filter
        mock_repo = MagicMock()
        mock_repo.search_with_options.return_value = [MagicMock()]
        self.mock_hub.get_repository.return_value = mock_repo

        results = self.service.search_all_content("fire", categories=["spells"])
        self.assertIn("spells", results)

    def test_get_content_statistics(self) -> None:
        """Test getting content statistics."""
        mock_stats = {"spells": 319, "monsters": 332, "classes": 12}
        self.mock_hub.get_statistics.return_value = mock_stats

        stats = self.service.get_content_statistics()

        self.assertEqual(stats["spells"], 319)
        self.assertEqual(stats["monsters"], 332)
        self.assertEqual(stats["classes"], 12)

    def test_calculate_spell_save_dc(self) -> None:
        """Test calculating spell save DC."""
        self.mock_hub.classes.get_by_name.return_value = self.sample_wizard_class
        self.mock_hub.classes.get_proficiency_bonus.return_value = 3

        # Level 5 wizard with +3 INT modifier
        dc = self.service.calculate_spell_save_dc("Wizard", 5, 3)

        self.assertEqual(dc, 14)  # 8 + 3 (prof) + 3 (mod)

        # Non-spellcasting class
        self.mock_hub.classes.get_by_name.return_value = MagicMock(spellcasting=None)
        dc = self.service.calculate_spell_save_dc("Fighter", 5, 3)
        self.assertIsNone(dc)


if __name__ == "__main__":
    unittest.main()
