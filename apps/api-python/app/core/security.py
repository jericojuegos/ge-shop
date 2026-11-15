from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import settings

_PBKDF2_ITERATIONS = 200_000
_BEARER_SCHEME = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    """Verified JWT principal attached to protected FastAPI routes."""

    model_config = ConfigDict(frozen=True)

    user_id: int = Field(..., ge=1)
    email: str
    role: Literal["buyer", "seller", "admin"]
    shop_id: int | None = Field(default=None, ge=1)


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2-HMAC-SHA256 hash."""
    try:
        scheme, salt_hex, digest_hex = stored_hash.split("$", 2)
        if scheme != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return hmac.compare_digest(actual, expected)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding)


def create_access_token(
    *,
    user_id: int,
    email: str,
    role: str,
    shop_id: int | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Sign an HS256 JWT containing user identity, role, and optional shop_id tenancy scope."""
    now = int(time.time())
    ttl_minutes = (
        expires_minutes if expires_minutes is not None else settings.jwt_access_token_expire_minutes
    )
    header = {"alg": settings.jwt_algorithm, "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "uid": user_id,
        "email": email,
        "role": role,
        "shop_id": shop_id,
        "iat": now,
        "exp": now + (ttl_minutes * 60),
    }
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> AuthenticatedUser:
    """Verify HS256 JWT signature and expiration and return AuthenticatedUser."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    parts = token.split(".")
    if len(parts) != 3:
        raise unauthorized

    header_b64, payload_b64, signature_b64 = parts
    try:
        header = json.loads(_b64url_decode(header_b64))
        if not isinstance(header, dict) or header.get("alg") != settings.jwt_algorithm:
            raise unauthorized
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(
            settings.jwt_secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        actual_sig = _b64url_decode(signature_b64)
        if not hmac.compare_digest(actual_sig, expected_sig):
            raise unauthorized

        payload = json.loads(_b64url_decode(payload_b64))
        if not isinstance(payload, dict):
            raise unauthorized
        exp = payload.get("exp")
        if not isinstance(exp, int) or isinstance(exp, bool) or exp < int(time.time()):
            raise unauthorized

        return AuthenticatedUser(
            user_id=payload["uid"],
            email=payload["email"],
            role=payload["role"],
            shop_id=payload.get("shop_id"),
        )
    except (ValueError, KeyError, TypeError, ValidationError) as exc:
        raise unauthorized from exc


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_BEARER_SCHEME)],
) -> AuthenticatedUser:
    """FastAPI dependency extracting and validating the Bearer JWT principal."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


def require_seller(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    """FastAPI dependency requiring an authenticated seller role."""
    if current_user.role != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller account required for this operation",
        )
    return current_user


def verify_shop_ownership(current_user: AuthenticatedUser, target_shop_id: int) -> None:
    """Enforce multi-vendor tenancy: authenticated seller JWT shop_id must match target_shop_id."""
    if current_user.role != "seller":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller role required for shop mutations",
        )
    if current_user.shop_id is None or current_user.shop_id != target_shop_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="FORBIDDEN: Authenticated seller does not own target shop_id",
        )
