from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.contracts import CatalogItemSummary
from app.core.security import AuthenticatedUser, verify_shop_ownership
from app.modules.catalog.models import Product, ProductSKU
from app.modules.catalog.schemas import (
    ProductCreateRequest,
    ProductResponse,
    ProductSKUCreateRequest,
    ProductSKUResponse,
    ProductSKUUpdateRequest,
    ProductUpdateRequest,
)


def _ensure_unique_sku_codes(db: Session, shop_id: int, sku_codes: list[str]) -> None:
    if len(sku_codes) != len(set(sku_codes)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate sku_code in request payload",
        )
    if not sku_codes:
        return
    existing = db.scalars(
        select(ProductSKU.sku_code).where(
            ProductSKU.shop_id == shop_id,
            ProductSKU.sku_code.in_(sku_codes),
        )
    ).all()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"sku_code already exists in shop: {existing[0]}",
        )


def create_product(
    db: Session,
    current_user: AuthenticatedUser,
    shop_id: int,
    payload: ProductCreateRequest,
) -> ProductResponse:
    """Create a product and optional initial SKUs after verifying JWT shop_id ownership."""
    verify_shop_ownership(current_user, shop_id)
    _ensure_unique_sku_codes(db, shop_id, [sku.sku_code for sku in payload.skus])

    product = Product(
        shop_id=shop_id,
        title=payload.title,
        description=payload.description.strip(),
        category=payload.category,
        is_active=True,
    )
    for sku_in in payload.skus:
        product.skus.append(
            ProductSKU(
                shop_id=shop_id,
                sku_code=sku_in.sku_code,
                variant_name=sku_in.variant_name,
                price_cents=sku_in.price_cents,
                stock_qty=sku_in.stock_qty,
                is_active=True,
            )
        )

    db.add(product)
    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


def update_product(
    db: Session,
    current_user: AuthenticatedUser,
    shop_id: int,
    product_id: int,
    payload: ProductUpdateRequest,
) -> ProductResponse:
    """Update product fields after verifying JWT shop_id and entity ownership."""
    verify_shop_ownership(current_user, shop_id)

    product = db.scalar(
        select(Product).options(selectinload(Product.skus)).where(Product.id == product_id)
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.shop_id != shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="FORBIDDEN: Product belongs to another shop",
        )

    if payload.title is not None:
        product.title = payload.title.strip()
    if payload.description is not None:
        product.description = payload.description.strip()
    if payload.category is not None:
        product.category = payload.category
    if payload.is_active is not None:
        product.is_active = payload.is_active

    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


def create_sku(
    db: Session,
    current_user: AuthenticatedUser,
    shop_id: int,
    product_id: int,
    payload: ProductSKUCreateRequest,
) -> ProductSKUResponse:
    """Create a SKU under an owned product after verifying JWT shop_id and product tenancy."""
    verify_shop_ownership(current_user, shop_id)

    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if product.shop_id != shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="FORBIDDEN: Product belongs to another shop",
        )

    _ensure_unique_sku_codes(db, shop_id, [payload.sku_code])

    sku = ProductSKU(
        product_id=product.id,
        shop_id=shop_id,
        sku_code=payload.sku_code,
        variant_name=payload.variant_name,
        price_cents=payload.price_cents,
        stock_qty=payload.stock_qty,
        is_active=True,
    )
    db.add(sku)
    db.commit()
    db.refresh(sku)
    return ProductSKUResponse.model_validate(sku)


def update_sku(
    db: Session,
    current_user: AuthenticatedUser,
    shop_id: int,
    sku_id: int,
    payload: ProductSKUUpdateRequest,
) -> ProductSKUResponse:
    """Modify an existing SKU after verifying JWT shop_id and SKU shop_id ownership."""
    verify_shop_ownership(current_user, shop_id)

    sku = db.scalar(select(ProductSKU).where(ProductSKU.id == sku_id))
    if sku is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SKU not found")
    if sku.shop_id != shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="FORBIDDEN: SKU belongs to another shop",
        )

    if payload.variant_name is not None:
        sku.variant_name = payload.variant_name
    if payload.price_cents is not None:
        sku.price_cents = payload.price_cents
    if payload.stock_qty is not None:
        sku.stock_qty = payload.stock_qty
    if payload.is_active is not None:
        sku.is_active = payload.is_active

    db.commit()
    db.refresh(sku)
    return ProductSKUResponse.model_validate(sku)


def _to_active_product_response(product: Product) -> ProductResponse:
    active_skus = [
        ProductSKUResponse.model_validate(sku) for sku in product.skus if sku.is_active
    ]
    return ProductResponse(
        id=product.id,
        shop_id=product.shop_id,
        title=product.title,
        description=product.description,
        category=product.category,
        is_active=product.is_active,
        skus=active_skus,
    )


def list_products(
    db: Session,
    *,
    shop_id: int | None = None,
    category: str | None = None,
    q: str | None = None,
) -> list[ProductResponse]:
    """List active catalog products with optional shop, category, and keyword filters."""
    stmt = (
        select(Product)
        .options(selectinload(Product.skus))
        .where(Product.is_active.is_(True))
        .order_by(Product.id)
    )
    if shop_id is not None:
        stmt = stmt.where(Product.shop_id == shop_id)
    if category is not None:
        stmt = stmt.where(Product.category == category.strip().lower())
    if q is not None and q.strip():
        needle = f"%{q.strip()}%"
        stmt = stmt.where(Product.title.ilike(needle) | Product.description.ilike(needle))

    products = db.scalars(stmt).all()
    return [_to_active_product_response(product) for product in products]


def get_product(db: Session, product_id: int) -> ProductResponse:
    """Fetch a single active product and its active SKUs by ID."""
    product = db.scalar(
        select(Product)
        .options(selectinload(Product.skus))
        .where(Product.id == product_id, Product.is_active.is_(True))
    )
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return _to_active_product_response(product)


def search_catalog_items(
    db: Session,
    category: str | None = None,
    max_price_cents: int | None = None,
) -> list[CatalogItemSummary]:
    """Catalog search adapter exposed to ai_search via app/core/contracts.py."""
    stmt = (
        select(Product)
        .options(selectinload(Product.skus))
        .where(Product.is_active.is_(True))
    )
    if category is not None:
        stmt = stmt.where(Product.category == category.strip().lower())

    summaries: list[CatalogItemSummary] = []
    for product in db.scalars(stmt).all():
        active_skus = [sku for sku in product.skus if sku.is_active]
        if not active_skus:
            continue
        min_price = min(sku.price_cents for sku in active_skus)
        if max_price_cents is not None and min_price > max_price_cents:
            continue
        summaries.append(
            CatalogItemSummary(
                product_id=product.id,
                shop_id=product.shop_id,
                title=product.title,
                description=product.description,
                category=product.category,
                min_price_cents=min_price,
                sku_count=len(active_skus),
                total_stock_qty=sum(sku.stock_qty for sku in active_skus),
            )
        )
    return summaries
