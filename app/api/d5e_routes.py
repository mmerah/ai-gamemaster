"""
D&D 5e reference data API routes.

This module provides a REST API for all D&D 5e data with
flexible query parameter filtering.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import Blueprint, Response, jsonify, request

from app.api.dependencies import get_content_service
from app.api.error_handlers import with_error_handling
from app.content.content_types import get_supported_content_types
from app.content.service import ContentService
from app.exceptions import (
    NotFoundError,
    ValidationError,
)

logger = logging.getLogger(__name__)

# Create blueprint for D&D 5e routes
d5e_bp = Blueprint("d5e", __name__, url_prefix="/api/d5e")


def _serialize_entities(entities: Any) -> Any:
    """Serialize D5e entities to JSON-compatible format."""
    if isinstance(entities, list):
        return [entity.model_dump() for entity in entities]
    elif hasattr(entities, "model_dump"):
        return entities.model_dump()
    return entities


@d5e_bp.route("/content")
@with_error_handling("get_content")
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

    service = get_content_service()

    # Extract common filters
    content_pack_ids = _parse_content_pack_ids(request.args)

    # Delegate to service layer with all query parameters
    # The service will handle type-specific filtering
    filters = dict(request.args)
    filters.pop("type", None)  # Remove type as it's not a filter

    content = service.get_content_filtered(content_type, filters, content_pack_ids)

    return jsonify(_serialize_entities(content))


@d5e_bp.route("/content/<string:content_type>/<string:item_id>")
@with_error_handling("get_content_by_id")
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
    # Validate content type
    supported_types = get_supported_content_types()
    if content_type not in supported_types:
        return jsonify(
            {
                "error": f"Invalid content type '{content_type}'",
                "valid_types": supported_types,
            }
        ), 400

    service = get_content_service()
    content_pack_ids = _parse_content_pack_ids(request.args)

    # Delegate to service layer
    item = service.get_content_by_id(content_type, item_id, content_pack_ids)

    if not item:
        raise NotFoundError(
            f"{content_type.rstrip('s').title()} '{item_id}' not found",
            resource_type=content_type,
        )

    return jsonify(_serialize_entities(item))


@d5e_bp.route("/search")
@with_error_handling("search_all_content")
def search_all_content() -> Union[Response, Tuple[Response, int]]:
    """
    Search across all D&D 5e content.

    Query Parameters:
        q (required): Search query string
        categories: Optional list of content categories to search within

    Returns:
        JSON object with search results organized by category
    """
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    categories_raw = request.args.getlist("categories")
    categories: Optional[List[str]] = categories_raw if categories_raw else None

    service = get_content_service()
    results = service.search_all_content(query, categories)

    # Serialize results
    serialized_results = {}
    for category, entities in results.items():
        serialized_results[category] = _serialize_entities(entities)

    return jsonify(
        {"query": query, "categories": categories, "results": serialized_results}
    )


@d5e_bp.route("/classes/<string:class_id>/levels/<int:level>")
@with_error_handling("get_class_at_level")
def get_class_at_level(
    class_id: str, level: int
) -> Union[Response, Tuple[Response, int]]:
    """
    Get comprehensive class information at a specific level.

    This is a specialized endpoint that cannot be consolidated because it
    involves complex calculations and data aggregation.
    """
    service = get_content_service()
    class_info = service.get_class_at_level(class_id, level)

    if not class_info:
        return jsonify({"error": "Class not found or invalid level"}), 404

    return jsonify(class_info)


@d5e_bp.route("/rule-sections/<string:section>/text")
@with_error_handling("get_rule_section_text")
def get_rule_section_text(section: str) -> Union[Response, Tuple[Response, int]]:
    """
    Get formatted rule text for a specific section.

    This is a specialized endpoint that returns formatted text rather than
    structured data.
    """
    service = get_content_service()
    rule_text = service.get_rule_section(section)

    if not rule_text:
        return jsonify({"error": "Rule section not found"}), 404

    return jsonify({"section": section, "text": rule_text})


@d5e_bp.route("/starting-equipment")
@with_error_handling("get_starting_equipment")
def get_starting_equipment() -> Union[Response, Tuple[Response, int]]:
    """Get starting equipment for a class and background combination."""
    class_name = request.args.get("class_name")
    background_name = request.args.get("background")

    if not class_name or not background_name:
        return jsonify(
            {"error": "Both 'class_name' and 'background' parameters are required"}
        ), 400

    service = get_content_service()
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


@d5e_bp.route("/encounter-budget")
@with_error_handling("get_encounter_budget")
def get_encounter_budget() -> Union[Response, Tuple[Response, int]]:
    """Calculate encounter XP budget for a party."""
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

    service = get_content_service()
    budget = service.get_encounter_xp_budget(party_levels, difficulty)

    return jsonify(
        {
            "party_levels": party_levels,
            "difficulty": difficulty,
            "xp_budget": budget,
        }
    )


@d5e_bp.route("/content-statistics")
@with_error_handling("get_content_statistics")
def get_content_statistics() -> Union[Response, Tuple[Response, int]]:
    """Get statistics about available D&D 5e content."""
    service = get_content_service()
    stats = service.get_content_statistics()
    return jsonify(stats)


def _parse_content_pack_ids(args: Dict[str, Any]) -> Optional[List[str]]:
    """Parse content pack IDs from query parameters."""
    content_pack_ids_param = args.get("content_pack_ids")

    # Return None only if parameter is not present
    # Empty string should still be processed to maintain consistency
    if content_pack_ids_param is None:
        return None

    # If empty string, return None to indicate no filtering
    if not content_pack_ids_param.strip():
        return None

    return [
        pack_id.strip()
        for pack_id in content_pack_ids_param.split(",")
        if pack_id.strip()
    ]
