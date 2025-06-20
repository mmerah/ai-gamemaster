"""
State update processor for AI response processing.
"""

import logging
from typing import Callable, List, Optional

from app.core.domain_interfaces import ICharacterService
from app.core.repository_interfaces import IGameStateRepository
from app.core.system_interfaces import IEventQueue
from app.models.events import ErrorContextModel, GameErrorEvent
from app.models.game_state import GameStateModel
from app.providers.ai.schemas import AIResponse
from app.services.ai_response_processors.interfaces import IStateUpdateProcessor
from app.services.state_updaters import (
    CombatStateUpdater,
    InventoryUpdater,
    QuestUpdater,
)
from app.utils.event_helpers import emit_event

logger = logging.getLogger(__name__)


class StateUpdateProcessor(IStateUpdateProcessor):
    """Handles game state updates from AI responses."""

    def __init__(
        self,
        game_state_repo: IGameStateRepository,
        character_service: ICharacterService,
        event_queue: IEventQueue,
    ):
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.event_queue = event_queue

    def find_combatant_id_by_name_or_id(self, identifier: str) -> Optional[str]:
        """Find combatant by name or ID."""
        return self.character_service.find_character_by_name_or_id(identifier)

    def _get_target_ids_for_update(
        self,
        game_state: GameStateModel,
        character_id_field: str,
        combatant_resolver: Callable[[str], Optional[str]],
    ) -> List[str]:
        """
        Resolves a character_id field that might be a specific ID, "party", or "all_players".
        Returns a list of specific character IDs.
        """
        if character_id_field.lower() in ["party", "all_players", "all_pcs"]:
            return list(game_state.party.keys())

        # Try to resolve as a single specific ID
        resolved_id = combatant_resolver(character_id_field)
        if resolved_id:
            return [resolved_id]

        logger.warning(
            f"Could not resolve '{character_id_field}' to any specific character or party keyword."
        )
        return []

    def process_game_state_updates(
        self,
        ai_response: AIResponse,
        correlation_id: Optional[str] = None,
        combatant_resolver: Optional[Callable[[str], Optional[str]]] = None,
    ) -> bool:
        """Apply game state updates from the AI response.

        Returns:
            bool: True if combat was started, False otherwise.
        """
        game_state = self.game_state_repo.get_game_state()
        combat_started = False
        combat_ended = False

        # Process each list of updates directly, in a logical order
        # (e.g., combat start before HP changes)
        if ai_response.combat_start:
            CombatStateUpdater.start_combat(
                game_state,
                ai_response.combat_start,
                self.event_queue,
                correlation_id,
                self.character_service,
            )
            combat_started = True

        if ai_response.hp_changes:
            self._process_hp_changes(ai_response, correlation_id, combatant_resolver)

        if ai_response.condition_adds:
            self._process_condition_adds(
                ai_response, correlation_id, combatant_resolver
            )

        if ai_response.condition_removes:
            self._process_condition_removes(
                ai_response, correlation_id, combatant_resolver
            )

        if ai_response.gold_changes:
            self._process_gold_changes(ai_response, correlation_id, combatant_resolver)

        if ai_response.inventory_adds:
            self._process_inventory_adds(
                ai_response, correlation_id, combatant_resolver
            )

        if ai_response.inventory_removes:
            self._process_inventory_removes(
                ai_response, correlation_id, combatant_resolver
            )

        if ai_response.quest_updates:
            self._process_quest_updates(ai_response, correlation_id)

        if ai_response.combatant_removals:
            self._process_combatant_removals(
                ai_response, correlation_id, combatant_resolver
            )

        if ai_response.combat_end:
            combat_ended = self._process_combat_end(ai_response, correlation_id)

        # Check for auto combat end if not explicitly ended
        if game_state.combat.is_active and not combat_ended:
            CombatStateUpdater.check_and_end_combat_if_over(
                game_state, self.event_queue, correlation_id, self.character_service
            )

        return combat_started

    def _process_hp_changes(
        self,
        ai_response: AIResponse,
        correlation_id: Optional[str] = None,
        combatant_resolver: Optional[Callable[[str], Optional[str]]] = None,
    ) -> None:
        """Process HP change updates."""
        game_state = self.game_state_repo.get_game_state()

        # Use provided resolver or fall back to our own
        resolver = combatant_resolver or self.find_combatant_id_by_name_or_id

        for hp_update in ai_response.hp_changes:
            target_id = resolver(hp_update.character_id)
            if target_id:
                CombatStateUpdater.apply_hp_change(
                    game_state,
                    hp_update,
                    target_id,
                    self.event_queue,
                    correlation_id,
                    self.character_service,
                )
            else:
                logger.error(
                    f"HPChangeUpdate: Unknown character_id '{hp_update.character_id}'"
                )
                # Emit GameErrorEvent for invalid character reference
                error_context = ErrorContextModel(
                    character_id=hp_update.character_id,
                    event_type="hp_change",
                )
                error_event = GameErrorEvent(
                    error_message=f"Unknown character_id '{hp_update.character_id}' in HP change update",
                    error_type="invalid_reference",
                    severity="error",
                    recoverable=True,
                    context=error_context,
                    correlation_id=correlation_id,
                )
                emit_event(
                    self.event_queue,
                    error_event,
                    f"Emitted GameErrorEvent for invalid character reference: {hp_update.character_id}",
                )

    def _process_condition_adds(
        self,
        ai_response: AIResponse,
        correlation_id: Optional[str] = None,
        combatant_resolver: Optional[Callable[[str], Optional[str]]] = None,
    ) -> None:
        """Process condition add updates."""
        game_state = self.game_state_repo.get_game_state()

        # Use provided resolver or fall back to our own
        resolver = combatant_resolver or self.find_combatant_id_by_name_or_id

        for condition_add in ai_response.condition_adds:
            # Handle multi-target updates
            target_ids = self._get_target_ids_for_update(
                game_state, condition_add.character_id, resolver
            )
            for target_id in target_ids:
                CombatStateUpdater.apply_condition_add(
                    game_state,
                    condition_add,
                    target_id,
                    self.event_queue,
                    correlation_id,
                    self.character_service,
                )

    def _process_condition_removes(
        self,
        ai_response: AIResponse,
        correlation_id: Optional[str] = None,
        combatant_resolver: Optional[Callable[[str], Optional[str]]] = None,
    ) -> None:
        """Process condition remove updates."""
        game_state = self.game_state_repo.get_game_state()

        # Use provided resolver or fall back to our own
        resolver = combatant_resolver or self.find_combatant_id_by_name_or_id

        for condition_remove in ai_response.condition_removes:
            # Handle multi-target updates
            target_ids = self._get_target_ids_for_update(
                game_state, condition_remove.character_id, resolver
            )
            for target_id in target_ids:
                CombatStateUpdater.apply_condition_remove(
                    game_state,
                    condition_remove,
                    target_id,
                    self.event_queue,
                    correlation_id,
                    self.character_service,
                )

    def _process_gold_changes(
        self,
        ai_response: AIResponse,
        correlation_id: Optional[str] = None,
        combatant_resolver: Optional[Callable[[str], Optional[str]]] = None,
    ) -> None:
        """Process gold change updates."""
        game_state = self.game_state_repo.get_game_state()

        # Use provided resolver or fall back to our own
        resolver = combatant_resolver or self.find_combatant_id_by_name_or_id

        for gold_update in ai_response.gold_changes:
            # Handle multi-target updates
            target_ids = self._get_target_ids_for_update(
                game_state, gold_update.character_id, resolver
            )
            for target_id in target_ids:
                InventoryUpdater.apply_gold_change(
                    game_state,
                    gold_update,
                    target_id,
                    self.event_queue,
                    correlation_id,
                    self.character_service,
                )

    def _process_inventory_adds(
        self,
        ai_response: AIResponse,
        correlation_id: Optional[str] = None,
        combatant_resolver: Optional[Callable[[str], Optional[str]]] = None,
    ) -> None:
        """Process inventory add updates."""
        game_state = self.game_state_repo.get_game_state()

        # Use provided resolver or fall back to our own
        resolver = combatant_resolver or self.find_combatant_id_by_name_or_id

        for inventory_add in ai_response.inventory_adds:
            # Handle multi-target updates
            target_ids = self._get_target_ids_for_update(
                game_state, inventory_add.character_id, resolver
            )
            for target_id in target_ids:
                InventoryUpdater.apply_inventory_add(
                    game_state,
                    inventory_add,
                    target_id,
                    self.event_queue,
                    correlation_id,
                    self.character_service,
                )

    def _process_inventory_removes(
        self,
        ai_response: AIResponse,
        correlation_id: Optional[str] = None,
        combatant_resolver: Optional[Callable[[str], Optional[str]]] = None,
    ) -> None:
        """Process inventory remove updates."""
        game_state = self.game_state_repo.get_game_state()

        # Use provided resolver or fall back to our own
        resolver = combatant_resolver or self.find_combatant_id_by_name_or_id

        for inventory_remove in ai_response.inventory_removes:
            # Handle multi-target updates
            target_ids = self._get_target_ids_for_update(
                game_state, inventory_remove.character_id, resolver
            )
            for target_id in target_ids:
                InventoryUpdater.apply_inventory_remove(
                    game_state,
                    inventory_remove,
                    target_id,
                    self.event_queue,
                    correlation_id,
                    self.character_service,
                )

    def _process_quest_updates(
        self, ai_response: AIResponse, correlation_id: Optional[str] = None
    ) -> None:
        """Process quest updates."""
        game_state = self.game_state_repo.get_game_state()

        for quest_update in ai_response.quest_updates:
            QuestUpdater.apply_quest_update(
                game_state, quest_update, self.event_queue, correlation_id
            )

    def _process_combatant_removals(
        self,
        ai_response: AIResponse,
        correlation_id: Optional[str] = None,
        combatant_resolver: Optional[Callable[[str], Optional[str]]] = None,
    ) -> None:
        """Process combatant removal updates."""
        game_state = self.game_state_repo.get_game_state()

        # Use provided resolver or fall back to our own
        resolver = combatant_resolver or self.find_combatant_id_by_name_or_id

        for removal_update in ai_response.combatant_removals:
            specific_id = resolver(removal_update.character_id)
            if specific_id:
                CombatStateUpdater.remove_combatant_from_state(
                    game_state,
                    specific_id,
                    removal_update.reason,
                    self.event_queue,
                    correlation_id,
                    self.character_service,
                )
            else:
                logger.error(
                    f"CombatantRemove: Unknown character_id '{removal_update.character_id}'"
                )

    def _process_combat_end(
        self, ai_response: AIResponse, correlation_id: Optional[str] = None
    ) -> bool:
        """Process combat end update.

        Returns:
            bool: True if combat was ended, False otherwise.
        """
        game_state = self.game_state_repo.get_game_state()

        if game_state.combat.is_active:
            from app.models.updates import CombatEndUpdateModel

            combat_end = ai_response.combat_end or CombatEndUpdateModel(
                reason="Combat ended by AI"
            )
            CombatStateUpdater.end_combat(
                game_state,
                combat_end,
                self.event_queue,
                correlation_id,
                self.character_service,
            )
            return True
        else:
            logger.warning("AI sent 'combat_end' but combat was already inactive.")
            return False
