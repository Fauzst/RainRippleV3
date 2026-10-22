"""Tests for the runtime configuration helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from rainrs_server.config import (
    DetectionSettings,
    ServerPaths,
    find_server_root,
    resolve_key_bits,
)


def test_server_paths_are_derived_from_the_root(tmp_path: Path) -> None:
    paths = ServerPaths.from_root(tmp_path)

    assert paths.root == tmp_path.resolve()
    assert paths.raw_images_dir == tmp_path.resolve() / "storage" / "images" / "raw"
    assert paths.processed_images_dir == (
        tmp_path.resolve() / "storage" / "images" / "processed"
    )
    assert paths.features_dir == tmp_path.resolve() / "storage" / "features"
    assert paths.database == tmp_path.resolve() / "storage" / "rainrs.db"
    assert paths.logs_dir == tmp_path.resolve() / "logs"
    assert paths.model_weights.name == "best.pt"


def test_ensure_directories_creates_the_layout(tmp_path: Path) -> None:
    paths = ServerPaths.from_root(tmp_path)
    paths.ensure_directories()

    assert paths.raw_images_dir.is_dir()
    assert paths.processed_images_dir.is_dir()
    assert paths.features_dir.is_dir()
    assert paths.logs_dir.is_dir()


def test_find_server_root_detects_the_application(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("RAINRS_HOME", raising=False)
    root = find_server_root()
    assert (root / "pyproject.toml").is_file()


def test_find_server_root_honours_the_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RAINRS_HOME", str(tmp_path))
    assert find_server_root() == tmp_path.resolve()


def test_detection_settings_are_validated() -> None:
    settings = DetectionSettings(conf=0.4, iou=0.5, imgsz=320, device="cpu").validated()
    assert settings.conf == 0.4

    with pytest.raises(ValueError):
        DetectionSettings(conf=0.0).validated()
    with pytest.raises(ValueError):
        DetectionSettings(iou=1.5).validated()
    with pytest.raises(ValueError):
        DetectionSettings(imgsz=0).validated()
    with pytest.raises(ValueError):
        DetectionSettings(device="").validated()


def test_resolve_key_bits() -> None:
    assert resolve_key_bits(32) == 32
    assert resolve_key_bits(64) == 64
    with pytest.raises(ValueError):
        resolve_key_bits(128)
