#!/usr/bin/env python3
"""Migrate D&D 5e data from JSON files to database.

This script reads the 25 JSON files from the 5e-database submodule and
populates the database with the D&D 5e SRD content.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Type, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

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


class D5eDataMigrator:
    """Migrates D&D 5e data from JSON files to the database."""

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
        self, database_url: str, json_path: str = "knowledge/5e-database/src/2014"
    ):
        """Initialize the migrator.

        Args:
            database_url: SQLAlchemy database URL
            json_path: Path to the directory containing JSON files
        """
        self.database_url = database_url
        self.json_path = Path(json_path)

        # Create engine and session
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Content pack ID for D&D 5e SRD
        self.content_pack_id = "dnd_5e_srd"

    def create_content_pack(self) -> None:
        """Create the D&D 5e SRD content pack."""
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
        else:
            self.session.add(content_pack)
            self.session.commit()
            logger.info("Created D&D 5e SRD content pack")

    def load_json_file(self, filename: str) -> List[Dict[str, Any]]:
        """Load data from a JSON file.

        Args:
            filename: Name of the JSON file

        Returns:
            List of items from the JSON file
        """
        file_path = self.json_path / filename
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

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

        # Handle special field mappings
        if hasattr(sqlalchemy_class, "__tablename__"):
            table_name = sqlalchemy_class.__tablename__

            # For classes table, map class_ref to class_ref
            if table_name == "classes" and "class" in data:
                data["class_ref"] = data.pop("class")

        # Get the column names from the SQLAlchemy model
        from sqlalchemy.inspection import inspect

        mapper = inspect(sqlalchemy_class)
        valid_columns = {col.key for col in mapper.columns}

        # Filter data to only include valid columns
        filtered_data = {k: v for k, v in data.items() if k in valid_columns}

        # Create the SQLAlchemy instance
        return sqlalchemy_class(**filtered_data)

    def migrate_file(self, filename: str) -> int:
        """Migrate data from a single JSON file.

        Args:
            filename: Name of the JSON file

        Returns:
            Number of items migrated
        """
        if filename not in self.FILE_MAPPING:
            logger.warning(f"No mapping found for file: {filename}")
            return 0

        pydantic_class, sqlalchemy_class = self.FILE_MAPPING[filename]

        logger.info(f"Migrating {filename}...")

        # Load JSON data
        json_data = self.load_json_file(filename)

        count = 0
        for item_data in json_data:
            try:
                # Validate with Pydantic
                pydantic_model = pydantic_class(**item_data)

                # Convert to SQLAlchemy
                db_model = self.convert_pydantic_to_sqlalchemy(
                    pydantic_model, sqlalchemy_class
                )

                # Add to session
                self.session.add(db_model)
                count += 1

            except Exception as e:
                logger.error(
                    f"Error migrating item {item_data.get('index', 'unknown')}: {e}"
                )
                raise

        logger.info(f"Migrated {count} items from {filename}")
        return count

    def migrate_all(self) -> None:
        """Migrate all data files."""
        # Create content pack first
        self.create_content_pack()

        total_count = 0

        # Migrate each file
        for filename in self.FILE_MAPPING:
            try:
                count = self.migrate_file(filename)
                total_count += count
            except Exception as e:
                logger.error(f"Failed to migrate {filename}: {e}")
                self.session.rollback()
                raise

        # Commit all changes
        try:
            self.session.commit()
            logger.info(f"Successfully migrated {total_count} items to the database")
        except Exception as e:
            logger.error(f"Failed to commit changes: {e}")
            self.session.rollback()
            raise
        finally:
            self.session.close()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate D&D 5e data to database")
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
        "--drop-tables",
        action="store_true",
        help="Drop all tables before migration (WARNING: destructive!)",
    )

    args = parser.parse_args()

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
    migrator = D5eDataMigrator(args.database_url, args.json_path)
    migrator.migrate_all()


if __name__ == "__main__":
    main()
