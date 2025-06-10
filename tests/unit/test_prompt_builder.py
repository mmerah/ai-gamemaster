"""
Unit tests for prompt building and filtering functionality.
"""

import unittest

from app.game.prompt_builder import PromptBuilder
from app.models import ChatMessageModel


class TestPromptFiltering(unittest.TestCase):
    """Test prompt filtering functionality to prevent system errors from reaching AI."""

    def setUp(self) -> None:
        """Set up test instance."""
        self.builder = PromptBuilder()

    def test_system_error_message_filtered_out(self) -> None:
        """Test that system error messages are excluded from AI prompts."""
        # System error message (should be filtered out)
        error_msg = ChatMessageModel(
            role="system",
            content="(Error: Failed to get a valid response from the AI. You can try clicking 'Retry Last Request' if this was due to a parsing error.)",
            is_dice_result=True,
            id="test-1",
            timestamp="2025-05-28T10:00:00Z",
        )

        result = self.builder._format_message_for_history(error_msg)
        self.assertIsNone(
            result, "System error messages should be filtered out from AI prompts"
        )

    def test_another_system_error_message_filtered_out(self) -> None:
        """Test that another variant of system error message is filtered out."""
        error_msg = ChatMessageModel(
            role="system",
            content="(Error processing AI step: Connection failed. You can try clicking 'Retry Last Request' if this was due to a parsing error.)",
            is_dice_result=True,
            id="test-2",
            timestamp="2025-05-28T10:00:00Z",
        )

        result = self.builder._format_message_for_history(error_msg)
        self.assertIsNone(
            result, "System error messages should be filtered out from AI prompts"
        )

    def test_regular_system_message_included(self) -> None:
        """Test that regular system messages are included."""
        system_msg = ChatMessageModel(
            role="system",
            content="Welcome to the adventure!",
            is_dice_result=False,
            id="test-3",
            timestamp="2025-05-28T10:00:00Z",
        )

        result = self.builder._format_message_for_history(system_msg)
        self.assertIsNotNone(result, "Regular system messages should be included")
        assert result is not None  # Type guard for mypy
        self.assertEqual(result.type, "system")
        self.assertEqual(result.content, "Welcome to the adventure!")

    def test_system_message_without_dice_result_flag_included(self) -> None:
        """Test that system messages without is_dice_result flag are included."""
        system_msg = ChatMessageModel(
            role="system",
            content="(Error: This is a test message)",
            id="test-4",
            timestamp="2025-05-28T10:00:00Z",
        )

        result = self.builder._format_message_for_history(system_msg)
        self.assertIsNotNone(
            result, "System messages without is_dice_result should be included"
        )

    def test_user_message_included(self) -> None:
        """Test that user messages are always included."""
        user_msg = ChatMessageModel(
            role="user",
            content="I want to cast fireball",
            id="test-5",
            timestamp="2025-05-28T10:00:00Z",
        )

        result = self.builder._format_message_for_history(user_msg)
        self.assertIsNotNone(result, "User messages should always be included")
        assert result is not None  # Type guard for mypy
        self.assertEqual(result.type, "human")
        self.assertEqual(result.content, "I want to cast fireball")

    def test_assistant_message_included(self) -> None:
        """Test that assistant messages are always included."""
        assistant_msg = ChatMessageModel(
            role="assistant",
            content="You cast fireball and it explodes!",
            id="test-6",
            timestamp="2025-05-28T10:00:00Z",
        )

        result = self.builder._format_message_for_history(assistant_msg)
        self.assertIsNotNone(result, "Assistant messages should always be included")
        assert result is not None  # Type guard for mypy
        self.assertEqual(result.type, "ai")
        self.assertEqual(result.content, "You cast fireball and it explodes!")

    def test_assistant_message_with_ai_response_json(self) -> None:
        """Test that assistant messages prefer ai_response_json content."""
        assistant_msg = ChatMessageModel(
            role="assistant",
            content="Short narrative",
            ai_response_json='{"reasoning": "test", "narrative": "Full narrative from JSON"}',
            id="test-7",
            timestamp="2025-05-28T10:00:00Z",
        )

        result = self.builder._format_message_for_history(assistant_msg)
        self.assertIsNotNone(result, "Assistant messages should always be included")
        assert result is not None  # Type guard for mypy
        self.assertEqual(result.type, "ai")
        self.assertEqual(
            result.content,
            '{"reasoning": "test", "narrative": "Full narrative from JSON"}',
        )

    def test_empty_content_message_filtered_out(self) -> None:
        """Test that messages with empty content are filtered out."""
        empty_msg = ChatMessageModel(
            role="user", content="", id="test-8", timestamp="2025-05-28T10:00:00Z"
        )

        result = self.builder._format_message_for_history(empty_msg)
        self.assertIsNone(result, "Messages with empty content should be filtered out")

    def test_system_error_message_edge_cases(self) -> None:
        """Test edge cases for system error message filtering."""
        # Test message that starts with (Error but is not marked as dice_result
        edge_case1 = ChatMessageModel(
            role="system",
            content="(Error: This should not be filtered)",
            is_dice_result=False,
            id="test-9",
            timestamp="2025-05-28T10:00:00Z",
        )

        result = self.builder._format_message_for_history(edge_case1)
        self.assertIsNotNone(
            result, "System messages without is_dice_result=True should be included"
        )

        # Test user message that starts with (Error - should be included
        edge_case2 = ChatMessageModel(
            role="user",
            content="(Error: I want to report an error)",
            is_dice_result=True,
            id="test-10",
            timestamp="2025-05-28T10:00:00Z",
        )

        result = self.builder._format_message_for_history(edge_case2)
        self.assertIsNotNone(
            result, "User messages should always be included regardless of content"
        )

        # Test system message with different error format
        edge_case3 = ChatMessageModel(
            role="system",
            content="Error occurred during processing",
            is_dice_result=True,
            id="test-11",
            timestamp="2025-05-28T10:00:00Z",
        )

        result = self.builder._format_message_for_history(edge_case3)
        self.assertIsNotNone(
            result, "System messages not starting with '(Error' should be included"
        )


if __name__ == "__main__":
    unittest.main()
