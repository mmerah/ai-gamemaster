"""
Validators for player actions and dice submissions.
"""

from typing import Any, Dict, List, Optional

from app.models import DiceRollSubmissionModel

from .result import ValidationResult


class PlayerActionValidator:
    """Validator for player actions."""

    @staticmethod
    def validate_action(action_data: Optional[Dict[str, Any]]) -> ValidationResult:
        """Validate player action data."""
        if not action_data:
            return ValidationResult(False, "No action data provided")

        action_type = action_data.get("action_type")
        if not action_type:
            return ValidationResult(False, "No action type specified")

        if action_type == "free_text":
            value = action_data.get("value", "").strip()
            if not value:
                return ValidationResult(False, "Empty text action", is_empty_text=True)

        return ValidationResult(True)


class DiceSubmissionValidator:
    """Validator for dice submission data."""

    @staticmethod
    def validate_submission(
        roll_data: Optional[List[DiceRollSubmissionModel]],
    ) -> ValidationResult:
        """Validate dice submission data."""
        if not isinstance(roll_data, list):
            return ValidationResult(
                False, "Invalid data format, expected list of roll requests"
            )

        if not roll_data:
            return ValidationResult(False, "No roll data provided")

        return ValidationResult(True)
