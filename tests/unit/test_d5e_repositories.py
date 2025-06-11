"""Unit tests for D5e repository implementations."""

import unittest
from typing import Any, Dict, List, cast
from unittest.mock import MagicMock, patch

from app.models.d5e import (
    APIReference,
    D5eClass,
    D5eEquipment,
    D5eMonster,
    D5eSpell,
)
from app.models.d5e.base import Cost
from app.repositories.d5e import (
    BaseD5eRepository,
    ClassRepository,
    D5eRepositoryFactory,
    D5eRepositoryHub,
    EquipmentRepository,
    MonsterRepository,
    SpellRepository,
)
from app.services.d5e.index_builder import D5eIndexBuilder
from app.services.d5e.reference_resolver import D5eReferenceResolver


class TestBaseD5eRepository(unittest.TestCase):
    """Test the base repository functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_index_builder = MagicMock(spec=D5eIndexBuilder)
        self.mock_reference_resolver = MagicMock(spec=D5eReferenceResolver)

        # Create repository
        self.repository = BaseD5eRepository(
            category="test-category",
            model_class=D5eSpell,
            index_builder=self.mock_index_builder,
            reference_resolver=self.mock_reference_resolver,
        )

        # Sample data
        self.sample_spell_data = {
            "index": "fireball",
            "name": "Fireball",
            "level": 3,
            "school": {
                "index": "evocation",
                "name": "Evocation",
                "url": "/api/magic-schools/evocation",
            },
            "casting_time": "1 action",
            "range": "150 feet",
            "components": ["V", "S", "M"],
            "material": "A tiny ball of bat guano and sulfur",
            "duration": "Instantaneous",
            "concentration": False,
            "ritual": False,
            "desc": ["A bright streak flashes..."],
            "higher_level": [
                "When you cast this spell using a spell slot of 4th level or higher..."
            ],
            "classes": [
                {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"},
                {
                    "index": "sorcerer",
                    "name": "Sorcerer",
                    "url": "/api/classes/sorcerer",
                },
            ],
            "subclasses": [],
            "url": "/api/spells/fireball",
        }

    def test_get_by_index_success(self) -> None:
        """Test successful retrieval by index."""
        self.mock_index_builder.get_by_index.return_value = self.sample_spell_data
        self.mock_reference_resolver.resolve_deep.return_value = self.sample_spell_data

        result = self.repository.get_by_index("fireball")

        self.assertIsNotNone(result)
        self.assertIsInstance(result, D5eSpell)
        # Cast to D5eSpell since we've verified it's not None and is the right type
        assert isinstance(result, D5eSpell)
        spell_result = result
        self.assertEqual(spell_result.index, "fireball")
        self.assertEqual(spell_result.name, "Fireball")
        self.mock_index_builder.get_by_index.assert_called_once_with(
            "test-category", "fireball"
        )

    def test_get_by_index_not_found(self) -> None:
        """Test retrieval by index when not found."""
        self.mock_index_builder.get_by_index.return_value = None

        result = self.repository.get_by_index("nonexistent")

        self.assertIsNone(result)

    def test_get_by_name_success(self) -> None:
        """Test successful retrieval by name."""
        self.mock_index_builder.get_by_name.return_value = self.sample_spell_data
        self.mock_reference_resolver.resolve_deep.return_value = self.sample_spell_data

        result = self.repository.get_by_name("Fireball")

        self.assertIsNotNone(result)
        # Cast to D5eSpell since we've verified it's not None
        assert isinstance(result, D5eSpell)
        spell_result = result
        self.assertEqual(spell_result.name, "Fireball")
        self.mock_index_builder.get_by_name.assert_called_once_with(
            "test-category", "Fireball"
        )

    def test_list_all(self) -> None:
        """Test listing all entities."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.sample_spell_data
        ]

        results = self.repository.list_all_with_options(resolve_references=False)

        self.assertEqual(len(results), 1)
        # Results are typed as List[D5eSpell] from list_all_with_options
        self.assertEqual(results[0].index, "fireball")

    def test_search(self) -> None:
        """Test search functionality."""
        self.mock_index_builder.search.return_value = [self.sample_spell_data]

        results = self.repository.search("fire")

        self.assertEqual(len(results), 1)
        # Cast to D5eSpell for type safety
        assert isinstance(results[0], D5eSpell)
        spell_result = results[0]
        self.assertEqual(spell_result.name, "Fireball")
        self.mock_index_builder.search.assert_called_once_with("test-category", "fire")

    def test_filter_by(self) -> None:
        """Test filtering by field values."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.sample_spell_data,
            {
                **self.sample_spell_data,
                "index": "magic-missile",
                "name": "Magic Missile",
                "level": 1,
            },
        ]

        results = self.repository.filter_by(level=3)

        self.assertEqual(len(results), 1)
        # Cast to D5eSpell for type safety
        assert isinstance(results[0], D5eSpell)
        spell_result = results[0]
        self.assertEqual(spell_result.index, "fireball")

    def test_exists(self) -> None:
        """Test existence check."""
        self.mock_index_builder.get_by_index.return_value = self.sample_spell_data

        self.assertTrue(self.repository.exists("fireball"))

        self.mock_index_builder.get_by_index.return_value = None
        self.assertFalse(self.repository.exists("nonexistent"))

    def test_count(self) -> None:
        """Test entity count."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.sample_spell_data,
            {},
            {},
        ]

        count = self.repository.count()

        self.assertEqual(count, 3)


class TestSpellRepository(unittest.TestCase):
    """Test the spell repository specialized functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_index_builder = MagicMock(spec=D5eIndexBuilder)
        self.mock_reference_resolver = MagicMock(spec=D5eReferenceResolver)

        self.repository = SpellRepository(
            index_builder=self.mock_index_builder,
            reference_resolver=self.mock_reference_resolver,
        )

        # Sample spells
        self.fireball_data = {
            "index": "fireball",
            "name": "Fireball",
            "level": 3,
            "school": {
                "index": "evocation",
                "name": "Evocation",
                "url": "/api/magic-schools/evocation",
            },
            "casting_time": "1 action",
            "range": "150 feet",
            "components": ["V", "S", "M"],
            "material": "A tiny ball of bat guano and sulfur",
            "duration": "Instantaneous",
            "concentration": False,
            "ritual": False,
            "desc": ["A bright streak flashes..."],
            "classes": [
                {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"},
                {
                    "index": "sorcerer",
                    "name": "Sorcerer",
                    "url": "/api/classes/sorcerer",
                },
            ],
            "subclasses": [],
            "url": "/api/spells/fireball",
        }

        self.identify_data = {
            "index": "identify",
            "name": "Identify",
            "level": 1,
            "school": {
                "index": "divination",
                "name": "Divination",
                "url": "/api/magic-schools/divination",
            },
            "casting_time": "1 minute",
            "range": "Touch",
            "components": ["V", "S", "M"],
            "material": "A pearl worth at least 100 gp and an owl feather",
            "duration": "Instantaneous",
            "concentration": False,
            "ritual": True,
            "desc": ["You choose one object..."],
            "classes": [
                {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"},
                {"index": "bard", "name": "Bard", "url": "/api/classes/bard"},
            ],
            "subclasses": [],
            "url": "/api/spells/identify",
        }

    def test_get_by_level(self) -> None:
        """Test getting spells by level."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.fireball_data,
            self.identify_data,
        ]

        level_3_spells = self.repository.get_by_level(3)

        self.assertEqual(len(level_3_spells), 1)
        self.assertEqual(level_3_spells[0].name, "Fireball")

    def test_get_by_school(self) -> None:
        """Test getting spells by school."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.fireball_data,
            self.identify_data,
        ]

        evocation_spells = self.repository.get_by_school("evocation")

        self.assertEqual(len(evocation_spells), 1)
        self.assertEqual(evocation_spells[0].name, "Fireball")

    def test_get_by_class(self) -> None:
        """Test getting spells by class."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.fireball_data,
            self.identify_data,
        ]

        wizard_spells = self.repository.get_by_class("wizard")

        self.assertEqual(len(wizard_spells), 2)

        bard_spells = self.repository.get_by_class("bard")
        self.assertEqual(len(bard_spells), 1)
        self.assertEqual(bard_spells[0].name, "Identify")

    def test_get_ritual_spells(self) -> None:
        """Test getting ritual spells."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.fireball_data,
            self.identify_data,
        ]

        ritual_spells = self.repository.get_ritual_spells()

        self.assertEqual(len(ritual_spells), 1)
        self.assertEqual(ritual_spells[0].name, "Identify")

    def test_get_by_components(self) -> None:
        """Test filtering by components."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.fireball_data,
            self.identify_data,
        ]

        # Both spells have all components
        all_components = self.repository.get_by_components(
            verbal=True, somatic=True, material=True
        )
        self.assertEqual(len(all_components), 2)

        # Test filtering for spells without material components
        no_material = self.repository.get_by_components(material=False)
        self.assertEqual(len(no_material), 0)


class TestMonsterRepository(unittest.TestCase):
    """Test the monster repository specialized functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_index_builder = MagicMock(spec=D5eIndexBuilder)
        self.mock_reference_resolver = MagicMock(spec=D5eReferenceResolver)

        self.repository = MonsterRepository(
            index_builder=self.mock_index_builder,
            reference_resolver=self.mock_reference_resolver,
        )

        # Sample monsters
        self.goblin_data = {
            "index": "goblin",
            "name": "Goblin",
            "size": "Small",
            "type": "humanoid (goblinoid)",
            "alignment": "neutral evil",
            "armor_class": [{"type": "natural", "value": 15}],
            "hit_points": 7,
            "hit_dice": "2d6",
            "hit_points_roll": "2d6",
            "speed": {"walk": "30 ft."},
            "strength": 8,
            "dexterity": 14,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 8,
            "charisma": 8,
            "proficiencies": [],
            "damage_vulnerabilities": [],
            "damage_resistances": [],
            "damage_immunities": [],
            "condition_immunities": [],
            "senses": {"darkvision": "60 ft.", "passive_perception": 9},
            "languages": "Common, Goblin",
            "challenge_rating": 0.25,
            "proficiency_bonus": 2,
            "xp": 50,
            "actions": [
                {
                    "name": "Scimitar",
                    "desc": "Melee Weapon Attack: +4 to hit...",
                    "attack_bonus": 4,
                    "damage": [
                        {
                            "damage_type": {
                                "index": "slashing",
                                "name": "Slashing",
                                "url": "/api/damage-types/slashing",
                            },
                            "damage_dice": "1d6+2",
                        }
                    ],
                }
            ],
            "url": "/api/monsters/goblin",
        }

        self.dragon_data = {
            "index": "adult-red-dragon",
            "name": "Adult Red Dragon",
            "size": "Huge",
            "type": "dragon",
            "alignment": "chaotic evil",
            "armor_class": [{"type": "natural", "value": 19}],
            "hit_points": 256,
            "hit_dice": "19d12+133",
            "hit_points_roll": "19d12+133",
            "speed": {"walk": "40 ft.", "climb": "40 ft.", "fly": "80 ft."},
            "strength": 27,
            "dexterity": 10,
            "constitution": 25,
            "intelligence": 16,
            "wisdom": 13,
            "charisma": 21,
            "proficiencies": [],
            "damage_vulnerabilities": [],
            "damage_resistances": [],
            "damage_immunities": ["fire"],
            "condition_immunities": [],
            "senses": {
                "blindsight": "60 ft.",
                "darkvision": "120 ft.",
                "passive_perception": 23,
            },
            "languages": "Common, Draconic",
            "challenge_rating": 17,
            "proficiency_bonus": 6,
            "xp": 18000,
            "legendary_actions": [
                {
                    "name": "Detect",
                    "desc": "The dragon makes a Wisdom (Perception) check.",
                },
                {"name": "Tail Attack", "desc": "The dragon makes a tail attack."},
                {
                    "name": "Wing Attack (Costs 2 Actions)",
                    "desc": "The dragon beats its wings...",
                },
            ],
            "actions": [],
            "url": "/api/monsters/adult-red-dragon",
        }

    def test_get_by_challenge_rating(self) -> None:
        """Test getting monsters by CR."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.goblin_data,
            self.dragon_data,
        ]

        cr_025_monsters = self.repository.get_by_challenge_rating(0.25)

        self.assertEqual(len(cr_025_monsters), 1)
        self.assertEqual(cr_025_monsters[0].name, "Goblin")

    def test_get_by_cr_range(self) -> None:
        """Test getting monsters within CR range."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.goblin_data,
            self.dragon_data,
        ]

        low_cr_monsters = self.repository.get_by_cr_range(0.0, 1.0)

        self.assertEqual(len(low_cr_monsters), 1)
        self.assertEqual(low_cr_monsters[0].name, "Goblin")

    def test_get_by_type(self) -> None:
        """Test getting monsters by type."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.goblin_data,
            self.dragon_data,
        ]

        dragons = self.repository.get_by_type("dragon")

        self.assertEqual(len(dragons), 1)
        self.assertEqual(dragons[0].name, "Adult Red Dragon")

    def test_get_legendary_monsters(self) -> None:
        """Test getting legendary monsters."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.goblin_data,
            self.dragon_data,
        ]

        legendary = self.repository.get_legendary_monsters()

        self.assertEqual(len(legendary), 1)
        self.assertEqual(legendary[0].name, "Adult Red Dragon")

    def test_get_by_damage_immunity(self) -> None:
        """Test getting monsters by damage immunity."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.goblin_data,
            self.dragon_data,
        ]

        fire_immune = self.repository.get_by_damage_immunity("fire")

        self.assertEqual(len(fire_immune), 1)
        self.assertEqual(fire_immune[0].name, "Adult Red Dragon")


class TestClassRepository(unittest.TestCase):
    """Test the class repository specialized functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_index_builder = MagicMock(spec=D5eIndexBuilder)
        self.mock_reference_resolver = MagicMock(spec=D5eReferenceResolver)

        self.repository = ClassRepository(
            index_builder=self.mock_index_builder,
            reference_resolver=self.mock_reference_resolver,
        )

        # Sample class data
        self.wizard_data = {
            "index": "wizard",
            "name": "Wizard",
            "hit_die": 6,
            "proficiency_choices": [],
            "proficiencies": [],
            "saving_throws": [
                {"index": "int", "name": "INT", "url": "/api/ability-scores/int"},
                {"index": "wis", "name": "WIS", "url": "/api/ability-scores/wis"},
            ],
            "starting_equipment": [],
            "starting_equipment_options": [],
            "class_levels": "/api/classes/wizard/levels",
            "multi_classing": {
                "prerequisites": [
                    {
                        "ability_score": {
                            "index": "int",
                            "name": "INT",
                            "url": "/api/ability-scores/int",
                        },
                        "minimum_score": 13,
                    }
                ],
                "proficiencies": [],
            },
            "subclasses": [],
            "spellcasting": {
                "level": 1,
                "spellcasting_ability": {
                    "index": "int",
                    "name": "INT",
                    "url": "/api/ability-scores/int",
                },
                "info": [],
            },
            "spells": "/api/classes/wizard/spells",
            "url": "/api/classes/wizard",
        }

        self.fighter_data = {
            "index": "fighter",
            "name": "Fighter",
            "hit_die": 10,
            "proficiency_choices": [],
            "proficiencies": [],
            "saving_throws": [
                {"index": "str", "name": "STR", "url": "/api/ability-scores/str"},
                {"index": "con", "name": "CON", "url": "/api/ability-scores/con"},
            ],
            "starting_equipment": [],
            "starting_equipment_options": [],
            "class_levels": "/api/classes/fighter/levels",
            "multi_classing": {
                "prerequisites": [
                    {
                        "ability_score": {
                            "index": "str",
                            "name": "STR",
                            "url": "/api/ability-scores/str",
                        },
                        "minimum_score": 13,
                    }
                ],
                "proficiencies": [],
            },
            "subclasses": [],
            "url": "/api/classes/fighter",
        }

    def test_get_spellcasting_classes(self) -> None:
        """Test getting spellcasting classes."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.wizard_data,
            self.fighter_data,
        ]

        spellcasters = self.repository.get_spellcasting_classes()

        self.assertEqual(len(spellcasters), 1)
        self.assertEqual(spellcasters[0].name, "Wizard")

    def test_get_by_hit_die(self) -> None:
        """Test getting classes by hit die."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.wizard_data,
            self.fighter_data,
        ]

        d10_classes = self.repository.get_by_hit_die(10)

        self.assertEqual(len(d10_classes), 1)
        self.assertEqual(d10_classes[0].name, "Fighter")

    def test_get_proficiency_bonus(self) -> None:
        """Test proficiency bonus calculation."""
        self.assertEqual(self.repository.get_proficiency_bonus(1), 2)
        self.assertEqual(self.repository.get_proficiency_bonus(5), 3)
        self.assertEqual(self.repository.get_proficiency_bonus(9), 4)
        self.assertEqual(self.repository.get_proficiency_bonus(13), 5)
        self.assertEqual(self.repository.get_proficiency_bonus(17), 6)


class TestEquipmentRepository(unittest.TestCase):
    """Test the equipment repository specialized functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_index_builder = MagicMock(spec=D5eIndexBuilder)
        self.mock_reference_resolver = MagicMock(spec=D5eReferenceResolver)

        self.repository = EquipmentRepository(
            index_builder=self.mock_index_builder,
            reference_resolver=self.mock_reference_resolver,
        )

        # Sample equipment
        self.longsword_data = {
            "index": "longsword",
            "name": "Longsword",
            "equipment_category": {
                "index": "weapon",
                "name": "Weapon",
                "url": "/api/equipment-categories/weapon",
            },
            "weapon_category": "Martial",
            "weapon_range": "Melee",
            "cost": {"quantity": 15, "unit": "gp"},
            "damage": {
                "damage_dice": "1d8",
                "damage_type": {
                    "index": "slashing",
                    "name": "Slashing",
                    "url": "/api/damage-types/slashing",
                },
            },
            "range": {"normal": 5},
            "weight": 3,
            "properties": [
                {
                    "index": "versatile",
                    "name": "Versatile",
                    "url": "/api/weapon-properties/versatile",
                }
            ],
            "url": "/api/equipment/longsword",
        }

        self.chain_mail_data = {
            "index": "chain-mail",
            "name": "Chain Mail",
            "equipment_category": {
                "index": "armor",
                "name": "Armor",
                "url": "/api/equipment-categories/armor",
            },
            "armor_category": "Heavy",
            "armor_class": {"base": 16, "dex_bonus": False, "max_bonus": None},
            "str_minimum": 13,
            "stealth_disadvantage": True,
            "cost": {"quantity": 75, "unit": "gp"},
            "weight": 55,
            "url": "/api/equipment/chain-mail",
        }

    def test_get_weapons(self) -> None:
        """Test getting all weapons."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.longsword_data,
            self.chain_mail_data,
        ]

        weapons = self.repository.get_weapons()

        self.assertEqual(len(weapons), 1)
        self.assertEqual(weapons[0].name, "Longsword")

    def test_get_armor(self) -> None:
        """Test getting all armor."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.longsword_data,
            self.chain_mail_data,
        ]

        armor = self.repository.get_armor()

        self.assertEqual(len(armor), 1)
        self.assertEqual(armor[0].name, "Chain Mail")

    def test_get_by_cost_range(self) -> None:
        """Test getting equipment by cost range."""
        self.mock_index_builder.get_all_in_category.return_value = [
            self.longsword_data,
            self.chain_mail_data,
        ]

        cheap_items = self.repository.get_by_cost_range(10, 20, "gp")

        self.assertEqual(len(cheap_items), 1)
        self.assertEqual(cheap_items[0].name, "Longsword")


class TestRepositoryFactory(unittest.TestCase):
    """Test the repository factory."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_index_builder = MagicMock(spec=D5eIndexBuilder)
        self.mock_reference_resolver = MagicMock(spec=D5eReferenceResolver)

        self.factory = D5eRepositoryFactory(
            index_builder=self.mock_index_builder,
            reference_resolver=self.mock_reference_resolver,
        )

    def test_get_repository_by_category(self) -> None:
        """Test getting repositories by category."""
        spells_repo = self.factory.get("spells")
        self.assertIsInstance(spells_repo, BaseD5eRepository)

        classes_repo = self.factory.get("classes")
        self.assertIsInstance(classes_repo, BaseD5eRepository)

    def test_get_typed_repositories(self) -> None:
        """Test getting typed repository methods."""
        spells_repo = self.factory.get_spells()
        self.assertIsInstance(spells_repo, BaseD5eRepository)

        monsters_repo = self.factory.get_monsters()
        self.assertIsInstance(monsters_repo, BaseD5eRepository)

    def test_invalid_category(self) -> None:
        """Test error on invalid category."""
        with self.assertRaises(KeyError):
            self.factory.get("invalid-category")


class TestRepositoryHub(unittest.TestCase):
    """Test the repository hub."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_data_loader = MagicMock()
        self.mock_reference_resolver = MagicMock()
        self.mock_index_builder = MagicMock()

        self.hub = D5eRepositoryHub(
            data_loader=self.mock_data_loader,
            reference_resolver=self.mock_reference_resolver,
            index_builder=self.mock_index_builder,
        )

    def test_specialized_repositories(self) -> None:
        """Test access to specialized repositories."""
        self.assertIsInstance(self.hub.spells, SpellRepository)
        self.assertIsInstance(self.hub.monsters, MonsterRepository)
        self.assertIsInstance(self.hub.classes, ClassRepository)
        self.assertIsInstance(self.hub.equipment, EquipmentRepository)

    def test_generic_repositories(self) -> None:
        """Test access to generic repositories."""
        self.assertIsInstance(self.hub.ability_scores, BaseD5eRepository)
        self.assertIsInstance(self.hub.skills, BaseD5eRepository)
        self.assertIsInstance(self.hub.conditions, BaseD5eRepository)

    def test_search_all(self) -> None:
        """Test searching across all repositories."""
        # Mock search results
        self.mock_index_builder.search.return_value = []

        results = self.hub.search_all("fire")

        # Should return empty dict when no results
        self.assertIsInstance(results, dict)

    def test_get_statistics(self) -> None:
        """Test getting statistics."""
        # Mock counts
        self.mock_index_builder.get_all_in_category.return_value = [{}] * 5

        stats = self.hub.get_statistics()

        self.assertIsInstance(stats, dict)
        self.assertIn("spells", stats)
        self.assertIn("monsters", stats)


if __name__ == "__main__":
    unittest.main()
