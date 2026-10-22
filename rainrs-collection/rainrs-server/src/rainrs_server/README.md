# `rainrs_server`

The application package of `rainrs-server` (src layout — the package
is imported from the installed distribution, never from the working
directory).

The package is a simple MVC split: the **model** describes the data,
the **input** layer brings the data in, the **process** layer computes
with it and the **output** layer stores the result.

```
rainrs_server/
  __init__.py          package metadata and the public API
  __main__.py          `python -m rainrs_server` entry point
  cli.py               the command line interface (process / derive / run)
  config.py            filesystem layout, detector settings, key sizes
  logging_setup.py     the rotating file logger
  model/               M - the data model (single source of truth)
    __init__.py        re-exports of the model types
    base.py            JsonObject, Serialisable, utc_now_iso()
    detection.py       RippleDetection, DetectionResult, RippleAttributes
    outcome.py         ImageOutcome and the status constants
    keys.py            MasterKey, SlaveKey
    state.py           Vector, Derivative, RippleWaveParameters, Trajectory
    schema.py          the field catalogue (SCHEMA) and its verification
  input/               I - everything that enters the pipeline
    __init__.py
    captures.py        CaptureLibrary, is_supported_image
  process/             P - the two stages of the pipeline
    __init__.py
    dev.py             the development-only console printing
    image_read.py      stage 1: detection and feature extraction
    rungge.py          stage 2: Runge-Kutta master and slave key derivation
  output/              O - everything that leaves the pipeline
    __init__.py
    attributes.py      the JSON attribute documents
    database.py        the SQLite schema and the persistence helpers
```

## Module boundaries

- `model/` is the contract between the layers. `RippleAttributes` is
  the input of the derivation and the output of the extraction;
  `MasterKey` and `SlaveKey` are the output of the derivation; the
  `ImageOutcome` describes what happened to one capture.
- `model/schema.py` is the **catalogue** of the model: it names every
  entity, every field, its type and its meaning. The catalogue is
  verified against the dataclasses by the test suite, so it cannot
  drift away from the code. It is also the source of the data model
  diagram and of the schema tables in the documentation.
- `input/captures.py` owns the incoming files: listing the captures,
  archiving a processed one and discarding a capture without features.
- `output/attributes.py` and `output/database.py` own the outgoing
  data: the JSON attribute documents and the SQLite rows.
- `config.py` derives every path from a single server root, so the
  detector, the database layer and the CLI always agree on where the
  data lives. `RAINRS_HOME` overrides the root.
- `process/image_read.py` owns the detection stage and knows nothing
  about key derivation.
- `process/rungge.py` owns the derivation stage and reads the stored
  attributes from the database.
- `process/dev.py` is the single place where development output is
  produced, so the console printing can be removed with one edit.

## Conventions

- Every module starts with a docstring that states its inputs and its
  outputs.
- The heavy imports (`ultralytics`, `torch`) happen inside the
  functions that need them, so `--help` stays fast and the test suite
  runs without the neural network. The detector is injected through the
  `RippleDetector` protocol for exactly that reason.
- Timestamps are UTC in ISO 8601 format (`model.base.utc_now_iso`).
- Errors are logged with `logger.error`; the CLI turns a failed capture
  into a non-zero exit code instead of raising.

## Tests

The test suite mirrors this structure in `tests/`
(`tests/model/`, `tests/input/`, `tests/process/`, `tests/output/`) and
imports the installed package.
