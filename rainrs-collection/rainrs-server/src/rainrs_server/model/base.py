"""Shared building blocks of the rainrs-server data model.

Every value that flows through the pipeline is described by a frozen
dataclass in this package. The data model is the contract between the
three layers of the application:

* ``rainrs_server.input`` produces and consumes the values of the
  capture pipeline;
* ``rainrs_server.process`` computes them;
* ``rainrs_server.output`` stores them.

Because the dataclasses are frozen, a value can never be changed
behind the back of the layer that produced it, and because every one of
them implements :meth:`to_dict` / :meth:`from_dict`, the same value
can travel through the pipeline, through the JSON attribute documents
and through the SQLite tables without a second representation.

The exact shape of the data — the field names, their types and their
meaning — is documented in :mod:`rainrs_server.model.schema`, and the
catalogue is verified against the dataclasses by the test suite.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

#: The JSON representation of a value of the data model.
JsonObject = dict[str, Any]

#: The format every timestamp of the data model uses.
TIMESTAMP_FORMAT = "ISO 8601 (UTC)"


@runtime_checkable
class Serialisable(Protocol):
    """A value that knows how to represent itself as a JSON object."""

    def to_dict(self) -> JsonObject:
        """Return the JSON representation of the value."""


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string.

    The whole application uses this format, so the timestamps of the
    attribute documents, of the database rows and of the log records
    can be compared with each other.
    """
    return datetime.now(UTC).isoformat(timespec="seconds")
