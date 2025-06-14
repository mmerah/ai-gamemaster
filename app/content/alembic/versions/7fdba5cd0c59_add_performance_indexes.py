"""Add performance indexes

Revision ID: 7fdba5cd0c59
Revises: 2032c7f301f0
Create Date: 2025-06-13 12:29:39.892839

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7fdba5cd0c59"
down_revision: Union[str, None] = "2032c7f301f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for all D&D 5e tables."""

    # Get connection for raw SQL
    conn = op.get_bind()

    # ========== Content Pack Indexes ==========
    # Active content packs are frequently filtered
    # Use raw SQL with IF NOT EXISTS for idempotency
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_content_packs_is_active ON content_packs(is_active)"
        )
    )

    # ========== Foreign Key Indexes for All Tables ==========
    # These improve JOIN performance with content_packs
    tables_with_content_pack = [
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

    for table in tables_with_content_pack:
        conn.execute(
            sa.text(
                f"CREATE INDEX IF NOT EXISTS idx_{table}_content_pack_id ON {table}(content_pack_id)"
            )
        )

    # ========== Name Search Indexes (Case-Insensitive) ==========
    # Most tables have name searches, create expression indexes
    tables_with_names = [
        "spells",
        "monsters",
        "equipment",
        "classes",
        "features",
        "races",
        "backgrounds",
        "conditions",
        "damage_types",
        "magic_items",
        "proficiencies",
        "skills",
        "alignments",
        "ability_scores",
        "equipment_categories",
        "feats",
        "languages",
        "magic_schools",
        "rule_sections",
        "rules",
        "subclasses",
        "subraces",
        "traits",
        "weapon_properties",
    ]

    # Note: SQLite supports expression indexes like lower(name)
    # We'll use raw SQL for these
    for table in tables_with_names:
        conn.execute(
            sa.text(
                f"CREATE INDEX IF NOT EXISTS idx_{table}_name_lower ON {table}(lower(name))"
            )
        )

    # ========== Spell-Specific Indexes ==========
    conn.execute(
        sa.text("CREATE INDEX IF NOT EXISTS idx_spells_level ON spells(level)")
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_spells_concentration ON spells(concentration)"
        )
    )
    conn.execute(
        sa.text("CREATE INDEX IF NOT EXISTS idx_spells_ritual ON spells(ritual)")
    )

    # Composite indexes for common filter combinations
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_spells_level_concentration ON spells(level, concentration)"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_spells_level_ritual ON spells(level, ritual)"
        )
    )

    # JSON field indexes (limited support in SQLite, but helps with exact matches)
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_spells_school_name ON spells(json_extract(school, '$.name'))"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_spells_casting_time ON spells(casting_time)"
        )
    )
    conn.execute(
        sa.text("CREATE INDEX IF NOT EXISTS idx_spells_range ON spells(range)")
    )

    # ========== Monster-Specific Indexes ==========
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_monsters_challenge_rating ON monsters(challenge_rating)"
        )
    )
    conn.execute(
        sa.text("CREATE INDEX IF NOT EXISTS idx_monsters_type ON monsters(type)")
    )
    conn.execute(
        sa.text("CREATE INDEX IF NOT EXISTS idx_monsters_size ON monsters(size)")
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_monsters_alignment ON monsters(alignment)"
        )
    )

    # Composite indexes for common queries
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_monsters_cr_type ON monsters(challenge_rating, type)"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_monsters_type_size ON monsters(type, size)"
        )
    )

    # HP and XP for sorting/filtering
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_monsters_hit_points ON monsters(hit_points)"
        )
    )
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_monsters_xp ON monsters(xp)"))

    # ========== Equipment-Specific Indexes ==========
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_equipment_weapon_category ON equipment(weapon_category)"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_equipment_armor_category ON equipment(armor_category)"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_equipment_weapon_range ON equipment(weapon_range)"
        )
    )

    # JSON field index for equipment category
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_equipment_category_name ON equipment(json_extract(equipment_category, '$.name'))"
        )
    )

    # Cost filtering (for shops)
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_equipment_cost_quantity ON equipment(json_extract(cost, '$.quantity'))"
        )
    )

    # ========== Class and Feature Indexes ==========
    conn.execute(
        sa.text("CREATE INDEX IF NOT EXISTS idx_classes_hit_die ON classes(hit_die)")
    )
    conn.execute(
        sa.text("CREATE INDEX IF NOT EXISTS idx_features_level ON features(level)")
    )

    # JSON field indexes for class/subclass references
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_features_class_index ON features(json_extract(class_ref, '$.index'))"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_features_subclass_index ON features(json_extract(subclass, '$.index'))"
        )
    )

    # ========== Level Indexes ==========
    conn.execute(
        sa.text("CREATE INDEX IF NOT EXISTS idx_levels_level ON levels(level)")
    )
    # JSON field indexes for class_ref and subclass
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_levels_class_index ON levels(json_extract(class_ref, '$.index'))"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_levels_subclass_index ON levels(json_extract(subclass, '$.index'))"
        )
    )

    # Composite for class progression queries with JSON extraction
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_levels_class_level ON levels(json_extract(class_ref, '$.index'), level)"
        )
    )
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_levels_subclass_level ON levels(json_extract(subclass, '$.index'), level)"
        )
    )

    # ========== Magic Item Indexes ==========
    # JSON field indexes for rarity and category
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_magic_items_rarity ON magic_items(json_extract(rarity, '$.name'))"
        )
    )

    # ========== Race and Background Indexes ==========
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_races_size ON races(size)"))
    # JSON field index for race reference
    conn.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS idx_subraces_race_index ON subraces(json_extract(race, '$.index'))"
        )
    )

    # ========== Update Statistics ==========
    # Tell SQLite to analyze the tables and update query planner statistics
    conn.execute(sa.text("ANALYZE"))


def downgrade() -> None:
    """Remove performance indexes."""

    # Get connection for raw SQL
    conn = op.get_bind()

    # Drop content pack indexes
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_content_packs_is_active"))

    # Drop foreign key indexes
    tables_with_content_pack = [
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

    for table in tables_with_content_pack:
        conn.execute(sa.text(f"DROP INDEX IF EXISTS idx_{table}_content_pack_id"))

    # Drop name indexes
    tables_with_names = [
        "spells",
        "monsters",
        "equipment",
        "classes",
        "features",
        "races",
        "backgrounds",
        "conditions",
        "damage_types",
        "magic_items",
        "proficiencies",
        "skills",
        "alignments",
        "ability_scores",
        "equipment_categories",
        "feats",
        "languages",
        "magic_schools",
        "rule_sections",
        "rules",
        "subclasses",
        "subraces",
        "traits",
        "weapon_properties",
    ]

    for table in tables_with_names:
        conn.execute(sa.text(f"DROP INDEX IF EXISTS idx_{table}_name_lower"))

    # Drop spell indexes
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_spells_level"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_spells_concentration"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_spells_ritual"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_spells_level_concentration"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_spells_level_ritual"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_spells_school_name"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_spells_casting_time"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_spells_range"))

    # Drop monster indexes
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_monsters_challenge_rating"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_monsters_type"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_monsters_size"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_monsters_alignment"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_monsters_cr_type"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_monsters_type_size"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_monsters_hit_points"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_monsters_xp"))

    # Drop equipment indexes
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_equipment_weapon_category"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_equipment_armor_category"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_equipment_weapon_range"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_equipment_category_name"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_equipment_cost_quantity"))

    # Drop class/feature indexes
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_classes_hit_die"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_features_level"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_features_class_index"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_features_subclass_index"))

    # Drop level indexes
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_levels_level"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_levels_class_index"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_levels_subclass_index"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_levels_class_level"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_levels_subclass_level"))

    # Drop other indexes
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_magic_items_rarity"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_races_size"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_subraces_race_index"))
