# Decision 0002 — rainrs-server capture pipeline and key derivation

- **Date:** 2026-10-22
- **Status:** Accepted
- **Scope:** `rainrs-collection/rainrs-server`
- **Deciders:** Joshua Elijah L. Pura (architect) — implementation by the programmer agent
- **Related:** `docs/decisions/0001-rainrs-server-initial-layout.md`,
  `rainrs-collection/rainrs-server/agent/TASKS.md` (S-001 … S-003)

## Context

Task S-002 asked for two things: a detector around the trained YOLO26
rain-ripple model, and a Runge–Kutta based key derivation from the
detected ripple attributes. Three questions had to be settled before the
implementation could be committed:

1. Which torch build the project depends on.
2. How a slave key is bound to its master key (the task suggested a
   plain XOR and explicitly left the choice open).
3. How the derived material is described, given that the derivation is
   deterministic.

The questions are recorded here because they change how every consumer
of the pipeline has to treat its output.

## Decision

### 1. CPU-only torch and torchvision

`torch` and `torchvision` are declared as **direct** dependencies and
are resolved from the PyTorch CPU wheel index:

```toml
[tool.uv]
[[tool.uv.index]]
name = "pytorch-cpu"
url = "https://download.pytorch.org/whl/cpu"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch-cpu" }
torchvision = { index = "pytorch-cpu" }
```

The reference host has no CUDA device and the model was trained for CPU
inference (`rain_ripple_yolo26_cpu`), so the default PyPI wheels — which
bundle the CUDA runtime — were pure overhead.

### 2. Slave keys are bound with HMAC-SHA256

The **master key** is derived from the averaged attributes of a capture
(mean position, mean radius, number of ripples) by integrating a
coupled van der Pol oscillator system with the classical fourth order
Runge–Kutta method and condensing the trajectory with SHA-256. The
**slave keys** are derived the same way, but from the individual
attributes of each ripple, and are then bound to the master key:

```
slave = HMAC-SHA256(key = master_key, message = ripple_digest)
```

A plain XOR — the variant proposed in the task — remains available as
`--binding xor` so the original idea can be reproduced and compared,
but it is **not** the default. XOR lets two equal inputs cancel out
(`a ⊕ a = 0`) and does not separate the child key from the parent: the
slave key would leak the XOR of the master key and the ripple digest.
HMAC-SHA256 is a standard primitive, provides key separation and is not
reversible without the master key.

### 3. The derived material is described as deterministic research material

The derivation is fully deterministic: the same capture always produces
the same key. The unpredictability of the artifact therefore comes from
the physical capture and not from the algorithm, and an attacker who
knows a capture can recompute its key. The generated 32/64-bit values
are documented everywhere as **experimental research artifacts** — not
production keys, and not the product of a CSPRNG. Production encryption
must use established cryptographic libraries, approved algorithms and
keys from a CSPRNG.

### 4. One master key per capture, slave keys identified by their master

The SQLite schema enforces the cardinality of the task:

- `master_keys.image_id` is `UNIQUE` → exactly one master key per
  capture;
- `slave_keys.master_key_id` references `master_keys(id)` → every slave
  key identifies the master key it belongs to;
- `slave_keys` also carries `image_id` and `ripple_index`, with
  `UNIQUE (master_key_id, ripple_index)`.

All foreign keys cascade on delete, so removing a capture removes its
ripples, its master key and that key's slave keys.

### 5. Derived data stays out of version control and out of the log

The repository `.gitignore` excludes every image file, the SQLite
database, the JSON attribute documents in `storage/features/` and the
log files. Curated test fixtures under
`rainrs-collection/rainrs-server/tests/fixtures/` are explicitly
re-included. The log records metadata only — file names, counters,
statuses and timings; never features and never key material. The
development printing lives in a single module
(`rainrs_server.process.dev`), writes to stdout only and is switched on
with `--print` or `RAINRS_DEV_PRINT=1`, so it can be removed with one
edit.

## Consequences

- Positive: the virtual environment shrank from 5.8 GB to 1.4 GB
  (torch 2.14.1+cpu, torchvision 0.29.1+cpu) and the pipeline runs on
  the reference hardware without a GPU.
- Positive: the slave keys are separated from the master key by a
  reviewed primitive instead of by an operation that can cancel out.
- Positive: the storage layout and the log contents make it impossible
  to commit or log derived features and key material by accident.
- Negative / risk: the derivation is reproducible from a known capture.
  It must never be presented as a secret that cannot be recomputed.
- Negative / risk: the material is 32/64 bit and has not been
  evaluated with a statistical test suite (e.g. NIST SP 800-22). No
  entropy estimate exists yet.
- Note: the API surface of the server is still undecided and is tracked
  in `rainrs-collection/rainrs-server/agent/PLAN.md`; the pipeline is
  currently reachable through the CLI only.
