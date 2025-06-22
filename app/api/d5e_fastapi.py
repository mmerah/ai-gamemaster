"""
D&D 5e reference data API routes - FastAPI version.

This module provides a REST API for all D&D 5e data with
flexible query parameter filtering.
"""

import logging
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies_fastapi import get_content_service
from app.content.content_types import get_supported_content_types
from app.content.schemas.types import D5eEntity
from app.core.content_interfaces import IContentService
from app.exceptions import map_to_http_exception

logger = logging.getLogger(__name__)

# Create router for D&D 5e routes
router = APIRouter(prefix="/api/d5e", tags=["d5e"])


def _parse_content_pack_ids(
    content_pack_ids_param: Optional[str],
) -> Optional[List[str]]:
    """Parse content pack IDs from query parameter string."""
    # Return None only if parameter is not present
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


@router.get("/content")
async def get_content(
    request: Request,
    type: str = Query(
        ..., description="Content type (e.g., 'spells', 'monsters', 'classes')"
    ),
    content_pack_ids: Optional[str] = Query(
        None, description="Comma-separated list of content pack IDs"
    ),
    service: IContentService = Depends(get_content_service),
) -> List[D5eEntity]:
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
    # Validate content type
    supported_types = get_supported_content_types()
    if type not in supported_types:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid content type '{type}'",
                "valid_types": supported_types,
            },
        )

    # Parse content pack IDs
    parsed_pack_ids = _parse_content_pack_ids(content_pack_ids)

    # Get all query parameters as filters
    # The service will handle type-specific filtering
    filters = dict(request.query_params)
    filters.pop("type", None)  # Remove type as it's not a filter
    filters.pop("content_pack_ids", None)  # Remove this as it's handled separately

    try:
        content = service.get_content_filtered(type, filters, parsed_pack_ids)
        return content
    except Exception as e:
        logger.error(f"Error fetching content of type '{type}': {e}")
        # Map our custom exceptions to HTTP exceptions
        raise map_to_http_exception(e)
