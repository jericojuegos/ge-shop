from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.contracts import resolve_user_shop_id
from app.core.security import (
    AuthenticatedUser,
    create_access_token,
    hash_password,
    verify_password,
)
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    AuthTokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


def _build_token_response(user: User, shop_id: int | None) -> AuthTokenResponse:
    token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        shop_id=shop_id,
    )
    user_payload = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,  # type: ignore[arg-type]
        is_active=user.is_active,
        shop_id=shop_id,
    )
    return AuthTokenResponse(user=user_payload, access_token=token)


def register_user(db: Session, payload: UserRegisterRequest) -> AuthTokenResponse:
    """Register a new buyer or seller and return a signed JWT."""
    if payload.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin self-registration is forbidden",
        )

    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _build_token_response(user, shop_id=None)


def login_user(db: Session, payload: UserLoginRequest) -> AuthTokenResponse:
    """Authenticate user credentials and issue a JWT with any owned shop_id."""
    user = db.scalar(select(User).where(User.email == payload.email))
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    shop_id = resolve_user_shop_id(db, user.id)
    return _build_token_response(user, shop_id=shop_id)


def refresh_user_token(db: Session, current_user: AuthenticatedUser) -> AuthTokenResponse:
    """Re-issue JWT with the user's latest DB role and shop_id tenancy scope."""
    user = db.scalar(select(User).where(User.id == current_user.user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or missing",
        )

    shop_id = resolve_user_shop_id(db, user.id)
    return _build_token_response(user, shop_id=shop_id)
