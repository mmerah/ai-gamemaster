"""Utility functions shared across state processors."""

import logging
from typing import List, Optional

from app.core.ai_interfaces import IAIResponseProcessor
from app.models.game_state import GameStateModel

logger = logging.getLogger(__name__)


def get_target_ids_for_update(
    game_state: GameStateModel,
    character_id_field: str,
    game_manager: Optional[IAIResponseProcessor] = None,
) -> List[str]:
    """
    Resolves a character_id field that might be a specific ID, "party", or "all_players".
    Returns a list of specific character IDs.
    """
    if character_id_field.lower() in ["party", "all_players", "all_pcs"]:
        return list(game_state.party.keys())

    # Try to resolve as a single specific ID
    resolved_id = (
        game_manager.find_combatant_id_by_name_or_id(character_id_field)
        if game_manager
        else character_id_field
    )
    if resolved_id:
        return [resolved_id]

    logger.warning(
        f"Could not resolve '{character_id_field}' to any specific character or party keyword."
    )
    return []
