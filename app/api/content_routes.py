"""
Content pack management API routes.
"""

import json
import logging
from typing import Dict, List, Tuple, Union

from flask import Blueprint, Response, jsonify, request
from pydantic import ValidationError as PydanticValidationError

from app.api.validators import (
    validate_content_type,
    validate_json_size,
    validate_pack_id,
    validate_pagination,
)
from app.content.schemas.content_pack import ContentPackCreate, ContentPackUpdate
from app.content.services.content_pack_service import ContentPackService
from app.content.services.indexing_service import IndexingService
from app.core.container import get_container
from app.exceptions import (
    ContentPackNotFoundError,
    DuplicateEntityError,
    ValidationError,
)

logger = logging.getLogger(__name__)

# Create blueprint for content management API routes
content_bp = Blueprint("content", __name__, url_prefix="/api/content")


def _get_content_pack_service() -> ContentPackService:
    """Get the content pack service from the container.

    Returns:
        ContentPackService instance
    """
    container = get_container()
    return container.get_content_pack_service()


def _get_indexing_service() -> IndexingService:
    """Get the indexing service from the container.

    Returns:
        IndexingService instance
    """
    container = get_container()
    return container.get_indexing_service()


@content_bp.route("/packs")
def get_content_packs() -> Union[Response, Tuple[Response, int]]:
    """Get all content packs.

    Query Parameters:
        active_only: If 'true', only return active packs
    """
    try:
        active_only = request.args.get("active_only", "false").lower() == "true"

        service = _get_content_pack_service()
        packs = service.list_content_packs(active_only=active_only)

        # Convert to dict for JSON serialization
        packs_data = [pack.model_dump(mode="json") for pack in packs]

        return jsonify({"packs": packs_data})

    except Exception as e:
        logger.error(f"Error getting content packs: {e}", exc_info=True)
        return jsonify({"error": "Failed to get content packs"}), 500


@content_bp.route("/packs/<pack_id>")
def get_content_pack(pack_id: str) -> Union[Response, Tuple[Response, int]]:
    """Get a specific content pack."""
    try:
        service = _get_content_pack_service()
        pack = service.get_content_pack(pack_id)

        if not pack:
            return jsonify({"error": f"Content pack '{pack_id}' not found"}), 404

        return jsonify(pack.model_dump(mode="json"))

    except Exception as e:
        logger.error(f"Error getting content pack {pack_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to get content pack"}), 500


@content_bp.route("/packs/<pack_id>/statistics")
def get_content_pack_statistics(pack_id: str) -> Union[Response, Tuple[Response, int]]:
    """Get statistics for a content pack."""
    try:
        service = _get_content_pack_service()
        pack_with_stats = service.get_content_pack_statistics(pack_id)

        return jsonify(pack_with_stats.model_dump(mode="json"))

    except ContentPackNotFoundError:
        return jsonify({"error": f"Content pack '{pack_id}' not found"}), 404
    except Exception as e:
        logger.error(f"Error getting pack statistics: {e}", exc_info=True)
        return jsonify({"error": "Failed to get content pack statistics"}), 500


@content_bp.route("/packs", methods=["POST"])
def create_content_pack() -> Union[Response, Tuple[Response, int]]:
    """Create a new content pack."""
    try:
        # Check content size
        if not validate_json_size(request.content_length):
            return jsonify({"error": "Request too large (max 10MB)"}), 413

        # Check content type
        if request.content_type != "application/json":
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json(silent=False)
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Parse and validate with Pydantic
        pack_create = ContentPackCreate(**data)

        # Create the pack
        service = _get_content_pack_service()
        pack = service.create_content_pack(pack_create)

        return jsonify(pack.model_dump(mode="json")), 201

    except PydanticValidationError as e:
        logger.error(f"Validation error creating content pack: {e}")
        return jsonify({"error": "Validation error", "details": e.errors()}), 422
    except DuplicateEntityError as e:
        logger.error(f"Content pack already exists: {e}")
        return jsonify({"error": str(e)}), 409
    except ValidationError as e:
        logger.error(f"Business validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating content pack: {e}", exc_info=True)
        return jsonify({"error": "Failed to create content pack"}), 500


@content_bp.route("/packs/<pack_id>", methods=["PUT"])
def update_content_pack(pack_id: str) -> Union[Response, Tuple[Response, int]]:
    """Update an existing content pack."""
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            return jsonify({"error": "Invalid pack ID format"}), 400
        # Check content size
        if not validate_json_size(request.content_length):
            return jsonify({"error": "Request too large (max 10MB)"}), 413

        # Check content type
        if request.content_type != "application/json":
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json(silent=False)
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Parse and validate with Pydantic
        pack_update = ContentPackUpdate(**data)

        # Update the pack
        service = _get_content_pack_service()
        pack = service.update_content_pack(pack_id, pack_update)

        return jsonify(pack.model_dump(mode="json"))

    except PydanticValidationError as e:
        logger.error(f"Validation error updating content pack: {e}")
        return jsonify({"error": "Validation error", "details": e.errors()}), 422
    except ContentPackNotFoundError:
        return jsonify({"error": f"Content pack '{pack_id}' not found"}), 404
    except ValidationError as e:
        logger.error(f"Business validation error: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating content pack: {e}", exc_info=True)
        return jsonify({"error": "Failed to update content pack"}), 500


@content_bp.route("/packs/<pack_id>/activate", methods=["POST"])
def activate_content_pack(pack_id: str) -> Union[Response, Tuple[Response, int]]:
    """Activate a content pack."""
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            return jsonify({"error": "Invalid pack ID format"}), 400
        service = _get_content_pack_service()
        pack = service.activate_content_pack(pack_id)

        return jsonify(pack.model_dump(mode="json"))

    except ContentPackNotFoundError:
        return jsonify({"error": f"Content pack '{pack_id}' not found"}), 404
    except Exception as e:
        logger.error(f"Error activating content pack: {e}", exc_info=True)
        return jsonify({"error": "Failed to activate content pack"}), 500


@content_bp.route("/packs/<pack_id>/deactivate", methods=["POST"])
def deactivate_content_pack(pack_id: str) -> Union[Response, Tuple[Response, int]]:
    """Deactivate a content pack."""
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            return jsonify({"error": "Invalid pack ID format"}), 400
        service = _get_content_pack_service()
        pack = service.deactivate_content_pack(pack_id)

        return jsonify(pack.model_dump(mode="json"))

    except ContentPackNotFoundError:
        return jsonify({"error": f"Content pack '{pack_id}' not found"}), 404
    except ValidationError as e:
        logger.error(f"Cannot deactivate system pack: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error deactivating content pack: {e}", exc_info=True)
        return jsonify({"error": "Failed to deactivate content pack"}), 500


@content_bp.route("/packs/<pack_id>", methods=["DELETE"])
def delete_content_pack(pack_id: str) -> Union[Response, Tuple[Response, int]]:
    """Delete a content pack and all its content."""
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            return jsonify({"error": "Invalid pack ID format"}), 400
        service = _get_content_pack_service()
        success = service.delete_content_pack(pack_id)

        if success:
            return jsonify(
                {"message": f"Content pack '{pack_id}' deleted successfully"}
            ), 200
        else:
            return jsonify({"error": "Failed to delete content pack"}), 500

    except ContentPackNotFoundError:
        return jsonify({"error": f"Content pack '{pack_id}' not found"}), 404
    except ValidationError as e:
        logger.error(f"Cannot delete system pack: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error deleting content pack: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete content pack"}), 500


@content_bp.route("/packs/<pack_id>/upload/<content_type>", methods=["POST"])
def upload_content(
    pack_id: str, content_type: str
) -> Union[Response, Tuple[Response, int]]:
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
            return jsonify({"error": "Invalid pack ID format"}), 400
        if not validate_content_type(content_type):
            return jsonify({"error": "Invalid content type format"}), 400

        # Check content size
        if not validate_json_size(request.content_length):
            return jsonify({"error": "Request too large (max 10MB)"}), 413

        # Verify pack exists
        service = _get_content_pack_service()
        pack = service.get_content_pack(pack_id)
        if not pack:
            return jsonify({"error": f"Content pack '{pack_id}' not found"}), 404

        # Validate content type against supported types
        supported_types = service.get_supported_content_types()
        if content_type not in supported_types:
            return jsonify({"error": f"Unsupported content type: {content_type}"}), 400

        # Get content data
        if request.content_type != "application/json":
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json(silent=False)
        if not data:
            return jsonify({"error": "No content data provided"}), 400

        # Upload and save the content
        result = service.upload_content(pack_id, content_type, data)

        # If upload successful, trigger indexing
        if result.failed_items == 0:
            try:
                indexing_service = _get_indexing_service()
                indexed_count = indexing_service.index_content_pack(pack_id)
                result.warnings.append(
                    f"Indexing triggered for {sum(indexed_count.values())} items."
                )
            except Exception as e:
                logger.warning(f"Failed to trigger indexing: {e}")
                result.warnings.append("Content saved but indexing failed")

        # Return result
        status_code = 200 if result.failed_items == 0 else 422
        return jsonify(result.model_dump()), status_code

    except ValidationError as e:
        logger.error(f"Invalid content type: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error uploading content: {e}", exc_info=True)
        return jsonify({"error": "Failed to upload content"}), 500


@content_bp.route("/packs/<pack_id>/content")
def get_content_pack_content(pack_id: str) -> Union[Response, Tuple[Response, int]]:
    """Get content items from a content pack.

    Query Parameters:
        content_type: Optional specific content type to fetch (e.g., 'spells')
        offset: Pagination offset (default: 0)
        limit: Maximum items to return (default: 50)
    """
    try:
        # Validate pack_id
        if not validate_pack_id(pack_id):
            return jsonify({"error": "Invalid pack ID format"}), 400

        # Parse and validate query parameters
        content_type = request.args.get("content_type")
        if content_type and not validate_content_type(content_type):
            return jsonify({"error": "Invalid content type format"}), 400

        try:
            offset, limit = validate_pagination(
                request.args.get("offset"), request.args.get("limit")
            )
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        service = _get_content_pack_service()
        result = service.get_content_pack_items(
            pack_id=pack_id, content_type=content_type, offset=offset, limit=limit
        )

        return jsonify(result)

    except ContentPackNotFoundError:
        return jsonify({"error": f"Content pack '{pack_id}' not found"}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting content pack items: {e}", exc_info=True)
        return jsonify({"error": "Failed to get content pack items"}), 500


@content_bp.route("/supported-types")
def get_supported_content_types() -> Union[Response, Tuple[Response, int]]:
    """Get a list of supported content types for upload."""
    try:
        service = _get_content_pack_service()
        types = service.get_supported_content_types()

        return jsonify({"types": types})

    except Exception as e:
        logger.error(f"Error getting supported types: {e}", exc_info=True)
        return jsonify({"error": "Failed to get supported content types"}), 500
