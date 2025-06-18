#!/usr/bin/env python3
"""
Generate TypeScript interfaces from Pydantic models.
This creates a single source of truth for data structures across the application.
"""

import inspect
import os
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin

from pydantic import BaseModel

# Handle Literal import for different Python versions
try:
    from typing import Literal
except ImportError:
    pass

# Add project root to Python path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

# Import types
from typing import Set, Tuple


class PydanticToTypeScript:
    """Convert Pydantic models to TypeScript interfaces."""

    def __init__(self) -> None:
        self.generated_models: Set[str] = set()
        self.model_dependencies: Dict[str, Set[str]] = {}

    def python_type_to_typescript(self, py_type: Any) -> str:
        """Convert a Python type annotation to TypeScript type."""
        # Handle None type
        if py_type is type(None):
            return "null"

        # Get origin for generic types
        origin = get_origin(py_type)

        # Handle Optional types
        if origin is Union:
            args = get_args(py_type)
            # Check if it's Optional (Union with None)
            if type(None) in args:
                non_none_args = [arg for arg in args if arg is not type(None)]
                if len(non_none_args) == 1:
                    return self.python_type_to_typescript(non_none_args[0])
                else:
                    # Handle Union types
                    return " | ".join(
                        self.python_type_to_typescript(arg) for arg in non_none_args
                    )
            else:
                # Regular Union
                return " | ".join(self.python_type_to_typescript(arg) for arg in args)

        # Handle List types
        if origin is list:
            args = get_args(py_type)
            if args:
                inner_type = self.python_type_to_typescript(args[0])
                return f"{inner_type}[]"
            return "any[]"

        # Handle Dict types
        if origin is dict:
            args = get_args(py_type)
            if args and len(args) == 2:
                key_type = self.python_type_to_typescript(args[0])
                value_type = self.python_type_to_typescript(args[1])
                # TypeScript Record type for string keys
                if key_type == "string":
                    return f"Record<string, {value_type}>"
                else:
                    return f"{{ [key: {key_type}]: {value_type} }}"
            return "Record<string, any>"

        # Handle Literal types
        if (
            hasattr(py_type, "__class__")
            and py_type.__class__.__name__ == "_LiteralGenericAlias"
        ):
            args = get_args(py_type)
            literals = []
            for arg in args:
                if isinstance(arg, str):
                    literals.append(f'"{arg}"')
                else:
                    literals.append(str(arg))
            return " | ".join(literals)

        # Handle basic types
        if py_type is str:
            return "string"
        elif py_type is int:
            return "number"
        elif py_type is float:
            return "number"
        elif py_type is bool:
            return "boolean"
        elif py_type is datetime:
            return "string"  # ISO string format
        elif py_type is Any:
            return "any"

        # Handle Pydantic models
        if inspect.isclass(py_type) and issubclass(py_type, BaseModel):
            return py_type.__name__

        # Handle Enums
        if inspect.isclass(py_type) and issubclass(py_type, Enum):
            return py_type.__name__

        # Default case
        return "any"

    def get_field_info(
        self, model: Type[BaseModel]
    ) -> List[Tuple[str, Any, bool, bool]]:
        """Extract field information from a Pydantic model."""
        fields: List[Tuple[str, Any, bool, bool]] = []

        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation
            is_optional = False

            # Check if field is optional
            origin = get_origin(field_type)
            if origin is Union:
                args = get_args(field_type)
                if type(None) in args:
                    is_optional = True

            # Check if field has a default value
            has_default = (
                field_info.default is not None or field_info.default_factory is not None
            )

            fields.append((field_name, field_type, is_optional, has_default))

        return fields

    def generate_interface(self, model: Type[BaseModel], indent: int = 0) -> str:
        """Generate TypeScript interface from a Pydantic model."""
        indent_str = "  " * indent
        lines = []

        # Check for inheritance (but ignore internal base classes)
        base_classes = [
            base
            for base in model.__bases__
            if base != BaseModel
            and issubclass(base, BaseModel)
            and base.__name__ not in ["BaseModelWithDatetimeSerializer"]
        ]

        if base_classes:
            extends = " extends " + ", ".join(base.__name__ for base in base_classes)
        else:
            extends = ""

        lines.append(f"{indent_str}export interface {model.__name__}{extends} {{")

        # Generate fields
        fields = self.get_field_info(model)
        for field_name, field_type, is_optional, has_default in fields:
            ts_type = self.python_type_to_typescript(field_type)

            # Mark as optional if it's Optional type or has a default (but not if it has default_factory)
            optional_marker = "?" if is_optional and not has_default else ""

            lines.append(f"{indent_str}  {field_name}{optional_marker}: {ts_type};")

        lines.append(f"{indent_str}}}")

        return "\n".join(lines)

    def generate_enum(self, enum_class: Type[Enum]) -> str:
        """Generate TypeScript enum from Python enum."""
        lines = [f"export enum {enum_class.__name__} {{"]

        members = list(enum_class)
        for i, member in enumerate(members):
            if isinstance(member.value, str):
                line = f'  {member.name} = "{member.value}"'
            else:
                line = f"  {member.name} = {member.value}"

            # Add comma except for last item
            if i < len(members) - 1:
                line += ","
            lines.append(line)

        lines.append("}")
        return "\n".join(lines)

    def extract_dependencies(self, model: Type[BaseModel]) -> Set[Type[BaseModel]]:
        """Extract all model dependencies for proper ordering."""
        deps: Set[Type[BaseModel]] = set()

        for field_name, field_info in model.model_fields.items():
            field_type = field_info.annotation

            # Unwrap Optional, List, etc.
            origin = get_origin(field_type)
            if origin:
                args = get_args(field_type)
                for arg in args:
                    if inspect.isclass(arg) and issubclass(arg, BaseModel):
                        deps.add(arg)
            elif inspect.isclass(field_type) and issubclass(field_type, BaseModel):
                deps.add(field_type)

        # Check base classes
        for base in model.__bases__:
            if base != BaseModel and issubclass(base, BaseModel):
                deps.add(base)

        return deps

    def sort_models_by_dependencies(
        self, models: List[Type[BaseModel]]
    ) -> List[Type[BaseModel]]:
        """Sort models so dependencies come before dependents."""
        # Build dependency graph
        dep_graph = {}
        for model in models:
            dep_graph[model] = self.extract_dependencies(model)

        # Topological sort
        sorted_models = []
        visited = set()

        def visit(model: Type[BaseModel]) -> None:
            if model in visited:
                return
            visited.add(model)

            # Visit dependencies first
            for dep in dep_graph.get(model, set()):
                if dep in dep_graph:  # Only if it's in our list
                    visit(dep)

            sorted_models.append(model)

        for model in models:
            visit(model)

        return sorted_models

    def generate_file(
        self,
        models: List[Type[BaseModel]],
        enums: Optional[List[Type[Enum]]] = None,
        constants: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate complete TypeScript file with all models."""
        lines = [
            "// Generated TypeScript interfaces from Pydantic models",
            "// DO NOT EDIT - This file is auto-generated",
            f"// Generated at: {datetime.now().isoformat()}",
            "",
            "// ============================================",
            "// Table of Contents",
            "// ============================================",
            "// 1. Constants and Enums",
            "// 2. D&D 5e Content Base Types",
            "// 3. D&D 5e Content Models",
            "// 4. Runtime Models - Core Types",
            "// 5. Runtime Models - Character & Campaign",
            "// 6. Runtime Models - Combat",
            "// 7. Runtime Models - Game State",
            "// 8. Runtime Models - Events",
            "// 9. Runtime Models - Updates",
            "// ============================================",
            "",
        ]

        # Section 1: Constants and Enums
        lines.append("// ============================================")
        lines.append("// 1. Constants and Enums")
        lines.append("// ============================================")
        lines.append("")

        # Generate constants
        if constants:
            for const_name, const_value in constants.items():
                if isinstance(const_value, dict):
                    lines.append(f"export const {const_name} = {{")
                    for key, value in const_value.items():
                        lines.append(f'  {key.upper().replace("-", "_")}: "{value}",')
                    lines.append("} as const;")
                    lines.append("")

                    # Generate type union from const
                    type_name = const_name.replace("CONTENT_TYPES", "ContentType")
                    lines.append(
                        f"export type {type_name} = typeof {const_name}[keyof typeof {const_name}];"
                    )
                    lines.append("")

        # Generate enums
        if enums:
            for enum_class in enums:
                lines.append(self.generate_enum(enum_class))
                lines.append("")

        # Sort models by dependencies
        sorted_models = self.sort_models_by_dependencies(models)

        # Categorize models by their module/purpose
        model_categories: Dict[str, List[Type[BaseModel]]] = {
            "d5e_base": [],
            "d5e_content": [],
            "core_types": [],
            "character_campaign": [],
            "combat": [],
            "game_state": [],
            "events": [],
            "updates": [],
        }

        # Categorize each model
        for model in sorted_models:
            if model.__name__ in ["BaseModelWithDatetimeSerializer"]:
                continue

            model_name = model.__name__

            # D&D 5e base types
            if model_name in [
                "APIReference",
                "Choice",
                "DC",
                "Cost",
                "Damage",
                "DamageAtLevel",
                "Usage",
                "OptionSet",
            ]:
                model_categories["d5e_base"].append(model)
            # D&D 5e content models
            elif model_name.startswith("D5e") or model_name in [
                "MonsterSpeed",
                "MonsterArmorClass",
                "MonsterProficiency",
                "SpecialAbility",
                "MonsterAction",
                "EquipmentRange",
                "ArmorClass",
                "AbilityBonus",
                "StartingEquipment",
                "StartingEquipmentOption",
                "SpellcastingInfo",
                "Spellcasting",
                "MultiClassing",
                "MultiClassingPrereq",
                "Feature",
                "SpellSlotInfo",
                "Prerequisite",
            ]:
                model_categories["d5e_content"].append(model)
            # Core runtime types
            elif model_name in [
                "ItemModel",
                "NPCModel",
                "QuestModel",
                "LocationModel",
                "HouseRulesModel",
                "GoldRangeModel",
                "BaseStatsModel",
                "ProficienciesModel",
                "TraitModel",
                "ClassFeatureModel",
            ]:
                model_categories["core_types"].append(model)
            # Character and campaign models
            elif "Character" in model_name or "Campaign" in model_name:
                model_categories["character_campaign"].append(model)
            # Combat models
            elif "Combat" in model_name or model_name in [
                "AttackModel",
                "InitialCombatantData",
            ]:
                model_categories["combat"].append(model)
            # Game state models
            elif model_name in [
                "GameStateModel",
                "ChatMessageModel",
                "DiceRequestModel",
                "DiceRollResultModel",
            ]:
                model_categories["game_state"].append(model)
            # Event models
            elif "Event" in model_name or model_name in [
                "CharacterChangesModel",
                "ErrorContextModel",
            ]:
                model_categories["events"].append(model)
            # Update models
            elif "Update" in model_name:
                model_categories["updates"].append(model)
            else:
                # Default to core types for anything we missed
                model_categories["core_types"].append(model)

        # Generate sections
        sections = [
            ("2. D&D 5e Content Base Types", "d5e_base"),
            ("3. D&D 5e Content Models", "d5e_content"),
            ("4. Runtime Models - Core Types", "core_types"),
            ("5. Runtime Models - Character & Campaign", "character_campaign"),
            ("6. Runtime Models - Combat", "combat"),
            ("7. Runtime Models - Game State", "game_state"),
            ("8. Runtime Models - Events", "events"),
            ("9. Runtime Models - Updates", "updates"),
        ]

        for section_title, category_key in sections:
            if model_categories[category_key]:
                lines.append("")
                lines.append("// ============================================")
                lines.append(f"// {section_title}")
                lines.append("// ============================================")
                lines.append("")

                for model in model_categories[category_key]:
                    lines.append(self.generate_interface(model))
                    lines.append("")

        return "\n".join(lines)


def main() -> None:
    """Generate TypeScript interfaces from unified models."""
    # Import content type constants
    from app.content.content_types import CONTENT_TYPE_TO_MODEL

    # Import D&D 5e content models
    from app.content.schemas.base import (
        DC,
        APIReference,
        Choice,
        Cost,
        Damage,
        DamageAtLevel,
        OptionSet,
        Usage,
    )
    from app.content.schemas.character import (
        AbilityBonus,
        D5eBackground,
        D5eClass,
        D5eFeat,
        D5eRace,
        D5eSubclass,
        D5eSubrace,
        D5eTrait,
        Feature,
        MultiClassing,
        MultiClassingPrereq,
        Spellcasting,
        SpellcastingInfo,
        StartingEquipment,
        StartingEquipmentOption,
    )
    from app.content.schemas.equipment import (
        ArmorClass,
        D5eEquipment,
        D5eEquipmentCategory,
        D5eMagicItem,
        D5eMagicSchool,
        D5eWeaponProperty,
        EquipmentRange,
    )
    from app.content.schemas.mechanics import (
        D5eAbilityScore,
        D5eAlignment,
        D5eCondition,
        D5eDamageType,
        D5eLanguage,
        D5eProficiency,
        D5eRule,
        D5eRuleSection,
        D5eSkill,
    )
    from app.content.schemas.progression import (
        D5eFeature,
        D5eLevel,
        Prerequisite,
        SpellSlotInfo,
    )
    from app.content.schemas.spells_monsters import (
        D5eMonster,
        D5eSpell,
        MonsterAction,
        MonsterArmorClass,
        MonsterProficiency,
        MonsterSpeed,
        SpecialAbility,
    )
    from app.models.campaign import (
        CampaignInstanceModel,
        CampaignTemplateModel,
    )
    from app.models.character import (
        CharacterInstanceModel,
        CharacterTemplateModel,
        CombinedCharacterModel,
    )
    from app.models.combat import (
        AttackModel,
        CombatantModel,
        CombatStateModel,
        InitialCombatantData,
    )
    from app.models.dice import DiceRequestModel, DiceRollResultModel
    from app.models.events import (
        BackendProcessingEvent,
        BaseGameEvent,
        CharacterChangesModel,
        CombatantAddedEvent,
        CombatantHpChangedEvent,
        CombatantInitiativeSetEvent,
        CombatantRemovedEvent,
        CombatantStatusChangedEvent,
        CombatEndedEvent,
        CombatStartedEvent,
        ErrorContextModel,
        GameErrorEvent,
        GameStateSnapshotEvent,
        InitiativeOrderDeterminedEvent,
        ItemAddedEvent,
        LocationChangedEvent,
        MessageSupersededEvent,
        NarrativeAddedEvent,
        NpcDiceRollProcessedEvent,
        PartyMemberUpdatedEvent,
        PlayerDiceRequestAddedEvent,
        PlayerDiceRequestsClearedEvent,
        QuestUpdatedEvent,
        TurnAdvancedEvent,
    )
    from app.models.game_state import ChatMessageModel, GameStateModel
    from app.models.updates import (
        CombatantRemoveUpdateModel,
        CombatEndUpdateModel,
        CombatStartUpdateModel,
        ConditionAddUpdateModel,
        ConditionRemoveUpdateModel,
        GoldUpdateModel,
        HPChangeUpdateModel,
        InventoryAddUpdateModel,
        InventoryRemoveUpdateModel,
        LocationUpdateModel,
        QuestUpdateModel,
    )
    from app.models.utils import (
        BaseStatsModel,
        ClassFeatureModel,
        GoldRangeModel,
        HouseRulesModel,
        ItemModel,
        LocationModel,
        NPCModel,
        ProficienciesModel,
        QuestModel,
        TraitModel,
    )

    # Collect all models
    all_models: List[Type[BaseModel]] = [
        # Base types
        ItemModel,
        NPCModel,
        QuestModel,
        LocationModel,
        HouseRulesModel,
        GoldRangeModel,
        BaseStatsModel,
        ProficienciesModel,
        TraitModel,
        ClassFeatureModel,
        AttackModel,
        # Core game mechanics
        ChatMessageModel,
        DiceRequestModel,
        DiceRollResultModel,
        InitialCombatantData,
        LocationUpdateModel,
        HPChangeUpdateModel,
        ConditionAddUpdateModel,
        ConditionRemoveUpdateModel,
        InventoryAddUpdateModel,
        InventoryRemoveUpdateModel,
        GoldUpdateModel,
        QuestUpdateModel,
        CombatStartUpdateModel,
        CombatEndUpdateModel,
        CombatantRemoveUpdateModel,
        # Main models
        CharacterTemplateModel,
        CampaignTemplateModel,
        CharacterInstanceModel,
        CampaignInstanceModel,
        CombinedCharacterModel,
        # Combat models
        CombatantModel,
        CombatStateModel,
        GameStateModel,
        # Events
        CharacterChangesModel,
        ErrorContextModel,  # Event helper models
        BaseGameEvent,
        NarrativeAddedEvent,
        MessageSupersededEvent,
        CombatStartedEvent,
        CombatEndedEvent,
        TurnAdvancedEvent,
        CombatantHpChangedEvent,
        CombatantStatusChangedEvent,
        CombatantAddedEvent,
        CombatantRemovedEvent,
        CombatantInitiativeSetEvent,
        InitiativeOrderDeterminedEvent,
        PlayerDiceRequestAddedEvent,
        PlayerDiceRequestsClearedEvent,
        NpcDiceRollProcessedEvent,
        LocationChangedEvent,
        PartyMemberUpdatedEvent,
        BackendProcessingEvent,
        GameErrorEvent,
        GameStateSnapshotEvent,
        QuestUpdatedEvent,
        ItemAddedEvent,
        # D&D 5e Content Base Types
        APIReference,
        Choice,
        DC,
        Cost,
        Damage,
        DamageAtLevel,
        Usage,
        OptionSet,
        # D&D 5e Spell Types
        D5eSpell,
        # D&D 5e Monster Types
        MonsterSpeed,
        MonsterArmorClass,
        MonsterProficiency,
        SpecialAbility,
        MonsterAction,
        D5eMonster,
        # D&D 5e Equipment Types
        EquipmentRange,
        ArmorClass,
        D5eEquipment,
        # D&D 5e Character Types
        AbilityBonus,
        StartingEquipment,
        StartingEquipmentOption,
        SpellcastingInfo,
        Spellcasting,
        MultiClassing,
        MultiClassingPrereq,
        Feature,
        D5eClass,
        D5eSubclass,
        D5eRace,
        D5eSubrace,
        D5eBackground,
        D5eFeat,
        D5eTrait,
        # D&D 5e Magic Item Types
        D5eMagicItem,
        D5eMagicSchool,
        D5eWeaponProperty,
        D5eEquipmentCategory,
        # D&D 5e Progression Types
        SpellSlotInfo,
        Prerequisite,
        D5eFeature,
        D5eLevel,
        # D&D 5e Rules Types
        D5eCondition,
        D5eDamageType,
        D5eLanguage,
        D5eProficiency,
        D5eSkill,
        D5eAbilityScore,
        D5eAlignment,
        D5eRule,
        D5eRuleSection,
    ]

    # Prepare constants
    constants = {"CONTENT_TYPES": {key: key for key in CONTENT_TYPE_TO_MODEL.keys()}}

    # Generate TypeScript
    generator = PydanticToTypeScript()
    ts_content = generator.generate_file(all_models, enums=None, constants=constants)

    # Write to file
    output_path = Path("frontend/src/types/unified.ts")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(ts_content)

    print(f"Generated TypeScript interfaces at: {output_path}")
    print(f"Total models generated: {len(all_models)}")
    print(f"Total content types: {len(CONTENT_TYPE_TO_MODEL)}")


if __name__ == "__main__":
    main()
