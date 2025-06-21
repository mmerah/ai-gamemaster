"""
Content pack management API routes - FastAPI version.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import ValidationError as PydanticValidationError

from app.api.dependencies_fastapi import get_content_pack_service, get_indexing_service
from app.api.validators import (
    validate_content_type,
    validate_json_size,
    validate_pack_id,
    validate_pagination,
)
from app.content.schemas.content_pack import ContentPackCreate, ContentPackUpdate
from app.core.content_interfaces import IContentPackService, IIndexingService
from app.exceptions import (
    ApplicationError,
    ContentPackNotFoundError,
    map_to_http_exception,
)

logger = logging.getLogger(__name__)

# Create router for content management API routes
router = APIRouter(prefix="/api/content", tags=["content"])


@router.get("/packs")
async def get_content_packs(
    active_only: bool = Query(False, description="If true, only return active packs"),
    service: IContentPackService = Depends(get_content_pack_service),
) -> Dict[str, Any]:
    """Get all content packs.

    Query Parameters:
        active_only: If 'true', only return active packs
    """
    try:
        packs = service.list_content_packs(active_only=active_only)

        # Convert to dict for JSON serialization
        packs_data = [pack.model_dump(mode="json") for pack in packs]

        return {"packs": packs_data}
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.get("/packs/{pack_id}")
async def get_content_pack(
    pack_id: str,
    service: IContentPackService = Depends(get_content_pack_service),
) -> Dict[str, Any]:
    """Get a specific content pack."""
    try:
        pack = service.get_content_pack(pack_id)

        if not pack:
            raise HTTPException(
                status_code=404, detail={"error": f"Content pack '{pack_id}' not found"}
            )

        return pack.model_dump(mode="json")  # type: ignore[no-any-return]
    except HTTPException:
        raise
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.get("/packs/{pack_id}/statistics")
async def get_content_pack_statistics(
    pack_id: str,
    service: IContentPackService = Depends(get_content_pack_service),
) -> Dict[str, Any]:
    """Get statistics for a content pack."""
    try:
        pack_with_stats = service.get_content_pack_statistics(pack_id)
        return pack_with_stats.model_dump(mode="json")  # type: ignore[no-any-return]
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.post("/packs", status_code=201)
async def create_content_pack(
    data: Dict[str, Any],
    content_length: Optional[int] = Header(None),
    service: IContentPackService = Depends(get_content_pack_service),
) -> Dict[str, Any]:
    """Create a new content pack."""
    try:
        # Check content size
        if not validate_json_size(content_length):
            raise HTTPException(
                status_code=413, detail={"error": "Request too large (max 10MB)"}
            )

        if not data:
            raise HTTPException(status_code=400, detail={"error": "No data provided"})

        # Parse and validate with Pydantic
        pack_create = ContentPackCreate(**data)

        # Create the pack
        pack = service.create_content_pack(pack_create)

        return pack.model_dump(mode="json")  # type: ignore[no-any-return]
    except PydanticValidationError as e:
        # Convert Pydantic errors to validation error format
        validation_errors = {}
        for err in e.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            validation_errors[field] = err["msg"]

        raise HTTPException(
            status_code=422,
            detail={
                "error": "Request validation failed",
                "validation_errors": validation_errors,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.put("/packs/{pack_id}")
async def update_content_pack(
    pack_id: str,
    data: Dict[str, Any],
    content_length: Optional[int] = Header(None),
    service: IContentPackService = Depends(get_content_pack_service),
) -> Dict[str, Any]:
    """Update an existing content pack."""
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            raise HTTPException(
                status_code=400, detail={"error": "Invalid pack ID format"}
            )

        # Check content size
        if not validate_json_size(content_length):
            raise HTTPException(
                status_code=413, detail={"error": "Request too large (max 10MB)"}
            )

        if not data:
            raise HTTPException(status_code=400, detail={"error": "No data provided"})

        # Parse and validate with Pydantic
        pack_update = ContentPackUpdate(**data)

        # Update the pack
        pack = service.update_content_pack(pack_id, pack_update)

        return pack.model_dump(mode="json")  # type: ignore[no-any-return]
    except PydanticValidationError as e:
        # Convert Pydantic errors to validation error format
        validation_errors = {}
        for err in e.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            validation_errors[field] = err["msg"]

        raise HTTPException(
            status_code=422,
            detail={
                "error": "Request validation failed",
                "validation_errors": validation_errors,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.post("/packs/{pack_id}/activate")
async def activate_content_pack(
    pack_id: str,
    service: IContentPackService = Depends(get_content_pack_service),
) -> Dict[str, Any]:
    """Activate a content pack."""
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            raise HTTPException(
                status_code=400, detail={"error": "Invalid pack ID format"}
            )

        pack = service.activate_content_pack(pack_id)
        return pack.model_dump(mode="json")  # type: ignore[no-any-return]
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.post("/packs/{pack_id}/deactivate")
async def deactivate_content_pack(
    pack_id: str,
    service: IContentPackService = Depends(get_content_pack_service),
) -> Dict[str, Any]:
    """Deactivate a content pack."""
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            raise HTTPException(
                status_code=400, detail={"error": "Invalid pack ID format"}
            )

        pack = service.deactivate_content_pack(pack_id)
        return pack.model_dump(mode="json")  # type: ignore[no-any-return]
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.delete("/packs/{pack_id}")
async def delete_content_pack(
    pack_id: str,
    service: IContentPackService = Depends(get_content_pack_service),
) -> Dict[str, Any]:
    """Delete a content pack and all its content."""
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            raise HTTPException(
                status_code=400, detail={"error": "Invalid pack ID format"}
            )

        success = service.delete_content_pack(pack_id)

        if success:
            return {"message": f"Content pack '{pack_id}' deleted successfully"}
        else:
            raise HTTPException(
                status_code=500, detail={"error": "Failed to delete content pack"}
            )
    except HTTPException:
        raise
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.post("/packs/{pack_id}/upload/{content_type}")
async def upload_content(
    pack_id: str,
    content_type: str,
    data: Union[List[Dict[str, Any]], Dict[str, Any]],
    content_length: Optional[int] = Header(None),
    service: IContentPackService = Depends(get_content_pack_service),
    indexing_service: IIndexingService = Depends(get_indexing_service),
) -> Dict[str, Any]:
    """Upload content to a content pack.

    Accepts JSON data containing one or more items of the specified content type.
    The data will be validated and imported into the content pack.

    Args:
        pack_id: The content pack ID to upload to
        content_type: The type of content (e.g., 'spells', 'monsters')

    Request Body:
        JSON array of content items or a single content item
    """
    try:
        # Validate inputs
        if not validate_pack_id(pack_id):
            raise HTTPException(
                status_code=400, detail={"error": "Invalid pack ID format"}
            )
        if not validate_content_type(content_type):
            raise HTTPException(
                status_code=400, detail={"error": "Invalid content type format"}
            )

        # Check content size
        if not validate_json_size(content_length):
            raise HTTPException(
                status_code=413, detail={"error": "Request too large (max 10MB)"}
            )

        # Verify pack exists
        pack = service.get_content_pack(pack_id)
        if not pack:
            raise HTTPException(
                status_code=404, detail={"error": f"Content pack '{pack_id}' not found"}
            )

        # Validate content type against supported types
        supported_types = service.get_supported_content_types()
        if content_type not in supported_types:
            raise HTTPException(
                status_code=400,
                detail={"error": f"Unsupported content type: {content_type}"},
            )

        if not data:
            raise HTTPException(
                status_code=400, detail={"error": "No content data provided"}
            )

        # Upload and save the content
        result = service.upload_content(pack_id, content_type, data)

        # If upload successful, trigger indexing
        if result.failed_items == 0:
            try:
                indexed_count = indexing_service.index_content_pack(pack_id)
                result.warnings.append(
                    f"Indexing triggered for {sum(indexed_count.values())} items."
                )
            except Exception as e:
                logger.warning(f"Failed to trigger indexing: {e}")
                result.warnings.append("Content saved but indexing failed")

        # Return result
        status_code = 200 if result.failed_items == 0 else 422
        if status_code == 422:
            raise HTTPException(status_code=status_code, detail=result.model_dump())
        return result.model_dump()  # type: ignore[no-any-return]
    except HTTPException:
        raise
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.get("/packs/{pack_id}/content")
async def get_content_pack_content(
    pack_id: str,
    content_type: Optional[str] = Query(
        None, description="Specific content type to fetch"
    ),
    offset: Optional[str] = Query(None, description="Pagination offset"),
    limit: Optional[str] = Query(None, description="Maximum items to return"),
    service: IContentPackService = Depends(get_content_pack_service),
) -> Dict[str, Any]:
    """Get content items from a content pack.

    Query Parameters:
        content_type: Optional specific content type to fetch (e.g., 'spells')
        offset: Pagination offset (default: 0)
        limit: Maximum items to return (default: 50)
    """
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            raise HTTPException(
                status_code=400, detail={"error": "Invalid pack ID format"}
            )

        # Parse and validate query parameters
        if content_type and not validate_content_type(content_type):
            raise HTTPException(
                status_code=400, detail={"error": "Invalid content type format"}
            )

        try:
            offset_int, limit_int = validate_pagination(offset, limit)
        except ValueError as e:
            raise HTTPException(status_code=400, detail={"error": str(e)})

        result = service.get_content_pack_items(
            pack_id=pack_id,
            content_type=content_type,
            offset=offset_int,
            limit=limit_int,
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.get("/supported-types")
async def get_supported_content_types(
    service: IContentPackService = Depends(get_content_pack_service),
) -> Dict[str, Any]:
    """Get a list of supported content types for upload."""
    try:
        types = service.get_supported_content_types()
        return {"types": types}
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )
