"""
Custom exception handlers for FastAPI with consistent error response format.
"""

import logging
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
    Custom handler for HTTPException to maintain consistent error format.

    Converts {"detail": "message"} to {"error": "message"} for API consistency.
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
    logger = logging.getLogger(__name__)

    # Cast to RequestValidationError to access attributes
    if not isinstance(exc, RequestValidationError):
        # Should not happen, but handle gracefully
        return JSONResponse(
            status_code=400,
            content={"error": "Bad request"},
        )

    # Log detailed validation error information
    errors = exc.errors()
    logger.error(f"Request validation failed for {request.method} {request.url.path}")
    logger.error(f"Validation errors: {errors}")

    # Try to log the request body for debugging
    try:
        body = await request.body()
        logger.error(
            f"Request body: {body.decode('utf-8')[:1000]}..."
        )  # Log first 1000 chars
    except Exception as e:
        logger.error(f"Could not read request body: {e}")

    # Extract first error for simple message
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


async def application_exception_handler(
    request: Request, exc: Exception
) -> Union[Response, JSONResponse]:
    """
    Custom handler for ApplicationError and its subclasses.

    Maps our custom exceptions to appropriate HTTP responses while preserving
    error details.
    """
    from app.exceptions import ApplicationError, map_to_http_exception

    if not isinstance(exc, ApplicationError):
        # Should not happen, but handle gracefully
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )

    # Map to HTTP exception to get proper status code
    http_exc = map_to_http_exception(exc)

    # Build response content from the ApplicationError
    content = exc.to_dict()

    return JSONResponse(
        status_code=http_exc.status_code,
        content=content,
    )
