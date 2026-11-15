from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from app.shared.money import StrictPositiveCents

MAX_INT32 = 2_147_483_647


def _validate_stock_qty(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("stock_qty must be an exact integer (no floats or booleans).")
    if value < 0 or value > MAX_INT32:
        raise ValueError(f"stock_qty must be between 0 and {MAX_INT32}.")
    return value


StrictStockQty = Annotated[int, BeforeValidator(_validate_stock_qty)]


class ProductSKUCreateRequest(BaseModel):
    """Payload for creating a product SKU with exact int64 price_cents."""

    model_config = ConfigDict(extra="forbid")

    sku_code: str = Field(..., min_length=1, max_length=80)
    variant_name: str = Field(..., min_length=1, max_length=120)
    price_cents: StrictPositiveCents
    stock_qty: StrictStockQty = 0

    @field_validator("sku_code", "variant_name")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be blank")
        return cleaned


class ProductSKUUpdateRequest(BaseModel):
    """Payload for modifying an existing product SKU."""

    model_config = ConfigDict(extra="forbid")

    variant_name: str | None = Field(default=None, min_length=1, max_length=120)
    price_cents: StrictPositiveCents | None = None
    stock_qty: StrictStockQty | None = None
    is_active: bool | None = None

    @field_validator("variant_name")
    @classmethod
    def strip_optional_variant(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("variant_name cannot be blank")
        return cleaned


class ProductSKUResponse(BaseModel):
    """Serialized SKU response with exact integer price_cents."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    shop_id: int
    sku_code: str
    variant_name: str
    price_cents: int
    stock_qty: int
    is_active: bool


class ProductCreateRequest(BaseModel):
    """Payload for creating a catalog product with optional initial SKUs."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    category: str = Field(..., min_length=1, max_length=80)
    skus: list[ProductSKUCreateRequest] = Field(default_factory=list, max_length=20)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("title must contain at least 2 non-whitespace characters")
        return cleaned

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("category cannot be blank")
        return cleaned


class ProductUpdateRequest(BaseModel):
    """Payload for updating product metadata."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    is_active: bool | None = None

    @field_validator("title")
    @classmethod
    def clean_optional_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("title must contain at least 2 non-whitespace characters")
        return cleaned

    @field_validator("category")
    @classmethod
    def normalize_optional_category(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("category cannot be blank")
        return cleaned


class ProductResponse(BaseModel):
    """Serialized Product with nested variant SKUs."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    shop_id: int
    title: str
    description: str
    category: str
    is_active: bool
    skus: list[ProductSKUResponse] = Field(default_factory=list)
