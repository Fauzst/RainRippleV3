"""Tests for the output layer (the JSON attribute documents)."""

from __future__ import annotations

import json
from pathlib import Path

from rainrs_server.model.detection import RippleAttributes, RippleDetection
from rainrs_server.output.attributes import AttributeWriter


def _attributes(source: str = "/captures/a.jpg") -> RippleAttributes:
    return RippleAttributes(
        source_path=source,
        image_width=200,
        image_height=113,
        detected_at="2026-10-22T10:00:00+00:00",
        ripples=(
            RippleDetection(
                index=0,
                center_x=100.0,
                center_y=56.5,
                radius=8.0,
                width=16.0,
                height=16.0,
                confidence=0.87,
            ),
        ),
    )


def test_write_creates_the_directory(tmp_path: Path) -> None:
    """The features directory is created when it does not exist."""
    writer = AttributeWriter(tmp_path / "features")

    target = writer.write(_attributes())

    assert target.exists()
    assert target.parent == tmp_path / "features"


def test_write_uses_the_stem_of_the_source(tmp_path: Path) -> None:
    """The document is named after the capture it belongs to."""
    writer = AttributeWriter(tmp_path / "features")

    target = writer.write(_attributes("/captures/sample.jpg"))

    assert target.name == "sample.json"


def test_document_holds_the_attributes(tmp_path: Path) -> None:
    """The written document is the JSON form of the attributes."""
    writer = AttributeWriter(tmp_path / "features")

    target = writer.write(_attributes())
    payload = json.loads(target.read_text(encoding="utf-8"))

    assert payload["ripple_count"] == 1
    assert payload["ripples"][0]["radius"] == 8.0
    assert payload["image_width"] == 200
    assert payload["source_path"] == "/captures/a.jpg"


def test_document_is_stable(tmp_path: Path) -> None:
    """Two runs over the same attributes produce the same document."""
    writer = AttributeWriter(tmp_path / "features")

    first = writer.write(_attributes()).read_text(encoding="utf-8")
    second = writer.write(_attributes()).read_text(encoding="utf-8")

    assert first == second
