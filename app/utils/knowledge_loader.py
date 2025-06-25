"""
Utility functions for loading knowledge data (lore, rulesets, etc.)
Replaces the minimal LoreRepository and RulesetRepository classes.
"""

import json
import logging
import os
from typing import Optional

from app.models.rag import LoreDataModel

logger = logging.getLogger(__name__)


def load_lore_info(
    lore_id: str, index_file_path: str = "app/content/data/knowledge/lores.json"
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
                    # Construct the full path relative to the content data directory
                    base_path = os.path.dirname(index_file_path)
                    full_file_path = os.path.join(base_path, file_path)

                    with open(full_file_path, encoding="utf-8") as lore_file:
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
                    logger.error(f"Error loading lore file {full_file_path}: {e}")
                    return None

        logger.warning(f"Lore {lore_id} not found in {index_file_path}")
        return None

    except Exception as e:
        logger.error(f"Error loading lore info: {e}")
        return None
