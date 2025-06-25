"""
Content pack management API routes - FastAPI version.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.api.dependencies import get_content_pack_service, get_indexing_service
from app.api.validators import (
    validate_content_type,
    validate_json_size,
    validate_pack_id,
    validate_pagination,
)
from app.content.schemas.content_pack import (
    ContentPackCreate,
    ContentPackUpdate,
    ContentPackWithStats,
    D5eContentPack,
)
from app.content.schemas.content_types import ContentTypeInfo
from app.core.content_interfaces import IContentPackService, IIndexingService
from app.exceptions import map_to_http_exception
from app.models.api import (
    ContentPackItemsResponse,
    ContentUploadRequest,
    ContentUploadResponse,
    SuccessResponse,
)

logger = logging.getLogger(__name__)

# Create router for content management API routes
router = APIRouter(prefix="/api/content", tags=["content"])


@router.get("/packs", response_model=List[D5eContentPack])
async def get_content_packs(
    active_only: bool = Query(False, description="If true, only return active packs"),
    service: IContentPackService = Depends(get_content_pack_service),
) -> List[D5eContentPack]:
    """Get all content packs.

    Query Parameters:
        active_only: If 'true', only return active packs
    """
    try:
        packs = service.list_content_packs(active_only=active_only)
        return packs
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.get("/packs/{pack_id}", response_model=D5eContentPack)
async def get_content_pack(
    pack_id: str,
    service: IContentPackService = Depends(get_content_pack_service),
) -> D5eContentPack:
    """Get a specific content pack."""
    try:
        pack = service.get_content_pack(pack_id)

        if not pack:
            raise HTTPException(
                status_code=404, detail={"error": f"Content pack '{pack_id}' not found"}
            )

        return pack
    except HTTPException:
        raise
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.get("/packs/{pack_id}/statistics", response_model=ContentPackWithStats)
async def get_content_pack_statistics(
    pack_id: str,
    service: IContentPackService = Depends(get_content_pack_service),
) -> ContentPackWithStats:
    """Get statistics for a content pack."""
    try:
        return service.get_content_pack_statistics(pack_id)
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.post("/packs", status_code=201, response_model=D5eContentPack)
async def create_content_pack(
    pack_create: ContentPackCreate,
    content_length: Optional[int] = Header(None),
    service: IContentPackService = Depends(get_content_pack_service),
) -> D5eContentPack:
    """Create a new content pack."""
    try:
        # Check content size
        if not validate_json_size(content_length):
            raise HTTPException(
                status_code=413, detail={"error": "Request too large (max 10MB)"}
            )

        # Create the pack
        pack = service.create_content_pack(pack_create)
        return pack
    except HTTPException:
        raise
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.put("/packs/{pack_id}", response_model=D5eContentPack)
async def update_content_pack(
    pack_id: str,
    pack_update: ContentPackUpdate,
    content_length: Optional[int] = Header(None),
    service: IContentPackService = Depends(get_content_pack_service),
) -> D5eContentPack:
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

        # Update the pack
        pack = service.update_content_pack(pack_id, pack_update)
        return pack
    except HTTPException:
        raise
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.post("/packs/{pack_id}/activate", response_model=SuccessResponse)
async def activate_content_pack(
    pack_id: str,
    service: IContentPackService = Depends(get_content_pack_service),
) -> SuccessResponse:
    """Activate a content pack."""
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            raise HTTPException(
                status_code=400, detail={"error": "Invalid pack ID format"}
            )

        pack = service.activate_content_pack(pack_id)
        return SuccessResponse(
            success=True, message=f"Content pack '{pack.name}' activated successfully"
        )
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.post("/packs/{pack_id}/deactivate", response_model=SuccessResponse)
async def deactivate_content_pack(
    pack_id: str,
    service: IContentPackService = Depends(get_content_pack_service),
) -> SuccessResponse:
    """Deactivate a content pack."""
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            raise HTTPException(
                status_code=400, detail={"error": "Invalid pack ID format"}
            )

        pack = service.deactivate_content_pack(pack_id)
        return SuccessResponse(
            success=True, message=f"Content pack '{pack.name}' deactivated successfully"
        )
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.delete("/packs/{pack_id}", response_model=SuccessResponse)
async def delete_content_pack(
    pack_id: str,
    service: IContentPackService = Depends(get_content_pack_service),
) -> SuccessResponse:
    """Delete a content pack and all its content."""
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            raise HTTPException(
                status_code=400, detail={"error": "Invalid pack ID format"}
            )

        success = service.delete_content_pack(pack_id)

        if success:
            return SuccessResponse(
                success=True, message=f"Content pack '{pack_id}' deleted successfully"
            )
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


@router.post(
    "/packs/{pack_id}/upload/{content_type}", response_model=ContentUploadResponse
)
async def upload_content(
    pack_id: str,
    content_type: str,
    request: ContentUploadRequest,
    content_length: Optional[int] = Header(None),
    service: IContentPackService = Depends(get_content_pack_service),
    indexing_service: IIndexingService = Depends(get_indexing_service),
) -> ContentUploadResponse:
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
        supported_type_ids = [ct.type_id for ct in supported_types]
        if content_type not in supported_type_ids:
            raise HTTPException(
                status_code=400,
                detail={"error": f"Unsupported content type: {content_type}"},
            )

        # Convert request items to raw data for service
        # Service expects list of dicts, not our typed models
        items = request.items if isinstance(request.items, list) else [request.items]
        data = [item.model_dump() for item in items]

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

        # Convert ContentUploadResult to ContentUploadResponse
        response = ContentUploadResponse(
            success=result.failed_items == 0,
            uploaded_count=result.successful_items,
            failed_count=result.failed_items,
            results=[],  # We don't have individual item results in the current implementation
        )

        if result.failed_items > 0:
            # Return with 422 status via exception
            raise HTTPException(status_code=422, detail=response.model_dump())
        return response
    except HTTPException:
        raise
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.get("/packs/{pack_id}/content", response_model=ContentPackItemsResponse)
async def get_content_pack_content(
    pack_id: str,
    content_type: Optional[str] = Query(
        None, description="Specific content type to fetch"
    ),
    offset: Optional[str] = Query(None, description="Pagination offset"),
    limit: Optional[str] = Query(None, description="Maximum items to return"),
    service: IContentPackService = Depends(get_content_pack_service),
) -> ContentPackItemsResponse:
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

        # Convert result dict to response model
        return ContentPackItemsResponse(
            items=result.get("items", []),
            total=result.get("total"),
            totals=result.get("totals"),
            page=result.get("page"),
            per_page=result.get("per_page"),
            content_type=result.get("content_type", content_type),
            offset=result.get("offset", offset_int),
            limit=result.get("limit", limit_int),
        )
    except HTTPException:
        raise
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )


@router.get("/supported-types", response_model=List[ContentTypeInfo])
async def get_supported_content_types(
    service: IContentPackService = Depends(get_content_pack_service),
) -> List[ContentTypeInfo]:
    """Get a list of supported content types for upload."""
    try:
        return service.get_supported_content_types()
    except Exception as e:
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )
