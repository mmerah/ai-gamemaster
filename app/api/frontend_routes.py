"""
Frontend routes for serving the Vue.js SPA.
"""

import os
from typing import Tuple, Union

from flask import Blueprint, Response, jsonify, send_from_directory

# Create blueprint for frontend routes
frontend_bp = Blueprint("frontend", __name__)


@frontend_bp.route("/")
def index() -> Response:
    """Serve the Vue.js SPA."""
    return send_from_directory(
        os.path.join(os.getcwd(), "static", "dist"), "index.html"
    )


# SPA fallback route - catch all other routes and serve the Vue.js app
@frontend_bp.route("/<path:path>")
def spa_fallback(path: str) -> Union[Response, Tuple[Response, int]]:
    """Fallback route for Vue.js SPA client-side routing."""
    # Don't interfere with API routes
    if path.startswith("api/"):
        return jsonify({"error": "API endpoint not found"}), 404
    # Serve the Vue.js app for all other routes
    return send_from_directory(
        os.path.join(os.getcwd(), "static", "dist"), "index.html"
    )
