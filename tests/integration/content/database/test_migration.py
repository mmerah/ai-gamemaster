"""Integration tests for enhanced migration script with robustness features."""

import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.content.models import (
    AbilityScore,
    Base,
    ContentPack,
    MigrationHistory,
    Monster,
    Spell,
)
from app.content.scripts.migrate_content import EnhancedD5eDataMigrator


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Create all tables
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()

    try:
        yield f"sqlite:///{db_path}"
    finally:
        # Cleanup
        Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def temp_json_dir() -> Generator[Path, None, None]:
    """Create a temporary directory with test JSON files."""
    temp_dir = Path(tempfile.mkdtemp())

    # Create minimal test data
    test_data = {
        "5e-SRD-Ability-Scores.json": [
            {
                "index": "str",
                "name": "STR",
                "full_name": "Strength",
                "desc": ["Test"],
                "url": "/api/ability-scores/str",
            },
            {
                "index": "dex",
                "name": "DEX",
                "full_name": "Dexterity",
                "desc": ["Test"],
                "url": "/api/ability-scores/dex",
            },
        ],
        "5e-SRD-Spells.json": [
            {
                "index": "fireball",
                "name": "Fireball",
                "desc": ["A bright streak..."],
                "range": "150 feet",
                "components": ["V", "S", "M"],
                "material": "A tiny ball of bat guano and sulfur",
                "ritual": False,
                "duration": "Instantaneous",
                "concentration": False,
                "casting_time": "1 action",
                "level": 3,
                "school": {
                    "index": "evocation",
                    "name": "Evocation",
                    "url": "/api/magic-schools/evocation",
                },
                "classes": [
                    {
                        "index": "sorcerer",
                        "name": "Sorcerer",
                        "url": "/api/classes/sorcerer",
                    }
                ],
                "subclasses": [],
                "url": "/api/spells/fireball",
            }
        ],
        "5e-SRD-Monsters.json": [
            {
                "index": "goblin",
                "name": "Goblin",
                "size": "Small",
                "type": "humanoid",
                "subtype": "goblinoid",
                "alignment": "neutral evil",
                "armor_class": [{"type": "natural", "value": 15}],
                "hit_points": 7,
                "hit_dice": "2d6",
                "speed": {"walk": "30 ft."},
                "strength": 8,
                "dexterity": 14,
                "constitution": 10,
                "intelligence": 10,
                "wisdom": 8,
                "charisma": 8,
                "proficiencies": [],
                "damage_vulnerabilities": [],
                "damage_resistances": [],
                "damage_immunities": [],
                "condition_immunities": [],
                "senses": {"darkvision": "60 ft.", "passive_perception": 9},
                "languages": "Common, Goblin",
                "challenge_rating": 0.25,
                "xp": 50,
                "proficiency_bonus": 2,
                "hit_points_roll": "2d6",
                "special_abilities": [],
                "actions": [],
                "legendary_actions": [],
                "reactions": [],
                "url": "/api/monsters/goblin",
            }
        ],
    }

    for filename, data in test_data.items():
        with open(temp_dir / filename, "w") as f:
            json.dump(data, f)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


class TestEnhancedMigration:
    """Test suite for enhanced migration functionality."""

    def test_check_only_mode(self, temp_db: str, temp_json_dir: Path) -> None:
        """Test --check-only mode reports status without making changes."""
        # First, run a normal migration
        migrator = EnhancedD5eDataMigrator(
            temp_db, str(temp_json_dir), check_only=False
        )
        try:
            migrator.migrate_all()
        finally:
            migrator.engine.dispose()

        # Setup a single engine for verification throughout the test
        engine = create_engine(temp_db)
        Session = sessionmaker(bind=engine)
        try:
            session = Session()

            initial_spell_count = session.query(Spell).count()
            initial_history_count = session.query(MigrationHistory).count()

            session.close()

            # Run in check-only mode
            migrator_check = EnhancedD5eDataMigrator(
                temp_db, str(temp_json_dir), check_only=True
            )
            try:
                migrator_check.migrate_all()
            finally:
                migrator_check.engine.dispose()

            # Verify no changes were made
            session = Session()
            assert session.query(Spell).count() == initial_spell_count
            assert session.query(MigrationHistory).count() == initial_history_count
            session.close()
        finally:
            engine.dispose()

    def test_idempotency(self, temp_db: str, temp_json_dir: Path) -> None:
        """Test that running migration multiple times doesn't create duplicates."""
        # Run migration twice
        for _ in range(2):
            migrator = EnhancedD5eDataMigrator(
                temp_db, str(temp_json_dir), check_only=False
            )
            try:
                migrator.migrate_all()
            finally:
                migrator.engine.dispose()

        # Verify no duplicates
        engine = create_engine(temp_db)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Check ability scores
            ability_scores = session.query(AbilityScore).all()
            assert len(ability_scores) == 2
            assert {a.index for a in ability_scores} == {"str", "dex"}

            # Check spells
            spells = session.query(Spell).all()
            assert len(spells) == 1
            assert spells[0].index == "fireball"

            # Check monsters
            monsters = session.query(Monster).all()
            assert len(monsters) == 1
            assert monsters[0].index == "goblin"
        finally:
            session.close()
            engine.dispose()

    def test_migration_history_tracking(
        self, temp_db: str, temp_json_dir: Path
    ) -> None:
        """Test that migration history is properly tracked."""
        migrator = EnhancedD5eDataMigrator(
            temp_db, str(temp_json_dir), check_only=False
        )
        try:
            migrator.migrate_all()
        finally:
            migrator.engine.dispose()

        engine = create_engine(temp_db)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Check migration history
            history_records = session.query(MigrationHistory).all()
            assert len(history_records) > 0

            # Verify history for each file
            file_names = {
                "5e-SRD-Ability-Scores.json",
                "5e-SRD-Spells.json",
                "5e-SRD-Monsters.json",
            }
            migrated_files = {h.file_name for h in history_records}
            assert file_names.issubset(migrated_files)

            # Check history details
            for history in history_records:
                if history.file_name in file_names:
                    assert history.status == "completed"
                    assert history.items_count > 0
                    assert history.completed_at is not None
                    assert history.started_at <= history.completed_at
        finally:
            session.close()
            engine.dispose()

    def test_savepoint_rollback_on_error(
        self, temp_db: str, temp_json_dir: Path
    ) -> None:
        """Test that savepoints properly rollback on error."""
        # Create invalid data that will fail validation
        invalid_spell = {
            "index": "invalid-spell",
            "name": "Invalid Spell",
            # Missing required fields like desc, range, etc.
        }

        # Add invalid data to spells file
        spells_file = temp_json_dir / "5e-SRD-Spells.json"
        with open(spells_file, "r") as f:
            spells_data = json.load(f)
        spells_data.append(invalid_spell)
        with open(spells_file, "w") as f:
            json.dump(spells_data, f)

        migrator = EnhancedD5eDataMigrator(
            temp_db, str(temp_json_dir), check_only=False
        )
        try:
            # Migration should complete but with errors logged
            migrator.migrate_all()
        finally:
            migrator.engine.dispose()

        engine = create_engine(temp_db)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Valid spell should still be migrated
            spells = session.query(Spell).all()
            assert len(spells) == 1
            assert spells[0].index == "fireball"

            # Check migration history shows completion with errors
            spell_history = (
                session.query(MigrationHistory)
                .filter_by(file_name="5e-SRD-Spells.json")
                .first()
            )
            assert spell_history is not None
            assert spell_history.items_count == 1  # Only valid item
        finally:
            session.close()
            engine.dispose()

    def test_backup_creation(self, temp_json_dir: Path) -> None:
        """Test automatic backup creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db_url = f"sqlite:///{db_path}"

            # Create initial database
            engine = create_engine(db_url)
            Base.metadata.create_all(engine)
            engine.dispose()

            # Run migration with backup
            migrator = EnhancedD5eDataMigrator(
                db_url, str(temp_json_dir), create_backup=True
            )
            try:
                migrator.migrate_all()
            finally:
                migrator.engine.dispose()

            # Check backup was created
            backup_files = list(db_path.parent.glob(f"{db_path.stem}_backup_*.db"))
            assert len(backup_files) == 1

            # Verify backup is valid
            backup_engine = create_engine(f"sqlite:///{backup_files[0]}")
            Session = sessionmaker(bind=backup_engine)
            session = Session()

            try:
                # Backup should be empty (created before migration)
                assert session.query(Spell).count() == 0
            finally:
                session.close()
                backup_engine.dispose()

    def test_rollback_functionality(self, temp_db: str, temp_json_dir: Path) -> None:
        """Test rollback of migrations."""
        # First, run a migration
        migrator = EnhancedD5eDataMigrator(
            temp_db, str(temp_json_dir), check_only=False
        )
        try:
            migrator.migrate_all()
        finally:
            migrator.engine.dispose()

        # Setup a single engine for verification throughout the test
        engine = create_engine(temp_db)
        Session = sessionmaker(bind=engine)
        try:
            session = Session()
            # Verify data was migrated
            assert session.query(Spell).count() == 1
            assert session.query(Monster).count() == 1

            # Get migration ID for spells
            spell_history = (
                session.query(MigrationHistory)
                .filter_by(file_name="5e-SRD-Spells.json", status="completed")
                .first()
            )
            assert spell_history is not None
            migration_id = spell_history.migration_id
            session.close()

            # Rollback specific migration
            migrator_rollback = EnhancedD5eDataMigrator(
                temp_db, str(temp_json_dir), create_backup=False
            )
            try:
                success = migrator_rollback.rollback_migration(migration_id)
                assert success
            finally:
                migrator_rollback.engine.dispose()

            # Verify rollback
            session = Session()
            assert session.query(Spell).count() == 0  # Spells should be removed
            assert session.query(Monster).count() == 1  # Monsters should remain

            # Check history was updated
            spell_history = (
                session.query(MigrationHistory)
                .filter_by(migration_id=migration_id)
                .first()
            )
            assert spell_history is not None
            assert spell_history.status == "rolled_back"
            session.close()
        finally:
            engine.dispose()

    def test_rollback_last_migration(self, temp_db: str, temp_json_dir: Path) -> None:
        """Test rollback of the last migration without specifying ID."""
        # Run migration
        migrator = EnhancedD5eDataMigrator(
            temp_db, str(temp_json_dir), check_only=False
        )
        try:
            migrator.migrate_all()
        finally:
            migrator.engine.dispose()

        # Rollback last migration (should be last file processed)
        migrator_rollback = EnhancedD5eDataMigrator(
            temp_db, str(temp_json_dir), create_backup=False
        )
        try:
            success = migrator_rollback.rollback_migration()  # No ID specified
            assert success
        finally:
            migrator_rollback.engine.dispose()

        # At least one file should have been rolled back
        engine = create_engine(temp_db)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            rolled_back = (
                session.query(MigrationHistory).filter_by(status="rolled_back").count()
            )
            assert rolled_back >= 1
        finally:
            session.close()
            engine.dispose()

    def test_progress_bar_integration(
        self, temp_db: str, temp_json_dir: Path, capsys: Any
    ) -> None:
        """Test that progress bars work correctly."""
        migrator = EnhancedD5eDataMigrator(
            temp_db, str(temp_json_dir), check_only=False
        )
        try:
            migrator.migrate_all()
        finally:
            migrator.engine.dispose()

        # Progress bar output should not interfere with logging
        captured = capsys.readouterr()
        # Check that progress bar was displayed (will be in stderr)
        assert "Migrating files:" in captured.err or "Migrating files:" in captured.out

    def test_concurrent_access_with_wal(
        self, temp_db: str, temp_json_dir: Path
    ) -> None:
        """Test that WAL mode is properly configured for SQLite."""
        if not temp_db.startswith("sqlite://"):
            pytest.skip("WAL test only applies to SQLite")

        migrator = EnhancedD5eDataMigrator(
            temp_db, str(temp_json_dir), check_only=False
        )
        try:
            # Check that connection has WAL mode
            with migrator.session_factory() as session:
                result = session.execute(text("PRAGMA journal_mode")).scalar()
                assert result == "wal"

            migrator.migrate_all()
        finally:
            migrator.engine.dispose()

    def test_error_handling_and_reporting(
        self, temp_db: str, temp_json_dir: Path
    ) -> None:
        """Test error handling and reporting in migration history."""
        # Create a file that will cause an error during processing
        with patch.object(
            EnhancedD5eDataMigrator,
            "convert_pydantic_to_sqlalchemy",
            side_effect=Exception("Test error"),
        ):
            migrator = EnhancedD5eDataMigrator(
                temp_db, str(temp_json_dir), check_only=False
            )
            try:
                # Migration should complete but with errors
                migrator.migrate_all()
            finally:
                migrator.engine.dispose()

        # Check that error was recorded in history
        engine = create_engine(temp_db)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            error_migrations = (
                session.query(MigrationHistory)
                .filter_by(status="completed_with_errors")
                .all()
            )
            assert len(error_migrations) > 0
            assert any(
                "Test error" in (m.error_message or "") for m in error_migrations
            )
        finally:
            session.close()
            engine.dispose()


class TestMigrationCLI:
    """Test command-line interface functionality."""

    def test_check_only_flag(
        self, temp_db: str, temp_json_dir: Path, monkeypatch: Any
    ) -> None:
        """Test --check-only CLI flag."""
        from app.content.scripts.migrate_content import main

        # Mock command line arguments
        test_args = [
            "migrate_json_to_db.py",
            temp_db,
            "--json-path",
            str(temp_json_dir),
            "--check-only",
        ]
        monkeypatch.setattr("sys.argv", test_args)

        # Run main function
        main()

        # Verify no data was migrated
        engine = create_engine(temp_db)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # Should only have content pack, no actual data
            assert session.query(Spell).count() == 0
            assert session.query(Monster).count() == 0
        finally:
            session.close()
            engine.dispose()

    def test_no_backup_flag(self, temp_json_dir: Path, monkeypatch: Any) -> None:
        """Test --no-backup CLI flag."""
        from app.content.scripts.migrate_content import main

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db_url = f"sqlite:///{db_path}"

            # Create initial database
            engine = create_engine(db_url)
            Base.metadata.create_all(engine)
            engine.dispose()

            # Mock command line arguments
            test_args = [
                "migrate_json_to_db.py",
                db_url,
                "--json-path",
                str(temp_json_dir),
                "--no-backup",
            ]
            monkeypatch.setattr("sys.argv", test_args)

            # Run main function
            main()

            # Verify no backup was created
            backup_files = list(db_path.parent.glob(f"{db_path.stem}_backup_*.db"))
            assert len(backup_files) == 0
