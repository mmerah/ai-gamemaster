"""
This module contains all Pydantic models for the application,
organized in a single location for consistent validation and type safety.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, NamedTuple, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.game.calculators.dice_mechanics import get_ability_modifier

# ===== Base Classes =====


class BaseModelWithDatetimeSerializer(BaseModel):
    """Base model with datetime serialization support for Pydantic v2."""

    @field_serializer(
        "created_date",
        "last_modified",
        "timestamp",
        when_used="json",
        check_fields=False,
    )
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string."""
        return dt.isoformat() if dt else None


# ===== Configuration Models =====


class ServiceConfigModel(BaseModel):
    """Complete service configuration structure."""

    # AI Provider Settings
    AI_PROVIDER: str = Field(default="llamacpp_http")
    AI_RESPONSE_PARSING_MODE: str = Field(default="strict")
    AI_TEMPERATURE: float = Field(default=0.7)
    AI_MAX_TOKENS: int = Field(default=4096)

    # AI Retry Configuration
    AI_MAX_RETRIES: int = Field(default=3)
    AI_RETRY_DELAY: float = Field(default=5.0)
    AI_REQUEST_TIMEOUT: int = Field(default=60)
    AI_RETRY_CONTEXT_TIMEOUT: int = Field(default=300)

    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL_NAME: Optional[str] = None
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")

    # Llama.cpp HTTP Server
    LLAMA_SERVER_URL: str = Field(default="http://127.0.0.1:8080")

    # Prompt Builder Configuration
    MAX_PROMPT_TOKENS_BUDGET: int = Field(default=128000)
    LAST_X_HISTORY_MESSAGES: int = Field(default=4)
    TOKENS_PER_MESSAGE_OVERHEAD: int = Field(default=4)

    # Auto-continuation Configuration
    MAX_AI_CONTINUATION_DEPTH: int = Field(default=20)

    # RAG Settings
    RAG_ENABLED: bool = Field(default=True)
    RAG_MAX_RESULTS_PER_QUERY: int = Field(default=3)
    RAG_MAX_TOTAL_RESULTS: int = Field(default=8)
    RAG_SCORE_THRESHOLD: float = Field(default=0.2)
    RAG_EMBEDDINGS_MODEL: str = Field(default="all-MiniLM-L6-v2")
    RAG_CHUNK_SIZE: int = Field(default=500)
    RAG_CHUNK_OVERLAP: int = Field(default=50)
    RAG_COLLECTION_NAME_PREFIX: str = Field(default="ai_gamemaster")
    RAG_METADATA_FILTERING_ENABLED: bool = Field(default=False)
    RAG_RELEVANCE_FEEDBACK_ENABLED: bool = Field(default=False)
    RAG_CACHE_TTL: int = Field(default=3600)

    # TTS Settings
    TTS_PROVIDER: str = Field(default="kokoro")
    TTS_VOICE: str = Field(default="default")
    KOKORO_LANG_CODE: str = Field(default="a")
    TTS_CACHE_DIR_NAME: str = Field(default="tts_cache")

    # Repository and Directory Settings
    GAME_STATE_REPO_TYPE: str = Field(default="memory")
    CAMPAIGNS_DIR: str = Field(default="saves/campaigns")
    CHARACTER_TEMPLATES_DIR: str = Field(default="saves/character_templates")
    CAMPAIGN_TEMPLATES_DIR: str = Field(default="saves/campaign_templates")
    SAVES_DIR: str = Field(default="saves")

    # Event Queue Settings
    EVENT_QUEUE_MAX_SIZE: int = Field(default=0)

    # Flask Configuration
    SECRET_KEY: str = Field(default="you-should-change-this")
    FLASK_APP: str = Field(default="run.py")
    FLASK_DEBUG: bool = Field(default=False)
    TESTING: bool = Field(default=False)

    # Server-Sent Events (SSE) Configuration
    SSE_HEARTBEAT_INTERVAL: int = Field(default=30)
    SSE_EVENT_TIMEOUT: float = Field(default=1.0)

    # System Settings
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FILE: str = Field(default="dnd_ai_poc.log")

    # Special field for tests - not serialized
    AI_SERVICE: Optional[Any] = Field(default=None, exclude=True)

    model_config = ConfigDict(extra="ignore")


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


# ===== Character Models =====


class CharacterModifierDataModel(BaseModel):
    """Data structure for calculating character modifiers."""

    stats: Dict[str, int] = Field(
        ..., description="Ability scores like {'STR': 14, 'DEX': 16, ...}"
    )
    proficiencies: Dict[str, List[str]] = Field(
        ..., description="Proficiencies like {'skills': [...], 'armor': [...]}"
    )
    level: int = Field(..., description="Character level")

    model_config = ConfigDict(extra="forbid")


class CharacterTemplateModel(BaseModelWithDatetimeSerializer):
    """Complete character template matching JSON structure"""

    # Versioning
    version: int = Field(default=1, description="Save format version")

    # Identity
    id: str
    name: str
    race: str
    subrace: Optional[str] = None
    char_class: str
    subclass: Optional[str] = None
    level: int = Field(ge=1, le=20, default=1)
    background: str
    alignment: str

    # Stats & Mechanics
    base_stats: BaseStatsModel
    proficiencies: ProficienciesModel
    languages: List[str] = Field(default_factory=list)

    # Traits & Features
    racial_traits: List[TraitModel] = Field(default_factory=list)
    class_features: List[ClassFeatureModel] = Field(default_factory=list)
    feats: List[TraitModel] = Field(default_factory=list)

    # Spellcasting
    spells_known: List[str] = Field(default_factory=list)
    cantrips_known: List[str] = Field(default_factory=list)

    # Equipment
    starting_equipment: List["ItemModel"] = Field(default_factory=list)
    starting_gold: int = Field(ge=0, default=0)

    # Character Details
    portrait_path: Optional[str] = None
    personality_traits: List[str] = Field(default_factory=list, max_length=2)
    ideals: List[str] = Field(default_factory=list)
    bonds: List[str] = Field(default_factory=list)
    flaws: List[str] = Field(default_factory=list)
    appearance: Optional[str] = None
    backstory: Optional[str] = None

    # Metadata
    created_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None

    model_config = ConfigDict(extra="forbid")


class CharacterInstanceModel(BaseModelWithDatetimeSerializer):
    """Character state within a specific campaign"""

    # Versioning
    version: int = Field(default=1, description="Save format version")

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
    last_played: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(extra="forbid")


class CombinedCharacterModel(BaseModel):
    """Combined character model for frontend consumption.

    This model merges CharacterTemplateModel and CharacterInstanceModel data
    to provide a complete view of a character for the frontend.
    """

    # From instance
    id: str = Field(..., description="Character ID (from instance)")
    template_id: str = Field(..., description="Reference to character template")
    campaign_id: str = Field(..., description="Campaign this instance belongs to")

    # From template - identity
    name: str = Field(..., description="Character name")
    race: str = Field(..., description="Character race")
    subrace: Optional[str] = Field(None, description="Character subrace")
    char_class: str = Field(..., description="Character class", alias="class")
    subclass: Optional[str] = Field(None, description="Character subclass")
    background: str = Field(..., description="Character background")
    alignment: str = Field(..., description="Character alignment")

    # From instance - current state
    current_hp: int = Field(..., description="Current hit points")
    max_hp: int = Field(..., description="Maximum hit points")
    temp_hp: int = Field(0, description="Temporary hit points")
    level: int = Field(..., description="Current level")
    experience_points: int = Field(
        0, description="Experience points", alias="experience"
    )

    # From template - base stats
    base_stats: BaseStatsModel = Field(..., description="Base ability scores")
    armor_class: int = Field(..., description="Armor class", alias="ac")

    # From instance - conditions and resources
    conditions: List[str] = Field(default_factory=list, description="Active conditions")
    spell_slots_used: Dict[int, int] = Field(
        default_factory=dict, description="Used spell slots by level"
    )
    hit_dice_used: int = Field(0, description="Number of hit dice used")
    death_saves: Dict[str, int] = Field(
        default_factory=lambda: {"successes": 0, "failures": 0}
    )
    exhaustion_level: int = Field(0, description="Exhaustion level (0-6)")

    # From instance - inventory
    inventory: List["ItemModel"] = Field(
        default_factory=list, description="Current inventory"
    )
    gold: int = Field(0, description="Current gold pieces")

    # From template - proficiencies and features
    proficiencies: ProficienciesModel = Field(
        ..., description="Character proficiencies"
    )
    languages: List[str] = Field(default_factory=list, description="Known languages")
    racial_traits: List[TraitModel] = Field(
        default_factory=list, description="Racial traits"
    )
    class_features: List[ClassFeatureModel] = Field(
        default_factory=list, description="Class features"
    )
    feats: List[TraitModel] = Field(default_factory=list, description="Character feats")

    # From template - spells
    spells_known: List[str] = Field(default_factory=list, description="Known spells")
    cantrips_known: List[str] = Field(
        default_factory=list, description="Known cantrips"
    )

    # From template - appearance
    portrait_path: Optional[str] = Field(None, description="Path to character portrait")

    # Computed/derived fields for frontend compatibility
    hp: int = Field(..., description="Alias for current_hp")
    maximum_hp: int = Field(..., description="Alias for max_hp")

    @property
    def proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on level."""
        from app.game.calculators.dice_mechanics import get_proficiency_bonus

        return get_proficiency_bonus(self.level)

    @classmethod
    def from_template_and_instance(
        cls,
        template: "CharacterTemplateModel",
        instance: "CharacterInstanceModel",
        character_id: str,
    ) -> "CombinedCharacterModel":
        """Create a combined model from template and instance data."""
        # Calculate derived stats
        dex_mod = get_ability_modifier(template.base_stats.DEX)
        base_ac = 10 + dex_mod  # Simplified AC calculation

        return cls(
            # Identity
            id=character_id,
            template_id=instance.template_id,
            campaign_id=instance.campaign_id,
            # From template
            name=template.name,
            race=template.race,
            subrace=template.subrace,
            char_class=template.char_class,
            subclass=template.subclass,
            background=template.background,
            alignment=template.alignment,
            base_stats=template.base_stats,
            armor_class=base_ac,
            proficiencies=template.proficiencies,
            languages=template.languages,
            racial_traits=template.racial_traits,
            class_features=template.class_features,
            feats=template.feats,
            spells_known=template.spells_known,
            cantrips_known=template.cantrips_known,
            portrait_path=template.portrait_path,
            # From instance
            current_hp=instance.current_hp,
            max_hp=instance.max_hp,
            temp_hp=instance.temp_hp,
            level=instance.level,
            experience_points=instance.experience_points,
            conditions=instance.conditions,
            spell_slots_used=instance.spell_slots_used,
            hit_dice_used=instance.hit_dice_used,
            death_saves=instance.death_saves,
            exhaustion_level=instance.exhaustion_level,
            inventory=instance.inventory,
            gold=instance.gold,
            # Aliases for frontend compatibility
            hp=instance.current_hp,
            maximum_hp=instance.max_hp,
        )

    model_config = ConfigDict(populate_by_name=True)


class CharacterData(NamedTuple):
    """Combined character data from template and instance."""

    template: CharacterTemplateModel
    instance: CharacterInstanceModel
    character_id: str


# ===== Campaign Models =====


class CampaignValidationDataModel(BaseModel):
    """Data structure for campaign validation."""

    id: str = Field(..., description="Campaign ID")
    name: str = Field(..., description="Campaign name")
    description: str = Field(..., description="Campaign description")
    party_character_ids: List[str] = Field(
        ..., description="List of character IDs in the party"
    )
    difficulty: Optional[str] = Field("normal", description="Campaign difficulty")
    starting_level: Optional[int] = Field(1, description="Starting character level")

    model_config = ConfigDict(extra="forbid")


class CampaignSummaryModel(BaseModel):
    """Summary information about a campaign."""

    id: str = Field(..., description="Campaign ID")
    name: str = Field(..., description="Campaign name")
    description: str = Field(..., description="Campaign description")
    starting_level: int = Field(..., description="Starting character level")
    difficulty: str = Field(..., description="Campaign difficulty setting")
    created_date: datetime = Field(..., description="When the campaign was created")
    last_modified: Optional[datetime] = Field(
        None, description="When the campaign was last modified"
    )

    model_config = ConfigDict(extra="forbid")


class CampaignTemplateModel(BaseModelWithDatetimeSerializer):
    """Complete campaign template matching JSON structure"""

    # Versioning
    version: int = Field(default=1, description="Save format version")

    # Identity
    id: str
    name: str
    description: str

    # Core Campaign Info
    campaign_goal: str
    starting_location: LocationModel
    opening_narrative: str

    # Mechanics
    starting_level: int = Field(ge=1, le=20, default=1)
    difficulty: str = "normal"  # easy, normal, hard, deadly
    ruleset_id: str = "dnd5e_standard"
    lore_id: str = "generic_fantasy"

    # Initial Content
    initial_npcs: Dict[str, NPCModel] = Field(default_factory=dict)
    initial_quests: Dict[str, QuestModel] = Field(default_factory=dict)
    world_lore: List[str] = Field(default_factory=list)

    # Rules & Restrictions
    house_rules: HouseRulesModel = Field(default_factory=HouseRulesModel)
    allowed_races: Optional[List[str]] = None
    allowed_classes: Optional[List[str]] = None
    starting_gold_range: Optional[GoldRangeModel] = None

    # Additional Info
    theme_mood: Optional[str] = None
    world_map_path: Optional[str] = None
    session_zero_notes: Optional[str] = None
    xp_system: str = "milestone"  # milestone, xp

    # TTS Settings (default for campaigns created from this template)
    narration_enabled: bool = Field(
        default=False, description="Default narration setting for campaigns"
    )
    tts_voice: str = Field(
        default="af_heart", description="Default TTS voice for campaigns"
    )

    # Metadata
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class CampaignInstanceModel(BaseModelWithDatetimeSerializer):
    """Active campaign with current state"""

    # Versioning
    version: int = Field(default=1, description="Save format version")

    # Identity
    id: str
    name: str
    template_id: Optional[str] = None  # Link to template if created from one

    # Party
    character_ids: List[str] = Field(default_factory=list)  # Character template IDs

    # Current state
    current_location: str
    session_count: int = 0
    in_combat: bool = False
    event_summary: List[str] = Field(default_factory=list)  # Accumulated during play

    # Event tracking
    event_log_path: str  # Path to event log file
    last_event_id: Optional[str] = None

    # TTS Settings (campaign-level override, optional)
    narration_enabled: Optional[bool] = Field(
        default=None, description="Campaign-specific narration override"
    )
    tts_voice: Optional[str] = Field(
        default=None, description="Campaign-specific TTS voice override"
    )

    # Metadata
    created_date: datetime = Field(default_factory=datetime.now)
    last_played: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(extra="forbid")


class CampaignTemplateMetadata(BaseModel):
    """Metadata for a campaign template in the index."""

    id: str
    name: str
    description: str
    created_date: Optional[str] = None
    last_modified: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class CampaignInstanceMetadata(BaseModel):
    """Metadata for a campaign instance in the index."""

    version: int
    id: str
    name: str
    template_id: Optional[str] = None
    character_ids: List[str]
    current_location: str
    session_count: int
    in_combat: bool
    event_summary: List[str]
    event_log_path: str
    last_event_id: Optional[str] = None
    created_date: str
    last_played: str
    narration_enabled: Optional[bool] = None
    tts_voice: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


# ===== Combat Models =====


class NextCombatantInfoModel(BaseModel):
    """Information about the next combatant in turn order."""

    combatant_id: str = Field(..., description="ID of the next combatant")
    combatant_name: str = Field(..., description="Name of the next combatant")
    is_player: bool = Field(
        ..., description="Whether the combatant is a player character"
    )
    round_number: int = Field(..., description="Current or new round number")
    is_new_round: bool = Field(..., description="Whether this starts a new round")
    should_end_combat: Optional[bool] = Field(
        None, description="Whether combat should end"
    )
    new_index: Optional[int] = Field(None, description="New turn index")

    model_config = ConfigDict(extra="forbid")


class CombatStatusDataModel(BaseModel):
    """Combat status data structure."""

    is_active: bool = Field(..., description="Whether combat is active")
    round: Optional[int] = Field(None, description="Current combat round")
    current_turn: Optional[str] = Field(None, description="Name of current combatant")
    current_turn_id: Optional[str] = Field(None, description="ID of current combatant")
    turn_order: Optional[List[str]] = Field(
        None, description="List of combatant IDs in turn order"
    )

    model_config = ConfigDict(extra="forbid")


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


class ChatMessageDictModel(BaseModel):
    """Simple chat message for RAG context."""

    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message role"
    )
    content: str = Field(..., description="Message content")

    model_config = ConfigDict(extra="forbid")


class EventMetadataModel(BaseModel):
    """Metadata for RAG events."""

    timestamp: str = Field(..., description="ISO timestamp of the event")
    location: Optional[str] = Field(None, description="Location where event occurred")
    participants: Optional[List[str]] = Field(
        None, description="List of participants in the event"
    )
    combat_active: Optional[bool] = Field(
        None, description="Whether combat was active during event"
    )

    model_config = ConfigDict(extra="forbid")


class CombatantModel(BaseModel):
    """Enhanced combatant model with validation and helper properties."""

    id: str
    name: str
    initiative: int
    initiative_modifier: int = Field(0, description="DEX modifier for tie-breaking")
    current_hp: int = Field(ge=0, description="Current hit points (non-negative)")
    max_hp: int = Field(gt=0, description="Maximum hit points (positive)")
    armor_class: int = Field(gt=0, description="Armor class")
    conditions: List[str] = Field(default_factory=list, description="Active conditions")
    is_player: bool = Field(..., description="Flag to distinguish player chars")
    icon_path: Optional[str] = None

    # Mostly for monsters/NPCs (None for players)
    stats: Optional[Dict[str, int]] = Field(
        None, description="Ability scores (e.g., {'STR': 16, 'DEX': 14})"
    )
    abilities: Optional[List[str]] = Field(
        None, description="Special abilities or features"
    )
    attacks: Optional[List[AttackModel]] = Field(
        None, description="Available attacks and their properties"
    )
    conditions_immune: Optional[List[str]] = Field(
        None, description="Conditions the creature is immune to"
    )
    resistances: Optional[List[str]] = Field(
        None, description="Damage types the creature resists"
    )
    vulnerabilities: Optional[List[str]] = Field(
        None, description="Damage types the creature is vulnerable to"
    )

    @property
    def is_player_controlled(self) -> bool:
        """Alias for is_player to maintain compatibility."""
        return self.is_player

    @property
    def is_defeated(self) -> bool:
        """Check if combatant is defeated (0 HP)."""
        return self.current_hp <= 0

    @property
    def is_incapacitated(self) -> bool:
        """Check if combatant cannot take actions."""
        incapacitating_conditions = {
            "unconscious",
            "stunned",
            "paralyzed",
            "petrified",
            "incapacitated",
        }
        return self.is_defeated or any(
            cond.lower() in incapacitating_conditions for cond in self.conditions
        )

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    def model_post_init(self, __context: Optional[Any] = None) -> None:
        """Validate HP relationship after initialization."""
        if self.current_hp > self.max_hp:
            raise ValueError(
                f"current_hp ({self.current_hp}) cannot exceed max_hp ({self.max_hp})"
            )


class CombatStateModel(BaseModel):
    """Enhanced combat state model with helper methods."""

    is_active: bool = False
    combatants: List[CombatantModel] = Field(default_factory=list)
    current_turn_index: int = -1  # -1 when no initiative set
    round_number: int = 1
    # Removed monster_stats - all data now stored in combatants with merged fields
    current_turn_instruction_given: bool = Field(
        default=False, description="Whether NPC turn instruction was given this turn"
    )

    # Private field for internal state tracking (not persisted)
    _combat_just_started_flag: bool = False

    def get_current_combatant(self) -> Optional[CombatantModel]:
        """Get the combatant whose turn it is."""
        if (
            not self.is_active
            or not self.combatants
            or not (0 <= self.current_turn_index < len(self.combatants))
        ):
            return None
        return self.combatants[self.current_turn_index]

    def get_combatant_by_id(self, combatant_id: str) -> Optional[CombatantModel]:
        """Find a combatant by ID."""
        for combatant in self.combatants:
            if combatant.id == combatant_id:
                return combatant
        return None

    def get_initiative_order(self) -> List[CombatantModel]:
        """Get combatants sorted by initiative (highest first), with DEX tie-breaker."""
        return sorted(
            self.combatants,
            key=lambda c: (c.initiative, c.initiative_modifier),
            reverse=True,
        )

    def get_next_active_combatant_index(self) -> tuple[int, int]:
        """
        Get the index of the next active (non-incapacitated) combatant.
        Returns (next_index, new_round_number).
        """
        if not self.combatants:
            return -1, self.round_number

        start_index = self.current_turn_index
        new_round_number = self.round_number
        wrapped = False

        # Try each combatant in turn order
        for i in range(1, len(self.combatants) + 1):
            next_index = (start_index + i) % len(self.combatants)

            # Check if we wrapped around the list
            if next_index <= start_index and not wrapped:
                wrapped = True
                new_round_number = self.round_number + 1

            combatant = self.combatants[next_index]
            if not combatant.is_incapacitated:
                return next_index, new_round_number

        # All combatants are incapacitated
        return -1, self.round_number

    @property
    def is_players_turn(self) -> bool:
        """Check if it's currently a player's turn."""
        current = self.get_current_combatant()
        return current is not None and current.is_player

    model_config = ConfigDict(extra="forbid")


class InitialCombatantData(BaseModel):
    """Core game model for initial combatant data when starting combat."""

    id: str = Field(..., description="Unique identifier for the combatant")
    name: str = Field(..., description="Display name of the combatant")
    hp: int = Field(..., description="Starting hit points")
    ac: int = Field(..., description="Armor class")
    stats: Optional[Dict[str, int]] = Field(
        None, description="Ability scores (e.g., {'DEX': 14, 'STR': 12})"
    )
    abilities: Optional[List[str]] = Field(
        None, description="Special abilities or features"
    )
    attacks: Optional[List[AttackModel]] = Field(
        None, description="Available attacks and their properties"
    )
    icon_path: Optional[str] = Field(
        None, description="Path to character portrait/icon"
    )

    model_config = ConfigDict(extra="forbid")


class CombatInfoResponseModel(BaseModel):
    """Combat information response model for frontend display."""

    is_active: bool = Field(..., description="Whether combat is currently active")
    round_number: int = Field(default=0, description="Current combat round")
    current_combatant_id: Optional[str] = Field(
        None, description="ID of current combatant"
    )
    current_combatant_name: Optional[str] = Field(
        None, description="Name of current combatant"
    )
    combatants: List[CombatantModel] = Field(
        default_factory=list, description="List of combatants"
    )
    turn_order: List[str] = Field(
        default_factory=list, description="Turn order by combatant ID"
    )

    model_config = ConfigDict(extra="forbid")


# ===== Dice Models =====


class DiceExecutionModel(BaseModel):
    """Internal model for dice roll execution results."""

    # Success fields
    total: Optional[int] = Field(None, description="Total result of the roll")
    individual_rolls: Optional[List[int]] = Field(
        None, description="Individual die results"
    )
    formula_description: Optional[str] = Field(
        None, description="Human-readable formula description"
    )

    # Error field
    error: Optional[str] = Field(None, description="Error message if roll failed")

    @property
    def is_error(self) -> bool:
        """Check if this represents an error result."""
        return self.error is not None

    model_config = ConfigDict(extra="forbid")


class DiceRollSubmissionModel(BaseModel):
    """Dice roll submission from frontend."""

    character_id: str = Field(..., description="ID of the character rolling")
    roll_type: str = Field(..., description="Type of roll")
    dice_formula: str = Field(..., description="Dice formula")
    request_id: Optional[str] = Field(
        None, description="Request ID if responding to a request"
    )
    total: Optional[int] = Field(None, description="Optional pre-calculated total")
    skill: Optional[str] = Field(None, description="Skill name for skill checks")
    ability: Optional[str] = Field(None, description="Ability name for ability checks")
    dc: Optional[int] = Field(None, description="Difficulty class")
    reason: Optional[str] = Field(None, description="Reason for the roll")
    character_name: Optional[str] = Field(
        None, description="Character name (sometimes included)"
    )

    model_config = ConfigDict(extra="forbid")


class DiceSubmissionEventModel(BaseModel):
    """Dice submission event data."""

    rolls: List[DiceRollSubmissionModel] = Field(..., description="List of dice rolls")

    model_config = ConfigDict(extra="forbid")


class DiceRequestModel(BaseModel):
    """Core game model for dice roll requests."""

    request_id: str = Field(
        ..., description="Unique ID for this specific roll request instance."
    )
    character_ids: List[str] = Field(
        ..., description="List of character IDs required to roll."
    )
    type: str = Field(
        ...,
        description="Type of roll (e.g., 'skill_check', 'saving_throw', 'initiative').",
    )
    dice_formula: str = Field(
        ..., description="Base dice formula (e.g., '1d20', '2d6+3')."
    )
    reason: str = Field(
        ..., description="Brief explanation for the roll shown to the player."
    )
    skill: Optional[str] = Field(
        None, description="Specific skill if type is 'skill_check'."
    )
    ability: Optional[str] = Field(
        None, description="Specific ability score if type is 'saving_throw' or related."
    )
    dc: Optional[int] = Field(None, description="Difficulty Class if applicable.")

    model_config = ConfigDict(extra="forbid")


class DiceRollResultModel(BaseModel):
    """Core game model for dice roll results."""

    character_id: str = Field(..., description="ID of the character who rolled")
    roll_type: str = Field(
        ..., description="Type of roll (e.g., 'attack', 'damage', 'skill_check')"
    )
    total: int = Field(..., description="Total result of the roll")
    result_summary: str = Field(
        ..., description="Brief summary of the roll (e.g., 'Elara: Attack Roll = 18')"
    )
    result_message: Optional[str] = Field(
        None, description="Detailed message about the roll"
    )
    skill: Optional[str] = Field(
        None, description="Skill name if this was a skill check"
    )
    ability: Optional[str] = Field(
        None, description="Ability name if this was an ability check"
    )
    dc: Optional[int] = Field(None, description="Difficulty class if applicable")
    reason: Optional[str] = Field(None, description="Reason for the roll")
    original_request_id: Optional[str] = Field(
        None, description="ID of the original request that triggered this roll"
    )

    model_config = ConfigDict(extra="forbid")


class DiceRollMessageModel(BaseModel):
    """Formatted dice roll messages."""

    detailed: str = Field(..., description="Detailed roll message with all information")
    summary: str = Field(..., description="Brief summary of the roll result")

    model_config = ConfigDict(extra="forbid")


class DiceRollResultResponseModel(BaseModel):
    """Response model for dice roll results."""

    request_id: str = Field(..., description="Request identifier")
    character_id: str = Field(..., description="Character who rolled")
    character_name: str = Field(..., description="Character name")
    roll_type: str = Field(..., description="Type of roll")
    dice_formula: str = Field(..., description="Dice formula used")
    character_modifier: int = Field(..., description="Character modifier applied")
    total_result: int = Field(..., description="Total result of roll")
    dc: Optional[int] = Field(None, description="Difficulty class if applicable")
    success: Optional[bool] = Field(None, description="Whether roll succeeded")
    reason: str = Field(..., description="Reason for roll")
    result_message: str = Field(..., description="Detailed result message")
    result_summary: str = Field(..., description="Brief result summary")
    error: Optional[str] = Field(None, description="Error message if roll failed")

    model_config = ConfigDict(extra="forbid")


# ===== Game State & Chat Models =====


class ChatMessageModel(BaseModel):
    """Core game model for chat history messages."""

    id: str = Field(..., description="Unique message identifier")
    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message role"
    )
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    is_dice_result: Optional[bool] = Field(
        False, description="Whether message represents dice roll results"
    )
    gm_thought: Optional[str] = Field(
        None, description="GM's internal thought or reasoning"
    )
    ai_response_json: Optional[str] = Field(
        None, description="Full AI response in JSON format"
    )
    detailed_content: Optional[str] = Field(
        None, description="Detailed content for expandable messages"
    )
    audio_path: Optional[str] = Field(None, description="Path to audio file for TTS")

    model_config = ConfigDict(extra="forbid")


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


# ===== Knowledge/RAG Models =====


class LoreDataModel(BaseModel):
    """Structure for lore entries."""

    id: str = Field(..., description="Lore entry ID")
    name: str = Field(..., description="Lore entry name")
    description: str = Field(..., description="Brief description")
    content: str = Field(..., description="Full lore content")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    category: Optional[str] = Field(None, description="Lore category")

    model_config = ConfigDict(extra="forbid")


class RulesetDataModel(BaseModel):
    """Structure for ruleset entries."""

    id: str = Field(..., description="Ruleset ID")
    name: str = Field(..., description="Ruleset name")
    description: str = Field(..., description="Ruleset description")
    rules: Dict[str, str] = Field(..., description="Map of rule names to descriptions")
    version: str = Field(..., description="Ruleset version")
    category: Optional[str] = Field(None, description="Ruleset category")

    model_config = ConfigDict(extra="forbid")


# ===== Event/Action Models =====


class PlayerActionEventModel(BaseModel):
    """Player action event data."""

    action_type: str = Field(..., description="Action type (e.g., 'free_text')")
    value: str = Field(..., description="The actual action text")
    character_id: Optional[str] = Field(None, description="Optional character ID")

    model_config = ConfigDict(extra="forbid")


class GameEventModel(BaseModel):
    """Base game event structure."""

    type: Literal["player_action", "dice_submission", "next_step", "retry"] = Field(
        ..., description="Event type"
    )
    data: Union[PlayerActionEventModel, DiceSubmissionEventModel, Dict[str, str]] = (
        Field(..., description="Event-specific data")
    )
    session_id: Optional[str] = Field(None, description="Optional session ID")

    model_config = ConfigDict(extra="forbid")


class AIRequestContextModel(BaseModel):
    """Context stored for AI request retry."""

    messages: List[Dict[str, str]] = Field(
        ..., description="Chat messages for AI context"
    )
    initial_instruction: Optional[str] = Field(
        None, description="Initial system instruction"
    )

    model_config = ConfigDict(extra="forbid")


class GameEventResponseModel(BaseModel):
    """Response model from game event handling."""

    # Game state data
    party: List[CombinedCharacterModel] = Field(..., description="Party members data")
    location: str = Field(..., description="Current location name")
    location_description: str = Field(..., description="Location description")
    chat_history: List[ChatMessageModel] = Field(..., description="Chat messages")
    dice_requests: List[DiceRequestModel] = Field(
        ..., description="Pending dice requests"
    )
    combat_info: Optional[CombatInfoResponseModel] = Field(
        None, description="Combat state info"
    )

    # Response metadata
    error: Optional[str] = Field(None, description="Error message if any")
    success: Optional[bool] = Field(None, description="Whether operation succeeded")
    message: Optional[str] = Field(None, description="Status message")
    needs_backend_trigger: Optional[bool] = Field(
        None, description="Whether backend should auto-trigger"
    )
    status_code: Optional[int] = Field(None, description="HTTP status code")
    can_retry_last_request: Optional[bool] = Field(
        None, description="Whether retry is available"
    )
    submitted_roll_results: Optional[List[DiceRollResultResponseModel]] = Field(
        None, description="Dice submission results"
    )

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
