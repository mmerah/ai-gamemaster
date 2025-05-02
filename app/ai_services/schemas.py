from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional, Union, Dict, Any

class DiceRequest(BaseModel):
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


class LocationUpdate(BaseModel):
    name: str = Field(..., description="The new name of the current location.")
    description: str = Field(
        ..., description="The updated description of the current location."
    )


class GameStateUpdate(BaseModel):
    # Define more specific update types later if needed
    type: str = Field(
        ..., description="Type of state update (e.g., 'condition_add', 'hp_change')."
    )
    character_id: str = Field(..., description="ID of the character affected.")
    # Use Union for flexibility in value (e.g., condition name or HP amount)
    value: Union[str, int, bool, None] = Field(
        ..., description="Value associated with the update."
    )
    # Optional extra details
    details: Optional[dict] = Field(
        None, description="Optional dictionary for extra details."
    )

class HPChangeUpdate(BaseModel):
    type: Literal["hp_change"] = "hp_change"
    character_id: str = Field(..., description="ID of the character (player or NPC) affected.")
    value: int = Field(..., description="The amount to change HP by (negative for damage, positive for healing).")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional details like {'source': 'Goblin Scimitar'}")

class ConditionUpdate(BaseModel):
    type: Literal["condition_add", "condition_remove"]
    character_id: str
    value: str = Field(..., description="The name of the condition (e.g., 'Poisoned', 'Prone').")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional details like {'duration': '1 minute'}")

class InventoryUpdate(BaseModel):
    type: Literal["inventory_add", "inventory_remove"]
    character_id: str
    value: Union[str, Dict] = Field(..., description="Item name (str) or an item object/dict.")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional details like {'quantity': 1}")

class GoldUpdate(BaseModel):
    type: Literal["gold_change"] = "gold_change"
    character_id: str # Could also be "party" for shared gold
    value: int = Field(..., description="Amount of gold to add (positive) or remove (negative).")

class CombatStartUpdate(BaseModel):
    type: Literal["combat_start"] = "combat_start"
    # AI provides initial list of non-player combatants it introduces
    combatants: List[Dict] = Field(..., description="List of NPC/monster combatants with basic stats (id, name, hp, ac). Players added automatically.")
    details: Optional[Dict[str, Any]] = None

class CombatEndUpdate(BaseModel):
    type: Literal["combat_end"] = "combat_end"
    details: Optional[Dict[str, Any]] = Field(None, description="Optional reason for combat ending.")

# Use Union for the GameStateUpdate field in AIResponse
GameStateUpdate = Union[
    HPChangeUpdate,
    ConditionUpdate,
    InventoryUpdate,
    GoldUpdate,
    CombatStartUpdate,
    CombatEndUpdate,
    # Keep generic one for flexibility or add more specific types
    # GenericUpdate? (type: str, character_id: str, value: Any, details: Optional[dict])
]

class AIResponse(BaseModel):
    """
    The structured response from the AI Game Master, detailing the narrative,
    player options, required dice rolls, and any game state changes.
    """
    reasoning: Optional[str] = Field(
        None,
        description="Explain the step-by-step thought process behind the provided values (narrative, rolls, updates). Include key considerations, interpretations of rules or player actions, and how they influenced the final decisions. This is for internal review and not shown directly to the player.",
    )
    narrative: str = Field(
        ...,
        description="The descriptive text detailing the current situation, results of actions, or NPC dialogue.",
    )
    dice_requests: List[DiceRequest] = Field(
        default_factory=list,
        description="List of dice rolls required before the player can act further. Empty list ([]) if no rolls needed now.",
    )
    location_update: Optional[LocationUpdate] = Field(
        None, description="Details of the new location, if it changed. Use null if no change."
    )
    game_state_updates: List[GameStateUpdate] = Field(
        default_factory=list,
        description="List of specific game state changes triggered by the AI's response (e.g., HP changes, conditions, combat start/end). Empty list ([]) if no state changes.",
    )
    end_turn: Optional[bool] = Field(
        None, # Default to None (meaning omitted/not applicable)
        description="**CRITICAL (Combat Only):** Set to `true` ONLY if the combatant whose turn it currently is (indicated in the context) has fully completed ALL their actions/rolls for this turn, and the turn should pass to the next combatant. Set to `false` if the current combatant still needs to act/roll. Omit (`null`) if not in active combat or if unsure."
    )

    # # Optional validator to ensure end_turn isn't true if dice are requested?
    # @validator('end_turn')
    # def check_end_turn_with_dice(cls, v, values):
    #     if v and values.get('dice_requests'):
    #         # This might be too strict if AI needs a roll THEN ends turn in same response?
    #         # Let's allow it for now and rely on prompt instructions.
    #         # raise ValueError('end_turn cannot be true if dice_requests is not empty')
    #         pass
    #     return v
