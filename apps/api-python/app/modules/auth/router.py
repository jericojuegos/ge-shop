from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import AuthenticatedUser, get_current_user
from app.modules.auth.schemas import AuthTokenResponse, UserLoginRequest, UserRegisterRequest
from app.modules.auth.service import login_user, refresh_user_token, register_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AuthTokenResponse:
    return register_user(db, payload)


@router.post("/login", response_model=AuthTokenResponse)
def login(
    payload: UserLoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AuthTokenResponse:
    return login_user(db, payload)


@router.post("/refresh", response_model=AuthTokenResponse)
def refresh_token(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AuthTokenResponse:
    return refresh_user_token(db, current_user)


@router.get("/me", response_model=AuthenticatedUser)
def read_me(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    return current_user
