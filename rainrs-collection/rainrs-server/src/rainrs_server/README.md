# `rainrs_server`

The application package of `rainrs-server` (src layout — the package
is imported from the installed distribution, never from the working
directory).

```
rainrs_server/
  __init__.py          package metadata and the public API
  __main__.py          `python -m rainrs_server` entry point
  cli.py               the command line interface (process / derive / run)
  config.py            filesystem layout, detector settings, key sizes
  logging_setup.py     the rotating file logger
  models.py            the dataclasses shared between the two stages
  process/
    __init__.py
    dev.py             the development-only console printing
    image_read.py      stage 1: detection and feature extraction
    rungge.py          stage 2: Runge-Kutta master and slave key derivation
  storage/
    __init__.py
    database.py        the SQLite schema and the persistence helpers
```

## Module boundaries

- `models.py` is the contract between the two stages. `RippleAttributes`
  is the input of the derivation and the output of the extraction.
- `config.py` derives every path from a single server root, so the
  detector, the database layer and the CLI always agree on where the
  data lives. `RAINRS_HOME` overrides the root.
- `process/image_read.py` owns the detection stage and knows nothing
  about key derivation.
- `process/rungge.py` owns the derivation stage and reads the stored
  attributes from the database.
- `process/dev.py` is the single place where development output is
  produced, so the console printing can be removed with one edit.
- `storage/database.py` is the only module that touches SQLite.

## Conventions

- Every module starts with a docstring that states its inputs and its
  outputs.
- The heavy imports (`ultralytics`, `torch`) happen inside the
  functions that need them, so `--help` stays fast and the test suite
  runs without the neural network. The detector is injected through the
  `RippleDetector` protocol for exactly that reason.
- Timestamps are UTC in ISO 8601 format (`utc_now_iso`).
- Errors are logged with `logger.error`; the CLI turns a failed capture
  into a non-zero exit code instead of raising.

## Tests

The test suite mirrors this structure in `tests/`
(`tests/process/`, `tests/storage/`) and imports the installed package.
