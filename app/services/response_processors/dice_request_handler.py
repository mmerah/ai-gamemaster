"""
Dice request handler for AI response processing.
"""

import logging
import random
from typing import Any, Dict, List, Optional, Tuple

from app.ai_services.schemas import AIResponse
from app.core.event_queue import EventQueue
from app.core.interfaces import (
    CharacterService,
    ChatService,
    DiceRollingService,
    GameStateRepository,
)
from app.models import DiceRequestModel, DiceRollResultResponseModel
from app.models.events import NpcDiceRollProcessedEvent, PlayerDiceRequestAddedEvent

logger = logging.getLogger(__name__)


class DiceRequestHandler:
    """Handles dice request processing for AI responses."""

    def __init__(
        self,
        game_state_repo: GameStateRepository,
        character_service: CharacterService,
        dice_service: DiceRollingService,
        chat_service: ChatService,
        event_queue: Optional[EventQueue] = None,
        correlation_id: Optional[str] = None,
    ):
        self.game_state_repo = game_state_repo
        self.character_service = character_service
        self.dice_service = dice_service
        self.chat_service = chat_service
        self.event_queue = event_queue
        self.correlation_id = correlation_id

    def process_dice_requests(
        self, ai_response: AIResponse, combat_just_started: bool
    ) -> Tuple[List[DiceRequestModel], bool, bool]:
        """Process dice requests from AI response."""
        game_state = self.game_state_repo.get_game_state()
        party_char_ids_set = set(game_state.party.keys())

        player_requests_to_send = []
        npc_requests_to_roll_internally = []
        has_initiative_request_from_ai = False

        # Process each dice request
        for req_obj in ai_response.dice_requests:
            req_dict = req_obj.model_dump()
            resolved_char_ids = self._resolve_character_ids(
                req_dict.get("character_ids", [])
            )

            if not resolved_char_ids:
                logger.error(
                    f"Could not resolve any valid character IDs for dice request: {req_dict}"
                )
                continue

            req_dict["character_ids"] = resolved_char_ids

            if req_dict.get("type") == "initiative":
                has_initiative_request_from_ai = True

            # Separate player vs NPC requests
            player_ids = [cid for cid in resolved_char_ids if cid in party_char_ids_set]
            npc_ids = [
                cid for cid in resolved_char_ids if cid not in party_char_ids_set
            ]

            if player_ids:
                # Create a new DiceRequestModel object for player characters
                player_request = DiceRequestModel(
                    request_id=req_obj.request_id,
                    character_ids=player_ids,
                    type=req_obj.type,
                    dice_formula=req_obj.dice_formula,
                    reason=req_obj.reason,
                    skill=req_obj.skill,
                    ability=req_obj.ability,
                    dc=req_obj.dc,
                )
                player_requests_to_send.append(player_request)

                # Emit PlayerDiceRequestAddedEvent for each player character
                if self.event_queue:
                    for char_id in player_ids:
                        char_name = self.character_service.get_character_name(char_id)
                        event = PlayerDiceRequestAddedEvent(
                            request_id=player_request.request_id,
                            character_id=char_id,
                            character_name=char_name,
                            roll_type=player_request.type,
                            dice_formula=player_request.dice_formula,
                            purpose=player_request.reason,
                            dc=player_request.dc,
                            skill=player_request.skill,
                            ability=player_request.ability,
                            correlation_id=self.correlation_id,
                        )
                        self.event_queue.put_event(event)

            if npc_ids:
                # NOTE: NPC requests use dict format for internal processing only.
                # These are transient objects that are immediately processed and not stored.
                # Player requests use DiceRequestModel models because they're stored in game state.
                npc_part = req_dict.copy()
                npc_part["character_ids"] = npc_ids
                npc_requests_to_roll_internally.append(npc_part)

        # Force initiative if combat just started and AI didn't request it
        if combat_just_started and not has_initiative_request_from_ai:
            self._force_initiative_rolls(
                player_requests_to_send,
                npc_requests_to_roll_internally,
                party_char_ids_set,
            )

        # Perform NPC rolls
        game_state._pending_npc_roll_results = []  # Clear before new rolls
        npc_rolls_performed, _ = self._perform_npc_rolls(
            npc_requests_to_roll_internally
        )

        needs_ai_rerun = npc_rolls_performed and not player_requests_to_send
        if needs_ai_rerun:
            logger.info(
                "NPC rolls performed and no player action required. Flagging for AI rerun."
            )

        return player_requests_to_send, npc_rolls_performed, needs_ai_rerun

    def _resolve_character_ids(self, req_char_ids_input: List[str]) -> List[str]:
        """Resolve character IDs, handling 'all' and 'party' keywords."""
        game_state = self.game_state_repo.get_game_state()
        party_char_ids_set = set(game_state.party.keys())
        resolved_char_ids = set()

        # Handle special keywords
        special_keywords = {"all", "party"}
        has_special_keyword = any(
            keyword in req_char_ids_input for keyword in special_keywords
        )

        if has_special_keyword:
            if "all" in req_char_ids_input:
                if game_state.combat.is_active:
                    # Include only non-defeated combatants
                    for c in game_state.combat.combatants:
                        from app.services.character_service import CharacterValidator

                        if not CharacterValidator.is_character_defeated(
                            c.id, self.game_state_repo
                        ):
                            resolved_char_ids.add(c.id)
                    logger.info(
                        f"Expanding 'all' in dice request to ACTIVE combatants: {list(resolved_char_ids)}"
                    )
                else:
                    # All party members if not in combat
                    resolved_char_ids.update(party_char_ids_set)
                    logger.info(
                        f"Expanding 'all' in dice request to party members: {list(resolved_char_ids)}"
                    )

            if "party" in req_char_ids_input:
                if game_state.combat.is_active:
                    # Include only non-defeated party members in combat
                    for c in game_state.combat.combatants:
                        if c.id in party_char_ids_set:
                            from app.services.character_service import (
                                CharacterValidator,
                            )

                            if not CharacterValidator.is_character_defeated(
                                c.id, self.game_state_repo
                            ):
                                resolved_char_ids.add(c.id)
                    logger.info(
                        f"Expanding 'party' in dice request to ACTIVE party members: {list(resolved_char_ids)}"
                    )
                else:
                    # All party members if not in combat
                    resolved_char_ids.update(party_char_ids_set)
                    logger.info(
                        f"Expanding 'party' in dice request to party members: {list(resolved_char_ids)}"
                    )

            # Add any other specific IDs mentioned alongside special keywords
            for specific_id in req_char_ids_input:
                if specific_id not in special_keywords:
                    resolved = self.character_service.find_character_by_name_or_id(
                        specific_id
                    )
                    if resolved:
                        resolved_char_ids.add(resolved)
        else:
            # Resolve specific IDs
            for specific_id_input in req_char_ids_input:
                resolved = self.character_service.find_character_by_name_or_id(
                    specific_id_input
                )
                if resolved:
                    resolved_char_ids.add(resolved)
                else:
                    logger.warning(
                        f"Could not resolve ID '{specific_id_input}' in dice request."
                    )

        # Sort to ensure deterministic order
        return sorted(list(resolved_char_ids))

    def _force_initiative_rolls(
        self,
        player_requests: List[DiceRequestModel],
        npc_requests: List[Dict[str, Any]],
        party_char_ids_set: set[Any],
    ) -> None:
        """Force initiative rolls if combat started but AI didn't request them."""
        logger.warning(
            "Combat started, but AI did not request initiative. Forcing initiative roll."
        )

        game_state = self.game_state_repo.get_game_state()
        ids_needing_init = [
            c.id for c in game_state.combat.combatants if c.initiative == -1
        ]

        if ids_needing_init:
            request_id = f"forced_init_{random.randint(1000, 9999)}"

            # Separate player/NPC for the forced request
            player_ids_forced = [
                cid for cid in ids_needing_init if cid in party_char_ids_set
            ]
            npc_ids_forced = [
                cid for cid in ids_needing_init if cid not in party_char_ids_set
            ]

            if player_ids_forced:
                # Create a proper DiceRequestModel object for player characters
                player_dice_request = DiceRequestModel(
                    request_id=request_id,
                    character_ids=player_ids_forced,
                    type="initiative",
                    dice_formula="1d20",
                    reason="Combat Started! Roll Initiative!",
                )
                player_requests.insert(0, player_dice_request)

                # Emit PlayerDiceRequestAddedEvent for forced initiative
                if self.event_queue:
                    for char_id in player_ids_forced:
                        char_name = self.character_service.get_character_name(char_id)
                        event = PlayerDiceRequestAddedEvent(
                            request_id=request_id,
                            character_id=char_id,
                            character_name=char_name,
                            roll_type="initiative",
                            dice_formula="1d20",
                            purpose="Combat Started! Roll Initiative!",
                            dc=None,
                            skill=None,
                            ability=None,
                            correlation_id=self.correlation_id,
                        )
                        self.event_queue.put_event(event)

            if npc_ids_forced:
                # NOTE: NPC requests still use dict format for internal processing
                # (see comment above about transient vs persistent data)
                npc_part = {
                    "request_id": request_id,
                    "character_ids": npc_ids_forced,
                    "type": "initiative",
                    "dice_formula": "1d20",
                    "reason": "Combat Started! Roll Initiative!",
                }
                npc_requests.insert(0, npc_part)
        else:
            logger.error("Failed to resolve any combatants for forced initiative roll.")

    def _perform_npc_rolls(
        self, npc_requests_to_roll: List[Dict[str, Any]]
    ) -> Tuple[bool, List[DiceRollResultResponseModel]]:
        """Perform NPC rolls internally."""
        if not npc_requests_to_roll:
            return False, []

        game_state = self.game_state_repo.get_game_state()
        npc_roll_results: List[DiceRollResultResponseModel] = []
        npc_rolls_performed = False

        logger.info(
            f"Performing {len(npc_requests_to_roll)} NPC roll request(s) internally..."
        )

        for npc_req in npc_requests_to_roll:
            for npc_id in npc_req.get("character_ids", []):
                # Check if NPC is defeated
                from app.services.character_service import CharacterValidator

                if CharacterValidator.is_character_defeated(
                    npc_id, self.game_state_repo
                ):
                    logger.debug(
                        f"Skipping roll for defeated NPC: {self.character_service.get_character_name(npc_id)} ({npc_id})"
                    )
                    continue

                # Perform the roll
                roll_type = npc_req.get("type", "")
                dice_formula = npc_req.get("dice_formula", "")
                if not roll_type or not dice_formula:
                    logger.error(
                        f"Missing required fields for NPC roll: type={roll_type}, formula={dice_formula}"
                    )
                    continue

                roll_result = self.dice_service.perform_roll(
                    character_id=npc_id,
                    roll_type=roll_type,
                    dice_formula=dice_formula,
                    skill=npc_req.get("skill"),
                    ability=npc_req.get("ability"),
                    dc=npc_req.get("dc"),
                    reason=npc_req.get("reason", ""),
                    original_request_id=npc_req.get("request_id"),
                )

                if not roll_result.error:
                    npc_roll_results.append(roll_result)
                    npc_rolls_performed = True

                    # Emit NpcDiceRollProcessedEvent
                    if self.event_queue:
                        character_name = self.character_service.get_character_name(
                            npc_id
                        )
                        event = NpcDiceRollProcessedEvent(
                            character_id=npc_id,
                            character_name=character_name,
                            roll_type=npc_req.get("type", ""),
                            dice_formula=npc_req.get("dice_formula", ""),
                            total=roll_result.total_result,
                            details=roll_result.result_message,
                            success=roll_result.success,
                            purpose=npc_req.get("reason", ""),
                            correlation_id=self.correlation_id,
                        )
                        self.event_queue.put_event(event)
                        logger.debug(
                            f"Emitted NpcDiceRollProcessedEvent for {character_name}: {npc_req.get('type', '')} roll"
                        )

                    # For initiative rolls, immediately update the combatant and emit event
                    if roll_type == "initiative" and game_state.combat.is_active:
                        combatant = game_state.combat.get_combatant_by_id(npc_id)
                        if combatant:
                            combatant.initiative = roll_result.total_result
                            logger.info(
                                f"Set initiative for NPC {combatant.name}: {roll_result.total_result}"
                            )

                            # Emit CombatantInitiativeSetEvent for immediate frontend update
                            if self.event_queue:
                                from app.models.events import (
                                    CombatantInitiativeSetEvent,
                                )

                                roll_details = (
                                    f"Roll result: {roll_result.total_result}"
                                )
                                init_event = CombatantInitiativeSetEvent(
                                    combatant_id=combatant.id,
                                    combatant_name=combatant.name,
                                    initiative_value=combatant.initiative,
                                    roll_details=roll_details,
                                    correlation_id=self.correlation_id,
                                )
                                self.event_queue.put_event(init_event)
                                logger.debug(
                                    f"Emitted CombatantInitiativeSetEvent for NPC {combatant.name}"
                                )
                else:
                    # Error case
                    error_msg = f"(Error rolling for NPC {self.character_service.get_character_name(npc_id)}: {roll_result.error})"
                    logger.error(error_msg)
                    self.chat_service.add_message(
                        "system", error_msg, is_dice_result=True
                    )

        # Store NPC roll results and add to history
        if npc_roll_results:
            # npc_roll_results already contains DiceRollResultResponseModel instances
            game_state._pending_npc_roll_results.extend(npc_roll_results)
            self._add_npc_rolls_to_history(npc_roll_results)

            # Save game state if we updated any initiatives
            has_initiative_rolls = any(
                r.roll_type == "initiative" for r in npc_roll_results
            )
            if has_initiative_rolls and game_state.combat.is_active:
                self.game_state_repo.save_game_state(game_state)
                logger.debug("Saved game state after updating NPC initiatives")

        return npc_rolls_performed, npc_roll_results

    def _add_npc_rolls_to_history(
        self, npc_roll_results: List[DiceRollResultResponseModel]
    ) -> None:
        """Add NPC roll results to chat history."""
        npc_roll_summaries = [
            str(r.result_summary) for r in npc_roll_results if r.result_summary
        ]
        npc_detailed_messages = [
            message
            for r in npc_roll_results
            if (message := str(r.result_message or r.result_summary or ""))
        ]

        if npc_roll_summaries:
            combined_summary = "**NPC Rolls:**\n" + "\n".join(npc_roll_summaries)
            combined_detailed = "**NPC Rolls:**\n" + "\n".join(npc_detailed_messages)
            self.chat_service.add_message(
                "user",
                combined_summary,
                is_dice_result=True,
                detailed_content=combined_detailed,
            )
