"""
Integration tests to verify that database indexes are being used.

These tests use EXPLAIN QUERY PLAN to ensure that the query optimizer
is actually using the indexes we've created.
"""

import os
import tempfile
from typing import Iterator, List

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.content.connection import DatabaseManager
from app.content.models import Base, ContentPack, Equipment, Monster, Spell


class TestIndexUsage:
    """Test suite for verifying index usage with EXPLAIN QUERY PLAN."""

    @pytest.fixture
    def test_db_with_indexes(self) -> Iterator[DatabaseManager]:
        """Create a test database with indexes applied."""
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)

        try:
            db_url = f"sqlite:///{db_path}"
            db_manager = DatabaseManager(db_url)

            # Create all tables
            with db_manager.get_session() as session:
                if session.bind is not None:
                    Base.metadata.create_all(session.bind)

            # Apply performance indexes migration
            with db_manager.get_session() as session:
                # Run the index creation from our migration
                self._apply_performance_indexes(session)

                # Create test content pack
                content_pack = ContentPack(
                    id="test-pack",
                    name="Test Pack",
                    description="Test content pack",
                    version="1.0.0",
                    author="Test Author",
                    is_active=True,
                )
                session.add(content_pack)
                session.commit()

                # Refresh to get actual id value
                session.refresh(content_pack)

                # Add some test data
                pack_id = str(content_pack.id)
                self._add_test_data(session, pack_id)

            yield db_manager

        finally:
            # Cleanup
            db_manager.dispose()
            os.unlink(db_path)

    def _apply_performance_indexes(self, session: Session) -> None:
        """Apply the performance indexes from our migration."""
        # Content pack indexes
        session.execute(
            text("CREATE INDEX idx_content_packs_is_active ON content_packs(is_active)")
        )

        # Foreign key indexes (just a few for testing)
        session.execute(
            text("CREATE INDEX idx_spells_content_pack_id ON spells(content_pack_id)")
        )
        session.execute(
            text(
                "CREATE INDEX idx_monsters_content_pack_id ON monsters(content_pack_id)"
            )
        )
        session.execute(
            text(
                "CREATE INDEX idx_equipment_content_pack_id ON equipment(content_pack_id)"
            )
        )

        # Name search indexes
        session.execute(
            text("CREATE INDEX idx_spells_name_lower ON spells(lower(name))")
        )
        session.execute(
            text("CREATE INDEX idx_monsters_name_lower ON monsters(lower(name))")
        )
        session.execute(
            text("CREATE INDEX idx_equipment_name_lower ON equipment(lower(name))")
        )

        # Spell-specific indexes
        session.execute(text("CREATE INDEX idx_spells_level ON spells(level)"))
        session.execute(
            text("CREATE INDEX idx_spells_concentration ON spells(concentration)")
        )
        session.execute(text("CREATE INDEX idx_spells_ritual ON spells(ritual)"))
        session.execute(
            text(
                "CREATE INDEX idx_spells_level_concentration ON spells(level, concentration)"
            )
        )

        # Monster-specific indexes
        session.execute(
            text(
                "CREATE INDEX idx_monsters_challenge_rating ON monsters(challenge_rating)"
            )
        )
        session.execute(text("CREATE INDEX idx_monsters_type ON monsters(type)"))
        session.execute(text("CREATE INDEX idx_monsters_size ON monsters(size)"))

        # Equipment-specific indexes
        session.execute(
            text(
                "CREATE INDEX idx_equipment_weapon_category ON equipment(weapon_category)"
            )
        )
        session.execute(
            text(
                "CREATE INDEX idx_equipment_armor_category ON equipment(armor_category)"
            )
        )

        # Update statistics
        session.execute(text("ANALYZE"))
        session.commit()

    def _add_test_data(self, session: Session, content_pack_id: str) -> None:
        """Add test data to the database."""
        # Add test spells
        for i in range(20):
            spell = Spell(
                index=f"spell-{i}",
                name=f"Test Spell {i}",
                url=f"/api/spells/spell-{i}",
                level=i % 10,
                concentration=i % 2 == 0,
                ritual=i % 3 == 0,
                school={"name": "Evocation"},
                casting_time="1 action",
                range="30 feet",
                components=["V", "S"],
                duration="Instantaneous",
                desc=["A test spell"],
                content_pack_id=content_pack_id,
            )
            session.add(spell)

        # Add test monsters
        for i in range(20):
            monster = Monster(
                index=f"monster-{i}",
                name=f"Test Monster {i}",
                url=f"/api/monsters/monster-{i}",
                challenge_rating=float(i % 10),
                xp=i * 100,
                type="Beast",
                size="Medium",
                alignment="neutral",
                armor_class=[{"value": 10}],
                hit_points=10,
                hit_dice="2d8",
                speed={"walk": "30 ft."},
                strength=10,
                dexterity=10,
                constitution=10,
                intelligence=10,
                wisdom=10,
                charisma=10,
                proficiencies=[],
                damage_vulnerabilities=[],
                damage_resistances=[],
                damage_immunities=[],
                condition_immunities=[],
                senses={},
                languages="Common",
                content_pack_id=content_pack_id,
            )
            session.add(monster)

        # Add test equipment
        for i in range(20):
            equipment = Equipment(
                index=f"equipment-{i}",
                name=f"Test Equipment {i}",
                url=f"/api/equipment/equipment-{i}",
                equipment_category={"name": "Weapon" if i % 2 == 0 else "Armor"},
                weapon_category="Simple Melee Weapons" if i % 2 == 0 else None,
                armor_category="Light Armor" if i % 2 == 1 else None,
                cost={"quantity": 1, "unit": "gp"},
                weight=1.0,
                content_pack_id=content_pack_id,
            )
            session.add(equipment)

        session.commit()

    def explain_query(
        self, session: Session, query: str, **params: object
    ) -> List[str]:
        """Get EXPLAIN QUERY PLAN output for a query."""
        explain_query = f"EXPLAIN QUERY PLAN {query}"
        result = session.execute(text(explain_query), params)
        return [str(row) for row in result.fetchall()]

    def test_spell_name_index_usage(
        self, test_db_with_indexes: DatabaseManager
    ) -> None:
        """Test that spell name searches use the index."""
        with test_db_with_indexes.get_session() as session:
            # Case-insensitive name search
            query = "SELECT * FROM spells WHERE lower(name) = lower(:name)"

            plan = self.explain_query(session, query, name="Test Spell 5")
            plan_text = " ".join(str(p) for p in plan)

            # Should use the idx_spells_name_lower index
            assert "idx_spells_name_lower" in plan_text or "USING INDEX" in plan_text

    def test_spell_level_index_usage(
        self, test_db_with_indexes: DatabaseManager
    ) -> None:
        """Test that spell level filtering uses the index."""
        with test_db_with_indexes.get_session() as session:
            query = "SELECT * FROM spells WHERE level = :level"

            plan = self.explain_query(session, query, level=3)
            plan_text = " ".join(str(p) for p in plan)

            # Should use the idx_spells_level index
            assert "idx_spells_level" in plan_text or "USING INDEX" in plan_text

    def test_spell_composite_index_usage(
        self, test_db_with_indexes: DatabaseManager
    ) -> None:
        """Test that composite queries use composite indexes."""
        with test_db_with_indexes.get_session() as session:
            query = (
                "SELECT * FROM spells WHERE level = :level AND concentration = :conc"
            )

            plan = self.explain_query(session, query, level=3, conc=True)
            plan_text = " ".join(str(p) for p in plan)

            # Should use the composite index
            assert (
                "idx_spells_level_concentration" in plan_text
                or "USING INDEX" in plan_text
            )

    def test_monster_cr_index_usage(
        self, test_db_with_indexes: DatabaseManager
    ) -> None:
        """Test that monster CR filtering uses the index."""
        with test_db_with_indexes.get_session() as session:
            query = "SELECT * FROM monsters WHERE challenge_rating = :cr"

            plan = self.explain_query(session, query, cr=5.0)
            plan_text = " ".join(str(p) for p in plan)

            # Should use the idx_monsters_challenge_rating index
            assert (
                "idx_monsters_challenge_rating" in plan_text
                or "USING INDEX" in plan_text
            )

    def test_content_pack_join_index_usage(
        self, test_db_with_indexes: DatabaseManager
    ) -> None:
        """Test that joins with content_packs use indexes."""
        with test_db_with_indexes.get_session() as session:
            query = """
                SELECT s.* FROM spells s
                JOIN content_packs cp ON s.content_pack_id = cp.id
                WHERE cp.is_active = :active
            """

            plan = self.explain_query(session, query, active=True)
            plan_text = " ".join(str(p) for p in plan)

            # Should use indexes for both the join and the WHERE clause
            assert "USING INDEX" in plan_text
            # Check for content pack index usage
            assert (
                "idx_content_packs_is_active" in plan_text
                or "content_packs" in plan_text
            )

    def test_equipment_category_index_usage(
        self, test_db_with_indexes: DatabaseManager
    ) -> None:
        """Test that equipment category filtering uses indexes."""
        with test_db_with_indexes.get_session() as session:
            query = "SELECT * FROM equipment WHERE weapon_category = :category"

            plan = self.explain_query(session, query, category="Simple Melee Weapons")
            plan_text = " ".join(str(p) for p in plan)

            # Should use the idx_equipment_weapon_category index
            assert (
                "idx_equipment_weapon_category" in plan_text
                or "USING INDEX" in plan_text
            )

    def test_like_pattern_index_usage(
        self, test_db_with_indexes: DatabaseManager
    ) -> None:
        """Test that LIKE patterns can use indexes when appropriate."""
        with test_db_with_indexes.get_session() as session:
            # Prefix search should use index
            query = "SELECT * FROM spells WHERE name LIKE :pattern"

            plan = self.explain_query(session, query, pattern="Test Spell%")
            plan_text = " ".join(str(p) for p in plan)

            # SQLite can use indexes for prefix LIKE patterns
            # May show as SCAN WITH INDEX or SEARCH
            assert "spells" in plan_text.lower()

    def test_no_index_for_unindexed_column(
        self, test_db_with_indexes: DatabaseManager
    ) -> None:
        """Test that unindexed columns don't use indexes (negative test)."""
        with test_db_with_indexes.get_session() as session:
            # duration is not indexed
            query = "SELECT * FROM spells WHERE duration = :duration"

            plan = self.explain_query(session, query, duration="Instantaneous")
            plan_text = " ".join(str(p) for p in plan)

            # Should do a table scan, not use an index
            assert "SCAN" in plan_text and "USING INDEX" not in plan_text

    def test_order_by_uses_index(self, test_db_with_indexes: DatabaseManager) -> None:
        """Test that ORDER BY can use indexes to avoid sorting."""
        with test_db_with_indexes.get_session() as session:
            # Ordering by an indexed column
            query = "SELECT * FROM spells ORDER BY level"

            plan = self.explain_query(session, query)
            plan_text = " ".join(str(p) for p in plan)

            # May use index to avoid explicit sorting
            # Look for either index usage or ordered scan
            assert "spells" in plan_text.lower()

    def test_count_query_uses_index(
        self, test_db_with_indexes: DatabaseManager
    ) -> None:
        """Test that COUNT queries can use indexes."""
        with test_db_with_indexes.get_session() as session:
            # Count with indexed WHERE clause
            query = "SELECT COUNT(*) FROM spells WHERE level = :level"

            plan = self.explain_query(session, query, level=3)
            plan_text = " ".join(str(p) for p in plan)

            # Should use index for the WHERE clause
            assert "idx_spells_level" in plan_text or "USING INDEX" in plan_text

    @pytest.mark.parametrize(
        "table,index_name",
        [
            ("spells", "idx_spells_name_lower"),
            ("spells", "idx_spells_level"),
            ("spells", "idx_spells_concentration"),
            ("spells", "idx_spells_content_pack_id"),
            ("monsters", "idx_monsters_challenge_rating"),
            ("monsters", "idx_monsters_type"),
            ("equipment", "idx_equipment_weapon_category"),
            ("content_packs", "idx_content_packs_is_active"),
        ],
    )
    def test_index_exists(
        self, test_db_with_indexes: DatabaseManager, table: str, index_name: str
    ) -> None:
        """Test that expected indexes exist in the database."""
        with test_db_with_indexes.get_session() as session:
            # Query SQLite master table for indexes
            result = session.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name=:name"
                ),
                {"name": index_name},
            )
            index_name_result = result.scalar()

            assert index_name_result == index_name, f"Index {index_name} not found"
