"""Tests for the semantic mapper."""

import pytest

from app.content.rag.semantic_mapper import SemanticMapper


class TestSemanticMapper:
    """Test suite for SemanticMapper."""

    def test_default_mappings(self) -> None:
        """Test that default mappings are loaded correctly."""
        mapper = SemanticMapper()

        # Test conceptual mappings
        assert "adventure" in mapper.mappings
        assert "monsters" in mapper.mappings["adventure"]
        assert "equipment" in mapper.mappings["adventure"]
        assert "spells" in mapper.mappings["adventure"]

    def test_map_conceptual_to_concrete(self) -> None:
        """Test mapping conceptual types to concrete types."""
        mapper = SemanticMapper()

        # Test single conceptual type
        result = mapper.map_to_concrete_types(["adventure"])
        assert "monsters" in result
        assert "equipment" in result
        assert "spells" in result

        # Test multiple conceptual types
        result = mapper.map_to_concrete_types(["adventure", "combat"])
        assert "monsters" in result
        assert "equipment" in result
        assert "spells" in result
        assert "mechanics" in result  # From combat

    def test_passthrough_concrete_types(self) -> None:
        """Test that concrete types pass through unchanged."""
        mapper = SemanticMapper()

        # Test direct concrete type
        result = mapper.map_to_concrete_types(["monsters"])
        assert result == {"monsters"}

        # Test unknown type (treated as concrete)
        result = mapper.map_to_concrete_types(["unknown_type"])
        assert result == {"unknown_type"}

    def test_mixed_conceptual_and_concrete(self) -> None:
        """Test mixing conceptual and concrete types."""
        mapper = SemanticMapper()

        result = mapper.map_to_concrete_types(["adventure", "monsters", "unknown"])
        assert "monsters" in result  # From both adventure and direct
        assert "equipment" in result  # From adventure
        assert "spells" in result  # From adventure
        assert "unknown" in result  # Passthrough

    def test_custom_mappings(self) -> None:
        """Test custom mappings override defaults."""
        custom = {"adventure": ["custom_source"], "new_concept": ["source1", "source2"]}
        mapper = SemanticMapper(custom_mappings=custom)

        # Test overridden mapping
        result = mapper.map_to_concrete_types(["adventure"])
        assert result == {"custom_source"}

        # Test new mapping
        result = mapper.map_to_concrete_types(["new_concept"])
        assert result == {"source1", "source2"}

        # Test default still works
        result = mapper.map_to_concrete_types(["combat"])
        assert "monsters" in result

    def test_add_mapping(self) -> None:
        """Test adding mappings dynamically."""
        mapper = SemanticMapper()

        # Add new mapping
        mapper.add_mapping("test_concept", ["test1", "test2"])
        result = mapper.map_to_concrete_types(["test_concept"])
        assert result == {"test1", "test2"}

        # Override existing mapping
        mapper.add_mapping("adventure", ["new_source"])
        result = mapper.map_to_concrete_types(["adventure"])
        assert result == {"new_source"}

    def test_get_all_concrete_types(self) -> None:
        """Test getting all unique concrete types."""
        mapper = SemanticMapper()

        all_types = mapper.get_all_concrete_types()
        assert "monsters" in all_types
        assert "spells" in all_types
        assert "equipment" in all_types
        assert "rules" in all_types
        assert "character_options" in all_types
        assert "mechanics" in all_types

    def test_empty_input(self) -> None:
        """Test empty input returns empty set."""
        mapper = SemanticMapper()

        result = mapper.map_to_concrete_types([])
        assert result == set()
