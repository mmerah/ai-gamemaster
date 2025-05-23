"""
Game state repository implementation for managing game state persistence.
"""
import logging
from app.core.interfaces import GameStateRepository
from app.game.models import GameState

logger = logging.getLogger(__name__)


class InMemoryGameStateRepository(GameStateRepository):
    """In-memory implementation of game state repository."""
    
    def __init__(self):
        self._game_state: GameState = GameState()
        self._initialized = False
    
    def get_game_state(self) -> GameState:
        """Retrieve the current game state."""
        if not self._initialized:
            self._initialize_game_state()
            self._initialized = True
        return self._game_state
    
    def save_game_state(self, state: GameState) -> None:
        """Save the game state."""
        self._game_state = state
        logger.debug("Game state saved to memory.")
    
    def _initialize_game_state(self) -> None:
        """Initialize the game state with default values."""
        from app.game.initial_data import (
            PARTY, INITIAL_CAMPAIGN_GOAL, INITIAL_KNOWN_NPCS, 
            INITIAL_ACTIVE_QUESTS, INITIAL_WORLD_LORE, 
            INITIAL_EVENT_SUMMARY, INITIAL_NARRATIVE
        )
        from app.game.models import CharacterInstance, CharacterSheet, AbilityScores, Proficiencies, KnownNPC, Quest
        from app.game import utils
        
        logger.info("Initializing game state...")
        
        # Load party data
        party_instances = {}
        for char_data in PARTY:
            try:
                sheet = CharacterSheet(
                    id=char_data["id"], name=char_data["name"], race=char_data["race"],
                    char_class=char_data["char_class"], level=char_data["level"],
                    icon=char_data.get("icon"),
                    base_stats=AbilityScores(**char_data.get("stats", {})),
                    proficiencies=Proficiencies(**char_data.get("proficiencies", {}))
                )
                
                # Calculate derived stats
                con_mod = utils.get_ability_modifier(sheet.base_stats.CON)
                dex_mod = utils.get_ability_modifier(sheet.base_stats.DEX)
                hit_die_avg = 5  # Simplified for PoC
                max_hp = max(1, (hit_die_avg + con_mod) * sheet.level)
                ac = 10 + dex_mod
                
                # Create character instance
                instance_data = sheet.model_dump()
                instance_data.update({
                    "current_hp": max_hp, "max_hp": max_hp, "armor_class": ac,
                    "temporary_hp": 0, "conditions": [], "inventory": [], "gold": 0,
                    "spell_slots": None, "initiative": None
                })
                char_instance = CharacterInstance(**instance_data)
                party_instances[char_instance.id] = char_instance
                
            except Exception as e:
                logger.error(f"Failed to load character {char_data.get('name', 'Unknown')}: {e}", exc_info=True)
        
        if not party_instances:
            logger.error("CRITICAL: Failed to load ANY character instances.")
        
        # Set up game state
        self._game_state.party = party_instances
        self._game_state.current_location = {"name": "Goblin Cave Entrance", "description": "The mouth of a dark cave."}
        self._game_state.campaign_goal = INITIAL_CAMPAIGN_GOAL
        self._game_state.known_npcs = {k: KnownNPC(**v) for k, v in INITIAL_KNOWN_NPCS.items()}
        self._game_state.active_quests = {k: Quest(**v) for k, v in INITIAL_ACTIVE_QUESTS.items()}
        self._game_state.world_lore = INITIAL_WORLD_LORE
        self._game_state.event_summary = INITIAL_EVENT_SUMMARY
        
        # Add initial narrative if no chat history exists
        if not self._game_state.chat_history:
            self._game_state.chat_history.append({
                "role": "assistant",
                "content": INITIAL_NARRATIVE,
                "gm_thought": "Game start. Setting initial scene. Goblins present but unaware."
            })
            self._game_state.current_location = {
                "name": "Goblin Cave Chamber",
                "description": "Dimly lit by torches, a campfire flickers near two goblins."
            }
        
        logger.info("Game state initialized successfully.")


class FileGameStateRepository(GameStateRepository):
    """File-based implementation of game state repository (for future use)."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._game_state: GameState = GameState()
        self._loaded = False
    
    def get_game_state(self) -> GameState:
        """Retrieve the current game state from file."""
        if not self._loaded:
            self._load_from_file()
            self._loaded = True
        return self._game_state
    
    def save_game_state(self, state: GameState) -> None:
        """Save the game state to file."""
        self._game_state = state
        self._save_to_file()
    
    def _load_from_file(self) -> None:
        """Load game state from file."""
        import json
        import os
        
        if not os.path.exists(self.file_path):
            logger.info(f"Save file {self.file_path} not found. Creating new game state.")
            # Initialize with default state like InMemoryGameStateRepository
            repo = InMemoryGameStateRepository()
            self._game_state = repo.get_game_state()
            return
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._game_state = GameState(**data)
            logger.info(f"Game state loaded from {self.file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load game state from {self.file_path}: {e}")
            # Fall back to default initialization
            repo = InMemoryGameStateRepository()
            self._game_state = repo.get_game_state()
    
    def _save_to_file(self) -> None:
        """Save game state to file."""
        import json
        import os
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Save to temporary file first, then rename for atomicity
            temp_path = self.file_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self._game_state.model_dump(), f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            os.replace(temp_path, self.file_path)
            logger.debug(f"Game state saved to {self.file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save game state to {self.file_path}: {e}")


class GameStateRepositoryFactory:
    """Factory for creating game state repositories."""
    
    @staticmethod
    def create_repository(repo_type: str = "memory", **kwargs) -> GameStateRepository:
        """Create a game state repository of the specified type."""
        if repo_type == "memory":
            return InMemoryGameStateRepository()
        elif repo_type == "file":
            file_path = kwargs.get("file_path", "saves/game_state.json")
            return FileGameStateRepository(file_path)
        else:
            raise ValueError(f"Unknown repository type: {repo_type}")
