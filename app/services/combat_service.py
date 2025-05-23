"""
Combat service implementation for managing combat operations.
"""
import logging
from typing import Dict, List
from app.core.interfaces import CombatService, GameStateRepository, CharacterService
from app.services.character_service import CharacterValidator
from app.game import utils

logger = logging.getLogger(__name__)


class CombatServiceImpl(CombatService):
    """Implementation of combat service."""
    
    def __init__(self, game_state_repo: GameStateRepository, character_service: CharacterService):
        self.game_state_repo = game_state_repo
        self.character_service = character_service
    
    def start_combat(self, combatants: List[Dict]) -> None:
        """Start a new combat encounter."""
        game_state = self.game_state_repo.get_game_state()
        
        if game_state.combat.is_active:
            logger.warning("Attempting to start combat while combat is already active.")
            return
        
        # Initialize combat state
        game_state.combat.is_active = True
        game_state.combat.round_number = 1
        game_state.combat.current_turn_index = 0
        game_state.combat.combatants = []
        game_state.combat.monster_stats = {}
        game_state.combat._combat_just_started_flag = True
        
        # Add combatants
        for combatant_data in combatants:
            self._add_combatant_to_combat(combatant_data, game_state)
        
        logger.info(f"Combat started with {len(game_state.combat.combatants)} combatants.")
    
    def end_combat(self) -> None:
        """End the current combat encounter."""
        game_state = self.game_state_repo.get_game_state()
        
        if not game_state.combat.is_active:
            logger.warning("Attempting to end combat when no combat is active.")
            return
        
        # Reset combat state
        game_state.combat.is_active = False
        game_state.combat.combatants = []
        game_state.combat.current_turn_index = 0
        game_state.combat.round_number = 1
        game_state.combat.monster_stats = {}
        game_state.combat._combat_just_started_flag = False
        
        # Clear any pending NPC roll results
        game_state._pending_npc_roll_results = []
        
        logger.info("Combat ended.")
    
    def advance_turn(self) -> None:
        """Advance to the next turn in combat."""
        game_state = self.game_state_repo.get_game_state()
        
        if not game_state.combat.is_active or not game_state.combat.combatants:
            logger.warning("Cannot advance turn: Combat not active or no combatants.")
            return
        
        original_index = game_state.combat.current_turn_index
        
        # Find next active combatant
        for _ in range(len(game_state.combat.combatants) + 1):
            game_state.combat.current_turn_index = (
                game_state.combat.current_turn_index + 1
            ) % len(game_state.combat.combatants)
            
            # Check if new round started
            if (game_state.combat.current_turn_index == 0 and 
                game_state.combat.current_turn_index != original_index):
                game_state.combat.round_number += 1
                logger.info(f"Advanced to Combat Round {game_state.combat.round_number}")
            
            current_combatant = game_state.combat.combatants[game_state.combat.current_turn_index]
            
            # Check if combatant is incapacitated
            if not CharacterValidator.is_character_incapacitated(
                current_combatant.id, self.game_state_repo
            ):
                logger.info(
                    f"Advanced turn. Current: {current_combatant.name} "
                    f"(Round {game_state.combat.round_number})"
                )
                return
            else:
                logger.debug(f"Skipping turn for incapacitated combatant: {current_combatant.name}")
        
        # If we get here, all combatants are incapacitated
        logger.warning("All combatants appear incapacitated. Auto-ending combat.")
        self._auto_end_combat_all_incapacitated()
    
    def determine_initiative_order(self, roll_results: List[Dict]) -> None:
        """Determine and set initiative order based on roll results."""
        game_state = self.game_state_repo.get_game_state()
        
        if not game_state.combat.is_active or not game_state.combat.combatants:
            logger.error("Cannot determine initiative: Combat not active or no combatants.")
            return
        
        logger.info("Determining initiative order...")
        
        # Map roll results to combatants
        initiative_map = {
            r["character_id"]: r["total_result"]
            for r in roll_results if r.get("roll_type") == "initiative"
        }
        
        initiative_messages = []
        
        # Update initiative values
        for combatant in game_state.combat.combatants:
            if combatant.id in initiative_map:
                combatant.initiative = initiative_map[combatant.id]
                roll_for_c = next(
                    (r for r in roll_results 
                     if r.get("character_id") == combatant.id and r.get("roll_type") == "initiative"), 
                    None
                )
                if roll_for_c:
                    initiative_messages.append(
                        roll_for_c.get("result_summary", f"{combatant.name} init: {combatant.initiative}")
                    )
            else:
                # Fallback for missing rolls
                logger.warning(f"Missing initiative roll for {combatant.name}. Using fallback.")
                fallback_initiative = self._generate_fallback_initiative(combatant.id)
                combatant.initiative = fallback_initiative
                initiative_messages.append(f"{combatant.name} init: {combatant.initiative} (Fallback)")
        
        # Sort by initiative (highest first), with DEX as tiebreaker
        game_state.combat.combatants.sort(
            key=lambda c: (c.initiative, self._get_dex_modifier(c.id)), 
            reverse=True
        )
        
        # Reset to first combatant
        game_state.combat.current_turn_index = 0
        
        # Log and display results
        order_display = [f"{c.name}: {c.initiative}" for c in game_state.combat.combatants]
        logger.info(f"Initiative order: {', '.join(order_display)}")
        
        # This would typically be handled by a chat service
        # For now, we'll let the calling code handle the message
    
    def _add_combatant_to_combat(self, combatant_data: Dict, game_state) -> None:
        """Add a combatant to the current combat."""
        from app.game.models import Combatant
        
        combatant_id = combatant_data.get("id")
        combatant_name = combatant_data.get("name", combatant_id)
        is_player = combatant_id in game_state.party
        
        # Create combatant
        combatant = Combatant(
            id=combatant_id,
            name=combatant_name,
            initiative=-1,  # Will be set during initiative rolls
            is_player=is_player
        )
        
        game_state.combat.combatants.append(combatant)
        
        # Add monster stats if not a player
        if not is_player:
            monster_stats = combatant_data.get("stats", {})
            game_state.combat.monster_stats[combatant_id] = monster_stats
    
    def _auto_end_combat_all_incapacitated(self) -> None:
        """Auto-end combat when all combatants are incapacitated."""
        # Import here to avoid circular imports
        from app.game import state_processors
        from app.ai_services.schemas import CombatEndUpdate
        
        game_state = self.game_state_repo.get_game_state()
        end_update = CombatEndUpdate(
            type="combat_end", 
            details={"reason": "All combatants incapacitated"}
        )
        state_processors.end_combat(game_state, end_update)
    
    def _generate_fallback_initiative(self, character_id: str) -> int:
        """Generate a fallback initiative for a character."""
        import random
        
        # Try to use character's DEX modifier
        dex_mod = self._get_dex_modifier(character_id)
        base_roll = random.randint(1, 20)
        return base_roll + dex_mod
    
    def _get_dex_modifier(self, character_id: str) -> int:
        """Get DEX modifier for a character."""
        character = self.character_service.get_character(character_id)
        if character:
            return utils.get_ability_modifier(character.base_stats.DEX)
        
        # Check monster stats
        game_state = self.game_state_repo.get_game_state()
        if game_state.combat.is_active and character_id in game_state.combat.monster_stats:
            monster_stats = game_state.combat.monster_stats[character_id]
            dex_score = monster_stats.get("stats", {}).get("DEX", 10)
            return utils.get_ability_modifier(dex_score)
        
        return 0


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
            "monster_status": game_state.combat.monster_stats
        }
