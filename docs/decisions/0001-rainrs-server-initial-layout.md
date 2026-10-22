# Decision 0001 — rainrs-server initial project layout

- **Date:** 2026-10-19
- **Status:** Accepted
- **Scope:** `rainrs-collection/rainrs-server`
- **Deciders:** Joshua Elijah L. Pura (architect)

## Context

`rainrs-server` was created as an empty directory in the initial
repository scaffold. Before any server code could be written, the
application needed a confirmed project layout, a package manager, and
a working test/lint/type-check toolchain, per the repository-root
`AGENTS.md`.

## Decision

Adopt the src-layout Python project structure confirmed by the
architect on 2026-10-19:

```
rainrs-server/
  AGENTS.md          # application-level agent instructions
  README.md          # setup and usage documentation
  pyproject.toml     # project metadata, dependencies, tool config
  uv.lock            # committed lockfile
  .python-version    # pins the uv-managed Python interpreter
  src/rainrs_server/ # application package (src layout)
  tests/             # test suite (mirrors src/ structure)
  agent/             # PLAN.md, TASKS.md, PROGRESS.md
  docs/              # server-specific documentation
```

Concretely:

- Distribution name `rainrs-server`, import package `rainrs_server`,
  src layout.
- Python `>=3.14`, pinned to the uv-managed CPython 3.14.8 via
  `.python-version`.
- `uv` is the only package manager; `uv.lock` is committed.
- Build backend: hatchling (`[build-system]` in `pyproject.toml`), so
  `uv sync` installs the package into the venv in editable mode.
- Dev tooling installed via the `dev` dependency group: `pytest`,
  `ruff`, `mypy`. Tool configuration lives in `pyproject.toml`.

## Consequences

- Positive: matches the root `AGENTS.md` stack (Python 3.14.x / uv),
  keeps the venv self-contained, and gives every agent a single
  verified command set (`uv sync`, `uv run pytest`, `uv run ruff
  check .`, `uv run ruff format --check .`, `uv run mypy`).
- Positive: src layout prevents accidental imports from the working
  directory, so tests exercise the installed package.
- Negative / risk: the system Python 3.14 at
  `/usr/local/bin/python3.14` is built without `_sqlite3` and crashes
  mypy; the project must always use the uv-managed interpreter.
- Note: no `__init__.py`-free namespace packages, no `docs/` build
  tooling yet; both can be revisited in `agent/PLAN.md` when needed.
