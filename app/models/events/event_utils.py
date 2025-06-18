"""
Utility functions for event management.
"""

from typing import Dict, List, Optional, Type, cast

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
