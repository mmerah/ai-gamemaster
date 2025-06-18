"""
Combat utility classes for validation and formatting.
"""

import logging
from typing import Any, List, Optional

from app.core.interfaces import IGameStateRepository
from app.models.combat import CombatantModel, CombatInfoResponseModel

logger = logging.getLogger(__name__)


class CombatValidator:
    """Utility class for combat validation operations."""

    @staticmethod
    def is_combat_active(game_state_repo: IGameStateRepository) -> bool:
        """Check if combat is currently active."""
        game_state = game_state_repo.get_game_state()
        return game_state.combat.is_active

    @staticmethod
    def get_current_combatant_id(game_state_repo: IGameStateRepository) -> str:
        """Get the ID of the current combatant."""
        game_state = game_state_repo.get_game_state()

        if (
            game_state.combat.is_active
            and game_state.combat.combatants
            and 0
            <= game_state.combat.current_turn_index
            < len(game_state.combat.combatants)
        ):
            return game_state.combat.combatants[game_state.combat.current_turn_index].id

        return ""


class CombatFormatter:
    """Utility class for formatting combat information."""

    @staticmethod
    def format_combat_status(
        game_state_repo: IGameStateRepository,
    ) -> Optional[CombatInfoResponseModel]:
        """Format current combat status for display."""
        game_state = game_state_repo.get_game_state()

        if not game_state.combat.is_active:
            return CombatInfoResponseModel(is_active=False)

        current_combatant_name: Optional[str] = None
        current_combatant_id: Optional[str] = None

        if (
            game_state.combat.combatants
            and 0
            <= game_state.combat.current_turn_index
            < len(game_state.combat.combatants)
        ):
            current_combatant = game_state.combat.combatants[
                game_state.combat.current_turn_index
            ]
            current_combatant_id = current_combatant.id
            current_combatant_name = current_combatant.name

        # Format combatants for frontend
        formatted_combatants: List[CombatantModel] = []
        turn_order: List[str] = []

        for combatant in game_state.combat.combatants:
            # combatant is already a CombatantModel, so we can use it directly
            formatted_combatants.append(combatant)
            turn_order.append(combatant.id)

        return CombatInfoResponseModel(
            is_active=True,
            round_number=game_state.combat.round_number,
            current_combatant_id=current_combatant_id,
            current_combatant_name=current_combatant_name,
            combatants=formatted_combatants,
            turn_order=turn_order,
        )
