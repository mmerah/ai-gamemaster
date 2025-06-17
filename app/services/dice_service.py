"""
Dice service for handling dice rolls and modifiers.
"""

import logging
import random
from typing import Any, Optional

from app.core.interfaces import (
    CharacterService,
    DiceRollingService,
    GameStateRepository,
)
from app.domain.shared.calculators.character_stats import (
    calculate_total_modifier_for_roll,
)
from app.domain.shared.calculators.dice_mechanics import (
    format_roll_type_description,
    roll_dice_formula,
)
from app.models.character import CharacterData, CharacterModifierDataModel
from app.models.dice import (
    DiceExecutionModel,
    DiceRollMessageModel,
    DiceRollResultResponseModel,
)

logger = logging.getLogger(__name__)


class DiceRollingServiceImpl(DiceRollingService):
    """Implementation of dice rolling service."""

    def __init__(
        self, character_service: CharacterService, game_state_repo: GameStateRepository
    ):
        self.character_service = character_service
        self.game_state_repo = game_state_repo

    def perform_roll(
        self,
        character_id: str,
        roll_type: str,
        dice_formula: str,
        skill: Optional[str] = None,
        ability: Optional[str] = None,
        dc: Optional[int] = None,
        reason: str = "",
        original_request_id: Optional[str] = None,
    ) -> DiceRollResultResponseModel:
        """Perform a dice roll and return the result."""
        actual_char_id = self.character_service.find_character_by_name_or_id(
            character_id
        )
        if not actual_char_id:
            error_msg = f"Cannot roll: Unknown character/combatant '{character_id}'."
            logger.error(error_msg)
            # Return error in model
            return DiceRollResultResponseModel(
                request_id=original_request_id or "",
                character_id=character_id or "",
                character_name="Unknown",
                roll_type=roll_type,
                dice_formula=dice_formula,
                character_modifier=0,
                total_result=0,
                reason=reason,
                result_message="",
                result_summary="",
                error=error_msg,
            )

        char_name = self.character_service.get_character_name(actual_char_id)

        # For damage rolls and custom rolls, don't add character modifiers
        # The AI already includes all modifiers in the dice formula (e.g., "1d8+3")
        if roll_type in ["damage_roll", "custom"]:
            char_modifier = 0
        else:
            char_modifier = self._calculate_character_modifier(
                actual_char_id, roll_type, skill, ability
            )

        # Perform the actual dice roll
        roll_result = self._execute_dice_roll(dice_formula)
        if roll_result.is_error:
            return DiceRollResultResponseModel(
                request_id=original_request_id
                or self._generate_request_id(actual_char_id, roll_type),
                character_id=actual_char_id,
                character_name=char_name,
                roll_type=roll_type,
                dice_formula=dice_formula,
                character_modifier=char_modifier,
                total_result=0,
                reason=reason,
                result_message="",
                result_summary="",
                error=f"Invalid dice formula '{dice_formula}' for {char_name}.",
            )

        # We know roll_result has values when not an error
        assert roll_result.total is not None
        final_result = roll_result.total + char_modifier
        success = self._determine_success(final_result, dc)

        # Generate result messages
        messages = self._generate_roll_messages(
            char_name,
            roll_type,
            skill,
            ability,
            dice_formula,
            char_modifier,
            roll_result,
            final_result,
            dc,
            success,
        )

        # Generate unique request ID if not provided
        result_request_id = original_request_id or self._generate_request_id(
            actual_char_id, roll_type
        )

        logger.info(f"Roll: {messages.detailed} (Reason: {reason})")

        return DiceRollResultResponseModel(
            request_id=result_request_id,
            character_id=actual_char_id,
            character_name=char_name,
            roll_type=roll_type,
            dice_formula=dice_formula,
            character_modifier=char_modifier,
            total_result=final_result,
            dc=dc,
            success=success,
            reason=reason,
            result_message=messages.detailed,
            result_summary=messages.summary,
        )

    def _calculate_character_modifier(
        self,
        character_id: str,
        roll_type: str,
        skill: Optional[str],
        ability: Optional[str],
    ) -> int:
        """Calculate the modifier for a character's roll."""
        char_instance = self.character_service.get_character(character_id)

        if char_instance:
            return self._calculate_player_modifier(
                char_instance, roll_type, skill, ability
            )
        else:
            return self._calculate_npc_modifier(character_id, roll_type, skill, ability)

    def _calculate_player_modifier(
        self,
        character: CharacterData,
        roll_type: str,
        skill: Optional[str],
        ability: Optional[str],
    ) -> int:
        """Calculate modifier for a player character."""
        # Handle new CharacterData structure
        # CharacterData is a NamedTuple with template and instance
        template = character.template
        instance = character.instance
        # Build CharacterModifierDataModel with model_dump (justified for internal calculations)
        char_data_for_mod = CharacterModifierDataModel(
            stats=template.base_stats.model_dump(),
            proficiencies=template.proficiencies.model_dump(),
            level=instance.level,
        )

        return calculate_total_modifier_for_roll(
            char_data_for_mod, roll_type, skill, ability
        )

    def _calculate_npc_modifier(
        self,
        character_id: str,
        roll_type: str,
        skill: Optional[str],
        ability: Optional[str],
    ) -> int:
        """Calculate modifier for an NPC."""
        game_state = self.game_state_repo.get_game_state()

        if game_state.combat.is_active:
            combatant = game_state.combat.get_combatant_by_id(character_id)
            if combatant and not combatant.is_player:
                temp_npc_data_for_mod = CharacterModifierDataModel(
                    stats=combatant.stats or {"DEX": 10},
                    proficiencies={},
                    level=1,  # Default level for NPCs
                )
                return calculate_total_modifier_for_roll(
                    temp_npc_data_for_mod, roll_type, skill, ability
                )

        logger.warning(
            f"perform_roll for non-player, non-tracked-NPC '{character_id}'. Assuming 0 modifier."
        )
        return 0

    def _execute_dice_roll(self, dice_formula: str) -> DiceExecutionModel:
        """Execute the actual dice roll."""
        base_total, individual_rolls, _, formula_desc = roll_dice_formula(dice_formula)

        if formula_desc.startswith("Invalid"):
            return DiceExecutionModel(error="Invalid dice formula")

        return DiceExecutionModel(
            total=base_total,
            individual_rolls=individual_rolls,
            formula_description=formula_desc,
        )

    def _determine_success(
        self, final_result: int, dc: Optional[int]
    ) -> Optional[bool]:
        """Determine if the roll was successful."""
        if dc is not None:
            return final_result >= dc
        return None

    def _generate_roll_messages(
        self,
        char_name: str,
        roll_type: str,
        skill: Optional[str],
        ability: Optional[str],
        dice_formula: str,
        char_modifier: int,
        roll_result: DiceExecutionModel,
        final_result: int,
        dc: Optional[int],
        success: Optional[bool],
    ) -> DiceRollMessageModel:
        """Generate detailed and summary messages for the roll."""
        type_desc = format_roll_type_description(roll_type, skill, ability)

        # For damage rolls and custom rolls, modifiers are already in the formula
        # We know these fields are not None when generating messages for successful rolls
        assert roll_result.individual_rolls is not None
        assert roll_result.formula_description is not None

        if roll_type in ["damage_roll", "custom"] or char_modifier == 0:
            # Don't show modifier for damage rolls
            roll_details = f"[{','.join(map(str, roll_result.individual_rolls))}]"
            detailed_msg = (
                f"{char_name} rolls {type_desc}: {roll_result.formula_description} "
                f"-> {roll_details} = **{final_result}**."
            )
        else:
            # Show modifier for other rolls (skill checks, saves, attacks)
            mod_str = f"{char_modifier:+}"
            roll_details = (
                f"[{','.join(map(str, roll_result.individual_rolls))}] {mod_str}"
            )
            detailed_msg = (
                f"{char_name} rolls {type_desc}: {roll_result.formula_description} "
                f"({mod_str}) -> {roll_details} = **{final_result}**."
            )

        # Summary message
        summary_msg = f"{char_name} rolls {type_desc}: Result **{final_result}**."

        # Add DC and success information
        if dc is not None:
            dc_text = f" (DC {dc})"
            detailed_msg += dc_text
            summary_msg += dc_text

            if success is not None:
                success_text = " Success!" if success else " Failure."
                detailed_msg += success_text
                summary_msg += success_text

        # Return a DiceRollMessageModel instead of dict
        return DiceRollMessageModel(
            detailed=detailed_msg.strip(), summary=summary_msg.strip()
        )

    def _generate_request_id(self, character_id: str, roll_type: str) -> str:
        """Generate a unique request ID for the roll."""
        return f"roll_{character_id}_{roll_type.replace(' ', '_')}_{random.randint(1000, 9999)}"
