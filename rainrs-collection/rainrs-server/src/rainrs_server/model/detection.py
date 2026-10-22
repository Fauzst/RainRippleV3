"""The measured geometry of the rain ripples of a single capture.

The dataclasses of this module describe what the detector sees in one
captured image:

* :class:`RippleDetection` — one detected ripple (position, radius, …).
* :class:`DetectionResult` — the raw detector output for one image.
* :class:`RippleAttributes` — every measurement extracted from a single
  captured image; this is the input of the Runge–Kutta key derivation.

All of them are JSON-serialisable through :meth:`to_dict`, which is what
the pipeline writes to ``storage/features/*.json`` and to the
``features_json`` column of the SQLite database.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = [
    "DetectionResult",
    "RippleAttributes",
    "RippleDetection",
]


@dataclass(frozen=True, slots=True)
class RippleDetection:
    """A single rain ripple detected inside a captured image.

    Attributes:
        index: Zero-based position of the ripple inside its image.
        center_x: Horizontal centre of the ripple in pixels.
        center_y: Vertical centre of the ripple in pixels.
        radius: Equivalent radius in pixels, ``(width + height) / 4``; for
            a circular ripple this equals the geometric radius.
        width: Bounding-box width in pixels.
        height: Bounding-box height in pixels.
        confidence: Detector confidence in the range ``0.0``–``1.0``.
    """

    index: int
    center_x: float
    center_y: float
    radius: float
    width: float
    height: float
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation of the detection."""
        return {
            "index": self.index,
            "center_x": self.center_x,
            "center_y": self.center_y,
            "radius": self.radius,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RippleDetection:
        """Rebuild a detection from :meth:`to_dict` output."""
        return cls(
            index=int(payload["index"]),
            center_x=float(payload["center_x"]),
            center_y=float(payload["center_y"]),
            radius=float(payload["radius"]),
            width=float(payload["width"]),
            height=float(payload["height"]),
            confidence=float(payload["confidence"]),
        )


@dataclass(frozen=True, slots=True)
class DetectionResult:
    """Raw detector output for a single image.

    Attributes:
        image_width: Width of the source image in pixels.
        image_height: Height of the source image in pixels.
        ripples: The detected ripples, ordered by detector output.
    """

    image_width: int
    image_height: int
    ripples: tuple[RippleDetection, ...] = ()


@dataclass(frozen=True, slots=True)
class RippleAttributes:
    """Every ripple measurement extracted from one captured image.

    This object is the *input* of the Runge–Kutta key derivation: the
    master key is derived from the averaged attributes, the slave keys
    from the individual ripple attributes.
    """

    source_path: str
    image_width: int
    image_height: int
    detected_at: str
    ripples: tuple[RippleDetection, ...] = ()
    image_id: int | None = None
    stored_path: str | None = None

    @property
    def count(self) -> int:
        """Number of detected ripples."""
        return len(self.ripples)

    @property
    def mean_center_x(self) -> float:
        """Mean horizontal centre of the ripples (0.0 when there are none)."""
        if not self.ripples:
            return 0.0
        return sum(r.center_x for r in self.ripples) / len(self.ripples)

    @property
    def mean_center_y(self) -> float:
        """Mean vertical centre of the ripples (0.0 when there are none)."""
        if not self.ripples:
            return 0.0
        return sum(r.center_y for r in self.ripples) / len(self.ripples)

    @property
    def mean_radius(self) -> float:
        """Mean radius of the ripples (0.0 when there are none)."""
        if not self.ripples:
            return 0.0
        return sum(r.radius for r in self.ripples) / len(self.ripples)

    def with_storage(
        self,
        *,
        image_id: int | None = None,
        stored_path: str | None = None,
    ) -> RippleAttributes:
        """Return a copy with the storage identifiers filled in.

        The dataclass is frozen and the identifiers of a capture only
        exist once its attributes were stored, so they are filled in
        through a copy. A value of ``None`` keeps the current one.

        Args:
            image_id: Identifier of the stored ``images`` row.
            stored_path: Path the capture was moved to.

        Returns:
            The updated attributes.
        """
        return RippleAttributes(
            source_path=self.source_path,
            image_width=self.image_width,
            image_height=self.image_height,
            detected_at=self.detected_at,
            ripples=self.ripples,
            image_id=self.image_id if image_id is None else image_id,
            stored_path=self.stored_path if stored_path is None else stored_path,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON-serialisable attribute document."""
        return {
            "image_id": self.image_id,
            "source_path": self.source_path,
            "stored_path": self.stored_path,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "detected_at": self.detected_at,
            "ripple_count": self.count,
            "mean_center_x": self.mean_center_x,
            "mean_center_y": self.mean_center_y,
            "mean_radius": self.mean_radius,
            "ripples": [r.to_dict() for r in self.ripples],
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RippleAttributes:
        """Rebuild an attribute document from :meth:`to_dict` output."""
        ripples = tuple(
            RippleDetection.from_dict(item) for item in payload.get("ripples", [])
        )
        return cls(
            source_path=str(payload["source_path"]),
            image_width=int(payload["image_width"]),
            image_height=int(payload["image_height"]),
            detected_at=str(payload["detected_at"]),
            ripples=ripples,
            image_id=payload.get("image_id"),
            stored_path=payload.get("stored_path"),
        )
