from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import AuthenticatedUser, require_seller
from app.modules.catalog.schemas import (
    ProductCreateRequest,
    ProductResponse,
    ProductSKUCreateRequest,
    ProductSKUResponse,
    ProductSKUUpdateRequest,
    ProductUpdateRequest,
)
from app.modules.catalog.service import (
    create_product,
    create_sku,
    get_product,
    list_products,
    update_product,
    update_sku,
)

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


@router.post(
    "/shops/{shop_id}/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_product(
    shop_id: int,
    payload: ProductCreateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_seller)],
    db: Annotated[Session, Depends(get_db)],
) -> ProductResponse:
    return create_product(db, current_user, shop_id, payload)


@router.patch("/shops/{shop_id}/products/{product_id}", response_model=ProductResponse)
def patch_product(
    shop_id: int,
    product_id: int,
    payload: ProductUpdateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_seller)],
    db: Annotated[Session, Depends(get_db)],
) -> ProductResponse:
    return update_product(db, current_user, shop_id, product_id, payload)


@router.post(
    "/shops/{shop_id}/products/{product_id}/skus",
    response_model=ProductSKUResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_sku(
    shop_id: int,
    product_id: int,
    payload: ProductSKUCreateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_seller)],
    db: Annotated[Session, Depends(get_db)],
) -> ProductSKUResponse:
    return create_sku(db, current_user, shop_id, product_id, payload)


@router.patch("/shops/{shop_id}/skus/{sku_id}", response_model=ProductSKUResponse)
def patch_sku(
    shop_id: int,
    sku_id: int,
    payload: ProductSKUUpdateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_seller)],
    db: Annotated[Session, Depends(get_db)],
) -> ProductSKUResponse:
    return update_sku(db, current_user, shop_id, sku_id, payload)


@router.get("/products", response_model=list[ProductResponse])
def browse_products(
    db: Annotated[Session, Depends(get_db)],
    shop_id: Annotated[int | None, Query(ge=1)] = None,
    category: Annotated[str | None, Query(max_length=80)] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
) -> list[ProductResponse]:
    return list_products(db, shop_id=shop_id, category=category, q=q)


@router.get("/products/{product_id}", response_model=ProductResponse)
def read_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ProductResponse:
    return get_product(db, product_id)
