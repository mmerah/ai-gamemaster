"""
System event models.

This module contains system-level events like processing status,
errors, and state snapshots.
"""

from typing import List, Literal, Optional, Union

from pydantic import Field

from app.models.character.combined import CombinedCharacterModel
from app.models.character.instance import CharacterInstanceModel
from app.models.combat.state import CombatStateModel
from app.models.dice import DiceRequestModel
from app.models.events.base import BaseGameEvent
from app.models.events.utils import ErrorContextModel
from app.models.shared import ChatMessageModel
from app.models.utils import LocationModel, QuestModel


class BackendProcessingEvent(BaseGameEvent):
    event_type: Literal["backend_processing"] = "backend_processing"
    is_processing: bool
    needs_backend_trigger: bool = False
    trigger_reason: Optional[str] = None


class GameErrorEvent(BaseGameEvent):
    event_type: Literal["game_error"] = "game_error"
    error_message: str
    error_type: str  # "ai_service_error", "invalid_reference", etc.
    severity: Literal["warning", "error", "critical"] = "error"
    recoverable: bool = True
    context: Optional[ErrorContextModel] = None
    error_code: Optional[str] = None


class GameStateSnapshotEvent(BaseGameEvent):
    """Event emitted to provide full game state snapshot for reconnection/sync."""

    event_type: Literal["game_state_snapshot"] = "game_state_snapshot"

    # Core game state
    campaign_id: Optional[str] = None
    session_id: Optional[str] = None
    location: LocationModel  # Typed location model

    # Party and characters - typed models for better type safety
    party_members: List[
        Union[CharacterInstanceModel, CombinedCharacterModel]
    ]  # Character instances or combined models

    # Quests - typed models
    active_quests: List[QuestModel] = Field(default_factory=list)

    # Combat state (if active) - typed model
    combat_state: Optional[CombatStateModel] = None

    # Pending requests - typed models
    pending_dice_requests: List[DiceRequestModel] = Field(default_factory=list)

    # Chat history - typed models
    chat_history: List[ChatMessageModel] = Field(default_factory=list)

    # Reason for snapshot
    reason: str = "reconnection"  # "initial_load", "reconnection", "state_recovery"
