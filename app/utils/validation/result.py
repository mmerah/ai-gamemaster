"""
Validation result classes and utilities.
"""


class ValidationResult:
    """Result of a validation operation."""

    def __init__(
        self, is_valid: bool, error_message: str = "", is_empty_text: bool = False
    ):
        self.is_valid = is_valid
        self.error_message = error_message
        self.is_empty_text = is_empty_text

    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean contexts."""
        return self.is_valid

    def __repr__(self) -> str:
        if self.is_valid:
            return "ValidationResult(valid=True)"
        else:
            return f"ValidationResult(valid=False, error='{self.error_message}')"
