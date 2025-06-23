"""
Character template management API routes - FastAPI version.
"""

import logging
import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    get_campaign_instance_repository,
    get_campaign_template_repository,
    get_character_template_repository,
    get_content_service,
    get_game_state_repository,
)
from app.core.content_interfaces import IContentService
from app.core.repository_interfaces import (
    ICampaignInstanceRepository,
    ICampaignTemplateRepository,
    ICharacterTemplateRepository,
    IGameStateRepository,
)
from app.models.api import (
    AdventureCharacterData,
    AdventureInfo,
    CharacterAdventuresResponse,
    CharacterCreationOptionsData,
    CharacterCreationOptionsMetadata,
    CharacterCreationOptionsResponse,
    SuccessResponse,
)
from app.models.character import CharacterTemplateModel
from app.models.character.template import CharacterTemplateUpdateModel

logger = logging.getLogger(__name__)

# Create router for character API routes
router = APIRouter(prefix="/api", tags=["characters"])


@router.get("/character_templates", response_model=List[CharacterTemplateModel])
async def get_character_templates(
    character_template_repo: ICharacterTemplateRepository = Depends(
        get_character_template_repository
    ),
) -> List[CharacterTemplateModel]:
    """Get all available character templates."""
    try:
        templates = character_template_repo.list()
        return templates
    except Exception as e:
        logger.error(f"Failed to fetch character templates: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch character templates"
        )


@router.get("/character_templates/{template_id}", response_model=CharacterTemplateModel)
async def get_character_template(
    template_id: str,
    character_template_repo: ICharacterTemplateRepository = Depends(
        get_character_template_repository
    ),
) -> CharacterTemplateModel:
    """Get a specific character template."""
    template = character_template_repo.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Character template not found")

    return template


@router.post(
    "/character_templates",
    status_code=status.HTTP_201_CREATED,
    response_model=CharacterTemplateModel,
)
async def create_character_template(
    request: CharacterTemplateModel,
    character_template_repo: ICharacterTemplateRepository = Depends(
        get_character_template_repository
    ),
) -> CharacterTemplateModel:
    """Create a new character template."""
    try:
        # Generate ID if not provided
        if not request.id:
            request.id = str(uuid.uuid4())

        # Save the validated template
        success = character_template_repo.save(request)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to save character template"
            )

        return request

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create character template: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create character template"
        )


@router.put("/character_templates/{template_id}", response_model=CharacterTemplateModel)
async def update_character_template(
    template_id: str,
    request: CharacterTemplateUpdateModel,
    character_template_repo: ICharacterTemplateRepository = Depends(
        get_character_template_repository
    ),
) -> CharacterTemplateModel:
    """Update an existing character template."""
    # Check if template exists first
    existing_template = character_template_repo.get(template_id)
    if not existing_template:
        raise HTTPException(status_code=404, detail="Character template not found")

    try:
        # Update only provided fields
        update_data = request.model_dump(exclude_unset=True)
        updated_template = existing_template.model_copy(update=update_data)

        # Save the validated template
        success = character_template_repo.save(updated_template)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to update character template"
            )

        return updated_template

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update character template: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update character template"
        )


@router.delete("/character_templates/{template_id}", response_model=SuccessResponse)
async def delete_character_template(
    template_id: str,
    character_template_repo: ICharacterTemplateRepository = Depends(
        get_character_template_repository
    ),
) -> SuccessResponse:
    """Delete a character template."""
    success = character_template_repo.delete(template_id)
    if not success:
        raise HTTPException(
            status_code=400, detail="Failed to delete character template"
        )

    return SuccessResponse(
        success=True, message="Character template deleted successfully"
    )


@router.get(
    "/character_templates/options", response_model=CharacterCreationOptionsResponse
)
async def get_character_creation_options(
    content_pack_ids: Optional[str] = Query(
        None, description="Comma-separated list of content pack IDs to filter by"
    ),
    campaign_id: Optional[str] = Query(
        None, description="Campaign ID to automatically get content pack priority from"
    ),
    content_service: IContentService = Depends(get_content_service),
    campaign_template_repo: ICampaignTemplateRepository = Depends(
        get_campaign_template_repository
    ),
    campaign_instance_repo: ICampaignInstanceRepository = Depends(
        get_campaign_instance_repository
    ),
) -> CharacterCreationOptionsResponse:
    """
    Get character creation options filtered by content packs.

    Query Parameters:
        content_pack_ids: Comma-separated list of content pack IDs to filter by
        campaign_id: Campaign ID to automatically get content pack priority from

    Returns:
        JSON object with races, classes, backgrounds, alignments, languages, skills
        filtered by the specified content packs
    """
    # Get content pack priority
    content_pack_priority: Optional[List[str]] = None

    # Option 1: Direct content pack IDs
    if content_pack_ids:
        content_pack_priority = [
            pack_id.strip()
            for pack_id in content_pack_ids.split(",")
            if pack_id.strip()
        ]

    # Option 2: Get from campaign
    if campaign_id and not content_pack_priority:
        # Get campaign template to find content pack priority
        # First try to get from instance
        campaign_instance = campaign_instance_repo.get(campaign_id)
        if campaign_instance and campaign_instance.content_pack_priority:
            content_pack_priority = campaign_instance.content_pack_priority
        elif campaign_instance and campaign_instance.template_id:
            # Fall back to template's content packs
            campaign_template = campaign_template_repo.get(
                campaign_instance.template_id
            )
            if campaign_template and campaign_template.content_pack_ids:
                content_pack_priority = campaign_template.content_pack_ids

    # Default to all content if no filtering specified
    if not content_pack_priority:
        content_pack_priority = []  # Empty list means all content

    # Get races with content pack filtering
    races = content_service.get_races(content_pack_priority=content_pack_priority)

    # Get classes with content pack filtering
    classes = content_service.get_classes(content_pack_priority=content_pack_priority)

    # Get backgrounds with content pack filtering
    backgrounds = content_service.get_backgrounds(
        content_pack_priority=content_pack_priority
    )

    # Get other options with content pack filtering
    alignments = content_service.get_alignments(
        content_pack_priority=content_pack_priority
    )

    languages = content_service.get_languages()

    skills = content_service.get_skills(content_pack_priority=content_pack_priority)

    ability_scores = content_service.get_ability_scores(
        content_pack_priority=content_pack_priority
    )

    # Create response models
    options = CharacterCreationOptionsData(
        races=races,
        classes=classes,
        backgrounds=backgrounds,
        alignments=alignments,
        languages=languages,
        skills=skills,
        ability_scores=ability_scores,
    )

    metadata = CharacterCreationOptionsMetadata(
        content_pack_ids=content_pack_priority,
        total_races=len(races),
        total_classes=len(classes),
        total_backgrounds=len(backgrounds),
    )

    return CharacterCreationOptionsResponse(options=options, metadata=metadata)


@router.get(
    "/character_templates/{template_id}/adventures",
    response_model=CharacterAdventuresResponse,
)
async def get_character_adventures(
    template_id: str,
    character_template_repo: ICharacterTemplateRepository = Depends(
        get_character_template_repository
    ),
    campaign_instance_repo: ICampaignInstanceRepository = Depends(
        get_campaign_instance_repository
    ),
    game_state_repo: IGameStateRepository = Depends(get_game_state_repository),
    content_service: IContentService = Depends(get_content_service),
) -> CharacterAdventuresResponse:
    """Get all campaigns this character is participating in."""
    # Verify character template exists
    template = character_template_repo.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Character template not found")

    # Get all campaign instances
    campaign_instances = campaign_instance_repo.list()
    adventures = []

    # Check each campaign instance for this character
    for instance in campaign_instances:
        # Check if this character is in the campaign's party
        if template_id in instance.character_ids:
            # Try to load the game state for this campaign
            game_state = None
            try:
                # Try to load the game state for this campaign instance
                # For file-based repositories, we can temporarily switch campaigns
                if hasattr(game_state_repo, "set_campaign"):
                    original_campaign_id = getattr(
                        game_state_repo, "_current_campaign_id", None
                    )
                    game_state_repo.set_campaign(instance.id)
                    game_state = game_state_repo.get_game_state()
                    if original_campaign_id:
                        game_state_repo.set_campaign(original_campaign_id)
                else:
                    # For in-memory repositories, try to get from campaign saves
                    if hasattr(game_state_repo, "_campaign_saves"):
                        game_state = game_state_repo._campaign_saves.get(instance.id)
                    else:
                        game_state = None
            except Exception as e:
                logger.warning(
                    f"Could not load game state for campaign instance {instance.id}: {e}"
                )

            # Find the character instance in the game state
            character_data = None
            if game_state and game_state.party:
                for _, character in game_state.party.items():
                    if character.template_id == template_id:
                        character_data = {
                            "current_hp": int(character.current_hp)
                            if hasattr(character, "current_hp")
                            else 0,
                            "max_hp": int(character.max_hp)
                            if hasattr(character, "max_hp")
                            else 0,
                            "level": int(character.level)
                            if hasattr(character, "level")
                            else 1,
                            "class": str(character.char_class)
                            if hasattr(character, "char_class")
                            else "Unknown",
                            "experience": int(getattr(character, "experience", 0)),
                        }
                        break

            # If no character data from game state, calculate proper defaults
            if not character_data:
                # Use the character factory to calculate proper HP
                from app.domain.characters.character_factory import CharacterFactory

                # CharacterFactory should accept the interface
                factory = CharacterFactory(content_service)

                # Calculate proper HP based on class and constitution
                max_hp = factory._calculate_character_hit_points(template)

                character_data = {
                    "current_hp": max_hp,
                    "max_hp": max_hp,
                    "level": template.level,
                    "class": template.char_class,
                    "experience": 0,
                }

            # Create typed character data
            typed_character_data = AdventureCharacterData(**character_data)

            # Create typed adventure info
            adventure_info = AdventureInfo(
                campaign_id=str(instance.id) if instance.id else None,
                campaign_name=str(instance.name) if instance.name else None,
                template_id=str(instance.template_id) if instance.template_id else None,
                last_played=instance.last_played.isoformat()
                if instance.last_played
                else None,
                created_date=instance.created_date.isoformat()
                if instance.created_date
                else None,
                session_count=instance.session_count,
                current_location=instance.current_location,
                in_combat=instance.in_combat,
                character_data=typed_character_data,
            )
            adventures.append(adventure_info)

    return CharacterAdventuresResponse(
        character_name=template.name, adventures=adventures
    )
