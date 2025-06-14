"""Add migration history table

Revision ID: 63db3a289b42
Revises: 7fdba5cd0c59
Create Date: 2025-06-13 11:24:49.943999

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "63db3a289b42"
down_revision: Union[str, None] = "7fdba5cd0c59"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create migration_history table for tracking migrations
    op.create_table(
        "migration_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("migration_id", sa.String(length=100), nullable=False),
        sa.Column("content_pack_id", sa.String(length=100), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("items_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("backup_path", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("migration_id"),
    )

    # Create indexes for efficient queries
    op.create_index(
        "idx_migration_history_content_pack", "migration_history", ["content_pack_id"]
    )
    op.create_index("idx_migration_history_status", "migration_history", ["status"])
    op.create_index(
        "idx_migration_history_started_at", "migration_history", ["started_at"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index("idx_migration_history_started_at", "migration_history")
    op.drop_index("idx_migration_history_status", "migration_history")
    op.drop_index("idx_migration_history_content_pack", "migration_history")

    # Drop the table
    op.drop_table("migration_history")
