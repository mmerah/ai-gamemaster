#!/usr/bin/env python3
"""
Script to generate vector embeddings for all D&D 5e content in the database.

This script reads content from the database, generates embeddings using
sentence-transformers, and updates the embedding columns for RAG search.
"""

import argparse
import logging
import sys
from typing import Any, Dict, List, Optional, Type

import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Add parent directory to path to import app modules
sys.path.insert(0, sys.path[0].replace("/scripts", ""))

from app.content.models import (
    AbilityScore,
    Alignment,
    Background,
    Base,
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
)
from app.content.types import Vector
from app.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Tables that should have embeddings for RAG search
# Include ALL content types for comprehensive search
RAG_ENABLED_TABLES = {
    "spells": Spell,
    "monsters": Monster,
    "equipment": Equipment,
    "classes": CharacterClass,
    "features": Feature,
    "backgrounds": Background,
    "races": Race,
    "feats": Feat,
    "magic_items": MagicItem,
    "traits": Trait,
    "conditions": Condition,
    "skills": Skill,
    # Additional content types for better coverage
    "rules": Rule,
    "rule_sections": RuleSection,
    "subclasses": Subclass,
    "subraces": Subrace,
    "proficiencies": Proficiency,
    "damage_types": DamageType,
    "languages": Language,
    "alignments": Alignment,
    "ability_scores": AbilityScore,
    # New content types for expanded coverage
    "equipment_categories": EquipmentCategory,
    "levels": Level,
    "magic_schools": MagicSchool,
    "weapon_properties": WeaponProperty,
}


def create_content_text(entity: Any, entity_type: str) -> str:
    """
    Create a text representation of an entity for embedding generation.

    Args:
        entity: The SQLAlchemy entity instance
        entity_type: The type of entity (e.g., 'spells', 'monsters')

    Returns:
        A text string suitable for embedding generation
    """
    parts = [f"{entity_type.rstrip('s').title()}: {entity.name}"]

    # Add type-specific information
    if entity_type == "spells":
        if hasattr(entity, "level"):
            parts.append(f"Level {entity.level}")
        if hasattr(entity, "school") and entity.school:
            parts.append(f"School: {entity.school.get('name', 'Unknown')}")
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)
        if hasattr(entity, "higher_level") and entity.higher_level:
            higher_text = (
                " ".join(entity.higher_level)
                if isinstance(entity.higher_level, list)
                else str(entity.higher_level)
            )
            parts.append(f"At Higher Levels: {higher_text}")

    elif entity_type == "monsters":
        # Basic info
        if hasattr(entity, "type"):
            parts.append(f"Type: {entity.type}")
        if hasattr(entity, "size"):
            parts.append(f"Size: {entity.size}")
        if hasattr(entity, "alignment"):
            parts.append(f"Alignment: {entity.alignment}")
        if hasattr(entity, "challenge_rating"):
            parts.append(f"CR: {entity.challenge_rating}")

        # Defensive stats
        if hasattr(entity, "armor_class") and entity.armor_class:
            ac_text = (
                str(entity.armor_class[0])
                if isinstance(entity.armor_class, list)
                else str(entity.armor_class)
            )
            parts.append(f"AC: {ac_text}")
        if hasattr(entity, "hit_points"):
            parts.append(f"HP: {entity.hit_points}")
        if hasattr(entity, "hit_dice"):
            parts.append(f"Hit Dice: {entity.hit_dice}")

        # Ability scores
        if all(
            hasattr(entity, attr)
            for attr in [
                "strength",
                "dexterity",
                "constitution",
                "intelligence",
                "wisdom",
                "charisma",
            ]
        ):
            parts.append(
                f"STR: {entity.strength}, DEX: {entity.dexterity}, CON: {entity.constitution}, INT: {entity.intelligence}, WIS: {entity.wisdom}, CHA: {entity.charisma}"
            )

        # Speed
        if hasattr(entity, "speed") and entity.speed:
            speed_parts = []
            if isinstance(entity.speed, dict):
                for move_type, dist in entity.speed.items():
                    speed_parts.append(f"{move_type}: {dist}")
            if speed_parts:
                parts.append(f"Speed: {', '.join(speed_parts)}")

        # Damage immunities/resistances
        if hasattr(entity, "damage_immunities") and entity.damage_immunities:
            parts.append(f"Damage Immunities: {', '.join(entity.damage_immunities)}")
        if hasattr(entity, "damage_resistances") and entity.damage_resistances:
            parts.append(f"Damage Resistances: {', '.join(entity.damage_resistances)}")

        # Languages
        if hasattr(entity, "languages") and entity.languages:
            parts.append(f"Languages: {entity.languages}")

        # Special abilities
        if hasattr(entity, "special_abilities") and entity.special_abilities:
            ability_names = []
            for ability in entity.special_abilities[:3]:  # First 3 abilities
                if isinstance(ability, dict) and "name" in ability:
                    ability_names.append(ability["name"])
            if ability_names:
                parts.append(f"Special Abilities: {', '.join(ability_names)}")

        # Actions
        if hasattr(entity, "actions") and entity.actions:
            action_names = []
            for action in entity.actions:
                if isinstance(action, dict) and "name" in action:
                    action_names.append(action["name"])
            if action_names:
                parts.append(f"Actions: {', '.join(action_names)}")

    elif entity_type == "equipment":
        if hasattr(entity, "equipment_category") and entity.equipment_category:
            parts.append(
                f"Category: {entity.equipment_category.get('name', 'Unknown')}"
            )
        if hasattr(entity, "cost") and entity.cost:
            parts.append(
                f"Cost: {entity.cost.get('quantity', 0)} {entity.cost.get('unit', 'gp')}"
            )
        if hasattr(entity, "weight"):
            parts.append(f"Weight: {entity.weight} lbs")
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)

    elif entity_type == "classes":
        if hasattr(entity, "hit_die"):
            parts.append(f"Hit Die: d{entity.hit_die}")
        if hasattr(entity, "proficiencies") and entity.proficiencies:
            prof_names = [
                p.get("name", "") for p in entity.proficiencies if isinstance(p, dict)
            ]
            if prof_names:
                parts.append(f"Proficiencies: {', '.join(prof_names)}")

    elif entity_type == "features":
        if hasattr(entity, "level"):
            parts.append(f"Level: {entity.level}")
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)

    elif entity_type == "rules":
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)

    elif entity_type == "rule_sections":
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)

    elif entity_type == "subclasses":
        if hasattr(entity, "subclass_flavor") and entity.subclass_flavor:
            parts.append(f"Flavor: {entity.subclass_flavor}")
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)

    elif entity_type == "subraces":
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)
        if hasattr(entity, "ability_bonuses") and entity.ability_bonuses:
            bonus_text = []
            for bonus in entity.ability_bonuses:
                if isinstance(bonus, dict):
                    ability = bonus.get("ability_score", {}).get("name", "Unknown")
                    value = bonus.get("bonus", 0)
                    bonus_text.append(f"{ability} +{value}")
            if bonus_text:
                parts.append(f"Ability Bonuses: {', '.join(bonus_text)}")

    elif entity_type == "backgrounds":
        if hasattr(entity, "feature") and entity.feature:
            if isinstance(entity.feature, dict) and "name" in entity.feature:
                parts.append(f"Feature: {entity.feature['name']}")
                if "desc" in entity.feature:
                    desc_text = (
                        " ".join(entity.feature["desc"])
                        if isinstance(entity.feature["desc"], list)
                        else str(entity.feature["desc"])
                    )
                    parts.append(desc_text)
        if hasattr(entity, "starting_proficiencies") and entity.starting_proficiencies:
            prof_names = [
                p.get("name", "")
                for p in entity.starting_proficiencies
                if isinstance(p, dict)
            ]
            if prof_names:
                parts.append(f"Proficiencies: {', '.join(prof_names)}")
        if hasattr(entity, "language_options") and entity.language_options:
            if (
                isinstance(entity.language_options, dict)
                and "choose" in entity.language_options
            ):
                parts.append(
                    f"Language Options: Choose {entity.language_options['choose']}"
                )

    elif entity_type == "feats":
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)
        if hasattr(entity, "prerequisites") and entity.prerequisites:
            prereq_parts = []
            for prereq in entity.prerequisites:
                if isinstance(prereq, dict):
                    if "ability_score" in prereq:
                        ability = prereq["ability_score"].get("name", "Unknown")
                        min_score = prereq.get("minimum_score", 0)
                        prereq_parts.append(f"{ability} {min_score}+")
                    elif "level" in prereq:
                        prereq_parts.append(f"Level {prereq['level']}+")
            if prereq_parts:
                parts.append(f"Prerequisites: {', '.join(prereq_parts)}")

    elif entity_type == "magic_items":
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)
        if hasattr(entity, "rarity") and entity.rarity:
            if isinstance(entity.rarity, dict) and "name" in entity.rarity:
                parts.append(f"Rarity: {entity.rarity['name']}")
        if hasattr(entity, "equipment_category") and entity.equipment_category:
            if (
                isinstance(entity.equipment_category, dict)
                and "name" in entity.equipment_category
            ):
                parts.append(f"Category: {entity.equipment_category['name']}")
        if hasattr(entity, "variant") and entity.variant:
            parts.append("(Variant)")

    elif entity_type == "traits":
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)
        if hasattr(entity, "races") and entity.races:
            race_names = [
                r.get("name", "") for r in entity.races if isinstance(r, dict)
            ]
            if race_names:
                parts.append(f"Races: {', '.join(race_names)}")
        if hasattr(entity, "subraces") and entity.subraces:
            subrace_names = [
                r.get("name", "") for r in entity.subraces if isinstance(r, dict)
            ]
            if subrace_names:
                parts.append(f"Subraces: {', '.join(subrace_names)}")
        if hasattr(entity, "proficiencies") and entity.proficiencies:
            prof_names = [
                p.get("name", "") for p in entity.proficiencies if isinstance(p, dict)
            ]
            if prof_names:
                parts.append(f"Grants Proficiencies: {', '.join(prof_names)}")

    elif entity_type == "conditions":
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)

    elif entity_type == "skills":
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)
        if hasattr(entity, "ability_score") and entity.ability_score:
            if (
                isinstance(entity.ability_score, dict)
                and "name" in entity.ability_score
            ):
                parts.append(f"Ability: {entity.ability_score['name']}")

    elif entity_type == "equipment_categories":
        if hasattr(entity, "equipment") and entity.equipment:
            equipment_names = [
                e.get("name", "") for e in entity.equipment if isinstance(e, dict)
            ]
            if equipment_names:
                # Limit to first 10 items to avoid overly long content
                sample = equipment_names[:10]
                if len(equipment_names) > 10:
                    sample.append(f"... and {len(equipment_names) - 10} more")
                parts.append(f"Equipment: {', '.join(sample)}")

    elif entity_type == "levels":
        if hasattr(entity, "level"):
            parts.append(f"Level: {entity.level}")
        if hasattr(entity, "class_ref") and entity.class_ref:
            if isinstance(entity.class_ref, dict) and "name" in entity.class_ref:
                parts.append(f"Class: {entity.class_ref['name']}")
        if hasattr(entity, "subclass") and entity.subclass:
            if isinstance(entity.subclass, dict) and "name" in entity.subclass:
                parts.append(f"Subclass: {entity.subclass['name']}")
        if hasattr(entity, "prof_bonus"):
            parts.append(f"Proficiency Bonus: +{entity.prof_bonus}")
        if hasattr(entity, "features") and entity.features:
            feature_names = [
                f.get("name", "") for f in entity.features if isinstance(f, dict)
            ]
            if feature_names:
                parts.append(f"Features: {', '.join(feature_names)}")
        if hasattr(entity, "spellcasting") and entity.spellcasting:
            if isinstance(entity.spellcasting, dict):
                if "spells_known" in entity.spellcasting:
                    parts.append(f"Spells Known: {entity.spellcasting['spells_known']}")
                if "cantrips_known" in entity.spellcasting:
                    parts.append(
                        f"Cantrips Known: {entity.spellcasting['cantrips_known']}"
                    )

    elif entity_type == "magic_schools":
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)

    elif entity_type == "weapon_properties":
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)

    elif entity_type in [
        "proficiencies",
        "damage_types",
        "languages",
        "alignments",
        "ability_scores",
    ]:
        # These are simple reference entities
        if hasattr(entity, "type") and entity.type:
            parts.append(f"Type: {entity.type}")
        if hasattr(entity, "desc") and entity.desc:
            desc_text = (
                " ".join(entity.desc)
                if isinstance(entity.desc, list)
                else str(entity.desc)
            )
            parts.append(desc_text)
        # Add any additional relevant info
        if hasattr(entity, "full_name") and entity.full_name:
            parts.append(f"Full Name: {entity.full_name}")

    else:
        # Generic handling for other entity types
        if hasattr(entity, "desc"):
            if entity.desc:
                desc_text = (
                    " ".join(entity.desc)
                    if isinstance(entity.desc, list)
                    else str(entity.desc)
                )
                parts.append(desc_text)

    return " ".join(parts)


def generate_embeddings_for_table(
    session: Session,
    model: SentenceTransformer,
    table_name: str,
    entity_class: Type[Any],
    batch_size: int = 100,
) -> int:
    """
    Generate embeddings for all entities in a table.

    Args:
        session: SQLAlchemy session
        model: SentenceTransformer model for embedding generation
        table_name: Name of the table
        entity_class: SQLAlchemy model class
        batch_size: Number of entities to process at once

    Returns:
        Number of entities updated
    """
    logger.info(f"Processing {table_name}...")

    # Count total entities
    total_count = session.query(entity_class).count()
    if total_count == 0:
        logger.info(f"No entities found in {table_name}")
        return 0

    logger.info(f"Found {total_count} entities in {table_name}")

    # Process in batches
    updated_count = 0
    offset = 0

    while offset < total_count:
        # Fetch batch of entities
        entities = session.query(entity_class).offset(offset).limit(batch_size).all()

        if not entities:
            break

        # Generate texts for embedding
        texts = []
        valid_entities = []

        for entity in entities:
            try:
                text = create_content_text(entity, table_name)
                if text and len(text.strip()) > 0:
                    texts.append(text)
                    valid_entities.append(entity)
            except Exception as e:
                logger.warning(f"Error creating text for {entity.name}: {e}")
                continue

        if texts:
            # Generate embeddings
            embeddings = model.encode(
                texts, convert_to_numpy=True, show_progress_bar=False
            )

            # Update entities with embeddings
            for entity, embedding in zip(valid_entities, embeddings):
                entity.embedding = embedding.astype(np.float32)
                updated_count += 1

            # Commit batch
            session.commit()
            logger.info(f"Updated {updated_count}/{total_count} entities...")

        offset += batch_size

    logger.info(f"Completed {table_name}: {updated_count} entities updated")
    return updated_count


def main() -> int:
    """Main function to run the indexing process."""
    parser = argparse.ArgumentParser(
        description="Generate vector embeddings for D&D 5e content"
    )
    parser.add_argument(
        "database_url",
        nargs="?",
        default="sqlite:///data/content.db",
        help="Database URL (default: sqlite:///data/content.db)",
    )
    parser.add_argument(
        "--model",
        default="intfloat/multilingual-e5-small",
        help="Sentence transformer model to use (default: intfloat/multilingual-e5-small)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for processing (default: 100)",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        choices=list(RAG_ENABLED_TABLES.keys()),
        help="Specific tables to index (default: all RAG-enabled tables)",
    )

    args = parser.parse_args()

    # Create database engine
    logger.info(f"Connecting to database: {args.database_url}")
    engine = create_engine(args.database_url)
    Session = sessionmaker(bind=engine)

    # Load embedding model
    logger.info(f"Loading embedding model: {args.model}")
    model = SentenceTransformer(args.model)

    # Get expected dimension from settings
    settings = get_settings()
    expected_dim = settings.rag.embedding_dimension

    # Verify model dimensions match our settings
    test_embedding = model.encode("test", convert_to_numpy=True)
    actual_dim = len(test_embedding)

    if actual_dim != expected_dim:
        logger.error(
            f"Model dimension mismatch! Expected {expected_dim} (from RAG_EMBEDDING_DIMENSION), got {actual_dim}. "
            f"Please either:\n"
            f"1. Use a model that produces {expected_dim}-dimensional embeddings, or\n"
            f"2. Update RAG_EMBEDDING_DIMENSION in your .env file to {actual_dim}"
        )
        return 1

    logger.info(f"Model produces {actual_dim}-dimensional embeddings ✓")

    # Process tables
    tables_to_process = args.tables or list(RAG_ENABLED_TABLES.keys())
    total_updated = 0

    with Session() as session:
        for table_name in tables_to_process:
            if table_name not in RAG_ENABLED_TABLES:
                logger.warning(f"Unknown table: {table_name}")
                continue

            entity_class = RAG_ENABLED_TABLES[table_name]
            updated = generate_embeddings_for_table(
                session, model, table_name, entity_class, args.batch_size
            )
            total_updated += updated

    logger.info(f"\nIndexing complete! Total entities updated: {total_updated}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
