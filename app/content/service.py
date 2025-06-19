"""Comprehensive data service for D&D 5e game data.

This service provides high-level methods for accessing and manipulating D&D 5e data,
building on top of the repository layer to provide game-specific functionality.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, TypeAlias, cast

from app.content.repositories.db_repository_hub import D5eDbRepositoryHub
from app.content.schemas import (
    AbilityModifiers,
    AbilityScores,
    ClassAtLevelInfo,
    D5eAbilityScore,
    D5eAlignment,
    D5eBackground,
    D5eClass,
    D5eCondition,
    D5eEntity,
    D5eEquipment,
    D5eFeature,
    D5eLanguage,
    D5eMonster,
    D5eRace,
    D5eSkill,
    D5eSpell,
    SearchResults,
    StartingEquipmentInfo,
)
from app.core.content_interfaces import IContentService


class ContentService(IContentService):
    """High-level service for D&D 5e content operations.

    This service acts as the primary interface to the content subsystem,
    providing convenient methods for common D&D 5e operations like character
    creation, spell management, combat setup, and rules lookup.
    """

    def __init__(self, repository_hub: D5eDbRepositoryHub) -> None:
        """Initialize the data service.

        Args:
            repository_hub: The D5e repository hub for data access
        """
        self._hub = repository_hub

    # Character Creation Helpers

    def get_class_at_level(
        self,
        class_name: str,
        level: int,
        content_pack_priority: Optional[List[str]] = None,
    ) -> Optional[ClassAtLevelInfo]:
        """Get complete class information at a specific level.

        This includes the base class data, all features gained up to that level,
        spell slots (if applicable), and other level-specific information.

        Args:
            class_name: Name or index of the class
            level: Character level (1-20)
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            Dictionary with comprehensive class info, or None if not found
        """
        # Get the base class
        class_data = self._hub.classes.get_by_name_with_options(
            class_name, content_pack_priority=content_pack_priority
        )
        if not class_data:
            class_data = self._hub.classes.get_by_index_with_options(
                class_name.lower(), content_pack_priority=content_pack_priority
            )

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
        self,
        class_name: str,
        spell_level: Optional[int] = None,
        content_pack_priority: Optional[List[str]] = None,
    ) -> List[D5eSpell]:
        """Get all spells available to a class.

        Args:
            class_name: Name or index of the class
            spell_level: Optional spell level filter (0-9)
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            List of spells available to the class
        """
        # Normalize class name
        class_data = self._hub.classes.get_by_name_with_options(
            class_name, content_pack_priority=content_pack_priority
        )
        if not class_data:
            class_data = self._hub.classes.get_by_index_with_options(
                class_name.lower(), content_pack_priority=content_pack_priority
            )

        if not class_data:
            return []

        # Get spells for the class
        class_spells = self._hub.spells.get_by_class_with_options(
            class_data.index, content_pack_priority=content_pack_priority
        )

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
        self,
        query: str,
        categories: Optional[List[str]] = None,
        content_pack_priority: Optional[List[str]] = None,
    ) -> SearchResults:
        """Search across all or specified categories.

        Args:
            query: Search query
            categories: Optional list of categories to search
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            Dictionary mapping category names to matching results
        """
        if categories:
            results: SearchResults = {}
            for category in categories:
                try:
                    repo = self._hub.get_repository(category)
                    matches = repo.search_with_options(
                        query, content_pack_priority=content_pack_priority
                    )
                    if matches:
                        results[category] = matches
                except Exception:
                    continue
            return results
        else:
            return self._hub.search_all_with_options(
                query, content_pack_priority=content_pack_priority
            )

    def get_content_statistics(self) -> Dict[str, int]:
        """Get statistics about available content.

        Returns:
            Dictionary mapping content types to counts
        """
        return self._hub.get_statistics()

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

    # Additional convenience methods for CharacterFactory and other services

    def get_equipment_by_name(
        self, name: str, content_pack_priority: Optional[List[str]] = None
    ) -> Optional[D5eEquipment]:
        """Get equipment by name with content pack priority.

        Args:
            name: Name of the equipment
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            The equipment or None if not found
        """
        equipment = self._hub.equipment.get_by_name_with_options(
            name, content_pack_priority=content_pack_priority
        )
        if not equipment:
            # Try by index as fallback
            equipment = self._hub.equipment.get_by_index_with_options(
                name.lower().replace(" ", "-"),
                content_pack_priority=content_pack_priority,
            )
        return equipment

    def get_class_by_name(
        self, name: str, content_pack_priority: Optional[List[str]] = None
    ) -> Optional[D5eClass]:
        """Get class by name with content pack priority.

        Args:
            name: Name of the class
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            The class or None if not found
        """
        class_data = self._hub.classes.get_by_name_with_options(
            name, content_pack_priority=content_pack_priority
        )
        if not class_data:
            # Try by index as fallback
            class_data = self._hub.classes.get_by_index_with_options(
                name.lower(), content_pack_priority=content_pack_priority
            )
        return class_data

    def get_content_filtered(
        self,
        content_type: str,
        filters: Dict[str, Any],
        content_pack_ids: Optional[List[str]] = None,
    ) -> List[D5eEntity]:
        """Get filtered content of a specific type.

        This method provides a unified interface for accessing any content type
        with flexible filtering, supporting the consolidated API design.

        Args:
            content_type: The type of content to retrieve (e.g., 'spells', 'monsters')
            filters: Dictionary of filter parameters specific to the content type
            content_pack_ids: Optional list of content pack IDs for filtering

        Returns:
            List of matching content items

        Raises:
            ValueError: If content type is invalid or filters are invalid
        """
        # Map content type to repository and handle type-specific filtering
        FilterFunc: TypeAlias = Callable[[List[Any], Dict[str, Any]], List[Any]]
        type_mapping: Dict[str, Tuple[Any, FilterFunc]] = {
            "ability-scores": (self._hub.ability_scores, self._filter_ability_scores),
            "alignments": (self._hub.alignments, self._filter_generic),
            "backgrounds": (self._hub.backgrounds, self._filter_generic),
            "classes": (self._hub.classes, self._filter_generic),
            "conditions": (self._hub.conditions, self._filter_generic),
            "damage-types": (self._hub.damage_types, self._filter_generic),
            "equipment": (self._hub.equipment, self._filter_equipment),
            "equipment-categories": (
                self._hub.equipment_categories,
                self._filter_generic,
            ),
            "feats": (self._hub.feats, self._filter_generic),
            "features": (self._hub.features, self._filter_features),
            "languages": (self._hub.languages, self._filter_languages),
            "levels": (self._hub.levels, self._filter_generic),
            "magic-items": (self._hub.magic_items, self._filter_generic),
            "magic-schools": (self._hub.magic_schools, self._filter_generic),
            "monsters": (self._hub.monsters, self._filter_monsters),
            "proficiencies": (self._hub.proficiencies, self._filter_generic),
            "races": (self._hub.races, self._filter_generic),
            "rules": (self._hub.rules, self._filter_generic),
            "rule-sections": (self._hub.rule_sections, self._filter_generic),
            "skills": (self._hub.skills, self._filter_generic),
            "spells": (self._hub.spells, self._filter_spells),
            "subclasses": (self._hub.subclasses, self._filter_generic),
            "subraces": (self._hub.subraces, self._filter_generic),
            "traits": (self._hub.traits, self._filter_generic),
            "weapon-properties": (self._hub.weapon_properties, self._filter_generic),
        }

        if content_type not in type_mapping:
            raise ValueError(f"Invalid content type: {content_type}")

        repository, filter_func = type_mapping[content_type]

        # Get all items (with content pack filtering if specified)
        # TODO: For better performance with large datasets, consider pushing filtering
        # to the database level instead of loading all items into memory.
        # This is acceptable for now as this is a single-player game with limited data.
        if content_pack_ids and hasattr(repository, "list_all_with_options"):
            all_items = repository.list_all_with_options(
                content_pack_priority=content_pack_ids
            )
        else:
            all_items = repository.list_all()

        # Apply type-specific filtering
        return cast(List[D5eEntity], filter_func(all_items, filters))

    def get_content_by_id(
        self,
        content_type: str,
        item_id: str,
        content_pack_ids: Optional[List[str]] = None,
    ) -> Optional[D5eEntity]:
        """Get a specific content item by ID.

        This method provides a unified interface for accessing any content item
        by its ID, supporting the consolidated API design.

        Args:
            content_type: The type of content (e.g., 'spells', 'monsters')
            item_id: The unique identifier for the item
            content_pack_ids: Optional list of content pack IDs for priority

        Returns:
            The requested item or None if not found

        Raises:
            ValueError: If content type is invalid
        """
        # Map content type to repository
        type_to_repository = {
            "ability-scores": self._hub.ability_scores,
            "alignments": self._hub.alignments,
            "backgrounds": self._hub.backgrounds,
            "classes": self._hub.classes,
            "conditions": self._hub.conditions,
            "damage-types": self._hub.damage_types,
            "equipment": self._hub.equipment,
            "equipment-categories": self._hub.equipment_categories,
            "feats": self._hub.feats,
            "features": self._hub.features,
            "languages": self._hub.languages,
            "levels": self._hub.levels,
            "magic-items": self._hub.magic_items,
            "magic-schools": self._hub.magic_schools,
            "monsters": self._hub.monsters,
            "proficiencies": self._hub.proficiencies,
            "races": self._hub.races,
            "rules": self._hub.rules,
            "rule-sections": self._hub.rule_sections,
            "skills": self._hub.skills,
            "spells": self._hub.spells,
            "subclasses": self._hub.subclasses,
            "subraces": self._hub.subraces,
            "traits": self._hub.traits,
            "weapon-properties": self._hub.weapon_properties,
        }

        if content_type not in type_to_repository:
            raise ValueError(f"Invalid content type: {content_type}")

        repository = type_to_repository[content_type]

        # Try to get by index first (with content pack priority if supported)
        if content_pack_ids and hasattr(repository, "get_by_index_with_options"):
            item = repository.get_by_index_with_options(
                item_id, content_pack_priority=content_pack_ids
            )
        else:
            item = repository.get_by_index(item_id)  # type: ignore[attr-defined]

        # If not found by index, try by name if repository supports it
        if not item and hasattr(repository, "get_by_name"):
            if content_pack_ids and hasattr(repository, "get_by_name_with_options"):
                item = repository.get_by_name_with_options(
                    item_id, content_pack_priority=content_pack_ids
                )
            else:
                item = repository.get_by_name(item_id)

        return cast(Optional[D5eEntity], item)

    # ========================================================================
    # Filter Helper Methods
    # ========================================================================

    def _filter_generic(
        self, items: List[D5eEntity], filters: Dict[str, Any]
    ) -> List[D5eEntity]:
        """Generic filter that returns all items (no filtering)."""
        return items

    def _filter_ability_scores(
        self, items: List[D5eAbilityScore], filters: Dict[str, Any]
    ) -> List[D5eAbilityScore]:
        """Filter ability scores."""
        # Ability scores typically don't need filtering
        return items

    def _filter_spells(
        self, items: List[D5eSpell], filters: Dict[str, Any]
    ) -> List[D5eSpell]:
        """Filter spells based on level, school, and class."""
        filtered = items

        # Filter by spell level
        if "level" in filters:
            try:
                # Handle both string (from query params) and int
                level_value = filters["level"]
                if isinstance(level_value, list):
                    level_value = level_value[0]  # Take first value if list
                level = int(level_value)
                filtered = [s for s in filtered if s.level == level]
            except (ValueError, TypeError):
                pass

        # Filter by school
        if "school" in filters:
            school_value = filters["school"]
            if isinstance(school_value, list):
                school_value = school_value[0]  # Take first value if list
            school = str(school_value).lower()
            filtered = [
                s
                for s in filtered
                if hasattr(s.school, "index") and s.school.index.lower() == school
            ]

        # Filter by class
        if "class_name" in filters:
            class_name_value = filters["class_name"]
            if isinstance(class_name_value, list):
                class_name_value = class_name_value[0]  # Take first value if list
            class_name = str(class_name_value).lower()
            filtered = self.get_spells_for_class(
                class_name, int(filters["level"]) if "level" in filters else None
            )

        return filtered

    def _filter_monsters(
        self, items: List[D5eMonster], filters: Dict[str, Any]
    ) -> List[D5eMonster]:
        """Filter monsters based on CR, type, and size."""
        filtered = items

        # Filter by CR range
        if "min_cr" in filters or "max_cr" in filters:
            try:
                min_cr_value = filters.get("min_cr", 0)
                max_cr_value = filters.get("max_cr", 30)
                # Handle list values from query params
                if isinstance(min_cr_value, list):
                    min_cr_value = min_cr_value[0]
                if isinstance(max_cr_value, list):
                    max_cr_value = max_cr_value[0]
                min_cr = float(min_cr_value)
                max_cr = float(max_cr_value)
                filtered = [
                    m
                    for m in filtered
                    if hasattr(m, "challenge_rating")
                    and min_cr <= m.challenge_rating <= max_cr
                ]
            except (ValueError, TypeError):
                pass

        # Filter by type
        if "type" in filters:
            type_value = filters["type"]
            if isinstance(type_value, list):
                type_value = type_value[0]
            monster_type = str(type_value).lower()
            filtered = [
                m
                for m in filtered
                if hasattr(m, "type") and m.type.lower() == monster_type
            ]

        # Filter by size
        if "size" in filters:
            size_value = filters["size"]
            if isinstance(size_value, list):
                size_value = size_value[0]
            size = str(size_value).lower()
            filtered = [
                m for m in filtered if hasattr(m, "size") and m.size.lower() == size
            ]

        return filtered

    def _filter_equipment(
        self, items: List[D5eEquipment], filters: Dict[str, Any]
    ) -> List[D5eEquipment]:
        """Filter equipment based on category."""
        if "category" in filters:
            category = filters["category"].lower()
            return [
                e
                for e in items
                if hasattr(e, "equipment_category")
                and hasattr(e.equipment_category, "index")
                and e.equipment_category.index.lower() == category
            ]
        return items

    def _filter_features(
        self, items: List[D5eFeature], filters: Dict[str, Any]
    ) -> List[D5eFeature]:
        """Filter features based on class and level."""
        filtered = items

        if "class" in filters:
            class_name = filters["class"].lower()
            filtered = [
                f
                for f in filtered
                if hasattr(f, "class_")
                and hasattr(f.class_, "index")
                and f.class_.index.lower() == class_name
            ]

        if "level" in filters:
            try:
                level = int(filters["level"])
                filtered = [f for f in filtered if f.level == level]
            except (ValueError, TypeError):
                pass

        return filtered

    def _filter_languages(
        self, items: List[D5eLanguage], filters: Dict[str, Any]
    ) -> List[D5eLanguage]:
        """Filter languages based on type."""
        if "type" in filters:
            lang_type = filters["type"].lower()
            return [
                lang
                for lang in items
                if hasattr(lang, "type_") and lang.type_.lower() == lang_type
            ]
        return items

    def get_races(
        self, content_pack_priority: Optional[List[str]] = None
    ) -> List[D5eRace]:
        """Get all available races filtered by content packs.

        Args:
            content_pack_priority: Optional content pack priority list

        Returns:
            List of races
        """
        if content_pack_priority:
            return self._hub.races.list_all_with_options(
                content_pack_priority=content_pack_priority
            )
        else:
            return self._hub.races.list_all()

    def get_classes(
        self, content_pack_priority: Optional[List[str]] = None
    ) -> List[D5eClass]:
        """Get all available classes filtered by content packs.

        Args:
            content_pack_priority: Optional content pack priority list

        Returns:
            List of classes
        """
        if content_pack_priority:
            return self._hub.classes.list_all_with_options(
                content_pack_priority=content_pack_priority
            )
        else:
            return self._hub.classes.list_all()

    def get_backgrounds(
        self, content_pack_priority: Optional[List[str]] = None
    ) -> List[D5eBackground]:
        """Get all available backgrounds filtered by content packs.

        Args:
            content_pack_priority: Optional content pack priority list

        Returns:
            List of backgrounds
        """
        if content_pack_priority:
            return self._hub.backgrounds.list_all_with_options(
                content_pack_priority=content_pack_priority
            )
        else:
            return self._hub.backgrounds.list_all()

    def get_alignments(
        self, content_pack_priority: Optional[List[str]] = None
    ) -> List[D5eAlignment]:
        """Get all available alignments filtered by content packs.

        Args:
            content_pack_priority: Optional content pack priority list

        Returns:
            List of alignments
        """
        if content_pack_priority:
            return self._hub.alignments.list_all_with_options(
                content_pack_priority=content_pack_priority
            )
        else:
            return self._hub.alignments.list_all()

    def get_skills(
        self, content_pack_priority: Optional[List[str]] = None
    ) -> List[D5eSkill]:
        """Get all available skills filtered by content packs.

        Args:
            content_pack_priority: Optional content pack priority list

        Returns:
            List of skills
        """
        if content_pack_priority:
            return self._hub.skills.list_all_with_options(
                content_pack_priority=content_pack_priority
            )
        else:
            return self._hub.skills.list_all()

    def get_ability_scores(
        self, content_pack_priority: Optional[List[str]] = None
    ) -> List[D5eAbilityScore]:
        """Get all available ability scores filtered by content packs.

        Args:
            content_pack_priority: Optional content pack priority list

        Returns:
            List of ability scores
        """
        if content_pack_priority:
            return self._hub.ability_scores.list_all_with_options(
                content_pack_priority=content_pack_priority
            )
        else:
            return self._hub.ability_scores.list_all()
