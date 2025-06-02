"""
Game state repository implementation for managing game state persistence.
"""
import logging
import os
import json
from typing import Optional, Dict
from app.core.interfaces import GameStateRepository
from app.game.unified_models import GameStateModel, CharacterInstanceModel, LocationModel, NPCModel, QuestModel
from app.game.calculators.dice_mechanics import get_ability_modifier

logger = logging.getLogger(__name__)


class InMemoryGameStateRepository(GameStateRepository):
    """In-memory implementation of game state repository."""
    
    def __init__(self):
        # active_game_state is the one currently being played.
        # _campaign_saves stores copies for different campaigns.
        self._active_game_state: GameStateModel = self._initialize_default_game_state()
        self._campaign_saves: Dict[str, GameStateModel] = {}

    def _initialize_default_game_state(self) -> GameStateModel:
        """Initialize default in-memory game state from goblin cave template."""
        logger.info("Initializing default in-memory game state from goblin cave template...")
        gs = GameStateModel()  # Create a new GameStateModel instance
        gs.campaign_id = None 

        # Load goblin cave template for default campaign data
        import json
        import os
        template_path = os.path.join("saves", "campaign_templates", "goblin_cave_template.json")
        
        try:
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    template_data = json.load(f)
                    
                # Set campaign data from template
                gs.campaign_goal = template_data.get("campaign_goal", "No specific goal set.")
                gs.world_lore = template_data.get("world_lore", [])
                gs.event_summary = template_data.get("event_summary", [])
                location_data = template_data.get("starting_location", {"name": "Unknown", "description": ""})
                gs.current_location = LocationModel(**location_data)
                
                # Convert NPCs and quests to proper models
                gs.known_npcs = {k: NPCModel(**v) for k, v in template_data.get("initial_npcs", {}).items()}
                gs.active_quests = {k: QuestModel(**v) for k, v in template_data.get("initial_quests", {}).items()}
                
                # Add initial narrative to chat history
                if not gs.chat_history and "opening_narrative" in template_data:
                    from datetime import datetime, timezone
                    from app.game.unified_models import ChatMessage
                    initial_message = ChatMessage(
                        id="initial_narrative",
                        role="assistant",
                        content=template_data["opening_narrative"],
                        timestamp=datetime.now(timezone.utc).isoformat(),
                        is_dice_result=False
                    )
                    gs.chat_history.append(initial_message)
            else:
                logger.warning(f"Goblin cave template not found at {template_path}, using empty defaults")
                
        except Exception as e:
            logger.error(f"Failed to load goblin cave template: {e}", exc_info=True)
        
        # Load default character templates for the party
        character_templates = ["torvin_stonebeard", "elara_meadowlight", "zaltar_mystic"]
        character_ids = ["char1", "char2", "char3"]
        party_instances = {}
        
        for idx, template_name in enumerate(character_templates):
            try:
                char_template_path = os.path.join("saves", "character_templates", f"{template_name}.json")
                if os.path.exists(char_template_path):
                    with open(char_template_path, 'r') as f:
                        char_data = json.load(f)
                        
                    # Load character template data
                    character_id = character_ids[idx]
                    template_id = template_name  # Use the actual template name as ID
                    template_data = char_data
                    level = template_data.get("level", 3)  # Default to level 3 for goblin cave
                    
                    # Get base stats for calculations
                    base_stats = template_data.get("base_stats", {})
                    con_score = base_stats.get("CON", 10)
                    dex_score = base_stats.get("DEX", 10)
                    
                    # Calculate HP and AC
                    con_mod = get_ability_modifier(con_score)
                    dex_mod = get_ability_modifier(dex_score)
                    
                    # Hit die by class (simplified)
                    char_class = template_data.get("char_class", "fighter").lower()
                    hit_dice = {"cleric": 8, "rogue": 8, "wizard": 6, "fighter": 10}
                    hit_die = hit_dice.get(char_class, 8)
                    hit_die_avg = (hit_die // 2) + 1
                    max_hp = max(1, hit_die + ((hit_die_avg + con_mod) * (level - 1)))
                    
                    # Basic AC calculation
                    ac = 10 + dex_mod
                    
                    # Create character instance using CharacterInstanceModel
                    char_instance = CharacterInstanceModel(
                        template_id=template_id,
                        campaign_id="default",  # Default campaign for in-memory
                        current_hp=max_hp,
                        max_hp=max_hp,
                        temp_hp=0,
                        experience_points=0,
                        level=level,
                        spell_slots_used={},
                        hit_dice_used=0,
                        death_saves={"successes": 0, "failures": 0},
                        inventory=[],
                        gold=template_data.get("starting_gold", 0),
                        conditions=[],
                        exhaustion_level=0,
                        notes="",
                        achievements=[],
                        relationships={}
                    )
                    party_instances[character_id] = char_instance
                else:
                    logger.warning(f"Character template {template_name} not found")
                    
            except Exception as e:
                logger.error(f"Failed to load character template {template_name}: {e}", exc_info=True)
        
        gs.party = party_instances
        logger.info("Default in-memory game state initialized from templates.")
        return gs

    def get_game_state(self) -> GameStateModel:
        return self._active_game_state

    def save_game_state(self, state: GameStateModel) -> None:
        self._active_game_state = state  # Always update the active one
        if state.campaign_id:
            self._campaign_saves[state.campaign_id] = state.model_copy(deep=True)
            logger.debug(f"Game state for campaign '{state.campaign_id}' saved to in-memory store.")
        else:
            logger.debug("Active game state (no campaign_id) updated in memory (default state).")

    def load_campaign_state(self, campaign_id: str) -> Optional[GameStateModel]:
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
        self._active_game_state: GameStateModel = self._load_or_initialize_default()
        self._loaded_from_campaign_specific_file = False

    def _get_campaign_save_path(self, campaign_id: str) -> str:
        campaign_dir = os.path.join(self.base_save_dir, "campaigns", campaign_id)
        return os.path.join(campaign_dir, "active_game_state.json")

    def _load_or_initialize_default(self) -> GameStateModel:
        if os.path.exists(self.default_game_state_file):
            try:
                with open(self.default_game_state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Migrate old save format if needed
                data = self._migrate_old_save_data(data, "default")
                
                logger.info(f"Default active game state loaded from {self.default_game_state_file}")
                return GameStateModel(**data)
            except Exception as e:
                logger.error(f"Failed to load default active game state from {self.default_game_state_file}: {e}. Initializing new.")
        
        # Fallback to InMemoryGameStateRepository's initialization logic for a true default
        # This ensures DRY - the default state initialization logic is only defined once
        # in InMemoryGameStateRepository._initialize_default_game_state()
        logger.info("Default active game state file not found. Initializing new default game state.")
        temp_in_memory_repo = InMemoryGameStateRepository()
        return temp_in_memory_repo.get_game_state()

    def get_game_state(self) -> GameStateModel:
        """Returns the current in-memory active state."""
        return self._active_game_state

    def save_game_state(self, state: GameStateModel) -> None:
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
                # Use model_dump with mode='json' to properly serialize datetime fields
                json.dump(state.model_dump(mode='json'), f, indent=2, ensure_ascii=False)
            os.replace(temp_path, save_path)
            logger.info(f"Game state saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save game state to {save_path}: {e}")

    def _migrate_old_save_data(self, data: dict, campaign_id: str) -> dict:
        """Migrate old save file format to new unified model format."""
        # Migrate party members to CharacterInstanceModel format
        if "party" in data:
            migrated_party = {}
            for char_id, char_data in data["party"].items():
                # If it's already in the new format (has template_id), skip migration
                if "template_id" in char_data and "campaign_id" in char_data:
                    migrated_party[char_id] = char_data
                else:
                    # Migrate old format to new CharacterInstanceModel format
                    migrated_char = {
                        "template_id": char_data.get("id", char_id),
                        "campaign_id": campaign_id,
                        "current_hp": char_data.get("current_hp", 1),
                        "max_hp": char_data.get("max_hp", 1),
                        "temp_hp": char_data.get("temporary_hp", 0),
                        "experience_points": 0,
                        "level": char_data.get("level", 1),
                        "spell_slots_used": {},
                        "hit_dice_used": 0,
                        "death_saves": {"successes": 0, "failures": 0},
                        "inventory": char_data.get("inventory", []),
                        "gold": char_data.get("gold", 0),
                        "conditions": char_data.get("conditions", []),
                        "exhaustion_level": 0,
                        "notes": "",
                        "achievements": [],
                        "relationships": {}
                    }
                    migrated_party[char_data.get("id", char_id)] = migrated_char
            data["party"] = migrated_party
        
        # Ensure current_location is a proper LocationModel dict
        if "current_location" in data and isinstance(data["current_location"], dict):
            if "name" not in data["current_location"]:
                data["current_location"] = {"name": "Unknown", "description": ""}
            elif "description" not in data["current_location"]:
                data["current_location"]["description"] = ""
        
        return data

    def load_campaign_state(self, campaign_id: str) -> Optional[GameStateModel]:
        campaign_specific_path = self._get_campaign_save_path(campaign_id)
        if not os.path.exists(campaign_specific_path):
            logger.info(f"No active save file found for campaign '{campaign_id}' at {campaign_specific_path}.")
            return None
        try:
            with open(campaign_specific_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Migrate old save format if needed
            data = self._migrate_old_save_data(data, campaign_id)
            
            loaded_state = GameStateModel(**data)
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
