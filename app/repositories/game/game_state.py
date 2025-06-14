"""
Game state repository implementation for managing game state persistence.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.core.interfaces import GameStateRepository
from app.models.game_state import ChatMessageModel, GameStateModel
from app.models.utils import LocationModel, MigrationResultModel

logger = logging.getLogger(__name__)


class BaseGameStateRepository(GameStateRepository):
    """Base class with common functionality for game state repositories."""

    def __init__(self, base_save_dir: str = "saves") -> None:
        self.base_save_dir = base_save_dir

    def _get_campaign_save_path(self, campaign_id: str) -> str:
        """Get the path for a campaign's save file."""
        campaign_dir = os.path.join(self.base_save_dir, "campaigns", campaign_id)
        return os.path.join(campaign_dir, "active_game_state.json")

    def _check_version(self, data: dict[str, Any]) -> MigrationResultModel:
        """Check save format version and handle migrations if needed."""
        version = data.get("version", 0)
        migrated = False

        if version < 1:
            # Legacy format without version field - add it
            data["version"] = 1
            version = 1
            migrated = True
            logger.info("Migrated game state from legacy format to version 1")

            # Migrate party members to ensure they have version field too
            if "party" in data:
                for _, char_data in data["party"].items():
                    if "version" not in char_data:
                        char_data["version"] = 1

        # Future migrations would go here:
        # if version < 2:
        #     data = self._migrate_v1_to_v2(data)
        #     data['version'] = 2
        #     version = 2
        #     migrated = True

        return MigrationResultModel(data=data, version=version, migrated=migrated)


class InMemoryGameStateRepository(BaseGameStateRepository):
    """In-memory implementation of game state repository."""

    def __init__(self, base_save_dir: str = "saves") -> None:
        super().__init__(base_save_dir)
        # active_game_state is the one currently being played.
        # _campaign_saves stores copies for different campaigns.
        self._active_game_state: GameStateModel = self._initialize_default_game_state()
        self._campaign_saves: Dict[str, GameStateModel] = {}

    def _initialize_default_game_state(self) -> GameStateModel:
        """Initialize default in-memory game state.

        This creates a minimal default state that can be used when no campaign
        is loaded.
        """
        logger.info("Initializing minimal default in-memory game state...")

        # Create minimal default state
        game_state = GameStateModel(
            campaign_id=None,
            campaign_name="Default Campaign",
            current_location=LocationModel(
                name="Tavern", description="A cozy tavern where adventures begin."
            ),
            campaign_goal="No specific goal set.",
            narration_enabled=False,
            tts_voice="af_heart",
        )

        # Add a simple welcome message
        initial_message = ChatMessageModel(
            id="welcome",
            role="assistant",
            content="Welcome! Please load or create a campaign to begin your adventure.",
            timestamp=datetime.now(timezone.utc).isoformat(),
            is_dice_result=False,
        )
        game_state.chat_history.append(initial_message)

        logger.info("Default in-memory game state initialized.")
        return game_state

    def get_game_state(self) -> GameStateModel:
        return self._active_game_state

    def save_game_state(self, state: GameStateModel) -> None:
        self._active_game_state = state  # Always update the active one
        if state.campaign_id:
            self._campaign_saves[state.campaign_id] = state.model_copy(deep=True)
            logger.debug(
                f"Game state for campaign '{state.campaign_id}' saved to in-memory store."
            )
        else:
            logger.debug(
                "Active game state (no campaign_id) updated in memory (default state)."
            )

    def load_campaign_state(self, campaign_id: str) -> Optional[GameStateModel]:
        """Load campaign state from in-memory storage or disk.

        This first checks if we have a saved state in memory. If not, it checks
        if a saved state exists on disk (same behavior as FileGameStateRepository).
        """
        # Check if we have it in memory
        if campaign_id in self._campaign_saves:
            loaded_state = self._campaign_saves[campaign_id].model_copy(deep=True)
            self._active_game_state = loaded_state
            logger.info(
                f"Game state for campaign '{campaign_id}' loaded from in-memory store and set as active."
            )
            return loaded_state

        # Check if saved state exists on disk
        campaign_save_path = self._get_campaign_save_path(campaign_id)
        if os.path.exists(campaign_save_path):
            try:
                with open(campaign_save_path, encoding="utf-8") as f:
                    data = json.load(f)

                # Check version and migrate if needed
                migration_result = self._check_version(data)

                loaded_state = GameStateModel(**migration_result.data)
                # Cache it in memory and set as active
                self._active_game_state = loaded_state
                self._campaign_saves[campaign_id] = loaded_state.model_copy(deep=True)
                logger.info(
                    f"Game state for campaign '{campaign_id}' loaded from disk into in-memory store and set as active."
                )
                return loaded_state
            except Exception as e:
                logger.error(
                    f"Failed to load game state for campaign '{campaign_id}' from disk: {e}"
                )
                return None

        # No saved state found anywhere
        logger.info(
            f"No saved state found for campaign '{campaign_id}' in memory or on disk."
        )
        return None


class FileGameStateRepository(BaseGameStateRepository):
    """File-based implementation of game state repository with campaign-specific saves."""

    def __init__(self, base_save_dir: str = "saves"):
        super().__init__(base_save_dir)
        self.default_game_state_file = os.path.join(
            base_save_dir, "game_state_default_active.json"
        )
        self._active_game_state: GameStateModel = self._load_or_initialize_default()
        self._loaded_from_campaign_specific_file = False

    def _load_or_initialize_default(self) -> GameStateModel:
        if os.path.exists(self.default_game_state_file):
            try:
                with open(self.default_game_state_file, encoding="utf-8") as f:
                    data = json.load(f)

                # Check version and migrate if needed
                migration_result = self._check_version(data)

                logger.info(
                    f"Default active game state loaded from {self.default_game_state_file}"
                )
                return GameStateModel(**migration_result.data)
            except Exception as e:
                logger.error(
                    f"Failed to load default active game state from {self.default_game_state_file}: {e}. Initializing new."
                )

        # Fallback to InMemoryGameStateRepository's initialization logic for a true default
        logger.info(
            "Default active game state file not found. Initializing new default game state."
        )
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

        logger.debug(
            f"Saving game state for campaign '{state.campaign_id or 'Default'}' to {save_path}"
        )
        try:
            temp_path = save_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                # Use model_dump with mode='json' to properly serialize datetime fields
                json.dump(
                    state.model_dump(mode="json"), f, indent=2, ensure_ascii=False
                )
            os.replace(temp_path, save_path)
            logger.info(f"Game state saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save game state to {save_path}: {e}")

    def load_campaign_state(self, campaign_id: str) -> Optional[GameStateModel]:
        campaign_specific_path = self._get_campaign_save_path(campaign_id)
        if not os.path.exists(campaign_specific_path):
            logger.info(
                f"No active save file found for campaign '{campaign_id}' at {campaign_specific_path}."
            )
            return None
        try:
            with open(campaign_specific_path, encoding="utf-8") as f:
                data = json.load(f)

            # Check version and migrate if needed
            migration_result = self._check_version(data)

            loaded_state = GameStateModel(**migration_result.data)
            self._active_game_state = loaded_state  # Make it the active one in memory
            self._loaded_from_campaign_specific_file = True
            logger.info(
                f"Game state for campaign '{campaign_id}' loaded from {campaign_specific_path} and set as active."
            )
            return loaded_state
        except Exception as e:
            logger.error(
                f"Failed to load game state for campaign '{campaign_id}' from {campaign_specific_path}: {e}"
            )
            # If loading specific campaign state fails, perhaps revert to default or raise
            self._active_game_state = (
                self._load_or_initialize_default()
            )  # Revert to default on error
            self._loaded_from_campaign_specific_file = False
            return None


class GameStateRepositoryFactory:
    """Factory for creating game state repositories."""

    @staticmethod
    def create_repository(
        repo_type: str = "memory", **kwargs: Any
    ) -> GameStateRepository:
        if repo_type == "memory":
            base_dir = kwargs.get("base_save_dir", "saves")
            return InMemoryGameStateRepository(base_save_dir=base_dir)
        elif repo_type == "file":
            base_dir = kwargs.get("base_save_dir", "saves")
            return FileGameStateRepository(base_save_dir=base_dir)
        else:
            raise ValueError(f"Unknown repository type: {repo_type}")


# Avoid circular dependencies
__all__ = [
    "BaseGameStateRepository",
    "FileGameStateRepository",
    "GameStateRepository",
    "GameStateRepositoryFactory",
    "InMemoryGameStateRepository",
]
