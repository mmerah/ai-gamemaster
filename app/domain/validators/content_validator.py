"""D&D 5e content validation utility.

This module provides validation for D&D 5e content references in character models,
campaigns, and other game entities. It ensures that references to races, classes,
spells, items, etc. are valid and exist in the content database.
"""

import logging
from typing import List, Optional, Set, Tuple, Union

from app.content.service import ContentService
from app.models.campaign.template import CampaignTemplateModel
from app.models.character.template import CharacterTemplateModel
from app.models.combat.combatant import CombatantModel
from app.models.utils import ProficienciesModel

logger = logging.getLogger(__name__)


class ContentValidationError:
    """Represents a content validation error."""

    def __init__(self, field: str, value: Union[str, List[str]], message: str) -> None:
        self.field = field
        self.value = value
        self.message = message

    def __str__(self) -> str:
        """String representation of the error."""
        if isinstance(self.value, list):
            value_str = ", ".join(self.value)
        else:
            value_str = str(self.value)
        return f"{self.field}: {self.message} (value: '{value_str}')"


class ContentValidator:
    """Validates D&D 5e content references in models."""

    def __init__(self, content_service: ContentService) -> None:
        """Initialize the validator with a content service.

        Args:
            content_service: The content service for validating references
        """
        self._content = content_service

    def validate_character_template(
        self,
        template: CharacterTemplateModel,
        content_pack_priority: Optional[List[str]] = None,
    ) -> Tuple[bool, List[ContentValidationError]]:
        """Validate all D&D 5e content references in a character template.

        Args:
            template: The character template to validate
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: List[ContentValidationError] = []

        # Use template's content pack IDs if not provided
        if content_pack_priority is None:
            content_pack_priority = template.content_pack_ids

        # Validate race
        if template.race:
            race = self._content._hub.races.get_by_name_with_options(
                template.race, content_pack_priority=content_pack_priority
            )
            if not race:
                race = self._content._hub.races.get_by_index_with_options(
                    template.race.lower().replace(" ", "-"),
                    content_pack_priority=content_pack_priority,
                )
            if not race:
                errors.append(
                    ContentValidationError(
                        "race", template.race, f"Race '{template.race}' not found"
                    )
                )

        # Validate subrace if present
        if template.subrace:
            subrace = self._content._hub.subraces.get_by_name_with_options(
                template.subrace, content_pack_priority=content_pack_priority
            )
            if not subrace:
                subrace = self._content._hub.subraces.get_by_index_with_options(
                    template.subrace.lower().replace(" ", "-"),
                    content_pack_priority=content_pack_priority,
                )
            if not subrace:
                errors.append(
                    ContentValidationError(
                        "subrace",
                        template.subrace,
                        f"Subrace '{template.subrace}' not found",
                    )
                )

        # Validate class
        if template.char_class:
            char_class = self._content._hub.classes.get_by_name_with_options(
                template.char_class, content_pack_priority=content_pack_priority
            )
            if not char_class:
                char_class = self._content._hub.classes.get_by_index_with_options(
                    template.char_class.lower(),
                    content_pack_priority=content_pack_priority,
                )
            if not char_class:
                errors.append(
                    ContentValidationError(
                        "char_class",
                        template.char_class,
                        f"Class '{template.char_class}' not found",
                    )
                )

        # Validate subclass if present
        if template.subclass:
            subclass = self._content._hub.subclasses.get_by_name_with_options(
                template.subclass, content_pack_priority=content_pack_priority
            )
            if not subclass:
                subclass = self._content._hub.subclasses.get_by_index_with_options(
                    template.subclass.lower().replace(" ", "-"),
                    content_pack_priority=content_pack_priority,
                )
            if not subclass:
                errors.append(
                    ContentValidationError(
                        "subclass",
                        template.subclass,
                        f"Subclass '{template.subclass}' not found",
                    )
                )

        # Validate background
        if template.background:
            background = self._content._hub.backgrounds.get_by_name_with_options(
                template.background, content_pack_priority=content_pack_priority
            )
            if not background:
                background = self._content._hub.backgrounds.get_by_index_with_options(
                    template.background.lower(),
                    content_pack_priority=content_pack_priority,
                )
            if not background:
                errors.append(
                    ContentValidationError(
                        "background",
                        template.background,
                        f"Background '{template.background}' not found",
                    )
                )

        # Validate alignment
        if template.alignment:
            alignment = self._content._hub.alignments.get_by_name_with_options(
                template.alignment, content_pack_priority=content_pack_priority
            )
            if not alignment:
                alignment = self._content._hub.alignments.get_by_index_with_options(
                    template.alignment.lower().replace(" ", "-"),
                    content_pack_priority=content_pack_priority,
                )
            if not alignment:
                errors.append(
                    ContentValidationError(
                        "alignment",
                        template.alignment,
                        f"Alignment '{template.alignment}' not found",
                    )
                )

        # Validate languages
        if template.languages:
            invalid_languages = self._validate_list_content(
                template.languages,
                "languages",
                content_pack_priority=content_pack_priority,
            )
            if invalid_languages:
                errors.append(
                    ContentValidationError(
                        "languages",
                        invalid_languages,
                        f"Invalid languages: {', '.join(invalid_languages)}",
                    )
                )

        # Validate spells
        if template.spells_known:
            invalid_spells = self._validate_list_content(
                template.spells_known,
                "spells",
                content_pack_priority=content_pack_priority,
            )
            if invalid_spells:
                errors.append(
                    ContentValidationError(
                        "spells_known",
                        invalid_spells,
                        f"Invalid spells: {', '.join(invalid_spells)}",
                    )
                )

        # Validate cantrips
        if template.cantrips_known:
            invalid_cantrips = self._validate_list_content(
                template.cantrips_known,
                "spells",
                content_pack_priority=content_pack_priority,
            )
            if invalid_cantrips:
                errors.append(
                    ContentValidationError(
                        "cantrips_known",
                        invalid_cantrips,
                        f"Invalid cantrips: {', '.join(invalid_cantrips)}",
                    )
                )

        # Validate proficiencies
        if template.proficiencies:
            prof_errors = self._validate_proficiencies(
                template.proficiencies, content_pack_priority=content_pack_priority
            )
            errors.extend(prof_errors)

        return (len(errors) == 0, errors)

    def validate_campaign_template(
        self,
        template: CampaignTemplateModel,
        content_pack_priority: Optional[List[str]] = None,
    ) -> Tuple[bool, List[ContentValidationError]]:
        """Validate D&D 5e content references in a campaign template.

        Args:
            template: The campaign template to validate
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: List[ContentValidationError] = []

        # Use template's content pack IDs if not provided
        if content_pack_priority is None:
            content_pack_priority = template.content_pack_ids

        # Validate allowed races if specified
        if template.allowed_races:
            invalid_races = self._validate_list_content(
                template.allowed_races,
                "races",
                content_pack_priority=content_pack_priority,
            )
            if invalid_races:
                errors.append(
                    ContentValidationError(
                        "allowed_races",
                        invalid_races,
                        f"Invalid races: {', '.join(invalid_races)}",
                    )
                )

        # Validate allowed classes if specified
        if template.allowed_classes:
            invalid_classes = self._validate_list_content(
                template.allowed_classes,
                "classes",
                content_pack_priority=content_pack_priority,
            )
            if invalid_classes:
                errors.append(
                    ContentValidationError(
                        "allowed_classes",
                        invalid_classes,
                        f"Invalid classes: {', '.join(invalid_classes)}",
                    )
                )

        return (len(errors) == 0, errors)

    def validate_combatant(
        self,
        combatant: CombatantModel,
        content_pack_priority: Optional[List[str]] = None,
    ) -> Tuple[bool, List[ContentValidationError]]:
        """Validate D&D 5e content references in a combatant.

        Args:
            combatant: The combatant to validate
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: List[ContentValidationError] = []

        # Validate conditions
        if combatant.conditions:
            invalid_conditions = self._validate_list_content(
                combatant.conditions,
                "conditions",
                content_pack_priority=content_pack_priority,
            )
            if invalid_conditions:
                errors.append(
                    ContentValidationError(
                        "conditions",
                        invalid_conditions,
                        f"Invalid conditions: {', '.join(invalid_conditions)}",
                    )
                )

        # Validate conditions_immune
        if combatant.conditions_immune:
            invalid_immune = self._validate_list_content(
                combatant.conditions_immune,
                "conditions",
                content_pack_priority=content_pack_priority,
            )
            if invalid_immune:
                errors.append(
                    ContentValidationError(
                        "conditions_immune",
                        invalid_immune,
                        f"Invalid condition immunities: {', '.join(invalid_immune)}",
                    )
                )

        # Validate damage resistances
        if combatant.resistances:
            invalid_resistances = self._validate_list_content(
                combatant.resistances,
                "damage-types",
                content_pack_priority=content_pack_priority,
            )
            if invalid_resistances:
                errors.append(
                    ContentValidationError(
                        "resistances",
                        invalid_resistances,
                        f"Invalid damage resistances: {', '.join(invalid_resistances)}",
                    )
                )

        # Validate damage vulnerabilities
        if combatant.vulnerabilities:
            invalid_vulnerabilities = self._validate_list_content(
                combatant.vulnerabilities,
                "damage-types",
                content_pack_priority=content_pack_priority,
            )
            if invalid_vulnerabilities:
                errors.append(
                    ContentValidationError(
                        "vulnerabilities",
                        invalid_vulnerabilities,
                        f"Invalid damage vulnerabilities: {', '.join(invalid_vulnerabilities)}",
                    )
                )

        # Note: We don't validate attacks here as they are free-form descriptions

        return (len(errors) == 0, errors)

    def validate_proficiencies(
        self,
        proficiencies: ProficienciesModel,
        content_pack_priority: Optional[List[str]] = None,
    ) -> Tuple[bool, List[ContentValidationError]]:
        """Validate proficiency references.

        Args:
            proficiencies: The proficiencies to validate
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = self._validate_proficiencies(proficiencies, content_pack_priority)
        return (len(errors) == 0, errors)

    def _validate_proficiencies(
        self,
        proficiencies: ProficienciesModel,
        content_pack_priority: Optional[List[str]] = None,
    ) -> List[ContentValidationError]:
        """Internal method to validate proficiencies."""
        errors: List[ContentValidationError] = []

        # Validate armor proficiencies
        if proficiencies.armor:
            invalid_armor = self._validate_proficiency_list(
                proficiencies.armor, "Armor", content_pack_priority
            )
            if invalid_armor:
                errors.append(
                    ContentValidationError(
                        "proficiencies.armor",
                        invalid_armor,
                        f"Invalid armor proficiencies: {', '.join(invalid_armor)}",
                    )
                )

        # Validate weapon proficiencies
        if proficiencies.weapons:
            invalid_weapons = self._validate_proficiency_list(
                proficiencies.weapons, "Weapons", content_pack_priority
            )
            if invalid_weapons:
                errors.append(
                    ContentValidationError(
                        "proficiencies.weapons",
                        invalid_weapons,
                        f"Invalid weapon proficiencies: {', '.join(invalid_weapons)}",
                    )
                )

        # Validate tool proficiencies
        if proficiencies.tools:
            invalid_tools = self._validate_proficiency_list(
                proficiencies.tools, "Tools", content_pack_priority
            )
            if invalid_tools:
                errors.append(
                    ContentValidationError(
                        "proficiencies.tools",
                        invalid_tools,
                        f"Invalid tool proficiencies: {', '.join(invalid_tools)}",
                    )
                )

        # Validate saving throw proficiencies (should be ability scores)
        if proficiencies.saving_throws:
            invalid_saves = self._validate_list_content(
                proficiencies.saving_throws,
                "ability-scores",
                content_pack_priority=content_pack_priority,
            )
            if invalid_saves:
                errors.append(
                    ContentValidationError(
                        "proficiencies.saving_throws",
                        invalid_saves,
                        f"Invalid saving throw proficiencies: {', '.join(invalid_saves)}",
                    )
                )

        # Validate skill proficiencies
        if proficiencies.skills:
            invalid_skills = self._validate_list_content(
                proficiencies.skills,
                "skills",
                content_pack_priority=content_pack_priority,
            )
            if invalid_skills:
                errors.append(
                    ContentValidationError(
                        "proficiencies.skills",
                        invalid_skills,
                        f"Invalid skill proficiencies: {', '.join(invalid_skills)}",
                    )
                )

        return errors

    def _validate_list_content(
        self,
        items: List[str],
        category: str,
        content_pack_priority: Optional[List[str]] = None,
    ) -> List[str]:
        """Validate a list of content references.

        Args:
            items: List of item names/indices to validate
            category: Content category (e.g., 'spells', 'races')
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            List of invalid items
        """
        invalid_items: List[str] = []
        repository = self._content._hub.get_repository(category)

        if not repository:
            logger.warning(f"No repository found for category '{category}'")
            return items  # Can't validate, assume all invalid

        for item in items:
            # Try by name first
            found = repository.get_by_name_with_options(
                item, content_pack_priority=content_pack_priority
            )
            if not found:
                # Try by index (lowercase, replace spaces with hyphens)
                index = item.lower().replace(" ", "-")
                found = repository.get_by_index_with_options(
                    index, content_pack_priority=content_pack_priority
                )

            if not found:
                invalid_items.append(item)

        return invalid_items

    def _validate_proficiency_list(
        self,
        items: List[str],
        proficiency_type: str,
        content_pack_priority: Optional[List[str]] = None,
    ) -> List[str]:
        """Validate a list of proficiency references.

        Args:
            items: List of proficiency names to validate
            proficiency_type: Type of proficiency (Armor, Weapons, Tools)
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            List of invalid proficiencies
        """
        invalid_items: List[str] = []
        all_proficiencies = self._content._hub.proficiencies.list_all_with_options(
            content_pack_priority=content_pack_priority
        )

        # Build a set of valid proficiency names for this type
        valid_proficiencies: Set[str] = set()
        for prof in all_proficiencies:
            if prof.type == proficiency_type:
                valid_proficiencies.add(prof.name.lower())
                # Also add the index
                valid_proficiencies.add(prof.index)

        # Check each item
        for item in items:
            if item.lower() not in valid_proficiencies:
                invalid_items.append(item)

        return invalid_items

    def validate_content_exists(
        self,
        content_type: str,
        identifier: str,
        content_pack_priority: Optional[List[str]] = None,
    ) -> bool:
        """Check if a specific content item exists.

        Args:
            content_type: Type of content (e.g., 'spell', 'monster', 'class')
            identifier: Name or index of the content
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            True if the content exists, False otherwise
        """
        # Map content type to repository category
        category_map = {
            "spell": "spells",
            "monster": "monsters",
            "class": "classes",
            "race": "races",
            "background": "backgrounds",
            "feat": "feats",
            "equipment": "equipment",
            "magic-item": "magic-items",
            "condition": "conditions",
            "damage-type": "damage-types",
            "skill": "skills",
            "language": "languages",
            "alignment": "alignments",
            "proficiency": "proficiencies",
        }

        category = category_map.get(content_type.lower())
        if not category:
            logger.warning(f"Unknown content type: {content_type}")
            return False

        repository = self._content._hub.get_repository(category)
        if not repository:
            logger.warning(f"No repository found for category '{category}'")
            return False

        # Try by name first
        found = repository.get_by_name_with_options(
            identifier, content_pack_priority=content_pack_priority
        )
        if found:
            return True

        # Try by index
        index = identifier.lower().replace(" ", "-")
        found = repository.get_by_index_with_options(
            index, content_pack_priority=content_pack_priority
        )

        return found is not None

    def get_valid_options(
        self,
        content_type: str,
        content_pack_priority: Optional[List[str]] = None,
    ) -> List[str]:
        """Get a list of valid options for a content type.

        Args:
            content_type: Type of content (e.g., 'races', 'classes')
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            List of valid option names
        """
        repository = self._content._hub.get_repository(content_type)
        if not repository:
            logger.warning(f"No repository found for content type '{content_type}'")
            return []

        items = repository.list_all_with_options(
            content_pack_priority=content_pack_priority
        )
        return [item.name for item in items]
