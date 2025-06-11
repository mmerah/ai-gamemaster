"""Comprehensive data service for D&D 5e game data.

This service provides high-level methods for accessing and manipulating D&D 5e data,
building on top of the repository layer to provide game-specific functionality.
"""

from typing import Any, Dict, List, Optional, Tuple, cast

from app.models.d5e import (
    AbilityModifiers,
    AbilityScores,
    APIReference,
    ClassAtLevelInfo,
    ContentStatistics,
    D5eAbilityScore,
    D5eAlignment,
    D5eBackground,
    D5eClass,
    D5eCondition,
    D5eDamageType,
    D5eEntity,
    D5eEquipment,
    D5eFeat,
    D5eFeature,
    D5eLanguage,
    D5eLevel,
    D5eMagicItem,
    D5eMonster,
    D5eProficiency,
    D5eRace,
    D5eSkill,
    D5eSpell,
    D5eSubclass,
    D5eSubrace,
    D5eTrait,
    D5eWeaponProperty,
    DamageInteractionsInfo,
    SearchResults,
    StartingEquipmentInfo,
)
from app.repositories.d5e.repository_hub import D5eRepositoryHub
from app.services.d5e.data_loader import D5eDataLoader
from app.services.d5e.index_builder import D5eIndexBuilder
from app.services.d5e.reference_resolver import D5eReferenceResolver


class D5eDataService:
    """High-level service for D&D 5e data operations.

    This service provides convenient methods for common D&D 5e operations
    like character creation, spell management, combat setup, and rules lookup.
    """

    def __init__(
        self,
        data_loader: Optional[D5eDataLoader] = None,
        reference_resolver: Optional[D5eReferenceResolver] = None,
        index_builder: Optional[D5eIndexBuilder] = None,
    ) -> None:
        """Initialize the data service.

        Args:
            data_loader: Optional data loader instance
            reference_resolver: Optional reference resolver instance
            index_builder: Optional index builder instance
        """
        # Create dependencies if not provided
        self._data_loader = data_loader or D5eDataLoader()
        self._reference_resolver = reference_resolver or D5eReferenceResolver(
            self._data_loader
        )
        self._index_builder = index_builder or D5eIndexBuilder(self._data_loader)

        # Create the repository hub
        self._hub = D5eRepositoryHub(
            data_loader=self._data_loader,
            reference_resolver=self._reference_resolver,
            index_builder=self._index_builder,
        )

    # Character Creation Helpers

    def get_class_at_level(
        self, class_name: str, level: int
    ) -> Optional[ClassAtLevelInfo]:
        """Get complete class information at a specific level.

        This includes the base class data, all features gained up to that level,
        spell slots (if applicable), and other level-specific information.

        Args:
            class_name: Name or index of the class
            level: Character level (1-20)

        Returns:
            Dictionary with comprehensive class info, or None if not found
        """
        # Get the base class
        class_data = self._hub.classes.get_by_name(class_name)
        if not class_data:
            class_data = self._hub.classes.get_by_index(class_name.lower())

        if not class_data:
            return None

        # Get level-specific data
        level_data = self._hub.classes.get_level_data(class_data.index, level)
        if not level_data:
            return None

        # Get all features gained up to this level
        all_features = self._hub.classes.get_class_features(class_data.index)
        features_at_level = [f for f in all_features if f.level <= level]

        # Build comprehensive result
        result: ClassAtLevelInfo = {
            "class_": class_data.model_dump(),
            "level": level,
            "level_data": level_data.model_dump(),
            "features": [f.model_dump() for f in features_at_level],
            "proficiency_bonus": self.get_proficiency_bonus(level),
            "hit_points": {
                "hit_die": class_data.hit_die,
                "average_hp": class_data.hit_die
                + ((level - 1) * ((class_data.hit_die // 2) + 1)),
                "max_hp": class_data.hit_die * level,
            },
        }

        # Add spell slots if spellcasting class
        if class_data.spellcasting and level_data.spellcasting:
            result["spell_slots"] = self.get_spell_slots(class_data.index, level)

        # Add multiclassing requirements
        if class_data.multi_classing:
            result["multiclass_requirements"] = (
                self._hub.classes.get_multiclass_requirements(class_data.index)
            )

        return result

    def calculate_ability_modifiers(self, scores: AbilityScores) -> AbilityModifiers:
        """Calculate ability modifiers from ability scores.

        Args:
            scores: Dictionary mapping ability names/indices to scores

        Returns:
            Dictionary mapping ability names to modifiers
        """
        modifiers: AbilityModifiers = {}

        # Get all ability scores for name normalization
        all_abilities_raw = self._hub.ability_scores.list_all()
        all_abilities = [ability for ability in all_abilities_raw]
        ability_map = {ability.index: ability for ability in all_abilities}

        # Also map by full name and abbreviated name
        for ability_score in all_abilities:
            ability_map[ability_score.full_name.lower()] = ability_score
            ability_map[ability_score.name.lower()] = ability_score

        # Calculate modifiers
        for ability_key, score in scores.items():
            # Normalize the ability name
            normalized_key = ability_key.lower()
            ability_score_obj = ability_map.get(normalized_key)

            if ability_score_obj:
                # D&D 5e modifier calculation
                modifier = (score - 10) // 2
                modifiers[ability_score_obj.index] = modifier
                # Also include the abbreviated name for convenience
                modifiers[ability_score_obj.name] = modifier

        return modifiers

    def get_proficiency_bonus(self, level: int) -> int:
        """Get proficiency bonus for a character level.

        Args:
            level: Character level (1-20)

        Returns:
            Proficiency bonus
        """
        return self._hub.classes.get_proficiency_bonus(level)

    # Spell Management Helpers

    def get_spells_for_class(
        self, class_name: str, spell_level: Optional[int] = None
    ) -> List[D5eSpell]:
        """Get all spells available to a class.

        Args:
            class_name: Name or index of the class
            spell_level: Optional spell level filter (0-9)

        Returns:
            List of spells available to the class
        """
        # Normalize class name
        class_data = self._hub.classes.get_by_name(class_name)
        if not class_data:
            class_data = self._hub.classes.get_by_index(class_name.lower())

        if not class_data:
            return []

        # Get spells for the class
        class_spells = self._hub.spells.get_by_class(class_data.index)

        # Filter by spell level if specified
        if spell_level is not None:
            class_spells = [
                spell for spell in class_spells if spell.level == spell_level
            ]

        return class_spells

    def get_spell_slots(self, class_name: str, level: int) -> Optional[Dict[int, int]]:
        """Get spell slots by class and level.

        Args:
            class_name: Name or index of the spellcasting class
            level: Character level

        Returns:
            Dictionary mapping spell level to number of slots, or None
        """
        # Normalize class name
        class_data = self._hub.classes.get_by_name(class_name)
        if not class_data:
            class_data = self._hub.classes.get_by_index(class_name.lower())

        if not class_data:
            return None

        return self._hub.classes.get_spell_slots(class_data.index, level)

    # Combat Helpers

    def get_monsters_by_cr(self, min_cr: float, max_cr: float) -> List[D5eMonster]:
        """Get monsters within a challenge rating range.

        Args:
            min_cr: Minimum challenge rating (inclusive)
            max_cr: Maximum challenge rating (inclusive)

        Returns:
            List of monsters within the CR range
        """
        return self._hub.monsters.get_by_cr_range(min_cr, max_cr)

    def get_encounter_xp_budget(
        self, party_levels: List[int], difficulty: str = "medium"
    ) -> int:
        """Calculate XP budget for an encounter based on party composition.

        Args:
            party_levels: List of character levels in the party
            difficulty: Encounter difficulty (easy, medium, hard, deadly)

        Returns:
            Total XP budget for the encounter
        """
        # XP thresholds by character level
        xp_thresholds = {
            1: {"easy": 25, "medium": 50, "hard": 75, "deadly": 100},
            2: {"easy": 50, "medium": 100, "hard": 150, "deadly": 200},
            3: {"easy": 75, "medium": 150, "hard": 225, "deadly": 400},
            4: {"easy": 125, "medium": 250, "hard": 375, "deadly": 500},
            5: {"easy": 250, "medium": 500, "hard": 750, "deadly": 1100},
            6: {"easy": 300, "medium": 600, "hard": 900, "deadly": 1400},
            7: {"easy": 350, "medium": 750, "hard": 1100, "deadly": 1700},
            8: {"easy": 450, "medium": 900, "hard": 1400, "deadly": 2100},
            9: {"easy": 550, "medium": 1100, "hard": 1600, "deadly": 2400},
            10: {"easy": 600, "medium": 1200, "hard": 1900, "deadly": 2800},
            11: {"easy": 800, "medium": 1600, "hard": 2400, "deadly": 3600},
            12: {"easy": 1000, "medium": 2000, "hard": 3000, "deadly": 4500},
            13: {"easy": 1100, "medium": 2200, "hard": 3400, "deadly": 5100},
            14: {"easy": 1250, "medium": 2500, "hard": 3800, "deadly": 5700},
            15: {"easy": 1400, "medium": 2800, "hard": 4300, "deadly": 6400},
            16: {"easy": 1600, "medium": 3200, "hard": 4800, "deadly": 7200},
            17: {"easy": 2000, "medium": 3900, "hard": 5900, "deadly": 8800},
            18: {"easy": 2100, "medium": 4200, "hard": 6300, "deadly": 9500},
            19: {"easy": 2400, "medium": 4900, "hard": 7300, "deadly": 10900},
            20: {"easy": 2800, "medium": 5700, "hard": 8500, "deadly": 12700},
        }

        difficulty_lower = difficulty.lower()
        if difficulty_lower not in ["easy", "medium", "hard", "deadly"]:
            difficulty_lower = "medium"

        total_budget = 0
        for char_level in party_levels:
            if char_level in xp_thresholds:
                total_budget += xp_thresholds[char_level][difficulty_lower]

        return total_budget

    # Equipment Helpers

    def get_starting_equipment(
        self, class_name: str, background_name: str
    ) -> StartingEquipmentInfo:
        """Get all starting equipment options for a character.

        Args:
            class_name: Name or index of the class
            background_name: Name or index of the background

        Returns:
            Dictionary with 'class_' and 'background' equipment lists
        """
        equipment: StartingEquipmentInfo = {
            "class_": [],
            "background": [],
        }

        # Get class equipment
        class_data = self._hub.classes.get_by_name(class_name)
        if not class_data:
            class_data = self._hub.classes.get_by_index(class_name.lower())

        if class_data and hasattr(class_data, "starting_equipment"):
            # Get guaranteed starting equipment
            for item_ref in class_data.starting_equipment:
                # The equipment reference might be in the item_ref
                if hasattr(item_ref, "equipment") and hasattr(
                    item_ref.equipment, "index"
                ):
                    equip = self._hub.equipment.get_by_index(item_ref.equipment.index)
                    if equip:
                        equipment["class_"].append(equip)

        # Get background equipment
        background = self._hub.backgrounds.get_by_name(background_name)
        if not background:
            background = self._hub.backgrounds.get_by_index(background_name.lower())

        if background and hasattr(background, "starting_equipment"):
            for item_ref in background.starting_equipment:
                # Similar structure for background equipment
                if hasattr(item_ref, "equipment") and hasattr(
                    item_ref.equipment, "index"
                ):
                    equip = self._hub.equipment.get_by_index(item_ref.equipment.index)
                    if equip:
                        equipment["background"].append(equip)

        return equipment

    def get_armor_ac(
        self, armor_name: str, dexterity_modifier: int = 0
    ) -> Optional[int]:
        """Calculate AC for a specific armor.

        Args:
            armor_name: Name or index of the armor
            dexterity_modifier: Character's dexterity modifier

        Returns:
            Calculated AC or None if armor not found
        """
        armor = self._hub.equipment.get_by_name(armor_name)
        if not armor:
            armor = self._hub.equipment.get_by_index(armor_name.lower())

        if not armor or not hasattr(armor, "armor_class") or not armor.armor_class:
            return None

        # Handle both dict and object representations
        armor_class_data: Any = armor.armor_class
        if hasattr(armor_class_data, "base"):
            # It's a Pydantic model (ArmorClass)
            ac = armor_class_data.base
            dex_bonus = armor_class_data.dex_bonus
            max_bonus = armor_class_data.max_bonus
        else:
            # It's a dict
            ac = armor_class_data["base"]
            dex_bonus = armor_class_data.get("dex_bonus", False)
            max_bonus = armor_class_data.get("max_bonus")

        # Apply dexterity modifier based on armor type
        if dex_bonus:
            if max_bonus is not None:
                ac += min(dexterity_modifier, max_bonus)
            else:
                ac += dexterity_modifier

        return int(ac)

    # Rules Helpers

    def get_rule_section(self, section: str) -> List[str]:
        """Get rules text for a specific section.

        Args:
            section: Name or index of the rule section

        Returns:
            List of rule text paragraphs
        """
        rule_sections = self._hub.rule_sections.list_all()

        # Find the section by name or index
        target_section = None
        for rule_section in rule_sections:
            if hasattr(rule_section, "index") and hasattr(rule_section, "name"):
                if (
                    rule_section.index.lower() == section.lower()
                    or rule_section.name.lower() == section.lower()
                ):
                    target_section = rule_section
                    break

        if not target_section:
            return []

        # Get the actual rule content
        rules = self._hub.rules.list_all()
        section_rules: List[str] = []

        for rule in rules:
            # Check if this rule belongs to our section
            if (
                hasattr(rule, "parent")
                and rule.parent
                and hasattr(rule.parent, "index")
            ):
                if (
                    hasattr(target_section, "index")
                    and rule.parent.index == target_section.index
                ):
                    if hasattr(rule, "desc") and rule.desc:
                        section_rules.extend(rule.desc)

        return section_rules

    # Character Validation Helpers

    def validate_ability_scores(
        self, scores: Dict[str, int], method: str = "standard"
    ) -> Tuple[bool, List[str]]:
        """Validate ability scores based on generation method.

        Args:
            scores: Dictionary of ability scores
            method: Generation method (standard, point-buy, rolled)

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: List[str] = []

        # Check all six abilities are present
        required_abilities = {"str", "dex", "con", "int", "wis", "cha"}
        provided_abilities = {key.lower()[:3] for key in scores.keys()}

        missing = required_abilities - provided_abilities
        if missing:
            errors.append(f"Missing ability scores: {', '.join(missing)}")

        # Validate score ranges
        for ability, score in scores.items():
            if score < 1:
                errors.append(f"{ability} score cannot be less than 1")
            elif score > 20 and method != "rolled":
                errors.append(f"{ability} score cannot exceed 20")
            elif score > 30:
                errors.append(f"{ability} score cannot exceed 30")

        # Validate point buy if applicable
        if method == "point-buy":
            point_cost = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
            total_cost = 0

            for score in scores.values():
                if score < 8 or score > 15:
                    errors.append(
                        f"Point buy scores must be between 8 and 15, got {score}"
                    )
                else:
                    total_cost += point_cost.get(score, 0)

            if total_cost > 27:
                errors.append(f"Point buy total {total_cost} exceeds limit of 27")

        return (len(errors) == 0, errors)

    # Utility Methods

    def search_all_content(
        self, query: str, categories: Optional[List[str]] = None
    ) -> SearchResults:
        """Search across all or specified categories.

        Args:
            query: Search query
            categories: Optional list of categories to search

        Returns:
            Dictionary mapping category names to matching results
        """
        if categories:
            results: SearchResults = {}
            for category in categories:
                try:
                    repo = self._hub.get_repository(category)
                    matches = repo.search(query)
                    if matches:
                        results[category] = matches
                except Exception:
                    continue
            return results
        else:
            return self._hub.search_all(query)

    def get_content_statistics(self) -> ContentStatistics:
        """Get statistics about available content.

        Returns:
            Dictionary mapping content types to counts
        """
        return self._hub.get_statistics()

    def resolve_reference(self, reference: APIReference) -> Optional[D5eEntity]:
        """Resolve an API reference to its full data.

        Args:
            reference: The API reference to resolve

        Returns:
            The resolved entity or None
        """
        # The resolver expects a reference object, not just a URL
        ref_obj = {
            "index": reference.index,
            "name": reference.name,
            "url": reference.url,
        }
        result = self._reference_resolver.resolve_reference(ref_obj)
        return result  # type: ignore[return-value]

    def get_proficiency_description(
        self, proficiency_type: str
    ) -> List[D5eProficiency]:
        """Get all proficiencies of a specific type.

        Args:
            proficiency_type: Type of proficiency (Armor, Weapons, Tools, Skills, etc.)

        Returns:
            List of proficiencies of that type
        """
        all_proficiencies_raw = self._hub.proficiencies.list_all()
        return [
            prof
            for prof in all_proficiencies_raw
            if prof.type.lower() == proficiency_type.lower()
        ]

    def get_damage_vulnerabilities_resistances_immunities(
        self, monster_name: str
    ) -> DamageInteractionsInfo:
        """Get damage interactions for a monster.

        Args:
            monster_name: Name or index of the monster

        Returns:
            Dictionary with vulnerabilities, resistances, and immunities
        """
        monster = self._hub.monsters.get_by_name(monster_name)
        if not monster:
            monster = self._hub.monsters.get_by_index(monster_name.lower())

        if not monster:
            return {
                "vulnerabilities": [],
                "resistances": [],
                "immunities": [],
            }

        return {
            "vulnerabilities": monster.damage_vulnerabilities,
            "resistances": monster.damage_resistances,
            "immunities": monster.damage_immunities,
        }

    def calculate_spell_save_dc(
        self, class_name: str, level: int, ability_modifier: int
    ) -> Optional[int]:
        """Calculate spell save DC for a spellcasting class.

        Args:
            class_name: Name or index of the class
            level: Character level
            ability_modifier: Spellcasting ability modifier

        Returns:
            Spell save DC or None if not a spellcasting class
        """
        class_data = self._hub.classes.get_by_name(class_name)
        if not class_data:
            class_data = self._hub.classes.get_by_index(class_name.lower())

        if (
            not class_data
            or not hasattr(class_data, "spellcasting")
            or not class_data.spellcasting
        ):
            return None

        proficiency_bonus = self.get_proficiency_bonus(level)
        return 8 + proficiency_bonus + ability_modifier

    def get_languages(self, language_type: Optional[str] = None) -> List[D5eLanguage]:
        """Get languages, optionally filtered by type.

        Args:
            language_type: Optional type filter (Standard, Exotic)

        Returns:
            List of languages
        """
        all_languages_raw = self._hub.languages.list_all()
        all_languages = [lang for lang in all_languages_raw]

        if language_type:
            return [
                lang
                for lang in all_languages
                if lang.type.lower() == language_type.lower()
            ]

        return all_languages

    def get_conditions(self) -> List[D5eCondition]:
        """Get all conditions with their effects.

        Returns:
            List of all conditions
        """
        return self._hub.conditions.list_all()

    def get_skills_for_ability(self, ability: str) -> List[D5eSkill]:
        """Get all skills associated with an ability score.

        Args:
            ability: Ability score name or index

        Returns:
            List of skills using that ability
        """
        # Get the ability score
        ability_score = self._hub.ability_scores.get_by_name(ability)
        if not ability_score:
            ability_score = self._hub.ability_scores.get_by_index(ability.lower())

        if not ability_score:
            return []

        # Get all skills and filter
        all_skills_raw = self._hub.skills.list_all()
        all_skills = [skill for skill in all_skills_raw]
        return [
            skill
            for skill in all_skills
            if skill.ability_score.index == ability_score.index
        ]
