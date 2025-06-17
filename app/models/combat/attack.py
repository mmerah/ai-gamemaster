"""
Attack model for combat.

This module contains the AttackModel used for creature/NPC attacks.
"""

from typing import TYPE_CHECKING, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.domain.validators.content_validator import (
        ContentValidationError,
        ContentValidator,
    )


class AttackModel(BaseModel):
    """Model for creature/NPC attacks."""

    name: str = Field(..., description="Attack name (e.g., 'scimitar', 'bite')")
    description: str = Field(..., description="Full attack description with mechanics")
    # Optional parsed fields for future use
    attack_type: Optional[Literal["melee", "ranged"]] = Field(
        None, description="Type of attack"
    )
    to_hit_bonus: Optional[int] = Field(None, description="Attack roll bonus")
    reach: Optional[str] = Field(None, description="Melee reach (e.g., '5 ft')")
    range: Optional[str] = Field(
        None, description="Ranged distance (e.g., '80/320 ft')"
    )
    damage_formula: Optional[str] = Field(
        None, description="Damage dice (e.g., '1d6+2')"
    )
    damage_type: Optional[str] = Field(
        None, description="Damage type (e.g., 'slashing', 'piercing')"
    )

    model_config = ConfigDict(extra="forbid")

    def validate_content(
        self,
        validator: "ContentValidator",
        content_pack_priority: Optional[List[str]] = None,
    ) -> Tuple[bool, List["ContentValidationError"]]:
        """Validate D&D 5e content references in this attack.

        Args:
            validator: The content validator to use
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors: List["ContentValidationError"] = []

        # Validate damage type if present
        if self.damage_type:
            invalid_damage_types = validator._validate_list_content(
                [self.damage_type],
                "damage-types",
                content_pack_priority=content_pack_priority,
            )
            if invalid_damage_types:
                from app.domain.validators.content_validator import (
                    ContentValidationError,
                )

                errors.append(
                    ContentValidationError(
                        "damage_type",
                        self.damage_type,
                        f"Invalid damage type: {self.damage_type}",
                    )
                )

        return (len(errors) == 0, errors)
