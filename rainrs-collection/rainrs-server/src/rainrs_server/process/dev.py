"""Development-only console printing.

Every diagnostic print in the processing pipeline goes through
:func:`dev_print`, so that development double-checking output can be
removed or disabled in exactly one place:

* to silence it permanently, delete the ``dev_print`` calls (or turn the
  body of :func:`dev_print` into a ``return``);
* to silence it temporarily, leave ``RAINRS_DEV_PRINT`` unset.

``dev_print`` writes to ``stdout`` only. It never writes to the logging
system, because the pipeline logs are a permanent artefact and must not
contain derived features or key material (see the repository-root
``AGENTS.md``, "Security Boundaries").
"""

from __future__ import annotations

import os
import sys
from typing import Any

ENV_DEV_PRINT = "RAINRS_DEV_PRINT"

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def dev_print_enabled() -> bool:
    """Return ``True`` when development printing is switched on."""
    return os.environ.get(ENV_DEV_PRINT, "").strip().lower() in _TRUTHY


def dev_print(message: str, *args: Any) -> None:
    """Print a development diagnostic message to stdout.

    The call is a no-op unless ``RAINRS_DEV_PRINT`` is set to a truthy
    value, which keeps the production output clean.
    """
    if not dev_print_enabled():
        return
    text = message % args if args else message
    print(f"[dev] {text}", file=sys.stdout, flush=True)
