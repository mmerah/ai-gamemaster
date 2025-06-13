"""SQLAlchemy database models for D&D 5e content.

This module defines all database tables for storing D&D 5e ruleset data,
including spells, monsters, equipment, and other game content.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

import numpy as np
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import BLOB, TypeDecorator

from app.database.types import (
    DEFAULT_VECTOR_DIMENSION,
    SUPPORTED_VECTOR_DIMENSIONS,
    OptionalVector,
    Vector,
    VectorInput,
    is_valid_vector_dimension,
    validate_vector_dimension,
)


class VECTOR(TypeDecorator[OptionalVector]):
    """Custom type for storing vector embeddings.

    When using SQLite with sqlite-vec, vectors are stored as BLOB.
    This type handles conversion between numpy arrays and binary format
    with dimension validation for type safety.
    """

    impl = BLOB
    cache_ok = True

    def __init__(self, dim: Optional[int] = None):
        """Initialize VECTOR type with dimension validation.

        Args:
            dim: Dimension of the vector (e.g., 384 for all-MiniLM-L6-v2).
                 If None, uses DEFAULT_VECTOR_DIMENSION.

        Raises:
            ValueError: If the dimension is not supported.
        """
        self.dim = dim if dim is not None else DEFAULT_VECTOR_DIMENSION

        if not is_valid_vector_dimension(self.dim):
            raise ValueError(
                f"Unsupported vector dimension: {self.dim}. "
                f"Supported dimensions: {sorted(SUPPORTED_VECTOR_DIMENSIONS)}"
            )

        super().__init__()

    def process_bind_param(
        self, value: Optional[VectorInput], dialect: Any
    ) -> Optional[bytes]:
        """Convert numpy array or list to binary format for storage.

        Args:
            value: Vector input (numpy array, list, or None)
            dialect: SQLAlchemy dialect

        Returns:
            Binary representation of the vector or None

        Raises:
            ValueError: If the input type is invalid or dimension doesn't match
        """
        if value is None:
            return None

        # Convert list to numpy array if needed
        if isinstance(value, list):
            value = np.array(value, dtype=np.float32)
        elif not isinstance(value, np.ndarray):
            raise ValueError(f"Expected numpy array or list, got {type(value)}")

        # Validate vector dimension if specified
        if self.dim is not None:
            validate_vector_dimension(value, self.dim)

        # Ensure correct dtype and convert to bytes
        return value.astype(np.float32).tobytes()

    def process_result_value(
        self, value: Optional[bytes], dialect: Any
    ) -> OptionalVector:
        """Convert binary format back to numpy array.

        Args:
            value: Binary vector data or None
            dialect: SQLAlchemy dialect

        Returns:
            Numpy array with correct dimensions or None

        Raises:
            ValueError: If the stored vector dimension doesn't match expected
        """
        if value is None:
            return None

        # Convert bytes back to numpy array
        vector = np.frombuffer(value, dtype=np.float32)

        # Validate dimension if specified
        if self.dim is not None:
            validate_vector_dimension(vector, self.dim)

        return vector


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class ContentPack(Base):
    """Represents a collection of D&D content (SRD, homebrew, etc.)."""

    __tablename__ = "content_packs"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    version = Column(String(20), nullable=False)
    author = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    ability_scores = relationship(
        "AbilityScore", back_populates="content_pack", cascade="all, delete-orphan"
    )
    alignments = relationship(
        "Alignment", back_populates="content_pack", cascade="all, delete-orphan"
    )
    backgrounds = relationship(
        "Background", back_populates="content_pack", cascade="all, delete-orphan"
    )
    classes = relationship(
        "CharacterClass", back_populates="content_pack", cascade="all, delete-orphan"
    )
    conditions = relationship(
        "Condition", back_populates="content_pack", cascade="all, delete-orphan"
    )
    damage_types = relationship(
        "DamageType", back_populates="content_pack", cascade="all, delete-orphan"
    )
    equipment = relationship(
        "Equipment", back_populates="content_pack", cascade="all, delete-orphan"
    )
    equipment_categories = relationship(
        "EquipmentCategory", back_populates="content_pack", cascade="all, delete-orphan"
    )
    feats = relationship(
        "Feat", back_populates="content_pack", cascade="all, delete-orphan"
    )
    features = relationship(
        "Feature", back_populates="content_pack", cascade="all, delete-orphan"
    )
    languages = relationship(
        "Language", back_populates="content_pack", cascade="all, delete-orphan"
    )
    levels = relationship(
        "Level", back_populates="content_pack", cascade="all, delete-orphan"
    )
    magic_items = relationship(
        "MagicItem", back_populates="content_pack", cascade="all, delete-orphan"
    )
    magic_schools = relationship(
        "MagicSchool", back_populates="content_pack", cascade="all, delete-orphan"
    )
    monsters = relationship(
        "Monster", back_populates="content_pack", cascade="all, delete-orphan"
    )
    proficiencies = relationship(
        "Proficiency", back_populates="content_pack", cascade="all, delete-orphan"
    )
    races = relationship(
        "Race", back_populates="content_pack", cascade="all, delete-orphan"
    )
    rules = relationship(
        "Rule", back_populates="content_pack", cascade="all, delete-orphan"
    )
    rule_sections = relationship(
        "RuleSection", back_populates="content_pack", cascade="all, delete-orphan"
    )
    skills = relationship(
        "Skill", back_populates="content_pack", cascade="all, delete-orphan"
    )
    spells = relationship(
        "Spell", back_populates="content_pack", cascade="all, delete-orphan"
    )
    subclasses = relationship(
        "Subclass", back_populates="content_pack", cascade="all, delete-orphan"
    )
    subraces = relationship(
        "Subrace", back_populates="content_pack", cascade="all, delete-orphan"
    )
    traits = relationship(
        "Trait", back_populates="content_pack", cascade="all, delete-orphan"
    )
    weapon_properties = relationship(
        "WeaponProperty", back_populates="content_pack", cascade="all, delete-orphan"
    )


class BaseContent(Base):
    """Abstract base class for all D&D content entities."""

    __abstract__ = True

    index = Column(String(100), primary_key=True)
    name = Column(String(200), nullable=False)
    url = Column(String(200), nullable=False)
    content_pack_id = Column(String(50), ForeignKey("content_packs.id"), nullable=False)

    # Vector embedding for RAG search (384 dimensions for all-MiniLM-L6-v2)
    embedding: Mapped[OptionalVector] = mapped_column(VECTOR(384), nullable=True)


class AbilityScore(BaseContent):
    """Represents an ability score (STR, DEX, etc.)."""

    __tablename__ = "ability_scores"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    full_name = Column(String(20))
    desc = Column(JSON)  # List of strings
    skills = Column(JSON)  # List of APIReference

    content_pack = relationship("ContentPack", back_populates="ability_scores")


class Alignment(BaseContent):
    """Represents a character alignment."""

    __tablename__ = "alignments"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    desc = Column(Text)
    abbreviation = Column(String(2))

    content_pack = relationship("ContentPack", back_populates="alignments")


class Background(BaseContent):
    """Represents a character background."""

    __tablename__ = "backgrounds"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    starting_proficiencies = Column(JSON)  # List of APIReference
    starting_equipment = Column(JSON)  # List of APIReference
    starting_equipment_options = Column(JSON)  # List of choice objects
    language_options = Column(JSON)  # Choice object
    feature = Column(JSON)  # Feature object
    personality_traits = Column(JSON)  # Choice object
    ideals = Column(JSON)  # Choice object
    bonds = Column(JSON)  # Choice object
    flaws = Column(JSON)  # Choice object

    content_pack = relationship("ContentPack", back_populates="backgrounds")


class CharacterClass(BaseContent):
    """Represents a character class."""

    __tablename__ = "classes"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    hit_die = Column(Integer, nullable=False)
    proficiencies = Column(JSON)  # List of APIReference
    proficiency_choices = Column(JSON)  # List of choice objects
    saving_throws = Column(JSON)  # List of APIReference
    starting_equipment = Column(JSON)  # List of APIReference
    starting_equipment_options = Column(JSON)  # List of choice objects
    class_levels = Column(String(200))  # URL to levels endpoint
    multi_classing = Column(JSON)  # Multi-classing object
    subclasses = Column(JSON)  # List of APIReference
    spellcasting = Column(JSON)  # Spellcasting object
    spells = Column(String(200))  # URL to spells endpoint

    content_pack = relationship("ContentPack", back_populates="classes")


class Condition(BaseContent):
    """Represents a condition (poisoned, stunned, etc.)."""

    __tablename__ = "conditions"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    desc = Column(JSON)  # List of strings

    content_pack = relationship("ContentPack", back_populates="conditions")


class DamageType(BaseContent):
    """Represents a damage type."""

    __tablename__ = "damage_types"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    desc = Column(JSON)  # List of strings

    content_pack = relationship("ContentPack", back_populates="damage_types")


class Equipment(BaseContent):
    """Represents equipment items."""

    __tablename__ = "equipment"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    equipment_category = Column(JSON)  # APIReference
    weapon_category = Column(String(50))
    weapon_range = Column(String(20))
    category_range = Column(String(100))
    cost = Column(JSON)  # Cost object
    damage = Column(JSON)  # Damage object
    range = Column(JSON)  # Range object
    weight = Column(Numeric(10, 2))
    properties = Column(JSON)  # List of APIReference
    armor_category = Column(String(50))
    armor_class = Column(JSON)  # ArmorClass object
    str_minimum = Column(Integer)
    stealth_disadvantage = Column(Boolean)
    tool_category = Column(String(50))
    vehicle_category = Column(String(50))
    speed = Column(JSON)  # Speed object
    capacity = Column(String(50))
    gear_category = Column(JSON)  # APIReference
    quantity = Column(Integer)
    desc = Column(JSON)  # List of strings

    content_pack = relationship("ContentPack", back_populates="equipment")


class EquipmentCategory(BaseContent):
    """Represents an equipment category."""

    __tablename__ = "equipment_categories"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    equipment = Column(JSON)  # List of APIReference

    content_pack = relationship("ContentPack", back_populates="equipment_categories")


class Feat(BaseContent):
    """Represents a feat."""

    __tablename__ = "feats"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    desc = Column(JSON)  # List of strings
    prerequisites = Column(JSON)  # List of prerequisites

    content_pack = relationship("ContentPack", back_populates="feats")


class Feature(BaseContent):
    """Represents a class or race feature."""

    __tablename__ = "features"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    level = Column(Integer)
    class_ref = Column(JSON)  # APIReference to class
    subclass = Column(JSON)  # APIReference to subclass
    desc = Column(JSON)  # List of strings
    parent = Column(JSON)  # APIReference to parent feature
    prerequisites = Column(JSON)  # List of prerequisites
    feature_specific = Column(JSON)  # Feature-specific data

    content_pack = relationship("ContentPack", back_populates="features")


class Language(BaseContent):
    """Represents a language."""

    __tablename__ = "languages"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    type = Column(String(20))
    typical_speakers = Column(JSON)  # List of strings
    script = Column(String(50))
    desc = Column(Text)

    content_pack = relationship("ContentPack", back_populates="languages")


class Level(BaseContent):
    """Represents a class level."""

    __tablename__ = "levels"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    level = Column(Integer, nullable=False)
    class_ref = Column(JSON)  # APIReference to class
    subclass = Column(JSON)  # APIReference to subclass
    ability_score_bonuses = Column(Integer)
    prof_bonus = Column(Integer)
    features = Column(JSON)  # List of APIReference
    spellcasting = Column(JSON)  # Spellcasting details
    class_specific = Column(JSON)  # Class-specific features

    content_pack = relationship("ContentPack", back_populates="levels")


class MagicItem(BaseContent):
    """Represents a magic item."""

    __tablename__ = "magic_items"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    equipment_category = Column(JSON)  # APIReference
    desc = Column(JSON)  # List of strings
    rarity = Column(JSON)  # Rarity object
    variants = Column(JSON)  # List of APIReference
    variant = Column(Boolean)

    content_pack = relationship("ContentPack", back_populates="magic_items")


class MagicSchool(BaseContent):
    """Represents a school of magic."""

    __tablename__ = "magic_schools"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    desc = Column(Text)

    content_pack = relationship("ContentPack", back_populates="magic_schools")


class Monster(BaseContent):
    """Represents a monster or NPC."""

    __tablename__ = "monsters"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    size = Column(String(20), nullable=False)
    type = Column(String(50), nullable=False)
    subtype = Column(String(50))
    alignment = Column(String(50))
    armor_class = Column(JSON)  # List of AC objects
    hit_points = Column(Integer, nullable=False)
    hit_dice = Column(String(20))
    hit_points_roll = Column(String(50))
    speed = Column(JSON)  # Speed object

    # Ability scores
    strength = Column(Integer, nullable=False)
    dexterity = Column(Integer, nullable=False)
    constitution = Column(Integer, nullable=False)
    intelligence = Column(Integer, nullable=False)
    wisdom = Column(Integer, nullable=False)
    charisma = Column(Integer, nullable=False)

    proficiencies = Column(JSON)  # List of proficiency objects
    damage_vulnerabilities = Column(JSON)  # List of strings
    damage_resistances = Column(JSON)  # List of strings
    damage_immunities = Column(JSON)  # List of strings
    condition_immunities = Column(JSON)  # List of APIReference
    senses = Column(JSON)  # Senses object
    languages = Column(Text)
    challenge_rating = Column(Numeric(5, 2), nullable=False)
    proficiency_bonus = Column(Integer)
    xp = Column(Integer, nullable=False)

    # Actions and abilities
    special_abilities = Column(JSON)  # List of special ability objects
    actions = Column(JSON)  # List of action objects
    legendary_actions = Column(JSON)  # List of legendary action objects
    reactions = Column(JSON)  # List of reaction objects

    content_pack = relationship("ContentPack", back_populates="monsters")


class Proficiency(BaseContent):
    """Represents a proficiency."""

    __tablename__ = "proficiencies"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    type = Column(String(50))
    classes = Column(JSON)  # List of APIReference
    races = Column(JSON)  # List of APIReference
    references = Column(JSON)  # List of APIReference

    content_pack = relationship("ContentPack", back_populates="proficiencies")


class Race(BaseContent):
    """Represents a character race."""

    __tablename__ = "races"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    speed = Column(Integer)
    ability_bonuses = Column(JSON)  # List of ability bonus objects
    ability_bonus_options = Column(JSON)  # Choice object
    alignment = Column(Text)
    age = Column(Text)
    size = Column(String(20))
    size_description = Column(Text)
    starting_proficiencies = Column(JSON)  # List of APIReference
    starting_proficiency_options = Column(JSON)  # Choice object
    languages = Column(JSON)  # List of APIReference
    language_options = Column(JSON)  # Choice object
    language_desc = Column(Text)
    traits = Column(JSON)  # List of APIReference
    subraces = Column(JSON)  # List of APIReference

    content_pack = relationship("ContentPack", back_populates="races")


class Rule(BaseContent):
    """Represents a game rule."""

    __tablename__ = "rules"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    desc = Column(Text)
    subsections = Column(JSON)  # List of APIReference

    content_pack = relationship("ContentPack", back_populates="rules")


class RuleSection(BaseContent):
    """Represents a section of rules."""

    __tablename__ = "rule_sections"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    desc = Column(Text)

    content_pack = relationship("ContentPack", back_populates="rule_sections")


class Skill(BaseContent):
    """Represents a skill."""

    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    desc = Column(JSON)  # List of strings
    ability_score = Column(JSON)  # APIReference

    content_pack = relationship("ContentPack", back_populates="skills")


class Spell(BaseContent):
    """Represents a spell."""

    __tablename__ = "spells"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    desc = Column(JSON)  # List of strings
    higher_level = Column(JSON)  # List of strings
    range = Column(String(50))
    components = Column(JSON)  # List of components (V, S, M)
    material = Column(Text)
    ritual = Column(Boolean, default=False)
    duration = Column(String(100))
    concentration = Column(Boolean, default=False)
    casting_time = Column(String(100))
    level = Column(Integer, nullable=False)
    attack_type = Column(String(20))
    damage = Column(JSON)  # Damage object
    school = Column(JSON)  # APIReference
    classes = Column(JSON)  # List of APIReference
    subclasses = Column(JSON)  # List of APIReference
    dc = Column(JSON)  # DC object
    area_of_effect = Column(JSON)  # Area of effect object

    content_pack = relationship("ContentPack", back_populates="spells")


class Subclass(BaseContent):
    """Represents a character subclass."""

    __tablename__ = "subclasses"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    class_ref = Column(JSON)  # APIReference to parent class
    subclass_flavor = Column(Text)
    desc = Column(JSON)  # List of strings
    subclass_levels = Column(String(200))  # URL to levels endpoint
    spells = Column(JSON)  # List of spell objects

    content_pack = relationship("ContentPack", back_populates="subclasses")


class Subrace(BaseContent):
    """Represents a character subrace."""

    __tablename__ = "subraces"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    race = Column(JSON)  # APIReference to parent race
    desc = Column(Text)
    ability_bonuses = Column(JSON)  # List of ability bonus objects
    starting_proficiencies = Column(JSON)  # List of APIReference
    languages = Column(JSON)  # List of APIReference
    language_options = Column(JSON)  # Choice object
    racial_traits = Column(JSON)  # List of APIReference

    content_pack = relationship("ContentPack", back_populates="subraces")


class Trait(BaseContent):
    """Represents a racial trait."""

    __tablename__ = "traits"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    races = Column(JSON)  # List of APIReference
    subraces = Column(JSON)  # List of APIReference
    desc = Column(JSON)  # List of strings
    proficiencies = Column(JSON)  # List of APIReference
    proficiency_choices = Column(JSON)  # Choice object
    language_options = Column(JSON)  # Choice object
    trait_specific = Column(JSON)  # Trait-specific data

    content_pack = relationship("ContentPack", back_populates="traits")


class WeaponProperty(BaseContent):
    """Represents a weapon property."""

    __tablename__ = "weapon_properties"
    __table_args__ = (UniqueConstraint("index", "content_pack_id"),)

    desc = Column(JSON)  # List of strings

    content_pack = relationship("ContentPack", back_populates="weapon_properties")


class MigrationHistory(Base):
    """Tracks migration history for idempotency and rollback support."""

    __tablename__ = "migration_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    migration_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    content_pack_id: Mapped[str] = mapped_column(String(100), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    items_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # pending, completed, failed, rolled_back
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    backup_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
