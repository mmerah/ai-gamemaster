"""
Combat event models.

This module contains events related to combat and combatants.
"""

from typing import List, Literal, Optional

from pydantic import Field

from app.models.combat.combatant import CombatantModel
from app.models.events.base import BaseGameEvent

# ===== COMBAT CONTROL EVENTS =====


class CombatStartedEvent(BaseGameEvent):
    event_type: Literal["combat_started"] = "combat_started"
    combatants: List[CombatantModel]  # Typed combatant models for type safety
    round_number: int = 1


class CombatEndedEvent(BaseGameEvent):
    event_type: Literal["combat_ended"] = "combat_ended"
    reason: str  # "victory", "retreat", "narrative"
    outcome_description: Optional[str] = None


class TurnAdvancedEvent(BaseGameEvent):
    event_type: Literal["turn_advanced"] = "turn_advanced"
    new_combatant_id: str
    new_combatant_name: str
    round_number: int
    is_new_round: bool = False
    is_player_controlled: bool = False


# ===== COMBATANT STATE EVENTS =====


class CombatantHpChangedEvent(BaseGameEvent):
    event_type: Literal["combatant_hp_changed"] = "combatant_hp_changed"
    combatant_id: str
    combatant_name: str
    old_hp: int
    new_hp: int
    max_hp: int
    change_amount: int
    is_player_controlled: bool = False
    source: Optional[str] = None


class CombatantStatusChangedEvent(BaseGameEvent):
    event_type: Literal["combatant_status_changed"] = "combatant_status_changed"
    combatant_id: str
    combatant_name: str
    new_conditions: List[str]
    added_conditions: List[str] = Field(default_factory=list)
    removed_conditions: List[str] = Field(default_factory=list)
    is_defeated: bool = False


class CombatantAddedEvent(BaseGameEvent):
    event_type: Literal["combatant_added"] = "combatant_added"
    combatant_id: str
    combatant_name: str
    hp: int
    max_hp: int
    ac: int
    is_player_controlled: bool = False
    position_in_order: Optional[int] = None


class CombatantRemovedEvent(BaseGameEvent):
    event_type: Literal["combatant_removed"] = "combatant_removed"
    combatant_id: str
    combatant_name: str
    reason: str  # "defeated", "fled", "narrative"


# ===== INITIATIVE EVENTS =====


class CombatantInitiativeSetEvent(BaseGameEvent):
    event_type: Literal["combatant_initiative_set"] = "combatant_initiative_set"
    combatant_id: str
    combatant_name: str
    initiative_value: int
    roll_details: Optional[str] = None


class InitiativeOrderDeterminedEvent(BaseGameEvent):
    event_type: Literal["initiative_order_determined"] = "initiative_order_determined"
    ordered_combatants: List[CombatantModel]
