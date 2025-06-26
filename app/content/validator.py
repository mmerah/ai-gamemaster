"""Database validation and setup utilities."""

import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.content.connection import DatabaseManager
from app.content.models import Base

logger = logging.getLogger(__name__)


class DatabaseValidator:
    """Validates and initializes database schema and content."""

    REQUIRED_TABLES = [
        "content_packs",
        "spells",
        "monsters",
        "equipment",
        "classes",
        "features",
        "levels",
        "races",
        "backgrounds",
        "conditions",
        "damage_types",
        "magic_items",
        "proficiencies",
        "skills",
        "alignments",
        "ability_scores",
        "equipment_categories",
        "feats",
        "languages",
        "magic_schools",
        "rule_sections",
        "rules",
        "subclasses",
        "subraces",
        "traits",
        "weapon_properties",
    ]

    CRITICAL_TABLES = ["content_packs", "spells", "monsters", "equipment"]

    def __init__(self, database_url: str):
        """Initialize validator with database URL."""
        self.database_url = database_url
        self.is_test_db = ":memory:" in database_url or "test" in database_url

    def validate_and_setup(self) -> Tuple[bool, Optional[str]]:
        """
        Validate database and perform setup if needed.

        Returns:
            Tuple of (success, error_message)
        """
        # Skip validation for in-memory databases
        if ":memory:" in self.database_url:
            logger.info("Using in-memory database, skipping validation")
            return True, None

        # Check if database file exists
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            if not os.path.exists(db_path):
                return False, f"Database not found at {db_path}"

        try:
            # Create engine for validation
            engine = create_engine(self.database_url)

            # Check schema
            schema_valid, schema_msg = self._validate_schema(engine)
            if not schema_valid:
                return False, schema_msg

            # Check content
            content_valid, content_msg = self._validate_content(engine)
            if not content_valid:
                # Content issues are warnings, not failures
                logger.warning(content_msg)

            # Check indexes for performance
            self._validate_indexes(engine)

            engine.dispose()
            return True, None

        except OperationalError as e:
            return False, f"Database connection failed: {e}"
        except Exception as e:
            return False, f"Unexpected database error: {e}"

    def _validate_schema(self, engine: Engine) -> Tuple[bool, Optional[str]]:
        """Validate database schema has required tables."""
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())

        # Check critical tables
        missing_critical = []
        for table in self.CRITICAL_TABLES:
            if table not in existing_tables:
                missing_critical.append(table)

        if missing_critical:
            return False, f"Missing critical tables: {', '.join(missing_critical)}"

        # Check all tables (warning only)
        missing_tables = []
        for table in self.REQUIRED_TABLES:
            if table not in existing_tables:
                missing_tables.append(table)

        if missing_tables:
            logger.warning(f"Missing optional tables: {', '.join(missing_tables)}")

        # Check for vector columns if not test database
        if not self.is_test_db:
            with engine.connect() as conn:
                # Check if embedding columns exist
                result = conn.execute(
                    text("""
                    SELECT COUNT(*) FROM pragma_table_info('spells') 
                    WHERE name = 'embedding'
                    """)
                ).scalar()

                if result == 0:
                    logger.warning(
                        "Vector embedding columns not found. "
                        "Run 'python -m app.content.scripts.index_for_rag.py' to add them."
                    )

        return True, None

    def _validate_content(self, engine: Engine) -> Tuple[bool, Optional[str]]:
        """Validate database has content."""
        with engine.connect() as conn:
            # Check content packs
            pack_count = conn.execute(
                text("SELECT COUNT(*) FROM content_packs")
            ).scalar()

            if pack_count == 0:
                return False, "No content packs found"

            # Check spell count as indicator of content
            spell_count = conn.execute(text("SELECT COUNT(*) FROM spells")).scalar()

            if spell_count == 0:
                return False, "Database is empty (no spells found)"

            logger.info(
                f"Database content validated: {pack_count} content pack(s), "
                f"{spell_count} spells"
            )

        return True, None

    def _validate_indexes(self, engine: Engine) -> None:
        """Check for performance indexes."""
        if self.is_test_db:
            return  # Skip index checks for test databases

        with engine.connect() as conn:
            # Check for important indexes
            indexes_to_check = [
                ("idx_spells_name_lower", "spells"),
                ("idx_monsters_name_lower", "monsters"),
                ("idx_equipment_name_lower", "equipment"),
            ]

            for index_name, table_name in indexes_to_check:
                result = conn.execute(
                    text("""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='index' AND name=:index_name
                    """),
                    {"index_name": index_name},
                ).scalar()

                if result == 0:
                    logger.warning(
                        f"Performance index {index_name} missing on {table_name}"
                    )


def validate_database(database_url: str) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate database.

    Args:
        database_url: Database connection URL

    Returns:
        Tuple of (success, error_message)
    """
    validator = DatabaseValidator(database_url)
    return validator.validate_and_setup()
