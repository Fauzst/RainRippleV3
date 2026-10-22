"""Shared fixtures for the rainrs-server test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from rainrs_server.model.detection import DetectionResult, RippleDetection


class StubDetector:
    """Detector double that returns canned detections.

    The stub keeps the test suite independent of the neural network: the
    real :class:`~rainrs_server.process.image_read.RainRippleDetector`
    needs the trained weights and several seconds of CPU time per
    image.
    """

    def __init__(
        self,
        detections: tuple[RippleDetection, ...] = (),
        *,
        width: int = 200,
        height: int = 113,
        error: Exception | None = None,
    ) -> None:
        self.detections = detections
        self.width = width
        self.height = height
        self.error = error
        self.calls: list[Path] = []

    def detect(self, image_path: Path) -> DetectionResult:
        self.calls.append(Path(image_path))
        if self.error is not None:
            raise self.error
        return DetectionResult(
            image_width=self.width,
            image_height=self.height,
            ripples=self.detections,
        )


@pytest.fixture
def sample_ripple() -> RippleDetection:
    """A single ripple with a deterministic geometry."""
    return RippleDetection(
        index=0,
        center_x=100.0,
        center_y=56.5,
        radius=8.0,
        width=16.0,
        height=16.0,
        confidence=0.87,
    )


@pytest.fixture
def sample_ripples() -> tuple[RippleDetection, ...]:
    """Three ripples with a deterministic geometry."""
    return (
        RippleDetection(
            index=0,
            center_x=40.0,
            center_y=30.0,
            radius=6.0,
            width=12.0,
            height=12.0,
            confidence=0.81,
        ),
        RippleDetection(
            index=1,
            center_x=120.0,
            center_y=60.0,
            radius=9.0,
            width=18.0,
            height=18.0,
            confidence=0.93,
        ),
        RippleDetection(
            index=2,
            center_x=170.0,
            center_y=90.0,
            radius=4.5,
            width=9.0,
            height=9.0,
            confidence=0.55,
        ),
    )


@pytest.fixture
def stub_detector(sample_ripples: tuple[RippleDetection, ...]) -> StubDetector:
    """A detector stub that reports three ripples."""
    return StubDetector(sample_ripples)


@pytest.fixture
def pipeline_dirs(tmp_path: Path) -> dict[str, Path]:
    """Directory layout used by the extraction tests."""
    paths = {
        "root": tmp_path,
        "raw": tmp_path / "raw",
        "processed": tmp_path / "processed",
        "features": tmp_path / "features",
        "database": tmp_path / "rainrs.db",
    }
    for key in ("raw", "processed", "features"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def write_capture(directory: Path, name: str = "capture.jpg", size: int = 64) -> Path:
    """Create a placeholder capture file and return its path."""
    target = directory / name
    target.write_bytes(b"\xff\xd8\xff\xe0" + b"0" * size)
    return target
