"""The result of processing a single capture.

The extraction stage reports one :class:`ImageOutcome` per capture it
handled. The status tells the caller what happened, and the remaining
fields carry the identifiers of the stored artefacts.

The status values are the contract between the extraction stage, the
CLI and the SQLite ``images.status`` column; they are kept as plain
strings so that they can be stored verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "STATUS_ERROR",
    "STATUS_NO_FEATURES",
    "STATUS_PROCESSED",
    "STATUS_VALUES",
    "ImageOutcome",
]

#: The features were extracted and stored.
STATUS_PROCESSED = "processed"

#: No ripple was detected; the capture carries no measurable feature.
STATUS_NO_FEATURES = "no_features"

#: The capture could not be processed; the error is reported in
#: :attr:`ImageOutcome.error`.
STATUS_ERROR = "error"

#: Every status the extraction stage can report.
STATUS_VALUES = (STATUS_PROCESSED, STATUS_NO_FEATURES, STATUS_ERROR)


@dataclass(frozen=True, slots=True)
class ImageOutcome:
    """Outcome of processing a single image file.

    Attributes:
        source: Path of the capture that was processed.
        status: One of ``processed``, ``no_features`` or ``error``.
        image_id: Identifier of the stored ``images`` row, when there is
            one.
        ripple_count: Number of detected ripples.
        features_path: Path of the JSON attribute document.
        stored_path: Path the capture was moved to.
        error: Error message, set only when ``status`` is ``error``.
    """

    source: str
    status: str
    image_id: int | None = None
    ripple_count: int = 0
    features_path: str | None = None
    stored_path: str | None = None
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        """``True`` when features were extracted and stored."""
        return self.status == STATUS_PROCESSED
