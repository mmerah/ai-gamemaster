"""
Core interfaces and abstract base classes for the application.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from app.ai_services.schemas import AIResponse
from app.game.models import GameState, CharacterInstance


class GameStateRepository(ABC):
    """Interface for game state persistence and retrieval."""
    
    @abstractmethod
    def get_game_state(self) -> GameState:
        """Retrieve the current game state."""
        pass
    
    @abstractmethod
    def save_game_state(self, state: GameState) -> None:
        """Save the game state."""
        pass


class CharacterService(ABC):
    """Interface for character-related operations."""
    
    @abstractmethod
    def get_character(self, character_id: str) -> Optional[CharacterInstance]:
        """Get a character by ID."""
        pass
    
    @abstractmethod
    def find_character_by_name_or_id(self, identifier: str) -> Optional[str]:
        """Find character ID by name or direct ID match."""
        pass
    
    @abstractmethod
    def get_character_name(self, character_id: str) -> str:
        """Get display name for a character."""
        pass


class DiceRollingService(ABC):
    """Interface for dice rolling operations."""
    
    @abstractmethod
    def perform_roll(self, character_id: str, roll_type: str, dice_formula: str,
                     skill: Optional[str] = None, ability: Optional[str] = None,
                     dc: Optional[int] = None, reason: str = "",
                     original_request_id: Optional[str] = None) -> Dict[str, Any]:
        """Perform a dice roll and return the result."""
        pass


class CombatService(ABC):
    """Interface for combat-related operations."""
    
    @abstractmethod
    def start_combat(self, combatants: List[Dict]) -> None:
        """Start a new combat encounter."""
        pass
    
    @abstractmethod
    def end_combat(self) -> None:
        """End the current combat encounter."""
        pass
    
    @abstractmethod
    def advance_turn(self) -> None:
        """Advance to the next turn in combat."""
        pass
    
    @abstractmethod
    def determine_initiative_order(self, roll_results: List[Dict]) -> None:
        """Determine and set initiative order based on roll results."""
        pass


class ChatService(ABC):
    """Interface for chat/message operations."""
    
    @abstractmethod
    def add_message(self, role: str, content: str, **kwargs) -> None:
        """Add a message to chat history."""
        pass
    
    @abstractmethod
    def get_chat_history(self) -> List[Dict]:
        """Get the current chat history."""
        pass


class AIResponseProcessor(ABC):
    """Interface for processing AI responses."""
    
    @abstractmethod
    def process_response(self, ai_response: AIResponse) -> Tuple[List[Dict], bool]:
        """Process an AI response and return pending requests and rerun flag."""
        pass


class GameEventHandler(ABC):
    """Interface for handling game events."""
    
    @abstractmethod
    def handle_player_action(self, action_data: Dict) -> Dict:
        """Handle a player action and return response data."""
        pass
    
    @abstractmethod
    def handle_dice_submission(self, roll_data: List[Dict]) -> Dict:
        """Handle submitted dice rolls and return response data."""
        pass
    
    @abstractmethod
    def handle_next_step_trigger(self) -> Dict:
        """Handle triggering the next step and return response data."""
        pass
