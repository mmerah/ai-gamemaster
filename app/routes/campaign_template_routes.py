"""API routes for managing campaign templates."""

import uuid
from typing import Tuple, Union

from flask import Blueprint, Response, jsonify, request
from pydantic import ValidationError

from app.core.container import get_container
from app.models.models import CampaignTemplateModel

campaign_template_bp = Blueprint(
    "campaign_template", __name__, url_prefix="/api/campaign_templates"
)


@campaign_template_bp.route("", methods=["GET"])
def get_campaign_templates() -> Union[Response, Tuple[Response, int]]:
    """Get all campaign templates."""
    container = get_container()
    template_repo = container.get_campaign_template_repository()

    templates = template_repo.get_all_templates()

    # Return in the format expected by frontend (from old /api/campaigns endpoint)
    return jsonify({"campaigns": [template.model_dump() for template in templates]})


@campaign_template_bp.route("/<template_id>", methods=["GET"])
def get_campaign_template(template_id: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific campaign template."""
    container = get_container()
    template_repo = container.get_campaign_template_repository()

    template = template_repo.get_template(template_id)

    if not template:
        return jsonify({"error": "Campaign template not found"}), 404

    # Return just the template data (matches old /api/campaigns/<id> format)
    return jsonify(template.model_dump())


@campaign_template_bp.route("", methods=["POST"])
def create_campaign_template() -> Union[Response, Tuple[Response, int]]:
    """Create a new campaign template."""
    try:
        template_data = request.get_json(force=True, silent=True)

        if not template_data:
            return jsonify({"error": "No template data provided"}), 400

        # Generate ID if not provided
        if "id" not in template_data:
            template_data["id"] = str(uuid.uuid4())

        # Parse and validate with Pydantic
        template = CampaignTemplateModel(**template_data)

        # Save the validated template
        container = get_container()
        template_repo = container.get_campaign_template_repository()

        success = template_repo.save_template(template)

        if not success:
            return jsonify({"error": "Failed to save template"}), 500

        # Return the template data
        return jsonify(template.model_dump()), 201

    except ValidationError as e:
        return jsonify({"error": e.errors()}), 422
    except Exception as e:
        return jsonify({"error": f"Failed to create campaign template: {e!s}"}), 500


@campaign_template_bp.route("/<template_id>", methods=["PUT"])
def update_campaign_template(template_id: str) -> Union[Response, Tuple[Response, int]]:
    """Update an existing campaign template."""
    try:
        container = get_container()
        template_repo = container.get_campaign_template_repository()

        # Check if template exists
        existing_template = template_repo.get_template(template_id)
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
        success = template_repo.save_template(template)

        if not success:
            return jsonify({"error": "Failed to update template"}), 500

        # Return the template data
        return jsonify(template.model_dump())

    except ValidationError as e:
        return jsonify({"error": e.errors()}), 422
    except Exception as e:
        return jsonify({"error": f"Failed to update campaign template: {e!s}"}), 500


@campaign_template_bp.route("/<template_id>", methods=["DELETE"])
def delete_campaign_template(template_id: str) -> Union[Response, Tuple[Response, int]]:
    """Delete a campaign template."""
    container = get_container()
    template_repo = container.get_campaign_template_repository()

    # Check if template exists
    existing_template = template_repo.get_template(template_id)
    if not existing_template:
        return jsonify({"error": "Campaign template not found"}), 404

    success = template_repo.delete_template(template_id)

    if not success:
        return jsonify({"error": "Failed to delete template"}), 500

    return jsonify({"message": "Campaign deleted successfully"})


@campaign_template_bp.route("/<template_id>/create_campaign", methods=["POST"])
def create_campaign_from_template(
    template_id: str,
) -> Union[Response, Tuple[Response, int]]:
    """Create a new campaign from a template."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        campaign_name = data.get("campaign_name")
        character_template_ids = data.get("character_template_ids", [])

        if not campaign_name:
            return jsonify({"error": "Campaign name is required"}), 400

        # Optional TTS overrides
        narration_enabled = data.get("narrationEnabled")
        tts_voice = data.get("ttsVoice")

        container = get_container()
        template_repo = container.get_campaign_template_repository()
        campaign_service = container.get_campaign_service()
        instance_repo = container.get_campaign_instance_repository()

        # Get the template
        template = template_repo.get_template(template_id)
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
            instance_repo.update_instance(campaign)

        return jsonify({"success": True, "campaign": campaign.model_dump()}), 201

    except ValidationError as e:
        return jsonify({"error": e.errors()}), 422
    except Exception as e:
        return jsonify({"error": f"Failed to create campaign: {e!s}"}), 500
