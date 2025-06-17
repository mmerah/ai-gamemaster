"""State processors for game state updates.

This module contains focused processors for handling different aspects of game state updates,
following the Single Responsibility Principle.
"""

from .combat_condition_processor import CombatConditionProcessor
from .combat_helpers import add_combatants_to_active_combat, add_combatants_to_state
from .combat_hp_processor import CombatHPProcessor
from .combat_state_processor import CombatStateProcessor
from .inventory_state_processor import InventoryStateProcessor
from .quest_state_processor import QuestStateProcessor
from .utils import get_correlation_id, get_target_ids_for_update

__all__ = [
    # Main processors
    "CombatStateProcessor",
    "InventoryStateProcessor",
    "QuestStateProcessor",
    # Combat sub-processors
    "CombatConditionProcessor",
    "CombatHPProcessor",
    # Helper functions
    "add_combatants_to_state",
    "add_combatants_to_active_combat",
    "get_correlation_id",
    "get_target_ids_for_update",
]
