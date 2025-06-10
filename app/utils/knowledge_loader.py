"""
Utility functions for loading knowledge data (lore, rulesets, etc.)
Replaces the minimal LoreRepository and RulesetRepository classes.
"""

import json
import logging
from typing import List, Optional

from app.models.models import LoreDataModel, RulesetDataModel

logger = logging.getLogger(__name__)


def load_lore_info(
    lore_id: str, index_file_path: str = "knowledge/lores.json"
) -> Optional[LoreDataModel]:
    """
    Load information about a specific lore entry.

    Args:
        lore_id: The ID of the lore to load
        index_file_path: Path to the lores index file

    Returns:
        LoreDataModel with lore information or None if not found
    """
    try:
        with open(index_file_path, encoding="utf-8") as f:
            lores_data = json.load(f)

        # Validate that we have a list
        if not isinstance(lores_data, list):
            logger.error(f"Expected list in {index_file_path}, got {type(lores_data)}")
            return None

        for lore_dict in lores_data:
            if not isinstance(lore_dict, dict):
                continue
            if lore_dict.get("id") == lore_id:
                # Found the lore entry, now load the actual content from file
                file_path = lore_dict.get("file_path")
                if not file_path:
                    logger.error(f"No file_path for lore {lore_id}")
                    return None

                try:
                    with open(file_path, encoding="utf-8") as lore_file:
                        lore_content = json.load(lore_file)

                    # Convert the lore content to a string representation
                    # The lore file contains nested JSON, so we'll format it nicely
                    content_parts = []
                    for section_name, section_data in lore_content.items():
                        content_parts.append(
                            f"\n## {section_name.replace('_', ' ').title()}"
                        )
                        if isinstance(section_data, dict):
                            for key, value in section_data.items():
                                content_parts.append(
                                    f"\n### {key.replace('_', ' ').title()}"
                                )
                                content_parts.append(f"{value}")
                        else:
                            content_parts.append(str(section_data))

                    # Create LoreDataModel with the loaded content
                    return LoreDataModel(
                        id=lore_id,
                        name=lore_dict.get("name", lore_id),
                        description=f"Lore content from {file_path}",
                        content="\n".join(content_parts),
                        tags=[],  # Could extract from content if needed
                        category="lore",
                    )

                except Exception as e:
                    logger.error(f"Error loading lore file {file_path}: {e}")
                    return None

        logger.warning(f"Lore {lore_id} not found in {index_file_path}")
        return None

    except Exception as e:
        logger.error(f"Error loading lore info: {e}")
        return None


def load_all_lores(
    index_file_path: str = "knowledge/lores.json",
) -> List[LoreDataModel]:
    """
    Load all available lore entries.

    Args:
        index_file_path: Path to the lores index file

    Returns:
        List of LoreDataModel entries
    """
    try:
        with open(index_file_path, encoding="utf-8") as f:
            lores_data = json.load(f)

        # Validate that we have a list
        if not isinstance(lores_data, list):
            logger.error(f"Expected list in {index_file_path}, got {type(lores_data)}")
            return []

        # Convert each dict to LoreDataModel
        lores = []
        for lore_dict in lores_data:
            if isinstance(lore_dict, dict):
                try:
                    lore_id = lore_dict.get("id")
                    if lore_id:
                        lore_model = load_lore_info(lore_id, index_file_path)
                        if lore_model:
                            lores.append(lore_model)
                except Exception as e:
                    logger.warning(f"Failed to parse lore entry: {e}")
                    continue
        return lores
    except Exception as e:
        logger.error(f"Error loading lores: {e}")
        return []


def load_ruleset_info(
    ruleset_id: str, index_file_path: str = "knowledge/rulesets.json"
) -> Optional[RulesetDataModel]:
    """
    Load information about a specific ruleset.

    Args:
        ruleset_id: The ID of the ruleset to load
        index_file_path: Path to the rulesets index file

    Returns:
        RulesetDataModel with ruleset information or None if not found
    """
    try:
        with open(index_file_path, encoding="utf-8") as f:
            rulesets_data = json.load(f)

        # Validate that we have a list
        if not isinstance(rulesets_data, list):
            logger.error(
                f"Expected list in {index_file_path}, got {type(rulesets_data)}"
            )
            return None

        for ruleset_dict in rulesets_data:
            if not isinstance(ruleset_dict, dict):
                continue
            if ruleset_dict.get("id") == ruleset_id:
                return RulesetDataModel(**ruleset_dict)

        logger.warning(f"Ruleset {ruleset_id} not found in {index_file_path}")
        return None

    except Exception as e:
        logger.error(f"Error loading ruleset info: {e}")
        return None


def load_all_rulesets(
    index_file_path: str = "knowledge/rulesets.json",
) -> List[RulesetDataModel]:
    """
    Load all available rulesets.

    Args:
        index_file_path: Path to the rulesets index file

    Returns:
        List of RulesetDataModel entries
    """
    try:
        with open(index_file_path, encoding="utf-8") as f:
            rulesets_data = json.load(f)

        # Validate that we have a list
        if not isinstance(rulesets_data, list):
            logger.error(
                f"Expected list in {index_file_path}, got {type(rulesets_data)}"
            )
            return []

        # Convert each dict to RulesetDataModel
        rulesets = []
        for ruleset_dict in rulesets_data:
            if isinstance(ruleset_dict, dict):
                try:
                    rulesets.append(RulesetDataModel(**ruleset_dict))
                except Exception as e:
                    logger.warning(f"Failed to parse ruleset entry: {e}")
                    continue
        return rulesets
    except Exception as e:
        logger.error(f"Error loading rulesets: {e}")
        return []
