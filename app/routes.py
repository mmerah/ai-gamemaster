"""
Flask routes for the AI Game Master application.

This module has been refactored to use modular route blueprints.
All routes are now organized in separate modules within the routes package.
"""

import logging

from app.routes import initialize_routes

logger = logging.getLogger(__name__)

# Export the initialize_routes function for backwards compatibility
__all__ = ["initialize_routes"]
