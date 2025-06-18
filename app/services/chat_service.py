"""
Chat service implementation for managing chat history and messages.
"""

import json
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any, List

from app.core.event_queue import EventQueue
from app.core.interfaces import IChatService, IGameStateRepository
from app.models.events import NarrativeAddedEvent
from app.models.shared import ChatMessageModel
from app.services.tts_integration_service import TTSIntegrationService

logger = logging.getLogger(__name__)


class ChatService(IChatService):
    """Implementation of chat service."""

    def __init__(
        self,
        game_state_repo: IGameStateRepository,
        event_queue: EventQueue,
        tts_integration_service: TTSIntegrationService | None = None,
    ) -> None:
        self.game_state_repo = game_state_repo
        self.event_queue = event_queue
        self.tts_integration_service = tts_integration_service

    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """Add a message to chat history."""
        if not self._validate_role(role):
            logger.warning(f"Invalid role '{role}' for chat message: {content[:100]}")
            return

        message = self._create_message(role, content, **kwargs)
        game_state = self.game_state_repo.get_game_state()
        game_state.chat_history.append(message)

        # Emit event if event queue
        event = NarrativeAddedEvent(
            role=role,
            content=content,
            gm_thought=kwargs.get("gm_thought"),
            audio_path=message.audio_path,
            message_id=message.id,
            correlation_id=kwargs.get("correlation_id"),
        )
        self.event_queue.put_event(event)

        logger.debug(f"Added {role} message to chat history.")

    def get_chat_history(self) -> list[ChatMessageModel]:
        """Get the current chat history."""
        game_state = self.game_state_repo.get_game_state()
        return game_state.chat_history.copy()

    def _validate_role(self, role: str) -> bool:
        """Validate that the role is allowed."""
        valid_roles = ["user", "assistant", "system"]
        return role in valid_roles

    def _create_message(
        self, role: str, content: str, **kwargs: Any
    ) -> ChatMessageModel:
        """Create a ChatMessageModel instance with the provided data."""

        # Generate unique ID and timestamp for each message
        timestamp = datetime.now(timezone.utc).isoformat()
        message_id = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"

        # NOTE: We build message_data as a dict first to collect all fields,
        # then create the ChatMessageModel object at the end. This is cleaner than
        # creating a ChatMessageModel with partial data and mutating it.
        message_data = {
            "role": role,
            "content": content,
            "id": message_id,
            "timestamp": timestamp,
            "is_dice_result": kwargs.get("is_dice_result", False),
            "gm_thought": kwargs.get("gm_thought"),
            "detailed_content": kwargs.get("detailed_content"),
            "ai_response_json": kwargs.get("ai_response_json"),
            "audio_path": None,
        }

        # Add AI response JSON for assistant messages
        if "ai_response_json" in kwargs and role == "assistant":
            message_data["ai_response_json"] = kwargs["ai_response_json"]

            # Extract narrative and reasoning if not already provided
            if not kwargs.get("detailed_content"):
                try:
                    parsed = json.loads(kwargs["ai_response_json"])
                    message_data["detailed_content"] = parsed.get("narrative", content)

                    if not kwargs.get("gm_thought") and parsed.get("reasoning"):
                        message_data["gm_thought"] = parsed.get("reasoning")
                except json.JSONDecodeError:
                    logger.warning(
                        "Could not parse AI JSON to extract narrative/thought for history."
                    )

        # Generate TTS for AI assistant messages only if narration is enabled
        if role == "assistant" and self.tts_integration_service:
            # Check if narration is enabled in the game state
            game_state = self.game_state_repo.get_game_state()
            if game_state and game_state.narration_enabled:
                # Use detailed_content if available, otherwise use content
                detailed_content_value = message_data.get("detailed_content")
                tts_text = (
                    detailed_content_value
                    if detailed_content_value is not None
                    else content
                )
                if tts_text and tts_text.strip():
                    try:
                        audio_path = (
                            self.tts_integration_service.generate_tts_for_message(
                                tts_text, message_id
                            )
                        )
                        if audio_path:
                            message_data["audio_path"] = audio_path
                            logger.info(
                                f"Generated TTS audio for AI message: {audio_path}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Failed to generate TTS for AI message {message_id}: {e}"
                        )

        # Create and return ChatMessageModel instance from the collected data
        # This is not "casting" - it's properly constructing a new ChatMessageModel object
        return ChatMessageModel(**message_data)


class ChatFormatter:
    """Utility class for formatting chat messages."""

    @staticmethod
    def format_for_frontend(
        chat_history: List[ChatMessageModel],
    ) -> List[ChatMessageModel]:
        """Format chat history for frontend display."""
        frontend_history: List[ChatMessageModel] = []

        for msg in chat_history:
            formatted_msg = ChatFormatter._format_single_message(msg)
            frontend_history.append(formatted_msg)

        return frontend_history

    @staticmethod
    def _format_single_message(msg: ChatMessageModel) -> ChatMessageModel:
        """Format a single message for frontend display."""
        # ChatMessageModel object
        role = msg.role
        content = msg.content
        detailed_content = msg.detailed_content
        gm_thought = msg.gm_thought
        is_dice_result = msg.is_dice_result or False
        audio_path = msg.audio_path
        msg_id = msg.id
        msg_timestamp = msg.timestamp

        # Use detailed_content if available, otherwise use content
        display_content = detailed_content if detailed_content else content

        # Include TTS audio URL for frontend if available
        formatted_audio_path = f"/static/{audio_path}" if audio_path else None

        # Create new ChatMessageModel with modified values
        # Note: We keep the original role and let the API layer handle conversion
        return ChatMessageModel(
            id=msg_id,
            role=role,  # Keep original role
            content=str(display_content) if display_content else "",
            timestamp=msg_timestamp,
            gm_thought=gm_thought,
            audio_path=formatted_audio_path,
            is_dice_result=is_dice_result,
            ai_response_json=msg.ai_response_json,
            detailed_content=detailed_content,
        )
