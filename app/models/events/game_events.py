"""
Game event models.

This module contains models for game events including requests and responses.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from app.models.character.combined import CombinedCharacterModel
from app.models.combat.response import CombatInfoResponseModel
from app.models.common import MessageDict
from app.models.dice import (
    DiceRequestModel,
    DiceRollResultResponseModel,
    DiceSubmissionEventModel,
)
from app.models.events.event_types import GameEventType
from app.models.shared import ChatMessageModel


class PlayerActionEventModel(BaseModel):
    """Player action event data."""

    action_type: str = Field(..., description="Action type (e.g., 'free_text')")
    value: str = Field(..., description="The actual action text")
    character_id: Optional[str] = Field(None, description="Optional character ID")

    model_config = ConfigDict(extra="forbid")


class GameEventModel(BaseModel):
    """Base game event structure."""

    type: GameEventType = Field(..., description="Event type")
    data: Union[PlayerActionEventModel, DiceSubmissionEventModel, Dict[str, Any]] = (
        Field(..., description="Event-specific data")
    )

    model_config = ConfigDict(extra="forbid")


class AIRequestContextModel(BaseModel):
    """Context stored for AI request retry."""

    messages: List[MessageDict] = Field(..., description="Chat messages for AI context")
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
