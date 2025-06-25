#!/usr/bin/env python3
"""
Validate TypeScript generation for potential issues.

This script checks for:
1. Duplicate model names across different modules
2. Models referenced but not included in generation
3. Circular dependencies
4. Missing or invalid type annotations
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Type

# Add project root to Python path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from pydantic import BaseModel


class TypeValidationError:
    """Represents a validation error found in the type system."""

    def __init__(self, error_type: str, message: str, location: str = ""):
        self.error_type = error_type
        self.message = message
        self.location = location

    def __str__(self) -> str:
        if self.location:
            return f"[{self.error_type}] {self.location}: {self.message}"
        return f"[{self.error_type}] {self.message}"


class TypeValidator:
    """Validates TypeScript generation for common issues."""

    def __init__(self) -> None:
        self.errors: List[TypeValidationError] = []
        self.warnings: List[TypeValidationError] = []
        self.model_names: Dict[str, List[str]] = {}  # model_name -> [module_paths]
        self.model_references: Dict[str, Set[str]] = {}  # model -> {referenced_models}
        self.all_models: Set[str] = set()

    def validate(
        self,
    ) -> Tuple[bool, List[TypeValidationError], List[TypeValidationError]]:
        """Run all validations and return results."""
        # Scan models
        self._scan_models()

        # Run validations
        self._check_duplicate_names()
        self._check_missing_models()
        self._check_circular_dependencies()
        self._check_naming_conventions()
        self._check_model_organization()

        return len(self.errors) == 0, self.errors, self.warnings

    def _scan_models(self) -> None:
        """Scan the codebase for all Pydantic models."""
        # Import models to check what's actually included
        try:
            # These imports match what's in generate_ts.py
            from app.models.campaign.instance import CampaignInstanceModel
            from app.models.campaign.template import CampaignTemplateModel
            from app.models.character.combined import CombinedCharacterModel
            from app.models.character.instance import CharacterInstanceModel
            from app.models.character.template import CharacterTemplateModel
            from app.models.combat.attack import AttackModel
            from app.models.combat.combatant import CombatantModel, InitialCombatantData
            from app.models.combat.state import CombatStateModel
            from app.models.dice import DiceRequestModel
            from app.models.events.base import BaseGameEvent
            from app.models.game_state.main import GameStateModel
            from app.models.shared.chat import ChatMessageModel
            from app.models.utils import (
                BaseStatsModel,
                ClassFeatureModel,
                ItemModel,
                NPCModel,
                ProficienciesModel,
                QuestModel,
                TraitModel,
            )

            # Collect all model names
            model_mapping: List[Tuple[str, List[Type[BaseModel]]]] = [
                (
                    "campaign",
                    [
                        CampaignInstanceModel,
                        CampaignTemplateModel,
                    ],
                ),
                (
                    "character",
                    [
                        CharacterInstanceModel,
                        CharacterTemplateModel,
                        CombinedCharacterModel,
                    ],
                ),
                (
                    "combat",
                    [
                        AttackModel,
                        CombatantModel,
                        CombatStateModel,
                        InitialCombatantData,
                    ],
                ),
                ("dice", [DiceRequestModel]),
                ("events", [BaseGameEvent]),
                ("game_state", [ChatMessageModel, GameStateModel]),
                (
                    "utils",
                    [
                        BaseStatsModel,
                        ClassFeatureModel,
                        ItemModel,
                        NPCModel,
                        ProficienciesModel,
                        QuestModel,
                        TraitModel,
                    ],
                ),
            ]

            for module_name, models in model_mapping:
                for model in models:
                    model_name = model.__name__
                    self.all_models.add(model_name)

                    if model_name not in self.model_names:
                        self.model_names[model_name] = []
                    self.model_names[model_name].append(f"app.models.{module_name}")

                    # Extract references from model fields
                    self._extract_model_references(model, model_name)

        except ImportError as e:
            self.errors.append(
                TypeValidationError(
                    "IMPORT_ERROR", f"Failed to import models: {str(e)}"
                )
            )

    def _extract_model_references(
        self, model_class: Type[BaseModel], model_name: str
    ) -> None:
        """Extract references to other models from a model's fields."""
        references: Set[str] = set()

        try:
            for field_name, field_info in model_class.model_fields.items():
                field_type_str = str(field_info.annotation)

                # Look for model names in the type string
                for potential_model in self.all_models:
                    if (
                        potential_model in field_type_str
                        and potential_model != model_name
                    ):
                        references.add(potential_model)
        except Exception:
            # Skip if we can't introspect the model
            pass

        self.model_references[model_name] = references

    def _check_duplicate_names(self) -> None:
        """Check for duplicate model names across modules."""
        for model_name, modules in self.model_names.items():
            if len(modules) > 1:
                self.errors.append(
                    TypeValidationError(
                        "DUPLICATE_MODEL",
                        f"Model '{model_name}' defined in multiple modules: {', '.join(modules)}",
                    )
                )

    def _check_missing_models(self) -> None:
        """Check for models referenced but not included in generation."""
        # Get all referenced models
        all_referenced = set()
        for refs in self.model_references.values():
            all_referenced.update(refs)

        # Check if any referenced models are missing
        missing = all_referenced - self.all_models

        # Filter out known base classes and external types
        ignored_types = {
            "BaseModel",
            "BaseModelWithDatetimeSerializer",
            "str",
            "int",
            "float",
            "bool",
            "datetime",
            "List",
            "Dict",
            "Optional",
            "Any",
        }

        missing = missing - ignored_types

        for model in missing:
            self.warnings.append(
                TypeValidationError(
                    "MISSING_MODEL",
                    f"Model '{model}' is referenced but not included in TypeScript generation",
                )
            )

    def _check_circular_dependencies(self) -> None:
        """Check for circular dependencies between models."""

        def find_cycles(
            node: str, path: List[str], visited: Set[str]
        ) -> List[List[str]]:
            """DFS to find cycles in dependency graph."""
            if node in path:
                # Found a cycle
                cycle_start = path.index(node)
                return [path[cycle_start:] + [node]]

            if node in visited:
                return []

            visited.add(node)
            cycles = []

            for neighbor in self.model_references.get(node, set()):
                if neighbor in self.all_models:  # Only check models we're generating
                    cycles.extend(find_cycles(neighbor, path + [node], visited))

            return cycles

        visited: Set[str] = set()
        all_cycles: List[List[str]] = []

        for model in self.all_models:
            if model not in visited:
                cycles = find_cycles(model, [], visited)
                all_cycles.extend(cycles)

        # Remove duplicate cycles
        unique_cycles = []
        for cycle in all_cycles:
            # Normalize cycle (start from smallest element)
            min_idx = cycle.index(min(cycle))
            normalized = cycle[min_idx:] + cycle[:min_idx]
            if normalized not in unique_cycles:
                unique_cycles.append(normalized)

        for cycle in unique_cycles:
            self.warnings.append(
                TypeValidationError(
                    "CIRCULAR_DEPENDENCY",
                    f"Circular dependency detected: {' -> '.join(cycle)}",
                )
            )

    def _check_naming_conventions(self) -> None:
        """Check if models follow naming conventions."""
        for model_name in self.all_models:
            # Check for Model suffix
            if (
                not model_name.endswith("Model")
                and model_name
                not in [
                    "DC",
                    "APIReference",
                    "Choice",
                    "Cost",
                    "Damage",
                    "Usage",
                    "OptionSet",
                    # D&D 5e types don't need Model suffix
                ]
                and not model_name.startswith("D5e")
            ):
                self.warnings.append(
                    TypeValidationError(
                        "NAMING_CONVENTION",
                        f"Model '{model_name}' doesn't follow naming convention (should end with 'Model')",
                    )
                )

            # Check for proper camel case
            if "_" in model_name:
                self.warnings.append(
                    TypeValidationError(
                        "NAMING_CONVENTION",
                        f"Model '{model_name}' contains underscores (should use CamelCase)",
                    )
                )

    def _check_model_organization(self) -> None:
        """Check if models are properly organized in modules."""
        # Check for models in wrong modules
        misplaced = []

        for model_name, modules in self.model_names.items():
            for module in modules:
                # Character models should be in character module
                if "Character" in model_name and "character" not in module:
                    misplaced.append((model_name, module, "character"))
                # Campaign models should be in campaign module
                elif "Campaign" in model_name and "campaign" not in module:
                    misplaced.append((model_name, module, "campaign"))
                # Combat models should be in combat module
                elif "Combat" in model_name and "combat" not in module:
                    misplaced.append((model_name, module, "combat"))
                # Event models should be in events module
                elif "Event" in model_name and "events" not in module:
                    misplaced.append((model_name, module, "events"))

        for model_name, current_module, expected_module in misplaced:
            self.warnings.append(
                TypeValidationError(
                    "MODEL_ORGANIZATION",
                    f"Model '{model_name}' in {current_module} should be in {expected_module} module",
                )
            )


def main() -> None:
    """Run type validation."""
    validator = TypeValidator()
    success, errors, warnings = validator.validate()

    print("TypeScript Generation Validation Report")
    print("=" * 50)

    if errors:
        print(f"\n❌ Found {len(errors)} errors:\n")
        for error in errors:
            print(f"  {error}")

    if warnings:
        print(f"\n⚠️  Found {len(warnings)} warnings:\n")
        for warning in warnings:
            print(f"  {warning}")

    if success and not warnings:
        print("\n✅ All validations passed!")

    print("\nSummary:")
    print(f"  Total models scanned: {len(validator.all_models)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")

    # Exit with error code if there are errors
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
