"""Unit tests for database types and vector type safety.

This module tests the type aliases, validation functions, and type guards
defined in app.content.types to ensure proper type safety for vector operations.
"""

from typing import Any

import numpy as np
import pytest

from app.content.types import (
    DEFAULT_VECTOR_DIMENSION,
    SUPPORTED_VECTOR_DIMENSIONS,
    VECTOR_DIM_384,
    VECTOR_DIM_768,
    VECTOR_DIM_1536,
    OptionalVector,
    Vector,
    Vector384,
    Vector768,
    Vector1536,
    VectorInput,
    ensure_vector_dimension,
    is_valid_vector_dimension,
    is_vector_384,
    is_vector_768,
    is_vector_1536,
    validate_vector_dimension,
)


class TestVectorDimensionConstants:
    """Test vector dimension constants and configuration."""

    def test_dimension_constants(self) -> None:
        """Test that dimension constants have expected values."""
        assert VECTOR_DIM_384 == 384
        assert VECTOR_DIM_768 == 768
        assert VECTOR_DIM_1536 == 1536

    def test_default_dimension(self) -> None:
        """Test that default dimension is 384."""
        assert DEFAULT_VECTOR_DIMENSION == 384
        assert DEFAULT_VECTOR_DIMENSION == VECTOR_DIM_384

    def test_supported_dimensions(self) -> None:
        """Test that supported dimensions set contains expected values."""
        expected_dimensions = {384, 768, 1536}
        assert SUPPORTED_VECTOR_DIMENSIONS == expected_dimensions


class TestVectorTypeAliases:
    """Test vector type aliases are properly defined."""

    def test_vector_type_creation(self) -> None:
        """Test that vector types can be created and assigned."""
        # Test basic Vector type
        vector_384: Vector = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        assert isinstance(vector_384, np.ndarray)
        assert vector_384.dtype == np.float32

        # Test dimension-specific types
        vector_384_specific: Vector384 = np.zeros(384, dtype=np.float32)
        vector_768_specific: Vector768 = np.zeros(768, dtype=np.float32)
        vector_1536_specific: Vector1536 = np.zeros(1536, dtype=np.float32)

        assert len(vector_384_specific) == 384
        assert len(vector_768_specific) == 768
        assert len(vector_1536_specific) == 1536

    def test_optional_vector_types(self) -> None:
        """Test that optional vector types can be None or vectors."""
        # Test OptionalVector
        opt_vector: OptionalVector = None
        assert opt_vector is None

        opt_vector = np.array([1.0, 2.0], dtype=np.float32)
        assert opt_vector is not None
        assert isinstance(opt_vector, np.ndarray)

    def test_vector_input_types(self) -> None:
        """Test VectorInput accepts both numpy arrays and lists."""
        # Test with numpy array
        vector_input: VectorInput = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        assert isinstance(vector_input, np.ndarray)

        # Test with list
        vector_input = [1.0, 2.0, 3.0]
        assert isinstance(vector_input, list)


class TestVectorValidation:
    """Test vector validation functions."""

    def test_is_valid_vector_dimension(self) -> None:
        """Test dimension validation function."""
        # Valid dimensions
        assert is_valid_vector_dimension(384) is True
        assert is_valid_vector_dimension(768) is True
        assert is_valid_vector_dimension(1536) is True

        # Invalid dimensions
        assert is_valid_vector_dimension(100) is False
        assert is_valid_vector_dimension(512) is False
        assert is_valid_vector_dimension(2048) is False
        assert is_valid_vector_dimension(0) is False
        assert is_valid_vector_dimension(-1) is False

    def test_validate_vector_dimension_success(self) -> None:
        """Test successful vector dimension validation."""
        vector_384 = np.zeros(384, dtype=np.float32)
        vector_768 = np.zeros(768, dtype=np.float32)
        vector_1536 = np.zeros(1536, dtype=np.float32)

        # Should not raise any exceptions
        validate_vector_dimension(vector_384, 384)
        validate_vector_dimension(vector_768, 768)
        validate_vector_dimension(vector_1536, 1536)

    def test_validate_vector_dimension_failure(self) -> None:
        """Test vector dimension validation failures."""
        vector_384 = np.zeros(384, dtype=np.float32)

        # Wrong dimension should raise ValueError
        with pytest.raises(
            ValueError, match="Vector dimension mismatch: expected 768, got 384"
        ):
            validate_vector_dimension(vector_384, 768)

        with pytest.raises(
            ValueError, match="Vector dimension mismatch: expected 1536, got 384"
        ):
            validate_vector_dimension(vector_384, 1536)

    def test_validate_vector_dimension_returns_vector(self) -> None:
        """Test that validate_vector_dimension returns the vector on success."""
        vector_384 = np.zeros(384, dtype=np.float32)
        vector_768 = np.zeros(768, dtype=np.float32)
        vector_1536 = np.zeros(1536, dtype=np.float32)

        # Should return the same vector
        result_384 = validate_vector_dimension(vector_384, 384)
        result_768 = validate_vector_dimension(vector_768, 768)
        result_1536 = validate_vector_dimension(vector_1536, 1536)

        assert result_384 is vector_384
        assert result_768 is vector_768
        assert result_1536 is vector_1536

    def test_ensure_vector_dimension_success(self) -> None:
        """Test successful vector dimension ensuring."""
        vector_384 = np.zeros(384, dtype=np.float32)

        # Should return the same vector via validate_vector_dimension
        result = ensure_vector_dimension(vector_384, 384)
        assert result is vector_384
        assert len(result) == 384

    def test_ensure_vector_dimension_failure(self) -> None:
        """Test vector dimension ensuring failures."""
        vector_384 = np.zeros(384, dtype=np.float32)

        # Wrong dimension should raise ValueError
        with pytest.raises(
            ValueError, match="Vector dimension mismatch: expected 768, got 384"
        ):
            ensure_vector_dimension(vector_384, 768)


class TestVectorTypeGuards:
    """Test vector type guard functions."""

    def test_is_vector_384(self) -> None:
        """Test 384-dimensional vector type guard."""
        vector_384 = np.zeros(384, dtype=np.float32)
        vector_768 = np.zeros(768, dtype=np.float32)
        vector_100 = np.zeros(100, dtype=np.float32)

        assert is_vector_384(vector_384) is True
        assert is_vector_384(vector_768) is False
        assert is_vector_384(vector_100) is False

    def test_is_vector_768(self) -> None:
        """Test 768-dimensional vector type guard."""
        vector_384 = np.zeros(384, dtype=np.float32)
        vector_768 = np.zeros(768, dtype=np.float32)
        vector_1536 = np.zeros(1536, dtype=np.float32)

        assert is_vector_768(vector_384) is False
        assert is_vector_768(vector_768) is True
        assert is_vector_768(vector_1536) is False

    def test_is_vector_1536(self) -> None:
        """Test 1536-dimensional vector type guard."""
        vector_768 = np.zeros(768, dtype=np.float32)
        vector_1536 = np.zeros(1536, dtype=np.float32)
        vector_2048 = np.zeros(2048, dtype=np.float32)

        assert is_vector_1536(vector_768) is False
        assert is_vector_1536(vector_1536) is True
        assert is_vector_1536(vector_2048) is False


class TestVectorTypeDecorator:
    """Test VECTOR TypeDecorator with dimension validation."""

    def test_vector_type_init_default_dimension(self) -> None:
        """Test VECTOR type initialization with default dimension."""
        from app.content.models import VECTOR

        vector_type = VECTOR()
        assert vector_type.dim == DEFAULT_VECTOR_DIMENSION
        assert vector_type.dim == 384

    def test_vector_type_init_custom_dimension(self) -> None:
        """Test VECTOR type initialization with custom dimension."""
        from app.content.models import VECTOR

        vector_type_768 = VECTOR(768)
        assert vector_type_768.dim == 768

        vector_type_1536 = VECTOR(1536)
        assert vector_type_1536.dim == 1536

    def test_vector_type_init_invalid_dimension(self) -> None:
        """Test VECTOR type initialization with invalid dimension."""
        from app.content.models import VECTOR

        with pytest.raises(ValueError, match="Unsupported vector dimension: 512"):
            VECTOR(512)

        with pytest.raises(ValueError, match="Unsupported vector dimension: 0"):
            VECTOR(0)

        with pytest.raises(ValueError, match="Unsupported vector dimension: -1"):
            VECTOR(-1)

    def test_process_bind_param_numpy_array(self) -> None:
        """Test VECTOR process_bind_param with numpy arrays."""
        from app.content.models import VECTOR

        vector_type = VECTOR(384)
        vector = np.random.rand(384).astype(np.float32)

        # Should convert to bytes
        result = vector_type.process_bind_param(vector, None)
        assert isinstance(result, bytes)
        assert len(result) == 384 * 4  # 4 bytes per float32

    def test_process_bind_param_list(self) -> None:
        """Test VECTOR process_bind_param with Python lists."""
        from app.content.models import VECTOR

        vector_type = VECTOR(384)  # Use valid dimension
        vector_list = [1.0] * 384  # Create 384-dimensional list

        # Should convert to bytes
        result = vector_type.process_bind_param(vector_list, None)
        assert isinstance(result, bytes)
        assert len(result) == 384 * 4  # 4 bytes per float32

    def test_process_bind_param_none(self) -> None:
        """Test VECTOR process_bind_param with None."""
        from app.content.models import VECTOR

        vector_type = VECTOR(384)

        # Should return None
        result = vector_type.process_bind_param(None, None)
        assert result is None

    def test_process_bind_param_wrong_dimension(self) -> None:
        """Test VECTOR process_bind_param with wrong dimension."""
        from app.content.models import VECTOR

        vector_type = VECTOR(384)
        wrong_vector = np.random.rand(768).astype(np.float32)

        # Should raise ValueError
        with pytest.raises(
            ValueError, match="Vector dimension mismatch: expected 384, got 768"
        ):
            vector_type.process_bind_param(wrong_vector, None)

    def test_process_bind_param_invalid_type(self) -> None:
        """Test VECTOR process_bind_param with invalid type."""
        from app.content.models import VECTOR

        vector_type = VECTOR(384)

        # Should raise ValueError for invalid types
        with pytest.raises(
            ValueError, match="Expected numpy array or list, got <class 'str'>"
        ):
            vector_type.process_bind_param("invalid", None)  # type: ignore[arg-type]

        with pytest.raises(
            ValueError, match="Expected numpy array or list, got <class 'int'>"
        ):
            vector_type.process_bind_param(42, None)  # type: ignore[arg-type]

    def test_process_result_value_success(self) -> None:
        """Test VECTOR process_result_value with valid data."""
        from app.content.models import VECTOR

        vector_type = VECTOR(384)
        original_vector = np.random.rand(384).astype(np.float32)
        bytes_data = original_vector.tobytes()

        # Should convert back to numpy array
        result = vector_type.process_result_value(bytes_data, None)
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32
        assert len(result) == 384
        np.testing.assert_array_almost_equal(result, original_vector)

    def test_process_result_value_none(self) -> None:
        """Test VECTOR process_result_value with None."""
        from app.content.models import VECTOR

        vector_type = VECTOR(384)

        # Should return None
        result = vector_type.process_result_value(None, None)
        assert result is None

    def test_process_result_value_wrong_dimension(self) -> None:
        """Test VECTOR process_result_value with wrong dimension."""
        from app.content.models import VECTOR

        vector_type = VECTOR(384)
        wrong_vector = np.random.rand(768).astype(np.float32)
        bytes_data = wrong_vector.tobytes()

        # Should raise ValueError
        with pytest.raises(
            ValueError, match="Vector dimension mismatch: expected 384, got 768"
        ):
            vector_type.process_result_value(bytes_data, None)

    def test_round_trip_conversion(self) -> None:
        """Test complete round-trip conversion (bind -> store -> result)."""
        from app.content.models import VECTOR

        vector_type = VECTOR(384)
        original_vector = np.random.rand(384).astype(np.float32)

        # Convert to bytes (bind)
        bytes_data = vector_type.process_bind_param(original_vector, None)
        assert isinstance(bytes_data, bytes)

        # Convert back to array (result)
        result_vector = vector_type.process_result_value(bytes_data, None)
        assert isinstance(result_vector, np.ndarray)

        # Should be identical
        np.testing.assert_array_equal(result_vector, original_vector)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_vector(self) -> None:
        """Test handling of empty vectors."""
        empty_vector = np.array([], dtype=np.float32)

        # Type guards should return False
        assert is_vector_384(empty_vector) is False
        assert is_vector_768(empty_vector) is False
        assert is_vector_1536(empty_vector) is False

        # Validation should fail
        with pytest.raises(
            ValueError, match="Vector dimension mismatch: expected 384, got 0"
        ):
            validate_vector_dimension(empty_vector, 384)

    def test_non_float32_vectors(self) -> None:
        """Test handling of vectors with different dtypes."""
        vector_int = np.array([1, 2, 3], dtype=np.int32)
        vector_float64 = np.array([1.0, 2.0, 3.0], dtype=np.float64)

        # Type guards should still work (they only check length)
        # Note: These are intentionally testing with wrong dtypes for robustness
        assert is_vector_384(vector_int) is False  # type: ignore[arg-type]  # Wrong length
        assert is_vector_384(vector_float64) is False  # type: ignore[arg-type]  # Wrong length

        # Validation should work (only checks length)
        # Note: These are intentionally testing with wrong dtypes for robustness
        validate_vector_dimension(vector_int, 3)  # type: ignore[arg-type]
        validate_vector_dimension(vector_float64, 3)  # type: ignore[arg-type]

    def test_very_large_dimensions(self) -> None:
        """Test handling of very large dimension values."""
        large_dim = 1000000

        # Should not be considered valid
        assert is_valid_vector_dimension(large_dim) is False

        # Creating VECTOR with large dimension should fail
        from app.content.models import VECTOR

        with pytest.raises(
            ValueError, match=f"Unsupported vector dimension: {large_dim}"
        ):
            VECTOR(large_dim)
