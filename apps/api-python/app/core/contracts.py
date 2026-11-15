from __future__ import annotations

from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session


class CatalogItemSummary(BaseModel):
    """Cross-module read projection of a catalog product used by ai_search."""

    model_config = ConfigDict(frozen=True)

    product_id: int = Field(..., ge=1)
    shop_id: int = Field(..., ge=1)
    title: str
    description: str
    category: str
    min_price_cents: int = Field(..., gt=0)
    sku_count: int = Field(..., ge=1)
    total_stock_qty: int = Field(..., ge=0)


ShopLookupFn = Callable[[Session, int], int | None]
CatalogSearchFn = Callable[[Session, str | None, int | None], list[CatalogItemSummary]]

_shop_lookup_provider: ShopLookupFn | None = None
_catalog_search_provider: CatalogSearchFn | None = None


def register_shop_lookup(provider: ShopLookupFn) -> None:
    """Register the shops module's owner_user_id -> shop_id lookup callback."""
    global _shop_lookup_provider
    _shop_lookup_provider = provider


def resolve_user_shop_id(db: Session, user_id: int) -> int | None:
    """Resolve the shop_id owned by user_id without cross-module imports."""
    if _shop_lookup_provider is None:
        return None
    return _shop_lookup_provider(db, user_id)


def register_catalog_search(provider: CatalogSearchFn) -> None:
    """Register the catalog module's active product search projection callback."""
    global _catalog_search_provider
    _catalog_search_provider = provider


def fetch_active_catalog_items(
    db: Session,
    *,
    category: str | None = None,
    max_price_cents: int | None = None,
) -> list[CatalogItemSummary]:
    """Fetch active catalog products via registered catalog adapter."""
    if _catalog_search_provider is None:
        return []
    return _catalog_search_provider(db, category, max_price_cents)
