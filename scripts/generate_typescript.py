#!/usr/bin/env python3
"""
Generate TypeScript interfaces from Pydantic models.
This creates a single source of truth for data structures across the application.
"""

import sys
import os
from pathlib import Path
from typing import Type, List, Dict, Any, Optional, get_origin, get_args, Union
from datetime import datetime
from enum import Enum
import inspect
from pydantic import BaseModel
from pydantic.fields import FieldInfo

# Handle Literal import for different Python versions
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PydanticToTypeScript:
    """Convert Pydantic models to TypeScript interfaces."""
    
    def __init__(self):
        self.generated_models: set = set()
        self.model_dependencies: Dict[str, set] = {}
    
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
                    return " | ".join(self.python_type_to_typescript(arg) for arg in non_none_args)
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
        try:
            from typing import Literal as LiteralType
        except ImportError:
            from typing_extensions import Literal as LiteralType
            
        if origin is LiteralType or (hasattr(py_type, "__class__") and py_type.__class__.__name__ == "_LiteralGenericAlias"):
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
    
    def get_field_info(self, model: Type[BaseModel]) -> List[tuple]:
        """Extract field information from a Pydantic model."""
        fields = []
        
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
            has_default = field_info.default is not None or field_info.default_factory is not None
            
            fields.append((field_name, field_type, is_optional, has_default))
        
        return fields
    
    def generate_interface(self, model: Type[BaseModel], indent: int = 0) -> str:
        """Generate TypeScript interface from a Pydantic model."""
        indent_str = "  " * indent
        lines = []
        
        # Check for inheritance (but ignore internal base classes)
        base_classes = [
            base for base in model.__bases__ 
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
                line = f'  {member.name} = {member.value}'
            
            # Add comma except for last item
            if i < len(members) - 1:
                line += ","
            lines.append(line)
        
        lines.append("}")
        return "\n".join(lines)
    
    def extract_dependencies(self, model: Type[BaseModel]) -> set:
        """Extract all model dependencies for proper ordering."""
        deps = set()
        
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
    
    def sort_models_by_dependencies(self, models: List[Type[BaseModel]]) -> List[Type[BaseModel]]:
        """Sort models so dependencies come before dependents."""
        # Build dependency graph
        dep_graph = {}
        for model in models:
            dep_graph[model] = self.extract_dependencies(model)
        
        # Topological sort
        sorted_models = []
        visited = set()
        
        def visit(model):
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
    
    def generate_file(self, models: List[Type[BaseModel]], 
                     enums: Optional[List[Type[Enum]]] = None) -> str:
        """Generate complete TypeScript file with all models."""
        lines = [
            "// Generated TypeScript interfaces from Pydantic models",
            "// DO NOT EDIT - This file is auto-generated",
            f"// Generated at: {datetime.now().isoformat()}",
            "",
        ]
        
        # Generate enums first
        if enums:
            for enum_class in enums:
                lines.append(self.generate_enum(enum_class))
                lines.append("")
        
        # Sort models by dependencies
        sorted_models = self.sort_models_by_dependencies(models)
        
        # Generate interfaces (skip internal base classes)
        for model in sorted_models:
            if model.__name__ not in ["BaseModelWithDatetimeSerializer"]:
                lines.append(self.generate_interface(model))
                lines.append("")
        
        # No need to import Literal in TypeScript - it's built-in
        # Remove the import line if it was added
        
        return "\n".join(lines)


def main():
    """Generate TypeScript interfaces from unified models."""
    from app.game.unified_models import (
        # Base types
        ItemModel, NPCModel, QuestModel, LocationModel, HouseRulesModel,
        GoldRangeModel, BaseStatsModel, ProficienciesModel, TraitModel,
        ClassFeatureModel,
        
        # Main models
        CharacterTemplateModel, CampaignTemplateModel,
        CharacterInstanceModel, CampaignInstanceModel,
        CombinedCharacterModel,
        
        # Combat models
        CombatantModel, CombatStateModel, GameStateModel,
        
        # Events
        BaseGameEvent, NarrativeAddedEvent, MessageSupersededEvent,
        CombatStartedEvent, CombatEndedEvent, TurnAdvancedEvent,
        CombatantHpChangedEvent, CombatantStatusChangedEvent,
        CombatantAddedEvent, CombatantRemovedEvent,
        CombatantInitiativeSetEvent, InitiativeOrderDeterminedEvent,
        PlayerDiceRequestAddedEvent, PlayerDiceRequestsClearedEvent,
        NpcDiceRollProcessedEvent, LocationChangedEvent,
        PartyMemberUpdatedEvent, BackendProcessingEvent, GameErrorEvent,
        GameStateSnapshotEvent, QuestUpdatedEvent, ItemAddedEvent,
        
        # Core game mechanics (moved from ai_services/schemas.py)
        DiceRequest, DiceRollResult, MonsterBaseStats, InitialCombatantData,
        LocationUpdate, HPChangeUpdate, ConditionUpdate, InventoryUpdate,
        GoldUpdate, QuestUpdate, CombatStartUpdate, CombatEndUpdate,
        CombatantRemoveUpdate, GameStateUpdate, ChatMessage,
        
        # Repository metadata models
        CampaignTemplateMetadata
    )
    
    # Collect all models
    all_models = [
        # Base types
        ItemModel, NPCModel, QuestModel, LocationModel, HouseRulesModel,
        GoldRangeModel, BaseStatsModel, ProficienciesModel, TraitModel,
        ClassFeatureModel,
        
        # Core game mechanics
        ChatMessage, DiceRequest, DiceRollResult, MonsterBaseStats, InitialCombatantData,
        LocationUpdate, HPChangeUpdate, ConditionUpdate, InventoryUpdate,
        GoldUpdate, QuestUpdate, CombatStartUpdate, CombatEndUpdate,
        CombatantRemoveUpdate,
        
        # Main models
        CharacterTemplateModel, CampaignTemplateModel,
        CharacterInstanceModel, CampaignInstanceModel,
        CombinedCharacterModel,
        
        # Combat models
        CombatantModel, CombatStateModel, GameStateModel,
        
        # Events
        BaseGameEvent, NarrativeAddedEvent, MessageSupersededEvent,
        CombatStartedEvent, CombatEndedEvent, TurnAdvancedEvent,
        CombatantHpChangedEvent, CombatantStatusChangedEvent,
        CombatantAddedEvent, CombatantRemovedEvent,
        CombatantInitiativeSetEvent, InitiativeOrderDeterminedEvent,
        PlayerDiceRequestAddedEvent, PlayerDiceRequestsClearedEvent,
        NpcDiceRollProcessedEvent, LocationChangedEvent,
        PartyMemberUpdatedEvent, BackendProcessingEvent, GameErrorEvent,
        GameStateSnapshotEvent, QuestUpdatedEvent, ItemAddedEvent,
        
        # Repository metadata models
        CampaignTemplateMetadata
    ]
    
    # Generate TypeScript
    generator = PydanticToTypeScript()
    ts_content = generator.generate_file(all_models)
    
    # Write to file
    output_path = Path("frontend/src/types/unified.ts")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(ts_content)
    
    print(f"Generated TypeScript interfaces at: {output_path}")
    print(f"Total models generated: {len(all_models)}")


if __name__ == "__main__":
    main()