"""Database type definitions and aliases for vector embeddings and related operations.

This module provides comprehensive type aliases for vector embeddings stored in the database,
including dimension validation and type safety utilities.
"""

from typing import List, NewType, Optional, TypeAlias, TypeGuard, Union

import numpy as np
from numpy.typing import NDArray

# ==============================================================================
# Vector Type Aliases
# ==============================================================================

# Base vector types
Vector: TypeAlias = NDArray[np.float32]
"""Base vector type using numpy float32 arrays."""

OptionalVector: TypeAlias = Optional[Vector]
"""Optional vector type for nullable embedding fields."""

# Dimension-specific vector types
Vector384: TypeAlias = NDArray[np.float32]  # all-MiniLM-L6-v2 standard
"""384-dimensional vector for all-MiniLM-L6-v2 sentence transformer model."""

Vector768: TypeAlias = NDArray[np.float32]  # BERT-base, potential future use
"""768-dimensional vector for BERT-base and similar models."""

Vector1536: TypeAlias = NDArray[np.float32]  # OpenAI text-embedding-ada-002
"""1536-dimensional vector for OpenAI's text-embedding-ada-002 model."""

# Optional dimension-specific types
OptionalVector384: TypeAlias = Optional[Vector384]
"""Optional 384-dimensional vector type."""

OptionalVector768: TypeAlias = Optional[Vector768]
"""Optional 768-dimensional vector type."""

OptionalVector1536: TypeAlias = Optional[Vector1536]
"""Optional 1536-dimensional vector type."""

# Input types for vector operations (before conversion to numpy)
VectorInput: TypeAlias = Union[Vector, List[float]]
"""Input type for vectors - accepts numpy arrays or Python lists."""

OptionalVectorInput: TypeAlias = Optional[VectorInput]
"""Optional input type for vectors."""

# ==============================================================================
# Database Entity Type Aliases
# ==============================================================================

ContentPackId = NewType("ContentPackId", int)
"""Distinct type for content pack identifiers."""

EntityIndex = NewType("EntityIndex", str)
"""Distinct type for entity index strings (e.g., 'fireball', 'ancient-red-dragon')."""

EntityName = NewType("EntityName", str)
"""Distinct type for entity display names."""

EntityUrl = NewType("EntityUrl", str)
"""Distinct type for entity URL references."""

EmbeddingModel = NewType("EmbeddingModel", str)
"""Distinct type for embedding model names (e.g., 'all-MiniLM-L6-v2')."""

# ==============================================================================
# Vector Dimension Constants
# ==============================================================================

# Standard dimensions for common embedding models
VECTOR_DIM_384 = 384  # all-MiniLM-L6-v2, all-MiniLM-L12-v2
VECTOR_DIM_768 = 768  # BERT-base, sentence-transformers/all-mpnet-base-v2
VECTOR_DIM_1536 = 1536  # OpenAI text-embedding-ada-002

# Current application standard
DEFAULT_VECTOR_DIMENSION = VECTOR_DIM_384
"""Default vector dimension used throughout the application."""

# Supported dimensions for validation
SUPPORTED_VECTOR_DIMENSIONS = {384, 768, 1536}
"""Set of supported vector dimensions for validation."""

# ==============================================================================
# Type Guards and Validation
# ==============================================================================


def is_valid_vector_dimension(dim: int) -> bool:
    """Check if a dimension is supported for vector operations.

    Args:
        dim: The dimension to validate

    Returns:
        True if the dimension is supported, False otherwise
    """
    return dim in SUPPORTED_VECTOR_DIMENSIONS


def is_vector_384(vector: Vector) -> TypeGuard[Vector384]:
    """Type guard to check if a vector has 384 dimensions.

    Args:
        vector: The vector to check

    Returns:
        True if the vector has exactly 384 dimensions
    """
    return vector.shape == (VECTOR_DIM_384,)


def is_vector_768(vector: Vector) -> TypeGuard[Vector768]:
    """Type guard to check if a vector has 768 dimensions.

    Args:
        vector: The vector to check

    Returns:
        True if the vector has exactly 768 dimensions
    """
    return vector.shape == (VECTOR_DIM_768,)


def is_vector_1536(vector: Vector) -> TypeGuard[Vector1536]:
    """Type guard to check if a vector has 1536 dimensions.

    Args:
        vector: The vector to check

    Returns:
        True if the vector has exactly 1536 dimensions
    """
    return vector.shape == (VECTOR_DIM_1536,)


def validate_vector_dimension(vector: Vector, expected_dim: int) -> Vector:
    """Validate that a vector has the expected dimension, returning it on success.

    Args:
        vector: The vector to validate
        expected_dim: The expected dimension

    Returns:
        The same vector if validation passes

    Raises:
        ValueError: If the vector dimension doesn't match expected
    """
    actual_dim = vector.shape[0]
    if actual_dim != expected_dim:
        raise ValueError(
            f"Vector dimension mismatch: expected {expected_dim}, got {actual_dim}"
        )
    return vector


def ensure_vector_dimension(vector: Vector, expected_dim: int) -> Vector:
    """Ensure a vector has the expected dimension, raising an error if not.

    Args:
        vector: The vector to check
        expected_dim: The expected dimension

    Returns:
        The same vector if validation passes

    Raises:
        ValueError: If the vector dimension doesn't match expected
    """
    return validate_vector_dimension(vector, expected_dim)


# Validated vector types (distinct types for statically enforced validation)
ValidatedVector384 = NewType("ValidatedVector384", Vector384)
"""Distinct type for 384-dimensional vectors that have been validated."""

ValidatedVector768 = NewType("ValidatedVector768", Vector768)
"""Distinct type for 768-dimensional vectors that have been validated."""

ValidatedVector1536 = NewType("ValidatedVector1536", Vector1536)
"""Distinct type for 1536-dimensional vectors that have been validated."""

# ==============================================================================
# Convenience Type Aliases
# ==============================================================================

# Current application standard aliases (384-dimensional)
AppVector: TypeAlias = Vector384
"""Application standard vector type (384-dimensional)."""

OptionalAppVector: TypeAlias = OptionalVector384
"""Optional application standard vector type."""

# Legacy compatibility
EmbeddingVector: TypeAlias = Vector384
"""Legacy alias for embedding vectors (384-dimensional)."""

OptionalEmbeddingVector: TypeAlias = OptionalVector384
"""Legacy alias for optional embedding vectors."""
