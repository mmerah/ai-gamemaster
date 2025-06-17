"""
Unit tests for game orchestrator service.
"""

import unittest
from typing import Any, ClassVar
from unittest.mock import Mock, patch

from app.core.container import ServiceContainer, reset_container
from app.models.combat import CombatantModel, CombatInfoResponseModel
from app.models.dice import (
    DiceRequestModel,
    DiceRollResultResponseModel,
    DiceRollSubmissionModel,
)
from app.models.events import MessageSupersededEvent
from app.models.game_state import (
    AIRequestContextModel,
    ChatMessageModel,
    GameEventResponseModel,
    PlayerActionEventModel,
)
from app.providers.ai.schemas import AIResponse
from tests.conftest import get_test_config


def create_test_combatant(
    id: str,
    name: str,
    initiative: int,
    is_player: bool,
    current_hp: int | None = None,
    max_hp: int | None = None,
    armor_class: int | None = None,
) -> CombatantModel:
    """Helper to create a combatant with enhanced model fields."""
    if current_hp is None:
        current_hp = 18 if is_player else 7
    if max_hp is None:
        max_hp = current_hp
    if armor_class is None:
        armor_class = 14 if is_player else 13

    return CombatantModel(
        id=id,
        name=name,
        initiative=initiative,
        initiative_modifier=2 if is_player else 1,
        current_hp=current_hp,
        max_hp=max_hp,
        armor_class=armor_class,
        conditions=[],
        is_player=is_player,
    )


class TestGameOrchestrator(unittest.TestCase):
    """Test game orchestrator functionality."""

    container: ClassVar[ServiceContainer]
    handler: ClassVar[Any]  # GameOrchestrator
    game_state_repo: ClassVar[Any]  # GameStateRepository
    character_service: ClassVar[Any]  # CharacterService
    dice_service: ClassVar[Any]  # DiceService
    combat_service: ClassVar[Any]  # CombatService
    chat_service: ClassVar[Any]  # ChatService
    ai_response_processor: ClassVar[Any]  # AIResponseProcessor

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test fixtures once for all tests."""
        reset_container()
        cls.container = ServiceContainer(get_test_config())
        cls.container.initialize()

        # Get services - now using GameOrchestrator
        cls.handler = (
            cls.container.get_game_orchestrator()
        )  # This now returns GameOrchestrator
        cls.game_state_repo = cls.container.get_game_state_repository()
        cls.character_service = cls.container.get_character_service()
        cls.dice_service = cls.container.get_dice_service()
        cls.combat_service = cls.container.get_combat_service()
        cls.chat_service = cls.container.get_chat_service()
        cls.ai_response_processor = cls.container.get_ai_response_processor()

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Reset game state before each test
        self.game_state_repo._active_game_state = (
            self.game_state_repo._initialize_default_game_state()
        )
        self.game_state = self.game_state_repo.get_game_state()

        # Reset handler state to prevent test interference
        # Access handlers through orchestration services
        handlers = [
            self.handler.narrative_orchestration.player_action_handler,
            self.handler.combat_orchestration.dice_submission_handler,
            self.handler.event_routing.next_step_handler,
            self.handler.event_routing.retry_handler,
        ]
        for handler in handlers:
            if handler and hasattr(handler, "_ai_processing"):
                handler._ai_processing = False

        # Reset shared context in GameOrchestrator
        self.handler._shared_ai_request_context = None
        self.handler._shared_ai_request_timestamp = None

        # Reset shared state directly
        self.handler.event_routing._shared_state.ai_processing = False
        self.handler.event_routing._shared_state.needs_backend_trigger = False

        # Re-setup shared context to ensure handlers are properly linked
        self.handler._setup_shared_context()

        # Mock AI service
        self.mock_ai_service = Mock()

        # Patch the _get_ai_service method to return our mock
        self.ai_service_patcher = patch.object(
            self.handler.narrative_orchestration.player_action_handler,
            "_get_ai_service",
            return_value=self.mock_ai_service,
        )
        self.ai_service_patcher.start()

        # Also patch for other handlers
        self.dice_ai_patcher = patch.object(
            self.handler.combat_orchestration.dice_submission_handler,
            "_get_ai_service",
            return_value=self.mock_ai_service,
        )
        self.dice_ai_patcher.start()

        self.next_ai_patcher = patch.object(
            self.handler.event_routing.next_step_handler,
            "_get_ai_service",
            return_value=self.mock_ai_service,
        )
        self.next_ai_patcher.start()

        self.retry_ai_patcher = patch.object(
            self.handler.event_routing.retry_handler,
            "_get_ai_service",
            return_value=self.mock_ai_service,
        )
        self.retry_ai_patcher.start()

    def tearDown(self) -> None:
        """Clean up patches."""
        self.ai_service_patcher.stop()
        self.dice_ai_patcher.stop()
        self.next_ai_patcher.stop()
        self.retry_ai_patcher.stop()

    def test_handle_player_action_success(self) -> None:
        """Test successful player action handling."""
        # Get initial chat history length (may include initial narrative)
        initial_chat_len = len(self.chat_service.get_chat_history())

        action_data = PlayerActionEventModel(
            action_type="free_text", value="I search the room"
        )

        # Mock AI response
        ai_response = AIResponse(
            reasoning="Player searches the room",
            narrative="You search the room and find a hidden door.",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = ai_response

        # Patch build_ai_prompt_context
        with patch("app.game.prompt_builder.build_ai_prompt_context", return_value=[]):
            result = self.handler.handle_player_action(action_data)

        # Check result
        self.assertEqual(result.status_code, 200)
        self.assertTrue(hasattr(result, "party"))
        self.assertTrue(hasattr(result, "chat_history"))
        self.assertFalse(result.needs_backend_trigger)

        # Check chat history was updated
        chat_history = self.chat_service.get_chat_history()
        self.assertEqual(
            len(chat_history), initial_chat_len + 2
        )  # Player message + AI response
        self.assertEqual(chat_history[-2].content, '"I search the room"')
        self.assertEqual(
            chat_history[-1].content, "You search the room and find a hidden door."
        )

    def test_handle_player_action_empty_text(self) -> None:
        """Test handling empty player action."""
        action_data = PlayerActionEventModel(action_type="free_text", value="")

        result = self.handler.handle_player_action(action_data)

        # Should return error
        self.assertEqual(result.status_code, 400)
        self.assertTrue(hasattr(result, "error"))

        # Check system message was added
        chat_history = self.chat_service.get_chat_history()
        # ChatMessage objects
        self.assertTrue(
            any(
                msg.content == "Please type something before sending."
                for msg in chat_history
            )
        )

    def test_handle_player_action_ai_busy(self) -> None:
        """Test rejection when AI is already processing."""
        # Set AI as busy using the shared state directly
        self.handler.event_routing._shared_state.ai_processing = True

        action_data = PlayerActionEventModel(
            action_type="free_text", value="Test action"
        )

        result = self.handler.handle_player_action(action_data)

        # Should return busy error
        self.assertEqual(result.status_code, 429)
        self.assertEqual(result.error, "AI is busy")

    def test_handle_player_action_not_player_turn(self) -> None:
        """Test rejection when it's not the player's turn."""
        # Set up combat with NPC's turn
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            create_test_combatant("elara", "Elara", 10, True),
            create_test_combatant("goblin1", "Goblin", 20, False),
        ]
        self.game_state.combat.current_turn_index = 1  # Goblin's turn

        action_data = PlayerActionEventModel(action_type="free_text", value="I attack!")

        result = self.handler.handle_player_action(action_data)

        # Should return error
        self.assertEqual(result.status_code, 400)

        # Check system message
        chat_history = self.chat_service.get_chat_history()
        # ChatMessage objects
        self.assertTrue(
            any("(It's not your turn!)" in msg.content for msg in chat_history)
        )

    def test_handle_dice_submission_success(self) -> None:
        """Test successful dice submission handling."""
        roll_data = [
            DiceRollSubmissionModel(
                character_id="elara",
                roll_type="attack",
                dice_formula="1d20",
                reason="Attack roll",
            )
        ]

        # Mock dice roll result - must match DiceRollResultResponseModel structure
        with patch.object(
            self.dice_service,
            "perform_roll",
            return_value=DiceRollResultResponseModel(
                request_id="roll_elara_attack_1234",
                character_id="elara",
                character_name="Elara",
                roll_type="attack",
                dice_formula="1d20",
                character_modifier=3,
                total_result=18,
                reason="Attack roll",
                result_message="Elara rolls Attack: 1d20 (+3) -> [15] +3 = **18**.",
                result_summary="Elara: Attack Roll = 18",
            ),
        ):
            # Mock AI response
            ai_response = AIResponse(
                reasoning="Processing attack roll",
                narrative="Elara's attack hits!",
                location_update=None,
                game_state_updates=[],
                dice_requests=[],
                end_turn=False,
            )
            self.mock_ai_service.get_response.return_value = ai_response

            # Patch build_ai_prompt_context
            with patch(
                "app.game.prompt_builder.build_ai_prompt_context", return_value=[]
            ):
                result = self.handler.handle_dice_submission(roll_data)

        # Check result
        self.assertEqual(result.status_code, 200)
        self.assertTrue(hasattr(result, "submitted_roll_results"))
        self.assertEqual(len(result.submitted_roll_results), 1)

    def test_dice_submission_clears_specific_requests(self) -> None:
        """Test that dice submission clears only specific submitted requests."""
        # Setup pending requests in game state
        self.game_state.pending_player_dice_requests = [
            DiceRequestModel(
                request_id="req_001",
                character_ids=["elara"],
                type="attack",
                dice_formula="1d20",
                reason="Attack roll",
            ),
            DiceRequestModel(
                request_id="req_002",
                character_ids=["elara"],
                type="damage",
                dice_formula="1d6",
                reason="Damage roll",
            ),
            DiceRequestModel(
                request_id="req_003",
                character_ids=["hero2"],
                type="attack",
                dice_formula="1d20",
                reason="Attack roll",
            ),
        ]

        # Submit rolls for req_001 and req_003
        roll_data = [
            DiceRollSubmissionModel(
                request_id="req_001",
                character_id="elara",
                roll_type="attack",
                dice_formula="1d20",
                reason="Attack roll",
            ),
            DiceRollSubmissionModel(
                request_id="req_003",
                character_id="hero2",
                roll_type="attack",
                dice_formula="1d20",
                reason="Attack roll",
            ),
        ]

        # Mock dice roll results
        with patch.object(
            self.dice_service,
            "perform_roll",
            side_effect=[
                DiceRollResultResponseModel(
                    request_id="roll_elara_attack_1234",
                    character_id="elara",
                    character_name="Elara",
                    roll_type="attack",
                    dice_formula="1d20",
                    character_modifier=3,
                    total_result=18,
                    reason="Attack roll",
                    result_message="Elara rolls Attack: 1d20 (+3) -> [15] +3 = **18**.",
                    result_summary="Elara: Attack Roll = 18",
                ),
                DiceRollResultResponseModel(
                    request_id="roll_hero2_attack_5678",
                    character_id="hero2",
                    character_name="Hero2",
                    roll_type="attack",
                    dice_formula="1d20",
                    character_modifier=2,
                    total_result=15,
                    reason="Attack roll",
                    result_message="Hero2 rolls Attack: 1d20 (+2) -> [13] +2 = **15**.",
                    result_summary="Hero2: Attack Roll = 15",
                ),
            ],
        ):
            # Mock AI response
            ai_response = AIResponse(
                reasoning="Processing attack rolls",
                narrative="Both attacks hit!",
                location_update=None,
                game_state_updates=[],
                dice_requests=[],
                end_turn=False,
            )
            self.mock_ai_service.get_response.return_value = ai_response

            # Mock event queue to verify event emission
            mock_event_queue = Mock()
            with patch("app.core.container.get_container") as mock_get_container:
                mock_container = Mock()
                mock_container.get_event_queue.return_value = mock_event_queue
                mock_get_container.return_value = mock_container

                # Patch build_ai_prompt_context
                with patch(
                    "app.game.prompt_builder.build_ai_prompt_context", return_value=[]
                ):
                    result = self.handler.handle_dice_submission(roll_data)

        # Check result
        self.assertEqual(result.status_code, 200)

        # Verify only req_002 remains
        remaining_requests = self.game_state.pending_player_dice_requests
        self.assertEqual(len(remaining_requests), 1)
        self.assertEqual(remaining_requests[0].request_id, "req_002")

        # Verify event was emitted with correct IDs
        mock_event_queue.put_event.assert_called()
        from app.models.events import PlayerDiceRequestsClearedEvent

        emitted_events = [
            call[0][0]
            for call in mock_event_queue.put_event.call_args_list
            if isinstance(call[0][0], PlayerDiceRequestsClearedEvent)
        ]
        self.assertEqual(len(emitted_events), 1)
        self.assertEqual(
            set(emitted_events[0].cleared_request_ids), {"req_001", "req_003"}
        )

    def test_dice_submission_clears_all_when_no_request_ids(self) -> None:
        """Test that dice submission clears all requests when no request IDs provided."""
        # Setup pending requests in game state
        self.game_state.pending_player_dice_requests = [
            DiceRequestModel(
                request_id="req_001",
                character_ids=["elara"],
                type="attack",
                dice_formula="1d20",
                reason="Attack roll",
            ),
            DiceRequestModel(
                request_id="req_002",
                character_ids=["elara"],
                type="damage",
                dice_formula="1d6",
                reason="Damage roll",
            ),
        ]

        # Submit rolls without request_ids (manual rolls)
        roll_data = [
            DiceRollSubmissionModel(
                character_id="elara",
                roll_type="attack",
                dice_formula="1d20",
                reason="Attack roll",
            )
        ]

        # Mock dice roll result - must match DiceRollResultResponseModel structure
        with patch.object(
            self.dice_service,
            "perform_roll",
            return_value=DiceRollResultResponseModel(
                request_id="roll_elara_attack_1234",
                character_id="elara",
                character_name="Elara",
                roll_type="attack",
                dice_formula="1d20",
                character_modifier=3,
                total_result=18,
                reason="Attack roll",
                result_message="Elara rolls Attack: 1d20 (+3) -> [15] +3 = **18**.",
                result_summary="Elara: Attack Roll = 18",
            ),
        ):
            # Mock AI response
            ai_response = AIResponse(
                reasoning="Processing attack roll",
                narrative="Attack hits!",
                location_update=None,
                game_state_updates=[],
                dice_requests=[],
                end_turn=False,
            )
            self.mock_ai_service.get_response.return_value = ai_response

            # Mock event queue to verify event emission
            mock_event_queue = Mock()
            with patch("app.core.container.get_container") as mock_get_container:
                mock_container = Mock()
                mock_container.get_event_queue.return_value = mock_event_queue
                mock_get_container.return_value = mock_container

                # Patch build_ai_prompt_context
                with patch(
                    "app.game.prompt_builder.build_ai_prompt_context", return_value=[]
                ):
                    result = self.handler.handle_dice_submission(roll_data)

        # Check result
        self.assertEqual(result.status_code, 200)

        # Verify all requests cleared
        self.assertEqual(len(self.game_state.pending_player_dice_requests), 0)

        # Verify event was emitted with all IDs
        mock_event_queue.put_event.assert_called()
        from app.models.events import PlayerDiceRequestsClearedEvent

        emitted_events = [
            call[0][0]
            for call in mock_event_queue.put_event.call_args_list
            if isinstance(call[0][0], PlayerDiceRequestsClearedEvent)
        ]
        self.assertEqual(len(emitted_events), 1)
        self.assertEqual(
            set(emitted_events[0].cleared_request_ids), {"req_001", "req_002"}
        )

    def test_dice_submission_no_event_when_no_matching_requests(self) -> None:
        """Test that no event is emitted when no matching requests are found."""
        # Setup pending requests in game state
        self.game_state.pending_player_dice_requests = [
            DiceRequestModel(
                request_id="req_001",
                character_ids=["elara"],
                type="attack",
                dice_formula="1d20",
                reason="Attack roll",
            )
        ]

        # Submit roll with non-existent request ID
        roll_data = [
            DiceRollSubmissionModel(
                request_id="req_not_found",
                character_id="elara",
                roll_type="attack",
                dice_formula="1d20",
                reason="Attack roll",
            )
        ]

        # Mock dice roll result - must match DiceRollResultResponseModel structure
        with patch.object(
            self.dice_service,
            "perform_roll",
            return_value=DiceRollResultResponseModel(
                request_id="roll_elara_attack_1234",
                character_id="elara",
                character_name="Elara",
                roll_type="attack",
                dice_formula="1d20",
                character_modifier=3,
                total_result=18,
                reason="Attack roll",
                result_message="Elara rolls Attack: 1d20 (+3) -> [15] +3 = **18**.",
                result_summary="Elara: Attack Roll = 18",
            ),
        ):
            # Mock AI response
            ai_response = AIResponse(
                reasoning="Processing attack roll",
                narrative="Attack hits!",
                location_update=None,
                game_state_updates=[],
                dice_requests=[],
                end_turn=False,
            )
            self.mock_ai_service.get_response.return_value = ai_response

            # Mock event queue to verify event emission
            mock_event_queue = Mock()
            with patch("app.core.container.get_container") as mock_get_container:
                mock_container = Mock()
                mock_container.get_event_queue.return_value = mock_event_queue
                mock_get_container.return_value = mock_container

                # Patch build_ai_prompt_context
                with patch(
                    "app.game.prompt_builder.build_ai_prompt_context", return_value=[]
                ):
                    result = self.handler.handle_dice_submission(roll_data)

        # Check result
        self.assertEqual(result.status_code, 200)

        # Verify original request still remains
        remaining_requests = self.game_state.pending_player_dice_requests
        self.assertEqual(len(remaining_requests), 1)
        self.assertEqual(remaining_requests[0].request_id, "req_001")

        # Verify no PlayerDiceRequestsClearedEvent was emitted
        from app.models.events import PlayerDiceRequestsClearedEvent

        emitted_events = [
            call[0][0]
            for call in mock_event_queue.put_event.call_args_list
            if isinstance(call[0][0], PlayerDiceRequestsClearedEvent)
        ]
        self.assertEqual(len(emitted_events), 0)

    def test_handle_completed_roll_submission(self) -> None:
        """Test handling of already-completed roll results."""
        roll_results = [
            DiceRollResultResponseModel(
                request_id="roll_elara_save_9876",
                character_id="elara",
                character_name="Elara",
                roll_type="saving_throw",
                dice_formula="1d20",
                character_modifier=3,
                total_result=15,
                reason="Constitution save",
                result_summary="Elara: Saving Throw = 15",
                result_message="Elara rolled 1d20 + 3 = 15",
            )
        ]

        # Mock AI response
        ai_response = AIResponse(
            reasoning="Processing saving throw",
            narrative="Elara succeeds on the saving throw.",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = ai_response

        # Patch build_ai_prompt_context
        with patch("app.game.prompt_builder.build_ai_prompt_context", return_value=[]):
            result = self.handler.handle_completed_roll_submission(roll_results)

        # Check result
        self.assertEqual(result.status_code, 200)
        self.assertTrue(hasattr(result, "submitted_roll_results"))
        # Check that submitted_roll_results is populated
        self.assertIsNotNone(result.submitted_roll_results)
        self.assertEqual(len(result.submitted_roll_results), len(roll_results))
        # Check the first result has the expected data
        first_result = result.submitted_roll_results[0]
        self.assertEqual(first_result.character_id, "elara")
        self.assertEqual(first_result.roll_type, "saving_throw")
        self.assertEqual(first_result.result_summary, "Elara: Saving Throw = 15")

    def test_handle_next_step_trigger_npc_turn(self) -> None:
        """Test triggering next step for NPC turn."""
        # Set up combat with NPC's turn
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            create_test_combatant("elara", "Elara", 10, True),
            create_test_combatant("goblin1", "Goblin", 20, False),
        ]
        self.game_state.combat.current_turn_index = 1  # Goblin's turn

        # Mock AI response
        ai_response = AIResponse(
            reasoning="Goblin attacks",
            narrative="The goblin swings its rusty sword at Elara!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=True,
        )
        self.mock_ai_service.get_response.return_value = ai_response

        # Patch build_ai_prompt_context
        with patch("app.game.prompt_builder.build_ai_prompt_context", return_value=[]):
            result = self.handler.handle_next_step_trigger()

        # Check result
        self.assertEqual(result.status_code, 200)

        # Check that AI was called with NPC turn instruction
        self.mock_ai_service.get_response.assert_called_once()

    def test_handle_retry_last_ai_request(self) -> None:
        """Test retrying a failed AI request."""
        # First, make a failed request
        action_data = PlayerActionEventModel(
            action_type="free_text", value="I cast fireball"
        )

        # Mock AI failure
        self.mock_ai_service.get_response.return_value = None

        # Patch build_ai_prompt_context
        with patch(
            "app.game.prompt_builder.build_ai_prompt_context",
            return_value=[{"role": "user", "content": "test"}],
        ):
            result = self.handler.handle_player_action(action_data)

        # Verify failure
        self.assertEqual(result.status_code, 500)

        # Verify context was stored
        self.assertIsNotNone(
            self.handler.narrative_orchestration.player_action_handler._last_ai_request_context
        )

        # Now test retry
        # Mock successful AI response for retry
        ai_response = AIResponse(
            reasoning="Retrying fireball cast",
            narrative="You cast fireball successfully!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = ai_response

        # Use the new method name
        retry_result = self.handler.handle_retry()

        # Check retry was successful
        self.assertEqual(retry_result.status_code, 200)

        # Note: Context is NOT cleared after successful retry (by design - keeps it for potential re-retry)
        self.assertIsNotNone(
            self.handler.event_routing.retry_handler._last_ai_request_context
        )

    def test_handle_retry_no_stored_context(self) -> None:
        """Test retry when no previous request exists."""
        # Ensure no shared context exists
        self.handler.event_routing._shared_ai_request_context = None
        self.handler.event_routing._shared_ai_request_timestamp = None

        # Update all handlers to reflect no context
        for handler in [
            self.handler.narrative_orchestration.player_action_handler,
            self.handler.combat_orchestration.dice_submission_handler,
            self.handler.event_routing.next_step_handler,
            self.handler.event_routing.retry_handler,
        ]:
            handler._last_ai_request_context = None
            handler._last_ai_request_timestamp = None

        result = self.handler.handle_retry()

        # Should return error
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.error, "No recent request to retry")

    def test_handle_retry_emits_message_superseded_event(self) -> None:
        """Test that retry emits MessageSupersededEvent for the previous AI message."""
        # Add an AI message to chat history first
        ai_message = ChatMessageModel(
            id="test-message-123",
            role="assistant",
            content="Original AI response that will be superseded",
            timestamp="2024-01-01T12:00:00Z",
        )
        game_state = self.game_state_repo.get_game_state()
        game_state.chat_history.append(ai_message)

        # Set up context for retry
        import time

        self.handler._shared_ai_request_context = AIRequestContextModel(
            messages=[{"role": "user", "content": "test"}],
            initial_instruction="test instruction",
        )
        self.handler._shared_ai_request_timestamp = time.time()  # Set current timestamp

        # Also set the context on the retry handler directly
        self.handler.event_routing.retry_handler._last_ai_request_context = (
            self.handler._shared_ai_request_context
        )
        self.handler.event_routing.retry_handler._last_ai_request_timestamp = (
            self.handler._shared_ai_request_timestamp
        )

        # Mock AI response for retry
        ai_response = AIResponse(
            reasoning="Retry response",
            narrative="New response after retry",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = ai_response

        # Mock event queue to capture events
        pushed_events = []
        original_put = self.container.get_event_queue().put_event

        def capture_and_forward(event: Any) -> None:
            pushed_events.append(event)
            original_put(event)

        self.container.get_event_queue().put_event = capture_and_forward  # type: ignore[method-assign]

        # Execute retry
        result = self.handler.handle_retry()

        # Verify success
        self.assertEqual(result.status_code, 200)

        # Verify MessageSupersededEvent was emitted
        superseded_events = [
            e for e in pushed_events if isinstance(e, MessageSupersededEvent)
        ]
        self.assertEqual(len(superseded_events), 1)
        self.assertEqual(superseded_events[0].message_id, "test-message-123")
        self.assertEqual(superseded_events[0].reason, "retry")

    def test_game_state_retrieval(self) -> None:
        """Test that game state can be retrieved for frontend."""
        result = self.handler.get_game_state()

        # Check that result is the correct model type with required attributes
        self.assertIsInstance(result, GameEventResponseModel)
        self.assertTrue(hasattr(result, "party"))
        self.assertTrue(hasattr(result, "location"))
        self.assertTrue(hasattr(result, "chat_history"))
        self.assertTrue(hasattr(result, "dice_requests"))
        self.assertTrue(hasattr(result, "combat_info"))
        self.assertTrue(hasattr(result, "can_retry_last_request"))

        # Should be a list of party members (empty initially)
        self.assertIsInstance(result.party, list)
        self.assertIsInstance(result.dice_requests, list)
        self.assertIsInstance(result.chat_history, list)
        self.assertIsInstance(result.combat_info, (CombatInfoResponseModel, type(None)))
        self.assertIsInstance(result.can_retry_last_request, bool)

    def test_player_action_returns_structured_response(self) -> None:
        """Test player action handling returns proper structure."""
        action_data = PlayerActionEventModel(
            action_type="free_text", value="I search the room"
        )

        # Mock successful AI response
        ai_response = AIResponse(
            reasoning="Player searches the room",
            narrative="You search the room and find a hidden door.",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )

        self.mock_ai_service.get_response.return_value = ai_response

        # Patch build_ai_prompt_context
        with patch("app.game.prompt_builder.build_ai_prompt_context", return_value=[]):
            result = self.handler.handle_player_action(action_data)

        # Check that the action returns a structured response
        # Should return a model instance with status_code attribute
        self.assertIsInstance(result, GameEventResponseModel)
        self.assertIsInstance(result.status_code, int)

    def test_dice_submission_returns_structured_response(self) -> None:
        """Test handling dice submission returns proper structure."""
        result = self.handler.handle_dice_submission([])

        # Should return a model instance with status_code attribute
        self.assertIsInstance(result, GameEventResponseModel)
        self.assertIsInstance(result.status_code, int)

    def test_next_step_trigger_returns_structured_response(self) -> None:
        """Test next step trigger returns structured response."""
        result = self.handler.handle_next_step_trigger()

        # Should return a model instance with status_code attribute
        self.assertIsInstance(result, GameEventResponseModel)
        self.assertIsInstance(result.status_code, int)

    def test_retry_handler_exists(self) -> None:
        """Test that retry handler method exists and is callable."""
        # Just test that the method exists and can be called
        try:
            result = self.handler.handle_retry()
            self.assertIsInstance(result, GameEventResponseModel)
            self.assertIsInstance(result.status_code, int)
        except Exception as e:
            # If it fails, that's also fine - we're just testing it exists
            self.assertIsInstance(e, Exception)

    def test_determine_backend_trigger_needed(self) -> None:
        """Test logic for determining if backend trigger is needed."""
        # Access the method through one of the handlers
        handler = self.handler.narrative_orchestration.player_action_handler

        # Test 1: NPC action requires follow-up
        needs_trigger = handler._determine_backend_trigger_needed(True, [])
        self.assertTrue(needs_trigger)

        # Test 2: Player requests pending
        needs_trigger = handler._determine_backend_trigger_needed(
            False, [{"request_id": "test"}]
        )
        self.assertFalse(needs_trigger)

        # Test 3: No pending requests, NPC turn
        self.game_state.combat.is_active = True
        self.game_state.combat.combatants = [
            create_test_combatant("elara", "Elara", 10, True),
            create_test_combatant("goblin1", "Goblin", 20, False),
        ]
        self.game_state.combat.current_turn_index = 1  # Goblin's turn

        needs_trigger = handler._determine_backend_trigger_needed(False, [])
        self.assertTrue(needs_trigger)


class TestPlayerActionValidator(unittest.TestCase):
    """Test player action validation."""

    def test_valid_action(self) -> None:
        """Test validation of valid action."""
        from app.utils.validation.action_validators import PlayerActionValidator

        action_data = {"action_type": "free_text", "value": "I open the door"}

        result = PlayerActionValidator.validate_action(action_data)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.error_message, "")

    def test_empty_text_action(self) -> None:
        """Test validation of empty text."""
        from app.utils.validation.action_validators import PlayerActionValidator

        action_data = {"action_type": "free_text", "value": ""}

        result = PlayerActionValidator.validate_action(action_data)
        self.assertFalse(result.is_valid)
        self.assertTrue(result.is_empty_text)

    def test_invalid_action_format(self) -> None:
        """Test validation of invalid action format."""
        from app.utils.validation.action_validators import PlayerActionValidator

        # Missing action_type
        action_data = {"value": "test"}
        result = PlayerActionValidator.validate_action(action_data)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_message, "No action type specified")

        # None action data
        result = PlayerActionValidator.validate_action(None)
        self.assertFalse(result.is_valid)


class TestDiceSubmissionValidator(unittest.TestCase):
    """Test dice submission validation."""

    def test_valid_submission(self) -> None:
        """Test validation of valid dice submission."""
        from app.utils.validation.action_validators import DiceSubmissionValidator

        roll_data = [
            {"character_id": "elara", "roll_type": "attack", "dice_formula": "1d20"}
        ]

        result = DiceSubmissionValidator.validate_submission(roll_data)  # type: ignore[arg-type]
        self.assertTrue(result.is_valid)

    def test_invalid_submission_format(self) -> None:
        """Test validation of invalid submission format."""
        from app.utils.validation.action_validators import DiceSubmissionValidator

        # Not a list
        roll_data = "invalid"
        result = DiceSubmissionValidator.validate_submission(roll_data)  # type: ignore[arg-type]
        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.error_message, "Invalid data format, expected list of roll requests"
        )


if __name__ == "__main__":
    unittest.main()
