#!/usr/bin/env python3
"""Migration script for moving user content from system database to user database.

This script migrates user-created content packs from the system database (content.db)
to the user database (user_content.db) as part of the dual database architecture.
"""

import argparse
import logging
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker
from tqdm import tqdm

# Add the parent directory to the path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.content.models import (
    AbilityScore,
    Alignment,
    Background,
    Base,
    CharacterClass,
    Condition,
    ContentPack,
    DamageType,
    Equipment,
    EquipmentCategory,
    Feat,
    Feature,
    Language,
    Level,
    MagicItem,
    MagicSchool,
    Monster,
    Proficiency,
    Race,
    Rule,
    RuleSection,
    Skill,
    Spell,
    Subclass,
    Subrace,
    Trait,
    WeaponProperty,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Base)


class UserContentMigrator:
    """Migrates user content from system database to user database."""

    # Content models that may have user content
    CONTENT_MODELS = [
        AbilityScore,
        Alignment,
        Background,
        CharacterClass,
        Condition,
        DamageType,
        Equipment,
        EquipmentCategory,
        Feat,
        Feature,
        Language,
        Level,
        MagicItem,
        MagicSchool,
        Monster,
        Proficiency,
        Race,
        Rule,
        RuleSection,
        Skill,
        Spell,
        Subclass,
        Subrace,
        Trait,
        WeaponProperty,
    ]

    # System content pack IDs that should NOT be migrated
    SYSTEM_PACK_IDS = ["dnd_5e_srd"]

    def __init__(
        self,
        system_db_url: str,
        user_db_url: str,
        dry_run: bool = False,
        create_backup: bool = True,
    ):
        """Initialize the migrator.

        Args:
            system_db_url: SQLAlchemy URL for system database
            user_db_url: SQLAlchemy URL for user database
            dry_run: If True, only report what would be migrated
            create_backup: If True, create backups before migration
        """
        self.system_db_url = system_db_url
        self.user_db_url = user_db_url
        self.dry_run = dry_run
        self.should_create_backup = create_backup

        # Create engines
        self.system_engine = create_engine(system_db_url)
        self.user_engine = create_engine(user_db_url)

        # Configure SQLite pragmas if using SQLite
        for engine, db_type in [
            (self.system_engine, "system"),
            (self.user_engine, "user"),
        ]:
            if str(engine.url).startswith("sqlite://"):

                @event.listens_for(engine, "connect")
                def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA busy_timeout=10000")
                    cursor.close()

        # Create sessions
        SystemSession = sessionmaker(bind=self.system_engine)
        UserSession = sessionmaker(bind=self.user_engine)
        self.system_session = SystemSession()
        self.user_session = UserSession()

        # Ensure user database schema exists
        self._ensure_user_db_schema()

    def _ensure_user_db_schema(self) -> None:
        """Ensure the user database has the required schema."""
        logger.info("Ensuring user database schema exists...")
        Base.metadata.create_all(self.user_engine)
        logger.info("User database schema ready")

    def create_backup(self, database_path: Path) -> Optional[Path]:
        """Create a backup of the database file.

        Args:
            database_path: Path to the database file

        Returns:
            Path to the backup file, or None if not applicable
        """
        if not self.should_create_backup or not database_path.exists():
            return None

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = (
            database_path.parent
            / f"{database_path.stem}_pre_migration_{timestamp}{database_path.suffix}"
        )

        try:
            shutil.copy2(database_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def find_user_content_packs(self) -> List[ContentPack]:
        """Find all user content packs in the system database.

        Returns:
            List of ContentPack objects that are user-created
        """
        user_packs = (
            self.system_session.query(ContentPack)
            .filter(~ContentPack.id.in_(self.SYSTEM_PACK_IDS))
            .all()
        )

        logger.info(f"Found {len(user_packs)} user content pack(s) to migrate")
        for pack in user_packs:
            logger.info(f"  - {pack.id}: {pack.name} by {pack.author}")

        return user_packs

    def count_pack_content(self, pack_id: str) -> Dict[str, int]:
        """Count content items for a specific pack.

        Args:
            pack_id: Content pack ID

        Returns:
            Dictionary mapping content type names to counts
        """
        counts = {}
        for model_class in self.CONTENT_MODELS:
            count = (
                self.system_session.query(model_class)
                .filter_by(content_pack_id=pack_id)
                .count()
            )
            if count > 0:
                counts[model_class.__tablename__] = count
        return counts

    def copy_pack_content(
        self, pack: ContentPack, progress_bar: Optional[tqdm] = None
    ) -> Tuple[int, Dict[str, int]]:
        """Copy a content pack and all its content to the user database.

        Args:
            pack: ContentPack to copy
            progress_bar: Optional progress bar for updates

        Returns:
            Tuple of (total items copied, dict of counts by type)
        """
        if self.dry_run:
            pack_id = str(pack.id)
            counts = self.count_pack_content(pack_id)
            total = sum(counts.values())
            logger.info(f"Would copy {total} items for pack {pack_id}")
            for table, count in counts.items():
                logger.info(f"  - {table}: {count} items")
            return 0, counts

        # Start transaction
        savepoint = self.user_session.begin_nested()

        try:
            # Copy the content pack itself
            new_pack = ContentPack(
                id=pack.id,
                name=pack.name,
                description=pack.description,
                version=pack.version,
                author=pack.author,
                is_active=pack.is_active,
                created_at=pack.created_at,
                updated_at=pack.updated_at,
            )
            self.user_session.add(new_pack)
            self.user_session.flush()

            # Copy all related content
            total_copied = 0
            counts_by_type = {}

            for model_class in self.CONTENT_MODELS:
                # Query items for this pack
                items = (
                    self.system_session.query(model_class)
                    .filter_by(content_pack_id=pack.id)
                    .all()
                )

                if items:
                    logger.info(
                        f"  Copying {len(items)} {model_class.__tablename__} items..."
                    )
                    counts_by_type[model_class.__tablename__] = len(items)

                    for item in items:
                        # Create a new instance with all attributes
                        item_dict = {
                            key: getattr(item, key)
                            for key in item.__mapper__.attrs.keys()
                            if not key.startswith("_")
                        }
                        new_item = model_class(**item_dict)
                        self.user_session.add(new_item)
                        total_copied += 1

                        if progress_bar:
                            progress_bar.update(1)

            # Commit the transaction
            savepoint.commit()
            logger.info(f"Successfully copied {total_copied} items for pack {pack.id}")

            return total_copied, counts_by_type

        except Exception as e:
            savepoint.rollback()
            logger.error(f"Failed to copy pack {pack.id}: {e}")
            raise

    def delete_pack_from_system(self, pack_id: str) -> int:
        """Delete a content pack and all its content from the system database.

        Args:
            pack_id: Content pack ID to delete

        Returns:
            Total number of items deleted
        """
        if self.dry_run:
            counts = self.count_pack_content(pack_id)
            total = sum(counts.values()) + 1  # +1 for the pack itself
            logger.info(f"Would delete {total} items for pack {pack_id}")
            return 0

        # Start transaction
        savepoint = self.system_session.begin_nested()

        try:
            total_deleted = 0

            # Delete all related content
            for model_class in self.CONTENT_MODELS:
                deleted = (
                    self.system_session.query(model_class)
                    .filter_by(content_pack_id=pack_id)
                    .delete()
                )
                if deleted > 0:
                    logger.info(
                        f"  Deleted {deleted} {model_class.__tablename__} items"
                    )
                    total_deleted += deleted

            # Delete the content pack itself
            pack = self.system_session.query(ContentPack).filter_by(id=pack_id).first()
            if pack:
                self.system_session.delete(pack)
                total_deleted += 1

            # Commit the transaction
            savepoint.commit()
            logger.info(
                f"Successfully deleted {total_deleted} items for pack {pack_id}"
            )

            return total_deleted

        except Exception as e:
            savepoint.rollback()
            logger.error(f"Failed to delete pack {pack_id}: {e}")
            raise

    def migrate_all(self) -> None:
        """Migrate all user content from system to user database."""
        logger.info("\n=== User Content Migration ===\n")

        # Create backups if requested
        backup_paths = []
        if self.should_create_backup and not self.dry_run:
            for db_url, db_name in [
                (self.system_db_url, "system"),
                (self.user_db_url, "user"),
            ]:
                if db_url.startswith("sqlite:///"):
                    db_path = Path(db_url.replace("sqlite:///", "").split("?")[0])
                    backup_path = self.create_backup(db_path)
                    if backup_path:
                        backup_paths.append((db_name, backup_path))

        # Find user content packs
        user_packs = self.find_user_content_packs()

        if not user_packs:
            logger.info("No user content packs found to migrate")
            return

        # Count total items to migrate
        total_items = 0
        for pack in user_packs:
            counts = self.count_pack_content(str(pack.id))
            total_items += sum(counts.values()) + 1  # +1 for pack itself

        if self.dry_run:
            logger.info(f"\nDry run: Would migrate {total_items} total items")
            return

        # Migrate each pack
        with tqdm(total=total_items, desc="Migrating items", unit="item") as pbar:
            for pack in user_packs:
                logger.info(f"\nMigrating pack: {pack.id}")

                try:
                    # Copy to user database
                    copied, counts = self.copy_pack_content(pack, pbar)
                    pbar.update(1)  # For the pack itself

                    # Delete from system database
                    deleted = self.delete_pack_from_system(str(pack.id))

                    # Verify counts match
                    if copied + 1 != deleted:  # +1 for pack itself
                        logger.warning(
                            f"Count mismatch: copied {copied + 1} but deleted {deleted}"
                        )

                except Exception as e:
                    logger.error(f"Failed to migrate pack {pack.id}: {e}")
                    self.system_session.rollback()
                    self.user_session.rollback()
                    raise

        # Commit all changes
        try:
            self.system_session.commit()
            self.user_session.commit()
            logger.info(f"\n✓ Successfully migrated {total_items} items")

            if backup_paths:
                logger.info("\nBackups created:")
                for db_name, path in backup_paths:
                    logger.info(f"  - {db_name}: {path}")

        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            self.system_session.rollback()
            self.user_session.rollback()
            raise

        finally:
            self.system_session.close()
            self.user_session.close()

    def verify_migration(self) -> bool:
        """Verify that migration was successful.

        Returns:
            True if verification passes
        """
        logger.info("\n=== Verifying Migration ===\n")

        # Check system database has no user content
        system_user_packs = (
            self.system_session.query(ContentPack)
            .filter(~ContentPack.id.in_(self.SYSTEM_PACK_IDS))
            .count()
        )

        if system_user_packs > 0:
            logger.error(
                f"System database still contains {system_user_packs} user pack(s)"
            )
            return False

        logger.info("✓ System database contains only system content")

        # Check user database has expected content
        user_packs = self.user_session.query(ContentPack).all()
        logger.info(f"✓ User database contains {len(user_packs)} pack(s)")

        for pack in user_packs:
            counts = {}
            for model_class in self.CONTENT_MODELS:
                count = (
                    self.user_session.query(model_class)
                    .filter_by(content_pack_id=pack.id)
                    .count()
                )
                if count > 0:
                    counts[model_class.__tablename__] = count

            total = sum(counts.values())
            logger.info(f"  - {pack.id}: {total} content items")

        return True


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate user content from system database to user database"
    )
    parser.add_argument(
        "--system-db",
        default="sqlite:///data/content.db",
        help="System database URL (default: sqlite:///data/content.db)",
    )
    parser.add_argument(
        "--user-db",
        default="sqlite:///data/user_content.db",
        help="User database URL (default: sqlite:///data/user_content.db)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be migrated without making changes",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backups before migration",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify migration status",
    )

    args = parser.parse_args()

    # Initialize migrator
    migrator = UserContentMigrator(
        system_db_url=args.system_db,
        user_db_url=args.user_db,
        dry_run=args.dry_run,
        create_backup=not args.no_backup,
    )

    if args.verify_only:
        success = migrator.verify_migration()
        sys.exit(0 if success else 1)
    else:
        migrator.migrate_all()
        # Always verify after migration
        if not args.dry_run:
            migrator.verify_migration()


if __name__ == "__main__":
    main()
