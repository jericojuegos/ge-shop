# Tasks: `00-scaffold` (GE Shop Polyglot Monorepo)

- [x] **T01:** Initialize `apps/api-python/` with `uv`, FastAPI, Pydantic v2, SQLAlchemy, Pytest, Ruff, and `/health` endpoint.
- [x] **T02:** Initialize `apps/engine-rust/` with `Cargo.toml` (`axum`, `tokio`, `serde`) and pure Rust `Money` / `StockPool` invariant unit tests (`cargo test`).
- [x] **T03:** Initialize `apps/mobile-kotlin/` Gradle project structure with pure-Kotlin `domain/model/` (`Money`, `CartGroup`) and unit tests.
- [x] **T04:** Add root `.gitignore` and CI workflow verifying Python, Rust, and Kotlin unit suites.

---

## 🧪 Feature Verification & UAT Gate
- [x] **V01:** Execute `/verify` (`docs/specs/00-scaffold/uat.md`) across Python, Rust, and Kotlin workspaces.

## 📝 Feature Activity Log
- `2026-11-15`: Completed `T01`–`T04` for `00-scaffold` (Python FastAPI + `MoneyCents` + `/health`, Rust `Money` + atomic `StockPool` + Axum, Kotlin `:core` + `:app` + `Money`/`CartGroup` + manifest permission guard, root `.gitignore`, and `.github/workflows/ci.yml`).