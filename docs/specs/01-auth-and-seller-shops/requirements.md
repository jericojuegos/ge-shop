# 📋 Feature Requirements: Auth, Seller Shops, Catalog & Gemini Search (`01-auth-and-seller-shops`)

> **Feature Slug:** `01-auth-and-seller-shops` · **Phase / Wave:** `Phase 1 (Wave 1)`  
> **Depends On:** `00-scaffold`  
> **Branch / Owner:** `feat/01-auth-and-seller-shops` · **Status:** `[x]` Complete

---

## 1. Introduction & Overview

This feature establishes the core multi-vendor marketplace identity, tenancy, catalog, and AI-assisted product discovery layer in `apps/api-python/`. Buyers and Sellers register and authenticate via standalone HS256 JWT tokens, Sellers onboard a dedicated Seller Shop (`shop_id` tenant), manage Products and SKUs with strict 64-bit integer minor-unit pricing (`price_cents`), and Buyers discover products via both deterministic catalog filtering and Gemini-powered semantic search (`ai_search`).

### Assumptions (Flagged for Review)

- **A1 (1-to-1 Seller-to-Shop Binding in Phase 1):** Each authenticated `seller` user owns at most one `Shop` in Phase 1 so the JWT `shop_id` claim is unambiguous. **Confirmed for Phase 1.**
- **A2 (JWT Implementation):** HS256 JWT signing/verification and PBKDF2-HMAC-SHA256 password hashing use Python standard library primitives (`hmac`, `hashlib`, `base64`, `json`) in `app/core/security.py` so zero external C-extension dependencies are required. **Confirmed.**
- **A3 (Offline-Capable Gemini Search):** `ai_search` calls Google Gemini REST API when `GEMINI_API_KEY` is set and `AI_PROVIDER=google`, and falls back deterministically to offline semantic intent parsing when `GEMINI_API_KEY` is unset (enabling `$0` CI and unit/eval verification). **Confirmed.**

### Domain Glossary

- **User (`users`):** Authenticated marketplace actor with `role` in `{"buyer", "seller", "admin"}`.
- **Seller Shop (`shops`):** Multi-vendor storefront tenant uniquely owned by one `seller` user (`owner_user_id`), identified by `shop_id`.
- **Product (`products`) & ProductSKU (`product_skus`):** Sellable catalog listing owned by a `shop_id`, containing one or more variant SKUs priced in integer `price_cents` (`int64`, zero floats) and `stock_qty`.
- **SemanticSearchIntent:** Structured Pydantic v2 intent extracted from a buyer's natural-language query (`keywords`, `category_hint`, `max_price_cents`, `sort_by`) by Gemini or offline fallback.

---

## 2. Requirements & EARS Acceptance Criteria

### Requirement 1: Standalone JWT Authentication & Role Onboarding

**User Story:** As a Buyer or Seller, I want to register and log in with email and password, so that I receive a signed JWT carrying my `user_id`, `role`, and `shop_id` tenancy scope.

#### Acceptance Criteria
1. **1.1:** WHEN a user submits `POST /api/v1/auth/register` with a unique email, password (`>= 8` chars), `full_name`, and `role` (`buyer` or `seller`), THE `auth` module SHALL hash the password with a random per-user salt, persist the user, and return HTTP `201` with user metadata and a signed HS256 `access_token`.
2. **1.2:** IF a registration payload requests `role="admin"` or uses an already-registered email, THEN THE `auth` module SHALL reject the request with HTTP `403 FORBIDDEN` (for `admin`) or `409 CONFLICT` (for duplicate email) and write zero database records.
3. **1.3:** WHEN a user submits valid credentials to `POST /api/v1/auth/login`, THE `auth` module SHALL verify the password hash, resolve any owned `shop_id`, and return HTTP `200` with an HS256 JWT containing `sub`, `email`, `role`, `shop_id`, and `exp`.
4. **1.4:** IF credentials are invalid, or a Bearer token is missing, malformed, tampered, or expired on `GET /api/v1/auth/me` or any protected route, THEN THE System SHALL reject the request with HTTP `401 UNAUTHORIZED`.

---

### Requirement 2: Seller Shop Onboarding & Multi-Vendor Tenancy Guard

**User Story:** As a Seller, I want to create and manage my own Seller Shop, so that my storefront and inventory are strictly isolated from other sellers.

#### Acceptance Criteria
1. **2.1:** WHEN an authenticated `seller` submits `POST /api/v1/shops` with a unique `name` and `slug`, THE `shops` module SHALL create the `Shop` bound to `owner_user_id = current_user.user_id` and return HTTP `201` including a refreshed `access_token` scoped to the new `shop_id`.
2. **2.2:** IF a `buyer` attempts to create a shop, or a `seller` already owns a shop or submits a duplicate `slug`, THEN THE `shops` module SHALL reject the request with HTTP `403 FORBIDDEN` (for `buyer`) or `409 CONFLICT` (for duplicate shop/slug) and write zero records.
3. **2.3:** WHEN an authenticated seller calls `PATCH /api/v1/shops/{shop_id}`, THE `shops` module SHALL enforce both `current_user.shop_id == shop_id` and `shop.owner_user_id == current_user.user_id`, rejecting cross-shop mutations with HTTP `403 FORBIDDEN`.

---

### Requirement 3: Multi-Vendor Catalog & Zero-Float SKU Pricing (`REQ-01`)

**User Story:** As a Seller, I want to create products and variant SKUs under my shop, while buyers browse active listings, so that pricing is exact and competitors cannot alter my catalog.

#### Acceptance Criteria
1. **3.1 (`REQ-01`):** WHEN a seller creates or modifies a product or SKU (`POST/PATCH /api/v1/catalog/shops/{shop_id}/...`), THE `catalog` module SHALL enforce JWT `shop_id` ownership (`current_user.shop_id == shop_id`) AND verify the target product/SKU belongs to `shop_id`, rejecting any cross-shop mutation with HTTP `403 FORBIDDEN`.
2. **3.2:** WHEN a seller submits a SKU with integer `price_cents > 0` and `stock_qty >= 0`, THE `catalog` module SHALL persist the SKU and return HTTP `201` (create) or `200` (update).
3. **3.3:** IF a SKU payload provides a `float` (including `19.99` or `19.0`), `bool`, or non-positive `price_cents <= 0`, or negative `stock_qty < 0`, THEN THE `catalog` module SHALL reject the payload with HTTP `422 UNPROCESSABLE ENTITY` and write zero records.
4. **3.4:** WHEN a buyer queries `GET /api/v1/catalog/products` or `GET /api/v1/catalog/products/{product_id}`, THE `catalog` module SHALL return active products and SKUs with integer `price_cents` (returning `404 NOT FOUND` for missing products).

---

### Requirement 4: Gemini Semantic Product Discovery (`ai_search`)

**User Story:** As a Buyer, I want to search products using natural language, so that I find relevant items across seller shops even when my query describes intent or budget rather than exact SKU titles.

#### Acceptance Criteria
1. **4.1:** WHEN a buyer submits `POST /api/v1/ai-search/search` with a natural-language `query`, THE `ai_search` module SHALL sanitize and wrap the query in `<user_input>...</user_input>` XML delimiters, extract a validated `SemanticSearchIntent`, and return ranked matching products with integer `min_price_cents`.
2. **4.2:** IF `GEMINI_API_KEY` is unset or `AI_PROVIDER` is configured for offline/mock mode, THEN THE `ai_search` module SHALL execute deterministic local intent extraction without network errors while preserving the exact `AISearchResponse` contract.
3. **4.3:** IF an input contains prompt-injection attempts or exceeds token limits (`> 500` chars), THEN THE `ai_search` module SHALL truncate oversized queries, treat `<user_input>` strictly as untrusted data, and enforce Pydantic v2 schema bounds on all returned results.

---

## 3. API & Entrypoint Locations

- **FastAPI App Composition Root:** `apps/api-python/app/main.py`
- **Core Infrastructure:** `apps/api-python/app/core/{config,security,contracts,ai_client}.py`
- **Domain Modules:** `apps/api-python/app/modules/{auth,shops,catalog,ai_search}/`
- **Design Reference:** Backend API feature (no `[FE]` mobile/web UI in Wave 1).

---

## 4. Non-Goals (Out of Scope for This Feature)

- **NG1:** Do NOT implement shopping cart, voucher stacking, or checkout (deferred to `02-multi-shop-cart-and-vouchers`).
- **NG2:** Do NOT modify `apps/engine-rust/` or `apps/mobile-kotlin/` (deferred to Waves 3 & 4).
- **NG3:** Do NOT build live video streaming commerce or 3PL fleet routing (`AGENTS.md` Anti-Hallucination List).

---

## 5. 📝 Revision History

| Rev | Date | Changes (Added / Changed / Removed) | Reason / User Feedback |
| :--- | :--- | :--- | :--- |
| `v1.0` | `2026-11-15` | Expanded starter `REQ-01` into full EARS specification for `auth`, `shops`, `catalog`, and `ai_search`. | Prepared via `/spec` Mode A before `/build 01-auth-and-seller-shops`. |
