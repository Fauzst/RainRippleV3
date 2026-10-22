"""The output layer of the pipeline.

This layer owns everything that *leaves* the application: the JSON
attribute documents and the SQLite rows that hold the extracted
features and the derived research artifacts.

Modules
-------
``output.attributes``
    Writes the JSON attribute document of a processed capture.
``output.database``
    The SQLite schema and the persistence helpers.
"""

from __future__ import annotations

from .attributes import AttributeWriter

__all__ = ["AttributeWriter"]
