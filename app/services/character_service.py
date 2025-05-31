"""
Character service implementation for managing character operations.
"""
import logging
from typing import Optional
from app.core.interfaces import CharacterService, GameStateRepository
from app.game.models import CharacterInstance

logger = logging.getLogger(__name__)


class CharacterServiceImpl(CharacterService):
    """Implementation of character service."""
    
    def __init__(self, game_state_repo: GameStateRepository):
        self.game_state_repo = game_state_repo
    
    def get_character(self, character_id: str) -> Optional[CharacterInstance]:
        """Get a character by ID."""
        game_state = self.game_state_repo.get_game_state()
        return game_state.party.get(character_id)
    
    def find_character_by_name_or_id(self, identifier: str) -> Optional[str]:
        """Find character ID by name or direct ID match."""
        if not identifier:
            return None
            
        game_state = self.game_state_repo.get_game_state()
        
        # Direct ID match in party
        if identifier in game_state.party:
            return identifier
        
        # Name-based search in party
        identifier_lower = identifier.lower()
        for char_id, character in game_state.party.items():
            if character.name.lower() == identifier_lower:
                logger.debug(f"Found party member ID '{char_id}' by name '{identifier}'.")
                return char_id
        
        # Check active combat monsters
        if game_state.combat.is_active:
            if identifier in game_state.combat.monster_stats:
                return identifier
            
            # Name-based search in combatants
            for combatant in game_state.combat.combatants:
                if combatant.name.lower() == identifier_lower:
                    logger.debug(f"Found combatant ID '{combatant.id}' by name '{identifier}'.")
                    return combatant.id
        
        logger.warning(f"Could not find character or active combatant for identifier '{identifier}'.")
        return None
    
    def get_character_name(self, character_id: str) -> str:
        """Get display name for a character."""
        # Try player character first
        player = self.get_character(character_id)
        if player:
            return player.name
        
        # Try monster in active combat
        game_state = self.game_state_repo.get_game_state()
        if game_state.combat.is_active and character_id in game_state.combat.monster_stats:
            monster_stat = game_state.combat.monster_stats[character_id]
            # NOTE: This code handles both dict and MonsterBaseStats for backward compatibility
            # during the transition period. Once all data is migrated, the dict check can be removed.
            # The GameState validator automatically converts dicts to MonsterBaseStats on load.
            if hasattr(monster_stat, 'name'):
                return monster_stat.name
            else:
                return monster_stat.get("name", character_id)
        
        # Fallback to ID
        return character_id


class CharacterValidator:
    """Utility class for character validation operations."""
    
    @staticmethod
    def is_character_defeated(character_id: str, game_state_repo: GameStateRepository) -> bool:
        """Check if a character is defeated."""
        game_state = game_state_repo.get_game_state()
        
        # Check player character
        player = game_state.party.get(character_id)
        if player:
            return player.current_hp <= 0
        
        # Check monster in combat
        if game_state.combat.is_active:
            combatant = game_state.combat.get_combatant_by_id(character_id)
            if combatant and not combatant.is_player:
                return combatant.current_hp <= 0 or "defeated" in [c.lower() for c in combatant.conditions]
        
        return False
    
    @staticmethod
    def is_character_incapacitated(character_id: str, game_state_repo: GameStateRepository) -> bool:
        """Check if a character is incapacitated (defeated or has incapacitating conditions)."""
        game_state = game_state_repo.get_game_state()
        
        # Check if defeated first
        if CharacterValidator.is_character_defeated(character_id, game_state_repo):
            return True
        
        # Check for incapacitating conditions
        player = game_state.party.get(character_id)
        if player:
            incapacitating_conditions = ["Unconscious", "Paralyzed", "Stunned", "Petrified"]
            return any(condition in player.conditions for condition in incapacitating_conditions)
        
        # Check monster conditions
        if game_state.combat.is_active:
            combatant = game_state.combat.get_combatant_by_id(character_id)
            if combatant and not combatant.is_player:
                incapacitating_conditions = ["unconscious", "paralyzed", "stunned", "petrified"]
                return any(condition.lower() in [c.lower() for c in combatant.conditions] for condition in incapacitating_conditions)
        
        return False


class CharacterStatsCalculator:
    """Utility class for calculating character statistics."""
    
    @staticmethod
    def calculate_ability_modifier(ability_score: int) -> int:
        """Calculate ability modifier from ability score."""
        return (ability_score - 10) // 2
    
    @staticmethod
    def calculate_proficiency_bonus(level: int) -> int:
        """Calculate proficiency bonus based on character level."""
        return 2 + ((level - 1) // 4)
    
    @staticmethod
    def calculate_max_hp(character: CharacterInstance) -> int:
        """Calculate maximum HP for a character."""
        con_mod = CharacterStatsCalculator.calculate_ability_modifier(character.base_stats.CON)
        hit_die_avg = 5  # Simplified for PoC (average of d8)
        return max(1, (hit_die_avg + con_mod) * character.level)
    
    @staticmethod
    def calculate_armor_class(character: CharacterInstance) -> int:
        """Calculate armor class for a character."""
        dex_mod = CharacterStatsCalculator.calculate_ability_modifier(character.base_stats.DEX)
        base_ac = 10  # Simplified calculation
        return base_ac + dex_mod
