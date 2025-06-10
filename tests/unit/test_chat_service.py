"""
Unit tests for chat service functionality.
"""

import unittest
from unittest.mock import Mock

from app.core.container import ServiceContainer, reset_container
from app.core.event_queue import EventQueue
from app.models import GameStateModel
from app.models.events import NarrativeAddedEvent
from app.services.chat_service import ChatServiceImpl
from tests.conftest import get_test_config


class TestChatService(unittest.TestCase):
    """Test chat service functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        reset_container()
        self.container = ServiceContainer(get_test_config())
        self.container.initialize()
        self.chat_service = self.container.get_chat_service()
        self.repo = self.container.get_game_state_repository()

    def test_add_message(self) -> None:
        """Test adding messages to chat history."""
        original_count = len(self.repo.get_game_state().chat_history)

        self.chat_service.add_message("user", "Hello, DM!")

        game_state = self.repo.get_game_state()
        self.assertEqual(len(game_state.chat_history), original_count + 1)
        self.assertEqual(game_state.chat_history[-1].role, "user")
        self.assertEqual(game_state.chat_history[-1].content, "Hello, DM!")

    def test_add_assistant_message(self) -> None:
        """Test adding assistant messages to chat history."""
        original_count = len(self.repo.get_game_state().chat_history)

        self.chat_service.add_message(
            "assistant", "Test narrative", gm_thought="Test reasoning"
        )

        game_state = self.repo.get_game_state()
        self.assertEqual(len(game_state.chat_history), original_count + 1)
        self.assertEqual(game_state.chat_history[-1].role, "assistant")
        self.assertEqual(game_state.chat_history[-1].content, "Test narrative")
        self.assertIsNotNone(game_state.chat_history[-1].gm_thought)

    def test_get_chat_history(self) -> None:
        """Test getting chat history."""
        # Add several messages
        for i in range(5):
            self.chat_service.add_message("user", f"Message {i}")

        history = self.chat_service.get_chat_history()
        # Should have original messages plus our 5 new ones
        self.assertGreater(len(history), 5)
        self.assertEqual(history[-1].content, "Message 4")


class TestChatServiceEvents(unittest.TestCase):
    """Test ChatService emits events when adding messages."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_game_state_repo = Mock()
        self.mock_game_state_repo.get_game_state.return_value = GameStateModel(
            party={},
            current_location={
                "name": "Test Location",
                "description": "Test Description",
            },
            chat_history=[],
            campaign_id="test_campaign",
        )

        self.mock_event_queue = Mock(spec=EventQueue)

        self.chat_service = ChatServiceImpl(
            game_state_repo=self.mock_game_state_repo,
            event_queue=self.mock_event_queue,
            tts_integration_service=None,
        )

    def test_chat_service_emits_narrative_event(self) -> None:
        """Test that add_message emits a NarrativeAddedEvent."""
        # Add a message
        content = "The goblin attacks!"
        self.chat_service.add_message(
            "assistant", content, gm_thought="Rolling for attack"
        )

        # Verify event was emitted
        self.mock_event_queue.put_event.assert_called_once()

        # Check the event details
        emitted_event = self.mock_event_queue.put_event.call_args[0][0]
        self.assertIsInstance(emitted_event, NarrativeAddedEvent)
        self.assertEqual(emitted_event.role, "assistant")
        self.assertEqual(emitted_event.content, content)
        self.assertEqual(emitted_event.gm_thought, "Rolling for attack")
        self.assertIsNotNone(emitted_event.message_id)

    def test_user_message_emits_event(self) -> None:
        """Test that user messages also emit events."""
        content = "I attack the goblin with my sword!"
        self.chat_service.add_message("user", content)

        # Verify event was emitted
        self.mock_event_queue.put_event.assert_called_once()

        emitted_event = self.mock_event_queue.put_event.call_args[0][0]
        self.assertIsInstance(emitted_event, NarrativeAddedEvent)
        self.assertEqual(emitted_event.role, "user")
        self.assertEqual(emitted_event.content, content)

    def test_system_message_emits_event(self) -> None:
        """Test that system messages emit events."""
        content = "Combat has started!"
        self.chat_service.add_message("system", content)

        # Verify event was emitted
        self.mock_event_queue.put_event.assert_called_once()

        emitted_event = self.mock_event_queue.put_event.call_args[0][0]
        self.assertIsInstance(emitted_event, NarrativeAddedEvent)
        self.assertEqual(emitted_event.role, "system")
        self.assertEqual(emitted_event.content, content)

    def test_invalid_role_does_not_emit_event(self) -> None:
        """Test that invalid roles don't emit events."""
        self.chat_service.add_message("invalid_role", "This shouldn't work")

        # Verify no event was emitted
        self.mock_event_queue.put_event.assert_not_called()

    def test_event_includes_tts_audio_path(self) -> None:
        """Test that TTS audio path is included in event when available."""
        # Setup TTS service mock
        mock_tts = Mock()
        mock_tts.generate_tts_for_message.return_value = "tts_cache/message_123.mp3"
        self.chat_service.tts_integration_service = mock_tts

        # Enable narration in the game state
        game_state = self.mock_game_state_repo.get_game_state()
        game_state.narration_enabled = True
        self.mock_game_state_repo.save_game_state(game_state)

        # Add assistant message
        content = "The dragon roars!"
        self.chat_service.add_message("assistant", content)

        # Verify event includes audio path
        emitted_event = self.mock_event_queue.put_event.call_args[0][0]
        self.assertEqual(emitted_event.audio_path, "tts_cache/message_123.mp3")

    def test_event_includes_message_id(self) -> None:
        """Test that events include the same message ID as stored in chat history."""
        content = "Test message"
        self.chat_service.add_message("assistant", content)

        # Get the message from chat history
        chat_history = self.chat_service.get_chat_history()
        stored_message = chat_history[-1]

        # Get the emitted event
        emitted_event = self.mock_event_queue.put_event.call_args[0][0]

        # Verify IDs match
        self.assertEqual(emitted_event.message_id, stored_message.id)

    def test_event_preserves_kwargs(self) -> None:
        """Test that events preserve additional kwargs from add_message."""
        self.chat_service.add_message(
            "assistant",
            "The spell hits!",
            detailed_content="The magic missile strikes the orc for 5 damage!",
            gm_thought="Rolling damage",
            is_dice_result=True,
        )

        emitted_event = self.mock_event_queue.put_event.call_args[0][0]
        self.assertEqual(emitted_event.content, "The spell hits!")
        self.assertEqual(emitted_event.gm_thought, "Rolling damage")
        # Note: detailed_content and is_dice_result are not part of NarrativeAddedEvent
        # but we ensure gm_thought is preserved

    def test_backward_compatibility_maintained(self) -> None:
        """Test that existing functionality still works while emitting events."""
        # Add a message
        self.chat_service.add_message("user", "Test message", gm_thought="Test thought")

        # Verify message was added to chat history (existing functionality)
        game_state = self.mock_game_state_repo.get_game_state()
        self.assertEqual(len(game_state.chat_history), 1)
        self.assertEqual(game_state.chat_history[0].content, "Test message")
        self.assertEqual(game_state.chat_history[0].gm_thought, "Test thought")

        # Verify event was also emitted (new functionality)
        self.assertTrue(self.mock_event_queue.put_event.called)


if __name__ == "__main__":
    unittest.main()
