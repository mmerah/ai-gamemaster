"""
Event type definitions for the game system.
"""

from enum import Enum


class GameEventType(str, Enum):
    """All possible game event types."""

    # Player actions
    PLAYER_ACTION = "player_action"

    # Dice events
    DICE_SUBMISSION = "dice_submission"
    COMPLETED_ROLL_SUBMISSION = "completed_roll_submission"

    # Game flow events
    NEXT_STEP = "next_step"
    RETRY = "retry"

    # Game state events
    GAME_STATE_REQUEST = "game_state_request"
    SAVE_GAME = "save_game"
