"""API routes for managing campaign templates - FastAPI version."""

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.api.dependencies_fastapi import (
    get_campaign_instance_repository,
    get_campaign_service,
    get_campaign_template_repository,
)
from app.core.domain_interfaces import ICampaignService
from app.core.repository_interfaces import (
    ICampaignInstanceRepository,
    ICampaignTemplateRepository,
)
from app.models.campaign import CampaignTemplateModel

router = APIRouter(prefix="/api/campaign_templates", tags=["campaign_templates"])


@router.get("")
async def get_campaign_templates(
    template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
) -> Dict[str, List[Dict[str, Any]]]:
    """Get all campaign templates."""
    try:
        templates = template_repo.list()

        # Return in the format expected by frontend (from old /api/campaigns endpoint)
        return {"campaigns": [template.model_dump() for template in templates]}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch campaign templates: {str(e)}"
        )


@router.get("/{template_id}")
async def get_campaign_template(
    template_id: str,
    template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
) -> Dict[str, Any]:
    """Get a specific campaign template."""
    try:
        template = template_repo.get(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Campaign template not found")

        # Return just the template data (matches old /api/campaigns/<id> format)
        return template.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch campaign template: {str(e)}"
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_campaign_template(
    template_data: Dict[str, Any],
    template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
) -> Dict[str, Any]:
    """Create a new campaign template."""
    try:
        # Generate ID if not provided
        if "id" not in template_data:
            template_data["id"] = str(uuid.uuid4())

        # Parse and validate with Pydantic
        template = CampaignTemplateModel(**template_data)

        # Save the validated template
        success = template_repo.save(template)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save template")

        # Return the template data
        return template.model_dump()

    except ValidationError as e:
        # Convert Pydantic validation errors to HTTP 400
        error_details = []
        for err in e.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            error_details.append(f"{field}: {err['msg']}")

        raise HTTPException(
            status_code=400, detail=f"Validation error: {'; '.join(error_details)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create campaign template: {str(e)}"
        )


@router.put("/{template_id}")
async def update_campaign_template(
    template_id: str,
    template_data: Dict[str, Any],
    template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
) -> Dict[str, Any]:
    """Update an existing campaign template."""
    try:
        # Check if template exists
        existing_template = template_repo.get(template_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Campaign template not found")

        # Ensure ID consistency
        template_data["id"] = template_id

        # Parse and validate with Pydantic
        template = CampaignTemplateModel(**template_data)

        # Save the validated template
        success = template_repo.save(template)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update template")

        # Return the template data
        return template.model_dump()

    except ValidationError as e:
        # Convert Pydantic validation errors to HTTP 400
        error_details = []
        for err in e.errors():
            field = ".".join(str(loc) for loc in err["loc"])
            error_details.append(f"{field}: {err['msg']}")

        raise HTTPException(
            status_code=400, detail=f"Validation error: {'; '.join(error_details)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update campaign template: {str(e)}"
        )


@router.delete("/{template_id}")
async def delete_campaign_template(
    template_id: str,
    template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
) -> Dict[str, str]:
    """Delete a campaign template."""
    try:
        # Check if template exists
        existing_template = template_repo.get(template_id)
        if not existing_template:
            raise HTTPException(status_code=404, detail="Campaign template not found")

        success = template_repo.delete(template_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete template")

        return {"message": "Campaign deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete campaign template: {str(e)}"
        )


@router.post("/{template_id}/create_campaign", status_code=status.HTTP_201_CREATED)
async def create_campaign_from_template(
    template_id: str,
    request_data: Dict[str, Any],
    template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
    campaign_service: ICampaignService = Depends(get_campaign_service),
    instance_repo: ICampaignInstanceRepository = Depends(
        get_campaign_instance_repository
    ),
) -> Dict[str, Any]:
    """Create a new campaign from a template."""
    try:
        campaign_name = request_data.get("campaign_name")
        character_template_ids = request_data.get("character_template_ids", [])

        if not campaign_name:
            raise HTTPException(status_code=400, detail="Campaign name is required")

        # Optional TTS overrides
        narration_enabled = request_data.get("narrationEnabled")
        tts_voice = request_data.get("ttsVoice")

        # Get the template
        template = template_repo.get(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Campaign template not found")

        # Create the campaign instance using the service
        campaign = campaign_service.create_campaign_instance(
            template_id=template_id,
            instance_name=campaign_name,
            character_ids=character_template_ids,
        )

        if not campaign:
            raise HTTPException(
                status_code=500, detail="Failed to create campaign instance"
            )

        # Apply TTS overrides if provided
        if narration_enabled is not None or tts_voice is not None:
            # Update the campaign instance with TTS overrides
            if narration_enabled is not None:
                campaign.narration_enabled = narration_enabled
            if tts_voice is not None:
                campaign.tts_voice = tts_voice

            # Save the updated instance
            instance_repo.save(campaign)

        return {"success": True, "campaign": campaign.model_dump()}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create campaign from template: {str(e)}"
        )
