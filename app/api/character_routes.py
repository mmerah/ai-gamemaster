"""
Character template management API routes.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import Blueprint, Response, jsonify, request
from pydantic import ValidationError

from app.api.dependencies import (
    get_campaign_instance_repository,
    get_campaign_template_repository,
    get_character_service,
    get_character_template_repository,
    get_content_service,
    get_game_state_repository,
)
from app.api.error_handlers import with_error_handling
from app.models.character import CharacterTemplateModel

logger = logging.getLogger(__name__)

# Create blueprint for character API routes
character_bp = Blueprint("character", __name__, url_prefix="/api")


@character_bp.route("/character_templates")
@with_error_handling("get_character_templates")
def get_character_templates() -> Union[Response, Tuple[Response, int]]:
    """Get all available character templates."""
    character_template_repo = get_character_template_repository()

    templates = character_template_repo.list()
    # Convert Pydantic models to dict for JSON serialization
    templates_data = [template.model_dump(mode="json") for template in templates]

    return jsonify({"templates": templates_data})


@character_bp.route("/character_templates/<template_id>")
@with_error_handling("get_character_template")
def get_character_template(template_id: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific character template."""
    character_template_repo = get_character_template_repository()

    template = character_template_repo.get(template_id)
    if not template:
        return jsonify({"error": "Character template not found"}), 404

    return jsonify(template.model_dump())


@character_bp.route("/character_templates", methods=["POST"])
@with_error_handling("create_character_template")
def create_character_template() -> Union[Response, Tuple[Response, int]]:
    """Create a new character template."""
    template_data = request.get_json(force=True, silent=True)
    if not template_data:
        return jsonify({"error": "No template data provided"}), 400

    # Generate ID if not provided
    if not template_data.get("id"):
        template_data["id"] = str(uuid.uuid4())

    # Handle frontend field mappings
    # Map skill_proficiencies to the nested proficiencies structure
    if "skill_proficiencies" in template_data:
        if "proficiencies" not in template_data:
            template_data["proficiencies"] = {}
        template_data["proficiencies"]["skills"] = template_data.pop(
            "skill_proficiencies"
        )

    # Parse and validate with Pydantic
    template = CharacterTemplateModel(**template_data)

    # Save the validated template
    character_template_repo = get_character_template_repository()

    success = character_template_repo.save(template)
    if not success:
        return jsonify({"error": "Failed to save character template"}), 500

    return jsonify(template.model_dump()), 201


@character_bp.route("/character_templates/<template_id>", methods=["PUT"])
@with_error_handling("update_character_template")
def update_character_template(
    template_id: str,
) -> Union[Response, Tuple[Response, int]]:
    """Update an existing character template."""
    # Check if template exists first
    character_template_repo = get_character_template_repository()

    existing_template = character_template_repo.get(template_id)
    if not existing_template:
        return jsonify({"error": "Character template not found"}), 404

    template_data = request.get_json(force=True, silent=True)
    if not template_data:
        return jsonify({"error": "No template data provided"}), 400

    # Ensure ID consistency
    template_data["id"] = template_id

    # Handle frontend field mappings
    # Map skill_proficiencies to the nested proficiencies structure
    if "skill_proficiencies" in template_data:
        if "proficiencies" not in template_data:
            template_data["proficiencies"] = {}
        template_data["proficiencies"]["skills"] = template_data.pop(
            "skill_proficiencies"
        )

    # Parse and validate with Pydantic
    template = CharacterTemplateModel(**template_data)

    # Save the validated template
    success = character_template_repo.save(template)
    if not success:
        return jsonify({"error": "Failed to update character template"}), 500

    return jsonify(template.model_dump())


@character_bp.route("/character_templates/<template_id>", methods=["DELETE"])
@with_error_handling("delete_character_template")
def delete_character_template(
    template_id: str,
) -> Union[Response, Tuple[Response, int]]:
    """Delete a character template."""
    character_template_repo = get_character_template_repository()

    success = character_template_repo.delete(template_id)
    if not success:
        return jsonify({"error": "Failed to delete character template"}), 400

    return jsonify({"message": "Character template deleted successfully"})


@character_bp.route("/character_templates/options")
@with_error_handling("get_character_creation_options")
def get_character_creation_options() -> Union[Response, Tuple[Response, int]]:
    """
    Get character creation options filtered by content packs.

    Query Parameters:
        content_pack_ids: Comma-separated list of content pack IDs to filter by
        campaign_id: Campaign ID to automatically get content pack priority from

    Returns:
        JSON object with races, classes, backgrounds, alignments, languages, skills
        filtered by the specified content packs
    """
    content_service = get_content_service()
    campaign_template_repo = get_campaign_template_repository()
    campaign_instance_repo = get_campaign_instance_repository()

    # Get content pack priority
    content_pack_ids: Optional[List[str]] = None

    # Option 1: Direct content pack IDs
    content_pack_ids_param = request.args.get("content_pack_ids")
    if content_pack_ids_param:
        content_pack_ids = [
            pack_id.strip()
            for pack_id in content_pack_ids_param.split(",")
            if pack_id.strip()
        ]

    # Option 2: Get from campaign
    campaign_id = request.args.get("campaign_id")
    if campaign_id and not content_pack_ids:
        # Get campaign template to find content pack priority
        # First try to get from instance
        campaign_instance = campaign_instance_repo.get(campaign_id)
        if campaign_instance and campaign_instance.content_pack_priority:
            content_pack_ids = campaign_instance.content_pack_priority
        elif campaign_instance and campaign_instance.template_id:
            # Fall back to template's content packs
            campaign_template = campaign_template_repo.get(
                campaign_instance.template_id
            )
            if campaign_template and campaign_template.content_pack_ids:
                content_pack_ids = campaign_template.content_pack_ids

    # Default to all content if no filtering specified
    if not content_pack_ids:
        content_pack_ids = []  # Empty list means all content

    # Fetch all character creation options with content pack filtering
    options: Dict[str, List[Dict[str, Any]]] = {
        "races": [],
        "classes": [],
        "backgrounds": [],
        "alignments": [],
        "languages": [],
        "skills": [],
        "ability_scores": [],
    }

    # Get races with content pack filtering
    races = content_service.get_races(content_pack_priority=content_pack_ids)
    options["races"] = [race.model_dump(mode="json") for race in races]

    # Get classes with content pack filtering
    classes = content_service.get_classes(content_pack_priority=content_pack_ids)
    options["classes"] = [class_.model_dump(mode="json") for class_ in classes]

    # Get backgrounds with content pack filtering
    backgrounds = content_service.get_backgrounds(
        content_pack_priority=content_pack_ids
    )
    options["backgrounds"] = [
        background.model_dump(mode="json") for background in backgrounds
    ]

    # Get other options with content pack filtering
    alignments = content_service.get_alignments(content_pack_priority=content_pack_ids)
    options["alignments"] = [
        alignment.model_dump(mode="json") for alignment in alignments
    ]

    languages = content_service.get_languages()
    options["languages"] = [language.model_dump(mode="json") for language in languages]

    skills = content_service.get_skills(content_pack_priority=content_pack_ids)
    options["skills"] = [skill.model_dump(mode="json") for skill in skills]

    ability_scores = content_service.get_ability_scores(
        content_pack_priority=content_pack_ids
    )
    options["ability_scores"] = [
        score.model_dump(mode="json") for score in ability_scores
    ]

    # Add metadata
    response = {
        "options": options,
        "metadata": {
            "content_pack_ids": content_pack_ids,
            "total_races": len(options["races"]),
            "total_classes": len(options["classes"]),
            "total_backgrounds": len(options["backgrounds"]),
        },
    }

    return jsonify(response)


@character_bp.route("/character_templates/<template_id>/adventures")
@with_error_handling("get_character_adventures")
def get_character_adventures(template_id: str) -> Union[Response, Tuple[Response, int]]:
    """Get all campaigns this character is participating in."""
    character_template_repo = get_character_template_repository()
    campaign_instance_repo = get_campaign_instance_repository()
    game_state_repo = get_game_state_repository()

    # Verify character template exists
    template = character_template_repo.get(template_id)
    if not template:
        return jsonify({"error": "Character template not found"}), 404

    # Get all campaign instances
    campaign_instances = campaign_instance_repo.list()
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
                if hasattr(game_state_repo, "set_campaign"):
                    original_campaign_id = getattr(
                        game_state_repo, "_current_campaign_id", None
                    )
                    game_state_repo.set_campaign(instance.id)
                    game_state = game_state_repo.get_game_state()
                    if original_campaign_id:
                        game_state_repo.set_campaign(original_campaign_id)
                else:
                    # For in-memory repositories, try to get from campaign saves
                    if hasattr(game_state_repo, "_campaign_saves"):
                        game_state = game_state_repo._campaign_saves.get(instance.id)
                    else:
                        game_state = None
            except Exception as e:
                logger.warning(
                    f"Could not load game state for campaign instance {instance.id}: {e}"
                )

            # Find the character instance in the game state
            character_data = None
            if game_state and game_state.party:
                for _, character in game_state.party.items():
                    if character.template_id == template_id:
                        character_data = {
                            "current_hp": int(character.current_hp)
                            if hasattr(character, "current_hp")
                            else 0,
                            "max_hp": int(character.max_hp)
                            if hasattr(character, "max_hp")
                            else 0,
                            "level": int(character.level)
                            if hasattr(character, "level")
                            else 1,
                            "class": str(character.char_class)
                            if hasattr(character, "char_class")
                            else "Unknown",
                            "experience": int(getattr(character, "experience", 0)),
                        }
                        break

            # If no character data from game state, calculate proper defaults
            if not character_data:
                # Use the character factory to calculate proper HP
                from app.domain.characters.character_factory import CharacterFactory

                # Get content service instead of loading JSON
                content_service = get_content_service()
                # CharacterFactory should accept the interface
                factory = CharacterFactory(content_service)

                # Calculate proper HP based on class and constitution
                max_hp = factory._calculate_character_hit_points(template)

                character_data = {
                    "current_hp": max_hp,
                    "max_hp": max_hp,
                    "level": template.level,
                    "class": template.char_class,
                    "experience": 0,
                }

            adventure_info = {
                "campaign_id": str(instance.id) if instance.id else None,
                "campaign_name": str(instance.name) if instance.name else None,
                "template_id": str(instance.template_id)
                if instance.template_id
                else None,
                "last_played": instance.last_played.isoformat()
                if instance.last_played
                else None,
                "created_date": instance.created_date.isoformat()
                if instance.created_date
                else None,
                "session_count": instance.session_count,
                "current_location": instance.current_location,
                "in_combat": instance.in_combat,
                "character_data": character_data,
            }
            adventures.append(adventure_info)

    return jsonify({"character_name": template.name, "adventures": adventures})
