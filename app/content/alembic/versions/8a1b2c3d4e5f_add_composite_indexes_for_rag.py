"""Add composite indexes for RAG content pack priority

Revision ID: 8a1b2c3d4e5f
Revises: 63db3a289b42
Create Date: 2025-06-15 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8a1b2c3d4e5f"
down_revision: Union[str, None] = "63db3a289b42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite indexes for content pack priority queries."""

    # Get connection for raw SQL
    conn = op.get_bind()

    # Tables that are commonly searched by name with content pack filtering
    # These are the tables used in RAG vector search
    tables_for_composite_index = [
        "spells",
        "monsters",
        "equipment",
        "classes",
        "races",
        "backgrounds",
        "feats",
        "features",
        "conditions",
        "traits",
        "magic_items",
    ]

    # Create composite indexes on (content_pack_id, name)
    # This helps the RAG query that does:
    # - Filter by content_pack_id IN (...)
    # - Partition by name
    # - Order by content pack priority
    for table in tables_for_composite_index:
        conn.execute(
            sa.text(
                f"CREATE INDEX IF NOT EXISTS idx_{table}_content_pack_name "
                f"ON {table}(content_pack_id, name)"
            )
        )

    # Add a comment explaining the purpose of these indexes
    # Note: SQLite doesn't support comments, but we document it here
    # These indexes optimize the RAG vector search query that uses:
    # ROW_NUMBER() OVER (PARTITION BY name ORDER BY CASE content_pack_id ...)

    # Update statistics for query planner
    conn.execute(sa.text("ANALYZE"))


def downgrade() -> None:
    """Remove composite indexes."""

    # Get connection for raw SQL
    conn = op.get_bind()

    # Drop composite indexes
    tables_for_composite_index = [
        "spells",
        "monsters",
        "equipment",
        "classes",
        "races",
        "backgrounds",
        "feats",
        "features",
        "conditions",
        "traits",
        "magic_items",
    ]

    for table in tables_for_composite_index:
        conn.execute(sa.text(f"DROP INDEX IF EXISTS idx_{table}_content_pack_name"))
