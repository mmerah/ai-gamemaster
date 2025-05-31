"""
Game state repository implementation for managing game state persistence.
"""
import logging
import os
import json
from typing import Optional, Dict
from app.core.interfaces import GameStateRepository
from app.game.models import GameState, CharacterInstance, CharacterSheet, AbilityScores, Proficiencies, KnownNPC, Quest
from app.game.calculators.dice_mechanics import get_ability_modifier

logger = logging.getLogger(__name__)


class InMemoryGameStateRepository(GameStateRepository):
    """In-memory implementation of game state repository."""
    
    def __init__(self):
        # active_game_state is the one currently being played.
        # _campaign_saves stores copies for different campaigns.
        self._active_game_state: GameState = self._initialize_default_game_state()
        self._campaign_saves: Dict[str, GameState] = {}

    def _initialize_default_game_state(self) -> GameState:
        """Initialize default in-memory game state."""
        logger.info("Initializing default in-memory game state...")
        gs = GameState()  # Create a new GameState instance
        # This should not have a campaign_id or a special one like "_default_"
        gs.campaign_id = None 

        # Copied and adapted from original _initialize_game_state logic
        from app.game.initial_data import (
            PARTY, INITIAL_CAMPAIGN_GOAL, INITIAL_KNOWN_NPCS, 
            INITIAL_ACTIVE_QUESTS, INITIAL_WORLD_LORE, 
            INITIAL_EVENT_SUMMARY, INITIAL_NARRATIVE
        )
        
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
                con_mod = get_ability_modifier(sheet.base_stats.CON)
                dex_mod = get_ability_modifier(sheet.base_stats.DEX)
                
                # Simplified HP/AC for default characters (can be improved)
                hit_die_avg_default = 5  # d8 avg
                max_hp = max(1, (hit_die_avg_default + con_mod) * sheet.level)
                ac = 10 + dex_mod 
                
                instance_data = sheet.model_dump()
                instance_data.update({
                    "current_hp": max_hp, "max_hp": max_hp, "armor_class": ac,
                    "temporary_hp": 0, "conditions": [], "inventory": [], "gold": 0,
                    "spell_slots": None, "initiative": None
                })
                char_instance = CharacterInstance(**instance_data)
                party_instances[char_instance.id] = char_instance
            except Exception as e:
                logger.error(f"Failed to load default character {char_data.get('name', 'Unknown')}: {e}", exc_info=True)
        
        gs.party = party_instances
        gs.current_location = {"name": "Goblin Cave Entrance", "description": "The mouth of a dark cave."}
        gs.campaign_goal = INITIAL_CAMPAIGN_GOAL
        gs.known_npcs = {k: KnownNPC(**v) for k, v in INITIAL_KNOWN_NPCS.items()}
        gs.active_quests = {k: Quest(**v) for k, v in INITIAL_ACTIVE_QUESTS.items()}
        gs.world_lore = INITIAL_WORLD_LORE
        gs.event_summary = INITIAL_EVENT_SUMMARY
        
        if not gs.chat_history:  # Only add initial narrative if history is empty
            from datetime import datetime, timezone
            from app.ai_services.schemas import ChatMessage
            initial_message = ChatMessage(
                id="initial_narrative",
                role="assistant",
                content=INITIAL_NARRATIVE,
                timestamp=datetime.now(timezone.utc).isoformat(),
                is_dice_result=False
            )
            gs.chat_history.append(initial_message)
        
        logger.info("Default in-memory game state initialized.")
        return gs

    def get_game_state(self) -> GameState:
        return self._active_game_state

    def save_game_state(self, state: GameState) -> None:
        self._active_game_state = state  # Always update the active one
        if state.campaign_id:
            self._campaign_saves[state.campaign_id] = state.model_copy(deep=True)
            logger.debug(f"Game state for campaign '{state.campaign_id}' saved to in-memory store.")
        else:
            logger.debug("Active game state (no campaign_id) updated in memory (default state).")

    def load_campaign_state(self, campaign_id: str) -> Optional[GameState]:
        if campaign_id in self._campaign_saves:
            loaded_state = self._campaign_saves[campaign_id].model_copy(deep=True)
            self._active_game_state = loaded_state  # Make it active
            logger.info(f"Game state for campaign '{campaign_id}' loaded from in-memory store and set as active.")
            return loaded_state
        logger.info(f"No in-memory save found for campaign '{campaign_id}'.")
        return None


class FileGameStateRepository(GameStateRepository):
    """File-based implementation of game state repository with campaign-specific saves."""
    
    def __init__(self, base_save_dir: str = "saves"):
        self.base_save_dir = base_save_dir
        self.default_game_state_file = os.path.join(base_save_dir, "game_state_default_active.json")
        self._active_game_state: GameState = self._load_or_initialize_default()
        self._loaded_from_campaign_specific_file = False

    def _get_campaign_save_path(self, campaign_id: str) -> str:
        campaign_dir = os.path.join(self.base_save_dir, "campaigns", campaign_id)
        return os.path.join(campaign_dir, "active_game_state.json")

    def _load_or_initialize_default(self) -> GameState:
        if os.path.exists(self.default_game_state_file):
            try:
                with open(self.default_game_state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Default active game state loaded from {self.default_game_state_file}")
                return GameState(**data)
            except Exception as e:
                logger.error(f"Failed to load default active game state from {self.default_game_state_file}: {e}. Initializing new.")
        
        # Fallback to InMemoryGameStateRepository's initialization logic for a true default
        # This ensures DRY - the default state initialization logic is only defined once
        # in InMemoryGameStateRepository._initialize_default_game_state()
        logger.info("Default active game state file not found. Initializing new default game state.")
        temp_in_memory_repo = InMemoryGameStateRepository()
        return temp_in_memory_repo.get_game_state()

    def get_game_state(self) -> GameState:
        """Returns the current in-memory active state."""
        return self._active_game_state

    def save_game_state(self, state: GameState) -> None:
        self._active_game_state = state  # Update in-memory active state first
        
        save_path = self.default_game_state_file
        if state.campaign_id:
            save_path = self._get_campaign_save_path(state.campaign_id)
            campaign_dir = os.path.dirname(save_path)
            os.makedirs(campaign_dir, exist_ok=True)
        else:
            # Ensure base_save_dir exists if saving default
            os.makedirs(self.base_save_dir, exist_ok=True)
            
        logger.debug(f"Saving game state for campaign '{state.campaign_id or 'Default'}' to {save_path}")
        try:
            temp_path = save_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(state.model_dump(), f, indent=2, ensure_ascii=False)
            os.replace(temp_path, save_path)
            logger.info(f"Game state saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save game state to {save_path}: {e}")

    def load_campaign_state(self, campaign_id: str) -> Optional[GameState]:
        campaign_specific_path = self._get_campaign_save_path(campaign_id)
        if not os.path.exists(campaign_specific_path):
            logger.info(f"No active save file found for campaign '{campaign_id}' at {campaign_specific_path}.")
            return None
        try:
            with open(campaign_specific_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            loaded_state = GameState(**data)
            self._active_game_state = loaded_state  # Make it the active one in memory
            self._loaded_from_campaign_specific_file = True
            logger.info(f"Game state for campaign '{campaign_id}' loaded from {campaign_specific_path} and set as active.")
            return loaded_state
        except Exception as e:
            logger.error(f"Failed to load game state for campaign '{campaign_id}' from {campaign_specific_path}: {e}")
            # If loading specific campaign state fails, perhaps revert to default or raise
            self._active_game_state = self._load_or_initialize_default()  # Revert to default on error
            self._loaded_from_campaign_specific_file = False
            return None


class GameStateRepositoryFactory:
    """Factory for creating game state repositories."""
    
    @staticmethod
    def create_repository(repo_type: str = "memory", **kwargs) -> GameStateRepository:
        if repo_type == "memory":
            return InMemoryGameStateRepository()
        elif repo_type == "file":
            # file_path arg is now base_save_dir
            base_dir = kwargs.get("file_path", "saves")  # Keep arg name for compatibility for now
            if "file_path" in kwargs and "base_save_dir" not in kwargs:
                logger.warning("Using 'file_path' for FileGameStateRepository base_save_dir. Consider renaming to 'base_save_dir'.")
            base_dir = kwargs.get("base_save_dir", base_dir)
            return FileGameStateRepository(base_save_dir=base_dir)
        else:
            raise ValueError(f"Unknown repository type: {repo_type}")
