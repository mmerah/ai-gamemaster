from typing import List, Optional

from pydantic import BaseModel, Field

# Import core game models from new model locations
from app.models.models import DiceRequestModel
from app.models.updates import (
    CombatantRemoveUpdateModel,
    CombatEndUpdateModel,
    CombatStartUpdateModel,
    ConditionAddUpdateModel,
    ConditionRemoveUpdateModel,
    GoldUpdateModel,
    HPChangeUpdateModel,
    InventoryAddUpdateModel,
    InventoryRemoveUpdateModel,
    LocationUpdateModel,
    QuestUpdateModel,
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
    dice_requests: List[DiceRequestModel] = Field(
        default_factory=list,
        description="List of dice rolls required before the player can act further. Empty list ([]) if no rolls needed now.",
    )
    # Specific typed state update fields (replacing generic game_state_updates)
    location_update: Optional[LocationUpdateModel] = Field(
        None,
        description="Details of the new location, if it changed. Use null if no change.",
    )
    hp_changes: List[HPChangeUpdateModel] = Field(
        default_factory=list,
        description="List of HP changes to apply (damage or healing). Empty list ([]) if no HP changes.",
    )
    condition_adds: List[ConditionAddUpdateModel] = Field(
        default_factory=list,
        description="List of conditions to add. Empty list ([]) if no conditions to add.",
    )
    condition_removes: List[ConditionRemoveUpdateModel] = Field(
        default_factory=list,
        description="List of conditions to remove. Empty list ([]) if no conditions to remove.",
    )
    inventory_adds: List[InventoryAddUpdateModel] = Field(
        default_factory=list,
        description="List of items to add to inventory. Empty list ([]) if no items to add.",
    )
    inventory_removes: List[InventoryRemoveUpdateModel] = Field(
        default_factory=list,
        description="List of items to remove from inventory. Empty list ([]) if no items to remove.",
    )
    gold_changes: List[GoldUpdateModel] = Field(
        default_factory=list,
        description="List of gold changes. Empty list ([]) if no gold changes.",
    )
    combat_start: Optional[CombatStartUpdateModel] = Field(
        None, description="Combat initiation details. Use null if not starting combat."
    )
    combat_end: Optional[CombatEndUpdateModel] = Field(
        None, description="Combat end details. Use null if not ending combat."
    )
    combatant_removals: List[CombatantRemoveUpdateModel] = Field(
        default_factory=list,
        description="List of combatants to remove from combat. Empty list ([]) if no removals.",
    )
    quest_updates: List[QuestUpdateModel] = Field(
        default_factory=list,
        description="List of quest status updates. Empty list ([]) if no quest changes.",
    )
    end_turn: Optional[bool] = Field(
        None,  # Default to None (meaning omitted/not applicable)
        description="**CRITICAL (Combat Only):** Set to `true` ONLY if the combatant whose turn it currently is (indicated in the context) has fully completed ALL their actions/rolls for this turn, and the turn should pass to the next combatant. Set to `false` if the current combatant still needs to act/roll. Omit (`null`) if not in active combat or if unsure.",
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
