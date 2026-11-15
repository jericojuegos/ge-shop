# 🧠 GE Shop — Agent Brain (`AGENTS.md`)

**Project:** GE Shop — Multi-Vendor High-Concurrency Marketplace (Shopee/Lazada/Amazon archetype) Monorepo powered by Python FastAPI, Rust Flash-Sale Engine, and Kotlin Jetpack Compose Mobile.
**Context:** Personal / Public Flagship Portfolio & JutsuWorks Marketplace Suite
**Stack:** Python 3.12+ (`uv`, FastAPI, Pydantic v2, SQLAlchemy, Pytest) · Rust (`axum`, `tokio`, `sqlx`) · Kotlin 2.x (`Jetpack Compose`, `Coroutines/Flow`, Material 3)
**Architecture Pattern:** Polyglot Monorepo (`apps/api-python/`, `apps/engine-rust/`, `apps/mobile-kotlin/`) sharing a single OpenAPI & Domain Contract (`docs/specs/`)
**Master Brain:** `python-fastapi+android-kotlin-compose`
**Last synced:** `python-fastapi+android-kotlin-compose-v1.0` — 2026-11-15

---

## 🚦 Project State

**Stage:** `scaffolded`
**Stage last updated:** `2026-11-15`

| Stage | Meaning | Next Action / Skill |
|-------|---------|---------------------|
| `initialized` | Brain & specs ready, Phase 0 not built yet | Run **`/build`** on `docs/specs/00-scaffold/tasks.md` |
| `scaffolded` | `apps/api-python/`, `apps/engine-rust/`, and `apps/mobile-kotlin/` workspaces initialized | Run **`/spec`** or **`/build`** on Wave 1 features in `docs/planning/roadmap.md` |
| `active` | Feature wave development in progress | **`/spec`** → **`/build`** → **`/verify`** → **`/ship`** |

---

## ⚡ Deterministic Verification Commands

Run these commands after every task before marking `[x]`:
- **Python API (`apps/api-python/`):** `cd apps/api-python && uv run ruff check . && uv run pytest`
- **Rust Flash-Sale Engine (`apps/engine-rust/`):** `cd apps/engine-rust && cargo check && cargo test`
- **Kotlin Mobile App (`apps/mobile-kotlin/`):** `cd apps/mobile-kotlin && ./gradlew testDebugUnitTest`

---

## 🗺️ Context Map (`docs/INDEX.md`) & Skills (`.agents/skills/`)

| Question / Action | File or Skill |
|-------------------|---------------|
| What is the phased roadmap & feature dependency wave matrix? | [`docs/planning/roadmap.md`](docs/planning/roadmap.md) |
| Create or expand a feature spec (`requirements`, `design`, `tasks`, `uat`) | **`/spec`** ([`.agents/skills/spec/SKILL.md`](.agents/skills/spec/SKILL.md)) |
| Build Phase 0 scaffold or execute tasks/waves for a feature | **`/build`** ([`.agents/skills/build/SKILL.md`](.agents/skills/build/SKILL.md)) |
| Verify tests, EARS acceptance criteria, and stack Hard Failures | **`/verify`** ([`.agents/skills/verify/SKILL.md`](.agents/skills/verify/SKILL.md)) |
| Ship completed feature, update `roadmap.md`, and generate PR summary | **`/ship`** ([`.agents/skills/ship/SKILL.md`](.agents/skills/ship/SKILL.md)) |
| System foundations (`prd`, `architecture`, `tech-stack`, `design-system`, `decisions`) | [`docs/foundation/`](docs/foundation/) |
| Execution & wave protocol | [`.agents/rules/execution-protocol.md`](.agents/rules/execution-protocol.md) |
| Merged Stack Rules (`python-fastapi` + `android-kotlin-compose`) | [`.agents/rules/stack-rules.md`](.agents/rules/stack-rules.md) |

---

## ⚠️ Critical Constraints — Never Violate

- **Zero-Float Money Math:** All prices, shop vouchers, platform vouchers, shipping fees, and seller escrow payouts MUST use 64-bit integer minor units (`price_cents`: Python `int`, Rust `i64`, Kotlin `Long`).
- **Multi-Vendor Tenancy Guard:** Every seller write operation in `apps/api-python/` MUST verify that the authenticated seller owns the target `shop_id`.
- **Atomic Flash-Sale & Stock Reservation:** Flash-sale inventory pools in `apps/engine-rust/` and SKU stock reservations MUST execute atomically with zero negative stock under concurrent load.
- **Portable Kotlin Domain:** `apps/mobile-kotlin/` `domain/` layer must remain pure Kotlin (`kotlinx.coroutines.flow`) with zero `android.*` imports.

---

## 🚫 Anti-Hallucination List (Out of Scope for Phase 1)

Do NOT build in Phase 1:
- Live video streaming commerce (Shopee Live)
- Third-party logistics (3PL) fleet routing (belongs to `GE-Move`)