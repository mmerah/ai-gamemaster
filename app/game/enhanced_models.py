from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal, Union
from datetime import datetime

# Enhanced models for the new JSON-based system

class RacialTrait(BaseModel):
    name: str
    description: str

class ClassFeature(BaseModel):
    name: str
    description: str
    level_acquired: int

class CharacterTemplate(BaseModel):
    """Enhanced character template with full D&D 5e support"""
    # Basic Info
    id: str = Field(..., description="Unique identifier for the character template")
    name: str
    race: str
    subrace_name: Optional[str] = None
    char_class: str = Field(..., description="Character's primary class")
    subclass_name: Optional[str] = None
    level: int = 1
    background: str
    alignment: str
    
    # Ability Scores
    base_stats: Dict[str, int] = Field(default_factory=dict)
    
    # D&D 5e Details
    proficiencies: Dict[str, List[str]] = Field(default_factory=dict)
    languages: List[str] = Field(default_factory=list)
    racial_traits: List[RacialTrait] = Field(default_factory=list)
    class_features: List[ClassFeature] = Field(default_factory=list)
    spells_known: Optional[List[str]] = None
    cantrips_known: Optional[List[str]] = None
    
    # Equipment & Appearance
    starting_equipment: List[Dict[str, Any]] = Field(default_factory=list)
    starting_gold: int = 0
    portrait_path: Optional[str] = None
    
    # Background Details
    personality_traits: List[str] = Field(default_factory=list)
    ideals: List[str] = Field(default_factory=list)
    bonds: List[str] = Field(default_factory=list)
    flaws: List[str] = Field(default_factory=list)

class CampaignDefinition(BaseModel):
    """Campaign definition loaded from JSON"""
    id: str
    name: str
    description: str
    created_date: datetime
    last_played: Optional[datetime] = None
    
    # Initial Campaign Data
    starting_location: Dict[str, str]
    campaign_goal: str
    initial_npcs: Dict[str, Dict[str, Any]]
    initial_quests: Dict[str, Dict[str, Any]]
    world_lore: List[str]
    event_summary: List[str]
    opening_narrative: str
    
    # Campaign Settings
    starting_level: int = 1
    difficulty: Literal["easy", "normal", "hard"] = "normal"
    house_rules: Dict[str, Any] = Field(default_factory=dict)
    ruleset_id: str = Field("dnd5e_standard", description="ID of the ruleset to use for this campaign (e.g., 'dnd5e_standard', 'homebrew_rules_v1')")
    lore_id: str = Field("generic_fantasy", description="ID of the lore set to use for this campaign (e.g., 'generic_fantasy', 'forgotten_realms_basic')")
    
    # Selected Characters (references to global templates)
    party_character_ids: List[str] = Field(default_factory=list)

    # TTS Settings
    narration_enabled: bool = Field(True, description="Whether narration is enabled for this campaign by default")
    tts_voice: Optional[str] = Field("af_heart", description="Selected TTS voice ID for narration (e.g., Kokoro voice ID)")

class CampaignMetadata(BaseModel):
    """Lightweight campaign info for listing"""
    id: str
    name: str
    description: str
    created_date: datetime
    last_played: Optional[datetime] = None
    starting_level: int
    difficulty: str
    party_size: int
    folder: str
    thumbnail: Optional[str] = None

class CharacterTemplateMetadata(BaseModel):
    """Lightweight character template info for listing"""
    id: str
    name: str
    race: str
    char_class: str
    level: int
    description: str
    file: str
    portrait_path: Optional[str] = None

class D5eRace(BaseModel):
    """D&D 5e race definition"""
    name: str
    size: str
    speed: int
    ability_score_increase: Dict[str, int]
    traits: List[RacialTrait]
    languages: List[str]
    proficiencies: Optional[Dict[str, List[str]]] = None
    subraces: Dict[str, Any] = Field(default_factory=dict)

class D5eClass(BaseModel):
    """D&D 5e class definition"""
    name: str
    hit_die: int
    primary_ability: List[str]
    saving_throw_proficiencies: List[str]
    armor_proficiencies: List[str]
    weapon_proficiencies: List[str]
    tool_proficiencies: List[str]
    skill_choices: Dict[str, Any]
    spellcasting: Optional[Dict[str, Any]] = None
    subclasses: Dict[str, Any] = Field(default_factory=dict)
    class_features: List[Dict[str, Any]] = Field(default_factory=list)

class SaveGameMetadata(BaseModel):
    """Metadata for save games"""
    campaign_id: str
    save_date: datetime
    game_session: int
    party_level: int
    current_location: str
    auto_save: bool = True

# Enhanced game state that can be loaded from campaigns
class EnhancedGameState(BaseModel):
    """Extended game state with campaign context"""
    # Campaign Context
    campaign_id: str
    campaign_name: str
    
    # Existing game state fields (from original GameState)
    party: Dict[str, Any] = Field(default_factory=dict)
    current_location: dict = {"name": "Unknown", "description": ""}
    chat_history: List[Dict] = []
    pending_player_dice_requests: List[Dict] = []
    combat: Dict[str, Any] = Field(default_factory=dict)
    
    # Structured Long-Term Context
    campaign_goal: str = "No specific goal set."
    known_npcs: Dict[str, Any] = Field(default_factory=dict)
    active_quests: Dict[str, Any] = Field(default_factory=dict)
    world_lore: List[str] = Field(default_factory=list)
    event_summary: List[str] = Field(default_factory=list)
    _pending_npc_roll_results: List[Dict] = []
    
    # Save metadata
    last_saved: datetime
    auto_save_enabled: bool = True
