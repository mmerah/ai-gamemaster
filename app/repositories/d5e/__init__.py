"""D&D 5e repository implementations.

This package contains database-backed repositories for accessing D&D 5e data.
Each repository provides type-safe access to specific data categories using SQLAlchemy.
"""

from app.repositories.d5e.db_base_repository import (
    BaseD5eDbRepository as BaseD5eRepository,
)
from app.repositories.d5e.db_class_repository import (
    DbClassRepository as ClassRepository,
)
from app.repositories.d5e.db_equipment_repository import (
    DbEquipmentRepository as EquipmentRepository,
)
from app.repositories.d5e.db_monster_repository import (
    DbMonsterRepository as MonsterRepository,
)
from app.repositories.d5e.db_repository_factory import (
    D5eDbRepositoryFactory as D5eRepositoryFactory,
)
from app.repositories.d5e.db_repository_hub import (
    D5eDbRepositoryHub as D5eRepositoryHub,
)
from app.repositories.d5e.db_spell_repository import (
    DbSpellRepository as SpellRepository,
)

__all__ = [
    "BaseD5eRepository",
    "ClassRepository",
    "D5eRepositoryFactory",
    "D5eRepositoryHub",
    "EquipmentRepository",
    "MonsterRepository",
    "SpellRepository",
]
