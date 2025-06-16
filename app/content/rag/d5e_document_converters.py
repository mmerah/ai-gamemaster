"""D5e Document Converters for RAG System.

This module provides converters that transform D5e entities into rich,
searchable documents for the RAG system's vector stores.
"""

from typing import Any, Callable, Dict, List, Optional, Union

from langchain_core.documents import Document

# Type alias for converter functions that take dict input
DictConverterFunc = Callable[[Dict[str, Any]], Document]

from app.content.schemas.base import APIReference
from app.content.schemas.character import (
    D5eBackground,
    D5eClass,
    D5eFeat,
    D5eRace,
    D5eSubclass,
    D5eSubrace,
    D5eTrait,
)
from app.content.schemas.equipment import (
    D5eEquipment,
    D5eEquipmentCategory,
    D5eMagicItem,
    D5eMagicSchool,
    D5eWeaponProperty,
)
from app.content.schemas.mechanics import (
    D5eAbilityScore,
    D5eAlignment,
    D5eCondition,
    D5eDamageType,
    D5eLanguage,
    D5eProficiency,
    D5eSkill,
)
from app.content.schemas.progression import D5eFeature, D5eLevel
from app.content.schemas.spells_monsters import D5eMonster, D5eSpell


class D5eDocumentConverters:
    """Converts D5e entities to searchable documents for RAG system."""

    @staticmethod
    def _format_reference_list(references: List[APIReference]) -> str:
        """Format a list of API references as comma-separated names."""
        if not references:
            return "None"
        return ", ".join(ref.name for ref in references)

    @staticmethod
    def _format_dict_list(items: List[Dict[str, Any]], key: str = "name") -> str:
        """Format a list of dicts as comma-separated values."""
        if not items:
            return "None"
        return ", ".join(str(item.get(key, "Unknown")) for item in items)

    @staticmethod
    def ability_score_to_document(ability: D5eAbilityScore) -> Document:
        """Convert ability score to document."""
        content = f"{ability.name} ({ability.full_name})\n\n"
        content += f"Description:\n{' '.join(ability.desc)}\n\n"
        content += (
            f"Skills: {D5eDocumentConverters._format_reference_list(ability.skills)}"
        )

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-ability-scores",
                "index": ability.index,
                "name": ability.name,
                "type": "ability_score",
            },
        )

    @staticmethod
    def skill_to_document(skill: D5eSkill) -> Document:
        """Convert skill to document."""
        content = f"{skill.name}\n\n"
        content += f"Ability Score: {skill.ability_score.name}\n"
        content += f"Description:\n{' '.join(skill.desc)}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-skills",
                "index": skill.index,
                "name": skill.name,
                "ability_score": skill.ability_score.index,
                "type": "skill",
            },
        )

    @staticmethod
    def proficiency_to_document(prof: D5eProficiency) -> Document:
        """Convert proficiency to document."""
        content = f"{prof.name} Proficiency\n\n"
        content += f"Type: {prof.type}\n"
        content += (
            f"Classes: {D5eDocumentConverters._format_reference_list(prof.classes)}\n"
        )
        content += f"Races: {D5eDocumentConverters._format_reference_list(prof.races)}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-proficiencies",
                "index": prof.index,
                "name": prof.name,
                "proficiency_type": prof.type,
                "type": "proficiency",
            },
        )

    @staticmethod
    def condition_to_document(condition: D5eCondition) -> Document:
        """Convert condition to document."""
        content = f"{condition.name}\n\n"
        content += f"Effects:\n{' '.join(condition.desc)}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-conditions",
                "index": condition.index,
                "name": condition.name,
                "type": "condition",
            },
        )

    @staticmethod
    def damage_type_to_document(damage: D5eDamageType) -> Document:
        """Convert damage type to document."""
        content = f"{damage.name} Damage\n\n"
        content += f"Description:\n{' '.join(damage.desc)}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-damage-types",
                "index": damage.index,
                "name": damage.name,
                "type": "damage_type",
            },
        )

    @staticmethod
    def language_to_document(language: D5eLanguage) -> Document:
        """Convert language to document."""
        content = f"{language.name}\n\n"
        content += f"Type: {language.type}\n"
        content += f"Typical Speakers: {', '.join(language.typical_speakers)}\n"
        if language.script:
            content += f"Script: {language.script}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-languages",
                "index": language.index,
                "name": language.name,
                "language_type": language.type,
                "type": "language",
            },
        )

    @staticmethod
    def alignment_to_document(alignment: D5eAlignment) -> Document:
        """Convert alignment to document."""
        content = f"{alignment.name} ({alignment.abbreviation})\n\n"
        content += f"Description: {alignment.desc}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-alignments",
                "index": alignment.index,
                "name": alignment.name,
                "abbreviation": alignment.abbreviation,
                "type": "alignment",
            },
        )

    @staticmethod
    def class_to_document(cls: D5eClass) -> Document:
        """Convert class to document with comprehensive information."""
        content = f"{cls.name}\n\n"
        content += f"Hit Die: d{cls.hit_die}\n"
        content += f"Primary Ability: {cls.primary_ability if hasattr(cls, 'primary_ability') else 'Various'}\n"
        content += f"Saving Throw Proficiencies: {D5eDocumentConverters._format_reference_list(cls.saving_throws)}\n\n"

        content += "Starting Proficiencies:\n"
        content += (
            f"- {D5eDocumentConverters._format_reference_list(cls.proficiencies)}\n\n"
        )

        if cls.proficiency_choices:
            content += "Proficiency Choices:\n"
            for choice in cls.proficiency_choices:
                if (
                    choice.from_
                    and hasattr(choice.from_, "options")
                    and choice.from_.options
                ):
                    # Convert options to APIReference if they have the right structure
                    api_refs = []
                    for opt in choice.from_.options:
                        if isinstance(opt, dict) and "name" in opt:
                            api_refs.append(APIReference(**opt))
                        elif hasattr(opt, "name"):
                            api_refs.append(opt)
                    formatted_options = (
                        D5eDocumentConverters._format_reference_list(api_refs)
                        if api_refs
                        else "various options"
                    )
                else:
                    formatted_options = "various options"
                content += f"- Choose {choice.choose} from: {formatted_options}\n"
            content += "\n"

        if hasattr(cls, "spellcasting") and cls.spellcasting:
            content += f"Spellcasting: Yes (Level {cls.spellcasting.level})\n"
            content += f"Spellcasting Ability: {cls.spellcasting.spellcasting_ability.name}\n\n"

        content += f"Subclasses: {D5eDocumentConverters._format_reference_list(cls.subclasses)}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-classes",
                "index": cls.index,
                "name": cls.name,
                "hit_die": cls.hit_die,
                "has_spellcasting": bool(
                    hasattr(cls, "spellcasting") and cls.spellcasting
                ),
                "type": "class",
            },
        )

    @staticmethod
    def subclass_to_document(subclass: D5eSubclass) -> Document:
        """Convert subclass to document."""
        class_name = subclass.class_.name if subclass.class_ else "Unknown Class"
        content = f"{subclass.name} ({class_name})\n\n"
        content += f"Subclass Type: {subclass.subclass_flavor}\n\n"
        content += f"Description:\n{' '.join(subclass.desc)}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-subclasses",
                "index": subclass.index,
                "name": subclass.name,
                "class": subclass.class_.index if subclass.class_ else "",
                "type": "subclass",
            },
        )

    @staticmethod
    def race_to_document(race: Union[D5eRace, D5eSubrace]) -> Document:
        """Convert race to document."""
        content = f"{race.name}\n\n"

        # Handle fields that are only in D5eRace
        if isinstance(race, D5eRace):
            content += f"Size: {race.size} ({race.size_description})\n"
            content += f"Speed: {race.speed} feet\n"
            content += f"Age: {race.age}\n"
            content += f"Alignment: {race.alignment}\n\n"
        else:  # D5eSubrace
            content += f"Subrace of: {race.race.name}\n"
            content += f"Description: {race.desc}\n\n"

        if race.ability_bonuses:
            content += "Ability Score Increases:\n"
            for bonus in race.ability_bonuses:
                content += f"- {bonus.ability_score.name}: +{bonus.bonus}\n"
            content += "\n"

        content += f"Languages: {D5eDocumentConverters._format_reference_list(race.languages)}\n"
        if hasattr(race, "language_desc") and race.language_desc:
            content += f"Language Options: {race.language_desc}\n"

        # Handle traits (D5eRace) vs racial_traits (D5eSubrace)
        if isinstance(race, D5eRace):
            content += f"\nRacial Traits: {D5eDocumentConverters._format_reference_list(race.traits)}\n"
        else:  # D5eSubrace
            content += f"\nRacial Traits: {D5eDocumentConverters._format_reference_list(race.racial_traits)}\n"

        if race.starting_proficiencies:
            content += f"Starting Proficiencies: {D5eDocumentConverters._format_reference_list(race.starting_proficiencies)}\n"

        if isinstance(race, D5eRace) and race.subraces:
            content += f"Subraces: {D5eDocumentConverters._format_reference_list(race.subraces)}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-races" if isinstance(race, D5eRace) else "d5e-subraces",
                "index": race.index,
                "name": race.name,
                "size": race.size if isinstance(race, D5eRace) else "Varies",
                "speed": race.speed if isinstance(race, D5eRace) else 0,
                "type": "race" if isinstance(race, D5eRace) else "subrace",
            },
        )

    @staticmethod
    def background_to_document(background: D5eBackground) -> Document:
        """Convert background to document."""
        content = f"{background.name}\n\n"

        if background.starting_proficiencies:
            content += f"Skill Proficiencies: {D5eDocumentConverters._format_reference_list(background.starting_proficiencies)}\n"

        # Backgrounds have language_options, not direct languages
        if background.language_options:
            lang_count = background.language_options.choose
            content += f"Languages: Choose {lang_count} language(s)\n"

        if background.starting_equipment:
            content += "Starting Equipment:\n"
            for equip in background.starting_equipment:
                content += f"- {equip.equipment.name} x{equip.quantity}\n"
            content += "\n"

        if background.feature:
            content += f"Feature: {background.feature.name}\n"
            content += f"{' '.join(background.feature.desc)}\n"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-backgrounds",
                "index": background.index,
                "name": background.name,
                "type": "background",
            },
        )

    @staticmethod
    def feat_to_document(feat: D5eFeat) -> Document:
        """Convert feat to document."""
        content = f"{feat.name}\n\n"

        if feat.prerequisites:
            prereq_strs = [
                str(prereq) for prereq in feat.prerequisites if isinstance(prereq, dict)
            ]
            if prereq_strs:
                content += f"Prerequisites: {', '.join(prereq_strs)}\n\n"

        content += f"Description:\n{' '.join(feat.desc)}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-feats",
                "index": feat.index,
                "name": feat.name,
                "has_prerequisite": bool(feat.prerequisites),
                "type": "feat",
            },
        )

    @staticmethod
    def trait_to_document(trait: D5eTrait) -> Document:
        """Convert trait to document."""
        content = f"{trait.name}\n\n"
        content += f"Description:\n{' '.join(trait.desc)}\n\n"

        if trait.races:
            content += (
                f"Races: {D5eDocumentConverters._format_reference_list(trait.races)}\n"
            )

        if trait.subraces:
            content += f"Subraces: {D5eDocumentConverters._format_reference_list(trait.subraces)}\n"

        if trait.proficiencies:
            content += f"Grants Proficiencies: {D5eDocumentConverters._format_reference_list(trait.proficiencies)}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-traits",
                "index": trait.index,
                "name": trait.name,
                "type": "trait",
            },
        )

    @staticmethod
    def feature_to_document(feature: D5eFeature) -> Document:
        """Convert feature to document."""
        content = f"{feature.name} (Level {feature.level})\n\n"
        content += f"Class: {feature.class_.name}\n"

        if feature.subclass:
            content += f"Subclass: {feature.subclass.name}\n"

        content += f"\nDescription:\n{' '.join(feature.desc)}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-features",
                "index": feature.index,
                "name": feature.name,
                "level": feature.level,
                "class": feature.class_.index,
                "subclass": feature.subclass.index if feature.subclass else None,
                "type": "feature",
            },
        )

    @staticmethod
    def equipment_to_document(equipment: D5eEquipment) -> Document:
        """Convert equipment to document."""
        content = f"{equipment.name}\n\n"
        content += f"Category: {equipment.equipment_category.name}\n"
        content += f"Cost: {equipment.cost.quantity} {equipment.cost.unit}\n"

        if equipment.weight:
            content += f"Weight: {equipment.weight} lbs\n"

        # Weapon specific
        if equipment.weapon_category:
            content += f"\nWeapon Type: {equipment.weapon_category} {equipment.weapon_range or ''}\n"
            if equipment.damage:
                content += f"Damage: {equipment.damage.damage_dice or 'Unknown'}"
                if equipment.damage.damage_type:
                    content += f" {equipment.damage.damage_type.name}"
                content += "\n"
            if equipment.properties:
                content += f"Properties: {D5eDocumentConverters._format_reference_list(equipment.properties)}\n"

        # Armor specific
        if equipment.armor_category:
            content += f"\nArmor Type: {equipment.armor_category}\n"
            if equipment.armor_class:
                base_ac = equipment.armor_class.base
                dex_bonus = equipment.armor_class.dex_bonus
                max_bonus = equipment.armor_class.max_bonus

                content += f"AC: {base_ac}"
                if dex_bonus:
                    content += " + Dex modifier"
                    if max_bonus is not None:
                        content += f" (max {max_bonus})"
                content += "\n"

            if equipment.str_minimum:
                content += f"Strength Required: {equipment.str_minimum}\n"
            if equipment.stealth_disadvantage:
                content += "Stealth: Disadvantage\n"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-equipment",
                "index": equipment.index,
                "name": equipment.name,
                "category": equipment.equipment_category.index,
                "cost_gp": equipment.cost.quantity
                if equipment.cost.unit == "gp"
                else 0,
                "type": "equipment",
            },
        )

    @staticmethod
    def magic_item_to_document(item: D5eMagicItem) -> Document:
        """Convert magic item to document."""
        content = f"{item.name}\n\n"
        content += f"Category: {item.equipment_category.name}\n"
        content += f"Rarity: {item.rarity.get('name', 'Unknown')}\n\n"
        content += f"Description:\n{' '.join(item.desc)}\n"

        if item.variant:
            content += "\nThis is a variant item."
            if item.variants:
                content += f" Variants: {D5eDocumentConverters._format_reference_list(item.variants)}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-magic-items",
                "index": item.index,
                "name": item.name,
                "rarity": item.rarity.get("name", "Unknown"),
                "variant": item.variant,
                "type": "magic_item",
            },
        )

    @staticmethod
    def spell_to_document(spell: D5eSpell) -> Document:
        """Convert spell to document with rich formatting."""
        content = f"{spell.name}\n"
        content += f"Level {spell.level} {spell.school.name}"
        if spell.ritual:
            content += " (ritual)"
        content += "\n\n"

        content += f"Casting Time: {spell.casting_time}\n"
        content += f"Range: {spell.range}\n"
        content += f"Components: {', '.join(spell.components)}"
        if spell.material:
            content += f" ({spell.material})"
        content += "\n"

        content += "Duration: "
        if spell.concentration:
            content += "Concentration, "
        content += f"{spell.duration}\n\n"

        content += "Description:\n"
        content += "\n".join(spell.desc)

        if spell.higher_level:
            content += "\n\nAt Higher Levels:\n"
            content += "\n".join(spell.higher_level)

        content += f"\n\nClasses: {D5eDocumentConverters._format_reference_list(spell.classes)}"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-spells",
                "index": spell.index,
                "name": spell.name,
                "level": spell.level,
                "school": spell.school.index,
                "ritual": spell.ritual,
                "concentration": spell.concentration,
                "classes": [c.index for c in spell.classes],
                "type": "spell",
            },
        )

    @staticmethod
    def monster_to_document(monster: D5eMonster) -> Document:
        """Convert monster to document with complete stat block."""
        content = f"{monster.name}\n"
        content += f"{monster.size} {monster.type}, {monster.alignment}\n\n"

        # Basic stats
        if isinstance(monster.armor_class, list) and monster.armor_class:
            ac = monster.armor_class[0]
            content += f"Armor Class: {ac.value}"
            if ac.type:
                content += f" ({ac.type})"
            content += "\n"
        else:
            content += f"Armor Class: {monster.armor_class}\n"
        content += f"Hit Points: {monster.hit_points} ({monster.hit_dice})\n"
        # Speed
        speed_dict = monster.speed.model_dump(exclude_none=True)
        speed_parts = []
        for key, value in speed_dict.items():
            if key != "hover" and value:  # hover is bool, not speed
                speed_parts.append(f"{key} {value}")
        content += f"Speed: {', '.join(speed_parts)}\n\n"

        # Ability scores
        content += f"STR: {monster.strength} "
        content += f"DEX: {monster.dexterity} "
        content += f"CON: {monster.constitution} "
        content += f"INT: {monster.intelligence} "
        content += f"WIS: {monster.wisdom} "
        content += f"CHA: {monster.charisma}\n\n"

        # Proficiencies
        if monster.proficiencies:
            saves = [
                p
                for p in monster.proficiencies
                if "saving-throw" in p.proficiency.index
            ]
            skills = [
                p for p in monster.proficiencies if "skill" in p.proficiency.index
            ]

            if saves:
                content += f"Saving Throws: {', '.join(f'{p.proficiency.name} +{p.value}' for p in saves)}\n"
            if skills:
                content += f"Skills: {', '.join(f'{p.proficiency.name} +{p.value}' for p in skills)}\n"

        # Damage interactions
        if monster.damage_vulnerabilities:
            content += (
                f"Damage Vulnerabilities: {', '.join(monster.damage_vulnerabilities)}\n"
            )
        if monster.damage_resistances:
            content += f"Damage Resistances: {', '.join(monster.damage_resistances)}\n"
        if monster.damage_immunities:
            content += f"Damage Immunities: {', '.join(monster.damage_immunities)}\n"
        if monster.condition_immunities:
            content += f"Condition Immunities: {D5eDocumentConverters._format_reference_list(monster.condition_immunities)}\n"

        # Senses and languages
        if monster.senses:
            content += (
                f"Senses: {', '.join(f'{k} {v}' for k, v in monster.senses.items())}\n"
            )
        content += f"Languages: {monster.languages}\n"
        content += f"Challenge Rating: {monster.challenge_rating}\n\n"

        # Special abilities
        if monster.special_abilities:
            content += "Special Abilities:\n"
            for ability in monster.special_abilities:
                content += f"- {ability.name}: {ability.desc}\n"
            content += "\n"

        # Actions
        if monster.actions:
            content += "Actions:\n"
            for action in monster.actions:
                content += f"- {action.name}: {action.desc}\n"
            content += "\n"

        # Legendary actions
        if monster.legendary_actions:
            content += "Legendary Actions:\n"
            for action in monster.legendary_actions:
                content += f"- {action.name}: {action.desc}\n"

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-monsters",
                "index": monster.index,
                "name": monster.name,
                "size": monster.size,
                "type": monster.type,
                "challenge_rating": monster.challenge_rating,
                "hit_points": monster.hit_points,
                "is_legendary": bool(monster.legendary_actions),
                "entity_type": "monster",
            },
        )

    @staticmethod
    def rule_to_document(rule: Dict[str, Any]) -> Document:
        """Convert rule to document."""
        content = f"{rule.get('name', 'Unknown Rule')}\n\n"

        if "desc" in rule:
            content += rule["desc"]
        elif "subsections" in rule:
            for subsection in rule["subsections"]:
                content += f"\n{subsection.get('name', '')}\n"
                content += subsection.get("desc", "")

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-rules",
                "index": rule.get("index", ""),
                "name": rule.get("name", ""),
                "type": "rule",
            },
        )

    @staticmethod
    def weapon_property_to_document(prop: Dict[str, Any]) -> Document:
        """Convert weapon property dict to document."""
        content = f"{prop.get('name', 'Unknown Property')}\n\n"

        if "desc" in prop:
            desc_list = (
                prop["desc"] if isinstance(prop["desc"], list) else [prop["desc"]]
            )
            content += "\n".join(desc_list)

        return Document(
            page_content=content,
            metadata={
                "source": "d5e-weapon-properties",
                "index": prop.get("index", "unknown"),
                "name": prop.get("name", "Unknown"),
                "type": "weapon_property",
            },
        )

    @staticmethod
    def get_converter_for_category(category: str) -> Optional[DictConverterFunc]:
        """Get the appropriate converter function for a data category.

        Note: This returns converters that accept dict input (from model_dump()).
        Only used for entities without dedicated typed converters.
        """
        converters: Dict[str, DictConverterFunc] = {
            "rules": D5eDocumentConverters.rule_to_document,
            "rule-sections": D5eDocumentConverters.rule_to_document,
            "weapon-properties": D5eDocumentConverters.weapon_property_to_document,
        }

        return converters.get(category)
