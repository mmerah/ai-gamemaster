"""
Tests for TypeScript type generation from Pydantic models.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class TestTypeScriptGenerator:
    """Test TypeScript generation from Pydantic models."""

    def test_simple_model_generation(self) -> None:
        """Test generating TypeScript from a simple Pydantic model."""
        from scripts.generate_typescript import PydanticToTypeScript

        class SimpleModel(BaseModel):
            id: str
            name: str
            age: int
            is_active: bool

        generator = PydanticToTypeScript()  # type: ignore[no-untyped-call]
        ts_code = generator.generate_interface(SimpleModel)

        expected = """export interface SimpleModel {
  id: string;
  name: string;
  age: number;
  is_active: boolean;
}"""
        assert ts_code.strip() == expected.strip()

    def test_optional_fields(self) -> None:
        """Test handling of optional fields."""
        from scripts.generate_typescript import PydanticToTypeScript

        class ModelWithOptionals(BaseModel):
            required_field: str
            optional_field: Optional[str] = None
            optional_int: Optional[int] = None

        generator = PydanticToTypeScript()  # type: ignore[no-untyped-call]
        ts_code = generator.generate_interface(ModelWithOptionals)

        assert "required_field: string;" in ts_code
        assert "optional_field?: string;" in ts_code
        assert "optional_int?: number;" in ts_code

    def test_list_types(self) -> None:
        """Test handling of List types."""
        from scripts.generate_typescript import PydanticToTypeScript

        class ModelWithLists(BaseModel):
            tags: List[str]
            numbers: List[int]
            items: List[Dict[str, str]]

        generator = PydanticToTypeScript()  # type: ignore[no-untyped-call]
        ts_code = generator.generate_interface(ModelWithLists)

        assert "tags: string[];" in ts_code
        assert "numbers: number[];" in ts_code
        assert "items: Record<string, string>[];" in ts_code

    def test_dict_types(self) -> None:
        """Test handling of Dict types."""
        from scripts.generate_typescript import PydanticToTypeScript

        class ModelWithDicts(BaseModel):
            metadata: Dict[str, str]
            scores: Dict[str, int]
            complex: Dict[str, List[str]]

        generator = PydanticToTypeScript()  # type: ignore[no-untyped-call]
        ts_code = generator.generate_interface(ModelWithDicts)

        assert "metadata: Record<string, string>;" in ts_code
        assert "scores: Record<string, number>;" in ts_code
        assert "complex: Record<string, string[]>;" in ts_code

    def test_literal_types(self) -> None:
        """Test handling of Literal types."""
        from scripts.generate_typescript import PydanticToTypeScript

        class ModelWithLiterals(BaseModel):
            status: Literal["active", "inactive", "pending"]
            priority: Literal[1, 2, 3]
            event_type: Literal["click", "hover"]

        generator = PydanticToTypeScript()  # type: ignore[no-untyped-call]
        ts_code = generator.generate_interface(ModelWithLiterals)

        assert 'status: "active" | "inactive" | "pending";' in ts_code
        assert "priority: 1 | 2 | 3;" in ts_code
        assert 'event_type: "click" | "hover";' in ts_code

    def test_nested_models(self) -> None:
        """Test handling of nested Pydantic models."""
        from scripts.generate_typescript import PydanticToTypeScript

        class Address(BaseModel):
            street: str
            city: str
            country: str

        class Person(BaseModel):
            name: str
            address: Address
            alt_addresses: List[Address]

        generator = PydanticToTypeScript()  # type: ignore[no-untyped-call]

        # Generate both models
        address_ts = generator.generate_interface(Address)
        person_ts = generator.generate_interface(Person)

        assert "export interface Address" in address_ts
        assert "street: string;" in address_ts

        assert "address: Address;" in person_ts
        assert "alt_addresses: Address[];" in person_ts

    def test_datetime_handling(self) -> None:
        """Test handling of datetime fields."""
        from scripts.generate_typescript import PydanticToTypeScript

        class ModelWithDates(BaseModel):
            created_at: datetime
            updated_at: Optional[datetime] = None

        generator = PydanticToTypeScript()  # type: ignore[no-untyped-call]
        ts_code = generator.generate_interface(ModelWithDates)

        assert "created_at: string;" in ts_code  # ISO string
        assert "updated_at?: string;" in ts_code

    def test_field_with_defaults(self) -> None:
        """Test handling of fields with default values."""
        from scripts.generate_typescript import PydanticToTypeScript

        class ModelWithDefaults(BaseModel):
            name: str
            count: int = 0
            tags: List[str] = Field(default_factory=list)
            is_active: bool = True

        generator = PydanticToTypeScript()  # type: ignore[no-untyped-call]
        ts_code = generator.generate_interface(ModelWithDefaults)

        # All fields should be present (not optional) since they have defaults
        assert "name: string;" in ts_code
        assert "count: number;" in ts_code
        assert "tags: string[];" in ts_code
        assert "is_active: boolean;" in ts_code

    def test_enum_generation(self) -> None:
        """Test generation of TypeScript enums from Python enums."""
        from enum import Enum

        from scripts.generate_typescript import PydanticToTypeScript

        class Status(str, Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"
            PENDING = "pending"

        generator = PydanticToTypeScript()  # type: ignore[no-untyped-call]
        enum_ts = generator.generate_enum(Status)

        expected = """export enum Status {
  ACTIVE = "active",
  INACTIVE = "inactive",
  PENDING = "pending"
}"""
        assert enum_ts.strip() == expected.strip()

    def test_full_file_generation(self) -> None:
        """Test generating a complete TypeScript file with multiple models."""
        from scripts.generate_typescript import PydanticToTypeScript

        class BaseItem(BaseModel):
            id: str
            created_at: datetime

        class Product(BaseItem):
            name: str
            price: float
            tags: List[str]

        class Order(BaseItem):
            products: List[Product]
            total: float
            status: Literal["pending", "completed", "cancelled"]

        generator = PydanticToTypeScript()  # type: ignore[no-untyped-call]
        models: List[Any] = [BaseItem, Product, Order]

        ts_content = generator.generate_file(models)

        # Check file structure
        assert "// Generated TypeScript interfaces from Pydantic models" in ts_content
        assert "export interface BaseItem" in ts_content
        assert "export interface Product extends BaseItem" in ts_content
        assert "export interface Order extends BaseItem" in ts_content

        # Check inheritance is handled
        assert "extends BaseItem" in ts_content

    def test_unified_models_generation(self) -> None:
        """Test generating TypeScript from our actual unified models."""
        from app.models.events import NarrativeAddedEvent
        from app.models.models import CampaignTemplateModel, CharacterTemplateModel
        from scripts.generate_typescript import PydanticToTypeScript

        generator = PydanticToTypeScript()  # type: ignore[no-untyped-call]

        # Test character template
        char_ts = generator.generate_interface(CharacterTemplateModel)
        assert "export interface CharacterTemplateModel" in char_ts
        assert "base_stats: BaseStatsModel;" in char_ts
        assert "proficiencies: ProficienciesModel;" in char_ts
        assert "racial_traits: TraitModel[];" in char_ts

        # Test campaign template
        camp_ts = generator.generate_interface(CampaignTemplateModel)
        assert "export interface CampaignTemplateModel" in camp_ts
        assert "initial_npcs: Record<string, NPCModel>;" in camp_ts
        assert "house_rules: HouseRulesModel;" in camp_ts

        # Test events
        event_ts = generator.generate_interface(NarrativeAddedEvent)
        assert "export interface NarrativeAddedEvent extends BaseGameEvent" in event_ts
        assert 'event_type: "narrative_added";' in event_ts
