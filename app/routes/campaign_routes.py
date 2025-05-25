"""
Campaign management API routes.
"""
import logging
from typing import Optional
from flask import Blueprint, request, jsonify
from app.core.container import get_container

logger = logging.getLogger(__name__)

# Create blueprint for campaign API routes
campaign_bp = Blueprint('campaign', __name__, url_prefix='/api')

@campaign_bp.route('/campaigns')
def get_campaigns():
    """Get all available campaigns."""
    try:
        container = get_container()
        campaign_service = container.get_campaign_service()
        
        campaigns = campaign_service.get_all_campaigns()
        # Convert to dict for JSON serialization
        campaigns_data = []
        for campaign in campaigns:
            campaign_dict = campaign.model_dump()
            # Convert datetime objects to ISO strings
            if campaign_dict.get("created_date"):
                campaign_dict["created_date"] = campaign.created_date.isoformat()
            if campaign_dict.get("last_played"):
                campaign_dict["last_played"] = campaign.last_played.isoformat() if campaign.last_played else None
            campaigns_data.append(campaign_dict)
        
        return jsonify({"campaigns": campaigns_data})
        
    except Exception as e:
        logger.error(f"Error getting campaigns: {e}", exc_info=True)
        return jsonify({"error": "Failed to get campaigns"}), 500

@campaign_bp.route('/campaigns/<campaign_id>')
def get_campaign(campaign_id):
    """Get a specific campaign."""
    try:
        container = get_container()
        campaign_service = container.get_campaign_service()
        
        campaign = campaign_service.get_campaign(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        
        # Convert to dict for JSON serialization
        campaign_dict = campaign.model_dump()
        if campaign_dict.get("created_date"):
            campaign_dict["created_date"] = campaign.created_date.isoformat()
        if campaign_dict.get("last_played"):
            campaign_dict["last_played"] = campaign.last_played.isoformat() if campaign.last_played else None
        
        return jsonify(campaign_dict)
        
    except Exception as e:
        logger.error(f"Error getting campaign {campaign_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to get campaign"}), 500

@campaign_bp.route('/campaigns', methods=['POST'])
def create_campaign():
    """Create a new campaign."""
    try:
        container = get_container()
        campaign_service = container.get_campaign_service()
        
        campaign_data = request.get_json()
        if not campaign_data:
            return jsonify({"error": "No campaign data provided"}), 400
        
        campaign = campaign_service.create_campaign(campaign_data)
        if not campaign:
            return jsonify({"error": "Failed to create campaign"}), 400
        
        # Convert to dict for JSON serialization
        campaign_dict = campaign.model_dump()
        if campaign_dict.get("created_date"):
            campaign_dict["created_date"] = campaign.created_date.isoformat()
        if campaign_dict.get("last_played"):
            campaign_dict["last_played"] = campaign.last_played.isoformat() if campaign.last_played else None
        
        return jsonify(campaign_dict), 201
        
    except Exception as e:
        logger.error(f"Error creating campaign: {e}", exc_info=True)
        return jsonify({"error": "Failed to create campaign"}), 500

@campaign_bp.route('/campaigns/<campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    """Delete a campaign."""
    try:
        container = get_container()
        campaign_service = container.get_campaign_service()
        
        success = campaign_service.delete_campaign(campaign_id)
        if not success:
            return jsonify({"error": "Failed to delete campaign"}), 400
        
        return jsonify({"message": "Campaign deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting campaign {campaign_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete campaign"}), 500

@campaign_bp.route('/campaigns/<campaign_id>/start', methods=['POST'])
def start_campaign(campaign_id):
    """Start/load a campaign."""
    try:
        container = get_container()
        campaign_service = container.get_campaign_service()
        game_state_repo = container.get_game_state_repository()
        
        loaded_game_state: Optional['GameState'] = None

        # Attempt to load existing saved state for this campaign
        if hasattr(game_state_repo, 'load_campaign_state'):
            loaded_game_state = game_state_repo.load_campaign_state(campaign_id)
        
        final_game_state: 'GameState'
        if loaded_game_state:
            logger.info(f"Loaded existing game state for campaign {campaign_id}")
            final_game_state = loaded_game_state
        else:
            logger.info(f"No existing save for campaign {campaign_id}, initializing new state from definition.")
            initial_state_dict = campaign_service.start_campaign(campaign_id)  # Gets initial definition as dict
            if not initial_state_dict:
                return jsonify({"error": "Failed to get initial campaign definition"}), 400
            
            # Convert dict to GameState
            from app.game.models import GameState, CharacterInstance, KnownNPC, Quest, CombatState
            
            party_instances = {}
            for char_id_key, char_data in initial_state_dict.get("party", {}).items():
                party_instances[char_id_key] = CharacterInstance(**char_data)
            
            known_npcs = {}
            for npc_id_key, npc_data in initial_state_dict.get("known_npcs", {}).items():
                if isinstance(npc_data, dict):  # Ensure it's a dict before splatting
                    known_npcs[npc_id_key] = KnownNPC(**npc_data)
                elif isinstance(npc_data, KnownNPC):  # If service already returned model
                    known_npcs[npc_id_key] = npc_data
                else:
                    logger.warning(f"NPC data for {npc_id_key} is not a dict or KnownNPC model. Skipping.")

            active_quests = {}
            for q_id_key, q_data in initial_state_dict.get("active_quests", {}).items():
                if isinstance(q_data, dict):  # Ensure it's a dict
                    active_quests[q_id_key] = Quest(**q_data)
                elif isinstance(q_data, Quest):  # If service already returned model
                    active_quests[q_id_key] = q_data
                else:
                     logger.warning(f"Quest data for {q_id_key} is not a dict or Quest model. Skipping.")

            combat_data = initial_state_dict.get("combat", {})
            combat_state_obj = CombatState(**combat_data) if isinstance(combat_data, dict) else combat_data

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
                "_pending_npc_roll_results": initial_state_dict.get("_pending_npc_roll_results", []),
                "campaign_id": initial_state_dict.get("campaign_id") 
            }
            final_game_state = GameState(**game_state_data_for_model)

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
