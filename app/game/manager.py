import json
import logging
import random
from typing import List, Dict, Optional, Any, Tuple

from flask import current_app
from .models import GameState, CharacterInstance, CharacterSheet, CombatState, Combatant, Item, AbilityScores, Proficiencies
from . import initial_data, utils
from app.ai_services.schemas import AIResponse, CombatEndUpdate, CombatStartUpdate, ConditionUpdate, HPChangeUpdate, LocationUpdate, DiceRequest, GameStateUpdate

logger = logging.getLogger(__name__)

# Helper to load initial party data into CharacterInstance
def load_initial_party() -> Dict[str, CharacterInstance]:
    party_instances = {}
    raw_party_data = initial_data.PARTY

    for char_data in raw_party_data:
        # 1. Prepare input data for CharacterSheet
        # Directly use the keys from initial_data
        sheet_input_data = {
            "id": char_data["id"],
            "name": char_data["name"],
            "race": char_data["race"],
            "char_class": char_data["char_class"],
            "level": char_data["level"],
            "icon": char_data.get("icon"),
            "base_stats": AbilityScores(**char_data.get("stats", {})),
            "proficiencies": Proficiencies(**char_data.get("proficiencies", {}))
        }
        try:
            # Create the CharacterSheet first
            sheet = CharacterSheet(**sheet_input_data)
        except Exception as e:
            logger.error(f"Failed validation creating CharacterSheet for {char_data.get('name', 'Unknown')}: {e}", exc_info=True)
            continue

        # 2. Calculate instance-specific fields
        prof_bonus = utils.get_proficiency_bonus(sheet.level)
        con_mod = utils.get_ability_modifier(sheet.base_stats.CON)
        dex_mod = utils.get_ability_modifier(sheet.base_stats.DEX)
        hit_die_avg = 5 # Avg of d8
        max_hp = (hit_die_avg + con_mod) * sheet.level
        max_hp = max(max_hp, 1)
        ac = 10 + dex_mod


        # 3. Create the CharacterInstance
        try:
            # Now that input `sheet` uses 'char_class', dumping it should work directly
            instance_creation_data = sheet.model_dump()
            instance_creation_data.update({
                "current_hp": max_hp,
                "max_hp": max_hp,
                "armor_class": ac,
                "temporary_hp": 0,
                "conditions": [],
                "inventory": [],
                "gold": 0,
                "spell_slots": None,
                "initiative": None
            })
            # Create instance using the dict
            char_instance = CharacterInstance(**instance_creation_data)
            party_instances[char_instance.id] = char_instance
            logger.info(f"Loaded character instance: {char_instance.name} (HP: {char_instance.current_hp}/{char_instance.max_hp}, AC: {char_instance.armor_class})")

        except Exception as e:
            import json
            logger.error(f"Failed validation creating CharacterInstance for {char_data.get('name', 'Unknown')}: {e}", exc_info=True)
            try:
                full_data_str = json.dumps(instance_creation_data, indent=2)
                logger.debug(f"Full data used for CharacterInstance creation:\n{full_data_str}")
            except TypeError:
                logger.debug(f"Data used for CharacterInstance creation (raw): {instance_creation_data}")
            continue

    if not party_instances:
        logger.error("Failed to load ANY character instances. Party will be empty.")

    return party_instances

class GameManager:
    """Manages the state and logic of a single game session using Pydantic models."""

    def __init__(self):
        logger.info("Initializing GameManager with Pydantic models...")
        self._game_state: GameState = GameState()
        self._is_ai_processing: bool = False
        self._initialize_state()
        logger.info("GameManager initialized.")

    def is_ai_processing(self) -> bool:
        return self._is_ai_processing

    def set_ai_processing(self, status: bool):
        self._is_ai_processing = status
        logger.debug(f"AI Processing status set to: {status}")

    def _initialize_state(self):
        """Sets up the initial game state."""
        logger.debug("Setting initial game state values.")
        # Load party character instances
        self._game_state.party = load_initial_party()

        initial_location_dict = {"name": "Goblin Cave Chamber", "description": "Dimly lit cave chamber with a campfire."}
        self._game_state.current_location = initial_location_dict

        if not self._game_state.chat_history:
            logger.info("History empty, setting initial narrative.")
            # Add initial GM message with reasoning
            initial_reasoning = "Game start. Setting the initial scene in the goblin cave entrance based on INITIAL_NARRATIVE. Goblins are present but unaware. Prompting player for action."
            self.add_chat_message("assistant", initial_data.INITIAL_NARRATIVE, gm_thought=initial_reasoning)
            # Update location to match narrative
            self._game_state.current_location = {"name": "Goblin Cave Chamber", "description": "Dimly lit by torches, a campfire flickers in the center near two goblins."}
        else:
            logger.info("History not empty, skipping initial narrative setup.")

    def get_character_instance(self, char_id: str) -> Optional[CharacterInstance]:
        """Gets a player character instance by ID."""
        return self._game_state.party.get(char_id)
    
    # Helper to find combatant ID by name or ID
    def find_combatant_id_by_name_or_id(self, identifier: str) -> Optional[str]:
        """Tries to find a combatant's ID, first by direct ID match, then by name match."""
        if not identifier: return None

        # 1. Check Player Party by ID
        if identifier in self._game_state.party:
            return identifier

        # 2. Check Combat Monster Stats by ID
        if self._game_state.combat.is_active and identifier in self._game_state.combat.monster_stats:
            return identifier

        # 3. Check Combatants List by Name (Case-insensitive fallback)
        if self._game_state.combat.is_active:
            identifier_lower = identifier.lower()
            for combatant in self._game_state.combat.combatants:
                if combatant.name.lower() == identifier_lower:
                    logger.debug(f"Found combatant ID '{combatant.id}' by matching name '{identifier}'.")
                    return combatant.id

        logger.warning(f"Could not find any character or active combatant matching identifier '{identifier}'.")
        return None
    
    def get_combatant_name(self, combatant_id: str) -> str:
        """Gets the name of a player or tracked monster."""
        player = self.get_character_instance(combatant_id)
        if player:
            return player.name
        # Use monster_stats for name lookup
        if self._game_state.combat.is_active and combatant_id in self._game_state.combat.monster_stats:
            monster = self._game_state.combat.monster_stats[combatant_id]
            return monster.get("name", combatant_id)
        return combatant_id
    
    def perform_roll(self, character_id, roll_type, dice_formula, skill=None, ability=None, dc=None, reason="") -> Dict[str, Any]:
        """
        Performs a dice roll for a character OR NPC, calculates modifier and success.
        Returns a dictionary with roll details including a simplified summary.
        """
        actual_char_id = self.find_combatant_id_by_name_or_id(character_id)
        if not actual_char_id:
            # If lookup failed completely, return error
            error_msg = f"Cannot perform roll: Unknown character/combatant identifier '{character_id}'."
            logger.error(error_msg)
            return {"error": error_msg}

        character = self.get_character_instance(actual_char_id)
        char_name = self.get_combatant_name(actual_char_id)
        char_modifier = 0
        is_npc = False

        if character:
             char_dict_for_mod = {
                "stats": character.base_stats.model_dump(),
                "proficiencies": character.proficiencies.model_dump(),
                "proficiency_bonus": utils.get_proficiency_bonus(character.level)
             }
             char_modifier = utils.calculate_modifier(char_dict_for_mod, roll_type, skill, ability)
        else:
            # Check if it's a tracked monster in combat (using resolved ID)
            if self._game_state.combat.is_active and actual_char_id in self._game_state.combat.monster_stats:
                is_npc = True
                # TODO: Implement better NPC modifier calculation (requires monster stat blocks)
                # For now, assume AI includes mods in formula or DC, or use 0 base mod.
                # Let's try to get DEX mod for initiative/attacks if possible
                npc_stats = self._game_state.combat.monster_stats[actual_char_id]
                temp_npc_data_for_mod = {
                    "stats": npc_stats.get("stats", {"DEX": 10}),
                    "proficiencies": {},
                    "proficiency_bonus": npc_stats.get("proficiency_bonus", 0)
                }
                char_modifier = utils.calculate_modifier(temp_npc_data_for_mod, roll_type, skill, ability)
                logger.debug(f"Calculated modifier {char_modifier} for tracked NPC '{actual_char_id}' ({char_name}).")
            else:
                # This case should be less likely now with find_combatant_id_by_name_or_id
                logger.warning(f"perform_roll called for non-player, non-tracked-combatant ID '{actual_char_id}'. Assuming 0 modifier.")
                char_modifier = 0

        # Roll dice formula (utils.roll_dice_formula remains mostly the same)
        base_total, individual_rolls, formula_mod, formula_desc = utils.roll_dice_formula(dice_formula)
        if formula_desc.startswith("Invalid"):
            return {"error": f"Invalid dice formula '{dice_formula}' for {char_name}."}

        final_result = base_total + char_modifier
        success = None
        if dc is not None:
            try:
                success = final_result >= int(dc)
            except (ValueError, TypeError):
                success = None

        # Format result message (Detailed)
        mod_string = f"{char_modifier:+}"
        roll_details_str = f"[{','.join(map(str, individual_rolls))}] {mod_string}"
        type_desc = roll_type.replace('_', ' ').title()
        if roll_type == 'skill_check' and skill: type_desc = f"{skill.title()} Check"
        elif roll_type == 'saving_throw' and ability: type_desc = f"{ability.upper()} Save"
        elif roll_type == 'initiative': type_desc = "Initiative"

        result_message_detailed = f"{char_name} rolls {type_desc}: {formula_desc} ({mod_string}) -> {roll_details_str} = **{final_result}**."
        if dc is not None: result_message_detailed += f" (DC {dc})"
        if success is not None: result_message_detailed += " Success!" if success else " Failure."

        # Simplified result summary for AI history
        result_summary = f"{char_name} rolls {type_desc}: Result **{final_result}**."
        if dc is not None: result_summary += f" (DC {dc})"
        if success is not None: result_summary += " Success!" if success else " Failure."

        logger.info(f"Roll performed: {result_message_detailed} (Reason: {reason})")

        return {
            "request_id": f"{roll_type}_{actual_char_id}_{random.randint(1000,9999)}",
            "character_id": actual_char_id,
            "character_name": char_name,
            "roll_type": roll_type,
            "dice_formula": dice_formula,
            "character_modifier": char_modifier,
            "total_result": final_result,
            "dc": dc,
            "success": success,
            "reason": reason,
            "result_message": result_message_detailed.strip(),
            "result_summary": result_summary.strip()
        }

    def get_current_state_model(self) -> GameState:
        """Returns the current GameState Pydantic model."""
        return self._game_state

    def get_state_for_frontend(self):
        """Prepares the state data needed by the frontend from the GameState model."""
        state = self._game_state
        frontend_history = []
        for msg in state.chat_history:
            sender = "Unknown"
            role = msg.get("role")
            content = msg.get("content", "")
            detailed_content = msg.get("detailed_content")
            gm_thought = msg.get("gm_thought")
            is_dice_result = msg.get("is_dice_result", False)
            message_content = ""

            if role == "assistant":
                sender = "GM"
                ai_response_json = msg.get("ai_response_json")
                if ai_response_json:
                    try:
                        parsed_response = json.loads(ai_response_json)
                        # Prioritize detailed_content if it exists, else parsed narrative, else fallback string
                        message_content = detailed_content or parsed_response.get("narrative", "") or "(Empty Narrative)"
                    except json.JSONDecodeError:
                        logger.warning("Frontend: Could not parse AI response JSON in history.")
                        # Fallback: detailed_content or original content or fallback string
                        message_content = detailed_content or content or "(Unparseable AI Response)"
                else:
                    # Fallback if ai_response_json wasn't stored
                    message_content = detailed_content or content or "(Missing AI Response)"
            elif role == "user":
                sender = "System" if is_dice_result else "Player"
                # Prioritize detailed_content, else content, else fallback
                message_content = detailed_content or content or "(Empty User/System Message)"
            elif role == "system":
                sender = "System"
                # Prioritize detailed_content, else content, else fallback
                message_content = detailed_content or content or "(Empty System Message)"
            else:
                # Should not happen with role validation in add_chat_message
                sender = "Unknown"
                message_content = detailed_content or content or "(Unknown Message Role)"

            # Ensure message_content is definitely a string before sending
            if not isinstance(message_content, str):
                logger.warning(f"Message content was not a string ({type(message_content)}), forcing empty string.")
                message_content = ""

            entry = {"sender": sender, "message": message_content}
            if gm_thought: entry["gm_thought"] = gm_thought

            frontend_history.append(entry)

        # Prepare party data for frontend (simplified view)
        party_frontend = [
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
            } for pc in state.party.values()
        ]

        # Prepare combat info if active
        combat_info = None
        if state.combat.is_active and state.combat.combatants:
            # Ensure index is valid before accessing
            if 0 <= state.combat.current_turn_index < len(state.combat.combatants):
                current_combatant_id = state.combat.combatants[state.combat.current_turn_index].id
                current_combatant_name = self.get_combatant_name(current_combatant_id)
                combat_info = {
                    "is_active": True,
                    "round": state.combat.round_number,
                    "turn_order": [c.model_dump() for c in state.combat.combatants],
                    "current_turn": current_combatant_name,
                    "current_turn_id": current_combatant_id,
                    "monster_status": state.combat.monster_stats
                }
            else:
                logger.error(f"Invalid current_turn_index ({state.combat.current_turn_index}) for combatants list length ({len(state.combat.combatants)})")
                combat_info = {
                    "is_active": True,
                    "round": state.combat.round_number,
                    "turn_order": [c.model_dump() for c in state.combat.combatants],
                    "current_turn": "Error: Invalid Index",
                    "current_turn_id": None,
                    "monster_status": state.combat.monster_stats
                }

        return {
            "party": party_frontend,
            "location": state.current_location["name"],
            "location_description": state.current_location["description"],
            "narrative": self.get_last_narrative(),
            "chat_history": frontend_history,
            "dice_requests": state.pending_player_dice_requests,
            "combat_info": combat_info
        }

    def get_last_narrative(self) -> str:
        """Helper to get the content of the last assistant message."""
        for msg in reversed(self._game_state.chat_history):
            if msg["role"] == "assistant":
                return msg["content"]
        return ""

    def add_chat_message(self, role, content, gm_thought=None, is_dice_result=False, detailed_content=None, ai_response_json: Optional[str] = None):
        """
        Adds a message to the chat history (managed within GameState model).
        Stores the full AI JSON response for assistant messages if provided.
        """
        if role not in ["user", "assistant", "system"]:
            logger.warning(f"Invalid role '{role}' for chat message: {content[:100]}")
            return

        # Base message structure
        message = {"role": role}

        # Store full JSON for assistant, narrative/summary otherwise
        if role == "assistant" and ai_response_json:
            message["content"] = ai_response_json
            # Attempt to parse narrative for detailed_content (for frontend)
            try:
                parsed_response = json.loads(ai_response_json)
                # Fallback to content if parse fails
                message["detailed_content"] = parsed_response.get("narrative", content)
                # Store reasoning separately if needed, or assume it's in the JSON
                if parsed_response.get("reasoning"):
                    message["gm_thought"] = parsed_response.get("reasoning")
            except json.JSONDecodeError:
                logger.warning("Could not parse AI response JSON to extract narrative/thought for history.")
                 # Use original content as fallback
                message["detailed_content"] = content
                if gm_thought: message["gm_thought"] = gm_thought
        else:
            # For user/system messages, content is the primary data
            message["content"] = content
            if detailed_content:
                message["detailed_content"] = detailed_content
            if gm_thought:
                message["gm_thought"] = gm_thought
        if is_dice_result:
            message["is_dice_result"] = True
        self._game_state.chat_history.append(message)
        history_len = len(self._game_state.chat_history)
        logger.debug(f"Added {role} message to history. New length: {history_len}")

        # Use config value directly, default to a reasonable number like 50 turns (100 messages)
        max_history_messages = current_app.config.get('MAX_HISTORY_TURNS', 50) * 2
        if history_len > max_history_messages:
            # Keep system prompt + context messages + recent history
            num_to_keep = max_history_messages
            num_to_remove = history_len - num_to_keep

            # Find the index of the first message *after* the initial system prompt
            # Assuming system prompt is always the first message.
            first_non_system_index = 0
            for i, msg in enumerate(self._game_state.chat_history):
                if msg["role"] != "system" and not msg["content"].startswith("CONTEXT INJECTION"):
                    first_non_system_index = i
                    break
                # Safety break if only system/context messages exist (unlikely)
                if i > 10: break

            # Calculate where to start slicing, ensuring we keep the system prompt(s)
            slice_start_index = max(first_non_system_index, history_len - num_to_keep)

            original_len = history_len
            self._game_state.chat_history = self._game_state.chat_history[:first_non_system_index] + \
                                             self._game_state.chat_history[slice_start_index:]
            new_len = len(self._game_state.chat_history)
            logger.info(f"Chat history truncated from {original_len} to {new_len} messages (kept first {first_non_system_index} system/context + {new_len - first_non_system_index} recent).")


    def update_location(self, location_data: Optional[LocationUpdate]):
         """Updates the current location if valid data is provided."""
         if isinstance(location_data, LocationUpdate):
            old_location_name = self._game_state.current_location["name"]
            self._game_state.current_location = location_data.model_dump()
            if old_location_name != location_data.name:
                logger.info(f"Location updated from '{old_location_name}' to '{location_data.name}'")
            else:
                logger.debug(f"Location description updated for '{location_data.name}'")
         elif location_data is not None:
            logger.warning(f"Invalid location_update data received: {location_data}")

    def set_pending_player_dice_requests(self, requests: List[Dict]):
        """Stores PLAYER dice requests that need user action."""
        self._game_state.pending_player_dice_requests = requests
        logger.debug(f"Stored {len(requests)} pending PLAYER dice requests.")

    def clear_pending_player_dice_requests(self):
        """Clears pending player dice requests."""
        self._game_state.pending_player_dice_requests = []
        logger.debug("Cleared pending player dice requests.")

    def clear_pending_npc_roll_results(self):
         """Clears stored NPC roll results."""
         self._game_state._pending_npc_roll_results = []

    def _apply_game_state_updates(self, updates: List[GameStateUpdate]):
        """Applies a list of validated GameStateUpdate objects to the game state."""
        if not updates: return

        logger.info(f"Applying {len(updates)} game state update(s)...")
        for update in updates:
            # Make a copy to potentially modify/filter before processing
            current_update = update
            update_type = getattr(current_update, 'type', None)
            if not update_type:
                logger.error(f"Skipping game state update with missing 'type': {current_update}")
                continue
            logger.debug(f"Applying update: {current_update.model_dump_json(indent=2)}")
            try:
                if update_type == "hp_change":
                    # Check if it's an HPChangeUpdate instance before accessing attributes
                    if isinstance(current_update, HPChangeUpdate):
                        resolved_id = self.find_combatant_id_by_name_or_id(current_update.character_id)
                        if not resolved_id:
                            logger.error(f"Cannot apply HP change: Unknown character/combatant identifier '{current_update.character_id}'")
                            continue
                        self._apply_hp_change(current_update, resolved_id)
                    else:
                        logger.error(f"Mismatched type for hp_change update: Expected HPChangeUpdate, got {type(current_update)}")

                elif update_type in ["condition_add", "condition_remove"]:
                     # Check if it's a ConditionUpdate instance
                    if isinstance(current_update, ConditionUpdate):
                        resolved_id = self.find_combatant_id_by_name_or_id(current_update.character_id)
                        if not resolved_id:
                            logger.error(f"Cannot apply Condition update: Unknown character/combatant identifier '{current_update.character_id}'")
                            continue
                        self._apply_condition_update(current_update, resolved_id)
                    else:
                        logger.error(f"Mismatched type for condition update: Expected ConditionUpdate, got {type(current_update)}")

                elif update_type == "combat_start":
                    # Check if it's a CombatStartUpdate instance
                    if isinstance(current_update, CombatStartUpdate):
                        self._start_combat(current_update)
                    else:
                        logger.error(f"Mismatched type for combat_start update: Expected CombatStartUpdate, got {type(current_update)}")

                elif update_type == "combat_end":
                    can_end_combat = True
                    if self._game_state.combat.is_active:
                        active_npcs_found = False
                        for combatant in self._game_state.combat.combatants:
                            if not combatant.is_player:
                                npc_stats = self._game_state.combat.monster_stats.get(combatant.id)
                                if npc_stats:
                                    # Check if HP is above 0 AND not marked as defeated
                                    if npc_stats.get("hp", 0) > 0 and "Defeated" not in npc_stats.get("conditions", []):
                                        active_npcs_found = True
                                        logger.warning(f"AI requested 'combat_end', but active NPC '{combatant.name}' (ID: {combatant.id}, HP: {npc_stats.get('hp')}) found. Ignoring combat_end request.")
                                        break
                                else:
                                    # NPC in combatants list but missing stats? Log warning but potentially allow end? Safer to assume active?
                                    logger.warning(f"NPC '{combatant.name}' (ID: {combatant.id}) is in combatants list but missing from monster_stats during combat_end check. Assuming active for safety.")
                                    active_npcs_found = True
                                    break
                        if active_npcs_found:
                            can_end_combat = False

                    if can_end_combat:
                        # Check if it's a CombatEndUpdate instance
                        if isinstance(current_update, CombatEndUpdate):
                            self._end_combat(current_update)
                        else:
                            logger.error(f"Mismatched type for combat_end update: Expected CombatEndUpdate, got {type(current_update)}")
                    else:
                        # Log that we ignored it (already logged specific NPC above)
                        logger.info("Skipped processing 'combat_end' update due to active NPCs.")
                # TODO: Add future update types below
                # Example for Inventory (if it has character_id)
                # elif update_type in ["inventory_add", "inventory_remove"]:
                #     resolved_id = self.find_combatant_id_by_name_or_id(update.character_id)
                #     if not resolved_id:
                #         logger.error(f"Cannot apply Inventory update: Unknown character/combatant identifier '{update.character_id}'")
                #         continue
                #     self._apply_inventory_update(update, resolved_id)
                # Example for Gold (if it has character_id)
                # elif update_type == "gold_change":
                #     resolved_id = self.find_combatant_id_by_name_or_id(update.character_id)
                #     if not resolved_id:
                #         logger.error(f"Cannot apply Gold update: Unknown character/combatant identifier '{update.character_id}'")
                #         continue
                #     self._apply_gold_update(update, resolved_id)
                else:
                    logger.warning(f"Unhandled game state update type: {update.type}")
            except AttributeError as ae:
                # Catch cases where an expected attribute (like character_id) is missing for a type
                logger.error(f"Attribute error applying game state update {update_type}: {ae}. Check if the update schema matches the handler logic.", exc_info=True)
            except Exception as e:
                logger.error(f"Error applying game state update {update.type} ({update.model_dump()}): {e}", exc_info=True)

    def _apply_hp_change(self, update: HPChangeUpdate, resolved_id: str):
        target_id = resolved_id
        delta = update.value
        player = self.get_character_instance(target_id)
        if player:
            old_hp = player.current_hp
            # Apply rules (e.g., HP doesn't go above max, handle death saves below 0?)
            player.current_hp = max(0, min(player.max_hp, player.current_hp + delta))
            logger.info(f"Updated HP for {player.name} ({target_id}): {old_hp} -> {player.current_hp} (Delta: {delta})")
            if player.current_hp == 0:
                logger.info(f"{player.name} has dropped to 0 HP!")
                # TODO: Add 'Unconscious' condition automatically?
                # self._apply_condition_update(ConditionUpdate(type="condition_add", character_id=target_id, value="Unconscious"), target_id)
        elif self._game_state.combat.is_active and target_id in self._game_state.combat.monster_stats:
            monster = self._game_state.combat.monster_stats[target_id]
            old_hp = monster.get("hp", 0)
            monster["hp"] = max(0, monster.get("hp", 0) + delta)
            logger.info(f"Updated HP for NPC {self.get_combatant_name(target_id)} ({target_id}): {old_hp} -> {monster['hp']} (Delta: {delta})")
            if monster["hp"] == 0:
                logger.info(f"NPC {self.get_combatant_name(target_id)} ({target_id}) has dropped to 0 HP!")
                # AI should describe defeat in narrative, but we can mark them internally
                if "Defeated" not in monster.get("conditions", []):
                    monster.setdefault("conditions", []).append("Defeated")
        else:
            logger.error(f"Internal Error: Cannot apply HP change to resolved ID '{target_id}' which is not player or tracked NPC.")

    def _apply_condition_update(self, update: ConditionUpdate, resolved_id: str):
        target_id = resolved_id
        condition = update.value.lower()
        player = self.get_character_instance(target_id)
        target_list = None
        target_name = self.get_combatant_name(target_id)

        if player:
            target_list = player.conditions
        elif self._game_state.combat.is_active and target_id in self._game_state.combat.monster_stats:
            monster = self._game_state.combat.monster_stats[target_id]
            if "conditions" not in monster: monster["conditions"] = []
            target_list = monster["conditions"]
        else:
            # This case should not happen if resolved_id is valid
            logger.error(f"Internal Error: Cannot apply Condition update to resolved ID '{target_id}'.")
            return

        if update.type == "condition_add":
            if condition not in target_list:
                target_list.append(condition)
                logger.info(f"Added condition '{condition}' to {target_name} ({target_id})")
            else:
                logger.debug(f"Condition '{condition}' already present on {target_name} ({target_id})")
        elif update.type == "condition_remove":
            if condition in target_list:
                target_list.remove(condition)
                logger.info(f"Removed condition '{condition}' from {target_name} ({target_id})")
            else:
                logger.debug(f"Condition '{condition}' not found on {target_name} ({target_id}) to remove")


    def _start_combat(self, update: CombatStartUpdate):
        if self._game_state.combat.is_active:
            logger.warning("Received combat_start while combat is already active. Ignoring.")
            return

        logger.info("Starting combat! Populating initial combatants list.")
        combat = self._game_state.combat
        combat.is_active = True
        combat.round_number = 1
        combat.current_turn_index = 0
        combat.combatants = []
        combat.monster_stats = {}

        # Add Players to combatants list first
        for pc_id, pc_instance in self._game_state.party.items():
            combatant = Combatant(id=pc_id, name=pc_instance.name, initiative=-1, is_player=True)
            combat.combatants.append(combatant)
            logger.debug(f"Added player {pc_instance.name} ({pc_id}) to initial combatants list.")

        # Add NPCs/Monsters provided by AI
        for npc_data in update.combatants:
            npc_id = npc_data.get("id")
            npc_name = npc_data.get("name", npc_id)
            if not npc_id:
                # For now, log error and skip. AI *must* provide IDs.
                logger.error(f"NPC data missing 'id' in combat_start: {npc_data}. Skipping this combatant.")
                continue
            if npc_id in combat.monster_stats or npc_id in self._game_state.party:
                logger.warning(f"Duplicate combatant ID '{npc_id}' provided in combat_start. Skipping.")
                continue

            # Store basic stats provided by AI
            initial_hp = npc_data.get("hp", 10)
            combat.monster_stats[npc_id] = {
                "name": npc_name,
                "hp": initial_hp,
                "ac": npc_data.get("ac", 10),
                "conditions": [],
                "initial_hp": initial_hp,
                "stats": npc_data.get("stats", {"DEX": 10})
            }
            logger.debug(f"Added NPC {npc_name} ({npc_id}) to combat tracker stats.")

            # Add NPC to combatants list
            combatant = Combatant(id=npc_id, name=npc_name, initiative=-1, is_player=False)
            combat.combatants.append(combatant)
            logger.debug(f"Added NPC {npc_name} ({npc_id}) to initial combatants list.")

        logger.info(f"Combat started with {len(combat.combatants)} participants (Initiative Pending).")

    def _end_combat(self, update: CombatEndUpdate):
        if not self._game_state.combat.is_active:
            logger.warning("Received combat_end while combat is not active. Ignoring.")
            return
        logger.info(f"Ending combat. Reason: {update.details or 'Not specified'}")
        self._game_state.combat = CombatState()


    def _determine_initiative_order(self, roll_results: List[Dict]):
        """Updates initiatives and sorts the combatants list based on roll results."""
        combat = self._game_state.combat
        if not combat.is_active or not combat.combatants:
            logger.error("Cannot determine initiative order: Combat not active or no combatants list.")
            return

        logger.info("Determining initiative order...")
        initiative_map = {r["character_id"]: r["total_result"]
                          for r in roll_results if r.get("roll_type") == "initiative" and "total_result" in r}

        # Update initiative for each combatant in the existing list
        missing_rolls = []
        initiative_messages = []
        for combatant in combat.combatants:
            roll_result_for_combatant = next((r for r in roll_results if r.get("character_id") == combatant.id and r.get("roll_type") == "initiative"), None)

            if combatant.id in initiative_map:
                combatant.initiative = initiative_map[combatant.id]
                if roll_result_for_combatant:
                    # Use simplified summary for history aggregation
                    initiative_messages.append(roll_result_for_combatant.get("result_summary", f"{combatant.name} initiative: {combatant.initiative}"))
            else:
                # Handle missing rolls
                logger.warning(f"Missing initiative roll result for {combatant.name} ({combatant.id}). Rolling d20 as fallback.")
                missing_rolls.append(combatant.id)
                # Use perform_roll for fallback to get consistent calculation
                fallback_roll = self.perform_roll(
                    character_id=combatant.id,
                    roll_type='initiative',
                    dice_formula='1d20',
                    reason="Fallback Initiative Roll"
                )
                if "error" in fallback_roll:
                    combatant.initiative = random.randint(1, 20)
                    initiative_messages.append(f"{combatant.name} initiative: {combatant.initiative} (Error during fallback roll)")
                else:
                    combatant.initiative = fallback_roll.get("total_result", random.randint(1,20))
                    initiative_messages.append(fallback_roll.get("result_summary", f"{combatant.name} initiative: {combatant.initiative}") + " (Fallback)")

        # Sort the *existing* list based on initiative and tiebreaker (DEX)
        def sort_key(c: Combatant):
            dex_mod = 0
            if c.is_player:
                player = self.get_character_instance(c.id)
                if player: dex_mod = utils.get_ability_modifier(player.base_stats.DEX)
            elif c.id in combat.monster_stats:
                # Use stored DEX stat for NPC tiebreaker if available
                npc_stats = combat.monster_stats[c.id].get("stats", {})
                dex_mod = utils.get_ability_modifier(npc_stats.get("DEX", 10))
            return (c.initiative, dex_mod)

        combat.combatants.sort(key=sort_key, reverse=True)
        combat.current_turn_index = 0 # Reset turn index

        # Aggregate Initiative Info for History
        initiative_order_display = [f"{c.name}: {c.initiative}" for c in combat.combatants]
        logger.info(f"Initiative order set: {', '.join(initiative_order_display)}")
        if missing_rolls:
            logger.warning(f"Used fallback rolls for initiative: {', '.join(missing_rolls)}")

        # Combine all initiative info into one message
        combined_initiative_message = "**Initiative Rolls:**\n" + "\n".join(initiative_messages) + \
                                      "\n\n**Final Order:** " + ', '.join(initiative_order_display)
        self.add_chat_message("user", combined_initiative_message, is_dice_result=True)

    def advance_turn(self):
        """Advances to the next turn in combat."""
        if not self._game_state.combat.is_active or not self._game_state.combat.combatants: return

        # Check for defeated combatants and skip turn
        combat = self._game_state.combat
        skipped_count = 0
        max_skips = len(combat.combatants)
        while skipped_count < max_skips:
            next_index = (combat.current_turn_index + 1) % len(combat.combatants)
            next_combatant_id = combat.combatants[next_index].id
            is_defeated = False
            # Check player status (e.g., unconscious)
            player = self.get_character_instance(next_combatant_id)
            if player and player.current_hp <= 0:
                # Or check for specific "Unconscious" condition
                is_defeated = True
            # Check NPC status
            elif next_combatant_id in combat.monster_stats:
                monster = combat.monster_stats[next_combatant_id]
                if monster.get("hp", 1) <= 0 or "Defeated" in monster.get("conditions", []):
                    is_defeated = True
            if is_defeated:
                logger.debug(f"Skipping turn for defeated/incapacitated combatant: {combat.combatants[next_index].name}")
                combat.current_turn_index = next_index
                skipped_count += 1
                # Check if we wrapped around to the start of a new round while skipping
                if combat.current_turn_index == 0 and skipped_count > 0:
                    combat.round_number += 1
                    logger.info(f"Advanced to Combat Round {combat.round_number} while skipping defeated.")
                    # TODO: Handle end-of-round effects if needed here
            else:
                break
        else:
            logger.warning("All combatants appear defeated or incapacitated. Ending combat.")
            self._end_combat(CombatEndUpdate(type="combat_end", details={"reason": "All combatants defeated/incapacitated"}))
            self.add_chat_message("system", "**Combat Ended:** All participants defeated or incapacitated.", is_dice_result=True)
            return

        # Advance to the next active combatant
        combat.current_turn_index = (combat.current_turn_index + 1) % len(combat.combatants)
        new_round = False
        if combat.current_turn_index == 0:
            combat.round_number += 1
            new_round = True
            logger.info(f"Starting Combat Round {combat.round_number}")
            # TODO: Handle end-of-round effects

        # Check index validity again just in case
        if not (0 <= combat.current_turn_index < len(combat.combatants)):
            logger.error(f"Cannot advance turn: Invalid index {combat.current_turn_index}")
            combat.is_active = False # Safer to end combat if state is broken
            self.add_chat_message("system", "(Error: Combat state corrupted, ending combat.)", is_dice_result=True)
            return

        current_combatant = combat.combatants[combat.current_turn_index]
        logger.info(f"Advanced turn. Current: {current_combatant.name} (Round {combat.round_number})")
    
    def process_ai_response(self, ai_response: AIResponse) -> Tuple[List[Dict], bool]:
        """
        Updates the game state based on a validated AIResponse Pydantic object.
        Stores the full AIResponse JSON in history.
        Separates player/NPC rolls, performs NPC rolls internally.
        Applies game state updates.
        Checks if combat should end automatically if all NPCs are defeated.
        Checks ai_response.end_turn (if present and True) to advance combat turn (if still active).
        Returns a tuple: (pending_player_dice_requests, needs_ai_rerun)
        """
        logger.debug("Processing AIResponse object...")
        needs_ai_rerun = False
        ai_response_json = ai_response.model_dump_json()
        turn_should_advance = False

        # Log Reasoning First
        if ai_response.reasoning:
            logger.info(f"AI Reasoning: {ai_response.reasoning}")
        else:
            logger.warning("AI Response missing 'reasoning'.")

        # 1. Add AI Response JSON to History
        self.add_chat_message("assistant", ai_response.narrative, ai_response_json=ai_response_json)

        # 2. Update Location
        self.update_location(ai_response.location_update)

        # 3. Apply Game State Updates *BEFORE* processing rolls or turn end
        # (Validation for combat_end happens inside this method now)
        self._apply_game_state_updates(ai_response.game_state_updates)

        # Check if combat should end automatically
        if self._game_state.combat.is_active:
            all_npcs_defeated = True
            active_npc_found_name = None
            for combatant in self._game_state.combat.combatants:
                if not combatant.is_player:
                    npc_stats = self._game_state.combat.monster_stats.get(combatant.id)
                    if npc_stats:
                        # Check if HP is above 0 AND not explicitly marked as defeated
                        if npc_stats.get("hp", 0) > 0 and "Defeated" not in npc_stats.get("conditions", []):
                            all_npcs_defeated = False
                            active_npc_found_name = combatant.name
                            break
                    else:
                        # NPC in list but missing stats? Safer to assume they *could* be active.
                        logger.warning(f"NPC '{combatant.name}' (ID: {combatant.id}) found in combatants list but missing from monster_stats during auto-end check. Assuming potentially active.")
                        all_npcs_defeated = False
                        active_npc_found_name = f"{combatant.name} (missing stats)"
                        break

            if all_npcs_defeated:
                logger.info(f"Auto-detect: All non-player combatants are defeated. Forcing combat end. (Last active NPC check: {active_npc_found_name or 'None'})")
                self._end_combat(CombatEndUpdate(type="combat_end", details={"reason": "All enemies defeated (Auto-detected)"}))
                self.add_chat_message("system", "**Combat Ended:** All detected enemies have been defeated.", is_dice_result=True)
                # Since combat just ended, turn advancement logic below is skipped/irrelevant now.
                # Also, ensure needs_ai_rerun is false if combat just ended.
                needs_ai_rerun = False
                player_requests_to_send = []
                # Directly jump to setting pending requests and return, skipping roll/turn logic for this response
                self.clear_pending_player_dice_requests()
                logger.debug("Auto-combat end triggered. Clearing player requests and skipping further processing for this response.")
                return [], False

        # 4. Handle Dice Requests (Separating Player/NPC)
        player_requests_to_send = []
        npc_requests_to_roll = []
        party_char_ids_set = set(self._game_state.party.keys())

        for req_obj in ai_response.dice_requests:
            req_dict = req_obj.model_dump()
            req_char_ids_input = req_dict.get("character_ids", [])
            if not req_char_ids_input:
                logger.warning(f"Dice request missing character_ids: {req_dict}")
                continue

            # Handle 'all' expansion based on current combat state
            resolved_char_ids = set()
            if "all" in req_char_ids_input:
                if self._game_state.combat.is_active:
                    all_active_combatant_ids = set()
                    for c in self._game_state.combat.combatants:
                        is_defeated = False
                        player = self.get_character_instance(c.id)
                        if player and player.current_hp <= 0: is_defeated = True
                        elif c.id in self._game_state.combat.monster_stats:
                            monster = self._game_state.combat.monster_stats[c.id]
                            if monster.get("hp", 1) <= 0 or "Defeated" in monster.get("conditions", []): is_defeated = True
                        if not is_defeated:
                            all_active_combatant_ids.add(c.id)
                    resolved_char_ids.update(all_active_combatant_ids)
                    logger.info(f"Expanding 'all' in dice request to ACTIVE combatants: {list(resolved_char_ids)}")
                else:
                    resolved_char_ids.update(party_char_ids_set)
                    logger.info(f"Expanding 'all' in dice request to party members: {list(resolved_char_ids)}")
                # Add any other specific IDs mentioned alongside 'all'
                for specific_id in req_char_ids_input:
                    if specific_id != "all":
                        resolved = self.find_combatant_id_by_name_or_id(specific_id)
                        if resolved: resolved_char_ids.add(resolved)
            else:
                # Resolve each specific ID provided
                for specific_id_input in req_char_ids_input:
                    resolved = self.find_combatant_id_by_name_or_id(specific_id_input)
                    if resolved:
                        resolved_char_ids.add(resolved)
                    else:
                        logger.warning(f"Could not resolve ID '{specific_id_input}' in dice request. Skipping.")

            if not resolved_char_ids:
                logger.error(f"Could not resolve any valid character IDs for dice request: {req_dict}")
                continue

            # Ensure list contains only unique resolved IDs
            req_dict["character_ids"] = list(resolved_char_ids)

            # Separate player vs NPC based on resolved IDs
            player_ids_in_req = [cid for cid in resolved_char_ids if cid in party_char_ids_set]
            npc_ids_in_req = [cid for cid in resolved_char_ids if cid not in party_char_ids_set]

            # Create separate request objects if mixed
            if player_ids_in_req and npc_ids_in_req:
                logger.info(f"Splitting mixed Player/NPC request ID '{req_dict.get('request_id')}' for IDs: {list(resolved_char_ids)}")
                # Player part
                player_part = req_dict.copy()
                player_part["character_ids"] = player_ids_in_req
                player_requests_to_send.append(player_part)
                # NPC part
                npc_part = req_dict.copy()
                npc_part["character_ids"] = npc_ids_in_req
                npc_requests_to_roll.append(npc_part)
            elif player_ids_in_req:
                player_requests_to_send.append(req_dict)
            elif npc_ids_in_req:
                npc_requests_to_roll.append(req_dict)


        # Perform NPC Rolls Internally
        self.clear_pending_npc_roll_results()
        npc_roll_results = []
        npc_rolls_performed = False
        if npc_requests_to_roll:
            logger.info(f"Performing {len(npc_requests_to_roll)} NPC roll request(s) internally...")
            for npc_req in npc_requests_to_roll:
                npc_char_ids = npc_req.get("character_ids", [])
                for npc_id in npc_char_ids:
                    # Check defeat status *specifically* for this npc_id
                    is_defeated = False
                    if self._game_state.combat.is_active and npc_id in self._game_state.combat.monster_stats:
                        monster = self._game_state.combat.monster_stats[npc_id]
                        if monster.get("hp", 1) <= 0 or "Defeated" in monster.get("conditions", []):
                            is_defeated = True
                            logger.debug(f"Skipping roll for defeated NPC: {self.get_combatant_name(npc_id)} ({npc_id})")
                    elif not self._game_state.combat.is_active:
                        logger.warning(f"Attempting NPC roll for {npc_id} outside of active combat. Skipping.")
                        continue
                    elif npc_id not in self._game_state.combat.monster_stats:
                        logger.error(f"Attempting NPC roll for {npc_id} but they are not in monster_stats. Skipping.")
                        continue
                    if is_defeated:
                        continue

                    # Perform the roll for the non-defeated NPC
                    npc_roll_result = self.perform_roll(
                        character_id=npc_id,
                        roll_type=npc_req.get("type"),
                        dice_formula=npc_req.get("dice_formula"),
                        skill=npc_req.get("skill"),
                        ability=npc_req.get("ability"),
                        dc=npc_req.get("dc"),
                        reason=npc_req.get("reason", "")
                    )
                    if npc_roll_result and "error" not in npc_roll_result:
                        npc_roll_results.append(npc_roll_result)
                        self._game_state._pending_npc_roll_results.append(npc_roll_result)
                        npc_rolls_performed = True
                    elif npc_roll_result:
                        error_msg = f"(Error rolling for NPC {self.get_combatant_name(npc_id)}: {npc_roll_result.get('error')})"
                        logger.error(error_msg)
                        self.add_chat_message("system", error_msg, is_dice_result=True)
                    else:
                        logger.error(f"Internal NPC roll for {npc_id} returned None or invalid result.")

            # Add NPC roll results to history if any were performed
            if npc_roll_results:
                logger.debug(f"Adding {len(npc_roll_results)} NPC roll results to history.")
                npc_roll_messages = []
                npc_detailed_messages = []
                for result in npc_roll_results:
                    message = result.get("result_summary")
                    detailed_message = result.get("result_message")
                    if message:
                        npc_roll_messages.append(message)
                        npc_detailed_messages.append(detailed_message or message)
                    else:
                        logger.warning(f"NPC Roll result missing 'result_summary': {result}")
                if npc_roll_messages:
                    combined_summary = "**NPC Rolls:**\n" + "\n".join(npc_roll_messages)
                    combined_detailed = "**NPC Rolls:**\n" + "\n".join(npc_detailed_messages)
                    self.add_chat_message("user", combined_summary, is_dice_result=True, detailed_content=combined_detailed)

        # Determine if AI needs immediate rerun
        # Rerun if NPC rolls were performed AND no player action is required
        # NOTE: Needs_ai_rerun might have been set to False by the auto-combat-end check above
        if npc_rolls_performed and not player_requests_to_send and not needs_ai_rerun:
            needs_ai_rerun = True
            logger.info("NPC rolls performed and no player action required. Flagging for AI rerun.")
        elif needs_ai_rerun and (player_requests_to_send or not npc_rolls_performed):
            needs_ai_rerun = False

        # Check for Turn Advancement Signal
        # Use getattr to safely access optional field, default to None if missing
        ai_signals_end_turn = getattr(ai_response, 'end_turn', None)
        # Ensure combat is *still* active before trying to advance turn
        if self._game_state.combat.is_active and ai_signals_end_turn is True:
            if needs_ai_rerun:
                logger.warning("AI requested 'end_turn: true' but also triggered an AI rerun (due to NPC rolls). Turn will advance *after* the rerun loop completes.")
            elif player_requests_to_send:
                logger.warning("AI requested 'end_turn: true' but also requested player dice rolls. Turn will advance *after* player submits rolls.")
            else:
                # Conditions met: AI says end turn, no rerun needed, no player rolls needed, combat still active.
                logger.info("AI signaled end_turn=true and conditions met. Advancing turn.")
                self.advance_turn()
        elif self._game_state.combat.is_active:
            # Log if end_turn was false or None during combat
            if ai_signals_end_turn is False:
                logger.debug("AI explicitly set end_turn=false, turn not advancing.")
            elif ai_signals_end_turn is None:
                logger.debug("AI omitted end_turn field during combat, turn not advancing.")

        # Set Pending Player Requests
        pending_player_requests_to_return = []
        if player_requests_to_send:
            self.set_pending_player_dice_requests(player_requests_to_send)
            pending_player_requests_to_return = self._game_state.pending_player_dice_requests
            logger.info(f"{len(pending_player_requests_to_return)} player dice requests pending.")
        elif not needs_ai_rerun:
            self.clear_pending_player_dice_requests()
            logger.debug("No pending player dice requests or AI rerun needed.")

        # Return player requests and the rerun flag
        return pending_player_requests_to_return, needs_ai_rerun

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
