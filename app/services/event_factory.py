"""
Factory for creating game events.

This module provides utility functions for creating complex events that require
service dependencies.
"""

from typing import List, Optional, Union

from app.core.domain_interfaces import ICharacterService
from app.models.character import CharacterInstanceModel, CombinedCharacterModel
from app.models.events import GameStateSnapshotEvent
from app.models.game_state import GameStateModel


def create_game_state_snapshot_event(
    game_state: GameStateModel,
    reason: str = "reconnection",
    character_service: Optional[ICharacterService] = None,
) -> GameStateSnapshotEvent:
    """Create a snapshot event from current game state.

    Args:
        game_state: The current game state
        reason: The reason for creating the snapshot
        character_service: Optional character service for fetching template data.
                         If provided, will return CombinedCharacterModel objects.
                         If not provided, will return CharacterInstanceModel objects.
    """

    # Extract party data
    party_data: List[Union[CharacterInstanceModel, CombinedCharacterModel]] = []
    for char_id, char_instance in game_state.party.items():
        if character_service:
            # Get the character template and create combined model
            char_data = character_service.get_character(char_id)
            if char_data:
                combined = CombinedCharacterModel.from_template_and_instance(
                    char_data.template, char_data.instance, char_id
                )
                party_data.append(combined)
            else:
                # Fallback to instance if template not found
                party_data.append(char_instance)
        else:
            # No character service provided - return instance directly
            party_data.append(char_instance)

    # Extract quest data - return QuestModel objects directly
    quest_data = list(game_state.active_quests.values())

    # Extract combat state if active - just use the CombatStateModel directly
    combat_data = game_state.combat if game_state.combat.is_active else None

    # Extract chat history - just return the ChatMessageModel objects
    chat_data = game_state.chat_history[-20:]  # Last 20 messages

    # Extract pending dice requests - return DiceRequestModel objects directly
    dice_requests = game_state.pending_player_dice_requests

    return GameStateSnapshotEvent(
        campaign_id=game_state.campaign_id,
        session_id=None,  # GameStateModel doesn't have session_id
        location=game_state.current_location,
        party_members=party_data,
        active_quests=quest_data,
        combat_state=combat_data,
        pending_dice_requests=dice_requests,
        chat_history=chat_data,
        reason=reason,
    )
