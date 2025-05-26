from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal, Union

# Base Stats & Proficiencies
class AbilityScores(BaseModel):
    STR: int = 10
    DEX: int = 10
    CON: int = 10
    INT: int = 10
    WIS: int = 10
    CHA: int = 10

class Proficiencies(BaseModel):
    armor: List[str] = []
    weapons: List[str] = []
    tools: List[str] = []
    skills: List[str] = []
    saving_throws: List[str] = []

# Inventory
class Item(BaseModel):
    id: str = Field(..., description="Unique ID for the item instance")
    name: str = Field(..., description="Display name of the item")
    description: Optional[str] = None
    quantity: int = 1
    # Add other relevant item properties: weight, type, effects etc. later

# Character Sheet (Static Definition)
class CharacterSheet(BaseModel):
    id: str = Field(..., description="Unique identifier for the character definition")
    name: str
    race: str
    char_class: str = Field(..., description="Character's primary class.")
    level: int = 1
    alignment: Optional[str] = None
    background: Optional[str] = None
    icon: Optional[str] = None

    base_stats: AbilityScores = Field(default_factory=AbilityScores)
    proficiencies: Proficiencies = Field(default_factory=Proficiencies)
    languages: List[str] = Field(default_factory=lambda: ["Common"])
    
    # New fields for template details
    subrace_name: Optional[str] = Field(None, description="Selected subrace name, if any")
    subclass_name: Optional[str] = Field(None, description="Selected subclass, archetype, or domain name, if any")
    portrait_path: Optional[str] = Field(None, description="Path to character portrait image")
    default_starting_gold: int = Field(0, description="Default starting gold for this template")
    # Note: skill_proficiencies from JS will be mapped to proficiencies.skills
    # Note: starting_equipment will be handled more dynamically, perhaps by class/background choices later

    # Add fields for racial traits, class features, feats, personality, etc. later.
    # For now, these are mostly derived from race/class/subrace/subclass selections
    # and the D&D 5e data files at runtime or during character finalization.

# Character Instance (Dynamic State in Game)
class CharacterInstance(CharacterSheet):
    """Represents a character actively participating in the game with dynamic state."""
    current_hp: int
    max_hp: int
    temporary_hp: int = 0
    armor_class: int = 10
    conditions: List[str] = []
    inventory: List[Item] = []
    gold: int = 0
    spell_slots: Optional[Dict[str, int]] = None
    initiative: Optional[int] = None
    # Need to initialize max_hp, current_hp, ac etc. based on sheet
    # This can be done post-init or when creating the instance

# Combat State
class Combatant(BaseModel):
    id: str
    name: str
    initiative: int
    # Flag to distinguish player chars
    is_player: bool = False

class CombatState(BaseModel):
    is_active: bool = False
    # Ordered by initiative
    combatants: List[Combatant] = []
    current_turn_index: int = 0
    round_number: int = 1
    # Store temporary monster data here if not using full CharacterInstance for them
    # Keyed by monster ID (e.g., "goblin_1") -> {"hp": 10, "ac": 12, "conditions": []}
    monster_stats: Dict[str, Dict] = {}
    _combat_just_started_flag: bool = False # Internal flag, not for AI/Frontend

class KnownNPC(BaseModel):
    id: str
    name: str
    # Brief description, relationship to party, status
    description: str
    last_location: Optional[str] = None

class Quest(BaseModel):
    id: str
    title: str
    description: str
    status: Literal["active", "completed", "failed"] = "active"
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary details about the quest progress added by the AI.")

# Overall Game State
class GameState(BaseModel):
    campaign_id: Optional[str] = None
    # Campaign-specific context for RAG
    # Populated from CampaignDefinition when campaign starts
    active_ruleset_id: Optional[str] = None
    active_lore_id: Optional[str] = None     
    # Set to saves/campaigns/{campaign_id}/event_log.json when campaign is active
    event_log_path: Optional[str] = None

    party: Dict[str, CharacterInstance] = Field(default_factory=dict)
    current_location: dict = {"name": "Unknown", "description": ""}
    chat_history: List[Dict] = []
    pending_player_dice_requests: List[Dict] = []
    combat: CombatState = Field(default_factory=CombatState)
    # Structured Long-Term Context
    campaign_goal: str = "No specific goal set."
    known_npcs: Dict[str, KnownNPC] = Field(default_factory=dict)
    active_quests: Dict[str, Quest] = Field(default_factory=dict)
    world_lore: List[str] = Field(default_factory=list)
    event_summary: List[str] = Field(default_factory=list)
    _pending_npc_roll_results: List[Dict] = []
