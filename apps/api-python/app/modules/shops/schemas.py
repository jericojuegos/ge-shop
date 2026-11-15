from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ShopCreateRequest(BaseModel):
    """Payload for onboarding a new seller shop."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=2, max_length=120)
    slug: str = Field(..., min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Shop name must contain at least 2 non-whitespace characters")
        return cleaned

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not _SLUG_PATTERN.match(cleaned):
            raise ValueError("Slug must contain lowercase letters, numbers, and single hyphens")
        return cleaned


class ShopUpdateRequest(BaseModel):
    """Payload for updating an owned seller shop."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def clean_optional_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Shop name must contain at least 2 non-whitespace characters")
        return cleaned


class ShopResponse(BaseModel):
    """Public storefront representation of a Seller Shop."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_user_id: int
    name: str
    slug: str
    description: str
    is_active: bool


class ShopCreateResponse(ShopResponse):
    """Response returned upon onboarding a shop, including a shop_id-scoped JWT."""

    access_token: str
    token_type: str = "bearer"
