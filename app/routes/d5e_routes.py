"""
D&D 5e reference data API routes.
"""

import json
import logging
import os
from typing import Tuple, Union

from flask import Blueprint, Response, jsonify

logger = logging.getLogger(__name__)

# Create blueprint for D&D 5e reference data routes
d5e_bp = Blueprint("d5e", __name__, url_prefix="/api/d5e")


@d5e_bp.route("/races")
def get_d5e_races() -> Union[Response, Tuple[Response, int]]:
    """Get D&D 5e race data."""
    try:
        races_file = os.path.join("saves", "d5e_data", "races.json")
        if not os.path.exists(races_file):
            return jsonify({"error": "D&D 5e race data not found"}), 404

        with open(races_file, encoding="utf-8") as f:
            races_data = json.load(f)

        return jsonify(races_data)

    except Exception as e:
        logger.error(f"Error getting D&D 5e races: {e}", exc_info=True)
        return jsonify({"error": "Failed to get D&D 5e races"}), 500


@d5e_bp.route("/classes")
def get_d5e_classes() -> Union[Response, Tuple[Response, int]]:
    """Get D&D 5e class data."""
    try:
        classes_file = os.path.join("saves", "d5e_data", "classes.json")
        if not os.path.exists(classes_file):
            return jsonify({"error": "D&D 5e class data not found"}), 404

        with open(classes_file, encoding="utf-8") as f:
            classes_data = json.load(f)

        return jsonify(classes_data)

    except Exception as e:
        logger.error(f"Error getting D&D 5e classes: {e}", exc_info=True)
        return jsonify({"error": "Failed to get D&D 5e classes"}), 500
