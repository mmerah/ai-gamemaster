#!/usr/bin/env python3
"""
Set up a test database with indexed content for integration tests.

This script:
1. Creates a copy of the production database for testing
2. Ensures all content has vector embeddings
"""

import argparse
import logging
import shutil
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.index_content_for_rag import main as index_main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def setup_test_database(
    source_db: str = "data/content.db", target_db: str = "data/test_content.db"
) -> None:
    """Set up the test database with indexed content."""
    source_path = Path(source_db)
    target_path = Path(target_db)

    # Ensure source exists
    if not source_path.exists():
        logger.error(f"Source database not found: {source_path}")
        sys.exit(1)

    # Copy database
    logger.info(f"Copying {source_path} to {target_path}")
    shutil.copy2(source_path, target_path)

    # Index the test database
    logger.info("Indexing test database...")
    test_db_url = f"sqlite:///{target_path}"

    # Call the indexing function
    original_argv = sys.argv
    try:
        sys.argv = ["index_content_for_rag.py", test_db_url]
        index_main()
    finally:
        sys.argv = original_argv

    logger.info(f"Test database ready at: {target_path}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Set up test database with indexed content"
    )
    parser.add_argument(
        "--source",
        default="data/content.db",
        help="Source database path (default: data/content.db)",
    )
    parser.add_argument(
        "--target",
        default="data/test_content.db",
        help="Target test database path (default: data/test_content.db)",
    )

    args = parser.parse_args()

    setup_test_database(args.source, args.target)


if __name__ == "__main__":
    main()
