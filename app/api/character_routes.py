"""
Character template management API routes.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import Blueprint, Response, jsonify, request
from pydantic import ValidationError

from app.core.container import get_container
from app.models.character import CharacterTemplateModel

logger = logging.getLogger(__name__)

# Create blueprint for character API routes
character_bp = Blueprint("character", __name__, url_prefix="/api")


@character_bp.route("/character_templates")
def get_character_templates() -> Union[Response, Tuple[Response, int]]:
    """Get all available character templates."""
    try:
        container = get_container()
        character_template_repo = container.get_character_template_repository()

        templates = character_template_repo.get_all_templates()
        # Convert Pydantic models to dict for JSON serialization
        templates_data = [template.model_dump(mode="json") for template in templates]

        return jsonify({"templates": templates_data})

    except Exception as e:
        logger.error(f"Error getting character templates: {e}", exc_info=True)
        return jsonify({"error": "Failed to get character templates"}), 500


@character_bp.route("/character_templates/<template_id>")
def get_character_template(template_id: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific character template."""
    try:
        container = get_container()
        character_template_repo = container.get_character_template_repository()

        template = character_template_repo.get_template(template_id)
        if not template:
            return jsonify({"error": "Character template not found"}), 404

        return jsonify(template.model_dump())

    except Exception as e:
        logger.error(
            f"Error getting character template {template_id}: {e}", exc_info=True
        )
        return jsonify({"error": "Failed to get character template"}), 500


@character_bp.route("/character_templates", methods=["POST"])
def create_character_template() -> Union[Response, Tuple[Response, int]]:
    """Create a new character template."""
    try:
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
        container = get_container()
        character_template_repo = container.get_character_template_repository()

        success = character_template_repo.save_template(template)
        if not success:
            return jsonify({"error": "Failed to save character template"}), 500

        return jsonify(template.model_dump()), 201

    except ValidationError as e:
        logger.error(f"Validation error creating character template: {e}")
        return jsonify({"error": e.errors()}), 422
    except Exception as e:
        logger.error(f"Error creating character template: {e}", exc_info=True)
        return jsonify({"error": "Failed to create character template"}), 500


@character_bp.route("/character_templates/<template_id>", methods=["PUT"])
def update_character_template(
    template_id: str,
) -> Union[Response, Tuple[Response, int]]:
    """Update an existing character template."""
    try:
        # Check if template exists first
        container = get_container()
        character_template_repo = container.get_character_template_repository()

        existing_template = character_template_repo.get_template(template_id)
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
        success = character_template_repo.save_template(template)
        if not success:
            return jsonify({"error": "Failed to update character template"}), 500

        return jsonify(template.model_dump())

    except ValidationError as e:
        logger.error(f"Validation error updating character template {template_id}: {e}")
        return jsonify({"error": e.errors()}), 422
    except Exception as e:
        logger.error(
            f"Error updating character template {template_id}: {e}", exc_info=True
        )
        return jsonify({"error": "Failed to update character template"}), 500


@character_bp.route("/character_templates/<template_id>", methods=["DELETE"])
def delete_character_template(
    template_id: str,
) -> Union[Response, Tuple[Response, int]]:
    """Delete a character template."""
    try:
        container = get_container()
        character_template_repo = container.get_character_template_repository()

        success = character_template_repo.delete_template(template_id)
        if not success:
            return jsonify({"error": "Failed to delete character template"}), 400

        return jsonify({"message": "Character template deleted successfully"})

    except Exception as e:
        logger.error(
            f"Error deleting character template {template_id}: {e}", exc_info=True
        )
        return jsonify({"error": "Failed to delete character template"}), 500


@character_bp.route("/character_templates/options")
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
    try:
        container = get_container()
        content_service = container.get_content_service()

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
            campaign_template_repo = container.get_campaign_template_repository()
            campaign_instance_repo = container.get_campaign_instance_repository()

            # First try to get from instance
            campaign_instance = campaign_instance_repo.get_instance(campaign_id)
            if campaign_instance and campaign_instance.content_pack_priority:
                content_pack_ids = campaign_instance.content_pack_priority
            elif campaign_instance and campaign_instance.template_id:
                # Fall back to template's content packs
                campaign_template = campaign_template_repo.get_template(
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

        # Get races with content pack info
        if content_pack_ids:
            races = content_service._hub.races.list_all_with_options(
                content_pack_priority=content_pack_ids
            )
        else:
            races = content_service._hub.races.list_all()

        for race in races:
            race_data = race.model_dump(mode="json")
            # Add source info if available
            if hasattr(race, "_content_pack"):
                race_data["_source"] = {
                    "content_pack_id": race._content_pack.id,
                    "content_pack_name": race._content_pack.display_name,
                }
            options["races"].append(race_data)

        # Get classes with content pack info
        if content_pack_ids:
            classes = content_service._hub.classes.list_all_with_options(
                content_pack_priority=content_pack_ids
            )
        else:
            classes = content_service._hub.classes.list_all()

        for class_ in classes:
            class_data = class_.model_dump(mode="json")
            if hasattr(class_, "_content_pack"):
                class_data["_source"] = {
                    "content_pack_id": class_._content_pack.id,
                    "content_pack_name": class_._content_pack.display_name,
                }
            options["classes"].append(class_data)

        # Get backgrounds with content pack info
        if content_pack_ids:
            backgrounds = content_service._hub.backgrounds.list_all_with_options(
                content_pack_priority=content_pack_ids
            )
        else:
            backgrounds = content_service._hub.backgrounds.list_all()

        for background in backgrounds:
            background_data = background.model_dump(mode="json")
            if hasattr(background, "_content_pack"):
                background_data["_source"] = {
                    "content_pack_id": background._content_pack.id,
                    "content_pack_name": background._content_pack.display_name,
                }
            options["backgrounds"].append(background_data)

        # Get other options (these don't typically vary by content pack)
        alignments = content_service._hub.alignments.list_all()
        options["alignments"] = [
            alignment.model_dump(mode="json") for alignment in alignments
        ]

        languages = content_service.get_languages()
        options["languages"] = [
            language.model_dump(mode="json") for language in languages
        ]

        skills = content_service._hub.skills.list_all()
        options["skills"] = [skill.model_dump(mode="json") for skill in skills]

        ability_scores = content_service._hub.ability_scores.list_all()
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

    except Exception as e:
        logger.error(f"Error getting character creation options: {e}", exc_info=True)
        return jsonify({"error": "Failed to get character creation options"}), 500


@character_bp.route("/character_templates/<template_id>/adventures")
def get_character_adventures(template_id: str) -> Union[Response, Tuple[Response, int]]:
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
                            game_state = game_state_repo._campaign_saves.get(
                                instance.id
                            )
                        else:
                            game_state = None
                except Exception as e:
                    logger.warning(
                        f"Could not load game state for campaign instance {instance.id}: {e}"
                    )

                # Find the character instance in the game state
                character_data = None
                if game_state and game_state.party:
                    for char_id, character in game_state.party.items():
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
                    from app.domain.characters.factories import CharacterFactory

                    # Get content service instead of loading JSON
                    content_service = get_container().get_content_service()
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

    except Exception as e:
        logger.error(
            f"Error getting character adventures for {template_id}: {e}", exc_info=True
        )
        return jsonify({"error": "Failed to get character adventures"}), 500
