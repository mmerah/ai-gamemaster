"""Tests for D5e document converters."""

import pytest
from langchain_core.documents import Document

from app.models.d5e.base import APIReference, Cost, Damage
from app.models.d5e.character import (
    AbilityBonus,
    D5eBackground,
    D5eClass,
    D5eFeat,
    D5eRace,
    D5eSubclass,
    D5eTrait,
)
from app.models.d5e.equipment import (
    D5eEquipment,
    D5eEquipmentCategory,
    D5eMagicItem,
    D5eMagicSchool,
)
from app.models.d5e.mechanics import (
    D5eAbilityScore,
    D5eAlignment,
    D5eCondition,
    D5eDamageType,
    D5eLanguage,
    D5eProficiency,
    D5eSkill,
)
from app.models.d5e.progression import D5eFeature
from app.models.d5e.spells_monsters import (
    D5eMonster,
    D5eSpell,
    MonsterAction,
    MonsterProficiency,
    MonsterSpeed,
    SpecialAbility,
)
from app.rag.d5e_document_converters import D5eDocumentConverters


class TestD5eDocumentConverters:
    """Test D5e document converter functionality."""

    def test_ability_score_to_document(self) -> None:
        """Test converting ability score to document."""
        ability = D5eAbilityScore(
            index="str",
            name="STR",
            full_name="Strength",
            desc=["Strength measures bodily power"],
            skills=[
                APIReference(
                    index="athletics", name="Athletics", url="/api/skills/athletics"
                )
            ],
            url="/api/ability-scores/str",
        )

        doc = D5eDocumentConverters.ability_score_to_document(ability)

        assert isinstance(doc, Document)
        assert "STR (Strength)" in doc.page_content
        assert "Strength measures bodily power" in doc.page_content
        assert "Athletics" in doc.page_content
        assert doc.metadata["source"] == "d5e-ability-scores"
        assert doc.metadata["index"] == "str"
        assert doc.metadata["type"] == "ability_score"

    def test_skill_to_document(self) -> None:
        """Test converting skill to document."""
        skill = D5eSkill(
            index="acrobatics",
            name="Acrobatics",
            desc=["Your Dexterity (Acrobatics) check"],
            ability_score=APIReference(
                index="dex", name="DEX", url="/api/ability-scores/dex"
            ),
            url="/api/skills/acrobatics",
        )

        doc = D5eDocumentConverters.skill_to_document(skill)

        assert "Acrobatics" in doc.page_content
        assert "Ability Score: DEX" in doc.page_content
        assert "Your Dexterity (Acrobatics) check" in doc.page_content
        assert doc.metadata["ability_score"] == "dex"

    def test_class_to_document(self) -> None:
        """Test converting class to document."""
        cls = D5eClass(
            index="fighter",
            name="Fighter",
            hit_die=10,
            proficiency_choices=[],
            proficiencies=[
                APIReference(
                    index="shields", name="Shields", url="/api/proficiencies/shields"
                ),
                APIReference(
                    index="simple-weapons",
                    name="Simple Weapons",
                    url="/api/proficiencies/simple-weapons",
                ),
            ],
            saving_throws=[
                APIReference(index="str", name="STR", url="/api/ability-scores/str"),
                APIReference(index="con", name="CON", url="/api/ability-scores/con"),
            ],
            starting_equipment=[],
            starting_equipment_options=[],
            class_levels="/api/classes/fighter/levels",
            subclasses=[
                APIReference(
                    index="champion", name="Champion", url="/api/subclasses/champion"
                )
            ],
            url="/api/classes/fighter",
        )

        doc = D5eDocumentConverters.class_to_document(cls)

        assert "Fighter" in doc.page_content
        assert "Hit Die: d10" in doc.page_content
        assert "STR, CON" in doc.page_content
        assert "Shields, Simple Weapons" in doc.page_content
        assert "Champion" in doc.page_content
        assert doc.metadata["hit_die"] == 10
        assert doc.metadata["has_spellcasting"] is False

    def test_spell_to_document(self) -> None:
        """Test converting spell to document."""
        spell = D5eSpell(
            index="fireball",
            name="Fireball",
            level=3,
            school=APIReference(
                index="evocation", name="Evocation", url="/api/magic-schools/evocation"
            ),
            casting_time="1 action",
            range="150 feet",
            components=["V", "S", "M"],
            material="A tiny ball of bat guano and sulfur",
            duration="Instantaneous",
            concentration=False,
            ritual=False,
            desc=["A bright streak flashes from your pointing finger"],
            higher_level=[
                "When you cast this spell using a spell slot of 4th level or higher"
            ],
            classes=[
                APIReference(
                    index="sorcerer", name="Sorcerer", url="/api/classes/sorcerer"
                ),
                APIReference(index="wizard", name="Wizard", url="/api/classes/wizard"),
            ],
            subclasses=[],
            url="/api/spells/fireball",
        )

        doc = D5eDocumentConverters.spell_to_document(spell)

        assert "Fireball" in doc.page_content
        assert "Level 3 Evocation" in doc.page_content
        assert "Casting Time: 1 action" in doc.page_content
        assert "Range: 150 feet" in doc.page_content
        assert "V, S, M" in doc.page_content
        assert "bat guano and sulfur" in doc.page_content
        assert "A bright streak flashes" in doc.page_content
        assert "Sorcerer, Wizard" in doc.page_content
        assert doc.metadata["level"] == 3
        assert doc.metadata["school"] == "evocation"
        assert doc.metadata["concentration"] is False

    def test_monster_to_document(self) -> None:
        """Test converting monster to document."""
        monster = D5eMonster(
            index="goblin",
            name="Goblin",
            size="Small",
            type="humanoid (goblinoid)",
            alignment="neutral evil",
            armor_class=[{"type": "natural", "value": 15}],
            hit_points=7,
            hit_points_roll="2d6",
            hit_dice="2d6",
            speed=MonsterSpeed(walk="30 ft."),
            strength=8,
            dexterity=14,
            constitution=10,
            intelligence=10,
            wisdom=8,
            charisma=8,
            proficiencies=[
                MonsterProficiency(
                    proficiency=APIReference(
                        index="skill-stealth",
                        name="Stealth",
                        url="/api/proficiencies/skill-stealth",
                    ),
                    value=6,
                )
            ],
            damage_vulnerabilities=[],
            damage_resistances=[],
            damage_immunities=[],
            condition_immunities=[],
            senses={"darkvision": "60 ft.", "passive_perception": "9"},
            languages="Common, Goblin",
            challenge_rating=0.25,
            xp=50,
            proficiency_bonus=2,
            actions=[
                MonsterAction(
                    name="Scimitar",
                    desc="Melee Weapon Attack: +4 to hit, reach 5 ft., one target. Hit: 5 (1d6 + 2) slashing damage.",
                )
            ],
            special_abilities=[
                SpecialAbility(
                    name="Nimble Escape",
                    desc="The goblin can take the Disengage or Hide action as a bonus action on each of its turns.",
                )
            ],
            url="/api/monsters/goblin",
        )

        doc = D5eDocumentConverters.monster_to_document(monster)

        assert "Goblin" in doc.page_content
        assert "Small humanoid (goblinoid), neutral evil" in doc.page_content
        assert "Armor Class: 15" in doc.page_content
        assert "Hit Points: 7 (2d6)" in doc.page_content
        assert "STR: 8" in doc.page_content
        assert "Skills: Stealth +6" in doc.page_content
        assert "darkvision 60 ft." in doc.page_content
        assert "Challenge Rating: 0.25" in doc.page_content
        assert "Nimble Escape" in doc.page_content
        assert "Scimitar" in doc.page_content
        assert doc.metadata["challenge_rating"] == 0.25
        assert doc.metadata["is_legendary"] is False

    def test_equipment_to_document(self) -> None:
        """Test converting equipment to document."""
        equipment = D5eEquipment(
            index="longsword",
            name="Longsword",
            equipment_category=APIReference(
                index="weapon", name="Weapon", url="/api/equipment-categories/weapon"
            ),
            cost=Cost(quantity=15, unit="gp"),
            weight=3.0,
            weapon_category="Martial",
            weapon_range="Melee",
            damage=Damage(
                damage_dice="1d8",
                damage_type=APIReference(
                    index="slashing", name="Slashing", url="/api/damage-types/slashing"
                ),
            ),
            properties=[
                APIReference(
                    index="versatile",
                    name="Versatile",
                    url="/api/weapon-properties/versatile",
                )
            ],
            url="/api/equipment/longsword",
        )

        doc = D5eDocumentConverters.equipment_to_document(equipment)

        assert "Longsword" in doc.page_content
        assert "Category: Weapon" in doc.page_content
        assert "Cost: 15 gp" in doc.page_content
        assert "Weight: 3.0 lbs" in doc.page_content
        assert "Weapon Type: Martial Melee" in doc.page_content
        assert "Damage: 1d8 Slashing" in doc.page_content
        assert "Properties: Versatile" in doc.page_content
        assert doc.metadata["cost_gp"] == 15

    def test_magic_item_to_document(self) -> None:
        """Test converting magic item to document."""
        magic_item = D5eMagicItem(
            index="potion-of-healing",
            name="Potion of Healing",
            equipment_category=APIReference(
                index="potion", name="Potion", url="/api/equipment-categories/potion"
            ),
            desc=["You regain 2d4 + 2 hit points when you drink this potion."],
            rarity={"name": "Common"},
            variant=False,
            variants=None,
            url="/api/magic-items/potion-of-healing",
        )

        doc = D5eDocumentConverters.magic_item_to_document(magic_item)

        assert "Potion of Healing" in doc.page_content
        assert "Category: Potion" in doc.page_content
        assert "Rarity: Common" in doc.page_content
        assert "You regain 2d4 + 2 hit points" in doc.page_content
        assert doc.metadata["rarity"] == "Common"
        assert doc.metadata["variant"] is False

    def test_race_to_document(self) -> None:
        """Test converting race to document."""
        race = D5eRace(
            index="dwarf",
            name="Dwarf",
            speed=25,
            ability_bonuses=[
                AbilityBonus(
                    ability_score=APIReference(
                        index="con", name="CON", url="/api/ability-scores/con"
                    ),
                    bonus=2,
                )
            ],
            alignment="Most dwarves are lawful",
            age="Dwarves mature at the same rate as humans",
            size="Medium",
            size_description="Dwarves stand between 4 and 5 feet tall",
            starting_proficiencies=[
                APIReference(
                    index="battleaxes",
                    name="Battleaxes",
                    url="/api/proficiencies/battleaxes",
                )
            ],
            languages=[
                APIReference(
                    index="common", name="Common", url="/api/languages/common"
                ),
                APIReference(
                    index="dwarvish", name="Dwarvish", url="/api/languages/dwarvish"
                ),
            ],
            language_desc="",
            traits=[
                APIReference(
                    index="darkvision", name="Darkvision", url="/api/traits/darkvision"
                ),
                APIReference(
                    index="dwarven-resilience",
                    name="Dwarven Resilience",
                    url="/api/traits/dwarven-resilience",
                ),
            ],
            subraces=[
                APIReference(
                    index="hill-dwarf",
                    name="Hill Dwarf",
                    url="/api/subraces/hill-dwarf",
                )
            ],
            url="/api/races/dwarf",
        )

        doc = D5eDocumentConverters.race_to_document(race)

        assert "Dwarf" in doc.page_content
        assert "Size: Medium" in doc.page_content
        assert "Speed: 25 feet" in doc.page_content
        assert "CON: +2" in doc.page_content
        assert "Languages: Common, Dwarvish" in doc.page_content
        assert "Darkvision, Dwarven Resilience" in doc.page_content
        assert "Hill Dwarf" in doc.page_content
        assert doc.metadata["speed"] == 25

    def test_get_converter_for_category(self) -> None:
        """Test getting converter for different categories."""
        # Test valid categories (only dict-based converters)
        assert D5eDocumentConverters.get_converter_for_category("rules") is not None
        assert (
            D5eDocumentConverters.get_converter_for_category("rule-sections")
            is not None
        )
        assert (
            D5eDocumentConverters.get_converter_for_category("weapon-properties")
            is not None
        )

        # Test invalid category
        assert D5eDocumentConverters.get_converter_for_category("invalid") is None

        # Categories with dedicated typed converters should return None
        assert D5eDocumentConverters.get_converter_for_category("spells") is None
        assert D5eDocumentConverters.get_converter_for_category("monsters") is None

    def test_format_reference_list(self) -> None:
        """Test formatting reference lists."""
        refs = [
            APIReference(
                index="athletics", name="Athletics", url="/api/skills/athletics"
            ),
            APIReference(
                index="acrobatics", name="Acrobatics", url="/api/skills/acrobatics"
            ),
        ]

        result = D5eDocumentConverters._format_reference_list(refs)
        assert result == "Athletics, Acrobatics"

        # Test empty list
        assert D5eDocumentConverters._format_reference_list([]) == "None"
