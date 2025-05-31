from pydantic import BaseModel, Field, model_validator
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime

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

# Enhanced Combat Models for Event-Driven System
class Combatant(BaseModel):
    """Enhanced combatant model with validation and helper properties."""
    id: str
    name: str
    initiative: int
    initiative_modifier: int = Field(0, description="DEX modifier for tie-breaking")
    current_hp: int = Field(ge=0, description="Current hit points (non-negative)")
    max_hp: int = Field(gt=0, description="Maximum hit points (positive)")
    armor_class: int = Field(gt=0, description="Armor class")
    conditions: List[str] = Field(default_factory=list, description="Active conditions")
    is_player: bool = Field(..., description="Flag to distinguish player chars")  # Keep original field name
    icon_path: Optional[str] = None
    
    @property
    def is_player_controlled(self) -> bool:
        """Alias for is_player to maintain compatibility."""
        return self.is_player
    
    @model_validator(mode='after')
    def validate_hp_relationship(self) -> 'Combatant':
        """Ensure current HP doesn't exceed max HP."""
        if self.current_hp > self.max_hp:
            raise ValueError(f"current_hp ({self.current_hp}) cannot exceed max_hp ({self.max_hp})")
        return self
    
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


class CombatState(BaseModel):
    """Enhanced combat state model with helper methods."""
    is_active: bool = False
    combatants: List[Combatant] = Field(default_factory=list)
    current_turn_index: int = -1  # -1 when no initiative set
    round_number: int = 1
    monster_stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Base stats for monsters in combat"
    )
    current_turn_instruction_given: bool = Field(
        default=False,
        description="Whether NPC turn instruction was given this turn"
    )
    
    def get_current_combatant(self) -> Optional[Combatant]:
        """Get the combatant whose turn it is."""
        if (not self.is_active or 
            not self.combatants or
            not (0 <= self.current_turn_index < len(self.combatants))):
            return None
        return self.combatants[self.current_turn_index]
    
    def get_combatant_by_id(self, combatant_id: str) -> Optional[Combatant]:
        """Find a combatant by ID."""
        for combatant in self.combatants:
            if combatant.id == combatant_id:
                return combatant
        return None
    
    def get_initiative_order(self) -> List[Combatant]:
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
    # NOTE: Using List[Any] to avoid circular imports with app.ai_services.schemas
    # The @model_validator below ensures these are converted to proper Pydantic models on load
    chat_history: List[Any] = []  # Will be ChatMessage objects
    pending_player_dice_requests: List[Any] = []  # Will be DiceRequest objects
    combat: CombatState = Field(default_factory=CombatState)
    # Structured Long-Term Context
    campaign_goal: str = "No specific goal set."
    known_npcs: Dict[str, KnownNPC] = Field(default_factory=dict)
    active_quests: Dict[str, Quest] = Field(default_factory=dict)
    world_lore: List[str] = Field(default_factory=list)
    event_summary: List[str] = Field(default_factory=list)
    _pending_npc_roll_results: List[Dict] = []

    def __init__(self, **data):
        super().__init__(**data)
        # Persistent RAG context to preserve knowledge across interactions (private attribute)
        self._last_rag_context: Optional[str] = None
    
    @model_validator(mode='before')
    @classmethod
    def convert_chat_history_and_dice_requests(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert dict objects to proper model types when loading from JSON.
        
        This validator ensures type safety when loading GameState from persistence
        (e.g., JSON files) by converting raw dicts to their corresponding Pydantic models.
        This allows the rest of the codebase to work with properly typed objects.
        """
        if isinstance(data, dict):
            # Convert chat_history dicts to ChatMessage objects
            if 'chat_history' in data and isinstance(data['chat_history'], list):
                from app.ai_services.schemas import ChatMessage
                converted_messages = []
                for msg in data['chat_history']:
                    if isinstance(msg, dict):
                        # Ensure all required fields have defaults
                        if 'id' not in msg:
                            msg['id'] = f"msg_{len(converted_messages)}"
                        if 'timestamp' not in msg:
                            from datetime import datetime, timezone
                            msg['timestamp'] = datetime.now(timezone.utc).isoformat()
                        converted_messages.append(ChatMessage(**msg))
                    else:
                        converted_messages.append(msg)
                data['chat_history'] = converted_messages
            
            # Convert pending_player_dice_requests dicts to DiceRequest objects
            if 'pending_player_dice_requests' in data and isinstance(data['pending_player_dice_requests'], list):
                from app.ai_services.schemas import DiceRequest
                converted_requests = []
                for req in data['pending_player_dice_requests']:
                    if isinstance(req, dict):
                        converted_requests.append(DiceRequest(**req))
                    else:
                        converted_requests.append(req)
                data['pending_player_dice_requests'] = converted_requests
            
            # Convert monster_stats dicts to MonsterBaseStats objects
            if 'combat' in data and isinstance(data['combat'], dict):
                if 'monster_stats' in data['combat'] and isinstance(data['combat']['monster_stats'], dict):
                    from app.ai_services.schemas import MonsterBaseStats
                    converted_stats = {}
                    for monster_id, stats in data['combat']['monster_stats'].items():
                        if isinstance(stats, dict):
                            # Ensure required fields have defaults
                            if 'name' not in stats:
                                stats['name'] = monster_id
                            if 'initial_hp' not in stats:
                                stats['initial_hp'] = 1
                            if 'ac' not in stats:
                                stats['ac'] = 10
                            converted_stats[monster_id] = MonsterBaseStats(**stats)
                        else:
                            converted_stats[monster_id] = stats
                    data['combat']['monster_stats'] = converted_stats
        
        return data


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
