"""Rain Ripple Key Generator — server component.

Experimental research software. The pipeline detects rain ripples in
captured images with a trained YOLO26 model, stores the extracted
attributes in SQLite and derives experimental 32/64 bit research
artifacts with a Runge–Kutta integration.

The generated material is **not** a production cryptographic key; see the
repository-root ``AGENTS.md``, section "Security Boundaries".

Modules
-------
``config``
    Filesystem layout and runtime settings.
``models``
    Data structures shared by the pipeline stages.
``logging_setup``
    Log configuration (file based, no feature or key material).
``cli``
    Command line interface (``python -m rainrs_server``).
``process.image_read``
    YOLO26 detection and feature extraction.
``process.rungge``
    Runge–Kutta derivation of the master and slave research keys.
``process.dev``
    Development-only console printing.
``storage.database``
    SQLite schema and persistence helpers.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
