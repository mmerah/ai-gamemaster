"""
Centralized error handling for API routes.

This module provides unified error handling utilities to eliminate code
duplication across route files and ensure consistent error responses.
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, Union, cast

from flask import Response, jsonify
from pydantic import ValidationError as PydanticValidationError

from app.exceptions import (
    ApplicationError,
    HTTPException,
    ValidationError,
    map_to_http_exception,
)

logger = logging.getLogger(__name__)

# Type variable for return types
T = TypeVar("T")


def handle_pydantic_validation_error(
    operation: str, error: PydanticValidationError
) -> Tuple[Response, int]:
    """
    Handle Pydantic validation errors specifically.

    Args:
        operation: The operation being performed
        error: The Pydantic validation error

    Returns:
        Tuple of (JSON response, HTTP status code)
    """
    # Convert Pydantic errors to our ValidationError format
    validation_errors = {}
    for err in error.errors():
        field = ".".join(str(loc) for loc in err["loc"])
        validation_errors[field] = err["msg"]

    # Create our ValidationError with details
    app_error = ValidationError("Request validation failed", field=None, value=None)
    app_error.details["validation_errors"] = validation_errors

    # Map the error to an appropriate HTTP exception
    http_error = map_to_http_exception(app_error)

    logger.warning(
        f"Validation error in {operation}",
        extra={
            "operation": operation,
            "error_type": "PydanticValidationError",
            "validation_errors": validation_errors,
        },
    )

    return jsonify(http_error.to_dict()), http_error.status_code


def with_error_handling(
    operation: str,
) -> Callable[[Callable[..., T]], Callable[..., Union[T, Tuple[Response, int]]]]:
    """
    Decorator to add consistent error handling to route handlers.

    Usage:
        @app.route('/api/resource')
        @with_error_handling('get_resource')
        def get_resource():
            # Route implementation
            return jsonify(data)

    Args:
        operation: The operation name for logging

    Returns:
        Decorator function
    """

    def decorator(
        func: Callable[..., T],
    ) -> Callable[..., Union[T, Tuple[Response, int]]]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Union[T, Tuple[Response, int]]:
            try:
                return func(*args, **kwargs)
            except PydanticValidationError as e:
                return handle_pydantic_validation_error(operation, e)
            except Exception as e:
                # Map the error to an appropriate HTTP exception
                http_error = map_to_http_exception(e)

                # Log appropriately based on error severity
                if http_error.status_code >= 500:
                    logger.error(
                        f"Error in {operation}: {e}",
                        exc_info=True,
                        extra={
                            "operation": operation,
                            "error_type": type(e).__name__,
                            "error_code": getattr(http_error, "code", None),
                        },
                    )
                else:
                    logger.warning(
                        f"Client error in {operation}: {e}",
                        extra={
                            "operation": operation,
                            "error_type": type(e).__name__,
                            "error_code": getattr(http_error, "code", None),
                        },
                    )

                return jsonify(http_error.to_dict()), http_error.status_code

        return wrapper

    return decorator
