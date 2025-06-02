"""
Enhanced Combat Service implementation following TDD approach.
This service manages combat state transitions and emits appropriate events.
"""
from typing import List, Dict, Tuple, Optional
from app.game.unified_models import GameStateModel, CombatantModel, CombatStateModel, InitialCombatantData, MonsterBaseStats
from app.repositories.game_state_repository import GameStateRepository
from app.services.character_service import CharacterService
from app.events.game_update_events import (
    CombatantInitiativeSetEvent, InitiativeOrderDeterminedEvent, TurnAdvancedEvent
)
from app.core.event_queue import EventQueue
import logging

logger = logging.getLogger(__name__)


class CombatServiceImpl:
    """Enhanced combat service with event emission support."""
    
    def __init__(self, game_state_repo: GameStateRepository, character_service: CharacterService, event_queue: Optional[EventQueue] = None):
        """Initialize the combat service with dependencies."""
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.event_queue = event_queue
    
    def start_combat(self, current_game_state: GameStateModel, initial_npc_data: List[InitialCombatantData]) -> GameStateModel:
        """
        Start combat by adding PCs and NPCs as combatants.
        
        Args:
            current_game_state: Current game state
            initial_npc_data: List of InitialCombatantData with id, name, hp, ac, stats
            
        Returns:
            Updated game state with combat initialized
        """
        # Don't start combat if already active
        if current_game_state.combat.is_active:
            return current_game_state
        
        # Create a new combat state
        new_combat_state = CombatStateModel(
            is_active=True,
            round_number=1,
            current_turn_index=-1,  # No initiative set yet
            combatants=[],
            monster_stats={}
        )
        
        # Add party members as combatants
        for char_id, character_instance in current_game_state.party.items():
            # Get combined character data (template + instance)
            char_data = self.character_service.get_character(char_id)
            if not char_data:
                logger.warning(f"Could not find character data for {char_id}, skipping combat")
                continue
            
            # Get DEX modifier for initiative tie-breaking from template
            dex_score = char_data.template.base_stats.DEX
            dex_modifier = (dex_score - 10) // 2
            
            # Calculate armor class from template 
            from app.services.character_service import CharacterStatsCalculator
            armor_class = CharacterStatsCalculator.calculate_armor_class(char_data.template)
            
            combatant = CombatantModel(
                id=char_id,
                name=char_data.template.name,  # From template
                initiative=0,  # Will be set later
                initiative_modifier=dex_modifier,
                current_hp=character_instance.current_hp,  # From instance
                max_hp=character_instance.max_hp,  # From instance
                armor_class=armor_class,  # Calculated from template
                is_player=True,
                icon_path=char_data.template.portrait_path  # From template
            )
            new_combat_state.combatants.append(combatant)
        
        # Add NPCs as combatants
        for npc_data in initial_npc_data:
            # Calculate DEX modifier from stats
            dex_score = npc_data.stats.get("DEX", 10) if npc_data.stats else 10
            dex_modifier = (dex_score - 10) // 2
            
            combatant = CombatantModel(
                id=npc_data.id,
                name=npc_data.name,
                initiative=0,  # Will be set later
                initiative_modifier=dex_modifier,
                current_hp=npc_data.hp,
                max_hp=npc_data.hp,
                armor_class=npc_data.ac,
                is_player=False,
                icon_path=npc_data.icon_path
            )
            new_combat_state.combatants.append(combatant)
            
            # Store base stats for NPCs
            new_combat_state.monster_stats[npc_data.id] = MonsterBaseStats(
                name=npc_data.name,
                initial_hp=npc_data.hp,
                ac=npc_data.ac,
                stats=npc_data.stats or {},
                abilities=npc_data.abilities or [],
                attacks=npc_data.attacks or []
            )
        
        # Update game state
        current_game_state.combat = new_combat_state
        return current_game_state
    
    def set_initiative_order(self, current_game_state: GameStateModel) -> GameStateModel:
        """
        Sort combatants by initiative (highest first) with DEX tie-breaker.
        Sets current_turn_index to 0 (first combatant).
        
        Args:
            current_game_state: Current game state
            
        Returns:
            Updated game state with sorted combatants
        """
        if not current_game_state.combat.is_active:
            return current_game_state
        
        # Sort combatants by initiative (desc), then by initiative_modifier (desc)
        sorted_combatants = sorted(
            current_game_state.combat.combatants,
            key=lambda c: (c.initiative, c.initiative_modifier),
            reverse=True
        )
        
        # Update combat state
        current_game_state.combat.combatants = sorted_combatants
        current_game_state.combat.current_turn_index = 0
        
        # Emit InitiativeOrderDeterminedEvent
        if self.event_queue:
            combatants_copy = []
            for combatant in sorted_combatants:
                combatant_copy = CombatantModel(
                    id=combatant.id,
                    name=combatant.name,
                    initiative=combatant.initiative,
                    initiative_modifier=combatant.initiative_modifier,
                    current_hp=combatant.current_hp,
                    max_hp=combatant.max_hp,
                    armor_class=combatant.armor_class,
                    conditions=combatant.conditions.copy(),  # Copy the list
                    is_player=combatant.is_player,
                    icon_path=combatant.icon_path
                )
                combatants_copy.append(combatant_copy)
            
            order_event = InitiativeOrderDeterminedEvent(ordered_combatants=combatants_copy)
            self.event_queue.put_event(order_event)
            
            # Also emit TurnAdvancedEvent for the first combatant
            if sorted_combatants:
                first_combatant = sorted_combatants[0]
                turn_event = TurnAdvancedEvent(
                    new_combatant_id=first_combatant.id,
                    new_combatant_name=first_combatant.name,
                    round_number=current_game_state.combat.round_number,
                    is_new_round=True,
                    is_player_controlled=first_combatant.is_player
                )
                self.event_queue.put_event(turn_event)
        
        return current_game_state
    
    def advance_turn(self, current_game_state: GameStateModel) -> GameStateModel:
        """
        Advance to the next active combatant's turn.
        Skips incapacitated combatants and increments round when wrapping.
        
        Args:
            current_game_state: Current game state
            
        Returns:
            Updated game state with advanced turn
        """
        if not current_game_state.combat.is_active:
            return current_game_state
        
        combat = current_game_state.combat
        
        # Find next active combatant
        next_index, new_round = combat.get_next_active_combatant_index()
        
        # Update turn and round
        combat.current_turn_index = next_index
        combat.round_number = new_round
        # Reset the turn instruction flag for the new turn
        combat.current_turn_instruction_given = False
        
        # Emit TurnAdvancedEvent
        if self.event_queue and combat.combatants:
            new_combatant = combat.get_current_combatant()
            if new_combatant:
                turn_event = TurnAdvancedEvent(
                    new_combatant_id=new_combatant.id,
                    new_combatant_name=new_combatant.name,
                    round_number=combat.round_number,
                    is_new_round=(next_index == 0 and new_round > 1),
                    is_player_controlled=new_combatant.is_player
                )
                self.event_queue.put_event(turn_event)
        
        return current_game_state
    
    def apply_damage(
        self, 
        current_game_state: GameStateModel, 
        target_id: str, 
        amount: int, 
        damage_type: str, 
        source: Optional[str] = None
    ) -> Tuple[GameStateModel, int, bool]:
        """
        Apply damage to a combatant, respecting HP bounds.
        
        Args:
            current_game_state: Current game state
            target_id: ID of the target combatant
            amount: Amount of damage to apply
            damage_type: Type of damage (e.g., "slashing", "fire")
            source: Optional source of damage
            
        Returns:
            Tuple of (updated_game_state, actual_damage_taken, is_defeated)
        """
        combat = current_game_state.combat
        combatant = combat.get_combatant_by_id(target_id)
        
        if not combatant:
            logger.warning(f"CombatantModel {target_id} not found")
            return current_game_state, 0, False
        
        # Calculate actual damage (can't go below 0)
        old_hp = combatant.current_hp
        actual_damage = min(amount, old_hp)
        new_hp = max(0, old_hp - amount)
        
        # Update combatant HP
        combatant.current_hp = new_hp
        
        # Check if defeated
        is_defeated = new_hp == 0
        
        logger.info(
            f"{combatant.name} takes {actual_damage} {damage_type} damage "
            f"from {source or 'unknown source'} ({old_hp} -> {new_hp} HP)"
        )
        
        return current_game_state, actual_damage, is_defeated
    
    def apply_healing(
        self,
        current_game_state: GameStateModel,
        target_id: str,
        amount: int,
        source: Optional[str] = None
    ) -> Tuple[GameStateModel, int]:
        """
        Apply healing to a combatant, respecting max HP.
        
        Args:
            current_game_state: Current game state
            target_id: ID of the target combatant
            amount: Amount of healing to apply
            source: Optional source of healing
            
        Returns:
            Tuple of (updated_game_state, actual_healing_done)
        """
        combat = current_game_state.combat
        combatant = combat.get_combatant_by_id(target_id)
        
        if not combatant:
            logger.warning(f"CombatantModel {target_id} not found")
            return current_game_state, 0
        
        # Calculate actual healing (can't exceed max HP)
        old_hp = combatant.current_hp
        actual_healing = min(amount, combatant.max_hp - old_hp)
        new_hp = min(combatant.max_hp, old_hp + amount)
        
        # Update combatant HP
        combatant.current_hp = new_hp
        
        logger.info(
            f"{combatant.name} heals {actual_healing} HP "
            f"from {source or 'unknown source'} ({old_hp} -> {new_hp} HP)"
        )
        
        return current_game_state, actual_healing
    
    def check_combat_end_conditions(self, current_game_state: GameStateModel) -> bool:
        """
        Check if combat should end (all enemies or all PCs defeated).
        
        Args:
            current_game_state: Current game state
            
        Returns:
            True if combat should end, False otherwise
        """
        if not current_game_state.combat.is_active:
            return False
        
        combatants = current_game_state.combat.combatants
        
        # Get active combatants by type
        active_pcs = [c for c in combatants if c.is_player and not c.is_defeated]
        active_npcs = [c for c in combatants if not c.is_player and not c.is_defeated]
        
        # Combat ends if either side has no active combatants
        should_end = len(active_pcs) == 0 or len(active_npcs) == 0
        
        if should_end:
            if len(active_pcs) == 0:
                logger.info("Combat ending: All player characters defeated")
            else:
                logger.info("Combat ending: All enemies defeated")
        
        return should_end
    
    def determine_initiative_order(self, all_initiative_results: List[Dict]) -> None:
        """
        Process initiative roll results and update combatant initiatives.
        
        Args:
            all_initiative_results: List of dicts with character_id and total_result
        
        NOTE: Using List[Dict] here instead of a Pydantic model because these are
        transient results from the dice service that are immediately processed
        and not stored. The dice service returns Dict[str, Any] for flexibility.
        Future enhancement: Update dice service to return DiceRollResult models.
        """
        game_state = self.game_state_repo.get_game_state()
        if not game_state.combat.is_active:
            return
        
        # Update combatant initiatives from roll results
        for result in all_initiative_results:
            combatant_id = result.get("character_id")
            initiative_value = result.get("total_result", 0)
            
            combatant = game_state.combat.get_combatant_by_id(combatant_id)
            if combatant:
                combatant.initiative = initiative_value
                logger.info(f"Set initiative for {combatant.name}: {initiative_value}")
                
                # Emit CombatantInitiativeSetEvent
                if self.event_queue:
                    roll_details = f"Roll result: {initiative_value}"
                    event = CombatantInitiativeSetEvent(
                        combatant_id=combatant.id,
                        combatant_name=combatant.name,
                        initiative_value=combatant.initiative,
                        roll_details=roll_details
                    )
                    self.event_queue.put_event(event)
        
        # Now sort and set the order
        self.set_initiative_order(game_state)
        
        # Save the updated state
        self.game_state_repo.save_game_state(game_state)