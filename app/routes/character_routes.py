"""
Character template management API routes.
"""
import logging
from flask import Blueprint, request, jsonify
from app.core.container import get_container

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
        # Convert to dict for JSON serialization
        templates_data = [template.model_dump() for template in templates]
        
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
        
        template_data = request.get_json()
        if not template_data:
            return jsonify({"error": "No template data provided"}), 400
        
        from app.game.models import CharacterTemplate

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
