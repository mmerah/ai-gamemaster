#!/usr/bin/env python3
"""Enhanced migration script for D&D 5e data with robustness features.

This script includes:
- Idempotency checks to prevent duplicates
- Transaction safety with savepoints
- Progress tracking with tqdm
- Migration history tracking
- Rollback capability
- Status reporting with --check-only
- Automatic backup creation
"""

import argparse
import hashlib
import json
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
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.models import (
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
    MigrationHistory,
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
from app.models.d5e import (
    D5eAbilityScore,
    D5eAlignment,
    D5eBackground,
    D5eClass,
    D5eCondition,
    D5eDamageType,
    D5eEquipment,
    D5eEquipmentCategory,
    D5eFeat,
    D5eFeature,
    D5eLanguage,
    D5eLevel,
    D5eMagicItem,
    D5eMagicSchool,
    D5eMonster,
    D5eProficiency,
    D5eRace,
    D5eRule,
    D5eRuleSection,
    D5eSkill,
    D5eSpell,
    D5eSubclass,
    D5eSubrace,
    D5eTrait,
    D5eWeaponProperty,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T")


class EnhancedD5eDataMigrator:
    """Enhanced migrator with robustness features."""

    # Mapping of file names to their corresponding Pydantic and SQLAlchemy models
    FILE_MAPPING = {
        "5e-SRD-Ability-Scores.json": (D5eAbilityScore, AbilityScore),
        "5e-SRD-Alignments.json": (D5eAlignment, Alignment),
        "5e-SRD-Backgrounds.json": (D5eBackground, Background),
        "5e-SRD-Classes.json": (D5eClass, CharacterClass),
        "5e-SRD-Conditions.json": (D5eCondition, Condition),
        "5e-SRD-Damage-Types.json": (D5eDamageType, DamageType),
        "5e-SRD-Equipment.json": (D5eEquipment, Equipment),
        "5e-SRD-Equipment-Categories.json": (D5eEquipmentCategory, EquipmentCategory),
        "5e-SRD-Feats.json": (D5eFeat, Feat),
        "5e-SRD-Features.json": (D5eFeature, Feature),
        "5e-SRD-Languages.json": (D5eLanguage, Language),
        "5e-SRD-Levels.json": (D5eLevel, Level),
        "5e-SRD-Magic-Items.json": (D5eMagicItem, MagicItem),
        "5e-SRD-Magic-Schools.json": (D5eMagicSchool, MagicSchool),
        "5e-SRD-Monsters.json": (D5eMonster, Monster),
        "5e-SRD-Proficiencies.json": (D5eProficiency, Proficiency),
        "5e-SRD-Races.json": (D5eRace, Race),
        "5e-SRD-Rules.json": (D5eRule, Rule),
        "5e-SRD-Rule-Sections.json": (D5eRuleSection, RuleSection),
        "5e-SRD-Skills.json": (D5eSkill, Skill),
        "5e-SRD-Spells.json": (D5eSpell, Spell),
        "5e-SRD-Subclasses.json": (D5eSubclass, Subclass),
        "5e-SRD-Subraces.json": (D5eSubrace, Subrace),
        "5e-SRD-Traits.json": (D5eTrait, Trait),
        "5e-SRD-Weapon-Properties.json": (D5eWeaponProperty, WeaponProperty),
    }

    def __init__(
        self,
        database_url: str,
        json_path: str = "knowledge/5e-database/src/2014",
        check_only: bool = False,
        create_backup: bool = True,
    ):
        """Initialize the enhanced migrator.

        Args:
            database_url: SQLAlchemy database URL
            json_path: Path to the directory containing JSON files
            check_only: If True, only report status without making changes
            create_backup: If True, create a backup before migration
        """
        self.database_url = database_url
        self.json_path = Path(json_path)
        self.check_only = check_only
        self.should_create_backup = create_backup

        # Create engine with appropriate settings
        self.engine = create_engine(database_url)

        # Configure SQLite pragmas for better concurrency if using SQLite
        if database_url.startswith("sqlite://"):

            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA busy_timeout=10000")  # 10 second timeout
                cursor.close()

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Content pack ID for D&D 5e SRD
        self.content_pack_id = "dnd_5e_srd"

    def generate_migration_id(self, filename: str) -> str:
        """Generate a unique migration ID for a file.

        Args:
            filename: Name of the file being migrated

        Returns:
            Unique migration ID
        """
        return f"{self.content_pack_id}_{filename}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    def check_migration_status(self, filename: str) -> Optional[MigrationHistory]:
        """Check if a file has already been migrated.

        Args:
            filename: Name of the file to check

        Returns:
            MigrationHistory record if found, None otherwise
        """
        return (
            self.session.query(MigrationHistory)
            .filter_by(content_pack_id=self.content_pack_id, file_name=filename)
            .order_by(MigrationHistory.started_at.desc())
            .first()
        )

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
            / f"{database_path.stem}_backup_{timestamp}{database_path.suffix}"
        )

        try:
            shutil.copy2(database_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def create_content_pack(self) -> bool:
        """Create the D&D 5e SRD content pack.

        Returns:
            True if created or already exists, False on error
        """
        if self.check_only:
            existing = (
                self.session.query(ContentPack)
                .filter_by(id=self.content_pack_id)
                .first()
            )
            if existing:
                logger.info("✓ Content pack already exists")
            else:
                logger.info("✗ Content pack does not exist")
            return bool(existing)

        content_pack = ContentPack(
            id=self.content_pack_id,
            name="D&D 5e SRD",
            description="Official D&D 5e System Reference Document content",
            version="5.1",
            author="Wizards of the Coast",
            is_active=True,
        )

        # Check if it already exists
        existing = (
            self.session.query(ContentPack).filter_by(id=self.content_pack_id).first()
        )
        if existing:
            logger.info("Content pack already exists, skipping creation")
            return True
        else:
            try:
                self.session.add(content_pack)
                self.session.commit()
                logger.info("Created D&D 5e SRD content pack")
                return True
            except Exception as e:
                logger.error(f"Failed to create content pack: {e}")
                self.session.rollback()
                return False

    def load_json_file(self, filename: str) -> List[Dict[str, Any]]:
        """Load data from a JSON file.

        Args:
            filename: Name of the JSON file

        Returns:
            List of items from the JSON file

        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        file_path = self.json_path / filename
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def preprocess_item_data(
        self, item_data: Dict[str, Any], sqlalchemy_class: Type[T]
    ) -> Dict[str, Any]:
        """Preprocess item data before Pydantic validation.

        Args:
            item_data: Raw JSON data
            sqlalchemy_class: SQLAlchemy model class

        Returns:
            Preprocessed data ready for Pydantic validation
        """
        # Make a copy to avoid modifying the original
        data = item_data.copy()

        # No preprocessing needed - Pydantic aliases should handle field mapping
        return data

    def convert_pydantic_to_sqlalchemy(
        self,
        pydantic_model: Any,
        sqlalchemy_class: Type[T],
    ) -> T:
        """Convert a Pydantic model to a SQLAlchemy model.

        Args:
            pydantic_model: Instance of a Pydantic model
            sqlalchemy_class: SQLAlchemy model class

        Returns:
            Instance of the SQLAlchemy model
        """
        # Get the data as a dict, converting Pydantic models to dicts
        data = pydantic_model.model_dump(mode="json")

        # Add the content pack ID
        data["content_pack_id"] = self.content_pack_id
        # Note: migration_id tracking would be available when schema includes the column

        # Handle special field mappings
        if hasattr(sqlalchemy_class, "__tablename__"):
            table_name = sqlalchemy_class.__tablename__

            # For classes table, map class_ref to class_ref
            if table_name == "classes" and "class" in data:
                data["class_ref"] = data.pop("class")

            # For features table, map class_ back to class_ref for database
            if table_name == "features" and "class_" in data:
                data["class_ref"] = data.pop("class_")

        # Get the column names from the SQLAlchemy model
        from sqlalchemy.inspection import inspect

        mapper = inspect(sqlalchemy_class)
        valid_columns = {col.key for col in mapper.columns}

        # Filter data to only include valid columns
        filtered_data = {k: v for k, v in data.items() if k in valid_columns}

        # Create the SQLAlchemy instance
        return sqlalchemy_class(**filtered_data)

    def check_item_exists(
        self, sqlalchemy_class: Type[T], index: str, content_pack_id: str
    ) -> bool:
        """Check if an item already exists in the database.

        Args:
            sqlalchemy_class: SQLAlchemy model class
            index: Index value of the item
            content_pack_id: Content pack ID

        Returns:
            True if item exists, False otherwise
        """
        return (
            self.session.query(sqlalchemy_class)
            .filter_by(index=index, content_pack_id=content_pack_id)
            .first()
            is not None
        )

    def migrate_file(
        self, filename: str, progress_bar: Optional[tqdm] = None
    ) -> Tuple[int, int]:
        """Migrate data from a single JSON file with idempotency.

        Args:
            filename: Name of the JSON file
            progress_bar: Optional progress bar for updates

        Returns:
            Tuple of (items_migrated, items_skipped)
        """
        if filename not in self.FILE_MAPPING:
            logger.warning(f"No mapping found for file: {filename}")
            return 0, 0

        pydantic_class, sqlalchemy_class = self.FILE_MAPPING[filename]

        # Check migration history
        history = self.check_migration_status(filename)
        if history and history.status == "completed":
            logger.info(f"File {filename} already migrated on {history.completed_at}")
            if progress_bar:
                progress_bar.update(1)
            return 0, history.items_count

        # Load JSON data
        try:
            json_data = self.load_json_file(filename)
        except FileNotFoundError:
            logger.warning(f"Skipping {filename}: file not found")
            if progress_bar:
                progress_bar.update(1)
            return 0, 0

        if self.check_only:
            # Count existing items
            existing_count = 0
            for item_data in json_data:
                if self.check_item_exists(
                    sqlalchemy_class, item_data.get("index", ""), self.content_pack_id
                ):
                    existing_count += 1

            total = len(json_data)
            new = total - existing_count
            logger.info(
                f"{filename}: {existing_count}/{total} already migrated, {new} new items"
            )
            if progress_bar:
                progress_bar.update(1)
            return 0, existing_count

        # Create migration history record
        migration_id = self.generate_migration_id(filename)
        history_record = MigrationHistory(
            migration_id=migration_id,
            content_pack_id=self.content_pack_id,
            file_name=filename,
            items_count=0,
            status="pending",
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(history_record)
        self.session.flush()

        logger.info(f"Migrating {filename}...")

        migrated = 0
        skipped = 0
        errors = []

        # Create a savepoint for this file
        savepoint = self.session.begin_nested()

        try:
            for item_data in json_data:
                item_index = item_data.get("index", "unknown")

                try:
                    # Check if item already exists (idempotency)
                    if self.check_item_exists(
                        sqlalchemy_class, item_index, self.content_pack_id
                    ):
                        skipped += 1
                        continue

                    # Apply field mappings before Pydantic validation
                    preprocessed_data = self.preprocess_item_data(
                        item_data, sqlalchemy_class
                    )

                    # Validate with Pydantic
                    pydantic_model = pydantic_class(**preprocessed_data)

                    # Convert to SQLAlchemy
                    db_model = self.convert_pydantic_to_sqlalchemy(
                        pydantic_model, sqlalchemy_class
                    )

                    # Add to session
                    self.session.add(db_model)
                    migrated += 1

                except Exception as e:
                    error_msg = f"Error migrating item {item_index}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    # Continue with other items
                    continue

            # Update history record
            history_record.items_count = migrated
            history_record.status = (
                "completed" if not errors else "completed_with_errors"
            )
            history_record.completed_at = datetime.now(timezone.utc)
            if errors:
                history_record.error_message = "\n".join(
                    errors[:10]
                )  # Store first 10 errors

            # Commit the savepoint
            savepoint.commit()
            logger.info(
                f"Migrated {migrated} items from {filename} ({skipped} skipped)"
            )

        except Exception as e:
            # Rollback the savepoint
            savepoint.rollback()
            history_record.status = "failed"
            history_record.error_message = str(e)
            logger.error(f"Failed to migrate {filename}: {e}")
            raise

        finally:
            if progress_bar:
                progress_bar.update(1)

        return migrated, skipped

    def migrate_all(self) -> None:
        """Migrate all data files with progress tracking."""
        if self.check_only:
            logger.info("\n=== Migration Status Check ===\n")
        else:
            logger.info("\n=== Starting Migration ===\n")

        # Create backup if requested and using SQLite
        backup_path = None
        if self.should_create_backup and self.database_url.startswith("sqlite:///"):
            db_path = Path(self.database_url.replace("sqlite:///", ""))
            backup_path = self.create_backup(db_path)

        # Create content pack first
        if not self.create_content_pack():
            logger.error("Failed to create content pack, aborting migration")
            return

        total_migrated = 0
        total_skipped = 0

        # Create progress bar
        with tqdm(
            total=len(self.FILE_MAPPING),
            desc="Migrating files",
            unit="file",
            disable=self.check_only,
        ) as pbar:
            # Migrate each file
            for filename in self.FILE_MAPPING:
                try:
                    migrated, skipped = self.migrate_file(filename, pbar)
                    total_migrated += migrated
                    total_skipped += skipped
                except Exception as e:
                    logger.error(f"Failed to migrate {filename}: {e}")
                    if not self.check_only:
                        self.session.rollback()
                        raise

        # Commit all changes
        if not self.check_only:
            try:
                self.session.commit()
                logger.info(
                    f"\n✓ Successfully migrated {total_migrated} items "
                    f"({total_skipped} already existed)"
                )
                if backup_path:
                    logger.info(f"Backup saved at: {backup_path}")
            except Exception as e:
                logger.error(f"Failed to commit changes: {e}")
                self.session.rollback()
                raise
            finally:
                self.session.close()
        else:
            logger.info(
                f"\n=== Summary ===\n"
                f"Total new items to migrate: {total_migrated}\n"
                f"Total items already migrated: {total_skipped}"
            )

    def rollback_migration(self, migration_id: Optional[str] = None) -> bool:
        """Rollback a specific migration or the last migration.

        Args:
            migration_id: Specific migration ID to rollback, or None for last migration

        Returns:
            True if rollback successful, False otherwise
        """
        if migration_id:
            history = (
                self.session.query(MigrationHistory)
                .filter_by(migration_id=migration_id)
                .first()
            )
        else:
            # Get the last completed migration
            history = (
                self.session.query(MigrationHistory)
                .filter_by(content_pack_id=self.content_pack_id, status="completed")
                .order_by(MigrationHistory.started_at.desc())
                .first()
            )

        if not history:
            logger.error("No migration found to rollback")
            return False

        logger.info(f"Rolling back migration: {history.migration_id}")

        # Get the model class for this file
        if history.file_name not in self.FILE_MAPPING:
            logger.error(f"Unknown file type: {history.file_name}")
            return False

        _, sqlalchemy_class = self.FILE_MAPPING[history.file_name]

        try:
            # Delete all items from this content pack (limitation: no per-migration tracking yet)
            # TODO: When migration_id column is added to schema, use: .filter_by(migration_id=history.migration_id)
            deleted = (
                self.session.query(sqlalchemy_class)
                .filter_by(content_pack_id=history.content_pack_id)
                .delete()
            )

            # Update history record
            history.status = "rolled_back"
            history.completed_at = datetime.now(timezone.utc)

            self.session.commit()
            logger.warning(
                f"Rolled back ALL {deleted} items from content pack {history.content_pack_id} "
                f"(precise migration tracking requires schema migration)"
            )
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            self.session.rollback()
            return False


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enhanced D&D 5e data migration with robustness features"
    )
    parser.add_argument(
        "database_url",
        help="SQLAlchemy database URL (e.g., sqlite:///data/content.db)",
    )
    parser.add_argument(
        "--json-path",
        default="knowledge/5e-database/src/2014",
        help="Path to JSON files directory",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check migration status without making changes",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup before migration",
    )
    parser.add_argument(
        "--rollback",
        metavar="MIGRATION_ID",
        nargs="?",
        const=True,
        help="Rollback last migration or specific migration ID",
    )
    parser.add_argument(
        "--drop-tables",
        action="store_true",
        help="Drop all tables before migration (WARNING: destructive!)",
    )

    args = parser.parse_args()

    # Handle rollback
    if args.rollback is not None:
        migrator = EnhancedD5eDataMigrator(
            args.database_url, args.json_path, create_backup=False
        )
        migration_id = args.rollback if args.rollback is not True else None
        success = migrator.rollback_migration(migration_id)
        sys.exit(0 if success else 1)

    # Create tables if needed
    if args.drop_tables:
        response = input("WARNING: This will drop all tables. Are you sure? (y/N): ")
        if response.lower() != "y":
            print("Aborted")
            return

        engine = create_engine(args.database_url)
        Base.metadata.drop_all(engine)
        logger.info("Dropped all tables")
        Base.metadata.create_all(engine)
        logger.info("Created all tables")
    else:
        # Just ensure tables exist
        engine = create_engine(args.database_url)
        Base.metadata.create_all(engine)

    # Run migration
    migrator = EnhancedD5eDataMigrator(
        args.database_url,
        args.json_path,
        check_only=args.check_only,
        create_backup=not args.no_backup,
    )
    migrator.migrate_all()


if __name__ == "__main__":
    main()
