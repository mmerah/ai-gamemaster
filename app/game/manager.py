import json
import logging
import random
from typing import List, Dict, Optional, Any, Tuple

from flask import current_app
from .models import GameState, CharacterInstance, CharacterSheet, CombatState, Combatant, Item, AbilityScores, KnownNPC, Proficiencies, Quest
from . import initial_data, utils
from app.ai_services.schemas import AIResponse, LocationUpdate
from .response_processor import ResponseProcessor

logger = logging.getLogger(__name__)

# Helper to load initial party data into CharacterInstance
def load_initial_party() -> Dict[str, CharacterInstance]:
    """Loads initial party data into CharacterInstance objects."""
    party_instances = {}
    for char_data in initial_data.PARTY:
        try:
            sheet = CharacterSheet(
                id=char_data["id"], name=char_data["name"], race=char_data["race"],
                char_class=char_data["char_class"], level=char_data["level"],
                icon=char_data.get("icon"),
                base_stats=AbilityScores(**char_data.get("stats", {})),
                proficiencies=Proficiencies(**char_data.get("proficiencies", {}))
            )
            con_mod = utils.get_ability_modifier(sheet.base_stats.CON)
            dex_mod = utils.get_ability_modifier(sheet.base_stats.DEX)
            # Simplified HP calculation for PoC (e.g., average of d8 + CON per level)
            hit_die_avg = 5 
            max_hp = max(1, (hit_die_avg + con_mod) * sheet.level)
            ac = 10 + dex_mod

            instance_data = sheet.model_dump()
            instance_data.update({
                "current_hp": max_hp, "max_hp": max_hp, "armor_class": ac,
                "temporary_hp": 0, "conditions": [], "inventory": [], "gold": 0,
                "spell_slots": None, "initiative": None
            })
            char_instance = CharacterInstance(**instance_data)
            party_instances[char_instance.id] = char_instance
        except Exception as e:
            logger.error(f"Failed to load character {char_data.get('name', 'Unknown')}: {e}", exc_info=True)
    if not party_instances: logger.error("CRITICAL: Failed to load ANY character instances.")
    return party_instances

class GameManager:
    """Manages the state and core logic of a single game session."""

    def __init__(self):
        logger.info("Initializing GameManager...")
        self._game_state: GameState = GameState()
        self._is_ai_processing: bool = False
        self._response_processor = ResponseProcessor(self)
        self._initialize_state()
        logger.info("GameManager initialized.")

    def is_ai_processing(self) -> bool:
        return self._is_ai_processing

    def set_ai_processing(self, status: bool):
        self._is_ai_processing = status
        logger.debug(f"AI Processing status set to: {status}")

    def _initialize_state(self):
        """Sets up the initial game state from predefined data."""
        logger.debug("Setting initial game state values.")
        self._game_state.party = load_initial_party()
        self._game_state.current_location = {"name": "Goblin Cave Entrance", "description": "The mouth of a dark cave."}
        self._game_state.campaign_goal = initial_data.INITIAL_CAMPAIGN_GOAL
        self._game_state.known_npcs = {k: KnownNPC(**v) for k, v in initial_data.INITIAL_KNOWN_NPCS.items()}
        self._game_state.active_quests = {k: Quest(**v) for k, v in initial_data.INITIAL_ACTIVE_QUESTS.items()}
        self._game_state.world_lore = initial_data.INITIAL_WORLD_LORE
        self._game_state.event_summary = initial_data.INITIAL_EVENT_SUMMARY

        if not self._game_state.chat_history:
            self.add_chat_message(
                "assistant", initial_data.INITIAL_NARRATIVE,
                gm_thought="Game start. Setting initial scene. Goblins present but unaware."
            )
            self._game_state.current_location = {
                "name": "Goblin Cave Chamber",
                "description": "Dimly lit by torches, a campfire flickers near two goblins."
            }

    def get_character_instance(self, char_id: str) -> Optional[CharacterInstance]:
        return self._game_state.party.get(char_id)

    def find_combatant_id_by_name_or_id(self, identifier: str) -> Optional[str]:
        """Tries to find a combatant's ID by direct ID match, then by name match."""
        if not identifier: return None
        if identifier in self._game_state.party: return identifier
        if self._game_state.combat.is_active:
            if identifier in self._game_state.combat.monster_stats: return identifier
            identifier_lower = identifier.lower()
            for combatant in self._game_state.combat.combatants:
                if combatant.name.lower() == identifier_lower:
                    logger.debug(f"Found combatant ID '{combatant.id}' by name '{identifier}'.")
                    return combatant.id
        logger.warning(f"Could not find character or active combatant for identifier '{identifier}'.")
        return None

    def get_combatant_name(self, combatant_id: str) -> str:
        """Gets the display name of a player or tracked monster."""
        player = self.get_character_instance(combatant_id)
        if player: return player.name
        if self._game_state.combat.is_active and combatant_id in self._game_state.combat.monster_stats:
            return self._game_state.combat.monster_stats[combatant_id].get("name", combatant_id)
        # Fallback to ID
        return combatant_id

    def perform_roll(self, character_id: str, roll_type: str, dice_formula: str,
                     skill: Optional[str] = None, ability: Optional[str] = None,
                     dc: Optional[int] = None, reason: str = "") -> Dict[str, Any]:
        """Performs a dice roll, calculates modifier, and determines success."""
        actual_char_id = self.find_combatant_id_by_name_or_id(character_id)
        if not actual_char_id:
            error_msg = f"Cannot roll: Unknown character/combatant '{character_id}'."
            logger.error(error_msg)
            return {"error": error_msg}

        char_name = self.get_combatant_name(actual_char_id)
        char_instance = self.get_character_instance(actual_char_id)
        char_modifier = 0

        if char_instance:
            char_data_for_mod = {
                "stats": char_instance.base_stats.model_dump(),
                "proficiencies": char_instance.proficiencies.model_dump(),
                "proficiency_bonus": utils.get_proficiency_bonus(char_instance.level)
            }
            char_modifier = utils.calculate_modifier(char_data_for_mod, roll_type, skill, ability)
        elif self._game_state.combat.is_active and actual_char_id in self._game_state.combat.monster_stats:
            npc_stats_data = self._game_state.combat.monster_stats[actual_char_id]
            # Basic NPC modifier calculation (can be expanded)
            temp_npc_data_for_mod = {
                "stats": npc_stats_data.get("stats", {"DEX": 10}),
                "proficiencies": {},
                "proficiency_bonus": npc_stats_data.get("proficiency_bonus", 2)
            }
            char_modifier = utils.calculate_modifier(temp_npc_data_for_mod, roll_type, skill, ability)
        else:
            logger.warning(f"perform_roll for non-player, non-tracked-NPC '{actual_char_id}'. Assuming 0 modifier.")

        base_total, individual_rolls, _, formula_desc = utils.roll_dice_formula(dice_formula)
        if formula_desc.startswith("Invalid"):
            return {"error": f"Invalid dice formula '{dice_formula}' for {char_name}."}

        final_result = base_total + char_modifier
        success = final_result >= dc if dc is not None else None

        # Detailed message for logs/UI
        mod_str = f"{char_modifier:+}"
        roll_details = f"[{','.join(map(str, individual_rolls))}] {mod_str}"
        type_desc = utils.format_roll_type_description(roll_type, skill, ability)
        detailed_msg = f"{char_name} rolls {type_desc}: {formula_desc} ({mod_str}) -> {roll_details} = **{final_result}**."
        if dc is not None: detailed_msg += f" (DC {dc})"
        if success is not None: detailed_msg += " Success!" if success else " Failure."

        # Simplified summary for AI history
        summary_msg = f"{char_name} rolls {type_desc}: Result **{final_result}**."
        if dc is not None: summary_msg += f" (DC {dc})"
        if success is not None: summary_msg += " Success!" if success else " Failure."
        
        logger.info(f"Roll: {detailed_msg} (Reason: {reason})")
        return {
            "request_id": f"{roll_type}_{actual_char_id}_{random.randint(1000,9999)}",
            "character_id": actual_char_id, "character_name": char_name,
            "roll_type": roll_type, "dice_formula": dice_formula,
            "character_modifier": char_modifier, "total_result": final_result,
            "dc": dc, "success": success, "reason": reason,
            "result_message": detailed_msg.strip(), "result_summary": summary_msg.strip()
        }

    def get_current_state_model(self) -> GameState:
        return self._game_state

    def _format_chat_history_for_frontend(self, chat_history: List[Dict]) -> List[Dict]:
        frontend_history = []
        for msg in chat_history:
            role = msg.get("role")
            content = msg.get("content", "")
            detailed_content = msg.get("detailed_content")
            gm_thought = msg.get("gm_thought")
            is_dice_result = msg.get("is_dice_result", False)
            sender = "Unknown"
            message_to_display = detailed_content or content

            if role == "assistant":
                sender = "GM"
                # If detailed_content wasn't pre-populated from narrative, try to parse from full JSON
                if not detailed_content and msg.get("ai_response_json"):
                    try:
                        parsed_response = json.loads(msg["ai_response_json"])
                        message_to_display = parsed_response.get("narrative", content)
                    except json.JSONDecodeError:
                        logger.warning("Frontend: Could not parse AI response JSON in history for display.")
            elif role == "user":
                sender = "System" if is_dice_result else "Player"
            elif role == "system":
                sender = "System"
            
            entry = {"sender": sender, "message": str(message_to_display)} # Ensure string
            if gm_thought: entry["gm_thought"] = gm_thought
            frontend_history.append(entry)
        return frontend_history

    def _format_party_for_frontend(self, party_instances: Dict[str, CharacterInstance]) -> List[Dict]:
        return [
            {
                "id": pc.id,
                "name": pc.name,
                "race": pc.race,
                "char_class": pc.char_class,
                "level": pc.level,
                "hp": pc.current_hp,
                "max_hp": pc.max_hp,
                "ac": pc.armor_class,
                "conditions": pc.conditions,
                "icon": pc.icon,
                "stats": pc.base_stats.model_dump(),
                "proficiencies": pc.proficiencies.model_dump(),
                "proficiency_bonus": utils.get_proficiency_bonus(pc.level)
            } for pc in party_instances.values()
        ]

    def _format_combat_info_for_frontend(self, combat_state: CombatState) -> Optional[Dict]:
        if not combat_state.is_active or not combat_state.combatants:
            return None
        
        current_combatant_id, current_combatant_name = "Error", "Error"
        if 0 <= combat_state.current_turn_index < len(combat_state.combatants):
            current_combatant_id = combat_state.combatants[combat_state.current_turn_index].id
            current_combatant_name = self.get_combatant_name(current_combatant_id)
        else:
            logger.error(f"Invalid current_turn_index ({combat_state.current_turn_index}) for combatants.")

        return {
            "is_active": True,
            "round": combat_state.round_number,
            "turn_order": [c.model_dump() for c in combat_state.combatants],
            "current_turn": current_combatant_name,
            "current_turn_id": current_combatant_id,
            "monster_status": combat_state.monster_stats
        }

    def get_state_for_frontend(self) -> Dict:
        """Prepares a dictionary of the game state suitable for the frontend."""
        state = self._game_state
        return {
            "party": self._format_party_for_frontend(state.party),
            "location": state.current_location.get("name", "Unknown"),
            "location_description": state.current_location.get("description", ""),
            "chat_history": self._format_chat_history_for_frontend(state.chat_history),
            "dice_requests": state.pending_player_dice_requests,
            "combat_info": self._format_combat_info_for_frontend(state.combat)
        }

    def add_chat_message(self, role: str, content: str, gm_thought: Optional[str] = None,
                         is_dice_result: bool = False, detailed_content: Optional[str] = None,
                         ai_response_json: Optional[str] = None):
        """Adds a message to the chat history, managing truncation."""
        if role not in ["user", "assistant", "system"]:
            logger.warning(f"Invalid role '{role}' for chat message: {content[:100]}")
            return

        # Base content is always the primary string
        message = {"role": role, "content": content}
        if detailed_content: message["detailed_content"] = detailed_content
        if gm_thought: message["gm_thought"] = gm_thought
        if is_dice_result: message["is_dice_result"] = True
        if ai_response_json and role == "assistant":
            message["ai_response_json"] = ai_response_json
            # If detailed_content wasn't provided, try to extract narrative for it
            if not detailed_content:
                try:
                    parsed = json.loads(ai_response_json)
                    message["detailed_content"] = parsed.get("narrative", content)
                    # Also extract reasoning if not already provided as gm_thought
                    if not gm_thought and parsed.get("reasoning"):
                        message["gm_thought"] = parsed.get("reasoning")
                except json.JSONDecodeError:
                    logger.warning("Could not parse AI JSON to extract narrative/thought for history.")


        self._game_state.chat_history.append(message)
        # Simple truncation to prevent unbounded growth
        MAX_HISTORY_MESSAGES = 1000
        if len(self._game_state.chat_history) > MAX_HISTORY_MESSAGES:
            # Keep system prompt + N most recent, remove from middle
            # A more sophisticated strategy might be needed for very long games
            num_to_remove = len(self._game_state.chat_history) - MAX_HISTORY_MESSAGES
            # Find first non-system/context message to start removing after
            first_content_idx = 0
            for i, msg in enumerate(self._game_state.chat_history):
                if i > 5 or (msg["role"] != "system" and not msg["content"].startswith("CONTEXT INJECTION:")): # Heuristic
                    first_content_idx = i
                    break
            if first_content_idx + num_to_remove < len(self._game_state.chat_history):
                del self._game_state.chat_history[first_content_idx : first_content_idx + num_to_remove]
                logger.info(f"Chat history truncated to {len(self._game_state.chat_history)} messages.")

    def update_location(self, location_data: Optional[LocationUpdate]):
        if isinstance(location_data, LocationUpdate):
            old_name = self._game_state.current_location.get("name")
            self._game_state.current_location = location_data.model_dump()
            logger.info(f"Location updated from '{old_name}' to '{location_data.name}'.")
        elif location_data is not None:
            # Received data but not the expected type
            logger.warning(f"Invalid location_update data type: {type(location_data)}")

    def set_pending_player_dice_requests(self, requests: List[Dict]):
        self._game_state.pending_player_dice_requests = requests

    def clear_pending_player_dice_requests(self):
        self._game_state.pending_player_dice_requests = []
    
    def clear_pending_npc_roll_results(self):
        self._game_state._pending_npc_roll_results = []

    def _determine_initiative_order(self, roll_results: List[Dict]):
        """Updates initiatives and sorts combatants based on roll results."""
        combat = self._game_state.combat
        if not combat.is_active or not combat.combatants:
            logger.error("Cannot determine initiative: Combat not active or no combatants.")
            return

        logger.info("Determining initiative order...")
        initiative_map = {r["character_id"]: r["total_result"]
                          for r in roll_results if r.get("roll_type") == "initiative"}
        
        initiative_messages = []
        for combatant in combat.combatants:
            if combatant.id in initiative_map:
                combatant.initiative = initiative_map[combatant.id]
                roll_for_c = next((r for r in roll_results if r.get("character_id") == combatant.id and r.get("roll_type") == "initiative"), None)
                if roll_for_c: initiative_messages.append(roll_for_c.get("result_summary", f"{combatant.name} init: {combatant.initiative}"))
            else:
                # Fallback if roll missing (should be rare with forced initiative)
                logger.warning(f"Missing initiative roll for {combatant.name}. Rolling d20 fallback.")
                fallback_roll = self.perform_roll(combatant.id, 'initiative', '1d20', reason="Fallback Initiative")
                combatant.initiative = fallback_roll.get("total_result", random.randint(1,20))
                initiative_messages.append(fallback_roll.get("result_summary", f"{combatant.name} init: {combatant.initiative}") + " (Fallback)")

        combat.combatants.sort(key=lambda c: (c.initiative, utils.get_ability_modifier(self.get_character_instance(c.id).base_stats.DEX if self.get_character_instance(c.id) else (combat.monster_stats.get(c.id, {}).get("stats", {}).get("DEX", 10)))), reverse=True)
        combat.current_turn_index = 0

        order_display = [f"{c.name}: {c.initiative}" for c in combat.combatants]
        logger.info(f"Initiative order: {', '.join(order_display)}")
        combined_msg = "**Initiative Rolls:**\n" + "\n".join(initiative_messages) + \
                       "\n\n**Final Order:** " + ', '.join(order_display)
        self.add_chat_message("user", combined_msg, is_dice_result=True)


    def advance_turn(self):
        """Advances to the next turn in combat, skipping defeated/incapacitated combatants."""
        combat = self._game_state.combat
        if not combat.is_active or not combat.combatants: return

        original_index = combat.current_turn_index
        # Iterate once through all combatants + safety
        for _ in range(len(combat.combatants) + 1):
            combat.current_turn_index = (combat.current_turn_index + 1) % len(combat.combatants)
            
            # Check if a new round started
            if combat.current_turn_index == 0 and combat.current_turn_index != original_index :
                # Avoid double count if only one combatant
                combat.round_number += 1
                logger.info(f"Advanced to Combat Round {combat.round_number}")
                # TODO: Handle end-of-round/start-of-round effects here

            current_combatant = combat.combatants[combat.current_turn_index]
            is_incapacitated = False
            player = self.get_character_instance(current_combatant.id)
            if player and player.current_hp <= 0:
                is_incapacitated = True
            elif current_combatant.id in combat.monster_stats:
                monster = combat.monster_stats[current_combatant.id]
                if monster.get("hp", 1) <= 0 or "Defeated" in monster.get("conditions", []):
                    is_incapacitated = True
            
            if not is_incapacitated:
                logger.info(f"Advanced turn. Current: {current_combatant.name} (Round {combat.round_number})")
                # Found next active combatant
                return
            else:
                logger.debug(f"Skipping turn for incapacitated combatant: {current_combatant.name}")
        
        # If loop completes, all combatants might be incapacitated
        logger.warning("All combatants appear incapacitated. Auto-ending combat.")
        # Local import to avoid cycle
        from .state_processors import end_combat, CombatEndUpdate
        end_combat(self._game_state, CombatEndUpdate(type="combat_end", details={"reason": "All combatants incapacitated"}))


    def process_ai_response(self, ai_response: AIResponse) -> Tuple[List[Dict], bool]:
        """
        Processes the AI's response using the ResponseProcessor.
        Returns a tuple: (pending_player_dice_requests, needs_ai_rerun_for_next_step)
        """
        return self._response_processor.process(ai_response)

# Singleton Instance
# For a simple PoC, a global instance can work.
# For more complex apps, consider dependency injection or app context.
_game_manager_instance = None
def get_game_manager():
    """Gets the singleton GameManager instance."""
    global _game_manager_instance
    if _game_manager_instance is None:
        _game_manager_instance = GameManager()
    return _game_manager_instance
