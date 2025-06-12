"""Test migration of backgrounds specifically."""

import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Background, Base, ContentPack
from scripts.migrate_json_to_db import D5eDataMigrator


def test_migrate_backgrounds() -> None:
    """Test migrating background data."""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Create all tables
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)

    try:
        # Run migration
        migrator = D5eDataMigrator(f"sqlite:///{db_path}")
        migrator.create_content_pack()

        # Migrate backgrounds
        count = migrator.migrate_file("5e-SRD-Backgrounds.json")
        assert count > 0

        migrator.session.commit()

        # Verify backgrounds were created
        Session = sessionmaker(bind=engine)
        session = Session()

        # Check acolyte
        acolyte = session.query(Background).filter_by(index="acolyte").first()
        assert acolyte is not None
        assert acolyte.name == "Acolyte"
        assert acolyte.content_pack_id == "dnd_5e_srd"

        # Check the JSON columns contain the expected data
        assert acolyte.personality_traits is not None
        assert acolyte.ideals is not None
        assert acolyte.bonds is not None
        assert acolyte.flaws is not None

        session.close()

    finally:
        # Cleanup
        Path(db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    test_migrate_backgrounds()
    print("Background migration test passed!")
