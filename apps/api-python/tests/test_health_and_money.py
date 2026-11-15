from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.shared.money import MoneyCents

client = TestClient(app)


def test_health_endpoint_returns_ok_and_cents_unit() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ge-shop-api-python",
        "money_unit": "cents_int64",
    }


def test_money_cents_accepts_integers_and_clamps_discounts() -> None:
    price = MoneyCents(amount_cents=150_000)
    shipping = MoneyCents(amount_cents=15_000)
    total = price.add(shipping)
    assert total.amount_cents == 165_000

    discounted = price.apply_discount_clamped(50_000)
    assert discounted.amount_cents == 100_000

    clamped_zero = price.apply_discount_clamped(250_000)
    assert clamped_zero.amount_cents == 0


def test_money_cents_rejects_floats_and_booleans() -> None:
    with pytest.raises((TypeError, ValidationError)):
        MoneyCents(amount_cents=19.99)  # type: ignore[arg-type]

    with pytest.raises((TypeError, ValidationError)):
        MoneyCents(amount_cents=True)  # type: ignore[arg-type]
