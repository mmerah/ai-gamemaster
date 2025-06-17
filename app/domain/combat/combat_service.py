"""
Enhanced Combat Service implementation following TDD approach.
This service manages combat state transitions and emits appropriate events.
"""

import logging
from typing import List, Optional, Tuple

from app.core.event_queue import EventQueue
from app.core.interfaces import CombatService, GameStateRepository
from app.domain.characters.character_service import CharacterService
from app.domain.combat.combat_factory import CombatFactory
from app.models.combat import CombatantModel, CombatStateModel, InitialCombatantData
from app.models.dice import DiceRollResultResponseModel
from app.models.events import (
    CombatantInitiativeSetEvent,
    InitiativeOrderDeterminedEvent,
    TurnAdvancedEvent,
)
from app.models.game_state import GameStateModel

logger = logging.getLogger(__name__)


class CombatServiceImpl(CombatService):
    """Enhanced combat service with event emission support."""

    def __init__(
        self,
        game_state_repo: GameStateRepository,
        character_service: CharacterService,
        combat_factory: CombatFactory,
        event_queue: Optional[EventQueue] = None,
    ):
        """Initialize the combat service with dependencies."""
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.combat_factory = combat_factory
        self.event_queue = event_queue

    def start_combat(self, combatants: List[InitialCombatantData]) -> None:
        """
        Start combat by adding combatants.

        Args:
            combatants: List of InitialCombatantData with id, name, hp, ac, stats
        """
        # Get current game state
        current_game_state = self.game_state_repo.get_game_state()

        # Don't start combat if already active
        if current_game_state.combat.is_active:
            return

        # Use factory to create the complete combat state
        new_combat_state = self.combat_factory.create_combat_state(
            party=current_game_state.party,
            npc_combatants=combatants,
            character_service=self.character_service,
        )

        # Update game state
        current_game_state.combat = new_combat_state
        self.game_state_repo.save_game_state(current_game_state)

    def set_initiative_order(
        self, current_game_state: GameStateModel
    ) -> GameStateModel:
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
            reverse=True,
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
                    icon_path=combatant.icon_path,
                )
                combatants_copy.append(combatant_copy)

            order_event = InitiativeOrderDeterminedEvent(
                ordered_combatants=combatants_copy
            )
            self.event_queue.put_event(order_event)

            # Also emit TurnAdvancedEvent for the first combatant
            if sorted_combatants:
                first_combatant = sorted_combatants[0]
                turn_event = TurnAdvancedEvent(
                    new_combatant_id=first_combatant.id,
                    new_combatant_name=first_combatant.name,
                    round_number=current_game_state.combat.round_number,
                    is_new_round=True,
                    is_player_controlled=first_combatant.is_player,
                )
                self.event_queue.put_event(turn_event)

        return current_game_state

    def advance_turn(self) -> None:
        """
        Advance to the next active combatant's turn.
        Skips incapacitated combatants and increments round when wrapping.
        """
        current_game_state = self.game_state_repo.get_game_state()
        if not current_game_state.combat.is_active:
            return

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
                    is_player_controlled=new_combatant.is_player,
                )
                self.event_queue.put_event(turn_event)

        # Save the updated game state
        self.game_state_repo.save_game_state(current_game_state)

    def apply_damage(
        self,
        current_game_state: GameStateModel,
        target_id: str,
        amount: int,
        damage_type: str,
        source: Optional[str] = None,
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
        source: Optional[str] = None,
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

    def end_combat(self) -> None:
        """End the current combat encounter."""
        game_state = self.game_state_repo.get_game_state()
        if game_state.combat.is_active:
            game_state.combat.is_active = False
            game_state.combat.combatants = []
            game_state.combat.current_turn_index = -1
            game_state.combat.round_number = 1
            game_state.combat.current_turn_instruction_given = False
            self.game_state_repo.save_game_state(game_state)
            logger.info("Combat ended")

    def determine_initiative_order(
        self, all_initiative_results: List[DiceRollResultResponseModel]
    ) -> None:
        """
        Process initiative roll results and update combatant initiatives.

        Args:
            all_initiative_results: List of DiceRollResultResponseModel objects
        """
        game_state = self.game_state_repo.get_game_state()
        if not game_state.combat.is_active:
            return

        # Update combatant initiatives from roll results
        for result in all_initiative_results:
            combatant_id = result.character_id
            initiative_value = result.total_result

            if not combatant_id:
                continue

            combatant = game_state.combat.get_combatant_by_id(combatant_id)
            if combatant:
                # Only emit event if initiative is changing (wasn't already set)
                old_initiative = combatant.initiative
                combatant.initiative = initiative_value
                logger.info(f"Set initiative for {combatant.name}: {initiative_value}")

                # Emit CombatantInitiativeSetEvent only if value changed
                # This prevents duplicate events for NPCs that already had their initiative set
                if self.event_queue and old_initiative != initiative_value:
                    roll_details = f"Roll result: {initiative_value}"
                    event = CombatantInitiativeSetEvent(
                        combatant_id=combatant.id,
                        combatant_name=combatant.name,
                        initiative_value=combatant.initiative,
                        roll_details=roll_details,
                    )
                    self.event_queue.put_event(event)

        # Now sort and set the order
        self.set_initiative_order(game_state)

        # Save the updated state
        self.game_state_repo.save_game_state(game_state)
