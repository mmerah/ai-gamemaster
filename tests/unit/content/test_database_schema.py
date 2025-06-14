"""Tests for database schema and migrations."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from app.content.models import Base


class TestDatabaseSchema:
    """Test database schema creation and migrations."""

    def test_schema_creation_via_sqlalchemy(self) -> None:
        """Test that we can create the schema using SQLAlchemy directly."""
        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")

        # Create all tables
        Base.metadata.create_all(engine)

        # Verify tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        # Filter out test tables that might be created by unit tests
        tables = [t for t in tables if not t.startswith("test_")]

        # Should have all tables
        assert len(tables) == 27  # 25 D5e tables + content_packs + migration_history
        assert "content_packs" in tables
        assert "spells" in tables
        assert "monsters" in tables

        # Verify content_packs columns
        columns = {col["name"] for col in inspector.get_columns("content_packs")}
        assert "id" in columns
        assert "name" in columns
        assert "is_active" in columns
        assert "created_at" in columns

    def test_alembic_migration_script_validity(self) -> None:
        """Test that the alembic migration script is valid without running it."""
        # Create a temporary database path
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(db_path)  # Remove to ensure fresh start

        try:
            # Create config
            config = Config("app/content/alembic.ini")
            config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

            # Get the script directory
            script_dir = ScriptDirectory.from_config(config)

            # Check we have migrations
            revisions = list(script_dir.walk_revisions())
            assert len(revisions) > 0, "No migrations found"

            # Get the head revision
            head = script_dir.get_current_head()
            assert head is not None, "No head revision found"

            # Verify the migration exists
            migration = script_dir.get_revision(head)
            assert migration is not None
            # Check that we have the performance indexes migration
            assert (
                migration.revision == "63db3a289b42"
            )  # Migration history table migration

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_table_structure_details(self) -> None:
        """Test detailed table structure including all D5e tables."""
        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        tables = inspector.get_table_names()
        # Filter out test tables that might be created by unit tests
        tables = [t for t in tables if not t.startswith("test_")]

        # Check all 25 D5e tables + content_packs
        expected_tables = [
            "content_packs",
            "ability_scores",
            "alignments",
            "backgrounds",
            "classes",
            "conditions",
            "damage_types",
            "equipment",
            "equipment_categories",
            "feats",
            "features",
            "languages",
            "levels",
            "magic_items",
            "magic_schools",
            "monsters",
            "proficiencies",
            "races",
            "rule_sections",
            "rules",
            "skills",
            "spells",
            "subclasses",
            "subraces",
            "traits",
            "weapon_properties",
        ]

        assert len(tables) == 27
        for table in expected_tables:
            assert table in tables, f"Missing table: {table}"

        # Verify spell columns as example
        columns = {col["name"] for col in inspector.get_columns("spells")}
        assert "index" in columns
        assert "name" in columns
        assert "level" in columns
        assert "school" in columns
        assert "content_pack_id" in columns
        assert "embedding" in columns  # Vector embedding column

    def test_foreign_key_constraints(self) -> None:
        """Test that foreign key constraints are properly defined."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)

        # Check spell foreign keys
        fks = inspector.get_foreign_keys("spells")
        assert len(fks) == 1
        assert fks[0]["constrained_columns"] == ["content_pack_id"]
        assert fks[0]["referred_table"] == "content_packs"
        assert fks[0]["referred_columns"] == ["id"]

        # Check monster foreign keys
        fks = inspector.get_foreign_keys("monsters")
        assert len(fks) == 1
        assert fks[0]["constrained_columns"] == ["content_pack_id"]

    def test_unique_constraints(self) -> None:
        """Test that unique constraints are properly defined."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        # Check spell unique constraints
        # SQLite returns unique constraints differently, so we check the table args
        from app.content.models import Spell

        # Verify the unique constraint is defined in the model
        constraints = [arg for arg in Spell.__table_args__ if hasattr(arg, "columns")]
        assert len(constraints) == 1
        constraint = constraints[0]
        column_names = [col.name for col in constraint.columns]
        assert "index" in column_names
        assert "content_pack_id" in column_names

    def test_migration_script_execution(self) -> None:
        """Test migration script logic without full data migration."""
        # Import the migration module directly to test its components
        sys.path.insert(0, ".")
        try:
            from app.content.scripts.migrate_content import EnhancedD5eDataMigrator
        finally:
            sys.path.pop(0)

        # Create a temporary test database file
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        try:
            # Create database URL
            db_url = f"sqlite:///{db_path}"

            # Create tables
            engine = create_engine(db_url)
            Base.metadata.create_all(engine)
            engine.dispose()

            # Create migrator instance with same database
            migrator = EnhancedD5eDataMigrator(db_url, json_path=".")

            # Test creating content pack using the instance
            migrator.create_content_pack()

            # Verify content pack was created
            from app.content.models import ContentPack

            pack = (
                migrator.session.query(ContentPack).filter_by(id="dnd_5e_srd").first()
            )
            assert pack is not None
            assert pack.id == "dnd_5e_srd"
            assert pack.name == "D&D 5e SRD"
            assert pack.is_active is True

            # Test loading JSON file (just structure, not full migration)
            test_spell_data = {  # type: ignore[unreachable]
                "index": "test-spell",
                "name": "Test Spell",
                "level": 1,
                "school": {"index": "evocation", "name": "Evocation"},
                "desc": ["A test spell"],
                "url": "/api/spells/test-spell",
            }

            # Create minimal test JSON file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump([test_spell_data], f)
                test_file = f.name

            try:
                # Test JSON loading using the migrator
                # Need to pass just the filename, not full path
                migrator.json_path = Path(os.path.dirname(test_file))
                data = migrator.load_json_file(os.path.basename(test_file))
                assert len(data) == 1
                assert data[0]["name"] == "Test Spell"
            finally:
                os.unlink(test_file)

            migrator.session.close()

        finally:
            # Cleanup database file
            if os.path.exists(db_path):
                os.unlink(db_path)
