"""
Utility functions for event management.
"""

from typing import Dict, List, Optional, Type, Union, cast

from app.core.interfaces import CharacterService
from app.models.character import CharacterInstanceModel, CombinedCharacterModel
from app.models.game_state import GameStateModel

from .base import BaseGameEvent
from .combat import (
    CombatantAddedEvent,
    CombatantHpChangedEvent,
    CombatantInitiativeSetEvent,
    CombatantRemovedEvent,
    CombatantStatusChangedEvent,
    CombatEndedEvent,
    CombatStartedEvent,
    InitiativeOrderDeterminedEvent,
    TurnAdvancedEvent,
)
from .dice import (
    NpcDiceRollProcessedEvent,
    PlayerDiceRequestAddedEvent,
    PlayerDiceRequestsClearedEvent,
)
from .game_state import (
    ItemAddedEvent,
    LocationChangedEvent,
    PartyMemberUpdatedEvent,
    QuestUpdatedEvent,
)
from .narrative import MessageSupersededEvent, NarrativeAddedEvent
from .system import BackendProcessingEvent, GameErrorEvent, GameStateSnapshotEvent


def create_game_state_snapshot_event(
    game_state: GameStateModel,
    reason: str = "reconnection",
    character_service: CharacterService | None = None,
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


# Utility function to get all event types
def get_all_event_types() -> List[Type[BaseGameEvent]]:
    """Get all event class types for validation."""
    event_types = [
        NarrativeAddedEvent,
        MessageSupersededEvent,
        CombatStartedEvent,
        CombatEndedEvent,
        TurnAdvancedEvent,
        CombatantHpChangedEvent,
        CombatantStatusChangedEvent,
        CombatantAddedEvent,
        CombatantRemovedEvent,
        CombatantInitiativeSetEvent,
        InitiativeOrderDeterminedEvent,
        PlayerDiceRequestAddedEvent,
        PlayerDiceRequestsClearedEvent,
        NpcDiceRollProcessedEvent,
        LocationChangedEvent,
        PartyMemberUpdatedEvent,
        BackendProcessingEvent,
        GameErrorEvent,
        GameStateSnapshotEvent,
        QuestUpdatedEvent,
        ItemAddedEvent,
    ]
    return cast(List[Type[BaseGameEvent]], event_types)


# Event Type Registry for dynamic class lookup
_EVENT_TYPE_REGISTRY: Dict[str, Type[BaseGameEvent]] = {}


def _build_event_registry() -> None:
    """Build the event type registry."""
    for event_class in get_all_event_types():
        if hasattr(event_class, "model_fields"):
            # For Pydantic V2 models, check the model fields
            fields = event_class.model_fields
            if "event_type" in fields:
                # Get the default value from the field
                field_info = fields["event_type"]
                default_value = field_info.default
                if default_value:
                    _EVENT_TYPE_REGISTRY[default_value] = event_class


def get_event_class_by_type(event_type: str) -> Optional[Type[BaseGameEvent]]:
    """Get event class by its event_type string."""
    if not _EVENT_TYPE_REGISTRY:
        _build_event_registry()
    return _EVENT_TYPE_REGISTRY.get(event_type)


# Build the registry on module import
_build_event_registry()
