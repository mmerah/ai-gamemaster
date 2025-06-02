"""
Unified data models that serve as the single source of truth for all data structures.
These models are used to:
1. Define the complete schema for all entities
2. Generate TypeScript interfaces automatically
3. Validate data consistency across JSON, backend, and frontend
"""

from typing import List, Optional, Dict, Any, Union, Literal
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict, field_serializer, field_validator

# Import sequence number utilities
from app.utils.event_sequence import get_next_sequence_number

# No more imports from ai_services.schemas to avoid circular dependency


# ===== BASE CLASSES =====

class BaseModelWithDatetimeSerializer(BaseModel):
    """Base model with datetime serialization support for Pydantic v2."""
    
    @field_serializer('created_date', 'last_modified', 'timestamp', when_used='json', check_fields=False)
    def serialize_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string."""
        return dt.isoformat() if dt else None


# ===== BASE TYPES =====

class ItemModel(BaseModel):
    """Equipment/Item structure"""
    id: str
    name: str
    description: str
    quantity: int = Field(ge=1, default=1)
    
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


class LocationModel(BaseModel):
    """Location structure"""
    name: str
    description: str
    
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


# ===== CHARACTER TEMPLATE =====

class CharacterTemplateModel(BaseModelWithDatetimeSerializer):
    """Complete character template matching JSON structure"""
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
    starting_equipment: List[ItemModel] = Field(default_factory=list)
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


# ===== CAMPAIGN TEMPLATE =====

class CampaignTemplateModel(BaseModelWithDatetimeSerializer):
    """Complete campaign template matching JSON structure"""
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
    narration_enabled: bool = Field(default=False, description="Default narration setting for campaigns")
    tts_voice: str = Field(default="af_heart", description="Default TTS voice for campaigns")
    
    # Metadata
    created_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_modified: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(extra="forbid")


# ===== CHARACTER INSTANCE (IN-CAMPAIGN STATE) =====

class CharacterInstanceModel(BaseModelWithDatetimeSerializer):
    """Character state within a specific campaign"""
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
    spell_slots_used: Dict[int, int] = Field(default_factory=dict)  # level -> used slots
    hit_dice_used: int = 0
    death_saves: Dict[str, int] = Field(default_factory=lambda: {"successes": 0, "failures": 0})
    
    # Inventory (extends starting equipment)
    inventory: List[ItemModel] = Field(default_factory=list)
    gold: int = 0
    
    # Conditions & Effects
    conditions: List[str] = Field(default_factory=list)
    exhaustion_level: int = Field(ge=0, le=6, default=0)
    
    # Campaign-specific data
    notes: str = ""
    achievements: List[str] = Field(default_factory=list)
    relationships: Dict[str, str] = Field(default_factory=dict)  # NPC ID -> relationship
    
    # Last activity
    last_played: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(extra="forbid")


# ===== CAMPAIGN INSTANCE =====

class CampaignInstanceModel(BaseModelWithDatetimeSerializer):
    """Active campaign with current state"""
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
    narration_enabled: Optional[bool] = Field(default=None, description="Campaign-specific narration override")
    tts_voice: Optional[str] = Field(default=None, description="Campaign-specific TTS voice override")
    
    # Metadata
    created_date: datetime = Field(default_factory=datetime.now)
    last_played: datetime = Field(default_factory=datetime.now)
    
    model_config = ConfigDict(extra="forbid")


# ===== COMBAT MODELS =====

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
            "unconscious", "stunned", "paralyzed", "petrified", "incapacitated"
        }
        return self.is_defeated or any(
            cond.lower() in incapacitating_conditions 
            for cond in self.conditions
        )
    
    model_config = ConfigDict(extra="forbid", validate_assignment=True)
    
    def model_post_init(self, __context: Any) -> None:
        """Validate HP relationship after initialization."""
        if self.current_hp > self.max_hp:
            raise ValueError(f"current_hp ({self.current_hp}) cannot exceed max_hp ({self.max_hp})")


class MonsterBaseStats(BaseModel):
    """Core game model for monster/NPC base statistics stored in combat state."""
    name: str = Field(..., description="Monster/NPC name")
    initial_hp: int = Field(..., description="Maximum hit points at start of combat")
    ac: int = Field(..., description="Armor class")
    stats: Optional[Dict[str, int]] = Field(None, description="Ability scores (e.g., {'STR': 16, 'DEX': 14})")
    abilities: Optional[List[str]] = Field(None, description="Special abilities or features")
    attacks: Optional[List[Dict]] = Field(None, description="Available attacks and their properties")
    conditions_immune: Optional[List[str]] = Field(None, description="Conditions the creature is immune to")
    resistances: Optional[List[str]] = Field(None, description="Damage types the creature resists")
    vulnerabilities: Optional[List[str]] = Field(None, description="Damage types the creature is vulnerable to")

    model_config = ConfigDict(extra="forbid")


class CombatStateModel(BaseModel):
    """Enhanced combat state model with helper methods."""
    is_active: bool = False
    combatants: List[CombatantModel] = Field(default_factory=list)
    current_turn_index: int = -1  # -1 when no initiative set
    round_number: int = 1
    monster_stats: Dict[str, MonsterBaseStats] = Field(
        default_factory=dict,
        description="Base stats for monsters in combat"
    )
    current_turn_instruction_given: bool = Field(
        default=False,
        description="Whether NPC turn instruction was given this turn"
    )
    
    # Private field for internal state tracking (not persisted)
    _combat_just_started_flag: bool = False
    
    def get_current_combatant(self) -> Optional[CombatantModel]:
        """Get the combatant whose turn it is."""
        if (not self.is_active or 
            not self.combatants or
            not (0 <= self.current_turn_index < len(self.combatants))):
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
            reverse=True
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


# ===== COMBINED MODELS FOR FRONTEND =====

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
    experience_points: int = Field(0, description="Experience points", alias="experience")
    
    # From template - base stats
    base_stats: BaseStatsModel = Field(..., description="Base ability scores")
    armor_class: int = Field(..., description="Armor class", alias="ac")
    
    # From instance - conditions and resources
    conditions: List[str] = Field(default_factory=list, description="Active conditions")
    spell_slots_used: Dict[int, int] = Field(default_factory=dict, description="Used spell slots by level")
    hit_dice_used: int = Field(0, description="Number of hit dice used")
    death_saves: Dict[str, int] = Field(default_factory=lambda: {"successes": 0, "failures": 0})
    exhaustion_level: int = Field(0, description="Exhaustion level (0-6)")
    
    # From instance - inventory
    inventory: List[ItemModel] = Field(default_factory=list, description="Current inventory")
    gold: int = Field(0, description="Current gold pieces")
    
    # From template - proficiencies and features
    proficiencies: ProficienciesModel = Field(..., description="Character proficiencies")
    languages: List[str] = Field(default_factory=list, description="Known languages")
    racial_traits: List[TraitModel] = Field(default_factory=list, description="Racial traits")
    class_features: List[ClassFeatureModel] = Field(default_factory=list, description="Class features")
    feats: List[TraitModel] = Field(default_factory=list, description="Character feats")
    
    # From template - spells
    spells_known: List[str] = Field(default_factory=list, description="Known spells")
    cantrips_known: List[str] = Field(default_factory=list, description="Known cantrips")
    
    # From template - appearance
    portrait_path: Optional[str] = Field(None, description="Path to character portrait")
    
    # Computed/derived fields for frontend compatibility
    hp: int = Field(..., description="Alias for current_hp")
    maximum_hp: int = Field(..., description="Alias for max_hp")
    
    @classmethod
    def from_template_and_instance(
        cls, 
        template: 'CharacterTemplateModel', 
        instance: 'CharacterInstanceModel',
        character_id: str
    ) -> 'CombinedCharacterModel':
        """Create a combined model from template and instance data."""
        # Calculate derived stats
        from app.game.calculators.character_stats import get_ability_modifier
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
            armor_class=base_ac,  # Could be overridden by equipment
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
            maximum_hp=instance.max_hp
        )
    
    model_config = ConfigDict(populate_by_name=True)


# ===== COMMUNICATION MODELS =====

class ChatMessage(BaseModel):
    """Core game model for chat history messages."""
    id: str = Field(..., description="Unique message identifier")
    role: Literal["user", "assistant", "system"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    is_dice_result: Optional[bool] = Field(False, description="Whether message represents dice roll results")
    gm_thought: Optional[str] = Field(None, description="GM's internal thought or reasoning")
    ai_response_json: Optional[str] = Field(None, description="Full AI response in JSON format")
    detailed_content: Optional[str] = Field(None, description="Detailed content for expandable messages")
    audio_path: Optional[str] = Field(None, description="Path to audio file for TTS")

    model_config = ConfigDict(extra="forbid")


# ===== DICE & GAME MECHANICS =====

class DiceRequest(BaseModel):
    """Core game model for dice roll requests."""
    request_id: str = Field(..., description="Unique ID for this specific roll request instance.")
    character_ids: List[str] = Field(..., description="List of character IDs required to roll.")
    type: str = Field(..., description="Type of roll (e.g., 'skill_check', 'saving_throw', 'initiative').")
    dice_formula: str = Field(..., description="Base dice formula (e.g., '1d20', '2d6+3').")
    reason: str = Field(..., description="Brief explanation for the roll shown to the player.")
    skill: Optional[str] = Field(None, description="Specific skill if type is 'skill_check'.")
    ability: Optional[str] = Field(None, description="Specific ability score if type is 'saving_throw' or related.")
    dc: Optional[int] = Field(None, description="Difficulty Class if applicable.")

    model_config = ConfigDict(extra="forbid")


class DiceRollResult(BaseModel):
    """Core game model for dice roll results."""
    character_id: str = Field(..., description="ID of the character who rolled")
    roll_type: str = Field(..., description="Type of roll (e.g., 'attack', 'damage', 'skill_check')")
    total: int = Field(..., description="Total result of the roll")
    result_summary: str = Field(..., description="Brief summary of the roll (e.g., 'Elara: Attack Roll = 18')")
    result_message: Optional[str] = Field(None, description="Detailed message about the roll")
    skill: Optional[str] = Field(None, description="Skill name if this was a skill check")
    ability: Optional[str] = Field(None, description="Ability name if this was an ability check")
    dc: Optional[int] = Field(None, description="Difficulty class if applicable")
    reason: Optional[str] = Field(None, description="Reason for the roll")
    original_request_id: Optional[str] = Field(None, description="ID of the original request that triggered this roll")

    model_config = ConfigDict(extra="forbid")


# ===== GAME STATE MODEL =====

class GameStateModel(BaseModel):
    """Complete game state matching the active game structure."""
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
    chat_history: List[ChatMessage] = Field(default_factory=list)
    pending_player_dice_requests: List[DiceRequest] = Field(default_factory=list)
    
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
    narration_enabled: bool = Field(default=False, description="Current game session narration setting")
    tts_voice: str = Field(default="af_heart", description="Current game session TTS voice")
    
    # Private fields (excluded from serialization)
    _pending_npc_roll_results: List[DiceRollResult] = []
    _last_rag_context: Optional[str] = None
    
    @field_validator('chat_history', mode='before')
    def validate_chat_history(cls, v):
        """Convert chat history dicts to ChatMessage objects."""
        if not v:
            return []
        
        result = []
        for item in v:
            if isinstance(item, dict):
                # Add defaults for required fields if missing
                if 'id' not in item:
                    item['id'] = f"msg_{uuid4()}"
                if 'timestamp' not in item:
                    item['timestamp'] = datetime.now(timezone.utc).isoformat()
                result.append(ChatMessage(**item))
            else:
                result.append(item)
        return result
    
    @field_validator('pending_player_dice_requests', mode='before')
    def validate_dice_requests(cls, v):
        """Convert dice request dicts to DiceRequest objects."""
        if not v:
            return []
        
        result = []
        for item in v:
            if isinstance(item, dict):
                result.append(DiceRequest(**item))
            else:
                result.append(item)
        return result
    
    @field_validator('combat', mode='before')
    def validate_combat(cls, v):
        """Convert combat dict to CombatStateModel and handle monster_stats."""
        if isinstance(v, dict) and 'monster_stats' in v:
            # Convert monster_stats dicts to MonsterBaseStats objects
            monster_stats = {}
            for monster_id, stats in v.get('monster_stats', {}).items():
                if isinstance(stats, dict):
                    # Add defaults for missing fields
                    if 'name' not in stats:
                        stats['name'] = monster_id
                    if 'initial_hp' not in stats:
                        stats['initial_hp'] = 1
                    if 'ac' not in stats:
                        stats['ac'] = 10
                    monster_stats[monster_id] = MonsterBaseStats(**stats)
                else:
                    monster_stats[monster_id] = stats
            v['monster_stats'] = monster_stats
        return v
    
    model_config = ConfigDict(extra="forbid")


# ===== COMBAT MODELS =====

class InitialCombatantData(BaseModel):
    """Core game model for initial combatant data when starting combat."""
    id: str = Field(..., description="Unique identifier for the combatant")
    name: str = Field(..., description="Display name of the combatant")
    hp: int = Field(..., description="Starting hit points")
    ac: int = Field(..., description="Armor class")
    stats: Optional[Dict[str, int]] = Field(None, description="Ability scores (e.g., {'DEX': 14, 'STR': 12})")
    abilities: Optional[List[str]] = Field(None, description="Special abilities or features")
    attacks: Optional[List[Dict]] = Field(None, description="Available attacks and their properties")
    icon_path: Optional[str] = Field(None, description="Path to character portrait/icon")

    model_config = ConfigDict(extra="forbid")


# ===== GAME STATE UPDATE MODELS =====

class LocationUpdate(BaseModel):
    """Core game model for location updates."""
    name: str = Field(..., description="The new name of the current location.")
    description: str = Field(..., description="The updated description of the current location.")

    model_config = ConfigDict(extra="forbid")


class HPChangeUpdate(BaseModel):
    """Core game model for HP change updates."""
    type: Literal["hp_change"] = "hp_change"
    character_id: str = Field(..., description="ID of the character (player or NPC) affected.")
    value: int = Field(..., description="The amount to change HP by (negative for damage, positive for healing).")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional details like {'source': 'Goblin Scimitar'}")

    model_config = ConfigDict(extra="forbid")


class ConditionUpdate(BaseModel):
    """Core game model for condition updates."""
    type: Literal["condition_add", "condition_remove"]
    character_id: str = Field(..., description="ID of the character getting the condition update.")
    value: str = Field(..., description="The name of the condition (e.g., 'Poisoned', 'Prone').")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional details like {'duration': '1 minute'}")

    model_config = ConfigDict(extra="forbid")


class InventoryUpdate(BaseModel):
    """Core game model for inventory updates."""
    type: Literal["inventory_add", "inventory_remove"]
    character_id: str = Field(..., description="ID of the character receiving or losing the item.")
    value: Union[str, Dict] = Field(..., description="Item name (str) or an item object/dict.")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional details like {'quantity': 1}")

    model_config = ConfigDict(extra="forbid")


class GoldUpdate(BaseModel):
    """Core game model for gold updates."""
    type: Literal["gold_change"] = "gold_change"
    character_id: str = Field(..., description="ID of the character changing gold. Can be 'all' or 'party'")
    value: int = Field(..., description="Amount of gold to add (positive) or remove (negative).")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional details like {'source': 'Goblins'}")

    model_config = ConfigDict(extra="forbid")


class QuestUpdate(BaseModel):
    """Core game model for quest updates."""
    type: Literal["quest_update"] = "quest_update"
    quest_id: str = Field(..., description="The ID of the quest being updated (must exist in game state).")
    status: Optional[Literal["active", "completed", "failed"]] = Field(None, description="Optional: The new status of the quest.")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional: A dictionary of details to add or update for the quest.")

    model_config = ConfigDict(extra="forbid")


class CombatStartUpdate(BaseModel):
    """Core game model for combat start updates."""
    type: Literal["combat_start"] = "combat_start"
    combatants: List[InitialCombatantData] = Field(..., description="List of NPC/monster combatants with basic stats. Players added automatically.")
    details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="forbid")


class CombatEndUpdate(BaseModel):
    """Core game model for combat end updates."""
    type: Literal["combat_end"] = "combat_end"
    details: Optional[Dict[str, Any]] = Field(None, description="Optional reason for combat ending.")

    model_config = ConfigDict(extra="forbid")


class CombatantRemoveUpdate(BaseModel):
    """Core game model for combatant removal updates."""
    type: Literal["combatant_remove"] = "combatant_remove"
    character_id: str = Field(..., description="ID of the combatant (player or NPC) to remove from combat.")
    details: Optional[Dict[str, Any]] = Field(None, description="Optional details like {'reason': 'Fled the scene'}")

    model_config = ConfigDict(extra="forbid")


# Union type for all game state updates
GameStateUpdate = Union[
    HPChangeUpdate,
    ConditionUpdate,
    InventoryUpdate,
    GoldUpdate,
    CombatStartUpdate,
    CombatEndUpdate,
    CombatantRemoveUpdate,
    QuestUpdate
]


# ===== GAME EVENTS =====

class BaseGameEvent(BaseModelWithDatetimeSerializer):
    """Base class for all game events"""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_number: int = Field(default_factory=get_next_sequence_number)
    event_type: str
    correlation_id: Optional[str] = None
    
    model_config = ConfigDict()


# Narrative Events
class NarrativeAddedEvent(BaseGameEvent):
    event_type: Literal["narrative_added"] = "narrative_added"
    role: str  # "assistant", "user", "system"
    content: str
    gm_thought: Optional[str] = None
    audio_path: Optional[str] = None
    message_id: Optional[str] = None


class MessageSupersededEvent(BaseGameEvent):
    event_type: Literal["message_superseded"] = "message_superseded"
    message_id: str
    reason: str = "retry"


# Combat Events
class CombatStartedEvent(BaseGameEvent):
    event_type: Literal["combat_started"] = "combat_started"
    combatants: List[CombatantModel]  # Typed combatant models for type safety
    round_number: int = 1


class CombatEndedEvent(BaseGameEvent):
    event_type: Literal["combat_ended"] = "combat_ended"
    reason: str  # "victory", "retreat", "narrative"
    outcome_description: Optional[str] = None


class TurnAdvancedEvent(BaseGameEvent):
    event_type: Literal["turn_advanced"] = "turn_advanced"
    new_combatant_id: str
    new_combatant_name: str
    round_number: int
    is_new_round: bool = False
    is_player_controlled: bool = False


# CombatantModel State Events
class CombatantHpChangedEvent(BaseGameEvent):
    event_type: Literal["combatant_hp_changed"] = "combatant_hp_changed"
    combatant_id: str
    combatant_name: str
    old_hp: int
    new_hp: int
    max_hp: int
    change_amount: int
    is_player_controlled: bool = False
    source: Optional[str] = None


class CombatantStatusChangedEvent(BaseGameEvent):
    event_type: Literal["combatant_status_changed"] = "combatant_status_changed"
    combatant_id: str
    combatant_name: str
    new_conditions: List[str]
    added_conditions: List[str] = Field(default_factory=list)
    removed_conditions: List[str] = Field(default_factory=list)
    is_defeated: bool = False


class CombatantAddedEvent(BaseGameEvent):
    event_type: Literal["combatant_added"] = "combatant_added"
    combatant_id: str
    combatant_name: str
    hp: int
    max_hp: int
    ac: int
    is_player_controlled: bool = False
    position_in_order: Optional[int] = None


class CombatantRemovedEvent(BaseGameEvent):
    event_type: Literal["combatant_removed"] = "combatant_removed"
    combatant_id: str
    combatant_name: str
    reason: str  # "defeated", "fled", "narrative"


# Initiative Events
class CombatantInitiativeSetEvent(BaseGameEvent):
    event_type: Literal["combatant_initiative_set"] = "combatant_initiative_set"
    combatant_id: str
    combatant_name: str
    initiative_value: int
    roll_details: Optional[str] = None


class InitiativeOrderDeterminedEvent(BaseGameEvent):
    event_type: Literal["initiative_order_determined"] = "initiative_order_determined"
    ordered_combatants: List[CombatantModel]


# Dice Roll Events
class PlayerDiceRequestAddedEvent(BaseGameEvent):
    event_type: Literal["player_dice_request_added"] = "player_dice_request_added"
    request_id: str
    character_id: str
    character_name: str
    roll_type: str  # "attack", "damage", "saving_throw", etc.
    dice_formula: str
    purpose: str
    dc: Optional[int] = None
    skill: Optional[str] = None
    ability: Optional[str] = None


class PlayerDiceRequestsClearedEvent(BaseGameEvent):
    event_type: Literal["player_dice_requests_cleared"] = "player_dice_requests_cleared"
    cleared_request_ids: List[str]


class NpcDiceRollProcessedEvent(BaseGameEvent):
    event_type: Literal["npc_dice_roll_processed"] = "npc_dice_roll_processed"
    character_id: str
    character_name: str
    roll_type: str
    dice_formula: str
    total: int
    details: str
    success: Optional[bool] = None
    purpose: str


# Game State Events
class LocationChangedEvent(BaseGameEvent):
    event_type: Literal["location_changed"] = "location_changed"
    new_location_name: str
    new_location_description: str
    old_location_name: Optional[str] = None


class PartyMemberUpdatedEvent(BaseGameEvent):
    event_type: Literal["party_member_updated"] = "party_member_updated"
    character_id: str
    character_name: str
    changes: Dict[str, Any]


# System Events
class BackendProcessingEvent(BaseGameEvent):
    event_type: Literal["backend_processing"] = "backend_processing"
    is_processing: bool
    needs_backend_trigger: bool = False
    trigger_reason: Optional[str] = None


class GameErrorEvent(BaseGameEvent):
    event_type: Literal["game_error"] = "game_error"
    error_message: str
    error_type: str  # "ai_service_error", "invalid_reference", etc.
    severity: Literal["warning", "error", "critical"] = "error"
    recoverable: bool = True
    context: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None


class GameStateSnapshotEvent(BaseGameEvent):
    """Event emitted to provide full game state snapshot for reconnection/sync."""
    event_type: Literal["game_state_snapshot"] = "game_state_snapshot"
    
    # Core game state
    campaign_id: Optional[str] = None
    session_id: Optional[str] = None
    location: LocationModel  # Typed location model
    
    # Party and characters - typed models for better type safety
    party_members: List[Union[CharacterInstanceModel, CombinedCharacterModel]]  # Character instances or combined models
    
    # Quests - typed models
    active_quests: List[QuestModel] = Field(default_factory=list)
    
    # Combat state (if active) - typed model
    combat_state: Optional[CombatStateModel] = None
    
    # Pending requests - typed models  
    pending_dice_requests: List[DiceRequest] = Field(default_factory=list)
    
    # Chat history - typed models
    chat_history: List[ChatMessage] = Field(default_factory=list)
    
    # Reason for snapshot
    reason: str = "reconnection"  # "initial_load", "reconnection", "state_recovery"


# Quest and Story Events
class QuestUpdatedEvent(BaseGameEvent):
    """Event emitted when a quest status changes."""
    event_type: Literal["quest_updated"] = "quest_updated"
    
    quest_id: str
    quest_title: str
    new_status: str  # "active", "completed", "failed"
    old_status: Optional[str] = None
    description_update: Optional[str] = None


class ItemAddedEvent(BaseGameEvent):
    """Event emitted when item is added to inventory."""
    event_type: Literal["item_added"] = "item_added"
    
    character_id: str
    character_name: str
    item_name: str
    quantity: int = 1
    item_description: Optional[str] = None


# ===== REPOSITORY METADATA MODELS =====
# These are lightweight models for listing campaigns without loading full details

class CampaignTemplateMetadata(BaseModel):
    """Lightweight metadata for campaign templates stored in index file."""
    id: str
    name: str
    description: str
    created_date: datetime
    last_modified: Optional[datetime]
    starting_level: int
    difficulty: str
    folder: str
    thumbnail: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(extra="forbid")
