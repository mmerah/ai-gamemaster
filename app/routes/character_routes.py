"""
Character template management API routes.
"""
import logging
from dataclasses import asdict
import uuid
from flask import Blueprint, request, jsonify
from app.core.container import get_container
from app.game.unified_models import CharacterTemplateModel

logger = logging.getLogger(__name__)

# Create blueprint for character API routes
character_bp = Blueprint('character', __name__, url_prefix='/api')

@character_bp.route('/character_templates')
def get_character_templates():
    """Get all available character templates."""
    try:
        container = get_container()
        character_template_repo = container.get_character_template_repository()
        
        templates = character_template_repo.get_all_templates()
        # Convert dataclass to dict for JSON serialization
        templates_data = [asdict(template) for template in templates]
        
        return jsonify({"templates": templates_data})
        
    except Exception as e:
        logger.error(f"Error getting character templates: {e}", exc_info=True)
        return jsonify({"error": "Failed to get character templates"}), 500

@character_bp.route('/character_templates/<template_id>')
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

@character_bp.route('/character_templates', methods=['POST'])
def create_character_template():
    """Create a new character template."""
    try:
        container = get_container()
        character_template_repo = container.get_character_template_repository()
        
        template_data = request.get_json(force=True, silent=True)
        if not template_data:
            return jsonify({"error": "No template data provided"}), 400

        # Prepare data for the CharacterTemplateModel model
        # Direct mapping for most fields
        model_input_data = {
            "id": template_data.get("id") or str(uuid.uuid4()),
            "name": template_data.get("name"),
            "race": template_data.get("race"),
            "char_class": template_data.get("char_class"),
            "level": template_data.get("level", 1),
            "alignment": template_data.get("alignment"),
            "background": template_data.get("background"),
            "portrait_path": template_data.get("portrait_path"),
            
            # Map to unified model field names
            "subrace": template_data.get("subrace"),
            "subclass": template_data.get("subclass"),
            "starting_gold": template_data.get("starting_gold", 0),
            "languages": template_data.get("languages", ["Common"]),
            
            # Additional fields from unified model
            "racial_traits": template_data.get("racial_traits", []),
            "class_features": template_data.get("class_features", []),
            "feats": template_data.get("feats", []),
            "spells_known": template_data.get("spells_known", []),
            "cantrips_known": template_data.get("cantrips_known", []),
            "starting_equipment": template_data.get("starting_equipment", []),
            "personality_traits": template_data.get("personality_traits", []),
            "ideals": template_data.get("ideals", []),
            "bonds": template_data.get("bonds", []),
            "flaws": template_data.get("flaws", []),
            "appearance": template_data.get("appearance"),
            "backstory": template_data.get("backstory"),
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
            template = CharacterTemplateModel(**model_input_data)
        except Exception as e: # Catch potential Pydantic validation errors
            logger.error(f"Error instantiating CharacterTemplateModel model: {e}", exc_info=True)
            return jsonify({"error": f"Invalid template data: {e}"}), 400

        success = character_template_repo.save_template(template)
        if not success:
            return jsonify({"error": "Failed to save character template"}), 400
        
        return jsonify(template.model_dump()), 201
        
    except Exception as e:
        logger.error(f"Error creating character template: {e}", exc_info=True)
        return jsonify({"error": "Failed to create character template"}), 500

@character_bp.route('/character_templates/<template_id>', methods=['PUT'])
def update_character_template(template_id):
    """Update an existing character template."""
    try:
        container = get_container()
        character_template_repo = container.get_character_template_repository()
        
        # Check if template exists
        existing_template = character_template_repo.get_template(template_id)
        if not existing_template:
            return jsonify({"error": "Character template not found"}), 404
        
        template_data = request.get_json(force=True, silent=True)
        if not template_data:
            return jsonify({"error": "No template data provided"}), 400

        # Prepare data for the CharacterTemplateModel model
        # Direct mapping for most fields
        model_input_data = {
            "id": template_id,  # Use the ID from URL to ensure consistency
            "name": template_data.get("name"),
            "race": template_data.get("race"),
            "char_class": template_data.get("char_class"),
            "level": template_data.get("level", 1),
            "alignment": template_data.get("alignment"),
            "background": template_data.get("background"),
            "portrait_path": template_data.get("portrait_path"),
            
            # Map to unified model field names
            "subrace": template_data.get("subrace"),
            "subclass": template_data.get("subclass"),
            "starting_gold": template_data.get("starting_gold", 0),
            "languages": template_data.get("languages", ["Common"]),
            
            # Additional fields from unified model
            "racial_traits": template_data.get("racial_traits", []),
            "class_features": template_data.get("class_features", []),
            "feats": template_data.get("feats", []),
            "spells_known": template_data.get("spells_known", []),
            "cantrips_known": template_data.get("cantrips_known", []),
            "starting_equipment": template_data.get("starting_equipment", []),
            "personality_traits": template_data.get("personality_traits", []),
            "ideals": template_data.get("ideals", []),
            "bonds": template_data.get("bonds", []),
            "flaws": template_data.get("flaws", []),
            "appearance": template_data.get("appearance"),
            "backstory": template_data.get("backstory"),
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
        
        logger.debug(f"Processed template data for model update: {model_input_data}")
        
        try:
            template = CharacterTemplateModel(**model_input_data)
        except Exception as e: # Catch potential Pydantic validation errors
            logger.error(f"Error instantiating CharacterTemplateModel model: {e}", exc_info=True)
            return jsonify({"error": f"Invalid template data: {e}"}), 400

        success = character_template_repo.save_template(template)
        if not success:
            return jsonify({"error": "Failed to update character template"}), 400
        
        return jsonify(template.model_dump())
        
    except Exception as e:
        logger.error(f"Error updating character template {template_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to update character template"}), 500

@character_bp.route('/character_templates/<template_id>', methods=['DELETE'])
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

@character_bp.route('/character_templates/<template_id>/adventures')
def get_character_adventures(template_id):
    """Get all campaigns this character is participating in."""
    try:
        container = get_container()
        character_template_repo = container.get_character_template_repository()
        campaign_instance_repo = container.get_campaign_instance_repository()
        game_state_repo = container.get_game_state_repository()
        
        # Verify character template exists
        template = character_template_repo.get_template(template_id)
        if not template:
            return jsonify({"error": "Character template not found"}), 404
        
        # Get all campaign instances
        campaign_instances = campaign_instance_repo.get_all_instances()
        adventures = []
        
        # Check each campaign instance for this character
        for instance in campaign_instances:
            # Check if this character is in the campaign's party
            if template_id in instance.character_ids:
                # Try to load the game state for this campaign
                game_state = None
                try:
                    # Try to load the game state for this campaign instance
                    # For file-based repositories, we can temporarily switch campaigns
                    if hasattr(game_state_repo, 'set_campaign'):
                        original_campaign_id = getattr(game_state_repo, '_current_campaign_id', None)
                        game_state_repo.set_campaign(instance.id)
                        game_state = game_state_repo.get_game_state()
                        if original_campaign_id:
                            game_state_repo.set_campaign(original_campaign_id)
                    else:
                        # For in-memory repositories, try to get from campaign saves
                        if hasattr(game_state_repo, '_campaign_saves'):
                            game_state = game_state_repo._campaign_saves.get(instance.id)
                        else:
                            game_state = None
                except Exception as e:
                    logger.warning(f"Could not load game state for campaign instance {instance.id}: {e}")
                
                # Find the character instance in the game state
                character_data = None
                if game_state and game_state.party:
                    for character in game_state.party:
                        if character.template_id == template_id:
                            character_data = {
                                "current_hp": int(character.current_hp) if hasattr(character, 'current_hp') else 0,
                                "max_hp": int(character.max_hp) if hasattr(character, 'max_hp') else 0,
                                "level": int(character.level) if hasattr(character, 'level') else 1,
                                "class": str(character.char_class) if hasattr(character, 'char_class') else "Unknown",
                                "experience": int(getattr(character, 'experience', 0))
                            }
                            break
                
                # If no character data from game state, calculate proper defaults
                if not character_data:
                    # Use the character factory to calculate proper HP
                    from app.game.factories.character_factory import CharacterFactory
                    from app.game.calculators.dice_mechanics import get_ability_modifier
                    
                    # Load D5e class data if available
                    d5e_classes_data = {}
                    try:
                        import json
                        import os
                        d5e_path = os.path.join(os.path.dirname(__file__), '..', '..', 'saves', 'd5e_data', 'classes.json')
                        if os.path.exists(d5e_path):
                            with open(d5e_path, 'r') as f:
                                d5e_classes_data = json.load(f)
                    except Exception as e:
                        logger.warning(f"Could not load D5e class data: {e}")
                    
                    factory = CharacterFactory(d5e_classes_data=d5e_classes_data)
                    
                    # Calculate proper HP based on class and constitution
                    max_hp = factory._calculate_character_hit_points(template)
                    
                    character_data = {
                        "current_hp": max_hp,
                        "max_hp": max_hp,
                        "level": template.level,
                        "class": template.char_class,
                        "experience": 0
                    }
                
                adventure_info = {
                    "campaign_id": str(instance.id) if instance.id else None,
                    "campaign_name": str(instance.name) if instance.name else None,
                    "template_id": str(instance.template_id) if instance.template_id else None,
                    "last_played": instance.last_played.isoformat() if instance.last_played else None,
                    "created_date": instance.created_date.isoformat() if instance.created_date else None,
                    "session_count": instance.session_count,
                    "current_location": instance.current_location,
                    "in_combat": instance.in_combat,
                    "character_data": character_data
                }
                adventures.append(adventure_info)
        
        return jsonify({
            "character_name": template.name,
            "adventures": adventures
        })
        
    except Exception as e:
        logger.error(f"Error getting character adventures for {template_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to get character adventures"}), 500
