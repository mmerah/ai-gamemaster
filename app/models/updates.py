"""
Update models and type definitions.

This module contains all game state update models and validation types.
"""

from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from app.models.combat import InitialCombatantData
from app.models.utils import ItemModel


class HPChangeUpdateModel(BaseModel):
    """Core game model for HP change updates."""

    character_id: str = Field(
        ..., description="ID of the character (player or NPC) affected."
    )
    value: int = Field(
        ...,
        description="The amount to change HP by (negative for damage, positive for healing).",
    )
    # Flattened combat details (previously in details dict)
    attacker: Optional[str] = Field(None, description="ID or name of the attacker")
    weapon: Optional[str] = Field(None, description="Weapon or spell used")
    damage_type: Optional[str] = Field(None, description="Type of damage dealt")
    critical: Optional[bool] = Field(
        None, description="Whether this was a critical hit"
    )
    source: Optional[str] = Field(None, description="Source of the HP change")
    reason: Optional[str] = Field(None, description="Reason for the HP change")
    description: Optional[str] = Field(None, description="Additional description")

    model_config = ConfigDict(extra="forbid")


class ConditionAddUpdateModel(BaseModel):
    """Core game model for adding conditions."""

    character_id: str = Field(
        ..., description="ID of the character getting the condition."
    )
    value: str = Field(
        ..., description="The name of the condition to add (e.g., 'Poisoned', 'Prone')."
    )
    # Flattened condition details (previously in details dict)
    duration: Optional[str] = Field(None, description="Duration of the condition")
    save_dc: Optional[int] = Field(
        None, description="DC for saving throw to end condition"
    )
    save_type: Optional[str] = Field(None, description="Type of saving throw needed")
    source: Optional[str] = Field(None, description="Source of the condition")
    reason: Optional[str] = Field(None, description="Reason for adding the condition")
    description: Optional[str] = Field(None, description="Additional description")

    model_config = ConfigDict(extra="forbid")


class ConditionRemoveUpdateModel(BaseModel):
    """Core game model for removing conditions."""

    character_id: str = Field(
        ..., description="ID of the character losing the condition."
    )
    value: str = Field(
        ...,
        description="The name of the condition to remove (e.g., 'Poisoned', 'Prone').",
    )

    model_config = ConfigDict(extra="forbid")


class InventoryAddUpdateModel(BaseModel):
    """Core game model for adding items to inventory."""

    character_id: str = Field(
        ..., description="ID of the character receiving the item."
    )
    value: Union[str, ItemModel] = Field(
        ..., description="Item name (str) or an item object (ItemModel)."
    )
    # Flattened item details (previously in details dict)
    quantity: Optional[int] = Field(None, description="Quantity of items to add")
    item_value: Optional[int] = Field(
        None, description="Value of the item in gold pieces"
    )
    rarity: Optional[str] = Field(None, description="Rarity of the item")
    source: Optional[str] = Field(None, description="Source of the item")
    reason: Optional[str] = Field(None, description="Reason for adding the item")
    description: Optional[str] = Field(None, description="Additional description")

    model_config = ConfigDict(extra="forbid")


class InventoryRemoveUpdateModel(BaseModel):
    """Core game model for removing items from inventory."""

    character_id: str = Field(..., description="ID of the character losing the item.")
    value: str = Field(..., description="Item name or item ID to remove.")

    model_config = ConfigDict(extra="forbid")


class GoldUpdateModel(BaseModel):
    """Core game model for gold updates."""

    character_id: str = Field(
        ..., description="ID of the character changing gold. Can be 'all' or 'party'"
    )
    value: int = Field(
        ..., description="Amount of gold to add (positive) or remove (negative)."
    )
    # Flattened details (previously in details dict)
    source: Optional[str] = Field(None, description="Source of the gold change")
    reason: Optional[str] = Field(None, description="Reason for the gold change")
    description: Optional[str] = Field(None, description="Additional description")

    model_config = ConfigDict(extra="forbid")


class LocationUpdateModel(BaseModel):
    """Core game model for location updates."""

    name: str = Field(..., description="The new name of the current location.")
    description: str = Field(
        ..., description="The updated description of the current location."
    )

    model_config = ConfigDict(extra="forbid")


class CombatStartUpdateModel(BaseModel):
    """Core game model for combat start updates."""

    combatants: List[InitialCombatantData] = Field(
        ...,
        description="List of NPC/monster combatants with basic stats. Players added automatically.",
    )
    # Flattened details (previously in details dict)
    source: Optional[str] = Field(None, description="Source of combat initiation")
    reason: Optional[str] = Field(None, description="Reason for starting combat")
    description: Optional[str] = Field(None, description="Additional description")

    model_config = ConfigDict(extra="forbid")


class CombatEndUpdateModel(BaseModel):
    """Core game model for combat end updates."""

    # Flattened details (previously in details dict)
    source: Optional[str] = Field(None, description="Source of combat ending")
    reason: Optional[str] = Field(None, description="Reason for ending combat")
    description: Optional[str] = Field(None, description="Additional description")

    model_config = ConfigDict(extra="forbid")


class CombatantRemoveUpdateModel(BaseModel):
    """Core game model for combatant removal updates."""

    character_id: str = Field(
        ..., description="ID of the combatant (player or NPC) to remove from combat."
    )
    # Flattened details (previously in details dict)
    source: Optional[str] = Field(None, description="Source of removal")
    reason: Optional[str] = Field(None, description="Reason for removing combatant")
    description: Optional[str] = Field(None, description="Additional description")

    model_config = ConfigDict(extra="forbid")


class QuestUpdateModel(BaseModel):
    """Core game model for quest updates."""

    quest_id: str = Field(
        ..., description="The ID of the quest being updated (must exist in game state)."
    )
    status: Optional[Literal["active", "completed", "failed"]] = Field(
        None, description="Optional: The new status of the quest."
    )
    # Flattened quest details (previously in details dict)
    objectives_completed: Optional[int] = Field(
        None, description="Number of objectives completed"
    )
    objectives_total: Optional[int] = Field(
        None, description="Total number of objectives"
    )
    rewards_experience: Optional[int] = Field(
        None, description="Experience points rewarded"
    )
    rewards_gold: Optional[int] = Field(None, description="Gold rewarded")
    rewards_items: Optional[List[str]] = Field(None, description="Items rewarded")
    rewards_reputation: Optional[str] = Field(None, description="Reputation change")
    source: Optional[str] = Field(None, description="Source of quest update")
    reason: Optional[str] = Field(None, description="Reason for quest update")
    description: Optional[str] = Field(None, description="Additional description")

    model_config = ConfigDict(extra="forbid")


# Forward references
from typing import List

__all__ = [
    # Pydantic models
    "HPChangeUpdateModel",
    "ConditionAddUpdateModel",
    "ConditionRemoveUpdateModel",
    "InventoryAddUpdateModel",
    "InventoryRemoveUpdateModel",
    "GoldUpdateModel",
    "LocationUpdateModel",
    "CombatStartUpdateModel",
    "CombatEndUpdateModel",
    "CombatantRemoveUpdateModel",
    "QuestUpdateModel",
]
