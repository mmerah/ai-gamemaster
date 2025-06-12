"""Integration tests for the database migration script."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterator, List

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import (
    Base,
    ContentPack,
    Equipment,
    Monster,
    Spell,
)
from scripts.migrate_json_to_db import D5eDataMigrator


class TestDatabaseMigration:
    """Test the JSON to database migration process."""

    @pytest.fixture
    def temp_db(self) -> Iterator[str]:
        """Create a temporary SQLite database."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        # Create all tables
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        yield f"sqlite:///{db_path}"

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def sample_json_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create sample JSON data for testing."""
        return {
            "5e-SRD-Backgrounds.json": [
                {
                    "index": "acolyte",
                    "name": "Acolyte",
                    "starting_proficiencies": [
                        {
                            "index": "skill-insight",
                            "name": "Skill: Insight",
                            "url": "/api/proficiencies/skill-insight",
                        }
                    ],
                    "language_options": {
                        "choose": 2,
                        "type": "languages",
                        "from": {
                            "option_set_type": "resource_list",
                            "resource_list_url": "/api/languages",
                        },
                    },
                    "starting_equipment": [
                        {
                            "equipment": {
                                "index": "clothes-common",
                                "name": "Clothes, common",
                                "url": "/api/equipment/clothes-common",
                            },
                            "quantity": 1,
                        }
                    ],
                    "starting_equipment_options": [],
                    "feature": {
                        "name": "Shelter of the Faithful",
                        "desc": [
                            "As an acolyte, you command the respect of those who share your faith."
                        ],
                    },
                    "personality_traits": {
                        "choose": 2,
                        "type": "personality_traits",
                        "from": {
                            "option_set_type": "options_array",
                            "options": [
                                {
                                    "option_type": "string",
                                    "string": "I idolize a particular hero of my faith.",
                                }
                            ],
                        },
                    },
                    "ideals": {
                        "choose": 1,
                        "type": "ideals",
                        "from": {
                            "option_set_type": "options_array",
                            "options": [
                                {
                                    "option_type": "ideal",
                                    "desc": "Tradition. The ancient traditions must be preserved.",
                                    "alignments": [],
                                }
                            ],
                        },
                    },
                    "bonds": {
                        "choose": 1,
                        "type": "bonds",
                        "from": {
                            "option_set_type": "options_array",
                            "options": [
                                {
                                    "option_type": "string",
                                    "string": "I would die to recover an ancient relic.",
                                }
                            ],
                        },
                    },
                    "flaws": {
                        "choose": 1,
                        "type": "flaws",
                        "from": {
                            "option_set_type": "options_array",
                            "options": [
                                {
                                    "option_type": "string",
                                    "string": "I judge others harshly.",
                                }
                            ],
                        },
                    },
                    "url": "/api/backgrounds/acolyte",
                }
            ],
            "5e-SRD-Spells.json": [
                {
                    "index": "fireball",
                    "name": "Fireball",
                    "desc": [
                        "A bright streak flashes from your pointing finger to a point you choose within range and then blossoms with a low roar into an explosion of flame."
                    ],
                    "higher_level": [
                        "When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d6 for each slot level above 3rd."
                    ],
                    "range": "150 feet",
                    "components": ["V", "S", "M"],
                    "material": "A tiny ball of bat guano and sulfur.",
                    "ritual": False,
                    "duration": "Instantaneous",
                    "concentration": False,
                    "casting_time": "1 action",
                    "level": 3,
                    "damage": {
                        "damage_type": {
                            "index": "fire",
                            "name": "Fire",
                            "url": "/api/damage-types/fire",
                        },
                        "damage_at_slot_level": {"3": "8d6"},
                    },
                    "dc": {
                        "dc_type": {
                            "index": "dex",
                            "name": "DEX",
                            "url": "/api/ability-scores/dex",
                        },
                        "dc_success": "half",
                    },
                    "area_of_effect": {"type": "sphere", "size": 20},
                    "school": {
                        "index": "evocation",
                        "name": "Evocation",
                        "url": "/api/magic-schools/evocation",
                    },
                    "classes": [
                        {
                            "index": "sorcerer",
                            "name": "Sorcerer",
                            "url": "/api/classes/sorcerer",
                        },
                        {
                            "index": "wizard",
                            "name": "Wizard",
                            "url": "/api/classes/wizard",
                        },
                    ],
                    "subclasses": [],
                    "url": "/api/spells/fireball",
                },
                {
                    "index": "magic-missile",
                    "name": "Magic Missile",
                    "desc": [
                        "You create three glowing darts of magical force. Each dart hits a creature of your choice that you can see within range."
                    ],
                    "higher_level": [
                        "When you cast this spell using a spell slot of 2nd level or higher, the spell creates one more dart for each slot level above 1st."
                    ],
                    "range": "120 feet",
                    "components": ["V", "S"],
                    "ritual": False,
                    "duration": "Instantaneous",
                    "concentration": False,
                    "casting_time": "1 action",
                    "level": 1,
                    "damage": {
                        "damage_type": {
                            "index": "force",
                            "name": "Force",
                            "url": "/api/damage-types/force",
                        },
                        "damage_at_slot_level": {"1": "1d4 + 1"},
                    },
                    "school": {
                        "index": "evocation",
                        "name": "Evocation",
                        "url": "/api/magic-schools/evocation",
                    },
                    "classes": [
                        {
                            "index": "sorcerer",
                            "name": "Sorcerer",
                            "url": "/api/classes/sorcerer",
                        },
                        {
                            "index": "wizard",
                            "name": "Wizard",
                            "url": "/api/classes/wizard",
                        },
                    ],
                    "subclasses": [],
                    "url": "/api/spells/magic-missile",
                },
            ],
            "5e-SRD-Monsters.json": [
                {
                    "index": "goblin",
                    "name": "Goblin",
                    "size": "Small",
                    "type": "humanoid",
                    "subtype": "goblinoid",
                    "alignment": "neutral evil",
                    "armor_class": [
                        {"type": "dex", "value": 15, "desc": "Leather Armor, Shield"}
                    ],
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
                    "proficiencies": [
                        {
                            "value": 2,
                            "proficiency": {
                                "index": "skill-stealth",
                                "name": "Skill: Stealth",
                                "url": "/api/proficiencies/skill-stealth",
                            },
                        }
                    ],
                    "damage_vulnerabilities": [],
                    "damage_resistances": [],
                    "damage_immunities": [],
                    "condition_immunities": [],
                    "senses": {"darkvision": "60 ft.", "passive_perception": 9},
                    "languages": "Common, Goblin",
                    "challenge_rating": 0.25,
                    "proficiency_bonus": 2,
                    "xp": 50,
                    "special_abilities": [
                        {
                            "name": "Nimble Escape",
                            "desc": "The goblin can take the Disengage or Hide action as a bonus action on each of its turns.",
                        }
                    ],
                    "actions": [
                        {
                            "name": "Scimitar",
                            "desc": "Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 5 (1d6 + 2) slashing damage.",
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
            ],
            "5e-SRD-Equipment.json": [
                {
                    "index": "longsword",
                    "name": "Longsword",
                    "equipment_category": {
                        "index": "weapon",
                        "name": "Weapon",
                        "url": "/api/equipment-categories/weapon",
                    },
                    "weapon_category": "Martial",
                    "weapon_range": "Melee",
                    "category_range": "Martial Melee",
                    "cost": {"quantity": 15, "unit": "gp"},
                    "damage": {
                        "damage_dice": "1d8",
                        "damage_type": {
                            "index": "slashing",
                            "name": "Slashing",
                            "url": "/api/damage-types/slashing",
                        },
                    },
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
            ],
        }

    @pytest.fixture
    def temp_json_dir(
        self, sample_json_data: Dict[str, List[Dict[str, Any]]]
    ) -> Iterator[Path]:
        """Create a temporary directory with sample JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write sample JSON files
            for filename, data in sample_json_data.items():
                file_path = tmpdir_path / filename
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

            yield tmpdir_path

    def test_create_content_pack(self, temp_db: str) -> None:
        """Test creating the D&D 5e SRD content pack."""
        migrator = D5eDataMigrator(temp_db)
        migrator.create_content_pack()

        # Verify content pack was created
        engine = create_engine(temp_db)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            content_pack = session.query(ContentPack).filter_by(id="dnd_5e_srd").first()
            assert content_pack is not None
            assert content_pack.name == "D&D 5e SRD"
            assert content_pack.is_active is True
        finally:
            session.close()
            engine.dispose()

    def test_migrate_spells(
        self,
        temp_db: str,
        temp_json_dir: Path,
    ) -> None:
        """Test migrating spell data."""
        migrator = D5eDataMigrator(temp_db, str(temp_json_dir))
        migrator.create_content_pack()

        # Migrate spells
        count = migrator.migrate_file("5e-SRD-Spells.json")
        assert count == 2

        migrator.session.commit()

        # Verify spells were created
        engine = create_engine(temp_db)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Check fireball
        fireball = session.query(Spell).filter_by(index="fireball").first()
        assert fireball is not None
        assert fireball.name == "Fireball"
        assert fireball.level == 3
        assert fireball.content_pack_id == "dnd_5e_srd"

        # Check magic missile
        magic_missile = session.query(Spell).filter_by(index="magic-missile").first()
        assert magic_missile is not None
        assert magic_missile.name == "Magic Missile"
        assert magic_missile.level == 1

        session.close()

    def test_migrate_monsters(
        self,
        temp_db: str,
        temp_json_dir: Path,
    ) -> None:
        """Test migrating monster data."""
        migrator = D5eDataMigrator(temp_db, str(temp_json_dir))
        migrator.create_content_pack()

        # Migrate monsters
        count = migrator.migrate_file("5e-SRD-Monsters.json")
        assert count == 1

        migrator.session.commit()

        # Verify monster was created
        engine = create_engine(temp_db)
        Session = sessionmaker(bind=engine)
        session = Session()

        goblin = session.query(Monster).filter_by(index="goblin").first()
        assert goblin is not None
        assert goblin.name == "Goblin"
        assert goblin.size == "Small"
        assert goblin.challenge_rating == 0.25
        assert goblin.hit_points == 7
        assert goblin.strength == 8
        assert goblin.dexterity == 14

        session.close()

    def test_migrate_equipment(
        self,
        temp_db: str,
        temp_json_dir: Path,
    ) -> None:
        """Test migrating equipment data."""
        migrator = D5eDataMigrator(temp_db, str(temp_json_dir))
        migrator.create_content_pack()

        # Migrate equipment
        count = migrator.migrate_file("5e-SRD-Equipment.json")
        assert count == 1

        migrator.session.commit()

        # Verify equipment was created
        engine = create_engine(temp_db)
        Session = sessionmaker(bind=engine)
        session = Session()

        longsword = session.query(Equipment).filter_by(index="longsword").first()
        assert longsword is not None
        assert longsword.name == "Longsword"
        assert longsword.weapon_category == "Martial"
        assert longsword.weight == 3

        session.close()

    def test_migrate_all(
        self,
        temp_db: str,
        temp_json_dir: Path,
    ) -> None:
        """Test migrating all data files."""
        # Update FILE_MAPPING to only include our test files
        original_mapping = D5eDataMigrator.FILE_MAPPING
        D5eDataMigrator.FILE_MAPPING = {
            k: v
            for k, v in original_mapping.items()
            if k
            in ["5e-SRD-Spells.json", "5e-SRD-Monsters.json", "5e-SRD-Equipment.json"]
        }

        try:
            migrator = D5eDataMigrator(temp_db, str(temp_json_dir))
            migrator.migrate_all()

            # Verify data was migrated
            engine = create_engine(temp_db)
            Session = sessionmaker(bind=engine)
            session = Session()

            # Check counts
            assert session.query(ContentPack).count() == 1
            assert session.query(Spell).count() == 2
            assert session.query(Monster).count() == 1
            assert session.query(Equipment).count() == 1

            session.close()
        finally:
            # Restore original mapping
            D5eDataMigrator.FILE_MAPPING = original_mapping

    def test_schema_integrity(self, temp_db: str) -> None:
        """Test that all expected tables are created with correct columns."""
        engine = create_engine(temp_db)
        inspector = inspect(engine)

        # Check that all expected tables exist
        expected_tables = [
            "content_packs",
            "ability_scores",
            "alignments",
            "backgrounds",
            "classes",
            "conditions",
            "damage_types",
            "equipment",
            "equipment_categories",
            "feats",
            "features",
            "languages",
            "levels",
            "magic_items",
            "magic_schools",
            "monsters",
            "proficiencies",
            "races",
            "rules",
            "rule_sections",
            "skills",
            "spells",
            "subclasses",
            "subraces",
            "traits",
            "weapon_properties",
        ]

        actual_tables = inspector.get_table_names()
        for table in expected_tables:
            assert table in actual_tables, f"Missing table: {table}"

        # Check some key columns in spells table
        spell_columns = {col["name"] for col in inspector.get_columns("spells")}
        expected_spell_columns = {
            "index",
            "name",
            "url",
            "content_pack_id",
            "desc",
            "level",
            "range",
            "components",
            "duration",
            "casting_time",
        }
        for col in expected_spell_columns:
            assert col in spell_columns, f"Missing column in spells: {col}"

        # Check foreign key constraint
        spell_fks = inspector.get_foreign_keys("spells")
        assert len(spell_fks) == 1
        assert spell_fks[0]["referred_table"] == "content_packs"
        assert spell_fks[0]["constrained_columns"] == ["content_pack_id"]
