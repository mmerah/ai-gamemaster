"""
D&D 5e reference data API routes - FastAPI version.

This module provides a REST API for all D&D 5e data with
flexible query parameter filtering.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies_fastapi import get_content_service
from app.content.content_types import get_supported_content_types
from app.core.content_interfaces import IContentService

logger = logging.getLogger(__name__)

# Create router for D&D 5e routes
router = APIRouter(prefix="/api/d5e", tags=["d5e"])


def _serialize_entities(entities: Any) -> Any:
    """Serialize D5e entities to JSON-compatible format."""
    if isinstance(entities, list):
        return [entity.model_dump() for entity in entities]
    elif hasattr(entities, "model_dump"):
        return entities.model_dump()
    return entities


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
) -> List[Dict[str, Any]]:
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
        return _serialize_entities(content)  # type: ignore[no-any-return]
    except Exception as e:
        logger.error(f"Error fetching content of type '{type}': {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch content")


@router.get("/content/{content_type}/{item_id}")
async def get_content_by_id(
    content_type: str,
    item_id: str,
    content_pack_ids: Optional[str] = Query(
        None,
        description="Optional comma-separated list of content pack IDs for priority",
    ),
    service: IContentService = Depends(get_content_service),
) -> Dict[str, Any]:
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
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid content type '{content_type}'",
                "valid_types": supported_types,
            },
        )

    # Parse content pack IDs
    parsed_pack_ids = _parse_content_pack_ids(content_pack_ids)

    try:
        # Delegate to service layer
        item = service.get_content_by_id(content_type, item_id, parsed_pack_ids)

        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"{content_type.rstrip('s').title()} '{item_id}' not found",
            )

        return _serialize_entities(item)  # type: ignore[no-any-return]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching {content_type} with id '{item_id}': {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch content item")


@router.get("/search")
async def search_all_content(
    q: str = Query(..., description="Search query string"),
    categories: List[str] = Query(
        default=[], description="Optional list of content categories to search within"
    ),
    service: IContentService = Depends(get_content_service),
) -> Dict[str, Any]:
    """
    Search across all D&D 5e content.

    Query Parameters:
        q (required): Search query string
        categories: Optional list of content categories to search within

    Returns:
        JSON object with search results organized by category
    """
    try:
        # Convert empty list to None for service layer
        categories_param: Optional[List[str]] = categories if categories else None

        results = service.search_all_content(q, categories_param)

        # Serialize results
        serialized_results = {}
        for category, entities in results.items():
            serialized_results[category] = _serialize_entities(entities)

        return {"query": q, "categories": categories, "results": serialized_results}
    except Exception as e:
        logger.error(f"Error searching content with query '{q}': {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/classes/{class_id}/levels/{level}")
async def get_class_at_level(
    class_id: str,
    level: int,
    service: IContentService = Depends(get_content_service),
) -> Dict[str, Any]:
    """
    Get comprehensive class information at a specific level.

    This is a specialized endpoint that cannot be consolidated because it
    involves complex calculations and data aggregation.
    """
    try:
        class_info = service.get_class_at_level(class_id, level)

        if not class_info:
            raise HTTPException(
                status_code=404, detail="Class not found or invalid level"
            )

        # Class info is already a dict according to service definition
        return class_info  # type: ignore[return-value]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching class '{class_id}' at level {level}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch class information")


@router.get("/rule-sections/{section}/text")
async def get_rule_section_text(
    section: str,
    service: IContentService = Depends(get_content_service),
) -> Dict[str, Any]:
    """
    Get formatted rule text for a specific section.

    This is a specialized endpoint that returns formatted text rather than
    structured data.
    """
    try:
        rule_text = service.get_rule_section(section)

        if not rule_text:
            raise HTTPException(status_code=404, detail="Rule section not found")

        return {"section": section, "text": rule_text}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching rule section '{section}': {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch rule section")


@router.get("/starting-equipment")
async def get_starting_equipment(
    class_name: str = Query(..., description="Character class name"),
    background: str = Query(..., description="Character background"),
    service: IContentService = Depends(get_content_service),
) -> Dict[str, Any]:
    """Get starting equipment for a class and background combination."""
    try:
        equipment = service.get_starting_equipment(class_name, background)

        return {
            "class_name": class_name,
            "background": background,
            "equipment": {
                "class": _serialize_entities(equipment["class_"]),
                "background": _serialize_entities(equipment["background"]),
            },
        }
    except Exception as e:
        logger.error(
            f"Error fetching starting equipment for {class_name}/{background}: {e}"
        )
        raise HTTPException(
            status_code=500, detail="Failed to fetch starting equipment"
        )


@router.get("/encounter-budget")
async def get_encounter_budget(
    levels: str = Query(..., description="Comma-separated list of party member levels"),
    difficulty: str = Query(
        "medium", description="Encounter difficulty (easy, medium, hard, deadly)"
    ),
    service: IContentService = Depends(get_content_service),
) -> Dict[str, Any]:
    """Calculate encounter XP budget for a party."""
    try:
        party_levels = [int(level.strip()) for level in levels.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid levels format. Use comma-separated integers (e.g., '3,4,5,5')",
        )

    try:
        budget = service.get_encounter_xp_budget(party_levels, difficulty)

        return {
            "party_levels": party_levels,
            "difficulty": difficulty,
            "xp_budget": budget,
        }
    except Exception as e:
        logger.error(f"Error calculating encounter budget: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to calculate encounter budget"
        )


@router.get("/content-statistics")
async def get_content_statistics(
    service: IContentService = Depends(get_content_service),
) -> Dict[str, Any]:
    """Get statistics about available D&D 5e content."""
    try:
        stats = service.get_content_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error fetching content statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch content statistics"
        )
