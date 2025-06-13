"""Tests for the custom exceptions module."""

import pytest

from app.exceptions import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    BadRequestError,
    ConfigurationError,
    ConflictError,
    ConnectionError,
    ContentPackInactiveError,
    ContentPackNotFoundError,
    DatabaseError,
    DuplicateEntityError,
    EmbeddingError,
    EntityNotFoundError,
    HTTPException,
    InternalServerError,
    InvalidVectorDimensionError,
    MigrationFailedError,
    NotFoundError,
    RateLimitError,
    RollbackError,
    ServiceUnavailableError,
    SessionError,
    UnprocessableEntityError,
    ValidationError,
    VectorExtensionError,
    map_to_http_exception,
)


class TestApplicationError:
    """Test the base ApplicationError class."""

    def test_basic_creation(self) -> None:
        """Test creating an ApplicationError with just a message."""
        error = ApplicationError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.code is None
        assert error.details == {}

    def test_creation_with_code_and_details(self) -> None:
        """Test creating an ApplicationError with all parameters."""
        details = {"field": "username", "value": "test"}
        error = ApplicationError("Invalid input", code="INVALID_INPUT", details=details)
        assert error.message == "Invalid input"
        assert error.code == "INVALID_INPUT"
        assert error.details == details

    def test_to_dict(self) -> None:
        """Test converting exception to dictionary."""
        error = ApplicationError(
            "Test error", code="TEST_CODE", details={"key": "value"}
        )
        result = error.to_dict()
        assert result == {
            "error": "Test error",
            "code": "TEST_CODE",
            "details": {"key": "value"},
        }

    def test_to_dict_minimal(self) -> None:
        """Test converting exception to dictionary with minimal data."""
        error = ApplicationError("Test error")
        result = error.to_dict()
        assert result == {"error": "Test error"}


class TestDatabaseErrors:
    """Test database-related exceptions."""

    def test_connection_error(self) -> None:
        """Test ConnectionError."""
        error = ConnectionError()
        assert error.message == "Failed to connect to database"
        assert error.code == "DB_CONNECTION_ERROR"

    def test_connection_error_custom(self) -> None:
        """Test ConnectionError with custom message."""
        error = ConnectionError(
            "Custom connection error", details={"host": "localhost"}
        )
        assert error.message == "Custom connection error"
        assert error.details == {"host": "localhost"}

    def test_session_error(self) -> None:
        """Test SessionError."""
        error = SessionError()
        assert error.message == "Database session error"
        assert error.code == "DB_SESSION_ERROR"

    def test_entity_not_found_error(self) -> None:
        """Test EntityNotFoundError."""
        error = EntityNotFoundError("Spell", "fireball", "index")
        assert error.message == "Spell with index 'fireball' not found"
        assert error.code == "ENTITY_NOT_FOUND"
        assert error.details == {
            "entity_type": "Spell",
            "identifier": "fireball",
            "identifier_type": "index",
        }

    def test_duplicate_entity_error(self) -> None:
        """Test DuplicateEntityError."""
        error = DuplicateEntityError("Monster", "goblin")
        assert error.message == "Monster with identifier 'goblin' already exists"
        assert error.code == "DUPLICATE_ENTITY"
        assert error.details == {
            "entity_type": "Monster",
            "identifier": "goblin",
            "content_pack_id": None,
        }

    def test_duplicate_entity_error_with_pack(self) -> None:
        """Test DuplicateEntityError with content pack."""
        error = DuplicateEntityError("Monster", "goblin", "homebrew-pack")
        assert (
            error.message
            == "Monster with identifier 'goblin' already exists in content pack 'homebrew-pack'"
        )
        assert error.details["content_pack_id"] == "homebrew-pack"


class TestValidationError:
    """Test ValidationError."""

    def test_basic_validation_error(self) -> None:
        """Test basic ValidationError."""
        error = ValidationError("Invalid value")
        assert error.message == "Invalid value"
        assert error.code == "VALIDATION_ERROR"
        assert error.details == {}

    def test_validation_error_with_field(self) -> None:
        """Test ValidationError with field information."""
        error = ValidationError(
            "Invalid email format", field="email", value="notanemail"
        )
        assert error.message == "Invalid email format"
        assert error.details == {"field": "email", "value": "notanemail"}


class TestContentPackErrors:
    """Test content pack related errors."""

    def test_content_pack_not_found(self) -> None:
        """Test ContentPackNotFoundError."""
        error = ContentPackNotFoundError("my-pack")
        assert error.message == "Content pack 'my-pack' not found"
        assert error.code == "CONTENT_PACK_NOT_FOUND"
        assert error.details == {"pack_id": "my-pack"}

    def test_content_pack_inactive(self) -> None:
        """Test ContentPackInactiveError."""
        error = ContentPackInactiveError("inactive-pack")
        assert error.message == "Content pack 'inactive-pack' is not active"
        assert error.code == "CONTENT_PACK_INACTIVE"
        assert error.details == {"pack_id": "inactive-pack"}


class TestVectorSearchErrors:
    """Test vector search related errors."""

    def test_vector_extension_error(self) -> None:
        """Test VectorExtensionError."""
        error = VectorExtensionError()
        assert error.message == "sqlite-vec extension not available"
        assert error.code == "VECTOR_EXTENSION_ERROR"

    def test_embedding_error(self) -> None:
        """Test EmbeddingError."""
        error = EmbeddingError()
        assert error.message == "Failed to process embeddings"
        assert error.code == "EMBEDDING_ERROR"

    def test_invalid_vector_dimension(self) -> None:
        """Test InvalidVectorDimensionError."""
        error = InvalidVectorDimensionError(384, 768)
        assert error.message == "Invalid vector dimension: expected 384, got 768"
        assert error.code == "INVALID_VECTOR_DIMENSION"
        assert error.details == {"expected": 384, "actual": 768}


class TestMigrationErrors:
    """Test migration related errors."""

    def test_migration_failed(self) -> None:
        """Test MigrationFailedError."""
        error = MigrationFailedError(
            "add_vector_columns", "Column already exists", details={"table": "spells"}
        )
        assert (
            error.message
            == "Migration 'add_vector_columns' failed: Column already exists"
        )
        assert error.code == "MIGRATION_FAILED"
        assert error.details == {
            "migration_name": "add_vector_columns",
            "reason": "Column already exists",
            "table": "spells",
        }

    def test_rollback_error(self) -> None:
        """Test RollbackError."""
        error = RollbackError("add_indexes", "Foreign key constraint")
        assert (
            error.message
            == "Failed to rollback migration 'add_indexes': Foreign key constraint"
        )
        assert error.code == "ROLLBACK_FAILED"
        assert error.details == {
            "migration_name": "add_indexes",
            "reason": "Foreign key constraint",
        }


class TestHTTPExceptions:
    """Test HTTP-specific exceptions."""

    def test_bad_request(self) -> None:
        """Test BadRequestError."""
        error = BadRequestError()
        assert error.message == "Bad request"
        assert error.status_code == 400
        assert error.code == "BAD_REQUEST"

    def test_not_found(self) -> None:
        """Test NotFoundError."""
        error = NotFoundError("Spell not found", resource_type="Spell")
        assert error.message == "Spell not found"
        assert error.status_code == 404
        assert error.details == {"resource_type": "Spell"}

    def test_conflict(self) -> None:
        """Test ConflictError."""
        error = ConflictError("Resource already exists")
        assert error.message == "Resource already exists"
        assert error.status_code == 409

    def test_unprocessable_entity(self) -> None:
        """Test UnprocessableEntityError."""
        validation_errors = {"email": "Invalid format", "age": "Must be positive"}
        error = UnprocessableEntityError(
            "Validation failed", validation_errors=validation_errors
        )
        assert error.status_code == 422
        assert error.details["validation_errors"] == validation_errors

    def test_internal_server_error(self) -> None:
        """Test InternalServerError."""
        error = InternalServerError()
        assert error.message == "Internal server error"
        assert error.status_code == 500

    def test_service_unavailable(self) -> None:
        """Test ServiceUnavailableError."""
        error = ServiceUnavailableError(retry_after=60)
        assert error.status_code == 503
        assert error.details == {"retry_after": 60}


class TestExceptionMapping:
    """Test the map_to_http_exception function."""

    def test_map_http_exception(self) -> None:
        """Test mapping an HTTPException returns itself."""
        original = NotFoundError("Not found")
        mapped = map_to_http_exception(original)
        assert mapped is original

    def test_map_entity_not_found(self) -> None:
        """Test mapping EntityNotFoundError to NotFoundError."""
        original = EntityNotFoundError("Spell", "fireball", "index")
        mapped = map_to_http_exception(original)
        assert isinstance(mapped, NotFoundError)
        assert mapped.status_code == 404
        assert mapped.details["resource_type"] == "Spell"

    def test_map_duplicate_entity(self) -> None:
        """Test mapping DuplicateEntityError to ConflictError."""
        original = DuplicateEntityError("Monster", "goblin")
        mapped = map_to_http_exception(original)
        assert isinstance(mapped, ConflictError)
        assert mapped.status_code == 409
        assert mapped.details == original.details

    def test_map_validation_error(self) -> None:
        """Test mapping ValidationError to UnprocessableEntityError."""
        original = ValidationError("Invalid field", field="email")
        mapped = map_to_http_exception(original)
        assert isinstance(mapped, UnprocessableEntityError)
        assert mapped.status_code == 422

    def test_map_authentication_error(self) -> None:
        """Test mapping AuthenticationError to BadRequestError."""
        original = AuthenticationError("Invalid credentials")
        mapped = map_to_http_exception(original)
        assert isinstance(mapped, BadRequestError)
        assert mapped.status_code == 400

    def test_map_rate_limit_error(self) -> None:
        """Test mapping RateLimitError to ServiceUnavailableError."""
        original = RateLimitError("Too many requests", retry_after=30)
        mapped = map_to_http_exception(original)
        assert isinstance(mapped, ServiceUnavailableError)
        assert mapped.status_code == 503
        assert mapped.details["retry_after"] == 30

    def test_map_application_error(self) -> None:
        """Test mapping generic ApplicationError to InternalServerError."""
        original = ApplicationError("Something went wrong")
        mapped = map_to_http_exception(original)
        assert isinstance(mapped, InternalServerError)
        assert mapped.status_code == 500

    def test_map_unknown_exception(self) -> None:
        """Test mapping unknown exception to InternalServerError."""
        original = ValueError("Unknown error")
        mapped = map_to_http_exception(original)
        assert isinstance(mapped, InternalServerError)
        assert mapped.status_code == 500
        assert mapped.message == "Unknown error"


class TestMiscellaneousErrors:
    """Test other error types."""

    def test_configuration_error(self) -> None:
        """Test ConfigurationError."""
        error = ConfigurationError("Missing API key", config_key="OPENAI_API_KEY")
        assert error.message == "Missing API key"
        assert error.code == "CONFIGURATION_ERROR"
        assert error.details == {"config_key": "OPENAI_API_KEY"}

    def test_authentication_error(self) -> None:
        """Test AuthenticationError."""
        error = AuthenticationError()
        assert error.message == "Authentication failed"
        assert error.code == "AUTHENTICATION_ERROR"

    def test_authorization_error(self) -> None:
        """Test AuthorizationError."""
        error = AuthorizationError("Insufficient permissions")
        assert error.message == "Insufficient permissions"
        assert error.code == "AUTHORIZATION_ERROR"

    def test_rate_limit_error(self) -> None:
        """Test RateLimitError."""
        error = RateLimitError()
        assert error.message == "Rate limit exceeded"
        assert error.code == "RATE_LIMIT_ERROR"
        assert error.details == {}
