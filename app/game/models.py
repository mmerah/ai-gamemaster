from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal, Union

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
    languages: List[str] = ["Common"]
    # Add fields for racial traits, class features, feats, personality, etc. later

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

# Overall Game State
class GameState(BaseModel):
    party: Dict[str, CharacterInstance] = Field(default_factory=dict)
    current_location: dict = {"name": "Unknown", "description": ""}
    chat_history: List[Dict] = []
    pending_player_dice_requests: List[Dict] = []
    combat: CombatState = Field(default_factory=CombatState)
    # Add more global state: game time, quest logs etc. later
    # Internal state not directly part of the model but managed alongside it
    _pending_npc_roll_results: List[Dict] = []
