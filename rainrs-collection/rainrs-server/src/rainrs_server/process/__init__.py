"""Processing stages of the rain-ripple capture pipeline.

* :mod:`rainrs_server.process.image_read` — YOLO26 detection and
  feature extraction from captured images.
* :mod:`rainrs_server.process.rungge` — Runge–Kutta derivation of the
  master and slave research keys.
* :mod:`rainrs_server.process.dev` — development-only console printing.
"""

from __future__ import annotations
