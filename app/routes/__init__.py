"""
Routes package for the AI Game Master application.
"""
import logging
from flask import Flask
from .frontend_routes import frontend_bp
from .game_routes import game_bp
from .campaign_routes import campaign_bp
from .campaign_template_routes import campaign_template_bp
from .character_routes import character_bp
from .d5e_routes import d5e_bp
from .tts_routes import tts_bp
from .sse_routes import sse_bp
from .config_routes import config_bp

logger = logging.getLogger(__name__)

def initialize_routes(app: Flask):
    """Initialize all routes with the Flask app."""
    # Register all blueprints
    app.register_blueprint(frontend_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(campaign_bp)
    app.register_blueprint(campaign_template_bp)
    app.register_blueprint(character_bp)
    app.register_blueprint(d5e_bp)
    app.register_blueprint(tts_bp)
    app.register_blueprint(sse_bp)
    app.register_blueprint(config_bp)
    
    logger.info("All routes initialized.")
