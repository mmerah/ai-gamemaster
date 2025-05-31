"""
Chat service implementation for managing chat history and messages.
"""
import json
import logging
import time
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.core.interfaces import ChatService, GameStateRepository
from app.events.game_update_events import NarrativeAddedEvent
from app.core.event_queue import EventQueue

logger = logging.getLogger(__name__)


class ChatServiceImpl(ChatService):
    """Implementation of chat service."""
    
    # Constants for history management
    MAX_HISTORY_MESSAGES = 1000  # Maximum messages to keep in history
    MIN_MESSAGES_TO_PRESERVE_AT_START = 5  # Always preserve first N messages (system prompts, initial narrative)
    
    def __init__(self, game_state_repo: GameStateRepository, tts_integration_service=None, event_queue: Optional[EventQueue] = None):
        self.game_state_repo = game_state_repo
        self.tts_integration_service = tts_integration_service
        self.event_queue = event_queue
        self.max_history_messages = self.MAX_HISTORY_MESSAGES
    
    def add_message(self, role: str, content: str, **kwargs) -> None:
        """Add a message to chat history."""
        if not self._validate_role(role):
            logger.warning(f"Invalid role '{role}' for chat message: {content[:100]}")
            return
        
        message = self._create_message(role, content, **kwargs)
        game_state = self.game_state_repo.get_game_state()
        game_state.chat_history.append(message)
        
        # Manage history size
        self._truncate_history_if_needed(game_state)
        
        # Emit event if event queue is available (backward compatible)
        if self.event_queue:
            event = NarrativeAddedEvent(
                role=role,
                content=content,
                gm_thought=kwargs.get("gm_thought"),
                audio_path=message.audio_path,
                message_id=message.id,
                correlation_id=kwargs.get("correlation_id")
            )
            self.event_queue.put_event(event)
        
        logger.debug(f"Added {role} message to chat history.")
    
    def get_chat_history(self):
        """Get the current chat history."""
        game_state = self.game_state_repo.get_game_state()
        return game_state.chat_history.copy()
    
    def _validate_role(self, role: str) -> bool:
        """Validate that the role is allowed."""
        valid_roles = ["user", "assistant", "system"]
        return role in valid_roles
    
    def _create_message(self, role: str, content: str, **kwargs):
        """Create a ChatMessage instance with the provided data."""
        from app.ai_services.schemas import ChatMessage
        
        # Generate unique ID and timestamp for each message
        timestamp = datetime.now(timezone.utc).isoformat()
        message_id = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        
        # NOTE: We build message_data as a dict first to collect all fields,
        # then create the ChatMessage object at the end. This is cleaner than
        # creating a ChatMessage with partial data and mutating it.
        message_data = {
            "role": role, 
            "content": content,
            "id": message_id,
            "timestamp": timestamp,
            "is_dice_result": kwargs.get("is_dice_result", False),
            "gm_thought": kwargs.get("gm_thought"),
            "detailed_content": kwargs.get("detailed_content"),
            "ai_response_json": kwargs.get("ai_response_json"),
            "audio_path": None
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
                    logger.warning("Could not parse AI JSON to extract narrative/thought for history.")
        
        # Generate TTS for AI assistant messages only if narration is enabled
        if role == "assistant" and self.tts_integration_service:
            # Check if narration is enabled for the current campaign
            game_state = self.game_state_repo.get_game_state()
            if game_state and game_state.campaign_id:
                # Get campaign service to check narration settings
                from app.core.container import get_container
                container = get_container()
                campaign_service = container.get_campaign_service()
                campaign = campaign_service.get_campaign(game_state.campaign_id)
                
                if campaign and campaign.narration_enabled:
                    # Use detailed_content if available, otherwise use content
                    detailed_content_value = message_data.get("detailed_content")
                    tts_text = detailed_content_value if detailed_content_value is not None else content
                    if tts_text and tts_text.strip():
                        try:
                            audio_path = self.tts_integration_service.generate_tts_for_message(tts_text, message_id)
                            if audio_path:
                                message_data["audio_path"] = audio_path
                                logger.info(f"Generated TTS audio for AI message: {audio_path}")
                        except Exception as e:
                            logger.error(f"Failed to generate TTS for AI message {message_id}: {e}")
        
        # Create and return ChatMessage instance from the collected data
        # This is not "casting" - it's properly constructing a new ChatMessage object
        return ChatMessage(**message_data)
    
    def _truncate_history_if_needed(self, game_state) -> None:
        """Truncate chat history if it exceeds the maximum size."""
        if len(game_state.chat_history) <= self.max_history_messages:
            return
        
        num_to_remove = len(game_state.chat_history) - self.max_history_messages
        
        # Find first non-system/context message to start removing after
        first_content_idx = self._find_first_content_message_index(game_state.chat_history)
        
        if first_content_idx + num_to_remove < len(game_state.chat_history):
            del game_state.chat_history[first_content_idx:first_content_idx + num_to_remove]
            logger.info(f"Chat history truncated to {len(game_state.chat_history)} messages.")
    
    def _find_first_content_message_index(self, chat_history) -> int:
        """Find the index of the first content message (not system/context).
        
        This preserves the initial system prompts and context messages that are
        critical for the AI to understand the game state and rules.
        """
        for i, msg in enumerate(chat_history):
            if i > self.MIN_MESSAGES_TO_PRESERVE_AT_START:
                break
            # ChatMessage objects
            if (msg.role != "system" and 
                not msg.content.startswith("CONTEXT INJECTION:")):
                return i
        return 0


class ChatFormatter:
    """Utility class for formatting chat messages."""
    
    @staticmethod
    def format_for_frontend(chat_history) -> List[Dict]:
        """Format chat history for frontend display."""
        frontend_history = []
        
        for i, msg in enumerate(chat_history):
            formatted_msg = ChatFormatter._format_single_message(msg, i)
            frontend_history.append(formatted_msg)
        
        return frontend_history
    
    @staticmethod
    def _determine_sender_type(role: str, is_dice_result: bool) -> str:  # noqa: ARG004
        """Determine the sender type for frontend (returns 'gm', 'user', 'system')."""
        if role == "assistant":
            return "gm"
        elif role == "user":
            # Player actions are role "user", dice results from player are also "user" but marked is_dice_result
            # System messages triggered by player (e.g. "Empty action") are role "system"
            return "user" # Simplified: if role is user, it's from the user input side.
        elif role == "system":
            return "system"
        else:
            logger.warning(f"Unknown role '{role}' in _determine_sender_type, defaulting to 'system'.")
            return "system"
    
    @staticmethod
    def _format_single_message(msg, index: int) -> Dict:  # noqa: ARG004
        """Format a single message for frontend display."""
        # ChatMessage object
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

        entry = {
            "id": msg_id,
            "type": ChatFormatter._determine_sender_type(role, is_dice_result),
            "content": str(display_content) if display_content else "",
            "timestamp": msg_timestamp,
        }
        
        if gm_thought:
            entry["gm_thought"] = gm_thought
        
        # Include TTS audio URL for frontend if available
        if audio_path:
            entry["tts_audio_url"] = f"/static/{audio_path}"
        
        # Example: If it's a dice result and content doesn't already indicate it, prepend.
        # This depends on how dice results are formatted before they reach here.
        # if is_dice_result and isinstance(entry["content"], str) and "🎲" not in entry["content"]:
        #     entry["content"] = f"🎲 {entry['content']}"
        
        return entry
    
    @staticmethod
    def _determine_display_content(msg, content: str, detailed_content: Optional[str]) -> str:
        """Determine what content to display."""
        # Use detailed content if available
        if detailed_content:
            return detailed_content
        
        # For assistant messages, try to parse AI response JSON
        role = msg.role if hasattr(msg, 'role') else msg.get("role")
        ai_response_json = msg.ai_response_json if hasattr(msg, 'ai_response_json') else msg.get("ai_response_json")
        
        if role == "assistant" and ai_response_json:
            try:
                parsed_response = json.loads(ai_response_json)
                return parsed_response.get("narrative", content)
            except json.JSONDecodeError:
                logger.warning("Frontend: Could not parse AI response JSON in history for display.")
        
        return content

