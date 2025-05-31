"""
Game update event models for the event-driven combat system.
These events are emitted by the backend and consumed by the frontend via SSE.
"""
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timezone
from uuid import uuid4
import threading


# Global sequence counter for event ordering
_sequence_counter = 0
_sequence_lock = threading.Lock()


def _get_next_sequence_number() -> int:
    """Get the next sequence number in a thread-safe manner."""
    global _sequence_counter
    with _sequence_lock:
        _sequence_counter += 1
        return _sequence_counter


class BaseGameUpdateEvent(BaseModel):
    """Base class for all game update events."""
    
    # Auto-generated fields
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_number: int = Field(default_factory=_get_next_sequence_number)
    
    # Event metadata
    event_type: str  # Discriminator field for event routing
    correlation_id: Optional[str] = None  # Links related events (e.g., attack->damage)
    
    model_config = ConfigDict()
    
    @field_serializer('timestamp')
    def serialize_timestamp(self, timestamp: datetime, _info) -> str:
        """Serialize datetime to ISO format string."""
        return timestamp.isoformat()


# Narrative and Chat Events
class NarrativeAddedEvent(BaseGameUpdateEvent):
    """Event emitted when narrative content is added to the game."""
    event_type: Literal["narrative_added"] = "narrative_added"
    
    role: str  # "assistant", "user", "system"
    content: str  # The narrative text
    gm_thought: Optional[str] = None  # AI's internal reasoning
    audio_path: Optional[str] = None  # Path to TTS audio file if generated
    message_id: Optional[str] = None  # ID for deduplication


class MessageSupersededEvent(BaseGameUpdateEvent):
    """Event emitted when a message is superseded by a retry."""
    event_type: Literal["message_superseded"] = "message_superseded"
    # ID of the message being superseded
    message_id: str
    # Reason for superseding
    reason: str = "retry"


# Combat State Events
class CombatStartedEvent(BaseGameUpdateEvent):
    """Event emitted when combat begins."""
    event_type: Literal["combat_started"] = "combat_started"
    
    # NOTE: Using Dict here instead of Pydantic models is intentional.
    # Events are Data Transfer Objects (DTOs) meant for SSE serialization to frontend.
    # This provides flexibility for the frontend without tight coupling to backend models.
    combatants: List[Dict[str, Any]]  # List of combatants with their initial state
    round_number: int = 1


class CombatEndedEvent(BaseGameUpdateEvent):
    """Event emitted when combat ends."""
    event_type: Literal["combat_ended"] = "combat_ended"
    
    reason: str  # "victory", "retreat", "narrative"
    outcome_description: Optional[str] = None


class TurnAdvancedEvent(BaseGameUpdateEvent):
    """Event emitted when turn advances to next combatant."""
    event_type: Literal["turn_advanced"] = "turn_advanced"
    
    new_combatant_id: str
    new_combatant_name: str
    round_number: int
    is_new_round: bool = False
    is_player_controlled: bool = False


# Combatant State Events
class CombatantHpChangedEvent(BaseGameUpdateEvent):
    """Event emitted when a combatant's HP changes."""
    event_type: Literal["combatant_hp_changed"] = "combatant_hp_changed"
    
    combatant_id: str
    combatant_name: str
    old_hp: int
    new_hp: int
    max_hp: int
    change_amount: int  # Negative for damage, positive for healing
    is_player_controlled: bool = False
    source: Optional[str] = None  # What caused the change


class CombatantStatusChangedEvent(BaseGameUpdateEvent):
    """Event emitted when a combatant's status changes."""
    event_type: Literal["combatant_status_changed"] = "combatant_status_changed"
    
    combatant_id: str
    combatant_name: str
    new_conditions: List[str]
    added_conditions: List[str] = []
    removed_conditions: List[str] = []
    is_defeated: bool = False


class CombatantAddedEvent(BaseGameUpdateEvent):
    """Event emitted when a new combatant joins combat."""
    event_type: Literal["combatant_added"] = "combatant_added"
    
    combatant_id: str
    combatant_name: str
    hp: int
    max_hp: int
    ac: int
    is_player_controlled: bool = False
    position_in_order: Optional[int] = None


class CombatantRemovedEvent(BaseGameUpdateEvent):
    """Event emitted when a combatant is removed from combat."""
    event_type: Literal["combatant_removed"] = "combatant_removed"
    
    combatant_id: str
    combatant_name: str
    reason: str  # "defeated", "fled", "narrative"


# Initiative Events
class CombatantInitiativeSetEvent(BaseGameUpdateEvent):
    """Event emitted when a combatant's initiative is set."""
    event_type: Literal["combatant_initiative_set"] = "combatant_initiative_set"
    
    combatant_id: str
    combatant_name: str
    initiative_value: int
    roll_details: Optional[str] = None


class InitiativeOrderDeterminedEvent(BaseGameUpdateEvent):
    """Event emitted when initiative order is finalized."""
    event_type: Literal["initiative_order_determined"] = "initiative_order_determined"
    
    # NOTE: Dict format maintained for frontend serialization consistency
    ordered_combatants: List[Dict[str, Any]]  # Ordered list with id, name, initiative


# Dice Roll Events
class PlayerDiceRequestAddedEvent(BaseGameUpdateEvent):
    """Event emitted when player needs to roll dice."""
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


class PlayerDiceRequestsClearedEvent(BaseGameUpdateEvent):
    """Event emitted when player dice requests are cleared."""
    event_type: Literal["player_dice_requests_cleared"] = "player_dice_requests_cleared"
    
    cleared_request_ids: List[str]


class NpcDiceRollProcessedEvent(BaseGameUpdateEvent):
    """Event emitted when an NPC dice roll is made."""
    event_type: Literal["npc_dice_roll_processed"] = "npc_dice_roll_processed"
    
    character_id: str
    character_name: str
    roll_type: str
    dice_formula: str
    total: int
    details: str  # Detailed roll breakdown
    success: Optional[bool] = None
    purpose: str


# Game State Events
class LocationChangedEvent(BaseGameUpdateEvent):
    """Event emitted when party location changes."""
    event_type: Literal["location_changed"] = "location_changed"
    
    new_location_name: str
    new_location_description: str
    old_location_name: Optional[str] = None


class PartyMemberUpdatedEvent(BaseGameUpdateEvent):
    """Event emitted when a party member's state changes."""
    event_type: Literal["party_member_updated"] = "party_member_updated"
    
    character_id: str
    character_name: str
    changes: Dict[str, Any]  # What changed (hp, conditions, inventory, etc.)


# System Events
class BackendProcessingEvent(BaseGameUpdateEvent):
    """Event emitted to indicate backend processing status."""
    event_type: Literal["backend_processing"] = "backend_processing"
    
    is_processing: bool
    needs_backend_trigger: bool = False
    trigger_reason: Optional[str] = None  # "npc_turn", "ai_continuation", etc.


class GameErrorEvent(BaseGameUpdateEvent):
    """Event emitted when an error occurs during game processing."""
    event_type: Literal["game_error"] = "game_error"
    
    error_message: str
    error_type: str  # "ai_service_error", "invalid_reference", "save_error", etc.
    severity: Literal["warning", "error", "critical"] = "error"
    recoverable: bool = True
    context: Optional[Dict[str, Any]] = None  # Additional error context
    error_code: Optional[str] = None  # Legacy field for backward compatibility
    
    @property
    def is_retryable(self) -> bool:
        """Alias for recoverable for backward compatibility."""
        return self.recoverable


class GameStateSnapshotEvent(BaseGameUpdateEvent):
    """Event emitted to provide full game state snapshot for reconnection/sync."""
    event_type: Literal["game_state_snapshot"] = "game_state_snapshot"
    
    # Core game state
    campaign_id: Optional[str] = None
    session_id: Optional[str] = None
    location: Dict[str, Any]  # Current location info
    
    # Party and characters
    party_members: List[Dict[str, Any]]  # Complete party data
    
    # Quests
    active_quests: List[Dict[str, Any]] = []
    
    # Combat state (if active)
    combat_state: Optional[Dict[str, Any]] = None
    
    # Pending requests
    pending_dice_requests: List[Dict[str, Any]] = []
    
    # Chat history
    chat_history: List[Dict[str, Any]] = []
    
    # Reason for snapshot
    reason: str = "reconnection"  # "initial_load", "reconnection", "state_recovery"
    
    @classmethod
    def from_game_state(cls, game_state) -> "GameStateSnapshotEvent":
        """Create a snapshot event from current game state."""
        from app.game.models import GameState
        
        # Extract party data
        party_data = []
        for char_id, char in game_state.party.items():
            party_data.append({
                "id": char_id,
                "name": char.name,
                "race": char.race,
                "char_class": char.char_class,
                "level": char.level,
                "current_hp": char.current_hp,
                "max_hp": char.max_hp,
                "armor_class": char.armor_class,
                "conditions": char.conditions,
                "inventory": char.inventory,
            })
        
        # Extract quest data
        quest_data = []
        for quest_id, quest in game_state.active_quests.items():
            quest_data.append({
                "id": quest_id,
                "title": quest.title,
                "description": quest.description,
                "status": quest.status,
                "details": getattr(quest, 'details', {})
            })
        
        # Extract combat state if active
        combat_data = None
        if game_state.combat.is_active:
            # Get current turn combatant ID
            current_turn_id = None
            if 0 <= game_state.combat.current_turn_index < len(game_state.combat.combatants):
                current_turn_id = game_state.combat.combatants[game_state.combat.current_turn_index].id
            
            # Build combatants list
            combatants = []
            for combatant in game_state.combat.combatants:
                combatant_data = {
                    "id": combatant.id,
                    "name": combatant.name,
                    "initiative": combatant.initiative,
                    "is_player": combatant.is_player
                }
                
                # Add HP/AC data
                if combatant.is_player:
                    char = game_state.party.get(combatant.id)
                    if char:
                        combatant_data["hp"] = char.current_hp
                        combatant_data["max_hp"] = char.max_hp
                        combatant_data["ac"] = char.armor_class
                else:
                    npc_stats = game_state.combat.monster_stats.get(combatant.id)
                    if npc_stats:
                        # Handle both dict (legacy) and MonsterBaseStats (new) formats
                        if hasattr(npc_stats, 'model_dump'):
                            # MonsterBaseStats object
                            combatant_data["hp"] = combatant.current_hp  # Use combatant's current HP
                            combatant_data["max_hp"] = npc_stats.initial_hp
                            combatant_data["ac"] = npc_stats.ac
                        else:
                            # Legacy dict format
                            combatant_data["hp"] = npc_stats.get("hp", 0)
                            combatant_data["max_hp"] = npc_stats.get("initial_hp", 0)
                            combatant_data["ac"] = npc_stats.get("ac", 10)
                    else:
                        combatant_data["hp"] = combatant.current_hp
                        combatant_data["max_hp"] = combatant.max_hp
                        combatant_data["ac"] = combatant.armor_class
                
                combatants.append(combatant_data)
            
            # Serialize monster_stats properly
            monster_stats_serialized = {}
            for monster_id, stats in game_state.combat.monster_stats.items():
                if hasattr(stats, 'model_dump'):
                    monster_stats_serialized[monster_id] = stats.model_dump()
                else:
                    monster_stats_serialized[monster_id] = stats
            
            combat_data = {
                "is_active": True,
                "round_number": game_state.combat.round_number,
                "current_turn_index": game_state.combat.current_turn_index,
                "current_turn_combatant_id": current_turn_id,
                "combatants": combatants,
                "monster_stats": monster_stats_serialized
            }
        
        # Extract chat history
        chat_data = []
        for msg in game_state.chat_history:
            # Handle both dict and ChatMessage objects
            if hasattr(msg, 'model_dump'):
                # ChatMessage object
                msg_dict = msg.model_dump()
                chat_data.append({
                    "id": msg_dict.get("id"),
                    "role": msg_dict.get("role"),
                    "content": msg_dict.get("content"),
                    "timestamp": msg_dict.get("timestamp"),
                    "gm_thought": msg_dict.get("gm_thought"),
                    "audio_path": msg_dict.get("audio_path")
                })
            else:
                # Dictionary format (legacy)
                chat_data.append({
                    "id": msg.get("id"),
                    "role": msg.get("role"),
                    "content": msg.get("content"),
                    "timestamp": msg.get("timestamp"),
                    "gm_thought": msg.get("gm_thought"),
                    "audio_path": msg.get("audio_path")
                })
        
        return cls(
            campaign_id=game_state.campaign_id,
            session_id=None,  # GameState doesn't have session_id
            location=game_state.current_location,
            party_members=party_data,
            active_quests=quest_data,
            combat_state=combat_data,
            pending_dice_requests=[req.model_dump() for req in game_state.pending_player_dice_requests],
            chat_history=chat_data
        )


# Quest and Story Events
class QuestUpdatedEvent(BaseGameUpdateEvent):
    """Event emitted when a quest status changes."""
    event_type: Literal["quest_updated"] = "quest_updated"
    
    quest_id: str
    quest_title: str
    new_status: str  # "active", "completed", "failed"
    old_status: Optional[str] = None
    description_update: Optional[str] = None


class ItemAddedEvent(BaseGameUpdateEvent):
    """Event emitted when item is added to inventory."""
    event_type: Literal["item_added"] = "item_added"
    
    character_id: str
    character_name: str
    item_name: str
    quantity: int = 1
    item_description: Optional[str] = None


# Utility function to get all event types
def get_all_event_types() -> List[type[BaseGameUpdateEvent]]:
    """Get all event class types for validation."""
    import sys
    import inspect
    
    current_module = sys.modules[__name__]
    event_types = []
    
    for name, obj in inspect.getmembers(current_module):
        if (inspect.isclass(obj) and 
            issubclass(obj, BaseGameUpdateEvent) and 
            obj is not BaseGameUpdateEvent):
            event_types.append(obj)
    
    return event_types


# Event Type Registry for dynamic class lookup
from typing import Type

_EVENT_TYPE_REGISTRY: Dict[str, Type[BaseGameUpdateEvent]] = {}


def _build_event_registry():
    """Build the event type registry."""
    for event_class in get_all_event_types():
        if hasattr(event_class, 'model_fields'):
            # For Pydantic V2 models, check the model fields
            fields = event_class.model_fields
            if 'event_type' in fields:
                # Get the default value from the field
                field_info = fields['event_type']
                default_value = field_info.default
                if default_value:
                    _EVENT_TYPE_REGISTRY[default_value] = event_class


def get_event_class_by_type(event_type: str) -> Optional[Type[BaseGameUpdateEvent]]:
    """Get event class by its event_type string."""
    if not _EVENT_TYPE_REGISTRY:
        _build_event_registry()
    return _EVENT_TYPE_REGISTRY.get(event_type)


# Build the registry on module import
_build_event_registry()