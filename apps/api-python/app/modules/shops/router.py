from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import AuthenticatedUser, require_seller
from app.modules.shops.schemas import (
    ShopCreateRequest,
    ShopCreateResponse,
    ShopResponse,
    ShopUpdateRequest,
)
from app.modules.shops.service import create_shop, get_shop, update_shop

router = APIRouter(prefix="/api/v1/shops", tags=["shops"])


@router.post("", response_model=ShopCreateResponse, status_code=status.HTTP_201_CREATED)
def onboard_shop(
    payload: ShopCreateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_seller)],
    db: Annotated[Session, Depends(get_db)],
) -> ShopCreateResponse:
    return create_shop(db, current_user, payload)


@router.get("/{shop_id}", response_model=ShopResponse)
def read_shop(
    shop_id: int,
    db: Annotated[Session, Depends(get_db)],
) -> ShopResponse:
    return get_shop(db, shop_id)


@router.patch("/{shop_id}", response_model=ShopResponse)
def patch_shop(
    shop_id: int,
    payload: ShopUpdateRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_seller)],
    db: Annotated[Session, Depends(get_db)],
) -> ShopResponse:
    return update_shop(db, current_user, shop_id, payload)
