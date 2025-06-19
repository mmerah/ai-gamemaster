"""API routes for managing campaign templates."""

import uuid
from typing import Tuple, Union

from flask import Blueprint, Response, jsonify, request
from pydantic import ValidationError

from app.api.dependencies import (
    get_campaign_instance_repository,
    get_campaign_service,
    get_campaign_template_repository,
)
from app.api.error_handlers import with_error_handling
from app.models.campaign import CampaignTemplateModel

campaign_template_bp = Blueprint(
    "campaign_template", __name__, url_prefix="/api/campaign_templates"
)


@campaign_template_bp.route("", methods=["GET"])
@with_error_handling("get_campaign_templates")
def get_campaign_templates() -> Union[Response, Tuple[Response, int]]:
    """Get all campaign templates."""
    template_repo = get_campaign_template_repository()

    templates = template_repo.list()

    # Return in the format expected by frontend (from old /api/campaigns endpoint)
    return jsonify({"campaigns": [template.model_dump() for template in templates]})


@campaign_template_bp.route("/<template_id>", methods=["GET"])
@with_error_handling("get_campaign_template")
def get_campaign_template(template_id: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific campaign template."""
    template_repo = get_campaign_template_repository()

    template = template_repo.get(template_id)

    if not template:
        return jsonify({"error": "Campaign template not found"}), 404

    # Return just the template data (matches old /api/campaigns/<id> format)
    return jsonify(template.model_dump())


@campaign_template_bp.route("", methods=["POST"])
@with_error_handling("create_campaign_template")
def create_campaign_template() -> Union[Response, Tuple[Response, int]]:
    """Create a new campaign template."""
    template_data = request.get_json(force=True, silent=True)

    if not template_data:
        return jsonify({"error": "No template data provided"}), 400

    # Generate ID if not provided
    if "id" not in template_data:
        template_data["id"] = str(uuid.uuid4())

    # Parse and validate with Pydantic
    template = CampaignTemplateModel(**template_data)

    # Save the validated template
    template_repo = get_campaign_template_repository()

    success = template_repo.save(template)

    if not success:
        return jsonify({"error": "Failed to save template"}), 500

    # Return the template data
    return jsonify(template.model_dump()), 201


@campaign_template_bp.route("/<template_id>", methods=["PUT"])
@with_error_handling("update_campaign_template")
def update_campaign_template(template_id: str) -> Union[Response, Tuple[Response, int]]:
    """Update an existing campaign template."""
    template_repo = get_campaign_template_repository()

    # Check if template exists
    existing_template = template_repo.get(template_id)
    if not existing_template:
        return jsonify({"error": "Campaign template not found"}), 404

    template_data = request.get_json(force=True, silent=True)
    if not template_data:
        return jsonify({"error": "No template data provided"}), 400

    # Ensure ID consistency
    template_data["id"] = template_id

    # Parse and validate with Pydantic
    template = CampaignTemplateModel(**template_data)

    # Save the validated template
    success = template_repo.save(template)

    if not success:
        return jsonify({"error": "Failed to update template"}), 500

    # Return the template data
    return jsonify(template.model_dump())


@campaign_template_bp.route("/<template_id>", methods=["DELETE"])
@with_error_handling("delete_campaign_template")
def delete_campaign_template(template_id: str) -> Union[Response, Tuple[Response, int]]:
    """Delete a campaign template."""
    template_repo = get_campaign_template_repository()

    # Check if template exists
    existing_template = template_repo.get(template_id)
    if not existing_template:
        return jsonify({"error": "Campaign template not found"}), 404

    success = template_repo.delete(template_id)

    if not success:
        return jsonify({"error": "Failed to delete template"}), 500

    return jsonify({"message": "Campaign deleted successfully"})


@campaign_template_bp.route("/<template_id>/create_campaign", methods=["POST"])
@with_error_handling("create_campaign_from_template")
def create_campaign_from_template(
    template_id: str,
) -> Union[Response, Tuple[Response, int]]:
    """Create a new campaign from a template."""
    data = request.get_json(force=True, silent=True) or {}
    campaign_name = data.get("campaign_name")
    character_template_ids = data.get("character_template_ids", [])

    if not campaign_name:
        return jsonify({"error": "Campaign name is required"}), 400

    # Optional TTS overrides
    narration_enabled = data.get("narrationEnabled")
    tts_voice = data.get("ttsVoice")

    template_repo = get_campaign_template_repository()
    campaign_service = get_campaign_service()
    instance_repo = get_campaign_instance_repository()

    # Get the template
    template = template_repo.get(template_id)
    if not template:
        return jsonify({"error": "Campaign template not found"}), 404

    # Create the campaign instance using the service
    campaign = campaign_service.create_campaign_instance(
        template_id=template_id,
        instance_name=campaign_name,
        character_ids=character_template_ids,
    )

    if not campaign:
        return jsonify({"error": "Failed to create campaign instance"}), 500

    # Apply TTS overrides if provided
    if narration_enabled is not None or tts_voice is not None:
        # Update the campaign instance with TTS overrides
        if narration_enabled is not None:
            campaign.narration_enabled = narration_enabled
        if tts_voice is not None:
            campaign.tts_voice = tts_voice

        # Save the updated instance
        instance_repo.save(campaign)

    return jsonify({"success": True, "campaign": campaign.model_dump()}), 201
