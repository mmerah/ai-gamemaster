"""
Campaign management API routes.
"""
import logging
from typing import Optional, Union, Tuple, Dict, Any
from flask import Blueprint, jsonify, Response
from app.core.container import get_container
from app.game.unified_models import GameStateModel, CharacterInstanceModel, NPCModel, QuestModel, CombatStateModel

logger = logging.getLogger(__name__)

# Create blueprint for campaign API routes
campaign_bp = Blueprint('campaign', __name__, url_prefix='/api')

@campaign_bp.route('/campaign-overview')
def get_campaign_overview() -> Union[Tuple[Dict[str, Any], int], Response]:
    """Get overview of both campaign templates and instances."""
    try:
        container = get_container()
        campaign_service = container.get_campaign_service()
        
        overview = campaign_service.get_campaign_overview()
        return jsonify(overview)
        
    except Exception as e:
        logger.error(f"Error getting campaign overview: {e}", exc_info=True)
        return jsonify({"error": "Failed to get campaign overview"}), 500

@campaign_bp.route('/campaign-instances')
def get_campaign_instances() -> Union[Tuple[Dict[str, Any], int], Response]:
    """Get all campaign instances (ongoing games)."""
    try:
        container = get_container()
        instance_repo = container.get_campaign_instance_repository()
        
        instances = instance_repo.get_all_instances()
        logger.info(f"Retrieved {len(instances)} campaign instances")
        # Convert to dict for JSON serialization
        instances_data = []
        for instance in instances:
            instance_dict = {
                "id": instance.id,
                "name": instance.name,
                "template_id": instance.template_id,
                "character_ids": instance.character_ids,
                "party_size": len(instance.character_ids),
                "current_location": instance.current_location,
                "session_count": instance.session_count,
                "in_combat": instance.in_combat,
                "created_date": instance.created_date.isoformat() if instance.created_date else None,
                "last_played": instance.last_played.isoformat() if instance.last_played else None,
                "created_at": instance.created_date.isoformat() if instance.created_date else None,  # Frontend compatibility
                "narration_enabled": instance.narration_enabled,
                "tts_voice": instance.tts_voice
            }
            instances_data.append(instance_dict)
        
        return jsonify({"campaigns": instances_data})
        
    except Exception as e:
        logger.error(f"Error getting campaign instances: {e}", exc_info=True)
        return jsonify({"error": "Failed to get campaign instances"}), 500







@campaign_bp.route('/campaigns/<campaign_id>/start', methods=['POST'])
def start_campaign(campaign_id):
    """Start/load a campaign.
    
    IMPORTANT: Despite the route name, campaign_id here can be either:
    - A campaign instance ID (for loading an existing game)
    - A campaign template ID (for starting a new game - deprecated path)
    
    This endpoint loads a saved campaign instance and makes it the active game.
    If no saved state exists, it initializes from the campaign template.
    """
    try:
        container = get_container()
        campaign_service = container.get_campaign_service()
        game_state_repo = container.get_game_state_repository()
        
        loaded_game_state: Optional['GameStateModel'] = None

        # Attempt to load existing saved state for this campaign
        if hasattr(game_state_repo, 'load_campaign_state'):
            loaded_game_state = game_state_repo.load_campaign_state(campaign_id)
        
        final_game_state: 'GameStateModel'
        if loaded_game_state:
            logger.info(f"Loaded existing game state for campaign {campaign_id}")
            final_game_state = loaded_game_state
        else:
            logger.info(f"No existing save for campaign {campaign_id}, initializing new state from definition.")
            initial_state_dict = campaign_service.start_campaign(campaign_id)  # Gets initial definition as dict
            if not initial_state_dict:
                return jsonify({"error": "Failed to get initial campaign definition"}), 400
            
            party_instances = {}
            for char_id_key, char_data in initial_state_dict.get("party", {}).items():
                party_instances[char_id_key] = CharacterInstanceModel(**char_data)
            
            known_npcs = {}
            for npc_id_key, npc_data in initial_state_dict.get("known_npcs", {}).items():
                if isinstance(npc_data, dict):  # Ensure it's a dict before splatting
                    known_npcs[npc_id_key] = NPCModel(**npc_data)
                elif isinstance(npc_data, NPCModel):  # If service already returned model
                    known_npcs[npc_id_key] = npc_data
                else:
                    logger.warning(f"NPC data for {npc_id_key} is not a dict or NPCModel. Skipping.")

            active_quests = {}
            for q_id_key, q_data in initial_state_dict.get("active_quests", {}).items():
                if isinstance(q_data, dict):  # Ensure it's a dict
                    active_quests[q_id_key] = QuestModel(**q_data)
                elif isinstance(q_data, QuestModel):  # If service already returned model
                    active_quests[q_id_key] = q_data
                else:
                     logger.warning(f"Quest data for {q_id_key} is not a dict or QuestModel. Skipping.")

            combat_data = initial_state_dict.get("combat", {})
            # Remove private fields that shouldn't be in the model
            if isinstance(combat_data, dict):
                combat_data.pop("_combat_just_started_flag", None)
                combat_state_obj = CombatStateModel(**combat_data)
            else:
                combat_state_obj = combat_data

            game_state_data_for_model = {
                "party": party_instances,
                "current_location": initial_state_dict.get("current_location", {"name": "Unknown", "description": ""}),
                "chat_history": initial_state_dict.get("chat_history", []),
                "pending_player_dice_requests": initial_state_dict.get("pending_player_dice_requests", []),
                "combat": combat_state_obj,
                "campaign_goal": initial_state_dict.get("campaign_goal", "No specific goal set."),
                "known_npcs": known_npcs,
                "active_quests": active_quests,
                "world_lore": initial_state_dict.get("world_lore", []),
                "event_summary": initial_state_dict.get("event_summary", []),
                "campaign_id": initial_state_dict.get("campaign_id"),
                "narration_enabled": initial_state_dict.get("narration_enabled", False),
                "tts_voice": initial_state_dict.get("tts_voice", "af_heart")
            }
            # Note: Private fields like _pending_npc_roll_results are not included
            final_game_state = GameStateModel(**game_state_data_for_model)

        # Save this state (either loaded or newly initialized)
        # This also makes it the "active" state in the repository's memory
        game_state_repo.save_game_state(final_game_state) 
        
        return jsonify({
            "message": "Campaign started successfully",
            "initial_state": final_game_state.model_dump()
        })
        
    except Exception as e:
        logger.error(f"Error starting campaign {campaign_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to start campaign"}), 500
