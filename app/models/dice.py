"""
Dice models.

This module contains all dice roll-related models.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DiceExecutionModel(BaseModel):
    """Internal model for dice roll execution results."""

    # Success fields
    total: Optional[int] = Field(None, description="Total result of the roll")
    individual_rolls: Optional[List[int]] = Field(
        None, description="Individual die results"
    )
    formula_description: Optional[str] = Field(
        None, description="Human-readable formula description"
    )

    # Error field
    error: Optional[str] = Field(None, description="Error message if roll failed")

    @property
    def is_error(self) -> bool:
        """Check if this represents an error result."""
        return self.error is not None

    model_config = ConfigDict(extra="forbid")


class DiceRollSubmissionModel(BaseModel):
    """Dice roll submission from frontend."""

    character_id: str = Field(..., description="ID of the character rolling")
    roll_type: str = Field(..., description="Type of roll")
    dice_formula: str = Field(..., description="Dice formula")
    request_id: Optional[str] = Field(
        None, description="Request ID if responding to a request"
    )
    total: Optional[int] = Field(None, description="Optional pre-calculated total")
    skill: Optional[str] = Field(None, description="Skill name for skill checks")
    ability: Optional[str] = Field(None, description="Ability name for ability checks")
    dc: Optional[int] = Field(None, description="Difficulty class")
    reason: Optional[str] = Field(None, description="Reason for the roll")
    character_name: Optional[str] = Field(
        None, description="Character name (sometimes included)"
    )

    model_config = ConfigDict(extra="forbid")


class DiceSubmissionEventModel(BaseModel):
    """Dice submission event data."""

    rolls: List[DiceRollSubmissionModel] = Field(..., description="List of dice rolls")

    model_config = ConfigDict(extra="forbid")


class DiceRequestModel(BaseModel):
    """Core game model for dice roll requests."""

    request_id: str = Field(
        ..., description="Unique ID for this specific roll request instance."
    )
    character_ids: List[str] = Field(
        ..., description="List of character IDs required to roll."
    )
    type: str = Field(
        ...,
        description="Type of roll (e.g., 'skill_check', 'saving_throw', 'initiative').",
    )
    dice_formula: str = Field(
        ..., description="Base dice formula (e.g., '1d20', '2d6+3')."
    )
    reason: str = Field(
        ..., description="Brief explanation for the roll shown to the player."
    )
    skill: Optional[str] = Field(
        None, description="Specific skill if type is 'skill_check'."
    )
    ability: Optional[str] = Field(
        None, description="Specific ability score if type is 'saving_throw' or related."
    )
    dc: Optional[int] = Field(None, description="Difficulty Class if applicable.")

    model_config = ConfigDict(extra="forbid")


class DiceRollMessageModel(BaseModel):
    """Formatted dice roll messages."""

    detailed: str = Field(..., description="Detailed roll message with all information")
    summary: str = Field(..., description="Brief summary of the roll result")

    model_config = ConfigDict(extra="forbid")


class DiceRollResultResponseModel(BaseModel):
    """Response model for dice roll results."""

    request_id: str = Field(..., description="Request identifier")
    character_id: str = Field(..., description="Character who rolled")
    character_name: str = Field(..., description="Character name")
    roll_type: str = Field(..., description="Type of roll")
    dice_formula: str = Field(..., description="Dice formula used")
    character_modifier: int = Field(..., description="Character modifier applied")
    total_result: int = Field(..., description="Total result of roll")
    dc: Optional[int] = Field(None, description="Difficulty class if applicable")
    success: Optional[bool] = Field(None, description="Whether roll succeeded")
    reason: str = Field(..., description="Reason for roll")
    result_message: str = Field(..., description="Detailed result message")
    result_summary: str = Field(..., description="Brief result summary")
    error: Optional[str] = Field(None, description="Error message if roll failed")

    model_config = ConfigDict(extra="forbid")
