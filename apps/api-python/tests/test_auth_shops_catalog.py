from __future__ import annotations

import ast
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import create_app


@pytest.fixture()
def api_client(tmp_path: Path) -> Generator[TestClient, None, None]:
    db_file = tmp_path / "test_ge_shop.db"
    test_engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    app = create_app()
    Base.metadata.create_all(bind=test_engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    test_engine.dispose()


def _register_and_create_shop(
    client: TestClient,
    *,
    email: str,
    name: str,
    slug: str,
) -> tuple[str, int]:
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": f"Owner of {name}",
            "role": "seller",
        },
    )
    assert reg.status_code == 201
    seller_token = reg.json()["access_token"]

    shop_res = client.post(
        "/api/v1/shops",
        headers={"Authorization": f"Bearer {seller_token}"},
        json={"name": name, "slug": slug, "description": f"{name} storefront"},
    )
    assert shop_res.status_code == 201
    data = shop_res.json()
    return data["access_token"], data["id"]


def test_auth_registration_login_and_jwt_validation(api_client: TestClient) -> None:
    # Admin self-registration is forbidden (Req 1.2)
    admin_res = api_client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@geshop.dev",
            "password": "StrongPassword123!",
            "full_name": "Rogue Admin",
            "role": "admin",
        },
    )
    assert admin_res.status_code == 403

    # Buyer registration succeeds with 201 + JWT (Req 1.1)
    buyer_res = api_client.post(
        "/api/v1/auth/register",
        json={
            "email": "Buyer@GeShop.dev",
            "password": "StrongPassword123!",
            "full_name": "Alice Buyer",
            "role": "buyer",
        },
    )
    assert buyer_res.status_code == 201
    assert buyer_res.json()["user"]["email"] == "buyer@geshop.dev"

    # Duplicate email rejected with 409 (Req 1.2)
    dup_res = api_client.post(
        "/api/v1/auth/register",
        json={
            "email": "buyer@geshop.dev",
            "password": "StrongPassword123!",
            "full_name": "Duplicate",
            "role": "buyer",
        },
    )
    assert dup_res.status_code == 409

    # Wrong password rejected with 401 (Req 1.4)
    bad_login = api_client.post(
        "/api/v1/auth/login",
        json={"email": "buyer@geshop.dev", "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # Missing, tampered, and expired tokens rejected with 401 (Req 1.4)
    assert api_client.get("/api/v1/auth/me").status_code == 401
    assert (
        api_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        ).status_code
        == 401
    )
    expired_token = create_access_token(
        user_id=1,
        email="buyer@geshop.dev",
        role="buyer",
        expires_minutes=-5,
    )
    assert (
        api_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        ).status_code
        == 401
    )


def test_shop_onboarding_and_ownership_guards(api_client: TestClient) -> None:
    # Buyers cannot create a shop (Req 2.2)
    buyer_reg = api_client.post(
        "/api/v1/auth/register",
        json={
            "email": "buyer-shop@geshop.dev",
            "password": "StrongPassword123!",
            "full_name": "Buyer One",
            "role": "buyer",
        },
    )
    buyer_token = buyer_reg.json()["access_token"]
    buyer_shop = api_client.post(
        "/api/v1/shops",
        headers={"Authorization": f"Bearer {buyer_token}"},
        json={"name": "Nope Shop", "slug": "nope-shop"},
    )
    assert buyer_shop.status_code == 403

    # Seller A creates shop and gets shop_id-scoped JWT (Req 2.1)
    token_a, shop_a_id = _register_and_create_shop(
        api_client,
        email="seller-a@geshop.dev",
        name="Alpha Tech",
        slug="alpha-tech",
    )

    # Login also resolves shop_id into JWT (Req 1.3)
    login_a = api_client.post(
        "/api/v1/auth/login",
        json={"email": "seller-a@geshop.dev", "password": "StrongPassword123!"},
    )
    assert login_a.status_code == 200
    assert login_a.json()["user"]["shop_id"] == shop_a_id

    # Duplicate shop for same seller rejected with 409 (Req 2.2)
    second_shop = api_client.post(
        "/api/v1/shops",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"name": "Alpha Two", "slug": "alpha-two"},
    )
    assert second_shop.status_code == 409

    # Seller B cannot reuse Seller A's slug (Req 2.2)
    seller_b_reg = api_client.post(
        "/api/v1/auth/register",
        json={
            "email": "seller-b@geshop.dev",
            "password": "StrongPassword123!",
            "full_name": "Seller B",
            "role": "seller",
        },
    )
    seller_b_token = seller_b_reg.json()["access_token"]
    dup_slug = api_client.post(
        "/api/v1/shops",
        headers={"Authorization": f"Bearer {seller_b_token}"},
        json={"name": "Copycat", "slug": "alpha-tech"},
    )
    assert dup_slug.status_code == 409

    # Seller B creates their own shop, cannot mutate Seller A's shop (Req 2.3)
    token_b, _shop_b_id = _register_and_create_shop(
        api_client,
        email="seller-b2@geshop.dev",
        name="Beta Goods",
        slug="beta-goods",
    )
    cross_patch = api_client.patch(
        f"/api/v1/shops/{shop_a_id}",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"name": "Hijacked Shop"},
    )
    assert cross_patch.status_code == 403

    # Owner can update their own shop
    owner_patch = api_client.patch(
        f"/api/v1/shops/{shop_a_id}",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"description": "Official Alpha Tech Store"},
    )
    assert owner_patch.status_code == 200
    assert owner_patch.json()["description"] == "Official Alpha Tech Store"


def test_catalog_enforces_zero_float_money_and_cross_shop_tenancy_req01(
    api_client: TestClient,
) -> None:
    token_a, shop_a_id = _register_and_create_shop(
        api_client,
        email="vendor-a@geshop.dev",
        name="Vendor A",
        slug="vendor-a",
    )
    token_b, shop_b_id = _register_and_create_shop(
        api_client,
        email="vendor-b@geshop.dev",
        name="Vendor B",
        slug="vendor-b",
    )

    # Zero-float & int64-bounded money math: reject floats, bools, <= 0, and > int64 max (Req 3.3)
    for bad_price in (19.99, 19.0, True, 0, -500, 9_223_372_036_854_775_808):
        bad_res = api_client.post(
            f"/api/v1/catalog/shops/{shop_a_id}/products",
            headers={"Authorization": f"Bearer {token_a}"},
            json={
                "title": "Bad Price Item",
                "description": "Invalid price test",
                "category": "electronics",
                "skus": [
                    {
                        "sku_code": "BAD-01",
                        "variant_name": "Default",
                        "price_cents": bad_price,
                        "stock_qty": 10,
                    }
                ],
            },
        )
        assert bad_res.status_code == 422

    # Valid integer price_cents creates product + SKU (Req 3.2)
    create_res = api_client.post(
        f"/api/v1/catalog/shops/{shop_a_id}/products",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "title": "Mechanical Keyboard",
            "description": "Hot-swappable 75% wireless keyboard",
            "category": "Electronics",
            "skus": [
                {
                    "sku_code": "KB-75-BLK",
                    "variant_name": "Matte Black",
                    "price_cents": 199_900,
                    "stock_qty": 25,
                }
            ],
        },
    )
    assert create_res.status_code == 201
    product = create_res.json()
    product_a_id = product["id"]
    sku_a_id = product["skus"][0]["id"]
    assert product["category"] == "electronics"
    assert product["skus"][0]["price_cents"] == 199_900

    # REQ-01: Seller B cannot create or mutate Seller A's product or SKU (403 FORBIDDEN)
    assert (
        api_client.post(
            f"/api/v1/catalog/shops/{shop_a_id}/products",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "title": "Injected Product",
                "description": "Unauthorized",
                "category": "electronics",
            },
        ).status_code
        == 403
    )
    assert (
        api_client.patch(
            f"/api/v1/catalog/shops/{shop_a_id}/products/{product_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"title": "Tampered"},
        ).status_code
        == 403
    )
    assert (
        api_client.post(
            f"/api/v1/catalog/shops/{shop_a_id}/products/{product_a_id}/skus",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "sku_code": "HIJACK-01",
                "variant_name": "Hijack",
                "price_cents": 100,
                "stock_qty": 1,
            },
        ).status_code
        == 403
    )
    assert (
        api_client.patch(
            f"/api/v1/catalog/shops/{shop_a_id}/skus/{sku_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"price_cents": 100},
        ).status_code
        == 403
    )

    # REQ-01 IDOR check: Seller B passes their OWN shop_b_id in URL, targeting Shop A's entity IDs
    assert (
        api_client.post(
            f"/api/v1/catalog/shops/{shop_b_id}/products/{product_a_id}/skus",
            headers={"Authorization": f"Bearer {token_b}"},
            json={
                "sku_code": "IDOR-01",
                "variant_name": "IDOR",
                "price_cents": 100,
                "stock_qty": 1,
            },
        ).status_code
        == 403
    )
    assert (
        api_client.patch(
            f"/api/v1/catalog/shops/{shop_b_id}/skus/{sku_a_id}",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"price_cents": 100},
        ).status_code
        == 403
    )

    # Owner can add a SKU and update stock/price (Req 3.2)
    add_sku_res = api_client.post(
        f"/api/v1/catalog/shops/{shop_a_id}/products/{product_a_id}/skus",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "sku_code": "KB-75-WHT",
            "variant_name": "Frost White",
            "price_cents": 209_900,
            "stock_qty": 12,
        },
    )
    assert add_sku_res.status_code == 201
    white_sku_id = add_sku_res.json()["id"]

    # Reject stock_qty > int32 max and whitespace-only product title on PATCH (422)
    assert (
        api_client.patch(
            f"/api/v1/catalog/shops/{shop_a_id}/skus/{white_sku_id}",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"stock_qty": 2_147_483_648},
        ).status_code
        == 422
    )
    assert (
        api_client.patch(
            f"/api/v1/catalog/shops/{shop_a_id}/products/{product_a_id}",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"title": "   "},
        ).status_code
        == 422
    )

    # Public catalog read returns active SKUs only (Req 3.4)
    browse_res = api_client.get("/api/v1/catalog/products", params={"shop_id": shop_a_id})
    assert browse_res.status_code == 200
    assert len(browse_res.json()) == 1
    assert len(browse_res.json()[0]["skus"]) == 2

    deactivate_res = api_client.patch(
        f"/api/v1/catalog/shops/{shop_a_id}/skus/{white_sku_id}",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"is_active": False},
    )
    assert deactivate_res.status_code == 200
    detail_res = api_client.get(f"/api/v1/catalog/products/{product_a_id}")
    assert detail_res.status_code == 200
    assert [sku["id"] for sku in detail_res.json()["skus"]] == [sku_a_id]
    assert api_client.get("/api/v1/catalog/products/999999").status_code == 404


def test_modules_have_zero_cross_module_internal_imports() -> None:
    modules_root = Path(__file__).resolve().parents[1] / "app" / "modules"
    for py_file in modules_root.rglob("*.py"):
        current_module = py_file.relative_to(modules_root).parts[0]
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("app.modules."):
                    imported_module = node.module.split(".")[2]
                    assert imported_module == current_module, (
                        f"Cross-module import forbidden: {py_file} imports {node.module}"
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("app.modules."):
                        imported_module = alias.name.split(".")[2]
                        assert imported_module == current_module, (
                            f"Cross-module import forbidden: {py_file} imports {alias.name}"
                        )
