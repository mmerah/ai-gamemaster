"""
Game state and action models.

This module contains game state, chat, and action-related models.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.character import CharacterInstanceModel
from app.models.combat import CombatStateModel
from app.models.dice import DiceRequestModel
from app.models.shared import ChatMessageModel
from app.models.utils import LocationModel, NPCModel, QuestModel


class GameStateModel(BaseModel):
    """Complete game state matching the active game structure."""

    # Versioning
    version: int = Field(default=1, description="Save format version")

    # Campaign identity
    campaign_id: Optional[str] = None
    campaign_name: Optional[str] = None

    # Campaign-specific context
    active_ruleset_id: Optional[str] = None
    active_lore_id: Optional[str] = None
    event_log_path: Optional[str] = None

    # Party state - using CharacterInstanceModel
    party: Dict[str, CharacterInstanceModel] = Field(default_factory=dict)

    # Location
    current_location: LocationModel = Field(
        default_factory=lambda: LocationModel(name="Unknown", description="")
    )

    # Chat and dice - properly typed
    chat_history: List[ChatMessageModel] = Field(default_factory=list)
    pending_player_dice_requests: List[DiceRequestModel] = Field(default_factory=list)

    # Combat
    combat: CombatStateModel = Field(default_factory=CombatStateModel)

    # Campaign context
    campaign_goal: str = "No specific goal set."
    known_npcs: Dict[str, NPCModel] = Field(default_factory=dict)
    active_quests: Dict[str, QuestModel] = Field(default_factory=dict)
    world_lore: List[str] = Field(default_factory=list)
    event_summary: List[str] = Field(default_factory=list)

    # Session tracking
    session_count: int = 0
    in_combat: bool = False
    last_event_id: Optional[str] = None

    # TTS Settings (game session override - highest priority)
    narration_enabled: bool = Field(
        default=False, description="Current game session narration setting"
    )
    tts_voice: str = Field(
        default="af_heart", description="Current game session TTS voice"
    )

    # Content Management
    content_pack_priority: List[str] = Field(
        default_factory=lambda: ["dnd_5e_srd"],
        description="Content pack IDs in priority order (first = highest priority)",
    )

    # Private fields (excluded from serialization)
    _pending_npc_roll_results: List[Any] = []  # Can be DiceRollResultModel or dict
    _last_rag_context: Optional[str] = None

    @field_validator("chat_history", mode="before")
    def validate_chat_history(cls, v: object) -> List[ChatMessageModel]:
        """Convert chat history dict to ChatMessageModel objects."""
        if not v:
            return []

        if not isinstance(v, list):
            return []

        result: List[ChatMessageModel] = []
        for item in v:
            if isinstance(item, dict):
                # Add defaults for required fields if missing
                if "id" not in item:
                    item["id"] = f"msg_{uuid4()}"
                if "timestamp" not in item:
                    item["timestamp"] = datetime.now(timezone.utc).isoformat()
                result.append(ChatMessageModel(**item))
            else:
                result.append(item)
        return result

    @field_validator("pending_player_dice_requests", mode="before")
    def validate_dice_requests(cls, v: object) -> List[DiceRequestModel]:
        """Convert dice request dicts to DiceRequestModel objects."""
        if not v:
            return []

        if not isinstance(v, list):
            return []

        result = []
        for item in v:
            if isinstance(item, dict):
                result.append(DiceRequestModel(**item))
            else:
                result.append(item)
        return result

    model_config = ConfigDict(extra="forbid")
