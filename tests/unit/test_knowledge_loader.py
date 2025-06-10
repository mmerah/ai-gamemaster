"""
Unit tests for the knowledge loader utility functions.
"""

import json
import unittest
from typing import Any
from unittest.mock import mock_open, patch

from app.models.models import LoreDataModel, RulesetDataModel
from app.utils.knowledge_loader import (
    load_all_lores,
    load_all_rulesets,
    load_lore_info,
    load_ruleset_info,
)


class TestKnowledgeLoader(unittest.TestCase):
    """Test the knowledge loader utility functions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Sample lores index data
        self.sample_lores_index = [
            {
                "id": "generic_fantasy",
                "name": "Generic Fantasy Lore",
                "file_path": "knowledge/lore/generic_fantasy_lore.json",
            },
            {
                "id": "dark_realm",
                "name": "Dark Realm Lore",
                "file_path": "knowledge/lore/dark_realm_lore.json",
            },
        ]

        # Sample lore content
        self.sample_lore_content = {
            "world_elements": {
                "ancient_magic": "The world is filled with ancient magic.",
                "mystical_creatures": "Dragons and unicorns roam the lands.",
            },
            "history": {
                "the_great_war": "A thousand years ago, a great war shook the realm."
            },
        }

        # Sample rulesets index data
        self.sample_rulesets_index = [
            {
                "id": "dnd5e_standard",
                "name": "D&D 5e Standard Rules",
                "description": "Standard Dungeons & Dragons 5th Edition rules",
                "rules": {
                    "combat": "Standard combat rules",
                    "magic": "Standard magic rules",
                },
                "version": "5e",
                "category": "standard",
            }
        ]

    def test_load_lore_info_success(self) -> None:
        """Test successfully loading a single lore entry."""
        with patch(
            "builtins.open", mock_open(read_data=json.dumps(self.sample_lores_index))
        ) as mock_index:
            # Mock the lore content file
            with patch(
                "builtins.open",
                mock_open(read_data=json.dumps(self.sample_lore_content)),
            ) as mock_content:
                # Configure the mocks to work correctly for both files
                mock_index.return_value.__enter__.return_value.read.return_value = (
                    json.dumps(self.sample_lores_index)
                )
                mock_content.return_value.__enter__.return_value.read.return_value = (
                    json.dumps(self.sample_lore_content)
                )

                # Create a side effect that returns the right mock based on filename
                def open_side_effect(filename: str, *args: Any, **kwargs: Any) -> Any:
                    if "generic_fantasy_lore.json" in filename:
                        return mock_content.return_value
                    else:
                        return mock_index.return_value

                with patch("builtins.open", side_effect=open_side_effect):
                    result = load_lore_info("generic_fantasy")

                    self.assertIsNotNone(result)
                    self.assertIsInstance(result, LoreDataModel)
                    assert result is not None  # Type guard for mypy
                    self.assertEqual(result.id, "generic_fantasy")
                    self.assertEqual(result.name, "Generic Fantasy Lore")
                    self.assertIn("World Elements", result.content)
                    self.assertIn("Ancient Magic", result.content)
                    self.assertIn("ancient magic", result.content.lower())

    def test_load_lore_info_not_found(self) -> None:
        """Test loading a lore entry that doesn't exist."""
        with patch(
            "builtins.open", mock_open(read_data=json.dumps(self.sample_lores_index))
        ):
            result = load_lore_info("nonexistent_lore")
            self.assertIsNone(result)

    def test_load_lore_info_missing_file(self) -> None:
        """Test handling when lore file is missing."""
        with patch(
            "builtins.open", mock_open(read_data=json.dumps(self.sample_lores_index))
        ) as mock_index:
            # First call succeeds (index file), second call fails (lore file)
            mock_index.side_effect = [
                mock_index.return_value,
                FileNotFoundError("File not found"),
            ]

            result = load_lore_info("generic_fantasy")
            self.assertIsNone(result)

    def test_load_lore_info_invalid_index_format(self) -> None:
        """Test handling invalid index file format."""
        # Test with non-list data
        with patch("builtins.open", mock_open(read_data=json.dumps({"not": "a list"}))):
            result = load_lore_info("generic_fantasy")
            self.assertIsNone(result)

    def test_load_all_lores_success(self) -> None:
        """Test loading all lore entries."""
        # Mock both index reads and content reads
        call_count = 0

        def mock_open_fn(filename: str, *args: Any, **kwargs: Any) -> Any:
            nonlocal call_count
            call_count += 1

            # First call is for load_all_lores
            if call_count == 1:
                mock = mock_open(read_data=json.dumps(self.sample_lores_index))
                return mock()
            # Subsequent calls alternate between index and content
            elif call_count % 2 == 0:  # Even calls are index files
                mock = mock_open(read_data=json.dumps(self.sample_lores_index))
                return mock()
            else:  # Odd calls are content files
                mock = mock_open(read_data=json.dumps(self.sample_lore_content))
                return mock()

        with patch("builtins.open", side_effect=mock_open_fn):
            result = load_all_lores()

            self.assertIsInstance(result, list)
            # We expect 2 lore entries based on our sample data
            self.assertEqual(len(result), 2)
            self.assertTrue(all(isinstance(lore, LoreDataModel) for lore in result))

    def test_load_all_lores_empty_index(self) -> None:
        """Test loading lores with empty index."""
        with patch("builtins.open", mock_open(read_data=json.dumps([]))):
            result = load_all_lores()
            self.assertEqual(result, [])

    def test_load_all_lores_file_error(self) -> None:
        """Test handling file errors when loading all lores."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            result = load_all_lores()
            self.assertEqual(result, [])

    def test_load_ruleset_info_success(self) -> None:
        """Test successfully loading a single ruleset."""
        with patch(
            "builtins.open", mock_open(read_data=json.dumps(self.sample_rulesets_index))
        ):
            result = load_ruleset_info("dnd5e_standard")

            self.assertIsNotNone(result)
            self.assertIsInstance(result, RulesetDataModel)
            assert result is not None  # Type guard for mypy
            self.assertEqual(result.id, "dnd5e_standard")
            self.assertEqual(result.name, "D&D 5e Standard Rules")

    def test_load_ruleset_info_not_found(self) -> None:
        """Test loading a ruleset that doesn't exist."""
        with patch(
            "builtins.open", mock_open(read_data=json.dumps(self.sample_rulesets_index))
        ):
            result = load_ruleset_info("nonexistent_ruleset")
            self.assertIsNone(result)

    def test_load_all_rulesets_success(self) -> None:
        """Test loading all rulesets."""
        with patch(
            "builtins.open", mock_open(read_data=json.dumps(self.sample_rulesets_index))
        ):
            result = load_all_rulesets()

            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], RulesetDataModel)
            self.assertEqual(result[0].id, "dnd5e_standard")

    def test_lore_content_formatting(self) -> None:
        """Test that lore content is properly formatted."""
        # Create lore content with various structures
        complex_lore_content = {
            "world_elements": {
                "ancient_magic": "The world is filled with ancient magic.",
                "mystical_creatures": "Dragons and unicorns roam the lands.",
            },
            "simple_element": "This is a simple string element",
            "history": {
                "the_great_war": "A thousand years ago, a great war shook the realm.",
                "the_peace_treaty": "Peace was achieved through great sacrifice.",
            },
        }

        with patch(
            "builtins.open", mock_open(read_data=json.dumps(self.sample_lores_index))
        ) as mock_index:
            with patch(
                "builtins.open", mock_open(read_data=json.dumps(complex_lore_content))
            ) as mock_content:

                def open_side_effect(filename: str, *args: Any, **kwargs: Any) -> Any:
                    if "generic_fantasy_lore.json" in filename:
                        return mock_content.return_value
                    else:
                        return mock_index.return_value

                with patch("builtins.open", side_effect=open_side_effect):
                    result = load_lore_info("generic_fantasy")

                    self.assertIsNotNone(result)
                    assert result is not None  # Type guard for mypy
                    # Check that sections are properly formatted
                    self.assertIn("## World Elements", result.content)
                    self.assertIn("### Ancient Magic", result.content)
                    self.assertIn("### Mystical Creatures", result.content)
                    self.assertIn("## Simple Element", result.content)
                    self.assertIn("## History", result.content)
                    # Check content is included
                    self.assertIn("ancient magic", result.content.lower())
                    self.assertIn("dragons and unicorns", result.content.lower())
                    self.assertIn("simple string element", result.content.lower())


if __name__ == "__main__":
    unittest.main()
