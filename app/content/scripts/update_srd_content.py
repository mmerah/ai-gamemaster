#!/usr/bin/env python3
"""Update D&D 5e SRD content in the database from updated JSON files.

This script is designed to update existing SRD content when the 5e-database
submodule is updated, without affecting custom content packs.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Type

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

# Add the parent directory to the path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.content.models import Base, BaseContent, ContentPack
from app.content.scripts.migrate_content import EnhancedD5eDataMigrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class D5eContentUpdater(EnhancedD5eDataMigrator):
    """Updates existing D&D 5e SRD content in the database."""

    def __init__(
        self,
        database_url: str,
        json_path: str = "app/content/data/5e-database/src/2014",
    ):
        """Initialize the updater.

        Args:
            database_url: SQLAlchemy database URL
            json_path: Path to the directory containing JSON files
        """
        super().__init__(database_url, json_path)
        self.stats = {
            "added": 0,
            "updated": 0,
            "deleted": 0,
            "unchanged": 0,
            "errors": 0,
        }

    def get_existing_indices(self, table_class: Type[BaseContent]) -> Set[str]:
        """Get all existing indices for a given table in the SRD content pack.

        Args:
            table_class: SQLAlchemy model class

        Returns:
            Set of existing index values
        """
        stmt = select(table_class.index).where(
            table_class.content_pack_id == self.content_pack_id
        )
        result = self.session.execute(stmt)
        return {row[0] for row in result}

    def update_or_create_item(
        self,
        pydantic_model: Any,
        sqlalchemy_class: Type[BaseContent],
        existing_indices: Set[str],
    ) -> str:
        """Update an existing item or create a new one.

        Args:
            pydantic_model: Validated Pydantic model instance
            sqlalchemy_class: SQLAlchemy model class
            existing_indices: Set of existing indices in the database

        Returns:
            Status: 'added', 'updated', or 'unchanged'
        """
        index = pydantic_model.index

        # Check if item exists
        existing = (
            self.session.query(sqlalchemy_class)
            .filter_by(index=index, content_pack_id=self.content_pack_id)
            .first()
        )

        if existing:
            # Convert Pydantic model to dict for comparison
            new_data = self.convert_pydantic_to_sqlalchemy(
                pydantic_model, sqlalchemy_class
            )

            # Compare and update if changed
            changed = False
            for key, value in new_data.__dict__.items():
                if key.startswith("_"):
                    continue
                if hasattr(existing, key) and getattr(existing, key) != value:
                    setattr(existing, key, value)
                    changed = True

            if changed:
                return "updated"
            else:
                return "unchanged"
        else:
            # Create new item
            db_model = self.convert_pydantic_to_sqlalchemy(
                pydantic_model, sqlalchemy_class
            )
            self.session.add(db_model)
            return "added"

    def delete_removed_items(
        self,
        sqlalchemy_class: Type[BaseContent],
        current_indices: Set[str],
        existing_indices: Set[str],
    ) -> int:
        """Delete items that no longer exist in the JSON files.

        Args:
            sqlalchemy_class: SQLAlchemy model class
            current_indices: Indices found in current JSON files
            existing_indices: Indices currently in the database

        Returns:
            Number of items deleted
        """
        removed_indices = existing_indices - current_indices

        if removed_indices:
            stmt = self.session.query(sqlalchemy_class).filter(
                sqlalchemy_class.index.in_(removed_indices),
                sqlalchemy_class.content_pack_id == self.content_pack_id,
            )
            count = stmt.delete(synchronize_session=False)
            return count

        return 0

    def update_file(self, filename: str) -> Tuple[int, int, int, int]:
        """Update data from a single JSON file.

        Args:
            filename: Name of the JSON file

        Returns:
            Tuple of (added, updated, deleted, unchanged) counts
        """
        if filename not in self.FILE_MAPPING:
            logger.warning(f"No mapping found for file: {filename}")
            return 0, 0, 0, 0

        pydantic_class, sqlalchemy_class = self.FILE_MAPPING[filename]

        logger.info(f"Updating {filename}...")

        # Get existing indices
        existing_indices = self.get_existing_indices(sqlalchemy_class)

        # Load and process JSON data
        json_data = self.load_json_file(filename)
        current_indices = set()

        added = updated = unchanged = 0

        for item_data in json_data:
            try:
                # Validate with Pydantic
                pydantic_model = pydantic_class(**item_data)
                current_indices.add(pydantic_model.index)

                # Update or create
                status = self.update_or_create_item(
                    pydantic_model, sqlalchemy_class, existing_indices
                )

                if status == "added":
                    added += 1
                elif status == "updated":
                    updated += 1
                else:
                    unchanged += 1

            except Exception as e:
                logger.error(
                    f"Error processing item {item_data.get('index', 'unknown')}: {e}"
                )
                self.stats["errors"] += 1

        # Delete removed items
        deleted = self.delete_removed_items(
            sqlalchemy_class, current_indices, existing_indices
        )

        logger.info(
            f"  Added: {added}, Updated: {updated}, "
            f"Deleted: {deleted}, Unchanged: {unchanged}"
        )

        return added, updated, deleted, unchanged

    def update_all(self) -> None:
        """Update all data files."""
        # Verify content pack exists
        content_pack = (
            self.session.query(ContentPack).filter_by(id=self.content_pack_id).first()
        )

        if not content_pack:
            raise ValueError(
                f"Content pack '{self.content_pack_id}' not found. "
                "Run the initial migration first."
            )

        logger.info(f"Updating content pack: {content_pack.name}")

        # Update each file
        for filename in self.FILE_MAPPING:
            try:
                added, updated, deleted, unchanged = self.update_file(filename)
                self.stats["added"] += added
                self.stats["updated"] += updated
                self.stats["deleted"] += deleted
                self.stats["unchanged"] += unchanged
            except Exception as e:
                logger.error(f"Failed to update {filename}: {e}")
                self.session.rollback()
                raise

        # Commit all changes
        try:
            self.session.commit()
            logger.info("\nUpdate Summary:")
            logger.info(f"  Items added: {self.stats['added']}")
            logger.info(f"  Items updated: {self.stats['updated']}")
            logger.info(f"  Items deleted: {self.stats['deleted']}")
            logger.info(f"  Items unchanged: {self.stats['unchanged']}")
            logger.info(f"  Errors: {self.stats['errors']}")
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            self.session.rollback()
            raise
        finally:
            self.session.close()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update D&D 5e SRD content in the database"
    )
    parser.add_argument(
        "database_url",
        help="SQLAlchemy database URL (e.g., sqlite:///data/content.db)",
    )
    parser.add_argument(
        "--json-path",
        default="app/content/data/5e-database/src/2014",
        help="Path to JSON files directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )

    args = parser.parse_args()

    # Run updater
    updater = D5eContentUpdater(args.database_url, args.json_path)

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        # TODO: Implement dry run logic

    updater.update_all()


if __name__ == "__main__":
    main()
