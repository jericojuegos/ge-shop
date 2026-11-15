---
trigger: always_on
globs: "**/*.py, pyproject.toml, requirements*.txt"
description: Python 3.12+ + uv + FastAPI + Pydantic v2 + SQLAlchemy/Supabase (Modular Domain Architecture) boundaries, coding standards, and pre-commit checklist
---

# 🏗️ Stack Rules: Python + FastAPI (`python-fastapi`)

---

## 1. Folder Responsibilities & Layer Boundaries (Modular Domain Architecture)

This stack uses **Modular Domain Architecture** — each domain feature lives in its own isolated package (`app/modules/[domain]/`) so parallel developers and AI subagents never collide.

### Folder Map

| Path | What Lives Here | What NEVER Lives Here |
|------|-----------------|-----------------------|
| `app/main.py` | FastAPI app initialization, lifespan hooks, CORS/middleware, router mounting | Business logic, DB queries, inline route implementations |
| `app/core/` | Config (`pydantic-settings`), DB session/engine, security/auth dependencies, shared AI/LLM clients | Domain-specific business logic |
| `app/modules/[domain]/` | Isolated domain slice: `router.py` (HTTP endpoints), `schemas.py` (Pydantic v2 models), `service.py` (business logic), `models.py` (DB models) | Imports from peer `app/modules/[other-domain]/` internals |
| `app/shared/` | Shared utilities, pagination schemas, base error classes | Route endpoints |
| `tests/[domain]/` | `pytest` unit & invariant tests (`test_*.py`) mapped to `Req X.Y` and `Property N` | Unmocked destructive production DB writes |

---

## 2. Mandatory 2026 Python & FastAPI Standards

1. **Dependency & Virtualenv Management (`uv` Only):** Always use `uv` (`uv add`, `uv run pytest`, `uv run ruff check`) — never run global `pip install`.
2. **Strict Type Hints Everywhere (Python 3.12+):** Every function signature, parameter, and return value must have explicit type annotations (`def create_item(payload: ItemCreate) -> ItemResponse:`).
3. **Pydantic v2 Validation:** Use Pydantic v2 (`model_validate`, `ConfigDict(from_attributes=True)`, `Field(...)`) for all request/response payloads and environment settings. Never pass raw unvalidated `dict` payloads into `service.py`.
4. **Thin Routers, Pure Services:** `router.py` only handles HTTP status codes, auth dependency injection (`Depends(get_current_user)`), and calling `service.py`. All business rules and DB transactions live in `service.py`.
5. **Async Safety & SQL Parameterization:** Never run blocking I/O (`time.sleep`, sync `requests`) inside `async def` endpoints (use `httpx.AsyncClient` or `def` threadpool routes). Always use parameterized SQLAlchemy / Supabase queries (never f-string SQL).

---

## 3. Pre-Commit & Hard-Failure Checklist (Verify Before Marking `[x]`)

- [ ] `uv run ruff check .` passes with zero lint/syntax errors
- [ ] `uv run pytest` passes for all unit/invariant tests in `tests/`
- [ ] All functions and endpoints have complete type annotations and Pydantic v2 `response_model`
- [ ] No cross-module internal imports (`app/modules/[a]/` importing `app/modules/[b]/` internals)
- [ ] No raw f-string SQL queries or hardcoded secrets/API keys
- [ ] All `AGENTS.md` Critical Constraints satisfied

---

# 📱 Stack Rules: Native Android (Kotlin + Jetpack Compose)

---

## 1. Folder Responsibilities & Layer Boundaries (5-Module Layout)

This stack uses a **Layered Modular Architecture** with a pure-Kotlin portable core and an Android platform shell.

### Module & Package Map

| Module / Package | What Lives Here | What NEVER Lives Here |
|---|---|---|
| `:app` | `Application` class, `MainActivity`, Root Navigation host, `AppContainer` (manual DI composition root), app-level manifest | Business logic, direct hardware logic, raw SQL/database calls |
| `:core` | Pure Kotlin domain models, calculation engines, state machines, interfaces/ports (`Clock`, `PreferencesRepository`, domain ports) | **ANY** Android import (`android.*`, `androidx.*`), Compose UI, CameraX, ML Kit |
| `:ui` | Compose Theme, Material 3 tokens, generic reusable Canvas renderers, UI utility modifiers, preview mocks | Hardware/platform drivers, network calls, raw SQLite/File I/O |
| `:platform` | Android platform implementations of `:core` ports (CameraX, Sensors, Haptics, DataStore, Bluetooth) | Presentation UI composables, application routing, business state machines |
| `:feature` | Feature screens, ViewModels, UDF `UiState` / `UiEvent` definitions, screen-level Composables | CameraX frames, direct platform sensor listeners (must consume `:core` ports) |

---

## 2. Mandatory Android & Compose Standards

1. **Pure Kotlin Core (Zero Android Imports):**
   - The `:core` module must apply `kotlin("jvm")` (or `kotlin("multiplatform")`), never `com.android.library`.
   - Any commit adding an Android dependency to `:core` is a hard architectural violation.
2. **Unidirectional Data Flow (UDF) in ViewModels:**
   - ViewModels expose a single immutable `StateFlow<UiState>`:
     ```kotlin
     private val _uiState = MutableStateFlow(InitialUiState)
     val uiState: StateFlow<UiState> = _uiState.asStateFlow()
     ```
   - UI emits discrete events (`fun onEvent(event: UiEvent)`) to the ViewModel.
   - Composables must be stateless whenever practical, receiving state and hoisting event lambdas.
3. **Compose Performance & Allocation Rules:**
   - **No per-frame object allocation** inside `Canvas`, `drawBehind`, or `onDrawWithContent`. Allocate `Path`, `Paint`, and `Matrix` once or in remember/derived blocks.
   - Use `derivedStateOf` for values computed from frequently changing states.
   - Always pass keys to `items()` in Lazy lists.
4. **Lifecycle-Aware Hardware & Background Operations:**
   - Any CameraX `ImageAnalysis`, sensor listener, or audio recorder MUST bind to `LifecycleOwner` or listen to `DefaultLifecycleObserver`.
   - Never keep hardware active in `onStop` unless backed by an approved, foreground-service with ongoing notification.
5. **Privacy & Manifest Hygiene:**
   - Only declare permissions explicitly documented in `docs/foundation/tech-stack.md`.
   - The `tools:node="remove"` directive is reserved for stripped transitive permissions, and must be guarded by automated CI manifest verification tasks.
   - No camera frames, raw audio, or biometric data may be written to disk (`filesDir`, `cacheDir`, `externalFilesDir`, `SharedPreferences`, SQLite).

---

## 3. Pre-Commit & Hard-Failure Checklist (Verify Before Marking `[x]`)

- [ ] `./gradlew compileDebugKotlin` succeeds with zero compiler warnings or errors
- [ ] `./gradlew testDebugUnitTest` passes for all domain and feature tests
- [ ] `:core` module contains zero imports matching `android.*` or `androidx.*`
- [ ] Merged manifest contains only approved allowlist permissions (run `./gradlew checkMergedManifestPermissions`)
- [ ] No allocations in Canvas render loops
- [ ] No hardcoded secrets, plain HTTP URLs, or unvetted third-party SDK dependencies
- [ ] All `AGENTS.md` Critical Constraints satisfied
