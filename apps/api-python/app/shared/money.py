from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
