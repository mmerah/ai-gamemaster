"""
Event utility models.

This module contains utility models used by various event types.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


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
