"""API routes for managing campaign templates - FastAPI version."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.api.dependencies import (
    get_campaign_instance_repository,
    get_campaign_service,
    get_campaign_template_repository,
)
from app.core.domain_interfaces import ICampaignService
from app.core.repository_interfaces import (
    ICampaignInstanceRepository,
    ICampaignTemplateRepository,
)
from app.models.api import (
    CreateCampaignFromTemplateRequest,
    CreateCampaignFromTemplateResponse,
    SuccessResponse,
)
from app.models.campaign.template import (
    CampaignOptionItem,
    CampaignOptionsResponse,
    CampaignTemplateModel,
    CampaignTemplateUpdateModel,
)

router = APIRouter(prefix="/api/campaign_templates", tags=["campaign_templates"])


@router.get("/options", response_model=CampaignOptionsResponse)
async def get_campaign_options() -> CampaignOptionsResponse:
    """Get available options for campaign templates."""
    import json
    import os

    # Load available lores from the knowledge base
    lore_options = []
    lore_file_path = os.path.join(
        os.path.dirname(__file__), "..", "content", "data", "knowledge", "lores.json"
    )

    if os.path.exists(lore_file_path):
        with open(lore_file_path, "r", encoding="utf-8") as f:
            lore_data = json.load(f)
            lore_options = [
                CampaignOptionItem(value=lore["id"], label=lore["name"])
                for lore in lore_data
            ]

    # Create response with difficulties (using defaults from model) and lores
    return CampaignOptionsResponse(
        lores=lore_options,
        # difficulties will use the defaults defined in the model
    )


@router.get("", response_model=List[CampaignTemplateModel])
async def get_campaign_templates(
    template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
) -> List[CampaignTemplateModel]:
    """Get all campaign templates."""
    try:
        templates = template_repo.list()
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch campaign templates: {str(e)}"
        )


@router.get("/{template_id}", response_model=CampaignTemplateModel)
async def get_campaign_template(
    template_id: str,
    template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
) -> CampaignTemplateModel:
    """Get a specific campaign template."""
    try:
        template = template_repo.get(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Campaign template not found")

        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch campaign template: {str(e)}"
        )


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=CampaignTemplateModel
)
async def create_campaign_template(
    template: CampaignTemplateModel,
    template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
) -> CampaignTemplateModel:
    """Create a new campaign template."""
    try:
        # Generate ID if not provided
        if not template.id:
            template.id = str(uuid.uuid4())

        # Save the validated template
        success = template_repo.save(template)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save template")

        return template

    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create campaign template: {str(e)}"
        )


@router.put("/{template_id}", response_model=CampaignTemplateModel)
async def update_campaign_template(
    template_id: str,
    request: CampaignTemplateUpdateModel,
    template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
) -> CampaignTemplateModel:
    """Update an existing campaign template."""
    try:
        # Check if template exists
        existing_template = template_repo.get(template_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Campaign template not found")

        # Update only provided fields
        update_data = request.model_dump(exclude_unset=True)
        updated_template = existing_template.model_copy(update=update_data)

        # Save the updated template
        success = template_repo.save(updated_template)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update template")

        return updated_template

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update campaign template: {str(e)}"
        )


@router.delete("/{template_id}", response_model=SuccessResponse)
async def delete_campaign_template(
    template_id: str,
    template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
) -> SuccessResponse:
    """Delete a campaign template."""
    try:
        # Check if template exists
        existing_template = template_repo.get(template_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Campaign template not found")

        success = template_repo.delete(template_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete template")

        return SuccessResponse(success=True, message="Campaign deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete campaign template: {str(e)}"
        )


@router.post(
    "/{template_id}/create_campaign",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateCampaignFromTemplateResponse,
)
async def create_campaign_from_template(
    template_id: str,
    request: CreateCampaignFromTemplateRequest,
    template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
    campaign_service: ICampaignService = Depends(get_campaign_service),
    instance_repo: ICampaignInstanceRepository = Depends(
        get_campaign_instance_repository
    ),
) -> CreateCampaignFromTemplateResponse:
    """Create a new campaign from a template."""
    try:
        # Get the template
        template = template_repo.get(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Campaign template not found")

        # Use provided character IDs or get from request
        character_ids = request.character_ids or []

        # Create the campaign instance using the service
        campaign = campaign_service.create_campaign_instance(
            template_id=template_id,
            instance_name=request.campaign_name,
            character_ids=character_ids,
            character_levels=request.character_levels,
        )

        if not campaign:
            raise HTTPException(
                status_code=500, detail="Failed to create campaign instance"
            )

        # Apply TTS overrides if provided
        if request.narration_enabled is not None or request.tts_voice is not None:
            # Update the campaign instance with TTS overrides
            if request.narration_enabled is not None:
                campaign.narration_enabled = request.narration_enabled
            if request.tts_voice is not None:
                campaign.tts_voice = request.tts_voice

            # Save the updated instance
            instance_repo.save(campaign)

        return CreateCampaignFromTemplateResponse(
            success=True,
            campaign=campaign,
            message=f"Campaign '{request.campaign_name}' created successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create campaign from template: {str(e)}"
        )
