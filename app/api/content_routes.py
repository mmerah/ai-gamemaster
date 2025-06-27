"""
Content pack management API routes - FastAPI version.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.api.dependencies import (
    get_campaign_instance_repository,
    get_character_template_repository,
    get_content_pack_service,
    get_game_state_repository,
    get_indexing_service,
    get_rag_service,
)
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
from app.core.ai_interfaces import IRAGService
from app.core.content_interfaces import IContentPackService, IIndexingService
from app.core.repository_interfaces import (
    ICampaignInstanceRepository,
    ICharacterTemplateRepository,
    IGameStateRepository,
)
from app.exceptions import map_to_http_exception
from app.models.api.requests import (
    ContentUploadRequest,
    RAGQueryRequest,
)
from app.models.api.responses import (
    ContentPackItemsResponse,
    ContentPackUsageStatistics,
    ContentUploadResponse,
    RAGQueryResponse,
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


@router.get("/packs/usage-statistics", response_model=List[ContentPackUsageStatistics])
async def get_content_pack_usage_statistics(
    content_pack_service: IContentPackService = Depends(get_content_pack_service),
    character_repo: ICharacterTemplateRepository = Depends(
        get_character_template_repository
    ),
) -> List[ContentPackUsageStatistics]:
    """Get usage statistics for all content packs (how many characters use each pack)."""
    try:
        # Get all content packs
        content_packs = content_pack_service.list_content_packs(active_only=False)

        # Get all character templates
        character_templates = character_repo.list()

        # Count usage for each content pack
        usage_stats = []
        for pack in content_packs:
            character_count = sum(
                1
                for template in character_templates
                if pack.id in template.content_pack_ids
            )

            usage_stats.append(
                ContentPackUsageStatistics(
                    pack_id=pack.id,
                    pack_name=pack.name,
                    character_count=character_count,
                )
            )

        # Sort by usage count (highest first)
        usage_stats.sort(key=lambda x: x.character_count, reverse=True)
        return usage_stats

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


@router.post("/rag/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    rag_service: IRAGService = Depends(get_rag_service),
    campaign_repo: ICampaignInstanceRepository = Depends(
        get_campaign_instance_repository
    ),
    game_state_repo: IGameStateRepository = Depends(get_game_state_repository),
) -> RAGQueryResponse:
    """Query the RAG system for testing purposes.

    This endpoint allows testing RAG queries with different configurations:
    - Override content pack priority
    - Override game context (combat state, location, etc.)
    - Filter by knowledge base types
    - Control number of results
    """
    try:
        # Initialize default values
        content_packs = ["System"]  # Default to System pack
        game_state = None

        # If campaign_id is provided, try to load campaign data
        if request.campaign_id:
            campaign = campaign_repo.get(request.campaign_id)
            if campaign:
                content_packs = campaign.content_pack_priority

                # Try to load game state for the campaign
                if hasattr(game_state_repo, "load_campaign_state"):
                    game_state = game_state_repo.load_campaign_state(
                        request.campaign_id
                    )

        # If no game state loaded, create a minimal one for testing
        if not game_state:
            from app.models.game_state.main import GameStateModel
            from app.models.utils import LocationModel

            # Create minimal game state for RAG testing
            game_state = GameStateModel(
                event_summary=[],
                session_count=0,
                in_combat=False,
                current_location=LocationModel(
                    name="Testing Environment",
                    description="A neutral testing environment for RAG queries",
                ),
                content_pack_priority=content_packs,
            )

        # Apply overrides if provided
        if request.override_content_packs:
            content_packs = request.override_content_packs

        # Use override game state if provided
        if request.override_game_state:
            game_state = request.override_game_state

        # Execute RAG query
        results = rag_service.get_relevant_knowledge(
            action=request.query,
            game_state=game_state,
            content_pack_priority=content_packs,
        )

        # Build response with debug info
        return RAGQueryResponse(
            results=results,
            query_info={
                "action": request.query,
                "kb_types": request.kb_types,
                "max_results": request.max_results,
                "game_context": {
                    "in_combat": game_state.in_combat,
                    "current_location": game_state.current_location.name
                    if game_state.current_location
                    else None,
                    "active_lore_id": game_state.active_lore_id,
                },
            },
            used_content_packs=content_packs,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG query error: {str(e)}", exc_info=True)
        http_error = map_to_http_exception(e)
        raise HTTPException(
            status_code=http_error.status_code, detail=http_error.to_dict()
        )
