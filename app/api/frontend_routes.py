"""
Frontend routes for serving the Vue.js SPA and static assets.
"""

import mimetypes
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


@frontend_bp.route("/campaigns")
def campaign_manager() -> Response:
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return send_from_directory(
        os.path.join(os.getcwd(), "static", "dist"), "index.html"
    )


@frontend_bp.route("/campaign-manager")
def campaign_manager_alt() -> Response:
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return send_from_directory(
        os.path.join(os.getcwd(), "static", "dist"), "index.html"
    )


@frontend_bp.route("/game")
def game() -> Response:
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return send_from_directory(
        os.path.join(os.getcwd(), "static", "dist"), "index.html"
    )


@frontend_bp.route("/characters")
def characters() -> Response:
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return send_from_directory(
        os.path.join(os.getcwd(), "static", "dist"), "index.html"
    )


@frontend_bp.route("/configuration")
def configuration() -> Response:
    """Serve the Vue.js SPA (client-side routing will handle this)."""
    return send_from_directory(
        os.path.join(os.getcwd(), "static", "dist"), "index.html"
    )


# Serve Vue.js static assets
@frontend_bp.route("/static/dist/<path:filename>")
def serve_vue_assets(filename: str) -> Response:
    """Serve Vue.js built assets."""
    # Set correct MIME type for JavaScript files
    if filename.endswith(".js"):
        mimetype = "application/javascript"
    elif filename.endswith(".css"):
        mimetype = "text/css"
    else:
        mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    response = send_from_directory(
        os.path.join(os.getcwd(), "static", "dist"), filename
    )
    response.headers["Content-Type"] = mimetype
    return response


# Serve Vite assets (JS/CSS files in /assets/ folder)
@frontend_bp.route("/assets/<path:filename>")
def serve_vite_assets(filename: str) -> Response:
    """Serve Vite-generated assets with correct MIME types."""
    # Set correct MIME type for JavaScript files
    if filename.endswith(".js"):
        mimetype = "application/javascript"
    elif filename.endswith(".css"):
        mimetype = "text/css"
    else:
        mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    response = send_from_directory(
        os.path.join(os.getcwd(), "static", "dist", "assets"), filename
    )
    response.headers["Content-Type"] = mimetype
    return response


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
