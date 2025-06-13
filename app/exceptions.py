"""Custom exceptions for the AI Game Master application.

This module defines domain-specific exceptions for better error handling
and clarity throughout the application.
"""

from typing import Any, Dict, Optional, Union


class ApplicationError(Exception):
    """Base exception class for all application errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the application error.

        Args:
            message: Human-readable error message
            code: Optional error code for programmatic handling
            details: Optional dictionary with additional error details
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for API responses.

        Returns:
            Dictionary representation of the error
        """
        result: Dict[str, Any] = {"error": self.message}
        if self.code:
            result["code"] = self.code
        if self.details:
            result["details"] = self.details
        return result


class DatabaseError(ApplicationError):
    """Base class for database-related errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code=code or "DATABASE_ERROR", details=details)


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""

    def __init__(
        self,
        message: str = "Failed to connect to database",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code="DB_CONNECTION_ERROR", details=details)


class SessionError(DatabaseError):
    """Raised when database session operations fail."""

    def __init__(
        self,
        message: str = "Database session error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code="DB_SESSION_ERROR", details=details)


class EntityNotFoundError(DatabaseError):
    """Raised when a requested entity is not found in the database."""

    def __init__(
        self,
        entity_type: str,
        identifier: Union[str, int],
        identifier_type: str = "id",
    ) -> None:
        """Initialize entity not found error.

        Args:
            entity_type: Type of entity (e.g., "Spell", "Monster")
            identifier: The identifier value that was searched
            identifier_type: Type of identifier (e.g., "id", "index", "name")
        """
        message = f"{entity_type} with {identifier_type} '{identifier}' not found"
        super().__init__(
            message,
            code="ENTITY_NOT_FOUND",
            details={
                "entity_type": entity_type,
                "identifier": identifier,
                "identifier_type": identifier_type,
            },
        )


class DuplicateEntityError(DatabaseError):
    """Raised when attempting to create an entity that already exists."""

    def __init__(
        self,
        entity_type: str,
        identifier: Union[str, int],
        content_pack_id: Optional[str] = None,
    ) -> None:
        """Initialize duplicate entity error.

        Args:
            entity_type: Type of entity
            identifier: The identifier that's duplicated
            content_pack_id: Optional content pack ID
        """
        message = f"{entity_type} with identifier '{identifier}' already exists"
        if content_pack_id:
            message += f" in content pack '{content_pack_id}'"
        super().__init__(
            message,
            code="DUPLICATE_ENTITY",
            details={
                "entity_type": entity_type,
                "identifier": identifier,
                "content_pack_id": content_pack_id,
            },
        )


class ValidationError(ApplicationError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error message
            field: Optional field name that failed validation
            value: Optional value that failed validation
        """
        details: Dict[str, Any] = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class ContentPackError(ApplicationError):
    """Base class for content pack related errors."""

    pass


class ContentPackNotFoundError(ContentPackError):
    """Raised when a content pack is not found."""

    def __init__(self, pack_id: str) -> None:
        message = f"Content pack '{pack_id}' not found"
        super().__init__(
            message, code="CONTENT_PACK_NOT_FOUND", details={"pack_id": pack_id}
        )


class ContentPackInactiveError(ContentPackError):
    """Raised when trying to access an inactive content pack."""

    def __init__(self, pack_id: str) -> None:
        message = f"Content pack '{pack_id}' is not active"
        super().__init__(
            message, code="CONTENT_PACK_INACTIVE", details={"pack_id": pack_id}
        )


class VectorSearchError(DatabaseError):
    """Base class for vector search related errors."""

    pass


class VectorExtensionError(VectorSearchError):
    """Raised when sqlite-vec extension is not available."""

    def __init__(self, message: str = "sqlite-vec extension not available") -> None:
        super().__init__(message, code="VECTOR_EXTENSION_ERROR")


class EmbeddingError(VectorSearchError):
    """Raised when embedding generation or processing fails."""

    def __init__(
        self,
        message: str = "Failed to process embeddings",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code="EMBEDDING_ERROR", details=details)


class InvalidVectorDimensionError(VectorSearchError):
    """Raised when vector dimensions don't match expected size."""

    def __init__(self, expected: int, actual: int) -> None:
        message = f"Invalid vector dimension: expected {expected}, got {actual}"
        super().__init__(
            message,
            code="INVALID_VECTOR_DIMENSION",
            details={"expected": expected, "actual": actual},
        )


class MigrationError(DatabaseError):
    """Base class for migration related errors."""

    pass


class MigrationFailedError(MigrationError):
    """Raised when a migration fails."""

    def __init__(
        self,
        migration_name: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        message = f"Migration '{migration_name}' failed: {reason}"
        super().__init__(
            message,
            code="MIGRATION_FAILED",
            details={
                "migration_name": migration_name,
                "reason": reason,
                **(details or {}),
            },
        )


class RollbackError(MigrationError):
    """Raised when a migration rollback fails."""

    def __init__(
        self,
        migration_name: str,
        reason: str,
    ) -> None:
        message = f"Failed to rollback migration '{migration_name}': {reason}"
        super().__init__(
            message,
            code="ROLLBACK_FAILED",
            details={"migration_name": migration_name, "reason": reason},
        )


class ServiceError(ApplicationError):
    """Base class for service layer errors."""

    pass


class AIServiceError(ServiceError):
    """Raised when AI service operations fail."""

    def __init__(
        self,
        message: str,
        service_name: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            code="AI_SERVICE_ERROR",
            details={"service_name": service_name, **(details or {})},
        )


class ConfigurationError(ApplicationError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
    ) -> None:
        details: Dict[str, Any] = {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, code="CONFIGURATION_ERROR", details=details)


class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, code="AUTHENTICATION_ERROR")


class AuthorizationError(ApplicationError):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message, code="AUTHORIZATION_ERROR")


class RateLimitError(ApplicationError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ) -> None:
        details: Dict[str, Any] = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, code="RATE_LIMIT_ERROR", details=details)


# HTTP-specific exceptions for API layer
class HTTPException(ApplicationError):
    """Base class for HTTP exceptions with status codes."""

    status_code: int = 500

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code, details)


class BadRequestError(HTTPException):
    """400 Bad Request."""

    status_code = 400

    def __init__(
        self, message: str = "Bad request", details: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message, code="BAD_REQUEST", details=details)


class NotFoundError(HTTPException):
    """404 Not Found."""

    status_code = 404

    def __init__(
        self, message: str = "Resource not found", resource_type: Optional[str] = None
    ) -> None:
        details: Dict[str, Any] = {}
        if resource_type:
            details["resource_type"] = resource_type
        super().__init__(message, code="NOT_FOUND", details=details)


class ConflictError(HTTPException):
    """409 Conflict."""

    status_code = 409

    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code="CONFLICT", details=details)


class UnprocessableEntityError(HTTPException):
    """422 Unprocessable Entity."""

    status_code = 422

    def __init__(
        self,
        message: str = "Unprocessable entity",
        validation_errors: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message,
            code="UNPROCESSABLE_ENTITY",
            details={"validation_errors": validation_errors or {}},
        )


class InternalServerError(HTTPException):
    """500 Internal Server Error."""

    status_code = 500

    def __init__(
        self,
        message: str = "Internal server error",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, code="INTERNAL_SERVER_ERROR", details=details)


class ServiceUnavailableError(HTTPException):
    """503 Service Unavailable."""

    status_code = 503

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: Optional[int] = None,
    ) -> None:
        details: Dict[str, Any] = {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, code="SERVICE_UNAVAILABLE", details=details)


# Exception mapping utilities
def map_to_http_exception(error: Exception) -> HTTPException:
    """Map application exceptions to HTTP exceptions.

    Args:
        error: The application exception

    Returns:
        An appropriate HTTP exception
    """
    if isinstance(error, HTTPException):
        return error

    if isinstance(error, EntityNotFoundError):
        return NotFoundError(
            error.message, resource_type=error.details.get("entity_type")
        )

    if isinstance(error, DuplicateEntityError):
        return ConflictError(error.message, details=error.details)

    if isinstance(error, ValidationError):
        return UnprocessableEntityError(error.message, validation_errors=error.details)

    if isinstance(error, (AuthenticationError, AuthorizationError)):
        # Note: In a real app, you'd return 401/403, but we'll use 400 for simplicity
        return BadRequestError(error.message, details=error.details)

    if isinstance(error, RateLimitError):
        return ServiceUnavailableError(
            error.message, retry_after=error.details.get("retry_after")
        )

    if isinstance(error, DatabaseError):
        # Database errors should preserve their error code
        result = InternalServerError(error.message, details=error.details)
        result.code = error.code  # Preserve the original error code
        return result

    if isinstance(error, ApplicationError):
        # Generic application errors become 500s
        return InternalServerError(error.message, details=error.details)

    # Unknown exceptions become generic 500s
    return InternalServerError(str(error))
