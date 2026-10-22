# Progress Log — rainrs-server

> The programmer appends one entry per work session, newest at the
> bottom. The architect can read this to review what happened without
> re-reading code.
>
> Scope: `rainrs-collection/rainrs-server` only. Repository-level
> sessions are logged at the root in `agent/PROGRESS.md`.

## Entry template

<!--
### YYYY-MM-DD — Session <n>
- **Tasks touched:** S-001, S-002
- **What was done:** Summary of changes (files created/modified, commands run).
- **Test results:** pass/fail, coverage notes, or "n/a".
- **Blockers:** anything preventing further progress.
- **Next steps:** what the programmer expects to pick up next.
-->

---

### 2026-10-19 — Session 1
- **Tasks touched:** none in `agent/TASKS.md` (direct architect instruction; layout confirmed by architect).
- **What was done:** Scaffolded the confirmed initial project layout (recorded in `docs/decisions/0001-rainrs-server-initial-layout.md` at the repository root). Installed `uv 0.13.2` to `~/.local/bin` (no sudo, same pattern as `gh`). Created `pyproject.toml` (hatchling build backend; project `rainrs-server`, package `rainrs_server`, src layout; dev group: pytest/ruff/mypy; tool config for pytest, ruff, mypy in the same file), `.python-version`, `src/rainrs_server/__init__.py`, `tests/test_smoke.py`, `docs/README.md`. Ran `uv sync` → `uv.lock` generated (13 packages). Found the system Python 3.14 at `/usr/local/bin/python3.14` lacks `_sqlite3` (crashes mypy's metastore); installed uv-managed CPython 3.14.8 and rebuilt the venv on it. Updated `AGENTS.md` (layout section now confirmed; environment note added), `README.md` (status + commands), and `agent/PLAN.md` (tech stack filled; decision logged).
- **Test results:** `uv run pytest` → 1 passed; `uv run ruff check .` → all checks passed; `uv run ruff format --check .` → 8 files already formatted; `uv run mypy` → success, no issues in 2 source files. All run on Python 3.14.8.
- **Blockers:** none.
- **Next steps:** Architect to draft the functional design in `agent/PLAN.md` (goals, API style, interfaces/contracts section); then break work into `S-###` tasks in `agent/TASKS.md`.

---

### 2026-10-22 — Session 2
- **Tasks touched:** S-001, S-002 (Yolo26 model integration), S-002 (Runge–Kutta integration), S-003.
- **What was done:**
  - **S-001 — Git preparation.** Fetched `origin`, confirmed `dev` was already at `origin/dev` (`04fc7ed`), created and switched to `feat/image_process` from `dev`, and extended the root `.gitignore`: all common image extensions (`*.jpg`, `*.jpeg`, `*.png`, `*.bmp`, `*.tif`, `*.tiff`, `*.webp`, `*.gif`, `*.heic`) are ignored globally, curated fixtures under `rainrs-collection/rainrs-server/tests/fixtures/` are re-included, and the server runtime artefacts (SQLite database, log files, derived feature documents, the redundant `last.pt` checkpoint) are excluded. Verified with `git check-ignore -v`.
  - **S-002 (detection) — `src/rainrs_server/process/image_read.py`.** Added `RainRippleDetector` (Ultralytics YOLO26, weights loaded once and reused), the `RippleDetector` protocol (so the test suite runs without torch), and `RippleFeatureExtractor` (`extract` / `process_image` / `process_directory`). Supporting modules: `models.py` (shared dataclasses), `config.py` (`ServerPaths`, `DetectionSettings`, `resolve_key_bits`), `logging_setup.py` (rotating file log), `storage/database.py` (SQLite schema) and `process/dev.py` (single choke point for the removable development printing). Real run over the ten sample captures: **`processed=10 no_features=0 errors=0`, 37 ripples**; all captures moved to `storage/images/processed`, ten JSON attribute documents written to `storage/features/`, rows written to the `images` and `ripples` tables, log written to `logs/rainrs.log`. The two failure paths were verified separately: the no-feature branch with `conf=0.95` (capture deleted, status `no_features`) and the error branch with a corrupt capture (error logged, status `error`, capture kept in `raw/`, CLI exit code 1). A failed capture never aborts the batch.
  - **S-002 (derivation) — `src/rainrs_server/process/rungge.py`.** Added the RK4 core (`rk4_step`, `rk4_integrate` — dt 0.01, 4000 steps, every 10th state sampled), the ODE system (`RippleWaveSystem`: two coupled van der Pol oscillators whose parameters are derived from the ripple geometry), `derive_master_key` (averaged position/radius/count → RK4 → SHA-256 digest truncated to 32/64 bit), `derive_slave_keys` (one key per ripple) and the `KeyDeriver` façade. Real run: **10 master keys and 37 slave keys** stored; every slave row carries the `master_key_id` foreign key identifying its master, and `master_keys.image_id` is `UNIQUE`, so exactly one master key can exist per capture.
  - **S-003 — documentation.** Wrote `tools/build_documentation.py`, which renders five diagrams with matplotlib and assembles them into `docs/rainrs-server-documentation.docx` (845 KB, 11 sections, 3 tables, 5 embedded images): component, activity, class, sequence and entity relationship diagram, plus the overview, storage layout, CLI reference, security considerations, known limitations and the verification results.
  - **Decision record.** Added `docs/decisions/0002-rainrs-server-pipeline.md` at the repository root, recording the CPU-only torch pinning, the HMAC-SHA256 slave-key binding (and why a plain XOR was rejected), and the deterministic-derivation caveat.
  - **Branch and review.** The work was committed on `feat/image_process` in four focused commits (`.gitignore`, the pipeline, the `.docx` report, the decision records and the agent tracking), pushed to `origin`, and opened as pull request **#2** into `dev` (https://github.com/Fauzst/RainRippleV3/pull/2, 40 files, +7130/−0, not a draft).
- **Test results:** `uv run pytest` → **50 passed**; `uv run ruff check .` → all checks passed; `uv run ruff format --check .` → 30 files already formatted; `uv run mypy` → success, no issues in 19 source files. The five rendered diagrams were additionally checked programmatically (text-to-text overlap and text-crosses-border): **0 overlaps and 0 border crossings** in every diagram. The log file was grepped for hex strings and feature fields: no key material and no feature values are logged.
- **Blockers:** none.
- **Notes / decisions:**
  - `torch` and `torchvision` are pinned to the PyTorch **CPU** wheel index (`[tool.uv] index pytorch-cpu` + `[tool.uv.sources]`). They had to be declared as *direct* dependencies for uv to honour the source; the reference host has no CUDA device. This shrank the virtual environment from 5.8 GB to 1.4 GB (torch 2.14.1+cpu, torchvision 0.29.1+cpu). CPU inference costs ≈ 6.7 s per 200×113 px capture, including warm-up.
  - The slave keys are bound to their master key with **HMAC-SHA256** by default instead of the plain XOR suggested in the task: a XOR lets two equal inputs cancel out and does not separate the child key from the parent. The XOR variant remains available as `--binding xor` so the original idea can be reproduced and compared.
  - The derivation is **deterministic**: the same capture always yields the same key. The unpredictability of the artifact comes from the physical capture, not from the algorithm — an attacker who knows the capture can recompute the key. The outputs are experimental 32/64-bit research artifacts and are documented as unsuitable for production encryption.
- **Next steps:** The architect to review `agent/PLAN.md` for the still-undecided API surface (the pipeline currently has a CLI only) and to define the shared contracts under `shared/contracts/` and `shared/schemas/` at the repository root.

---

### 2026-10-22 — Session 3
- **Tasks touched:** S-004 (Add Data Model).
- **What was done:**
  - **The MVC split.** The package was restructured into
    `model/` / `input/` / `process/` / `output/`:
    - `model/base.py` — `JsonObject`, `Serialisable`, `utc_now_iso()`;
    - `model/detection.py` — `RippleDetection`, `DetectionResult`,
      `RippleAttributes` (+ `with_storage()`);
    - `model/keys.py` — `MasterKey` (+ `with_image_id()`), `SlaveKey`
      (+ `with_master_key_id()`);
    - `model/outcome.py` — `ImageOutcome` and the `STATUS_*` constants;
    - `model/state.py` — `Vector`, `Derivative`,
      `RippleWaveParameters`, `Trajectory` (moved out of
      `process/rungge.py`, re-exported there for API stability);
    - `model/schema.py` — the declarative catalogue of the model;
    - `input/captures.py` — `CaptureLibrary` (list / archive / discard)
      and `is_supported_image`;
    - `output/attributes.py` — `AttributeWriter` (the JSON documents);
    - `output/database.py` — the SQLite schema and persistence, moved
      from `storage/`.
    `models.py` and the `storage/` package were removed without a
    compatibility shim. The dependency direction is one-way: `input`
    and `output` know the model, `process` knows the model and both
    sides, and the model knows nothing else.
  - **The data model as a catalogue.** `model/schema.py` holds
    `Field(name, type, description, nullable)`,
    `Entity(name, description, table, fields)`, the `SCHEMA` tuple and
    the `ENTITY_CLASSES` registry. `verify()` compares the catalogue
    with the dataclasses field by field (the raw `__annotations__` are
    compared, `Optional[X]` is folded into `X | None`); the new test
    `tests/model/test_schema.py` calls it, so a field that was added,
    renamed or retyped without updating the catalogue fails the build.
    The same catalogue generates the data model diagram and the
    per-entity schema tables of the documentation.
  - **The stages own their collaborators.**
    `RippleFeatureExtractor` no longer reaches for the filesystem or
    for SQLite: it receives the detector, the capture library and the
    attribute writer, and the CLI builds them.
  - **Tests.** `tests/storage/test_database.py` moved to
    `tests/output/test_database.py`; new tests for the model
    (`tests/model/test_model.py`), the catalogue
    (`tests/model/test_schema.py`), the input layer
    (`tests/input/test_captures.py`) and the attribute writer
    (`tests/output/test_attributes.py`).
  - **Documentation.** `tools/build_documentation.py` was extended:
    the class diagram now shows the four layers, a new **data model
    diagram** was added (generated from the catalogue) and section 7 of
    the document describes the model with one table per entity (field,
    type, nullable, description). `docs/rainrs-server-documentation.docx`
    was regenerated (12 sections, 11 tables, 6 diagrams). The READMEs
    (`README.md`, `src/rainrs_server/README.md`, `docs/README.md`) were
    updated for the new layout and `agent/PLAN.md` describes the layers
    and the data flow.
  - **Decision record.** Added
    `docs/decisions/0003-rainrs-server-mvc-data-model.md` at the
    repository root, recording the split, the declarative catalogue, the
    injected collaborators and the frozen-dataclass copy helpers.
- **Test results:** `uv run pytest` → **79 passed**;
  `uv run ruff check .` → all checks passed;
  `uv run ruff format --check .` → 43 files already formatted;
  `uv run mypy` → success, no issues in 32 source files.
  *Behaviour preservation:* a real run over the ten sample captures into
  a temporary home gave `processed=10 no_features=0 errors=0` and
  `derived_master_keys=10`; the derived master and slave keys are
  **byte-identical** to the ones in the pre-refactor database (compared
  programmatically — no key material was printed). The log of that run
  contains no key material and no feature values.
  *Diagrams:* all six rendered diagrams were checked programmatically —
  **0 texts leaving their frame, 0 label overlaps, 0 arrow crossings**.
- **Blockers:** none.
- **Notes / decisions:**
  - The catalogue deliberately duplicates the dataclass definitions: it
    adds the *meaning* of a field, which a dataclass cannot carry. The
    duplication is kept in check by `verify()` and the test suite.
  - The frozen model classes get `with_*` copy helpers instead of being
    reconstructed field by field.
  - The documentation is generated from the catalogue, so the document
    and the code cannot drift apart.
- **Next steps:** The work was committed on `feat/image_process` in two commits (`44a940d` the MVC split, `2f0832f` the documentation) and pushed to `origin`; pull request **#2** (into `dev`) was updated with the new scope and the verification results. The architect to note that `dev` is behind `prod` — PR #1 landed the scaffold on `prod` while `dev` is still at the baseline `04fc7ed` — so a `dev` → `prod` sync is needed before this work reaches `prod`. The API surface of the server remains undecided (`agent/PLAN.md`), as do the shared contracts under `shared/contracts/` and `shared/schemas/`; no statistical evaluation of the derived material exists yet (no entropy estimate, no NIST SP 800-22 run).


