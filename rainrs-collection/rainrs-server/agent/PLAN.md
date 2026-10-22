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

<!-- Describe major components/modules and how they interact. -->

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
