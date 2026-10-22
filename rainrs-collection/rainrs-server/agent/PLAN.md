# Plan — rainrs-server

> Authored by: Joshua Elijah L. Pura
> Status: Draft
> Scope: `rainrs-collection/rainrs-server` only. Repository-wide plan
> lives at the root in `agent/PLAN.md`.

## Overview

<!-- What does the server do? One or two paragraphs describing its
     role in the Rain Ripple Key Generator pipeline: what it receives,
     what it computes, what it exposes, and to whom. -->

## Goals

<!-- Bullet list of goals this application must achieve. -->

- [ ] Goal 1

## Non-Goals

<!-- What is explicitly out of scope for the server. -->

## Architecture

<!-- High-level design: components, data flow, API style, storage. -->

### Tech Stack

- Language: Python 3.14.x (uv-managed CPython 3.14.8)
- Toolchain: uv (hatchling build backend; `uv.lock` committed)
- Key dependencies: none at runtime yet; dev group: pytest, ruff, mypy

### Components

The package is a simple MVC split. The model describes the data, the
input layer brings the data in, the process layer computes with it and
the output layer stores the result. The dependency direction is
one-way: `input` and `output` know the model, `process` knows the
model and both sides, and the model knows nothing else.

| Layer | Package | Responsibility |
|---|---|---|
| Model | `rainrs_server.model` | The dataclasses of the pipeline (`RippleDetection`, `DetectionResult`, `RippleAttributes`, `MasterKey`, `SlaveKey`, `ImageOutcome`, the ODE state types) and the catalogue `model/schema.py` that names every field, its type and its meaning. The catalogue is verified against the dataclasses by the test suite. |
| Input | `rainrs_server.input` | The incoming captures: `CaptureLibrary` (list, archive, discard) and `is_supported_image`. |
| Process | `rainrs_server.process` | Stage 1 (`image_read.py`: detection and feature extraction) and stage 2 (`rungge.py`: Runge–Kutta master and slave key derivation). `dev.py` holds the development-only printing. |
| Output | `rainrs_server.output` | The JSON attribute documents (`attributes.py`) and the SQLite persistence (`database.py`). |

Data flow of one capture:

```
input/captures.py  ->  process/image_read.py  ->  model/RippleAttributes
                                              ->  output/attributes.py  (JSON document)
                                              ->  output/database.py    (images, ripples)
                                              ->  input/captures.py     (archive / discard)
model/RippleAttributes  ->  process/rungge.py  ->  model/MasterKey, model/SlaveKey
                                              ->  output/database.py    (master_keys, slave_keys)
```

## Interfaces and Contracts

<!-- Define before implementing any externally consumed interface.
     See root AGENTS.md section 6 and this app's AGENTS.md section 7. -->

- API style: <!-- e.g. REST/JSON, RPC — undecided -->
- Timestamp format: <!-- UTC / ISO 8601 — undecided -->
- Error format: <!-- undecided -->
- Shared schemas: `shared/schemas/` (root) — owner and compatibility policy apply.

## Milestones

| # | Milestone | Description | Target |
|---|-----------|-------------|--------|

## Open Questions

<!-- Questions the architect wants answered before or during implementation. -->

- [ ] Question 1

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-10-19 | Initial project layout confirmed: src layout, package `rainrs_server`, uv + hatchling, dev group (pytest/ruff/mypy), `.python-version` pins uv-managed CPython 3.14.8 | Architect approval; see `docs/decisions/0001-rainrs-server-initial-layout.md` |
| 2026-10-22 | Capture pipeline implemented: YOLO26 detection stage + Runge–Kutta master/slave key derivation, stored in SQLite; CPU-only torch wheels; slave keys bound to the master key with HMAC-SHA256 (XOR kept as an option); derived material documented as deterministic experimental research material | Implementation of S-001 … S-003; see `docs/decisions/0002-rainrs-server-pipeline.md` |
| 2026-10-22 | The package is split into a simple MVC (model / input / process / output); the model is declarative — `model/schema.py` catalogues every entity and field and is verified against the dataclasses by the test suite; `models.py` and `storage/` were removed | Implementation of S-004; see `docs/decisions/0003-rainrs-server-mvc-data-model.md` |
