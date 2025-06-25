"""
Unit tests for game orchestrator service.
"""

import asyncio
import unittest
from typing import Any, ClassVar
from unittest.mock import Mock, patch

import pytest

from app.core.container import ServiceContainer, reset_container
from app.domain.combat.combat_utilities import CombatFormatter
from app.models.character.instance import CharacterInstanceModel
from app.models.combat.combatant import CombatantModel, InitialCombatantData
from app.models.common import MessageDict
from app.models.dice import (
    DiceRequestModel,
    DiceRollResultResponseModel,
    DiceRollSubmissionModel,
)
from app.models.events.event_types import GameEventType
from app.models.events.game_events import GameEventModel, PlayerActionEventModel
from app.providers.ai.schemas import AIResponse
from tests.conftest import get_test_settings


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


def create_test_initial_combatant(
    id: str,
    name: str,
    hp: int | None = None,
    ac: int | None = None,
) -> InitialCombatantData:
    """Helper to create initial combatant data for combat start."""
    if hp is None:
        hp = 18
    if ac is None:
        ac = 14

    return InitialCombatantData(
        id=id,
        name=name,
        hp=hp,
        ac=ac,
    )


class TestGameOrchestrator(unittest.TestCase):
    """Test game orchestrator functionality."""

    container: ClassVar[ServiceContainer]
    handler: ClassVar[Any]  # GameOrchestrator
    game_state_repo: ClassVar[Any]  # IGameStateRepository
    character_service: ClassVar[Any]  # ICharacterService
    dice_service: ClassVar[Any]  # DiceService
    combat_service: ClassVar[Any]  # ICombatService
    chat_service: ClassVar[Any]  # IChatService
    ai_response_processor: ClassVar[Any]  # IAIResponseProcessor

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test fixtures once for all tests."""
        reset_container()
        cls.container = ServiceContainer(get_test_settings())
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
        # State is now managed by SharedStateManager, no longer on individual handlers

        # Reset shared state using SharedStateManager
        # Get the shared state manager from container
        self.shared_state_manager = self.container.get_shared_state_manager()
        # Reset to clean state
        self.shared_state_manager.reset_state()

        # Re-setup shared context to ensure handlers are properly linked
        self.handler._setup_shared_context()

        # Mock AI service
        self.mock_ai_service = Mock()

        # Patch the _get_ai_service method to return our mock
        self.ai_service_patcher = patch.object(
            self.handler.player_action_handler,
            "_get_ai_service",
            return_value=self.mock_ai_service,
        )
        self.ai_service_patcher.start()

        # Also patch for other handlers
        self.dice_ai_patcher = patch.object(
            self.handler.dice_submission_handler,
            "_get_ai_service",
            return_value=self.mock_ai_service,
        )
        self.dice_ai_patcher.start()

        self.next_ai_patcher = patch.object(
            self.handler.next_step_handler,
            "_get_ai_service",
            return_value=self.mock_ai_service,
        )
        self.next_ai_patcher.start()

        self.retry_ai_patcher = patch.object(
            self.handler.retry_handler,
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
        with patch(
            "app.providers.ai.prompt_builder.build_ai_prompt_context", return_value=[]
        ):
            event = GameEventModel(type=GameEventType.PLAYER_ACTION, data=action_data)
        result = asyncio.run(self.handler.handle_event(event))

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

    def test_handle_player_action_error(self) -> None:
        """Test player action handling with error."""
        action_data = PlayerActionEventModel(action_type="free_text", value="Test")

        # Mock AI service error
        self.mock_ai_service.get_response.side_effect = Exception("AI service error")

        # Check shared state is available
        self.assertIsNotNone(self.handler.player_action_handler._shared_state_manager)

        # Patch build_ai_prompt_context
        with patch(
            "app.providers.ai.prompt_builder.build_ai_prompt_context", return_value=[]
        ):
            event = GameEventModel(type=GameEventType.PLAYER_ACTION, data=action_data)
        result = asyncio.run(self.handler.handle_event(event))

        # Check error response
        self.assertEqual(result.status_code, 500)
        self.assertTrue(hasattr(result, "party"))
        self.assertTrue(hasattr(result, "chat_history"))
        self.assertFalse(result.needs_backend_trigger)

        # Check error message was added to chat
        chat_history = self.chat_service.get_chat_history()
        self.assertTrue(
            any("Error processing AI step" in msg.content for msg in chat_history)
        )

    def test_handle_player_action_ai_busy(self) -> None:
        """Test player action handling when AI is busy."""
        action_data = PlayerActionEventModel(action_type="free_text", value="Test")

        # Set AI as busy using shared state manager
        self.shared_state_manager.set_ai_processing(True)

        event = GameEventModel(type=GameEventType.PLAYER_ACTION, data=action_data)
        result = asyncio.run(self.handler.handle_event(event))

        # Check busy response
        self.assertEqual(result.status_code, 429)
        self.assertTrue(hasattr(result, "party"))
        self.assertTrue(hasattr(result, "chat_history"))

        # No need to check chat history for AI busy message

    def test_handle_dice_submission_success(self) -> None:
        """Test successful dice submission handling."""
        # Add dice request to game state
        dice_request = DiceRequestModel(
            request_id="test-dice-1",
            character_ids=["pc-1"],
            type="attack",
            dice_formula="1d20+3",
            reason="Attack roll",
            dc=15,
        )
        self.game_state.pending_player_dice_requests = [dice_request]
        self.game_state_repo.save_game_state(self.game_state)

        # Create dice submission
        roll_data = [
            DiceRollSubmissionModel(
                character_id="pc-1",
                roll_type="attack",
                dice_formula="1d20+3",
                request_id="test-dice-1",
                total=18,
            )
        ]

        # Mock AI response
        ai_response = AIResponse(
            reasoning="Attack hits",
            narrative="Your attack strikes the goblin!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = ai_response

        # Patch build_ai_prompt_context
        with patch(
            "app.providers.ai.prompt_builder.build_ai_prompt_context",
            return_value=[],
        ):
            event = GameEventModel(
                type=GameEventType.DICE_SUBMISSION, data={"rolls": roll_data}
            )
        result = asyncio.run(self.handler.handle_event(event))

        # Check result
        self.assertEqual(result.status_code, 200)
        self.assertTrue(hasattr(result, "party"))
        self.assertTrue(hasattr(result, "chat_history"))
        self.assertFalse(result.needs_backend_trigger)

        # Check dice requests were cleared
        updated_state = self.game_state_repo.get_game_state()
        self.assertEqual(len(updated_state.pending_player_dice_requests), 0)

    def test_handle_dice_submission_no_matching_request(self) -> None:
        """Test dice submission with no matching request."""
        # Add a character to the party so character validation passes
        char_instance = CharacterInstanceModel(
            id="pc-1",
            name="Test Fighter",
            template_id="fighter-template",
            campaign_id="test-campaign",
            current_hp=20,
            max_hp=20,
            level=1,
        )
        self.game_state.party["pc-1"] = char_instance
        self.game_state_repo.save_game_state(self.game_state)

        # Create dice submission with no matching request
        roll_data = [
            DiceRollSubmissionModel(
                character_id="pc-1",
                roll_type="attack",
                dice_formula="1d20+3",
                request_id="non-existent",
                total=18,
            )
        ]

        # Mock AI response for the case where dice submission is processed
        ai_response = AIResponse(
            reasoning="No matching dice request found",
            narrative="The dice roll is noted but no specific action was requested.",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = ai_response

        # Patch build_ai_prompt_context
        with patch(
            "app.providers.ai.prompt_builder.build_ai_prompt_context", return_value=[]
        ):
            event = GameEventModel(
                type=GameEventType.DICE_SUBMISSION, data={"rolls": roll_data}
            )
        result = asyncio.run(self.handler.handle_event(event))

        # Check result
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.needs_backend_trigger)

    def test_handle_dice_submission_ai_busy(self) -> None:
        """Test dice submission handling when AI is busy."""
        roll_data = [
            DiceRollSubmissionModel(
                character_id="pc-1",
                roll_type="attack",
                dice_formula="1d20+3",
                request_id="test-dice-1",
                total=18,
            )
        ]

        # Set AI as busy
        self.shared_state_manager.set_ai_processing(True)

        event = GameEventModel(
            type=GameEventType.DICE_SUBMISSION, data={"rolls": roll_data}
        )
        result = asyncio.run(self.handler.handle_event(event))

        # Check busy response
        self.assertEqual(result.status_code, 429)
        self.assertTrue(hasattr(result, "party"))
        self.assertTrue(hasattr(result, "chat_history"))

        # No need to check chat history for AI busy message

    def test_handle_completed_roll_submission(self) -> None:
        """Test completed roll submission handling."""
        # Create completed roll results
        roll_results = [
            DiceRollResultResponseModel(
                request_id="test-dice-1",
                character_id="pc-1",
                character_name="Thorin",
                roll_type="attack",
                dice_formula="1d20+3",
                character_modifier=3,
                total_result=18,
                dc=15,
                success=True,
                reason="Attack roll",
                result_message="Thorin's attack hits the goblin!",
                result_summary="Attack Roll: 18 vs AC 15 - Hit!",
            )
        ]

        # Mock AI response
        ai_response = AIResponse(
            reasoning="Attack hits",
            narrative="Your attack strikes the goblin!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = ai_response

        # Patch build_ai_prompt_context
        with patch(
            "app.providers.ai.prompt_builder.build_ai_prompt_context",
            return_value=[],
        ):
            event = GameEventModel(
                type=GameEventType.COMPLETED_ROLL_SUBMISSION,
                data={"roll_results": roll_results},
            )
        result = asyncio.run(self.handler.handle_event(event))

        # Check result
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.needs_backend_trigger)

    def test_handle_next_step_trigger(self) -> None:
        """Test next step trigger handling."""
        # Mock AI response
        ai_response = AIResponse(
            reasoning="Continuing game",
            narrative="The adventure continues...",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = ai_response

        # Patch build_ai_prompt_context
        with patch(
            "app.providers.ai.prompt_builder.build_ai_prompt_context", return_value=[]
        ):
            event = GameEventModel(type=GameEventType.NEXT_STEP, data={})
        result = asyncio.run(self.handler.handle_event(event))

        # Check result
        self.assertEqual(result.status_code, 200)
        self.assertTrue(hasattr(result, "party"))
        self.assertTrue(hasattr(result, "chat_history"))
        self.assertFalse(result.needs_backend_trigger)

    def test_handle_retry_success(self) -> None:
        """Test successful retry handling."""
        # First, make a player action to store context
        action_data = PlayerActionEventModel(
            action_type="free_text", value="I search the room"
        )

        # Mock initial AI response
        initial_response = AIResponse(
            reasoning="Player searches",
            narrative="You search but find nothing.",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = initial_response

        # Make initial action
        with patch(
            "app.providers.ai.prompt_builder.build_ai_prompt_context", return_value=[]
        ):
            event = GameEventModel(type=GameEventType.PLAYER_ACTION, data=action_data)
            asyncio.run(self.handler.handle_event(event))

        # Mock retry AI response
        retry_response = AIResponse(
            reasoning="Player searches again",
            narrative="On second look, you find a hidden compartment!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = retry_response

        # Now test retry
        event = GameEventModel(type=GameEventType.RETRY, data={})
        retry_result = asyncio.run(self.handler.handle_event(event))

        # Check result
        self.assertEqual(retry_result.status_code, 200)
        self.assertTrue(hasattr(retry_result, "party"))
        self.assertTrue(hasattr(retry_result, "chat_history"))
        self.assertFalse(retry_result.needs_backend_trigger)

    def test_handle_retry_no_context(self) -> None:
        """Test retry with no stored context."""
        # Try retry without any previous request
        event = GameEventModel(type=GameEventType.RETRY, data={})
        result = asyncio.run(self.handler.handle_event(event))

        # Check error response
        self.assertEqual(result.status_code, 400)
        self.assertTrue(hasattr(result, "party"))
        self.assertTrue(hasattr(result, "chat_history"))

        # Check error message was added to chat
        chat_history = self.chat_service.get_chat_history()
        self.assertTrue(
            any("No recent AI request to retry" in msg.content for msg in chat_history)
        )

    def test_handle_retry_removes_last_message(self) -> None:
        """Test retry removes last AI message."""
        # Add an AI message to chat history
        self.chat_service.add_message(
            "assistant", "Original AI response", is_dice_result=False
        )
        initial_chat_len = len(self.chat_service.get_chat_history())

        # Store context manually for retry
        self.shared_state_manager.store_ai_request_context(
            [MessageDict(role="user", content="test")], None
        )

        # Mock retry AI response
        retry_response = AIResponse(
            reasoning="Retry",
            narrative="New response",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = retry_response

        # Patch build_ai_prompt_context
        with patch(
            "app.providers.ai.prompt_builder.build_ai_prompt_context", return_value=[]
        ):
            event = GameEventModel(type=GameEventType.RETRY, data={})
        asyncio.run(self.handler.handle_event(event))

        # Check that AI message was removed and new one added
        chat_history = self.chat_service.get_chat_history()
        self.assertEqual(len(chat_history), initial_chat_len)  # Same length
        self.assertEqual(chat_history[-1].content, "New response")
        self.assertNotEqual(chat_history[-1].content, "Original AI response")

    def test_combat_integration(self) -> None:
        """Test combat integration with dice rolls."""
        # Set up combat with test combatants
        combatants = [
            create_test_initial_combatant("pc-1", "Fighter", hp=18, ac=14),
            create_test_initial_combatant("npc-1", "Goblin", hp=7, ac=13),
        ]

        # Start combat
        self.combat_service.start_combat(combatants)
        combat_state = self.game_state_repo.get_game_state().combat
        self.assertIsNotNone(combat_state)
        self.assertTrue(combat_state.is_active)

        # Create dice request for attack
        dice_request = DiceRequestModel(
            request_id="attack-1",
            character_ids=["pc-1"],
            type="attack",
            dice_formula="1d20+5",
            reason="Attack roll",
        )
        self.game_state.pending_player_dice_requests = [dice_request]
        self.game_state_repo.save_game_state(self.game_state)

        # Submit dice roll
        roll_data = [
            DiceRollSubmissionModel(
                character_id="pc-1",
                roll_type="attack",
                dice_formula="1d20+5",
                request_id="attack-1",
                total=18,
            )
        ]

        # Mock AI response
        ai_response = AIResponse(
            reasoning="Attack hits",
            narrative="Your sword strikes true!",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = ai_response

        # Patch build_ai_prompt_context
        with patch(
            "app.providers.ai.prompt_builder.build_ai_prompt_context",
            return_value=[],
        ):
            event = GameEventModel(
                type=GameEventType.DICE_SUBMISSION, data={"rolls": roll_data}
            )
        result = asyncio.run(self.handler.handle_event(event))

        # Check result
        self.assertEqual(result.status_code, 200)
        self.assertIsNotNone(result.combat_info)

        # Verify combat state
        combat_info = CombatFormatter.format_combat_status(self.game_state_repo)
        self.assertIsNotNone(combat_info)
        assert combat_info is not None  # For mypy
        self.assertTrue(combat_info.is_active)
        self.assertEqual(len(combat_info.combatants), 2)

    def test_event_handling_integration(self) -> None:
        """Test event handling through GameOrchestrator."""
        # Create a player action event
        event = GameEventModel(
            type="player_action",
            data=PlayerActionEventModel(action_type="free_text", value="I look around"),
        )

        # Mock AI response
        ai_response = AIResponse(
            reasoning="Player observes",
            narrative="You see a dimly lit chamber.",
            location_update=None,
            game_state_updates=[],
            dice_requests=[],
            end_turn=False,
        )
        self.mock_ai_service.get_response.return_value = ai_response

        # Patch build_ai_prompt_context
        with patch(
            "app.providers.ai.prompt_builder.build_ai_prompt_context", return_value=[]
        ):
            result = asyncio.run(self.handler.handle_event(event))

        # Check result
        self.assertEqual(result.status_code, 200)
        self.assertTrue(hasattr(result, "party"))
        self.assertTrue(hasattr(result, "chat_history"))
        self.assertFalse(result.needs_backend_trigger)

        # Check chat was updated
        chat_history = self.chat_service.get_chat_history()
        self.assertTrue(
            any("You see a dimly lit chamber" in msg.content for msg in chat_history)
        )
