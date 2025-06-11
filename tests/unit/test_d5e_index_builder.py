"""Unit tests for D5eIndexBuilder."""

from typing import Any, Dict, List
from unittest.mock import Mock, create_autospec

import pytest

from app.services.d5e.data_loader import D5eDataLoader
from app.services.d5e.index_builder import D5eIndexBuilder


class TestD5eIndexBuilder:
    """Test suite for D5eIndexBuilder."""

    @pytest.fixture
    def mock_data_loader(self) -> Mock:
        """Create a mock data loader."""
        mock: Mock = create_autospec(D5eDataLoader, instance=True)
        return mock

    @pytest.fixture
    def sample_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Sample data for testing."""
        return {
            "spells": [
                {
                    "index": "acid-arrow",
                    "name": "Acid Arrow",
                    "url": "/api/spells/acid-arrow",
                },
                {
                    "index": "fireball",
                    "name": "Fireball",
                    "url": "/api/spells/fireball",
                },
            ],
            "classes": [
                {"index": "wizard", "name": "Wizard", "url": "/api/classes/wizard"},
                {"index": "fighter", "name": "Fighter", "url": "/api/classes/fighter"},
            ],
        }

    @pytest.fixture
    def index_builder(self, mock_data_loader: Mock) -> D5eIndexBuilder:
        """Create an index builder with mock data loader."""
        return D5eIndexBuilder(mock_data_loader)

    def test_init(self, mock_data_loader: Mock) -> None:
        """Test initialization."""
        builder = D5eIndexBuilder(mock_data_loader)
        assert builder._data_loader is mock_data_loader
        assert builder._indices == {}
        assert builder._name_indices == {}

    def test_build_indices(
        self,
        index_builder: D5eIndexBuilder,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test building indices for all categories."""
        # Mock the data loader to return our sample data
        mock_data_loader.get_all_categories.return_value = ["spells", "classes"]
        mock_data_loader.load_category.side_effect = lambda cat: sample_data.get(
            cat, []
        )

        indices = index_builder.build_indices()

        # Check that indices were built correctly
        assert "spells" in indices
        assert "classes" in indices
        assert indices["spells"]["acid-arrow"]["name"] == "Acid Arrow"
        assert indices["spells"]["fireball"]["name"] == "Fireball"
        assert indices["classes"]["wizard"]["name"] == "Wizard"
        assert indices["classes"]["fighter"]["name"] == "Fighter"

        # Check that data loader was called correctly
        mock_data_loader.get_all_categories.assert_called_once()
        assert mock_data_loader.load_category.call_count == 2

    def test_build_indices_caching(
        self,
        index_builder: D5eIndexBuilder,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test that indices are cached after building."""
        mock_data_loader.get_all_categories.return_value = ["spells"]
        mock_data_loader.load_category.return_value = sample_data["spells"]

        # First call
        indices1 = index_builder.build_indices()
        # Second call (should use cache)
        indices2 = index_builder.build_indices()

        assert indices1 is indices2
        # Data loader should only be called once
        mock_data_loader.get_all_categories.assert_called_once()
        mock_data_loader.load_category.assert_called_once()

    def test_build_indices_force_rebuild(
        self,
        index_builder: D5eIndexBuilder,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test forcing a rebuild of indices."""
        mock_data_loader.get_all_categories.return_value = ["spells"]
        mock_data_loader.load_category.return_value = sample_data["spells"]

        # First call
        index_builder.build_indices()
        # Second call with force_rebuild
        index_builder.build_indices(force_rebuild=True)

        # Data loader should be called twice
        assert mock_data_loader.get_all_categories.call_count == 2
        assert mock_data_loader.load_category.call_count == 2

    def test_get_by_index(
        self,
        index_builder: D5eIndexBuilder,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test getting an item by index."""
        mock_data_loader.get_all_categories.return_value = ["spells"]
        mock_data_loader.load_category.return_value = sample_data["spells"]

        result = index_builder.get_by_index("spells", "fireball")

        assert result is not None
        assert result["name"] == "Fireball"

    def test_get_by_index_not_found(
        self, index_builder: D5eIndexBuilder, mock_data_loader: Mock
    ) -> None:
        """Test getting non-existent item by index."""
        mock_data_loader.get_all_categories.return_value = []

        result = index_builder.get_by_index("spells", "nonexistent")

        assert result is None

    def test_get_by_name(
        self,
        index_builder: D5eIndexBuilder,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test getting an item by name (case-insensitive)."""
        mock_data_loader.get_all_categories.return_value = ["spells"]
        mock_data_loader.load_category.return_value = sample_data["spells"]

        # Test exact match
        result = index_builder.get_by_name("spells", "Fireball")
        assert result is not None
        assert result["index"] == "fireball"

        # Test case-insensitive match
        result = index_builder.get_by_name("spells", "FIREBALL")
        assert result is not None
        assert result["index"] == "fireball"

        # Test with extra spaces
        result = index_builder.get_by_name("spells", " Fireball ")
        assert result is not None
        assert result["index"] == "fireball"

    def test_get_by_name_not_found(
        self,
        index_builder: D5eIndexBuilder,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test getting non-existent item by name."""
        mock_data_loader.get_all_categories.return_value = ["spells"]
        mock_data_loader.load_category.return_value = sample_data["spells"]

        result = index_builder.get_by_name("spells", "Nonexistent Spell")

        assert result is None

    def test_search(
        self,
        index_builder: D5eIndexBuilder,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test searching for items by partial name."""
        mock_data_loader.get_all_categories.return_value = ["spells"]
        mock_data_loader.load_category.return_value = sample_data["spells"]

        # Search for "fire" should find "Fireball"
        results = index_builder.search("spells", "fire")

        assert len(results) == 1
        assert results[0]["name"] == "Fireball"

    def test_search_case_insensitive(
        self,
        index_builder: D5eIndexBuilder,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test case-insensitive search."""
        mock_data_loader.get_all_categories.return_value = ["spells"]
        mock_data_loader.load_category.return_value = sample_data["spells"]

        # Search should be case-insensitive
        results = index_builder.search("spells", "FIRE")

        assert len(results) == 1
        assert results[0]["name"] == "Fireball"

    def test_search_multiple_results(
        self,
        index_builder: D5eIndexBuilder,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test search returning multiple results."""
        mock_data_loader.get_all_categories.return_value = ["spells"]
        mock_data_loader.load_category.return_value = sample_data["spells"]

        # Search for "a" should find both spells
        results = index_builder.search("spells", "a")

        assert len(results) == 2
        names = [r["name"] for r in results]
        assert "Acid Arrow" in names
        assert "Fireball" in names

    def test_search_no_results(
        self,
        index_builder: D5eIndexBuilder,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test search with no results."""
        mock_data_loader.get_all_categories.return_value = ["spells"]
        mock_data_loader.load_category.return_value = sample_data["spells"]

        results = index_builder.search("spells", "xyz")

        assert results == []

    def test_get_all_in_category(
        self,
        index_builder: D5eIndexBuilder,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test getting all items in a category."""
        mock_data_loader.get_all_categories.return_value = ["spells", "classes"]
        mock_data_loader.load_category.side_effect = lambda cat: sample_data.get(
            cat, []
        )

        spells = index_builder.get_all_in_category("spells")
        classes = index_builder.get_all_in_category("classes")

        assert len(spells) == 2
        assert len(classes) == 2
        assert all(item["url"].startswith("/api/spells/") for item in spells)
        assert all(item["url"].startswith("/api/classes/") for item in classes)

    def test_get_all_in_category_unknown(
        self, index_builder: D5eIndexBuilder, mock_data_loader: Mock
    ) -> None:
        """Test getting all items from unknown category."""
        mock_data_loader.get_all_categories.return_value = []

        results = index_builder.get_all_in_category("unknown")

        assert results == []

    def test_clear_cache(
        self,
        index_builder: D5eIndexBuilder,
        mock_data_loader: Mock,
        sample_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test clearing the index cache."""
        mock_data_loader.get_all_categories.return_value = ["spells"]
        mock_data_loader.load_category.return_value = sample_data["spells"]

        # Build indices
        index_builder.build_indices()
        assert len(index_builder._indices) > 0

        # Clear cache
        index_builder.clear_cache()
        assert index_builder._indices == {}
        assert index_builder._name_indices == {}
