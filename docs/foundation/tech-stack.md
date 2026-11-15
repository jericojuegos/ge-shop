# 🧰 Tech Stack — GE Shop (`ge-shop`)

- **Core Marketplace API (`apps/api-python/`):** Python 3.12+, `uv`, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async SQLite/Postgres), Pytest, Ruff.
- **High-Concurrency Engine (`apps/engine-rust/`):** Rust 2021+, Cargo, `axum`, `tokio`, `serde`, atomic lock-free/transactional stock pools.
- **Mobile Client (`apps/mobile-kotlin/`):** Kotlin 2.x, Jetpack Compose, Material 3, Coroutines/StateFlow, JUnit 5.
- **AI Ecosystem:** Google Gemini (`AI_PROVIDER=google`) with offline mock evaluation mode (`test_ai_eval.py`).