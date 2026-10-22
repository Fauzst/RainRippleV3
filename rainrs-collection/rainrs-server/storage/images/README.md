# Images

Captured rain-ripple images handled by the pipeline.

```
images/
  raw/                 incoming captures (the input of the pipeline)
  processed/           captures whose features were extracted
```

- **`raw/`** — put new captures here. The detector scans this directory
  for files with a supported extension (`.jpg`, `.jpeg`, `.png`, `.bmp`,
  `.tif`, `.tiff`, `.webp`). A capture is moved to `processed/` once its
  features were extracted, deleted when no ripple was detected, and
  kept here when the detection failed.
- **`processed/`** — the captures whose features were extracted.

**Image files are never committed.** They are research data and are
excluded by the repository `.gitignore` (all common image extensions
are ignored globally; curated fixtures under
`rainrs-collection/rainrs-server/tests/fixtures/` are explicitly
re-included).

See `../../storage/README.md` for the full storage layout and the
handling rules.
