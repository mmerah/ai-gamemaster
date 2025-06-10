"""
Utility and basic models.

This module contains basic model structures and utility models used throughout the application.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

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
    """D&D base ability scores"""

    STR: int = Field(ge=1, le=30)
    DEX: int = Field(ge=1, le=30)
    CON: int = Field(ge=1, le=30)
    INT: int = Field(ge=1, le=30)
    WIS: int = Field(ge=1, le=30)
    CHA: int = Field(ge=1, le=30)

    model_config = ConfigDict(extra="forbid")


class ProficienciesModel(BaseModel):
    """All proficiency types"""

    armor: List[str] = Field(default_factory=list)
    weapons: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    saving_throws: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class TraitModel(BaseModel):
    """Racial trait or feat structure"""

    name: str
    description: str

    model_config = ConfigDict(extra="forbid")


class ClassFeatureModel(BaseModel):
    """Class feature with level info"""

    name: str
    description: str
    level_acquired: int = Field(ge=1, le=20)

    model_config = ConfigDict(extra="forbid")


class D5EClassModel(BaseModel):
    """D&D 5e class data model."""

    name: str = Field(..., description="Class name")
    hit_die: int = Field(..., description="Hit die size (e.g., 6 for d6)")
    primary_ability: str = Field(..., description="Primary ability score")
    saving_throw_proficiencies: List[str] = Field(
        ..., description="Saving throw proficiencies"
    )
    skill_proficiencies: List[str] = Field(
        ..., description="Available skill proficiencies"
    )
    num_skill_proficiencies: int = Field(..., description="Number of skills to choose")
    starting_equipment: List[str] = Field(
        default_factory=list, description="Starting equipment"
    )

    model_config = ConfigDict(extra="forbid")


class ArmorModel(BaseModel):
    """Armor data model."""

    name: str = Field(..., description="Armor name")
    base_ac: int = Field(..., description="Base armor class")
    type: str = Field(..., description="Armor type: light, medium, heavy, or shield")
    ac_bonus: Optional[int] = Field(None, description="AC bonus (for shields)")
    max_dex_bonus: Optional[int] = Field(
        None, description="Maximum DEX bonus (for medium/heavy armor)"
    )
    strength_requirement: int = Field(
        default=0, description="Minimum strength requirement"
    )
    stealth_disadvantage: bool = Field(
        default=False, description="Whether armor gives stealth disadvantage"
    )
    weight: Optional[float] = Field(None, description="Weight of the armor")
    cost: Optional[int] = Field(None, description="Cost in gold pieces")

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
