"""
D&D 5e reference data API routes.

This module provides a REST API for all D&D 5e data with
flexible query parameter filtering.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import Blueprint, Response, jsonify, request

from app.content.content_types import get_supported_content_types
from app.content.service import ContentService
from app.core.container import get_container
from app.exceptions import (
    NotFoundError,
    ValidationError,
    map_to_http_exception,
)

logger = logging.getLogger(__name__)

# Create blueprint for D&D 5e routes
d5e_bp = Blueprint("d5e", __name__, url_prefix="/api/d5e")


def get_d5e_service() -> ContentService:
    """Get the content service from the container."""
    container = get_container()
    return container.get_content_service()


def _handle_service_error(operation: str, error: Exception) -> Tuple[Response, int]:
    """Handle service errors consistently."""
    http_error = map_to_http_exception(error)

    if http_error.status_code >= 500:
        logger.error(
            f"Error in {operation}: {error}",
            exc_info=True,
            extra={"operation": operation, "error_type": type(error).__name__},
        )
    else:
        logger.warning(
            f"Client error in {operation}: {error}",
            extra={"operation": operation, "error_type": type(error).__name__},
        )

    return jsonify(http_error.to_dict()), http_error.status_code


def _serialize_entities(entities: Any) -> Any:
    """Serialize D5e entities to JSON-compatible format."""
    if isinstance(entities, list):
        return [entity.model_dump() for entity in entities]
    elif hasattr(entities, "model_dump"):
        return entities.model_dump()
    return entities


@d5e_bp.route("/content")
def get_content() -> Union[Response, Tuple[Response, int]]:
    """
    Get D&D 5e content with flexible filtering.

    Query Parameters:
        type (required): Content type (e.g., 'spells', 'monsters', 'classes')

        Common filters:
        - content_pack_ids: Comma-separated list of content pack IDs

        Type-specific filters:
        - For spells: level (int), school (str), class_name (str)
        - For monsters: min_cr (float), max_cr (float), type (str), size (str)
        - For languages: type (str)

    Returns:
        JSON array of matching content items

    Examples:
        GET /api/d5e/content?type=spells&level=3&school=evocation
        GET /api/d5e/content?type=monsters&min_cr=1&max_cr=5
        GET /api/d5e/content?type=classes&content_pack_ids=dnd_5e_srd,homebrew
    """
    try:
        # Get and validate content type
        content_type = request.args.get("type")
        if not content_type:
            return jsonify({"error": "Query parameter 'type' is required"}), 400

        supported_types = get_supported_content_types()
        if content_type not in supported_types:
            return jsonify(
                {
                    "error": f"Invalid content type '{content_type}'",
                    "valid_types": supported_types,
                }
            ), 400

        service = get_d5e_service()

        # Extract common filters
        content_pack_ids = _parse_content_pack_ids(request.args)

        # Delegate to service layer with all query parameters
        # The service will handle type-specific filtering
        filters = dict(request.args)
        filters.pop("type", None)  # Remove type as it's not a filter

        content = service.get_content_filtered(content_type, filters, content_pack_ids)

        return jsonify(_serialize_entities(content))

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return _handle_service_error(f"get {content_type} content", e)


@d5e_bp.route("/content/<string:content_type>/<string:item_id>")
def get_content_by_id(
    content_type: str, item_id: str
) -> Union[Response, Tuple[Response, int]]:
    """
    Get a specific D&D 5e content item by ID.

    Path Parameters:
        content_type: The type of content (e.g., 'spells', 'monsters')
        item_id: The unique identifier for the item

    Query Parameters:
        content_pack_ids: Optional comma-separated list of content pack IDs for priority

    Returns:
        JSON object of the requested item

    Examples:
        GET /api/d5e/content/spells/fireball
        GET /api/d5e/content/monsters/aboleth
        GET /api/d5e/content/classes/wizard?content_pack_ids=homebrew,dnd_5e_srd
    """
    try:
        # Validate content type
        supported_types = get_supported_content_types()
        if content_type not in supported_types:
            return jsonify(
                {
                    "error": f"Invalid content type '{content_type}'",
                    "valid_types": supported_types,
                }
            ), 400

        service = get_d5e_service()
        content_pack_ids = _parse_content_pack_ids(request.args)

        # Delegate to service layer
        item = service.get_content_by_id(content_type, item_id, content_pack_ids)

        if not item:
            raise NotFoundError(
                f"{content_type.rstrip('s').title()} '{item_id}' not found",
                resource_type=content_type,
            )

        return jsonify(_serialize_entities(item))

    except NotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return _handle_service_error(f"get {content_type} by id", e)


@d5e_bp.route("/search")
def search_all_content() -> Union[Response, Tuple[Response, int]]:
    """
    Search across all D&D 5e content.

    Query Parameters:
        q (required): Search query string
        categories: Optional list of content categories to search within

    Returns:
        JSON object with search results organized by category
    """
    try:
        query = request.args.get("q")
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400

        categories_raw = request.args.getlist("categories")
        categories: Optional[List[str]] = categories_raw if categories_raw else None

        service = get_d5e_service()
        results = service.search_all_content(query, categories)

        # Serialize results
        serialized_results = {}
        for category, entities in results.items():
            serialized_results[category] = _serialize_entities(entities)

        return jsonify(
            {"query": query, "categories": categories, "results": serialized_results}
        )
    except Exception as e:
        return _handle_service_error("search content", e)


@d5e_bp.route("/character-options")
def get_character_options() -> Union[Response, Tuple[Response, int]]:
    """
    Get combined character creation data.

    Query Parameters:
        content_pack_ids: Optional comma-separated list of content pack IDs

    Returns:
        JSON object with all data needed for character creation
    """
    try:
        service = get_d5e_service()
        content_pack_ids = _parse_content_pack_ids(request.args)

        # Get all character options with optional content pack filtering
        character_options = service.get_character_options(content_pack_ids)

        return jsonify(
            {
                "races": _serialize_entities(character_options["races"]),
                "classes": _serialize_entities(character_options["classes"]),
                "backgrounds": _serialize_entities(character_options["backgrounds"]),
                "ability_scores": _serialize_entities(
                    character_options["ability_scores"]
                ),
                "skills": _serialize_entities(character_options["skills"]),
                "languages": _serialize_entities(character_options["languages"]),
            }
        )
    except Exception as e:
        return _handle_service_error("get character options", e)


@d5e_bp.route("/classes/<string:class_id>/levels/<int:level>")
def get_class_at_level(
    class_id: str, level: int
) -> Union[Response, Tuple[Response, int]]:
    """
    Get comprehensive class information at a specific level.

    This is a specialized endpoint that cannot be consolidated because it
    involves complex calculations and data aggregation.
    """
    try:
        service = get_d5e_service()
        class_info = service.get_class_at_level(class_id, level)

        if not class_info:
            return jsonify({"error": "Class not found or invalid level"}), 404

        return jsonify(class_info)
    except Exception as e:
        return _handle_service_error("get class at level", e)


@d5e_bp.route("/rule-sections/<string:section>/text")
def get_rule_section_text(section: str) -> Union[Response, Tuple[Response, int]]:
    """
    Get formatted rule text for a specific section.

    This is a specialized endpoint that returns formatted text rather than
    structured data.
    """
    try:
        service = get_d5e_service()
        rule_text = service.get_rule_section(section)

        if not rule_text:
            return jsonify({"error": "Rule section not found"}), 404

        return jsonify({"section": section, "text": rule_text})
    except Exception as e:
        return _handle_service_error("get rule section text", e)


@d5e_bp.route("/starting-equipment")
def get_starting_equipment() -> Union[Response, Tuple[Response, int]]:
    """Get starting equipment for a class and background combination."""
    try:
        class_name = request.args.get("class_name")
        background_name = request.args.get("background")

        if not class_name or not background_name:
            return jsonify(
                {"error": "Both 'class_name' and 'background' parameters are required"}
            ), 400

        service = get_d5e_service()
        equipment = service.get_starting_equipment(class_name, background_name)

        return jsonify(
            {
                "class_name": class_name,
                "background": background_name,
                "equipment": {
                    "class": _serialize_entities(equipment["class_"]),
                    "background": _serialize_entities(equipment["background"]),
                },
            }
        )
    except Exception as e:
        return _handle_service_error("get starting equipment", e)


@d5e_bp.route("/encounter-budget")
def get_encounter_budget() -> Union[Response, Tuple[Response, int]]:
    """Calculate encounter XP budget for a party."""
    try:
        levels_str = request.args.get("levels")
        difficulty = request.args.get("difficulty", "medium")

        if not levels_str:
            return jsonify({"error": "Parameter 'levels' is required"}), 400

        try:
            party_levels = [int(level.strip()) for level in levels_str.split(",")]
        except ValueError:
            return jsonify(
                {
                    "error": "Invalid levels format. Use comma-separated integers (e.g., '3,4,5,5')"
                }
            ), 400

        service = get_d5e_service()
        budget = service.get_encounter_xp_budget(party_levels, difficulty)

        return jsonify(
            {
                "party_levels": party_levels,
                "difficulty": difficulty,
                "xp_budget": budget,
            }
        )
    except Exception as e:
        return _handle_service_error("calculate encounter budget", e)


@d5e_bp.route("/content-statistics")
def get_content_statistics() -> Union[Response, Tuple[Response, int]]:
    """Get statistics about available D&D 5e content."""
    try:
        service = get_d5e_service()
        stats = service.get_content_statistics()
        return jsonify(stats)
    except Exception as e:
        return _handle_service_error("get content statistics", e)


def _parse_content_pack_ids(args: Dict[str, Any]) -> Optional[List[str]]:
    """Parse content pack IDs from query parameters."""
    content_pack_ids_param = args.get("content_pack_ids")
    if not content_pack_ids_param:
        return None

    return [
        pack_id.strip()
        for pack_id in content_pack_ids_param.split(",")
        if pack_id.strip()
    ]
