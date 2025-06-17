"""
Combat response models.

This module contains DTOs for combat information responses.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.combat.combatant import CombatantModel


class CombatInfoResponseModel(BaseModel):
    """Combat information response model for frontend display."""

    is_active: bool = Field(..., description="Whether combat is currently active")
    round_number: int = Field(default=0, description="Current combat round")
    current_combatant_id: Optional[str] = Field(
        None, description="ID of current combatant"
    )
    current_combatant_name: Optional[str] = Field(
        None, description="Name of current combatant"
    )
    combatants: List[CombatantModel] = Field(
        default_factory=list, description="List of combatants"
    )
    turn_order: List[str] = Field(
        default_factory=list, description="Turn order by combatant ID"
    )

    model_config = ConfigDict(extra="forbid")
