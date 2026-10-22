"""Allow ``python -m rainrs_server`` to run the pipeline CLI."""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
