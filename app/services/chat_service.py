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

logger = logging.getLogger(__name__)


class ChatServiceImpl(ChatService):
    """Implementation of chat service."""
    
    def __init__(self, game_state_repo: GameStateRepository, tts_integration_service=None):
        self.game_state_repo = game_state_repo
        self.tts_integration_service = tts_integration_service
        self.max_history_messages = 1000
    
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
        
        logger.debug(f"Added {role} message to chat history.")
    
    def get_chat_history(self) -> List[Dict]:
        """Get the current chat history."""
        game_state = self.game_state_repo.get_game_state()
        return game_state.chat_history.copy()
    
    def _validate_role(self, role: str) -> bool:
        """Validate that the role is allowed."""
        valid_roles = ["user", "assistant", "system"]
        return role in valid_roles
    
    def _create_message(self, role: str, content: str, **kwargs) -> Dict:
        """Create a message dictionary with the provided data."""
        # Generate unique ID and timestamp for each message
        timestamp = datetime.now(timezone.utc).isoformat()
        message_id = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        
        message = {
            "role": role, 
            "content": content,
            "id": message_id,
            "timestamp": timestamp
        }
        
        # Add optional fields
        if "detailed_content" in kwargs:
            message["detailed_content"] = kwargs["detailed_content"]
        
        if "gm_thought" in kwargs:
            message["gm_thought"] = kwargs["gm_thought"]
        
        if "is_dice_result" in kwargs:
            message["is_dice_result"] = kwargs["is_dice_result"]
        
        if "ai_response_json" in kwargs and role == "assistant":
            message["ai_response_json"] = kwargs["ai_response_json"]
            
            # Extract narrative and reasoning if not already provided
            if not kwargs.get("detailed_content"):
                try:
                    parsed = json.loads(kwargs["ai_response_json"])
                    message["detailed_content"] = parsed.get("narrative", content)
                    
                    if not kwargs.get("gm_thought") and parsed.get("reasoning"):
                        message["gm_thought"] = parsed.get("reasoning")
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
                    tts_text = message.get("detailed_content", content)
                    if tts_text and tts_text.strip():
                        try:
                            audio_path = self.tts_integration_service.generate_tts_for_message(tts_text, message_id)
                            if audio_path:
                                message["audio_path"] = audio_path
                                logger.info(f"Generated TTS audio for AI message: {audio_path}")
                        except Exception as e:
                            logger.error(f"Failed to generate TTS for AI message {message_id}: {e}")
        
        return message
    
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
    
    def _find_first_content_message_index(self, chat_history: List[Dict]) -> int:
        """Find the index of the first content message (not system/context)."""
        for i, msg in enumerate(chat_history):
            if i > 5:  # Keep first few messages
                break
            if (msg["role"] != "system" and 
                not msg["content"].startswith("CONTEXT INJECTION:")):
                return i
        return 0


class ChatFormatter:
    """Utility class for formatting chat messages."""
    
    @staticmethod
    def format_for_frontend(chat_history: List[Dict]) -> List[Dict]:
        """Format chat history for frontend display."""
        frontend_history = []
        
        for i, msg in enumerate(chat_history):
            formatted_msg = ChatFormatter._format_single_message(msg, i)
            frontend_history.append(formatted_msg)
        
        return frontend_history
    
    @staticmethod
    def _determine_sender_type(role: str, is_dice_result: bool) -> str:
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
    def _format_single_message(msg: Dict, index: int) -> Dict:
        """Format a single message for frontend display."""
        role = msg.get("role")
        content = msg.get("content", "")
        # detailed_content can be used by frontend if available, otherwise just content
        detailed_content = msg.get("detailed_content") 
        gm_thought = msg.get("gm_thought")
        is_dice_result = msg.get("is_dice_result", False)
        audio_path = msg.get("audio_path")
        
        # Use detailed_content if available, otherwise use content
        display_content = detailed_content if detailed_content else content
        
        # Ensure each message has a unique ID and timestamp if not already present
        # These might be added by ChatServiceImpl.add_message already.
        # If msg comes directly from initial_data, it might lack these.
        msg_id = msg.get("id", f"{msg.get('timestamp', time.time())}-{random.randint(1000,9999)}")
        msg_timestamp = msg.get("timestamp", datetime.now(timezone.utc).isoformat())

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
    def _determine_display_content(msg: Dict, content: str, detailed_content: Optional[str]) -> str:
        """Determine what content to display."""
        # Use detailed content if available
        if detailed_content:
            return detailed_content
        
        # For assistant messages, try to parse AI response JSON
        if msg.get("role") == "assistant" and msg.get("ai_response_json"):
            try:
                parsed_response = json.loads(msg["ai_response_json"])
                return parsed_response.get("narrative", content)
            except json.JSONDecodeError:
                logger.warning("Frontend: Could not parse AI response JSON in history for display.")
        
        return content


class ChatValidator:
    """Utility class for validating chat operations."""
    
    @staticmethod
    def validate_message_content(content: str) -> bool:
        """Validate that message content is acceptable."""
        if not content or not isinstance(content, str):
            return False
        
        # Check for reasonable length
        if len(content.strip()) == 0:
            return False
        
        # Could add more validation rules here
        return True
    
    @staticmethod
    def validate_role(role: str) -> bool:
        """Validate that a role is acceptable."""
        valid_roles = ["user", "assistant", "system"]
        return role in valid_roles


class ChatHistoryManager:
    """Utility class for managing chat history operations."""
    
    @staticmethod
    def get_recent_messages(chat_history: List[Dict], count: int = 10) -> List[Dict]:
        """Get the most recent messages from chat history."""
        if count <= 0:
            return []
        
        return chat_history[-count:] if len(chat_history) > count else chat_history.copy()
    
    @staticmethod
    def get_messages_by_role(chat_history: List[Dict], role: str) -> List[Dict]:
        """Get all messages from a specific role."""
        return [msg for msg in chat_history if msg.get("role") == role]
    
    @staticmethod
    def count_messages_by_role(chat_history: List[Dict]) -> Dict[str, int]:
        """Count messages by role."""
        counts = {"user": 0, "assistant": 0, "system": 0}
        
        for msg in chat_history:
            role = msg.get("role", "unknown")
            if role in counts:
                counts[role] += 1
        
        return counts
    
    @staticmethod
    def find_last_message_by_role(chat_history: List[Dict], role: str) -> Optional[Dict]:
        """Find the last message from a specific role."""
        for msg in reversed(chat_history):
            if msg.get("role") == role:
                return msg
        return None
