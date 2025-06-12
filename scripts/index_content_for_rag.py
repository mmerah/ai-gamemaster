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

from app.database.models import (
    Background,
    Base,
    CharacterClass,
    Condition,
    Equipment,
    Feat,
    Feature,
    MagicItem,
    Monster,
    Race,
    Skill,
    Spell,
    Trait,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Tables that should have embeddings for RAG search
# These are the most important content types for gameplay
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
        if hasattr(entity, "type"):
            parts.append(f"Type: {entity.type}")
        if hasattr(entity, "size"):
            parts.append(f"Size: {entity.size}")
        if hasattr(entity, "challenge_rating"):
            parts.append(f"CR: {entity.challenge_rating}")
        if hasattr(entity, "armor_class") and entity.armor_class:
            ac_text = (
                str(entity.armor_class[0])
                if isinstance(entity.armor_class, list)
                else str(entity.armor_class)
            )
            parts.append(f"AC: {ac_text}")
        if hasattr(entity, "hit_points"):
            parts.append(f"HP: {entity.hit_points}")

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


def main():
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
        default="all-MiniLM-L6-v2",
        help="Sentence transformer model to use (default: all-MiniLM-L6-v2)",
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

    # Verify model dimensions match our schema
    test_embedding = model.encode("test", convert_to_numpy=True)
    expected_dim = 384  # Our schema expects 384 dimensions
    actual_dim = len(test_embedding)

    if actual_dim != expected_dim:
        logger.error(
            f"Model dimension mismatch! Expected {expected_dim}, got {actual_dim}. "
            f"Please use a model that produces {expected_dim}-dimensional embeddings."
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
