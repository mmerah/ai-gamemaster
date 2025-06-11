"""D&D 5e repository implementations.

This package contains repositories for accessing D&D 5e data from the 5e-database.
Each repository provides type-safe access to specific data categories.
"""

from app.repositories.d5e.base_repository import BaseD5eRepository
from app.repositories.d5e.class_repository import ClassRepository
from app.repositories.d5e.equipment_repository import EquipmentRepository
from app.repositories.d5e.monster_repository import MonsterRepository
from app.repositories.d5e.repository_factory import D5eRepositoryFactory
from app.repositories.d5e.repository_hub import D5eRepositoryHub
from app.repositories.d5e.spell_repository import SpellRepository

__all__ = [
    "BaseD5eRepository",
    "ClassRepository",
    "D5eRepositoryFactory",
    "D5eRepositoryHub",
    "EquipmentRepository",
    "MonsterRepository",
    "SpellRepository",
]
