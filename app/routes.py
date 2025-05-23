"""
Flask routes for the AI Game Master application.
"""
import logging
from typing import Optional
from flask import Blueprint, render_template, request, jsonify, current_app
from app.core.container import get_container

logger = logging.getLogger(__name__)

# Create blueprint
main = Blueprint('main', __name__)

def initialize_routes(app):
    """Initialize routes with the Flask app."""
    app.register_blueprint(main)
    logger.info("Routes initialized.")

@main.route('/')
def index():
    """Serve the main game interface or redirect to campaign manager."""
    try:
        container = get_container()
        game_state_repo = container.get_game_state_repository()
        
        # Check if there's an active game state
        current_game_state = game_state_repo.get_game_state()
        if not current_game_state.party or not getattr(current_game_state, 'campaign_id', None):
            # No active campaign, redirect to campaign manager
            return render_template('campaign_manager.html')
        
        # Active campaign found, serve the main game interface
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error checking game state: {e}", exc_info=True)
        # If there's an error, default to campaign manager
        return render_template('campaign_manager.html')

@main.route('/campaigns')
def campaign_manager():
    """Serve the campaign manager interface."""
    return render_template('campaign_manager.html')

@main.route('/game')
def game():
    """Serve the main game interface (forced)."""
    return render_template('index.html')

@main.route('/api/game_state')
def get_game_state():
    """Get current game state for frontend."""
    try:
        container = get_container()
        game_event_handler = container.get_game_event_handler()
        
        # Get current state without triggering any actions
        response_data = game_event_handler._get_state_for_frontend()
        response_data["needs_backend_trigger"] = False
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error getting game state: {e}", exc_info=True)
        return jsonify({"error": "Failed to get game state"}), 500

@main.route('/api/player_action', methods=['POST'])
def player_action():
    """Handle player actions."""
    try:
        container = get_container()
        game_event_handler = container.get_game_event_handler()
        
        action_data = request.get_json()
        if not action_data:
            return jsonify({"error": "No action data provided"}), 400
        
        # Handle the player action through the service
        response_data = game_event_handler.handle_player_action(action_data)
        status_code = response_data.pop("status_code", 200)
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Unhandled exception in player_action: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@main.route('/api/submit_rolls', methods=['POST'])
def submit_rolls():
    """Handle dice roll submissions."""
    try:
        container = get_container()
        game_event_handler = container.get_game_event_handler()
        
        roll_data = request.get_json()
        if roll_data is None:
            return jsonify({"error": "No roll data provided"}), 400
        
        logger.debug(f"Received roll data: {roll_data}")
        logger.debug(f"Roll data type: {type(roll_data)}")
        logger.debug(f"Has roll_results key: {'roll_results' in roll_data if isinstance(roll_data, dict) else 'Not a dict'}")
        
        # Check if this is the new format with roll_results
        if isinstance(roll_data, dict) and "roll_results" in roll_data:
            # New format: roll results already computed
            logger.info("Using completed roll submission handler")
            response_data = game_event_handler.handle_completed_roll_submission(roll_data["roll_results"])
        else:
            # Legacy format: roll requests that need to be processed
            logger.info("Using legacy dice submission handler")
            response_data = game_event_handler.handle_dice_submission(roll_data)
        
        status_code = response_data.pop("status_code", 200)
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Unhandled exception in submit_rolls: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@main.route('/api/trigger_next_step', methods=['POST'])
def trigger_next_step():
    """Trigger the next step in the game (usually for NPC turns)."""
    try:
        container = get_container()
        game_event_handler = container.get_game_event_handler()
        
        # Handle the next step trigger through the service
        response_data = game_event_handler.handle_next_step_trigger()
        status_code = response_data.pop("status_code", 200)
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Unhandled exception in trigger_next_step: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@main.route('/api/retry_last_ai_request', methods=['POST'])
def retry_last_ai_request():
    """Retry the last AI request that failed."""
    try:
        container = get_container()
        game_event_handler = container.get_game_event_handler()
        
        # Handle the retry through the service
        response_data = game_event_handler.handle_retry_last_ai_request()
        status_code = response_data.pop("status_code", 200)
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        logger.error(f"Unhandled exception in retry_last_ai_request: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@main.route('/api/perform_roll', methods=['POST'])
def perform_roll():
    """Perform an immediate dice roll and return the result."""
    try:
        container = get_container()
        dice_service = container.get_dice_service()
        
        roll_data = request.get_json()
        if not roll_data:
            return jsonify({"error": "No roll data provided"}), 400
        
        # Extract roll parameters
        character_id = roll_data.get('character_id')
        roll_type = roll_data.get('roll_type')
        dice_formula = roll_data.get('dice_formula')
        skill = roll_data.get('skill')
        ability = roll_data.get('ability')
        dc = roll_data.get('dc')
        reason = roll_data.get('reason', '')
        request_id = roll_data.get('request_id')
        
        if not all([character_id, roll_type, dice_formula]):
            return jsonify({"error": "Missing required roll parameters"}), 400
        
        # Perform the roll
        roll_result = dice_service.perform_roll(
            character_id=character_id,
            roll_type=roll_type,
            dice_formula=dice_formula,
            skill=skill,
            ability=ability,
            dc=dc,
            reason=reason,
            original_request_id=request_id
        )
        
        if "error" in roll_result:
            return jsonify(roll_result), 400
        
        return jsonify(roll_result)
        
    except Exception as e:
        logger.error(f"Unhandled exception in perform_roll: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# Campaign Management API Routes
@main.route('/api/campaigns')
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

@main.route('/api/campaigns/<campaign_id>')
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

@main.route('/api/campaigns', methods=['POST'])
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

@main.route('/api/campaigns/<campaign_id>', methods=['DELETE'])
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

@main.route('/api/campaigns/<campaign_id>/start', methods=['POST'])
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

# Character Template Management API Routes
@main.route('/api/character_templates')
def get_character_templates():
    """Get all available character templates."""
    try:
        container = get_container()
        character_template_repo = container.get_character_template_repository()
        
        templates = character_template_repo.get_all_templates()
        # Convert to dict for JSON serialization
        templates_data = [template.model_dump() for template in templates]
        
        return jsonify({"templates": templates_data})
        
    except Exception as e:
        logger.error(f"Error getting character templates: {e}", exc_info=True)
        return jsonify({"error": "Failed to get character templates"}), 500

@main.route('/api/character_templates/<template_id>')
def get_character_template(template_id):
    """Get a specific character template."""
    try:
        container = get_container()
        character_template_repo = container.get_character_template_repository()
        
        template = character_template_repo.get_template(template_id)
        if not template:
            return jsonify({"error": "Character template not found"}), 404
        
        return jsonify(template.model_dump())
        
    except Exception as e:
        logger.error(f"Error getting character template {template_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to get character template"}), 500

@main.route('/api/character_templates', methods=['POST'])
def create_character_template():
    """Create a new character template."""
    try:
        container = get_container()
        character_template_repo = container.get_character_template_repository()
        
        template_data = request.get_json()
        if not template_data:
            return jsonify({"error": "No template data provided"}), 400
        
        from app.game.enhanced_models import CharacterTemplate
        template = CharacterTemplate(**template_data)
        
        success = character_template_repo.save_template(template)
        if not success:
            return jsonify({"error": "Failed to save character template"}), 400
        
        return jsonify(template.model_dump()), 201
        
    except Exception as e:
        logger.error(f"Error creating character template: {e}", exc_info=True)
        return jsonify({"error": "Failed to create character template"}), 500

@main.route('/api/character_templates/<template_id>', methods=['DELETE'])
def delete_character_template(template_id):
    """Delete a character template."""
    try:
        container = get_container()
        character_template_repo = container.get_character_template_repository()
        
        success = character_template_repo.delete_template(template_id)
        if not success:
            return jsonify({"error": "Failed to delete character template"}), 400
        
        return jsonify({"message": "Character template deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting character template {template_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete character template"}), 500

# D&D 5e Reference Data API Routes
@main.route('/api/d5e/races')
def get_d5e_races():
    """Get D&D 5e race data."""
    try:
        import json
        import os
        
        races_file = os.path.join("saves", "d5e_data", "races.json")
        if not os.path.exists(races_file):
            return jsonify({"error": "D&D 5e race data not found"}), 404
        
        with open(races_file, 'r', encoding='utf-8') as f:
            races_data = json.load(f)
        
        return jsonify(races_data)
        
    except Exception as e:
        logger.error(f"Error getting D&D 5e races: {e}", exc_info=True)
        return jsonify({"error": "Failed to get D&D 5e races"}), 500

@main.route('/api/d5e/classes')
def get_d5e_classes():
    """Get D&D 5e class data."""
    try:
        import json
        import os
        
        classes_file = os.path.join("saves", "d5e_data", "classes.json")
        if not os.path.exists(classes_file):
            return jsonify({"error": "D&D 5e class data not found"}), 404
        
        with open(classes_file, 'r', encoding='utf-8') as f:
            classes_data = json.load(f)
        
        return jsonify(classes_data)
        
    except Exception as e:
        logger.error(f"Error getting D&D 5e classes: {e}", exc_info=True)
        return jsonify({"error": "Failed to get D&D 5e classes"}), 500
