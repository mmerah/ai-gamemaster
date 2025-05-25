"""
Flask routes for the AI Game Master application.
"""
import logging
import os
from typing import Optional
from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory
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
    """Serve the Vue.js SPA."""
    return send_from_directory(os.path.join(os.getcwd(), 'static', 'dist'), 'index.html')

@main.route('/campaigns')
def campaign_manager():
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return send_from_directory(os.path.join(os.getcwd(), 'static', 'dist'), 'index.html')

@main.route('/campaign-manager')
def campaign_manager_alt():
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return send_from_directory(os.path.join(os.getcwd(), 'static', 'dist'), 'index.html')

@main.route('/game')
def game():
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return send_from_directory(os.path.join(os.getcwd(), 'static', 'dist'), 'index.html')

# Serve Vue.js static assets
@main.route('/static/dist/<path:filename>')
def serve_vue_assets(filename):
    """Serve Vue.js built assets."""
    from flask import Response
    import mimetypes
    
    # Get the file and determine MIME type
    file_path = os.path.join(os.getcwd(), 'static', 'dist', filename)
    
    # Set correct MIME type for JavaScript files
    if filename.endswith('.js'):
        mimetype = 'application/javascript'
    elif filename.endswith('.css'):
        mimetype = 'text/css'
    else:
        mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
    response = send_from_directory(os.path.join(os.getcwd(), 'static', 'dist'), filename)
    response.headers['Content-Type'] = mimetype
    return response

# Serve Vite assets (JS/CSS files in /assets/ folder)
@main.route('/assets/<path:filename>')
def serve_vite_assets(filename):
    """Serve Vite-generated assets with correct MIME types."""
    from flask import Response
    import mimetypes
    
    # Set correct MIME type for JavaScript files
    if filename.endswith('.js'):
        mimetype = 'application/javascript'
    elif filename.endswith('.css'):
        mimetype = 'text/css'
    else:
        mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    
    response = send_from_directory(os.path.join(os.getcwd(), 'static', 'dist', 'assets'), filename)
    response.headers['Content-Type'] = mimetype
    return response

# SPA fallback route - catch all other routes and serve the Vue.js app
@main.route('/<path:path>')
def spa_fallback(path):
    """Fallback route for Vue.js SPA client-side routing."""
    # Don't interfere with API routes
    if path.startswith('api/'):
        return jsonify({"error": "API endpoint not found"}), 404
    # Serve the Vue.js app for all other routes
    return send_from_directory(os.path.join(os.getcwd(), 'static', 'dist'), 'index.html')

@main.route('/api/game_state')
def get_game_state():
    """Get current game state for frontend."""
    try:
        container = get_container()
        game_event_manager = container.get_game_event_handler()
        
        # Get current state without triggering any actions
        response_data = game_event_manager.get_game_state()
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
        game_event_manager = container.get_game_event_handler()
        
        action_data = request.get_json()
        if not action_data:
            return jsonify({"error": "No action data provided"}), 400
        
        # Handle the player action through the service
        response_data = game_event_manager.handle_player_action(action_data)
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
        game_event_manager = container.get_game_event_handler()
        
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
            response_data = game_event_manager.handle_completed_roll_submission(roll_data["roll_results"])
        else:
            # Legacy format: roll requests that need to be processed
            logger.info("Using legacy dice submission handler")
            response_data = game_event_manager.handle_dice_submission(roll_data)
        
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
        game_event_manager = container.get_game_event_handler()
        
        # Handle the next step trigger through the service
        response_data = game_event_manager.handle_next_step_trigger()
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
        game_event_manager = container.get_game_event_handler()
        
        # Handle the retry through the service
        response_data = game_event_manager.handle_retry()
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
        from app.game.models import AbilityScores, Proficiencies

        # Prepare data for the CharacterTemplate model
        # Direct mapping for most fields
        model_input_data = {
            "id": template_data.get("id"),
            "name": template_data.get("name"),
            "race": template_data.get("race"),
            "char_class": template_data.get("char_class"),
            "level": template_data.get("level", 1),
            "alignment": template_data.get("alignment"),
            "background": template_data.get("background"),
            "icon": template_data.get("icon"), # Not currently set by form, will be None
            "portrait_path": template_data.get("portrait_path"),
            
            # New fields from CharacterSheet update
            "subrace_name": template_data.get("subrace"), # JS sends 'subrace'
            "subclass_name": template_data.get("subclass"), # JS sends 'subclass'
            "default_starting_gold": template_data.get("starting_gold", 0), # JS sends 'starting_gold'
            
            "languages": template_data.get("languages", ["Common"]),
        }

        # Handle nested base_stats - Pydantic expects a dict here, not an instance
        model_input_data["base_stats"] = template_data.get("base_stats", {})

        # Handle nested proficiencies - Pydantic expects a dict here
        js_proficiencies_data = template_data.get("proficiencies", {})
        proficiencies_dict = {
            "skills": template_data.get("skill_proficiencies", []),
            "armor": js_proficiencies_data.get("armor", []),
            "weapons": js_proficiencies_data.get("weapons", []),
            "tools": js_proficiencies_data.get("tools", []),
            "saving_throws": [] # Not currently set by frontend, defaults in model
        }
        model_input_data["proficiencies"] = proficiencies_dict
        
        # Filter out None values for optional fields to rely on Pydantic defaults if needed
        # However, explicit None is usually fine for Optional fields.
        # For now, let's pass them as is.
        
        logger.debug(f"Processed template data for model: {model_input_data}")
        
        try:
            template = CharacterTemplate(**model_input_data)
        except Exception as e: # Catch potential Pydantic validation errors
            logger.error(f"Error instantiating CharacterTemplate model: {e}", exc_info=True)
            return jsonify({"error": f"Invalid template data: {e}"}), 400

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

# TTS API Routes
@main.route('/api/tts/voices')
def get_tts_voices():
    """Get available TTS voices."""
    try:
        container = get_container()
        tts_service = container.get_tts_service()
        if not tts_service:
            return jsonify({"error": "TTS service not available"}), 503
        
        # Assuming lang_code 'a' for English for now, or make it a query param
        voices = tts_service.get_available_voices(lang_code='a') 
        return jsonify({"voices": voices})
        
    except Exception as e:
        logger.error(f"Error getting TTS voices: {e}", exc_info=True)
        return jsonify({"error": "Failed to get TTS voices"}), 500

@main.route('/api/tts/synthesize', methods=['POST'])
def synthesize_speech():
    """Synthesize speech from text."""
    try:
        container = get_container()
        tts_service = container.get_tts_service()
        if not tts_service:
            return jsonify({"error": "TTS service not available"}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        text = data.get('text')
        voice_id = data.get('voice_id', 'af_heart')  # Default voice
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Generate the audio file
        audio_path = tts_service.synthesize_speech(text, voice_id)
        if not audio_path:
            return jsonify({"error": "Failed to synthesize speech"}), 500
        
        # Construct proper URL for the audio file
        audio_url = f"/static/{audio_path}"
        
        # Return the URL to the audio file (frontend expects audio_url)
        return jsonify({
            "audio_url": audio_url,
            "voice_id": voice_id,
            "text": text
        })
        
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}", exc_info=True)
        return jsonify({"error": "Failed to synthesize speech"}), 500
