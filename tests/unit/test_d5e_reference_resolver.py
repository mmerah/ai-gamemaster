"""Unit tests for D5eReferenceResolver."""

from typing import Any, Dict, List, Optional
from unittest.mock import Mock, create_autospec

import pytest

from app.models.d5e.types import is_api_reference
from app.services.d5e.data_loader import D5eDataLoader
from app.services.d5e.reference_resolver import (
    CircularReferenceError,
    D5eReferenceResolver,
    ReferenceNotFoundError,
)


class TestD5eReferenceResolver:
    """Test suite for D5eReferenceResolver."""

    @pytest.fixture
    def mock_data_loader(self) -> Mock:
        """Create a mock data loader."""
        mock: Mock = create_autospec(D5eDataLoader, instance=True)
        return mock

    @pytest.fixture
    def sample_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Sample data with references."""
        return {
            "spells": [
                {
                    "index": "fireball",
                    "name": "Fireball",
                    "url": "/api/spells/fireball",
                    "school": {
                        "index": "evocation",
                        "name": "Evocation",
                        "url": "/api/magic-schools/evocation",
                    },
                    "classes": [
                        {
                            "index": "wizard",
                            "name": "Wizard",
                            "url": "/api/classes/wizard",
                        }
                    ],
                }
            ],
            "magic-schools": [
                {
                    "index": "evocation",
                    "name": "Evocation",
                    "url": "/api/magic-schools/evocation",
                    "desc": "Evocation spells manipulate energy...",
                }
            ],
            "classes": [
                {
                    "index": "wizard",
                    "name": "Wizard",
                    "url": "/api/classes/wizard",
                    "hit_die": 6,
                    "spellcasting": {
                        "index": "wizard",
                        "name": "Wizard",
                        "url": "/api/spellcasting/wizard",
                    },
                }
            ],
        }

    @pytest.fixture
    def resolver(self, mock_data_loader: Mock) -> D5eReferenceResolver:
        """Create a reference resolver with mock data loader."""
        return D5eReferenceResolver(mock_data_loader)

    def test_init(self, mock_data_loader: Mock) -> None:
        """Test initialization."""
        resolver = D5eReferenceResolver(mock_data_loader)
        assert resolver._data_loader is mock_data_loader
        assert resolver._reference_cache == {}

    def test_parse_reference_url(self, resolver: D5eReferenceResolver) -> None:
        """Test parsing reference URLs."""
        category, index = resolver._parse_reference_url("/api/spells/fireball")
        assert category == "spells"
        assert index == "fireball"

        category, index = resolver._parse_reference_url("/api/magic-schools/evocation")
        assert category == "magic-schools"
        assert index == "evocation"

    def test_parse_reference_url_invalid(self, resolver: D5eReferenceResolver) -> None:
        """Test parsing invalid reference URLs."""
        with pytest.raises(ValueError, match="Invalid reference URL"):
            resolver._parse_reference_url("invalid-url")

        with pytest.raises(ValueError, match="Invalid reference URL"):
            resolver._parse_reference_url("/api/")

        with pytest.raises(ValueError, match="Invalid reference URL"):
            resolver._parse_reference_url("/different/format/url")

    def test_is_reference(self, resolver: D5eReferenceResolver) -> None:
        """Test identifying reference objects."""
        # Valid reference
        assert (
            is_api_reference(
                {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"}
            )
            is True
        )

        # Missing url
        assert is_api_reference({"index": "wizard", "name": "Wizard"}) is False

        # Not a dict
        assert is_api_reference("not a reference") is False
        assert is_api_reference([1, 2, 3]) is False

    def test_resolve_reference_simple(
        self,
        resolver: D5eReferenceResolver,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test resolving a simple reference."""
        mock_data_loader.get_by_index.return_value = sample_data["magic-schools"][0]

        reference = {
            "index": "evocation",
            "name": "Evocation",
            "url": "/api/magic-schools/evocation",
        }

        result = resolver.resolve_reference(reference)

        assert result == sample_data["magic-schools"][0]
        mock_data_loader.get_by_index.assert_called_once_with(
            "magic-schools", "evocation"
        )

    def test_resolve_reference_cached(
        self,
        resolver: D5eReferenceResolver,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test that resolved references are cached."""
        mock_data_loader.get_by_index.return_value = sample_data["magic-schools"][0]

        reference = {
            "index": "evocation",
            "name": "Evocation",
            "url": "/api/magic-schools/evocation",
        }

        # First resolution
        result1 = resolver.resolve_reference(reference)
        # Second resolution (should use cache)
        result2 = resolver.resolve_reference(reference)

        assert result1 == result2
        # Should only call data loader once
        assert mock_data_loader.get_by_index.call_count == 1

    def test_resolve_reference_not_found(
        self, resolver: D5eReferenceResolver, mock_data_loader: Mock
    ) -> None:
        """Test handling of non-existent reference."""
        mock_data_loader.get_by_index.return_value = None

        reference = {
            "index": "nonexistent",
            "name": "Nonexistent",
            "url": "/api/spells/nonexistent",
        }

        with pytest.raises(ReferenceNotFoundError, match="Reference not found"):
            resolver.resolve_reference(reference)

    def test_resolve_deep_nested(
        self,
        resolver: D5eReferenceResolver,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test resolving an object with nested references."""

        # Set up mock to return different data based on category and index
        def mock_get_by_index(category: str, index: str) -> Optional[Dict[str, Any]]:
            if category == "spells" and index == "fireball":
                # Return spell data without nested references
                return {
                    "index": "fireball",
                    "name": "Fireball",
                    "url": "/api/spells/fireball",
                    "level": 3,
                    "description": "A bright streak...",
                }
            elif category == "magic-schools" and index == "evocation":
                return sample_data["magic-schools"][0]
            elif category == "classes" and index == "wizard":
                # Return class data without the spellcasting reference
                return {
                    "index": "wizard",
                    "name": "Wizard",
                    "url": "/api/classes/wizard",
                    "hit_die": 6,
                }
            return None

        mock_data_loader.get_by_index.side_effect = mock_get_by_index

        # Create object with nested references
        obj = {
            "name": "Test Spell",
            "school": {
                "index": "evocation",
                "name": "Evocation",
                "url": "/api/magic-schools/evocation",
            },
            "classes": [
                {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"}
            ],
        }

        result = resolver.resolve_deep(obj)

        # Check that references were resolved
        assert "desc" in result["school"]
        assert result["school"]["desc"] == "Evocation spells manipulate energy..."
        assert "hit_die" in result["classes"][0]
        assert result["classes"][0]["hit_die"] == 6

    def test_resolve_deep_max_depth(
        self, resolver: D5eReferenceResolver, mock_data_loader: Mock
    ) -> None:
        """Test max depth limit to prevent infinite recursion."""
        # Create a reference that would resolve to itself
        circular_ref = {
            "index": "circular",
            "name": "Circular",
            "url": "/api/test/circular",
        }

        obj = {"ref": circular_ref}

        # Max depth = 0 should prevent any resolution
        result = resolver.resolve_deep(obj, max_depth=0)

        # At max depth, references should not be resolved
        assert result["ref"] == circular_ref

    def test_detect_circular_reference(
        self, resolver: D5eReferenceResolver, mock_data_loader: Mock
    ) -> None:
        """Test detection of circular references."""

        # Set up circular reference: A -> B -> A
        def mock_get_by_index(category: str, index: str) -> Optional[Dict[str, Any]]:
            if category == "test" and index == "a":
                return {
                    "index": "a",
                    "name": "A",
                    "url": "/api/test/a",
                    "ref": {"index": "b", "name": "B", "url": "/api/test/b"},
                }
            elif category == "test" and index == "b":
                return {
                    "index": "b",
                    "name": "B",
                    "url": "/api/test/b",
                    "ref": {"index": "a", "name": "A", "url": "/api/test/a"},
                }
            return None

        mock_data_loader.get_by_index.side_effect = mock_get_by_index

        obj = {"ref": {"index": "a", "name": "A", "url": "/api/test/a"}}

        with pytest.raises(CircularReferenceError, match="Circular reference detected"):
            resolver.resolve_deep(obj)

    def test_clear_cache(
        self,
        resolver: D5eReferenceResolver,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test clearing the reference cache."""
        mock_data_loader.get_by_index.return_value = sample_data["magic-schools"][0]

        reference = {
            "index": "evocation",
            "name": "Evocation",
            "url": "/api/magic-schools/evocation",
        }

        # Resolve to populate cache
        resolver.resolve_reference(reference)
        assert len(resolver._reference_cache) == 1

        # Clear cache
        resolver.clear_cache()
        assert len(resolver._reference_cache) == 0

        # Next resolution should call data loader again
        resolver.resolve_reference(reference)
        assert mock_data_loader.get_by_index.call_count == 2

    def test_resolve_deep_with_lists(
        self,
        resolver: D5eReferenceResolver,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test resolving references within lists."""
        # Return class data without nested references
        mock_data_loader.get_by_index.return_value = {
            "index": "wizard",
            "name": "Wizard",
            "url": "/api/classes/wizard",
            "hit_die": 6,
        }

        obj = {
            "name": "Test",
            "classes": [
                {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"}
            ],
            "other_list": [1, 2, "string", None],
        }

        result = resolver.resolve_deep(obj)

        # Check that reference in list was resolved
        assert result["classes"][0]["hit_die"] == 6
        # Check that non-reference list items are preserved
        assert result["other_list"] == [1, 2, "string", None]

    def test_resolve_deep_preserve_non_references(
        self, resolver: D5eReferenceResolver, mock_data_loader: Mock
    ) -> None:
        """Test that non-reference values are preserved."""
        obj = {
            "name": "Test Object",
            "number": 42,
            "boolean": True,
            "null_value": None,
            "array": [1, 2, 3],
            "nested": {"key": "value"},
        }

        result = resolver.resolve_deep(obj)

        # All non-reference values should be preserved
        assert result == obj

    @pytest.mark.parametrize(
        "url,expected_category,expected_index",
        [
            ("/api/spells/fireball", "spells", "fireball"),
            ("/api/magic-schools/evocation", "magic-schools", "evocation"),
            ("/api/classes/wizard", "classes", "wizard"),
            ("/api/equipment/longsword", "equipment", "longsword"),
            ("/api/monsters/ancient-red-dragon", "monsters", "ancient-red-dragon"),
        ],
    )
    def test_parse_various_urls(
        self,
        resolver: D5eReferenceResolver,
        url: str,
        expected_category: str,
        expected_index: str,
    ) -> None:
        """Test parsing various reference URL formats."""
        category, index = resolver._parse_reference_url(url)
        assert category == expected_category
        assert index == expected_index
