"""Pydantic models for product input and output."""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from src.core.constants import NutritionLabelType
from src.utils.validators import (
    sanitize_text,
    validate_alcohol_content,
    validate_product_id,
    validate_product_name,
    validate_upc,
)


class ProductInput(BaseModel):
    """Input schema for product classification request."""

    product_id: str = Field(
        ...,
        description="Unique identifier (UPC, SKU, or internal ID)",
        examples=["SKU-12345"],
    )
    product_name: str = Field(
        ...,
        description="Human-readable product name",
        examples=["Monster Energy Drink Original"],
    )
    description: Optional[str] = Field(
        default=None,
        description="Product description",
        examples=["Energy drink with caffeine and B vitamins"],
    )
    category: Optional[str] = Field(
        default=None,
        description="Product category",
        examples=["Beverages", "Snacks", "Produce"],
    )
    brand: Optional[str] = Field(
        default=None,
        description="Brand name",
        examples=["Monster"],
    )
    upc: Optional[str] = Field(
        default=None,
        description="Universal Product Code",
        examples=["070847811169"],
    )
    ingredients: Optional[list[str]] = Field(
        default=None,
        description="List of ingredients",
        examples=[["carbonated water", "sugar", "glucose", "citric acid"]],
    )
    nutrition_label_type: Optional[Literal["nutrition_facts", "supplement_facts", "none"]] = Field(
        default=None,
        description="Type of nutrition label on the product",
    )
    is_hot_at_sale: Optional[bool] = Field(
        default=None,
        description="Is product hot at point of sale",
    )
    is_for_onsite_consumption: Optional[bool] = Field(
        default=None,
        description="Intended for on-premises consumption",
    )
    alcohol_content: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Alcohol by volume (0.0 - 1.0)",
        examples=[0.0, 0.05, 0.13],
    )
    contains_tobacco: Optional[bool] = Field(
        default=None,
        description="Contains tobacco/nicotine",
    )
    contains_cbd_cannabis: Optional[bool] = Field(
        default=None,
        description="Contains CBD or cannabis",
    )
    is_live_animal: Optional[bool] = Field(
        default=None,
        description="Is a live animal",
    )
    additional_attributes: Optional[dict[str, Any]] = Field(
        default=None,
        description="Extensible attributes",
    )

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, v: str) -> str:
        return validate_product_id(v)

    @field_validator("product_name")
    @classmethod
    def validate_product_name(cls, v: str) -> str:
        return validate_product_name(v)

    @field_validator("upc")
    @classmethod
    def validate_upc(cls, v: Optional[str]) -> Optional[str]:
        return validate_upc(v)

    @field_validator("alcohol_content")
    @classmethod
    def validate_alcohol(cls, v: Optional[float]) -> Optional[float]:
        return validate_alcohol_content(v)

    @field_validator("description", "category", "brand")
    @classmethod
    def sanitize_strings(cls, v: Optional[str]) -> Optional[str]:
        return sanitize_text(v)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "product_id": "SKU-12345",
                    "product_name": "Monster Energy Drink Original",
                    "description": "Energy drink with caffeine and B vitamins",
                    "category": "Beverages",
                    "brand": "Monster",
                    "upc": "070847811169",
                    "ingredients": ["carbonated water", "sugar", "glucose"],
                    "nutrition_label_type": "nutrition_facts",
                    "is_hot_at_sale": False,
                    "alcohol_content": 0.0,
                    "contains_tobacco": False,
                    "contains_cbd_cannabis": False,
                }
            ]
        }
    }


class BulkClassifyOptions(BaseModel):
    """Options for bulk classification requests."""

    parallel_processing: bool = Field(
        default=True,
        description="Process products in parallel",
    )
    max_concurrent: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent classifications",
    )
    fail_fast: bool = Field(
        default=False,
        description="Stop on first error if True",
    )


class BulkClassifyRequest(BaseModel):
    """Request schema for bulk classification."""

    products: list[ProductInput] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of products to classify",
    )
    options: Optional[BulkClassifyOptions] = Field(
        default=None,
        description="Bulk processing options",
    )
