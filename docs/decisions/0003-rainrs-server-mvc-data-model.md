# Decision 0003 — rainrs-server MVC split with a declarative data model

- **Date:** 2026-10-22
- **Status:** Accepted
- **Scope:** `rainrs-collection/rainrs-server`
- **Deciders:** Joshua Elijah L. Pura (architect) — implementation by the programmer agent
- **Related:** `docs/decisions/0001-rainrs-server-initial-layout.md`,
  `docs/decisions/0002-rainrs-server-pipeline.md`,
  `rainrs-collection/rainrs-server/agent/TASKS.md` (S-004)

## Context

Task S-004 asked for a model package that holds the data model of the
pipeline — the variable types and their names — and asked for that
model to be used as the backbone of a simple MVC split of the `input/`,
`process/` and `output/` folders. The purpose was stated plainly: make
the shape of the data that is flowing easy to visualize.

Before the task the package had grown organically:

- `models.py` held the dataclasses of both stages in a single file;
- `storage/` held the SQLite persistence;
- the input side (finding the captures, deciding which file is an
  image) was spread across `process/image_read.py` and `config.py`;
- the JSON attribute documents were written by a helper inside the
  process layer.

Two consequences made the shape of the data hard to see: the model was
buried in a file next to the code that consumed it, and the model was
described only by the dataclasses. Nothing stated which fields an
entity has, what type they are and what they mean, so the documentation
had to be written by hand and could silently disagree with the code.

## Decision

### 1. The package is split into model / input / process / output

```
src/rainrs_server/
  model/      the data model
  input/      the incoming captures
  process/    the two stages
  output/     the attribute documents and the SQLite rows
```

The dependency direction is one-way: `input` and `output` know the
model, `process` knows the model and both sides, and the model knows
nothing else. The model is therefore the contract of the application.

`models.py` and the `storage/` package were removed without a
compatibility shim; the classes moved to `model/detection.py`,
`model/keys.py`, `model/outcome.py` and `model/state.py`, and the
SQLite module moved to `output/database.py`. The `input/` and
`output/` folders already existed in the initial scaffold, so the split
follows the intent of the original layout.

### 2. The model is declarative: a catalogue next to the dataclasses

`model/schema.py` holds the catalogue of the model:

- `Field(name, type, description, nullable)` — one field;
- `Entity(name, description, table, fields)` — one entity;
- `SCHEMA` — the tuple of every entity, and `ENTITY_CLASSES`, the map
  from the entity name to the dataclass that implements it.

`verify()` compares the catalogue with the dataclasses field by field
(the raw `__annotations__` are compared, so `Optional[X]` and `X | None`
are treated as the same type). The test suite calls it, so a field that
was added, renamed or retyped without updating the catalogue fails the
build. The catalogue is also the input of the data model diagram and of
the per-entity schema tables in the documentation, so the document
cannot drift away from the code either.

The `table` field of an entity names the SQLite table the entity is
persisted in; entities without a table are transient values that only
exist inside the pipeline.

### 3. The stages own their collaborators

`RippleFeatureExtractor` no longer reaches for the filesystem or for
SQLite. It receives the detector, the capture library and the attribute
writer, and the CLI builds them:

```python
RippleFeatureExtractor(
    detector=detector,
    database_path=database_path,
    captures=captures,
    writer=writer,
    move_images=...,
    delete_without_features=...,
)
```

This is what makes the layers visible: the input layer produces the
captures, the process layer consumes them and produces the model
objects, and the output layer stores them.

### 4. Frozen dataclasses get copy helpers

The model classes are frozen, so a stage that learns something new
about an object (the storage path of an image, the id of a master key)
cannot mutate it. Instead of reconstructing the object field by field,
the model provides `with_storage(...)`, `with_image_id(...)` and
`with_master_key_id(...)`, which keep the copy helpers next to the
definition of the data.

## Consequences

- Positive: the shape of the data is described once, in
  `model/schema.py`, and is checked by the test suite against the
  dataclasses that implement it.
- Positive: the documentation (data model diagram and schema tables) is
  generated from that catalogue and therefore describes the running
  code.
- Positive: the layers are independent enough to be tested on their own
  — the new tests cover the model, the input layer and the output layer
  without a detector and without a database.
- Positive: the behaviour of the pipeline did not change. A real run
  over the ten sample captures produces the same counts as before the
  refactoring (`processed=10 no_features=0 errors=0`, 10 master keys,
  37 slave keys), and the derived keys are byte-identical to the ones
  written by the previous implementation.
- Negative / risk: the module paths changed (`models.py` and
  `storage/` disappeared). Anything outside this application that
  imported them has to be updated. The server is not published and has
  no external consumers yet.
- Negative / risk: the catalogue duplicates the dataclass definitions.
  The duplication is deliberate — it adds the meaning of a field, which
  a dataclass cannot carry — and it is controlled by `verify()` and the
  test suite.
- Note: the API surface of the server is still undecided and is tracked
  in `rainrs-collection/rainrs-server/agent/PLAN.md`; the pipeline is
  currently reachable through the CLI only.
