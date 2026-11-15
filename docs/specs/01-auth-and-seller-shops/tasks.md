# ✅ Feature Tasks: Auth, Seller Shops, Catalog & Gemini Search (`01-auth-and-seller-shops`)

> **Phase / Wave:** `Phase 1 (Wave 1)` · **Branch / Owner:** `feat/01-auth-and-seller-shops` · **Status:** `[x]` Complete  
> **Depends On:** `00-scaffold` · **Touches:** `apps/api-python/app/core/, apps/api-python/app/shared/, apps/api-python/app/modules/{auth,shops,catalog,ai_search}/, apps/api-python/tests/`  
> **Spec Links:** [`requirements.md`](./requirements.md) · [`design.md`](./design.md) · [`uat.md`](./uat.md)

---

## 🔄 Implementation Tasks

### 1. Core Security, Contracts & Money Helpers (`⚡ BATCH`: Core Infrastructure)
- [x] **1.1** `[BE]` Extend `apps/api-python/app/core/config.py` and `apps/api-python/app/shared/money.py` with JWT/Gemini settings and `StrictPositiveCents` / `validate_exact_int_cents` zero-float validator.
  - _Requirements: 1.3, 3.2, 3.3, 4.1_
- [x] **1.2** `[BE]` Implement `apps/api-python/app/core/security.py` (PBKDF2-HMAC-SHA256 password hashing, HS256 JWT encode/decode, `AuthenticatedUser`, `get_current_user`, `require_seller`, `verify_shop_ownership`) and `apps/api-python/app/core/contracts.py` (cross-module lookup/search registry).
  - _Requirements: 1.1, 1.3, 1.4, 2.3, 3.1_
- [x] **1.3** `[BE]` Implement `apps/api-python/app/core/ai_client.py` with XML `<user_input>` prompt builder, Gemini REST call via `httpx`, and deterministic offline fallback intent extractor.
  - _Requirements: 4.1, 4.2, 4.3_
- [x] **1.4** `[REVIEW]` **Core Infrastructure Checkpoint:** Run `uv run ruff check .` and `uv run pytest` — must pass with zero errors.

### 2. Auth & Seller Shops Modules (`⚡ BATCH`: Identity & Multi-Vendor Tenancy)
- [x] **2.1** `[BE]` Implement `apps/api-python/app/modules/auth/{models,schemas,service,router}.py` (`/register`, `/login`, `/refresh`, `/me`).
  - _Requirements: 1.1, 1.2, 1.3, 1.4_
- [x] **2.2** `[BE]` Implement `apps/api-python/app/modules/shops/{models,schemas,service,router}.py` (create shop with scoped JWT, public read, owner-guarded update) and expose `lookup_user_shop_id` adapter.
  - _Requirements: 2.1, 2.2, 2.3_
- [x] **2.3** `[REVIEW]` **Auth & Shops Checkpoint:** Run `uv run ruff check .` — must pass with zero errors.

### 3. Catalog & Gemini AI Search Modules (`⚡ BATCH`: Multi-Vendor Catalog & Discovery)
- [x] **3.1** `[BE]` Implement `apps/api-python/app/modules/catalog/{models,schemas,service,router}.py` (Product & SKU CRUD with `403 FORBIDDEN` cross-shop guard and strict `price_cents` int64 validation) and expose `search_catalog_items` adapter.
  - _Requirements: 3.1, 3.2, 3.3, 3.4_
- [x] **3.2** `[BE]` Implement `apps/api-python/app/modules/ai_search/{schemas,service,router}.py` (`POST /api/v1/ai-search/search` using `app/core/ai_client.py` and `contracts.search_catalog_items`).
  - _Requirements: 4.1, 4.2, 4.3_
- [x] **3.3** `[BE]` Wire module routers, model imports, and `contracts` callbacks in `apps/api-python/app/main.py`.
  - _Requirements: 1.1, 2.1, 3.1, 4.1_
- [x] **3.4** `[REVIEW]` **Modules & Composition Root Checkpoint:** Run `uv run ruff check .` — must pass with zero errors.

### 4. Automated Unit, Tenancy Invariant & AI Eval Suites (`⚡ BATCH`: Tier 1 Tests & Verification)
- [x] **4.1** `[BE]` Write `apps/api-python/tests/test_auth_shops_catalog.py` testing auth lifecycle, shop onboarding, float/bool `price_cents` rejection (`422`), and `REQ-01` cross-shop SKU mutation rejection (`403 FORBIDDEN`).
  - _Validates: Property 1, Property 2 (Requirements 1.1–3.4)_
- [x] **4.2** `[BE]` Write `apps/api-python/tests/evals/test_ai_search_eval.py` (Tier 1 deterministic XML/injection/schema/ranking evals + Tier 2 `RUN_AI_EVALS=1` golden dataset).
  - _Validates: Property 3 (Requirements 4.1–4.3)_
- [x] **4.3** `[REVIEW]` **Final Feature Checkpoint:** Run `uv run ruff check .` and `uv run pytest`, then run `/verify` and `/ship`.

---

## 🔀 Task Dependency Graph (Intra-Feature Waves)

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["1.4"] },
    { "id": 2, "tasks": ["2.1", "2.2"] },
    { "id": 3, "tasks": ["2.3"] },
    { "id": 4, "tasks": ["3.1", "3.2", "3.3"] },
    { "id": 5, "tasks": ["3.4"] },
    { "id": 6, "tasks": ["4.1", "4.2"] },
    { "id": 7, "tasks": ["4.3"] }
  ]
}
```

---

## 🐛 Ad-Hoc / Small Enhancements
*(None)*

---

## 🧪 Feature Verification & UAT Gate
- [x] **Level 1 (Automated Build & Unit Tests):** `uv run ruff check .` and `uv run pytest` pass with zero errors
- [x] **Level 2 & 3 (UAT & Verification):** `/verify` completed in [`uat.md`](./uat.md)

---

## 🛑 Blocked / Waiting
*(None)*

---

## 📝 Feature Activity Log

| Date | Task | Action & Files Touched |
| :--- | :--- | :--- |
| `2026-11-15` | Spec Init | Expanded `requirements.md`, `design.md`, `tasks.md`, and `uat.md` via `/spec` Mode A on branch `feat/01-auth-and-seller-shops`. |
| `2026-11-15` | 1.1–4.3 | Implemented `core/{config,security,contracts,ai_client}.py`, `shared/money.py`, `modules/{auth,shops,catalog,ai_search}/`, `main.py`, `tests/test_auth_shops_catalog.py`, and `tests/evals/test_ai_search_eval.py`. |
| `2026-11-15` | Verify | Blind-diff reviewer surfaced 5 `P1` defects (blocking DB in `async def`, int64/int32 overflow, XML tag breakout, inactive SKU leakage, blank PATCH title); fixed all 5 + added regression tests. `ruff check .` (0 errors) and `pytest -v` (12 passed, 3 live-evals skipped) green. |
