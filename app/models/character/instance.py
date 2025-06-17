"""
Character instance model.

This module contains the CharacterInstanceModel which tracks dynamic
character state during gameplay (HP, inventory, conditions, etc.).
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from pydantic import ConfigDict, Field

from app.models.base import BaseModelWithDatetimeSerializer
from app.models.utils import ItemModel

if TYPE_CHECKING:
    from app.domain.validators.content_validator import (
        ContentValidationError,
        ContentValidator,
    )


class CharacterInstanceModel(BaseModelWithDatetimeSerializer):
    """Character instance data that tracks dynamic state during gameplay.

    This model represents the mutable state of a character within a specific
    campaign (HP, inventory, conditions, etc.). Each instance is tied to
    a character template and a campaign.
    """

    # Versioning
    version: int = Field(default=1, description="Save format version")

    # Identity
    id: str
    name: str  # Character name (may differ from template if renamed)

    # Link to template
    template_id: str
    campaign_id: str

    # Current state
    current_hp: int
    max_hp: int
    temp_hp: int = 0

    # Experience
    experience_points: int = 0
    level: int = Field(ge=1, le=20)

    # Resources
    spell_slots_used: Dict[int, int] = Field(
        default_factory=dict
    )  # level -> used slots
    hit_dice_used: int = 0
    death_saves: Dict[str, int] = Field(
        default_factory=lambda: {"successes": 0, "failures": 0}
    )

    # Inventory (extends starting equipment)
    inventory: List[ItemModel] = Field(default_factory=list)
    gold: int = 0

    # Conditions & Effects
    conditions: List[str] = Field(default_factory=list)
    exhaustion_level: int = Field(ge=0, le=6, default=0)

    # Campaign-specific data
    notes: str = ""
    achievements: List[str] = Field(default_factory=list)
    relationships: Dict[str, str] = Field(
        default_factory=dict
    )  # NPC ID -> relationship

    # Last activity
    last_played: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(extra="forbid")

    def validate_content(
        self,
        validator: "ContentValidator",
        content_pack_priority: Optional[List[str]] = None,
    ) -> Tuple[bool, List["ContentValidationError"]]:
        """Validate D&D 5e content references in this character instance.

        Args:
            validator: The content validator to use
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: List["ContentValidationError"] = []

        # Validate conditions
        if self.conditions:
            invalid_conditions = validator._validate_list_content(
                self.conditions,
                "conditions",
                content_pack_priority=content_pack_priority,
            )
            if invalid_conditions:
                from app.domain.validators.content_validator import (
                    ContentValidationError,
                )

                errors.append(
                    ContentValidationError(
                        "conditions",
                        invalid_conditions,
                        f"Invalid conditions: {', '.join(invalid_conditions)}",
                    )
                )

        return (len(errors) == 0, errors)
