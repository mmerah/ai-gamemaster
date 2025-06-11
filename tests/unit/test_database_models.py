"""Tests for database models."""

import datetime
from decimal import Decimal
from typing import Any, Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import (
    AbilityScore,
    Alignment,
    Background,
    Base,
    CharacterClass,
    Condition,
    ContentPack,
    DamageType,
    Equipment,
    EquipmentCategory,
    Feat,
    Feature,
    Language,
    Level,
    MagicItem,
    MagicSchool,
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
    WeaponProperty,
)


class TestDatabaseModels:
    """Test database model definitions and relationships."""

    @pytest.fixture
    def db_session(self) -> Generator[Session, None, None]:
        """Create a test database session."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    def test_content_pack_creation(self, db_session: Session) -> None:
        """Test creating a content pack."""
        pack = ContentPack(
            id="srd",
            name="D&D 5e SRD",
            description="System Reference Document for D&D 5e",
            version="1.0.0",
            author="Wizards of the Coast",
            is_active=True,
        )
        db_session.add(pack)
        db_session.commit()

        # Query back
        result = db_session.execute(
            select(ContentPack).where(ContentPack.id == "srd")
        ).scalar_one()
        assert result.name == "D&D 5e SRD"
        assert result.is_active is True
        assert result.created_at is not None  # type: ignore[unreachable]

    def test_spell_creation_with_content_pack(self, db_session: Session) -> None:
        """Test creating a spell associated with a content pack."""
        # Create content pack first
        pack = ContentPack(
            id="srd",
            name="D&D 5e SRD",
            description="System Reference Document",
            version="1.0.0",
            author="WotC",
        )
        db_session.add(pack)
        db_session.commit()

        # Create spell
        spell = Spell(
            index="fireball",
            name="Fireball",
            url="/api/spells/fireball",
            content_pack_id="srd",
            desc=["A bright streak flashes..."],
            higher_level=[
                "When you cast this spell using a spell slot of 4th level..."
            ],
            range="150 feet",
            components=["V", "S", "M"],
            material="A tiny ball of bat guano and sulfur",
            ritual=False,
            duration="Instantaneous",
            concentration=False,
            casting_time="1 action",
            level=3,
            damage={
                "damage_type": {
                    "index": "fire",
                    "name": "Fire",
                    "url": "/api/damage-types/fire",
                },
                "damage_at_slot_level": {"3": "8d6"},
            },
            school={
                "index": "evocation",
                "name": "Evocation",
                "url": "/api/magic-schools/evocation",
            },
            classes=[
                {
                    "index": "sorcerer",
                    "name": "Sorcerer",
                    "url": "/api/classes/sorcerer",
                }
            ],
            subclasses=[],
        )
        db_session.add(spell)
        db_session.commit()

        # Query back with content pack
        result = db_session.execute(
            select(Spell).where(Spell.index == "fireball")
        ).scalar_one()
        assert result.name == "Fireball"
        assert result.level == 3
        assert result.content_pack_id == "srd"
        assert result.content_pack.name == "D&D 5e SRD"

    def test_monster_creation_with_cr(self, db_session: Session) -> None:
        """Test creating a monster with challenge rating."""
        pack = ContentPack(
            id="srd", name="SRD", description="", version="1.0", author="WotC"
        )
        db_session.add(pack)

        monster = Monster(
            index="goblin",
            name="Goblin",
            url="/api/monsters/goblin",
            content_pack_id="srd",
            size="Small",
            type="humanoid",
            alignment="neutral evil",
            armor_class=[{"type": "armor", "value": 15}],
            hit_points=7,
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
            senses={"darkvision": "60 ft.", "passive_perception": 9},
            languages="Common, Goblin",
            challenge_rating=0.25,
            proficiency_bonus=2,
            xp=50,
            actions=[],
        )
        db_session.add(monster)
        db_session.commit()

        result = db_session.execute(
            select(Monster).where(Monster.index == "goblin")
        ).scalar_one()
        assert result.challenge_rating == Decimal("0.25")
        assert result.xp == 50

    def test_equipment_with_cost(self, db_session: Session) -> None:
        """Test creating equipment with cost."""
        pack = ContentPack(
            id="srd", name="SRD", description="", version="1.0", author="WotC"
        )
        db_session.add(pack)

        equipment = Equipment(
            index="longsword",
            name="Longsword",
            url="/api/equipment/longsword",
            content_pack_id="srd",
            equipment_category={
                "index": "weapon",
                "name": "Weapon",
                "url": "/api/equipment-categories/weapon",
            },
            weapon_category="Martial",
            weapon_range="Melee",
            category_range="Martial Melee Weapons",
            cost={"quantity": 15, "unit": "gp"},
            damage={
                "damage_dice": "1d8",
                "damage_type": {
                    "index": "slashing",
                    "name": "Slashing",
                    "url": "/api/damage-types/slashing",
                },
            },
            weight=3,
            properties=[
                {
                    "index": "versatile",
                    "name": "Versatile",
                    "url": "/api/weapon-properties/versatile",
                }
            ],
        )
        db_session.add(equipment)
        db_session.commit()

        result = db_session.execute(
            select(Equipment).where(Equipment.index == "longsword")
        ).scalar_one()
        assert result.cost["quantity"] == 15
        assert result.cost["unit"] == "gp"
        assert result.weight == 3

    def test_class_with_levels(self, db_session: Session) -> None:
        """Test creating a character class."""
        pack = ContentPack(
            id="srd", name="SRD", description="", version="1.0", author="WotC"
        )
        db_session.add(pack)

        char_class = CharacterClass(
            index="fighter",
            name="Fighter",
            url="/api/classes/fighter",
            content_pack_id="srd",
            hit_die=10,
            proficiencies=[],
            proficiency_choices=[],
            saving_throws=[
                {"index": "str", "name": "STR", "url": "/api/ability-scores/str"},
                {"index": "con", "name": "CON", "url": "/api/ability-scores/con"},
            ],
            starting_equipment=[],
            starting_equipment_options=[],
            class_levels="/api/classes/fighter/levels",
            subclasses=[],
            spellcasting=None,
        )
        db_session.add(char_class)
        db_session.commit()

        result = db_session.execute(
            select(CharacterClass).where(CharacterClass.index == "fighter")
        ).scalar_one()
        assert result.hit_die == 10
        assert len(result.saving_throws) == 2

    def test_multiple_content_packs(self, db_session: Session) -> None:
        """Test querying entities from specific content packs."""
        # Create two content packs
        srd = ContentPack(
            id="srd",
            name="SRD",
            description="",
            version="1.0",
            author="WotC",
            is_active=True,
        )
        homebrew = ContentPack(
            id="homebrew",
            name="Homebrew",
            description="",
            version="1.0",
            author="DM",
            is_active=True,
        )
        db_session.add_all([srd, homebrew])
        db_session.commit()

        # Create spells in different packs
        spell1 = Spell(
            index="magic-missile",
            name="Magic Missile",
            url="/api/spells/magic-missile",
            content_pack_id="srd",
            level=1,
            school={
                "index": "evocation",
                "name": "Evocation",
                "url": "/api/magic-schools/evocation",
            },
            classes=[],
            desc=["You create three glowing darts..."],
        )
        spell2 = Spell(
            index="custom-blast",
            name="Custom Blast",
            url="/api/spells/custom-blast",
            content_pack_id="homebrew",
            level=2,
            school={
                "index": "evocation",
                "name": "Evocation",
                "url": "/api/magic-schools/evocation",
            },
            classes=[],
            desc=["A custom spell..."],
        )
        db_session.add_all([spell1, spell2])
        db_session.commit()

        # Query only SRD spells
        srd_spells = (
            db_session.execute(select(Spell).where(Spell.content_pack_id == "srd"))
            .scalars()
            .all()
        )
        assert len(srd_spells) == 1
        assert srd_spells[0].name == "Magic Missile"

        # Query all active content packs' spells
        active_packs = (
            db_session.execute(select(ContentPack.id).where(ContentPack.is_active))
            .scalars()
            .all()
        )
        all_spells = (
            db_session.execute(
                select(Spell).where(Spell.content_pack_id.in_(active_packs))
            )
            .scalars()
            .all()
        )
        assert len(all_spells) == 2

    def test_json_field_storage(self, db_session: Session) -> None:
        """Test that JSON fields store and retrieve correctly."""
        pack = ContentPack(
            id="srd", name="SRD", description="", version="1.0", author="WotC"
        )
        db_session.add(pack)

        # Complex JSON data
        armor_class = [
            {"type": "natural", "value": 13},
            {
                "type": "armor",
                "value": 15,
                "armor": [
                    {
                        "index": "scale-mail",
                        "name": "Scale Mail",
                        "url": "/api/equipment/scale-mail",
                    }
                ],
            },
        ]

        monster = Monster(
            index="complex-monster",
            name="Complex Monster",
            url="/api/monsters/complex-monster",
            content_pack_id="srd",
            size="Medium",
            type="monstrosity",
            armor_class=armor_class,
            hit_points=50,
            hit_dice="8d8+8",
            speed={"walk": "30 ft.", "fly": "60 ft."},
            strength=14,
            dexterity=12,
            constitution=13,
            intelligence=10,
            wisdom=11,
            charisma=10,
            proficiencies=[],
            senses={},
            languages="Common",
            challenge_rating=3,
            xp=700,
            actions=[
                {
                    "name": "Multiattack",
                    "desc": "The monster makes two attacks.",
                },
                {
                    "name": "Bite",
                    "desc": "Melee Weapon Attack: +5 to hit, reach 5 ft., one target. Hit: 10 (2d6 + 3) piercing damage.",
                    "attack_bonus": 5,
                    "damage": [
                        {
                            "damage_dice": "2d6+3",
                            "damage_type": {
                                "index": "piercing",
                                "name": "Piercing",
                                "url": "/api/damage-types/piercing",
                            },
                        }
                    ],
                },
            ],
        )
        db_session.add(monster)
        db_session.commit()

        # Retrieve and verify
        result = db_session.execute(
            select(Monster).where(Monster.index == "complex-monster")
        ).scalar_one()
        assert len(result.armor_class) == 2
        assert result.armor_class[0]["type"] == "natural"
        assert result.armor_class[1]["armor"][0]["name"] == "Scale Mail"
        assert len(result.actions) == 2
        assert result.actions[1]["attack_bonus"] == 5
