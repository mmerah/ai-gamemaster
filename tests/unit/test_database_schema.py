"""Tests for database schema and migrations."""

import os
import subprocess
import sys
import tempfile

from sqlalchemy import create_engine, inspect, text

from alembic.config import Config
from alembic.script import ScriptDirectory
from app.database.models import Base


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
        assert len(tables) == 26  # 25 D5e tables + content_packs
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
            config = Config("alembic.ini")
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
            assert migration.revision == "2a409eb9e9d3"

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

        assert len(tables) == 26
        for table in expected_tables:
            assert table in tables, f"Missing table: {table}"

        # Verify spell columns as example
        columns = {col["name"] for col in inspector.get_columns("spells")}
        assert "index" in columns
        assert "name" in columns
        assert "level" in columns
        assert "school" in columns
        assert "content_pack_id" in columns

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
        from app.database.models import Spell

        # Verify the unique constraint is defined in the model
        constraints = [arg for arg in Spell.__table_args__ if hasattr(arg, "columns")]
        assert len(constraints) == 1
        constraint = constraints[0]
        column_names = [col.name for col in constraint.columns]
        assert "index" in column_names
        assert "content_pack_id" in column_names

    def test_migration_script_execution(self) -> None:
        """Test that the migration script can run successfully."""
        # Create a temporary database
        fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(db_path)  # Remove to ensure fresh start

        try:
            # Run the migration script
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/migrate_json_to_db.py",
                    f"sqlite:///{db_path}",
                ],
                capture_output=True,
                text=True,
            )

            # Check it ran successfully
            assert result.returncode == 0, f"Migration failed: {result.stderr}"
            # The output is in stderr due to logging
            output = result.stderr + result.stdout
            assert "Successfully migrated" in output
            assert "2317 items" in output  # Expected total

            # Verify database was created and populated
            engine = create_engine(f"sqlite:///{db_path}")
            inspector = inspect(engine)

            # Check tables exist
            tables = inspector.get_table_names()
            assert "content_packs" in tables
            assert "spells" in tables

            # Check data was inserted
            with engine.connect() as conn:
                # Check content pack
                cp_result = conn.execute(text("SELECT COUNT(*) FROM content_packs"))
                assert cp_result.scalar() == 1

                # Check spells
                spell_result = conn.execute(text("SELECT COUNT(*) FROM spells"))
                assert spell_result.scalar() == 319  # Expected number of spells

                # Check a specific spell exists
                fireball_result = conn.execute(
                    text("SELECT name, level FROM spells WHERE \"index\" = 'fireball'")
                )
                row = fireball_result.fetchone()
                assert row is not None
                assert row[0] == "Fireball"
                assert row[1] == 3

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
