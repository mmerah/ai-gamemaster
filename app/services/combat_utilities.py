"""
Combat utility classes for validation and formatting.
"""
import logging
from typing import Dict, List
from app.core.interfaces import GameStateRepository

logger = logging.getLogger(__name__)


class CombatValidator:
    """Utility class for combat validation operations."""
    
    @staticmethod
    def is_combat_active(game_state_repo: GameStateRepository) -> bool:
        """Check if combat is currently active."""
        game_state = game_state_repo.get_game_state()
        return game_state.combat.is_active
    
    @staticmethod
    def is_valid_combatant_turn(character_id: str, game_state_repo: GameStateRepository) -> bool:
        """Check if it's a valid turn for the specified character."""
        game_state = game_state_repo.get_game_state()
        
        if not game_state.combat.is_active or not game_state.combat.combatants:
            return False
        
        if not (0 <= game_state.combat.current_turn_index < len(game_state.combat.combatants)):
            return False
        
        current_combatant = game_state.combat.combatants[game_state.combat.current_turn_index]
        return current_combatant.id == character_id
    
    @staticmethod
    def get_current_combatant_id(game_state_repo: GameStateRepository) -> str:
        """Get the ID of the current combatant."""
        game_state = game_state_repo.get_game_state()
        
        if (game_state.combat.is_active and game_state.combat.combatants and
            0 <= game_state.combat.current_turn_index < len(game_state.combat.combatants)):
            return game_state.combat.combatants[game_state.combat.current_turn_index].id
        
        return ""


class CombatFormatter:
    """Utility class for formatting combat information."""
    
    @staticmethod
    def format_initiative_order(combatants: List) -> str:
        """Format the initiative order for display."""
        if not combatants:
            return "No combatants in initiative order."
        
        order_items = [f"{c.name}: {c.initiative}" for c in combatants]
        return "Initiative Order: " + ", ".join(order_items)
    
    @staticmethod
    def format_combat_status(game_state_repo: GameStateRepository) -> Dict:
        """Format current combat status for display."""
        game_state = game_state_repo.get_game_state()
        
        if not game_state.combat.is_active:
            return {"is_active": False}
        
        current_combatant_name = "Unknown"
        current_combatant_id = "Unknown"
        
        if (game_state.combat.combatants and 
            0 <= game_state.combat.current_turn_index < len(game_state.combat.combatants)):
            current_combatant = game_state.combat.combatants[game_state.combat.current_turn_index]
            current_combatant_id = current_combatant.id
            current_combatant_name = current_combatant.name
        
        return {
            "is_active": True,
            "round": game_state.combat.round_number,
            "current_turn": current_combatant_name,
            "current_turn_id": current_combatant_id,
            "turn_order": [c.model_dump() for c in game_state.combat.combatants],
            "monster_status": {
                monster_id: stats.model_dump() if hasattr(stats, 'model_dump') else stats
                for monster_id, stats in game_state.combat.monster_stats.items()
            }
        }