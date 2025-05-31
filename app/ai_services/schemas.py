from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Union, Dict, Any

class InitialCombatantData(BaseModel):
    """Model for initial combatant data when starting combat."""
    id: str = Field(..., description="Unique identifier for the combatant")
    name: str = Field(..., description="Display name of the combatant")
    hp: int = Field(..., description="Starting hit points")
    ac: int = Field(..., description="Armor class")
    stats: Optional[Dict[str, int]] = Field(None, description="Ability scores (e.g., {'DEX': 14, 'STR': 12})")
    abilities: Optional[List[str]] = Field(None, description="Special abilities or features")
    attacks: Optional[List[Dict]] = Field(None, description="Available attacks and their properties")
    icon_path: Optional[str] = Field(None, description="Path to character portrait/icon")

class MonsterBaseStats(BaseModel):
    """Model for monster/NPC base statistics stored in combat state."""
    name: str = Field(..., description="Monster/NPC name")
    initial_hp: int = Field(..., description="Maximum hit points at start of combat")
    ac: int = Field(..., description="Armor class")
    stats: Optional[Dict[str, int]] = Field(None, description="Ability scores (e.g., {'STR': 16, 'DEX': 14})")
    abilities: Optional[List[str]] = Field(None, description="Special abilities or features")
    attacks: Optional[List[Dict]] = Field(None, description="Available attacks and their properties")
    conditions_immune: Optional[List[str]] = Field(None, description="Conditions the creature is immune to")
    resistances: Optional[List[str]] = Field(None, description="Damage types the creature resists")
    vulnerabilities: Optional[List[str]] = Field(None, description="Damage types the creature is vulnerable to")


class ChatMessage(BaseModel):
    """Model for chat history messages with enhanced typing."""
    id: str = Field(..., description="Unique message identifier")
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    is_dice_result: Optional[bool] = Field(False, description="Whether message represents dice roll results")
    gm_thought: Optional[str] = Field(None, description="GM's internal thought or reasoning")
    ai_response_json: Optional[str] = Field(None, description="Full AI response in JSON format")
    detailed_content: Optional[str] = Field(None, description="Detailed content for expandable messages")
    audio_path: Optional[str] = Field(None, description="Path to audio file for TTS")

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


class DiceRollResult(BaseModel):
    """Model for dice roll results with enhanced typing."""
    character_id: str = Field(..., description="ID of the character who rolled")
    roll_type: str = Field(..., description="Type of roll (e.g., 'attack', 'damage', 'skill_check')")
    total: int = Field(..., description="Total result of the roll")
    result_summary: str = Field(..., description="Brief summary of the roll (e.g., 'Elara: Attack Roll = 18')")
    result_message: Optional[str] = Field(None, description="Detailed message about the roll")
    skill: Optional[str] = Field(None, description="Skill name if this was a skill check")
    ability: Optional[str] = Field(None, description="Ability name if this was an ability check")
    dc: Optional[int] = Field(None, description="Difficulty class if applicable")
    reason: Optional[str] = Field(None, description="Reason for the roll")
    original_request_id: Optional[str] = Field(None, description="ID of the original request that triggered this roll")


class PlayerAction(BaseModel):
    """Model for player action data with enhanced typing."""
    action_type: str = Field(..., description="Type of action (e.g., 'free_text')")
    value: str = Field(..., description="The content/value of the action")


class DiceSubmissionData(BaseModel):
    """Model for individual dice submission data."""
    character_id: str = Field(..., description="ID of the character rolling")
    roll_type: str = Field(..., description="Type of roll")
    dice_formula: str = Field(..., description="Dice formula to roll")
    reason: Optional[str] = Field(None, description="Reason for the roll")
    request_id: Optional[str] = Field(None, description="ID of the request that triggered this roll")


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
    character_id: str = Field(..., description="ID of the character getting the condition update.")
    value: str = Field(..., description="The name of the condition (e.g., 'Poisoned', 'Prone').")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional details like {'duration': '1 minute'}")

class InventoryUpdate(BaseModel):
    type: Literal["inventory_add", "inventory_remove"]
    character_id: str = Field(..., description="ID of the character receiving or losing the item.")
    value: Union[str, Dict] = Field(..., description="Item name (str) or an item object/dict.")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional details like {'quantity': 1}")

class GoldUpdate(BaseModel):
    type: Literal["gold_change"] = "gold_change"
    character_id: str = Field(..., description="ID of the character changing gold. Can be 'all' or 'party'")
    value: int = Field(..., description="Amount of gold to add (positive) or remove (negative).")

class QuestUpdate(BaseModel):
    type: Literal["quest_update"] = "quest_update"
    quest_id: str = Field(..., description="The ID of the quest being updated (must exist in game state).")
    # Allow updating status or adding details
    status: Optional[Literal["active", "completed", "failed"]] = Field(None, description="Optional: The new status of the quest.")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional: A dictionary of details to add or update for the quest (e.g., {'clue_found': 'Rune Token'}). Merged with existing details.")

class CombatStartUpdate(BaseModel):
    type: Literal["combat_start"] = "combat_start"
    # AI provides initial list of non-player combatants it introduces
    combatants: List[InitialCombatantData] = Field(..., description="List of NPC/monster combatants with basic stats. Players added automatically.")
    details: Optional[Dict[str, Any]] = None

class CombatEndUpdate(BaseModel):
    type: Literal["combat_end"] = "combat_end"
    details: Optional[Dict[str, Any]] = Field(None, description="Optional reason for combat ending.")

class CombatantRemoveUpdate(BaseModel):
    type: Literal["combatant_remove"] = "combatant_remove"
    character_id: str = Field(..., description="ID of the combatant (player or NPC) to remove from combat (e.g., fled, banished).")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional details like {'reason': 'Fled the scene'}")

# Use Union for the GameStateUpdate field in AIResponse
GameStateUpdate = Union[
    HPChangeUpdate,
    ConditionUpdate,
    InventoryUpdate,
    GoldUpdate,
    CombatStartUpdate,
    CombatEndUpdate,
    CombatantRemoveUpdate,
    QuestUpdate
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
