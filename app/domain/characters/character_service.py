"""
Character service implementation for managing character operations.
"""

import logging
from typing import Optional

from app.core.domain_interfaces import ICharacterService
from app.core.repository_interfaces import (
    ICharacterTemplateRepository,
    IGameStateRepository,
)
from app.models.character import (
    CharacterData,
    CharacterTemplateModel,
)

logger = logging.getLogger(__name__)


class CharacterService(ICharacterService):
    """Implementation of character service."""

    def __init__(
        self,
        game_state_repo: IGameStateRepository,
        character_template_repo: ICharacterTemplateRepository,
    ):
        self.game_state_repo = game_state_repo
        self.template_repo = character_template_repo

    def get_character(self, character_id: str) -> Optional[CharacterData]:
        """Get a character by ID, returning both instance and template data."""
        game_state = self.game_state_repo.get_game_state()
        instance = game_state.party.get(character_id)
        if not instance:
            return None

        # Get the template for static data
        template = self.template_repo.get(instance.template_id)
        if not template:
            logger.warning(
                f"Template {instance.template_id} not found for character {character_id}"
            )
            return None

        return CharacterData(
            template=template, instance=instance, character_id=character_id
        )

    def find_character_by_name_or_id(self, identifier: str) -> Optional[str]:
        """Find character ID by name or direct ID match."""
        if not identifier:
            return None

        game_state = self.game_state_repo.get_game_state()

        # Direct ID match in party
        if identifier in game_state.party:
            return identifier

        # Name-based search in party
        identifier_lower = identifier.lower()
        for char_id, instance in game_state.party.items():
            # Get template to check name
            template = self.template_repo.get(instance.template_id)
            if template and template.name.lower() == identifier_lower:
                logger.debug(
                    f"Found party member ID '{char_id}' by name '{identifier}'."
                )
                return char_id

        # Check active combat monsters
        if game_state.combat.is_active:
            # Direct ID check in combatants
            combatant = game_state.combat.get_combatant_by_id(identifier)
            if combatant and not combatant.is_player:
                return identifier

            # Name-based search in combatants
            for combatant in game_state.combat.combatants:
                if combatant.name.lower() == identifier_lower:
                    logger.debug(
                        f"Found combatant ID '{combatant.id}' by name '{identifier}'."
                    )
                    return combatant.id

        logger.warning(
            f"Could not find character or active combatant for identifier '{identifier}'."
        )
        return None

    def get_character_name(self, character_id: str) -> str:
        """Get display name for a character."""
        # Try player character first
        game_state = self.game_state_repo.get_game_state()
        instance = game_state.party.get(character_id)
        if instance:
            template = self.template_repo.get(instance.template_id)
            if template:
                return template.name

        # Try monster in active combat
        game_state = self.game_state_repo.get_game_state()
        if game_state.combat.is_active:
            combatant = game_state.combat.get_combatant_by_id(character_id)
            if combatant and not combatant.is_player:
                return combatant.name

        # Fallback to ID
        return character_id


class CharacterValidator:
    """Utility class for character validation operations."""

    @staticmethod
    def is_character_defeated(
        character_id: str, game_state_repo: IGameStateRepository
    ) -> bool:
        """Check if a character is defeated."""
        game_state = game_state_repo.get_game_state()

        # Check player character
        instance = game_state.party.get(character_id)
        if instance:
            return instance.current_hp <= 0

        # Check monster in combat
        if game_state.combat.is_active:
            combatant = game_state.combat.get_combatant_by_id(character_id)
            if combatant and not combatant.is_player:
                return combatant.current_hp <= 0 or "defeated" in [
                    c.lower() for c in combatant.conditions
                ]

        return False

    @staticmethod
    def is_character_incapacitated(
        character_id: str, game_state_repo: IGameStateRepository
    ) -> bool:
        """Check if a character is incapacitated (defeated or has incapacitating conditions)."""
        game_state = game_state_repo.get_game_state()

        # Check if defeated first
        if CharacterValidator.is_character_defeated(character_id, game_state_repo):
            return True

        # Check for incapacitating conditions
        instance = game_state.party.get(character_id)
        if instance:
            incapacitating_conditions = [
                "Unconscious",
                "Paralyzed",
                "Stunned",
                "Petrified",
            ]
            return any(
                condition in instance.conditions
                for condition in incapacitating_conditions
            )

        # Check monster conditions
        if game_state.combat.is_active:
            combatant = game_state.combat.get_combatant_by_id(character_id)
            if combatant and not combatant.is_player:
                incapacitating_conditions = [
                    "unconscious",
                    "paralyzed",
                    "stunned",
                    "petrified",
                ]
                return any(
                    condition.lower() in [c.lower() for c in combatant.conditions]
                    for condition in incapacitating_conditions
                )

        return False


class CharacterStatsCalculator:
    """Utility class for calculating character statistics."""

    @staticmethod
    def calculate_ability_modifier(ability_score: int) -> int:
        """Calculate ability modifier from ability score."""
        return (ability_score - 10) // 2

    @staticmethod
    def calculate_proficiency_bonus(level: int) -> int:
        """Calculate proficiency bonus based on character level."""
        return 2 + ((level - 1) // 4)

    @staticmethod
    def calculate_max_hp(template: CharacterTemplateModel, level: int) -> int:
        """Calculate maximum HP for a character."""
        con_mod = CharacterStatsCalculator.calculate_ability_modifier(
            template.base_stats.CON
        )
        hit_die_avg = 5  # Simplified for PoC (average of d8)
        return max(1, (hit_die_avg + con_mod) * level)

    @staticmethod
    def calculate_armor_class(template: CharacterTemplateModel) -> int:
        """Calculate armor class for a character."""
        dex_mod = CharacterStatsCalculator.calculate_ability_modifier(
            template.base_stats.DEX
        )
        base_ac = 10  # Simplified calculation
        return base_ac + dex_mod


# Avoid circular dependencies
__all__ = [
    "CharacterData",
    "ICharacterService",
    "CharacterService",
    "CharacterStatsCalculator",
    "CharacterValidator",
]
