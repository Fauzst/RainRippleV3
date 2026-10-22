"""Tests for the YOLO26 feature extraction stage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from conftest import StubDetector, write_capture

from rainrs_server.models import STATUS_ERROR, STATUS_NO_FEATURES, STATUS_PROCESSED
from rainrs_server.process.image_read import (
    RippleFeatureExtractor,
    is_supported_image,
    process_directory,
    process_image,
)
from rainrs_server.storage.database import list_image_ids, load_image, open_database


def _extractor(
    pipeline_dirs: dict[str, Path],
    detector: StubDetector,
    **kwargs: Any,
) -> RippleFeatureExtractor:
    return RippleFeatureExtractor(
        detector=detector,
        database_path=pipeline_dirs["database"],
        features_dir=pipeline_dirs["features"],
        raw_dir=pipeline_dirs["raw"],
        processed_dir=pipeline_dirs["processed"],
        **kwargs,
    )


def test_extract_returns_ripple_attributes(
    pipeline_dirs: dict[str, Path], stub_detector: StubDetector
) -> None:
    capture = write_capture(pipeline_dirs["raw"])
    extractor = _extractor(pipeline_dirs, stub_detector)

    attributes = extractor.extract(capture)

    assert attributes.count == 3
    assert attributes.image_width == 200
    assert attributes.image_height == 113
    assert attributes.ripples[1].center_x == 120.0
    assert attributes.mean_radius == 6.5


def test_process_image_stores_features_and_moves_capture(
    pipeline_dirs: dict[str, Path], stub_detector: StubDetector
) -> None:
    capture = write_capture(pipeline_dirs["raw"], "sample.jpg")
    extractor = _extractor(pipeline_dirs, stub_detector)

    outcome = extractor.process_image(capture)

    assert outcome.status == STATUS_PROCESSED
    assert outcome.ripple_count == 3
    assert outcome.image_id is not None

    # The capture moved out of the raw directory.
    assert not capture.exists()
    moved = pipeline_dirs["processed"] / "sample.jpg"
    assert moved.exists()

    # The JSON attribute document was written.
    features_file = pipeline_dirs["features"] / "sample.json"
    assert features_file.exists()
    payload = json.loads(features_file.read_text(encoding="utf-8"))
    assert payload["ripple_count"] == 3
    assert payload["ripples"][0]["radius"] == 6.0
    assert payload["image_id"] == outcome.image_id
    assert payload["stored_path"] == str(moved)

    # And the database holds the image and its ripple rows.
    with open_database(pipeline_dirs["database"]) as connection:
        assert list_image_ids(connection) == [outcome.image_id]
        stored = load_image(connection, outcome.image_id)
        assert stored is not None
        assert stored.count == 3
        assert stored.stored_path == str(moved)


def test_capture_without_ripples_is_deleted(pipeline_dirs: dict[str, Path]) -> None:
    capture = write_capture(pipeline_dirs["raw"], "empty.jpg")
    detector = StubDetector(())
    extractor = _extractor(pipeline_dirs, detector)

    outcome = extractor.process_image(capture)

    assert outcome.status == STATUS_NO_FEATURES
    assert outcome.ripple_count == 0
    assert not capture.exists()
    assert not (pipeline_dirs["features"] / "empty.json").exists()

    with open_database(pipeline_dirs["database"]) as connection:
        assert list_image_ids(connection) == [outcome.image_id]


def test_capture_without_ripples_can_be_kept(pipeline_dirs: dict[str, Path]) -> None:
    capture = write_capture(pipeline_dirs["raw"], "empty.jpg")
    extractor = _extractor(
        pipeline_dirs, StubDetector(()), delete_without_features=False
    )

    outcome = extractor.process_image(capture)

    assert outcome.status == STATUS_NO_FEATURES
    assert capture.exists()


def test_detection_error_is_logged_and_recorded(pipeline_dirs: dict[str, Path]) -> None:
    capture = write_capture(pipeline_dirs["raw"], "broken.jpg")
    detector = StubDetector(error=RuntimeError("model exploded"))
    extractor = _extractor(pipeline_dirs, detector)

    outcome = extractor.process_image(capture)

    assert outcome.status == STATUS_ERROR
    assert outcome.error == "model exploded"
    # A failed capture stays in the raw directory so it can be retried.
    assert capture.exists()

    with open_database(pipeline_dirs["database"]) as connection:
        row = connection.execute("SELECT status, error FROM images").fetchone()
        assert row["status"] == STATUS_ERROR
        assert row["error"] == "model exploded"


def test_process_directory_handles_every_capture(
    pipeline_dirs: dict[str, Path], stub_detector: StubDetector
) -> None:
    write_capture(pipeline_dirs["raw"], "a.jpg")
    write_capture(pipeline_dirs["raw"], "b.jpg")
    (pipeline_dirs["raw"] / "notes.txt").write_text("ignored", encoding="utf-8")
    extractor = _extractor(pipeline_dirs, stub_detector)

    outcomes = extractor.process_directory()

    assert len(outcomes) == 2
    assert all(outcome.status == STATUS_PROCESSED for outcome in outcomes)
    assert len(stub_detector.calls) == 2
    # Files that are not images are ignored, not deleted.
    assert (pipeline_dirs["raw"] / "notes.txt").exists()


def test_process_directory_without_directory(
    pipeline_dirs: dict[str, Path], stub_detector: StubDetector
) -> None:
    extractor = _extractor(pipeline_dirs, stub_detector)
    assert extractor.process_directory(pipeline_dirs["root"] / "missing") == []


def test_no_move_keeps_the_capture_in_place(
    pipeline_dirs: dict[str, Path], stub_detector: StubDetector
) -> None:
    capture = write_capture(pipeline_dirs["raw"], "keep.jpg")
    extractor = _extractor(pipeline_dirs, stub_detector, move_images=False)

    outcome = extractor.process_image(capture)

    assert outcome.status == STATUS_PROCESSED
    assert capture.exists()
    assert not list(pipeline_dirs["processed"].iterdir())


def test_is_supported_image() -> None:
    assert is_supported_image(Path("capture.jpg"))
    assert is_supported_image(Path("capture.JPEG"))
    assert not is_supported_image(Path("capture.txt"))


def test_functional_wrappers_delegate_to_the_extractor(
    pipeline_dirs: dict[str, Path], stub_detector: StubDetector
) -> None:
    capture = write_capture(pipeline_dirs["raw"], "wrapper.jpg")
    extractor = _extractor(pipeline_dirs, stub_detector)

    outcome = process_image(capture, extractor=extractor)

    assert outcome.status == STATUS_PROCESSED
    assert outcome.ripple_count == 3
    assert not capture.exists()

    write_capture(pipeline_dirs["raw"], "second.jpg")
    outcomes = process_directory(extractor=extractor)

    assert len(outcomes) == 1
    assert outcomes[0].status == STATUS_PROCESSED
