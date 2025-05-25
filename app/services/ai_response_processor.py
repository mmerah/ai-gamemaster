"""
AI response processor service implementation.

This module has been refactored into multiple focused modules for better maintainability.
This file now serves as a compatibility layer to preserve existing imports.
"""
from .response_processors.ai_response_processor_impl import AIResponseProcessorImpl
from .response_processors.dice_request_handler import DiceRequestHandler
from .response_processors.turn_advancement_handler import TurnAdvancementHandler

# Re-export for backward compatibility
__all__ = ['AIResponseProcessorImpl', 'DiceRequestHandler', 'TurnAdvancementHandler']
