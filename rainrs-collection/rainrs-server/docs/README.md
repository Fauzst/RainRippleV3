# rainrs-server documentation

## `rainrs-server-documentation.docx`

The main report of this application: overview of the two pipeline
stages, the data model, the storage layout, the command line reference,
the security considerations, the known limitations and the verification
results.

It embeds six diagrams:

| # | Diagram | Shows |
|---|---|---|
| 1 | Component | The modules of `rainrs_server` and the files and services they talk to. |
| 2 | Activity | The flow of one capture through detection, storage, movement and key derivation, including the no-feature and error branches. |
| 3 | Class | The classes of the input layer, the process layer, the output layer and the data model, with their relations. |
| 4 | Sequence | The runtime order between the CLI, the extraction stage, the detector, the database and the derivation stage. |
| 5 | ERD | The four tables of `storage/rainrs.db` and their relationships. |
| 6 | Data model | The entities of `rainrs_server.model` and the fields they are built from. |

Section 7 of the document describes the data model: one table per
entity with the field names, the types, the nullability and the
meaning of every field. The tables and the diagram are generated from
the catalogue in `src/rainrs_server/model/schema.py`, so they describe
the code that actually runs.

### Regenerating the document

The document is generated — do not edit the `.docx` by hand:

```bash
uv run python tools/build_documentation.py
```

The generator (`tools/build_documentation.py`) renders the diagrams with
matplotlib into a temporary directory and assembles them with
`python-docx` into `docs/rainrs-server-documentation.docx`. The
temporary images are removed afterwards, so only the `.docx` is kept in
the repository. `matplotlib` and `python-docx` are development
dependencies; they are not needed at runtime.

The rendered diagrams were verified programmatically: no two text labels
overlap, no label crosses a box border and no text leaves its frame.

## Other documentation

Server-specific notes are kept here as they are written. Repository-wide
documentation lives in `docs/` at the repository root (architecture,
roadmap, and the decision records in `docs/decisions/`).

The application's own agent documents live in `agent/`:

- `agent/PLAN.md` — the design draft and the decision log
- `agent/TASKS.md` — the task breakdown with the acceptance criteria
- `agent/PROGRESS.md` — the session log
