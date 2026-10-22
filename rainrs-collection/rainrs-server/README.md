# rainrs-server

Server component of the **Rain Ripple Key Generator** — a research
project exploring the generation of experimental key material from
captured rain ripple images. See the repository root `AGENTS.md` and
`docs/architecture.md` for the project-wide context and security
boundaries.

> **Status: pipeline implemented.** The capture-processing pipeline
> (YOLO26 detection → Runge–Kutta key derivation) is implemented,
> tested and documented; the API surface is still undecided and lives
> in `agent/PLAN.md`. Python 3.14 is pinned via `.python-version` and
> resolved by uv (do not use the system interpreter — see `AGENTS.md`,
> section 2).

## What it does

The server turns captured rain-ripple images into experimental key
material in two stages.

1. **Feature extraction** (`src/rainrs_server/process/image_read.py`) —
   every capture in `storage/images/raw/` is passed through the trained
   YOLO26 detector
   (`model/content/runs/detect/rain_ripple_yolo26_cpu/weights/best.pt`).
   For every detected ripple the centre position, the bounding box and
   the equivalent radius are measured, stored in the SQLite database and
   in a JSON attribute document. Captures with measurable ripples are
   moved to `storage/images/processed/`; captures without any ripple are
   deleted; failed captures stay in `raw/` so they can be retried.

2. **Key derivation** (`src/rainrs_server/process/rungge.py`) — the
   stored attributes feed a Runge–Kutta integration of a coupled
   oscillator system. The *averaged* attributes of a capture produce one
   **master key**; every *individual* ripple produces one **slave key**
   that is bound to its master key. All keys are written to the SQLite
   database.

## Tech Stack

- Language: Python 3.14.x (uv-managed CPython 3.14.8)
- Package manager: [uv](https://docs.astral.sh/uv/) — the only supported one
- Lockfile: `uv.lock` (committed)
- Runtime dependencies: `numpy`, `ultralytics`, `torch`, `torchvision`
- Dev dependencies: `pytest`, `ruff`, `mypy`, `matplotlib`, `python-docx`
- `torch`/`torchvision` are pinned to the PyTorch **CPU** wheel index —
  the reference host has no CUDA device.

## Setup

Run from this directory:

```bash
uv sync                 # install dependencies into .venv
```

The virtual environment is ~1.4 GB with the CPU-only torch wheels.

## Usage

```bash
# Stage 1: detect ripples and store the features
uv run python -m rainrs_server process
uv run python -m rainrs_server process --raw /path/to/raw --no-move

# Stage 2: derive the master and slave keys from the stored attributes
uv run python -m rainrs_server derive --bits 64
uv run python -m rainrs_server derive --bits 32 --binding xor

# Both stages in sequence
uv run python -m rainrs_server run --print
```

| Command | Effect |
|---|---|
| `process` | Detects ripples in `storage/images/raw/` and stores the features. |
| `derive` | Derives the master and slave keys from the stored attributes. |
| `run` | Runs the detection stage and the derivation stage in sequence. |
| `--print` | Enables the development console printing (stdout only). |
| `--no-move` | Keeps the captures in the raw directory (dry run). |
| `--keep-no-features` | Keeps captures for which no ripple was detected. |
| `--bits 32\|64` | Size of the generated research artifacts. |
| `--binding hmac\|xor` | Binding of the slave keys to their master key. |
| `--overwrite` | Re-derives keys for captures that already have a master key. |
| `--image-id N` | Restricts `derive` to one capture (repeatable). |

The exit code of `process` is `1` when at least one capture failed, so
the command can be used in a batch script.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `RAINRS_HOME` | detected server root | Overrides the root that all paths are derived from. |
| `RAINRS_DEV_PRINT` | unset | `1` enables the development console printing. |
| `RAINRS_LOG_LEVEL` | `INFO` | Log level of `logs/rainrs.log` (`DEBUG` … `CRITICAL`). |

The detector thresholds (`--conf`, `--iou`, `--imgsz`, `--device`) are
command line options; the defaults (`0.25`, `0.7`, `416`, `cpu`) match
the training run of the model.

## Development Commands

```bash
uv run pytest                  # run the full test suite
uv run pytest tests/process    # run a focused subset
uv run ruff check .            # lint
uv run ruff format --check .   # format check
uv run mypy                    # type check (src + tests, per pyproject.toml)
uv run python tools/build_documentation.py   # regenerate docs/*.docx
```

All four checks (pytest, ruff check, ruff format --check, mypy) must
pass before a task is marked `DONE`.

## Data Handling

- **Never logged.** The log file records file names, counters, statuses
  and timings only — no captures, no derived features and no key
  material. Feature values and keys are printed by
  `src/rainrs_server/process/dev.py` instead, which is development-only
  and stdout-bound.
- **Never committed.** `storage/rainrs.db`, `storage/features/*.json`,
  `logs/*.log` and every image file are excluded by the repository
  `.gitignore`.
- **Derived material is research material.** The generated 32/64-bit
  values are experimental artifacts, not production keys.

## Documentation

- `docs/rainrs-server-documentation.docx` — the full report with the
  component, activity, class, sequence and entity relationship diagrams
  (regenerate with `uv run python tools/build_documentation.py`)
- `AGENTS.md` — agent instructions for working in this application
- `agent/PLAN.md` — design draft, goals, architecture, open questions
- `agent/TASKS.md` — task breakdown and status
- `agent/PROGRESS.md` — per-session progress log
- `docs/decisions/` at the repository root — material decisions

## Security Note

This project produces **experimental 32–64-bit research artifacts**, not
production encryption keys. The derivation is deterministic: the same
capture always yields the same key, so the unpredictability comes from
the physical capture and not from the algorithm. Statistical randomness
(e.g. passing NIST SP 800-22) does not imply cryptographic security.
See the root `AGENTS.md`, section "Security Boundaries".
