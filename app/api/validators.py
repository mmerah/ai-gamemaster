"""Input validation utilities for API routes.

This module provides validation functions for user input to prevent
security vulnerabilities like injection attacks.
"""

import re
from typing import Optional


def validate_pack_id(pack_id: str) -> bool:
    """Validate that a pack ID contains only safe characters.

    Args:
        pack_id: The pack ID to validate

    Returns:
        True if valid, False otherwise
    """
    # Allow only alphanumeric, hyphens, and underscores
    # Max length 100 to prevent DoS
    if not pack_id or len(pack_id) > 100:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", pack_id))


def validate_content_type(content_type: str) -> bool:
    """Validate that a content type contains only safe characters.

    Args:
        content_type: The content type to validate

    Returns:
        True if valid, False otherwise
    """
    # Allow only lowercase letters, hyphens
    # Max length 50 to prevent DoS
    if not content_type or len(content_type) > 50:
        return False
    return bool(re.match(r"^[a-z-]+$", content_type))


def validate_pagination(offset: Optional[str], limit: Optional[str]) -> tuple[int, int]:
    """Validate and parse pagination parameters.

    Args:
        offset: String offset value
        limit: String limit value

    Returns:
        Tuple of (offset, limit) as integers

    Raises:
        ValueError: If parameters are invalid
    """
    try:
        offset_int = int(offset or "0")
        limit_int = int(limit or "50")
    except (ValueError, OverflowError) as e:
        raise ValueError("Invalid pagination parameters") from e

    # Validate ranges
    if offset_int < 0:
        raise ValueError("Offset must be non-negative")
    if offset_int > 1000000:  # Prevent excessive offset
        raise ValueError("Offset too large")

    if limit_int < 1:
        raise ValueError("Limit must be positive")
    if limit_int > 1000:
        raise ValueError("Limit must be between 1 and 1000")

    return offset_int, limit_int


def validate_json_size(
    content_length: Optional[int], max_size: int = 10 * 1024 * 1024
) -> bool:
    """Validate request content size.

    Args:
        content_length: Content-Length header value
        max_size: Maximum allowed size in bytes (default 10MB)

    Returns:
        True if valid, False if too large
    """
    if content_length is None:
        return True  # No content-length header, will be limited by Flask
    return content_length <= max_size
