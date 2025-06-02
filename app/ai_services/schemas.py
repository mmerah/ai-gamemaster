from pydantic import BaseModel, Field
from typing import List, Optional

# Import core game models from unified_models
from app.game.unified_models import (
    DiceRequest, LocationUpdate, GameStateUpdate
)

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
