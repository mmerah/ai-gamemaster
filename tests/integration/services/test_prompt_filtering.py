"""
Integration tests for prompt filtering functionality.
Tests that system error messages are excluded from AI prompts but preserved in chat history.
"""

from typing import Any, Dict, Generator, Optional, cast

import pytest

from app.core.container import get_container
from app.models.shared.chat import ChatMessageModel
from app.providers.ai.prompt_builder import build_ai_prompt_context


class MockHandler:
    """Mock handler for prompt building tests."""

    def __init__(
        self,
        rag_service: Optional[Any] = None,
        campaign_service: Optional[Any] = None,
        character_service: Optional[Any] = None,
    ) -> None:
        self.rag_service = rag_service
        self.campaign_service = campaign_service
        self.character_service = character_service

    def get_character_template_repository(self) -> Any:
        """Mock method to return character template repository."""
        # Return a mock or None - the prompt builder should handle None gracefully
        return None


class TestPromptFilteringIntegration:
    """Integration tests for system error message filtering."""

    # Using the centralized app fixture from tests/conftest.py which includes proper AI mocking
    # The app fixture is automatically provided by pytest

    @pytest.fixture
    def setup(self, app: Any) -> Generator[None, None, None]:
        """Set up test environment."""
        with app.app_context():
            self.container = get_container()
            self.game_state_repo = self.container.get_game_state_repository()
            self.chat_service = self.container.get_chat_service()
            self.game_state = self.game_state_repo.get_game_state()
            yield

    def test_system_error_messages_excluded_from_ai_prompts(self, setup: None) -> None:
        """Test that system error messages appear in chat history but not in AI prompts."""
        # Add various messages to chat history
        self.chat_service.add_message("user", "I want to cast fireball")
        self.chat_service.add_message(
            "system",
            "(Error: Failed to get a valid response from the AI. You can try clicking 'Retry Last Request' if this was due to a parsing error.)",
            is_dice_result=True,
        )
        self.chat_service.add_message("user", "Let me try that again")
        self.chat_service.add_message("assistant", "You cast fireball successfully!")
        self.chat_service.add_message(
            "system",
            "(Error processing AI step: Connection failed. You can try clicking 'Retry Last Request' if this was due to a parsing error.)",
            is_dice_result=True,
        )

        # Get chat history for frontend (should include all messages)
        frontend_history = self.chat_service.get_chat_history()

        # Build AI prompt context (should exclude error messages)
        campaign_service = self.container.get_campaign_service()
        mock_handler = MockHandler(campaign_service=campaign_service)
        # Cast to satisfy type checker - MockHandler has the needed attributes
        ai_prompt_messages = build_ai_prompt_context(
            self.game_state, cast(Any, mock_handler), None
        )

        # Helper function to get content from ChatMessage objects (frontend_history)
        def get_content_frontend(msg: ChatMessageModel) -> str:
            return msg.content

        def get_role_frontend(msg: ChatMessageModel) -> str:
            return msg.role

        # Helper function to get content from dict objects (ai_prompt_messages)
        def get_content_ai(msg: Dict[str, Any]) -> str:
            return str(msg.get("content", ""))

        def get_role_ai(msg: Dict[str, Any]) -> Optional[str]:
            return msg.get("role")

        # Verify frontend history includes error messages
        frontend_errors = [
            msg
            for msg in frontend_history
            if get_role_frontend(msg) == "system"
            and get_content_frontend(msg).strip().startswith("(Error")
        ]
        assert len(frontend_errors) == 2, (
            "Frontend history should contain 2 error messages"
        )

        # Verify AI prompt excludes error messages
        ai_prompt_errors = [
            msg
            for msg in ai_prompt_messages
            if get_content_ai(msg).strip().startswith("(Error")
        ]
        assert len(ai_prompt_errors) == 0, "AI prompt should contain 0 error messages"

        # Verify other messages are included in AI prompt
        user_messages_in_prompt = [
            msg
            for msg in ai_prompt_messages
            if get_role_ai(msg) == "user" and "fireball" in get_content_ai(msg)
        ]
        assert len(user_messages_in_prompt) > 0, "User messages should be in AI prompt"

        assistant_messages_in_prompt = [
            msg
            for msg in ai_prompt_messages
            if get_role_ai(msg) == "assistant" and "successfully" in get_content_ai(msg)
        ]
        assert len(assistant_messages_in_prompt) > 0, (
            "Assistant messages should be in AI prompt"
        )

    def test_regular_system_messages_not_filtered(self, setup: None) -> None:
        """Test that regular system messages are not filtered out."""
        # Add regular system message
        self.chat_service.add_message(
            "system", "Welcome to the adventure!", is_dice_result=False
        )
        self.chat_service.add_message(
            "system", "Combat has started!", is_dice_result=True
        )

        # Build AI prompt
        campaign_service = self.container.get_campaign_service()
        mock_handler = MockHandler(campaign_service=campaign_service)
        # Cast to satisfy type checker - MockHandler has the needed attributes
        ai_prompt_messages = build_ai_prompt_context(
            self.game_state, cast(Any, mock_handler), None
        )

        # Helper function to get content from dict objects (ai_prompt_messages)
        def get_content_ai(msg: Dict[str, Any]) -> str:
            return str(msg.get("content", ""))

        # Verify regular system messages are included
        welcome_msg_found = any(
            get_content_ai(msg) == "Welcome to the adventure!"
            for msg in ai_prompt_messages
        )
        combat_msg_found = any(
            get_content_ai(msg) == "Combat has started!" for msg in ai_prompt_messages
        )

        assert welcome_msg_found, "Welcome system message should be in AI prompt"
        assert combat_msg_found, "Combat system message should be in AI prompt"

    def test_mixed_message_scenario(self, setup: None) -> None:
        """Test a realistic scenario with mixed message types."""
        # Simulate a game session with various message types
        messages = [
            ("user", "I search the room", {}),
            ("assistant", "You find a hidden door!", {}),
            (
                "system",
                "(Error: Failed to get a valid response from the AI. You can try clicking 'Retry Last Request' if this was due to a parsing error.)",
                {"is_dice_result": True},
            ),
            ("user", "I open the hidden door", {}),
            ("assistant", "The door creaks open revealing a dark corridor.", {}),
            ("system", "Roll for perception check", {"is_dice_result": True}),
            ("user", "**Player Rolls Submitted:**\nResult: 15", {}),
            (
                "system",
                "(Error processing AI step: Timeout. You can try clicking 'Retry Last Request' if this was due to a parsing error.)",
                {"is_dice_result": True},
            ),
            ("assistant", "You notice a trap trigger!", {}),
        ]

        # Add all messages
        for role, content, kwargs in messages:
            self.chat_service.add_message(role, content, **kwargs)

        # Get both histories
        frontend_history = self.chat_service.get_chat_history()
        campaign_service = self.container.get_campaign_service()
        mock_handler = MockHandler(campaign_service=campaign_service)
        # Cast to satisfy type checker - MockHandler has the needed attributes
        ai_prompt_messages = build_ai_prompt_context(
            self.game_state, cast(Any, mock_handler), None
        )

        # Count message types in each
        frontend_msg_count = len(frontend_history)

        # Frontend should have all messages plus any initial messages
        # The game state starts with an initial narrative message
        initial_message_count = len(self.game_state.chat_history) - len(messages)
        assert frontend_msg_count == len(messages) + initial_message_count, (
            "Frontend should have all messages plus initial messages"
        )

        # Helper function to get content from dict objects (ai_prompt_messages)
        def get_content_ai(msg: Dict[str, Any]) -> str:
            return str(msg.get("content", ""))

        # The actual count might be less due to truncation, but should not include errors
        ai_errors = [
            msg
            for msg in ai_prompt_messages
            if get_content_ai(msg).strip().startswith("(Error")
        ]
        assert len(ai_errors) == 0, "No error messages should be in AI prompt"

        # Verify specific non-error messages are present
        trap_msg_found = any(
            "trap trigger" in get_content_ai(msg) for msg in ai_prompt_messages
        )
        assert trap_msg_found, "Trap trigger message should be in AI prompt"
