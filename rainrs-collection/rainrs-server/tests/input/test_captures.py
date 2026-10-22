"""Tests for the input layer (the capture library)."""

from __future__ import annotations

from pathlib import Path

from conftest import write_capture

from rainrs_server.input.captures import CaptureLibrary, is_supported_image


def _library(tmp_path: Path) -> CaptureLibrary:
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    raw.mkdir(parents=True, exist_ok=True)
    return CaptureLibrary(raw_dir=raw, processed_dir=processed)


def test_is_supported_image() -> None:
    """Only the known image suffixes are supported."""
    assert is_supported_image(Path("capture.jpg"))
    assert is_supported_image(Path("capture.JPEG"))
    assert is_supported_image(Path("capture.png"))
    assert not is_supported_image(Path("capture.txt"))
    assert not is_supported_image(Path("capture"))


def test_list_captures_is_sorted_and_filtered(tmp_path: Path) -> None:
    """The library picks up the images of the raw directory, in order."""
    library = _library(tmp_path)
    write_capture(library.raw_dir, "b.jpg")
    write_capture(library.raw_dir, "a.png")
    (library.raw_dir / "notes.txt").write_text("ignored", encoding="utf-8")

    captures = library.list_captures()

    assert [path.name for path in captures] == ["a.png", "b.jpg"]


def test_list_captures_of_a_missing_directory(tmp_path: Path) -> None:
    """A missing directory yields no captures instead of raising."""
    library = _library(tmp_path)

    assert library.list_captures(tmp_path / "missing") == []


def test_archive_moves_the_capture(tmp_path: Path) -> None:
    """Archiving moves the capture into the processed directory."""
    library = _library(tmp_path)
    capture = write_capture(library.raw_dir, "sample.jpg")

    stored = library.archive(capture)

    assert stored == library.processed_dir / "sample.jpg"
    assert stored.exists()
    assert not capture.exists()


def test_archive_never_overwrites_an_existing_capture(tmp_path: Path) -> None:
    """A second capture with the same name gets a numeric suffix."""
    library = _library(tmp_path)
    library.processed_dir.mkdir(parents=True, exist_ok=True)
    (library.processed_dir / "sample.jpg").write_bytes(b"old")
    capture = write_capture(library.raw_dir, "sample.jpg")

    stored = library.archive(capture)

    assert stored.name == "sample_1.jpg"
    assert (library.processed_dir / "sample.jpg").read_bytes() == b"old"


def test_discard_deletes_the_capture(tmp_path: Path) -> None:
    """A capture without a measurable ripple is removed."""
    library = _library(tmp_path)
    capture = write_capture(library.raw_dir, "empty.jpg")

    library.discard(capture)

    assert not capture.exists()


def test_discard_of_a_missing_capture_is_tolerated(tmp_path: Path) -> None:
    """Discarding a capture that is already gone does not raise."""
    library = _library(tmp_path)

    library.discard(library.raw_dir / "gone.jpg")


def test_directories_are_exposed(tmp_path: Path) -> None:
    """The library exposes the directories it works on."""
    library = _library(tmp_path)

    assert library.raw_dir == tmp_path / "raw"
    assert library.processed_dir == tmp_path / "processed"
