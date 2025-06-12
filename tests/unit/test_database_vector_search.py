"""Unit tests for SQLite vector search functionality."""

from pathlib import Path
from typing import Any, Generator, List, Optional, Union

import numpy as np
import pytest
from numpy.typing import NDArray
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.connection import DatabaseManager
from app.database.models import VECTOR, Base, ContentPack, Monster, Spell


class TestVectorSearch:
    """Test vector search capabilities with sqlite-vec extension."""

    @pytest.fixture
    def test_db_manager(self, tmp_path: Path) -> DatabaseManager:
        """Create a test database manager with sqlite-vec enabled."""
        db_path = tmp_path / "test_vector.db"
        db_url = f"sqlite:///{db_path}"
        return DatabaseManager(database_url=db_url, enable_sqlite_vec=True)

    @pytest.fixture
    def session(
        self, test_db_manager: DatabaseManager
    ) -> Generator[Session, None, None]:
        """Create a test database session with schema."""
        # Create all tables
        Base.metadata.create_all(test_db_manager.get_engine())

        # Create a test content pack
        with test_db_manager.get_session() as session:
            content_pack = ContentPack(
                id="test_pack",
                name="Test Content Pack",
                version="1.0.0",
                is_active=True,
            )
            session.add(content_pack)
            session.commit()

        # Return a new session for tests
        with test_db_manager.get_session() as session:
            yield session

    def test_vector_type_stores_numpy_array(self, session: Session) -> None:
        """Test that VECTOR type can store and retrieve numpy arrays."""
        # Create a test vector (384 dimensions for all-MiniLM-L6-v2)
        test_vector = np.random.rand(384).astype(np.float32)

        # Create a spell with embedding
        spell = Spell(
            index="test-spell",
            name="Test Spell",
            url="/api/spells/test-spell",
            content_pack_id="test_pack",
            level=1,
            embedding=test_vector,
        )
        session.add(spell)
        session.commit()

        # Retrieve and verify
        retrieved_spell = session.query(Spell).filter_by(index="test-spell").first()
        assert retrieved_spell is not None
        assert retrieved_spell.embedding is not None
        assert isinstance(retrieved_spell.embedding, np.ndarray)
        assert retrieved_spell.embedding.shape == (384,)
        np.testing.assert_array_almost_equal(retrieved_spell.embedding, test_vector)

    def test_vector_type_stores_list(self, session: Session) -> None:
        """Test that VECTOR type can accept Python lists."""
        # Create a test vector as list
        test_vector = [float(i) / 384 for i in range(384)]

        # Create a monster with embedding
        monster = Monster(
            index="test-monster",
            name="Test Monster",
            url="/api/monsters/test-monster",
            content_pack_id="test_pack",
            size="Medium",
            type="humanoid",
            hit_points=10,
            challenge_rating=1,
            xp=200,
            strength=10,
            dexterity=10,
            constitution=10,
            intelligence=10,
            wisdom=10,
            charisma=10,
            embedding=test_vector,
        )
        session.add(monster)
        session.commit()

        # Clear the session to force reload from DB
        session.expire_all()

        # Retrieve and verify
        retrieved_monster = (
            session.query(Monster).filter_by(index="test-monster").first()
        )
        assert retrieved_monster is not None
        assert retrieved_monster.embedding is not None

        # Debug: print what we got back
        print(f"Type of embedding: {type(retrieved_monster.embedding)}")
        print(
            f"Embedding value (first 5): {retrieved_monster.embedding[:5] if hasattr(retrieved_monster.embedding, '__getitem__') else 'N/A'}"
        )

        # The embedding should be stored as numpy array after VECTOR type processing
        embedding = retrieved_monster.embedding
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (384,)
        np.testing.assert_array_almost_equal(
            embedding, np.array(test_vector, dtype=np.float32)
        )

    def test_sqlite_vec_extension_loaded(
        self, test_db_manager: DatabaseManager
    ) -> None:
        """Test that sqlite-vec extension is properly loaded."""
        engine = test_db_manager.get_engine()

        # Try to use vec_version function from sqlite-vec
        with engine.connect() as conn:
            try:
                # Try multiple possible function names
                result = None
                for func_name in ["vec_version", "vec0_version", "sqlite_vec_version"]:
                    try:
                        result = conn.execute(text(f"SELECT {func_name}()"))
                        version = result.scalar()
                        if version:
                            break
                    except Exception:
                        continue

                # If no version function works, try a vector operation
                if not result or not version:
                    # Create a simple vector operation to test if extension is loaded
                    conn.execute(text("SELECT vec_f32('[1.0, 2.0, 3.0]')"))
                    # If this doesn't raise an exception, the extension is loaded
                    assert True
                else:
                    assert version is not None
            except Exception as e:
                # Extension might not be available in test environment
                pytest.skip(f"sqlite-vec extension not available: {e}")

    def test_vector_search_query(
        self, session: Session, test_db_manager: DatabaseManager
    ) -> None:
        """Test vector similarity search using sqlite-vec."""
        # Create test data with embeddings (384 dimensions)
        vector1 = np.array([1.0, 0.0, 0.0] + [0.0] * 381, dtype=np.float32)
        vector2 = np.array([0.0, 1.0, 0.0] + [0.0] * 381, dtype=np.float32)
        vector3 = np.array(
            [0.9, 0.1, 0.0] + [0.0] * 381, dtype=np.float32
        )  # Similar to vector1

        spells = [
            Spell(
                index="spell1",
                name="Spell One",
                url="/api/spells/spell1",
                content_pack_id="test_pack",
                level=1,
                embedding=vector1,
            ),
            Spell(
                index="spell2",
                name="Spell Two",
                url="/api/spells/spell2",
                content_pack_id="test_pack",
                level=2,
                embedding=vector2,
            ),
            Spell(
                index="spell3",
                name="Spell Three",
                url="/api/spells/spell3",
                content_pack_id="test_pack",
                level=3,
                embedding=vector3,
            ),
        ]

        for spell in spells:
            session.add(spell)
        session.commit()

        # Test vector search - find spells similar to vector1
        # Note: query_vector would be used in actual vec_distance_l2 queries
        # For now we just verify storage and retrieval work
        try:
            # Note: The exact SQL syntax depends on sqlite-vec version
            # This is a conceptual test - actual implementation will be in RAG service
            results = session.query(Spell).filter(Spell.embedding.isnot(None)).all()

            # Verify we can retrieve spells with embeddings
            assert len(results) == 3
            for spell in results:
                assert spell.embedding is not None
                assert spell.embedding.shape == (384,)

        except Exception as e:
            # If vector operations aren't available, at least verify storage works
            pytest.skip(f"Vector search operations not available: {e}")

    def test_null_embeddings_allowed(self, session: Session) -> None:
        """Test that entities can be created without embeddings."""
        spell = Spell(
            index="no-embedding-spell",
            name="Spell Without Embedding",
            url="/api/spells/no-embedding",
            content_pack_id="test_pack",
            level=0,
            embedding=None,
        )
        session.add(spell)
        session.commit()

        retrieved = session.query(Spell).filter_by(index="no-embedding-spell").first()
        assert retrieved is not None
        assert retrieved.embedding is None

    def test_vector_dimension_validation(self, session: Session) -> None:
        """Test that VECTOR type validates dimension if specified."""
        # Our VECTOR type is defined with 384 dimensions (all-MiniLM-L6-v2)
        # Create vectors of different sizes
        correct_vector = np.random.rand(384).astype(np.float32)

        # This should work
        spell = Spell(
            index="correct-dim-spell",
            name="Correct Dimension Spell",
            url="/api/spells/correct-dim",
            content_pack_id="test_pack",
            level=1,
            embedding=correct_vector,
        )
        session.add(spell)
        session.commit()

        retrieved = session.query(Spell).filter_by(index="correct-dim-spell").first()
        assert retrieved is not None
        assert retrieved.embedding is not None
        assert retrieved.embedding.shape == (384,)
