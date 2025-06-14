"""
Game event models.

This module contains all game event models for the event-driven architecture.
"""

from datetime import datetime, timezone
from typing import List, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import BaseModelWithDatetimeSerializer
from app.models.character import CharacterInstanceModel, CombinedCharacterModel
from app.models.combat import CombatantModel, CombatStateModel
from app.models.dice import DiceRequestModel
from app.models.game_state import ChatMessageModel
from app.models.utils import LocationModel, QuestModel
from app.utils.event_sequence import get_next_sequence_number


class CharacterChangesModel(BaseModel):
    """Changes to a character during game play."""

    current_hp: Optional[int] = Field(None, description="New current HP")
    max_hp: Optional[int] = Field(None, description="New maximum HP")
    temp_hp: Optional[int] = Field(None, description="New temporary HP")
    conditions: Optional[List[str]] = Field(None, description="New conditions list")
    gold: Optional[int] = Field(None, description="New gold amount")
    experience_points: Optional[int] = Field(None, description="New experience points")
    level: Optional[int] = Field(None, description="New character level")
    exhaustion_level: Optional[int] = Field(None, description="New exhaustion level")
    inventory_added: Optional[List[str]] = Field(
        None, description="Items added to inventory"
    )
    inventory_removed: Optional[List[str]] = Field(
        None, description="Items removed from inventory"
    )

    model_config = ConfigDict(extra="forbid")


class ErrorContextModel(BaseModel):
    """Context information for game errors."""

    event_type: Optional[str] = Field(
        None, description="Type of event that caused error"
    )
    character_id: Optional[str] = Field(None, description="Character ID involved")
    location: Optional[str] = Field(None, description="Location where error occurred")
    user_action: Optional[str] = Field(
        None, description="User action that triggered error"
    )
    ai_response: Optional[str] = Field(
        None, description="AI response that caused error"
    )
    stack_trace: Optional[str] = Field(None, description="Python stack trace")

    model_config = ConfigDict(extra="forbid")


# ===== BASE EVENT CLASS =


class BaseGameEvent(BaseModelWithDatetimeSerializer):
    """Base class for all game events"""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_number: int = Field(default_factory=get_next_sequence_number)
    event_type: str
    correlation_id: Optional[str] = None

    model_config = ConfigDict()


# ===== NARRATIVE EVENTS =====


class NarrativeAddedEvent(BaseGameEvent):
    event_type: Literal["narrative_added"] = "narrative_added"
    role: str  # "assistant", "user", "system"
    content: str
    gm_thought: Optional[str] = None
    audio_path: Optional[str] = None
    message_id: Optional[str] = None


class MessageSupersededEvent(BaseGameEvent):
    event_type: Literal["message_superseded"] = "message_superseded"
    message_id: str
    reason: str = "retry"


# ===== COMBAT EVENTS =====


class CombatStartedEvent(BaseGameEvent):
    event_type: Literal["combat_started"] = "combat_started"
    combatants: List[CombatantModel]  # Typed combatant models for type safety
    round_number: int = 1


class CombatEndedEvent(BaseGameEvent):
    event_type: Literal["combat_ended"] = "combat_ended"
    reason: str  # "victory", "retreat", "narrative"
    outcome_description: Optional[str] = None


class TurnAdvancedEvent(BaseGameEvent):
    event_type: Literal["turn_advanced"] = "turn_advanced"
    new_combatant_id: str
    new_combatant_name: str
    round_number: int
    is_new_round: bool = False
    is_player_controlled: bool = False


# ===== COMBATANT STATE EVENTS =====


class CombatantHpChangedEvent(BaseGameEvent):
    event_type: Literal["combatant_hp_changed"] = "combatant_hp_changed"
    combatant_id: str
    combatant_name: str
    old_hp: int
    new_hp: int
    max_hp: int
    change_amount: int
    is_player_controlled: bool = False
    source: Optional[str] = None


class CombatantStatusChangedEvent(BaseGameEvent):
    event_type: Literal["combatant_status_changed"] = "combatant_status_changed"
    combatant_id: str
    combatant_name: str
    new_conditions: List[str]
    added_conditions: List[str] = Field(default_factory=list)
    removed_conditions: List[str] = Field(default_factory=list)
    is_defeated: bool = False


class CombatantAddedEvent(BaseGameEvent):
    event_type: Literal["combatant_added"] = "combatant_added"
    combatant_id: str
    combatant_name: str
    hp: int
    max_hp: int
    ac: int
    is_player_controlled: bool = False
    position_in_order: Optional[int] = None


class CombatantRemovedEvent(BaseGameEvent):
    event_type: Literal["combatant_removed"] = "combatant_removed"
    combatant_id: str
    combatant_name: str
    reason: str  # "defeated", "fled", "narrative"


# ===== INITIATIVE EVENTS =====


class CombatantInitiativeSetEvent(BaseGameEvent):
    event_type: Literal["combatant_initiative_set"] = "combatant_initiative_set"
    combatant_id: str
    combatant_name: str
    initiative_value: int
    roll_details: Optional[str] = None


class InitiativeOrderDeterminedEvent(BaseGameEvent):
    event_type: Literal["initiative_order_determined"] = "initiative_order_determined"
    ordered_combatants: List[CombatantModel]


# ===== DICE ROLL EVENTS =====


class PlayerDiceRequestAddedEvent(BaseGameEvent):
    event_type: Literal["player_dice_request_added"] = "player_dice_request_added"
    request_id: str
    character_id: str
    character_name: str
    roll_type: str  # "attack", "damage", "saving_throw", etc.
    dice_formula: str
    purpose: str
    dc: Optional[int] = None
    skill: Optional[str] = None
    ability: Optional[str] = None


class PlayerDiceRequestsClearedEvent(BaseGameEvent):
    event_type: Literal["player_dice_requests_cleared"] = "player_dice_requests_cleared"
    cleared_request_ids: List[str]


class NpcDiceRollProcessedEvent(BaseGameEvent):
    event_type: Literal["npc_dice_roll_processed"] = "npc_dice_roll_processed"
    character_id: str
    character_name: str
    roll_type: str
    dice_formula: str
    total: int
    details: str
    success: Optional[bool] = None
    purpose: str


# ===== GAME STATE EVENTS =====


class LocationChangedEvent(BaseGameEvent):
    event_type: Literal["location_changed"] = "location_changed"
    new_location_name: str
    new_location_description: str
    old_location_name: Optional[str] = None


class PartyMemberUpdatedEvent(BaseGameEvent):
    event_type: Literal["party_member_updated"] = "party_member_updated"
    character_id: str
    character_name: str
    changes: CharacterChangesModel
    gold_source: Optional[str] = None  # Source of gold change if applicable


# ===== SYSTEM EVENTS =====


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


# ===== QUEST AND STORY EVENTS =====


class QuestUpdatedEvent(BaseGameEvent):
    """Event emitted when a quest status changes."""

    event_type: Literal["quest_updated"] = "quest_updated"

    quest_id: str
    quest_title: str
    new_status: str  # "active", "completed", "failed"
    old_status: Optional[str] = None
    description_update: Optional[str] = None


class ItemAddedEvent(BaseGameEvent):
    """Event emitted when item is added to inventory."""

    event_type: Literal["item_added"] = "item_added"

    character_id: str
    character_name: str
    item_name: str
    quantity: int = 1
    item_description: Optional[str] = None
    item_value: Optional[int] = None  # Value in gold pieces
    item_rarity: Optional[str] = None  # common, uncommon, rare, etc.
