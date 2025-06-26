"""add_fts5_virtual_tables

Revision ID: 0ee5c6730f10
Revises: 8a1b2c3d4e5f
Create Date: 2025-06-26 19:13:29.332381

"""

import logging
from typing import List, Sequence, Tuple, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "0ee5c6730f10"
down_revision: Union[str, None] = "8a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Define tables and their searchable columns for FTS5
    tables_config: List[Tuple[str, List[str]]] = [
        ("ability_scores", ["index", "full_name", "desc"]),
        ("alignments", ["index", "name", "abbreviation", "desc"]),
        ("backgrounds", ["index", "name", "desc"]),
        ("classes", ["index", "name", "desc", "hit_die"]),
        ("conditions", ["index", "name", "desc"]),
        ("damage_types", ["index", "name", "desc"]),
        ("equipment", ["index", "name", "equipment_category", "desc"]),
        ("equipment_categories", ["index", "name"]),
        ("feats", ["index", "name", "desc", "prerequisites"]),
        ("features", ["index", "name", "desc"]),
        ("languages", ["index", "name", "type", "typical_speakers"]),
        ("levels", ["index", "class_name"]),
        ("magic_items", ["index", "name", "equipment_category", "desc"]),
        ("magic_schools", ["index", "name", "desc"]),
        ("monsters", ["index", "name", "size", "type", "alignment"]),
        ("proficiencies", ["index", "type", "name"]),
        ("races", ["index", "name", "desc", "size_description", "age", "alignment"]),
        ("rule_sections", ["index", "name", "desc"]),
        ("rules", ["index", "name", "desc"]),
        ("skills", ["index", "name", "desc"]),
        ("spells", ["index", "name", "desc", "range", "components", "duration"]),
        ("subclasses", ["index", "class_name", "name", "subclass_flavor", "desc"]),
        ("subraces", ["index", "name", "race", "desc"]),
        ("traits", ["index", "name", "desc"]),
        ("weapon_properties", ["index", "name", "desc"]),
    ]

    # Check FTS5 support
    connection = op.get_bind()
    try:
        result = connection.execute(
            text("SELECT sqlite_compileoption_used('ENABLE_FTS5')")
        ).scalar()
        if not result:
            logging.warning(
                "SQLite FTS5 extension not available. Skipping FTS table creation."
            )
            return
    except Exception as e:
        logging.error(f"Error checking FTS5 support: {e}")
        return

    # Create FTS5 virtual tables
    for table_name, searchable_columns in tables_config:
        fts_table_name = f"{table_name}_fts"

        # Drop existing FTS table if it exists
        op.execute(text(f"DROP TABLE IF EXISTS {fts_table_name}"))

        # Create FTS5 virtual table
        columns_str = ", ".join(
            searchable_columns[1:]
        )  # Skip 'id' as it will be 'entity_id'
        create_sql = f"""
            CREATE VIRTUAL TABLE {fts_table_name} 
            USING fts5(
                entity_id UNINDEXED,
                {columns_str},
                tokenize='porter unicode61'
            )
        """
        op.execute(text(create_sql))

        # Populate FTS table from source table
        # Build column list for INSERT and SELECT
        insert_columns = ["entity_id"] + searchable_columns[1:]

        # Special handling for classes table to convert hit_die to searchable text
        if table_name == "classes":
            select_expressions = []
            for col in searchable_columns:
                if col == "hit_die":
                    # Convert numeric hit_die to searchable text like "Hit Die: d12"
                    select_expressions.append(
                        f'CASE WHEN "{col}" IS NOT NULL THEN \'Hit Die: d\' || "{col}" ELSE NULL END'
                    )
                else:
                    select_expressions.append(f'"{col}"')
        else:
            # For other tables, use columns as-is
            select_expressions = [f'"{col}"' for col in searchable_columns]

        # Build WHERE clause to ensure at least one searchable column is not NULL
        where_conditions = " OR ".join(
            f'"{col}" IS NOT NULL' for col in searchable_columns[1:]
        )

        # Quote column names to handle reserved keywords like 'index'
        quoted_insert_columns = [f'"{col}"' for col in insert_columns]

        insert_sql = f"""
            INSERT INTO {fts_table_name} ({", ".join(quoted_insert_columns)})
            SELECT {", ".join(select_expressions)}
            FROM {table_name}
            WHERE {where_conditions}
        """
        op.execute(text(insert_sql))

        logging.info(f"Created FTS5 table '{fts_table_name}' for '{table_name}'")


def downgrade() -> None:
    """Downgrade schema."""
    # List of tables that have FTS5 virtual tables
    tables = [
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

    # Drop all FTS5 virtual tables
    for table_name in tables:
        fts_table_name = f"{table_name}_fts"
        op.execute(text(f"DROP TABLE IF EXISTS {fts_table_name}"))
