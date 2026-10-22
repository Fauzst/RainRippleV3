"""Rain Ripple Key Generator — server component.

Experimental research software. The pipeline detects rain ripples in
captured images with a trained YOLO26 model, stores the extracted
attributes in SQLite and derives experimental 32/64 bit research
artifacts with a Runge–Kutta integration.

The generated material is **not** a production cryptographic key; see the
repository-root ``AGENTS.md``, section "Security Boundaries".

Structure
---------
The package follows a simple MVC layout. The *model* describes the data,
the other two layers use it:

``model``
    The data model: every value that flows through the pipeline, plus
    the catalogue of its shape (``model.schema``).
``input``
    The capture library: which files are picked up and what happens to
    them.
``process``
    The computation: the YOLO26 detection and the Runge–Kutta
    derivation.
``output``
    The persistence: the JSON attribute documents and the SQLite rows.

Modules
-------
``config``
    Filesystem layout and runtime settings.
``model``
    The data model shared by the three layers.
``logging_setup``
    Log configuration (file based, no feature or key material).
``cli``
    Command line interface (``python -m rainrs_server``).
``input.captures``
    The incoming captures and the lifecycle of their files.
``process.image_read``
    YOLO26 detection and feature extraction.
``process.rungge``
    Runge–Kutta derivation of the master and slave research keys.
``process.dev``
    Development-only console printing.
``output.attributes``
    The JSON attribute documents.
``output.database``
    SQLite schema and persistence helpers.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
