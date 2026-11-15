# 🧪 Feature UAT & Verification: GE Shop Polyglot Monorepo (`00-scaffold`)

> **Feature Slug:** `00-scaffold` · **Spec Links:** [`requirements.md`](./requirements.md) · [`design.md`](./design.md) · [`tasks.md`](./tasks.md)  
> **Overall Status:** `[x]` Verified PASS · **Verified Date:** `2026-11-15`

---

## Level 1 — Automated Terminal, Unit & E2E Checks (AI Executes)

- [x] **Python Build & Lint Check:** `cd apps/api-python && uv run ruff check .` passes with zero errors.
- [x] **Python Unit & Invariant Tests:** `cd apps/api-python && uv run pytest` passes (`3 passed` in `tests/test_health_and_money.py`).
- [x] **Rust Build & Unit Tests:** `cd apps/engine-rust && cargo check && cargo test` passes with zero warnings/errors (`3 passed` in `src/lib.rs`).
- [x] **Kotlin Compile, Unit Tests & Manifest Guard:** `cd apps/mobile-kotlin && ./gradlew compileDebugKotlin testDebugUnitTest checkMergedManifestPermissions` passes (`BUILD SUCCESSFUL`).
- [x] **Stack Hard-Failure Audit:** All items in `.agents/rules/stack-rules.md` (Pre-Commit Checklist) and `AGENTS.md` (Critical Constraints) pass (`:core` has zero `android.*` imports; all money values use 64-bit integer cents).

---

## Level 2 — Functional & EARS Requirement Verification (Deterministic Evidence)

| Check ID | Requirement Ref | Scenario (WHEN / IF) | Expected Outcome (THE System SHALL) | Evidence / Proof (`test:line`, CLI output, or `./evidence/*.png`) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UAT-1.1** | `Req 1.1` | `GET /health` requested on `apps/api-python/` | Returns HTTP `200 OK` with `{"status": "ok", "service": "ge-shop-api-python", "money_unit": "cents_int64"}` and `MoneyCents` rejects floats | `apps/api-python/tests/test_health_and_money.py:L13-L39` (`3 passed` via `uv run pytest`) | `[x]` |
| **UAT-1.2** | `Req 1.2` | `Money` and `StockPool` operations in `apps/engine-rust/` | Enforces integer-cent arithmetic (`i64`) and atomic CAS stock reservation with zero negative stock under 200-thread contention | `apps/engine-rust/src/lib.rs:L11-L78` (`3 passed` via `cargo test`) | `[x]` |
| **UAT-1.3** | `Req 1.3` | `Money` and `CartGroup` domain models in `apps/mobile-kotlin/` | Computes shop subtotals and clamps voucher discounts at `0L` in `Long` cents with zero `android.*` imports in `:core` | `apps/mobile-kotlin/core/src/test/kotlin/com/jutsuworks/geshop/domain/model/MoneyAndCartGroupTest.kt:L10-L56` (`./gradlew testDebugUnitTest PASS`) | `[x]` |
| **UAT-1.4** | `Req 1.4` | Repository root `.gitignore` and CI gate | `.gitignore` excludes build artifacts and `.github/workflows/ci.yml` runs Python, Rust, and Kotlin verification suites on PR/push | `.gitignore` & `.github/workflows/ci.yml:L1-L71` | `[x]` |

---

## Level 3 — Visual Fidelity (`design-reference/`), Evidence Pack & Human UX Sign-Off

- [x] **Design System Tokens:** `GeShopBrandTokens` (`#EA580C`, `#0D9488`, `#0F172A`) verified in `apps/mobile-kotlin/app/src/main/java/com/jutsuworks/geshop/ui/GeShopBrandTokens.kt`.
- [x] **Sign-Off:** Approved to mark `[x]` in `docs/planning/roadmap.md` via `/ship`.

---

## 🧭 Manual Testing Walkthrough (Step-by-Step Human QA)

### 1. Prerequisites & Local Setup
- **Python API:** `cd apps/api-python && uv run uvicorn app.main:app --reload --port 8000`
- **Rust Flash-Sale Engine:** `cd apps/engine-rust && cargo run` (binds `http://127.0.0.1:8081`)
- **Kotlin Mobile Suite:** `cd apps/mobile-kotlin && ./gradlew testDebugUnitTest checkMergedManifestPermissions`

### 2. Happy-Path Walkthrough (`Req 1.1–1.4`)
1. **Python API Health Check:** Visit `http://127.0.0.1:8000/health` (or run `cd apps/api-python && uv run pytest`) → Confirm HTTP `200 OK` with `{"status":"ok","service":"ge-shop-api-python","money_unit":"cents_int64"}`.
2. **Rust Engine Invariants:** Run `cd apps/engine-rust && cargo test` → Confirm all 3 unit/concurrency tests pass (`test_money_integer_cents_and_clamped_discounts`, `test_stock_pool_sequential_and_error_invariants`, `test_stock_pool_concurrent_contention_never_goes_negative`).
3. **Kotlin Domain & Manifest Guard:** Run `cd apps/mobile-kotlin && ./gradlew compileDebugKotlin testDebugUnitTest checkMergedManifestPermissions` → Confirm `Merged manifest permissions verified against allowlist` and all JUnit 5 tests pass.

### 3. Edge Cases & Error Validation
1. **Float Rejection in Python `MoneyCents`:** Passing `19.99` to `MoneyCents(amount_cents=19.99)` raises `TypeError`/`ValidationError`.
2. **Oversized Voucher Clamping in Rust & Kotlin:** Applying a discount larger than the item/shop subtotal clamps net payable cents to `0` (`0L` / `0_i64`) without underflowing into negative numbers.
