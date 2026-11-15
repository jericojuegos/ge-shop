from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

MAX_INT64 = 9_223_372_036_854_775_807


def validate_exact_int_cents(value: object, *, allow_zero: bool = True) -> int:
    """Reject booleans, floats, strings, and values outside signed 64-bit integer range."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("Money values must be exact integers in cents (no floats or booleans).")
    if value > MAX_INT64:
        raise ValueError(f"Money value in cents cannot exceed int64 max ({MAX_INT64}).")
    if allow_zero:
        if value < 0:
            raise ValueError("Money value in cents cannot be negative.")
    elif value <= 0:
        raise ValueError("Money value in cents must be strictly positive.")
    return value


def _validate_positive_cents(value: object) -> int:
    return validate_exact_int_cents(value, allow_zero=False)


def _validate_non_negative_cents(value: object) -> int:
    return validate_exact_int_cents(value, allow_zero=True)


StrictPositiveCents = Annotated[int, BeforeValidator(_validate_positive_cents)]
StrictNonNegativeCents = Annotated[int, BeforeValidator(_validate_non_negative_cents)]


class MoneyCents(BaseModel):
    """64-bit integer minor-unit money wrapper (Zero-Float Money Math)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    amount_cents: int = Field(..., ge=0, description="Non-negative integer cents")

    @field_validator("amount_cents", mode="before")
    @classmethod
    def reject_non_int(cls, value: object) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("MoneyCents requires an exact integer amount in cents (no floats).")
        return value

    def add(self, other: MoneyCents) -> MoneyCents:
        return MoneyCents(amount_cents=self.amount_cents + other.amount_cents)

    def apply_discount_clamped(self, discount_cents: int) -> MoneyCents:
        if isinstance(discount_cents, bool) or not isinstance(discount_cents, int):
            raise TypeError("discount_cents must be an integer.")
        if discount_cents < 0:
            raise ValueError("discount_cents cannot be negative.")
        return MoneyCents(amount_cents=max(0, self.amount_cents - discount_cents))
