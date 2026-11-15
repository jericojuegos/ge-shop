# 🧪 Feature UAT & Verification: Auth, Seller Shops, Catalog & Gemini Search (`01-auth-and-seller-shops`)

> **Feature Slug:** `01-auth-and-seller-shops` · **Spec Links:** [`requirements.md`](./requirements.md) · [`design.md`](./design.md) · [`tasks.md`](./tasks.md)  
> **Overall Status:** `[x]` Passed · **Verified Date:** `2026-11-15`

---

## Level 1 — Automated Terminal, Unit & AI Eval Checks (AI Executes)

- [x] **Lint & Syntax Check:** `cd apps/api-python && uv run ruff check .` passed (`All checks passed!`).
- [x] **Stack Hard-Failure Audit:** Verified zero cross-module `app.modules.<other>` imports (`test_auth_shops_catalog.py:L403`), Pydantic v2 validation, parameterized SQLAlchemy queries, zero-float int64 money math, and multi-vendor `shop_id` tenancy guard; blind-diff reviewer found 5 `P1` defects (blocking I/O in `async def`, int64/int32 overflow, XML tag breakout, inactive SKU leakage, blank PATCH title), all 5 fixed with regression tests.
- [x] **Unit & Tenancy Invariant Tests:** `cd apps/api-python && uv run pytest -v` passed (`12 passed, 3 skipped` — skipped tests are live Gemini evals gated on `RUN_AI_EVALS=1`).
- [x] **AI Prompt / LLM Evals:** `tests/evals/test_ai_search_eval.py` passed all 5 Tier 1 deterministic prompt-injection, XML delimiter escaping, token-budget truncation, schema invariant, and offline semantic ranking checks.

---

## Level 2 — Functional & EARS Requirement Verification (Deterministic Evidence)

| Check ID | Requirement Ref | Scenario (WHEN / IF) | Expected Outcome (THE System SHALL) | Evidence / Proof (`test:line`, CLI output) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UAT-1.1** | `Req 1.1, 1.2` | Register buyer/seller vs duplicate email or `role="admin"` | `201` with JWT on valid; `403` on `admin`; `409` on duplicate email | `tests/test_auth_shops_catalog.py:L71` PASS (`201`, `403`, `409`) | `[x]` |
| **UAT-1.2** | `Req 1.3, 1.4` | Login with valid vs invalid credentials; `/auth/me` with tampered/expired token | `200` with `shop_id` claim on valid; `401` on invalid/expired | `tests/test_auth_shops_catalog.py:L71,L140` PASS (`200`, `401`) | `[x]` |
| **UAT-2.1** | `Req 2.1, 2.2` | Seller creates shop vs buyer or duplicate seller/slug | `201` + `shop_id`-scoped JWT; `403` for buyer; `409` on duplicate | `tests/test_auth_shops_catalog.py:L140` PASS (`201`, `403`, `409`) | `[x]` |
| **UAT-2.2** | `Req 2.3` | Seller A attempts `PATCH /api/v1/shops/{shop_b_id}` | `403 FORBIDDEN` and zero DB mutation | `tests/test_auth_shops_catalog.py:L140` PASS (`403`) | `[x]` |
| **UAT-3.1** | `Req 3.1 (REQ-01)` | Seller B attempts to create/modify product or SKU under Shop A (direct or IDOR) | `403 FORBIDDEN` and zero DB mutation | `tests/test_auth_shops_catalog.py:L225` PASS (`403` across all 6 cross-shop vectors) | `[x]` |
| **UAT-3.2** | `Req 3.2, 3.3` | Create/update SKU with integer `price_cents` vs float/bool/`<=0`/`>int64` or blank title | `201`/`200` on exact int64; `422` on invalid money/stock/title | `tests/test_auth_shops_catalog.py:L225` PASS (`201`, `200`, `422`) | `[x]` |
| **UAT-3.3** | `Req 3.4` | Query `GET /api/v1/catalog/products` and `/products/{id}` after deactivating SKU | `200` with active SKUs & integer `price_cents`; `404` for unknown ID | `tests/test_auth_shops_catalog.py:L225` PASS (`200`, `404`) | `[x]` |
| **UAT-4.1** | `Req 4.1–4.3` | `POST /api/v1/ai-search/search` with natural-language query, XML breakout, & injection input | XML-delimited escaped prompt, offline fallback works, integer `min_price_cents` | `tests/evals/test_ai_search_eval.py:L164,L177,L183,L196,L225` PASS | `[x]` |

---

## Level 3 — Manual API Walkthrough & Sign-Off

- [x] **API Surface & Contracts:** Backend-only Wave 1 scope (`[BE]`); no `[FE]` UI screens in this feature.
- [x] **Sign-Off:** Approved to mark `[x]` in `docs/planning/roadmap.md` via `/ship`.

### 1. Prerequisites & Local Setup
- **Start Server:** `cd apps/api-python && uv run uvicorn app.main:app --reload --port 8000`
- **API Docs:** `http://127.0.0.1:8000/docs`

### 2. Happy-Path Walkthrough (`Req 1.1–4.1`)
1. `POST /api/v1/auth/register` with `role: "seller"` → capture `access_token`.
2. `POST /api/v1/shops` with Bearer token → capture `id` (`shop_id`) and updated `access_token`.
3. `POST /api/v1/catalog/shops/{shop_id}/products` with integer `price_cents: 199900` → product & SKU created (`201`).
4. `POST /api/v1/ai-search/search` with `{"query": "wireless mechanical keyboard under 250000 cents"}` → ranked product returned with `min_price_cents: 199900`.

### 3. Edge Cases & Security Validation (`Req 1.2, 3.1, 3.3`)
1. Submit `price_cents: 199.99` or `9223372036854775808` → rejected with `422`.
2. Authenticate as Seller B and call `PATCH /api/v1/catalog/shops/{shop_a_id}/skus/{sku_id}` → rejected with `403 FORBIDDEN`.
