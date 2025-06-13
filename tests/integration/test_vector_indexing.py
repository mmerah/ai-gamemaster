"""Integration tests for vector indexing script."""

from typing import Any, Dict, Generator, List, Optional, Type, Union

import numpy as np
import pytest
from sqlalchemy import create_engine, func
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Base, ContentPack, Monster, Spell
from app.database.types import Vector


class TestVectorIndexing:
    """Test the vector indexing script results."""

    @pytest.fixture
    def db_session(self, test_db_session: Session) -> Generator[Session, None, None]:
        """Use the test database session."""
        yield test_db_session

    def test_spells_have_embeddings(self, db_session: Session) -> None:
        """Test that spells have been indexed with embeddings."""
        # Count total spells
        total_spells = db_session.query(Spell).count()
        assert total_spells > 0, "No spells found in database"

        # Count spells with embeddings
        spells_with_embeddings = (
            db_session.query(Spell).filter(Spell.embedding.isnot(None)).count()
        )

        # All spells should have embeddings after indexing
        assert spells_with_embeddings == total_spells, (
            f"Not all spells have embeddings: {spells_with_embeddings}/{total_spells}"
        )

        # Check a specific spell
        fireball = db_session.query(Spell).filter_by(index="fireball").first()
        assert fireball is not None, "Fireball spell not found"
        assert fireball.embedding is not None, "Fireball has no embedding"

        # Verify embedding dimensions
        # The VECTOR type should convert to numpy array
        assert isinstance(fireball.embedding, np.ndarray)
        assert fireball.embedding.shape == (384,), (
            f"Wrong embedding dimensions: {fireball.embedding.shape}"
        )

    def test_monsters_have_embeddings(self, db_session: Session) -> None:
        """Test that monsters have been indexed with embeddings."""
        # Count total monsters
        total_monsters = db_session.query(Monster).count()
        assert total_monsters > 0, "No monsters found in database"

        # Count monsters with embeddings
        monsters_with_embeddings = (
            db_session.query(Monster).filter(Monster.embedding.isnot(None)).count()
        )

        # All monsters should have embeddings after indexing
        assert monsters_with_embeddings == total_monsters, (
            f"Not all monsters have embeddings: {monsters_with_embeddings}/{total_monsters}"
        )

        # Check a specific monster
        goblin = db_session.query(Monster).filter_by(index="goblin").first()
        assert goblin is not None, "Goblin monster not found"
        assert goblin.embedding is not None, "Goblin has no embedding"

    def test_embedding_content_quality(self, db_session: Session) -> None:
        """Test that embeddings capture relevant content."""
        # Get two similar spells (fire damage spells)
        fireball = db_session.query(Spell).filter_by(index="fireball").first()
        burning_hands = db_session.query(Spell).filter_by(index="burning-hands").first()

        # Get a dissimilar spell (healing)
        cure_wounds = db_session.query(Spell).filter_by(index="cure-wounds").first()

        assert fireball is not None, "Fireball spell not found"
        assert burning_hands is not None, "Burning Hands spell not found"
        assert cure_wounds is not None, "Cure Wounds spell not found"

        # Convert embeddings to numpy arrays if needed
        def to_numpy(
            embedding: Union[bytes, Vector, None],
        ) -> Vector:
            if isinstance(embedding, bytes):
                return np.frombuffer(embedding, dtype=np.float32)
            assert embedding is not None
            return embedding

        assert fireball.embedding is not None
        assert burning_hands.embedding is not None
        assert cure_wounds.embedding is not None

        fireball_emb = to_numpy(fireball.embedding)
        burning_hands_emb = to_numpy(burning_hands.embedding)
        cure_wounds_emb = to_numpy(cure_wounds.embedding)

        # Calculate cosine similarities
        def cosine_similarity(a: Vector, b: Vector) -> float:
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

        fire_similarity = cosine_similarity(fireball_emb, burning_hands_emb)
        heal_similarity = cosine_similarity(fireball_emb, cure_wounds_emb)

        # Fire spells should be more similar to each other than to healing spells
        assert fire_similarity > heal_similarity, (
            f"Fire spell similarity ({fire_similarity:.3f}) should be higher than "
            f"fire-healing similarity ({heal_similarity:.3f})"
        )

    def test_all_content_types_indexed(self, db_session: Session) -> None:
        """Test that all major content types have embeddings."""
        from app.database.models import (
            Background,
            CharacterClass,
            Condition,
            Equipment,
            Feat,
            Feature,
            MagicItem,
            Race,
            Skill,
            Trait,
        )

        content_types: Dict[str, Type[Any]] = {
            "Equipment": Equipment,
            "Classes": CharacterClass,
            "Features": Feature,
            "Backgrounds": Background,
            "Races": Race,
            "Feats": Feat,
            "Magic Items": MagicItem,
            "Traits": Trait,
            "Conditions": Condition,
            "Skills": Skill,
        }

        for content_name, content_class in content_types.items():
            total = db_session.query(content_class).count()
            if total > 0:  # Only check if there's content
                with_embeddings = (
                    db_session.query(content_class)
                    .filter(content_class.embedding.isnot(None))
                    .count()
                )
                assert with_embeddings == total, (
                    f"{content_name}: Not all entities have embeddings "
                    f"({with_embeddings}/{total})"
                )
