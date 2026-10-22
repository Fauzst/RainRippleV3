# AGENTS.md — rainrs-server

Application-level agent instructions for the Rain Ripple Key Generator
server component. The repository-root `AGENTS.md` always takes
precedence; this file adds server-specific rules and context.

Read the root `AGENTS.md` (repository root) before working here.

## 1. Scope and Role

`rainrs-server` is the server component of the Rain Ripple Key
Generator research project. Its role within the multi-app repository
(see `docs/architecture.md` and `rainrs-collection/README.md`) is to
provide the shared backend services consumed by the desktop, mobile,
and website applications, and to interface with the embedded system.

Responsibilities are still being defined by the architect. Until the
server design is recorded in `agent/PLAN.md`, treat all functional
requirements as undecided and confirm scope before implementing
endpoints or data flows.

## 2. Technology Stack

- Language: Python 3.14.x (subject to verified dependency
  compatibility — see the root `AGENTS.md`).
- Package manager: `uv`. The virtual environment and dependency
  resolution are managed exclusively through `uv`.
- Lockfile: `uv.lock` — committed to version control, never edited by
  hand.
- No other package manager (pip, poetry, conda, ...) may be used
  inside this application.

Tooling (configured in `pyproject.toml`, installed as dev
dependencies; check existing manifests before adding more):

- Tests: `pytest`
- Lint / format: `ruff`
- Type checking: `mypy`

Environment note: the system Python 3.14 at `/usr/local/bin/python3.14`
is built without `_sqlite3`, which crashes mypy. The project venv uses
uv-managed CPython 3.14.8 (pinned via `.python-version`), which is
complete. Do not point the venv at the system interpreter.

## 3. Commands

Run all commands from `rainrs-collection/rainrs-server/`. All four
checks (pytest, ruff check, ruff format --check, mypy) must pass
before a task is marked `DONE`.

- Sync dependencies: `uv sync`
- Run tests: `uv run pytest`
- Run focused tests: `uv run pytest tests/<path>`
- Lint: `uv run ruff check .`
- Format check: `uv run ruff format --check .`
- Type check: `uv run mypy src`

## 4. Project Layout

Confirmed by the architect on 2026-10-19 (see
`docs/decisions/0001-rainrs-server-initial-layout.md` at the
repository root, and the `agent/PLAN.md` decision log):

```
rainrs-server/
  AGENTS.md          # this file
  README.md          # setup and usage documentation
  pyproject.toml     # project metadata, dependencies, tool config
  uv.lock            # committed lockfile
  .python-version    # pins the uv-managed Python interpreter
  src/rainrs_server/ # application package (src layout)
  tests/             # test suite (mirrors src/ structure)
  agent/             # PLAN.md, TASKS.md, PROGRESS.md
  docs/              # server-specific documentation
  model/             # Yolo 26 model
  storage/           # Use for storing images and data
  logs/              # Use for logging of events in rainrs-server
```

Rules:

- The package name is `rainrs_server` (import name); the distribution
  name is `rainrs-server`.
- Use the src layout: application code lives under
  `src/rainrs_server/`; tests import the installed package, never via
  `sys.path` hacks.
- Mirror the `src/` structure inside `tests/` (e.g.
  `src/rainrs_server/api/` → `tests/api/`).
- Build backend is hatchling (declared in `pyproject.toml`); do not
  remove `[build-system]`, or uv will stop installing the package
  into the venv and imports will break.

## 5. Agentic Workflow

This application follows the planning workflow defined in the root
`AGENTS.md` (section 7), with per-application tracking in `agent/`:

- `agent/PLAN.md` — the architect's design: goals, non-goals,
  architecture, tech stack decisions, milestones, open questions.
- `agent/TASKS.md` — task breakdown with statuses and acceptance
  criteria. The architect defines tasks; the programmer updates
  statuses and checks off criteria.
- `agent/PROGRESS.md` — session log. Append one entry per work
  session, newest at the bottom.

Rules:

1. Read `agent/PLAN.md` and `agent/TASKS.md` before starting work in
   this application.
2. Work on one task at a time unless tasks are demonstrably
   independent.
3. Update `agent/PROGRESS.md` at meaningful checkpoints with what was
   done, verification results, blockers, and next steps.
4. Do not mark a task `DONE` until its acceptance criteria pass and
   the relevant checks have actually been executed.
5. Never report an unexecuted test as passing.

## 6. Server-Specific Security Rules

In addition to the root security rules:

- Never log captured ripple images, derived features, or generated
  key material — not in application logs, request logs, error
  reports, or test output.
- Validate all externally received data (HTTP payloads, file uploads,
  sensor data from the embedded system) before use; reject malformed
  input with explicit errors.
- Do not persist raw captures or key material beyond what a task
  explicitly requires, and never commit them (see root `.gitignore`).
- Rate-limit and authenticate endpoints that expose the key-generation
  pipeline once the API design is approved.
- Statistical randomness is not cryptographic security (root
  `AGENTS.md`, Security Boundaries); the server must not present
  generated outputs as production-grade keys in any user-facing
  response or documentation.

## 7. Cross-Platform Contracts

The server participates in the repository's cross-platform contracts
(root `AGENTS.md`, section 6):

- Shared schemas and API contracts live in `shared/contracts/` and
  `shared/schemas/` at the repository root; their owner and
  compatibility policy apply here.
- Any change to externally consumed endpoints or payload schemas must
  be coordinated with the desktop, mobile, website, and embedded
  consumers, versioned when compatibility requires it, and covered by
  serialization/validation tests.
- Define units, coordinate systems, timestamp formats (UTC, ISO 8601
  unless the architect decides otherwise), and error formats in
  `agent/PLAN.md` before implementing interfaces.

## 8. Documentation

- Record the API surface, configuration, environment variables, and
  data-handling methodology in this application's `README.md` (or
  `docs/` when it grows) as they are implemented.
- Document implemented behavior only — never describe intended
  behavior that has not been verified.
- Material architectural decisions must be recorded in
  `docs/decisions/` at the repository root with a cross-reference
  from `agent/PLAN.md`.
