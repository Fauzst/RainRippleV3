# Tasks — rainrs-server

> Status legend: `TODO` · `IN PROGRESS` · `BLOCKED` · `DONE` · `CANCELLED`
>
> The architect adds and defines tasks. The programmer updates statuses
> and checks off acceptance criteria as work completes.
>
> Scope: `rainrs-collection/rainrs-server` only. Repository-level tasks
> live at the root in `agent/TASKS.md`.

## Backlog

<!-- Add tasks here. Copy the template below.

### S-001: <Task title>
- **Status:** TODO
- **Depends on:** —
- **Description:** What needs to be done and why.
- **Acceptance criteria:**
  - [ ] Criterion 1
  - [ ] Criterion 2
-->

### S-001: <Github Preparation>
- **Status:** DONE
- **Depends on:** —
- **Description:** Make a new branch called feat/image_process, it should be based from the updated dev branch. Use this new branch
- **Acceptance criteria:**
  - [x] Created feat/image_process branch
  - [x] Switch and used feat/image_process branch
  - [x] ensure .gitignore includes .jpeg or any images file
- **Verification:** `feat/image_process` was created from `dev` @ `04fc7ed`
  (`origin/dev` was fetched first and was already up to date) and is the
  branch all of the following work was committed on. The root
  `.gitignore` now ignores `*.jpg`, `*.jpeg`, `*.png`, `*.bmp`, `*.tif`,
  `*.tiff`, `*.webp`, `*.gif` and `*.heic` globally, re-includes the
  curated fixtures under `rainrs-collection/rainrs-server/tests/fixtures/`,
  and additionally excludes the server runtime artefacts (SQLite
  database, log files, derived feature documents and the redundant
  `last.pt` checkpoint). Confirmed with `git check-ignore -v`.

### S-002: <Yolo26 Model Integration>
- **Status:** DONE
- **Depends on:** —
- **Description:** on the /home/rain_dev/Documents/Development/rainrs/rainrs-collection/rainrs-server/src/rainrs_server/process/image_read.py, create an algorithm that will utiliize the yolo26 model in rainrs-collection/rainrs-server/model/content/runs/detect/rain_ripple_yolo26_cpu. It should use the images in /storage/images/raw as a test input and it should output JSON rain ripple attribute.
- **Acceptance criteria:**
  - [x] The algorithm should be modular with documentation (specifically on what are the inputs and what are the outputs)
  - [x] The algorithm should successfully process the 10 test images on /storage/images/raw
  - [x] The algorithm should have error handling, and logs saved in /home/rain_dev/Documents/Development/rainrs/rainrs-collection/rainrs-server/logs
  - [x] The algorithm should move the used image from raw to processed once the features are successfully extracted.
  - [x] If no features are extracted on an image, it should be deleted
  - [x] Save the extracted features in an SQLite database.
  - [x] There must be an easy to remove console printing for development double checking
- **Verification:** Implemented in
  `src/rainrs_server/process/image_read.py` (`RainRippleDetector`,
  `RippleDetector` protocol, `RippleFeatureExtractor`), supported by
  `src/rainrs_server/models.py`, `config.py`, `logging_setup.py` and
  `storage/database.py`. The module docstring documents the inputs
  (capture file + detector weights) and the outputs
  (`RippleAttributes`, JSON attribute document, `images`/`ripples` rows,
  moved capture). Real run over the ten sample captures:
  `processed=10 no_features=0 errors=0`, 37 ripples, all captures moved
  to `storage/images/processed`, ten JSON documents in
  `storage/features/`, log written to `logs/rainrs.log`. The no-feature
  branch was verified separately (`conf=0.95`: capture deleted, status
  `no_features`) and the error branch with a corrupt file (error logged,
  status `error`, capture kept, CLI exit code 1). The development
  printing is centralised in `src/rainrs_server/process/dev.py`
  (`dev_print`, env var `RAINRS_DEV_PRINT`, stdout only, never logged),
  so it can be removed with a single edit.

### S-002: <Rungge-Kutta Integration>
- **Status:** DONE
- **Depends on:** S-002 (image_read.py)
- **Description:** On rungge.py, do rungge-kutta integration. The goal of rungge-kutta is make a random numbers that are so random, using the rain ripple as our parameter. If I am not mistaken, the result of the S-001 should contain number of ripples, position of ripples, radius of ripples. The expected output of this code is a master key (derived from running the average of rain attributes: position, radius, number to the rungge-kutta generator function) and a slave key (which runs every individual rain attribute to rungge-kutta function and XOR it with master key [I dont know if that would create random enough numbers, you are free to suggest after process for slave key]). You should save the output on a SQLite database.
- **Acceptance criteria:**
  - [x] The algorithm must have logging and error handling
  - [x] The algorithm is expected to accept rain ripple attribute as an input, and return a rungge-kuta processed output.
  - [x] For every image, there must only one master key, and many slave key
  - [x] When storing on database, slave key must have an identification on which master key it belongs
  - [x] There must be an easy to remove print for development double checking
- **Verification:** Implemented in `src/rainrs_server/process/rungge.py`:
  `rk4_step` / `rk4_integrate` (classical RK4, dt 0.01, 4000 steps,
  every 10th state sampled), `RippleWaveSystem` (two coupled van der Pol
  oscillators whose parameters are derived from the ripple geometry),
  `derive_master_key` (averaged attributes -> RK4 -> SHA-256 digest
  truncated to 32/64 bit) and `derive_slave_keys` (one key per ripple),
  plus the `KeyDeriver` façade that reads the stored attributes, writes
  the keys and skips captures that already have a master key.
  Real run: 10 master keys and 37 slave keys stored; every slave row
  carries the `master_key_id` foreign key that identifies its master,
  and `master_keys.image_id` is `UNIQUE`, so exactly one master key can
  exist per capture.
  **Architectural note (answer to the open question in the task):** the
  slave keys are bound to the master key with **HMAC-SHA256** by default
  instead of a plain XOR, because a XOR lets two equal inputs cancel out
  and does not separate the child key from the parent. The XOR variant
  is kept as the `--binding xor` option so the original idea can still
  be reproduced and compared. The rationale is recorded in
  `docs/decisions/0002-rainrs-server-pipeline.md`.

### S-003: <Document>
- **Status:** DONE
- **Depends on:** S-002 and S-003
- **Description:** Make the necessary and related documentations of what we have done. It is preferred to use docx. format, add diagrams to easily visualize data flow, functions, and entity relationship for database related documentation
- **Acceptance criteria:**
  - [x] A docx file for documentation must be located at /home/rain_dev/Documents/Development/rainrs/rainrs-collection/rainrs-server/docs
  - [x] The documentation must include activity diagram, sequence diagram, class diagram, ERD, and component diagram
- **Verification:** `docs/rainrs-server-documentation.docx` (845 KB) is
  generated by `tools/build_documentation.py`
  (`uv run python tools/build_documentation.py`). It contains all five
  diagrams as embedded images — component, activity, class, sequence and
  entity relationship — plus the overview, the storage layout, the CLI
  reference, the security considerations, the known limitations and the
  verification results. The five rendered diagrams were checked
  programmatically: no overlapping text labels and no label crossing a
  box border.
## Active

## Done

- S-001 — Github Preparation
- S-002 — Yolo26 Model Integration
- S-002 — Rungge-Kutta Integration
- S-003 — Document

## Cancelled
