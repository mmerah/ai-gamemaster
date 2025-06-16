"""Unit tests for D5e Pydantic models."""

import pytest
from pydantic import ValidationError

from app.content.schemas import (
    DC,
    APIReference,
    Choice,
    ChoiceOption,
    Cost,
    D5eAbilityScore,
    D5eAlignment,
    D5eBackground,
    D5eClass,
    D5eCondition,
    D5eDamageType,
    D5eEquipment,
    D5eEquipmentCategory,
    D5eFeat,
    D5eFeature,
    D5eLanguage,
    D5eLevel,
    D5eMagicItem,
    D5eMagicSchool,
    D5eMonster,
    D5eProficiency,
    D5eRace,
    D5eSkill,
    D5eSpell,
    D5eSubclass,
    D5eSubrace,
    D5eTrait,
    D5eWeaponProperty,
    Damage,
    DamageAtLevel,
    MonsterAction,
    MonsterArmorClass,
    MonsterProficiency,
    MonsterSpeed,
    OptionSet,
    SpecialAbility,
    Usage,
)


class TestBaseModels:
    """Test suite for base D5e models."""

    def test_api_reference_valid(self) -> None:
        """Test creating a valid APIReference."""
        ref = APIReference(index="wizard", name="Wizard", url="/api/classes/wizard")
        assert ref.index == "wizard"
        assert ref.name == "Wizard"
        assert ref.url == "/api/classes/wizard"

    def test_api_reference_frozen(self) -> None:
        """Test that APIReference is immutable."""
        ref = APIReference(index="wizard", name="Wizard", url="/api/classes/wizard")
        with pytest.raises(ValidationError):
            ref.index = "sorcerer"  # type: ignore

    def test_api_reference_missing_field(self) -> None:
        """Test APIReference validation with missing field."""
        with pytest.raises(ValidationError) as exc_info:
            APIReference(index="wizard", name="Wizard")  # type: ignore
        assert "url" in str(exc_info.value)

    def test_cost_model(self) -> None:
        """Test Cost model."""
        cost = Cost(quantity=50, unit="gp")
        assert cost.quantity == 50
        assert cost.unit == "gp"

    def test_dc_model(self) -> None:
        """Test DC model."""
        dc = DC(
            dc_type=APIReference(
                index="str", name="STR", url="/api/ability-scores/str"
            ),
            dc_value=15,
            success_type="half",
        )
        assert dc.dc_value == 15
        assert dc.success_type == "half"

    def test_damage_model(self) -> None:
        """Test Damage model."""
        damage = Damage(
            damage_type=APIReference(
                index="fire", name="Fire", url="/api/damage-types/fire"
            ),
            damage_dice="2d6",
        )
        assert damage.damage_dice == "2d6"

    def test_damage_at_level_model(self) -> None:
        """Test DamageAtLevel model."""
        damage = DamageAtLevel(
            damage_type=APIReference(
                index="fire", name="Fire", url="/api/damage-types/fire"
            ),
            damage_at_slot_level={"3": "8d6", "4": "9d6"},
        )
        assert damage.damage_at_slot_level is not None
        assert damage.damage_at_slot_level["3"] == "8d6"

    def test_usage_model(self) -> None:
        """Test Usage model."""
        usage = Usage(type="per day", times=3, rest_types=["long"])
        assert usage.times == 3
        assert usage.rest_types is not None
        assert "long" in usage.rest_types

    def test_option_set_model(self) -> None:
        """Test OptionSet model."""
        option_set = OptionSet(
            option_set_type="equipment_category",
            equipment_category=APIReference(
                index="simple-weapons",
                name="Simple Weapons",
                url="/api/equipment-categories/simple-weapons",
            ),
        )
        assert option_set.option_set_type == "equipment_category"

    def test_choice_model(self) -> None:
        """Test Choice model."""
        choice = Choice(
            desc="Choose two skills",
            choose=2,
            type="proficiencies",
            from_=OptionSet(option_set_type="skills_list"),
        )
        assert choice.choose == 2
        assert choice.type == "proficiencies"


class TestMechanicsModels:
    """Test suite for game mechanics models."""

    def test_ability_score_model(self) -> None:
        """Test D5eAbilityScore model."""
        ability = D5eAbilityScore(
            index="str",
            name="STR",
            full_name="Strength",
            desc=["Strength measures bodily power..."],
            skills=[
                APIReference(
                    index="athletics", name="Athletics", url="/api/skills/athletics"
                )
            ],
            url="/api/ability-scores/str",
        )
        assert ability.full_name == "Strength"
        assert len(ability.skills) == 1

    def test_skill_model(self) -> None:
        """Test D5eSkill model."""
        skill = D5eSkill(
            index="acrobatics",
            name="Acrobatics",
            desc=["Your Dexterity (Acrobatics) check..."],
            ability_score=APIReference(
                index="dex", name="DEX", url="/api/ability-scores/dex"
            ),
            url="/api/skills/acrobatics",
        )
        assert skill.name == "Acrobatics"
        assert skill.ability_score.index == "dex"

    def test_proficiency_model(self) -> None:
        """Test D5eProficiency model."""
        prof = D5eProficiency(
            index="skill-persuasion",
            type="Skills",
            name="Skill: Persuasion",
            classes=[APIReference(index="bard", name="Bard", url="/api/classes/bard")],
            races=[],
            url="/api/proficiencies/skill-persuasion",
        )
        assert prof.type == "Skills"
        assert len(prof.classes) == 1

    def test_condition_model(self) -> None:
        """Test D5eCondition model."""
        condition = D5eCondition(
            index="blinded",
            name="Blinded",
            desc=["A blinded creature can't see..."],
            url="/api/conditions/blinded",
        )
        assert condition.name == "Blinded"

    def test_damage_type_model(self) -> None:
        """Test D5eDamageType model."""
        damage_type = D5eDamageType(
            index="acid",
            name="Acid",
            desc=["The corrosive spray of a black dragon's breath..."],
            url="/api/damage-types/acid",
        )
        assert damage_type.name == "Acid"

    def test_language_model(self) -> None:
        """Test D5eLanguage model."""
        language = D5eLanguage(
            index="common",
            name="Common",
            type="Standard",
            typical_speakers=["Humans"],
            script="Common",
            url="/api/languages/common",
        )
        assert language.type == "Standard"
        assert "Humans" in language.typical_speakers

    def test_alignment_model(self) -> None:
        """Test D5eAlignment model."""
        alignment = D5eAlignment(
            index="lawful-good",
            name="Lawful Good",
            abbreviation="LG",
            desc="Lawful good creatures can be counted on...",
            url="/api/alignments/lawful-good",
        )
        assert alignment.abbreviation == "LG"


class TestCharacterModels:
    """Test suite for character option models."""

    def test_class_model_minimal(self) -> None:
        """Test D5eClass model with minimal data."""
        cls = D5eClass(
            index="fighter",
            name="Fighter",
            hit_die=10,
            class_levels="/api/classes/fighter/levels",
            url="/api/classes/fighter",
        )
        assert cls.hit_die == 10
        assert cls.name == "Fighter"

    def test_class_model_full(self) -> None:
        """Test D5eClass model with full data."""
        cls = D5eClass(
            index="wizard",
            name="Wizard",
            hit_die=6,
            proficiency_choices=[
                Choice(desc="Choose two skills", choose=2, type="proficiencies")
            ],
            proficiencies=[
                APIReference(
                    index="daggers", name="Daggers", url="/api/proficiencies/daggers"
                )
            ],
            saving_throws=[
                APIReference(index="int", name="INT", url="/api/ability-scores/int"),
                APIReference(index="wis", name="WIS", url="/api/ability-scores/wis"),
            ],
            class_levels="/api/classes/wizard/levels",
            url="/api/classes/wizard",
            spells="/api/classes/wizard/spells",
        )
        assert len(cls.saving_throws) == 2
        assert cls.spells == "/api/classes/wizard/spells"

    def test_subclass_model(self) -> None:
        """Test D5eSubclass model."""
        subclass = D5eSubclass(
            index="champion",
            **{
                "class": APIReference(
                    index="fighter", name="Fighter", url="/api/classes/fighter"
                )
            },
            name="Champion",
            subclass_flavor="Martial Archetype",
            desc=["The archetypal Champion focuses on..."],
            subclass_levels="/api/subclasses/champion/levels",
            url="/api/subclasses/champion",
        )
        assert subclass.subclass_flavor == "Martial Archetype"

    def test_race_model(self) -> None:
        """Test D5eRace model."""
        race = D5eRace(
            index="elf",
            name="Elf",
            speed=30,
            ability_bonuses=[],
            alignment="Elves love freedom...",
            age="Although elves reach physical maturity...",
            size="Medium",
            size_description="Elves range from under 5 to over 6 feet tall...",
            languages=[
                APIReference(
                    index="common", name="Common", url="/api/languages/common"
                ),
                APIReference(
                    index="elvish", name="Elvish", url="/api/languages/elvish"
                ),
            ],
            language_desc="You can speak, read, and write Common and Elvish.",
            url="/api/races/elf",
        )
        assert race.speed == 30
        assert len(race.languages) == 2

    def test_background_model(self) -> None:
        """Test D5eBackground model."""
        from app.content.schemas.character import Feature

        background = D5eBackground(
            index="acolyte",
            name="Acolyte",
            starting_proficiencies=[],
            starting_equipment=[],
            starting_equipment_options=[],
            feature=Feature(
                name="Shelter of the Faithful", desc=["As an acolyte, you command..."]
            ),
            personality_traits=Choice(
                choose=2,
                type="personality_traits",
                **{
                    "from": {
                        "option_set_type": "options_array",
                        "options": [
                            {
                                "option_type": "string",
                                "string": "I idolize a particular hero...",
                            }
                        ],
                    }
                },
            ),
            ideals=Choice(
                choose=1,
                type="ideals",
                **{
                    "from": {
                        "option_set_type": "options_array",
                        "options": [
                            {
                                "option_type": "ideal",
                                "desc": "Tradition. The ancient traditions...",
                                "alignments": [],
                            }
                        ],
                    }
                },
            ),
            bonds=Choice(
                choose=1,
                type="bonds",
                **{
                    "from": {
                        "option_set_type": "options_array",
                        "options": [
                            {
                                "option_type": "string",
                                "string": "I would die to recover...",
                            }
                        ],
                    }
                },
            ),
            flaws=Choice(
                choose=1,
                type="flaws",
                **{
                    "from": {
                        "option_set_type": "options_array",
                        "options": [
                            {
                                "option_type": "string",
                                "string": "I judge others harshly...",
                            }
                        ],
                    }
                },
            ),
            url="/api/backgrounds/acolyte",
        )
        assert background.name == "Acolyte"
        assert background.feature.name == "Shelter of the Faithful"

    def test_feat_model(self) -> None:
        """Test D5eFeat model."""
        feat = D5eFeat(
            index="grappler",
            name="Grappler",
            prerequisites=[
                {"type": "ability_score", "ability_score": "str", "minimum": 13}
            ],
            desc=["You've developed the skills necessary..."],
            url="/api/feats/grappler",
        )
        assert feat.name == "Grappler"
        assert len(feat.prerequisites) == 1

    def test_trait_model(self) -> None:
        """Test D5eTrait model."""
        trait = D5eTrait(
            index="darkvision",
            races=[APIReference(index="elf", name="Elf", url="/api/races/elf")],
            subraces=[],
            name="Darkvision",
            desc=["You can see in dim light..."],
            url="/api/traits/darkvision",
        )
        assert trait.name == "Darkvision"
        assert len(trait.races) == 1


class TestProgressionModels:
    """Test suite for character progression models."""

    def test_feature_model(self) -> None:
        """Test D5eFeature model."""
        feature = D5eFeature(
            index="fighter-fighting-style",
            name="Fighting Style",
            level=1,
            **{
                "class": APIReference(
                    index="fighter", name="Fighter", url="/api/classes/fighter"
                )
            },
            desc=["You adopt a particular style..."],
            url="/api/features/fighter-fighting-style",
        )
        assert feature.level == 1
        assert feature.name == "Fighting Style"

    def test_level_model(self) -> None:
        """Test D5eLevel model."""
        level = D5eLevel(
            level=3,
            ability_score_bonuses=0,
            prof_bonus=2,
            features=[
                APIReference(
                    index="fighter-archetype",
                    name="Martial Archetype",
                    url="/api/features/fighter-archetype",
                )
            ],
            class_specific={"action_surges": 1, "indomitable_uses": 0},
            index="fighter-3",
            **{
                "class": APIReference(
                    index="fighter", name="Fighter", url="/api/classes/fighter"
                )
            },
            url="/api/classes/fighter/levels/3",
        )
        assert level.level == 3
        assert level.prof_bonus == 2


class TestEquipmentModels:
    """Test suite for equipment models."""

    def test_equipment_weapon(self) -> None:
        """Test D5eEquipment model for a weapon."""
        weapon = D5eEquipment(
            index="longsword",
            name="Longsword",
            equipment_category=APIReference(
                index="weapon", name="Weapon", url="/api/equipment-categories/weapon"
            ),
            cost=Cost(quantity=15, unit="gp"),
            weight=3,
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
        assert weapon.weapon_category == "Martial"
        assert weapon.damage.damage_dice == "1d8"  # type: ignore

    def test_equipment_armor(self) -> None:
        """Test D5eEquipment model for armor."""
        from app.content.schemas.equipment import ArmorClass

        armor = D5eEquipment(
            index="chain-mail",
            name="Chain Mail",
            equipment_category=APIReference(
                index="armor", name="Armor", url="/api/equipment-categories/armor"
            ),
            cost=Cost(quantity=75, unit="gp"),
            weight=55,
            armor_category="Heavy",
            armor_class=ArmorClass(base=16, dex_bonus=False),
            str_minimum=13,
            stealth_disadvantage=True,
            url="/api/equipment/chain-mail",
        )
        assert armor.armor_category == "Heavy"
        assert armor.armor_class.base == 16  # type: ignore

    def test_magic_item_model(self) -> None:
        """Test D5eMagicItem model."""
        item = D5eMagicItem(
            index="bag-of-holding",
            name="Bag of Holding",
            equipment_category=APIReference(
                index="wondrous-item",
                name="Wondrous Item",
                url="/api/equipment-categories/wondrous-item",
            ),
            desc=["This bag has an interior space..."],
            rarity={"name": "Uncommon"},
            variant=False,
            url="/api/magic-items/bag-of-holding",
        )
        assert item.rarity["name"] == "Uncommon"

    def test_weapon_property_model(self) -> None:
        """Test D5eWeaponProperty model."""
        prop = D5eWeaponProperty(
            index="finesse",
            name="Finesse",
            desc=["When making an attack with a finesse weapon..."],
            url="/api/weapon-properties/finesse",
        )
        assert prop.name == "Finesse"

    def test_magic_school_model(self) -> None:
        """Test D5eMagicSchool model."""
        school = D5eMagicSchool(
            index="evocation",
            name="Evocation",
            desc="Evocation spells manipulate magical energy...",
            url="/api/magic-schools/evocation",
        )
        assert school.name == "Evocation"


class TestSpellsAndMonsters:
    """Test suite for spell and monster models."""

    def test_spell_model(self) -> None:
        """Test D5eSpell model."""
        spell = D5eSpell(
            index="fireball",
            name="Fireball",
            desc=["A bright streak flashes..."],
            range="150 feet",
            components=["V", "S", "M"],
            material="A tiny ball of bat guano and sulfur",
            ritual=False,
            duration="Instantaneous",
            concentration=False,
            casting_time="1 action",
            level=3,
            damage=DamageAtLevel(
                damage_type=APIReference(
                    index="fire", name="Fire", url="/api/damage-types/fire"
                ),
                damage_at_slot_level={"3": "8d6", "4": "9d6"},
            ),
            dc=DC(
                dc_type=APIReference(
                    index="dex", name="DEX", url="/api/ability-scores/dex"
                ),
                success_type="half",
            ),
            school=APIReference(
                index="evocation", name="Evocation", url="/api/magic-schools/evocation"
            ),
            classes=[
                APIReference(index="wizard", name="Wizard", url="/api/classes/wizard")
            ],
            url="/api/spells/fireball",
        )
        assert spell.level == 3
        assert spell.damage.damage_at_slot_level["3"] == "8d6"  # type: ignore

    def test_monster_model(self) -> None:
        """Test D5eMonster model."""
        monster = D5eMonster(
            index="goblin",
            name="Goblin",
            size="Small",
            type="humanoid",
            subtype="goblinoid",
            alignment="neutral evil",
            armor_class=[MonsterArmorClass(type="armor", value=15)],
            hit_points=7,
            hit_dice="2d6",
            hit_points_roll="2d6",
            speed=MonsterSpeed(walk="30 ft."),
            strength=8,
            dexterity=14,
            constitution=10,
            intelligence=10,
            wisdom=8,
            charisma=8,
            proficiencies=[
                MonsterProficiency(
                    value=4,
                    proficiency=APIReference(
                        index="skill-stealth",
                        name="Skill: Stealth",
                        url="/api/proficiencies/skill-stealth",
                    ),
                )
            ],
            senses={"darkvision": "60 ft.", "passive_perception": 9},
            languages="Common, Goblin",
            challenge_rating=0.25,
            proficiency_bonus=2,
            xp=50,
            special_abilities=[
                SpecialAbility(
                    name="Nimble Escape", desc="The goblin can take the Disengage..."
                )
            ],
            actions=[
                MonsterAction(
                    name="Scimitar",
                    desc="Melee Weapon Attack: +4 to hit...",
                    attack_bonus=4,
                    damage=[
                        Damage(
                            damage_dice="1d6+2",
                            damage_type=APIReference(
                                index="slashing",
                                name="Slashing",
                                url="/api/damage-types/slashing",
                            ),
                        )
                    ],
                )
            ],
            url="/api/monsters/goblin",
        )
        assert monster.challenge_rating == 0.25
        assert monster.hit_points == 7
        assert len(monster.actions) == 1  # type: ignore

    def test_monster_speed_model(self) -> None:
        """Test MonsterSpeed model."""
        speed = MonsterSpeed(walk="30 ft.", fly="60 ft.", hover=True)
        assert speed.walk == "30 ft."
        assert speed.hover is True

    def test_special_ability_model(self) -> None:
        """Test SpecialAbility model."""
        ability = SpecialAbility(
            name="Pack Tactics",
            desc="The creature has advantage on attack rolls...",
            usage=Usage(type="per turn", times=1),
        )
        assert ability.name == "Pack Tactics"


class TestModelValidation:
    """Test model validation edge cases."""

    def test_empty_lists_default(self) -> None:
        """Test that empty lists are properly defaulted."""
        skill = D5eSkill(
            index="test",
            name="Test",
            desc=[],  # Empty list should be valid
            ability_score=APIReference(
                index="str", name="STR", url="/api/ability-scores/str"
            ),
            url="/api/skills/test",
        )
        assert skill.desc == []

    def test_optional_fields(self) -> None:
        """Test models with optional fields."""
        spell = D5eSpell(
            index="light",
            name="Light",
            desc=["You touch one object..."],
            range="Touch",
            components=["V", "M"],
            material="A firefly or phosphorescent moss",
            ritual=False,
            duration="1 hour",
            concentration=False,
            casting_time="1 action",
            level=0,
            school=APIReference(
                index="evocation", name="Evocation", url="/api/magic-schools/evocation"
            ),
            url="/api/spells/light",
            # No damage, dc, or higher_level - all optional
        )
        assert spell.damage is None
        assert spell.dc is None
        assert spell.higher_level is None

    def test_field_alias(self) -> None:
        """Test models with field aliases."""
        # Test 'from_' alias for 'from' field
        choice_data = {
            "desc": "Choose two",
            "choose": 2,
            "type": "skills",
            "from": {"option_set_type": "skills"},
        }
        choice = Choice(**choice_data)
        assert choice.from_ is not None
        assert choice.from_.option_set_type == "skills"

        # Test 'class_' alias for 'class' field
        subclass_data = {
            "index": "champion",
            "class": {
                "index": "fighter",
                "name": "Fighter",
                "url": "/api/classes/fighter",
            },
            "name": "Champion",
            "subclass_flavor": "Martial Archetype",
            "desc": ["The archetypal Champion..."],
            "subclass_levels": "/api/subclasses/champion/levels",
            "url": "/api/subclasses/champion",
        }
        subclass = D5eSubclass(**subclass_data)
        assert subclass.class_ is not None
        assert subclass.class_.index == "fighter"
