"""
Dice roll event models.

This module contains events related to dice rolling and requests.
"""

from typing import List, Literal, Optional

from app.models.events.base import BaseGameEvent


class PlayerDiceRequestAddedEvent(BaseGameEvent):
    event_type: Literal["player_dice_request_added"] = "player_dice_request_added"
    request_id: str
    character_id: str
    character_name: str
    roll_type: str  # "attack", "damage", "saving_throw", etc.
    dice_formula: str
    purpose: str
    dc: Optional[int] = None
    skill: Optional[str] = None
    ability: Optional[str] = None


class PlayerDiceRequestsClearedEvent(BaseGameEvent):
    event_type: Literal["player_dice_requests_cleared"] = "player_dice_requests_cleared"
    cleared_request_ids: List[str]


class NpcDiceRollProcessedEvent(BaseGameEvent):
    event_type: Literal["npc_dice_roll_processed"] = "npc_dice_roll_processed"
    character_id: str
    character_name: str
    roll_type: str
    dice_formula: str
    total: int
    details: str
    success: Optional[bool] = None
    purpose: str
