from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import AuthenticatedUser, create_access_token, verify_shop_ownership
from app.modules.shops.models import Shop
from app.modules.shops.schemas import (
    ShopCreateRequest,
    ShopCreateResponse,
    ShopResponse,
    ShopUpdateRequest,
)


def lookup_user_shop_id(db: Session, user_id: int) -> int | None:
    """Resolve active or inactive shop_id owned by user_id for JWT claims."""
    return db.scalar(select(Shop.id).where(Shop.owner_user_id == user_id))


def create_shop(
    db: Session,
    current_user: AuthenticatedUser,
    payload: ShopCreateRequest,
) -> ShopCreateResponse:
    """Onboard a shop for an authenticated seller and mint a shop_id-scoped JWT."""
    existing_owner_shop = db.scalar(
        select(Shop).where(Shop.owner_user_id == current_user.user_id)
    )
    if existing_owner_shop is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seller already owns a registered shop",
        )

    existing_slug = db.scalar(select(Shop).where(Shop.slug == payload.slug))
    if existing_slug is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Shop slug is already taken",
        )

    shop = Shop(
        owner_user_id=current_user.user_id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description.strip(),
        is_active=True,
    )
    db.add(shop)
    db.commit()
    db.refresh(shop)

    scoped_token = create_access_token(
        user_id=current_user.user_id,
        email=current_user.email,
        role=current_user.role,
        shop_id=shop.id,
    )
    return ShopCreateResponse(
        id=shop.id,
        owner_user_id=shop.owner_user_id,
        name=shop.name,
        slug=shop.slug,
        description=shop.description,
        is_active=shop.is_active,
        access_token=scoped_token,
    )


def get_shop(db: Session, shop_id: int) -> ShopResponse:
    """Retrieve public storefront details by shop_id."""
    shop = db.scalar(select(Shop).where(Shop.id == shop_id))
    if shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found",
        )
    return ShopResponse.model_validate(shop)


def update_shop(
    db: Session,
    current_user: AuthenticatedUser,
    shop_id: int,
    payload: ShopUpdateRequest,
) -> ShopResponse:
    """Update shop metadata after enforcing JWT shop_id and DB owner_user_id tenancy."""
    verify_shop_ownership(current_user, shop_id)

    shop = db.scalar(select(Shop).where(Shop.id == shop_id))
    if shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found",
        )
    if shop.owner_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="FORBIDDEN: Authenticated seller does not own target shop",
        )

    if payload.name is not None:
        shop.name = payload.name
    if payload.description is not None:
        shop.description = payload.description.strip()
    if payload.is_active is not None:
        shop.is_active = payload.is_active

    db.commit()
    db.refresh(shop)
    return ShopResponse.model_validate(shop)
