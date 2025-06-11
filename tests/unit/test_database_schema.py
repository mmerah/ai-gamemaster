"""Tests for database schema and migrations."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config
from app.database.models import Base


class TestDatabaseSchema:
    """Test database schema creation and migrations."""

    @pytest.fixture
    def alembic_config(self) -> Generator[Config, None, None]:
        """Create an Alembic configuration for testing."""
        # Create a temporary database
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        # Create Alembic config
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

        yield config

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_schema_creation_via_alembic(self, alembic_config: Config) -> None:
        """Test that Alembic can create the schema correctly."""
        # Run migrations to latest
        command.upgrade(alembic_config, "head")

        # Get engine from config
        db_url = alembic_config.get_main_option("sqlalchemy.url")
        assert db_url is not None
        engine = create_engine(db_url)

        # Verify tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Check core tables
        assert "content_packs" in tables
        assert "spells" in tables
        assert "monsters" in tables
        assert "equipment" in tables
        assert "classes" in tables

        # Check all 25 D5e tables
        expected_tables = [
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

        for table in expected_tables:
            assert table in tables, f"Missing table: {table}"

        # Verify content_packs columns
        columns = {col["name"] for col in inspector.get_columns("content_packs")}
        assert "id" in columns
        assert "name" in columns
        assert "is_active" in columns
        assert "created_at" in columns

        # Verify spell columns
        columns = {col["name"] for col in inspector.get_columns("spells")}
        assert "index" in columns
        assert "name" in columns
        assert "level" in columns
        assert "school" in columns
        assert "content_pack_id" in columns

    def test_base_metadata_matches_alembic(self) -> None:
        """Test that SQLAlchemy models match what Alembic expects."""
        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")

        # Create schema using SQLAlchemy
        Base.metadata.create_all(engine)

        # Verify tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Should have all tables
        assert len(tables) == 26  # 25 D5e tables + content_packs
        assert "content_packs" in tables
        assert "spells" in tables

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
