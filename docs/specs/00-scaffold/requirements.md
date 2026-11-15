# Requirements: `00-scaffold` — GE Shop Polyglot Monorepo Scaffold

## 1. Overview
Initialize the polyglot monorepo workspaces for **GE Shop** (`apps/api-python/`, `apps/engine-rust/`, and `apps/mobile-kotlin/`), enforcing the `AGENTS.md` critical constraints (`Zero-Float Money Math`, `Atomic Flash-Sale & Stock Reservation`, and `Portable Kotlin Domain`) from Day 0, plus a root `.gitignore` and GitHub Actions CI gate.

## 2. Assumptions & Non-Goals
- **A1:** All monetary amounts across Python (`int`), Rust (`i64`), and Kotlin (`Long`) use 64-bit integer minor units (`price_cents`).
- **A2:** `apps/mobile-kotlin/` separates the pure-Kotlin `:core` (`domain/`) layer from the Android `:app` shell so domain unit tests run on the JVM without Android dependencies.
- **Non-Goals:** Full database migrations, JWT authentication, and multi-shop checkout orchestration belong to Waves 1–4 (`01`–`04`).

## 3. EARS Acceptance Criteria
- **Req 1.1:** WHEN `GET /health` is requested on `apps/api-python/`, THE SYSTEM SHALL return HTTP `200 OK` with `{"status": "ok", "service": "ge-shop-api-python", "money_unit": "cents_int64"}` and pass `uv run ruff check . && uv run pytest`.
- **Req 1.2:** WHEN `Money` or `StockPool` operations execute in `apps/engine-rust/`, THE SYSTEM SHALL enforce integer-cent arithmetic (`i64`) and atomic stock reservation with zero negative stock under concurrent access (`cargo check && cargo test`).
- **Req 1.3:** WHEN `Money` and `CartGroup` domain models execute in `apps/mobile-kotlin/`, THE SYSTEM SHALL compute shop subtotals and voucher clamping in `Long` cents with zero `android.*` or `androidx.*` imports in `:core` (`./gradlew testDebugUnitTest`).
- **Req 1.4:** WHEN repository changes are pushed or opened as a Pull Request on `main`/`master`, THE SYSTEM SHALL provide a root `.gitignore` and `.github/workflows/ci.yml` that verify the Python, Rust, and Kotlin test suites.

## 4. Revision History
- `2026-11-15`: Initial `00-scaffold` specification created during Phase 0 build.
