#!/usr/bin/env python3
"""Verify the D&D 5e database migration was successful.

This script checks the database for expected content and provides
a summary of what was migrated.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Type

from sqlalchemy import create_engine, func, select
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


class MigrationVerifier:
    """Verifies the database migration was successful."""

    # Expected content types and their models
    CONTENT_TYPES = {
        "Ability Scores": AbilityScore,
        "Alignments": Alignment,
        "Backgrounds": Background,
        "Classes": CharacterClass,
        "Conditions": Condition,
        "Damage Types": DamageType,
        "Equipment": Equipment,
        "Equipment Categories": EquipmentCategory,
        "Feats": Feat,
        "Features": Feature,
        "Languages": Language,
        "Levels": Level,
        "Magic Items": MagicItem,
        "Magic Schools": MagicSchool,
        "Monsters": Monster,
        "Proficiencies": Proficiency,
        "Races": Race,
        "Rules": Rule,
        "Rule Sections": RuleSection,
        "Skills": Skill,
        "Spells": Spell,
        "Subclasses": Subclass,
        "Subraces": Subrace,
        "Traits": Trait,
        "Weapon Properties": WeaponProperty,
    }

    def __init__(self, database_url: str):
        """Initialize the verifier.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def verify_content_pack(self) -> bool:
        """Verify the D&D 5e SRD content pack exists.

        Returns:
            True if content pack exists, False otherwise
        """
        content_pack = (
            self.session.query(ContentPack).filter_by(id="dnd_5e_srd").first()
        )

        if content_pack:
            print("✅ Content Pack Found:")
            print(f"   ID: {content_pack.id}")
            print(f"   Name: {content_pack.name}")
            print(f"   Version: {content_pack.version}")
            print(f"   Author: {content_pack.author}")
            print(f"   Active: {content_pack.is_active}")
            print(f"   Created: {content_pack.created_at}")
            return True
        else:
            print("❌ Content Pack 'dnd_5e_srd' not found!")
            return False

    def count_content(self) -> Dict[str, int]:
        """Count items in each content type.

        Returns:
            Dictionary mapping content type names to counts
        """
        counts = {}

        for name, model_class in self.CONTENT_TYPES.items():
            stmt = (
                select(func.count())
                .select_from(model_class)
                .where(model_class.content_pack_id == "dnd_5e_srd")
            )
            count = self.session.execute(stmt).scalar()
            counts[name] = count

        return counts

    def verify_sample_content(self) -> None:
        """Verify some sample content to ensure data integrity."""
        print("\n📋 Sample Content Verification:")

        # Check a spell
        fireball = (
            self.session.query(Spell)
            .filter_by(index="fireball", content_pack_id="dnd_5e_srd")
            .first()
        )

        if fireball:
            print("\n✅ Spell 'Fireball' found:")
            print(f"   Name: {fireball.name}")
            print(f"   Level: {fireball.level}")
            print(
                f"   School: {fireball.school.get('name') if fireball.school else 'N/A'}"
            )
            print(f"   Range: {fireball.range}")
            print(f"   Components: {fireball.components}")
        else:
            print("\n❌ Spell 'Fireball' not found!")

        # Check a monster
        goblin = (
            self.session.query(Monster)
            .filter_by(index="goblin", content_pack_id="dnd_5e_srd")
            .first()
        )

        if goblin:
            print("\n✅ Monster 'Goblin' found:")
            print(f"   Name: {goblin.name}")
            print(f"   Size: {goblin.size}")
            print(f"   Type: {goblin.type}")
            print(f"   CR: {goblin.challenge_rating}")
            print(f"   HP: {goblin.hit_points}")
        else:
            print("\n❌ Monster 'Goblin' not found!")

        # Check a class
        fighter = (
            self.session.query(CharacterClass)
            .filter_by(index="fighter", content_pack_id="dnd_5e_srd")
            .first()
        )

        if fighter:
            print("\n✅ Class 'Fighter' found:")
            print(f"   Name: {fighter.name}")
            print(f"   Hit Die: {fighter.hit_die}")
            print(
                f"   Proficiencies: {len(fighter.proficiencies) if fighter.proficiencies else 0} items"
            )
        else:
            print("\n❌ Class 'Fighter' not found!")

    def verify_all(self) -> None:
        """Run all verification checks."""
        print("🔍 D&D 5e Database Migration Verification")
        print("=" * 50)

        # Check content pack
        if not self.verify_content_pack():
            print("\n⚠️  Migration may not have been run yet.")
            return

        # Count content
        print("\n📊 Content Summary:")
        counts = self.count_content()
        total = 0

        for content_type, count in sorted(counts.items()):
            print(f"   {content_type:.<30} {count:>6}")
            total += count

        print(f"   {'TOTAL':.<30} {total:>6}")

        # Verify sample content
        self.verify_sample_content()

        # Check for expected minimums
        print("\n✔️  Verification Results:")
        expected_minimums = {
            "Spells": 300,
            "Monsters": 300,
            "Equipment": 200,
            "Classes": 12,
            "Races": 9,
        }

        all_good = True
        for content_type, expected_min in expected_minimums.items():
            actual = counts.get(content_type, 0)
            if actual >= expected_min:
                print(f"   ✅ {content_type}: {actual} (expected ≥ {expected_min})")
            else:
                print(f"   ❌ {content_type}: {actual} (expected ≥ {expected_min})")
                all_good = False

        if all_good and total > 2000:
            print(f"\n✅ Migration successful! Total items: {total}")
        else:
            print(f"\n⚠️  Migration may be incomplete. Total items: {total}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Verify D&D 5e database migration")
    parser.add_argument(
        "database_url",
        help="SQLAlchemy database URL (e.g., sqlite:///data/content.db)",
    )

    args = parser.parse_args()

    # Run verification
    verifier = MigrationVerifier(args.database_url)
    verifier.verify_all()


if __name__ == "__main__":
    main()
