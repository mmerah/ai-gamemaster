"""
Game state and action models.

This module contains game state, chat, and action-related models.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .campaign import CampaignInstanceModel
from .character import CharacterInstanceModel, CombinedCharacterModel
from .combat import CombatInfoResponseModel, CombatStateModel
from .dice import (
    DiceRequestModel,
    DiceRollResultResponseModel,
    DiceSubmissionEventModel,
)
from .utils import LocationModel, NPCModel, QuestModel


class ChatMessageModel(BaseModel):
    """Core game model for chat history messages."""

    id: str = Field(..., description="Unique message identifier")
    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message role"
    )
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    is_dice_result: Optional[bool] = Field(
        False, description="Whether message represents dice roll results"
    )
    gm_thought: Optional[str] = Field(
        None, description="GM's internal thought or reasoning"
    )
    ai_response_json: Optional[str] = Field(
        None, description="Full AI response in JSON format"
    )
    detailed_content: Optional[str] = Field(
        None, description="Detailed content for expandable messages"
    )
    audio_path: Optional[str] = Field(None, description="Path to audio file for TTS")

    model_config = ConfigDict(extra="forbid")


class GameStateModel(BaseModel):
    """Complete game state matching the active game structure."""

    # Versioning
    version: int = Field(default=1, description="Save format version")

    # Campaign identity
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None

    # Campaign-specific context
    active_ruleset_id: Optional[str] = None
    active_lore_id: Optional[str] = None
    event_log_path: Optional[str] = None

    # Party state - using CharacterInstanceModel
    party: Dict[str, CharacterInstanceModel] = Field(default_factory=dict)

    # Location
    current_location: LocationModel = Field(
        default_factory=lambda: LocationModel(name="Unknown", description="")
    )

    # Chat and dice - properly typed
    chat_history: List[ChatMessageModel] = Field(default_factory=list)
    pending_player_dice_requests: List[DiceRequestModel] = Field(default_factory=list)

    # Combat
    combat: CombatStateModel = Field(default_factory=CombatStateModel)

    # Campaign context
    campaign_goal: str = "No specific goal set."
    known_npcs: Dict[str, NPCModel] = Field(default_factory=dict)
    active_quests: Dict[str, QuestModel] = Field(default_factory=dict)
    world_lore: List[str] = Field(default_factory=list)
    event_summary: List[str] = Field(default_factory=list)

    # Session tracking
    session_count: int = 0
    in_combat: bool = False
    last_event_id: Optional[str] = None

    # TTS Settings (game session override - highest priority)
    narration_enabled: bool = Field(
        default=False, description="Current game session narration setting"
    )
    tts_voice: str = Field(
        default="af_heart", description="Current game session TTS voice"
    )

    # Private fields (excluded from serialization)
    _pending_npc_roll_results: List[Any] = []  # Can be DiceRollResultModel or dict
    _last_rag_context: Optional[str] = None

    @field_validator("chat_history", mode="before")
    def validate_chat_history(cls, v: object) -> List[ChatMessageModel]:
        """Convert chat history dict to ChatMessageModel objects."""
        if not v:
            return []

        if not isinstance(v, list):
            return []

        result: List[ChatMessageModel] = []
        for item in v:
            if isinstance(item, dict):
                # Add defaults for required fields if missing
                if "id" not in item:
                    item["id"] = f"msg_{uuid4()}"
                if "timestamp" not in item:
                    item["timestamp"] = datetime.now(timezone.utc).isoformat()
                result.append(ChatMessageModel(**item))
            else:
                result.append(item)
        return result

    @field_validator("pending_player_dice_requests", mode="before")
    def validate_dice_requests(cls, v: object) -> List[DiceRequestModel]:
        """Convert dice request dicts to DiceRequestModel objects."""
        if not v:
            return []

        if not isinstance(v, list):
            return []

        result = []
        for item in v:
            if isinstance(item, dict):
                result.append(DiceRequestModel(**item))
            else:
                result.append(item)
        return result

    model_config = ConfigDict(extra="forbid")


class PlayerActionEventModel(BaseModel):
    """Player action event data."""

    action_type: str = Field(..., description="Action type (e.g., 'free_text')")
    value: str = Field(..., description="The actual action text")
    character_id: Optional[str] = Field(None, description="Optional character ID")

    model_config = ConfigDict(extra="forbid")


class GameEventModel(BaseModel):
    """Base game event structure."""

    type: Literal["player_action", "dice_submission", "next_step", "retry"] = Field(
        ..., description="Event type"
    )
    data: Union[PlayerActionEventModel, DiceSubmissionEventModel, Dict[str, str]] = (
        Field(..., description="Event-specific data")
    )
    session_id: Optional[str] = Field(None, description="Optional session ID")

    model_config = ConfigDict(extra="forbid")


class AIRequestContextModel(BaseModel):
    """Context stored for AI request retry."""

    messages: List[Dict[str, str]] = Field(
        ..., description="Chat messages for AI context"
    )
    initial_instruction: Optional[str] = Field(
        None, description="Initial system instruction"
    )

    model_config = ConfigDict(extra="forbid")


class GameEventResponseModel(BaseModel):
    """Response model from game event handling."""

    # Game state data
    party: List[CombinedCharacterModel] = Field(..., description="Party members data")
    location: str = Field(..., description="Current location name")
    location_description: str = Field(..., description="Location description")
    chat_history: List[ChatMessageModel] = Field(..., description="Chat messages")
    dice_requests: List[DiceRequestModel] = Field(
        ..., description="Pending dice requests"
    )
    combat_info: Optional[CombatInfoResponseModel] = Field(
        None, description="Combat state info"
    )

    # Response metadata
    error: Optional[str] = Field(None, description="Error message if any")
    success: Optional[bool] = Field(None, description="Whether operation succeeded")
    message: Optional[str] = Field(None, description="Status message")
    needs_backend_trigger: Optional[bool] = Field(
        None, description="Whether backend should auto-trigger"
    )
    status_code: Optional[int] = Field(None, description="HTTP status code")
    can_retry_last_request: Optional[bool] = Field(
        None, description="Whether retry is available"
    )
    submitted_roll_results: Optional[List[DiceRollResultResponseModel]] = Field(
        None, description="Dice submission results"
    )

    model_config = ConfigDict(extra="forbid")
