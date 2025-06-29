"""
Event models package.

This package contains all game event models organized by category:
- base.py: BaseGameEvent
- utils.py: Utility models (CharacterChangesModel, ErrorContextModel)
- narrative.py: Narrative and chat events
- combat.py: Combat and combatant events
- dice.py: Dice roll events
- game_state.py: Location, party, quest, and item events
- system.py: System events (processing, errors, snapshots)
"""

# Base event
from app.models.events.base import BaseGameEvent

# Combat events
from app.models.events.combat import (
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

# Dice events
from app.models.events.dice import (
    NpcDiceRollProcessedEvent,
    PlayerDiceRequestAddedEvent,
    PlayerDiceRequestsClearedEvent,
)

# Event types
from app.models.events.event_types import GameEventType

# Event utility functions
from app.models.events.event_utils import (
    get_all_event_types,
    get_event_class_by_type,
)

# Game events
from app.models.events.game_events import (
    AIRequestContextModel,
    GameEventModel,
    GameEventResponseModel,
    PlayerActionEventModel,
)

# Game state events
from app.models.events.game_state import (
    ItemAddedEvent,
    LocationChangedEvent,
    PartyMemberUpdatedEvent,
    QuestUpdatedEvent,
)

# Narrative events
from app.models.events.narrative import MessageSupersededEvent, NarrativeAddedEvent

# System events
from app.models.events.system import (
    BackendProcessingEvent,
    GameErrorEvent,
    GameStateSnapshotEvent,
)

# Utility models
from app.models.events.utils import CharacterChangesModel, ErrorContextModel

__all__ = [
    # Base
    "BaseGameEvent",
    # Event types
    "GameEventType",
    # Game events
    "GameEventModel",
    "PlayerActionEventModel",
    "GameEventResponseModel",
    "AIRequestContextModel",
    # Utils
    "CharacterChangesModel",
    "ErrorContextModel",
    # Narrative
    "NarrativeAddedEvent",
    "MessageSupersededEvent",
    # Combat
    "CombatStartedEvent",
    "CombatEndedEvent",
    "TurnAdvancedEvent",
    "CombatantHpChangedEvent",
    "CombatantStatusChangedEvent",
    "CombatantAddedEvent",
    "CombatantRemovedEvent",
    "CombatantInitiativeSetEvent",
    "InitiativeOrderDeterminedEvent",
    # Dice
    "PlayerDiceRequestAddedEvent",
    "PlayerDiceRequestsClearedEvent",
    "NpcDiceRollProcessedEvent",
    # Game state
    "LocationChangedEvent",
    "PartyMemberUpdatedEvent",
    "QuestUpdatedEvent",
    "ItemAddedEvent",
    # System
    "BackendProcessingEvent",
    "GameErrorEvent",
    "GameStateSnapshotEvent",
    # Utility functions
    "get_all_event_types",
    "get_event_class_by_type",
]
