"""
Character template management API routes - FastAPI version.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies_fastapi import (
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
from app.models.character import CharacterTemplateModel

logger = logging.getLogger(__name__)

# Create router for character API routes
router = APIRouter(prefix="/api", tags=["characters"])


def preprocess_character_template(data: Dict[str, Any]) -> Dict[str, Any]:
    """Preprocess character template data from frontend.

    Handles the skill_proficiencies mapping that the frontend sends separately.
    """
    if "skill_proficiencies" in data:
        if "proficiencies" not in data:
            data["proficiencies"] = {}
        data["proficiencies"]["skills"] = data.pop("skill_proficiencies")
    return data


@router.get("/character_templates")
async def get_character_templates(
    character_template_repo: ICharacterTemplateRepository = Depends(
        get_character_template_repository
    ),
) -> Dict[str, Any]:
    """Get all available character templates."""
    try:
        templates = character_template_repo.list()
        # Convert Pydantic models to dict for JSON serialization
        templates_data = [template.model_dump(mode="json") for template in templates]
        return {"templates": templates_data}
    except Exception as e:
        logger.error(f"Failed to fetch character templates: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to fetch character templates"
        )


@router.get("/character_templates/{template_id}")
async def get_character_template(
    template_id: str,
    character_template_repo: ICharacterTemplateRepository = Depends(
        get_character_template_repository
    ),
) -> Dict[str, Any]:
    """Get a specific character template."""
    template = character_template_repo.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Character template not found")

    return template.model_dump()


@router.post("/character_templates", status_code=status.HTTP_201_CREATED)
async def create_character_template(
    template_data: Dict[str, Any],  # Accept raw dict to handle field mappings
    character_template_repo: ICharacterTemplateRepository = Depends(
        get_character_template_repository
    ),
) -> Dict[str, Any]:
    """Create a new character template."""
    try:
        # Generate ID if not provided
        if not template_data.get("id"):
            template_data["id"] = str(uuid.uuid4())

        # Preprocess the data from frontend
        template_data = preprocess_character_template(template_data)

        # Parse and validate with Pydantic
        template = CharacterTemplateModel(**template_data)

        # Save the validated template
        success = character_template_repo.save(template)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to save character template"
            )

        return template.model_dump()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create character template: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create character template"
        )


@router.put("/character_templates/{template_id}")
async def update_character_template(
    template_id: str,
    template_data: Dict[str, Any],  # Accept raw dict to handle field mappings
    character_template_repo: ICharacterTemplateRepository = Depends(
        get_character_template_repository
    ),
) -> Dict[str, Any]:
    """Update an existing character template."""
    # Check if template exists first
    existing_template = character_template_repo.get(template_id)
    if not existing_template:
        raise HTTPException(status_code=404, detail="Character template not found")

    try:
        # Ensure ID consistency
        template_data["id"] = template_id

        # Preprocess the data from frontend
        template_data = preprocess_character_template(template_data)

        # Parse and validate with Pydantic
        template = CharacterTemplateModel(**template_data)

        # Save the validated template
        success = character_template_repo.save(template)
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to update character template"
            )

        return template.model_dump()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update character template: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to update character template"
        )


@router.delete("/character_templates/{template_id}")
async def delete_character_template(
    template_id: str,
    character_template_repo: ICharacterTemplateRepository = Depends(
        get_character_template_repository
    ),
) -> Dict[str, str]:
    """Delete a character template."""
    success = character_template_repo.delete(template_id)
    if not success:
        raise HTTPException(
            status_code=400, detail="Failed to delete character template"
        )

    return {"message": "Character template deleted successfully"}


@router.get("/character_templates/options")
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
) -> Dict[str, Any]:
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

    # Fetch all character creation options with content pack filtering
    options: Dict[str, List[Dict[str, Any]]] = {
        "races": [],
        "classes": [],
        "backgrounds": [],
        "alignments": [],
        "languages": [],
        "skills": [],
        "ability_scores": [],
    }

    # Get races with content pack filtering
    races = content_service.get_races(content_pack_priority=content_pack_priority)
    options["races"] = [race.model_dump(mode="json") for race in races]

    # Get classes with content pack filtering
    classes = content_service.get_classes(content_pack_priority=content_pack_priority)
    options["classes"] = [class_.model_dump(mode="json") for class_ in classes]

    # Get backgrounds with content pack filtering
    backgrounds = content_service.get_backgrounds(
        content_pack_priority=content_pack_priority
    )
    options["backgrounds"] = [
        background.model_dump(mode="json") for background in backgrounds
    ]

    # Get other options with content pack filtering
    alignments = content_service.get_alignments(
        content_pack_priority=content_pack_priority
    )
    options["alignments"] = [
        alignment.model_dump(mode="json") for alignment in alignments
    ]

    languages = content_service.get_languages()
    options["languages"] = [language.model_dump(mode="json") for language in languages]

    skills = content_service.get_skills(content_pack_priority=content_pack_priority)
    options["skills"] = [skill.model_dump(mode="json") for skill in skills]

    ability_scores = content_service.get_ability_scores(
        content_pack_priority=content_pack_priority
    )
    options["ability_scores"] = [
        score.model_dump(mode="json") for score in ability_scores
    ]

    # Add metadata
    response = {
        "options": options,
        "metadata": {
            "content_pack_ids": content_pack_priority,
            "total_races": len(options["races"]),
            "total_classes": len(options["classes"]),
            "total_backgrounds": len(options["backgrounds"]),
        },
    }

    return response


@router.get("/character_templates/{template_id}/adventures")
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
) -> Dict[str, Any]:
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

            adventure_info = {
                "campaign_id": str(instance.id) if instance.id else None,
                "campaign_name": str(instance.name) if instance.name else None,
                "template_id": str(instance.template_id)
                if instance.template_id
                else None,
                "last_played": instance.last_played.isoformat()
                if instance.last_played
                else None,
                "created_date": instance.created_date.isoformat()
                if instance.created_date
                else None,
                "session_count": instance.session_count,
                "current_location": instance.current_location,
                "in_combat": instance.in_combat,
                "character_data": character_data,
            }
            adventures.append(adventure_info)

    return {"character_name": template.name, "adventures": adventures}
