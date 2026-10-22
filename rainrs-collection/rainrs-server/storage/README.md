# Storage

Runtime data of the rainrs-server pipeline. **Everything in this
directory is derived data** and is excluded from version control by the
repository `.gitignore`.

```
storage/
  rainrs.db              SQLite database (features + derived keys)
  images/
    raw/                 incoming captures (the input of the pipeline)
    processed/           captures whose features were extracted
  features/              JSON attribute documents, one per capture
```

## `images/raw/`

Where new captures are placed. The detector only looks at files with a
supported extension (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.tif`, `.tiff`,
`.webp`).

A capture leaves `raw/` in one of three ways:

| Outcome | Status | What happens to the file |
|---|---|---|
| Ripples detected | `processed` | Moved to `images/processed/` after the features were stored. |
| No ripple detected | `no_features` | **Deleted** — the capture carries no measurable information. Use `--keep-no-features` to keep it. |
| Detection failed | `error` | **Kept** in `raw/` so the capture can be retried. The error is logged. |

The features are always written *before* the capture is moved, so a
failure can never lose data.

## `images/processed/`

The captures whose features were extracted. They are kept as evidence
for a later re-derivation of the keys. A file name collision is
resolved with a numeric suffix (`capture.jpg` → `capture_1.jpg`).

## `features/`

One JSON document per processed capture, named after the capture
(`sample1.json`). The document holds the source path, the image
geometry, the number of detected ripples, the averaged position and
radius and the individual ripple measurements. The same document is
stored in the `features_json` column of the `images` table.

## `rainrs.db`

The SQLite database with four tables:

| Table | Purpose | Key columns |
|---|---|---|
| `images` | One row per processed capture | `id`, `source_path`, `stored_path`, `status`, `features_json` |
| `ripples` | One row per detected ripple | `id`, `image_id` (FK), `center_x`/`center_y`, `radius`, `confidence` |
| `master_keys` | Exactly one master key per capture | `id`, `image_id` (FK, unique), `master_key`, `bits`, `algorithm` |
| `slave_keys` | One row per ripple, bound to a master key | `id`, `master_key_id` (FK), `image_id` (FK), `ripple_index`, `slave_key` |

Deleting an image row cascades to its ripples, its master key and that
master key's slave keys.

The database holds derived features and key material. It is never
committed, and it is never logged.

## Handling the data

The captures, the attribute documents and the database are research data
of a running experiment. They are not production assets:

- do not commit any of it;
- do not paste feature values or key material into logs, issues or
  chat;
- the key material is experimental (32/64 bit) and deterministic — the
  same capture always yields the same key.
