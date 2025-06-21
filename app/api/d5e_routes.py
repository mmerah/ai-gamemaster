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
