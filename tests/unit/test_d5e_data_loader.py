"""Unit tests for D5eDataLoader."""

import json
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, mock_open, patch

import pytest

from app.services.d5e.data_loader import D5eDataLoader


class TestD5eDataLoader:
    """Test suite for D5eDataLoader."""

    @pytest.fixture
    def mock_json_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Mock JSON data for different categories."""
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
                {
                    "index": "wizard",
                    "name": "Wizard",
                    "url": "/api/classes/wizard",
                    "hit_die": 6,
                }
            ],
            "monsters": [
                {
                    "index": "goblin",
                    "name": "Goblin",
                    "url": "/api/monsters/goblin",
                    "challenge_rating": 0.25,
                }
            ],
        }

    @pytest.fixture
    def data_loader(self, tmp_path: Path) -> D5eDataLoader:
        """Create a data loader with a temporary path."""
        return D5eDataLoader(base_path=str(tmp_path))

    def test_init_with_default_path(self) -> None:
        """Test initialization with default path."""
        loader = D5eDataLoader()
        assert loader._base_path == "knowledge/5e-database/src/2014"
        assert loader._cache == {}

    def test_init_with_custom_path(self, tmp_path: Path) -> None:
        """Test initialization with custom path."""
        custom_path = str(tmp_path / "custom")
        loader = D5eDataLoader(base_path=custom_path)
        assert loader._base_path == custom_path
        assert loader._cache == {}

    def test_category_files_mapping(self, data_loader: D5eDataLoader) -> None:
        """Test that all 25 category files are mapped correctly."""
        assert len(data_loader.CATEGORY_FILES) == 25

        # Check some key mappings
        assert data_loader.CATEGORY_FILES["spells"] == "5e-SRD-Spells.json"
        assert data_loader.CATEGORY_FILES["classes"] == "5e-SRD-Classes.json"
        assert data_loader.CATEGORY_FILES["monsters"] == "5e-SRD-Monsters.json"
        assert (
            data_loader.CATEGORY_FILES["ability-scores"] == "5e-SRD-Ability-Scores.json"
        )
        assert (
            data_loader.CATEGORY_FILES["weapon-properties"]
            == "5e-SRD-Weapon-Properties.json"
        )

    def test_load_category_success(
        self,
        data_loader: D5eDataLoader,
        mock_json_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test successful loading of a category."""
        spells_data = json.dumps(mock_json_data["spells"])

        with patch("builtins.open", mock_open(read_data=spells_data)):
            result = data_loader.load_category("spells")

        assert result == mock_json_data["spells"]
        assert len(result) == 2
        assert result[0]["name"] == "Acid Arrow"

    def test_load_category_caching(
        self,
        data_loader: D5eDataLoader,
        mock_json_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test that loaded data is cached."""
        spells_data = json.dumps(mock_json_data["spells"])

        with patch("builtins.open", mock_open(read_data=spells_data)) as mock_file:
            # First load
            result1 = data_loader.load_category("spells")
            # Second load (should use cache)
            result2 = data_loader.load_category("spells")

        # File should only be opened once
        assert mock_file.call_count == 1
        assert result1 == result2
        assert "spells" in data_loader._cache

    def test_load_category_invalid_category(self, data_loader: D5eDataLoader) -> None:
        """Test loading an invalid category."""
        with pytest.raises(ValueError, match="Unknown category: invalid-category"):
            data_loader.load_category("invalid-category")

    def test_load_category_file_not_found(self, data_loader: D5eDataLoader) -> None:
        """Test handling of missing file."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                data_loader.load_category("spells")

    def test_load_category_invalid_json(self, data_loader: D5eDataLoader) -> None:
        """Test handling of invalid JSON."""
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with pytest.raises(json.JSONDecodeError):
                data_loader.load_category("spells")

    def test_get_by_index(
        self,
        data_loader: D5eDataLoader,
        mock_json_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test getting an item by index."""
        spells_data = json.dumps(mock_json_data["spells"])

        with patch("builtins.open", mock_open(read_data=spells_data)):
            result = data_loader.get_by_index("spells", "fireball")

        assert result is not None
        assert result["name"] == "Fireball"
        assert result["index"] == "fireball"

    def test_get_by_index_not_found(
        self,
        data_loader: D5eDataLoader,
        mock_json_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test getting non-existent item by index."""
        spells_data = json.dumps(mock_json_data["spells"])

        with patch("builtins.open", mock_open(read_data=spells_data)):
            result = data_loader.get_by_index("spells", "nonexistent")

        assert result is None

    def test_clear_cache(
        self,
        data_loader: D5eDataLoader,
        mock_json_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test clearing the cache."""
        spells_data = json.dumps(mock_json_data["spells"])

        with patch("builtins.open", mock_open(read_data=spells_data)):
            # Load data to populate cache
            data_loader.load_category("spells")
            assert "spells" in data_loader._cache

            # Clear cache
            data_loader.clear_cache()
            assert data_loader._cache == {}

    def test_clear_cache_category(
        self,
        data_loader: D5eDataLoader,
        mock_json_data: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Test clearing cache for specific category."""
        spells_data = json.dumps(mock_json_data["spells"])
        classes_data = json.dumps(mock_json_data["classes"])

        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=spells_data).return_value,
                mock_open(read_data=classes_data).return_value,
            ]

            # Load multiple categories
            data_loader.load_category("spells")
            data_loader.load_category("classes")
            assert len(data_loader._cache) == 2

            # Clear only spells
            data_loader.clear_cache("spells")
            assert "spells" not in data_loader._cache
            assert "classes" in data_loader._cache

    def test_get_all_categories(self, data_loader: D5eDataLoader) -> None:
        """Test getting list of all categories."""
        categories = data_loader.get_all_categories()
        assert len(categories) == 25
        assert "spells" in categories
        assert "classes" in categories
        assert "monsters" in categories

    @pytest.mark.parametrize(
        "category,expected_file",
        [
            ("ability-scores", "5e-SRD-Ability-Scores.json"),
            ("alignments", "5e-SRD-Alignments.json"),
            ("backgrounds", "5e-SRD-Backgrounds.json"),
            ("classes", "5e-SRD-Classes.json"),
            ("conditions", "5e-SRD-Conditions.json"),
            ("damage-types", "5e-SRD-Damage-Types.json"),
            ("equipment", "5e-SRD-Equipment.json"),
            ("equipment-categories", "5e-SRD-Equipment-Categories.json"),
            ("feats", "5e-SRD-Feats.json"),
            ("features", "5e-SRD-Features.json"),
            ("languages", "5e-SRD-Languages.json"),
            ("levels", "5e-SRD-Levels.json"),
            ("magic-items", "5e-SRD-Magic-Items.json"),
            ("magic-schools", "5e-SRD-Magic-Schools.json"),
            ("monsters", "5e-SRD-Monsters.json"),
            ("proficiencies", "5e-SRD-Proficiencies.json"),
            ("races", "5e-SRD-Races.json"),
            ("rules", "5e-SRD-Rules.json"),
            ("rule-sections", "5e-SRD-Rule-Sections.json"),
            ("skills", "5e-SRD-Skills.json"),
            ("spells", "5e-SRD-Spells.json"),
            ("subclasses", "5e-SRD-Subclasses.json"),
            ("subraces", "5e-SRD-Subraces.json"),
            ("traits", "5e-SRD-Traits.json"),
            ("weapon-properties", "5e-SRD-Weapon-Properties.json"),
        ],
    )
    def test_all_category_mappings(
        self, data_loader: D5eDataLoader, category: str, expected_file: str
    ) -> None:
        """Test that all categories map to correct files."""
        assert data_loader.CATEGORY_FILES[category] == expected_file
