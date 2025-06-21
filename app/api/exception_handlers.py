"""
Custom exception handlers for FastAPI to maintain Flask compatibility.
"""

from typing import Any, Dict, Union

from fastapi import Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.responses import Response


async def http_exception_handler(
    request: Request, exc: Exception
) -> Union[Response, JSONResponse]:
    """
    Custom handler for HTTPException to maintain Flask error format.

    Converts {"detail": "message"} to {"error": "message"} for compatibility.
    """
    # Cast to HTTPException to access attributes
    if not isinstance(exc, HTTPException):
        # Should not happen, but handle gracefully
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )

    # Get the detail message with explicit typing to help mypy
    detail: Union[str, Dict[str, Any], Any] = exc.detail

    # Determine content based on detail type
    content: Dict[str, Any]
    if isinstance(detail, str):
        # If detail is a string, wrap it in error key
        content = {"error": detail}
    elif isinstance(detail, dict):
        # If detail is a dict, check if it already has "error" key
        if "error" in detail:
            content = detail
        else:
            # Wrap dict in error key
            content = {"error": detail}
    else:
        # For any other type, convert to string and wrap
        content = {"error": str(detail)}

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> Union[Response, JSONResponse]:
    """
    Custom handler for request validation errors.

    Provides user-friendly error messages for Pydantic validation failures.
    """
    # Cast to RequestValidationError to access attributes
    if not isinstance(exc, RequestValidationError):
        # Should not happen, but handle gracefully
        return JSONResponse(
            status_code=400,
            content={"error": "Bad request"},
        )

    # Extract first error for simple message
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        loc = " -> ".join(str(x) for x in first_error["loc"])
        msg = f"Validation error in {loc}: {first_error['msg']}"
    else:
        msg = "Request validation failed"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": msg, "validation_errors": errors},
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: Exception
) -> Union[Response, JSONResponse]:
    """
    Custom handler for Pydantic validation errors.

    This handles model validation errors in route handlers.
    """
    # Cast to ValidationError to access attributes
    if not isinstance(exc, ValidationError):
        # Should not happen, but handle gracefully
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid request data"},
        )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid request data", "details": exc.errors()},
    )
