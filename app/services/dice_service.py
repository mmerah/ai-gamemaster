"""
Dice service for handling dice rolls and modifiers.
"""
import logging
import random
from typing import Dict, List, Optional, Tuple, Any
from app.game.calculators.dice_mechanics import roll_dice_formula, format_roll_type_description
from app.game.calculators.character_stats import calculate_total_modifier_for_roll
from app.game.validators.campaign_validators import validate_dice_roll_data
from app.core.interfaces import DiceRollingService, CharacterService, GameStateRepository

logger = logging.getLogger(__name__)


class DiceRollingServiceImpl(DiceRollingService):
    """Implementation of dice rolling service."""
    
    def __init__(self, character_service: CharacterService, game_state_repo: GameStateRepository):
        self.character_service = character_service
        self.game_state_repo = game_state_repo
    
    def perform_roll(self, character_id: str, roll_type: str, dice_formula: str,
                     skill: Optional[str] = None, ability: Optional[str] = None,
                     dc: Optional[int] = None, reason: str = "",
                     original_request_id: Optional[str] = None) -> Dict[str, Any]:
        """Perform a dice roll and return the result."""
        actual_char_id = self.character_service.find_character_by_name_or_id(character_id)
        if not actual_char_id:
            error_msg = f"Cannot roll: Unknown character/combatant '{character_id}'."
            logger.error(error_msg)
            return {"error": error_msg}

        char_name = self.character_service.get_character_name(actual_char_id)
        char_modifier = self._calculate_character_modifier(actual_char_id, roll_type, skill, ability)
        
        # Perform the actual dice roll
        roll_result = self._execute_dice_roll(dice_formula)
        if "error" in roll_result:
            return {"error": f"Invalid dice formula '{dice_formula}' for {char_name}."}
        
        final_result = roll_result["total"] + char_modifier
        success = self._determine_success(final_result, dc)
        
        # Generate result messages
        messages = self._generate_roll_messages(
            char_name, roll_type, skill, ability, dice_formula, 
            char_modifier, roll_result, final_result, dc, success
        )
        
        # Generate unique request ID if not provided
        result_request_id = original_request_id or self._generate_request_id(
            actual_char_id, roll_type
        )
        
        logger.info(f"Roll: {messages['detailed']} (Reason: {reason})")
        
        return {
            "request_id": result_request_id,
            "character_id": actual_char_id,
            "character_name": char_name,
            "roll_type": roll_type,
            "dice_formula": dice_formula,
            "character_modifier": char_modifier,
            "total_result": final_result,
            "dc": dc,
            "success": success,
            "reason": reason,
            "result_message": messages["detailed"],
            "result_summary": messages["summary"]
        }
    
    def _calculate_character_modifier(self, character_id: str, roll_type: str, 
                                    skill: Optional[str], ability: Optional[str]) -> int:
        """Calculate the modifier for a character's roll."""
        char_instance = self.character_service.get_character(character_id)
        
        if char_instance:
            return self._calculate_player_modifier(char_instance, roll_type, skill, ability)
        else:
            return self._calculate_npc_modifier(character_id, roll_type, skill, ability)
    
    def _calculate_player_modifier(self, character: Any, roll_type: str, 
                                 skill: Optional[str], ability: Optional[str]) -> int:
        """Calculate modifier for a player character."""
        char_data_for_mod = {
            "stats": character.base_stats if hasattr(character.base_stats, 'model_dump') else character.base_stats,
            "proficiencies": character.proficiencies if hasattr(character.proficiencies, 'model_dump') else character.proficiencies,
            "level": getattr(character, 'level', 1)
        }
        
        # Handle model_dump if it's a Pydantic model
        if hasattr(character.base_stats, 'model_dump'):
            char_data_for_mod["stats"] = character.base_stats.model_dump()
        if hasattr(character.proficiencies, 'model_dump'):
            char_data_for_mod["proficiencies"] = character.proficiencies.model_dump()
            
        return calculate_total_modifier_for_roll(char_data_for_mod, roll_type, skill, ability)
    
    def _calculate_npc_modifier(self, character_id: str, roll_type: str, 
                              skill: Optional[str], ability: Optional[str]) -> int:
        """Calculate modifier for an NPC."""
        game_state = self.game_state_repo.get_game_state()
        
        if game_state.combat.is_active and character_id in game_state.combat.monster_stats:
            npc_stats_data = game_state.combat.monster_stats[character_id]
            temp_npc_data_for_mod = {
                "stats": npc_stats_data.get("stats", {"DEX": 10}),
                "proficiencies": {},
                "level": npc_stats_data.get("level", 1)
            }
            return calculate_total_modifier_for_roll(temp_npc_data_for_mod, roll_type, skill, ability)
        else:
            logger.warning(f"perform_roll for non-player, non-tracked-NPC '{character_id}'. Assuming 0 modifier.")
            return 0
    
    def _execute_dice_roll(self, dice_formula: str) -> Dict[str, Any]:
        """Execute the actual dice roll."""
        base_total, individual_rolls, _, formula_desc = roll_dice_formula(dice_formula)
        
        if formula_desc.startswith("Invalid"):
            return {"error": "Invalid dice formula"}
        
        return {
            "total": base_total,
            "individual_rolls": individual_rolls,
            "formula_description": formula_desc
        }
    
    def _determine_success(self, final_result: int, dc: Optional[int]) -> Optional[bool]:
        """Determine if the roll was successful."""
        if dc is not None:
            return final_result >= dc
        return None
    
    def _generate_roll_messages(self, char_name: str, roll_type: str, skill: Optional[str], 
                              ability: Optional[str], dice_formula: str, char_modifier: int,
                              roll_result: Dict, final_result: int, dc: Optional[int], 
                              success: Optional[bool]) -> Dict[str, str]:
        """Generate detailed and summary messages for the roll."""
        mod_str = f"{char_modifier:+}"
        roll_details = f"[{','.join(map(str, roll_result['individual_rolls']))}] {mod_str}"
        type_desc = format_roll_type_description(roll_type, skill, ability)
        
        # Detailed message
        detailed_msg = (f"{char_name} rolls {type_desc}: {roll_result['formula_description']} "
                       f"({mod_str}) -> {roll_details} = **{final_result}**.")
        
        # Summary message
        summary_msg = f"{char_name} rolls {type_desc}: Result **{final_result}**."
        
        # Add DC and success information
        if dc is not None:
            dc_text = f" (DC {dc})"
            detailed_msg += dc_text
            summary_msg += dc_text
            
            if success is not None:
                success_text = " Success!" if success else " Failure."
                detailed_msg += success_text
                summary_msg += success_text
        
        return {
            "detailed": detailed_msg.strip(),
            "summary": summary_msg.strip()
        }
    
    def _generate_request_id(self, character_id: str, roll_type: str) -> str:
        """Generate a unique request ID for the roll."""
        return f"roll_{character_id}_{roll_type.replace(' ','_')}_{random.randint(1000,9999)}"


class DiceRollValidator:
    """Utility class for validating dice roll requests."""
    
    @staticmethod
    def validate_dice_formula(formula: str) -> bool:
        """Validate that a dice formula is properly formatted."""
        if not formula or not isinstance(formula, str):
            return False
        
        # Basic validation - could be expanded
        import re
        pattern = r'^\d*d\d+([+-]\d+)?$'
        return bool(re.match(pattern, formula.strip().lower()))
    
    @staticmethod
    def validate_roll_type(roll_type: str) -> bool:
        """Validate that a roll type is supported."""
        valid_types = [
            "ability_check", "skill_check", "saving_throw", "attack_roll",
            "damage_roll", "initiative", "custom"
        ]
        return roll_type in valid_types
    
    @staticmethod
    def validate_ability_score(ability: str) -> bool:
        """Validate that an ability score is valid."""
        valid_abilities = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
        return ability.upper() in valid_abilities


class DiceRollFormatter:
    """Utility class for formatting dice roll results."""
    
    @staticmethod
    def format_roll_for_chat(roll_result: Dict[str, Any]) -> str:
        """Format a roll result for display in chat."""
        char_name = roll_result.get("character_name", "Unknown")
        roll_type = roll_result.get("roll_type", "roll")
        total = roll_result.get("total_result", 0)
        
        base_msg = f"{char_name} rolled {total} for {roll_type}"
        
        if roll_result.get("dc"):
            success = "Success" if roll_result.get("success") else "Failure"
            base_msg += f" (DC {roll_result['dc']}) - {success}"
        
        return base_msg
    
    @staticmethod
    def format_multiple_rolls(roll_results: list) -> str:
        """Format multiple roll results for display."""
        if not roll_results:
            return "No rolls performed."
        
        if len(roll_results) == 1:
            return DiceRollFormatter.format_roll_for_chat(roll_results[0])
        
        formatted_rolls = [
            DiceRollFormatter.format_roll_for_chat(roll) 
            for roll in roll_results
        ]
        return "\n".join(formatted_rolls)
