"""
Utility and basic models.

This module contains basic model structures and utility models used throughout the application.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.domain.validators.content_validator import (
        ContentValidationError,
        ContentValidator,
    )

# ===== Basic/Primitive Models =====


class ItemModel(BaseModel):
    """Equipment/Item structure"""

    id: str
    name: str
    description: str
    quantity: int = Field(ge=1, default=1)

    model_config = ConfigDict(extra="forbid")


class LocationModel(BaseModel):
    """Location structure"""

    name: str
    description: str

    model_config = ConfigDict(extra="forbid")


class NPCModel(BaseModel):
    """NPC structure for campaigns"""

    id: str
    name: str
    description: str
    last_location: str

    model_config = ConfigDict(extra="forbid")


class QuestModel(BaseModel):
    """Quest structure for campaigns"""

    id: str
    title: str
    description: str
    status: str = "active"  # active, completed, failed, inactive

    model_config = ConfigDict(extra="forbid")


class BaseStatsModel(BaseModel):
    """Runtime character ability scores.

    This represents the current state of a character's abilities,
    not the static D&D 5e ability score definitions.
    """

    STR: int = Field(ge=1, le=30)
    DEX: int = Field(ge=1, le=30)
    CON: int = Field(ge=1, le=30)
    INT: int = Field(ge=1, le=30)
    WIS: int = Field(ge=1, le=30)
    CHA: int = Field(ge=1, le=30)

    model_config = ConfigDict(extra="forbid")


class ProficienciesModel(BaseModel):
    """Runtime character proficiencies.

    This represents a character's current proficiencies,
    not the static D&D 5e proficiency definitions.
    """

    armor: List[str] = Field(default_factory=list)
    weapons: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    saving_throws: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    def validate_content(
        self,
        validator: "ContentValidator",
        content_pack_priority: Optional[List[str]] = None,
    ) -> Tuple[bool, List["ContentValidationError"]]:
        """Validate D&D 5e content references in proficiencies.

        Args:
            validator: The content validator to use
            content_pack_priority: List of content pack IDs in priority order

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        return validator.validate_proficiencies(self, content_pack_priority)


class TraitModel(BaseModel):
    """Runtime character trait.

    This represents a trait actively possessed by a character,
    not the static D&D 5e trait definitions.
    """

    name: str
    description: str

    model_config = ConfigDict(extra="forbid")


class ClassFeatureModel(BaseModel):
    """Runtime character class feature.

    This represents a feature actively possessed by a character,
    not the static D&D 5e feature definitions.
    """

    name: str
    description: str
    level_acquired: int = Field(ge=1, le=20)

    model_config = ConfigDict(extra="forbid")


class HouseRulesModel(BaseModel):
    """House rules configuration"""

    critical_hit_tables: bool = False
    flanking_rules: bool = False
    milestone_leveling: bool = True
    death_saves_public: bool = False

    model_config = ConfigDict(extra="forbid")


class GoldRangeModel(BaseModel):
    """Gold range for starting equipment"""

    min: int = Field(ge=0)
    max: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid")


# ===== Utility Models =====


class VoiceInfoModel(BaseModel):
    """TTS voice information."""

    id: str = Field(..., description="Voice identifier")
    name: str = Field(..., description="Voice display name")

    model_config = ConfigDict(extra="forbid")


class TemplateValidationResult(BaseModel):
    """Result of template ID validation."""

    template_id: str = Field(..., description="Template ID that was validated")
    exists: bool = Field(..., description="Whether the template exists")

    model_config = ConfigDict(extra="forbid")


class TemplateValidationResultsModel(BaseModel):
    """Results of multiple template ID validations."""

    results: List[TemplateValidationResult] = Field(
        ..., description="Validation results for each template ID"
    )

    def to_dict(self) -> Dict[str, bool]:
        """Convert to dict format for backward compatibility."""
        return {result.template_id: result.exists for result in self.results}

    model_config = ConfigDict(extra="forbid")


class MigrationResultModel(BaseModel):
    """Result of data migration/version check."""

    data: Dict[str, Any] = Field(..., description="Migrated data")
    version: int = Field(..., description="Current version after migration")
    migrated: bool = Field(..., description="Whether migration was performed")

    model_config = ConfigDict(extra="forbid")


class SharedHandlerStateModel(BaseModel):
    """Shared state between handlers."""

    ai_processing: bool = Field(..., description="Whether AI is currently processing")
    needs_backend_trigger: bool = Field(
        ..., description="Whether backend trigger is needed"
    )

    model_config = ConfigDict(extra="forbid")


class TokenStatsModel(BaseModel):
    """Token usage statistics."""

    total_prompt_tokens: int = Field(0, description="Total prompt tokens used")
    total_completion_tokens: int = Field(0, description="Total completion tokens used")
    total_tokens: int = Field(0, description="Total tokens used")
    call_count: int = Field(0, description="Number of API calls")
    average_tokens_per_call: float = Field(
        0.0, description="Average tokens per API call"
    )

    model_config = ConfigDict(extra="forbid")
