from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.ai_client import SemanticSearchIntent
from app.shared.money import StrictPositiveCents


class AISearchRequest(BaseModel):
    """Natural-language product discovery request."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., min_length=1, max_length=1000)
    category: str | None = Field(default=None, max_length=80)
    max_price_cents: StrictPositiveCents | None = None
    limit: int = Field(default=10, ge=1, le=50)

    @field_validator("query")
    @classmethod
    def ensure_non_blank_query(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Search query cannot be blank")
        return cleaned

    @field_validator("category")
    @classmethod
    def normalize_category(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        return cleaned or None


class AISearchResultItem(BaseModel):
    """Ranked search hit with exact integer min_price_cents."""

    model_config = ConfigDict(frozen=True)

    product_id: int
    shop_id: int
    title: str
    description: str
    category: str
    min_price_cents: int
    sku_count: int
    total_stock_qty: int
    relevance_score: int


class AISearchResponse(BaseModel):
    """Structured semantic search response with extracted intent and ranked hits."""

    model_config = ConfigDict(frozen=True)

    query: str
    provider: str
    intent: SemanticSearchIntent
    results: list[AISearchResultItem]
